import logging
import subprocess

from . import config
from .readme_parser import parse_readme


logger = logging.getLogger(__name__)


class GitHubClient:

    def fetch_jobs(self):
        try:
            result = subprocess.run(
                [
                    "curl",
                    "-fsSL",
                    config.GITHUB_README_URL,
                ],
                capture_output=True,
                text=True,
                timeout=20,
                check=True,
            )

            markdown = result.stdout

            jobs = parse_readme(markdown)

            logger.info(
                f"Parsed {len(jobs)} jobs from README"
            )

            return jobs

        except subprocess.CalledProcessError as e:
            logger.error(
                f"curl failed (exit {e.returncode}): {e.stderr.strip()}"
            )
            return []

        except subprocess.TimeoutExpired:
            logger.error("README fetch timed out")
            return []

        except Exception as e:
            logger.exception(
                f"README fetch failed: {e}"
            )
            return []