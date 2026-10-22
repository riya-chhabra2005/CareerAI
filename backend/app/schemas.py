import json
from pydantic import BaseModel, EmailStr, Field, model_validator
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    name: str
    email: EmailStr
    target_job_role: str
    experience_level: str

class UserRegister(UserBase):
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters")

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    target_job_role: Optional[str] = None
    experience_level: Optional[str] = None

class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

# Resume Schemas
class ResumeResponse(BaseModel):
    id: int
    filename: str
    raw_text: str
    created_at: datetime

    class Config:
        from_attributes = True

# Job Description Schemas
class JobDescriptionCreate(BaseModel):
    role_title: str
    raw_jd_text: str

class JobDescriptionResponse(BaseModel):
    id: int
    role_title: str
    raw_jd_text: str
    created_at: datetime

    class Config:
        from_attributes = True

# ATS Scoring Schemas
class ATSDetailScore(BaseModel):
    score: int
    max: int
    feedback: list[str]

class ATSScoreDetails(BaseModel):
    headings: ATSDetailScore
    structure: ATSDetailScore
    contact: ATSDetailScore
    dates: ATSDetailScore
    layout: ATSDetailScore
    keywords: ATSDetailScore

class ATSResponse(BaseModel):
    score: int
    details: ATSScoreDetails
    feedback_list: list[str]


# JD Match and Skill Gap Analysis Schemas
class MatchRequest(BaseModel):
    jd_id: int


class SkillInfo(BaseModel):
    name: str
    frequency: int


class MatchResponse(BaseModel):
    match_score: int
    tfidf_score: int
    semantic_score: int
    matched_skills: list[SkillInfo]
    missing_skills: list[SkillInfo]


# Resume Suggestions Schemas
class SuggestionItem(BaseModel):
    category: str
    explanation: str
    example_rewrite: Optional[str] = None
    requires_verification: bool = False
    unverified_skills: list[str] = []


class SuggestionsResponse(BaseModel):
    suggestions: list[SuggestionItem]


# Interview Prep Plan Schemas
class InterviewPlanCreate(BaseModel):
    resume_id: int
    jd_id: int


class PrepQuestionResponse(BaseModel):
    id: int
    plan_id: int
    question_text: str
    type: str
    difficulty: str
    topic_tag: str
    created_at: datetime

    class Config:
        from_attributes = True


class InterviewPlanResponse(BaseModel):
    id: int
    user_id: int
    resume_id: Optional[int] = None
    jd_id: Optional[int] = None
    role_title: str
    created_at: datetime
    questions: list[PrepQuestionResponse]

    class Config:
        from_attributes = True


# Interview Session & Mock Evaluation Schemas
class InterviewSessionCreate(BaseModel):
    plan_id: int


class EvaluationResponse(BaseModel):
    id: int
    answer_id: int
    overall_score: int
    correctness_score: int
    relevance_score: int
    completeness_score: int
    depth_score: int
    communication_score: int
    strengths: list[str]
    gaps: list[str]
    model_answer: str
    revision_topics: list[str]
    created_at: datetime

    @model_validator(mode="before")
    @classmethod
    def parse_json_fields(cls, data):
        if not hasattr(data, "__getitem__"):
            # SQLAlchemy object: use getattr/setattr
            for field in ["strengths", "gaps", "revision_topics"]:
                val = getattr(data, field, None)
                if isinstance(val, str):
                    try:
                        setattr(data, field, json.loads(val))
                    except Exception:
                        setattr(data, field, [])
        else:
            # Dictionary: modify in place
            for field in ["strengths", "gaps", "revision_topics"]:
                val = data.get(field)
                if isinstance(val, str):
                    try:
                        data[field] = json.loads(val)
                    except Exception:
                        data[field] = []
        return data

    class Config:
        from_attributes = True


class AnswerResponse(BaseModel):
    id: int
    session_id: int
    question_id: int
    answer_text: str
    input_type: str
    audio_path: Optional[str] = None
    submitted_at: datetime
    evaluation: Optional[EvaluationResponse] = None

    class Config:
        from_attributes = True


class InterviewSessionResponse(BaseModel):
    id: int
    user_id: int
    plan_id: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    answers: list[AnswerResponse]

    class Config:
        from_attributes = True


class NextQuestionResponse(BaseModel):
    completed: bool
    question: Optional[PrepQuestionResponse] = None


class DashboardResponse(BaseModel):
    latest_ats_score: Optional[int] = None
    latest_match_score: Optional[int] = None
    avg_interview_score: Optional[int] = None
    questions_attempted: int
    weak_topics: list[str]
    revision_topics: list[str]
    score_history: list[dict]
    topic_performance: list[dict]
    recent_sessions: list[dict]


# Study Plan Schemas
class StudyPlanCreate(BaseModel):
    duration: int  # 7, 14, 30


class StudyPlanDayUpdate(BaseModel):
    completed_items: list[str]


class StudyPlanDayResponse(BaseModel):
    id: int
    plan_id: int
    day_number: int
    theme: str
    action_items: list[str]
    completed_items: list[str]

    @model_validator(mode="before")
    @classmethod
    def parse_json_fields(cls, data):
        if not hasattr(data, "__getitem__"):
            # SQLAlchemy object: use getattr/setattr
            for field in ["action_items", "completed_items"]:
                val = getattr(data, field, None)
                if isinstance(val, str):
                    try:
                        setattr(data, field, json.loads(val))
                    except Exception:
                        setattr(data, field, [])
        else:
            # Dictionary: modify in place
            for field in ["action_items", "completed_items"]:
                val = data.get(field)
                if isinstance(val, str):
                    try:
                        data[field] = json.loads(val)
                    except Exception:
                        data[field] = []
        return data

    class Config:
        from_attributes = True


class StudyPlanResponse(BaseModel):
    id: int
    user_id: int
    duration: int
    created_at: datetime
    days: list[StudyPlanDayResponse]

    class Config:
        from_attributes = True







