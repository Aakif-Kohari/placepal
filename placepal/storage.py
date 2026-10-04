"""Local storage. Sessions live in a JSON file on this machine and nowhere else."""
from __future__ import annotations

import json
import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


def data_path() -> Path:
    """Where sessions are stored (override with PLACEPAL_DATA)."""
    return Path(os.environ.get("PLACEPAL_DATA", "data/sessions.json"))


def load_sessions(path: Optional[Path] = None) -> list[dict[str, Any]]:
    path = Path(path) if path else data_path()
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        # Keep the unreadable file for inspection instead of silently destroying it.
        try:
            path.replace(path.with_suffix(".corrupt"))
        except OSError:
            pass
        return []
    return data if isinstance(data, list) else []


def _write_atomic(path: Path, sessions: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(sessions, handle, indent=2, ensure_ascii=False)
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def new_session(role: str, difficulty: str, model: str, items: list[dict[str, Any]]) -> dict[str, Any]:
    scores = [item["score"] for item in items if "score" in item]
    return {
        "id": uuid.uuid4().hex[:8],
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "role": role,
        "difficulty": difficulty,
        "model": model,
        "items": items,
        "avg_score": round(sum(scores) / len(scores), 2) if scores else None,
    }


def save_session(session: dict[str, Any], path: Optional[Path] = None) -> None:
    path = Path(path) if path else data_path()
    sessions = load_sessions(path)
    sessions.append(session)
    _write_atomic(path, sessions)


def clear_sessions(path: Optional[Path] = None) -> None:
    path = Path(path) if path else data_path()
    if path.exists():
        path.unlink()
