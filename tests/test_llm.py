import pytest

from placepal import llm


def test_extract_json_plain():
    assert llm.extract_json('{"a": 1}') == {"a": 1}


def test_extract_json_from_markdown_fence():
    assert llm.extract_json('Sure!\n```json\n{"a": 2}\n```') == {"a": 2}


def test_extract_json_with_chatter_around_it():
    assert llm.extract_json('Here you go: {"a": 3} hope that helps') == {"a": 3}


def test_extract_json_rejects_garbage():
    with pytest.raises(ValueError):
        llm.extract_json("no json here")
    with pytest.raises(ValueError):
        llm.extract_json("   ")


def test_ask_json_retries_then_succeeds(monkeypatch):
    replies = iter(["not json", '{"ok": true}'])
    monkeypatch.setattr(llm, "_chat", lambda messages, model: next(replies))
    assert llm.ask_json("hi") == {"ok": True}


def test_ask_json_gives_up_after_retries(monkeypatch):
    monkeypatch.setattr(llm, "_chat", lambda messages, model: "still not json")
    with pytest.raises(llm.LLMError):
        llm.ask_json("hi", retries=1)


def test_model_and_host_come_from_environment(monkeypatch):
    monkeypatch.delenv("PLACEPAL_MODEL", raising=False)
    assert llm.get_model() == llm.DEFAULT_MODEL
    monkeypatch.setenv("PLACEPAL_MODEL", "qwen3:4b")
    assert llm.get_model() == "qwen3:4b"


@pytest.mark.parametrize(
    "host,expected",
    [
        ("http://127.0.0.1:11434", True),
        ("localhost:11434", True),
        ("http://[::1]:11434", True),
        ("http://192.168.1.50:11434", False),
        ("https://ollama.example.com", False),
    ],
)
def test_is_local_host(host, expected):
    assert llm.is_local_host(host) is expected
