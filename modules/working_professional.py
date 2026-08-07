"""
Streamlit UI for the Working Professional Module.
"""
import streamlit as st
import json
import time
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from database import db_session, User
from modules.wp_models import (
    WP_ProfessionalProfile, WP_SkillAssessment, WP_RoleRequirement,
    WP_TrendingSkill, WP_Certification, WP_SalaryBenchmark,
    WP_ResumeAnalysis, WP_LeadershipEvaluation, WP_CareerCoachChat
)
from modules.wp_logic import (
    calculate_promotion_readiness, match_career_transition,
    get_salary_growth, recommend_certifications, generate_action_plan,
    advanced_job_matching, extract_text_from_file, analyze_working_prof_resume,
    evaluate_leadership_skills, CareerCoachEngine, LEADERSHIP_DIMENSIONS
)
from modules.wp_report import generate_growth_opportunity_pdf


# Navigation Item Definitions
NAV_ITEMS = [
    ("👤 Overview & Profile", "overview"),
    ("📈 Promotion & Salary", "promotion"),
    ("🔄 Career Transition", "transition"),
    ("📊 Growth Summary", "growth"),
    ("📄 Resume Update Assistant", "resume"),
    ("🤖 AI Career Coach", "coach"),
    ("👑 Leadership Evaluation", "leadership"),
]


# =============================================================================
# SECTION 1: OVERVIEW & PROFILE
# =============================================================================
def render_overview_and_profile(user_id, username, user_obj, profile, assessments):
    with st.container(border=True):
        st.subheader("👤 Professional Profile")
    with st.expander("Update Profile", expanded=profile is None):
        with st.form("prof_profile_form"):
            col1, col2 = st.columns(2)
            with col1:
                full_name = st.text_input("Full Name", value=user_obj.full_name if user_obj and user_obj.full_name else "")
                company = st.text_input("Current Company", value=profile.current_company if profile else "")
                role = st.text_input("Current Role", value=profile.current_role if profile else "")
                exp = st.number_input("Total Experience (Years)", min_value=0.0, step=0.5, value=profile.total_experience_years if profile and profile.total_experience_years else 0.0)
                tech_skills = st.text_input("Technical Skills (comma-separated)", value=profile.technical_skills if profile else "")
            with col2:
                certs_input = st.text_input("Certifications (comma-separated)", value=profile.certifications if profile else "")
                pref_roles = st.text_input("Preferred Job Roles (comma-separated)", value=profile.preferred_job_roles if profile else "")
                goals = st.text_area("Career Goals", value=profile.career_goals if profile else "")
                has_lead = st.checkbox("Leadership Experience?", value=profile.leadership_experience if profile else False)
                lead_desc = st.text_input("Leadership Description", value=profile.leadership_description if profile else "")
                
            submit_prof = st.form_submit_button("Save Profile")
            if submit_prof:
                with db_session() as sess:
                    p = sess.query(WP_ProfessionalProfile).filter_by(user_id=user_id).first()
                    if not p:
                        p = WP_ProfessionalProfile(user_id=user_id)
                        sess.add(p)
                    p.current_company = company
                    p.current_role = role
                    p.total_experience_years = exp
                    p.technical_skills = tech_skills
                    p.certifications = certs_input
                    p.preferred_job_roles = pref_roles
                    p.career_goals = goals
                    p.leadership_experience = has_lead
                    p.leadership_description = lead_desc
                    
                    u = sess.query(User).filter_by(id=user_id).first()
                    if u:
                        u.full_name = full_name
                st.success("Profile saved successfully!")
                st.rerun()

    with st.container(border=True):
        st.subheader("📊 Skill Assessment")
    with st.expander("Evaluate Skills", expanded=len(assessments) == 0):
        with st.form("skill_assess_form"):
            st.write("Rate your technical competencies (0-100):")
            col_a, col_b = st.columns(2)
            skills_input = {}
            preset_skills = ["Backend Development", "System Design", "Cloud Computing", "DevOps", "Leadership"]
            
            for i, skill in enumerate(preset_skills):
                col = col_a if i % 2 == 0 else col_b
                existing_score = next((a.score for a in assessments if a.skill_area == skill), 50.0)
                skills_input[skill] = col.slider(skill, 0, 100, int(existing_score))
            
            submit_skills = st.form_submit_button("Save Skill Assessment")
            if submit_skills:
                with db_session() as sess:
                    # Clear old
                    sess.query(WP_SkillAssessment).filter_by(user_id=user_id).delete()
                    for s_name, s_val in skills_input.items():
                        sess.add(WP_SkillAssessment(user_id=user_id, skill_area=s_name, score=float(s_val)))
                st.success("Skills updated!")
                st.rerun()
                
    if assessments:
        data = {"Skill Area": [a.skill_area for a in assessments], "Score": [a.score for a in assessments]}
        fig = px.bar(data, x="Score", y="Skill Area", orientation='h', range_x=[0, 100])
        fig.update_traces(marker_color='#1F9D77')
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#12213B')
        )
        st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# SECTION 2: PROMOTION & SALARY
# =============================================================================
def render_promotion_and_salary(assessments, profile, readiness, best_match, benchmarks):
    with st.container(border=True):
        st.subheader("📈 Promotion Readiness Analysis")
        if not assessments or not profile:
            st.info("Please complete your Profile and Skill Assessment first.")
        else:
            c1, c2, c3 = st.columns(3)
            c1.metric("Overall Readiness", f"{readiness['Promotion Readiness %']}%")
            c2.metric("Technical Readiness", f"{int(readiness['Technical Readiness'])}%")
            c3.metric("Leadership Readiness", f"{int(readiness['Leadership Readiness'])}%")
            
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=readiness["Promotion Readiness %"],
                title={'text': "Promotion Probability Score"},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "#1F9D77"},
                    'steps': [
                        {'range': [0, 50], 'color': "#f4f4f4"},
                        {'range': [50, 75], 'color': "#e2f0d9"},
                        {'range': [75, 100], 'color': "#c5e0b4"}
                    ]
                }
            ))
            fig_gauge.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#12213B'), height=300)
            st.plotly_chart(fig_gauge, use_container_width=True)

    with st.container(border=True):
        st.subheader("💰 Salary Benchmark Insights")
        curr_sal = st.number_input("Your Current CTC (LPA in ₹)", min_value=0.0, step=0.5, value=12.0)
        if best_match and best_match != "Pending Assessment":
            growth = get_salary_growth(curr_sal, best_match, benchmarks)
        else:
            growth = None
            
        if growth:
            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric("Market Average", f"₹{growth['Market Average']} LPA")
            col_m2.metric("Target Range", growth["Target Range"])
            col_m3.metric("Potential Growth", f"+{growth['Potential Growth %']}%")
        else:
            st.info("Benchmark data will appear after setting your career goals or completing assessments.")


# =============================================================================
# SECTION 3: CAREER TRANSITION
# =============================================================================
def render_career_transition(matches, trending_skills, roles, certs, skill_scores, best_match):
    with st.container(border=True):
        st.subheader("🚀 AI Career Transition Suggestions")
        if not matches:
            st.info("No matches available yet. Complete your skills assessment.")
        else:
            st.markdown("**Top Matching Target Roles**")
            match_data = {"Next Role": [m["Next Role"] for m in matches], "Match %": [f"{m['Match %']}%" for m in matches]}
            st.dataframe(match_data, use_container_width=True, hide_index=True)
            
    with st.container(border=True):
        st.subheader("📊 Industry Trend Recommendations")
        if trending_skills:
            ts_data = {"Skill": [t.skill_name for t in trending_skills], "Growth %": [t.demand_growth_percent for t in trending_skills]}
            fig2 = px.bar(ts_data, x="Skill", y="Growth %", title="Demand Growth in Tech Sector")
            fig2.update_traces(marker_color='#1F9D77')
            fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#12213B'))
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No trending skills configured.")
            
    with st.container(border=True):
        st.subheader("📜 Certification Suggestions")
        if best_match and best_match != "Pending Assessment":
            best_role_obj = next((r for r in roles if r.role_name == best_match), None)
            rec_certs = recommend_certifications(skill_scores, best_role_obj, certs)
            if rec_certs:
                st.dataframe(rec_certs, use_container_width=True, hide_index=True)
            else:
                st.info("No missing certifications for top match.")


# =============================================================================
# SECTION 4: GROWTH SUMMARY
# =============================================================================
def render_growth_summary(user_id, username, assessments, profile, matches, best_match, benchmarks, readiness, readiness_pct, skill_scores, certs, roles):
    with st.container(border=True):
        st.subheader("📋 Growth Opportunity Analysis")
        if not assessments or not profile or not matches:
            st.info("Not enough data to generate summary. Please complete your profile and assessment.")
        else:
            best_match_name = matches[0]["Next Role"]
            growth = get_salary_growth(12.0, best_match_name, benchmarks)
            sal_growth_pct = growth["Potential Growth %"] if growth else 0
            
            strong = [k for k, v in skill_scores.items() if v >= 75]
            improve = [k for k, v in skill_scores.items() if v < 75]
            
            best_role_obj = next((r for r in roles if r.role_name == best_match_name), None)
            rec_certs = recommend_certifications(skill_scores, best_role_obj, certs)
            action_plan = generate_action_plan(skill_scores)
            
            # Display Summary Card
            st.markdown(f"""
            ### Professional Snapshot
            - **Current Role**: {profile.current_role or 'Software Engineer'}
            - **Experience**: {profile.total_experience_years or 0} Years
            - **Promotion Readiness**: {readiness_pct}%
            - **Salary Growth Potential**: +{sal_growth_pct}%
            - **Top Job Match**: {best_match_name} ({matches[0]['Match %']}%)
            """)
            
            st.subheader("Current Skill Progress")
            for k, v in skill_scores.items():
                st.progress(v / 100, text=f"{k}: {int(v)}%")
            
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                st.subheader("💪 Strong Areas")
                for s in strong: st.write(f"✅ {s}")
            with col_s2:
                st.subheader("🎯 Improvement Areas")
                for s in improve: st.write(f"⚡ {s}")
                
            if action_plan:
                st.subheader("📅 90-Day Action Plan")
                for item in action_plan:
                    st.write(f"**{item['Month']}**: {item['Focus']}")
                    
            # PDF Generation
            pdf_buffer = generate_growth_opportunity_pdf(
                user_name=username,
                current_role=profile.current_role or "Professional",
                next_best_role=best_match_name,
                promotion_ready_pct=readiness_pct,
                salary_growth_pct=sal_growth_pct,
                strong_areas=strong,
                improvement_areas=improve,
                recommended_certs=rec_certs,
                action_plan=action_plan
            )
            
            st.download_button(
                label="📥 Download Growth Opportunity PDF",
                data=pdf_buffer,
                file_name=f"{username}_Growth_Analysis.pdf",
                mime="application/pdf"
            )


# =============================================================================
# SECTION 5: RESUME UPDATE ASSISTANT
# =============================================================================
def render_resume_assistant(user_id, username, profile, trending_skills, roles, latest_resume):
    with st.container(border=True):
        st.subheader("📄 Resume Update Assistant")
        st.caption("Scan and evaluate your resume against real-time industry benchmarks, detect outdated skills, and get ATS-optimized suggestions.")

    uploaded_file = st.file_uploader(
        "Upload Your Latest Resume (PDF or DOCX)",
        type=["pdf", "docx"],
        key="wp_resume_uploader",
        help="Upload your resume to perform deep AI gap analysis and ATS optimization."
    )

    analysis_result = None

    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        filename = uploaded_file.name
        file_ext = filename.split(".")[-1].lower()

        with st.spinner("🔍 Extracting text and performing comprehensive AI resume analysis..."):
            extracted_text = extract_text_from_file(file_bytes, filename)
            if not extracted_text:
                st.error("Could not extract text from the uploaded file. Please ensure it is a valid PDF or DOCX file.")
            else:
                analysis_result = analyze_working_prof_resume(
                    resume_text=extracted_text,
                    user_profile=profile,
                    trending_skills=trending_skills,
                    role_requirements=roles
                )

                # Save to Database
                with db_session() as sess:
                    db_record = WP_ResumeAnalysis(
                        user_id=user_id,
                        filename=filename,
                        file_type=file_ext,
                        completeness_score=analysis_result["completeness_score"],
                        extracted_skills=json.dumps(analysis_result["extracted_skills"]),
                        missing_skills=json.dumps(analysis_result["missing_skills"]),
                        outdated_skills=json.dumps(analysis_result["outdated_skills"]),
                        recommended_skills=json.dumps([r["skill"] for r in analysis_result["recommended_skills"]]),
                        suggestions_json=json.dumps({
                            "summary": analysis_result["summary_suggestion"],
                            "tech_skills": analysis_result["tech_skills_suggestion"],
                            "projects": analysis_result["project_suggestions"],
                            "experience": analysis_result["experience_suggestions"],
                            "certs": analysis_result["cert_suggestions"],
                            "ats_tips": analysis_result["ats_tips"]
                        })
                    )
                    sess.add(db_record)
                st.success(f"✅ Successfully analyzed **{filename}** and updated your professional insights!")
    
    elif latest_resume:
        # Load cached previous analysis
        try:
            cached_extracted = json.loads(latest_resume.extracted_skills or "[]")
            cached_missing = json.loads(latest_resume.missing_skills or "[]")
            cached_outdated = json.loads(latest_resume.outdated_skills or "[]")
            cached_rec_names = json.loads(latest_resume.recommended_skills or "[]")
            cached_suggestions = json.loads(latest_resume.suggestions_json or "{}")

            analysis_result = {
                "completeness_score": latest_resume.completeness_score,
                "extracted_skills": cached_extracted,
                "extracted_by_category": {},
                "missing_skills": cached_missing,
                "outdated_skills": cached_outdated,
                "recommended_skills": [{"skill": s, "growth": "+30%", "reason": "High market demand"} for s in cached_rec_names],
                "summary_suggestion": cached_suggestions.get("summary", ""),
                "tech_skills_suggestion": cached_suggestions.get("tech_skills", []),
                "project_suggestions": cached_suggestions.get("projects", []),
                "experience_suggestions": cached_suggestions.get("experience", []),
                "cert_suggestions": cached_suggestions.get("certs", []),
                "ats_tips": cached_suggestions.get("ats_tips", []),
                "download_text": f"# RESUME ANALYSIS ({latest_resume.filename})\nCompleteness: {latest_resume.completeness_score}/100",
                "section_checklist": {
                    "Contact Details": True,
                    "Professional Summary": True,
                    "Technical Skills": len(cached_extracted) >= 3,
                    "Work Experience": True,
                    "Projects": True,
                    "Education": True,
                    "Certifications": True,
                    "Measurable Metrics": True
                }
            }
            st.info(f"📁 Showing previous analysis for: `{latest_resume.filename}` (Uploaded: {latest_resume.uploaded_at.strftime('%Y-%m-%d %H:%M')})")
        except Exception:
            analysis_result = None

    # Render Analysis Results
    if analysis_result:
        score = analysis_result["completeness_score"]

        # Top Score Metrics
        r_col1, r_col2, r_col3, r_col4 = st.columns(4)
        with r_col1:
            st.metric("Completeness Score", f"{score}/100")
        with r_col2:
            st.metric("Extracted Skills", len(analysis_result["extracted_skills"]))
        with r_col3:
            st.metric("Missing Industry Skills", len(analysis_result["missing_skills"]))
        with r_col4:
            outdated_count = len(analysis_result["outdated_skills"])
            st.metric("Legacy / Outdated Skills", outdated_count, delta=None if outdated_count == 0 else f"{outdated_count} detected", delta_color="inverse")

        # Improvement Progress Bar
        st.markdown("#### 🎯 Resume Completeness & ATS Quality Bar")
        st.progress(score / 100, text=f"Resume Score: {score}% — {'🌟 Excellent ATS Profile' if score >= 80 else '⚠️ Needs Optimization' if score < 60 else '👍 Good Baseline'}")

        # Section Checklist Pills
        st.markdown("##### Section Verification Checklist:")
        chk_cols = st.columns(4)
        for idx, (sec_name, is_present) in enumerate(analysis_result.get("section_checklist", {}).items()):
            c = chk_cols[idx % 4]
            if is_present:
                c.markdown(f"✅ **{sec_name}**")
            else:
                c.markdown(f"❌ <span style='color:#d9534f'>**{sec_name}**</span>", unsafe_allow_html=True)

        # Extracted Skills Display
        with st.container(border=True):
            st.subheader("🛠️ Extracted Technical & Leadership Skills")
            if analysis_result["extracted_skills"]:
                st.write(", ".join([f"`{s}`" for s in analysis_result["extracted_skills"]]))
            else:
                st.warning("No recognized technical keywords were detected. Consider adding industry standard terms.")

        # Industry Gap Analysis: Missing, Outdated, and Recommended
        with st.container(border=True):
            st.subheader("⚡ Industry Demand & Skill Gap Analysis")
            gap_c1, gap_c2, gap_c3 = st.columns(3)
            
            with gap_c1:
                st.markdown("##### 🔴 Missing In-Demand Skills")
                if analysis_result["missing_skills"]:
                    for ms in analysis_result["missing_skills"]:
                        st.markdown(f"- ⚠️ **{ms}**")
                else:
                    st.success("Great job! All core skills present.")
                    
            with gap_c2:
                st.markdown("##### ⚠️ Outdated / Legacy Skills")
                if analysis_result["outdated_skills"]:
                    for os_skill in analysis_result["outdated_skills"]:
                        st.markdown(f"- ⛔ **{os_skill}** *(Replace with modern alternative)*")
                else:
                    st.success("No legacy or obsolete technologies found.")
                    
            with gap_c3:
                st.markdown("##### 🟢 Recommended Skills")
                for rec in analysis_result["recommended_skills"]:
                    st.markdown(f"- **{rec['skill']}** ({rec['growth']})")

        # Section-by-Section Improvement Suggestions
        with st.container(border=True):
            st.subheader("💡 Section-by-Section Improvement Suggestions")
            
            with st.expander("📝 Professional Summary Optimization", expanded=True):
                st.markdown(analysis_result["summary_suggestion"])
                
            with st.expander("🛠️ Technical Skills Structure", expanded=False):
                for tip in analysis_result["tech_skills_suggestion"]:
                    st.markdown(f"- {tip}")
                    
            with st.expander("🚀 Projects & System Architecture (STAR Format)", expanded=False):
                for tip in analysis_result["project_suggestions"]:
                    st.markdown(f"- {tip}")
                    
            with st.expander("💼 Professional Experience & Business Impact", expanded=False):
                for tip in analysis_result["experience_suggestions"]:
                    st.markdown(f"- {tip}")
                    
            with st.expander("📜 Recommended Certifications to Boost ATS Rank", expanded=False):
                for tip in analysis_result["cert_suggestions"]:
                    st.markdown(f"- 🎓 **{tip}**")

        # ATS Improvement Tips
        with st.container(border=True):
            st.subheader("🤖 ATS (Applicant Tracking System) Best Practices")
            for tip in analysis_result["ats_tips"]:
                st.markdown(tip)

        # Download Improved Suggestions Button
        st.download_button(
            label="📥 Download Resume Improvement Report",
            data=analysis_result.get("download_text", "Resume Improvement Report"),
            file_name=f"{username}_Resume_Improvement_Report.md",
            mime="text/markdown"
        )
    else:
        st.info("👆 Please upload your resume in PDF or DOCX format above to generate a comprehensive gap analysis and ATS optimization plan.")


# =============================================================================
# SECTION 6: AI CAREER COACH
# =============================================================================
def render_ai_career_coach(user_id, username, profile, best_match, skill_scores, readiness_pct, growth_potential_str, chat_records):
    with st.container(border=True):
        st.subheader("🤖 AI Career Coach")
        st.caption("Your 24/7 intelligent career advisor for promotions, transitions, skill gaps, and salary benchmarks.")

    coach_engine = CareerCoachEngine()

    # Build comprehensive live profile context for AI Coach
    coach_context = {
        "current_role": profile.current_role if profile and profile.current_role else "Software Engineer",
        "experience": profile.total_experience_years if profile and profile.total_experience_years else 3.5,
        "career_goal": profile.career_goals if profile and profile.career_goals else (best_match if best_match else "Senior Backend Engineer"),
        "skill_scores": skill_scores,
        "promotion_readiness": readiness_pct,
        "best_match": best_match,
        "salary_growth": growth_potential_str
    }

    # Initialize session state chat messages from DB if not loaded
    if "wp_chat_messages" not in st.session_state:
        st.session_state.wp_chat_messages = [
            {"role": r.role, "message": r.message} for r in chat_records
        ]

    # Suggested Questions Bar (Quick Prompts)
    st.markdown("##### 💡 Suggested Questions")
    prompt_cols = st.columns(3)
    suggested_queries = [
        ("🚀 How do I become Senior Backend Engineer?", "How do I become Senior Backend Engineer?"),
        ("📜 What certification should I do?", "What certification should I do?"),
        ("🐍 What should I learn after Python?", "What should I learn after Python?"),
        ("📈 How can I get promoted?", "How can I get promoted?"),
        ("💰 What salary can I expect?", "What salary can I expect?"),
        ("🎯 How to bridge my skill gap?", "How to bridge my skill gap?")
    ]

    clicked_prompt = None
    for i, (btn_label, query_text) in enumerate(suggested_queries):
        with prompt_cols[i % 3]:
            if st.button(btn_label, key=f"quick_prompt_{i}", use_container_width=True):
                clicked_prompt = query_text

    # Clear Chat Button
    top_btn_c1, top_btn_c2 = st.columns([8, 2])
    with top_btn_c2:
        if st.button("🗑️ Clear Chat History", key="clear_chat_wp"):
            with db_session() as sess:
                sess.query(WP_CareerCoachChat).filter_by(user_id=user_id).delete()
            st.session_state.wp_chat_messages = []
            st.rerun()

    # Display Chat History
    chat_container = st.container()
    with chat_container:
        if not st.session_state.wp_chat_messages:
            with st.chat_message("assistant", avatar="💼"):
                st.markdown(
                    f"👋 **Hello {username}!** I am your **AI Career Coach**.\n\n"
                    f"I have live access to your profile (*{coach_context['current_role']}*, *{coach_context['experience']} Yrs Exp*, *{readiness_pct}% Promotion Readiness*). "
                    f"Ask me about **career transitions**, **salary negotiation**, **promotion strategies**, **certifications**, or click any suggested question above to get started!"
                )

        for msg in st.session_state.wp_chat_messages:
            avatar = "🧑‍💼" if msg["role"] == "user" else "💼"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["message"])

    # Process user query (either from chat_input or clicked suggested prompt)
    user_query = st.chat_input("Ask your AI Career Coach...")
    if clicked_prompt:
        user_query = clicked_prompt

    if user_query:
        # Display and store user message
        with st.chat_message("user", avatar="🧑‍💼"):
            st.markdown(user_query)

        st.session_state.wp_chat_messages.append({"role": "user", "message": user_query})
        with db_session() as sess:
            sess.add(WP_CareerCoachChat(user_id=user_id, role="user", message=user_query))

        # Generate Assistant Response
        with st.chat_message("assistant", avatar="💼"):
            with st.spinner("AI Coach is formulating your career strategy..."):
                coach_response = coach_engine.get_response(
                    user_query=user_query,
                    context=coach_context,
                    history=st.session_state.wp_chat_messages
                )
                st.markdown(coach_response)

        st.session_state.wp_chat_messages.append({"role": "assistant", "message": coach_response})
        with db_session() as sess:
            sess.add(WP_CareerCoachChat(user_id=user_id, role="assistant", message=coach_response))


# =============================================================================
# SECTION 7: LEADERSHIP EVALUATION
# =============================================================================
def render_leadership_evaluation(user_id, leadership_eval):
    with st.container(border=True):
        st.subheader("⭐ Leadership Skill Evaluation")
        st.caption("Evaluate your competencies across 7 core leadership dimensions to measure Tech Lead, Architecture, and Engineering Management readiness.")

    # Default values from DB if available
    init_scores = {
        "Team Coordination": leadership_eval.team_coordination if leadership_eval else 70.0,
        "Mentoring": leadership_eval.mentoring if leadership_eval else 65.0,
        "Decision Making": leadership_eval.decision_making if leadership_eval else 75.0,
        "Conflict Resolution": leadership_eval.conflict_resolution if leadership_eval else 60.0,
        "Project Ownership": leadership_eval.project_ownership if leadership_eval else 80.0,
        "Communication": leadership_eval.communication if leadership_eval else 75.0,
        "Strategic Thinking": leadership_eval.strategic_thinking if leadership_eval else 70.0
    }

    # 7 Interactive Sliders in Form
    with st.expander("⚙️ Adjust Leadership Competency Sliders", expanded=True):
        with st.form("leadership_eval_form"):
            st.write("Rate your proficiency in each leadership dimension (0-100):")
            lead_col1, lead_col2 = st.columns(2)
            
            slider_scores = {}
            for i, dim in enumerate(LEADERSHIP_DIMENSIONS):
                target_col = lead_col1 if i % 2 == 0 else lead_col2
                slider_scores[dim] = target_col.slider(
                    f"**{dim}**",
                    min_value=0,
                    max_value=100,
                    value=int(init_scores.get(dim, 50.0)),
                    help=f"Assess your capabilities in {dim}."
                )
                
            save_lead_btn = st.form_submit_button("💾 Save Leadership Assessment")
            if save_lead_btn:
                eval_data = evaluate_leadership_skills(slider_scores)
                with db_session() as sess:
                    lead_record = sess.query(WP_LeadershipEvaluation).filter_by(user_id=user_id).first()
                    if not lead_record:
                        lead_record = WP_LeadershipEvaluation(user_id=user_id)
                        sess.add(lead_record)
                    lead_record.team_coordination = float(slider_scores["Team Coordination"])
                    lead_record.mentoring = float(slider_scores["Mentoring"])
                    lead_record.decision_making = float(slider_scores["Decision Making"])
                    lead_record.conflict_resolution = float(slider_scores["Conflict Resolution"])
                    lead_record.project_ownership = float(slider_scores["Project Ownership"])
                    lead_record.communication = float(slider_scores["Communication"])
                    lead_record.strategic_thinking = float(slider_scores["Strategic Thinking"])
                    lead_record.overall_score = eval_data["overall_score"]
                    lead_record.grade = eval_data["grade"]
                    lead_record.promotion_impact = eval_data["promotion_impact"]
                    
                    # Sync Leadership skill into WP_SkillAssessment
                    lead_skill = sess.query(WP_SkillAssessment).filter_by(user_id=user_id, skill_area="Leadership").first()
                    if not lead_skill:
                        lead_skill = WP_SkillAssessment(user_id=user_id, skill_area="Leadership", score=eval_data["overall_score"])
                        sess.add(lead_skill)
                    else:
                        lead_skill.score = eval_data["overall_score"]

                st.success("✅ Leadership evaluation saved! Top metrics and promotion scores updated.")
                st.rerun()

    # Compute Live Evaluation Analytics
    current_eval = evaluate_leadership_skills(init_scores)

    # Top Metric Cards
    l_col1, l_col2, l_col3, l_col4 = st.columns(4)
    with l_col1:
        st.metric("Overall Leadership Score", f"{current_eval['overall_score']} / 100")
    with l_col2:
        st.metric("Leadership Grade", current_eval["grade"].split()[0] + " Level")
    with l_col3:
        st.metric("Promotion Impact", f"+{current_eval['promotion_impact']}%")
    with l_col4:
        st.metric("Leadership Maturity", "Tech Lead Ready" if current_eval['overall_score'] >= 75 else "Developing")

    # Visual Analytics: Radar & Bar Charts
    with st.container(border=True):
        st.subheader("📊 Leadership Analytics & Benchmarking")
        chart_c1, chart_c2 = st.columns(2)
        
        # Radar Chart
        with chart_c1:
            st.markdown("##### 🕸️ 7-Dimension Leadership Radar")
            categories = list(current_eval["scores"].keys())
            values = list(current_eval["scores"].values())
            
            # Close the radar loop
            categories_loop = categories + [categories[0]]
            values_loop = values + [values[0]]
            
            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=values_loop,
                theta=categories_loop,
                fill='toself',
                fillcolor='rgba(31, 157, 119, 0.25)',
                line=dict(color='#1F9D77', width=2),
                name='Current Score'
            ))
            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, 100], color='#12213B')
                ),
                showlegend=False,
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#12213B'),
                height=350,
                margin=dict(l=40, r=40, t=30, b=30)
            )
            st.plotly_chart(fig_radar, use_container_width=True)

        # Bar Chart with Senior Benchmark
        with chart_c2:
            st.markdown("##### 📊 Competency vs. Senior Benchmark (75)")
            bar_data = {
                "Dimension": list(current_eval["scores"].keys()),
                "Score": list(current_eval["scores"].values())
            }
            fig_bar = px.bar(bar_data, x="Score", y="Dimension", orientation='h', range_x=[0, 100])
            fig_bar.update_traces(marker_color='#1F9D77')
            fig_bar.add_vline(x=75, line_dash="dash", line_color="#E74C3C", annotation_text="Senior Lead Bar (75)")
            fig_bar.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#12213B'),
                height=350,
                margin=dict(l=40, r=40, t=30, b=30)
            )
            st.plotly_chart(fig_bar, use_container_width=True)

    # Dynamic AI Leadership Insights
    with st.container(border=True):
        st.subheader("💡 Dynamic AI Leadership Insights")
        st.info(f"**Readiness Assessment:** {current_eval['readiness_status']}")
        
        ins_col1, ins_col2 = st.columns(2)
        with ins_col1:
            st.markdown("##### 🌟 Strong Leadership Areas (>= 75)")
            if current_eval["strong_areas"]:
                for s in current_eval["strong_areas"]:
                    st.markdown(f"- ✅ **{s}**: Exceeds standard baseline for technical leads.")
            else:
                st.write("Keep practicing to elevate key competencies above 75.")
                
        with ins_col2:
            st.markdown("##### ⚡ Growth Focus Areas (< 75)")
            if current_eval["weak_areas"]:
                for w in current_eval["weak_areas"]:
                    st.markdown(f"- 🎯 **{w}**: Key priority for accelerating promotion.")
            else:
                st.success("All dimensions are at or above senior leadership benchmarks!")

        # Actionable Improvement Suggestions
        if current_eval["improvement_suggestions"]:
            st.markdown("##### 🛠️ Tailored Improvement Recommendations")
            for item in current_eval["improvement_suggestions"]:
                st.markdown(f"- **{item['area']}**: {item['tip']}")

    # Curated Leadership Courses
    with st.container(border=True):
        st.subheader("🎓 Recommended Leadership & Management Courses")
        for course in current_eval["recommended_courses"]:
            col_c1, col_c2 = st.columns([3, 1])
            with col_c1:
                st.markdown(f"**{course['name']}**")
                st.caption(f"Focus: {course['focus']}")
            with col_c2:
                st.badge(course['provider']) if hasattr(st, 'badge') else st.info(course['provider'])


# =============================================================================
# MAIN DASHBOARD ENTRY POINT
# =============================================================================
def show_dashboard(ai_engine=None):
    user_id = st.session_state.get('user_id')
    username = st.session_state.get('username')
    
    if not user_id:
        st.error("Authentication error. Please log in again.")
        return

    # Initialize navigation state
    if "wp_selected_page" not in st.session_state:
        st.session_state.wp_selected_page = "👤 Overview & Profile"

    # Sidebar User Profile & Navigation
    with st.sidebar:
        st.title("TalentSphere Elevate")
        st.markdown("---")
        st.write(f"👤 **{username}**")
        st.write(f"*{st.session_state.get('user_type', 'Working Professional')}*")
        st.divider()
        
        st.write("**Navigation**")
        nav_labels = [item[0] for item in NAV_ITEMS]
        current_idx = nav_labels.index(st.session_state.wp_selected_page) if st.session_state.wp_selected_page in nav_labels else 0
        sidebar_choice = st.radio(
            "Go to",
            options=nav_labels,
            index=current_idx,
            key="wp_sidebar_nav_radio",
            label_visibility="collapsed"
        )
        if sidebar_choice != st.session_state.wp_selected_page:
            st.session_state.wp_selected_page = sidebar_choice
            st.rerun()

        st.divider()
        if st.button("🚪 Logout", key="wp_sidebar_logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    # Top Header with Title and Logout button
    head_col1, head_col2 = st.columns([6, 1])
    with head_col1:
        st.title("💼 Working Professional Dashboard")
        st.caption(f"Welcome back, {username}! Navigate through your professional growth journey.")
    with head_col2:
        st.write("")  # Spacing
        if st.button("🚪 Logout", key="wp_header_logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()
    
    # Initialize DB Session and Data
    with db_session() as session:
        user_obj = session.query(User).filter_by(id=user_id).first()
        profile = session.query(WP_ProfessionalProfile).filter_by(user_id=user_id).first()
        assessments = session.query(WP_SkillAssessment).filter_by(user_id=user_id).all()
        roles = session.query(WP_RoleRequirement).all()
        trending_skills = session.query(WP_TrendingSkill).all()
        certs = session.query(WP_Certification).all()
        benchmarks = session.query(WP_SalaryBenchmark).all()
        leadership_eval = session.query(WP_LeadershipEvaluation).filter_by(user_id=user_id).first()
        latest_resume = session.query(WP_ResumeAnalysis).filter_by(user_id=user_id).order_by(WP_ResumeAnalysis.uploaded_at.desc()).first()
        chat_records = session.query(WP_CareerCoachChat).filter_by(user_id=user_id).order_by(WP_CareerCoachChat.created_at.asc()).all()
        
    # --- Calculate Top Metrics ---
    skill_scores = {a.skill_area: a.score for a in assessments} if assessments else {}
    
    # If leadership evaluation exists, use its overall score to enrich leadership score
    lead_score = leadership_eval.overall_score if leadership_eval else skill_scores.get("Leadership", 50)
    
    if assessments and profile:
        tech_avg = sum([v for k, v in skill_scores.items() if k != "Leadership"]) / max(1, len(skill_scores) - 1)
        readiness = calculate_promotion_readiness(
            years_exp=profile.total_experience_years or 0,
            project_complexity=75,
            leadership_score=lead_score,
            tech_score=tech_avg,
            comms_score=80,
            team_score=75
        )
        readiness_pct = readiness["Promotion Readiness %"]
    else:
        readiness = {"Promotion Readiness %": 0, "Technical Readiness": 0, "Leadership Readiness": 0}
        readiness_pct = 0
        
    matches = match_career_transition(skill_scores, roles) if skill_scores else []
    best_match = matches[0]["Next Role"] if matches else "Pending Assessment"
    
    growth_data = get_salary_growth(12.0, best_match, benchmarks) if (best_match and best_match != "Pending Assessment") else None
    growth_str = f"+{growth_data['Potential Growth %']}%" if growth_data else "+30%"
    
    # Header Summary Cards (always displayed at top)
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    with m_col1:
        st.metric("Promotion Readiness", f"{readiness_pct}%")
    with m_col2:
        st.metric("Top Job Match", best_match)
    with m_col3:
        st.metric("Skills Assessed", len(assessments))
    with m_col4:
        st.metric("Years Exp", f"{profile.total_experience_years if profile and profile.total_experience_years else 0} Yrs")
        
    st.write("")  # Visual vertical spacer

    # =========================================================================
    # RENDER SELECTED PAGE CONTENT DIRECTLY
    # =========================================================================
    current_page = st.session_state.wp_selected_page

    if current_page == "👤 Overview & Profile":
        render_overview_and_profile(user_id, username, user_obj, profile, assessments)

    elif current_page == "📈 Promotion & Salary":
        render_promotion_and_salary(assessments, profile, readiness, best_match, benchmarks)

    elif current_page == "🔄 Career Transition":
        render_career_transition(matches, trending_skills, roles, certs, skill_scores, best_match)

    elif current_page == "📊 Growth Summary":
        render_growth_summary(
            user_id=user_id,
            username=username,
            assessments=assessments,
            profile=profile,
            matches=matches,
            best_match=best_match,
            benchmarks=benchmarks,
            readiness=readiness,
            readiness_pct=readiness_pct,
            skill_scores=skill_scores,
            certs=certs,
            roles=roles
        )

    elif current_page == "📄 Resume Update Assistant":
        render_resume_assistant(user_id, username, profile, trending_skills, roles, latest_resume)

    elif current_page == "🤖 AI Career Coach":
        render_ai_career_coach(
            user_id=user_id,
            username=username,
            profile=profile,
            best_match=best_match,
            skill_scores=skill_scores,
            readiness_pct=readiness_pct,
            growth_potential_str=growth_str,
            chat_records=chat_records
        )

    elif current_page == "👑 Leadership Evaluation":
        render_leadership_evaluation(user_id, leadership_eval)
