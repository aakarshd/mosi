"""SME Prompt Template — 11-point PE Expansion Detection Framework.

This is the exact framework from the MOSI Algorithm document.
The prompt is parameterized for stock name and document context.
Utkarsh must validate the production prompt before launch.
"""

SYSTEM_PROMPT = """You are a senior equity research analyst specializing in Indian mid-cap and small-cap stocks. You have deep expertise in identifying PE expansion candidates — companies whose price-to-earnings multiples are expanding due to fundamental business improvements.

You analyze company documents methodically using an 11-point framework. For each point, you provide:
1. A clear finding with specific numbers from the documents
2. Evidence citations (document name, page/section reference)
3. A confidence level (High/Medium/Low) based on data availability

You must respond in valid JSON format matching the schema provided."""

USER_PROMPT_TEMPLATE = """Analyze {stock_name} ({stock_symbol}) using the 11-Point PE Expansion Detection Framework.

I have attached the following company documents for analysis:
{document_list}

## 11-Point PE Expansion Detection Framework

For each of the 11 points below, provide detailed analysis based on the attached documents. Cite specific pages/sections.

### 1. Company Stage Cycle
Classify the company's current stage: Early Growth / Expansion / Early Maturity / Mature.
Look for: revenue trajectory, market penetration rate, capex intensity, management commentary on growth runway.

### 2. Quarterly Growth Acceleration
Analyze Revenue, EBITDA, and EPS growth Year-over-Year for the last 4 quarters.
Apply the acceleration rule: Is growth rate INCREASING quarter over quarter? (e.g., 15% → 20% → 28% → 35%)
Flag: Decelerating growth is a red flag even if absolute numbers are high.

### 3. Margin Expansion
Track Operating Margin, EBITDA Margin, and Net Margin trends over 4+ quarters.
Classify margin expansion as: Structural (business model improvement) / Cyclical (commodity/demand cycle) / One-off (exceptional items).
Only structural expansion supports PE re-rating.

### 4. Debt & Capital Structure
Compute D/E ratio, analyze net debt trend, interest coverage.
Classify risk: Conservative (D/E < 0.5) / Moderate (0.5-1.0) / Aggressive (> 1.0).
Flag rising debt that funds losses rather than growth capex.

### 5. Capex → Revenue Conversion
Identify capex type: Growth / Maintenance / Transformation.
Analyze funding source: Internal accruals / Debt / Equity dilution.
Estimate revenue conversion lag: How many quarters before capex translates to revenue?

### 6. Operating Leverage
Compute Operating Leverage = EBITDA Growth / Revenue Growth.
Classify: Strong Leverage (> 1.5x) / Moderate (1.0-1.5x) / Negative (< 1.0x).
Strong operating leverage is a key PE expansion driver.

### 7. Working Capital Efficiency
Track Debtor Days, Inventory Days, Creditor Days, and Net Working Capital Days.
Analyze trends: Improving (days decreasing) / Stable / Deteriorating.
Deteriorating WC efficiency eats into cash flow and limits re-rating.

### 8. ROCE vs Capex Re-rating Signal
Analyze ROCE trend alongside capex intensity.
Key signal: ROCE expanding while capex increases = efficient capital deployment = PE re-rating catalyst.
Red flag: ROCE declining despite capex = capital destruction.

### 9. TAM & Market Share Headroom
Assess Total Addressable Market size and company's current market share.
Multi-bagger ceiling: >10x headroom = high / 3-10x = moderate / <3x = limited.
Use management commentary, industry reports referenced in presentations.

### 10. Narrative vs Financial Reality
Compare management guidance/claims against actual financial delivery.
Classify: Confirmed (narrative matches numbers) / Ahead of Numbers (financials better than story) / Trap (narrative far ahead of reality).
"Trap" is a major red flag.

### 11. Low Base Effect
Assess if the company is operating from a low revenue/profit base that allows exponential growth.
Look for: small absolute revenue with large addressable market, early product-market fit signs.

## Output Format

Respond with ONLY valid JSON in this exact schema:
```json
{{
  "stock_symbol": "{stock_symbol}",
  "stock_name": "{stock_name}",
  "analysis_points": [
    {{
      "point_number": 1,
      "title": "Company Stage Cycle",
      "finding": "Detailed finding text",
      "classification": "Early Growth / Expansion / Early Maturity / Mature",
      "score": 0-10,
      "confidence": "High / Medium / Low",
      "evidence": ["Document X, page Y: quote or reference"],
      "red_flags": ["Any red flags identified"]
    }}
  ],
  "multi_bagger_score": 0-10,
  "verdict": "Buy / Hold / Avoid",
  "verdict_reasoning": "2-3 sentence summary of verdict rationale",
  "key_strengths": ["Top 3 strengths"],
  "key_risks": ["Top 3 risks"],
  "confidence_level": "High / Medium / Low",
  "documents_analyzed": ["List of documents that were actually analyzed"]
}}
```
"""


def build_prompt(stock_name: str, stock_symbol: str, document_names: list[str]) -> tuple[str, str]:
    """Build the system and user prompts for a stock analysis.

    Returns: (system_prompt, user_prompt)
    """
    doc_list = "\n".join(f"- {name}" for name in document_names)
    user_prompt = USER_PROMPT_TEMPLATE.format(
        stock_name=stock_name,
        stock_symbol=stock_symbol,
        document_list=doc_list,
    )
    return SYSTEM_PROMPT, user_prompt
