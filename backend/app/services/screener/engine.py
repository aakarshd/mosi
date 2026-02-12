"""Screener Engine — runs all 3 models against the stock universe."""

import logging
from datetime import date

from sqlalchemy.orm import Session

from app.models.screener import ModelType, ScreenerResult
from app.models.stock import Stock, Exchange, MarketCapCategory
from app.services.screener.adapters.base import DataSourceAdapter, FinancialData
from app.services.screener.models import PassiveIncomeModel, GrowthModel, PeExpansionModel

logger = logging.getLogger(__name__)

MODEL_MAP = {
    ModelType.PASSIVE_INCOME: PassiveIncomeModel(),
    ModelType.GROWTH: GrowthModel(),
    ModelType.PE_EXPANSION: PeExpansionModel(),
}


def _classify_market_cap(mcap_cr: float) -> MarketCapCategory:
    if mcap_cr >= 20000:
        return MarketCapCategory.LARGE
    elif mcap_cr >= 5000:
        return MarketCapCategory.MID
    return MarketCapCategory.SMALL


def _upsert_stock(db: Session, data: FinancialData) -> Stock:
    """Insert or update stock master record."""
    stock = db.query(Stock).filter(Stock.symbol == data.symbol).first()
    if stock is None:
        stock = Stock(
            symbol=data.symbol,
            isin=data.isin,
            name=data.name,
            exchange=Exchange(data.exchange) if data.exchange in ("NSE", "BSE") else Exchange.NSE,
            sector=data.sector,
            market_cap_category=_classify_market_cap(data.market_cap_cr),
            is_active=True,
        )
        db.add(stock)
        db.flush()
    else:
        stock.sector = data.sector
        stock.market_cap_category = _classify_market_cap(data.market_cap_cr)
        stock.is_active = True
    return stock


async def run_screener(
    adapter: DataSourceAdapter,
    db: Session,
    run_date: date | None = None,
    models: list[ModelType] | None = None,
) -> dict:
    """Run screener models against the full stock universe.

    Args:
        adapter: Data source to fetch financial data from.
        db: Database session.
        run_date: Date for this screener run (defaults to today).
        models: Which models to run (defaults to all 3).

    Returns:
        Summary dict with counts per model.
    """
    if run_date is None:
        run_date = date.today()
    if models is None:
        models = list(MODEL_MAP.keys())

    stocks_data = await adapter.fetch_all_stocks()
    logger.info(f"Fetched {len(stocks_data)} stocks from data source")

    summary = {}

    for model_type in models:
        model = MODEL_MAP[model_type]
        qualified_count = 0
        skipped_count = 0

        for data in stocks_data:
            try:
                stock = _upsert_stock(db, data)
                qualified, score, criteria = model.evaluate(data)

                result = ScreenerResult(
                    stock_id=stock.id,
                    model_type=model_type,
                    score=score,
                    qualified=qualified,
                    criteria_json={c.name: {"passed": c.passed, "value": c.value, "threshold": c.threshold} for c in criteria},
                    run_date=run_date,
                )
                db.add(result)

                if qualified:
                    qualified_count += 1
            except Exception as e:
                logger.warning(f"Skipping {data.symbol}: {e}")
                skipped_count += 1

        db.commit()
        summary[model_type.value] = {"qualified": qualified_count, "total": len(stocks_data), "skipped": skipped_count}
        logger.info(f"Model {model_type.value}: {qualified_count}/{len(stocks_data)} qualified ({skipped_count} skipped)")

    return summary
