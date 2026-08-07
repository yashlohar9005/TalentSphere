"""
Working Professional Database Models

Defines the SQLAlchemy models specific to the Working Professional module.
These models are designed to be imported into `app.py` before `init_db()`
so they are automatically created in the existing `talentsphere.db`.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
import sys
import os

# Add parent directory to path so we can import from database
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import Base

class WP_ProfessionalProfile(Base):
    """
    Stores the professional's profile details including their current role and skills.
    """
    __tablename__ = 'wp_professional_profile'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, unique=True)
    
    current_company = Column(String(200), nullable=True)
    current_role = Column(String(200), nullable=True)
    total_experience_years = Column(Float, nullable=True)
    
    # Stored as JSON strings
    technical_skills = Column(Text, nullable=True) 
    leadership_experience = Column(Boolean, default=False)
    leadership_description = Column(Text, nullable=True)
    certifications = Column(Text, nullable=True)
    career_goals = Column(Text, nullable=True)
    preferred_job_roles = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User")

class WP_SkillAssessment(Base):
    """
    Stores individual skill area assessments for the user.
    """
    __tablename__ = 'wp_skill_assessment'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    skill_area = Column(String(100), nullable=False)
    score = Column(Float, nullable=False) # 0 to 100
    
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")

class WP_RoleRequirement(Base):
    """
    Config table mapping roles to required skills and their weights.
    """
    __tablename__ = 'wp_role_requirement'

    id = Column(Integer, primary_key=True, autoincrement=True)
    role_name = Column(String(200), nullable=False, unique=True)
    
    # JSON string mapping skill_area -> weight (e.g., {"Backend Development": 0.8})
    required_skills_weights = Column(Text, nullable=False) 
    min_experience_years = Column(Float, default=0.0)
    
class WP_TrendingSkill(Base):
    """
    Config table for trending skills in the industry.
    """
    __tablename__ = 'wp_trending_skill'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    skill_name = Column(String(100), nullable=False, unique=True)
    demand_growth_percent = Column(Float, nullable=False)
    target_role = Column(String(200), nullable=True) # Optional, if tied to a specific role

class WP_Certification(Base):
    """
    Config table mapping certifications to skills.
    """
    __tablename__ = 'wp_certification'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    priority = Column(String(50), nullable=False) # High, Medium, Low
    related_skill = Column(String(100), nullable=False)

class WP_SalaryBenchmark(Base):
    """
    Config table storing average and target salaries for roles.
    """
    __tablename__ = 'wp_salary_benchmark'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    role_name = Column(String(200), nullable=False, unique=True)
    market_average = Column(Float, nullable=False)
    target_min = Column(Float, nullable=False)
    target_max = Column(Float, nullable=False)


class WP_ResumeAnalysis(Base):
    """
    Stores resume analysis and improvement recommendations for working professionals.
    """
    __tablename__ = 'wp_resume_analysis'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    filename = Column(String(200), nullable=False)
    file_type = Column(String(20), nullable=False)  # pdf, docx, txt
    completeness_score = Column(Integer, default=0)
    
    # Stored as JSON strings
    extracted_skills = Column(Text, nullable=True)
    missing_skills = Column(Text, nullable=True)
    outdated_skills = Column(Text, nullable=True)
    recommended_skills = Column(Text, nullable=True)
    suggestions_json = Column(Text, nullable=True)
    
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")


class WP_LeadershipEvaluation(Base):
    """
    Stores 7-dimension leadership evaluations and AI readiness scores.
    """
    __tablename__ = 'wp_leadership_evaluation'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, unique=True)
    
    # 7 Core Leadership Dimensions (0-100)
    team_coordination = Column(Float, default=50.0)
    mentoring = Column(Float, default=50.0)
    decision_making = Column(Float, default=50.0)
    conflict_resolution = Column(Float, default=50.0)
    project_ownership = Column(Float, default=50.0)
    communication = Column(Float, default=50.0)
    strategic_thinking = Column(Float, default=50.0)
    
    overall_score = Column(Float, default=50.0)
    grade = Column(String(50), default="B Developing Leader")
    promotion_impact = Column(Float, default=0.0)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User")


class WP_CareerCoachChat(Base):
    """
    Stores conversation history between working professional and AI Career Coach.
    """
    __tablename__ = 'wp_career_coach_chat'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")

