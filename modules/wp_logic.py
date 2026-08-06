"""
Working Professional Logic Module

Contains core rule-based algorithms for the Working Professional Module:
- Career Transition Matching
- Promotion Readiness Scoring
- Salary Benchmarking
- Certification Recommendations
"""
import json

def calculate_promotion_readiness(years_exp, project_complexity, leadership_score, tech_score, comms_score, team_score):
    """
    Computes a weighted Promotion Readiness % based on multiple factors.
    Weights: Technical (35%), Leadership (25%), Communication (15%), Team/Project (15%), Experience Base (10%)
    """
    # Normalize inputs to 100 max
    tech_w = (tech_score / 100) * 35
    lead_w = (leadership_score / 100) * 25
    comm_w = (comms_score / 100) * 15
    team_proj_score = (project_complexity + team_score) / 2
    team_w = (team_proj_score / 100) * 15
    
    # Experience gives a baseline boost (up to 10% for >= 5 years)
    exp_w = min(years_exp * 2, 10)
    
    total = tech_w + lead_w + comm_w + team_w + exp_w
    
    return {
        "Promotion Readiness %": int(total),
        "Technical Readiness": tech_score,
        "Leadership Readiness": leadership_score,
        "Communication Readiness": comms_score
    }

def match_career_transition(user_skill_scores, role_requirements):
    """
    Given a user's skill scores (dict: area -> score 0-100) and a list of 
    WP_RoleRequirement objects, returns a ranked list of roles and match %.
    
    user_skill_scores: e.g. {"Backend Development": 88, "System Design": 72}
    role_requirements: list of WP_RoleRequirement instances.
    """
    matches = []
    
    for role in role_requirements:
        reqs = json.loads(role.required_skills_weights)
        total_weight = 0
        weighted_score = 0
        
        for skill, weight in reqs.items():
            user_score = user_skill_scores.get(skill, 0)
            weighted_score += user_score * weight
            total_weight += weight
            
        if total_weight > 0:
            match_pct = int(weighted_score / total_weight)
        else:
            match_pct = 0
            
        matches.append({
            "Next Role": role.role_name,
            "Match %": match_pct
        })
        
    matches.sort(key=lambda x: x["Match %"], reverse=True)
    return matches

def advanced_job_matching(user_profile, user_skill_scores, role_requirements):
    """
    Similar to match_career_transition but factors in Experience and Salary Expectations.
    (Simplified rule-based approach)
    """
    matches = match_career_transition(user_skill_scores, role_requirements)
    # Apply a slight penalty if min experience is not met
    user_exp = user_profile.total_experience_years or 0
    
    for role_model in role_requirements:
        for match in matches:
            if match["Next Role"] == role_model.role_name:
                if user_exp < role_model.min_experience_years:
                    penalty = (role_model.min_experience_years - user_exp) * 5
                    match["Match %"] = max(0, match["Match %"] - int(penalty))
                    
    matches.sort(key=lambda x: x["Match %"], reverse=True)
    return matches

def get_salary_growth(current_salary, target_role, salary_benchmarks):
    """
    Calculates potential salary growth.
    salary_benchmarks is a list of WP_SalaryBenchmark instances.
    """
    for sb in salary_benchmarks:
        if sb.role_name == target_role:
            growth_pct = ((sb.market_average - current_salary) / current_salary) * 100 if current_salary > 0 else 0
            return {
                "Market Average": sb.market_average,
                "Target Range": f"₹{sb.target_min} - ₹{sb.target_max} LPA",
                "Potential Growth %": int(growth_pct)
            }
    return None

def recommend_certifications(user_skill_scores, target_role_req, certifications_list):
    """
    Recommends certifications based on user's lowest skills required by the target role.
    target_role_req is a WP_RoleRequirement.
    certifications_list is a list of WP_Certification.
    """
    if not target_role_req:
        return []
        
    reqs = json.loads(target_role_req.required_skills_weights)
    
    # Find skills where user score is < 70
    gaps = []
    for skill in reqs.keys():
        score = user_skill_scores.get(skill, 0)
        if score < 70:
            gaps.append(skill)
            
    recs = []
    for cert in certifications_list:
        if cert.related_skill in gaps:
            recs.append({
                "Certification": cert.name,
                "Priority": cert.priority,
                "Related Skill": cert.related_skill
            })
            
    # Sort High -> Medium -> Low
    priority_map = {"High": 1, "Medium": 2, "Low": 3}
    recs.sort(key=lambda x: priority_map.get(x["Priority"], 4))
    return recs

def generate_action_plan(user_skill_scores):
    """
    Generates a 90-Day Action Plan focusing on the user's lowest skills.
    """
    if not user_skill_scores:
        return []
        
    # Sort skills by score ascending
    sorted_skills = sorted(user_skill_scores.items(), key=lambda x: x[1])
    lowest = [s[0] for s in sorted_skills[:3]]
    
    plan = []
    if len(lowest) > 0:
        plan.append({"Month": "Month 1", "Focus": f"Core Fundamentals in {lowest[0]}"})
    if len(lowest) > 1:
        plan.append({"Month": "Month 2", "Focus": f"Advanced Practices in {lowest[1]}"})
    if len(lowest) > 2:
        plan.append({"Month": "Month 3", "Focus": f"Integration & Mastery of {lowest[2]}"})
        
    return plan
