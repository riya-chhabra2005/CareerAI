import os
import json
import random

def generate_prep_questions_fallback(
    role_title: str,
    experience_level: str,
    resume_skills: list[str],
    matched_skills: list[str],
    missing_skills: list[str]
) -> list[dict]:
    """
    Deterministic rule-based fallback generator.
    Creates 9 highly customized interview questions grouped into Technical, Coding, and HR/Behavioral,
    specifically focusing on matched and missing skills.
    """
    questions = []

    # Safe defaults if skill lists are empty
    matched = matched_skills if matched_skills else (resume_skills if resume_skills else ["Software Engineering"])
    missing = missing_skills if missing_skills else ["System Design"]
    
    # Primary programming language detection from resume skills
    prog_lang = "Python"
    lang_options = ["JavaScript", "TypeScript", "Java", "C++", "C#", "Go", "Ruby", "PHP"]
    for lang in lang_options:
        if lang in resume_skills:
            prog_lang = lang
            break

    # Determine difficulties based on experience level
    diff_tier = "Medium"
    if "senior" in role_title.lower() or "lead" in role_title.lower() or "5+" in experience_level or "mid" not in experience_level.lower() and "1-3" not in experience_level:
        diff_tier = "Hard"
    elif "junior" in role_title.lower() or "intern" in role_title.lower() or "0-1" in experience_level:
        diff_tier = "Easy"

    # 1. Technical Questions (3)
    questions.append({
        "question_text": f"Explain the core architectural concepts of {matched[0]}. In your experience, what are some of the common pitfalls developers encounter when working with it, and how do you resolve them?",
        "type": "technical",
        "difficulty": diff_tier,
        "topic_tag": matched[0]
    })
    
    questions.append({
        "question_text": f"The job description highlights a requirement for {missing[0]}. Since this is currently a skill gap on your profile, how do you see it fitting into our tech stack, and what steps would you take to ramp up quickly?",
        "type": "technical",
        "difficulty": diff_tier,
        "topic_tag": missing[0]
    })

    sub_topic = matched[1] if len(matched) > 1 else (missing[1] if len(missing) > 1 else "Database Design")
    questions.append({
        "question_text": f"Walk me through a system architecture design involving {sub_topic}. How do you ensure high availability, data consistency, and low latency?",
        "type": "technical",
        "difficulty": "Hard" if diff_tier == "Medium" else diff_tier,
        "topic_tag": sub_topic
    })

    # 2. Coding Questions (3)
    questions.append({
        "question_text": f"Implement a function in {prog_lang} to reverse a singly linked list in-place. Discuss the time and space complexity of your solution.",
        "type": "coding",
        "difficulty": "Easy" if diff_tier == "Easy" else "Medium",
        "topic_tag": "Algorithms"
    })

    coding_topic = missing[1] if len(missing) > 1 else (matched[2] if len(matched) > 2 else "API Design")
    questions.append({
        "question_text": f"Write a code snippet or design the schema/routes representing how you would implement a secure authentication rate-limiter using {coding_topic}.",
        "type": "coding",
        "difficulty": diff_tier,
        "topic_tag": coding_topic
    })

    questions.append({
        "question_text": "Given an array of integers representing stock prices on consecutive days, write an efficient function to find the maximum profit you could make by buying and selling once. Optimize it to run in O(n) time.",
        "type": "coding",
        "difficulty": diff_tier,
        "topic_tag": "Data Structures"
    })

    # 3. HR / Behavioral Questions (3)
    questions.append({
        "question_text": f"Tell me about a time you had to work on a project involving {missing[0]} or a similar unfamiliar technology. How did you handle the learning curve under pressure, and what was the outcome?",
        "type": "hr",
        "difficulty": "Medium",
        "topic_tag": "Problem Solving"
    })

    questions.append({
        "question_text": f"Describe a situation where you had a strong technical disagreement with a team member or senior architect regarding how to build a feature. How did you communicate your viewpoints and resolve the conflict?",
        "type": "hr",
        "difficulty": "Medium",
        "topic_tag": "Collaboration"
    })

    questions.append({
        "question_text": f"What motivated you to apply for this {role_title} position? How do your strengths in {matched[0]} and your career goals align with what we are building here?",
        "type": "hr",
        "difficulty": "Easy",
        "topic_tag": "Motivation"
    })

    return questions

def generate_prep_questions(
    role_title: str,
    experience_level: str,
    resume_skills: list[str],
    matched_skills: list[str],
    missing_skills: list[str],
    jd_text: str
) -> list[dict]:
    """
    Main generator coordinator. Queries Gemini if GEMINI_API_KEY is present,
    otherwise falls back to generating a deterministic, highly relevant prep plan.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            
            prompt = f"""
You are an expert technical interviewer. Create a personalized interview preparation plan for a candidate.

Target Job Role: {role_title}
Experience Level: {experience_level}
Job Description Text:
\"\"\"
{jd_text}
\"\"\"

Candidate's Resume Skills: {", ".join(resume_skills)}
Matched Skills (strengths): {", ".join(matched_skills)}
Missing Skills (weakness/gaps): {", ".join(missing_skills)}

Instructions:
1. Generate exactly 9 questions divided equally into three types:
   - 3 Technical Questions: Focus on concepts, split between matched strengths and missing gaps.
   - 3 Coding Questions: Algorithm, coding, or system schema design questions suited to their experience level.
   - 3 HR/Behavioral Questions: HR, teamwork, and problem-solving questions.
2. Weight the plan towards their missing gaps, but do not ignore their matched strengths.
3. Return the result as a raw JSON array of objects.

JSON schema:
[
  {{
    "question_text": "...",
    "type": "technical", // Must be exactly 'technical', 'coding', or 'hr'
    "difficulty": "Medium", // Easy, Medium, or Hard
    "topic_tag": "FastAPI" // Short topic name (e.g. React, SQL, Algorithms, Collaboration)
  }}
]
"""
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            questions = json.loads(response.text)
            if isinstance(questions, list) and len(questions) > 0:
                return questions
        except Exception as e:
            print(f"Gemini API interview plan generation failed: {e}. Falling back to rule-based generation.")
            
    return generate_prep_questions_fallback(
        role_title, experience_level, resume_skills, matched_skills, missing_skills
    )
