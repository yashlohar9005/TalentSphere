"""
Resume Analyzer for TalentSphere Elevate.
Enhanced Rule-based ATS Resume Checker and Parser.
"""
import re
import json
import spacy
import nltk

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    # Fallback if model isn't downloaded yet
    nlp = None

class ResumeAnalyzer:
    def parse_resume(self, file_content: bytes, filename: str) -> dict:
        """
        Extract text from PDF/DOCX and populate Student Profile fields.
        Note: For simplicity in this demo, this parses plaintext or relies on 
        external libraries like PyPDF2 if available. We will simulate the extraction 
        heuristically.
        """
        # In a real environment, you would use PyPDF2 or python-docx here.
        # We will assume `file_content` is passed as string for text resumes, 
        # or we gracefully extract some mock data if it's binary.
        try:
            text = file_content.decode('utf-8', errors='ignore')
        except:
            text = str(file_content)
            
        parsed_data = {
            "name": "",
            "email": "",
            "phone": "",
            "college": "",
            "degree": "",
            "skills": "",
            "projects": "",
            "internships": "",
            "certifications": "",
            "experience": "",
            "github": "",
            "linkedin": ""
        }
        
        # Simple regex heuristics for extraction
        email_match = re.search(r'[\w\.-]+@[\w\.-]+', text)
        if email_match: parsed_data["email"] = email_match.group(0)
            
        phone_match = re.search(r'\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}', text)
        if phone_match: parsed_data["phone"] = phone_match.group(0)
            
        linkedin_match = re.search(r'linkedin\.com/in/[\w-]+', text)
        if linkedin_match: parsed_data["linkedin"] = "https://" + linkedin_match.group(0)
            
        github_match = re.search(r'github\.com/[\w-]+', text)
        if github_match: parsed_data["github"] = "https://" + github_match.group(0)
            
        # Basic section extraction heuristic
        sections = {"skills": [], "projects": [], "experience": [], "education": []}
        current_section = None
        for line in text.split('\n'):
            lower_line = line.strip().lower()
            if "skill" in lower_line and len(lower_line) < 20:
                current_section = "skills"
            elif "project" in lower_line and len(lower_line) < 20:
                current_section = "projects"
            elif ("experience" in lower_line or "employment" in lower_line) and len(lower_line) < 20:
                current_section = "experience"
            elif "education" in lower_line and len(lower_line) < 20:
                current_section = "education"
            elif current_section and line.strip():
                sections[current_section].append(line.strip())
                
        parsed_data["skills"] = "\n".join(sections["skills"])
        parsed_data["projects"] = "\n".join(sections["projects"])
        parsed_data["experience"] = "\n".join(sections["experience"])
        parsed_data["degree"] = "\n".join(sections["education"][:2]) # Just grab first few lines
        
        return parsed_data

    def _extract_skills_nlp(self, text: str) -> list:
        """
        Uses spaCy NER and NLTK for advanced skill extraction.
        """
        if not nlp:
            return []
            
        doc = nlp(text)
        skills = set()
        
        # Simple extraction heuristic based on proper nouns and known keywords
        known_tech = {"python", "java", "sql", "aws", "docker", "kubernetes", "react", "fastapi", "postgresql"}
        
        for token in doc:
            if token.text.lower() in known_tech:
                skills.add(token.text.capitalize())
            # Noun chunks could also be analyzed here
                
        return list(skills)

    def analyze_resume(self, resume_text: str, target_role: str = "") -> dict:
        """
        Evaluate Skills, Keywords, Education, Projects, Experience.
        Generate comprehensive ATS Scores and feedback.
        """
        text = resume_text.lower()
        
        # Sub-scores
        education_score = 0
        project_score = 0
        experience_score = 0
        tech_skills_score = 0
        soft_skills_score = 0
        formatting_score = 70 # Default base
        keyword_match = 0
        
        strengths = []
        weaknesses = []
        suggestions = []
        
        # Education Check
        if re.search(r'\b(education|university|college|degree|btech|bsc|bachelor)\b', text):
            education_score = 90
            strengths.append("Contains clear Education section.")
        else:
            education_score = 30
            weaknesses.append("Missing Education section.")
            suggestions.append("Add your educational background prominently.")
            
        # Experience Check
        if re.search(r'\b(experience|work|employment|internship)\b', text):
            experience_score = 85
            strengths.append("Contains Experience/Internship section.")
        else:
            experience_score = 40
            weaknesses.append("Missing Experience section.")
            suggestions.append("Detail your past work or internship experience.")
            
        # Projects Check
        if re.search(r'\b(projects|portfolio)\b', text):
            project_score = 90
            strengths.append("Contains Projects section.")
        else:
            project_score = 30
            weaknesses.append("Missing Projects section.")
            suggestions.append("Showcase your portfolio or academic projects.")
            
        # Tech Skills Check
        if re.search(r'\b(skills|technologies|tools|languages|frameworks)\b', text):
            tech_skills_score = 85
            strengths.append("Contains Technical Skills section.")
            if not re.search(r'\b(sql|git)\b', text):
                weaknesses.append("Missing standard tech keywords (e.g., SQL, Git).")
                suggestions.append("Missing SQL. Missing Git. Add these if you know them.")
        else:
            tech_skills_score = 40
            weaknesses.append("Missing Skills section.")
            suggestions.append("List your hard skills clearly.")
            
        # Soft Skills Check
        soft_skills = ['leadership', 'communication', 'teamwork', 'agile', 'problem solving', 'management']
        found_soft = [s for s in soft_skills if s in text]
        if found_soft:
            soft_skills_score = min(50 + (len(found_soft) * 10), 100)
        else:
            soft_skills_score = 40
            suggestions.append("Add soft skills like 'Leadership', 'Teamwork', or 'Agile'.")

        # Action Verbs & Metrics Check
        if re.search(r'\b(increased|reduced|developed|led|managed|achieved|improved)\b', text):
            formatting_score += 15
        else:
            weaknesses.append("Weak action verbs used.")
            suggestions.append("Use strong action verbs (e.g., Developed, Achieved, Led).")
            
        if re.search(r'\d+%', text) or re.search(r'\$\d+', text):
            formatting_score += 15
        else:
            suggestions.append("Add measurable achievements (e.g., 'improved efficiency by 20%').")
            
        formatting_score = min(formatting_score, 100)

        # Target role keyword matching
        if target_role:
            target_words = set(target_role.lower().replace(',', ' ').split())
            resume_words = set(text.replace(',', ' ').split())
            overlap = target_words.intersection(resume_words)
            if len(target_words) > 0:
                keyword_match = int((len(overlap) / len(target_words)) * 100)
            
            if keyword_match > 60:
                strengths.append(f"Good keyword match for '{target_role}'.")
            else:
                weaknesses.append(f"Weak technical keywords for '{target_role}'.")
                missing = target_words - resume_words
                if missing:
                    suggestions.append(f"Incorporate missing keywords: {', '.join(list(missing)[:5])}.")
        else:
            keyword_match = 70 # default if no role specified

        # Objective Check
        if not re.search(r'\b(objective|summary)\b', text):
            suggestions.append("Improve Career Objective / Add a Summary section.")

        # Calculate final aggregated scores
        ats_compatibility = int((formatting_score + keyword_match + tech_skills_score) / 3)
        resume_score = int((education_score + experience_score + project_score + tech_skills_score + soft_skills_score + formatting_score) / 6)
        
        job_compatibility = "High Fit" if ats_compatibility >= 80 else "Medium Fit" if ats_compatibility >= 60 else "Low Fit"
        
        industry_recommendation = "Technology / IT"
        if re.search(r'\b(data|machine learning|ai|statistics|analytics)\b', text):
            industry_recommendation = "Data Science & AI"
        elif re.search(r'\b(finance|accounting|banking|investment)\b', text):
            industry_recommendation = "Finance"
        elif re.search(r'\b(marketing|seo|sales|brand)\b', text):
            industry_recommendation = "Marketing & Sales"
        
        return {
            "resume_score": min(resume_score, 100),
            "ats_compatibility": min(ats_compatibility, 100),
            "keyword_match": min(keyword_match, 100),
            "formatting_score": formatting_score,
            "education_score": education_score,
            "project_score": project_score,
            "experience_score": experience_score,
            "technical_skills_score": tech_skills_score,
            "soft_skills_score": soft_skills_score,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "suggestions": suggestions,
            "job_compatibility": job_compatibility,
            "industry_recommendation": industry_recommendation
        }
