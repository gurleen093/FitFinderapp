# backend/rag_matcher.py
from __future__ import annotations
import os, json, re
import streamlit as st
from dotenv import load_dotenv

# OpenAI v1 client
try:
    from openai import OpenAI
except Exception:
    OpenAI = None  # allow import even if openai not installed yet

# ---- secrets helper (works local + Streamlit Cloud) ----
load_dotenv()  # loads .env if present

def _get_secret(name: str, default: str = "") -> str:
    # Prefer OS env (local .env or real env)
    val = os.getenv(name)
    if val:
        return val
    # Fall back to Streamlit secrets if available
    try:
        return st.secrets[name]
    except Exception:
        return default

OPENAI_API_KEY = _get_secret("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY) if (OpenAI and OPENAI_API_KEY) else None

# --------------------------------------------------------
# Public API
# --------------------------------------------------------

def extract_skills(text: str, source: str = "resume") -> list[str]:
    """
    Extract a clean, de-duplicated list of skills/technologies/tools/soft-skills
    from arbitrary text. Uses OpenAI if a key is configured; otherwise falls back
    to a lightweight heuristic so your app still works.
    Returns lowercased skill phrases.
    """
    cleaned = (text or "").strip()
    if not cleaned:
        return []

    # 1) Try LLM for high-quality extraction (JSON array only)
    if client:
        system = (
            "You extract SKILLS from text. Return ONLY a compact JSON array of short skill phrases "
            "(e.g., [\"Excel\",\"SQL\",\"inventory management\",\"customer service\"]). "
            "Include software/tools, frameworks, programming languages, platforms, methods, and clearly job-relevant soft skills. "
            "NO commentary, NO keys, ONLY a JSON array."
        )
        user = f"Source: {source}\n\nText:\n{cleaned[:4000]}"
        try:
            resp = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=0.2,
                max_tokens=400,
            )
            content = resp.choices[0].message.content.strip()
            # Guard: ensure we slice the JSON array if the model wraps anything
            start = content.find("[")
            end = content.rfind("]")
            if start != -1 and end != -1:
                arr = json.loads(content[start:end+1])
                skills = [s.strip().lower() for s in arr if isinstance(s, str) and s.strip()]
                # de-duplicate preserving order
                seen, out = set(), []
                for s in skills:
                    if s not in seen:
                        seen.add(s); out.append(s)
                return out[:50]
        except Exception:
            pass  # fall through to heuristic

    # 2) Heuristic fallback (works without OpenAI)
    #    - split on commas/bullets/semicolons/newlines
    #    - keep tokens with letters/numbers, remove very short words
    tokens = re.split(r"[\n,;•\-–]+", cleaned.lower())
    tokens = [t.strip() for t in tokens if t and len(t.strip()) > 2]
    # remove obviously non-skill stopwords
    stop = set("and or with for to the a an in on of etc responsible duties role job description requirements".split())
    rough = []
    for t in tokens:
        # keep multiword phrases or single tech-like tokens
        if any(ch.isalpha() for ch in t) and not all(w in stop for w in t.split()):
            rough.append(t)
    # de-duplicate
    seen, out = set(), []
    for r in rough:
        if r not in seen:
            seen.add(r); out.append(r)
    return out[:50]


def llm_analysis(resume_text: str, job_text: str, expert_result: dict | None = None, task: str = "reasoning") -> str:
    """
    Generate concise narrative sections. Falls back to a simple string if OpenAI is not configured.
    task in {"reasoning","lacking_skills","recommendation"}
    """
    if not client:
        # Fallback without OpenAI: return a brief placeholder using expert_result, if any.
        if task == "reasoning":
            return "Top strengths: " + ", ".join((expert_result or {}).get("matched", [])[:6]) if expert_result else "N/A"
        if task == "lacking_skills":
            return "Key gaps: " + ", ".join((expert_result or {}).get("missing", [])[:6]) if expert_result else "N/A"
        if task == "recommendation":
            gaps = (expert_result or {}).get("missing", [])[:6]
            if gaps:
                bullets = "\n".join(f"- Learn {g.title()}" for g in gaps)
                return f"Recommendations:\n{bullets}"
            return "Tailor your resume to the role, quantify impact, and apply."
        return "Analysis unavailable (no OpenAI key configured)."

    system = "You are a concise, practical career advisor."
    tasks = {
        "reasoning": "Summarize the top strengths this resume shows for this job as 3–5 crisp bullets.",
        "lacking_skills": "List the most important missing or weak skills required by the job (3–6 bullets).",
        "recommendation": "Give 3–6 actionable recommendations to close gaps (courses, projects, certifications).",
    }
    prompt = tasks.get(task, "Provide a short helpful analysis.")
    prompt += f"\n\nRESUME:\n{(resume_text or '')[:2000]}\n\nJOB DESCRIPTION:\n{(job_text or '')[:2000]}"
    if expert_result:
        prompt += f"\n\nEXPERT RESULT: {expert_result}"

    resp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        temperature=0.4,
        max_tokens=500,
    )
    return resp.choices[0].message.content.strip()
