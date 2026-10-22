import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from app.database import SessionLocal
from app.models import User, Resume, JobDescription, InterviewPlan, PrepQuestion, InterviewSession, Answer, Evaluation
from app.schemas import DashboardResponse
from app.auth import get_db, get_current_user
from app.ats_scorer import calculate_ats_score
from app.match_scorer import calculate_blend_match

router = APIRouter(tags=["Analytics Dashboard"])

@router.get("/dashboard", response_model=DashboardResponse)
def get_user_dashboard_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Latest Resume & ATS Score
    latest_resume = db.query(Resume).filter(Resume.user_id == current_user.id).order_by(Resume.created_at.desc()).first()
    latest_ats_score = None
    if latest_resume:
        try:
            latest_ats_score = calculate_ats_score(latest_resume.raw_text)["score"]
        except Exception as e:
            print(f"Failed to calculate rolling ATS score: {e}")

    # 2. Latest Job Description & Match Score
    latest_jd = db.query(JobDescription).filter(JobDescription.user_id == current_user.id).order_by(JobDescription.created_at.desc()).first()
    latest_match_score = None
    if latest_resume and latest_jd:
        try:
            latest_match_score = calculate_blend_match(latest_resume.raw_text, latest_jd.raw_jd_text)["match_score"]
        except Exception as e:
            print(f"Failed to calculate rolling Match score: {e}")

    # 3. Total Answers Submitted (Questions Attempted)
    questions_attempted = db.query(Answer).join(InterviewSession).filter(InterviewSession.user_id == current_user.id).count()

    # 4. Fetch all user evaluations
    evals = db.query(Evaluation).join(Answer).join(InterviewSession).filter(InterviewSession.user_id == current_user.id).all()

    # 5. Average Interview Score
    avg_interview_score = None
    if evals:
        avg_interview_score = int(sum(e.overall_score for e in evals) / len(evals))

    # 6. Evaluation Score History over time (Line Chart)
    # Sorted chronologically by answer submission time
    evals_sorted = sorted(evals, key=lambda x: x.created_at)
    score_history = []
    for idx, e in enumerate(evals_sorted):
        score_history.append({
            "idx": idx + 1,
            "date": e.created_at.strftime("%Y-%m-%d"),
            "score": e.overall_score,
            "topic": e.answer.question.topic_tag if e.answer.question else "General"
        })

    # 7. Topic Performance (Bar Chart)
    topic_scores = {}
    for e in evals:
        if e.answer.question:
            topic = e.answer.question.topic_tag
            if topic not in topic_scores:
                topic_scores[topic] = []
            topic_scores[topic].append(e.overall_score)

    topic_performance = []
    for topic, scores in topic_scores.items():
        topic_performance.append({
            "topic": topic,
            "score": int(sum(scores) / len(scores)),
            "count": len(scores)
        })
    topic_performance = sorted(topic_performance, key=lambda x: x["score"], reverse=True)

    # 8. Weak Topics list (average score < 70)
    weak_topics_dict = {}
    for e in evals:
        if e.overall_score < 70 and e.answer.question:
            topic = e.answer.question.topic_tag
            weak_topics_dict[topic] = weak_topics_dict.get(topic, 0) + 1
    # Sorted by fail count descending
    weak_topics = [topic for topic, count in sorted(weak_topics_dict.items(), key=lambda x: x[1], reverse=True)]

    # 9. Revision Topics recommendations list
    rev_topics_set = set()
    for e in evals:
        try:
            topics = json.loads(e.revision_topics)
            for t in topics:
                rev_topics_set.add(t)
        except Exception:
            pass
    revision_topics = list(rev_topics_set)[:6]  # Limit to top 6 topics

    # 10. Recent Interview Sessions list
    sessions = db.query(InterviewSession).filter(InterviewSession.user_id == current_user.id).order_by(InterviewSession.started_at.desc()).limit(5).all()
    recent_sessions = []
    for s in sessions:
        # Calculate session average score
        sess_evals = db.query(Evaluation).join(Answer).filter(Answer.session_id == s.id).all()
        sess_score = None
        if sess_evals:
            sess_score = int(sum(se.overall_score for se in sess_evals) / len(sess_evals))
            
        plan = db.query(InterviewPlan).filter(InterviewPlan.id == s.plan_id).first()
        recent_sessions.append({
            "session_id": s.id,
            "plan_id": s.plan_id,
            "role_title": plan.role_title if plan else "Mock Session",
            "started_at": s.started_at.strftime("%Y-%m-%d %H:%M"),
            "completed": s.completed_at is not None,
            "score": sess_score,
            "answers_count": len(s.answers)
        })

    return {
        "latest_ats_score": latest_ats_score,
        "latest_match_score": latest_match_score,
        "avg_interview_score": avg_interview_score,
        "questions_attempted": questions_attempted,
        "weak_topics": weak_topics,
        "revision_topics": revision_topics,
        "score_history": score_history,
        "topic_performance": topic_performance,
        "recent_sessions": recent_sessions
    }
