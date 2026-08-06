"""
Streamlit UI for the Working Professional Module.
"""
import streamlit as st
import json
import plotly.express as px
import plotly.graph_objects as go
from database import db_session, User
from modules.wp_models import (
    WP_ProfessionalProfile, WP_SkillAssessment, WP_RoleRequirement,
    WP_TrendingSkill, WP_Certification, WP_SalaryBenchmark
)
from modules.wp_logic import (
    calculate_promotion_readiness, match_career_transition,
    get_salary_growth, recommend_certifications, generate_action_plan,
    advanced_job_matching
)
from modules.wp_report import generate_growth_opportunity_pdf

def show_dashboard(ai_engine=None):
    user_id = st.session_state.get('user_id')
    username = st.session_state.get('username')
    
    if not user_id:
        st.error("Authentication error. Please log in again.")
        return
        
    st.title("💼 Working Professional Dashboard")
    st.caption(f"Welcome back, {username}! Navigate through your professional growth journey.")
    
    # Initialize DB Session and Data
    with db_session() as session:
        user_obj = session.query(User).filter_by(id=user_id).first()
        profile = session.query(WP_ProfessionalProfile).filter_by(user_id=user_id).first()
        assessments = session.query(WP_SkillAssessment).filter_by(user_id=user_id).all()
        roles = session.query(WP_RoleRequirement).all()
        trending_skills = session.query(WP_TrendingSkill).all()
        certs = session.query(WP_Certification).all()
        benchmarks = session.query(WP_SalaryBenchmark).all()
        
    # --- Calculate Top Metrics ---
    skill_scores = {a.skill_area: a.score for a in assessments} if assessments else {}
    if assessments and profile:
        tech_avg = sum([v for k,v in skill_scores.items() if k != "Leadership"]) / max(1, len(skill_scores)-1)
        lead_score = skill_scores.get("Leadership", 50)
        readiness = calculate_promotion_readiness(
            years_exp=profile.total_experience_years,
            project_complexity=70, leadership_score=lead_score, tech_score=tech_avg, comms_score=80, team_score=75
        )
        readiness_pct = readiness["Promotion Readiness %"]
    else:
        readiness_pct = 0
        
    matches = match_career_transition(skill_scores, roles) if skill_scores else []
    best_match = matches[0]["Next Role"] if matches else "Pending Assessment"
    
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    with m_col1:
        st.metric("Promotion Readiness", f"{readiness_pct}%")
    with m_col2:
        st.metric("Top Job Match", best_match)
    with m_col3:
        st.metric("Skills Assessed", len(assessments))
    with m_col4:
        st.metric("Years Exp", profile.total_experience_years if profile else 0)
        
    tabs = st.tabs([
        "Overview & Profile", 
        "Promotion & Salary", 
        "Career Transition",
        "Growth Summary"
    ])
    
    # --- Tab 1: Profile & Skills ---
    with tabs[0]:
        with st.container(border=True):
            st.subheader("Professional Profile")
        with st.expander("Update Profile", expanded=profile is None):
            with st.form("prof_profile_form"):
                col1, col2 = st.columns(2)
                with col1:
                    full_name = st.text_input("Full Name", value=user_obj.full_name if user_obj and user_obj.full_name else "")
                    company = st.text_input("Current Company", value=profile.current_company if profile else "")
                    role = st.text_input("Current Role", value=profile.current_role if profile else "")
                    exp = st.number_input("Total Experience (Years)", min_value=0.0, step=0.5, value=profile.total_experience_years if profile else 0.0)
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
            st.subheader("Skill Assessment")
        with st.expander("Evaluate Skills", expanded=len(assessments) == 0):
            with st.form("skill_assess_form"):
                st.write("Rate your skills (0-100):")
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

    # --- Prepare Data for calculations ---
    skill_scores = {a.skill_area: a.score for a in assessments} if assessments else {}
    
    # --- Tab 2: Promotion & Salary ---
    with tabs[1]:
        with st.container(border=True):
            st.subheader("Promotion Readiness Analysis")
            if not assessments or not profile:
                st.info("Please complete your Profile and Skill Assessment first.")
            else:
                tech_avg = sum([v for k,v in skill_scores.items() if k != "Leadership"]) / max(1, len(skill_scores)-1)
                lead_score = skill_scores.get("Leadership", 50)
                
                readiness = calculate_promotion_readiness(
                    years_exp=profile.total_experience_years,
                    project_complexity=70, # Simulated
                    leadership_score=lead_score,
                    tech_score=tech_avg,
                    comms_score=80, # Simulated
                    team_score=75 # Simulated
                )
                
                col_g1, col_g2, col_g3 = st.columns(3)
                def plot_gauge(val, title):
                    fig = go.Figure(go.Indicator(
                        mode = "gauge+number", value = val, title = {'text': title},
                        gauge = {'axis': {'range': [None, 100]}, 'bar': {'color': "darkblue"}}
                    ))
                    fig.update_layout(height=250, margin=dict(l=20, r=20, t=30, b=20))
                    return fig
                    
                col_g1.plotly_chart(plot_gauge(readiness["Promotion Readiness %"], "Overall Readiness"), use_container_width=True)
                col_g2.plotly_chart(plot_gauge(readiness["Technical Readiness"], "Tech Readiness"), use_container_width=True)
                col_g3.plotly_chart(plot_gauge(readiness["Leadership Readiness"], "Lead Readiness"), use_container_width=True)
            
        with st.container(border=True):
            st.subheader("Salary Benchmark Insights")
            curr_sal = st.number_input("Current Salary (LPA)", min_value=0.0, step=0.5, value=6.0)
        
        matches = match_career_transition(skill_scores, roles) if skill_scores else []
        best_match = matches[0]["Next Role"] if matches else None
        
        if best_match:
            growth = get_salary_growth(curr_sal, best_match, benchmarks)
            if growth:
                st.metric("Target Role", best_match)
                col_m1, col_m2, col_m3 = st.columns(3)
                col_m1.metric("Market Average", f"₹{growth['Market Average']} LPA")
                col_m2.metric("Target Range", growth["Target Range"])
                col_m3.metric("Potential Growth", f"+{growth['Potential Growth %']}%")

    # --- Tab 3: Career Transition ---
    with tabs[2]:
        with st.container(border=True):
            st.subheader("AI Career Transition Suggestions")
            if not matches:
                st.info("No matches available yet. Complete your skills assessment.")
            else:
                st.markdown("**Top Matching Roles**")
                match_data = {"Next Role": [m["Next Role"] for m in matches], "Match %": [m["Match %"] for m in matches]}
                st.dataframe(match_data, use_container_width=True, hide_index=True)
                
        with st.container(border=True):
            st.subheader("Industry Trend Recommendations")
            if trending_skills:
                ts_data = {"Skill": [t.skill_name for t in trending_skills], "Growth %": [t.demand_growth_percent for t in trending_skills]}
                fig2 = px.bar(ts_data, x="Skill", y="Growth %")
                fig2.update_traces(marker_color='#1F9D77')
                fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#12213B'))
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("No trending skills configured.")
                
        with st.container(border=True):
            st.subheader("Certification Suggestions")
            if best_match and best_match != "Pending Assessment":
                best_role_obj = next((r for r in roles if r.role_name == best_match), None)
                rec_certs = recommend_certifications(skill_scores, best_role_obj, certs)
                if rec_certs:
                    st.dataframe(rec_certs, use_container_width=True, hide_index=True)
                else:
                    st.info("No missing certifications for top match.")

    # --- Tab 4: AI Output Summary ---
    with tabs[3]:
        with st.container(border=True):
            st.subheader("Growth Opportunity Analysis")
            if not assessments or not profile or not matches:
                st.info("Not enough data to generate summary.")
            else:
                best_match = matches[0]["Next Role"]
                growth = get_salary_growth(curr_sal, best_match, benchmarks)
                sal_growth_pct = growth["Potential Growth %"] if growth else 0
                readiness_pct = readiness["Promotion Readiness %"] if 'readiness' in locals() else 0
                
                strong = [k for k,v in skill_scores.items() if v >= 75]
                improve = [k for k,v in skill_scores.items() if v < 75]
                
                best_role_obj = next((r for r in roles if r.role_name == best_match), None)
                rec_certs = recommend_certifications(skill_scores, best_role_obj, certs)
                
                action_plan = generate_action_plan(skill_scores)
                
                # Display Summary Card
                st.markdown(f"""
                ### Professional Snapshot
                - **Current Role**: {profile.current_role}
                - **Experience**: {profile.total_experience_years} Years
                - **Promotion Readiness**: {readiness_pct}%
                - **Salary Growth Potential**: +{sal_growth_pct}%
                - **Top Job Match**: {best_match} ({matches[0]['Match %']}%)
                """)
                
                st.subheader("Current Skill Progress")
                for k, v in skill_scores.items():
                    st.progress(v / 100, text=f"{k} {v}%")
                
                col_s1, col_s2 = st.columns(2)
                with col_s1:
                    st.subheader("Strong Areas")
                    for s in strong: st.write(f"- {s}")
                with col_s2:
                    st.subheader("Improvement Areas")
                    for s in improve: st.write(f"- {s}")
                    
                if action_plan:
                    st.subheader("90-Day Action Plan")
                    for item in action_plan:
                        st.write(f"**{item['Month']}**: {item['Focus']}")
                        
                # PDF Generation
                pdf_buffer = generate_growth_opportunity_pdf(
                    user_name=username,
                    current_role=profile.current_role,
                    next_best_role=best_match,
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

