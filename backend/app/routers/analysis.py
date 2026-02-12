from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.analysis import AnalysisCache
from app.models.stock import Stock
from app.schemas.analysis import AnalysisResponse, AnalysisSummaryResponse, AnalysisPoint
from app.utils.error_handlers import NotFoundError

router = APIRouter(tags=["analysis"])


def _get_latest_analysis(db: Session, stock_id: int) -> AnalysisCache:
    result = (
        db.query(AnalysisCache)
        .join(Stock)
        .filter(AnalysisCache.stock_id == stock_id)
        .order_by(AnalysisCache.analyzed_at.desc())
        .first()
    )
    if result is None:
        raise NotFoundError(f"No analysis found for stock {stock_id}")
    return result


@router.get("/{stock_id}", response_model=AnalysisResponse)
async def get_analysis(
    stock_id: int,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get full 11-point AI analysis for a stock."""
    result = _get_latest_analysis(db, stock_id)
    analysis_data = result.analysis_json or {}

    points = []
    for pt in analysis_data.get("analysis_points", []):
        points.append(AnalysisPoint(
            point_number=pt.get("point_number", 0),
            title=pt.get("title", ""),
            finding=pt.get("finding", ""),
            score=pt.get("score"),
            evidence=pt.get("evidence", []),
        ))

    return AnalysisResponse(
        stock_id=result.stock_id,
        symbol=result.stock.symbol,
        name=result.stock.name,
        points=points,
        multi_bagger_score=result.multi_bagger_score,
        verdict=result.verdict.value if result.verdict else "hold",
        summary=result.summary_text or "",
        quarter_label=result.quarter_label,
        analyzed_at=result.analyzed_at,
        documents_used=result.documents_used or [],
    )


@router.get("/{stock_id}/summary", response_model=AnalysisSummaryResponse)
async def get_analysis_summary(
    stock_id: int,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get analysis summary — verdict, score, key highlights."""
    result = _get_latest_analysis(db, stock_id)
    return AnalysisSummaryResponse(
        stock_id=result.stock_id,
        symbol=result.stock.symbol,
        name=result.stock.name,
        multi_bagger_score=result.multi_bagger_score,
        verdict=result.verdict.value if result.verdict else "hold",
        summary=result.summary_text or "",
        quarter_label=result.quarter_label,
        analyzed_at=result.analyzed_at,
    )
