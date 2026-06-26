import json
import re
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from crews.tamyez_crew import (
    generate_main_quiz,
    evaluate_and_match,
    generate_sub_quiz,
    evaluate_written_answers
)

app = FastAPI(title="Tamyez AI Service")


# ── Models ──────────────────────────────────────────

class GenerateQuizRequest(BaseModel):
    num_questions: int = 10
    language: str = "English"

class Option(BaseModel):
    id: str
    text: str

class Answer(BaseModel):
    text: str
    type: str
    options: Optional[List[Option]] = None
    userAnswer: List[str]

class CareerItem(BaseModel):
    careerId: str
    title: str
    summary: str

class EvaluateRequest(BaseModel):
    careerList: List[CareerItem]
    answers: List[Answer]

class SubQuizRequest(BaseModel):
    topic: str
    career: str
    level: str
    num_questions: int = 5

class WrittenAnswer(BaseModel):
    question_id: str
    question: str
    answer: str
class EvaluateWrittenRequest(BaseModel):
    topic: str
    career: str
    level: str
    answers: List[WrittenAnswer]


# ── Helper ───────────────────────────────────────────

def extract_json(text: str):
    try:
        return json.loads(text)
    except:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise HTTPException(status_code=500, detail="AI returned invalid JSON")


# ── Endpoints ────────────────────────────────────────

@app.get("/")
def root():
    return {"message": "Tamyez AI Service is running"}

@app.post("/ai/generate-main-quiz")
def api_generate_main_quiz(request: GenerateQuizRequest):
    return extract_json(generate_main_quiz(request.num_questions, request.language))

@app.post("/ai/evaluate-and-match")
def api_evaluate_and_match(request: EvaluateRequest):
    careers = [{"careerId": c.careerId, "title": c.title, "summary": c.summary}
               for c in request.careerList]
    answers = [a.dict() for a in request.answers]
    return extract_json(evaluate_and_match(answers, careers))
@app.post("/ai/generate-sub-quiz")
def api_generate_sub_quiz(request: SubQuizRequest):
    return extract_json(generate_sub_quiz(
        request.topic, request.career,
        request.level, request.num_questions
    ))

@app.post("/ai/evaluate-written-answers")
def api_evaluate_written_answers(request: EvaluateWrittenRequest):
    return extract_json(evaluate_written_answers(
        request.topic, request.career,
        request.level, [a.dict() for a in request.answers]
    ))
