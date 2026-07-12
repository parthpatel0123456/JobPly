"""
Tests for the storage module.
"""

import os
import tempfile
import unittest
from datetime import datetime

from discovery_worker.storage import JobStore

class TestJobStore(unittest.TestCase):
    def setUp(self):
        # Create a temporary database file
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.store = JobStore(db_path=self.db_path)

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_add_job_success(self):
        job_data = {
            "github_id": 12345,
            "title": "Software Engineering Intern",
            "company": "Tech Corp",
            "location": "San Francisco, CA",
            "url": "https://github.com/company/repo/issues/1",
            "description": "Build cool stuff.",
            "created_at": "2023-01-01T00:00:00Z",
            "fetched_at": "2023-01-02T00:00:00Z",
        }
        # Add the job
        result = self.store.add_job(job_data)
        self.assertTrue(result, "Job should be added successfully")

        # Try to add the same job again (should fail due to duplicate github_id)
        result = self.store.add_job(job_data)
        self.assertFalse(result, "Duplicate job should not be added")

        # Retrieve the job and verify
        job = self.store.get_job_by_github_id(12345)
        self.assertIsNotNone(job)
        self.assertEqual(job["github_id"], 12345)
        self.assertEqual(job["title"], "Software Engineering Intern")
        self.assertEqual(job["status"], "new")  # Default status

    def test_add_job_with_status(self):
        job_data = {
            "github_id": 54321,
            "title": "Data Science Intern",
            "company": "Data Inc",
            "location": "New York, NY",
            "url": "https://github.com/company/repo/issues/2",
            "description": "Analyze data.",
            "created_at": "2023-01-01T00:00:00Z",
            "fetched_at": "2023-01-02T00:00:00Z",
            "status": "reviewed",  # Explicit status
        }
        result = self.store.add_job(job_data)
        self.assertTrue(result)

        job = self.store.get_job_by_github_id(54321)
        self.assertIsNotNone(job)
        self.assertEqual(job["status"], "reviewed")

    def test_get_jobs_by_status(self):
        # Add a few jobs with different statuses
        job1 = {
            "github_id": 1001,
            "title": "Job 1",
            "company": "Co1",
            "location": "Loc1",
            "url": "url1",
            "description": "desc1",
            "created_at": "2023-01-01T00:00:00Z",
            "fetched_at": "2023-01-02T00:00:00Z",
        }
        job2 = {
            "github_id": 1002,
            "title": "Job 2",
            "company": "Co2",
            "location": "Loc2",
            "url": "url2",
            "description": "desc2",
            "created_at": "2023-01-01T00:00:00Z",
            "fetched_at": "2023-01-02T00:00:00Z",
            "status": "reviewed",
        }
        job3 = {
            "github_id": 1003,
            "title": "Job 3",
            "company": "Co3",
            "location": "Loc3",
            "url": "url3",
            "description": "desc3",
            "created_at": "2023-01-01T00:00:00Z",
            "fetched_at": "2023-01-02T00:00:00Z",
            "status": "applied",
        }

        self.store.add_job(job1)
        self.store.add_job(job2)
        self.store.add_job(job3)

        # Get new jobs (status='new')
        new_jobs = self.store.get_new_jobs()
        self.assertEqual(len(new_jobs), 1)
        self.assertEqual(new_jobs[0]["github_id"], 1001)

        # Get reviewed jobs
        reviewed_jobs = self.store.get_jobs_by_status("reviewed")
        self.assertEqual(len(reviewed_jobs), 1)
        self.assertEqual(reviewed_jobs[0]["github_id"], 1002)

        # Get applied jobs
        applied_jobs = self.store.get_jobs_by_status("applied")
        self.assertEqual(len(applied_jobs), 1)
        self.assertEqual(applied_jobs[0]["github_id"], 1003)

    def test_update_job_status(self):
        job_data = {
            "github_id": 9999,
            "title": "Test Job",
            "company": "Test Co",
            "location": "Test Loc",
            "url": "test_url",
            "description": "test desc",
            "created_at": "2023-01-01T00:00:00Z",
            "fetched_at": "2023-01-02T00:00:00Z",
        }
        self.store.add_job(job_data)

        # Update status
        result = self.store.update_job_status(9999, "matched")
        self.assertTrue(result)

        # Verify the update
        job = self.store.get_job_by_github_id(9999)
        self.assertEqual(job["status"], "matched")

    def test_get_recent_jobs(self):
        # Add three jobs with different fetched_at times (we'll use same for simplicity, but order by fetched_at then github_id?)
        # For simplicity, we'll just add three jobs and check we get up to the limit.
        for i in range(3):
            job_data = {
                "github_id": 2000 + i,
                "title": f"Job {i}",
                "company": f"Co {i}",
                "location": f"Loc {i}",
                "url": f"url {i}",
                "description": f"desc {i}",
                "created_at": "2023-01-01T00:00:00Z",
                "fetched_at": "2023-01-02T00:00:00Z",  # Same time, but ordering may be by github_id due to how we insert
            }
            self.store.add_job(job_data)

        jobs = self.store.get_recent_jobs(limit=2)
        self.assertEqual(len(jobs), 2)
        # The order is by fetched_at descending, then by the natural order (which may be insertion order or rowid)
        # We'll just check that we got two jobs.

    def test_etag_handling(self):
        job_data = {
            "github_id": 3333,
            "title": "ETag Job",
            "company": "ETag Co",
            "location": "ETag Loc",
            "url": "etag_url",
            "description": "etag desc",
            "created_at": "2023-01-01T00:00:00Z",
            "fetched_at": "2023-01-02T00:00:00Z",
            "etag": "W/\"abcdef123456\"",
        }
        self.store.add_job(job_data)

        # Get the etag
        etag = self.store.get_etag(3333)
        self.assertEqual(etag, "W/\"abcdef123456\"")

        # Update the etag
        self.store.update_etag(3333, "W/\"newetag789\"")
        etag = self.store.get_etag(3333)
        self.assertEqual(etag, "W/\"newetag789\"")

    def test_delete_job(self):
        job_data = {
            "github_id": 4444,
            "title": "Delete Job",
            "company": "Delete Co",
            "location": "Delete Loc",
            "url": "delete_url",
            "description": "delete desc",
            "created_at": "2023-01-01T00:00:00Z",
            "fetched_at": "2023-01-02T00:00:00Z",
        }
        self.store.add_job(job_data)

        # Delete the job
        result = self.store.delete_job(4444)
        self.assertTrue(result)

        # Try to delete again (should return False)
        result = self.store.delete_job(4444)
        self.assertFalse(result)

        # Verify job is gone
        job = self.store.get_job_by_github_id(4444)
        self.assertIsNone(job)

if __name__ == '__main__':
    unittest.main()
