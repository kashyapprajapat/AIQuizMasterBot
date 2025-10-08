from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.models import QuizRequest, QuizResponse
from app.services import GroqService

# Load environment variables
load_dotenv()

app = FastAPI(
    title="AIQuizMasterBot API",
    description="Generate AI-powered quiz questions",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize service lazily to avoid startup errors
groq_service = None

@app.on_event("startup")
async def startup_event():
    global groq_service
    groq_service = GroqService()


@app.get("/")
async def root():
    return {
        "message": "AIQuizMasterBot API",
        "status": "running",
        "endpoints": {
            "generate_quiz": "/api/quiz/generate"
        }
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/api/quiz/generate", response_model=QuizResponse)
async def generate_quiz(request: QuizRequest):
    """
    Generate quiz questions based on topic and number of questions
    
    - **topic**: Subject for quiz questions (e.g., "React", "Python")
    - **num_questions**: Number of MCQs (3-30)
    """
    try:
        quiz = await groq_service.generate_quiz(
            topic=request.topic,
            num_questions=request.num_questions
        )
        return quiz
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)