"""Validation of model output.

Local models are good but not perfectly reliable, so everything the model returns
is checked and normalised here before the UI sees it.
"""
from __future__ import annotations

import re
from typing import Any

VALID_TYPES = {"technical", "project", "hr"}


def parse_questions(data: Any, expected: int = 5) -> list[dict[str, str]]:
    """Normalise the model's question list. Raises ValueError if unusable."""
    items = data.get("questions") if isinstance(data, dict) else data
    if not isinstance(items, list) or not items:
        raise ValueError("expected a non-empty 'questions' list")

    questions: list[dict[str, str]] = []
    for item in items:
        if isinstance(item, str):
            item = {"question": item}
        if not isinstance(item, dict):
            continue
        text = str(item.get("question", "")).strip()
        if len(text) < 8:
            continue
        qtype = str(item.get("type", "technical")).strip().lower()
        if qtype not in VALID_TYPES:
            qtype = "technical"
        topic = str(item.get("topic") or qtype.title()).strip()[:40]
        questions.append({"question": text, "type": qtype, "topic": topic})

    if len(questions) < expected:
        raise ValueError(f"expected {expected} questions but got {len(questions)}")
    return questions[:expected]


def _clamp_score(value: Any) -> int:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        score = int(round(value))
    else:
        match = re.search(r"\d+(?:\.\d+)?", str(value))
        if not match:
            raise ValueError("the evaluation had no numeric score")
        score = int(round(float(match.group())))
    return max(1, min(10, score))


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, (list, tuple)):
        return []
    return [str(v).strip() for v in value if str(v).strip()]


def parse_evaluation(data: Any) -> dict[str, Any]:
    """Normalise the model's evaluation of one answer. Raises ValueError if unusable."""
    if not isinstance(data, dict):
        raise ValueError("expected a JSON object")
    return {
        "score": _clamp_score(data.get("score")),
        "strengths": _as_list(data.get("strengths")),
        "gaps": _as_list(data.get("gaps")),
        "improved_answer": str(data.get("improved_answer", "")).strip(),
    }
