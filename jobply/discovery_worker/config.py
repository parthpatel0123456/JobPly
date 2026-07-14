import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DATABASE_PATH = DATA_DIR / "jobs.db"
RESUME_PATH = BASE_DIR / "jobply" / "Parth_Patel_Resume.pdf"

GITHUB_REPO = os.getenv("GITHUB_REPO", "vanshb03/Summer2027-Internships")
GITHUB_README_URL = "https://raw.githubusercontent.com/vanshb03/Summer2027-Internships/main/README.md"
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", 300))
USER_AGENT = "JobPly-Discovery-Worker/1.0"
MATCH_THRESHOLD = float(os.getenv("MATCH_THRESHOLD", 0.5))

JOBS_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    github_id TEXT UNIQUE NOT NULL,
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
