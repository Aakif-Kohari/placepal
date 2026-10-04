"""PlacePal - an offline mock-interview coach for campus placements.

Run with:  streamlit run app.py
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from placepal import analytics, interview, llm, prompts, resume, storage

st.set_page_config(page_title="PlacePal", page_icon="🎯", layout="wide")

DIFFICULTIES = ["Easy", "Medium", "Hard"]
NUM_QUESTIONS = 5


def reset_interview() -> None:
    """Forget the current interview, including the answer boxes."""
    for key in list(st.session_state.keys()):
        if key.startswith("ans_"):
            del st.session_state[key]
    st.session_state.update(questions=[], evals={}, saved=False)


def privacy_badge() -> None:
    if llm.is_local_host():
        st.success(
            f"🔒 Running 100% locally with `{llm.get_model()}`. "
            "Your resume and answers never leave this laptop."
        )
    else:
        st.warning(
            f"⚠️ OLLAMA_HOST points to `{llm.get_host()}`, which is not this machine. "
            "Your data is being sent to that server."
        )


def start_interview(role: str, difficulty: str, uploaded, pasted: str) -> None:
    """Read the resume, then ask the local model for questions."""
    try:
        text = resume.extract_text_from_pdf(uploaded) if uploaded else pasted
    except Exception:  # noqa: BLE001 - a corrupt PDF should give a friendly message
        st.error("Could not read that PDF. Try another file or paste your resume text instead.")
        return
    text = resume.clean_text(text or "")
    if not resume.is_usable(text):
        st.error(
            "I could not find enough text in your resume. If the PDF is a scan, "
            "paste the text into the box instead."
        )
        return
    reset_interview()
    with st.spinner(f"{llm.get_model()} is reading your resume and writing questions..."):
        try:
            questions = interview.generate_questions(text, role, difficulty, NUM_QUESTIONS)
        except llm.LLMError as exc:
            st.error(str(exc))
            return
    st.session_state.update(questions=questions, role=role, difficulty=difficulty)


def render_result(result: dict) -> None:
    st.metric("Score", f"{result['score']}/10")
    left, right = st.columns(2)
    with left:
        st.markdown("**What worked**")
        for point in result["strengths"] or ["Nothing stood out yet."]:
            st.markdown(f"- {point}")
    with right:
        st.markdown("**What to improve**")
        for point in result["gaps"] or ["No major gaps noted."]:
            st.markdown(f"- {point}")
    if result["improved_answer"]:
        with st.expander("See a stronger answer"):
            st.write(result["improved_answer"])


def interview_tab() -> None:
    questions = st.session_state.get("questions") or []
    if not questions:
        st.info(
            "Upload your resume (or paste its text) in the sidebar, pick a role and "
            "press **Start interview**."
        )
        return

    role = st.session_state["role"]
    difficulty = st.session_state["difficulty"]
    st.caption(f"{role} · {difficulty} · {len(questions)} questions")

    for index, question in enumerate(questions):
        with st.container(border=True):
            st.markdown(f"**Q{index + 1}.** {question['question']}")
            st.caption(f"{question['type'].title()} · {question['topic']}")
            st.text_area(
                "Your answer",
                key=f"ans_{index}",
                height=140,
                label_visibility="collapsed",
                placeholder="Answer out loud in your head first, then type it as you would say it.",
            )
            if st.button("Evaluate", key=f"eval_{index}"):
                answer = st.session_state.get(f"ans_{index}", "")
                try:
                    with st.spinner("Evaluating..."):
                        result = interview.evaluate_answer(question, answer, role, difficulty)
                    st.session_state["evals"][index] = result
                except ValueError as exc:
                    st.warning(str(exc))
                except llm.LLMError as exc:
                    st.error(str(exc))
            result = st.session_state["evals"].get(index)
            if result:
                render_result(result)

    evals = st.session_state["evals"]
    if len(evals) == len(questions):
        average = sum(e["score"] for e in evals.values()) / len(evals)
        st.divider()
        st.subheader(f"Session average: {average:.1f}/10")
        if not st.session_state.get("saved"):
            items = [
                {**questions[i], "answer": st.session_state.get(f"ans_{i}", ""), **evals[i]}
                for i in range(len(questions))
            ]
            storage.save_session(storage.new_session(role, difficulty, llm.get_model(), items))
            st.session_state["saved"] = True
        st.success("Session saved on this machine. Check the Progress tab for weak topics.")


def progress_tab() -> None:
    sessions = storage.load_sessions()
    if not sessions:
        st.info("No finished sessions yet. Complete an interview and your progress shows up here.")
        return

    scored = [s["avg_score"] for s in sessions if s.get("avg_score") is not None]
    col1, col2, col3 = st.columns(3)
    col1.metric("Sessions", len(sessions))
    col2.metric("Average score", f"{sum(scored) / len(scored):.1f}/10" if scored else "-")
    col3.metric("Best session", f"{max(scored):.1f}/10" if scored else "-")

    topics = analytics.topic_scores(sessions)
    st.subheader("Average score by topic")
    frame = pd.DataFrame(
        {"Average score": [v["average"] for v in topics.values()]}, index=list(topics.keys())
    )
    st.bar_chart(frame)

    st.subheader("Weakest topics to revise")
    for topic, average in analytics.weakest_topics(sessions, limit=3):
        st.markdown(f"- **{topic}**: {average}/10")

    st.subheader("History")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "When (UTC)": s["created_at"],
                    "Role": s["role"],
                    "Difficulty": s["difficulty"],
                    "Model": s.get("model", ""),
                    "Average": s.get("avg_score"),
                }
                for s in reversed(sessions)
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )

    with st.expander("Delete my data"):
        confirm = st.checkbox("Yes, permanently delete all saved sessions from this machine")
        if st.button("Delete everything", disabled=not confirm):
            storage.clear_sessions()
            st.rerun()


def main() -> None:
    st.session_state.setdefault("questions", [])
    st.session_state.setdefault("evals", {})
    st.session_state.setdefault("saved", False)

    st.title("🎯 PlacePal")
    st.caption("An offline mock-interview partner for campus placements, powered by an open-weight model.")
    privacy_badge()

    with st.sidebar:
        st.header("Set up your interview")
        role = st.selectbox("Target role", list(prompts.ROLES.keys()))
        difficulty = st.select_slider("Difficulty", options=DIFFICULTIES, value="Medium")
        uploaded = st.file_uploader("Resume (PDF)", type=["pdf"])
        pasted = st.text_area("...or paste your resume text", height=160)
        start = st.button("Start interview", type="primary", use_container_width=True)
        st.caption(f"Model: `{llm.get_model()}` (change with PLACEPAL_MODEL)")

    if start:
        start_interview(role, difficulty, uploaded, pasted)

    tab_interview, tab_progress = st.tabs(["Interview", "Progress"])
    with tab_interview:
        interview_tab()
    with tab_progress:
        progress_tab()


main()
