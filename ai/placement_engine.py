class PlacementEngine:
    def calculate_readiness(self, data: dict) -> dict:
        """
        Calculates Placement Readiness using weighted factors:
        Resume (20%), ATS (15%), Coding (25%), Projects (15%), 
        Communication (10%), Internship (10%), Certification (5%).
        """
        resume_score = data.get("resume_score", 0)
        ats_score = data.get("ats_score", 0)
        coding_score = data.get("coding_score", 0)
        projects_score = data.get("projects_score", 0)
        comm_score = data.get("communication_score", 0)
        internship_score = data.get("internship_score", 0)
        cert_score = data.get("certification_score", 0)
        
        # Calculate weighted final score
        placement_score = (
            (resume_score * 0.25) +
            (coding_score * 0.30) +
            (projects_score * 0.20) +
            (comm_score * 0.15) +
            (internship_score * 0.10) # Mapping Experience to internship_score/experience_score
        )
        
        placement_score = int(placement_score)
        industry_readiness = min(placement_score + 5, 100) # Slight heuristic for industry readiness
        
        if placement_score >= 80:
            overall_recommendation = "Highly Prepared. Focus on top-tier product companies."
        elif placement_score >= 60:
            overall_recommendation = "Moderately Prepared. Focus on improving technical and coding skills."
        else:
            overall_recommendation = "Needs Preparation. Start a 90-day learning roadmap immediately."
            
        strengths = []
        weaknesses = []
        improvement_plan = []
        
        if coding_score >= 75:
            strengths.append("Strong Coding Skills")
        else:
            weaknesses.append("Needs Coding Practice")
            improvement_plan.append("Complete Advanced Data Structures modules.")
            
        if resume_score >= 80:
            strengths.append("Excellent Resume")
        else:
            weaknesses.append("Resume needs ATS optimization")
            improvement_plan.append("Use Resume Builder to improve keyword matches.")
            
        if comm_score >= 80:
            strengths.append("Great Communication")
        else:
            weaknesses.append("Communication could be improved")
            improvement_plan.append("Practice more Mock Interviews.")
            
        if not strengths:
            strengths.append("Developing foundational skills")
        if not improvement_plan:
            improvement_plan.append("Apply to target companies!")

        return {
            "placement_score": placement_score,
            "industry_readiness": industry_readiness,
            "overall_recommendation": overall_recommendation,
            "strength_analysis": strengths,
            "weakness_analysis": weaknesses,
            "improvement_plan": improvement_plan,
            "details": {
                "Resume (25%)": int(resume_score * 0.25),
                "Coding (30%)": int(coding_score * 0.30),
                "Projects (20%)": int(projects_score * 0.20),
                "Communication (15%)": int(comm_score * 0.15),
                "Experience (10%)": int(internship_score * 0.10)
            }
        }
