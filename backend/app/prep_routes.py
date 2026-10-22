from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import User, Resume, JobDescription, InterviewPlan, PrepQuestion
from app.schemas import InterviewPlanCreate, InterviewPlanResponse
from app.auth import get_db, get_current_user
from app.match_scorer import calculate_blend_match
from app.prep_generator import generate_prep_questions

router = APIRouter(tags=["Interview Prep"])

@router.post("/interview-plans", response_model=InterviewPlanResponse, status_code=status.HTTP_201_CREATED)
def create_interview_plan(
    plan_in: InterviewPlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Fetch Resume and verify ownership
    resume = db.query(Resume).filter(Resume.id == plan_in.resume_id, Resume.user_id == current_user.id).first()
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found or does not belong to the user."
        )
        
    # 2. Fetch Job Description and verify ownership
    jd = db.query(JobDescription).filter(JobDescription.id == plan_in.jd_id, JobDescription.user_id == current_user.id).first()
    if not jd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job description not found or does not belong to the user."
        )

    # 3. Analyze skills overlap using match scorer
    match_dict = calculate_blend_match(resume.raw_text, jd.raw_jd_text)
    
    resume_skills = [s["name"] for s in match_dict["matched_skills"]] + [s["name"] for s in match_dict["missing_skills"]]
    matched_skills = [s["name"] for s in match_dict["matched_skills"]]
    missing_skills = [s["name"] for s in match_dict["missing_skills"]]

    # 4. Generate interview questions
    generated_questions = generate_prep_questions(
        role_title=jd.role_title,
        experience_level=current_user.experience_level,
        resume_skills=resume_skills,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        jd_text=jd.raw_jd_text
    )

    # 5. Create and save InterviewPlan
    db_plan = InterviewPlan(
        user_id=current_user.id,
        resume_id=resume.id,
        jd_id=jd.id,
        role_title=jd.role_title
    )
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)

    # 6. Create and save PrepQuestions
    for q in generated_questions:
        db_question = PrepQuestion(
            plan_id=db_plan.id,
            question_text=q["question_text"],
            type=q["type"],
            difficulty=q["difficulty"],
            topic_tag=q["topic_tag"]
        )
        db.add(db_question)
    
    db.commit()
    db.refresh(db_plan)
    
    return db_plan

@router.get("/interview-plans/latest", response_model=InterviewPlanResponse)
def get_latest_interview_plan(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    plan = db.query(InterviewPlan).filter(InterviewPlan.user_id == current_user.id).order_by(InterviewPlan.created_at.desc()).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No interview preparation plan found for the current user."
        )
    return plan
