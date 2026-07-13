import re
import hashlib
from datetime import datetime


def generate_id(company, title, url):
    value = f"{company}{title}{url}"
    return abs(hash(value))


def parse_readme(markdown):
    jobs = []

    lines = markdown.splitlines()

    for line in lines:

        # Ignore headers/separators
        if not line.startswith("|"):
            continue

        if "Company" in line:
            continue

        if "---" in line:
            continue

        columns = [
            x.strip()
            for x in line.split("|")
        ]

        # remove empty first/last column
        columns = [
            x for x in columns
            if x
        ]

        if len(columns) < 5:
            continue


        company = columns[0]
        title = columns[1]
        location = columns[2]
        application = columns[3]
        date = columns[4]


        # extract URL
        match = re.search(
            r'href="([^"]+)"',
            application
        )

        if match:
            url = match.group(1)
        else:
            continue


        jobs.append({
            "github_id": generate_id(
                company,
                title,
                url
            ),
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