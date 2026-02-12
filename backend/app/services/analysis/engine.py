"""Layer 2 AI Analysis Engine — orchestrates the full analysis pipeline.

Pipeline per stock:
1. Fetch documents from store (Task #4)
2. Build SME prompt with stock context
3. Send to LLM (multimodal — PDFs direct, no OCR)
4. Parse structured output
5. Compute/validate scores
6. Cache results in database
"""

import logging
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.analysis import AnalysisCache, Verdict
from app.models.stock import Stock
from app.services.analysis.adapters.base import LLMAdapter
from app.services.analysis.prompt import build_prompt
from app.services.analysis.parser import parse_llm_output
from app.services.analysis.scoring import compute_multi_bagger_score, compute_verdict, compute_confidence
from app.services.documents.store import DocumentStore
from app.utils.datetime_helpers import format_quarter, utc_now

logger = logging.getLogger(__name__)

MAX_RETRIES = 1


async def analyze_stock(
    stock: Stock,
    llm: LLMAdapter,
    doc_store: DocumentStore,
    db: Session,
) -> AnalysisCache | None:
    """Run full 11-point analysis for a single stock.

    Returns:
        AnalysisCache record, or None if analysis failed.
    """
    # 1. Fetch documents
    doc_paths = doc_store.get_latest_documents(stock.isin)
    if not doc_paths:
        logger.warning(f"No documents available for {stock.symbol} ({stock.isin})")
        return None

    doc_names = [p.name for p in doc_paths]
    logger.info(f"Analyzing {stock.symbol} with {len(doc_paths)} documents: {doc_names}")

    # 2. Build prompt
    system_prompt, user_prompt = build_prompt(stock.name, stock.symbol, doc_names)

    # 3. Call LLM (with retry)
    llm_response = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            llm_response = await llm.analyze_documents(system_prompt, user_prompt, doc_paths)
            break
        except Exception as e:
            logger.warning(f"LLM call failed for {stock.symbol} (attempt {attempt + 1}): {e}")
            if attempt == MAX_RETRIES:
                logger.error(f"All LLM retries exhausted for {stock.symbol}")
                return None

    if llm_response is None:
        return None

    # 4. Parse output
    parsed = parse_llm_output(llm_response.content)
    if parsed.parse_warnings:
        logger.warning(f"Parse warnings for {stock.symbol}: {parsed.parse_warnings}")

    # 5. Compute scores
    score = compute_multi_bagger_score(parsed)
    total_red_flags = sum(len(p.red_flags) for p in parsed.points)
    verdict = compute_verdict(score, total_red_flags)
    confidence_label, confidence_score = compute_confidence(parsed.documents_analyzed)

    # 6. Map verdict string to enum
    verdict_map = {"Buy": Verdict.BUY, "Hold": Verdict.HOLD, "Avoid": Verdict.AVOID}
    verdict_enum = verdict_map.get(verdict, Verdict.HOLD)

    # 7. Build analysis JSON
    analysis_json = {
        "points": [
            {
                "point_number": p.point_number,
                "title": p.title,
                "finding": p.finding,
                "classification": p.classification,
                "score": p.score,
                "confidence": p.confidence,
                "evidence": p.evidence,
                "red_flags": p.red_flags,
            }
            for p in parsed.points
        ],
        "key_strengths": parsed.key_strengths,
        "key_risks": parsed.key_risks,
        "verdict_reasoning": parsed.verdict_reasoning,
        "confidence_level": confidence_label,
        "confidence_score": confidence_score,
        "llm_model": llm_response.model,
        "llm_cost_usd": llm_response.cost_usd,
        "llm_tokens": {"input": llm_response.input_tokens, "output": llm_response.output_tokens},
        "raw_output": llm_response.content[:5000],  # Truncate raw for debugging
    }

    quarter_label = format_quarter(utc_now())

    # 8. Upsert into database
    existing = db.query(AnalysisCache).filter(
        AnalysisCache.stock_id == stock.id,
        AnalysisCache.quarter_label == quarter_label,
    ).first()

    if existing:
        existing.analysis_json = analysis_json
        existing.multi_bagger_score = score
        existing.verdict = verdict_enum
        existing.summary_text = parsed.verdict_reasoning
        existing.analyzed_at = datetime.now(timezone.utc)
        existing.documents_used = [str(p) for p in doc_paths]
        cache = existing
    else:
        cache = AnalysisCache(
            stock_id=stock.id,
            analysis_json=analysis_json,
            multi_bagger_score=score,
            verdict=verdict_enum,
            summary_text=parsed.verdict_reasoning,
            analyzed_at=datetime.now(timezone.utc),
            documents_used=[str(p) for p in doc_paths],
            quarter_label=quarter_label,
        )
        db.add(cache)

    db.commit()
    logger.info(f"Analysis complete for {stock.symbol}: score={score}, verdict={verdict}, confidence={confidence_label}")
    return cache
