import logging
import subprocess
import os

from . import config
from .readme_parser import parse_readme

logger = logging.getLogger(__name__)

class GitHubClient:

    def fetch_jobs(self):
        try:
            # Build the base curl command
            curl_cmd = ["curl", "-fsSL"]
            
            # Check for a token in the environment and inject it if found
            github_token = os.environ.get("GITHUB_TOKEN")
            if github_token:
                curl_cmd.extend(["-H", f"Authorization: token {github_token}"])
            
            # Append the target URL
            curl_cmd.append(config.GITHUB_README_URL)

            result = subprocess.run(
                curl_cmd,
                capture_output=True,
                text=True,
                timeout=20,
                check=True,
            )

            markdown = result.stdout
            jobs = parse_readme(markdown)

            logger.info(f"Parsed {len(jobs)} jobs from README")
            return jobs

        except subprocess.CalledProcessError as e:
            logger.error(f"curl failed (exit {e.returncode}): {e.stderr.strip()}")
            return []
        except subprocess.TimeoutExpired:
            logger.error("README fetch timed out")
            return []
        except Exception as e:
            logger.exception(f"README fetch failed: {e}")
            return []