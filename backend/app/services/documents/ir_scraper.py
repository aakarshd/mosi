"""Company Investor Relations page scraper.

Fallback source for document URLs when BSE is rate-limited.
Discovers investor presentation and annual report URLs from company IR pages.
"""

import logging
import re

import httpx

logger = logging.getLogger(__name__)

# Common IR page URL patterns for Indian companies
IR_URL_PATTERNS = [
    "{base_url}/investors",
    "{base_url}/investor-relations",
    "{base_url}/investor",
    "{base_url}/investors/financial-information",
    "{base_url}/investor-relations/annual-reports",
]

PDF_LINK_PATTERN = re.compile(r'href=["\']([^"\']*\.pdf)["\']', re.IGNORECASE)


async def discover_ir_documents(
    company_website: str,
    stock_symbol: str,
) -> list[dict]:
    """Discover document URLs from a company's investor relations page.

    Args:
        company_website: Base URL of the company website (e.g., "https://www.reliance.com").
        stock_symbol: Stock symbol for logging.

    Returns:
        List of dicts with: doc_url, doc_type (best guess), period_label
    """
    documents = []

    async with httpx.AsyncClient(timeout=20, follow_redirects=True, headers={"User-Agent": "MOSI/1.0"}) as client:
        for pattern in IR_URL_PATTERNS:
            url = pattern.format(base_url=company_website.rstrip("/"))
            try:
                response = await client.get(url)
                if response.status_code != 200:
                    continue

                html = response.text
                pdf_urls = PDF_LINK_PATTERN.findall(html)

                for pdf_url in pdf_urls:
                    if not pdf_url.startswith("http"):
                        pdf_url = company_website.rstrip("/") + "/" + pdf_url.lstrip("/")

                    doc_type = _guess_doc_type(pdf_url)
                    if doc_type is None:
                        continue

                    documents.append({
                        "doc_url": pdf_url,
                        "doc_type": doc_type,
                        "period_label": _guess_period(pdf_url),
                        "source": "ir_page",
                    })

                if documents:
                    logger.info(f"Found {len(documents)} docs on IR page for {stock_symbol}: {url}")
                    break  # Found a working IR page, stop trying other patterns

            except httpx.RequestError as e:
                logger.debug(f"IR page not found at {url}: {e}")
                continue

    return documents


def _guess_doc_type(url: str) -> str | None:
    """Guess document type from URL path/filename."""
    url_lower = url.lower()
    if "annual" in url_lower and "report" in url_lower:
        return "annual_report"
    if "investor" in url_lower and "presentation" in url_lower:
        return "investor_presentation"
    if "quarterly" in url_lower or "q1" in url_lower or "q2" in url_lower or "q3" in url_lower or "q4" in url_lower:
        return "quarterly_results"
    if "transcript" in url_lower:
        return "earnings_transcript"
    return None


def _guess_period(url: str) -> str:
    """Try to extract period from URL."""
    fy_match = re.search(r"fy[- ]?(\d{2,4})", url, re.IGNORECASE)
    if fy_match:
        return f"FY{fy_match.group(1)}"
    year_match = re.search(r"20\d{2}", url)
    if year_match:
        return year_match.group(0)
    return "unknown"
