# alexa_skill/skill_handler.py
import json
import os
import boto3

dynamodb = boto3.resource("dynamodb")
TABLE    = os.environ["DYNAMODB_TABLE"]
table    = dynamodb.Table(TABLE)

def lambda_handler(event, context):
    intent = event["request"]["intent"]["name"]
    if intent != "FindObjectIntent":
        return _alexa_response("Sorry, I can only find objects right now.")

    obj = event["request"]["intent"]["slots"]["object"]["value"]
    resp = table.get_item(Key={"object": obj})

    if "Item" not in resp:
        speech = f"I haven't seen your {obj} yet."
    else:
        item = resp["Item"]
        ts   = item["timestamp"]
        nbrs = item.get("neighbors", [])

        if nbrs:
            if len(nbrs) == 1:
                near_str = nbrs[0]
            else:
                near_str = " and ".join([", ".join(nbrs[:-1]), nbrs[-1]])
            speech = (f"I last saw your {obj} near {near_str} "
                      f"at {ts} UTC.")
        else:
            speech = f"I last saw your {obj} at {ts} UTC."

    return _alexa_response(speech)

def _alexa_response(text):
    return {
      "version": "1.0",
      "response": {
        "outputSpeech": {
          "type": "PlainText",
          "text": text
        },
        "shouldEndSession": True
      }
    }
