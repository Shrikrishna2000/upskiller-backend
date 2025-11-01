from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from database import Base
from sqlalchemy.sql import func # for default timestamp values

# --- Core Entities (Milestone 2) ---

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

    # Relationship to user progress (for Milestone 3)
    progress = relationship("UserProgress", back_populates="user")
    
    # Relationship to other future entities (e.g., goals)
    # goals = relationship("LearningGoal", back_populates="user") 


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    playlist_id = Column(String)
    thumbnail_url = Column(String)

    videos = relationship("Video", back_populates="course")

class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"))
    order_index = Column(Integer)
    title = Column(String)
    youtube_id = Column(String)
    duration_seconds = Column(Integer)
    
    course = relationship("Course", back_populates="videos")
    quizzes = relationship("Quiz", back_populates="video", uselist=False) # One quiz per video

class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"))
    
    # Stores the list of questions as a JSON string
    question_data = Column(Text) 

    video = relationship("Video", back_populates="quizzes")


# --- Progress Entity (Milestone 3) ---

class UserProgress(Base):
    __tablename__ = "user_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    video_id = Column(Integer, ForeignKey("videos.id"))
    
    # Tracking the 'Mastery Gate' completion
    is_completed = Column(Boolean, default=False)
    quiz_score = Column(Integer, nullable=True) # Store the percentage score (0-100)
    
    # Timestamps for tracking
    started_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="progress")
    video = relationship("Video") # No back_populates needed on Video for progress