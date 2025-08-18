# backend/expert_system.py
from typing import List, Dict
from .rules_engine import evaluate_skills_match

def score_from_skill_lists(resume_skills: List[str], jd_skills: List[str], job_description: str = "") -> Dict:
    """
    Enhanced skill matching using rules-based expert system.
    Maintains backward compatibility while providing advanced matching.
    """
    if not jd_skills:
        return {"score": 0, "matched": [], "missing": []}
    
    # Use the new rules engine for advanced matching
    result = evaluate_skills_match(resume_skills, jd_skills, job_description)
    
    # Return enhanced result with backward compatibility
    return {
        "score": result["score"],
        "matched": result["matched"],
        "missing": result["missing"],
        "rules_analysis": result.get("detailed_analysis", {}),
        "recommendations": result.get("recommendations", [])
    }

def score_from_skill_lists_simple(resume_skills: List[str], jd_skills: List[str]) -> Dict:
    """
    Original simple overlap-based scoring (kept for fallback).
    """
    jd_set = {s.strip().lower() for s in jd_skills if s.strip()}
    res_set = {s.strip().lower() for s in resume_skills if s.strip()}
    if not jd_set:
        return {"score": 0, "matched": [], "missing": []}

    matched = sorted(list(jd_set & res_set))
    missing = sorted(list(jd_set - res_set))
    score = int(round(100 * len(matched) / max(1, len(jd_set))))
    return {"score": max(0, min(100, score)), "matched": matched, "missing": missing}
