import os
import json
from groq import Groq
from app.models import QuizResponse, MCQ, MCQOption


class GroqService:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    async def generate_quiz(self, topic: str, num_questions: int) -> QuizResponse:
        prompt = f"""Generate {num_questions} multiple choice questions about {topic}.

Return ONLY a valid JSON object with this exact structure:
{{
  "questions": [
    {{
      "question": "Question text here?",
      "options": {{
        "A": "Option A text",
        "B": "Option B text",
        "C": "Option C text",
        "D": "Option D text"
      }},
      "correct_answer": "A"
    }}
  ]
}}

Rules:
- Each question must have exactly 4 options (A, B, C, D)
- correct_answer must be one of: A, B, C, or D
- Make questions educational and challenging
- Ensure only one correct answer per question
- Return ONLY the JSON, no additional text"""

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a quiz generator. Always respond with valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.7,
                max_tokens=4096
            )
            
            response_text = chat_completion.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            quiz_data = json.loads(response_text)
            
            # Parse questions
            questions = []
            for q in quiz_data["questions"]:
                mcq = MCQ(
                    question=q["question"],
                    options=MCQOption(**q["options"]),
                    correct_answer=q["correct_answer"]
                )
                questions.append(mcq)
            
            return QuizResponse(topic=topic, questions=questions)
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response from AI: {str(e)}")
        except Exception as e:
            raise Exception(f"Error generating quiz: {str(e)}")