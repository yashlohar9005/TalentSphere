"""
Seed data script for Working Professional Module.
Run this script once to populate default roles, benchmarks, and a sample user (Arun Kumar).
"""
import sys
import os
import json
import bcrypt

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import engine, SessionLocal, User, init_db
from modules.wp_models import (
    WP_RoleRequirement, WP_TrendingSkill, WP_Certification,
    WP_SalaryBenchmark, WP_ProfessionalProfile, WP_SkillAssessment
)

def seed_data():
    init_db() # Ensure tables exist
    
    session = SessionLocal()
    
    try:
        print("Seeding Config Data...")
        
        # 1. Role Requirements
        roles = [
            ("Senior Backend Engineer", {"Backend Development": 0.4, "System Design": 0.3, "Cloud Computing": 0.2, "DevOps": 0.1}, 3.0),
            ("Backend Architect", {"System Design": 0.4, "Backend Development": 0.3, "Cloud Computing": 0.2, "Leadership": 0.1}, 5.0),
            ("Cloud Engineer", {"Cloud Computing": 0.5, "DevOps": 0.3, "Backend Development": 0.2}, 2.0),
            ("Engineering Lead", {"Leadership": 0.4, "System Design": 0.3, "Backend Development": 0.2, "DevOps": 0.1}, 5.0)
        ]
        
        for name, skills, min_exp in roles:
            if not session.query(WP_RoleRequirement).filter_by(role_name=name).first():
                session.add(WP_RoleRequirement(role_name=name, required_skills_weights=json.dumps(skills), min_experience_years=min_exp))

        # 2. Salary Benchmarks
        benchmarks = [
            ("Senior Backend Engineer", 7.5, 9.0, 12.0),
            ("Backend Architect", 12.0, 15.0, 20.0),
            ("Cloud Engineer", 8.0, 9.0, 13.0),
            ("Engineering Lead", 15.0, 18.0, 25.0)
        ]
        for name, avg, tmin, tmax in benchmarks:
            if not session.query(WP_SalaryBenchmark).filter_by(role_name=name).first():
                session.add(WP_SalaryBenchmark(role_name=name, market_average=avg, target_min=tmin, target_max=tmax))
                
        # 3. Trending Skills
        trends = [
            ("Kubernetes", 38.0, None),
            ("AWS", 32.0, None),
            ("Microservices", 28.0, None),
            ("System Design", 25.0, None)
        ]
        for skill, growth, target in trends:
            if not session.query(WP_TrendingSkill).filter_by(skill_name=skill).first():
                session.add(WP_TrendingSkill(skill_name=skill, demand_growth_percent=growth, target_role=target))
                
        # 4. Certifications
        certs = [
            ("AWS Solutions Architect", "High", "Cloud Computing"),
            ("Docker Certified Associate", "High", "DevOps"),
            ("Kubernetes Administrator", "Medium", "DevOps"),
            ("System Design Fundamentals", "Medium", "System Design")
        ]
        for name, prio, rel in certs:
            if not session.query(WP_Certification).filter_by(name=name).first():
                session.add(WP_Certification(name=name, priority=prio, related_skill=rel))
                
        # 5. Sample User (Yash)
        username = "yash_pro"
        user = session.query(User).filter_by(username=username).first()
        if not user:
            print("Creating sample user Yash...")
            hashed_pw = bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            user = User(username=username, password_hash=hashed_pw, user_type="Working Professional", full_name="Yash")
            session.add(user)
            session.commit()
            
            # Add Profile
            prof = WP_ProfessionalProfile(
                user_id=user.id,
                current_company="TechCorp",
                current_role="Software Developer",
                total_experience_years=4.0,
                career_goals="Become Senior Backend Engineer"
            )
            session.add(prof)
            
            # Add Skills
            scores = {
                "Backend Development": 88,
                "System Design": 72,
                "Cloud Computing": 55,
                "DevOps": 48,
                "Leadership": 70
            }
            for k, v in scores.items():
                session.add(WP_SkillAssessment(user_id=user.id, skill_area=k, score=v))
                
        session.commit()
        print("Seed data successfully added!")
        print("You can log in with username: 'yash_pro' and password: 'password123'")
        
    except Exception as e:
        session.rollback()
        print(f"Error seeding data: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    seed_data()
