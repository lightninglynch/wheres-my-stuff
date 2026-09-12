"""Validate detector track payloads before they are written to DynamoDB."""

from __future__ import annotations

from datetime import datetime

from shared.names import canonicalize, canonicalize_tracked


def parse_track_body(body: dict) -> tuple[dict | None, str | None]:
    """Validate and normalize a track payload. Returns (item, error)."""
    if not isinstance(body, dict):
        return None, "JSON object required"

    obj = canonicalize_tracked(body.get("object"))
    if not obj:
        return None, "unknown or missing object"

    ts = body.get("timestamp")
    if not ts or not isinstance(ts, str):
        return None, "object and timestamp required"
    try:
        parsed = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None, "timestamp must be ISO-8601"
    if parsed.tzinfo is None:
        ts = ts + "Z"

    raw_neighbors = body.get("neighbors", [])
    if raw_neighbors is None:
        raw_neighbors = []
    if not isinstance(raw_neighbors, list):
        return None, "neighbors must be a list"

    neighbors = []
    seen = set()
    for raw in raw_neighbors:
        name = canonicalize(raw) if isinstance(raw, str) else None
        if name and name != obj and name not in seen:
            neighbors.append(name)
            seen.add(name)

    return {"object": obj, "timestamp": ts, "neighbors": neighbors}, None
