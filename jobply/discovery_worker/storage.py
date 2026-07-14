"""
Storage module for handling SQLite database operations for job postings.
"""

import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any
from . import config

class JobStore:
    def __init__(self, db_path: str = config.DATABASE_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dict-like objects
        return conn

    def _init_db(self):
        """Create the jobs table if it doesn't exist, and ensure schema is up-to-date."""
        with self._get_connection() as conn:
            # Create table if not exists
            conn.executescript(config.JOBS_TABLE_SCHEMA)
            
            # Check if status column exists, add if missing (for migration)
            cursor = conn.execute("PRAGMA table_info(jobs)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'status' not in columns:
                try:
                    conn.execute("ALTER TABLE jobs ADD COLUMN status TEXT NOT NULL DEFAULT 'new'")
                    conn.commit()
                except sqlite3.OperationalError:
                    # Column might already exist in some cases
                    pass
                    
            # Check if similarity_score column exists, add if missing
            if 'similarity_score' not in columns:
                try:
                    conn.execute("ALTER TABLE jobs ADD COLUMN similarity_score REAL")
                    conn.commit()
                except sqlite3.OperationalError:
                    pass
                    
            # Check if external_url column exists, add if missing
            if 'external_url' not in columns:
                try:
                    conn.execute("ALTER TABLE jobs ADD COLUMN external_url TEXT")
                    conn.commit()
                except sqlite3.OperationalError:
                    pass
                    
            # Check if cover_letter column exists, add if missing
            if 'cover_letter' not in columns:
                try:
                    conn.execute("ALTER TABLE jobs ADD COLUMN cover_letter TEXT")
                    conn.commit()
                except sqlite3.OperationalError:
                    pass
                    
            # Check if application_result column exists, add if missing
            if 'application_result' not in columns:
                try:
                    conn.execute("ALTER TABLE jobs ADD COLUMN application_result TEXT")
                    conn.commit()
                except sqlite3.OperationalError:
                    pass
            conn.commit()

    def add_job(self, job_data: Dict[str, Any]) -> bool:
        """
        Add a new job to the database.
        Returns True if the job was inserted (new), False if it already existed.
        Sets status to 'new' by default.
        """
        # Ensure status is set to 'new' if not provided
        if 'status' not in job_data:
            job_data['status'] = 'new'
        
        # Ensure optional fields default to None
        job_data.setdefault('similarity_score', None)
        job_data.setdefault('external_url', None)
        job_data.setdefault('cover_letter', None)
        job_data.setdefault('application_result', None)
        
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    """
                    INSERT strO jobs (github_id, title, company, location, url, description, created_at, fetched_at, etag, status, similarity_score, external_url, cover_letter, application_result)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        job_data["github_id"],
                        job_data["title"],
                        job_data["company"],
                        job_data.get("location"),
                        job_data["url"],
                        job_data.get("description"),
                        job_data.get("created_at"),
                        job_data["fetched_at"],
                        job_data.get("etag"),
                        job_data["status"],
                        job_data.get("similarity_score"),
                        job_data.get("external_url"),
                        job_data.get("cover_letter"),
                        job_data.get("application_result"),
                    ),
                )
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.IntegrityError:
            # Job with this github_id already exists
            return False

    def get_job_by_github_id(self, github_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a job by its GitHub ID."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM jobs WHERE github_id = ?", (github_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_recent_jobs(self, limit: str = 50) -> List[Dict[str, Any]]:
        """Retrieve the most recent jobs, ordered by fetched_at descending."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM jobs ORDER BY fetched_at DESC LIMIT ?", (limit,)
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_new_jobs(self) -> List[Dict[str, Any]]:
        """Retrieve jobs with status 'new'."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM jobs WHERE status = 'new' ORDER BY fetched_at"
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_matched_jobs(self) -> List[Dict[str, Any]]:
        """Retrieve jobs with status 'matched'."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM jobs WHERE status = 'matched' ORDER BY similarity_score DESC"
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_tailored_jobs(self) -> List[Dict[str, Any]]:
        """Retrieve jobs with status 'tailored'."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM jobs WHERE status = 'tailored' ORDER BY similarity_score DESC"
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_applied_jobs(self) -> List[Dict[str, Any]]:
        """Retrieve jobs with status 'applied'."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM jobs WHERE status = 'applied' ORDER BY fetched_at DESC"
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_failed_jobs(self) -> List[Dict[str, Any]]:
        """Retrieve jobs with status 'application_failed'."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM jobs WHERE status = 'application_failed' ORDER BY fetched_at DESC"
            )
            return [dict(row) for row in cursor.fetchall()]

    def update_job_status(self, github_id: str, status: str) -> bool:
        """Update the status of a job. Returns True if updated."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "UPDATE jobs SET status = ? WHERE github_id = ?", (status, github_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def update_job_status_and_score(self, github_id: str, status: str, score: float) -> bool:
        """Update both status and similarity_score of a job. Returns True if updated."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "UPDATE jobs SET status = ?, similarity_score = ? WHERE github_id = ?", 
                (status, score, github_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def update_cover_letter(self, github_id: str, cover_letter: str) -> bool:
        """Store the generated cover letter for a job. Returns True if updated."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "UPDATE jobs SET cover_letter = ? WHERE github_id = ?", (cover_letter, github_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def update_job_to_applied(self, github_id: str, result_message: str) -> bool:
        """Mark a job as applied and store a result message. Returns True if updated."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE jobs 
                SET status = 'applied', application_result = ? 
                WHERE github_id = ?
                """,
                (result_message, github_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def update_job_application_failed(self, github_id: str, error_message: str) -> bool:
        """Mark a job as application_failed and store an error message. Returns True if updated."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE jobs 
                SET status = 'application_failed', application_result = ? 
                WHERE github_id = ?
                """,
                (error_message, github_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def delete_job(self, github_id: str) -> bool:
        """Delete a job by its GitHub ID. Returns True if deleted."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM jobs WHERE github_id = ?", (github_id,)
            )
            conn.commit()
            return cursor.rowcount > 0