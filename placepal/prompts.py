"""Prompt templates. Kept separate so they are easy to read, tweak and test."""
from __future__ import annotations

ROLES: dict[str, str] = {
    "Software Engineer (SDE)": (
        "data structures and algorithms, OOP, DBMS and SQL, operating systems, "
        "computer networks, system design basics"
    ),
    "Data Analyst": (
        "SQL, statistics, Excel, Python and pandas, data visualisation, business metrics, A/B testing"
    ),
    "ML / Data Science Engineer": (
        "machine learning fundamentals, model evaluation, feature engineering, Python, "
        "statistics, deployment basics"
    ),
    "Cybersecurity Analyst": (
        "networking, OWASP Top 10, cryptography basics, Linux, threat modelling, incident response"
    ),
    "Frontend / Full-Stack Developer": (
        "JavaScript and TypeScript, React, HTTP and REST, databases, performance, accessibility"
    ),
}

DIFFICULTY_NOTES: dict[str, str] = {
    "Easy": "Ask fundamentals a well-prepared fresher should know.",
    "Medium": "Ask a mix of fundamentals and applied scenario questions.",
    "Hard": "Ask deep, scenario-based questions that probe trade-offs and edge cases.",
}

SYSTEM_PROMPT = (
    "You are PlacePal, a strict but encouraging interviewer who prepares Indian engineering "
    "students for campus placement interviews. You always reply with a single JSON object "
    "and nothing else."
)

MAX_RESUME_CHARS = 6000


def build_question_prompt(resume_text: str, role: str, difficulty: str, n: int = 5) -> str:
    focus = ROLES.get(role, "core computer science fundamentals")
    note = DIFFICULTY_NOTES.get(difficulty, DIFFICULTY_NOTES["Medium"])
    resume = resume_text.strip()[:MAX_RESUME_CHARS]
    return f"""TASK: GENERATE_QUESTIONS

Target role: {role}
Role focus areas: {focus}
Difficulty: {difficulty}. {note}

Candidate resume:
\"\"\"
{resume}
\"\"\"

Write exactly {n} interview questions for this candidate:
- 2 questions of type "technical" (about the role focus areas)
- 2 questions of type "project" (refer to a specific project, skill or experience named in the resume)
- 1 question of type "hr"
Each question must be one clear question. Give each a short "topic" tag (1-3 words, e.g. "DBMS", "REST APIs").

Reply with JSON in exactly this format:
{{"questions": [{{"question": "...", "type": "technical", "topic": "..."}}]}}"""


def build_evaluation_prompt(
    question: str, answer: str, role: str, difficulty: str, qtype: str = "technical"
) -> str:
    return f"""TASK: EVALUATE_ANSWER

Target role: {role}
Difficulty: {difficulty}
Question type: {qtype}

Question: {question}

Candidate's answer:
\"\"\"
{answer.strip()}
\"\"\"

Evaluate the answer like a real interviewer. Be honest and do not inflate scores.
Scoring guide: 1-3 = wrong, off-topic or too thin; 4-5 = partially correct; 6-7 = solid;
8-9 = strong with good detail; 10 = exceptional (rare).

Reply with JSON in exactly this format:
{{"score": 6, "strengths": ["..."], "gaps": ["..."], "improved_answer": "A stronger model answer in 3-6 sentences."}}"""
