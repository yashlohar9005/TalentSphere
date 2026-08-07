"""
College Module for TalentSphere Elevate.

This module provides functionalities tailored for College Students.
It inherits from BasePortal to adhere to DRY principles and implements 
college-specific assessments (internships, GPA, networking, major).
"""

import streamlit as st
import json
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from database import db_session, Assessment, Roadmap, Progress, CollegeCodingTest, MockInterviewResult, PlacementReadiness, JobMatchResult, InternshipRecommendation
from modules.base_portal import BasePortal

class CollegePortal(BasePortal):
    """
    College Student portal inheriting from BasePortal.
    """
    
    def __init__(self, user_id: int, username: str, ai_engine=None):
        super().__init__(user_id, username, portal_prefix="col", ai_engine=ai_engine)
        self.pages = ["Dashboard", "Student Profile", "Assessment", "Skill Gap Analysis", "Roadmap & Progress", "Resume Builder", "Reports & Certificates", "Notifications"]

    def render_dashboard(self) -> None:
        head_col1, head_col2 = st.columns([6, 1])
        with head_col1:
            st.title("📊 College Dashboard")
            st.caption(f"Welcome back, {self.username}! Here is your personalized placement & career progress.")
        with head_col2:
            st.write("")  # Spacing
            if st.button("🚪 Logout", key="col_header_logout", use_container_width=True):
                st.session_state.clear()
                st.rerun()
        
        with db_session() as session:
            assessments = self.fetch_assessments(session)
            roadmaps = self.fetch_roadmaps(session)
            coding_tests = session.query(CollegeCodingTest).filter_by(user_id=self.user_id).all()
            interviews = session.query(MockInterviewResult).filter_by(user_id=self.user_id).all()
            
            # Recalculate Placement Readiness dynamically if ai_engine is present
            if self.ai_engine:
                resume_score = 0
                ats_score = 0
                coding_score = sum(c.score for c in coding_tests) / max(len(coding_tests), 1) if coding_tests else 0
                comm_score = sum(i.communication_score for i in interviews) / max(len(interviews), 1) if interviews else 0
                
                # Try fetching ATS result if it existed, otherwise mock it
                # For this implementation, we rely on the placement engine calculation
                readiness_data = self.ai_engine.placement_engine.calculate_readiness({
                    "resume_score": resume_score,
                    "ats_score": ats_score,
                    "coding_score": coding_score,
                    "projects_score": 60, # Mock data
                    "communication_score": comm_score,
                    "internship_score": 50,
                    "certification_score": 20
                })
                placement_score = readiness_data["placement_score"]
                recommendation = readiness_data["overall_recommendation"]
            else:
                placement_score = 0
                recommendation = "Complete assessments to generate readiness."

            # Top metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Placement Readiness", f"{placement_score}%")
            with col2:
                st.metric("Assessments Done", len(assessments))
            with col3:
                st.metric("Coding Tests Taken", len(coding_tests))
            with col4:
                st.metric("Active Roadmaps", len(roadmaps))
                
            # Tabs layout
            tab_overview, tab_progress = st.tabs(["Overview", "Progress Insights"])
            
            with tab_overview:
                with st.container(border=True):
                    st.info(f"**Recommendation:** {recommendation}")

            with tab_progress:
                chart_col1, chart_col2 = st.columns(2)
                
                with chart_col1:
                    with st.container(border=True):
                        st.subheader("Industry Readiness")
                        # Gauge Chart for Placement Readiness
                        fig1 = go.Figure(go.Indicator(
                            mode = "gauge+number",
                            value = placement_score,
                            gauge = {
                                'axis': {'range': [0, 100]},
                                'bar': {'color': "#1F9D77"},
                                'steps': [
                                    {'range': [0, 50], 'color': "rgba(0,0,0,0.1)"},
                                    {'range': [50, 80], 'color': "rgba(0,0,0,0.2)"}],
                                'threshold': {
                                    'line': {'color': "#E8A33D", 'width': 4},
                                    'thickness': 0.75,
                                    'value': 90}
                            }
                        ))
                        fig1.update_layout(
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(0,0,0,0)',
                            font=dict(color='#12213B')
                        )
                        st.plotly_chart(fig1, use_container_width=True)
                    
                with chart_col2:
                    with st.container(border=True):
                        st.subheader("Coding Performance Trend")
                        # Progress line chart for coding if data exists
                        if coding_tests:
                            df = {"Test": [f"Test {i+1}" for i in range(len(coding_tests))], "Score": [c.score for c in coding_tests]}
                            fig2 = px.line(df, x="Test", y="Score")
                            fig2.update_traces(line_color='#1F9D77', marker_color='#1F9D77')
                            fig2.update_layout(
                                paper_bgcolor='rgba(0,0,0,0)',
                                plot_bgcolor='rgba(0,0,0,0)',
                                font=dict(color='#12213B')
                            )
                            st.plotly_chart(fig2, use_container_width=True)
                        else:
                            st.info("Take coding tests to see your performance trend.")

    def render_assessment(self) -> None:
        st.title("📝 College Assessments")
        st.caption("Evaluate your skills through readiness assessments, coding tests, and mock interviews.")
        
        tab_readiness, tab_coding, tab_interview = st.tabs(["Readiness Assessment", "Coding Practice Tests", "Mock Interviews"])
        
        with tab_readiness:
            with st.container(border=True):
                st.write("Evaluate your preparedness for internships and early-career opportunities.")
                with st.form("col_assessment_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        q1 = st.slider("How confident are you in your Core Major Skills?", 1, 10, 5)
                        q2 = st.slider("How would you rate your Networking skills?", 1, 10, 5)
                        q3 = st.slider("How robust is your current Resume/Portfolio?", 1, 10, 5)
                    with col2:
                        q4 = st.slider("How effectively do you manage your time (GPA/Extracurricular)?", 1, 10, 5)
                        q5 = st.slider("How confident are you in Interviewing?", 1, 10, 5)
                    
                    submitted = st.form_submit_button("Submit Assessment")
                    
                    if submitted:
                        hard_skills = (q1 + q3) / 2 * 10
                        soft_skills = (q2 + q4 + q5) / 3 * 10
                        category = "Technical & Hard Skills Focused" if hard_skills > soft_skills else "Soft Skills & Networking Focused"
                        final_score = max(hard_skills, soft_skills)
                        
                        details = {
                            "Core Skills": q1, "Networking": q2, "Portfolio": q3, 
                            "Time Management": q4, "Interviewing": q5,
                            "hard_skills_score": hard_skills, "soft_skills_score": soft_skills
                        }
                        
                        with db_session() as session:
                            new_assessment = Assessment(
                                user_id=self.user_id,
                                category=category,
                                score=int(final_score),
                                details=json.dumps(details)
                            )
                            session.add(new_assessment)
                        st.success(f"Assessment completed! Your primary strength is: {category}")
                    
        with tab_coding:
            with st.container(border=True):
                st.subheader("Interactive Coding Practice")
                if not self.ai_engine:
                    st.error("AI Engine offline.")
                else:
                    topics = self.ai_engine.coding_engine.get_topics()
                    selected_topic = st.selectbox("Select a Topic", topics)
                    
                    if st.button("Start Assessment"):
                        st.session_state["active_coding_topic"] = selected_topic
                        st.session_state["coding_questions"] = self.ai_engine.coding_engine.generate_questions(selected_topic)
                        
                    if "coding_questions" in st.session_state and st.session_state.get("active_coding_topic") == selected_topic:
                        with st.form("coding_test_form"):
                            answers = {}
                            for q in st.session_state["coding_questions"]:
                                answers[q['id']] = st.radio(q['question'], q['options'], key=f"q_{q['id']}")
                            
                            if st.form_submit_button("Submit Test"):
                                with st.spinner("AI Evaluating..."):
                                    result = self.ai_engine.coding_engine.evaluate_assessment(selected_topic, answers, len(st.session_state["coding_questions"]))
                                    
                                    with db_session() as session:
                                        test_record = CollegeCodingTest(
                                            user_id=self.user_id,
                                            topic=selected_topic,
                                            score=result["score"],
                                            total_questions=result["total_questions"],
                                            weak_topics=json.dumps(result["weak_topics"]),
                                            strong_topics=json.dumps(result["strong_topics"]),
                                            ai_suggestions=result["ai_suggestions"]
                                        )
                                        session.add(test_record)
                                        
                                    st.success(f"Score: {result['score']}%")
                                    st.info(result['ai_suggestions'])
                                    del st.session_state["coding_questions"]
                                    del st.session_state["active_coding_topic"]

        with tab_interview:
            with st.container(border=True):
                st.subheader("Mock Interview Simulator")
                if not self.ai_engine:
                    st.error("AI Engine offline.")
                else:
                    int_type = st.selectbox("Select Interview Type", ["Technical", "HR", "Behavioral"])
                    
                    if st.button("Start Interview"):
                        st.session_state["active_interview_type"] = int_type
                        st.session_state["interview_questions"] = self.ai_engine.interview_engine.get_questions(int_type)
                        
                    if "interview_questions" in st.session_state and st.session_state.get("active_interview_type") == int_type:
                        with st.form("mock_interview_form"):
                            answers = {}
                            for i, q in enumerate(st.session_state["interview_questions"]):
                                answers[i] = st.text_area(q, key=f"int_q_{i}")
                            
                            if st.form_submit_button("Complete Interview"):
                                with st.spinner("AI evaluating your responses..."):
                                    result = self.ai_engine.interview_engine.evaluate_interview(int_type, answers)
                                    
                                    with db_session() as session:
                                        int_record = MockInterviewResult(
                                            user_id=self.user_id,
                                            interview_type=int_type,
                                            confidence_score=result["confidence"],
                                            communication_score=result["communication"],
                                            technical_accuracy=result["technical_accuracy"],
                                            answer_relevance=result["answer_relevance"],
                                            problem_solving=result["problem_solving"],
                                            overall_score=result["overall_score"],
                                            ai_feedback=result["ai_feedback"],
                                            improvement_suggestions=json.dumps(result["improvement_suggestions"])
                                        )
                                        session.add(int_record)
                                        
                                    st.success(f"Overall Interview Score: {result['overall_score']}/100")
                                    st.write(f"**Feedback:** {result['ai_feedback']}")
                                    st.write("**Suggestions:**", ", ".join(result["improvement_suggestions"]))
                                    del st.session_state["interview_questions"]
                                    del st.session_state["active_interview_type"]

    def render_skill_gap(self) -> None:
        st.title("🎯 Skill Gap & Career Matching")
        st.caption("Analyze your missing skills, discover target roles, and find internships.")
        
        tab1, tab2, tab3 = st.tabs(["Skill Gap Analysis", "Job Matching", "Internship Recommendations"])
        
        with tab1:
            with st.container(border=True):
                st.subheader("Skill Gap Analysis")
                # We mock the current skills for demonstration; in a real app, these are fetched from CollegeStudentProfile
                target_role = st.selectbox("Select Target Role for Analysis", ["Software Developer", "Data Analyst", "AI Engineer", "Product Manager"])
                if st.button("Analyze Skill Gap") and self.ai_engine:
                    with st.spinner("Analyzing..."):
                        # Mocking required vs current for demo
                        required_skills = {"python": 5, "sql": 4, "git": 3, "react": 3, "aws": 2}
                        current_skills = {"python": 3, "sql": 4, "java": 3, "git": 1}
                        
                        result = self.ai_engine.skill_gap.analyze_gap(current_skills, required_skills, target_role)
                        
                        st.metric("Skill Match", f"{result['readiness_percentage']}%")
                        st.write("**Missing Skills & Priority:**")
                        for s in result["priority_ranking"]:
                            st.write(f"- {s} (Gap: {result['missing_skills'][s]})")
                            
                        st.write("**Learning Recommendations:**")
                        for rec in result["learning_suggestions"]:
                            st.write(f"- {rec}")
                        
        with tab2:
            with st.container(border=True):
                st.subheader("Job Matching Engine")
                if self.ai_engine:
                    role = st.selectbox("Select Role to Match", self.ai_engine.job_matching.roles)
                    if st.button("Calculate Match %"):
                        # Pass mock data. Real data should be fetched from Profile
                        match_result = self.ai_engine.job_matching.get_job_match(role, "python, sql, git, react", 8.5)
                        st.metric("Match Percentage", f"{match_result['match_percentage']}%")
                        st.success(match_result["career_recommendation"])
                        st.info(f"Estimated Salary Range: {match_result['salary_range']}")
                        st.write("**Reasons:**", " ".join(match_result["reasons"]))
                        if match_result["missing_skills"]:
                            st.error(f"Missing Skills: {', '.join(match_result['missing_skills'])}")
                        
        with tab3:
            with st.container(border=True):
                st.subheader("Internship Recommendations")
                if self.ai_engine:
                    if st.button("Find Internships"):
                        # Pass mock data. Real data should be fetched from Profile
                        interns = self.ai_engine.internship_engine.get_recommendations(8.5, "python, java, sql", "Bangalore", "Software")
                        for i in interns:
                            with st.expander(f"{i['company']} - {i['role']} ({i['match_percentage']}% Match)"):
                                st.write(f"**Location:** {i['location']}")
                                st.write(f"**Eligibility:** {i['eligibility']}")
                                st.write(f"**Required Skills:** {', '.join(i['required_skills'])}")

    def render_roadmap_ui(self) -> None:
        """Override BasePortal's roadmap to integrate 30/60/90 Day Roadmaps dynamically."""
        st.header("🗺️ Personalized Learning Roadmap")
        
        with db_session() as session:
            roadmaps = self.fetch_roadmaps(session)
            
            if not roadmaps:
                st.info("You don't have any roadmaps yet. Generate one to track your progress.")
                
            if st.button("Generate New 30/60/90-Day Roadmap") and self.ai_engine:
                # We mock generating a roadmap for Software Engineer here
                new_roadmap = self.ai_engine.roadmap_generator.generate_career_roadmap("Software Engineer")
                self.generate_roadmap(new_roadmap["title"], new_roadmap["flat_steps"], "30/60/90-Day Plan")
                st.rerun()

            for roadmap in roadmaps:
                with st.expander(f"Roadmap: {roadmap.title}", expanded=True):
                    progress_items = session.query(Progress).filter_by(roadmap_id=roadmap.id).all()
                    
                    completed_count = sum(1 for item in progress_items if item.is_completed)
                    total_count = len(progress_items)
                    
                    if total_count > 0:
                        prog_pct = completed_count / total_count
                        st.progress(prog_pct, text=f"Overall Progress: {completed_count}/{total_count} completed")
                        if prog_pct == 1.0:
                            st.success("🎉 Roadmap Completed! Certificate Unlocked in Reports & Certificates tab.")
                    
                    for item in progress_items:
                        checked = st.checkbox(item.milestone_name, value=bool(item.is_completed), key=f"prog_{item.id}")
                        if checked != bool(item.is_completed):
                            item.is_completed = 1 if checked else 0
                            item.completed_at = datetime.utcnow() if checked else None
                            session.commit()
                            st.rerun()

def show_dashboard(ai_engine=None) -> None:
    user_id = st.session_state.get('user_id')
    username = st.session_state.get('username')
    
    if not user_id:
        st.error("Authentication error. Please log in again.")
        return
        
    portal = CollegePortal(user_id, username, ai_engine=ai_engine)
    portal.run(portal.pages)
