from __future__ import annotations

import os
import unittest

from alexa_skill.skill_handler import lambda_handler, slot_object
from shared.speech import HELP_SPEECH, LAUNCH_SPEECH, STOP_SPEECH


class SlotObjectTests(unittest.TestCase):
    def test_uses_resolution_match(self):
        request = {
            "intent": {
                "slots": {
                    "object": {
                        "value": "iphone",
                        "resolutions": {
                            "resolutionsPerAuthority": [
                                {
                                    "status": {"code": "ER_SUCCESS_MATCH"},
                                    "values": [{"value": {"name": "phone"}}],
                                }
                            ]
                        },
                    }
                }
            }
        }
        self.assertEqual(slot_object(request), "phone")

    def test_falls_back_to_spoken_value(self):
        request = {"intent": {"slots": {"object": {"value": "my keys"}}}}
        self.assertEqual(slot_object(request), "keys")

    def test_missing_slot(self):
        self.assertIsNone(slot_object({"intent": {"slots": {}}}))


class AlexaHandlerTests(unittest.TestCase):
    def test_launch(self):
        event = {"request": {"type": "LaunchRequest"}}
        resp = lambda_handler(event, None)
        self.assertEqual(resp["response"]["outputSpeech"]["text"], LAUNCH_SPEECH)
        self.assertFalse(resp["response"]["shouldEndSession"])

    def test_help_stop_cancel(self):
        help_resp = lambda_handler(
            {"request": {"type": "IntentRequest", "intent": {"name": "AMAZON.HelpIntent"}}},
            None,
        )
        self.assertEqual(help_resp["response"]["outputSpeech"]["text"], HELP_SPEECH)
        stop_resp = lambda_handler(
            {"request": {"type": "IntentRequest", "intent": {"name": "AMAZON.StopIntent"}}},
            None,
        )
        self.assertEqual(stop_resp["response"]["outputSpeech"]["text"], STOP_SPEECH)

    def test_rejects_wrong_skill_id(self):
        os.environ["ALEXA_SKILL_ID"] = "amzn1.ask.skill.expected"
        try:
            with self.assertRaises(PermissionError):
                lambda_handler(
                    {
                        "session": {
                            "application": {"applicationId": "amzn1.ask.skill.other"}
                        },
                        "request": {"type": "LaunchRequest"},
                    },
                    None,
                )
        finally:
            os.environ.pop("ALEXA_SKILL_ID", None)

    def test_find_without_slot_prompts(self):
        resp = lambda_handler(
            {
                "request": {
                    "type": "IntentRequest",
                    "intent": {"name": "FindObjectIntent", "slots": {}},
                }
            },
            None,
        )
        self.assertIn("What should I look for", resp["response"]["outputSpeech"]["text"])
        self.assertFalse(resp["response"]["shouldEndSession"])


if __name__ == "__main__":
    unittest.main()
