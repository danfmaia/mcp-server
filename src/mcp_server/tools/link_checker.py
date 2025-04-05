# src/mcp_server/logic.py

import asyncio
import logging
import re

# Import requests later when implementing link checking
# import requests
from typing import Any

import aiohttp  # Import async HTTP client
from aiohttp import ClientTimeout  # Import ClientTimeout
from markdown_it import MarkdownIt

logger = logging.getLogger(__name__)

# --- Link Extraction Logic (Using markdown-it-py) ---


def _extract_links(content: str) -> list[str]:
    """
    Extracts HTTP and HTTPS links from a string containing Markdown using markdown-it-py.
    Handles plain URLs and URLs within Markdown [text](url) syntax.
    """
    if not content:
        return []

    links: set[str] = set()
    # Enable linkify to auto-detect bare URLs
    md = MarkdownIt(options_update={'linkify': True})
    try:
        # Parse the block tokens first
        block_tokens = md.parse(content)
    except Exception as e:
        logger.error(f"Markdown parsing failed: {e}", exc_info=True)
        return []

    # Iterate through block tokens, then process inline content
    for token in block_tokens:
        if token.type == 'inline' and token.children:
            # Process inline tokens within the block
            for child in token.children:
                if child.type == 'link_open':
                    href = child.attrGet('href')
                    # logger.debug(f"      Found link_open child, href='{href}'") # Removed debug
                    # Ensure href is a string before calling startswith
                    if isinstance(href, str) and (href.startswith("http://") or href.startswith("https://")):
                        links.add(href)
                elif child.type == 'text' and child.content:
                    potential_links = re.findall(
                        r"https?://[^\s<>\"\']+", child.content)
                    for link in potential_links:
                        cleaned_link = link.rstrip('.,;!?)')
                        if cleaned_link:
                            links.add(cleaned_link)

    return sorted(list(links))


# --- Link Status Checking Logic ---

MAX_REDIRECTS = 5  # Prevent infinite redirect loops
USER_AGENT = "CareerAgentMCP/0.1 (LinkChecker)"  # Basic user agent
TIMEOUT_SECONDS = 10  # Request timeout
TIMEOUT = ClientTimeout(total=TIMEOUT_SECONDS)


async def _check_link_status(
    session: aiohttp.ClientSession,
    url: str,
    *,  # Force subsequent arguments to be keyword-only
    _redirect_depth: int = 0  # Internal recursion counter
) -> tuple[str, str | None]:
    """
    Checks the status of a single URL using an existing aiohttp session.
    Handles redirects manually up to MAX_REDIRECTS.
    Returns tuple: (status_string, error_string_or_None)
    Status can be "OK", "BROKEN", "ERROR".
    """
    if _redirect_depth > MAX_REDIRECTS:
        logger.warning(f"Link ERROR (Too many redirects): {url}")
        return ("ERROR", "Too many redirects")

    try:
        async with session.head(
            url,
            timeout=TIMEOUT,
            headers={"User-Agent": USER_AGENT},
            allow_redirects=False  # Handle redirects manually
        ) as response:
            if 200 <= response.status < 300:
                logger.debug(f"Link OK ({response.status}): {url}")
                return ("OK", None)
            elif 300 <= response.status < 400:
                location = response.headers.get('Location')
                if not location:
                    reason = f"{response.status} {response.reason} (Redirect without Location)"
                    logger.warning(f"Link BROKEN ({reason}): {url}")
                    return ("BROKEN", reason)

                # Resolve relative redirects (basic handling)
                # TODO: More robust relative URL resolution if needed
                redirect_url = aiohttp.helpers.URL(location, encoded=True)
                if not redirect_url.is_absolute():
                    base_url = response.url  # Use the URL we just queried as base
                    redirect_url = base_url.join(redirect_url)

                logger.debug(
                    f"Redirect ({response.status}) from {url} to {redirect_url}")
                # Recursively check the new location
                return await _check_link_status(
                    session,
                    str(redirect_url),  # Convert back to string
                    _redirect_depth=_redirect_depth + 1
                )
            else:
                reason = f"{response.status} {response.reason}"
                logger.warning(f"Link BROKEN ({reason}): {url}")
                return ("BROKEN", reason)

    except asyncio.TimeoutError:
        logger.warning(f"Link ERROR (Timeout): {url}")
        return ("ERROR", "Timeout")
    except aiohttp.ClientError as e:
        err_type = type(e).__name__
        # Log specific connection errors differently? Maybe later.
        logger.warning(f"Link ERROR ({err_type}): {url}")
        return ("ERROR", err_type)
    except Exception as e:
        err_type = type(e).__name__
        # Log full traceback for unexpected
        logger.exception(f"Unexpected error checking {url}: {e}")
        return ("ERROR", f"Unexpected: {err_type}")


async def check_links_in_content(content: str) -> dict[str, Any]:
    """
    Extracts links and checks their status concurrently.
    Returns a dictionary with results.
    """
    extracted_links = _extract_links(content)
    if not extracted_links:
        logger.info("No links found to check.")
        return {"total": 0, "valid": [], "broken": [], "errors": []}

    results: dict[str, Any] = {
        "total": len(extracted_links),
        "valid": [],
        "broken": [],
        "errors": []
    }

    async with aiohttp.ClientSession() as session:
        tasks = [
            _check_link_status(session, link) for link in extracted_links
        ]
        link_results = await asyncio.gather(*tasks, return_exceptions=True)

    for i, result in enumerate(link_results):
        link = extracted_links[i]
        if isinstance(result, Exception):
            err_type = type(result).__name__
            reason = f"Task Exception: {err_type}"
            logger.error(f"{reason} for {link}")
            results["errors"].append({"url": link, "reason": reason})
        elif isinstance(result, tuple) and len(result) == 2:
            status = result[0]  # Status is always expected to be str
            reason = result[1]  # Reason can be str or None
            if status == "OK":
                results["valid"].append(link)
            elif status == "BROKEN":
                # Reason is expected here for BROKEN
                results["broken"].append(
                    {"url": link, "reason": str(reason) if reason else "Unknown"})
            else:  # ERROR
                # Reason is expected here for ERROR
                results["errors"].append(
                    {"url": link, "reason": str(reason) if reason else "Unknown Error"})
        else:  # Handle unexpected result type
            logger.error(f"Unexpected result type for {link}: {result}")
            results["errors"].append(
                {"url": link, "reason": f"Unexpected: {type(result).__name__}"})

    # Log results summary
    log_msg = (
        f"Link check: Total={results['total']}, "
        f"Valid={len(results['valid'])}, "
        f"Broken={len(results['broken'])}, "
        f"Errors={len(results['errors'])}"
    )
    logger.info(log_msg)
    return results
