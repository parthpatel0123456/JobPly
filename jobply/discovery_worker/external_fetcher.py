"""
Fetches the visible text of an external job-posting URL.

Uses curl instead of requests because OpenClaw sandbox networking blocks
Python HTTP clients through the proxy. Falls back to OpenClaw Chrome browser
when needed.
"""

import logging
import re
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)


def _strip_html(text: str) -> str:
    """Remove HTML tags and collapse whitespace."""

    # Remove script/style blocks
    text = re.sub(
        r"<(script|style)[^>]*>.*?</\1>",
        " ",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )

    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", text)

    # Normalize whitespace
    return re.sub(r"\s+", " ", text).strip()


def fetch_via_http(url: str, timeout: int = 20) -> Optional[str]:
    """
    Download page using curl.

    requests does not work inside the OpenClaw sandbox because of
    proxy restrictions.
    """

    try:
        result = subprocess.run(
            [
                "curl",
                "-fsSL",
                "-A",
                "Mozilla/5.0 JobPly/1.0",
                url,
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        if result.returncode != 0:
            logger.warning(
                f"curl fetch failed for {url}: {result.stderr.strip()}"
            )
            return None

        return _strip_html(result.stdout)

    except subprocess.TimeoutExpired:
        logger.warning(f"curl timeout fetching {url}")
        return None

    except Exception as e:
        logger.warning(f"curl fetch failed for {url}: {e}")
        return None


def fetch_via_openclaw(url: str, timeout_sec: int = 20) -> Optional[str]:
    """
    Use OpenClaw managed Chrome browser to get rendered text.
    """

    try:
        import openclaw

        tab = openclaw.browser.action(
            action="open",
            url=url,
            profile="chrome",
        )

        target_id = tab.get("targetId")

        if not target_id:
            logger.error("No browser targetId returned")
            return None

        openclaw.browser.action(
            action="wait",
            timeoutMs=5000,
            targetId=target_id,
        )

        result = openclaw.browser.action(
            action="evaluate",
            targetId=target_id,
            javaScript="() => document.body.innerText",
        )

        openclaw.browser.action(
            action="close",
            targetId=target_id,
        )

        text = result.get("value", "")

        return text.strip() if text else None

    except Exception as e:
        logger.error(
            f"OpenClaw browser fetch failed for {url}: {e}"
        )
        return None


def get_job_description(
    url: str,
    prefer_openclaw: bool = False
) -> Optional[str]:
    """
    Try curl first.

    If curl fails or returns weak content, use OpenClaw browser.
    """

    text = fetch_via_http(url)

    if text and len(text) > 50:
        return text

    logger.info(
        f"curl returned insufficient content for {url}, trying browser"
    )

    if prefer_openclaw or not text:
        return fetch_via_openclaw(url)

    return text