# Environment variables for JobPly worker
# Generated on 2026-07-11

# ── Core job‑discovery settings ────────────────────────────────────────
export GITHUB_REPO="SimplifyJobs/Summer2026-Internships"
export POLL_INTERVAL=60               # seconds between GitHub polls (60 = 1 min for testing)
export MATCH_THRESHOLD=0.7            # similarity cut‑off for a “match”

# ── Résumé location (inside the sandbox) ─────────────────────────────────
export RESUME_PATH="/sandbox/.openclaw-data/workspace/jobply/Parth_Patel_Resume.pdf"

# ── Chrome profile with Simplify (from your earlier setup) ─────────────────
export CHROME_USER_DATA_DIR="/Users/parth/ChromeProfile_Simplify"

# ── Personal info for application forms (set only what you want to share) ─
export APP_NAME="Parth Patel"
export APP_EMAIL="pdpate22@ncsu.edu"
export APP_PHONE="+1-555-123-4567"            # optional – uncomment if you want it sent
export APP_LINKEDIN="https://www.linkedin.com/in/parthpatel2006/"
export APP_GPA="3.7"
export APP_GRAD_YEAR="2028"                   # updated to 2028
export APP_WORK_AUTH="US citizen"
export APP_MILITARY="not a veteran"
export APP_GENDER="male"
export APP_ETHNICITY="Asian American"