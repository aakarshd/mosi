"""SEBI disclaimer middleware — injects regulatory disclaimer into API responses.

Required on every endpoint that returns signals, verdicts, readiness
statuses, or any form of investment recommendation/opinion.
"""

SEBI_DISCLAIMER = (
    "DISCLAIMER: This information is for educational and informational purposes only. "
    "It does not constitute investment advice, a recommendation, or a solicitation to "
    "buy or sell any securities. MOSI is not a SEBI-registered investment advisor. "
    "Past performance is not indicative of future results. Please consult a qualified "
    "financial advisor before making any investment decisions. Investments in the "
    "securities market are subject to market risks. Read all the related documents "
    "carefully before investing."
)

# Endpoints that must include the disclaimer
DISCLAIMER_PATHS = {
    "/api/v1/readiness",
    "/api/v1/analysis",
    "/api/v1/screener",
    "/api/v1/portfolio",
}


def should_include_disclaimer(path: str) -> bool:
    """Check if a response path requires SEBI disclaimer."""
    return any(path.startswith(p) for p in DISCLAIMER_PATHS)


def inject_disclaimer(response_data: dict) -> dict:
    """Add SEBI disclaimer to a response dict."""
    response_data["disclaimer"] = SEBI_DISCLAIMER
    return response_data
