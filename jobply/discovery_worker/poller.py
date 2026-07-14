import logging
from jobply.discovery_worker.storage import JobStore
from jobply.embedding_matcher.matcher import SkillMatcher
from jobply.discovery_worker.github_client import GitHubClient
from jobply.discovery_worker.resume_parser import extract_text_from_pdf
from jobply.discovery_worker import config

logger = logging.getLogger(__name__)

class Poller:
    def __init__(self):
        self.github_client = GitHubClient()
        self.matcher = SkillMatcher()
        self.store = JobStore()

    def start(self):
        resume_text = extract_text_from_pdf(config.RESUME_PATH)
        if not resume_text:
            logger.error("Failed to extract text from resume.")
            return
        
        raw_jobs = self.github_client.fetch_jobs()
        for job_data in raw_jobs:
            self.store.add_job(job_data)
            
        jobs_to_match = self.store.get_new_jobs()
        for job in jobs_to_match:
            job_str = f"Title: {job['title']} | Company: {job['company']}"
            score = self.matcher.match(resume_text, job_str)
            
            # Save the score regardless of whether it's a match or reject
            status = 'matched' if score >= config.MATCH_THRESHOLD else 'rejected'
            self.store.update_job_status_and_score(job['github_id'], status, float(score))
            
            if status == 'matched':
                logger.info(f"🎉 MATCHED: {job['title']} ({score:.4f})")
