import sqlite3
import argparse


DB_PATH = "data/jobs.db"


def debug_view(conn):
    conn.row_factory = sqlite3.Row

    jobs = conn.execute("""
        SELECT title, company, location, created_at, similarity_score, url
        FROM jobs
    """).fetchall()

    print("=" * 100)
    print(f"Total Jobs in Database: {len(jobs)}")
    print()

    print("Data Quality:")
    print("-" * 100)

    missing_company = sum(
        1 for job in jobs if not job["company"]
    )

    missing_title = sum(
        1 for job in jobs if not job["title"]
    )

    missing_url = sum(
        1 for job in jobs if not job["url"]
    )

    missing_date = sum(
        1 for job in jobs if not job["created_at"]
    )

    missing_score = sum(
        1 for job in jobs if job["similarity_score"] is None
    )

    duplicates = conn.execute("""
        SELECT company, title, COUNT(*) as count
        FROM jobs
        GROUP BY company, title
        HAVING COUNT(*) > 1
    """).fetchall()

    print(f"Missing Company:        {missing_company}")
    print(f"Missing Title:          {missing_title}")
    print(f"Missing URL:            {missing_url}")
    print(f"Missing Date:           {missing_date}")
    print(f"Missing Match Score:    {missing_score}")
    print(f"Possible Duplicates:    {len(duplicates)}")

    print()
    print("Sample Jobs:")
    print("-" * 100)

    for i, job in enumerate(jobs[:10], 1):
        print(
            f"{i}. "
            f"{job['company']} | "
            f"{job['title']} | "
            f"{job['location']}"
        )

    print("=" * 100)


def normal_view(conn):
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

    print(f"\nTotal Jobs: {len(jobs)}")
    print("=" * 100)

    for i, job in enumerate(jobs, 1):
        print(f"\n#{i}")

        print(f"Company:     {job['company']}")
        print(f"Title:       {job['title']}")
        print(f"Location:    {job['location']}")
        print(f"Date Posted: {job['created_at']}")

        if job["similarity_score"] is not None:
            print(
                f"Match Score: {job['similarity_score']:.4f}"
            )
        else:
            print("Match Score: N/A")

        print(f"URL:         {job['url']}")
        print("-" * 100)


def main():
    parser = argparse.ArgumentParser(
        description="View JobPly jobs database"
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Show database debug information"
    )

    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)

    try:
        if args.all:
            debug_view(conn)
        else:
            normal_view(conn)

    finally:
        conn.close()


if __name__ == "__main__":
    main()