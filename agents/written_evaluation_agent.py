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