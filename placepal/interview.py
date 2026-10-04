"""The interview logic: generate questions and evaluate answers with the local model."""
from __future__ import annotations

from typing import Any

from . import llm, prompts, schema

SHORT_ANSWER_WORDS = 5
THIN_ANSWER_WORDS = 15


def generate_questions(resume_text: str, role: str, difficulty: str, n: int = 5) -> list[dict[str, str]]:
    """Ask the local model for `n` tailored interview questions."""
    prompt = prompts.build_question_prompt(resume_text, role, difficulty, n)
    return llm.ask_json(
        prompt,
        system=prompts.SYSTEM_PROMPT,
        validate=lambda data: schema.parse_questions(data, expected=n),
    )


def cap_score_for_length(answer: str, score: int) -> int:
    """Stop tiny answers from receiving high scores, whatever the model says."""
    words = len(answer.split())
    if words < SHORT_ANSWER_WORDS:
        return min(score, 2)
    if words < THIN_ANSWER_WORDS:
        return min(score, 4)
    return score


def evaluate_answer(question: dict[str, str], answer: str, role: str, difficulty: str) -> dict[str, Any]:
    """Score one answer and return strengths, gaps and a stronger sample answer."""
    if not answer.strip():
        raise ValueError("Write an answer before asking for an evaluation.")
    prompt = prompts.build_evaluation_prompt(
        question["question"], answer, role, difficulty, question.get("type", "technical")
    )
    result = llm.ask_json(prompt, system=prompts.SYSTEM_PROMPT, validate=schema.parse_evaluation)
    result["score"] = cap_score_for_length(answer, result["score"])
    return result
