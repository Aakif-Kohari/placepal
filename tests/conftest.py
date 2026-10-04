import json

import pytest

QUESTIONS = {
    "questions": [
        {"question": "Explain how a hash map handles collisions.", "type": "technical", "topic": "DSA"},
        {"question": "What is the difference between SQL joins?", "type": "technical", "topic": "DBMS"},
        {"question": "Walk me through the architecture of your main project.", "type": "project", "topic": "Projects"},
        {"question": "Which technical decision in your project would you change?", "type": "project", "topic": "Projects"},
        {"question": "Tell me about a time you worked in a team.", "type": "hr", "topic": "Teamwork"},
    ]
}

EVALUATION = {
    "score": 8,
    "strengths": ["Clear structure"],
    "gaps": ["Missing an example"],
    "improved_answer": "A stronger answer would add a concrete example.",
}


def fake_chat(messages, model):
    """Stand-in for the Ollama call so tests never need a model."""
    prompt = messages[-1]["content"]
    if "TASK: GENERATE_QUESTIONS" in prompt or any("TASK: GENERATE_QUESTIONS" in m["content"] for m in messages):
        return json.dumps(QUESTIONS)
    return json.dumps(EVALUATION)


@pytest.fixture
def fake_llm(monkeypatch, tmp_path):
    monkeypatch.setattr("placepal.llm._chat", fake_chat)
    monkeypatch.setenv("PLACEPAL_DATA", str(tmp_path / "sessions.json"))
    return tmp_path / "sessions.json"
