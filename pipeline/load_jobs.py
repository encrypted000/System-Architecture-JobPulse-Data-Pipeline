import pandas as pd
from pathlib import Path
from sqlalchemy import text
from database.db_connection import engine


def load_jobs():
    # read from already transformed CSV — no API call
    processed_path = Path("data/processed/jobs_clean.csv")

    if not processed_path.exists():
        raise FileNotFoundError(
            "jobs_clean.csv not found — run transform_jobs.py first"
        )

    df = pd.read_csv(processed_path, encoding="utf-8-sig")
    print(f"Rows in CSV: {len(df)}")

    # find which job_ids already exist in the database
    with engine.connect() as conn:
        existing = pd.read_sql(
            text("SELECT job_id FROM jobs"), conn
        )

    existing_ids = set(existing["job_id"].astype(str))
    new_df = df[~df["job_id"].astype(str).isin(existing_ids)]

    print(f"Already in DB:  {len(df) - len(new_df)} skipped")
    print(f"New rows to add: {len(new_df)}")

    if new_df.empty:
        print("Nothing new to load — database is already up to date.")
        return

    # only keep columns that exist in your schema
    db_columns = [
        "job_id", "job_title", "company_name", "location",
        "country", "region", "county", "city", "area_name",
        "category", "contract_type",
        "salary_min", "salary_max", "salary_avg", "salary_band",
        "salary_is_predicted", "salary_is_single_point",
        "seniority", "work_type", "skills_found", "skills_count",
        "posted_date", "posted_month", "days_since_posted",
        "latitude", "longitude",
        "source", "job_url", "description", "run_date"
    ]

    # only include columns that actually exist in the dataframe
    cols_to_load = [c for c in db_columns if c in new_df.columns]
    new_df = new_df[cols_to_load]

    # load into postgres
    new_df.to_sql(
        "jobs",
        con=engine,
        if_exists="append",
        index=False,
        method="multi",    # faster — sends multiple rows per INSERT
        chunksize=500      # commit in batches of 500
    )

    print(f"Successfully loaded {len(new_df)} new rows into jobs table.")


if __name__ == "__main__":
    load_jobs()
