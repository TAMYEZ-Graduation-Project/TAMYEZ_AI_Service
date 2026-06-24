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