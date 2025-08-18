import json
import streamlit as st

from backend.resume_praser import extract_text_from_pdf, extract_text_from_docx
from backend.job_fetcher import fetch_jobs
from backend.expert_system import score_from_skill_lists
from backend.rag_matcher import llm_analysis, extract_skills
from backend.radar_chart import create_skills_radar_chart, create_skills_match_summary, create_skill_category_chart


# ---------------- Page config ----------------
st.set_page_config(page_title="FitFinder", page_icon=":briefcase:", layout="wide")


# ---------------- Helper: ask the LLM to pick trainable skills only ----------------
def pick_trainable_skills_ai(missing: list[str], resume_text: str, jd_text: str) -> list[str]:
    """
    Uses the LLM to return ONLY 3–8 sensible, trainable skills from 'missing'.
    The model must ignore non-trainables (licenses, shifts/availability, background checks,
    work authorization/visa, age, dress code/uniform, transportation/commute, etc.).
    Output must be ONLY a JSON array of strings (no prose).
    """
    if not missing:
        return []

    instruction = (
        "From the following items, select ONLY the trainable, course-learnable skills that would "
        "improve the candidate's fit. Ignore items that are not trainable (licenses, shifts or availability, "
        "scheduling/attendance, background checks, work authorization/visa, age, transportation/commute, "
        "uniform/dress code, education level requirements). Prefer concrete tools, platforms, methods, "
        "and business competencies. Return ONLY a JSON array of 3 to 8 skill strings. No extra text."
    )

    prompt = (
        instruction
        + "\n\nITEMS:\n"
        + json.dumps(missing, ensure_ascii=False)
        + "\n\nRESUME (context):\n"
        + (resume_text or "")[:1500]
        + "\n\nJOB DESCRIPTION (context):\n"
        + (jd_text or "")[:1500]
    )

    try:
        raw = llm_analysis(resume_text, prompt, expert_result=None, task="reasoning")
        i, j = raw.find("["), raw.rfind("]")
        if i != -1 and j != -1:
            arr = json.loads(raw[i:j+1])
            out = [s.strip() for s in arr if isinstance(s, str) and s.strip()]
            # de-dup preserve order
            seen, final = set(), []
            for s in out:
                k = s.lower()
                if k not in seen:
                    seen.add(k)
                    final.append(s)
            return final[:8]
    except Exception:
        pass

    # fallback: keep first few unique strings (app stays robust)
    return list(dict.fromkeys(missing))[:8]


# ---------------- Global styling (background + buttons + typography) ----------------
st.markdown("""
<style>
/* Soft graphic background */
html, body, [class*="css"]  {
  background:
    radial-gradient(1200px 600px at 100% 0%, #f3ecff 0%, rgba(243,236,255,0) 60%),
    radial-gradient(900px 600px at 0% 100%, #e8f7ff 0%, rgba(232,247,255,0) 60%),
    linear-gradient(135deg, #f8fbff 0%, #f3f6ff 40%, #f8f6ff 100%) !important;
  font-family: "Segoe UI", system-ui, -apple-system, Roboto, Arial, sans-serif;
}

/* Fancy green buttons */
.stButton > button {
  background: #22a06b !important; color: #fff !important; font-weight: 700 !important;
  border: none !important; border-radius: 12px !important; padding: 10px 18px !important;
  box-shadow: 0 8px 18px rgba(34,160,107,0.25) !important;
}
.stButton > button:hover { background:#1b5e4a !important; }

/* Radio label spacing */
.block-container .stRadio > label, .block-container .stRadio div[role="radiogroup"] label {
  font-weight: 600;
}

/* Centered header */
.header { text-align:center; margin-top:-10px; margin-bottom:6px; }
.header h1 { color:#7E57C2; margin:6px 0 2px; font-size: 34px; font-weight: 800; }
.subtitle { color:#5b5f76; margin:0 0 8px 0; }

/* Divider */
hr { border:none; border-top:1px solid #e7e9f2; margin:10px 0 14px; }

/* Score badge (green chip) */
.score-badge {
  display:inline-block; background:#eaffea; color:#0c7a3d; border:2px solid #1aa251;
  padding:6px 12px; border-radius:12px; font-weight:800; font-size:16px;
  box-shadow:0 6px 14px rgba(26,162,81,0.15);
}

/* Job card look */
.job-card {
  background:#fff; border:1px solid #e7e9f2; border-radius:16px;
  padding:14px 16px; margin:10px 0; box-shadow:0 4px 10px rgba(22,34,69,0.05);
}
</style>
""", unsafe_allow_html=True)


# ---------------- Header with bigger logo + centered light-purple title ----------------
st.markdown('<div class="header">', unsafe_allow_html=True)
st.image("logo.png", width=180)  # ensure logo.png is beside app.py
st.markdown("<h1>FitFinder – Find job that suits you</h1>", unsafe_allow_html=True)
st.markdown('<p class="subtitle">Upload your resume, find roles, and get clear skill insights.</p>', unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)
st.markdown("<hr/>", unsafe_allow_html=True)


# ---------------- Session state ----------------
if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""
if "jobs" not in st.session_state:
    st.session_state.jobs = []
if "extracted_skills" not in st.session_state:
    st.session_state.extracted_skills = []
if "edited_skills" not in st.session_state:
    st.session_state.edited_skills = []
if "skills_extracted" not in st.session_state:
    st.session_state.skills_extracted = False
if "skills_confirmed" not in st.session_state:
    st.session_state.skills_confirmed = False


# ---------------- Upload Resume ----------------
uploaded_file = st.file_uploader("Upload your Resume (PDF or DOCX)", type=["pdf", "docx"])
if uploaded_file:
    if uploaded_file.type == "application/pdf":
        st.session_state.resume_text = extract_text_from_pdf(uploaded_file)
    else:
        st.session_state.resume_text = extract_text_from_docx(uploaded_file)
    st.session_state.skills_extracted = False
    st.session_state.skills_confirmed = False
    st.success("✅ Resume uploaded successfully!")

resume_text = st.session_state.resume_text

# ---------------- Extract and Display Skills ----------------
if resume_text and not st.session_state.skills_extracted:
    if st.button("🔍 Extract Skills from Resume"):
        with st.spinner("Extracting skills from your resume..."):
            skills = extract_skills(resume_text, source="resume")
            st.session_state.extracted_skills = skills
            st.session_state.edited_skills = skills.copy()
            st.session_state.skills_extracted = True
            st.session_state.skills_confirmed = False
        st.success("✅ Skills extracted successfully!")

# Display skills if extracted
if st.session_state.skills_extracted and st.session_state.extracted_skills:
    st.subheader("🎯 Your Skills")
    st.success("✅ **Skills Extracted Successfully!**")
    
    # Display extracted skills in a colorful table format
    st.markdown("**Your Skills:**")
    
    # Create skills data for table display
    skills_data = []
    colors = ["🔵", "🟢", "🟡", "🔴", "🟣", "🟠"]  # Cycle through different colors
    
    # Group skills into rows of 3 for better table layout
    skills_list = st.session_state.extracted_skills
    for i in range(0, len(skills_list), 3):
        row = skills_list[i:i+3]
        # Pad with empty strings if needed
        while len(row) < 3:
            row.append("")
        skills_data.append(row)
    
    # Create DataFrame for table display
    import pandas as pd
    df = pd.DataFrame(skills_data, columns=["Skill 1", "Skill 2", "Skill 3"])
    
    # Style the dataframe with colors and formatting
    def style_skills_table(df):
        # Create a styler object
        styler = df.style
        
        # Apply styling
        styler = styler.set_properties(**{
            'background-color': '#f0f8ff',
            'border': '2px solid #4CAF50',
            'border-radius': '8px',
            'padding': '10px',
            'text-align': 'center',
            'font-weight': 'bold',
            'color': '#2E8B57'
        })
        
        # Style headers
        styler = styler.set_table_styles([
            {'selector': 'th', 'props': [
                ('background-color', '#4CAF50'),
                ('color', 'white'),
                ('font-weight', 'bold'),
                ('text-align', 'center'),
                ('padding', '12px'),
                ('border-radius', '8px 8px 0 0')
            ]},
            {'selector': 'td', 'props': [
                ('padding', '8px 12px'),
                ('border-bottom', '1px solid #ddd')
            ]},
            {'selector': '', 'props': [
                ('border-collapse', 'collapse'),
                ('margin', '10px 0'),
                ('width', '100%')
            ]}
        ])
        
        return styler
    
    # Display the styled table
    if not df.empty and not all(df.iloc[0] == ""):
        styled_df = style_skills_table(df)
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
    
    st.markdown(f"**Total Skills: {len(st.session_state.extracted_skills)}**")
    
    # Set skills as confirmed and ready to use
    st.session_state.edited_skills = st.session_state.extracted_skills.copy()
    st.session_state.skills_confirmed = True


# ---------------- Job Input ----------------
job_option = st.radio("Select Job Input Method", ["Find Jobs by Query", "Analyze Job Description"])


# ---------------- Find Jobs by Query (traditional search) ----------------
if job_option == "Find Jobs by Query":
    query = st.text_input("Enter Job Title (e.g. Data Scientist, Web Developer)")
    if st.button("🔎 Find Jobs"):
        if not resume_text:
            st.warning("⚠️ Please upload your resume first so I can find matching jobs for you.")
        else:
            st.session_state.jobs = fetch_jobs(query) if query else []

    if st.session_state.jobs:
        for i, job in enumerate(st.session_state.jobs, start=1):
            title = job.get("title", "Untitled Role")
            company = job.get("company", "Company")
            desc = job.get("description", "") or ""
            url = job.get("url") or job.get("redirect_url") or "#"

            st.markdown("<div class='job-card'>", unsafe_allow_html=True)
            st.markdown(f"**{i}. {title}** — *{company}*")
            st.write(desc[:320] + ("..." if len(desc) > 320 else ""))
            st.markdown(f"[👉 Apply here]({url})")
            st.markdown("</div>", unsafe_allow_html=True)

# ---------------- Analyze pasted Job Description (resume required to run) ----------------
elif job_option == "Analyze Job Description":
    job_description = st.text_area("Paste Job Description here", height=220)

    if st.button("📊 Analyze Match"):
        if not resume_text:
            st.warning("⚠️ Please upload resume first.")
        elif not (job_description or "").strip():
            st.warning("Please paste a job description.")
        else:
            # 1) Extract skills and compute enhanced rule-based score
            if st.session_state.skills_extracted and st.session_state.edited_skills:
                # Use user's edited skills for more accurate matching
                resume_skills = st.session_state.edited_skills
            else:
                resume_skills = extract_skills(resume_text, source="resume")
            
            jd_skills = extract_skills(job_description, source="job")
            scored = score_from_skill_lists(resume_skills, jd_skills, job_description)

            # 2) Show score prominently (out of 10)
            score_100 = int(scored.get("score", 0))
            score_10 = max(0, min(10, round(score_100 / 10)))
            st.markdown(f"<span class='score-badge'>⭐ {score_10}/10</span>", unsafe_allow_html=True)

            # 3) Hiring-manager style recommendation (resume tweaks + focus areas)
            hm_prefix = (
                "You are a hiring manager reviewing a candidate's resume against this job. "
                "Write a concise, helpful recommendation:\n"
                "1) Summarize overall fit and key strengths in 2–3 sentences.\n"
                "2) If a concept is present in the resume under a different name, suggest precise resume wording changes "
                "so ATS/recruiters see the right keywords.\n"
                "3) List the top gaps to learn next (short bullets, most impactful first). Be constructive and specific."
            )
            augmented_jd = hm_prefix + "\n\n--- JOB DESCRIPTION ---\n" + job_description

            try:
                reco_text = llm_analysis(resume_text, augmented_jd, expert_result=scored, task="recommendation")
            except TypeError:
                reco_text = llm_analysis(resume_text, augmented_jd)

            st.subheader("💡 Recommendation")
            st.write(reco_text)

            # 4) Skills Radar Chart Visualization
            st.write("🔍 Debug Info:")
            st.write(f"- extracted_skills: {len(st.session_state.get('extracted_skills', []))} skills")
            st.write(f"- edited_skills: {len(st.session_state.get('edited_skills', []))} skills")
            st.write(f"- skills_extracted: {st.session_state.get('skills_extracted', False)}")
            st.write(f"- skills_confirmed: {st.session_state.get('skills_confirmed', False)}")
            st.write(f"- jd_skills count: {len(jd_skills) if jd_skills else 0}")
            
            # Try to show radar chart
            try:
                user_skills_for_chart = st.session_state.get('edited_skills', []) or st.session_state.get('extracted_skills', [])
                
                if user_skills_for_chart and jd_skills:
                    st.subheader("📊 Skills Comparison Radar Chart")
                    st.write(f"Using {len(user_skills_for_chart)} user skills and {len(jd_skills)} job skills")
                else:
                    st.warning(f"Cannot show radar chart: user_skills={len(user_skills_for_chart) if user_skills_for_chart else 0}, job_skills={len(jd_skills) if jd_skills else 0}")
                
                # Use extracted or edited skills
                user_skills_for_chart = st.session_state.get('edited_skills', []) or st.session_state.get('extracted_skills', [])
                
                # Create radar chart
                radar_fig = create_skills_radar_chart(
                    user_skills_for_chart, 
                    jd_skills,
                    "Job Position"
                )
                st.plotly_chart(radar_fig, use_container_width=True)
                
                # Create skills summary
                match_summary = create_skills_match_summary(user_skills_for_chart, jd_skills)
                
                # Display summary metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Match %", f"{match_summary['match_percentage']}%")
                with col2:
                    st.metric("Matched Skills", match_summary['matched_count'])
                with col3:
                    st.metric("Missing Skills", match_summary['missing_count'])
                with col4:
                    st.metric("Extra Skills", match_summary['extra_count'])
                
                # Skills breakdown
                if match_summary['matched_skills']:
                    st.success(f"✅ **Matched Skills:** {', '.join(match_summary['matched_skills'][:10])}")
                if match_summary['missing_skills']:
                    st.warning(f"⚠️ **Missing Skills:** {', '.join(match_summary['missing_skills'][:10])}")
                if match_summary['extra_skills']:
                    st.info(f"➕ **Your Extra Skills:** {', '.join(match_summary['extra_skills'][:10])}")
                
                # Category comparison chart
                st.subheader("📈 Skills by Category")
                category_fig = create_skill_category_chart(user_skills_for_chart, jd_skills)
                st.plotly_chart(category_fig, use_container_width=True)
                
            except Exception as e:
                st.error(f"Error creating radar chart: {str(e)}")
                st.write("Radar chart creation failed, but other analysis continues...")

            # 5) Enhanced Rules-based Analysis
            rules_analysis = scored.get("rules_analysis", {})
            if rules_analysis:
                with st.expander("🔍 Detailed Match Analysis"):
                    # Show rule-by-rule breakdown
                    rule_results = rules_analysis.get("rule_results", [])
                    if rule_results:
                        for rule_result in rule_results:
                            rule_name = rule_result.get("rule_name", "")
                            rule_score = rule_result.get("score", 0)
                            rule_explanation = rule_result.get("explanation", "")
                            rule_matches = rule_result.get("matches", [])
                            
                            st.write(f"**{rule_name}** (Score: {rule_score:.1f})")
                            st.write(rule_explanation)
                            if rule_matches:
                                st.write("Matches:", ", ".join(rule_matches[:3]))
                            st.divider()
                
                # Show expert recommendations
                recommendations = scored.get("recommendations", [])
                if recommendations:
                    st.subheader("🎯 Expert Recommendations")
                    for rec in recommendations:
                        st.markdown(f"• {rec}")

            # 6) AI-filtered learning skills → links
            missing_raw = scored.get("missing", []) or []
            ai_skills = pick_trainable_skills_ai(missing_raw, resume_text, job_description)

            if ai_skills:
                st.subheader("📚 Skill Boost – Targeted Learning")
                st.markdown("To improve your fit for roles like this, start with:")
                for s in ai_skills:
                    q = s.replace(" ", "+")
                    st.markdown(
                        f"- **{s}** — "
                        f"[Coursera](https://www.coursera.org/search?query={q}) · "
                        f"[edX](https://www.edx.org/search?q={q}) · "
                        f"[Udemy](https://www.udemy.com/courses/search/?q={q})"
                    )
            else:
                st.info("No critical, trainable gaps detected. Tweak resume keywords as suggested and apply confidently.")
