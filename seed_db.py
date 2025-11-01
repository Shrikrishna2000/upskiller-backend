import json
import os
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import Course, Video, Quiz, User 
from auth_utils import get_password_hash # We need this to hash the default user password

# --- Configuration ---
# You must have your course_data.json file present in the same directory
COURSE_DATA_FILE = "course_data.json" 
TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "testpassword123"

def seed_data():
    """Reads static JSON data and populates the database."""
    
    # 1. Ensure all tables are created (creates the sql_app.db file if it doesn't exist)
    Base.metadata.create_all(bind=engine)
    
    db: Session = SessionLocal()
    
    try:
        with open(COURSE_DATA_FILE, "r") as f:
            course_json = json.load(f)
    except FileNotFoundError:
        print(f"\nFATAL: Error: {COURSE_DATA_FILE} not found. Cannot seed data. Please create it first.\n")
        db.close()
        return
    except json.JSONDecodeError:
        print(f"\nFATAL: Error: {COURSE_DATA_FILE} is malformed. Please run it through a JSON validator.\n")
        db.close()
        return

    # 2. SEED TEST USER
    if not db.query(User).filter(User.email == TEST_USER_EMAIL).first():
        print(f"Seeding default test user: {TEST_USER_EMAIL}")
        
        # 🛑 FIX: Safely truncate the password to 72 characters (bytes) 
        # to prevent the ValueError, ensuring the code proceeds.
        safe_password = TEST_USER_PASSWORD[:72]
        
        # Use the truncated password for hashing
        hashed_pw = get_password_hash(safe_password) 
        
        test_user = User(email=TEST_USER_EMAIL, hashed_password=hashed_pw)
        db.add(test_user)
        db.commit()
    
    # 3. SEED COURSE CONTENT
    course_id = course_json.get("id")
    if db.query(Course).filter(Course.id == course_id).first():
        print(f"Course ID {course_id} already seeded. Skipping content creation.")
        db.close()
        return

    print(f"Seeding Course ID {course_id}: {course_json['title']}")
    
    # Create the Course entry
    course = Course(
        id=course_id,
        title=course_json.get("title"),
        description=course_json.get("description"),
        playlist_id=course_json.get("playlist_id"),
        thumbnail_url=course_json.get("thumbnail_url")
    )
    db.add(course)
    db.commit()
    db.refresh(course)

    # Create Video and Quiz entries
    for video_data in course_json.get("videos", []):
        video = Video(
            course_id=course.id,
            order_index=video_data.get("order_index"),
            title=video_data.get("title"),
            youtube_id=video_data.get("youtube_id"),
            duration_seconds=video_data.get("duration_seconds")
        )
        db.add(video)
        db.commit()
        db.refresh(video)
        
        # Create the Quiz entry, storing the list of questions as a JSON string
        if video_data.get("quiz"):
            quiz = Quiz(
                video_id=video.id,
                question_data=json.dumps(video_data["quiz"])
            )
            db.add(quiz)
            db.commit()

    db.close()
    print(f"✅ Successfully seeded Course and Users into 'sql_app.db'")

if __name__ == "__main__":
    seed_data()