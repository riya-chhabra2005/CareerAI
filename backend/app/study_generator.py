import os
import json

def generate_study_plan_fallback(
    role_title: str,
    experience_level: str,
    duration: int,
    weak_topics: list[str],
    matched_skills: list[str]
) -> list[dict]:
    """
    Deterministic spaced-learning rule-based generator.
    Creates a customized study guide of N days containing achievable tasks
    grounded in candidate career parameters and weak areas.
    """
    days = []
    
    # Safe fallback if user has no weak topics yet
    topics = weak_topics if weak_topics else (matched_skills if matched_skills else ["System Design", "Data Structures", "Algorithms"])
    
    for d in range(1, duration + 1):
        if d == 1:
            days.append({
                "day_number": 1,
                "theme": "Diagnostic Setup & Pathway Alignment",
                "action_items": [
                    f"Review target requirements for the {role_title} role.",
                    "Review matching score gaps in your dashboard profile.",
                    "Set up a dedicated git repository for logging your daily study progress."
                ]
            })
        elif d == duration:
            days.append({
                "day_number": duration,
                "theme": "Mock Simulator Challenge & Final Review",
                "action_items": [
                    "Conduct a full 9-question Mock Interview in the Simulator.",
                    "Inspect overall progress metrics and Recharts progression lines in your Dashboard.",
                    "Update your resume with verified accomplishments before sending applications."
                ]
            })
        elif d % 4 == 0:
            # Spacing lighter review days to avoid burnout
            days.append({
                "day_number": d,
                "theme": "Refinement, Quantification & Spaced Review",
                "action_items": [
                    "Quantify your resume bullets using metric placeholders: [X]%.",
                    "Refactor layouts and Date Formatting in your Section Headings.",
                    "Read technical blogs on scaling best practices and rest."
                ]
            })
        else:
            # Topic focused day
            # Cycle through weak topics
            topic = topics[(d - 2) % len(topics)]
            
            # Alternate between concept dive and hands-on coding application
            if d % 2 == 0:
                days.append({
                    "day_number": d,
                    "theme": f"Deep Dive: {topic} Core Principles",
                    "action_items": [
                        f"Read core docs, RFCs, or best practices regarding {topic}.",
                        f"Write a brief summary explaining how {topic} handles state, memory, or networking.",
                        f"Draft a resume bullet point detailing how you configured {topic} in past roles."
                    ]
                })
            else:
                days.append({
                    "day_number": d,
                    "theme": f"Hands-on Practice: {topic} Integrations",
                    "action_items": [
                        f"Implement a small utility or API showcasing a {topic} integration.",
                        f"Solve 2 coding challenges or conceptual problems testing {topic}.",
                        f"Test performance bottlenecks or edge cases of your {topic} implementation."
                    ]
                })

    return days

def generate_study_plan(
    role_title: str,
    experience_level: str,
    duration: int,
    weak_topics: list[str],
    matched_skills: list[str],
    ats_score: int,
    match_score: int
) -> list[dict]:
    """
    Generates personalized study plans.
    Leverages Gemini if API key is present, otherwise triggers rule-based schedules.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            
            prompt = f"""
You are an expert career mentor and technical educator. Create a personalized day-by-day study plan.

Target Job Role: {role_title}
Experience Level: {experience_level}
Duration: {duration} days
Weak Topics (prioritize these): {", ".join(weak_topics)}
Matched Strengths: {", ".join(matched_skills)}
Latest ATS Score: {ats_score}
Latest JD Match Score: {match_score}

Instructions:
1. Generate exactly {duration} days of structured study guidelines.
2. Each day must contain a focused "theme" and a list of exactly 3 concrete, realistic "action_items" (review concepts, code utilities, revise resume sections).
3. Weight the plan so that the most critical weak topics are introduced early when candidate motivation is highest. Include lighter review days (every 4-5 days) to prevent burnout.
4. Output the result strictly as a raw JSON array of objects.

JSON schema:
[
  {{
    "day_number": 1,
    "theme": "...",
    "action_items": ["Action 1", "Action 2", "Action 3"]
  }}
]
"""
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            result = json.loads(response.text)
            if isinstance(result, list) and len(result) > 0:
                return result
        except Exception as e:
            print(f"Gemini Study Plan generation failed: {e}. Falling back to rule-based generation.")

    return generate_study_plan_fallback(
        role_title, experience_level, duration, weak_topics, matched_skills
    )
