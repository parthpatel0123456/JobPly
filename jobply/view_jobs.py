import sqlite3

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