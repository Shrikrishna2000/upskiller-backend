import os
import json
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from auth_utils import GEMINI_API_KEY
from youtube_transcript_api import YouTubeTranscriptApi

# -----------------------------------------------------------------
# 1. AI Output Schema
# -----------------------------------------------------------------

class QuizQuestion(BaseModel):
    """Schema for a single multiple-choice question."""
    question: str = Field(description="The question text.")
    options: list[str] = Field(description="List of 4 possible answers.")
    correct: int = Field(description="The 0-based index of the correct option (0, 1, 2, or 3).")
    explaination: str = Field(description="A brief explanation of the correct answer.")
    
class GeneratedQuiz(BaseModel):
    """The final quiz structure the AI must output."""
    video_title: str = Field(description="The title of the YouTube video.")
    quiz: list[QuizQuestion] = Field(description="A list of 3 high-quality, knowledge-based quiz questions.")

class FlashcardItem(BaseModel):
    """Schema for a single flashcard (Front: Concept, Back: Definition)."""
    front: str = Field(description="Question on key concept or term from the video. ")
    back: str = Field(description="The definition or explanation of the concept.")

class GeneratedFlashcards(BaseModel):
    """The final flashcard structure the AI must output."""
    video_title: str = Field(description="The title of the YouTube video.")
    flashcards: list[FlashcardItem] = Field(description="A list of 5 key-concept flashcards.")

# -----------------------------------------------------------------
# 2. Pipeline Utility Functions
# -----------------------------------------------------------------

def get_transcript(youtube_id: str) -> str:
    """Fetches the transcript for a given YouTube video ID."""
    try:
        yt_api = YouTubeTranscriptApi()
        transcript_list = yt_api.fetch(youtube_id, languages=['en', 'hi'])
        # Concatenate all lines into a single string
        transcript = " ".join([item.text for item in transcript_list.snippets])
        return transcript
    except Exception as e:
        # Fallback if transcript isn't available
        return f"Transcript not available. Use the video ID and topic to generate the quiz. Error: {e}"

# -----------------------------------------------------------------
# 3. LangChain Agents (Adding Flashcard Generator)
# -----------------------------------------------------------------

def generate_quiz_content(youtube_id: str) -> dict:
    """
    Core function to orchestrate content generation using Gemini and LangChain.
    """

    # Use a powerful model for complex JSON generation
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", temperature=0.0)
    parser = JsonOutputParser(pydantic_object=GeneratedQuiz)

    # --- Data Retrieval ---
    transcript_text = get_transcript(youtube_id)
    
    # --- System Prompt ---
    system_prompt = (
        "You are an expert educational content generator. Your task is to analyze the provided video content (transcript/topic) "
        "and generate exactly **3 difficult, knowledge-based multiple-choice questions** that serve as a 'Mastery Gate'. "
        "The output MUST strictly follow the provided JSON schema. Do not include any text outside the JSON block."
    )
    
    # --- Template ---
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("user", "Video Content: {content}"),
            ("user", "Output Format: {format_instructions}"),
        ]
    ).partial(format_instructions=parser.get_format_instructions())
    
    # --- Chain Execution ---
    chain = prompt | llm | parser

    # NOTE: In a real app, we'd handle the response if parsing failed.
    response = chain.invoke({"content": transcript_text})

    # The output is already a Python dictionary matching the GeneratedQuiz schema
    return response 

def generate_flashcard_content(youtube_id: str) -> dict:
    """
    Orchestrates content generation for flashcards using Gemini and LangChain.
    """
    os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY

    llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", temperature=0.0)
    parser = JsonOutputParser(pydantic_object=GeneratedFlashcards)
    transcript_text = get_transcript(youtube_id)
    
    system_prompt = (
        "You are an expert educational content generator. Your task is to analyze the provided video content (transcript/topic) "
        "and generate exactly **5 key concept flashcards**. Each flashcard must have a clear 'front' (term) and 'back' (definition). "
        "The output MUST strictly follow the provided JSON schema. Do not include any text outside the JSON block."
    )
    
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("user", "Video Content: {content}"),
            ("user", "Output Format: {format_instructions}"),
        ]
    ).partial(format_instructions=parser.get_format_instructions())
    
    chain = prompt | llm | parser

    response = chain.invoke({"content": transcript_text})
    return response

# -----------------------------------------------------------------
# 4. Agent Orchestrator (Combine all generation steps)
# -----------------------------------------------------------------

def generate_all_content(youtube_id: str) -> tuple[dict, dict]:
    """
    Runs both the quiz and flashcard pipelines and returns their results.
    """
    quiz_data = generate_quiz_content(youtube_id)
    flashcard_data = generate_flashcard_content(youtube_id)
    
    return quiz_data, flashcard_data

# Placeholder for LangGraph Agent (Will be expanded in Milestone 4B)
# def run_generation_agent(youtube_id: str) -> dict:
#     # Future: This will wrap the chain execution with retries and state management
#     return generate_quiz_content(youtube_id)

if __name__ == "__main__":
    # Test the pipeline with a sample YouTube video ID
    sample_video_id = "TqPzwenhMj0"  # Replace with a valid video ID for real testing
    # test generate_quiz_content
    responce = generate_quiz_content(sample_video_id)
    print(json.dumps(responce))