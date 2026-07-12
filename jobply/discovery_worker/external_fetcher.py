"""
Fetches the visible text of an external job‑posting URL.
Tries a fast HTTP request first; falls back to OpenClaw’s managed Chrome browser
if needed (or if explicitly requested).
"""

import logging
import re
import requests
from typing import Optional
from bs4 import BeautifulSoup  # for light HTML stripping

logger = logging.getLogger(__name__)

def _strip_html(text: str) -> str:
    """Very naive HTML stripper – replace tags with spaces and collapse whitespace."""
    # Remove script/style contents
    text = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', text, flags=re.DOTALL | re.IGNORECASE)
    # Replace remaining tags with a space
    text = re.sub(r'<[^>]+>', ' ', text)
    # Collapse whitespace
    return re.sub(r'\s+', ' ', text).strip()

def fetch_via_http(url: str, timeout: int = 10) -> Optional[str]:
    """Download the page with requests and return plain text."""
    try:
        headers = {"User-Agent": "JobPly/1.0"}
        resp = requests.get(url, timeout=timeout, headers=headers)
        resp.raise_for_status()
        return _strip_html(resp.text)
    except Exception as e:
        logger.warning(f"HTTP fetch failed for {url}: {e}")
        return None

def fetch_via_openclaw(url: str, timeout_sec: int = 20) -> Optional[str]:
    """
    Use OpenClaw's managed Chrome browser to get the rendered text.
    Requires the `openclaw` package to be installed and available.
    """
    try:
        import openclaw
        # Open a new tab
        tab = openclaw.browser.action(
            action="open",
            url=url,
            profile="chrome",          # will use the profile pointed to by CHROME_USER_DATA_DIR
        )
        # Wait for page to load (fixed wait; could be polled for document.readyState)
        openclaw.browser.action(
            action="wait",
            timeoutMs=5000,
            targetId=tab["targetId"]
        )
        # Extract all visible text
        result = openclaw.browser.action(
            action="evaluate",
            targetId=tab["targetId"],
            javaScript="() => document.body.innerText"
        )
        # Close the tab
        openclaw.browser.action(action="close", targetId=tab["targetId"])
        text = result.get("value", "")
        return text.strip() if text else None
    except Exception as e:
        logger.error(f"OpenClaw browser fetch failed for {url}: {e}")
        return None

def get_job_description(url: str, prefer_openclaw: bool = False) -> Optional[str]:
    """
    Try HTTP first (fast); fall back to OpenClaw if needed or if explicitly requested.
    Returns None if both attempts fail.
    """
    text = fetch_via_http(url)
    if text and len(text) > 50:   # arbitrary threshold – adjust if you see too‑short extracts
        return text
    if prefer_openclaw or not text:
        return fetch_via_openclaw(url)
    return text