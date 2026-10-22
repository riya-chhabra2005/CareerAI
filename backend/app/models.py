from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    target_job_role = Column(String, nullable=False)
    experience_level = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String, nullable=False)
    raw_text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_title = Column(String, nullable=False)
    raw_jd_text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class InterviewPlan(Base):
    __tablename__ = "interview_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True)
    jd_id = Column(Integer, ForeignKey("job_descriptions.id", ondelete="SET NULL"), nullable=True)
    role_title = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    questions = relationship("PrepQuestion", back_populates="plan", cascade="all, delete-orphan")


class PrepQuestion(Base):
    __tablename__ = "prep_questions"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("interview_plans.id", ondelete="CASCADE"), nullable=False)
    question_text = Column(Text, nullable=False)
    type = Column(String, nullable=False)  # technical, coding, hr
    difficulty = Column(String, nullable=False)  # Easy, Medium, Hard
    topic_tag = Column(String, nullable=False)  # React, Python, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    plan = relationship("InterviewPlan", back_populates="questions")


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plan_id = Column(Integer, ForeignKey("interview_plans.id", ondelete="CASCADE"), nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    answers = relationship("Answer", back_populates="session", cascade="all, delete-orphan")


class Answer(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(Integer, ForeignKey("prep_questions.id", ondelete="CASCADE"), nullable=False)
    answer_text = Column(Text, nullable=False)
    input_type = Column(String, nullable=False)  # text or voice
    audio_path = Column(String, nullable=True)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session = relationship("InterviewSession", back_populates="answers")
    question = relationship("PrepQuestion")
    evaluation = relationship("Evaluation", back_populates="answer", uselist=False, cascade="all, delete-orphan")


class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, index=True)
    answer_id = Column(Integer, ForeignKey("answers.id", ondelete="CASCADE"), unique=True, nullable=False)
    overall_score = Column(Integer, nullable=False)
    correctness_score = Column(Integer, nullable=False)
    relevance_score = Column(Integer, nullable=False)
    completeness_score = Column(Integer, nullable=False)
    depth_score = Column(Integer, nullable=False)
    communication_score = Column(Integer, nullable=False)
    strengths = Column(Text, nullable=False)  # JSON list
    gaps = Column(Text, nullable=False)  # JSON list
    model_answer = Column(Text, nullable=False)
    revision_topics = Column(Text, nullable=False)  # JSON list
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    answer = relationship("Answer", back_populates="evaluation")


class StudyPlan(Base):
    __tablename__ = "study_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    duration = Column(Integer, nullable=False)  # 7, 14, 30
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    days = relationship("StudyPlanDay", back_populates="plan", order_by="StudyPlanDay.day_number", cascade="all, delete-orphan")


class StudyPlanDay(Base):
    __tablename__ = "study_plan_days"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("study_plans.id", ondelete="CASCADE"), nullable=False)
    day_number = Column(Integer, nullable=False)
    theme = Column(String, nullable=False)
    action_items = Column(Text, nullable=False)  # JSON list
    completed_items = Column(Text, nullable=False)  # JSON list

    # Relationships
    plan = relationship("StudyPlan", back_populates="days")





