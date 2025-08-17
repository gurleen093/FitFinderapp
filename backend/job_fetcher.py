# backend/job_fetcher.py
import os
import requests
from dotenv import load_dotenv
import streamlit as st

# Load .env for local runs; harmless in cloud
load_dotenv()

def _get_secret(name: str, default: str = "") -> str:
    # Prefer OS env (from .env locally or real env in servers)
    val = os.getenv(name)
    if val:
        return val
    # Fall back to Streamlit secrets only if present
    try:
        return st.secrets[name]
    except Exception:
        return default

ADZUNA_APP_ID  = _get_secret("ADZUNA_APP_ID")
ADZUNA_APP_KEY = _get_secret("ADZUNA_APP_KEY")

def fetch_jobs(query: str, location: str = "Canada", results_per_page: int = 5):
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        raise RuntimeError(
            "Adzuna credentials missing. Set ADZUNA_APP_ID and ADZUNA_APP_KEY in .env (local) "
            "or in Streamlit Secrets (cloud)."
        )

    url = "https://api.adzuna.com/v1/api/jobs/ca/search/1"
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "what": query,
        "where": location,
        "results_per_page": results_per_page,
    }
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    results = r.json().get("results", [])

    jobs = []
    for j in results:
        company = j.get("company")
        if isinstance(company, dict):
            company = company.get("display_name") or "Company"
        elif not isinstance(company, str):
            company = "Company"

        jobs.append({
            "title": j.get("title") or "Untitled Role",
            "company": company,
            "description": j.get("description") or "",
            "url": j.get("redirect_url") or "#",
        })
    return jobs
