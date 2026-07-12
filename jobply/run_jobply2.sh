#!/usr/bin/env bash
set -e
cd /sandbox/.openclaw-data/workspace/jobply
export GITHUB_REPO="SimplifyJobs/Summer2026-Internships"
export POLL_INTERVAL=30
export MATCH_THRESHOLD=0.7
export RESUME_PATH="/sandbox/.openclaw-data/workspace/jobply/Parth_Patel_Resume.pdf"
export APP_NAME="Parth Patel"
export APP_EMAIL="pdpate22@ncsu.edu"
export APP_PHONE="+1-555-123-4567"
export APP_LINKEDIN="https://www.linkedin.com/in/parthpatel2006/"
export APP_GPA="3.7"
export APP_GRAD_YEAR="2028"
export APP_WORK_AUTH="US citizen"
export APP_MILITARY="not a veteran"
export APP_GENDER="male"
export APP_ETHNICITY="Asian American"
timeout 60s python -m discovery_worker.worker 2>&1 | tee /tmp/jobply_output.txt