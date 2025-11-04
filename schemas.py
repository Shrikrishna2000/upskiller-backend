# schemas.py

from pydantic import BaseModel, EmailStr
from typing import List, Optional

# --------------------------------------------------
# --- AI-Generated Content Schemas (NEW) ---
# --------------------------------------------------

class QuizQuestion(BaseModel):
    """Schema for a single multiple-choice question inside the JSON data."""
    question: str
    options: List[str]
    correct: int

class FlashcardItem(BaseModel):
    """Schema for a single flashcard inside the JSON data."""
    front: str
    back: str

# --------------------------------------------------
# --- ORM MAPPING Schemas (NEW) ---
# --------------------------------------------------

class QuizSchema(BaseModel):
    """Schema for the Quiz ORM model."""
    id: int
    video_id: int
    
    # CRITICAL: This is where we tell Pydantic that the JSON string from the DB 
    # (after deserialization in main.py) should be treated as a list of objects.
    question_data: List[QuizQuestion]

    class Config:
        from_attributes = True

class FlashcardSchema(BaseModel):
    """Schema for the Flashcard ORM model."""
    id: int
    video_id: int
    
    # CRITICAL: Same transformation as the quiz data.
    flashcard_data: List[FlashcardItem]

    class Config:
        from_attributes = True

class VideoSchema(BaseModel):
    """Schema for the Video ORM model, including nested content."""
    # Columns
    id: int
    course_id: int
    order_index: int
    title: str
    youtube_id: str
    duration_seconds: int

    # Relationships (Must be Lists based on models.py)
    quizzes: List[QuizSchema]
    flashcards: List[FlashcardSchema]

    class Config:
        from_attributes = True

class CourseSchema(BaseModel):
    """The complete schema for fetching a single course and all its content."""
    # Columns
    id: int
    title: str
    description: str
    playlist_id: Optional[str]
    thumbnail_url: Optional[str]

    # Relationship
    videos: List[VideoSchema]

    class Config:
        from_attributes = True

# --------------------------------------------------
# --- User Schemas (Existing) ---
# --------------------------------------------------

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True

# --- Authentication Schemas (Existing) ---

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class ProgressSubmit(BaseModel):
    video_id: int
    quiz_score: int
    is_completed: bool

class UserProgressSchema(BaseModel):
    video_id: int
    is_completed: bool
    quiz_score: int

    class Config:
        from_attributes = True

# --- Course List Schema (Existing) ---

class CourseListSchema(BaseModel):
    id: int
    title: str
    description: str

    class Config:
        from_attributes = True