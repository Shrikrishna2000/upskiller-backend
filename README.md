
# 🚀 Upskiller-backend: AI-Powered Learning Platform

This repository houses the core API services for the Upskiller learning platform, built with **FastAPI** and **LangChain**. It manages user authentication, stores learning content, tracks user progress, and dynamically generates course material using the Gemini AI model.

## ✨ Project Status: Core Loop Complete (Milestone 4C)

The backend has successfully implemented all core requirements for a functional, secure, and dynamically-generating MVP.

| Milestone | Goal | Status |
| :--- | :--- | :--- |
| **Milestone 1/2 (Security)** | User Auth & Secure Data Access | ✅ **Complete** |
| **Milestone 3 (Persistence)** | Progress Tracking (`UserProgress`) | ✅ **Complete** |
| **Milestone 4A/B/C (AI Core)** | Multi-Content Generation & Persistence | ✅ **Complete** |

### Implemented Functionality

* **Secure Authentication:** JWT-based login and registration.
* **Persistent Progress:** Saves and loads user progress (`quiz_score`, `is_completed`).
* **AI Pipeline:** Integrates **LangChain** and **Gemini** to analyze YouTube content.
* **Multi-Content Generation:** Dynamically generates **Quizzes** and **Flashcards** from a single YouTube URL.
* **Decoupled Persistence:** Uses a dedicated `services.py` layer to handle complex database transactions.

---

## 🛠️ Challenges Overcome (Situation, Task, Action, Result)

The development of the AI pipeline and persistence layer required strategic solutions to maintain a scalable architecture.

| Situation | Task | Action | Result |
| :--- | :--- | :--- | :--- |
| **Non-Persistent Data** | The AI generated content, but changes didn't save to `sql_app.db`. | Verified `db.commit()` was explicitly called on the final transaction, and used **database rollback** on exceptions for integrity. | **Successful Persistence:** Data for `Course`, `Video`, `Quiz`, and `Flashcard` now correctly saves to the database. |
| **API/Database Coupling** | Persistence logic (`save_generated_content`) was embedded directly in the router (`main.py`). | Created a dedicated **`services.py`** file and moved all data transaction logic into this new layer. | **Scalable Architecture:** Router (`main.py`) is now clean, and persistence logic is reusable by any future background job or tool. |
| **Rigid AI Output** | Needed to reliably generate both Quiz and Flashcard JSON from a single API call. | Created two dedicated **Pydantic schemas** (`GeneratedQuiz`, `GeneratedFlashcards`) and two separate LangChain **chains** in `ai_pipeline.py`. | **Reliable Multi-Content:** The AI is now forced to output clean, validated JSON for both Quizzes and Flashcards simultaneously. |

---

## ⏭️ Next Steps Guide (Milestone 4D and Beyond)

The backend is now ready, and the remaining work focuses on exposing this content via the frontend.

| Step | Goal | Required Action |
| :--- | :--- | :--- |
| **Milestone 4D** | **Frontend Integration & Course Discovery** | Build a new **`GET /api/courses`** endpoint to list all available courses (both static and AI-generated) for a user dashboard. |
| **Milestone 5** | **Frontend Display & Use** | Update the frontend to display the new list of courses, and render the newly generated **Flashcards** in the course player UI. |
| **Milestone 6 (Refinement)** | **AI Error Handling** | Integrate **LangGraph** (as planned) into `ai_pipeline.py` to handle automated retries if the Gemini model fails to produce valid JSON output on the first attempt. |