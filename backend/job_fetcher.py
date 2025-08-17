# backend/job_fetcher.py
from __future__ import annotations
import os
from typing import List, Dict, Any
import requests
from dotenv import load_dotenv

# Load keys from .env in your project root
# .env should contain:
# ADZUNA_APP_ID=your_app_id
# ADZUNA_APP_KEY=your_app_key
load_dotenv()

ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID", "").strip()
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY", "").strip()

class AdzunaAuthError(RuntimeError):
    pass

def _ensure_keys():
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        raise AdzunaAuthError(
            "Adzuna credentials missing. Add ADZUNA_APP_ID and ADZUNA_APP_KEY to your .env file."
        )

def fetch_jobs(
    query: str,
    location: str = "Canada",
    results_per_page: int = 5,
    page: int = 1,
    country: str = "ca",  # change to "us", "gb", "in", etc. if you want
) -> List[Dict[str, Any]]:
    """
    Fetch jobs from Adzuna and return a normalized list your app can render.
    Returns a list of dicts with: title, company, description, url (apply link).
    """
    _ensure_keys()
    if not query:
        return []

    base = f"https://api.adzuna.com/v1/api/jobs/{country}/search/{page}"
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "what": query,
        "where": location,
        "results_per_page": max(1, min(int(results_per_page), 50)),
        "content-type": "application/json",
    }

    resp = requests.get(base, params=params, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    results = data.get("results", []) or []

    jobs: List[Dict[str, Any]] = []
    for j in results:
        # company can be a dict or string; normalize to string
        company = j.get("company")
        if isinstance(company, dict):
            company = company.get("display_name") or "Company"
        elif not isinstance(company, str) or not company:
            company = "Company"

        jobs.append(
            {
                "title": j.get("title") or "Untitled Role",
                "company": company,
                "description": j.get("description") or "",
                "url": j.get("redirect_url") or "",
            }
        )
    return jobs
