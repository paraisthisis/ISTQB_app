#!/usr/bin/env python3
"""
ingestion/scrape.py
Downloads the ISTQB CTFL v4.0.1 Syllabus PDF and Sample Exam PDFs.
Files are saved to data/raw/.
"""

import os
import sys
import requests

# Official ISTQB document URLs (publicly available)
DOCUMENTS = [
    {
        "name": "CTFL-v4.0.1-Syllabus.pdf",
        "url": "https://www.istqb.org/certifications/certified-tester-foundation-level",
        "description": "CTFL v4.0.1 Syllabus"
    },
    {
        "name": "CTFL-Sample-Exam-A.pdf",
        "url": "https://www.istqb.org/certifications/certified-tester-foundation-level",
        "description": "CTFL Sample Exam A"
    }
]

RAW_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw")


def download_file(url: str, dest_path: str, name: str) -> bool:
    """Attempt to download a file. Returns True on success."""
    print(f"  Downloading {name}...")
    try:
        resp = requests.get(url, timeout=30, headers={
            "User-Agent": "Mozilla/5.0 (compatible; ISTQB-StudyApp/1.0)"
        })
        resp.raise_for_status()
        with open(dest_path, "wb") as f:
            f.write(resp.content)
        size_kb = len(resp.content) // 1024
        print(f"  ✓ Saved {name} ({size_kb} KB)")
        return True
    except requests.RequestException as e:
        print(f"  ✗ Failed to download {name}: {e}")
        return False


def main():
    os.makedirs(RAW_DIR, exist_ok=True)
    print(f"Download directory: {RAW_DIR}\n")

    success_count = 0
    for doc in DOCUMENTS:
        dest = os.path.join(RAW_DIR, doc["name"])
        if os.path.exists(dest):
            print(f"  ✓ {doc['name']} already exists, skipping.")
            success_count += 1
            continue
        if download_file(doc["url"], dest, doc["description"]):
            success_count += 1

    print(f"\nDownloaded {success_count}/{len(DOCUMENTS)} documents.")
    print("\nNOTE: ISTQB PDFs are protected behind a registration wall.")
    print("If download failed, manually place PDFs in data/raw/")
    print("The app will work without PDFs — it uses JSON seed data instead.")


if __name__ == "__main__":
    main()
