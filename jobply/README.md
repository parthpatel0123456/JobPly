# JobPly

An automated internship application pipeline.

## Overview

JobPly is a modular Python-based system designed to automate the process of discovering, matching, and applying for internships. The system consists of several workers that handle different stages of the pipeline:

1. **Discovery Worker**: Polls GitHub repositories for internship postings
2. **Skill Matcher**: Uses local embeddings to match candidate resumes with opportunities  
3. **OpenClaw Integration**: Tailors applications for jobs that meet similarity thresholds
4. **Application Worker** (Future): Handles submission of tailored applications

## Architecture

The project follows a modular architecture with separate workers for each concern:

```
jobply/
├── README.md
├── requirements.txt
├── setup.py
├── discovery_worker/         # Discovers and stores internships
│   ├── __init__.py
│   ├── config.py             # Configuration management
│   ├── github_client.py      # GitHub API client with ETag support
│   ├── poller.py             # Discovery + matching orchestration
│   ├── storage.py            # SQLite database operations
│   └── worker.py             # Entry point
├── embedding_matcher/        # Matches resumes to job descriptions
│   ├── __init__.py
│   └── matcher.py            # Local embedding-based similarity
├── openclaw_integration/     # Tailors applications using OpenClaw
│   ├── __init__.py
│   └── tailor.py             # Threshold-based, PII-protected prompting
├── tests/                    # Test suites
│   ├── test_storage.py
│   ├── test_matcher.py
│   └─ test_openclaw_integration.py
└── data/                     # SQLite database (created at runtime)
    └── jobs.db
```

## How It Works

### 1. Discovery Phase
The discovery worker polls a configured GitHub repository for issues labeled as internships. For each new issue:
- Extracts job details (title, company, location, URL, description)
- Stores in SQLite database with `status = 'new'`
- Uses ETags to minimize API calls (only fetches changed resources)

### 2. Matching Phase
After storing new jobs, the system automatically:
- Retrieves all jobs with `status = 'new'`
- Computes semantic similarity between your resume and each job description
- Uses `all-MiniLM-L6-v2` sentence-transformers model for embeddings
- Updates each job with:
  - `similarity_score`: Float between 0.0 and 1.0
  - `status`: `'matched'` (>= threshold) or `'reviewed'` (< threshold)

### 3. Tailoring Phase
Jobs with `status = 'matched'` are processed by the OpenClaw integration:
- Only jobs meeting the similarity threshold are processed
- Resume is sanitized to remove PII (SSN, DOB, phone numbers)
- Creates structured prompt for OpenClaw AI
- Generates tailored cover letter (or other application materials)
- Never includes unnecessary personal information in prompts

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables
```bash
# Required: GitHub repository to monitor for internships
export GITHUB_REPO="SimplifyJobs/Summer2026-Internships"

# Optional: Polling interval in seconds (default: 300 = 5 minutes)
export POLL_INTERVAL=60

# Optional: Similarity threshold for matching (default: 0.7)
export MATCH_THRESHOLD=0.7

# Optional: Provide your resume (choose one method)
# Method 1: Path to resume file
export RESUME_PATH="/path/to/your/resume.txt"

# Method 2: Raw resume text (for testing or simple resumes)
export RESUME_TEXT="Your resume text here..."

# If neither is provided, a placeholder resume is used for testing
```

### 3. Initialize Database
The database (`data/jobs.db`) will be created automatically on first run.

### 4. Start the Pipeline
```bash
cd /sandbox/.openclaw-data/workspace/jobply
python -m discovery_worker.worker
```

The worker will:
1. Poll GitHub every `POLL_INTERVAL` seconds
2. Store new internships
3. Match them against your resume
4. Update scores and statuses
5. Repeat

## Database Schema

The `jobs` table contains:
- `github_id`: Unique identifier from GitHub (UNIQUE)
- `title`: Internship position title
- `company`: Company offering the internship
- `location`: Job location (if specified)
- `url`: Link to the GitHub issue
- `description`: Full job description text
- `created_at`: When the issue was created on GitHub
- `fetched_at`: When JobPly first saw the issue
- `etag`: For efficient GitHub API polling
- `status`: Processing state (`new`, `matched`, `reviewed`, `applied`)
- `similarity_score`: Float between 0.0-1.0 from resume matching

## Usage Examples

### Check Stored Jobs
```bash
# See recent jobs with their match status
sqlite3 data/jobs.db "SELECT github_id, title, company, similarity_score, status FROM jobs ORDER BY fetched_at DESC LIMIT 10;"

# See only jobs that matched your resume (above threshold)
sqlite3 data/jobs.db "SELECT github_id, title, company, similarity_score FROM jobs WHERE status = 'matched' ORDER BY similarity_score DESC;"

# See jobs that were reviewed but didn't meet threshold
sqlite3 data/jobs.db "SELECT github_id, title, company, similarity_score FROM jobs WHERE status = 'reviewed' ORDER BY similarity_score ASC;"
```

### Manual Testing
To test the matcher directly:
```bash
python -c "
from embedding_matcher.matcher import SkillMatcher
matcher = SkillMatcher()
resume = 'Experienced Python developer with web development skills'
job = 'We seek a Python engineer for backend development'
score = matcher.match(resume, job)
print(f'Similarity: {score:.3f}')
"
```

## Extending the Pipeline

### Adding New Workers
1. Create a new directory under `jobply/` (e.g., `application_worker/`)
2. Implement your worker logic following the existing patterns
3. Integrate with the database status flow (e.g., process jobs with `status = 'matched'`)

### Configuration Options
All settings can be adjusted via environment variables:
- `GITHUB_REPO`: Target GitHub repository (format: "owner/repo")
- `POLL_INTERVAL`: Seconds between GitHub polls (default: 300)
- `MATCH_THRESHOLD`: Similarity score threshold for matching (default: 0.7)
- `RESUME_PATH`: File path to your resume
- `RESUME_TEXT`: Raw resume text (overrides RESUME_PATH if both set)

## Requirements

See `requirements.txt` for dependencies:
- `requests`: For GitHub API communication
- `sentence-transformers`: For local semantic matching
- `openclaw`: For AI-powered application tailoring

## Development

### Running Tests
```bash
# Run all tests
python -m unittest discover tests

# Run specific test module
python -m unittest tests.test_matcher
```

### Code Quality
- Follows PEP 8 style guidelines
- Comprehensive type hints
- Detailed docstrings
- Structured logging
- Error handling and graceful degradation

## License

MIT