import re
import hashlib
from datetime import datetime

def generate_id(company, title, url):
    """
    Generates a deterministic ID. Using SHA256 ensures the ID stays 
    the same even if you restart the script.
    """
    value = f"{company}{title}{url}"
    return hashlib.sha256(value.encode('utf-8')).hexdigest()

def parse_readme(markdown):
    jobs = []
    lines = markdown.splitlines()
    
    # State tracking: remembers the company of the previous row
    last_known_company = None

    for line in lines:
        # Ignore non-table rows, headers, or separators
        if not line.startswith("|") or "Company" in line or "---" in line:
            continue

        # Split columns and strip whitespace
        columns = [x.strip() for x in line.split("|") if x.strip()]

        # Ensure the row has enough data (Company, Title, Location, Application, Date)
        if len(columns) < 5:
            continue

        raw_company = columns[0]
        title = columns[1]
        location = columns[2]
        application = columns[3]
        date = columns[4]

        # --- CONTEXT-AWARE LOGIC ---
        # If the company is "↳", it belongs to the previous company found.
        if raw_company == "↳":
            company = last_known_company if last_known_company else raw_company
        else:
            company = raw_company
            last_known_company = company
        # ---------------------------

        # Extract URL from HTML tag
        match = re.search(r'href="([^"]+)"', application)

        if match:
            url = match.group(1)
        else:
            match = re.search(r'\((https?://[^)]+)\)', application)
            url = match.group(1) if match else None

        # Prevent duplicate entries in the same parsing run
        job_id = generate_id(company, title, url)
        
        jobs.append({
            "github_id": job_id,
            "title": title,
            "company": company,
            "location": location,
            "url": url,
            "external_url": url,
            "description": (
                f"{title} at {company}. "
                f"Location: {location}"
            ),
            "created_at": date,
            "fetched_at": datetime.now().isoformat(),
            "etag": None,
        })

    return jobs