"""
Tests for the OpenClaw integration module.
"""

import unittest
from unittest.mock import patch, MagicMock

# Try to import the tailor module
try:
    from openclaw_integration.tailor import Tailor
    TAILOR_AVAILABLE = True
except ImportError:
    TAILOR_AVAILABLE = False

class TestTailor(unittest.TestCase):
    def setUp(self):
        self.sample_resume = """
        John Doe
        email: john.doe@example.com
        phone: 555-123-4567
        SSN: 123-45-6789
        DOB: 01/01/1990
        
        Experience:
        - Software Engineer at XYZ Corp (2020-Present)
        - Developed web applications using Python and JavaScript
        
        Education:
        - Bachelor of Science in Computer Science, University of Example (2020)
        """
        
        self.sample_job_description = """
        We are looking for a Software Engineer with experience in Python and JavaScript.
        The ideal candidate will have:
        - 2+ years of experience in web development
        - Proficiency in Python and JavaScript
        - Experience with RESTful APIs
        - Strong problem-solving skills
        """
    
    @unittest.skipIf(not TAILOR_AVAILABLE, "Tailor module not available")
    def test_init(self):
        """Test that the Tailor initializes correctly."""
        tailor = Tailor(resume=self.sample_resume, threshold=0.7)
        self.assertEqual(tailor.resume, self.sample_resume)
        self.assertEqual(tailor.threshold, 0.7)
    
    @unittest.skipIf(not TAILOR_AVAILABLE, "Tailor module not available")
    def test_clean_resume(self):
        """Test that sensitive information is removed from resume."""
        tailor = Tailor(resume=self.sample_resume)
        cleaned = tailor._clean_resume(self.sample_resume)
        
        # Check that sensitive patterns are replaced
        self.assertNotIn("123-45-6789", cleaned)
        self.assertNotIn("01/01/1990", cleaned)
        self.assertNotIn("555-123-4567", cleaned)
        
        # Check that placeholders are present
        self.assertIn("[REDACTED SSN]", cleaned)
        self.assertIn("[REDACTED DOB]", cleaned)
        self.assertIn("[REDACTED PHONE]", cleaned)
        
        # Check that non-sensitive information is preserved
        self.assertIn("John Doe", cleaned)
        self.assertIn("john.doe@example.com", cleaned)
        self.assertIn("Software Engineer", cleaned)
    
    @unittest.skipIf(not TAILOR_AVAILABLE, "Tailor module not available")
    def test_create_prompt(self):
        """Test that the prompt is created correctly."""
        tailor = Tailor(resume=self.sample_resume)
        cleaned_resume = tailor._clean_resume(self.sample_resume)
        prompt = tailor._create_prompt(self.sample_job_description, cleaned_resume)
        
        # Check that the prompt contains the expected sections
        self.assertIn("[JOB DESCRIPTION]", prompt)
        self.assertIn("[RESUME]", prompt)
        self.assertIn("[INSTRUCTIONS]", prompt)
        self.assertIn("[OUTPUT FORMAT]", prompt)
        
        # Check that the job description and cleaned resume are in the prompt
        self.assertIn(self.sample_job_description, prompt)
        self.assertIn(cleaned_resume, prompt)
    
    @unittest.skipIf(not TAILOR_AVAILABLE, "Tailor module not available")
    @patch('openclaw_integration.tailor.OPENCLAW_AVAILABLE', True)
    @patch('openclaw_integration.tailor.openclaw')
    def test_tailor_application_below_threshold(self, mock_openclaw):
        """Test that tailoring is skipped when score is below threshold."""
        tailor = Tailor(resume=self.sample_resume, threshold=0.8)
        result = tailor.tailor_application(
            job_description=self.sample_job_description,
            similarity_score=0.6  # Below threshold
        )
        
        # Should return None when below threshold
        self.assertIsNone(result)
        
        # OpenClaw should not be called
        mock_openclaw.assert_not_called()
    
    @unittest.skipIf(not TAILOR_AVAILABLE, "Tailor module not available")
    @patch('openclaw_integration.tailor.OPENCLAW_AVAILABLE', False)
    def test_tailor_application_openclaw_unavailable(self):
        """Test that None is returned when OpenClaw is not available."""
        tailor = Tailor(resume=self.sample_resume, threshold=0.7)
        result = tailor.tailor_application(
            job_description=self.sample_job_description,
            similarity_score=0.8  # Above threshold
        )
        
        # Should return None when OpenClaw is not available
        self.assertIsNone(result)
    
    @unittest.skipIf(not TAILOR_AVAILABLE, "Tailor module not available")
    @patch('openclaw_integration.tailor.OPENCLAW_AVAILABLE', True)
    @patch('openclaw_integration.tailor.openclaw')
    def test_tailor_application_success(self, mock_openclaw):
        """Test successful tailoring when OpenClaw is available."""
        # Since we're using a placeholder implementation, we expect the placeholder response
        tailor = Tailor(resume=self.sample_resume, threshold=0.7)
        result = tailor.tailor_application(
            job_description=self.sample_job_description,
            similarity_score=0.8  # Above threshold
        )
        
        # Should return the placeholder formatted response
        self.assertIsInstance(result, str)
        self.assertIn("[TAILORED COVER LETTER FOR JOB WITH SIMILARITY 0.80]", result)
        self.assertIn("Dear Hiring Manager,", result)
        self.assertIn("Sincerely,", result)
        self.assertIn("[APPLICANT NAME]", result)
        
        # Verify that we attempted to use OpenClaw (checked availability)
        # Note: In our current implementation, we don't actually call OpenClaw due to the placeholder
        # but we do check that it's available

if __name__ == '__main__':
    unittest.main()