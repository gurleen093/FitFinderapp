# backend/rag_matcher.py
import json
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def _extract_skills_llm(text: str, source: str = "resume") -> list[str]:
    """
    Use the LLM to extract a clean list of skills/technologies/tools/soft-skills.
    Returns a Python list of strings. Falls back to a simple regex if parsing fails.
    """
    system = (
        "You extract SKILLS from text. Return ONLY a compact JSON array of skill phrases "
        "(e.g., [\"Excel\",\"SQL\",\"inventory management\",\"customer service\"]). "
        "Include tech tools, platforms, methodologies, soft skills when clearly job-relevant. "
        "No commentary, no keys, just a JSON array."
    )
    user = f"Source: {source}\n\nText:\n{text[:4000]}"

    try:
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
            temperature=0.2,
            max_tokens=400,
        )
        content = resp.choices[0].message.content.strip()
        # ensure it's a JSON array
        start = content.find("[")
        end = content.rfind("]")
        skills = json.loads(content[start:end+1])
        # normalize
        skills = [s.strip().lower() for s in skills if isinstance(s, str) and s.strip()]
        # dedupe while preserving order
        seen, clean = set(), []
        for s in skills:
            if s not in seen:
                seen.add(s); clean.append(s)
        return clean
    except Exception:
        # very light fallback: comma/semicolon split + dedupe
        import re
        tokens = re.split(r"[,\n;•\-–]+", text.lower())
        tokens = [t.strip() for t in tokens if 2 < len(t.strip()) < 60]
        seen, skills = set(), []
        for t in tokens:
            if t not in seen:
                seen.add(t); skills.append(t)
        return skills[:30]

def llm_analysis(resume_text: str, job_text: str, expert_result: dict | None = None, task: str = "reasoning") -> str:
    """
    Kept for backward compatibility with your app.
    For narrative sections (reasoning / lacking_skills / recommendation).
    """
    system_prompt = "You are a concise career advisor."
    if task == "reasoning":
        user_prompt = (
            "Summarize the top strengths this resume demonstrates for the job in 3–5 bullet points."
        )
    elif task == "lacking_skills":
        user_prompt = (
            "List the most important missing skills for this job (bullet points, brief)."
        )
    elif task == "recommendation":
        user_prompt = (
            "Give 3–6 focused recommendations to close those gaps (brief bullets)."
        )
    else:
        user_prompt = "Provide a short, helpful analysis."

    user_prompt += f"\n\nRESUME:\n{resume_text[:2000]}\n\nJOB DESCRIPTION:\n{job_text[:2000]}\n"
    if expert_result:
        user_prompt += f"\nEXPERT RESULT (optional): {expert_result}"

    resp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": system_prompt},
                  {"role": "user", "content": user_prompt}],
        temperature=0.4,
        max_tokens=500,
    )
    return resp.choices[0].message.content.strip()

# Expose a convenience wrapper the app can use
def extract_skills(text: str, source: str) -> list[str]:
    return _extract_skills_llm(text, source)
