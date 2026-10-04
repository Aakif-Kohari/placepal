"""Progress analytics across saved practice sessions."""
from __future__ import annotations

from collections import defaultdict
from typing import Any


def topic_scores(sessions: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    """Average score and attempt count for every topic tag."""
    buckets: dict[str, list[int]] = defaultdict(list)
    for session in sessions:
        for item in session.get("items", []):
            if "score" in item:
                buckets[item.get("topic") or "General"].append(item["score"])
    return {
        topic: {"average": round(sum(scores) / len(scores), 2), "attempts": len(scores)}
        for topic, scores in buckets.items()
    }


def weakest_topics(sessions: list[dict[str, Any]], limit: int = 3) -> list[tuple[str, float]]:
    """Topics with the lowest average score, weakest first."""
    ranked = sorted(topic_scores(sessions).items(), key=lambda kv: (kv[1]["average"], -kv[1]["attempts"]))
    return [(topic, stats["average"]) for topic, stats in ranked[:limit]]


def score_trend(sessions: list[dict[str, Any]]) -> list[tuple[str, float]]:
    """(timestamp, average score) per session, oldest first."""
    points = [(s["created_at"], s["avg_score"]) for s in sessions if s.get("avg_score") is not None]
    return sorted(points)
