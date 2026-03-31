import sys
import logging
import smtplib
from pathlib import Path
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os

# make sure project root is in path
sys.path.append(str(Path(__file__).resolve().parent.parent))

load_dotenv()

# ─── logging setup ────────────────────────────────────────────────────────────
log_folder = Path(__file__).resolve().parent.parent / "logs"
log_folder.mkdir(exist_ok=True)
log_file = log_folder / f"pipeline_{datetime.now().strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger(__name__)


# ─── email alert on failure ───────────────────────────────────────────────────
def send_failure_email(error: str):
    try:
        sender    = os.getenv("ALERT_EMAIL_FROM")
        receiver  = os.getenv("ALERT_EMAIL_TO")
        password  = os.getenv("ALERT_EMAIL_PASSWORD")
        smtp_host = os.getenv("ALERT_SMTP_HOST", "smtp.gmail.com")
        smtp_port = int(os.getenv("ALERT_SMTP_PORT", "587"))

        if not all([sender, receiver, password]):
            log.warning("Email credentials not set in .env — skipping alert")
            return

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"JobPulse Pipeline FAILED — {datetime.now().strftime('%d %b %Y')}"
        msg["From"]    = sender
        msg["To"]      = receiver

        body = f"""
        <html><body style="font-family:sans-serif;background:#0a0a0f;color:#e8e8f0;padding:32px">
            <h2 style="color:#f5756c">⚠️ JobPulse Pipeline Failed</h2>
            <p style="color:#6b6b8a">Run date: {datetime.now().strftime('%d %b %Y %H:%M')}</p>
            <div style="background:#1e1e2e;padding:16px;border-radius:8px;
                        border-left:4px solid #f5756c;margin:16px 0">
                <code style="color:#f5756c;font-size:13px">{error}</code>
            </div>
            <p>Check your log file at: <code>{log_file}</code></p>
            <p style="color:#6b6b8a;font-size:12px">JobPulse Automated Pipeline</p>
        </body></html>
        """

        msg.attach(MIMEText(body, "html"))

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, receiver, msg.as_string())

        log.info(f"Failure alert sent to {receiver}")

    except Exception as e:
        log.error(f"Could not send email alert: {e}")


# ─── pipeline steps ───────────────────────────────────────────────────────────
def run_pipeline():
    start = datetime.now()
    log.info("=" * 60)
    log.info(f"JobPulse pipeline started — {start.strftime('%d %b %Y %H:%M')}")
    log.info("=" * 60)

    try:
        # step 1 — fetch
        log.info("STEP 1: Fetching jobs from Adzuna...")
        from pipeline.fetch_jobs import fetch_jobs
        fetch_jobs(pages=100, max_days_old=7)
        log.info("STEP 1: Complete")

        # step 2 — transform
        log.info("STEP 2: Transforming data...")
        from pipeline.transform_jobs import load_latest_raw, transform_jobs
        raw_df   = load_latest_raw()
        clean_df = transform_jobs(raw_df, run_date=datetime.now().date())
        log.info(f"STEP 2: Complete — {len(clean_df)} rows transformed")

        # step 3 — load
        log.info("STEP 3: Loading into PostgreSQL...")
        from pipeline.load_jobs import load_jobs
        load_jobs()
        log.info("STEP 3: Complete")

        duration = (datetime.now() - start).seconds
        log.info("=" * 60)
        log.info(f"Pipeline completed successfully in {duration}s")
        log.info("=" * 60)

    except Exception as e:
        log.error(f"Pipeline failed: {e}", exc_info=True)
        send_failure_email(str(e))
        sys.exit(1)


if __name__ == "__main__":
    run_pipeline()