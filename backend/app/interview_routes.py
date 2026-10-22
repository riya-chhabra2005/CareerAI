import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from app.database import SessionLocal
from app.models import User, InterviewPlan, PrepQuestion, InterviewSession, Answer
from app.schemas import (
    InterviewSessionCreate,
    InterviewSessionResponse,
    AnswerResponse,
    NextQuestionResponse,
    PrepQuestionResponse
)
from app.auth import get_db, get_current_user
from app.transcriber import transcribe_audio

router = APIRouter(tags=["AI Mock Interview"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/interviews/sessions", response_model=InterviewSessionResponse, status_code=status.HTTP_201_CREATED)
def start_interview_session(
    session_in: InterviewSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify the prep plan belongs to the current user
    plan = db.query(InterviewPlan).filter(InterviewPlan.id == session_in.plan_id, InterviewPlan.user_id == current_user.id).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview preparation plan not found or does not belong to the user."
        )
        
    db_session = InterviewSession(
        user_id=current_user.id,
        plan_id=plan.id,
        completed_at=None
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

@router.get("/interviews/sessions/{session_id}/next", response_model=NextQuestionResponse)
def get_next_question(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(InterviewSession).filter(InterviewSession.id == session_id, InterviewSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview session not found or does not belong to the user."
        )
        
    # Get all questions in this plan
    plan_questions = db.query(PrepQuestion).filter(PrepQuestion.plan_id == session.plan_id).order_by(PrepQuestion.id.asc()).all()
    
    # Get all answered question IDs in this session
    answered_qids = {ans.question_id for ans in session.answers}
    
    # Find the first unanswered question
    next_q = None
    for q in plan_questions:
        if q.id not in answered_qids:
            next_q = q
            break
            
    if not next_q:
        # No unanswered questions remain - session is complete
        if not session.completed_at:
            session.completed_at = func.now()
            db.commit()
            db.refresh(session)
        return {"completed": True, "question": None}
        
    return {"completed": False, "question": next_q}

@router.post("/interviews/{session_id}/answers", response_model=AnswerResponse)
async def submit_answer(
    session_id: int,
    question_id: int = Form(...),
    input_type: str = Form(...),  # text or voice
    answer_text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(InterviewSession).filter(InterviewSession.id == session_id, InterviewSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview session not found or does not belong to the user."
        )
        
    question = db.query(PrepQuestion).filter(PrepQuestion.id == question_id, PrepQuestion.plan_id == session.plan_id).first()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found in the plan associated with this session."
        )

    # Prevent double submissions for the same question in the same session
    existing_answer = db.query(Answer).filter(Answer.session_id == session_id, Answer.question_id == question_id).first()
    if existing_answer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An answer has already been submitted for this question in this session."
        )

    final_text = ""
    saved_audio_path = None

    if input_type == "text":
        if not answer_text or not answer_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="answer_text is required for text replies."
            )
        final_text = answer_text
    elif input_type == "voice":
        if not file:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Audio file upload is required for voice replies."
            )
        
        # Save audio file to uploads directory
        # Sanitize filename extension (standardize to .webm or .wav)
        file_ext = os.path.splitext(file.filename)[1] or ".webm"
        file_name = f"session_{session_id}_q_{question_id}{file_ext}"
        saved_audio_path = os.path.join(UPLOAD_DIR, file_name)
        
        with open(saved_audio_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Transcribe the saved audio file
        final_text = transcribe_audio(saved_audio_path, question.topic_tag)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input_type. Must be 'text' or 'voice'."
        )

    # Save the answer
    db_answer = Answer(
        session_id=session.id,
        question_id=question.id,
        answer_text=final_text,
        input_type=input_type,
        audio_path=saved_audio_path
    )
    db.add(db_answer)
    db.commit()
    db.refresh(db_answer)

    # Check if there are any remaining unanswered questions
    plan_questions = db.query(PrepQuestion).filter(PrepQuestion.plan_id == session.plan_id).all()
    answered_count = db.query(Answer).filter(Answer.session_id == session_id).count()
    
    if answered_count >= len(plan_questions):
        session.completed_at = func.now()
        db.commit()

    return db_answer
