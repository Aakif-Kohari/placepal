import pytest

from placepal import schema
from tests.conftest import QUESTIONS


def test_parse_questions_ok():
    parsed = schema.parse_questions(QUESTIONS, expected=5)
    assert len(parsed) == 5
    assert {q["type"] for q in parsed} <= schema.VALID_TYPES


def test_parse_questions_too_few_raises():
    with pytest.raises(ValueError):
        schema.parse_questions({"questions": QUESTIONS["questions"][:2]}, expected=5)


def test_parse_questions_normalises_unknown_type():
    data = {"questions": [{"question": "What is a deadlock exactly?", "type": "weird"}] * 5}
    assert schema.parse_questions(data)[0]["type"] == "technical"


def test_parse_evaluation_clamps_and_parses_score():
    assert schema.parse_evaluation({"score": 15})["score"] == 10
    assert schema.parse_evaluation({"score": 0})["score"] == 1
    assert schema.parse_evaluation({"score": "7/10"})["score"] == 7


def test_parse_evaluation_requires_score():
    with pytest.raises(ValueError):
        schema.parse_evaluation({"strengths": []})


def test_parse_evaluation_accepts_string_lists():
    result = schema.parse_evaluation({"score": 5, "strengths": "Good", "gaps": None})
    assert result["strengths"] == ["Good"] and result["gaps"] == []
