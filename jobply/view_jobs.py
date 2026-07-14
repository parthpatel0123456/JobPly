import sqlite3

conn = sqlite3.connect("data/jobs.db")
conn.row_factory = sqlite3.Row

jobs = conn.execute("""
SELECT title, company, location, created_at, similarity_score, url
FROM jobs
ORDER BY 
    CASE 
        WHEN created_at LIKE 'Jul %' THEN CAST(substr(created_at, 5) AS INTEGER)
        ELSE 0
    END DESC
LIMIT 20
""").fetchall()

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