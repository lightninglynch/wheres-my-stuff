"""HTTP ingest Lambda: store last-seen object locations in DynamoDB."""

from __future__ import annotations

import json
import os

import boto3

from shared.ingest import parse_track_body

dynamodb = boto3.resource("dynamodb")
_TABLE_NAME = os.environ.get("DYNAMODB_TABLE")
table = dynamodb.Table(_TABLE_NAME) if _TABLE_NAME else None


def _response(status: int, payload: dict) -> dict:
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(payload),
    }


def handler(event, context):
    if table is None:
        return _response(500, {"error": "DYNAMODB_TABLE is not configured"})

    try:
        body = json.loads(event.get("body") or "{}")
    except (TypeError, json.JSONDecodeError):
        return _response(400, {"error": "invalid JSON"})

    item, error = parse_track_body(body)
    if error:
        return _response(400, {"error": error})

    table.put_item(Item=item)
    return _response(200, {"status": "OK", "object": item["object"]})
