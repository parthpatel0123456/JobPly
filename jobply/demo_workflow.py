#!/usr/bin/env python3
"""
Demonstration script for JobPly workflow.

This script demonstrates the complete workflow:
1. Store sample jobs in the database
2. Match them against a resume
3. Show the results
"""

import os
import sys
import tempfile

# Add the jobply directory to the path so we can import modules
sys.path.insert(0, '/sandbox/.openclaw-data/workspace/jobply')

from discovery_worker.storage import JobStore
from discovery_worker.config import MATCH_THRESHOLD
from embedding_matcher.matcher import SkillMatcher

def main():
    print("=== JobPly Workflow Demonstration ===\n")
    
    # Create a temporary database for demonstration
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    try:
        # Initialize storage with our temporary database
        store = JobStore(db_path=db_path)
        matcher = SkillMatcher()
        
        # Sample resume
        resume_text = """
        SOFTWARE ENGINEERING STUDENT
        Experience with Python, JavaScript, and web development
        Built web applications using Flask and React
        Familiar with RESTful APIs and PostgreSQL databases
        Proficient in Git and GitHub
        Strong problem-solving and teamwork skills
        """
        
        print(f"Using resume:\n{resume_text.strip()}\n")
        print(f"Matching threshold: {MATCH_THRESHOLD}\n")
        
        # Sample jobs to demonstrate the workflow
        sample_jobs = [
            {
                "github_id": 1001,
                "title": "Backend Software Engineering Intern",
                "company": "TechInnovate Inc",
                "location": "Remote (US-based)",
                "url": "https://github.com/techcompanies/internships/issues/1001",
                "description": """
                We are seeking a backend engineering intern to help develop our cloud platform.
                
                Responsibilities:
                - Develop RESTful APIs using Python/FastAPI
                - Work with PostgreSQL databases
                - Implement automated testing suites
                - Collaborate in agile development environment
                
                Requirements:
                - Currently pursuing Computer Science or related degree
                - Proficiency in Python programming
                - Experience with SQL and database design
                - Familiarity with Git version control
                - Basic knowledge of web frameworks (Flask, Django, or FastAPI)
                """,
                "created_at": "2026-07-10T08:00:00Z",
                "fetched_at": "2026-07-11T10:00:00Z"
            },
            {
                "github_id": 1002,
                "title": "Frontend Web Development Intern",
                "company": "WebCraft Studios",
                "location": "San Francisco, CA (Hybrid)",
                "url": "https://github.com/techcompanies/internships/issues/1002",
                "description": """
                Join our frontend team to create beautiful user interfaces.
                
                Responsibilities:
                - Develop responsive websites using React and TypeScript
                - Implement UI/UX designs from Figma mockups
                - Optimize web performance and accessibility
                - Participate in code reviews and team ceremonies
                
                Requirements:
                - Experience with HTML, CSS, and JavaScript
                - Familiarity with React or similar frameworks
                - Knowledge of UI/UX principles
                - Strong attention to detail
                - Portfolio of web projects (personal or academic)
                """,
                "created_at": "2026-07-10T09:00:00Z",
                "fetched_at": "2026-07-11T10:00:00Z"
            },
            {
                "github_id": 1003,
                "title": "Data Science Intern",
                "company": "DataInsights LLC",
                "location": "New York, NY (Remote)",
                "url": "https://github.com/techcompanies/internships/issues/1003",
                "description": """
                Help us extract insights from complex datasets.
                
                Responsibilities:
                - Clean and preprocess data using Python/pandas
                - Build predictive models with scikit-learn
                - Create data visualizations with matplotlib/seaborn
                - Communicate findings to stakeholders
                
                Requirements:
                - Coursework in statistics or machine learning
                - Proficiency in Python programming
                - Experience with data manipulation libraries
                - Familiarity with Jupyter notebooks
                - Strong analytical thinking
                """,
                "created_at": "2026-07-10T10:00:00Z",
                "fetched_at": "2026-07-11T10:00:00Z"
            }
        ]
        
        print("--- STEP 1: Storing Sample Jobs ---")
        stored_count = 0
        for job_data in sample_jobs:
            if store.add_job(job_data):
                stored_count += 1
                print(f"✓ Stored: {job_data['title']} at {job_data['company']}")
            else:
                print(f"⚠ Duplicate skipped: {job_data['title']} at {job_data['company']}")
        
        print(f"\nStored {stored_count} new job(s) out of {len(sample_jobs)} total\n")
        
        print("--- STEP 2: Matching Jobs Against Resume ---")
        # Get all new jobs (status = 'new')
        new_jobs = store.get_new_jobs()
        print(f"Found {len(new_jobs)} new job(s) to process\n")
        
        matched_jobs = []
        reviewed_jobs = []
        
        for job in new_jobs:
            # Calculate similarity score
            similarity = matcher.match(resume_text, job['description'])
            
            # Determine status based on threshold
            if similarity >= MATCH_THRESHOLD:
                status = 'matched'
                matched_jobs.append((job, similarity))
                result_emoji = "🎯"
            else:
                status = 'reviewed'
                reviewed_jobs.append((job, similarity))
                result_emoji = "👁"
            
            # Update the job in database
            store.update_job_status_and_score(job['github_id'], status, similarity)
            
            print(f"{result_emoji} {job['title']} at {job['company']}")
            print(f"   Similarity: {similarity:.3f} | Status: {status.upper()}")
            print(f"   Company: {job['company']} | Location: {job['location']}")
            print()
        
        print("--- STEP 3: Results Summary ---")
        print(f"Matched Jobs (≥ {MATCH_THRESHOLD}): {len(matched_jobs)}")
        for job, score in sorted(matched_jobs, key=lambda x: x[1], reverse=True):
            print(f"  • {job['title']} at {job['company']} ({score:.3f})")
        
        print(f"\nReviewed Jobs (< {MATCH_THRESHOLD}): {len(reviewed_jobs)}")
        for job, score in sorted(reviewed_jobs, key=lambda x: x[1], reverse=True):
            print(f"  • {job['title']} at {job['company']} ({score:.3f})")
        
        print("\n--- STEP 4: Database Verification ---")
        # Show what's actually stored in the database
        all_jobs = store.get_recent_jobs(limit=10)
        print(f"Total jobs in database: {len(all_jobs)}")
        print("\nStored records:")
        print("-" * 80)
        print(f"{'ID':<6} {'Title':<35} {'Company':<20} {'Score':<8} {'Status'}")
        print("-" * 80)
        for job in all_jobs:
            title = job['title'][:34] + "..." if len(job['title']) > 35 else job['title']
            company = job['company'][:19] + "..." if len(job['company']) > 19 else job['company']
            score = f"{job['similarity_score']:.3f}" if job['similarity_score'] is not None else "None"
            status = job['status']
            print(f"{job['github_id']:<6} {title:<35} {company:<20} {score:<8} {status}")
        
        print("\n=== Demonstration Complete ===")
        print("\nNext steps in a full implementation:")
        print("1. Set up continuous polling with real GitHub repository")
        print("2. Configure actual resume (via RESUME_PATH or RESUME_TEXT env vars)")
        print("3. Integrate with OpenClaw for tailoring applications (already implemented)")
        print("4. Add notification system when tailored applications are ready")
        print("5. Implement application tracking and follow-up reminders")
        
    finally:
        # Clean up temporary database
        os.close(db_fd)
        os.unlink(db_path)

if __name__ == "__main__":
    main()