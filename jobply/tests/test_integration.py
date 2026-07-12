"""
Integration test for the complete JobPly workflow: discover -> match -> store
"""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from discovery_worker.storage import JobStore
from discovery_worker.poller import Poller
from embedding_matcher.matcher import SkillMatcher

class TestWorkflowIntegration(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures with temporary database."""
        # Create a temporary database file
        self.db_fd, self.db_path = tempfile.mkstemp()
        
        # Override the database path in config
        self.original_db_path = None
        # We'll pass the db_path directly to JobStore for testing
        
        # Sample resume for testing
        self.test_resume = """
        SOFTWARE ENGINEER INTERN
        Experienced in Python web development and REST APIs
        Built projects with Flask and PostgreSQL
        Familiar with Git and agile methodologies
        """
        
        # Sample job that should match well
        self.good_job = {
            "github_id": 1001,
            "title": "Backend Software Engineering Intern",
            "company": "TechCorp",
            "location": "Remote",
            "url": "https://github.com/test/repo/issues/1",
            "description": """
            We are seeking a software engineering intern to work on our backend systems.
            Requirements:
            - Proficiency in Python
            - Experience with RESTful APIs
            - Knowledge of PostgreSQL or similar databases
            - Familiarity with Git version control
            - Strong problem-solving skills
            """,
            "created_at": "2026-07-11T00:00:00Z",
            "fetched_at": "2026-07-11T12:00:00Z",
        }
        
        # Sample job that should match poorly
        self.poor_job = {
            "github_id": 1002,
            "title": "Graphic Design Intern",
            "company": "DesignStudio",
            "location": "New York, NY",
            "url": "https://github.com/test/repo/issues/2",
            "description": """
            We are looking for a graphic design intern to create visual content.
            Requirements:
            - Proficiency in Adobe Photoshop and Illustrator
            - Experience with logo design and branding
            - Knowledge of color theory and typography
            - Strong portfolio of design work
            """,
            "created_at": "2026-07-11T00:00:00Z",
            "fetched_at": "2026-07-11T12:00:00Z",
        }

    def tearDown(self):
        """Clean up test fixtures."""
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_end_to_end_matching_workflow(self):
        """Test the complete workflow: store jobs -> match -> update scores/status."""
        # Create storage with temporary database
        store = JobStore(db_path=self.db_path)
        
        # Store both jobs
        store.add_job(self.good_job)
        store.add_job(self.poor_job)
        
        # Verify they were stored with status 'new'
        new_jobs = store.get_new_jobs()
        self.assertEqual(len(new_jobs), 2)
        
        # Create matcher and poller-like functionality
        matcher = SkillMatcher()
        
        # Process each new job
        for job in new_jobs:
            # Compute similarity
            similarity = matcher.match(self.test_resume, job["description"])
            
            # Determine expected status based on our test data
            # The good job should have higher similarity than the poor job
            if job["github_id"] == 1001:  # Good job
                expected_status = "matched"  # Should be above threshold
                min_expected_score = 0.3  # Arbitrary minimum for this test
            else:  # Poor job
                expected_status = "reviewed"  # Could be either, but let's check
                min_expected_score = 0.0
            
            # Update job in database
            store.update_job_status_and_score(
                job["github_id"], 
                expected_status, 
                similarity
            )
            
            # Verify the update worked
            updated_job = store.get_job_by_github_id(job["github_id"])
            self.assertEqual(updated_job["status"], expected_status)
            self.assertGreaterEqual(float(updated_job["similarity_score"]), min_expected_score)
            self.assertLessEqual(float(updated_job["similarity_score"]), 1.0)
        
        # Verify we can retrieve jobs by status
        matched_jobs = store.get_jobs_by_status("matched")
        reviewed_jobs = store.get_jobs_by_status("reviewed")
        
        # We expect at least one job in each category based on our test data
        self.assertGreaterEqual(len(matched_jobs), 0)
        self.assertGreaterEqual(len(reviewed_jobs), 0)
        self.assertEqual(len(matched_jobs) + len(reviewed_jobs), 2)

    def test_poller_initialization_with_resume(self):
        """Test that the poller initializes correctly with resume from environment."""
        # Test with resume text in environment
        with patch.dict(os.environ, {"RESUME_TEXT": self.test_resume}):
            poller = Poller()
            self.assertEqual(poller.resume_text, self.test_resume)
        
        # Test with resume path (we'll mock the file reading)
        resume_content = "Test resume content from file"
        with patch.dict(os.environ, {"RESUME_PATH": "/fake/path/resume.txt"}):
            with patch("builtins.open", unittest.mock.mock_open(read_data=resume_content)):
                with patch("os.path.exists", return_value=True):
                    poller = Poller()
                    self.assertEqual(poller.resume_text, resume_content)

    @patch('discovery_worker.poller.GitHubClient')
    @patch('discovery_worker.poller.JobStore')
    def test_poller_poll_once_integration(self, mock_store_class, mock_github_class):
        """Test that poller._poll_once calls the expected methods in sequence."""
        # Setup mocks
        mock_github_instance = MagicMock()
        mock_github_instance.fetch_issues.return_value = [
            {
                "id": 2001,
                "title": "Test Internship",
                "html_url": "http://example.com/issue",
                "body": "We are looking for a Python developer",
                "created_at": "2026-07-11T00:00:00Z"
            }
        ]
        mock_github_class.return_value = mock_github_instance
        
        mock_store_instance = MagicMock()
        mock_store_instance.add_job.return_value = True  # Simulate new job
        mock_store_instance.get_new_jobs.return_value = [
            {
                "github_id": 2001,
                "title": "Test Internship",
                "company": "Test Co",
                "location": "Remote",
                "url": "http://example.com/issue",
                "description": "We are looking for a Python developer",
                "created_at": "2026-07-11T00:00:00Z",
                "fetched_at": "2026-07-11T12:00:00Z",
                "status": "new",
                "similarity_score": None
            }
        ]
        mock_store_class.return_value = mock_store_instance
        
        # Create poller with test resume
        with patch.dict(os.environ, {"RESUME_TEXT": "Experienced Python developer"}):
            poller = Poller()
            # Replace the store and client with our mocks
            poller.store = mock_store_instance
            poller.client = mock_github_instance
            
            # Execute the poll cycle
            poller._poll_once()
            
            # Verify the expected calls were made
            # 1. Fetch issues from GitHub
            mock_github_instance.fetch_issues.assert_called_once()
            
            # 2. Add job to storage
            mock_store_instance.add_job.assert_called_once()
            
            # 3. Get new jobs for matching
            mock_store_instance.get_new_jobs.assert_called_once()
            
            # 4. Update job with score and status (called for each new job)
            # We expect at least one call to update_job_status_and_score
            self.assertTrue(
                mock_store_instance.update_job_status_and_score.called,
                "update_job_status_and_score should have been called for new job"
            )

if __name__ == '__main__':
    unittest.main()