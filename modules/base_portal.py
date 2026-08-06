"""
Base Portal Architecture for TalentSphere Elevate.

This module provides the BasePortal class that all specific user modules 
(High School, College, Professional) inherit from. It handles common 
functionality such as session management, sidebar rendering, and plotting.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from abc import ABC, abstractmethod
from database import db_session, Assessment, Roadmap, Progress
import json
from resume.resume_builder import render_resume_manager
from reports import render_reports_manager

class BasePortal(ABC):
    """
    Abstract base class for user portals. Implements common DRY logic.
    """
    
    def __init__(self, user_id: int, username: str, portal_prefix: str, ai_engine=None):
        self.user_id = user_id
        self.username = username
        self.portal_prefix = portal_prefix
        self.ai_engine = ai_engine
        self.page_state_key = f"{portal_prefix}_current_page"

    def render_sidebar(self, pages: list[str]) -> None:
        """Renders the common sidebar navigation."""
        st.sidebar.title("TalentSphere Elevate")
        st.sidebar.markdown("---")
        
        if self.page_state_key not in st.session_state:
            st.session_state[self.page_state_key] = pages[0]

        # Use native radio styled by primaryColor for navigation
        selected_page = st.sidebar.radio(
            "Navigation", 
            options=pages, 
            index=pages.index(st.session_state.get(self.page_state_key, pages[0]))
        )
        if selected_page != st.session_state.get(self.page_state_key):
            st.session_state[self.page_state_key] = selected_page
            st.rerun()
            
        st.sidebar.divider()
        st.sidebar.write(f"👤 **{self.username}**")
        st.sidebar.write(f"*{st.session_state.get('user_type', 'User')}*")
        
        if st.sidebar.button("Logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    def fetch_assessments(self, session) -> list:
        """Fetches all assessments for the user."""
        return session.query(Assessment).filter_by(user_id=self.user_id).all()

    def fetch_roadmaps(self, session) -> list:
        """Fetches all roadmaps for the user."""
        return session.query(Roadmap).filter_by(user_id=self.user_id).all()

    def plot_assessment_history(self, assessments: list) -> None:
        """Plots the assessment history."""
        data = {"Category": [], "Score": []}
        for a in assessments:
            data["Category"].append(a.category)
            data["Score"].append(a.score)
        
        df = pd.DataFrame(data)
        fig = px.bar(df, x='Category', y='Score', title="Your Assessment Performance", range_y=[0,100])
        fig.update_traces(marker_color='#1F9D77')
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#12213B')
        )
        st.plotly_chart(fig, width='stretch')

    def plot_radar_chart(self, details: dict, exclude_keys: list[str] = None) -> None:
        """Plots a radar chart for skill gaps."""
        if exclude_keys is None:
            exclude_keys = []
            
        df = pd.DataFrame(list(details.items()), columns=["Skill Area", "Rating"])
        df_radar = df[~df["Skill Area"].isin(exclude_keys)]
        
        fig = px.line_polar(df_radar, r='Rating', theta='Skill Area', line_close=True, title="Skill Profile")
        fig.update_traces(fill='toself', fillcolor='rgba(31, 157, 119, 0.4)', line_color='#1F9D77')
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#12213B')
        )
        st.plotly_chart(fig, width='stretch')

    def render_roadmap_ui(self) -> None:
        """Standardized method to render roadmaps and progress."""
        st.header("Learning Roadmap & Progress")
        
        with db_session() as session:
            roadmaps = self.fetch_roadmaps(session)
            
            if not roadmaps:
                st.info("You don't have any roadmaps yet. Complete your Skill Gap Analysis to generate one.")
                return
                
            for roadmap in roadmaps:
                with st.expander(f"Roadmap: {roadmap.title}", expanded=True):
                    progress_items = session.query(Progress).filter_by(roadmap_id=roadmap.id).all()
                    
                    completed_count = sum(1 for item in progress_items if item.is_completed)
                    total_count = len(progress_items)
                    
                    if total_count > 0:
                        st.progress(completed_count / total_count, text=f"Progress: {completed_count}/{total_count} completed")
                    
                    for item in progress_items:
                        checked = st.checkbox(item.milestone_name, value=bool(item.is_completed), key=f"prog_{item.id}")
                        if checked != bool(item.is_completed):
                            item.is_completed = 1 if checked else 0
                            item.completed_at = datetime.utcnow() if checked else None
                            session.commit()
                            st.rerun()

    def generate_roadmap(self, title: str, steps: list[str], description: str = "") -> None:
        """Helper to generate a roadmap and its milestones."""
        with db_session() as session:
            existing = session.query(Roadmap).filter_by(user_id=self.user_id, title=title).first()
            if existing:
                st.info("You already have this roadmap in your profile! Check the Roadmap tab.")
                return

            new_roadmap = Roadmap(
                user_id=self.user_id,
                title=title,
                content=json.dumps({"description": description})
            )
            session.add(new_roadmap)
            session.flush() # Flush to populate ID
            
            for step in steps:
                milestone = Progress(
                    roadmap_id=new_roadmap.id,
                    milestone_name=step,
                    is_completed=0
                )
                session.add(milestone)
                
            # No need to explicitly commit since db_session context manager handles it.
            st.success(f"Roadmap '{title}' generated successfully! Navigate to the Roadmap & Progress tab to view it.")

    @abstractmethod
    def render_dashboard(self) -> None:
        pass

    @abstractmethod
    def render_assessment(self) -> None:
        pass

    @abstractmethod
    def render_skill_gap(self) -> None:
        pass

    def run(self, pages: list[str]) -> None:
        """Orchestrates the portal rendering."""
        self.render_sidebar(pages)
        page = st.session_state.get(self.page_state_key, pages[0])
        
        if page == "Dashboard":
            self.render_dashboard()
        elif page == "Personal Information":
            from modules.hs_features.personal_information import render_personal_information
            render_personal_information(self.user_id)
        elif page == "Assessment":
            self.render_assessment()
        elif page == "Skill Gap Analysis":
            self.render_skill_gap()
        elif page == "Career Explorer":
            from modules.career_explorer import render_career_explorer
            render_career_explorer(self.user_id, self.ai_engine, portal=self)
        elif page == "Roadmap & Progress":
            self.render_roadmap_ui()
        elif page == "Resume Builder":
            render_resume_manager(self.user_id, self.ai_engine)
        elif page == "Reports & Certificates":
            render_reports_manager(self.user_id, self.ai_engine)
        elif page == "Notifications":
            from notifications import render_notification_center
            render_notification_center(self.user_id)
        # ── High School Module — Enhanced Features ──
        elif page == "AI Career Quiz":
            from modules.hs_features.career_quiz import render_career_quiz
            render_career_quiz(self.user_id, self.ai_engine)
        elif page == "Interest Assessment":
            from modules.hs_features.interest_assessment import render_interest_assessment
            render_interest_assessment(self.user_id, self.ai_engine)
        elif page == "Future Skills Roadmap":
            from modules.hs_features.future_roadmap import render_future_roadmap
            render_future_roadmap(self.user_id, self.ai_engine, portal=self)
        elif page == "Daily Learning Tasks":
            from modules.hs_features.daily_tasks import render_daily_tasks
            render_daily_tasks(self.user_id)
        elif page == "Coding Basics":
            from modules.hs_features.coding_basics import render_coding_basics
            render_coding_basics(self.user_id)
        elif page == "Aptitude Practice":
            from modules.hs_features.aptitude_practice import render_aptitude_practice
            render_aptitude_practice(self.user_id)
        elif page == "Communication Skills":
            from modules.hs_features.communication_skills import render_communication_skills
            render_communication_skills(self.user_id)
        elif page == "Goal Tracker":
            from modules.hs_features.goal_tracker import render_goal_tracker
            render_goal_tracker(self.user_id)
        elif page == "AI Mentor Chatbot":
            from modules.hs_features.ai_mentor import render_ai_mentor
            render_ai_mentor(self.user_id)
        # ── College Module — Student Profile ──
        elif page == "Student Profile":
            from modules.college_features.college_profile import render_college_profile
            render_college_profile(self.user_id, self.ai_engine)
