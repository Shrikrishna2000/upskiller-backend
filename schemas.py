from pydantic import BaseModel, EmailStr

# --- User Schemas ---

class UserBase(BaseModel):
    """Base schema for user data (used for both input and output)"""
    email: EmailStr

class UserCreate(UserBase):
    """Schema for user registration request (must include password)"""
    password: str

class User(UserBase):
    """Schema for user response (ID is added, password is omitted)"""
    id: int
    is_active: bool

    class Config:
        orm_mode = True # Allows mapping from SQLAlchemy models

# --- Authentication Schemas ---

class Token(BaseModel):
    """Schema for the JWT token response"""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """Schema for the data contained inside the JWT payload"""
    email: str | None = None

class ProgressSubmit(BaseModel):
    """Schema for the client sending quiz results."""
    video_id: int
    quiz_score: int # The percentage score (0-100)
    is_completed: bool # True if the score meets the Mastery Gate threshold (>= 70)

class UserProgressSchema(BaseModel):
    """Schema for fetching the user's progress records."""
    video_id: int
    is_completed: bool
    quiz_score: int
    # Note: We omit timestamps for simplicity in the MVP response

    class Config:
        orm_mode = True