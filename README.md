@"
<div align="center">

# ⚡ JobPulse
### UK IT Job Market Intelligence Pipeline

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-2.0-150458?style=for-the-badge&logo=pandas&logoColor=white)

*A fully automated end-to-end data pipeline that tracks, analyses and visualises the UK IT job market — refreshed every week automatically.*

[View Dashboard](#dashboard) • [Architecture](#architecture) • [Setup](#setup) • [API Docs](#api)

---

</div>

## 🗺 Architecture

![System Architecture](images/System%20Architecture%20%E2%80%93%20JobPulse%20Data%20Pipeline.png)

---

## ✨ What It Does

| Feature | Details |
|---|---|
| 📥 **Data Ingestion** | Fetches up to 5,000 UK IT jobs weekly from Adzuna API |
| 🧹 **Data Cleaning** | Extracts skills, seniority, work type, salary bands from raw listings |
| 🗄 **Storage** | Appends new jobs weekly into PostgreSQL — builds historical dataset over time |
| ⚡ **API Layer** | FastAPI REST endpoints serving salary, skills and hiring trend data |
| 📊 **Dashboard** | Interactive Streamlit dashboard with Plotly charts |
| 🤖 **Automation** | Windows Task Scheduler runs the full pipeline every Monday at 10am |
| 📧 **Alerting** | Email notification on pipeline failure |

---

## 📊 Dashboard

> *Dark-themed analytics dashboard answering real business questions about the UK IT job market*

### Business Questions Answered
- 🏙 Which UK cities pay the most for IT roles?
- 🛠 What skills are most in demand right now?
- 📈 Is IT hiring increasing or decreasing?
- 💼 Does seniority significantly affect salary?
- 🌍 Are more IT jobs remote, hybrid or on-site?
- 🏢 Which companies are hiring the most?
- 💰 Do contract roles pay more than permanent?

---

## 🏗 Project Structure
```
jobpulse/
│
├── 📂 pipeline/
│   ├── fetch_jobs.py          # Adzuna API ingestion with retry logic
│   ├── transform_jobs.py      # cleaning, enrichment, skill extraction
│   └── load_jobs.py           # PostgreSQL upsert loader
│
├── 📂 api/
│   └── main.py                # FastAPI REST endpoints
│
├── 📂 dashboard/
│   └── streamlit_app.py       # interactive Streamlit dashboard
│
├── 📂 scheduler/
│   ├── run_pipeline.py        # orchestrates all pipeline steps
│   └── run_pipeline.ps1       # Windows Task Scheduler entry point
│
├── 📂 database/
│   └── db_connection.py       # SQLAlchemy engine setup
│
├── 📂 sql/
│   └── schema.sql             # PostgreSQL table schema
│
├── 📂 docker/
│   ├── Dockerfile.api         # FastAPI container
│   └── Dockerfile.streamlit   # Streamlit container
│
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | \`/jobs\` | All jobs with filters (city, seniority, work type) |
| GET | \`/jobs/top-skills\` | Most in-demand IT skills |
| GET | \`/jobs/salary-by-city\` | Average salary per UK city |
| GET | \`/jobs/salary-by-seniority\` | Junior vs Mid vs Senior vs Management pay |
| GET | \`/jobs/work-type\` | Remote vs Hybrid vs On-site breakdown |
| GET | \`/jobs/hiring-trends\` | Job volume by month |
| GET | \`/jobs/salary-bands\` | Salary band distribution |
| GET | \`/jobs/top-companies\` | Top hiring companies |
| GET | \`/jobs/contract-types\` | Permanent vs contract pay |

Interactive docs available at \`http://localhost:8000/docs\`

---

## ⚙️ Tech Stack

\`\`\`
Data Source      Adzuna Jobs API (UK)
Language         Python 3.11
ETL              Pandas, Requests
Database         PostgreSQL 16
ORM              SQLAlchemy
API              FastAPI + Uvicorn
Dashboard        Streamlit + Plotly
Scheduler        Windows Task Scheduler
Containerisation Docker + Docker Compose
Version Control  Git + GitHub
\`\`\`

---

## 🚀 Setup

### Prerequisites
- Python 3.11+
- PostgreSQL 16
- Adzuna API credentials — [register free here](https://developer.adzuna.com)

### 1 — Clone the repo
\`\`\`bash
git clone https://github.com/encrypted000/System-Architecture-JobPulse-Data-Pipeline.git
cd System-Architecture-JobPulse-Data-Pipeline
\`\`\`

### 2 — Create virtual environment
\`\`\`bash
python -m venv .venv
.venv\Scripts\activate       # Windows
pip install -r requirements.txt
\`\`\`

### 3 — Configure environment variables
\`\`\`bash
cp .env.example .env
\`\`\`
Edit \`.env\` with your credentials:
\`\`\`env
ADZUNA_APP_ID=your_app_id
ADZUNA_APP_KEY=your_app_key
DATABASE_URL=postgresql://user:password@localhost:5432/jobpulse
ALERT_EMAIL_FROM=your@gmail.com
ALERT_EMAIL_TO=your@gmail.com
ALERT_EMAIL_PASSWORD=your_app_password
\`\`\`

### 4 — Set up the database
\`\`\`bash
psql -U postgres -d jobpulse -f sql/schema.sql
\`\`\`

### 5 — Run the pipeline
\`\`\`bash
python -m pipeline.fetch_jobs
python -m pipeline.transform_jobs
python -m pipeline.load_jobs
\`\`\`

### 6 — Start API and dashboard
\`\`\`bash
# terminal 1
uvicorn api.main:app --reload

# terminal 2
streamlit run dashboard/streamlit_app.py
\`\`\`

---

## 🤖 Automation

The pipeline runs automatically every Monday at 10am via Windows Task Scheduler.

\`\`\`
Every Monday 10am
      ↓
Windows Task Scheduler triggers run_pipeline.ps1
      ↓
fetch_jobs.py    — pulls last 7 days from Adzuna API
      ↓
transform_jobs.py — cleans, enriches, detects skills & seniority
      ↓
load_jobs.py     — appends new jobs to PostgreSQL
      ↓
Streamlit dashboard shows fresh data automatically
      ↓
Email alert sent only if pipeline fails
\`\`\`

---

## 📦 Data Pipeline

\`\`\`
Adzuna API
    │
    ▼
data/raw/adzuna_it_jobs_TIMESTAMP.json     ← raw backup
    │
    ▼
transform_jobs.py
    │  • extract salary_min, salary_max, salary_avg
    │  • detect seniority from job title
    │  • detect work type from description
    │  • extract 30+ skills from description
    │  • parse location into city, region, county
    │  • assign salary band
    │
    ▼
data/processed/jobs_clean.csv              ← clean data
    │
    ▼
PostgreSQL jobs table                      ← historical store
    │
    ▼
FastAPI endpoints                          ← data access layer
    │
    ▼
Streamlit dashboard                        ← visualisation
\`\`\`

---

## 📄 License

MIT License — feel free to fork and build on this project.

---

<div align="center">

Built with ⚡ by [encrypted000](https://github.com/encrypted000)

</div>
"@ | Out-File -FilePath "G:\System Architecture – JobPulse Data Pipeline\README.md" -Encoding UTF8
