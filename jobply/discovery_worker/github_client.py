"""
GitHub client for the discovery worker.

Handles communication with the GitHub API, including conditional requests
using ETags to minimize API calls.
"""

import logging
import requests
from . import config

logger = logging.getLogger(__name__)

class GitHubClient:
    def __init__(self):
        self.etag: str | None = None
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": config.USER_AGENT,
        })

    def fetch_issues(self) -> list[dict]:
        """
        Fetch issues with the 'internship' label from the configured repository.
        Uses conditional requests with ETag if available.
        Returns a list of issue dictionaries (as returned by the GitHub API).
        Returns an empty list if not modified (304).
        """
        url = f"{config.GITHUB_API_URL}/search/issues"
        params = {
            "q": f"repo:{config.GITHUB_REPO} label:internship type:issue",
            "sort": "created",
            "order": "asc",
            "per_page": 100,
        }
        headers = {}
        if self.etag:
            headers["If-None-Match"] = self.etag

        try:
            response = self.session.get(url, params=params, headers=headers, timeout=10)
            if response.status_code == 304:
                logger.debug("GitHub indicated not modified (304).")
                return []
            response.raise_for_status()
            data = response.json()
            # Update ETag for next request
            self.etag = response.headers.get("ETag", self.etag)
            items = data.get("items", [])
            logger.debug(f"Fetched {len(items)} issues from GitHub.")
            return items
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching from GitHub: {e}")
            return []