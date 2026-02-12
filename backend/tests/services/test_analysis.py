"""Tests for Layer 2 AI analysis — parser, scoring, prompt builder."""

import json

from app.services.analysis.parser import parse_llm_output, ParsedAnalysis
from app.services.analysis.scoring import compute_multi_bagger_score, compute_verdict, compute_confidence
from app.services.analysis.prompt import build_prompt


# --- Sample LLM output for testing ---

SAMPLE_LLM_OUTPUT = json.dumps({
    "stock_symbol": "TESTCO",
    "stock_name": "Test Company Ltd",
    "analysis_points": [
        {
            "point_number": i,
            "title": f"Point {i}",
            "finding": f"Finding for point {i}",
            "classification": "Expansion" if i == 1 else None,
            "score": 7.5 if i <= 6 else 5.0,
            "confidence": "High" if i <= 8 else "Medium",
            "evidence": [f"Annual Report, page {i * 10}"],
            "red_flags": ["Minor concern"] if i == 10 else [],
        }
        for i in range(1, 12)
    ],
    "multi_bagger_score": 6.8,
    "verdict": "Buy",
    "verdict_reasoning": "Strong growth with PE expansion signals",
    "key_strengths": ["Revenue acceleration", "Margin expansion", "Low base"],
    "key_risks": ["High valuation", "Execution risk"],
    "confidence_level": "High",
    "documents_analyzed": ["annual_report_2025.pdf", "quarterly_results_q3.pdf"],
})


# --- Parser Tests ---

class TestParser:
    def test_valid_json_parses(self):
        result = parse_llm_output(SAMPLE_LLM_OUTPUT)
        assert result.stock_symbol == "TESTCO"
        assert result.stock_name == "Test Company Ltd"
        assert len(result.points) == 11
        assert result.multi_bagger_score == 6.8
        assert result.verdict == "Buy"
        assert len(result.parse_warnings) == 0

    def test_markdown_fences_stripped(self):
        wrapped = f"```json\n{SAMPLE_LLM_OUTPUT}\n```"
        result = parse_llm_output(wrapped)
        assert result.stock_symbol == "TESTCO"
        assert len(result.points) == 11

    def test_invalid_json_returns_empty(self):
        result = parse_llm_output("This is not JSON at all")
        assert result.stock_symbol == "UNKNOWN"
        assert len(result.points) == 0
        assert len(result.parse_warnings) > 0

    def test_wrong_point_count_warns(self):
        data = json.loads(SAMPLE_LLM_OUTPUT)
        data["analysis_points"] = data["analysis_points"][:5]  # Only 5 points
        result = parse_llm_output(json.dumps(data))
        assert len(result.points) == 5
        assert any("Expected 11" in w for w in result.parse_warnings)

    def test_invalid_verdict_defaults_to_hold(self):
        data = json.loads(SAMPLE_LLM_OUTPUT)
        data["verdict"] = "Strong Buy"  # Invalid
        result = parse_llm_output(json.dumps(data))
        assert result.verdict == "Hold"
        assert any("Invalid verdict" in w for w in result.parse_warnings)

    def test_score_clamped_to_range(self):
        data = json.loads(SAMPLE_LLM_OUTPUT)
        data["analysis_points"][0]["score"] = 15  # Over 10
        data["analysis_points"][1]["score"] = -5  # Under 0
        result = parse_llm_output(json.dumps(data))
        assert result.points[0].score == 10.0
        assert result.points[1].score == 0.0

    def test_evidence_and_red_flags_preserved(self):
        result = parse_llm_output(SAMPLE_LLM_OUTPUT)
        assert result.points[0].evidence == ["Annual Report, page 10"]
        assert result.points[9].red_flags == ["Minor concern"]
        assert result.points[0].red_flags == []


# --- Scoring Tests ---

class TestScoring:
    def test_score_computation(self):
        result = parse_llm_output(SAMPLE_LLM_OUTPUT)
        score = compute_multi_bagger_score(result)
        assert 0 <= score <= 10

    def test_verdict_buy_high_score(self):
        assert compute_verdict(8.0) == "Buy"

    def test_verdict_hold_mid_score(self):
        assert compute_verdict(5.0) == "Hold"

    def test_verdict_avoid_low_score(self):
        assert compute_verdict(2.0) == "Avoid"

    def test_red_flags_downgrade_buy_to_hold(self):
        assert compute_verdict(8.0, red_flag_count=3) == "Hold"

    def test_many_red_flags_force_avoid(self):
        assert compute_verdict(9.0, red_flag_count=5) == "Avoid"

    def test_confidence_high_with_all_docs(self):
        docs = ["annual_report.pdf", "quarterly_results.pdf", "earnings_transcript.pdf", "investor_presentation.pdf"]
        label, score = compute_confidence(docs)
        assert label == "High"
        assert score >= 0.8

    def test_confidence_low_with_no_docs(self):
        label, score = compute_confidence([])
        assert label == "Low"
        assert score == 0.0

    def test_confidence_medium_with_partial_docs(self):
        docs = ["annual_report.pdf", "quarterly_results.pdf"]
        label, score = compute_confidence(docs)
        assert label in ("Medium", "High")
        assert score >= 0.5


# --- Prompt Builder Tests ---

class TestPromptBuilder:
    def test_builds_prompts(self):
        system, user = build_prompt("Reliance Industries", "RELIANCE", ["AR_2025.pdf", "Q3_Results.pdf"])
        assert "equity research analyst" in system.lower()
        assert "Reliance Industries" in user
        assert "RELIANCE" in user
        assert "AR_2025.pdf" in user
        assert "Q3_Results.pdf" in user

    def test_all_11_points_in_prompt(self):
        _, user = build_prompt("Test", "TEST", [])
        for i in range(1, 12):
            assert f"### {i}." in user

    def test_json_schema_in_prompt(self):
        _, user = build_prompt("Test", "TEST", [])
        assert "multi_bagger_score" in user
        assert "verdict" in user
        assert "analysis_points" in user
