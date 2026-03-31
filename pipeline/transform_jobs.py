import json
import re
import pandas as pd
from pathlib import Path
from datetime import datetime


def load_latest_raw() -> pd.DataFrame:
    base_dir = Path(__file__).resolve().parent.parent
    raw_folder = base_dir / "data" / "raw"

    raw_files = list(raw_folder.glob("adzuna_*.json"))

    if not raw_files:
        raise FileNotFoundError(f"No raw JSON files found in {raw_folder}")

    # sort by actual file modification time — always gets the newest file
    latest_file = max(raw_files, key=lambda f: f.stat().st_mtime)
    print(f"Loading: {latest_file.name}")

    with open(latest_file, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    all_jobs = []
    for page_obj in raw_data:
        results = page_obj.get("response", {}).get("results", [])
        all_jobs.extend(results)

    print(f"Jobs loaded from JSON: {len(all_jobs)}")
    return pd.DataFrame(all_jobs)


def transform_jobs(df: pd.DataFrame, run_date=None) -> pd.DataFrame:
    transformed = pd.DataFrame()

    # --- core fields ---
    transformed["job_id"]   = df["id"]
    transformed["job_title"] = df["title"]
    transformed["job_url"]  = df["redirect_url"]
    transformed["description"] = df["description"]

    # --- salary ---
    transformed["salary_min"] = pd.to_numeric(df.get("salary_min"), errors="coerce")
    transformed["salary_max"] = pd.to_numeric(df.get("salary_max"), errors="coerce")

    # if both exist → average them
    # if only one exists → use that one
    # if neither exists → null
    transformed["salary_avg"] = transformed.apply(
        lambda row:
            (row["salary_min"] + row["salary_max"]) / 2
            if pd.notna(row["salary_min"]) and pd.notna(row["salary_max"])
            else row["salary_min"]
            if pd.notna(row["salary_min"])
            else row["salary_max"]
            if pd.notna(row["salary_max"])
            else None,
        axis=1
    )

    # salary_is_predicted comes as string "1" or "0" — convert to clean boolean
    transformed["salary_is_predicted"] = (
        df.get("salary_is_predicted")
        .astype(str)
        .str.strip()
        .map({"1": True, "0": False})
    )

    # flag jobs where salary_min == salary_max — Adzuna is guessing a single number
    # not a real salary range — useful to filter in analysis
    transformed["salary_is_single_point"] = (
        transformed["salary_min"] == transformed["salary_max"]
    )

    # --- contract ---
    # contract_type is only present on some jobs
    # missing means permanent in most cases
    transformed["contract_type"] = (
        df.get("contract_type")
          .fillna("permanent")
          .str.lower()
          .str.strip()
    )

    # --- location ---
    transformed["latitude"]  = pd.to_numeric(df.get("latitude"),  errors="coerce")
    transformed["longitude"] = pd.to_numeric(df.get("longitude"), errors="coerce")

    transformed["location"] = df["location"].apply(
        lambda x: x.get("display_name") if isinstance(x, dict) else None
    )

    location_area = df["location"].apply(
        lambda x: x.get("area", []) if isinstance(x, dict) else []
    )

    transformed["country"]   = location_area.apply(lambda x: x[0] if len(x) > 0 else None)
    transformed["region"]    = location_area.apply(lambda x: x[1] if len(x) > 1 else None)
    transformed["county"]    = location_area.apply(lambda x: x[2] if len(x) > 2 else None)
    transformed["area_name"] = location_area.apply(lambda x: x[4] if len(x) > 4 else None)

    LONDON_DISTRICTS = {
        "the city", "farringdon", "canary wharf", "shoreditch",
        "islington", "hackney", "southwark", "lambeth", "wandsworth",
        "hammersmith", "kensington", "westminster", "camden"
    }

    COUNTRY_LEVEL = {"uk", "united kingdom", "england", "scotland", "wales", "britain"}

    REGION_NATIONWIDE = {
        "scotland": "Scotland (Nationwide)",
        "wales": "Wales (Nationwide)",
        "northern ireland": "Northern Ireland (Nationwide)",
    }

    def extract_city(row):
        area    = row["area"] if isinstance(row["area"], list) else []
        display = row["display_name"] if isinstance(row["display_name"], str) else ""

        # only country level e.g. ["UK"] → nationwide
        if len(area) == 1 and area[0].lower() in COUNTRY_LEVEL:
            return "UK (Nationwide)"

        # region is London → always London
        if len(area) > 1 and area[1].lower() == "london":
            return "London"

        # region level e.g. ["UK", "Scotland"] → nationwide region
        if len(area) == 2 and area[1].lower() in REGION_NATIONWIDE:
            return REGION_NATIONWIDE[area[1].lower()]

        # normal case → city is area[3]
        city = area[3] if len(area) > 3 else None

        # known London district → normalize to London
        if city and city.lower() in LONDON_DISTRICTS:
            return "London"

        # no city → fall back to county
        if city is None and len(area) > 2:
            return area[2]

        # no county either → try display_name first part
        if city is None and display:
            first_part = display.split(",")[0].strip()
            if first_part.lower() not in COUNTRY_LEVEL:
                return first_part

        return city

    location_df  = df["location"].apply(
        lambda x: {
            "area":         x.get("area", [])         if isinstance(x, dict) else [],
            "display_name": x.get("display_name", "") if isinstance(x, dict) else ""
        }
    )

    location_area        = location_df.apply(lambda x: x["area"])
    transformed["city"]  = location_df.apply(extract_city)

    # --- company ---
    transformed["company_name"] = df["company"].apply(
        lambda x: x.get("display_name") if isinstance(x, dict) else None
    )

    # --- category ---
    transformed["category"] = df["category"].apply(
        lambda x: x.get("label") if isinstance(x, dict) else None
    )

    # --- dates ---
    transformed["posted_date"] = pd.to_datetime(
        df["created"], errors="coerce"
    ).dt.date

    transformed["posted_month"] = pd.to_datetime(
        df["created"], errors="coerce"
    ).dt.tz_localize(None).dt.to_period("M").astype(str)  #useful for monthly trend charts

    transformed["days_since_posted"] = (
        pd.Timestamp.now() - pd.to_datetime(df["created"], errors="coerce").dt.tz_localize(None)
    ).dt.days

    transformed["run_date"] = run_date or datetime.now().date()

    # --- seniority from title ---
    def detect_seniority(title):
        if not isinstance(title, str):
            return "Unknown"
        t = title.lower()
        if any(w in t for w in ["senior", "sr.", "lead", "principal", "staff", "head of"]):
            return "Senior"
        elif any(w in t for w in ["junior", "jr.", "graduate", "entry", "trainee", "apprentice"]):
            return "Junior"
        elif any(w in t for w in ["manager", "director", "vp", "chief", "cto", "cio"]):
            return "Management"
        return "Mid"

    transformed["seniority"] = df["title"].apply(detect_seniority)

    # --- work type from title + description ---
    def detect_work_type(row):
        text = f"{row.get('title', '')} {row.get('description', '')}".lower()
        
        remote_keywords = [
            "remote", "work from home", "wfh", "fully remote",
            "home based", "home-based", "anywhere in the uk",
            "remote first", "remote-first", "distributed team"
        ]
        
        hybrid_keywords = [
            "hybrid", "flexible working", "blend of home",
            "mix of office", "part remote", "partially remote",
            "2 days", "3 days", "days per week in",
            "days a week in", "days in the office",
            "home and office", "office and home"
        ]
        
        onsite_keywords = [
            "on-site", "onsite", "on site", "fully office",
            "office based", "office-based", "in the office",
            "must be based", "required to be in",
            "no remote", "not remote"
        ]

        # order matters — check remote first, then hybrid, then onsite
        if any(k in text for k in remote_keywords):
            return "Remote"
        elif any(k in text for k in hybrid_keywords):
            return "Hybrid"
        elif any(k in text for k in onsite_keywords):
            return "On-site"
        return "Not Specified"

    transformed["work_type"] = df[["title", "description"]].apply(detect_work_type, axis=1)

    # --- skills from description ---
    SKILLS = [
        "Python", "SQL", "Java", "JavaScript", "TypeScript", "C#", "C++", "R",
        "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform", "Linux",
        "React", "Node.js", "Django", "FastAPI", "Flask", "Spring",
        "Machine Learning", "Deep Learning", "NLP", "LLM",
        "Power BI", "Tableau", "Excel", "Looker",
        "PostgreSQL", "MySQL", "MongoDB", "Redis", "Snowflake",
        "Spark", "Airflow", "dbt", "Kafka", "Git", "CI/CD",
        "SAP", "GDPR", "Agile", "Scrum"
    ]

    def extract_skills(desc):
        if not isinstance(desc, str):
            return ""
        found = []
        for skill in SKILLS:
            # use word boundary for short skills to avoid false matches
            if len(skill) <= 2:
                pattern = rf'\b{re.escape(skill)}\b'
                if re.search(pattern, desc, re.IGNORECASE):
                    found.append(skill)
            else:
                if skill.lower() in desc.lower():
                    found.append(skill)
        return ", ".join(found)

    transformed["skills_found"] = df["description"].apply(extract_skills)

    transformed["skills_count"] = transformed["skills_found"].apply(
        lambda x: len(x.split(", ")) if x else 0
    )

    # --- clean salary range label for charts ---
    def salary_band(avg):
        if pd.isna(avg):
            return "Unknown"
        elif avg < 25000:
            return "Under 25k"
        elif avg < 40000:
            return "25k–40k"
        elif avg < 60000:
            return "40k–60k"
        elif avg < 80000:
            return "60k–80k"
        elif avg < 100000:
            return "80k–100k"
        else:
            return "100k+"

    transformed["salary_band"] = transformed["salary_avg"].apply(salary_band)

    # --- fill nulls ---
    transformed = transformed.fillna({
        "company_name": "Unknown Company",
        "location":     "Unknown Location",
        "category":     "Unknown Category",
        "contract_type": "permanent",
        "skills_found":  "",
        "skills_count":  0,
        "seniority":     "Unknown",
        "work_type":     "Not Specified",
        "salary_band":   "Unknown"
    })

    # --- deduplicate ---
    before = len(transformed)
    transformed = transformed.drop_duplicates(subset=["job_id"])
    after = len(transformed)
    if before != after:
        print(f"Duplicates removed: {before - after}")

    # --- save / append ---
    processed_folder = Path("data/processed")
    processed_folder.mkdir(parents=True, exist_ok=True)
    output_path = processed_folder / "jobs_clean.csv"

    if output_path.exists():
        existing = pd.read_csv(output_path, encoding="utf-8-sig")
        
        # find truly new jobs this week
        existing_ids = set(existing["job_id"].astype(str))
        new_jobs = transformed[~transformed["job_id"].astype(str).isin(existing_ids)]
        
        print(f"This week:     {len(transformed)} jobs fetched")
        print(f"Already in DB: {len(transformed) - len(new_jobs)} duplicates skipped")
        print(f"Truly new:     {len(new_jobs)} new jobs added")
        
        combined = pd.concat([existing, new_jobs], ignore_index=True)
        combined.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"Total in CSV:  {len(combined)} rows")
    else:
        transformed.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"Created jobs_clean.csv with {len(transformed)} rows")

    return transformed


if __name__ == "__main__":
    raw_df   = load_latest_raw()
    clean_df = transform_jobs(raw_df)

    print(clean_df.head())
    print(clean_df.columns.tolist())
    print("Rows transformed:", len(clean_df))