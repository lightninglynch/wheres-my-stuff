"""Spoken responses for the Alexa skill."""

from __future__ import annotations

from datetime import datetime, timezone

from shared.names import CANONICAL_OBJECTS


def join_with_and(items: list[str]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return f"{', '.join(items[:-1])}, and {items[-1]}"


def near_phrase(neighbors: list[str] | None) -> str:
    names = [n for n in (neighbors or []) if n]
    if not names:
        return ""
    labeled = [f"the {n}" for n in names]
    return join_with_and(labeled)


def format_relative_time(ts: str, now: datetime | None = None) -> str:
    try:
        then = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return "at an unknown time"
    if then.tzinfo is None:
        then = then.replace(tzinfo=timezone.utc)
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    seconds = int((now - then).total_seconds())
    if seconds < 0:
        seconds = 0
    if seconds < 45:
        return "just now"
    minutes = seconds // 60
    if minutes < 2:
        return "about a minute ago"
    if minutes < 60:
        return f"about {minutes} minutes ago"
    hours = minutes // 60
    if hours < 2:
        return "about an hour ago"
    if hours < 24:
        return f"about {hours} hours ago"
    days = hours // 24
    if days < 2:
        return "yesterday"
    if days < 14:
        return f"about {days} days ago"
    return then.strftime("on %B %d")


def format_find_speech(obj: str, timestamp: str, neighbors: list[str] | None) -> str:
    when = format_relative_time(timestamp)
    near = near_phrase(neighbors)
    if near:
        return f"I last saw your {obj} near {near}, {when}."
    return f"I last saw your {obj} {when}."


def format_missing_speech(obj: str) -> str:
    options = join_with_and(list(CANONICAL_OBJECTS))
    return (
        f"I haven't seen your {obj} yet. "
        f"I can look for {options}."
    )


def format_list_speech(items: list[dict]) -> str:
    if not items:
        return "I haven't seen any of your things yet."
    parts = []
    for item in items:
        obj = item.get("object", "something")
        when = format_relative_time(str(item.get("timestamp", "")))
        parts.append(f"your {obj}, {when}")
    return f"I've seen {join_with_and(parts)}."


LAUNCH_SPEECH = (
    "You can ask me where your phone or wallet is, "
    "or say what have you seen."
)

HELP_SPEECH = (
    "Ask where your wallet, keys, charger, phone, remote, glasses, "
    "or headphones are. You can also ask what I have seen."
)

STOP_SPEECH = "Okay."
