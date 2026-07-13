import logging
import base64
import requests

from . import config
from .readme_parser import parse_readme


logger = logging.getLogger(__name__)


class GitHubClient:

    def __init__(self):
        self.session = requests.Session()

        self.session.headers.update(
            config.get_github_headers()
        )


    def fetch_jobs(self):

        try:

            response = self.session.get(
                config.GITHUB_README_URL,
                timeout=10
            )

            response.raise_for_status()

            data = response.json()

            markdown = base64.b64decode(
                data["content"]
            ).decode("utf-8")

            jobs = parse_readme(markdown)

            logger.info(
                f"Parsed {len(jobs)} jobs from README"
            )

            return jobs


        except Exception as e:

            logger.error(
                f"README fetch failed: {e}"
            )

            return []