# aws_backend/function.py
import json
import os
import boto3

dynamodb = boto3.resource("dynamodb")
TABLE    = os.environ["DYNAMODB_TABLE"]  # e.g. "ObjectLocations"
table    = dynamodb.Table(TABLE)

def handler(event, context):
    body = json.loads(event.get("body") or "{}")
    obj  = body.get("object")
    ts   = body.get("timestamp")
    nbrs = body.get("neighbors", [])

    if not obj or not ts:
        return {
          "statusCode": 400,
          "body": json.dumps({"error": "object & timestamp required"})
        }

    table.put_item(Item={
        "object":    obj,
        "timestamp": ts,
        "neighbors": nbrs
    })
    return {"statusCode": 200, "body": json.dumps({"status": "OK"})}
