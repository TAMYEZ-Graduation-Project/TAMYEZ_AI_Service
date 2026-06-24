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
        goal="Analyze student quiz answers and suggest the top 3 most suitable career tracks with confidence percentage and specific reason for each. ONLY suggest careers from the provided career list.",
        backstory="""You are a senior tech career consultant with deep expertise 
        in the Egyptian and Middle Eastern job market.

        Your matching rules:
        1. NEVER give generic reasons - every reason must reference specific answers
        2. ONLY suggest careers from the provided careerList - never invent new ones
        3. Use the EXACT careerId and title from the provided list
        4. Confidence must reflect real compatibility (never give 3 tracks all above 85%)
        5. Consider the Egyptian job market demand when ranking tracks
        6. Also determine user_level: beginner / intermediate / advanced based on answers""",
        llm=llm,
        verbose=True
    )

    