"""Behavioral pattern detection and Value Discipline Score.

Monthly batch analysis of trade journal entries to detect common
behavioral patterns: selling winners too early, averaging down losers,
ignoring exit rules, FOMO buying, overtrading.
"""

import logging
from collections import defaultdict
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models.journal import TradeJournal, TradeType, BehavioralAnalysis
from app.models.readiness import ReadinessLevel

logger = logging.getLogger(__name__)

# Pattern detection thresholds
EARLY_EXIT_DAYS = 5        # Selling within N trading days of profitable entry
EARLY_EXIT_PROFIT_PCT = 5  # Minimum profit % to count as "winner sold too early"
FOMO_PREMIUM_PCT = 5       # Buying above recommended range threshold
OVERTRADE_SPIKE_RATIO = 2  # Trade frequency spike vs 3-month baseline


def detect_early_exit(trades: list[dict]) -> list[dict]:
    """Detect selling winners too early — exit within N days of profitable entry.

    A "winner sold too early" is defined as: sell within EARLY_EXIT_DAYS trading
    days of a buy, where the sell price is >= EARLY_EXIT_PROFIT_PCT above buy price.
    """
    patterns = []
    buys_by_stock: dict[int, list[dict]] = defaultdict(list)

    for t in trades:
        if t["trade_type"] == "buy":
            buys_by_stock[t["stock_id"]].append(t)
        elif t["trade_type"] == "sell":
            stock_buys = buys_by_stock.get(t["stock_id"], [])
            for buy in stock_buys:
                days_held = (t["trade_date"] - buy["trade_date"]).days
                profit_pct = ((t["price"] - buy["price"]) / buy["price"]) * 100

                if days_held <= EARLY_EXIT_DAYS and profit_pct >= EARLY_EXIT_PROFIT_PCT:
                    patterns.append({
                        "pattern": "early_exit",
                        "stock_id": t["stock_id"],
                        "symbol": t.get("symbol", ""),
                        "buy_date": buy["trade_date"].isoformat(),
                        "sell_date": t["trade_date"].isoformat(),
                        "days_held": days_held,
                        "profit_pct": round(profit_pct, 1),
                        "detail": f"Sold {t.get('symbol', '')} after {days_held} days with {profit_pct:.1f}% gain",
                    })
    return patterns


def detect_averaging_down(trades: list[dict]) -> list[dict]:
    """Detect averaging down losers — adding to positions below entry price."""
    patterns = []
    entry_prices: dict[int, float] = {}

    for t in trades:
        if t["trade_type"] == "buy" and t["stock_id"] not in entry_prices:
            entry_prices[t["stock_id"]] = t["price"]
        elif t["trade_type"] == "add":
            entry_price = entry_prices.get(t["stock_id"])
            if entry_price and t["price"] < entry_price:
                loss_pct = ((entry_price - t["price"]) / entry_price) * 100
                patterns.append({
                    "pattern": "averaging_down",
                    "stock_id": t["stock_id"],
                    "symbol": t.get("symbol", ""),
                    "entry_price": entry_price,
                    "addition_price": t["price"],
                    "loss_pct": round(loss_pct, 1),
                    "detail": f"Added to {t.get('symbol', '')} at {t['price']} while entry was {entry_price} ({loss_pct:.1f}% below)",
                })
    return patterns


def detect_ignored_exit_rules(trades: list[dict]) -> list[dict]:
    """Detect ignoring exit rules — holding past exit signal trigger.

    Checks if the MOSI context at trade time shows an exit_alert status
    but the user didn't sell.
    """
    patterns = []
    stocks_with_exit_alert: set[int] = set()

    for t in trades:
        mosi_ctx = t.get("mosi_context", {})
        readiness = mosi_ctx.get("readiness", {})
        if readiness.get("status") == ReadinessLevel.EXIT_ALERT.value:
            stocks_with_exit_alert.add(t["stock_id"])

    # Check if any exit-alerted stocks were NOT sold in this period
    sold_stocks = {t["stock_id"] for t in trades if t["trade_type"] == "sell"}
    for stock_id in stocks_with_exit_alert - sold_stocks:
        patterns.append({
            "pattern": "ignored_exit",
            "stock_id": stock_id,
            "detail": f"Stock {stock_id} had exit alert but was not sold in the analysis period",
        })
    return patterns


def detect_fomo_buying(trades: list[dict]) -> list[dict]:
    """Detect FOMO buying — entering above recommended entry range.

    A FOMO buy is when the readiness status was NOT 'ready_now' at entry time.
    """
    patterns = []
    for t in trades:
        if t["trade_type"] != "buy":
            continue
        mosi_ctx = t.get("mosi_context", {})
        readiness = mosi_ctx.get("readiness", {})
        status = readiness.get("status", "")
        if status and status != ReadinessLevel.READY_NOW.value:
            patterns.append({
                "pattern": "fomo_buy",
                "stock_id": t["stock_id"],
                "symbol": t.get("symbol", ""),
                "readiness_status": status,
                "detail": f"Bought {t.get('symbol', '')} when readiness was '{status}' (not Ready Now)",
            })
    return patterns


def detect_overtrading(trades: list[dict], baseline_monthly_count: float) -> list[dict]:
    """Detect overtrading — trade frequency spikes vs baseline."""
    if baseline_monthly_count <= 0:
        return []

    current_count = len(trades)
    ratio = current_count / baseline_monthly_count

    if ratio >= OVERTRADE_SPIKE_RATIO:
        return [{
            "pattern": "overtrading",
            "current_count": current_count,
            "baseline_monthly": round(baseline_monthly_count, 1),
            "ratio": round(ratio, 1),
            "detail": f"{current_count} trades this month vs {baseline_monthly_count:.0f} avg ({ratio:.1f}x spike)",
        }]
    return []


def compute_discipline_score(trades: list[dict]) -> float:
    """Compute Value Discipline Score — % of buy trades with Ready Now status at entry.

    Returns 0-100 percentage.
    """
    buy_trades = [t for t in trades if t["trade_type"] == "buy"]
    if not buy_trades:
        return 0.0

    aligned_count = 0
    for t in buy_trades:
        mosi_ctx = t.get("mosi_context", {})
        readiness = mosi_ctx.get("readiness", {})
        if readiness.get("status") == ReadinessLevel.READY_NOW.value:
            aligned_count += 1

    return round((aligned_count / len(buy_trades)) * 100, 1)


def run_monthly_analysis(
    db: Session,
    user_id: str,
    month_label: str,
    analysis_window_days: int = 90,
) -> BehavioralAnalysis:
    """Run monthly behavioral analysis for a user.

    Analyzes trades over the trailing analysis_window_days to detect patterns,
    compute discipline score, and generate insights.
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=analysis_window_days)

    # Fetch trades in window
    journal_entries = (
        db.query(TradeJournal)
        .filter(
            TradeJournal.user_id == user_id,
            TradeJournal.trade_date >= start_date,
            TradeJournal.trade_date <= end_date,
        )
        .order_by(TradeJournal.trade_date.asc())
        .all()
    )

    trades = [
        {
            "stock_id": e.stock_id,
            "symbol": e.stock.symbol if e.stock else "",
            "trade_type": e.trade_type.value,
            "quantity": e.quantity,
            "price": e.price,
            "trade_date": e.trade_date,
            "mosi_context": e.mosi_context_json or {},
        }
        for e in journal_entries
    ]

    # Baseline: monthly trade count over 3 months
    baseline_entries = (
        db.query(TradeJournal)
        .filter(
            TradeJournal.user_id == user_id,
            TradeJournal.trade_date >= end_date - timedelta(days=analysis_window_days),
        )
        .count()
    )
    baseline_monthly = baseline_entries / max(1, analysis_window_days / 30)

    # Current month trades only for overtrading check
    current_month_trades = [t for t in trades if (end_date - t["trade_date"]).days <= 30]

    # Detect patterns
    all_patterns = []
    all_patterns.extend(detect_early_exit(trades))
    all_patterns.extend(detect_averaging_down(trades))
    all_patterns.extend(detect_ignored_exit_rules(trades))
    all_patterns.extend(detect_fomo_buying(trades))
    all_patterns.extend(detect_overtrading(current_month_trades, baseline_monthly))

    discipline_score = compute_discipline_score(trades)

    # Generate insights
    insights = _generate_insights(trades, all_patterns, discipline_score)

    # Persist
    existing = (
        db.query(BehavioralAnalysis)
        .filter(BehavioralAnalysis.user_id == user_id, BehavioralAnalysis.month_label == month_label)
        .first()
    )

    patterns_json = {
        "patterns": all_patterns,
        "summary": {p["pattern"]: sum(1 for x in all_patterns if x["pattern"] == p["pattern"]) for p in all_patterns},
        "trade_count": len(trades),
        "window_days": analysis_window_days,
    }

    if existing:
        existing.discipline_score = discipline_score
        existing.patterns_json = patterns_json
        existing.insights_text = insights
    else:
        existing = BehavioralAnalysis(
            user_id=user_id,
            month_label=month_label,
            discipline_score=discipline_score,
            patterns_json=patterns_json,
            insights_text=insights,
        )
        db.add(existing)

    db.commit()
    logger.info(f"Behavioral analysis for {user_id} ({month_label}): discipline={discipline_score}, patterns={len(all_patterns)}")
    return existing


def _generate_insights(trades: list[dict], patterns: list[dict], discipline_score: float) -> str:
    """Generate actionable text insights from detected patterns."""
    lines = []
    buy_trades = [t for t in trades if t["trade_type"] == "buy"]

    lines.append(f"Value Discipline Score: {discipline_score}%")
    lines.append(f"Total trades analyzed: {len(trades)} ({len(buy_trades)} buys)")

    if not patterns:
        lines.append("No behavioral patterns detected — well-disciplined trading!")
        return "\n".join(lines)

    pattern_counts = defaultdict(int)
    for p in patterns:
        pattern_counts[p["pattern"]] += 1

    if pattern_counts.get("early_exit", 0) > 0:
        lines.append(f"- Selling winners early: {pattern_counts['early_exit']} instances. Consider holding longer when MOSI Score is high.")
    if pattern_counts.get("averaging_down", 0) > 0:
        lines.append(f"- Averaging down losers: {pattern_counts['averaging_down']} instances. MOSI recommends against adding below entry price.")
    if pattern_counts.get("ignored_exit", 0) > 0:
        lines.append(f"- Ignored exit signals: {pattern_counts['ignored_exit']} instances. Trust the exit rules to protect capital.")
    if pattern_counts.get("fomo_buy", 0) > 0:
        lines.append(f"- FOMO buying: {pattern_counts['fomo_buy']} instances. Wait for Ready Now status before entering.")
    if pattern_counts.get("overtrading", 0) > 0:
        lines.append("- Overtrading detected. Fewer, higher-conviction trades tend to outperform.")

    # Best vs worst trade comparison
    if buy_trades:
        scored = [t for t in buy_trades if t.get("mosi_context", {}).get("readiness", {}).get("mosi_score")]
        if scored:
            scores = [t["mosi_context"]["readiness"]["mosi_score"] for t in scored]
            lines.append(f"- Average MOSI Score at entry: {sum(scores) / len(scores):.1f}")

    return "\n".join(lines)
