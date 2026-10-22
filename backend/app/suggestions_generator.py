import re
import os
import json
from typing import Optional
from app.match_scorer import extract_skills

# Categories
CAT_WORDING = "Wording"
CAT_QUANTIFY = "Quantify Your Impact"
CAT_SECTIONS = "Missing Sections"

def run_hallucination_check(suggestions: list[dict], resume_text: str) -> list[dict]:
    """
    Validation Pass:
    Extracts tech keywords from the example rewrites and explanations of suggestions.
    Checks if they are present in the original resume.
    If a skill/tool is suggested but not present in the original resume, flags it with
    requires_verification=True and unverified_skills=[...].
    """
    resume_skills = set(extract_skills(resume_text).keys())
    
    validated_suggestions = []
    for sug in suggestions:
        category = sug.get("category", CAT_WORDING)
        explanation = sug.get("explanation", "")
        example_rewrite = sug.get("example_rewrite") or ""
        
        # Extract skills mentioned in the suggestion (explanation and rewrite)
        combined_text = explanation + " " + example_rewrite
        suggested_skills = set(extract_skills(combined_text).keys())
        
        # Find which suggested skills are not in the original resume
        unverified = list(suggested_skills - resume_skills)
        
        # Copy suggestion and append validation flags
        new_sug = {
            "category": category,
            "explanation": explanation,
            "example_rewrite": sug.get("example_rewrite"),
            "requires_verification": len(unverified) > 0,
            "unverified_skills": unverified
        }
        validated_suggestions.append(new_sug)
        
    return validated_suggestions

def generate_suggestions_fallback(resume_text: str, jd_text: str, missing_skills: list[str]) -> list[dict]:
    """
    Advanced rule-based fallback suggestions engine.
    Analyzes the raw resume text and missing skills list to generate highly specific,
    grounded, mentor-style suggestions.
    """
    suggestions = []
    
    # 1. Missing Sections suggestions
    sections = {
        "Projects": ["projects", "personal projects", "portfolio", "key projects"],
        "Summary/Objective": ["summary", "objective", "profile", "about me", "professional summary"],
        "Skills": ["skills", "technologies", "expertise", "core competencies", "technical skills"]
    }
    
    resume_lower = resume_text.lower()
    for section_name, keywords in sections.items():
        found = False
        for kw in keywords:
            pattern = r'(?:^|\n)\s*' + re.escape(kw) + r'\b'
            if re.search(pattern, resume_lower):
                found = True
                break
        if not found:
            sec_type = section_name.split('/')[0]
            suggestions.append({
                "category": CAT_SECTIONS,
                "explanation": f"Your resume lacks an explicit '{sec_type}' section header. Dedicating a specific section for '{sec_type}' is highly recommended to improve ATS parser layout readability.",
                "example_rewrite": f"### {sec_type}\n- [Describe your {sec_type.lower()} here using action-oriented statements]"
            })

    # 2. Wording (Missing Skills) suggestions
    # We suggest adding high-priority missing skills if the user has experience in them
    if missing_skills:
        for skill in missing_skills[:3]: # Propose top 3 missing skills
            suggestions.append({
                "category": CAT_WORDING,
                "explanation": f"The job description emphasizes '{skill}' as a key skill, but it is currently not explicitly mentioned in your resume. If you have experience with '{skill}', integrate it into your work achievements or technical skills summary.",
                "example_rewrite": f"Add '{skill}' to your skills list or list it under a relevant project (e.g. 'Utilized {skill} for building scalable features')."
            })

    # 3. Quantify Your Impact suggestions
    # We look for bullet points in the resume that describe work but contain no numbers/metrics
    lines = [line.strip() for line in resume_text.split('\n') if line.strip()]
    bullet_pattern = r'^(?:•|\*|\-|\▪|\◦)\s*(.*)'
    
    non_quantified_bullets = []
    for line in lines:
        match = re.match(bullet_pattern, line)
        if match:
            content = match.group(1)
            # Check if there are no digits in the content
            if not re.search(r'\b\d+\b', content) and len(content) > 15:
                non_quantified_bullets.append(content)
                
    if non_quantified_bullets:
        for bullet in non_quantified_bullets[:2]: # Suggest quantification for top 2 non-quantified bullets
            # Create a placeholder metrics example rewrite
            suggestions.append({
                "category": CAT_QUANTIFY,
                "explanation": f"Your accomplishments description: \"{bullet}\" lacks measurable impact. Recruiter filters favor quantified achievements (e.g., performance improvements, scaling, percentage reductions, team size).",
                "example_rewrite": f"{bullet}, improving execution efficiency by [X]% and reducing system downtime by [Y]%."
            })
    else:
        # Generic suggestion if no bullet points matched or if they are already quantified
        suggestions.append({
            "category": CAT_QUANTIFY,
            "explanation": "Ensure all major project bullet points have measurable results. Instead of just stating what you built, mention the scale: database size, number of active users, or latency improvements.",
            "example_rewrite": "Built REST APIs in Python [supporting X active users and reducing database query response time by Y%]."
        })

    return suggestions

def generate_suggestions(resume_text: str, jd_text: str, missing_skills: list[str]) -> list[dict]:
    """
    Main suggestions coordinator. Attempts to query the Gemini API if available,
    otherwise gracefully falls back to the deterministic rule-based generator.
    Always runs the anti-hallucination validation check on suggestions.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    suggestions = []
    
    if api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            
            # Use gemini-1.5-flash model
            model = genai.GenerativeModel("gemini-1.5-flash")
            
            prompt = f"""
You are an expert career advisor. Analyze this Resume and Job Description (JD) along with the missing skills list.
Provide actionable suggestions to improve the resume.

Resume:
\"\"\"
{resume_text}
\"\"\"

Job Description:
\"\"\"
{jd_text}
\"\"\"

Missing Skills (from JD, absent in Resume):
{", ".join(missing_skills)}

Instructions:
1. Divide suggestions into these exact categories:
   - "Wording": Rewrite existing bullet points from the resume to reflect JD keywords and show technical depth.
   - "Quantify Your Impact": Locate weak bullet points that lack metrics and rewrite them to add placeholders or suggest metrics.
   - "Missing Sections": Point out missing sections (like summary, projects) or skills groupings that should be added.
2. CRITICAL - NO FABRICATION:
   - Do NOT fabricate work experience, project names, or degrees.
   - Example rewrites must improve the existing wording and bullet points already present in the resume. 
   - Never invent achievements that are completely absent in the original work history.
3. Output format must be a raw JSON array of objects.

JSON schema:
[
  {{
    "category": "Wording",
    "explanation": "Mentor explanation here...",
    "example_rewrite": "improved bullet point with placeholders or specific phrasing"
  }}
]
"""
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            suggestions = json.loads(response.text)
        except Exception as e:
            print(f"Gemini API suggestions generation failed: {e}. Falling back to rule-based generation.")
            suggestions = generate_suggestions_fallback(resume_text, jd_text, missing_skills)
    else:
        suggestions = generate_suggestions_fallback(resume_text, jd_text, missing_skills)
        
    # Run verification pass to flag/unverify hallucinated skills
    return run_hallucination_check(suggestions, resume_text)
