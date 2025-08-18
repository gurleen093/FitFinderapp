# backend/rules_engine.py
from typing import List, Dict, Any, Tuple
import re

class SkillRule:
    """Base class for skill matching rules"""
    def __init__(self, name: str, weight: float = 1.0, description: str = ""):
        self.name = name
        self.weight = weight
        self.description = description
    
    def evaluate(self, user_skills: List[str], job_skills: List[str], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Evaluate the rule and return result with score and explanation"""
        raise NotImplementedError

class ExactMatchRule(SkillRule):
    """Rule for exact skill matches"""
    def __init__(self):
        super().__init__("Exact Match", weight=3.0, 
                        description="Direct matches between user and job skills")
    
    def evaluate(self, user_skills: List[str], job_skills: List[str], context: Dict[str, Any] = None) -> Dict[str, Any]:
        user_set = {skill.strip().lower() for skill in user_skills}
        job_set = {skill.strip().lower() for skill in job_skills}
        
        matches = list(user_set & job_set)
        score = len(matches) * self.weight
        
        return {
            "score": score,
            "matches": matches,
            "explanation": f"Found {len(matches)} exact skill matches"
        }

class TechnicalSkillRule(SkillRule):
    """Rule that gives higher weight to technical skills"""
    def __init__(self):
        super().__init__("Technical Skills", weight=2.5,
                        description="Higher weight for programming languages and technical tools")
        
        self.technical_keywords = {
            'python', 'java', 'javascript', 'c++', 'sql', 'html', 'css', 'react', 'angular',
            'node.js', 'docker', 'kubernetes', 'aws', 'azure', 'git', 'linux', 'mongodb',
            'postgresql', 'mysql', 'tensorflow', 'pytorch', 'pandas', 'numpy', 'django',
            'flask', 'spring', 'restapi', 'graphql', 'machine learning', 'data analysis',
            'tableau', 'power bi', 'excel', 'r programming', 'scala', 'golang', 'rust'
        }
    
    def evaluate(self, user_skills: List[str], job_skills: List[str], context: Dict[str, Any] = None) -> Dict[str, Any]:
        user_tech = [skill for skill in user_skills if self._is_technical(skill)]
        job_tech = [skill for skill in job_skills if self._is_technical(skill)]
        
        user_tech_set = {skill.strip().lower() for skill in user_tech}
        job_tech_set = {skill.strip().lower() for skill in job_tech}
        
        tech_matches = list(user_tech_set & job_tech_set)
        score = len(tech_matches) * self.weight
        
        return {
            "score": score,
            "matches": tech_matches,
            "explanation": f"Found {len(tech_matches)} technical skill matches (weighted {self.weight}x)"
        }
    
    def _is_technical(self, skill: str) -> bool:
        skill_lower = skill.lower().strip()
        return any(tech in skill_lower for tech in self.technical_keywords)

class SoftSkillRule(SkillRule):
    """Rule for soft skills with moderate weight"""
    def __init__(self):
        super().__init__("Soft Skills", weight=1.5,
                        description="Moderate weight for soft skills and interpersonal abilities")
        
        self.soft_skill_keywords = {
            'communication', 'leadership', 'teamwork', 'problem solving', 'critical thinking',
            'time management', 'project management', 'analytical thinking', 'creativity',
            'adaptability', 'collaboration', 'presentation', 'negotiation', 'customer service'
        }
    
    def evaluate(self, user_skills: List[str], job_skills: List[str], context: Dict[str, Any] = None) -> Dict[str, Any]:
        user_soft = [skill for skill in user_skills if self._is_soft_skill(skill)]
        job_soft = [skill for skill in job_skills if self._is_soft_skill(skill)]
        
        user_soft_set = {skill.strip().lower() for skill in user_soft}
        job_soft_set = {skill.strip().lower() for skill in job_soft}
        
        soft_matches = list(user_soft_set & job_soft_set)
        score = len(soft_matches) * self.weight
        
        return {
            "score": score,
            "matches": soft_matches,
            "explanation": f"Found {len(soft_matches)} soft skill matches (weighted {self.weight}x)"
        }
    
    def _is_soft_skill(self, skill: str) -> bool:
        skill_lower = skill.lower().strip()
        return any(soft in skill_lower for soft in self.soft_skill_keywords)

class SimilarityRule(SkillRule):
    """Rule for similar or related skills"""
    def __init__(self):
        super().__init__("Similar Skills", weight=1.8,
                        description="Matches for similar or related skills")
        
        self.similarity_map = {
            'python': ['scripting', 'automation', 'data analysis'],
            'javascript': ['web development', 'frontend', 'react', 'angular'],
            'sql': ['database', 'data querying', 'mysql', 'postgresql'],
            'project management': ['coordination', 'planning', 'scrum', 'agile'],
            'data analysis': ['analytics', 'statistics', 'reporting', 'excel'],
            'machine learning': ['ai', 'artificial intelligence', 'deep learning', 'ml'],
            'communication': ['presentation', 'writing', 'verbal communication'],
            'leadership': ['management', 'team lead', 'supervision']
        }
    
    def evaluate(self, user_skills: List[str], job_skills: List[str], context: Dict[str, Any] = None) -> Dict[str, Any]:
        similar_matches = []
        score = 0
        
        for user_skill in user_skills:
            user_lower = user_skill.lower().strip()
            for job_skill in job_skills:
                job_lower = job_skill.lower().strip()
                if self._are_similar(user_lower, job_lower):
                    similar_matches.append(f"{user_skill} ≈ {job_skill}")
                    score += self.weight
        
        return {
            "score": score,
            "matches": similar_matches,
            "explanation": f"Found {len(similar_matches)} similar skill matches"
        }
    
    def _are_similar(self, skill1: str, skill2: str) -> bool:
        # Check if skills are in similarity map
        for base_skill, related_skills in self.similarity_map.items():
            if base_skill in skill1 and any(related in skill2 for related in related_skills):
                return True
            if base_skill in skill2 and any(related in skill1 for related in related_skills):
                return True
        
        # Additional fuzzy matching for common variations
        # Check for partial matches (at least 4 characters)
        if len(skill1) >= 4 and len(skill2) >= 4:
            if skill1[:4] == skill2[:4]:  # Same first 4 chars
                return True
            
        # Common abbreviations and variations
        common_matches = [
            ('js', 'javascript'), ('py', 'python'), ('sql', 'database'),
            ('ml', 'machine learning'), ('ai', 'artificial intelligence'),
            ('pm', 'project management'), ('dev', 'development'),
            ('admin', 'administration'), ('mgmt', 'management')
        ]
        
        for short, full in common_matches:
            if (short in skill1 and full in skill2) or (short in skill2 and full in skill1):
                return True
                
        return False

class ExperienceRule(SkillRule):
    """Rule that considers experience level indicators"""
    def __init__(self):
        super().__init__("Experience Level", weight=2.0,
                        description="Matches experience levels and seniority")
        
        self.experience_keywords = {
            'senior': ['senior', 'lead', 'principal', 'architect'],
            'mid': ['mid-level', 'intermediate', 'experienced'],
            'junior': ['junior', 'entry-level', 'associate', 'trainee']
        }
    
    def evaluate(self, user_skills: List[str], job_skills: List[str], context: Dict[str, Any] = None) -> Dict[str, Any]:
        user_exp = self._extract_experience_level(user_skills)
        job_exp = self._extract_experience_level(job_skills)
        
        score = 0
        explanation = ""
        
        if user_exp and job_exp:
            if user_exp == job_exp:
                score = self.weight * 3
                explanation = f"Experience level match: {user_exp}"
            elif (user_exp == 'senior' and job_exp == 'mid') or (user_exp == 'mid' and job_exp == 'junior'):
                score = self.weight * 2
                explanation = f"Experience level compatible: {user_exp} > {job_exp}"
            else:
                score = self.weight * 0.5
                explanation = f"Experience level mismatch: {user_exp} vs {job_exp}"
        
        return {
            "score": score,
            "matches": [explanation] if explanation else [],
            "explanation": explanation or "No clear experience level indicators found"
        }
    
    def _extract_experience_level(self, skills: List[str]) -> str:
        skills_text = " ".join(skills).lower()
        
        for level, keywords in self.experience_keywords.items():
            if any(keyword in skills_text for keyword in keywords):
                return level
        return None

class RulesEngine:
    """Main rules engine that combines multiple rules for skill matching"""
    
    def __init__(self):
        self.rules = [
            ExactMatchRule(),
            TechnicalSkillRule(),
            SoftSkillRule(),
            SimilarityRule(),
            ExperienceRule()
        ]
    
    def evaluate_match(self, user_skills: List[str], job_skills: List[str], 
                      job_description: str = "", user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Evaluate job match using all rules and return comprehensive results
        """
        if not user_skills or not job_skills:
            return {
                "total_score": 0,
                "percentage": 0,
                "rule_results": [],
                "recommendations": ["No skills data available for comparison"],
                "missing_skills": job_skills if job_skills else [],
                "matched_skills": []
            }
        
        rule_results = []
        total_score = 0
        all_matches = []
        
        context = user_context or {}
        context["job_description"] = job_description
        
        # Evaluate each rule
        for rule in self.rules:
            try:
                result = rule.evaluate(user_skills, job_skills, context)
                rule_result = {
                    "rule_name": rule.name,
                    "score": result.get("score", 0),
                    "weight": rule.weight,
                    "matches": result.get("matches", []),
                    "explanation": result.get("explanation", "")
                }
                rule_results.append(rule_result)
                total_score += rule_result["score"]
                all_matches.extend(rule_result["matches"])
                
            except Exception as e:
                # Log error but continue with other rules
                rule_results.append({
                    "rule_name": rule.name,
                    "score": 0,
                    "weight": rule.weight,
                    "matches": [],
                    "explanation": f"Error: {str(e)}"
                })
        
        # Better percentage calculation based on actual matches vs job requirements
        # Calculate percentage based on job coverage rather than theoretical maximum
        job_skills_lower = {skill.lower().strip() for skill in job_skills}
        user_skills_lower = {skill.lower().strip() for skill in user_skills}
        
        # Base percentage on exact matches
        exact_matches = len(job_skills_lower & user_skills_lower)
        base_percentage = (exact_matches / max(1, len(job_skills_lower))) * 100
        
        # Add bonus points for rule-based matches (capped at 30% bonus)
        rule_bonus = min(30, total_score * 2)  # Each rule point = 2% bonus
        
        percentage = min(100, int(base_percentage + rule_bonus))
        
        # Identify missing skills
        user_skills_lower = {skill.lower().strip() for skill in user_skills}
        missing_skills = [skill for skill in job_skills 
                         if skill.lower().strip() not in user_skills_lower]
        
        # Generate recommendations
        recommendations = self._generate_recommendations(rule_results, missing_skills, percentage)
        
        return {
            "total_score": round(total_score, 2),
            "percentage": percentage,
            "rule_results": rule_results,
            "recommendations": recommendations,
            "missing_skills": missing_skills[:10],  # Limit to top 10
            "matched_skills": list(set(all_matches))[:15]  # Limit to top 15
        }
    
    def _generate_recommendations(self, rule_results: List[Dict], missing_skills: List[str], 
                                percentage: int) -> List[str]:
        """Generate actionable recommendations based on rule results"""
        recommendations = []
        
        # Performance-based recommendations
        if percentage >= 80:
            recommendations.append("🎯 Excellent match! You have most required skills.")
        elif percentage >= 60:
            recommendations.append("👍 Good match! Focus on closing key skill gaps.")
        elif percentage >= 40:
            recommendations.append("⚡ Moderate match. Significant skill development needed.")
        else:
            recommendations.append("📚 Low match. Consider building foundational skills first.")
        
        # Rule-specific recommendations
        for rule_result in rule_results:
            rule_name = rule_result["rule_name"]
            score = rule_result["score"]
            
            if rule_name == "Technical Skills" and score < 3:
                recommendations.append("💻 Focus on building technical skills for better job match.")
            elif rule_name == "Experience Level" and score < 2:
                recommendations.append("⭐ Consider roles matching your experience level.")
        
        # Missing skills recommendations
        if missing_skills:
            top_missing = missing_skills[:3]
            recommendations.append(f"📖 Priority skills to learn: {', '.join(top_missing)}")
        
        return recommendations

# Convenience function for backward compatibility
def evaluate_skills_match(user_skills: List[str], job_skills: List[str], 
                         job_description: str = "") -> Dict[str, Any]:
    """
    Simplified function that maintains compatibility with existing code
    """
    engine = RulesEngine()
    result = engine.evaluate_match(user_skills, job_skills, job_description)
    
    # Convert to format similar to original expert_system
    return {
        "score": result["percentage"],
        "matched": result["matched_skills"],
        "missing": result["missing_skills"],
        "detailed_analysis": result,
        "recommendations": result["recommendations"]
    }