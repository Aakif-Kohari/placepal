"""Thin wrapper around a local Ollama server.

PlacePal never talks to a hosted API. Every prompt goes to an open-weight model
served by Ollama on this machine. The model is chosen with the PLACEPAL_MODEL
environment variable, so swapping Gemma for Qwen, Llama, etc. is a one-line change.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any, Callable, Optional

DEFAULT_MODEL = "gemma3:4b"
DEFAULT_HOST = "http://127.0.0.1:11434"


class LLMError(RuntimeError):
    """Raised when the local model is unreachable or keeps returning unusable output."""


def get_model() -> str:
    """Model tag to use (override with PLACEPAL_MODEL)."""
    return os.environ.get("PLACEPAL_MODEL", "").strip() or DEFAULT_MODEL


def get_host() -> str:
    """Ollama server address (override with OLLAMA_HOST)."""
    return os.environ.get("OLLAMA_HOST", "").strip() or DEFAULT_HOST


def is_local_host(host: Optional[str] = None) -> bool:
    """True if the Ollama server address points at this machine."""
    host = (host or get_host()).strip()
    host = re.sub(r"^[a-zA-Z]+://", "", host).split("/")[0]
    if host.startswith("["):  # IPv6 literal, e.g. [::1]:11434
        name = host[1:].split("]")[0]
    else:
        name = host.split(":")[0]
    return name in {"", "localhost", "127.0.0.1", "0.0.0.0", "::1"}


def _chat(messages: list[dict[str, str]], model: str) -> str:
    """Send a chat request to Ollama and return the raw text reply.

    Kept as a small module-level function so tests can replace it with a fake.
    """
    try:
        import ollama
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise LLMError(
            "The 'ollama' Python package is not installed. Run: pip install -r requirements.txt"
        ) from exc

    try:
        response = ollama.chat(
            model=model,
            messages=messages,
            format="json",
            options={"temperature": 0.3},
        )
    except ollama.ResponseError as exc:
        if getattr(exc, "status_code", None) == 404:
            raise LLMError(
                f"Model '{model}' is not available locally. Run: ollama pull {model}"
            ) from exc
        raise LLMError(f"Ollama returned an error: {exc}") from exc
    except Exception as exc:  # connection refused, timeouts, ...
        raise LLMError(
            "Could not reach Ollama. Make sure it is running (open the Ollama app or run "
            "`ollama serve`) and that the model is pulled: "
            f"`ollama pull {model}`."
        ) from exc
    return response["message"]["content"]


_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


def extract_json(text: str) -> Any:
    """Pull the first JSON object/array out of a model reply.

    Small local models sometimes wrap JSON in markdown fences or add chatter,
    so we look for the first thing that parses instead of trusting the whole string.
    """
    if not text or not text.strip():
        raise ValueError("the reply was empty")
    match = _FENCE.search(text)
    candidate = match.group(1) if match else text
    decoder = json.JSONDecoder()
    for index, char in enumerate(candidate):
        if char in "{[":
            try:
                obj, _ = decoder.raw_decode(candidate[index:])
                return obj
            except json.JSONDecodeError:
                continue
    raise ValueError("no valid JSON found in the reply")


def ask_json(
    user_prompt: str,
    system: Optional[str] = None,
    validate: Optional[Callable[[Any], Any]] = None,
    retries: int = 2,
    model: Optional[str] = None,
) -> Any:
    """Ask the local model for JSON, validating and retrying on bad output."""
    model = model or get_model()
    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": user_prompt})

    last_error: Optional[Exception] = None
    for _ in range(retries + 1):
        raw = _chat(messages, model)
        try:
            data = extract_json(raw)
            return validate(data) if validate else data
        except (ValueError, TypeError, KeyError) as exc:
            last_error = exc
            messages = messages + [
                {"role": "assistant", "content": raw or ""},
                {
                    "role": "user",
                    "content": (
                        f"That reply was not usable ({exc}). Reply again with ONLY the JSON "
                        "object, in exactly the format requested."
                    ),
                },
            ]
    raise LLMError(
        f"The model did not return usable JSON after {retries + 1} attempts: {last_error}"
    )
