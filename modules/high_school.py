"""
High School Module for TalentSphere Elevate.

This module provides functionalities tailored for High School Students.
It inherits from BasePortal to adhere to DRY principles.
"""

import streamlit as st
import json
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from database import (
    db_session, Assessment, Roadmap, Progress, CareerGoal,
    CareerQuizResult, InterestProfile, DailyTask, CodingProgress,
    AptitudeResult, CommunicationProgress, Goal,
)
from modules.base_portal import BasePortal

class HighSchoolPortal(BasePortal):
    """
    High School Student portal inheriting from BasePortal.
    """
    
    def __init__(self, user_id: int, username: str, ai_engine=None):
        super().__init__(user_id, username, portal_prefix="hs", ai_engine=ai_engine)
        self.pages = [
            "Dashboard",
            "Personal Information",
            "Career Explorer",
            "AI Career Quiz",
            "Interest Assessment",
            "Assessment",
            "Skill Gap Analysis",
            "Future Skills Roadmap",
            "Daily Learning Tasks",
            "Coding Basics",
            "Aptitude Practice",
            "Communication Skills",
            "Goal Tracker",
            "AI Mentor Chatbot",
            "Roadmap & Progress",
            "Reports & Certificates",
            "Notifications",
        ]

    def render_dashboard(self) -> None:
        """Renders the enhanced High School Dashboard."""
        st.title("🎓 High School Dashboard")
        st.caption(f"Welcome back, {self.username}! Track your learning progress, goals, and skill gaps.")
        
        with db_session() as session:
            assessments = self.fetch_assessments(session)
            roadmaps = self.fetch_roadmaps(session)
            career_goals = session.query(CareerGoal).filter_by(user_id=self.user_id).all()
            quiz_result = (
                session.query(CareerQuizResult)
                .filter_by(user_id=self.user_id)
                .order_by(CareerQuizResult.completed_at.desc())
                .first()
            )
            interest_profile = (
                session.query(InterestProfile)
                .filter_by(user_id=self.user_id)
                .order_by(InterestProfile.completed_at.desc())
                .first()
            )
            goals = session.query(Goal).filter_by(user_id=self.user_id, status="Active").all()

            # ── Key Metrics Row ──
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📝 Assessments", len(assessments))
            with col2:
                st.metric("🗺️ Active Roadmaps", len(roadmaps))
            with col3:
                st.metric("🎯 Career Goals", len(career_goals))
            with col4:
                st.metric("📌 Active Goals", len(goals))

            # ── Tabs ──
            tab_overview, tab_learning, tab_progress = st.tabs(["Overview", "Learning & Tasks", "Progress & History"])
            
            with tab_overview:
                # ── Career Quiz Result Summary ──
                col_left, col_right = st.columns(2)
                with col_left:
                    with st.container(border=True):
                        if quiz_result:
                            st.subheader("🧠 Career Quiz Profile")
                            scores = json.loads(quiz_result.scores)
                            categories = list(scores.keys())
                            values = list(scores.values())
                            fig = go.Figure(data=go.Scatterpolar(
                                r=values + [values[0]],
                                theta=categories + [categories[0]],
                                fill='toself', 
                                fillcolor='rgba(31, 157, 119, 0.4)',
                                line=dict(color='#1F9D77'),
                            ))
                            fig.update_layout(
                                polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                                showlegend=False, height=300,
                                margin=dict(l=40, r=40, t=30, b=30),
                                paper_bgcolor='rgba(0,0,0,0)',
                                plot_bgcolor='rgba(0,0,0,0)',
                                font=dict(color='#12213B')
                            )
                            st.plotly_chart(fig, width='stretch')
                            st.caption(f"Personality: **{quiz_result.personality_type}** | Confidence: **{quiz_result.confidence_level}%**")
                        else:
                            st.info("📝 Take the **Career Quiz** to discover your career profile!")
                            if st.button("Take Career Quiz"):
                                st.session_state[self.page_state_key] = "AI Career Quiz"
                                st.rerun()

                # ── Interest Profile Summary ──
                with col_right:
                    with st.container(border=True):
                        if interest_profile:
                            st.subheader("🎯 Interest Profile")
                            scores = json.loads(interest_profile.scores)
                            streams = json.loads(interest_profile.recommended_streams)
                            df_interest = pd.DataFrame({
                                "Stream": list(scores.keys()),
                                "Score": list(scores.values()),
                            })
                            fig = px.bar(df_interest, x="Stream", y="Score", range_y=[0, 100], height=300)
                            fig.update_traces(marker_color='#1F9D77')
                            fig.update_layout(
                                margin=dict(l=40, r=40, t=30, b=30), 
                                showlegend=False,
                                paper_bgcolor='rgba(0,0,0,0)',
                                plot_bgcolor='rgba(0,0,0,0)',
                                font=dict(color='#12213B')
                            )
                            st.plotly_chart(fig, width='stretch')
                            st.caption(f"Top streams: **{', '.join(streams[:3])}**")
                        else:
                            st.info("📝 Complete the **Interest Assessment** to see your interest profile!")
                            if st.button("Start Interest Assessment"):
                                st.session_state[self.page_state_key] = "Interest Assessment"
                                st.rerun()

            with tab_learning:
                # ── Daily Tasks & Learning Progress ──
                col_daily, col_coding = st.columns(2)
                with col_daily:
                    with st.container(border=True):
                        from datetime import datetime
                        today = datetime.utcnow().strftime("%Y-%m-%d")
                        today_tasks = session.query(DailyTask).filter_by(
                            user_id=self.user_id, task_date=today,
                        ).all()
                        if today_tasks:
                            completed = sum(1 for t in today_tasks if t.is_completed)
                            total = len(today_tasks)
                            st.subheader("📋 Today's Tasks")
                            st.progress(completed / total, text=f"{completed}/{total} completed")
                            for t in today_tasks:
                                icon = "✅" if t.is_completed else "⬜"
                                st.caption(f"{icon} {t.task_text}")
                        else:
                            st.subheader("📋 Daily Tasks")
                            st.info("Visit **Daily Learning Tasks** to generate today's tasks!")
                            if st.button("View Daily Tasks"):
                                st.session_state[self.page_state_key] = "Daily Learning Tasks"
                                st.rerun()

                with col_coding:
                    with st.container(border=True):
                        coding_records = session.query(CodingProgress).filter_by(user_id=self.user_id).all()
                        if coding_records:
                            st.subheader("💻 Coding Progress")
                            lessons_done = sum(1 for c in coding_records if c.lesson_completed)
                            quizzes_done = sum(1 for c in coding_records if c.quiz_score is not None)
                            st.metric("Topics Completed", f"{lessons_done}/10")
                            st.metric("Quizzes Passed", f"{quizzes_done}/10")
                            st.progress(lessons_done / 10)
                        else:
                            st.subheader("💻 Coding Basics")
                            st.info("Start learning **Python** in the Coding Basics module!")
                            if st.button("Start Coding Basics"):
                                st.session_state[self.page_state_key] = "Coding Basics"
                                st.rerun()

            with tab_progress:
                # ── Goal Progress & Aptitude Summary ──
                col_goals, col_aptitude = st.columns(2)
                with col_goals:
                    with st.container(border=True):
                        if goals:
                            st.subheader("🎯 Active Goals")
                            for g in goals[:5]:
                                st.markdown(f"**{g.title}**")
                                st.progress(g.progress / 100, text=f"{g.progress}%")
                        else:
                            st.subheader("🎯 Goals")
                            st.info("Set goals in the **Goal Tracker** to track your progress!")
                            if st.button("Set Goals"):
                                st.session_state[self.page_state_key] = "Goal Tracker"
                                st.rerun()

                with col_aptitude:
                    with st.container(border=True):
                        apt_results = session.query(AptitudeResult).filter_by(user_id=self.user_id).all()
                        if apt_results:
                            st.subheader("🧮 Aptitude Scores")
                            cat_scores: dict[str, list[int]] = {}
                            for r in apt_results:
                                if r.category not in cat_scores:
                                    cat_scores[r.category] = []
                                cat_scores[r.category].append(r.score)
                            df_apt = pd.DataFrame([
                                {"Category": cat, "Avg Score": int(sum(s) / len(s))}
                                for cat, s in cat_scores.items()
                            ])
                            fig = px.bar(df_apt, x="Category", y="Avg Score", range_y=[0, 100], height=250)
                            fig.update_traces(marker_color='#1F9D77')
                            fig.update_layout(
                                margin=dict(l=40, r=40, t=30, b=30), 
                                showlegend=False,
                                paper_bgcolor='rgba(0,0,0,0)',
                                plot_bgcolor='rgba(0,0,0,0)',
                                font=dict(color='#12213B')
                            )
                            st.plotly_chart(fig, width='stretch')
                        else:
                            st.subheader("🧮 Aptitude Practice")
                            st.info("Take an **Aptitude Practice** quiz to see your scores!")
                            if st.button("Practice Aptitude"):
                                st.session_state[self.page_state_key] = "Aptitude Practice"
                                st.rerun()

                # ── Assessment History ──
                if assessments:
                    with st.container(border=True):
                        st.subheader("📊 Assessment History")
                        self.plot_assessment_history(assessments)

    def render_assessment(self) -> None:
        st.title("Career Interest Assessment")
        st.caption("Answer the following questions to help us understand your interests and build your profile.")
        
        # Prevent duplicate submissions
        if st.session_state.get("hs_assessment_submitted"):
            st.success(st.session_state.get("hs_assessment_message", "Assessment saved!"))
            st.balloons()
            del st.session_state["hs_assessment_submitted"]
            if "hs_assessment_message" in st.session_state:
                del st.session_state["hs_assessment_message"]
            return
        
        with st.form("hs_assessment_form"):
            col1, col2 = st.columns(2)
            with col1:
                q1 = st.slider("Enjoy solving complex math problems?", 1, 10, 5)
                q2 = st.slider("Enjoy creative writing or arts?", 1, 10, 5)
                q3 = st.slider("Like working with computers and technology?", 1, 10, 5)
            with col2:
                q4 = st.slider("Interested in science and experiments?", 1, 10, 5)
                q5 = st.slider("Enjoy public speaking or debate?", 1, 10, 5)
            
            submitted = st.form_submit_button("Submit Assessment")
            
        if submitted:
            stem_score = (q1 + q3 + q4) / 3 * 10
            arts_score = (q2 + q5) / 2 * 10
            
            category = "STEM" if stem_score > arts_score else "Arts & Humanities"
            final_score = max(stem_score, arts_score)
            
            details = {
                "math": q1, "arts": q2, "tech": q3, 
                "science": q4, "communication": q5,
                "stem_score": stem_score, "arts_score": arts_score
            }
            
            try:
                with db_session() as session:
                    new_assessment = Assessment(
                        user_id=self.user_id,
                        category=category,
                        score=int(final_score),
                        details=json.dumps(details)
                    )
                    session.add(new_assessment)
                
                st.session_state["hs_assessment_submitted"] = True
                st.session_state["hs_assessment_message"] = f"Assessment completed! Your primary aptitude lies in: {category}"
                st.rerun()
            except Exception as e:
                st.error(f"Failed to save assessment: {e}")

    def render_skill_gap(self) -> None:
        st.title("Skill Gap Analysis")
        st.caption("Identify your core strengths and receive tailored recommendations to bridge any gaps.")
        
        with db_session() as session:
            latest_assessment = session.query(Assessment).filter_by(user_id=self.user_id).order_by(Assessment.completed_at.desc()).first()
            
            if not latest_assessment:
                st.info("Please complete an Assessment first to view your skill gap analysis.")
                if st.button("Go to Assessment"):
                    st.session_state[self.page_state_key] = "Assessment"
                    st.rerun()
                return
                
            details = json.loads(latest_assessment.details)
            
            tab_analysis, tab_recs = st.tabs(["Analysis", "Recommendations"])
            
            with tab_analysis:
                with st.container(border=True):
                    st.write(f"**Primary Aptitude:** {latest_assessment.category}")
                    st.subheader("Detailed Breakdown")
                    self.plot_radar_chart(details, exclude_keys=["stem_score", "arts_score"])
            
            with tab_recs:
                with st.container(border=True):
                    st.subheader("Actionable Recommendations")
                    if self.ai_engine:
                        with st.spinner("Generating personalized recommendations..."):
                            recs = self.ai_engine.recommendation_engine.generate_recommendations("high_school", latest_assessment.category, details)
                        if recs.get("courses"):
                            st.write("**Recommended Courses:** " + ", ".join(recs["courses"]))
                        if recs.get("projects"):
                            st.write("**Recommended Projects:** " + ", ".join(recs["projects"]))
                        if recs.get("career_suggestions"):
                            st.write("**Career Suggestions:** " + ", ".join(recs["career_suggestions"]))
                        
                        roadmap = self.ai_engine.roadmap_generator.generate_roadmap("high_school", latest_assessment.category)
                        roadmap_title = roadmap["title"]
                        roadmap_steps = roadmap["flat_steps"]
                    else:
                        if latest_assessment.category == "STEM":
                            st.write("We recommend exploring majors like Computer Science, Engineering, or Physics.")
                            roadmap_title = "Intro to Computer Science Pathway"
                            roadmap_steps = ["Learn Python Basics", "Build a simple App", "Take AP Computer Science", "Participate in a Hackathon"]
                        else:
                            st.write("We recommend exploring majors like Literature, Communications, or Design.")
                            roadmap_title = "Communications & Arts Pathway"
                            roadmap_steps = ["Join the Debate Team", "Write an article", "Take AP English Literature", "Start a Blog"]
                        
                    if st.button("Generate Learning Roadmap", type="primary"):
                        self.generate_roadmap(roadmap_title, roadmap_steps, f"Generated roadmap for {roadmap_title}.")


def show_dashboard(ai_engine=None) -> None:
    user_id = st.session_state.get('user_id')
    username = st.session_state.get('username')
    
    if not user_id:
        st.error("Authentication error. Please log in again.")
        return
        
    portal = HighSchoolPortal(user_id, username, ai_engine=ai_engine)
    portal.run(portal.pages)
