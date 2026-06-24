
```markdown
# Tamyez AI Service — Implementation Documentation

---

## AI Service Overview

The AI Service is a Python microservice that provides all AI capabilities
for the Tamyez platform. It exposes REST API endpoints that the Node.js
Backend calls to generate quizzes, match careers, evaluate answers, and
recommend courses.
---

### Overall AI Service Flow

```
Student Opens App
->
[1] Backend -> POST /ai/generate-main-quiz
->
AI generates scenario-based assessment questions
->
Student Answers All Questions
->
[2] Backend -> POST /ai/evaluate-and-match
->
AI analyzes answers -> returns top 3 careers + user_level
->
Backend saves user_level in Database
->
Student Selects a Career Track
->
Backend fetches Roadmap from Database (no AI involved)
->
[3] Backend -> POST /ai/recommend-courses
->
Serper API searches YouTube -> AI selects best 3 courses
->
[4] Backend -> POST /ai/generate-sub-quiz
->
AI generates MCQ + written questions
->
MCQ answers -> Backend evaluates automatically
Written answers -> [5] Backend -> POST /ai/evaluate-written-answers
->
AI scores each written answer + gives feedback
->
Student sees Score and Feedback -> moves to next step
```
---

## Tech Stack

| Technology | Purpose |
|---|---|
| Python 3.11 | Main language |
| CrewAI | Multi-Agent Framework |
| FastAPI | REST API |
| Groq + Llama 3.3 70B | LLM (Development) |
| GPT-4o | LLM (Final Presentation) |
| Serper API | Real YouTube course search |
| LiteLLM | LLM connector |
| Uvicorn | ASGI Server |

---

## Project Structure

```
tamyez-ai/
|-- .env
|-- main.py
|-- agents/
|   |-- quiz_generator_agent.py
|   |-- matching_agent.py
|   |-- sub_quiz_agent.py
|   |-- written_evaluation_agent.py
|-- crews/
|   |-- tamyez_crew.py
|-- tools/
    |-- search_tool.py
```

---

---

# Agents

---

## Agent 1: Quiz Generator Agent

### File
`agents/quiz_generator_agent.py`

### What it does
Generates scenario-based career assessment questions that reveal
the student's true skills, personality, and interests without
asking direct obvious questions.

### Input
Called internally by `generate_main_quiz()` in `tamyez_crew.py`

### Output

```json
{
  "id": "q1",
  "text": "question text",
  "type": "mcq-single | mcq-multi | written",
  "options": [
    { "id": "optA", "text": "option A" },
    { "id": "optB", "text": "option B" },
    { "id": "optC", "text": "option C" },
    { "id": "optD", "text": "option D" }
  ]
}
```
Note: written questions have no options field.

### Code
```python
import os
from crewai import Agent, LLM
from dotenv import load_dotenv

load_dotenv()

def create_quiz_generator_agent():
    llm = LLM(
        model="groq/llama-3.3-70b-versatile",
        api_key=os.getenv("GROQ_API_KEY")
    )
    return Agent(
        role="Career Assessment Quiz Generator",
        goal="Generate insightful scenario-based quiz questions that deeply reveal student skills, personality, and interests",
        backstory="""You are a world-class career assessment expert with 15 years 
        of experience in psychometric testing and career counseling.
        You design questions that deeply reveal:
        - Technical aptitude and logical thinking
        - Creative vs analytical personality
        - Team player vs independent worker
        - Problem-solving approach
        - Learning style and preferences
        - Work environment preferences
        Rules you ALWAYS follow:
        1. Never ask direct questions like "do you like coding?" 
           Instead ask scenario-based questions
        2. Each question must reveal something different about the person
        3. Questions must be clear, unambiguous, and culture-neutral
        4. Mix between personality, aptitude, and preference questions
        5. Never repeat similar questions""",
        llm=llm,
        verbose=True
    )
```

### Flow
```
POST /ai/generate-main-quiz
{ num_questions, language }
        ↓
Quiz Generator Agent
        ↓
{ questions: [ { id, text, type, options } ] }
        ↓
Backend displays questions to student
```

---

## Agent 2: Matching Agent

### File
`agents/matching_agent.py`

### What it does
Analyzes student quiz answers and recommends the top 3 most suitable
career tracks from a provided list. Returns exact careerId and title
from the list, confidence percentage, specific reason, and user_level.

### Input
- `answers` — list of student answers with question text and selected options
- `careers` — list of available careers from the Database

### Output
```json
{
  "suggestedCareers": [
    {
      "careerId": "exact_id_from_list",
      "title": "exact_title_from_list",
      "reason": "Specific reason based on actual answers",
      "confidence": 90
    }
  ],
  "user_level": "beginner | intermediate | advanced"
}
```

### Code
```python
import os
from crewai import Agent, LLM
from dotenv import load_dotenv

load_dotenv()

def create_matching_agent():
    llm = LLM(
        model="groq/llama-3.3-70b-versatile",
        api_key=os.getenv("GROQ_API_KEY")
    )
    return Agent(
        role="Career Matching Specialist",
        goal="Analyze student quiz answers and suggest the top 3 most suitable career tracks with confidence percentage and specific reason for each",
        backstory="""You are a senior tech career consultant with deep expertise 
        in the Egyptian and Middle Eastern job market.
        You have placed thousands of graduates in the following tracks:
        - Data Science & Machine Learning
        - Backend Development (Python, .NET, Node.js)
        - Frontend Development (React, Vue)
        - Mobile Development (Flutter, Android, iOS)
        - UI/UX Design
        - Cybersecurity
        - AI Engineering
        - DevOps & Cloud
        Your matching rules:
        1. NEVER give generic reasons - every reason must reference specific answers
        2. Confidence must reflect real compatibility (never give 3 tracks all above 85%)
        3. Consider the Egyptian job market demand when ranking tracks
        4. If answers are contradictory, mention it in the reason field
        5. Always suggest tracks that have good job opportunities in Egypt""",
        llm=llm,
        verbose=True
    )
```

### Flow
```
POST /ai/evaluate-and-match
{ careerList: [...from DB], answers: [...student answers] }
        ↓
Matching Agent analyzes answers
        ↓
Matches student profile to careers from the list ONLY
        ↓
{ suggestedCareers: [...], user_level: "beginner" }
        ↓
Backend saves user_level in DB
        ↓
user_level reused in all subsequent endpoints
```

---

## Agent 3: Sub Quiz Agent

### File
`agents/sub_quiz_agent.py`

### What it does
Generates a quiz for each roadmap step to measure the student's
understanding. MCQ questions include correct answers and explanations.
Written questions have no answer — evaluated by Agent 4.

### Input
- `topic` — the roadmap step topic
- `career` — student's selected career
- `level` — student level from DB (beginner/intermediate/advanced)
- `num_questions` — number of questions to generate

### Output
```json
{
  "questions": [
    {
      "id": "q1",
      "text": "question text",
      "type": "mcq-single",
      "options": [
        { "id": "optA", "text": "option" },
        { "id": "optB", "text": "option" },
        { "id": "optC", "text": "option" },
        { "id": "optD", "text": "option" }
      ],
      "correctAnswer": ["optB"],
      "explanation": "Why this is correct"
    },
    {
      "id": "q2",
      "text": "written question text",
      "type": "written"
    }
  ]
}
```

### Code
```python
import os
from crewai import Agent, LLM
from dotenv import load_dotenv

load_dotenv()

def create_sub_quiz_agent():
    llm = LLM(
        model="groq/llama-3.3-70b-versatile",
        api_key=os.getenv("GROQ_API_KEY")
    )
    return Agent(
        role="Roadmap Step Quiz Generator",
        goal="Generate accurate quiz questions for a specific roadmap step to measure student understanding",
        backstory="""You are an expert technical educator who creates 
        high-quality assessments for tech students.
        Your question design rules:
        1. MCQ questions must have ONE clearly correct answer
        2. Wrong options must be plausible (not obviously wrong)
        3. Explanations must teach, not just state the answer
        4. Written questions must be open-ended and thought-provoking
        5. Questions must match the student level exactly
        6. Never repeat concepts across questions
        7. For beginner level: focus on concepts and definitions
        8. For intermediate: focus on application and problem-solving
        9. For advanced: focus on optimization and best practices""",
        llm=llm,
        verbose=True
    )
```

### Flow
```
Student finishes a roadmap step
        ↓
POST /ai/generate-sub-quiz
{ topic, career, level, num_questions }
        ↓
Sub Quiz Agent generates MCQ + written questions
        ↓
{ questions: [...] }
        ↓
MCQ → Backend evaluates using correctAnswer automatically
Written → sent to Agent 4 for AI evaluation
```

---

## Agent 4: Written Evaluation Agent

### File
`agents/written_evaluation_agent.py`

### What it does
Evaluates student written answers and returns a score (0-100) with
constructive feedback. Feedback language automatically matches the
student's answer language. Evaluates multiple answers in one request.

### Input
- `topic` — the roadmap step topic
- `career` — student's selected career
- `level` — student level from DB
- `answers` — list of { question, answer }

### Output
```json
{
  "evaluations": [
    {
      "question": "question text",
      "student_answer": "student answer",
      "score": 75,
      "feedback": "Constructive feedback here"
    }
  ],
  "overall_score": 75,
  "overall_feedback": "Summary of student performance"
}
```

### Code
```python
import os
from crewai import Agent, LLM
from dotenv import load_dotenv

load_dotenv()

def create_written_evaluation_agent():
    llm = LLM(
        model="groq/llama-3.3-70b-versatile",
        api_key=os.getenv("GROQ_API_KEY")
    )
    return Agent(
        role="Written Answer Evaluator",
        goal="Evaluate student written answers for roadmap step quizzes and provide a score with constructive feedback",
        backstory="""You are an expert technical educator and assessor with 15 years 
        of experience evaluating programming and tech students.
        Your evaluation rules:
        1. Evaluate based on: correctness, depth of understanding, and clarity
        2. Score from 0 to 100 — be fair but strict
        3. Feedback must be constructive — tell what they got right AND what they missed
        4. Never give 100 unless the answer is truly complete and accurate
        5. Never give 0 unless the answer is completely wrong or irrelevant
        6. Consider the student level (beginner/intermediate/advanced) when scoring
        7. Feedback must be in the SAME language as the student's answer
        8. Keep feedback concise — max 3 sentences""",
        llm=llm,
        verbose=True
    )
```

### Flow
```
Student submits written answers
        ↓
Backend collects all written answers
        ↓
POST /ai/evaluate-written-answers
{ topic, career, level, answers: [ { question, answer } ] }
        ↓
Written Evaluation Agent scores each answer
        ↓
{ evaluations: [...], overall_score, overall_feedback }
        ↓
Backend saves scores → Student sees feedback
```

---

---

# Tools

---

## Search Tool

### File
`tools/search_tool.py`

### What it does
Uses Serper API to search YouTube for real, up-to-date course links.
Solves the LLM hallucination problem where AI invents fake URLs.

### Input
- `topic` — roadmap step topic
- `career` — student's selected career
- `level` — student level

### Output
```json
{
  "courses": [
    {
      "title": "Course Title",
      "url": "https://youtube.com/watch?v=...",
      "description": "Why this course is recommended",
      "platform": "YouTube",
      "level": "beginner"
    }
  ]
}
```

### Code
```python
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def search_youtube_courses(query: str, num_results: int = 3) -> list:
    api_key = os.getenv("SERPER_API_KEY")
    url = "https://google.serper.dev/search"
    payload = {
        "q": f"{query} course tutorial site:youtube.com",
        "num": num_results * 2
    }
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        results = []
        for item in data.get("organic", [])[:num_results]:
            results.append({
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "description": item.get("snippet", ""),
                "source": "YouTube"
            })
        return results
    except Exception as e:
        print(f"Search error: {e}")
        return []

def search_courses(topic: str, career: str, num_results: int = 3) -> list:
    query = f"best {topic} course for {career} beginners 2025"
    return search_youtube_courses(query, num_results)
```

### Flow
```
POST /ai/recommend-courses
{ topic, career, level }
        ↓
search_courses builds query:
"best Python Fundamentals course for Data Science beginners 2025"
        ↓
Serper API searches Google with site:youtube.com
        ↓
Returns real YouTube links
        ↓
AI selects best 3
        ↓
{ courses: [...] } → Student gets real working links
```

---

---

# API Endpoints

---

## POST /ai/generate-main-quiz

**Input:**
```json
{ "num_questions": 10, "language": "English" }
```

**Output:**
```json
{
  "questions": [
    {
      "id": "q1",
      "text": "question",
      "type": "mcq-single",
      "options": [
        { "id": "optA", "text": "option" },
        { "id": "optB", "text": "option" },
        { "id": "optC", "text": "option" },
        { "id": "optD", "text": "option" }
      ]
    }
  ]
}
```

---

## POST /ai/evaluate-and-match

**Input:**
```json
{
  "careerList": [
    { "careerId": "id", "title": "Title", "summary": "Summary" }
  ],
  "answers": [
    {
      "text": "question",
      "type": "mcq-single",
      "options": [
        { "id": "optA", "text": "option" }
      ],
      "userAnswer": ["optA"]
    },
    {
      "text": "written question",
      "type": "written",
      "userAnswer": "student written answer"
    }
  ]
}
```

**Output:**
```json
{
  "suggestedCareers": [
    {
      "careerId": "exact_id",
      "title": "exact_title",
      "reason": "Specific reason",
      "confidence": 90
    }
  ],
  "user_level": "beginner"
}
```

---

## POST /ai/generate-sub-quiz

**Input:**
```json
{
  "topic": "Statistics & Math",
  "career": "Data Science",
  "level": "beginner",
  "num_questions": 5
}
```

**Output:**
```json
{
  "questions": [
    {
      "id": "q1",
      "text": "question",
      "type": "mcq-single",
      "options": [
        { "id": "optA", "text": "option" },
        { "id": "optB", "text": "option" },
        { "id": "optC", "text": "option" },
        { "id": "optD", "text": "option" }
      ],
      "correctAnswer": ["optB"],
      "explanation": "Why correct"
    },
    {
      "id": "q2",
      "text": "written question",
      "type": "written"
    }
  ]
}
```

---

## POST /ai/evaluate-written-answers

**Input:**
```json
{
  "topic": "Statistics & Math",
  "career": "Data Science",
  "level": "beginner",
  "answers": [
    {
      "question": "Explain the difference between mean and median.",
      "answer": "Mean is the average. Median is the middle value."
    }
  ]
}
```

**Output:**
```json
{
  "evaluations": [
    {
      "question": "Explain the difference between mean and median.",
      "student_answer": "Mean is the average. Median is the middle value.",
      "score": 65,
      "feedback": "Good basic understanding. However, you missed explaining when to use each one."
    }
  ],
  "overall_score": 65,
  "overall_feedback": "Student shows basic understanding but needs to work on practical application."
}
```

---

## POST /ai/recommend-courses

**Input:**
```json
{
  "topic": "Statistics & Math",
  "career": "Data Science",
  "level": "beginner"
}
```

**Output:**
```json
{
  "courses": [
    {
      "title": "Statistics for Data Science",
      "url": "https://youtube.com/watch?v=...",
      "description": "Why recommended",
      "platform": "YouTube",
      "level": "beginner"
    }
  ]
}
```

---

## How to Run

```bash
.\venv\Scripts\activate
uvicorn main:app --reload
```

API Docs: `http://127.0.0.1:8000/docs`

---



