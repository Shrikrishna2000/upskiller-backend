# services.py

import json
from sqlalchemy.orm import Session
from models import Course, Video, Quiz, UserProgress, Flashcard
    
# ------------------------------------------------------------------
# --- PERSISTENCE HELPER FUNCTION ---
# ------------------------------------------------------------------

def save_generated_content(db: Session, quiz_data: dict, flashcard_data: dict, video_id: str) -> Course:
    """
    Saves ALL generated content (Quiz and Flashcards) into the DB.
    """
    try:
        # 1. Create/Update the Course and Video Entries (Logic remains the same)
        course_title = f"AI Generated: {quiz_data['video_title']}"
        
        existing_course = db.query(Course).filter(Course.title == course_title).first()
        if existing_course:
            # Delete old content (including flashcards) for update
            for video in existing_course.videos:
                db.query(Quiz).filter(Quiz.video_id == video.id).delete()
                db.query(Flashcard).filter(Flashcard.video_id == video.id).delete() # NEW: Delete old flashcards
            db.query(Video).filter(Video.course_id == existing_course.id).delete()
            course = existing_course
        else:
            # Create a new course entry
            course = Course(
                title=course_title,
                description=f"AI-generated content for YouTube video ID: {video_id}",
                playlist_id=None,
                thumbnail_url=None
            )
            db.add(course)
            
        db.flush() 
        db.refresh(course) 

        # 2. Create the Video Entry (Uses quiz_data title)
        video = Video(
            course_id=course.id,
            order_index=1,
            title=quiz_data['video_title'], # Use quiz data for video title
            youtube_id=video_id,
            duration_seconds=0
        )
        db.add(video)
        db.flush()
        db.refresh(video) 

        # 3. Create the Quiz Entry (Logic remains the same)
        quiz = Quiz(
            video_id=video.id,
            question_data=json.dumps(quiz_data['quiz'])
        )
        db.add(quiz)
        
        # 🛑 NEW STEP: Create the Flashcard Entry
        flashcard = Flashcard(
            video_id=video.id,
            flashcard_data=json.dumps(flashcard_data['flashcards'])
        )
        db.add(flashcard)
        
        db.commit() 
        db.refresh(course)
        return course

    except Exception as e:
        db.rollback() 
        raise e