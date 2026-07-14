import logging
import os

from .readme_parser import parse_readme

logger = logging.getLogger(__name__)

class GitHubClient:

    def fetch_jobs(self):
        try:
            # Point directly to the uploaded markdown file inside the workspace
            local_readme_path = "/sandbox/.openclaw/workspace/JobPly/jobply/Summer2027_README.md"
            
            if not os.path.exists(local_readme_path):
                logger.error(f"Local README file not found at {local_readme_path}")
                return []

            with open(local_readme_path, "r", encoding="utf-8") as f:
                markdown = f.read()

            jobs = parse_readme(markdown)
            logger.info(f"Successfully parsed {len(jobs)} jobs from local README mirror.")
            return jobs

        except Exception as e:
            logger.exception(f"Local file parsing failed: {e}")
            return []
