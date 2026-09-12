"""Canonical object names shared by the detector, ingest Lambda, and Alexa skill."""

from __future__ import annotations

CANONICAL_OBJECTS = (
    "wallet",
    "keys",
    "charger",
    "phone",
    "remote",
    "glasses",
    "headphones",
)

LANDMARKS = (
    "couch",
    "chair",
    "table",
    "lamp",
    "tv",
    "laptop",
    "bottle",
    "backpack",
)

KNOWN_CLASSES = frozenset(CANONICAL_OBJECTS) | frozenset(LANDMARKS)

# YOLO-World does better with a few descriptive prompts than with COCO ids.
_PROMPT_FOR = {
    "phone": "cell phone",
    "keys": "keys",
    "charger": "phone charger",
    "remote": "remote control",
    "glasses": "glasses",
    "headphones": "headphones",
    "wallet": "wallet",
    "tv": "television",
    "table": "table",
    "couch": "couch",
    "chair": "chair",
    "lamp": "lamp",
    "laptop": "laptop",
    "bottle": "bottle",
    "backpack": "backpack",
}

ALIASES = {
    "cell phone": "phone",
    "mobile": "phone",
    "iphone": "phone",
    "smartphone": "phone",
    "cellphone": "phone",
    "key": "keys",
    "house keys": "keys",
    "car keys": "keys",
    "phone charger": "charger",
    "cable": "charger",
    "charging cable": "charger",
    "power adapter": "charger",
    "remote control": "remote",
    "tv remote": "remote",
    "eyeglasses": "glasses",
    "spectacles": "glasses",
    "headset": "headphones",
    "earbuds": "headphones",
    "ear buds": "headphones",
    "airpods": "headphones",
    "television": "tv",
    "t.v.": "tv",
    "dining table": "table",
    "coffee table": "table",
    "sofa": "couch",
}


def parse_class_list(raw: str | None, fallback: tuple[str, ...]) -> tuple[str, ...]:
    if not raw or not raw.strip():
        return fallback
    items = []
    seen = set()
    for part in raw.split(","):
        name = canonicalize(part)
        if name and name not in seen:
            items.append(name)
            seen.add(name)
    return tuple(items) if items else fallback


def canonicalize(name: str | None) -> str | None:
    """Map a spoken or detected label to a known class, or None if unknown."""
    if not name:
        return None
    n = " ".join(str(name).strip().lower().split())
    for prefix in ("the ", "my ", "a ", "an "):
        if n.startswith(prefix):
            n = n[len(prefix) :]
            break
    n = n.rstrip(".")
    mapped = ALIASES.get(n, n)
    if mapped in KNOWN_CLASSES:
        return mapped
    return None


def canonicalize_tracked(name: str | None) -> str | None:
    """Like canonicalize, but only accepts objects we persist as last-seen items."""
    mapped = canonicalize(name)
    if mapped in CANONICAL_OBJECTS:
        return mapped
    return None


def yolo_prompts(tracked: tuple[str, ...], landmarks: tuple[str, ...]) -> list[str]:
    prompts = []
    seen = set()
    for cls in list(tracked) + list(landmarks):
        prompt = _PROMPT_FOR.get(cls, cls)
        if prompt not in seen:
            prompts.append(prompt)
            seen.add(prompt)
    return prompts
