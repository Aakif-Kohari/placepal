# PlacePal architecture

PlacePal is a small, dependency-light Streamlit app. The design goal is that the **model is a swappable, local component** and everything around it is deterministic and testable.

## Request flow

1. **Resume in.** `resume.py` extracts text from an uploaded PDF with `pypdf` (or takes pasted text) and rejects near-empty input.
2. **Prompt.** `prompts.build_question_prompt` combines the resume (truncated to 6,000 characters), the role's focus areas and the difficulty note.
3. **Local inference.** `llm.ask_json` sends the prompt to Ollama on localhost with `format="json"` and a low temperature.
4. **Defensive parsing.** `llm.extract_json` finds JSON inside markdown fences or surrounding chatter. `schema.parse_*` validates and normalises it. If anything is malformed, the model is told what was wrong and asked again (2 retries by default), then a clear `LLMError` is shown.
5. **Evaluate.** For each answer the model returns a score, strengths, gaps and an improved answer. `interview.cap_score_for_length` then caps the score of very short answers deterministically.
6. **Persist.** When all questions are evaluated the session is written atomically to `data/sessions.json`.
7. **Analyse.** `analytics.py` aggregates scores per topic tag and surfaces the weakest topics.

## Design decisions

- **Why Ollama?** It gives one stable local API for many open-weight models, so `PLACEPAL_MODEL` is the only thing that changes when you switch models.
- **Why validate model output?** Small models sometimes return fenced JSON, extra prose, scores like `"7/10"` or too few questions. Handling this in one place keeps the UI simple.
- **Why cap short-answer scores in code?** Prompts alone do not stop a small model from rewarding a one-liner. A deterministic rule does.
- **Why a JSON file instead of a database?** The data is tiny, human-readable and easy to delete. Writes are atomic (temp file + `os.replace`) and corrupt files are set aside rather than destroyed.
- **Why a `_chat` seam?** `llm._chat` is the only function that touches the network (localhost). Tests replace it with a fake.

## Extending

- **New role:** add an entry to `ROLES` in `prompts.py`.
- **Different model:** set `PLACEPAL_MODEL`.
- **Different backend** (llama.cpp server, vLLM): replace `_chat` in `llm.py`; nothing else changes.
