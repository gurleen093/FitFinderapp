# backend/expert_system.py
from typing import List, Dict

def score_from_skill_lists(resume_skills: List[str], jd_skills: List[str]) -> Dict:
    """
    Compute overlap-based score from two skill lists (already normalized to lowercase).
    Score = matched / unique jd skills * 100 (capped).
    """
    jd_set = {s.strip().lower() for s in jd_skills if s.strip()}
    res_set = {s.strip().lower() for s in resume_skills if s.strip()}
    if not jd_set:
        return {"score": 0, "matched": [], "missing": []}

    matched = sorted(list(jd_set & res_set))
    missing = sorted(list(jd_set - res_set))
    score = int(round(100 * len(matched) / max(1, len(jd_set))))
    return {"score": max(0, min(100, score)), "matched": matched, "missing": missing}
