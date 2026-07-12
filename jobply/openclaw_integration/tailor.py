"""
OpenClaw tailoring integration for the JobPly system.

This module provides functionality to tailor job applications using
OpenClaw's capabilities, only for jobs that meet a similarity threshold.
"""

import re
import logging
from typing import Optional, Dict, Any

try:
    import openclaw
    OPENCLAW_AVAILABLE = True
except ImportError:
    OPENCLAW_AVAILABLE = False
    # Create a mock for type hints when not available
    class openclaw:
        pass

logger = logging.getLogger(__name__)

class Tailor:
    def __init__(self, resume: str, threshold: float = 0.7):
        """
        Initialize the Tailor with a resume and similarity threshold.
        
        Args:
            resume: The resume text to use for tailoring
            threshold: Minimum similarity score (0-1) to consider a job for tailoring
        """
        self.resume = resume
        self.threshold = threshold
        
        # Patterns to identify and remove sensitive personal information
        self.ssn_pattern = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')  # SSN: XXX-XX-XXXX
        self.dob_pattern = re.compile(r'\b\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}\b')  # DOB: MM/DD/YYYY or MM-DD-YYYY
        self.phone_pattern = re.compile(
            r'\b\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}\b|'  # XXX-XXX-XXXX
            r'\(\d{3}\)\s*\d{3}[-\.\s]??\d{4}|\d{3}[-\.\s]??\d{4}'  # (XXX) XXX-XXXX or XXX-XXX-XXXX
        )
        # Note: We intentionally keep email addresses as they may be relevant for contact
        # but we could add email filtering if deemed unnecessary for the specific use case

    def _clean_resume(self, resume: str) -> str:
        """
        Remove sensitive personal information from the resume.
        
        Args:
            resume: Raw resume text
            
        Returns:
            Cleaned resume with sensitive information redacted or removed
        """
        lines = resume.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Skip lines containing sensitive information
            if (self.ssn_pattern.search(line) or 
                self.dob_pattern.search(line) or 
                self.phone_pattern.search(line)):
                # Replace the line with a placeholder indicating redaction
                # Alternatively, we could remove the line entirely
                # Here we replace sensitive patterns within the line
                cleaned_line = self.ssn_pattern.sub('[REDACTED SSN]', line)
                cleaned_line = self.dob_pattern.sub('[REDACTED DOB]', cleaned_line)
                cleaned_line = self.phone_pattern.sub('[REDACTED PHONE]', cleaned_line)
                cleaned_lines.append(cleaned_line)
            else:
                cleaned_lines.append(line)
                
        return '\n'.join(cleaned_lines)

    def _create_prompt(self, job_description: str, cleaned_resume: str) -> str:
        """
        Create a structured prompt for the OpenClaw AI to generate tailored content.
        
        Args:
            job_description: The job description text
            cleaned_resume: The resume with sensitive information removed
            
        Returns:
            A formatted prompt string
        """
        return f"""
[JOB DESCRIPTION]
{job_description}

[RESUME]
{cleaned_resume}

[INSTRUCTIONS]
You are an expert career advisor helping a job seeker tailor their application materials.
Using the provided job description and resume, generate a tailored cover letter that highlights
the most relevant skills and experiences. Focus on matching the candidate's qualifications
to the specific requirements of the position.

Do not include any personal information such as social security numbers, date of birth,
or phone numbers in the output. Keep the tone professional and enthusiastic.

[OUTPUT FORMAT]
Generate only the cover letter text, no additional commentary or explanations.
"""

    def tailor_application(self, job_description: str, similarity_score: float) -> Optional[str]:
        """
        Generate a tailored application for a job if it meets the similarity threshold.
        
        Args:
            job_description: The job description text
            similarity_score: The similarity score between resume and job description (0-1)
            
        Returns:
            Tailored cover letter text if score >= threshold and OpenClaw is available,
            None otherwise
        """
        # Check if score meets threshold
        if similarity_score < self.threshold:
            logger.info(f"Job similarity score {similarity_score:.2f} below threshold {self.threshold}. Skipping tailoring.")
            return None
            
        # Check if OpenClaw is available
        if not OPENCLAW_AVAILABLE:
            logger.warning("OpenClaw not available. Cannot generate tailored application.")
            return None
            
        try:
            # Clean the resume to remove sensitive information
            cleaned_resume = self._clean_resume(self.resume)
            
            # Create the prompt
            prompt = self._create_prompt(job_description, cleaned_resume)
            
            # Use OpenClaw to generate the tailored content
            # Note: This is a placeholder for actual OpenClaw integration
            # In a real implementation, we would call the appropriate OpenClaw API
            logger.info("Generating tailored application using OpenClaw...")
            
            # For now, we'll simulate the response
            # In reality, this would be something like:
            # response = openclaw.generate_text(prompt, max_length=500, temperature=0.7)
            # return response.text
            
            # Placeholder response
            tailored_content = f"[TAILORED COVER LETTER FOR JOB WITH SIMILARITY {similarity_score:.2f}]\n\n" \
                              f"Dear Hiring Manager,\n\n" \
                              f"I am excited to apply for the position described in the job posting. " \
                              f"My background in [RELEVANT SKILLS] aligns well with the requirements outlined. " \
                              f"Specifically, my experience with [SPECIFIC EXPERIENCE] makes me a strong candidate.\n\n" \
                              f"I am particularly drawn to this opportunity because [REASON FOR INTEREST]. " \
                              f"I look forward to discussing how my skills can contribute to your team.\n\n" \
                              f"Sincerely,\n[APPLICANT NAME]"
            
            logger.info("Successfully generated tailored application.")
            return tailored_content
            
        except Exception as e:
            logger.error(f"Error generating tailored application: {str(e)}")
            return None

    def is_available(self) -> bool:
        """
        Check if the OpenClaw tailoring functionality is available.
        
        Returns:
            True if OpenClaw is installed and configured, False otherwise
        """
        return OPENCLAW_AVAILABLE