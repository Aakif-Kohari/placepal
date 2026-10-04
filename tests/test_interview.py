import pytest

from placepal import interview


def test_generate_questions(fake_llm):
    questions = interview.generate_questions("resume " * 30, "Data Analyst", "Medium")
    assert len(questions) == 5


def test_evaluate_answer(fake_llm):
    question = {"question": "Explain hashing.", "type": "technical", "topic": "DSA"}
    answer = "A hash function maps keys to buckets so lookups take constant time on average. " * 2
    result = interview.evaluate_answer(question, answer, "Software Engineer (SDE)", "Easy")
    assert result["score"] == 8


def test_empty_answer_is_rejected(fake_llm):
    with pytest.raises(ValueError):
        interview.evaluate_answer({"question": "Q?", "type": "hr", "topic": "HR"}, "   ", "Data Analyst", "Easy")


@pytest.mark.parametrize(
    "answer,score,expected",
    [("idk", 9, 2), ("it depends on the situation really", 9, 4), ("word " * 20, 9, 9)],
)
def test_short_answers_are_capped(answer, score, expected):
    assert interview.cap_score_for_length(answer, score) == expected
