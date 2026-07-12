"""
Poller for the discovery worker.

Coordinates fetching from GitHub, storing jobs, matching resumes to job descriptions,
generating tailored cover letters via OpenClaw, and applying to jobs.
"""

import time
import logging
import os
from typing import Optional
from .github_client import GitHubClient
from .storage import JobStore
from . import config
from ..embedding_matcher.matcher import SkillMatcher
from .external_fetcher import get_job_description
from ..openclaw_integration.tailor import Tailor

logger = logging.getLogger(__name__)

class Poller:
    def __init__(self):
        self.client = GitHubClient()
        self.store = JobStore()
        self.matcher = SkillMatcher()
        self.tailor = Tailor(resume="", threshold=config.MATCH_THRESHOLD)  # resume will be set later
        self.running = False
        # Get resume from environment variable or use a default
        self.resume_text = os.getenv("RESUME_TEXT", "")
        self.resume_path = os.getenv("RESUME_PATH", "")
        # Personal info for application forms
        self.app_name = os.getenv("APP_NAME", "")
        self.app_email = os.getenv("APP_EMAIL", "")
        self.app_phone = os.getenv("APP_PHONE", "")
        self.app_linkedin = os.getenv("APP_LINKEDIN", "")
        self.app_gpa = os.getenv("APP_GPA", "")
        self.app_grad_year = os.getenv("APP_GRAD_YEAR", "")
        self.app_work_auth = os.getenv("APP_WORK_AUTH", "")
        self.app_military = os.getenv("APP_MILITARY", "")
        self.app_gender = os.getenv("APP_GENDER", "")
        self.app_ethnicity = os.getenv("APP_ETHNICITY", "")
        
        # Load resume from path or text
        self._load_resume()
        
        # If still no resume, use a placeholder for testing
        if not self.resume_text:
            logger.warning("No resume provided. Using placeholder for testing.")
            self.resume_text = """
            EXPERIENCED SOFTWARE ENGINEER
            Skilled in Python, JavaScript, and web development
            Experience with RESTful APIs, databases, and agile methodologies
            Strong problem-solving and communication skills
            """
        
        # Update tailor with actual resume text
        self.tailor = Tailor(resume=self.resume_text, threshold=config.MATCH_THRESHOLD)
        
        # Cache for external descriptions to avoid re-fetching same URL in a single run
        self._desc_cache: dict[str, str] = {}

    def _load_resume(self):
        """Load resume from RESUME_TEXT or RESUME_PATH, handling PDF files."""
        # If resume text is directly provided, use it
        if self.resume_text:
            logger.info("Using resume text from RESUME_TEXT environment variable")
            return
            
        # If resume path is provided, try to load it
        if self.resume_path:
            logger.info(f"Loading resume from path: {self.resume_path}")
            try:
                # Check if file exists
                if not os.path.exists(self.resume_path):
                    logger.error(f"Resume file not found: {self.resume_path}")
                    self.resume_text = ""
                    return
                    
                # Handle PDF files
                if self.resume_path.lower().endswith('.pdf'):
                    # Try to import PyPDF2
                    try:
                        import PyPDF2
                    except ImportError:
                        logger.error("PyPDF2 is not installed. Cannot extract text from PDF. "
                                   "Install with: pip install PyPDF2")
                        self.resume_text = ""
                        return
                    
                    # Extract text from PDF
                    text = ""
                    with open(self.resume_path, 'rb') as file:
                        pdf_reader = PyPDF2.PdfReader(file)
                        for page in pdf_reader.pages:
                            text += page.extract_text() + "\n"
                    self.resume_text = text
                    if self.resume_text:
                        logger.info(f"Successfully extracted text from PDF resume ({len(self.resume_text)} characters)")
                    else:
                        logger.warning("PDF text extraction returned empty text")
                        self.resume_text = ""
                else:
                    # Assume plain text file
                    with open(self.resume_path, 'r', encoding='utf-8') as f:
                        self.resume_text = f.read()
                    logger.info(f"Loaded resume from text file ({len(self.resume_text)} characters)")
            except Exception as e:
                logger.error(f"Failed to load resume from {self.resume_path}: {e}")
                self.resume_text = ""
        # If neither text nor path provided, res**educe_text remains empty (will get placeholder later)

    def _poll_once(self):
        """Perform a single polling cycle: discover, store, match, tailor, apply."""
        logger.debug("Starting poll cycle: discovering new internships...")
        
        # Step 1: Discover and store new jobs from GitHub
        new_jobs_count = self._discover_and_store_jobs()
        
        # Step 2: Match new jobs against resume
        if new_jobs_count > 0:
            self._match_new_jobs()
        else:
            logger.debug("No new jobs to match")
        
        # Step 3: Tailor matched jobs (generate cover letter)
        tailored_count = self._tailor_matched_jobs()
        
        # Step 4: Apply to tailored jobs
        applied_count = self._apply_to_tailored_jobs()
        
        logger.debug("Poll cycle completed")

    def _discover_and_store_jobs(self) -> int:
        """
        Discover new internships from GitHub and store them in the database.
        
        database.
        Returns:
        #     Number of new jobs stored
        """
        
        logger.debug("Fetching new issues from GitHub...")
        issues = self.client.fetch_issues()
        
        if not issues:
            logger.debug("No new issues found (or not modified)")
            return 0
            
        logger.info(f"Fetched {len(issues)} issues from GitHub")
        
        new_count = 0
        for issue in issues:
            job = self._convert_issue_to_job(issue)
            if self.store.add_job(job):
                new_count += 1
                logger.info(f"Stored new job: {job['title']} at {job['company']}")
            else:
                logger.debug(f"Job already seen: {job['title']}")
        
        if new_count > 0:
            logger.info(f"Discovered and stored {new_count} new job(s)")
        else:
            logger.info("No new jobs to store (all were duplicates)")
            
        return new_count

    def _match_new_jobs(self):
        """Match all new jobs against the resume and update their scores and status."""
        logger.info("Starting matching process for new jobs...")
        
        # Get jobs that need matching (status = 'new')
        new_jobs = self.store.get_new_jobs()
        
        if not new_jobs:
            logger.debug("No new jobs found for matching")
            return
            
        logger.info(f"Found {len(new_jobs)} new job(s) to match")
        
        matched_count = 0
        reviewed_count = 0
        
        for job in new_jobs:
            try:
                # Determine which description to use for matching:
                # Prefer external URL's content; fall back to issue body.
                desc_source = job["description"]   # default to issue body
                if job.get("external_url"):
                    # Avoid re-fetching the same URL multiple times in one run
                    cached = self._desc_cache.get(job["external_url"])
                    if cached is not None:
                        desc_source = cached
                    else:
                        fetched = get_job_description(
                            job["external_url"],
                            prefer_openclaw=False   # set True to force OpenClaw browser
                        )
                        if fetched is not None and len(fetched) > 0:
                            desc_source = fetched
                        # else keep issue body as fallback
                        self._desc_cache[job["external_url"]] = desc_source
                
                # Compute similarity between resume and chosen description
                similarity = self.matcher.match(self.resume_text, desc_source)
                
                # Determine status based on threshold
                if similarity >= config.MATCH_THRESHOLD:
                    status = 'matched'
                    matched_count += 1
                    logger.info(
                        f"Job '{job['title']}' at {job['company']} "
                        f"matched with score {similarity:.3f} (>= {config.MATCH_THRESHOLD})"
                    )
                else:
                    status = 'reviewed'
                    reviewed_count += 1
                    logger.info(
                        f"Job '{job['title']}' at {job['company']} "
                        f"reviewed with score {similarity:.3f} (< {config.MATCH_THRESHOLD})"
                    )
                
                # Update job with score and status
                success = self.store.update_job_status_and_score(
                    job['github_id'], 
                    status, 
                    similarity
                )
                
                if not success:
                    logger.warning(
                        f"Failed to update job {job['github_id']} "
                        f"with score {similarity:.3f} and status {status}"
                    )
                    
            except Exception as e:
                logger.error(
                    f"Error matching job {job.get('github_id', 'unknown')}: {e}"
                )
                # Leave as new for retry
                continue
        
        logger.info(
            f"Matching complete: {matched_count} matched, {reviewed_count} reviewed "
            f"(threshold: {config.MATCH_THRESHOLD})"
        )

    def _tailor_matched_jobs(self) -> int:
        """Generate cover letters for matched jobs and store them, setting status to 'tailored'."""
        logger.info("Starting tailoring process for matched jobs...")
        
        matched_jobs = self.store.get_matched_jobs()
        
        if not matched_jobs:
            logger.debug("No matched jobs found for tailoring")
            return 0
            
        logger.info(f"Found {len(matched_jobs)} matched job(s) to tailor")
        
        tailored_count = 0
        
        for job in matched_jobs:
            try:
                # Use external description if available, otherwise issue description
                desc_source = job["description"]
                if job.get("external_url"):
                    cached = self._desc_cache.get(job["external_url"])
                    if cached is not None:
                        desc_source = cached
                
                # Generate tailored cover letter
                cover_letter = self.tailor.tailor_application(
                    job_description=desc_source,
                    similarity_score=float(job["similarity_score"]) if job["similarity_score"] is not None else 0.0
                )
                
                if cover_letter is None:
                    logger.warning(
                        f"Tailoring failed for job {job['github_id']} ({job['title']}) - "
                        f"OpenClaw unavailable or below threshold"
                    )
                    # Keep as matched; tailoring will be retried later
                    continue
                
                # Store the cover letter and update status to tailored
                success_store = self.store.update_cover_letter(job["github_id"], cover_letter)
                success_status = self.store.update_job_status(job["github_id"], "tailored")
                
                if success_store and success_status:
                    tailored_count += 1
                    logger.info(
                        f"Tailored job '{job['title']}' at {job['company']} "
                        f"(similarity: {job['similarity_score']:.3f})"
                    )
                else:
                    logger.warning(
                        f"Failed to store tailoring results for job {job['github_id']}"
                    )
                    
            except Exception as e:
                logger.error(
                    f"Error tailoring job {job.get('github_id', 'unknown')}: {e}"
                )
                continue
        
        logger.info(f"Tailoring complete: {tailored_count} job(s) tailored")
        return tailored_count

    def _apply_to_tailored_jobs(self) -> int:
        """Attempt to apply to tailored jobs using OpenClaw browser."""
        logger.info("Starting application process for tailored jobs...")
        
        tailored_jobs = self.store.get_tailored_jobs()
        
        if not tailored_jobs:
            logger.debug("No tailored jobs found for application")
            return 0
            
        logger.info(f"Found {len(tailored_jobs)} tailored job(s) to apply to")
        
        applied_count = 0
        failed_count = 0
        
        for job in tailored_jobs:
            try:
                logger.info(f"Attempting to apply to: {job['title']} at {job['company']}")
                
                # Get the external URL to apply to
                apply_url = job.get("external_url")
                if not apply_url:
                    logger.warning(f"No external URL for job {job['github_id']}; skipping application")
                    self.store.update_job_application_failed(
                        job['github_id'], 
                        "No external URL found in issue"
                    )
                    failed_count += 1
                    continue
                
                # Prepare application data
                app_data = {
                    "full_name": self.app_name,
                    "email": self.app_email,
                    "phone": self.app_phone,
                    "linkedin": self.app_linkedin,
                    "gpa": self.app_gpa,
                    "grad_year": self.app_grad_year,
                    "work_auth": self.app_work_auth,
                    "military": self.app_military,
                    "gender": self.app_gender,
                    "ethnicity": self.app_ethnicity,
                    "resume_path": self.resume_path,
                    "cover_letter": job["cover_letter"] or "",
                }
                
                # Attempt to apply using OpenClaw browser
                success = self._submit_application_via_openclaw(apply_url, app_data)
                
                if success:
                    self.store.update_job_to_applied(
                        job['github_id'], 
                        "Application submitted successfully via automated form"
                    )
                    applied_count += 1
                    logger.info(f"Successfully applied to {job['title']} at {job['company']}")
                else:
                    self.store.update_job_application_failed(
                        job['github_id'], 
                        "Form submission failed or timed out"
                    )
                    failed_count += 1
                    logger.warning(f"Failed to apply to {job['title']} at {job['company']}")
                    
            except Exception as e:
                logger.error(
                    f"Error applying to job {job.get('github_id', 'unknown')}: {e}"
                )
                self.store.update_job_application_failed(
                    job['github_id'], 
                    f"Exception during application: {str(e)}"
                )
                failed_count += 1
                continue
        
        logger.info(
            f"Application process complete: {applied_count} successful, {failed_count} failed"
        )
        return applied_count

    def _submit_application_via_openclaw(self, url: str, data: dict) -> bool:
        """
        Use OpenClaw's Chrome browser to fill out a job application form.

        Uses the existing Chrome profile with Simplify already logged in.

        Returns:
            bool: True if application submission appears successful.
        """
        try:
            import openclaw

            logger.info(f"Opening application page: {url}")

            tab = openclaw.browser.action(
                action="open",
                url=url,
                profile="chrome",
            )

            target_id = tab.get("targetId")

            if not target_id:
                logger.error("Failed to get browser target ID")
                return False

            openclaw.browser.action(
                action="wait",
                timeoutMs=8000,
                targetId=target_id
            )

            def try_fill(field_name, value):
                """
                Attempt to fill a form field using common selectors.
                """

                if not value:
                    return False

                selectors = [
                    f'input[name="{field_name}"]',
                    f'input[id="{field_name}"]',
                    f'input[placeholder*="{field_name}" i]',
                    f'textarea[name="{field_name}"]',
                    f'textarea[placeholder*="{field_name}" i]',
                ]

                for selector in selectors:
                    try:
                        result = openclaw.browser.action(
                            action="fill",
                            targetId=target_id,
                            selector=selector,
                            value=value,
                        )

                        if result:
                            logger.info(
                                f"Filled application field: {field_name}"
                            )
                            return True

                    except Exception:
                        continue

                logger.debug(
                    f"Unable to locate application field: {field_name}"
                )

                return False

            # Fill common application fields
            fields = {
                "name": data.get("full_name"),
                "full_name": data.get("full_name"),
                "email": data.get("email"),
                "phone": data.get("phone"),
                "linkedin": data.get("linkedin"),
                "gpa": data.get("gpa"),
                "graduation": data.get("grad_year"),
            }

            for field, value in fields.items():
                try_fill(field, value)

            # Upload resume
            resume_path = data.get("resume_path")

            if resume_path:
                try:
                    openclaw.browser.action(
                        action="upload",
                        targetId=target_id,
                        selector='input[type="file"]',
                        filePath=resume_path,
                    )

                    logger.info("Resume uploaded successfully")

                except Exception as e:
                    logger.warning(
                        f"Resume upload failed: {e}"
                    )

            # Fill cover letter if available
            cover_letter = data.get("cover_letter")

            if cover_letter:
                try_fill(
                    "cover_letter",
                    cover_letter
                )

            # Click submit
            try:
                openclaw.browser.action(
                    action="click",
                    targetId=target_id,
                    selector='button[type="submit"]'
                )

                logger.info(
                    "Application submit button clicked"
                )

            except Exception as e:
                logger.error(
                    f"Failed clicking submit button: {e}"
                )
                return False

            # Wait for submission
            openclaw.browser.action(
                action="wait",
                timeoutMs=5000,
                targetId=target_id
            )

            logger.info(
                "Application submission completed"
            )

            return True

        except Exception as e:
            logger.exception(
                f"OpenClaw application automation failed: {e}"
            )
            return False