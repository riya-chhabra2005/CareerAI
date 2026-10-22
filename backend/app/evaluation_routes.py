import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import User, Answer, Evaluation, PrepQuestion, InterviewSession
from app.schemas import EvaluationResponse
from app.auth import get_db, get_current_user
from app.evaluator import evaluate_answer

router = APIRouter(tags=["Answer Evaluation"])

@router.post("/answers/{answer_id}/evaluate", response_model=EvaluationResponse, status_code=status.HTTP_201_CREATED)
def evaluate_user_answer(
    answer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Fetch answer and verify ownership via the session link
    answer = db.query(Answer).join(InterviewSession).filter(
        Answer.id == answer_id, 
        InterviewSession.user_id == current_user.id
    ).first()
    
    if not answer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Answer not found or does not belong to the user's session."
        )

    # 2. Prevent duplicate evaluations - return existing if already evaluated
    existing_eval = db.query(Evaluation).filter(Evaluation.answer_id == answer_id).first()
    if existing_eval:
        return existing_eval

    # 3. Retrieve question details
    question = db.query(PrepQuestion).filter(PrepQuestion.id == answer.question_id).first()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Linked preparation question could not be found."
        )

    # 4. Trigger evaluation scoring
    eval_dict = evaluate_answer(
        question_text=question.question_text,
        question_type=question.type,
        topic_tag=question.topic_tag,
        difficulty=question.difficulty,
        answer_text=answer.answer_text
    )

    # 5. Serialize lists to JSON strings for database columns
    db_eval = Evaluation(
        answer_id=answer.id,
        overall_score=eval_dict["overall_score"],
        correctness_score=eval_dict["correctness_score"],
        relevance_score=eval_dict["relevance_score"],
        completeness_score=eval_dict["completeness_score"],
        depth_score=eval_dict["depth_score"],
        communication_score=eval_dict["communication_score"],
        strengths=json.dumps(eval_dict["strengths"]),
        gaps=json.dumps(eval_dict["gaps"]),
        model_answer=eval_dict["model_answer"],
        revision_topics=json.dumps(eval_dict["revision_topics"])
    )

    db.add(db_eval)
    db.commit()
    db.refresh(db_eval)

    return db_eval
