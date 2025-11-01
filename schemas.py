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