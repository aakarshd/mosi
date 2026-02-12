"""Scoring and verdict computation from parsed analysis.

Computes the final Multi-Bagger Score and maps to institutional verdict.
Also computes confidence adjustment based on document availability.
"""

from app.services.analysis.parser import ParsedAnalysis

# Score → Verdict mapping
VERDICT_THRESHOLDS = {
    "Buy": 7.0,   # Score >= 7 → Buy
    "Hold": 4.0,  # Score >= 4 → Hold
    "Avoid": 0.0, # Score < 4 → Avoid
}

# Document type weights for confidence
DOC_WEIGHTS = {
    "annual_report": 0.3,
    "quarterly_results": 0.3,
    "earnings_transcript": 0.25,
    "investor_presentation": 0.15,
}


def compute_multi_bagger_score(analysis: ParsedAnalysis) -> float:
    """Compute weighted Multi-Bagger Score from the 11 analysis points.

    If the LLM already provided a score, we validate it against our computation.
    The final score is the average of all point scores.

    Returns:
        Score in 0-10 range.
    """
    if not analysis.points:
        return analysis.multi_bagger_score  # Fallback to LLM's score

    point_scores = [p.score for p in analysis.points]
    computed = sum(point_scores) / len(point_scores)

    # If LLM score diverges significantly from computed, flag it
    llm_score = analysis.multi_bagger_score
    if abs(computed - llm_score) > 2.0:
        # Use computed score as it's more systematic
        return round(computed, 1)

    # Average of LLM and computed for robustness
    return round((computed + llm_score) / 2, 1)


def compute_verdict(score: float, red_flag_count: int = 0) -> str:
    """Map score to institutional verdict.

    Red flags can downgrade the verdict:
    - 3+ red flags: cap at Hold
    - 5+ red flags: force Avoid
    """
    if red_flag_count >= 5:
        return "Avoid"

    if score >= VERDICT_THRESHOLDS["Buy"]:
        if red_flag_count >= 3:
            return "Hold"
        return "Buy"
    elif score >= VERDICT_THRESHOLDS["Hold"]:
        return "Hold"
    return "Avoid"


def compute_confidence(
    documents_analyzed: list[str],
    expected_doc_types: list[str] | None = None,
) -> tuple[str, float]:
    """Compute confidence level based on document coverage.

    Args:
        documents_analyzed: List of document names/types that were analyzed.
        expected_doc_types: Expected document types (defaults to all 4).

    Returns:
        (confidence_label, confidence_score) where score is 0-1.
    """
    if expected_doc_types is None:
        expected_doc_types = list(DOC_WEIGHTS.keys())

    docs_lower = [d.lower() for d in documents_analyzed]
    score = 0.0

    for doc_type, weight in DOC_WEIGHTS.items():
        if doc_type in expected_doc_types:
            # Check if any analyzed document matches this type
            if any(doc_type.replace("_", " ") in d or doc_type.replace("_", "") in d for d in docs_lower):
                score += weight

    if score >= 0.8:
        return "High", score
    elif score >= 0.5:
        return "Medium", score
    return "Low", score
