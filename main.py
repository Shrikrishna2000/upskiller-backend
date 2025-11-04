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
from ai_pipeline import generate_all_content
from services import save_generated_content
from schemas import ProgressSubmit, UserProgressSchema
from pydantic import BaseModel, HttpUrl
from services import get_all_courses 
from schemas import CourseListSchema, CourseSchema 
from typing import List

# --- Request Schema for Content Generation ---
class ContentRequest(BaseModel):
    """Schema for the request body when generating new content."""
    youtube_url: HttpUrl # Use HttpUrl for validation

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

@app.get("/api/courses/{course_id}", response_model=CourseSchema)
async def get_course_by_id(
    course_id: int, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    course = db.query(Course).filter(Course.id == course_id).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # 🛑 CRITICAL FIX: Deserialize JSON strings for AI content
    # This loop ensures the client receives Python objects, not JSON strings.
    for video in course.videos:
        # Deserialize all quizzes for this video
        for quiz in video.quizzes:
            if quiz.question_data:
                quiz.question_data = json.loads(quiz.question_data)

        # Deserialize all flashcards for this video
        for flashcard in video.flashcards:
            if flashcard.flashcard_data:
                flashcard.flashcard_data = json.loads(flashcard.flashcard_data)

    return course

# --- Example Protected Endpoint for user details (Useful for initial testing) ---
@app.get("/api/users/me", response_model=UserSchema)
def read_users_me(current_user: User = Depends(get_current_user)):
    """Returns the details of the currently authenticated user."""
    return current_user


# ------------------------------------------------------------------
# --- PROGRESS ENDPOINTS (Task 3.2) ---
# ------------------------------------------------------------------

# 🛑 FIX: Removed /{video_id} from the path and the video_id argument from the function.
@app.post("/api/progress", response_model=UserProgressSchema)
async def submit_progress(
    progress_data: ProgressSubmit, # All required data (including video_id) is in the body
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Submits the completion status and score for a video's quiz."""
    
    # Use the video_id from the Pydantic model (progress_data)
    video_id_from_body = progress_data.video_id 
    
    # 1. Check if progress record already exists
    progress = db.query(UserProgress).filter(
        UserProgress.user_id == current_user.id,
        UserProgress.video_id == video_id_from_body # Use the ID from the body
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
            video_id=video_id_from_body,
            quiz_score=progress_data.quiz_score,
            is_completed=progress_data.is_completed,
            completed_at=func.now() if progress_data.is_completed else None
        )
        db.add(progress)
        
    db.commit()
    db.refresh(progress)
    return progress

# 🛑 FIX: Renamed the GET route to /api/progress and updated response_model to List
@app.get("/api/progress", response_model=List[UserProgressSchema])
async def get_user_all_progress(
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Returns all progress records for the logged-in user."""
    progress_list = db.query(UserProgress).filter(
        UserProgress.user_id == current_user.id
    ).all()
    
    return progress_list
# ------------------------------------------------------------------
# --- AI GENERATION ENDPOINT (Milestone 4B Integration) ---
# ------------------------------------------------------------------

@app.post("/api/content/generate")
async def generate_content(
    request: ContentRequest,
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db) # CRITICAL: Inject DB session here
):
    """
    Triggers the AI pipeline, generates content, and persists it to the database.
    """
    
    # 1. Extract Video ID (Existing logic)
    video_id = str(request.youtube_url).split("v=")[-1].split("&")[0]

    if not video_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL provided.")
        
    try:
        # 1. Run the COMBINED LangChain/Gemini pipeline
        # 🛑 NEW: Get both quiz and flashcard data simultaneously
        quiz_data, flashcard_data = generate_all_content(video_id)
        
        # 2. Call the service layer to handle persistence
        # 🛑 NEW: Pass both data dictionaries
        new_course = save_generated_content(db, quiz_data, flashcard_data, video_id)
                
        # Return success and the ID of the new course
        return {
            "message": "AI content successfully generated and saved.",
            "course_id": new_course.id,
            "video_id": video_id,
            "title": new_course.title
        }

    except Exception as e:
        # Note: Rollback ensures database integrity if an error occurs
        db.rollback() 
        print(f"AI Generation Error: {e}")
        raise HTTPException(status_code=500, detail=f"AI pipeline failed during generation or saving: {e}")
    
# ------------------------------------------------------------------
# --- COURSE DISCOVERY ENDPOINT (Milestone 4D) ---
# ------------------------------------------------------------------

@app.get("/api/courses", response_model=List[CourseListSchema])
async def list_all_courses(
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """
    Returns a list of all courses the user can view.
    """
    courses = get_all_courses(db)
    # Note: In a real app, you'd filter this by user enrollment or access rights.
    return courses