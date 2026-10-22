import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from app.models import User, Resume, JobDescription, InterviewSession, Answer, Evaluation, StudyPlan, StudyPlanDay
from app.schemas import StudyPlanCreate, StudyPlanResponse, StudyPlanDayResponse, StudyPlanDayUpdate
from app.auth import get_db, get_current_user
from app.ats_scorer import calculate_ats_score
from app.match_scorer import calculate_blend_match
from app.study_generator import generate_study_plan

router = APIRouter(tags=["Personalized Study Plan"])

@router.post("/study-plans", response_model=StudyPlanResponse, status_code=status.HTTP_201_CREATED)
def create_study_plan(
    plan_in: StudyPlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if plan_in.duration not in [7, 14, 30]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duration must be exactly 7, 14, or 30 days."
        )

    # 1. Fetch scores & weak topics (Similar to Dashboard aggregation)
    latest_resume = db.query(Resume).filter(Resume.user_id == current_user.id).order_by(Resume.created_at.desc()).first()
    latest_jd = db.query(JobDescription).filter(JobDescription.user_id == current_user.id).order_by(JobDescription.created_at.desc()).first()
    
    ats_score = 0
    if latest_resume:
        try:
            ats_score = calculate_ats_score(latest_resume.raw_text)["score"]
        except Exception:
            pass
            
    match_score = 0
    if latest_resume and latest_jd:
        try:
            match_score = calculate_blend_match(latest_resume.raw_text, latest_jd.raw_jd_text)["match_score"]
        except Exception:
            pass

    # Gather evaluations to identify weak topics and strengths
    evals = db.query(Evaluation).join(Answer).join(InterviewSession).filter(InterviewSession.user_id == current_user.id).all()
    
    weak_topics_dict = {}
    matched_skills = []
    for e in evals:
        if e.overall_score < 70 and e.answer.question:
            topic = e.answer.question.topic_tag
            weak_topics_dict[topic] = weak_topics_dict.get(topic, 0) + 1
            
    weak_topics = [topic for topic, count in sorted(weak_topics_dict.items(), key=lambda x: x[1], reverse=True)]

    # Fetch matched skills from latest JD match scorer runs
    if latest_resume and latest_jd:
        try:
            m_res = calculate_blend_match(latest_resume.raw_text, latest_jd.raw_jd_text)
            matched_skills = [s["name"] for s in m_res["matched_skills"]]
        except Exception:
            pass

    # 2. Call generator service
    generated_days = generate_study_plan(
        role_title=current_user.target_job_role,
        experience_level=current_user.experience_level,
        duration=plan_in.duration,
        weak_topics=weak_topics,
        matched_skills=matched_skills,
        ats_score=ats_score,
        match_score=match_score
    )

    # 3. Save StudyPlan
    db_plan = StudyPlan(
        user_id=current_user.id,
        duration=plan_in.duration
    )
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)

    # 4. Save StudyPlanDays
    for day in generated_days:
        db_day = StudyPlanDay(
            plan_id=db_plan.id,
            day_number=day["day_number"],
            theme=day["theme"],
            action_items=json.dumps(day["action_items"]),
            completed_items=json.dumps([])
        )
        db.add(db_day)
        
    db.commit()
    db.refresh(db_plan)
    
    return db_plan

@router.get("/study-plans/latest", response_model=StudyPlanResponse)
def get_latest_study_plan(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    plan = db.query(StudyPlan).filter(StudyPlan.user_id == current_user.id).order_by(StudyPlan.created_at.desc()).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No study plan found for the current user."
        )
    return plan

@router.put("/study-plan-days/{day_id}", response_model=StudyPlanDayResponse)
def update_study_plan_day_progress(
    day_id: int,
    day_in: StudyPlanDayUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    day = db.query(StudyPlanDay).join(StudyPlan).filter(
        StudyPlanDay.id == day_id,
        StudyPlan.user_id == current_user.id
    ).first()
    
    if not day:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study plan day not found or does not belong to the user's plan."
        )

    # Update completed items checklist
    day.completed_items = json.dumps(day_in.completed_items)
    db.commit()
    db.refresh(day)
    
    return day
