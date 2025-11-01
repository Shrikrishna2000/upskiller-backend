# main.py

import json
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from sqlalchemy.orm import Session
from datetime import timedelta

from models import UserProgress
from schemas import ProgressSubmit, UserProgressSchema
from sqlalchemy.sql import func
from datetime import datetime

from database import get_db 
from models import Course, Video, Quiz, User # Added User
from schemas import UserCreate, User as UserSchema, Token
from auth_utils import get_password_hash, verify_password, create_access_token, get_current_user
from fastapi.security import OAuth2PasswordRequestForm


# --- Configuration ---
ACCESS_TOKEN_EXPIRE_MINUTES = 30 # Defined in auth_utils

app = FastAPI()

# Setup CORS (Ensure your React client's URL is allowed)
origins = [
    "http://localhost",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Helper Function (CRUD) ---

def create_user(db: Session, user: UserCreate):
    """Helper function to create a new user in the database."""
    # This ensures passwords are NEVER stored in plain text
    hashed_password = get_password_hash(user.password)
    db_user = User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# ------------------------------------------------------------------
# --- AUTHENTICATION ENDPOINTS (Task 2.4) ---
# ------------------------------------------------------------------

@app.post("/api/auth/register", response_model=UserSchema)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """Handles user registration and checks for existing users."""
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    return create_user(db=db, user=user)

@app.post("/api/auth/login", response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    """Authenticates the user and issues a JWT token."""
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Successful login: create the token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

# ------------------------------------------------------------------
# --- PROTECTED COURSE ENDPOINT (Task 2.3 & Final Check) ---
# ------------------------------------------------------------------

@app.get("/api/courses/{course_id}")
async def get_course_db(
    course_id: int, 
    # CRITICAL: This line uses the dependency to ensure a valid token is present.
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Fetches the course data from the database, only for authenticated users."""
    
    # 1. Fetch the Course object
    course = db.query(Course).filter(Course.id == course_id).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # 2. Fetch all Videos and their Quizzes for the course
    videos_db = db.query(Video).filter(Video.course_id == course_id).order_by(Video.order_index).all()
    
    videos_list = []
    for video_db in videos_db:
        quiz_db = db.query(Quiz).filter(Quiz.video_id == video_db.id).first()
        
        videos_list.append({
            "id": video_db.id,
            "order_index": video_db.order_index,
            "title": video_db.title,
            "youtube_id": video_db.youtube_id,
            "duration_seconds": video_db.duration_seconds,
            # Load the JSON string back into a Python list/dict
            "quiz": json.loads(quiz_db.question_data) if quiz_db else [] 
        })

    # 3. Assemble the final response structure
    return {
        "id": course.id,
        "title": course.title,
        "description": course.description,
        "playlist_id": course.playlist_id,
        "thumbnail_url": course.thumbnail_url,
        "videos": videos_list
    }

# --- Example Protected Endpoint for user details (Useful for initial testing) ---
@app.get("/api/users/me", response_model=UserSchema)
def read_users_me(current_user: User = Depends(get_current_user)):
    """Returns the details of the currently authenticated user."""
    return current_user


# ------------------------------------------------------------------
# --- PROGRESS ENDPOINTS (Task 3.2) ---
# ------------------------------------------------------------------

@app.post("/api/progress/{video_id}", response_model=UserProgressSchema)
async def submit_progress(
    video_id: int, 
    progress_data: ProgressSubmit, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Submits the completion status and score for a video's quiz."""
    
    # 1. Check if progress record already exists
    progress = db.query(UserProgress).filter(
        UserProgress.user_id == current_user.id,
        UserProgress.video_id == video_id
    ).first()

    if progress:
        # Update existing record
        progress.quiz_score = progress_data.quiz_score
        progress.is_completed = progress_data.is_completed
        # Only update completed_at if it's being marked complete for the first time
        if progress_data.is_completed and not progress.completed_at:
            progress.completed_at = func.now()
    else:
        # Create new record
        progress = UserProgress(
            user_id=current_user.id,
            video_id=video_id,
            quiz_score=progress_data.quiz_score,
            is_completed=progress_data.is_completed,
            completed_at=func.now() if progress_data.is_completed else None
        )
        db.add(progress)
        
    db.commit()
    db.refresh(progress)
    return progress

@app.get("/api/progress/me", response_model=list[UserProgressSchema])
async def get_user_progress(
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Returns all progress records for the logged-in user."""
    progress_list = db.query(UserProgress).filter(
        UserProgress.user_id == current_user.id
    ).all()
    
    return progress_list