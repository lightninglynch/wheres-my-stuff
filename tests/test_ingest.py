from __future__ import annotations

import unittest

from shared.ingest import parse_track_body


class ParseTrackBodyTests(unittest.TestCase):
    def test_normalizes_and_drops_unknown_neighbors(self):
        item, error = parse_track_body(
            {
                "object": "cell phone",
                "timestamp": "2026-09-12T21:20:00Z",
                "neighbors": ["lamp", "banana", "couch", "phone"],
            }
        )
        self.assertIsNone(error)
        self.assertEqual(item["object"], "phone")
        self.assertEqual(item["neighbors"], ["lamp", "couch"])

    def test_rejects_unknown_object(self):
        item, error = parse_track_body(
            {"object": "couch", "timestamp": "2026-09-12T21:20:00Z"}
        )
        self.assertIsNone(item)
        self.assertIn("unknown", error)

    def test_rejects_bad_timestamp(self):
        item, error = parse_track_body({"object": "wallet", "timestamp": "soon"})
        self.assertIsNone(item)
        self.assertIn("timestamp", error)

    def test_requires_object_and_timestamp(self):
        item, error = parse_track_body({"object": "wallet"})
        self.assertIsNone(item)
        self.assertIn("timestamp", error)


if __name__ == "__main__":
    unittest.main()
