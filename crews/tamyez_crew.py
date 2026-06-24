import os
from crewai import Crew, Task
from dotenv import load_dotenv
from agents.quiz_generator_agent import create_quiz_generator_agent
from agents.matching_agent import create_matching_agent
from agents.sub_quiz_agent import create_sub_quiz_agent
from agents.written_evaluation_agent import create_written_evaluation_agent

load_dotenv()


def generate_main_quiz(num_questions: int, language: str):
    agent = create_quiz_generator_agent()
    task = Task(
        description=f"""Generate {num_questions} career assessment quiz questions in {language}.
        Mix the questions between:
        - mcq-single: one correct answer
        - mcq-multi: multiple correct answers
        - written: open ended question
        
        Each MCQ question must have exactly 4 options with ids: optA, optB, optC, optD.
        
        Return ONLY a valid JSON in this exact format:
        {{
            "questions": [
                {{
                    "id": "unique_id_here",
                    "text": "question text here",
                    "type": "mcq-single",
                    "options": [
                        {{"id": "optA", "text": "option A text"}},
                        {{"id": "optB", "text": "option B text"}},
                        {{"id": "optC", "text": "option C text"}},
                        {{"id": "optD", "text": "option D text"}}
                    ]
                }}
            ]
        }}
        For written questions, do not include options field.
        Return ONLY the JSON, no extra text.""",
        expected_output="A valid JSON object containing the quiz questions",
        agent=agent
    )
    crew = Crew(agents=[agent], tasks=[task], verbose=True)
    return str(crew.kickoff())


def evaluate_and_match(answers: list, careers: list):
    agent = create_matching_agent()

    answers_text = ""
    for a in answers:
        if a['type'] == 'written':
            user_ans = a['userAnswer']
            if isinstance(user_ans, list):
                user_ans = user_ans[0] if user_ans else ""
            answers_text += f"Q: {a['text']} | A: {user_ans}\n"
        else:
            raw = a['userAnswer']
            selected = raw if isinstance(raw, list) else [raw]
            if not selected:
                answers_text += f"Q: {a['text']} | A: No answer provided\n"
                continue
            options_ordered = {opt['id']: (i, opt['text']) for i, opt in enumerate(a.get('options', []))}
            selected_sorted = sorted(selected, key=lambda s: options_ordered.get(s, (99, s))[0])
            selected_text = ", ".join([options_ordered.get(s, (0, s))[1] for s in selected_sorted])
            answers_text += f"Q: {a['text']} | A: {selected_text}\n"

    careers_text = "\n".join([
        f"- ID: {c['careerId']} | Title: {c['title']} | Summary: {c['summary']}"
        for c in careers
    ])

    task = Task(
        description=f"""Analyze the following student answers and suggest the top 3 most suitable careers.

        Available Careers (ONLY suggest from this list):
        {careers_text}

        Student Answers:
        {answers_text}

        Return ONLY valid JSON in this exact format:
        {{
            "suggestedCareers": [
                {{
                    "careerId": "exact_id_from_career_list",
                    "title": "exact_title_from_career_list",
                    "reason": "Specific reason based on student answers",
                    "confidence": 85
                }}
            ],
            "user_level": "beginner"
        }}

        Rules:
        - ONLY suggest careers from the provided career list
        - Use the EXACT careerId and title from the list
        - Suggest exactly 3 careers
        - confidence is integer between 0 and 100
        - reason must be specific to the student actual answers
        - user_level must be: beginner / intermediate / advanced
        - Return ONLY the JSON, no extra text.""",
        expected_output="Valid JSON with top 3 suggested careers and user_level",
        agent=agent
    )

    crew = Crew(agents=[agent], tasks=[task], verbose=True)
    return str(crew.kickoff())


def generate_sub_quiz(topic: str, career: str, level: str, num_questions: int):
    agent = create_sub_quiz_agent()
    task = Task(
        description=f"""Generate {num_questions} quiz questions about the following topic.

        Topic: {topic}
        Career Track: {career}
        Student Level: {level}

        Mix between mcq-single and written questions.

        Return ONLY a valid JSON in this exact format:
        {{
            "questions": [
                {{
                    "id": "unique_id_here",
                    "text": "question text here",
                    "type": "mcq-single",
                    "options": [
                        {{"id": "optA", "text": "option text"}},
                        {{"id": "optB", "text": "option text"}},
                        {{"id": "optC", "text": "option text"}},
                        {{"id": "optD", "text": "option text"}}
                    ],
                    "correctAnswer": ["optB"],
                    "explanation": "Why this is the correct answer"
                }}
            ]
        }}

        Rules:
        - For written questions: no options, no correctAnswer, no explanation
        - For mcq-single: always include correctAnswer and explanation
        - Return ONLY the JSON, no extra text.""",
        expected_output="A valid JSON object containing the quiz questions",
        agent=agent
    )
    crew = Crew(agents=[agent], tasks=[task], verbose=True)
    return str(crew.kickoff())


def evaluate_written_answers(topic: str, career: str, level: str, answers: list):
    agent = create_written_evaluation_agent()
    answers_text = "\n".join([
        f"Q{i+1} [id:{a['question_id']}]: {a['question']}\nA{i+1}: {a['answer']}"
        for i, a in enumerate(answers)
    ])
    task = Task(
        description=f"""Evaluate these written answers.
        Topic: {topic} | Career: {career} | Level: {level}

        {answers_text}

        Return ONLY valid JSON:
        {{
            "evaluations": [
                {{
                    "question_id": "id here"
                    "question": "question text",
                    "student_answer": "student answer",
                    "score": 75,
                    "feedback": "Constructive feedback"
                }}
            ],
            "overall_score": 75,
            "overall_feedback": "Summary of performance"
        }}
        Rules:
        - score integer 0-100
        - overall_score = average of all scores
        - feedback in same language as student answer
        Return ONLY the JSON.""",
        expected_output="Valid JSON with scores and feedback",
        agent=agent
    )
    crew = Crew(agents=[agent], tasks=[task], verbose=True)
    return str(crew.kickoff())