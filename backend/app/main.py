from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import check_db_connection, engine, Base
from app.auth_routes import router as auth_router
from app.jd_routes import router as jd_router
from app.prep_routes import router as prep_router
from app.interview_routes import router as interview_router
from app.evaluation_routes import router as evaluation_router
from app.dashboard_routes import router as dashboard_router
from app.study_routes import router as study_router


# Import models so SQLAlchemy finds the metadata
import app.models
_ = app.models


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables if they do not exist
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="CareerAI Backend",
    description="Backend API services for CareerAI AI-powered career development platform",
    version="1.0.0",
    lifespan=lifespan
)


# Enable CORS for frontend on localhost (any port like 5173, 5174, etc.)
# and production Vercel deployments
import os as _os

_FRONTEND_URL = _os.getenv("FRONTEND_URL", "")

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:5175",
    "http://127.0.0.1:5175",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Add production frontend URL if configured
if _FRONTEND_URL:
    origins.append(_FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    # Allows localhost (dev) + all *.vercel.app preview/production URLs
    allow_origin_regex=r"^(https?://(localhost|127\.0\.0\.1)(:[0-9]+)?|https://.*\.vercel\.app)$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(jd_router)
app.include_router(prep_router)
app.include_router(interview_router)
app.include_router(evaluation_router)
app.include_router(dashboard_router)
app.include_router(study_router)



@app.get("/")
def read_root():
    return {
        "app": "CareerAI API",
        "version": "1.0.0",
        "docs_url": "/docs"
    }

@app.get("/api/health")
def health_check():
    """
    Health check endpoint to verify backend server status and database connectivity.
    """
    db_connected = check_db_connection()
    if db_connected:
        return {
            "status": "healthy",
            "database": "connected"
        }
    else:
        return {
            "status": "unhealthy",
            "database": "disconnected"
        }
