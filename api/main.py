from fastapi import FastAPI, Query
from sqlalchemy import text
from database.db_connection import engine
import pandas as pd

app = FastAPI(
    title="JobPulse API",
    description="UK IT Job Market Analytics API",
    version="1.0.0"
)


# ─── helper ───────────────────────────────────────────────────────────────────
def query_db(sql: str, params: dict = {}) -> list:
    with engine.connect() as conn:
        result = conn.execute(text(sql), params)
        rows = result.fetchall()
        keys = result.keys()
        return [dict(zip(keys, row)) for row in rows]


# ─── health check ─────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "ok", "message": "JobPulse API is running"}


# ─── all jobs ─────────────────────────────────────────────────────────────────
@app.get("/jobs")
def get_jobs(
    city:          str  = Query(None),
    seniority:     str  = Query(None),
    work_type:     str  = Query(None),
    contract_type: str  = Query(None),
    salary_band:   str  = Query(None),
    limit:         int  = Query(100, le=1000)
):
    filters = ["1=1"]
    params  = {}

    if city:
        filters.append("city ILIKE :city")
        params["city"] = f"%{city}%"
    if seniority:
        filters.append("seniority = :seniority")
        params["seniority"] = seniority
    if work_type:
        filters.append("work_type = :work_type")
        params["work_type"] = work_type
    if contract_type:
        filters.append("contract_type = :contract_type")
        params["contract_type"] = contract_type
    if salary_band:
        filters.append("salary_band = :salary_band")
        params["salary_band"] = salary_band

    where = " AND ".join(filters)

    sql = f"""
        SELECT job_id, job_title, company_name, city, region,
               category, contract_type, seniority, work_type,
               salary_min, salary_max, salary_avg, salary_band,
               skills_found, posted_date, job_url
        FROM jobs
        WHERE {where}
        ORDER BY posted_date DESC
        LIMIT :limit
    """
    params["limit"] = limit
    return query_db(sql, params)


# ─── top skills ───────────────────────────────────────────────────────────────
@app.get("/jobs/top-skills")
def top_skills(limit: int = Query(20, le=50)):
    sql = """
        SELECT skill, COUNT(*) as job_count
        FROM jobs,
             UNNEST(STRING_TO_ARRAY(skills_found, ', ')) AS skill
        WHERE skills_found != ''
        GROUP BY skill
        ORDER BY job_count DESC
        LIMIT :limit
    """
    return query_db(sql, {"limit": limit})


# ─── salary by city ───────────────────────────────────────────────────────────
@app.get("/jobs/salary-by-city")
def salary_by_city(limit: int = Query(15, le=50)):
    sql = """
        SELECT city,
               ROUND(AVG(salary_avg)) AS avg_salary,
               ROUND(MIN(salary_avg)) AS min_salary,
               ROUND(MAX(salary_avg)) AS max_salary,
               COUNT(*)               AS job_count
        FROM jobs
        WHERE salary_avg IS NOT NULL
          AND city IS NOT NULL
          AND city != 'UK (Nationwide)'
        GROUP BY city
        HAVING COUNT(*) > 5
        ORDER BY avg_salary DESC
        LIMIT :limit
    """
    return query_db(sql, {"limit": limit})


# ─── salary by seniority ──────────────────────────────────────────────────────
@app.get("/jobs/salary-by-seniority")
def salary_by_seniority():
    sql = """
        SELECT seniority,
               ROUND(AVG(salary_avg)) AS avg_salary,
               ROUND(MIN(salary_avg)) AS min_salary,
               ROUND(MAX(salary_avg)) AS max_salary,
               COUNT(*)               AS job_count
        FROM jobs
        WHERE salary_avg IS NOT NULL
          AND seniority != 'Unknown'
        GROUP BY seniority
        ORDER BY avg_salary DESC
    """
    return query_db(sql, {})


# ─── work type breakdown ──────────────────────────────────────────────────────
@app.get("/jobs/work-type")
def work_type_breakdown():
    sql = """
        SELECT work_type,
               COUNT(*) AS job_count,
               ROUND(AVG(salary_avg)) AS avg_salary
        FROM jobs
        GROUP BY work_type
        ORDER BY job_count DESC
    """
    return query_db(sql, {})


# ─── hiring trends by month ───────────────────────────────────────────────────
@app.get("/jobs/hiring-trends")
def hiring_trends():
    sql = """
        SELECT posted_month,
               COUNT(*)               AS job_count,
               ROUND(AVG(salary_avg)) AS avg_salary
        FROM jobs
        WHERE posted_month IS NOT NULL
        GROUP BY posted_month
        ORDER BY posted_month ASC
    """
    return query_db(sql, {})


# ─── salary band breakdown ────────────────────────────────────────────────────
@app.get("/jobs/salary-bands")
def salary_bands():
    sql = """
        SELECT salary_band,
               COUNT(*) AS job_count
        FROM jobs
        GROUP BY salary_band
        ORDER BY job_count DESC
    """
    return query_db(sql, {})


# ─── top hiring companies ─────────────────────────────────────────────────────
@app.get("/jobs/top-companies")
def top_companies(limit: int = Query(10, le=50)):
    sql = """
        SELECT company_name,
               COUNT(*)               AS job_count,
               ROUND(AVG(salary_avg)) AS avg_salary
        FROM jobs
        WHERE company_name != 'Unknown Company'
        GROUP BY company_name
        ORDER BY job_count DESC
        LIMIT :limit
    """
    return query_db(sql, {"limit": limit})


# ─── contract type breakdown ──────────────────────────────────────────────────
@app.get("/jobs/contract-types")
def contract_types():
    sql = """
        SELECT contract_type,
               COUNT(*)               AS job_count,
               ROUND(AVG(salary_avg)) AS avg_salary
        FROM jobs
        GROUP BY contract_type
        ORDER BY job_count DESC
    """
    return query_db(sql, {})