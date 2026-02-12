"""BSE Corporate Announcements URL scraper.

Discovers document URLs from BSE's corporate announcements API.
URL discovery is lightweight (JSON parsing) — no PDF downloads here.
"""

import logging
from datetime import date, timedelta

import httpx

logger = logging.getLogger(__name__)

BSE_API_BASE = "https://api.bseindia.com/BseIndiaAPI/api"
BSE_ANNOUNCEMENTS_URL = f"{BSE_API_BASE}/AnnGetData/w"


# Mapping BSE announcement categories to our document types
CATEGORY_MAP = {
    "Result": "quarterly_results",
    "Annual Report": "annual_report",
    "Investor Presentation": "investor_presentation",
    "Press Release": "quarterly_results",  # Press releases often contain quarterly data
}


async def discover_document_urls(
    scrip_code: str,
    from_date: date | None = None,
    to_date: date | None = None,
) -> list[dict]:
    """Discover document URLs for a stock from BSE corporate announcements.

    Args:
        scrip_code: BSE scrip code for the company.
        from_date: Start date for announcements search.
        to_date: End date for announcements search.

    Returns:
        List of dicts with: doc_url, doc_type, period_label, filing_date
    """
    if to_date is None:
        to_date = date.today()
    if from_date is None:
        from_date = to_date - timedelta(days=365)

    params = {
        "strCat": "-1",  # All categories
        "strPrevDate": from_date.strftime("%Y%m%d"),
        "strScrip": scrip_code,
        "strSearch": "P",
        "strToDate": to_date.strftime("%Y%m%d"),
        "strType": "C",
    }

    documents = []

    try:
        async with httpx.AsyncClient(timeout=30, headers={"User-Agent": "MOSI/1.0"}) as client:
            response = await client.get(BSE_ANNOUNCEMENTS_URL, params=params)
            response.raise_for_status()
            data = response.json()

            if not isinstance(data, dict) or "Table" not in data:
                logger.warning(f"Unexpected BSE response format for scrip {scrip_code}")
                return []

            for item in data.get("Table", []):
                category = item.get("CATEGORYNAME", "")
                attachment_url = item.get("ATTACHMENTNAME", "")

                if not attachment_url or not attachment_url.endswith(".pdf"):
                    continue

                doc_type = None
                for key, dtype in CATEGORY_MAP.items():
                    if key.lower() in category.lower():
                        doc_type = dtype
                        break

                if doc_type is None:
                    continue

                filing_date_str = item.get("NEWS_DT", "")
                period_label = _extract_period(item.get("HEADLINE", ""), filing_date_str)

                documents.append({
                    "doc_url": attachment_url,
                    "doc_type": doc_type,
                    "period_label": period_label,
                    "filing_date": filing_date_str,
                    "headline": item.get("HEADLINE", ""),
                })

    except httpx.HTTPStatusError as e:
        logger.error(f"BSE API error for scrip {scrip_code}: {e.response.status_code}")
    except httpx.RequestError as e:
        logger.error(f"BSE API request failed for scrip {scrip_code}: {e}")

    logger.info(f"Discovered {len(documents)} documents for scrip {scrip_code}")
    return documents


def _extract_period(headline: str, filing_date_str: str) -> str:
    """Extract period label from announcement headline or filing date."""
    headline_lower = headline.lower()
    for quarter in ["q1", "q2", "q3", "q4"]:
        if quarter in headline_lower:
            # Try to find FY reference
            for fy_marker in ["fy", "20"]:
                idx = headline_lower.find(fy_marker)
                if idx >= 0:
                    return headline[idx - 1 : idx + 4].strip().upper()
            return quarter.upper()

    # Fallback: use filing date
    if filing_date_str:
        try:
            parts = filing_date_str.split("-")
            if len(parts) >= 2:
                return f"{parts[1]}-{parts[0]}"
        except (IndexError, ValueError):
            pass

    return "unknown"


async def discover_for_stocks(scrip_codes: list[str]) -> dict[str, list[dict]]:
    """Discover documents for a list of stocks. Returns {scrip_code: [documents]}."""
    results = {}
    for code in scrip_codes:
        results[code] = await discover_document_urls(code)
    return results
