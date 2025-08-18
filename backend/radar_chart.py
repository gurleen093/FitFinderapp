# backend/radar_chart.py
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from typing import List, Dict, Tuple

def create_skills_radar_chart(user_skills: List[str], job_skills: List[str], 
                             job_title: str = "Job Position") -> go.Figure:
    """
    Create a radar chart comparing user skills vs job requirements.
    
    Args:
        user_skills: List of user's skills
        job_skills: List of job required skills
        job_title: Title of the job for display
    
    Returns:
        Plotly figure object
    """
    
    # Normalize skills to lowercase for comparison
    user_skills_lower = [skill.strip().lower() for skill in user_skills if skill.strip()]
    job_skills_lower = [skill.strip().lower() for skill in job_skills if skill.strip()]
    
    # Get all unique skills from both sets
    all_skills = list(set(user_skills_lower + job_skills_lower))
    
    # Limit to top skills to avoid overcrowded chart (max 12 skills for readability)
    if len(all_skills) > 12:
        # Prioritize skills that appear in job requirements
        priority_skills = [skill for skill in job_skills_lower if skill in all_skills]
        other_skills = [skill for skill in all_skills if skill not in priority_skills]
        all_skills = priority_skills[:8] + other_skills[:4]
    
    # Calculate scores for each skill
    user_scores = []
    job_scores = []
    skill_labels = []
    
    for skill in all_skills:
        # Find original case version for display
        original_skill = skill
        for us in user_skills:
            if us.strip().lower() == skill:
                original_skill = us.strip()
                break
        for js in job_skills:
            if js.strip().lower() == skill:
                original_skill = js.strip()
                break
        
        skill_labels.append(original_skill.title())
        
        # User score: 1 if they have the skill, 0 if not
        user_score = 1 if skill in user_skills_lower else 0
        user_scores.append(user_score)
        
        # Job score: 1 if required, 0.3 if user has extra skill not required
        job_score = 1 if skill in job_skills_lower else 0.3
        job_scores.append(job_score)
    
    # Create radar chart
    fig = go.Figure()
    
    # Add job requirements trace
    fig.add_trace(go.Scatterpolar(
        r=job_scores,
        theta=skill_labels,
        fill='toself',
        name='Job Requirements',
        line_color='rgba(255, 99, 71, 0.8)',
        fillcolor='rgba(255, 99, 71, 0.1)'
    ))
    
    # Add user skills trace
    fig.add_trace(go.Scatterpolar(
        r=user_scores,
        theta=skill_labels,
        fill='toself',
        name='Your Skills',
        line_color='rgba(0, 128, 255, 0.8)',
        fillcolor='rgba(0, 128, 255, 0.1)'
    ))
    
    # Update layout
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1],
                tickvals=[0, 0.3, 1],
                ticktext=['Not Required', 'Bonus', 'Required']
            )
        ),
        showlegend=True,
        title=f"Skills Comparison: {job_title}",
        title_x=0.5,
        title_font_size=16,
        height=500,
        width=600
    )
    
    return fig

def create_skills_match_summary(user_skills: List[str], job_skills: List[str]) -> Dict[str, any]:
    """
    Create a summary of skills match for display alongside radar chart.
    
    Returns:
        Dictionary with match statistics
    """
    user_skills_lower = set(skill.strip().lower() for skill in user_skills if skill.strip())
    job_skills_lower = set(skill.strip().lower() for skill in job_skills if skill.strip())
    
    matched_skills = user_skills_lower & job_skills_lower
    missing_skills = job_skills_lower - user_skills_lower
    extra_skills = user_skills_lower - job_skills_lower
    
    # Calculate match percentage
    if job_skills_lower:
        match_percentage = len(matched_skills) / len(job_skills_lower) * 100
    else:
        match_percentage = 0
    
    # Find original case versions for display
    def get_original_case(skill_set, reference_list):
        result = []
        for skill_lower in skill_set:
            for original in reference_list:
                if original.strip().lower() == skill_lower:
                    result.append(original.strip())
                    break
            else:
                result.append(skill_lower.title())
        return result
    
    return {
        "match_percentage": round(match_percentage, 1),
        "matched_count": len(matched_skills),
        "missing_count": len(missing_skills),
        "extra_count": len(extra_skills),
        "total_job_skills": len(job_skills_lower),
        "matched_skills": get_original_case(matched_skills, user_skills + job_skills),
        "missing_skills": get_original_case(missing_skills, job_skills),
        "extra_skills": get_original_case(extra_skills, user_skills)
    }

def create_skill_category_chart(user_skills: List[str], job_skills: List[str]) -> go.Figure:
    """
    Create a bar chart showing skill categories comparison.
    """
    # Define skill categories
    categories = {
        "Technical": ["python", "java", "javascript", "sql", "html", "css", "react", "angular", 
                     "node.js", "docker", "kubernetes", "aws", "azure", "git", "linux", "mongodb"],
        "Data & Analytics": ["data analysis", "machine learning", "tableau", "power bi", "excel", 
                           "pandas", "numpy", "tensorflow", "pytorch", "statistics", "r programming"],
        "Soft Skills": ["communication", "leadership", "teamwork", "problem solving", "project management",
                       "time management", "critical thinking", "presentation", "collaboration"],
        "Business": ["marketing", "sales", "customer service", "business analysis", "strategy",
                    "finance", "accounting", "operations", "consulting"]
    }
    
    user_categories = {cat: 0 for cat in categories}
    job_categories = {cat: 0 for cat in categories}
    
    # Count skills by category
    for skill in user_skills:
        skill_lower = skill.lower()
        for category, keywords in categories.items():
            if any(keyword in skill_lower for keyword in keywords):
                user_categories[category] += 1
                break
    
    for skill in job_skills:
        skill_lower = skill.lower()
        for category, keywords in categories.items():
            if any(keyword in skill_lower for keyword in keywords):
                job_categories[category] += 1
                break
    
    # Create bar chart
    categories_list = list(categories.keys())
    user_counts = [user_categories[cat] for cat in categories_list]
    job_counts = [job_categories[cat] for cat in categories_list]
    
    fig = go.Figure(data=[
        go.Bar(name='Your Skills', x=categories_list, y=user_counts, 
               marker_color='rgba(0, 128, 255, 0.7)'),
        go.Bar(name='Job Requirements', x=categories_list, y=job_counts,
               marker_color='rgba(255, 99, 71, 0.7)')
    ])
    
    fig.update_layout(
        barmode='group',
        title='Skills by Category',
        title_x=0.5,
        xaxis_title='Skill Categories',
        yaxis_title='Number of Skills',
        height=400,
        showlegend=True
    )
    
    return fig