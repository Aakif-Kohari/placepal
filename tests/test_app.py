"""End-to-end UI test using Streamlit's AppTest with a fake model (no Ollama needed)."""
from pathlib import Path

from streamlit.testing.v1 import AppTest

from placepal import storage

APP = str(Path(__file__).resolve().parent.parent / "app.py")
RESUME = (
    "Aakif Example. B.E. Computer Science. Projects: built a sales prediction web app with "
    "Python, scikit-learn and Flask; contributed to open-source Python projects. Skills: SQL, Git."
)
LONG_ANSWER = "A hash map stores values in buckets chosen by hashing the key and resolves collisions by chaining. " * 2


def test_full_interview_flow(fake_llm):
    at = AppTest.from_file(APP, default_timeout=30).run()
    assert not at.exception
    assert any("100% locally" in s.value for s in at.success)

    at.sidebar.text_area[0].set_value(RESUME)
    at.sidebar.button[0].click().run()
    assert not at.exception, at.exception
    assert len(at.text_area) >= 5  # five answer boxes

    for i in range(5):
        at.text_area(key=f"ans_{i}").set_value(LONG_ANSWER)
    for i in range(5):
        at.button(key=f"eval_{i}").click().run()
        assert not at.exception, at.exception

    assert any("Session average" in s.value for s in at.subheader)
    sessions = storage.load_sessions()
    assert len(sessions) == 1 and sessions[0]["avg_score"] == 8.0


def test_short_resume_is_rejected(fake_llm):
    at = AppTest.from_file(APP, default_timeout=30).run()
    at.sidebar.text_area[0].set_value("too short")
    at.sidebar.button[0].click().run()
    assert any("enough text" in e.value for e in at.error)


def test_non_local_host_shows_warning(fake_llm, monkeypatch):
    monkeypatch.setenv("OLLAMA_HOST", "http://203.0.113.9:11434")
    at = AppTest.from_file(APP, default_timeout=30).run()
    assert any("not this machine" in w.value for w in at.warning)
