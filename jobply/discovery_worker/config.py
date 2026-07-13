"""
Configuration module for the discovery worker.
"""

import os
from pathlib import Path

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Directory for storing data (e.g., SQLite database)
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Path to the SQLite database file
DATABASE_PATH = DATA_DIR / "jobs.db"

# The repository to monitor for internships (format: "owner/repo")
GITHUB_REPO = os.getenv(
    "GITHUB_REPO",
    "vanshb03/Summer2027-Internships"
)

GITHUB_README_URL = (
    "https://raw.githubusercontent.com/"
    "vanshb03/Summer2027-Internships/"
    "main/README.md"
)
# Polling interval in seconds (default: 5 minutes)
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", 300))

# User agent for GitHub API requests
USER_AGENT = "JobPly-Discovery-Worker/1.0"

# Matching threshold for similarity score (default: 0.7)
MATCH_THRESHOLD = float(os.getenv("MATCH_THRESHOLD", 0.7))

# Database schema for the jobs table
JOBS_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    github_id INTEGER UNIQUE NOT NULL,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT,
    url TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP,
    fetched_at TIMESTAMP NOT NULL,
    etag TEXT,
    status TEXT NOT NULL DEFAULT "new",
    similarity_score REAL
);
"""