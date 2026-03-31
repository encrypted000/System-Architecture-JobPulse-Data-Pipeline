import os
import time
import json
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

load_dotenv()

APP_ID = os.getenv("ADZUNA_APP_ID")
APP_KEY = os.getenv("ADZUNA_APP_KEY")


def fetch_jobs(pages=100, max_days_old=7) -> pd.DataFrame:
    all_jobs = []
    raw_responses = []

    # retry up to 3 times on server errors with increasing wait
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=2,        # waits 2s, 4s, 8s between retries
        status_forcelist=[500, 502, 503, 504]
    )
    session.mount("https://", HTTPAdapter(max_retries=retry))

    print(f"Fetching IT jobs — last {max_days_old} days...")

    for page in range(1, pages + 1):
        url = f"https://api.adzuna.com/v1/api/jobs/gb/search/{page}"

        params = {
            "app_id": APP_ID,
            "app_key": APP_KEY,
            "results_per_page": 50,
            "category": "it-jobs",
            "max_days_old": max_days_old,
            "sort_by": "date",
            "salary_include_unknown": 1,
        }

        try:
            response = session.get(url, params=params, timeout=30)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(f"Page {page}: HTTP error — {e} — skipping")
            time.sleep(5)
            continue
        except requests.exceptions.RequestException as e:
            print(f"Page {page}: Request failed — {e} — skipping")
            time.sleep(5)
            continue

        data = response.json()
        results = data.get("results", [])

        if not results:
            print(f"Page {page}: no results — stopping early")
            break

        all_jobs.extend(results)
        raw_responses.append({"page": page, "response": data})

        total = data.get("count", "?")
        print(f"Page {page}: {len(results)} jobs (total available this week: {total})")

        time.sleep(1)

    # save raw JSON
    raw_folder = Path("data/raw")
    raw_folder.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_file = raw_folder / f"adzuna_it_jobs_{timestamp}.json"

    with open(raw_file, "w", encoding="utf-8") as f:
        json.dump(raw_responses, f, indent=2, ensure_ascii=False)

    print(f"Raw saved → {raw_file}")
    print(f"Total jobs fetched: {len(all_jobs)}")

    return pd.DataFrame(all_jobs)


if __name__ == "__main__":
    df = fetch_jobs(pages=100, max_days_old=7)
    print(df.head())