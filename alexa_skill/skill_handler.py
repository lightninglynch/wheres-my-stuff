"""Alexa skill Lambda: speak last-seen locations from DynamoDB."""

from __future__ import annotations

import os

from shared.names import CANONICAL_OBJECTS, canonicalize_tracked
from shared.speech import (
    HELP_SPEECH,
    LAUNCH_SPEECH,
    STOP_SPEECH,
    format_find_speech,
    format_list_speech,
    format_missing_speech,
)


def _get_table():
    table_name = os.environ.get("DYNAMODB_TABLE")
    if not table_name:
        return None
    import boto3

    return boto3.resource("dynamodb").Table(table_name)


def lambda_handler(event, context):
    skill_id = os.environ.get("ALEXA_SKILL_ID", "").strip()
    if skill_id:
        app_id = (
            event.get("context", {})
            .get("System", {})
            .get("application", {})
            .get("applicationId")
            or event.get("session", {})
            .get("application", {})
            .get("applicationId")
        )
        if app_id and app_id != skill_id:
            raise PermissionError("Invalid Alexa application ID")

    request = event.get("request") or {}
    request_type = request.get("type")

    if request_type == "LaunchRequest":
        return _alexa_response(LAUNCH_SPEECH, should_end=False)
    if request_type == "SessionEndedRequest":
        return {"version": "1.0", "response": {}}
    if request_type != "IntentRequest":
        return _alexa_response("Sorry, I didn't understand that.")

    intent_name = request.get("intent", {}).get("name")
    if intent_name == "FindObjectIntent":
        return _handle_find(request)
    if intent_name == "ListObjectsIntent":
        return _handle_list()
    if intent_name == "AMAZON.HelpIntent":
        return _alexa_response(HELP_SPEECH, should_end=False)
    if intent_name in ("AMAZON.StopIntent", "AMAZON.CancelIntent"):
        return _alexa_response(STOP_SPEECH)
    return _alexa_response(HELP_SPEECH, should_end=False)


def slot_object(request: dict) -> str | None:
    slot = (request.get("intent") or {}).get("slots", {}).get("object") or {}
    resolutions = slot.get("resolutions", {}).get("resolutionsPerAuthority", [])
    for authority in resolutions:
        if authority.get("status", {}).get("code") == "ER_SUCCESS_MATCH":
            values = authority.get("values") or []
            if values:
                return canonicalize_tracked(values[0].get("value", {}).get("name"))
    return canonicalize_tracked(slot.get("value"))


def _handle_find(request: dict) -> dict:
    obj = slot_object(request)
    if not obj:
        options = ", ".join(CANONICAL_OBJECTS[:-1]) + f", or {CANONICAL_OBJECTS[-1]}"
        return _alexa_response(
            f"What should I look for? I can find {options}.",
            should_end=False,
        )
    table = _get_table()
    if table is None:
        return _alexa_response("I can't reach the location table right now.")

    resp = table.get_item(Key={"object": obj})
    item = resp.get("Item")
    if not item:
        return _alexa_response(format_missing_speech(obj))
    neighbors = list(item.get("neighbors") or [])
    return _alexa_response(
        format_find_speech(obj, str(item.get("timestamp", "")), neighbors)
    )


def _handle_list() -> dict:
    table = _get_table()
    if table is None:
        return _alexa_response("I can't reach the location table right now.")
    resp = table.scan(Limit=50)
    allowed = set(CANONICAL_OBJECTS)
    items = [
        row
        for row in (resp.get("Items") or [])
        if row.get("object") in allowed
    ]
    items.sort(key=lambda row: str(row.get("timestamp", "")), reverse=True)
    return _alexa_response(format_list_speech(items))


def _alexa_response(text: str, should_end: bool = True) -> dict:
    return {
        "version": "1.0",
        "response": {
            "outputSpeech": {"type": "PlainText", "text": text},
            "shouldEndSession": should_end,
        },
    }
