"""Output parser — validates and structures LLM analysis response.

Enforces the 11-point schema, extracts scores, and handles malformed output.
"""

import json
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

EXPECTED_POINTS = 11
VALID_VERDICTS = {"Buy", "Hold", "Avoid"}
VALID_STAGES = {"Early Growth", "Expansion", "Early Maturity", "Mature"}
VALID_CONFIDENCE = {"High", "Medium", "Low"}


@dataclass
class AnalysisPoint:
    point_number: int
    title: str
    finding: str
    classification: str | None
    score: float
    confidence: str
    evidence: list[str]
    red_flags: list[str]


@dataclass
class ParsedAnalysis:
    stock_symbol: str
    stock_name: str
    points: list[AnalysisPoint]
    multi_bagger_score: float
    verdict: str
    verdict_reasoning: str
    key_strengths: list[str]
    key_risks: list[str]
    confidence_level: str
    documents_analyzed: list[str]
    raw_json: dict  # Preserve raw output for debugging
    parse_warnings: list[str]


def parse_llm_output(raw_text: str) -> ParsedAnalysis:
    """Parse LLM output into structured analysis.

    Handles common issues: markdown code fences, extra whitespace, partial JSON.

    Returns:
        ParsedAnalysis with structured data and any parse warnings.
    """
    warnings = []

    # Strip markdown code fences if present
    text = raw_text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:]  # Remove opening ```json
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]  # Remove closing ```
        text = "\n".join(lines)

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM output as JSON: {e}")
        return _empty_analysis(raw_text, [f"JSON parse error: {e}"])

    # Validate and extract fields
    stock_symbol = data.get("stock_symbol", "UNKNOWN")
    stock_name = data.get("stock_name", "Unknown")

    # Parse analysis points
    points = []
    raw_points = data.get("analysis_points", [])

    if len(raw_points) != EXPECTED_POINTS:
        warnings.append(f"Expected {EXPECTED_POINTS} analysis points, got {len(raw_points)}")

    for i, rp in enumerate(raw_points):
        point = AnalysisPoint(
            point_number=rp.get("point_number", i + 1),
            title=rp.get("title", f"Point {i + 1}"),
            finding=rp.get("finding", "No finding provided"),
            classification=rp.get("classification"),
            score=_clamp_score(rp.get("score", 0)),
            confidence=_validate_enum(rp.get("confidence", "Low"), VALID_CONFIDENCE, "Low"),
            evidence=rp.get("evidence", []),
            red_flags=rp.get("red_flags", []),
        )
        points.append(point)

    # Multi-bagger score
    mb_score = _clamp_score(data.get("multi_bagger_score", 0))

    # Verdict
    verdict = _validate_enum(data.get("verdict", "Hold"), VALID_VERDICTS, "Hold")
    if data.get("verdict") and data["verdict"] not in VALID_VERDICTS:
        warnings.append(f"Invalid verdict '{data['verdict']}', defaulted to 'Hold'")

    return ParsedAnalysis(
        stock_symbol=stock_symbol,
        stock_name=stock_name,
        points=points,
        multi_bagger_score=mb_score,
        verdict=verdict,
        verdict_reasoning=data.get("verdict_reasoning", ""),
        key_strengths=data.get("key_strengths", []),
        key_risks=data.get("key_risks", []),
        confidence_level=_validate_enum(data.get("confidence_level", "Low"), VALID_CONFIDENCE, "Low"),
        documents_analyzed=data.get("documents_analyzed", []),
        raw_json=data,
        parse_warnings=warnings,
    )


def _clamp_score(value) -> float:
    """Clamp score to 0-10 range."""
    try:
        v = float(value)
        return max(0.0, min(10.0, v))
    except (TypeError, ValueError):
        return 0.0


def _validate_enum(value: str, valid: set, default: str) -> str:
    """Return value if in valid set, otherwise default."""
    return value if value in valid else default


def _empty_analysis(raw_text: str, warnings: list[str]) -> ParsedAnalysis:
    """Return an empty analysis for unparseable output."""
    return ParsedAnalysis(
        stock_symbol="UNKNOWN",
        stock_name="Unknown",
        points=[],
        multi_bagger_score=0,
        verdict="Hold",
        verdict_reasoning="AI analysis could not be parsed",
        key_strengths=[],
        key_risks=["Analysis output was unparseable"],
        confidence_level="Low",
        documents_analyzed=[],
        raw_json={"raw_text": raw_text[:2000]},
        parse_warnings=warnings,
    )
