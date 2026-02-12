"""Readiness Engine — cross-layer orchestration.

Combines Layer 1, Layer 2, and signal source data to compute readiness
status and MOSI Score per user per stock. Tracks transitions and emits
notification events on status changes.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.readiness import ReadinessLevel, ReadinessStatus, StatusTransition
from app.models.screener import ScreenerResult
from app.models.analysis import AnalysisCache
from app.models.stock import Stock
from app.services.readiness.signal_source import ISignalSource, SignalResult
from app.services.readiness.classification import classify_readiness, LayerInputs
from app.services.readiness.scoring import compute_mosi_score, ScoreBreakdown

logger = logging.getLogger(__name__)


@dataclass
class ReadinessResult:
    status: ReadinessLevel
    reason: str
    score_breakdown: ScoreBreakdown
    changed: bool


class ReadinessEngine:
    """Orchestrates readiness computation across all 3 layers."""

    def __init__(self, signal_sources: dict[str, ISignalSource]):
        self._signal_sources = signal_sources
        self._notification_callbacks: list = []

    def register_notification_callback(self, callback) -> None:
        self._notification_callbacks.append(callback)

    def get_signal_source(self, source_name: str) -> ISignalSource | None:
        return self._signal_sources.get(source_name)

    async def evaluate_stock(
        self,
        db: Session,
        user_id: str,
        stock_id: int,
        signal_source_name: str = "layer3",
        is_holding: bool = False,
    ) -> ReadinessResult:
        """Evaluate readiness for a single stock for a single user.

        Fetches latest Layer 1 and Layer 2 data from DB, gets signal from
        the configured signal source, classifies, scores, persists, and
        emits notification if status changed.
        """
        stock = db.query(Stock).filter(Stock.id == stock_id).first()
        if stock is None:
            raise ValueError(f"Stock {stock_id} not found")

        # Layer 1: latest screener result for any qualifying model
        screener = (
            db.query(ScreenerResult)
            .filter(ScreenerResult.stock_id == stock_id, ScreenerResult.qualified.is_(True))
            .order_by(ScreenerResult.run_date.desc())
            .first()
        )
        layer1_qualified = screener is not None
        layer1_model = screener.model_type.value if screener else "none"
        layer1_score = screener.score if screener else 0.0

        # Layer 2: latest analysis cache
        analysis = (
            db.query(AnalysisCache)
            .filter(AnalysisCache.stock_id == stock_id)
            .order_by(AnalysisCache.analyzed_at.desc())
            .first()
        )
        layer2_verdict = analysis.verdict.value.capitalize() if analysis and analysis.verdict else None
        layer2_mbs = analysis.analysis_json.get("multi_bagger_score", 0.0) if analysis and analysis.analysis_json else 0.0

        # Signal source
        source = self.get_signal_source(signal_source_name)
        if source is None:
            logger.warning(f"Signal source '{signal_source_name}' not available, using empty signal")
            signal_result = SignalResult()
        else:
            signal_result = await source.get_signal(stock.symbol, user_id)

        # Build inputs and classify
        inputs = LayerInputs(
            layer1_qualified=layer1_qualified,
            layer1_model=layer1_model,
            layer1_score=layer1_score,
            layer2_verdict=layer2_verdict,
            layer2_multi_bagger_score=layer2_mbs,
            signal_result=signal_result,
            is_holding=is_holding,
        )

        status, reason = classify_readiness(inputs)
        score_breakdown = compute_mosi_score(inputs)

        # Persist and track transition
        changed = await self._persist(db, user_id, stock_id, stock, status, reason, score_breakdown, inputs)

        result = ReadinessResult(
            status=status,
            reason=reason,
            score_breakdown=score_breakdown,
            changed=changed,
        )

        if changed:
            await self._notify(user_id, stock.symbol, result)

        return result

    async def evaluate_all_stocks(
        self,
        db: Session,
        user_id: str,
        signal_source_name: str = "layer3",
        holdings: set[int] | None = None,
    ) -> list[ReadinessResult]:
        """Evaluate readiness for all stocks that passed Layer 1 screening."""
        qualified_results = (
            db.query(ScreenerResult)
            .filter(ScreenerResult.qualified.is_(True))
            .order_by(ScreenerResult.run_date.desc())
            .all()
        )

        # Deduplicate by stock_id (keep latest)
        seen: set[int] = set()
        stock_ids: list[int] = []
        for r in qualified_results:
            if r.stock_id not in seen:
                seen.add(r.stock_id)
                stock_ids.append(r.stock_id)

        results = []
        for stock_id in stock_ids:
            is_holding = holdings is not None and stock_id in holdings
            try:
                result = await self.evaluate_stock(db, user_id, stock_id, signal_source_name, is_holding)
                results.append(result)
            except Exception as e:
                logger.warning(f"Failed to evaluate stock {stock_id}: {e}")

        return results

    async def _persist(
        self,
        db: Session,
        user_id: str,
        stock_id: int,
        stock: Stock,
        status: ReadinessLevel,
        reason: str,
        score: ScoreBreakdown,
        inputs: LayerInputs,
    ) -> bool:
        """Persist readiness status and create transition record if changed.

        Returns True if status changed.
        """
        from app.models.screener import ModelType

        existing = (
            db.query(ReadinessStatus)
            .filter(ReadinessStatus.user_id == user_id, ReadinessStatus.stock_id == stock_id)
            .first()
        )

        changed = False
        now = datetime.now(timezone.utc)

        if existing is None:
            model_type_enum = ModelType(inputs.layer1_model) if inputs.layer1_model != "none" else ModelType.PASSIVE_INCOME
            from app.models.analysis import Verdict
            verdict_enum = Verdict(inputs.layer2_verdict.lower()) if inputs.layer2_verdict else None

            existing = ReadinessStatus(
                user_id=user_id,
                stock_id=stock_id,
                status=status,
                mosi_score=score.total,
                layer1_qualified=inputs.layer1_qualified,
                layer1_model=model_type_enum,
                layer2_verdict=verdict_enum,
                signal_source_result=inputs.signal_result.raw_data,
                status_changed_at=now,
            )
            db.add(existing)
            db.flush()

            # First record — log initial transition
            transition = StatusTransition(
                readiness_status_id=existing.id,
                from_status=None,
                to_status=status,
                reason_text=reason,
            )
            db.add(transition)
            changed = True
        else:
            old_status = existing.status
            from app.models.analysis import Verdict
            verdict_enum = Verdict(inputs.layer2_verdict.lower()) if inputs.layer2_verdict else None

            existing.status = status
            existing.mosi_score = score.total
            existing.layer1_qualified = inputs.layer1_qualified
            existing.layer2_verdict = verdict_enum
            existing.signal_source_result = inputs.signal_result.raw_data
            existing.updated_at = now

            if old_status != status:
                existing.status_changed_at = now
                transition = StatusTransition(
                    readiness_status_id=existing.id,
                    from_status=old_status,
                    to_status=status,
                    reason_text=reason,
                )
                db.add(transition)
                changed = True

        db.commit()
        return changed

    async def _notify(self, user_id: str, symbol: str, result: ReadinessResult) -> None:
        """Emit notification event on status change."""
        event = {
            "user_id": user_id,
            "symbol": symbol,
            "new_status": result.status.value,
            "reason": result.reason,
            "mosi_score": result.score_breakdown.total,
        }
        logger.info(f"Readiness change: {symbol} → {result.status.value} (user: {user_id})")
        for callback in self._notification_callbacks:
            try:
                await callback(event)
            except Exception as e:
                logger.error(f"Notification callback failed: {e}")
