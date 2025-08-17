import streamlit as st
from backend.resume_praser import extract_text_from_pdf, extract_text_from_docx  # keep your current module name
from backend.job_fetcher import fetch_jobs
from backend.expert_system import score_from_skill_lists
from backend.rag_matcher import llm_analysis, extract_skills

# ---------------- Page config ----------------
st.set_page_config(page_title="FitFinder", page_icon=":briefcase:", layout="wide")

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

/* Fancy green buttons (all st.button) */
.stButton > button {
  background: #22a06b !important; color: #fff !important; font-weight: 700 !important;
  border: none !important; border-radius: 12px !important; padding: 10px 18px !important;
  box-shadow: 0 8px 18px rgba(34,160,107,0.25) !important;
}
.stButton > button:hover { background:#1b8a5c !important; }

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

/* Small pill badge (use later if needed) */
.badge {
  display:inline-block; background:#eef2ff; color:#3a41a6;
  padding:4px 8px; border-radius:8px; margin-right:6px; font-size:12px; font-weight:600;
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
st.image("logo.png", width=180)  # bigger logo; ensure logo.png is beside app.py
st.markdown("<h1>FitFinder – Find job that suits you</h1>", unsafe_allow_html=True)
st.markdown('<p class="subtitle">Upload your resume, find roles, and get clear skill insights.</p>', unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)
st.markdown("<hr/>", unsafe_allow_html=True)

# ---------------- Session state (so resume/jobs persist across clicks) ----------------
if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""
if "jobs" not in st.session_state:
    st.session_state.jobs = []

# ---------------- Upload Resume ----------------
uploaded_file = st.file_uploader("Upload your Resume (PDF or DOCX)", type=["pdf", "docx"])

if uploaded_file:
    if uploaded_file.type == "application/pdf":
        st.session_state.resume_text = extract_text_from_pdf(uploaded_file)
    else:
        st.session_state.resume_text = extract_text_from_docx(uploaded_file)
    st.success("✅ Resume uploaded successfully!")

resume_text = st.session_state.resume_text

# ---------------- Job Input (renamed radio options) ----------------
job_option = st.radio("Select Job Input Method", ["Find Jobs", "Analyze Job Description"])

job_description = ""
jobs = []

# ---------------- Find Jobs (resume required to run) ----------------
if job_option == "Find Jobs":
    query = st.text_input("Enter Job Title (e.g. Data Scientist, Web Developer)")

    # Fancy green button with icon (kept)
    if st.button("🔎 Find Jobs"):
        if not resume_text:
            st.warning("⚠️ Please upload your resume first so I can find matching jobs for you.")
        else:
            jobs = fetch_jobs(query) if query else []
            st.session_state.jobs = jobs

    # Render fetched jobs (Apply links) — no score here
    if st.session_state.jobs:
        for i, job in enumerate(st.session_state.jobs, start=1):
            title = job.get("title", "Untitled Role")
            company = job.get("company", "Company")
            desc = job.get("description", "")
            url = job.get("url") or job.get("redirect_url") or "#"

            st.markdown("<div class='job-card'>", unsafe_allow_html=True)
            st.markdown(f"**{i}. {title}** — *{company}*")
            st.write(desc[:320] + ("..." if len(desc) > 320 else ""))
            st.markdown(f"[👉 Apply here]({url})")
            st.markdown("</div>", unsafe_allow_html=True)

# ---------------- Analyze pasted Job Description (resume required to run) ----------------
elif job_option == "Analyze Job Description":
    job_description = st.text_area("Paste Job Description here", height=220)

# ---------------- Match Resume with Job (kept your button behavior) ----------------
# Button label mirrors your flow but uses fancy style from CSS above
if st.button("📊 Analyze Match" if job_option == "Analyze Job Description" else "Match Resume"):
    if not resume_text:
        st.warning("⚠️ Please upload resume first.")
    elif job_option == "Analyze Job Description" and not job_description.strip():
        st.warning("Please paste a job description.")
    else:
        # Case A: Analyze pasted JD → show matched/lacking/recommendations from your current pipeline
        if job_option == "Analyze Job Description" and job_description:
            # Still using your current extractor + scorer (no semicircle chart)
            resume_skills = extract_skills(resume_text, source="resume")
            jd_skills = extract_skills(job_description, source="job")
            scored = score_from_skill_lists(resume_skills, jd_skills)  # {'score','matched','missing'}

            st.subheader("✅ Matching Skills")
            st.write(", ".join(scored["matched"]) if scored["matched"] else "None detected.")

            st.subheader("❌ Lacking Skills")
            st.write(", ".join(scored["missing"]) if scored["missing"] else "None detected.")

            st.subheader("💡 Recommendations")
            if scored["missing"]:
                st.markdown("To improve your fit for roles like this, learn:")
                for s in scored["missing"][:8]:
                    q = s.replace(" ", "+")
                    st.markdown(
                        f"- **{s.title()}** — learn via "
                        f"[Coursera](https://www.coursera.org/search?query={q}) · "
                        f"[edX](https://www.edx.org/search?q={q}) · "
                        f"[Udemy](https://www.udemy.com/courses/search/?q={q}) · "
                        f"[Official docs](https://www.google.com/search?q={q}+official+documentation)"
                    )
            else:
                st.write("Looks great! Apply now and tailor your resume to emphasize these matched strengths.")

        # Case B: If you also want to match against the fetched jobs (optional)
        elif job_option == "Find Jobs" and st.session_state.jobs:
            for job in st.session_state.jobs:
                # keep your existing analysis here if you still want it:
                expert_result = score_from_skill_lists(
                    extract_skills(resume_text, "resume"),
                    extract_skills(job.get("description",""), "job")
                )
                st.subheader(f"🔍 Expert System Match for {job.get('title','Role')}: {expert_result['score']} / 100")
                st.write(f"✅ Matched: {expert_result['matched']}")
                st.write(f"❌ Missing: {expert_result['missing']}")
                rag_result = llm_analysis(resume_text, job.get("description",""), expert_result)
                st.write("💡 Guidance:")
                st.write(rag_result)
                st.markdown("<hr/>", unsafe_allow_html=True)
        else:
            st.warning("Please paste a job description or use Find Jobs first.")
