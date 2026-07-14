import sqlite3
import argparse


def get_jobs():
    conn = sqlite3.connect("data/jobs.db")
    conn.row_factory = sqlite3.Row

    jobs = conn.execute("""
    SELECT title, company, location, created_at, similarity_score, url
    FROM jobs
    ORDER BY 
        CASE substr(created_at, 1, 3)
            WHEN 'Jul' THEN 7
            WHEN 'Jun' THEN 6
            WHEN 'May' THEN 5
            WHEN 'Apr' THEN 4
            WHEN 'Mar' THEN 3
            WHEN 'Feb' THEN 2
            WHEN 'Jan' THEN 1
            ELSE 0
        END DESC,
        CAST(substr(created_at, 5) AS INTEGER) DESC,
        similarity_score DESC
    """).fetchall()

    conn.close()

    return jobs


def debug_jobs(jobs):
    print("\nDEBUG JOB PIPELINE")
    print("=" * 100)

    print(f"Total Jobs in Database: {len(jobs)}")

    missing_company = 0
    missing_title = 0
    missing_url = 0
    missing_date = 0
    missing_score = 0

    seen = set()
    duplicates = 0

    for job in jobs:
        if not job["company"]:
            missing_company += 1

        if not job["title"]:
            missing_title += 1

        if not job["url"]:
            missing_url += 1

        if not job["created_at"]:
            missing_date += 1

        if job["similarity_score"] is None:
            missing_score += 1

        key = (
            job["company"],
            job["title"],
            job["location"]
        )

        if key in seen:
            duplicates += 1

        seen.add(key)

    print("\nData Quality:")
    print("-" * 100)
    print(f"Missing Company:        {missing_company}")
    print(f"Missing Title:          {missing_title}")
    print(f"Missing URL:            {missing_url}")
    print(f"Missing Date:           {missing_date}")
    print(f"Missing Match Score:    {missing_score}")
    print(f"Possible Duplicates:    {duplicates}")

    print("\nSample Jobs:")
    print("-" * 100)

    for i, job in enumerate(jobs[:10], 1):
        print(
            f"{i}. {job['company']} | "
            f"{job['title']} | "
            f"{job['location']}"
        )

    print("=" * 100)


def display_jobs(jobs):
    print(f"\nTotal Jobs: {len(jobs)}")
    print("=" * 100)

    for i, job in enumerate(jobs, 1):
        print(f"\n#{i}")
        print(f"Company:     {job['company']}")
        print(f"Title:       {job['title']}")
        print(f"Location:    {job['location']}")
        print(f"Date Posted: {job['created_at']}")

        print(
            f"Match Score: {job['similarity_score']:.4f}"
            if job['similarity_score']
            else "Match Score: N/A"
        )

        print(f"URL:         {job['url']}")
        print("-" * 100)


def main():
    parser = argparse.ArgumentParser(
        description="View JobPly discovered jobs"
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Show debug information for all jobs"
    )

    args = parser.parse_args()

    jobs = get_jobs()

    if args.all:
        debug_jobs(jobs)
    else:
        display_jobs(jobs)


if __name__ == "__main__":
    main()