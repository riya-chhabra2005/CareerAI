import io
import re
import json
import os
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from typing import Optional
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import User, Resume, JobDescription
from app.schemas import (
    ResumeResponse,
    JobDescriptionCreate,
    JobDescriptionResponse,
    ATSResponse,
    MatchRequest,
    MatchResponse,
    SuggestionsResponse
)
from app.auth import get_db, get_current_user
from app.ats_scorer import calculate_ats_score
from app.match_scorer import calculate_blend_match
from app.suggestions_generator import generate_suggestions

router = APIRouter(tags=["ATS Scorer"])

@router.post("/resumes", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: Optional[UploadFile] = File(None),
    pasted_text: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    filename = "pasted_resume.txt"
    raw_text = ""
    
    if file:
        filename = file.filename
        content = await file.read()
        
        if filename.endswith(".pdf"):
            try:
                from pypdf import PdfReader
                pdf_file = io.BytesIO(content)
                reader = PdfReader(pdf_file)
                text_list = []
                for page in reader.pages:
                    text_list.append(page.extract_text() or "")
                raw_text = "\n".join(text_list)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to parse PDF resume: {str(e)}"
                )
        else:
            # Assume text/plain format
            try:
                raw_text = content.decode("utf-8")
            except Exception:
                try:
                    raw_text = content.decode("latin-1")
                except Exception:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Unsupported file encoding. Please upload a UTF-8 encoded text file or PDF."
                    )
    elif pasted_text:
        raw_text = pasted_text
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide either an uploaded file or pasted text content."
        )
        
    if not raw_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resume content cannot be empty."
        )

    db_resume = Resume(
        user_id=current_user.id,
        filename=filename,
        raw_text=raw_text
    )
    db.add(db_resume)
    db.commit()
    db.refresh(db_resume)
    return db_resume


@router.get("/resumes", response_model=list[ResumeResponse])
def list_resumes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Resume).filter(Resume.user_id == current_user.id).order_by(Resume.created_at.desc()).all()

def extract_text_from_file(filename: str, content: bytes) -> str:
    if filename.lower().endswith(".pdf"):
        from pypdf import PdfReader
        pdf_file = io.BytesIO(content)
        reader = PdfReader(pdf_file)
        text_list = []
        for page in reader.pages:
            text_list.append(page.extract_text() or "")
        return "\n".join(text_list)
    else:
        # Assume text/plain format
        try:
            return content.decode("utf-8")
        except Exception:
            try:
                return content.decode("latin-1")
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Unsupported file encoding. Please upload a UTF-8 encoded text file or PDF."
                )

def extract_role_title(jd_text: str) -> str:
    # Try using Gemini if API key is present
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            prompt = f"""
Analyze the following Job Description (JD) text and extract the exact job role / title (e.g. "Senior Python Developer", "React Frontend Engineer", "Product Manager").
Return ONLY a JSON object with a single key "role_title". Do not include any markdown formatting, just the raw JSON.
If you cannot find a clear job title, return "Software Engineer" as the default.

Job Description:
\"\"\"
{jd_text[:4000]}
\"\"\"
"""
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            data = json.loads(response.text)
            if "role_title" in data and data["role_title"]:
                return data["role_title"].strip()
        except Exception as e:
            print(f"Gemini role title extraction failed: {e}. Falling back to rule-based.")

    # Fallback to rule-based extraction
    lines = [line.strip() for line in jd_text.split("\n") if line.strip()]
    if not lines:
        return "Software Engineer"
        
    # Look for patterns like "Role: ...", "Title: ...", "Position: ..." in the first 15 lines
    title_indicators = [
        r"(?:job\s+)?title\s*:\s*(.*)",
        r"role\s*:\s*(.*)",
        r"position\s*:\s*(.*)",
        r"(?:job\s+)?role\s+title\s*:\s*(.*)"
    ]
    
    for line in lines[:15]:
        for pattern in title_indicators:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                title = re.sub(r"[*_#`\-]", "", title).strip()
                if title and len(title) < 100:
                    return title

    # Look for common job titles/keywords in the first few lines
    role_keywords = ["engineer", "developer", "designer", "manager", "lead", "architect", "analyst", "consultant", "specialist"]
    for line in lines[:5]:
        if any(kw in line.lower() for kw in role_keywords) and len(line) < 80:
            clean_line = re.sub(r"[*_#`\-]", "", line).strip()
            if clean_line:
                return clean_line

    # Default fallback: return the first line if it's reasonably short
    first_line = lines[0]
    if len(first_line) < 60:
        return re.sub(r"[*_#`\-]", "", first_line).strip()
        
    return "Software Engineer"


@router.post("/jd/parse")
async def parse_jd(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    filename = file.filename
    content = await file.read()
    
    try:
        raw_text = extract_text_from_file(filename, content)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse file: {str(e)}"
        )
        
    if not raw_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content is empty."
        )
        
    extracted_role = extract_role_title(raw_text)
    
    return {
        "role_title": extracted_role,
        "raw_jd_text": raw_text
    }


@router.post("/jd", response_model=JobDescriptionResponse, status_code=status.HTTP_201_CREATED)
def create_jd(
    jd_in: JobDescriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_jd = JobDescription(
        user_id=current_user.id,
        role_title=jd_in.role_title,
        raw_jd_text=jd_in.raw_jd_text
    )
    db.add(db_jd)
    db.commit()
    db.refresh(db_jd)
    return db_jd


@router.get("/jd", response_model=list[JobDescriptionResponse])
def list_jds(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(JobDescription).filter(JobDescription.user_id == current_user.id).order_by(JobDescription.created_at.desc()).all()

@router.get("/resumes/{id}/ats-score", response_model=ATSResponse)
def get_ats_score(
    id: int,
    jd_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    resume = db.query(Resume).filter(Resume.id == id, Resume.user_id == current_user.id).first()
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found or does not belong to the user."
        )
    
    jd_text = ""
    if jd_id:
        jd = db.query(JobDescription).filter(JobDescription.id == jd_id, JobDescription.user_id == current_user.id).first()
        if not jd:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job description not found or does not belong to the user."
            )
        jd_text = jd.raw_jd_text
        
    score_dict = calculate_ats_score(resume.raw_text, jd_text, current_user.target_job_role)
    return score_dict


@router.post("/resumes/{id}/match", response_model=MatchResponse)
def match_resume_jd(
    id: int,
    request: MatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    resume = db.query(Resume).filter(Resume.id == id, Resume.user_id == current_user.id).first()
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found or does not belong to the user."
        )
        
    jd = db.query(JobDescription).filter(JobDescription.id == request.jd_id, JobDescription.user_id == current_user.id).first()
    if not jd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job description not found or does not belong to the user."
        )
        
    match_dict = calculate_blend_match(resume.raw_text, jd.raw_jd_text)
    return match_dict


@router.post("/resumes/{id}/suggestions", response_model=SuggestionsResponse)
def get_resume_suggestions(
    id: int,
    request: MatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    resume = db.query(Resume).filter(Resume.id == id, Resume.user_id == current_user.id).first()
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found or does not belong to the user."
        )
        
    jd = db.query(JobDescription).filter(JobDescription.id == request.jd_id, JobDescription.user_id == current_user.id).first()
    if not jd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job description not found or does not belong to the user."
        )
        
    # Get missing skills using match scorer
    match_dict = calculate_blend_match(resume.raw_text, jd.raw_jd_text)
    missing_skills = [s["name"] for s in match_dict["missing_skills"]]
    
    # Generate suggestions
    suggestions_list = generate_suggestions(resume.raw_text, jd.raw_jd_text, missing_skills)
    return {"suggestions": suggestions_list}


