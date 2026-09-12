from __future__ import annotations

import unittest
from datetime import datetime, timezone

from shared.speech import (
    format_find_speech,
    format_list_speech,
    format_missing_speech,
    format_relative_time,
    join_with_and,
    near_phrase,
)


class SpeechTests(unittest.TestCase):
    def test_join_with_and(self):
        self.assertEqual(join_with_and([]), "")
        self.assertEqual(join_with_and(["lamp"]), "lamp")
        self.assertEqual(join_with_and(["lamp", "couch"]), "lamp and couch")
        self.assertEqual(
            join_with_and(["lamp", "couch", "table"]),
            "lamp, couch, and table",
        )

    def test_near_phrase(self):
        self.assertEqual(near_phrase([]), "")
        self.assertEqual(near_phrase(["lamp"]), "the lamp")
        self.assertEqual(near_phrase(["lamp", "couch"]), "the lamp and the couch")

    def test_relative_time(self):
        now = datetime(2026, 9, 12, 21, 30, tzinfo=timezone.utc)
        self.assertEqual(
            format_relative_time("2026-09-12T21:29:50Z", now=now),
            "just now",
        )
        self.assertEqual(
            format_relative_time("2026-09-12T21:20:00Z", now=now),
            "about 10 minutes ago",
        )
        self.assertEqual(
            format_relative_time("2026-09-12T19:30:00Z", now=now),
            "about 2 hours ago",
        )
        self.assertEqual(
            format_relative_time("2026-09-11T21:30:00Z", now=now),
            "yesterday",
        )

    def test_find_and_missing_speech(self):
        speech = format_find_speech(
            "phone",
            "2026-09-12T21:20:00Z",
            ["lamp"],
        )
        self.assertIn("your phone near the lamp", speech)
        missing = format_missing_speech("keys")
        self.assertIn("haven't seen your keys", missing)
        self.assertIn("wallet", missing)

    def test_list_speech_empty(self):
        self.assertEqual(
            format_list_speech([]),
            "I haven't seen any of your things yet.",
        )

    def test_list_speech_with_items(self):
        speech = format_list_speech(
            [
                {"object": "phone", "timestamp": "2026-09-12T21:20:00Z"},
                {"object": "wallet", "timestamp": "2026-09-12T19:30:00Z"},
            ]
        )
        self.assertIn("your phone", speech)
        self.assertIn("your wallet", speech)


if __name__ == "__main__":
    unittest.main()
