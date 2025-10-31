# main.py (FastAPI application)

import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

app = FastAPI()

# 1. Setup CORS (Crucial for client-server interaction in development)
# This allows your React client (e.g., on http://localhost:3000) to talk to your FastAPI server.
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

# 2. Define the Endpoint
@app.get("/api/courses/{course_id}")
async def get_course(course_id: int):
    """Fetches the course data from the static JSON file with robust error handling."""
    
    # 1. Simple ID Check
    if course_id != 3:
        raise HTTPException(status_code=404, detail="Course not found")

    file_path = Path("course_data.json")
    
    # 2. File Path Check
    if not file_path.exists():
        # This error means the file is not in the directory where uvicorn is running.
        print(f"\nFATAL: Course data file NOT FOUND at: {file_path.resolve()}\n")
        raise HTTPException(status_code=500, detail="Server Error: Course data file missing.")

    try:
        with open(file_path, "r") as f:
            data = json.load(f)
        
        # 3. Data Structure Check
        if not data.get("videos"):
             raise ValueError("JSON file is missing the 'videos' key.")

        return data

    except json.JSONDecodeError as e:
        # This error means there's a typo (extra comma, missing quote) in your JSON.
        print(f"\nFATAL: JSON Decoding Error in course_data.json: {e}\n")
        raise HTTPException(status_code=500, detail="Server Error: Malformed JSON data.")
        
    except ValueError as e:
        # Catch the check above
        print(f"\nFATAL: Data Structure Error: {e}\n")
        raise HTTPException(status_code=500, detail=str(e))
        
    except Exception as e:
        # Catch all other unexpected errors
        print(f"\nFATAL: Unhandled error loading course data: {e}\n")
        raise HTTPException(status_code=500, detail="Server Error: An unknown error occurred.")