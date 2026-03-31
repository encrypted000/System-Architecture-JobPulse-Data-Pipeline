import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

API_BASE = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="JobPulse — UK IT Job Market",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #0a0a0f;
    color: #e8e8f0;
}

/* sidebar */
[data-testid="stSidebar"] {
    background: #0f0f1a !important;
    border-right: 1px solid #1e1e2e;
}
[data-testid="stSidebar"] * { color: #e8e8f0 !important; }

/* main background */
[data-testid="stAppViewContainer"] { background: #0a0a0f; }
[data-testid="stHeader"] { background: #0a0a0f; }

/* metric cards */
[data-testid="metric-container"] {
    background: #0f0f1a;
    border: 1px solid #1e1e2e;
    border-radius: 12px;
    padding: 20px 24px;
    transition: border-color 0.2s;
}
[data-testid="metric-container"]:hover { border-color: #00d4aa; }
[data-testid="stMetricValue"] {
    font-family: 'Syne', sans-serif !important;
    font-size: 2rem !important;
    font-weight: 700 !important;
    color: #00d4aa !important;
}
[data-testid="stMetricLabel"] {
    font-size: 0.75rem !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    color: #6b6b8a !important;
}

/* section headers */
h1 {
    font-family: 'Syne', sans-serif !important;
    font-size: 2.4rem !important;
    font-weight: 800 !important;
    color: #ffffff !important;
    letter-spacing: -0.02em !important;
}
h2, h3 {
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    color: #ffffff !important;
}

/* chart containers */
[data-testid="stPlotlyChart"] {
    background: #0f0f1a;
    border: 1px solid #1e1e2e;
    border-radius: 12px;
    padding: 8px;
}

/* selectbox */
[data-testid="stSelectbox"] > div > div {
    background: #0f0f1a !important;
    border: 1px solid #1e1e2e !important;
    border-radius: 8px !important;
    color: #e8e8f0 !important;
}

/* dataframe */
[data-testid="stDataFrame"] {
    border: 1px solid #1e1e2e;
    border-radius: 12px;
}

/* divider */
hr { border-color: #1e1e2e !important; }

/* caption */
.caption-text {
    font-size: 0.78rem;
    color: #6b6b8a;
    margin-bottom: 12px;
    letter-spacing: 0.02em;
}

/* accent pill */
.pill {
    display: inline-block;
    background: #00d4aa18;
    color: #00d4aa;
    border: 1px solid #00d4aa40;
    border-radius: 100px;
    padding: 2px 12px;
    font-size: 0.72rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    font-weight: 500;
}
</style>
""", unsafe_allow_html=True)

# ─── plotly theme ─────────────────────────────────────────────────────────────
CHART_BG    = "#0f0f1a"
GRID_COLOR  = "#1e1e2e"
TEXT_COLOR  = "#e8e8f0"
ACCENT      = "#00d4aa"
PALETTE     = ["#00d4aa", "#7c6cf5", "#f5756c", "#f5c842", "#4299e1", "#ed64a6"]
TEAL_SCALE  = ["#0f3d35", "#1a6b5a", "#00d4aa", "#5eecd4", "#c0fff5"]

def chart_layout(fig, height=400):
    fig.update_layout(
        paper_bgcolor=CHART_BG,
        plot_bgcolor=CHART_BG,
        font=dict(family="DM Sans", color=TEXT_COLOR, size=12),
        height=height,
        margin=dict(l=12, r=12, t=24, b=12),
        xaxis=dict(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR),
        yaxis=dict(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR),
        legend=dict(
            bgcolor="#0f0f1a",
            bordercolor="#1e1e2e",
            borderwidth=1
        )
    )
    return fig


# ─── data fetching ────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def fetch(endpoint, params={}):
    try:
        r = requests.get(f"{API_BASE}{endpoint}", params=params, timeout=10)
        r.raise_for_status()
        return pd.DataFrame(r.json())
    except Exception as e:
        st.error(f"API error: {e}")
        return pd.DataFrame()


# ─── sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding: 8px 0 24px'>
        <div style='font-family:Syne,sans-serif;font-size:1.5rem;font-weight:800;color:#fff'>
            ⚡ JobPulse
        </div>
        <div style='font-size:0.75rem;color:#6b6b8a;letter-spacing:0.06em;
                    text-transform:uppercase;margin-top:4px'>
            UK IT Market Intelligence
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**Filters**")

    cities      = ["All","London","Manchester","Birmingham","Leeds",
                   "Edinburgh","Bristol","Cambridge","Reading","Sheffield"]
    seniorities = ["All","Junior","Mid","Senior","Management"]
    work_types  = ["All","Remote","Hybrid","On-site","Not Specified"]
    contracts   = ["All","permanent","contract"]

    city_f     = st.selectbox("City",          cities)
    seniority_f= st.selectbox("Seniority",     seniorities)
    work_f     = st.selectbox("Work Type",     work_types)
    contract_f = st.selectbox("Contract",      contracts)

    filters = {}
    if city_f      != "All": filters["city"]          = city_f
    if seniority_f != "All": filters["seniority"]     = seniority_f
    if work_f      != "All": filters["work_type"]     = work_f
    if contract_f  != "All": filters["contract_type"] = contract_f

    st.divider()
    st.markdown("""
    <div style='font-size:0.72rem;color:#6b6b8a'>
        Data sourced from Adzuna API<br>
        Refreshed weekly every Monday
    </div>
    """, unsafe_allow_html=True)


# ─── fetch all data ───────────────────────────────────────────────────────────
jobs_df      = fetch("/jobs",                    {**filters, "limit": 1000})
skills_df    = fetch("/jobs/top-skills")
city_df      = fetch("/jobs/salary-by-city")
seniority_df = fetch("/jobs/salary-by-seniority")
work_df      = fetch("/jobs/work-type")
trends_df    = fetch("/jobs/hiring-trends")
bands_df     = fetch("/jobs/salary-bands")
companies_df = fetch("/jobs/top-companies")
contracts_df = fetch("/jobs/contract-types")

# fix trends — only show 2026 data
if not trends_df.empty and "posted_month" in trends_df.columns:
    trends_df = trends_df[trends_df["posted_month"] >= "2026"]


# ─── header ───────────────────────────────────────────────────────────────────
st.markdown("""
<div style='padding: 32px 0 8px'>
    <span class='pill'>Live Dashboard</span>
    <h1 style='margin: 12px 0 4px'>UK IT Job Market</h1>
    <p style='color:#6b6b8a;font-size:0.95rem;margin:0'>
        Real-time analytics on salary, skills, hiring trends and more — powered by Adzuna
    </p>
</div>
""", unsafe_allow_html=True)

st.divider()


# ─── KPI row ──────────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    st.metric("Total Jobs", f"{len(jobs_df):,}" if not jobs_df.empty else "—")
with c2:
    if not jobs_df.empty and "salary_avg" in jobs_df.columns:
        avg = jobs_df["salary_avg"].dropna().mean()
        st.metric("Avg Salary", f"£{avg:,.0f}")
    else:
        st.metric("Avg Salary", "—")
with c3:
    if not jobs_df.empty and "salary_avg" in jobs_df.columns:
        med = jobs_df["salary_avg"].dropna().median()
        st.metric("Median Salary", f"£{med:,.0f}")
    else:
        st.metric("Median Salary", "—")
with c4:
    if not companies_df.empty:
        st.metric("Top Hiring Co.", companies_df.iloc[0]["company_name"])
    else:
        st.metric("Top Hiring Co.", "—")
with c5:
    if not skills_df.empty:
        st.metric("Most Wanted Skill", skills_df.iloc[0]["skill"])
    else:
        st.metric("Most Wanted Skill", "—")

st.divider()


# ─── row 1: salary by city + top skills ───────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.markdown("### Salary by City")
    st.markdown('<p class="caption-text">Which UK cities pay the most for IT roles?</p>',
                unsafe_allow_html=True)
    if not city_df.empty:
        fig = px.bar(
            city_df.head(10), x="avg_salary", y="city",
            orientation="h",
            color="avg_salary",
            color_continuous_scale=["#e0f7f3", "#80e8d4", "#00d4aa"],
            text="avg_salary"
        )
        fig.update_traces(
            texttemplate="£%{text:,.0f}",
            textposition="inside",
            textfont=dict(color="#0a0a0f", size=11, family="DM Sans"),
            marker_line_width=0
        )
        fig.update_coloraxes(showscale=False)
        fig.update_yaxes(
            categoryorder="total ascending",
            title="",
            tickfont=dict(size=12, color=TEXT_COLOR)
        )
        fig.update_xaxes(
            title="Average Salary (£)",
            tickprefix="£",
            tickformat=",",
            tickfont=dict(color=TEXT_COLOR)
        )
        fig.update_layout(
            margin=dict(l=130, r=30, t=20, b=40),
            paper_bgcolor=CHART_BG,
            plot_bgcolor=CHART_BG,
            font=dict(family="DM Sans", color=TEXT_COLOR),
            height=430
        )
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("### Top 10 In-Demand Skills")
    st.markdown('<p class="caption-text">What skills should IT professionals prioritise right now?</p>',
                unsafe_allow_html=True)
    if not skills_df.empty:
        plot_skills = skills_df[skills_df["skill"] != "R"].head(10).copy()

        # fix C# label — replace # with unicode to prevent vertical rendering
        plot_skills["skill"] = plot_skills["skill"].str.replace(
            "C#", "C\u266f", regex=False
        )

        fig = px.bar(
            plot_skills, x="job_count", y="skill",
            orientation="h",
            color="job_count",
            color_continuous_scale=["#ede9ff", "#b8aefc", "#7c6cf5"],
            text="job_count"
        )
        fig.update_traces(
            textposition="inside",
            textfont=dict(color="#0a0a0f", size=11, family="DM Sans"),
            marker_line_width=0
        )
        fig.update_coloraxes(showscale=False)
        fig.update_yaxes(
            categoryorder="total ascending",
            title="",
            tickfont=dict(size=12, color=TEXT_COLOR)
        )
        fig.update_xaxes(
            title="Number of Jobs",
            tickformat=",",
            tickfont=dict(color=TEXT_COLOR)
        )
        fig.update_layout(
            margin=dict(l=120, r=30, t=20, b=40),
            paper_bgcolor=CHART_BG,
            plot_bgcolor=CHART_BG,
            font=dict(family="DM Sans", color=TEXT_COLOR),
            height=430
        )
        st.plotly_chart(fig, use_container_width=True)


# ─── row 2: hiring trends + salary bands ──────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.markdown("### Hiring Trends — 2026")
    st.markdown('<p class="caption-text">Is IT hiring increasing or decreasing month on month?</p>',
                unsafe_allow_html=True)
    if not trends_df.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=trends_df["posted_month"],
            y=trends_df["job_count"],
            mode="lines+markers",
            line=dict(color=ACCENT, width=2.5),
            marker=dict(color=ACCENT, size=8,
                        line=dict(color="#0a0a0f", width=2)),
            fill="tozeroy",
            fillcolor="rgba(0, 212, 170, 0.08)",
            name="Jobs Posted"
        ))
        chart_layout(fig, 380)
        fig.update_xaxes(title="Month")
        fig.update_yaxes(title="Jobs Posted")
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("### Salary Band Distribution")
    st.markdown('<p class="caption-text">What salary range do most IT jobs fall into?</p>',
                unsafe_allow_html=True)
    if not bands_df.empty:
        # remove Unknown and sort manually by salary order
        order = ["Under 25k", "25k\u201340k", "40k\u201360k", 
                 "60k\u201380k", "80k\u2013100k", "100k+"]
        plot_bands = bands_df[bands_df["salary_band"] != "Unknown"].copy()
        plot_bands["salary_band"] = pd.Categorical(
            plot_bands["salary_band"], categories=order, ordered=True
        )
        plot_bands = plot_bands.sort_values("salary_band")
        fig = px.bar(
            plot_bands,
            x="salary_band", y="job_count",
            color="salary_band",
            color_discrete_sequence=PALETTE,
            text="job_count"
        )
        fig.update_traces(
            textposition="outside",
            textfont=dict(color=TEXT_COLOR),
            marker_line_width=0
        )
        fig.update_layout(showlegend=False)
        fig.update_xaxes(title="Salary Band")
        fig.update_yaxes(title="Number of Jobs")
        chart_layout(fig, 380)
        st.plotly_chart(fig, use_container_width=True)


# ─── row 3: seniority + work type ─────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.markdown("### Salary by Seniority")
    st.markdown('<p class="caption-text">Does career level significantly affect IT pay?</p>',
                unsafe_allow_html=True)
    if not seniority_df.empty:
        order = ["Junior", "Mid", "Senior", "Management"]
        sen = seniority_df[seniority_df["seniority"].isin(order)].copy()
        sen["seniority"] = pd.Categorical(
            sen["seniority"], categories=order, ordered=True
        )
        sen = sen.sort_values("seniority")
        fig = px.bar(
            sen, x="seniority", y="avg_salary",
            color="seniority",
            color_discrete_sequence=PALETTE,
            text="avg_salary"
        )
        fig.update_traces(
            texttemplate="£%{text:,.0f}",
            textposition="outside",
            textfont=dict(color=TEXT_COLOR),
            marker_line_width=0
        )
        fig.update_layout(showlegend=False)
        fig.update_xaxes(title="")
        fig.update_yaxes(title="Average Salary (£)")
        chart_layout(fig, 380)
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("### Work Type Breakdown")
    st.markdown('<p class="caption-text">Are more IT jobs remote, hybrid or on-site?</p>',
                unsafe_allow_html=True)
    if not work_df.empty:
        work_filtered = work_df[work_df["work_type"] != "Not Specified"].copy()
        fig = px.pie(
            work_filtered, names="work_type", values="job_count",
            color_discrete_sequence=PALETTE,
            hole=0.55
        )
        fig.update_traces(
            textfont=dict(color=TEXT_COLOR, size=12),
            marker=dict(line=dict(color=CHART_BG, width=3))
        )
        fig.update_layout(
            legend=dict(
                bgcolor=CHART_BG,
                bordercolor=GRID_COLOR,
                borderwidth=1,
                font=dict(color=TEXT_COLOR)
            )
        )
        chart_layout(fig, 380)
        st.plotly_chart(fig, use_container_width=True)


# ─── row 4: top companies + contract ──────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.markdown("### Top Hiring Companies")
    st.markdown('<p class="caption-text">Which companies are posting the most IT jobs?</p>',
                unsafe_allow_html=True)
    if not companies_df.empty:
        fig = px.bar(
            companies_df.head(10),
            x="job_count", y="company_name",
            orientation="h",
            color="avg_salary",
            color_continuous_scale=TEAL_SCALE,
            text="job_count",
            labels={"avg_salary": "Avg Salary (£)"}
        )
        fig.update_traces(
            textposition="outside",
            textfont=dict(color=TEXT_COLOR, size=11),
            marker_line_width=0
        )
        fig.update_yaxes(categoryorder="total ascending", title="")
        fig.update_xaxes(title="Jobs Posted")
        chart_layout(fig, 430)
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("### Permanent vs Contract Pay")
    st.markdown('<p class="caption-text">Do contract roles pay more than permanent positions?</p>',
                unsafe_allow_html=True)
    if not contracts_df.empty:
        # add difference annotation
        perm = contracts_df[contracts_df["contract_type"] == "permanent"]["avg_salary"].values
        cont = contracts_df[contracts_df["contract_type"] == "contract"]["avg_salary"].values
        
        fig = px.bar(
            contracts_df,
            x="contract_type", y="avg_salary",
            color="contract_type",
            color_discrete_map={
                "permanent": "#00d4aa",
                "contract":  "#7c6cf5"
            },
            text="avg_salary",
            labels={"avg_salary": "Average Salary (£)", "contract_type": ""},
        )
        fig.update_traces(
            texttemplate="£%{text:,.0f}",
            textposition="outside",
            textfont=dict(color=TEXT_COLOR, size=13, family="DM Sans"),
            marker_line_width=0,
            width=0.4           # ← narrower bars, less blocky
        )

        # add difference annotation
        if len(perm) > 0 and len(cont) > 0:
            diff = cont[0] - perm[0]
            fig.add_annotation(
                x=1, y=cont[0] / 2,
                text=f"+£{diff:,.0f}<br>more",
                showarrow=False,
                font=dict(color="#f5c842", size=13, family="Syne"),
                bgcolor="rgba(245, 200, 66, 0.12)",
                bordercolor="rgba(245, 200, 66, 0.8)",
                borderwidth=1,
                borderpad=6,
                xshift=80
            )

        fig.update_layout(
            showlegend=False,
            margin=dict(l=20, r=100, t=40, b=20),
            paper_bgcolor=CHART_BG,
            plot_bgcolor=CHART_BG,
            font=dict(family="DM Sans", color=TEXT_COLOR),
            height=430,
            yaxis=dict(
                gridcolor=GRID_COLOR,
                tickprefix="£",
                tickformat=",",
                title="Average Salary (£)"
            ),
            xaxis=dict(
                gridcolor=GRID_COLOR,
                tickfont=dict(size=13)
            )
        )
        st.plotly_chart(fig, use_container_width=True)


# ─── jobs table ───────────────────────────────────────────────────────────────
st.divider()
st.markdown("### Job Listings")
st.markdown(f'<p class="caption-text">Showing {len(jobs_df):,} jobs based on your filters</p>',
            unsafe_allow_html=True)

if not jobs_df.empty:
    cols = ["job_title", "company_name", "city", "seniority",
            "work_type", "contract_type", "salary_avg", "salary_band", "posted_date"]
    cols = [c for c in cols if c in jobs_df.columns]
    display_df = jobs_df[cols].copy().head(100)

    display_df["salary_avg"] = display_df["salary_avg"].apply(
        lambda x: f"£{x:,.0f}" if pd.notna(x) else "—"
    )
    display_df["contract_type"] = display_df["contract_type"].str.capitalize()

    seniority_badge = {
        "Junior": "🟢 Junior", "Mid": "🔵 Mid",
        "Senior": "🟣 Senior", "Management": "🟡 Management", "Unknown": "⚪ Unknown"
    }
    work_badge = {
        "Remote": "🌍 Remote", "Hybrid": "🔀 Hybrid",
        "On-site": "🏢 On-site", "Not Specified": "— N/A"
    }
    display_df["seniority"] = display_df["seniority"].map(lambda x: seniority_badge.get(x, x))
    display_df["work_type"] = display_df["work_type"].map(lambda x: work_badge.get(x, x))
    display_df["posted_date"] = pd.to_datetime(
        display_df["posted_date"], errors="coerce"
    ).dt.strftime("%d %b %Y")

    display_df = display_df.rename(columns={
        "job_title":     "Title",
        "company_name":  "Company",
        "city":          "City",
        "seniority":     "Seniority",
        "work_type":     "Work Type",
        "contract_type": "Contract",
        "salary_avg":    "Salary",
        "salary_band":   "Band",
        "posted_date":   "Posted"
    })

    # render as HTML table — full control over styling
    def render_table(df):
        rows = ""
        for _, row in df.iterrows():
            rows += "<tr>"
            for val in row:
                rows += f"<td>{val}</td>"
            rows += "</tr>"

        headers = "".join([f"<th>{col}</th>" for col in df.columns])

        return f"""
        <style>
        .job-table-wrap {{
            overflow-x: hidden;
            border-radius: 12px;
            border: 1px solid #1e1e2e;
        }}
        .job-table {{
            width: 100%;
            border-collapse: collapse;
            font-family: 'DM Sans', sans-serif;
            font-size: 13px;
            table-layout: fixed;
        }}
        .job-table th {{
            background: #12122a;
            color: #6b6b8a;
            font-size: 11px;
            font-weight: 500;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            padding: 14px 16px;
            text-align: left;
            border-bottom: 1px solid #1e1e2e;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .job-table td {{
            padding: 13px 16px;
            color: #e8e8f0;
            border-bottom: 1px solid #12122a;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 0;
        }}
        .job-table tr:last-child td {{
            border-bottom: none;
        }}
        .job-table tr:nth-child(even) {{
            background: #0d0d1f;
        }}
        .job-table tr:nth-child(odd) {{
            background: #0a0a17;
        }}
        .job-table tr:hover td {{
            background: #1a1a35;
            color: #ffffff;
        }}
        .job-table td:nth-child(1) {{ width: 22%; }}
        .job-table td:nth-child(2) {{ width: 14%; }}
        .job-table td:nth-child(3) {{ width: 10%; }}
        .job-table td:nth-child(4) {{ width: 12%; }}
        .job-table td:nth-child(5) {{ width: 10%; }}
        .job-table td:nth-child(6) {{ width: 9%; }}
        .job-table td:nth-child(7) {{ width: 9%; color: #00d4aa; font-weight: 500; }}
        .job-table td:nth-child(8) {{ width: 8%; }}
        .job-table td:nth-child(9) {{ width: 9%; color: #6b6b8a; font-size: 12px; }}
        </style>
        <div class="job-table-wrap">
            <table class="job-table">
                <thead><tr>{headers}</tr></thead>
                <tbody>{rows}</tbody>
            </table>
        </div>
        """

    st.markdown(render_table(display_df), unsafe_allow_html=True)