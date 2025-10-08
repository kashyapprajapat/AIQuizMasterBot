from pydantic import BaseModel, Field
from typing import List


class QuizRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=100)
    num_questions: int = Field(..., ge=3, le=30)


class MCQOption(BaseModel):
    A: str
    B: str
    C: str
    D: str


class MCQ(BaseModel):
    question: str
    options: MCQOption
    correct_answer: str = Field(..., pattern="^[A-D]$")


class QuizResponse(BaseModel):
    topic: str
    questions: List[MCQ]