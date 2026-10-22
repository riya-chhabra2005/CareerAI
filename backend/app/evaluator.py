import os
import json

def get_fallback_model_answer(topic_tag: str, difficulty: str) -> str:
    """
    Returns a sample professional model answer based on topic tag and difficulty level.
    """
    d = difficulty.capitalize()
    return (
        f"A standard high-quality response for a {d}-level question about {topic_tag} should cover: "
        f"1. A direct, clear definition of the concepts involved. "
        f"2. A practical example showing how you configured, built, or debugged it in past production environments. "
        f"3. Architectural trade-offs (e.g. read/write performance, scaling parameters, security, or state management rules). "
        f"For example, you should detail your deployment settings, unit test metrics, and state exactly how you aligned with team standards."
    )

def evaluate_answer_fallback(
    question_text: str,
    question_type: str,
    topic_tag: str,
    difficulty: str,
    answer_text: str
) -> dict:
    """
    Deterministic rule-based fallback evaluator.
    Grades responses based on length and keyword overlaps, producing realistic JSON feedback.
    """
    text_clean = answer_text.strip()
    word_count = len(text_clean.split())
    
    # Check if answer is too brief or empty
    if len(text_clean) < 30:
        return {
            "overall_score": 45,
            "correctness_score": 2,
            "relevance_score": 3,
            "completeness_score": 1,
            "depth_score": 1,
            "communication_score": 2,
            "strengths": ["Submitted response promptly during the simulator session."],
            "gaps": [
                "Answer is extremely brief and lacks technical elaboration.",
                f"Did not provide clear context, configurations, or coding details on {topic_tag}."
            ],
            "model_answer": get_fallback_model_answer(topic_tag, difficulty),
            "revision_topics": [topic_tag, f"Core concepts of {topic_tag}"]
        }

    # Answer is of moderate length: analyze keyword presence and length
    contains_keyword = topic_tag.lower() in text_clean.lower()
    
    # Calculate dimensional scores
    correctness = 4 if contains_keyword else 3
    relevance = 4 if len(text_clean) > 50 else 3
    completeness = 4 if word_count > 25 else 3
    depth = min(5, 2 + (word_count // 15))
    communication = 4 if word_count > 30 else 3
    
    # Formulate overall score
    base_score = 70
    length_bonus = min(15, word_count // 2)
    keyword_bonus = 10 if contains_keyword else 0
    overall_score = min(98, base_score + length_bonus + keyword_bonus)

    return {
        "overall_score": overall_score,
        "correctness_score": correctness,
        "relevance_score": relevance,
        "completeness_score": completeness,
        "depth_score": depth,
        "communication_score": communication,
        "strengths": [
            f"Grounded response directly in {topic_tag}.",
            "Presented response clearly and with appropriate professional terminology."
        ],
        "gaps": [
            "Could include quantitative results or direct project impact metrics.",
            "Consider discussing alternative architectures or potential scaling bottlenecks."
        ],
        "model_answer": get_fallback_model_answer(topic_tag, difficulty),
        "revision_topics": [topic_tag, f"Advanced {topic_tag} architectures"]
    }

def evaluate_answer(
    question_text: str,
    question_type: str,
    topic_tag: str,
    difficulty: str,
    answer_text: str
) -> dict:
    """
    Evaluates mock interview answers.
    Utilizes Gemini model if key is present, otherwise falls back to deterministic rules.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            
            prompt = f"""
You are an expert technical interviewer. Evaluate the candidate's answer to the interview question below.

Question: {question_text}
Question Type: {question_type}
Topic Tag: {topic_tag}
Difficulty: {difficulty}

Candidate's Actual Answer:
\"\"\"
{answer_text}
\"\"\"

Instructions:
Evaluate the answer on the following 5 dimensions (scores from 1 to 5):
1. Correctness: Technical accuracy of the explanation or code.
2. Relevance: Directness in answering the question.
3. Completeness: Coverage of all components of the question.
4. Technical Depth: Level of details, architectures, or practical examples shown.
5. Communication: Delivery structure, clarity, and articulation.

Formulate an overall rating from 1 to 100 based on these dimensions.
Provide strengths, gaps, an improved professional model answer, and revision recommendations.

Return your response strictly as a raw JSON object matching this schema:
{{
  "overall_score": 78,
  "correctness_score": 4,
  "relevance_score": 5,
  "completeness_score": 3,
  "depth_score": 3,
  "communication_score": 4,
  "strengths": ["List item 1", "List item 2"],
  "gaps": ["List item 1", "List item 2"],
  "model_answer": "Model answer string...",
  "revision_topics": ["Topic A", "Topic B"]
}}
"""
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            result = json.loads(response.text)
            if isinstance(result, dict) and "overall_score" in result:
                return result
        except Exception as e:
            print(f"Gemini API Answer Evaluation failed: {e}. Falling back to rule-based evaluation.")

    return evaluate_answer_fallback(
        question_text, question_type, topic_tag, difficulty, answer_text
    )
