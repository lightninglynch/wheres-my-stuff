from __future__ import annotations

import unittest

from shared.names import (
    canonicalize,
    canonicalize_tracked,
    parse_class_list,
    yolo_prompts,
)


class CanonicalizeTests(unittest.TestCase):
    def test_aliases(self):
        self.assertEqual(canonicalize("cell phone"), "phone")
        self.assertEqual(canonicalize("my iPhone"), "phone")
        self.assertEqual(canonicalize("key"), "keys")
        self.assertEqual(canonicalize("the TV remote"), "remote")
        self.assertEqual(canonicalize("phone charger"), "charger")

    def test_unknown_returns_none(self):
        self.assertIsNone(canonicalize("banana"))
        self.assertIsNone(canonicalize(""))
        self.assertIsNone(canonicalize(None))

    def test_tracked_rejects_landmarks(self):
        self.assertEqual(canonicalize("lamp"), "lamp")
        self.assertIsNone(canonicalize_tracked("lamp"))
        self.assertEqual(canonicalize_tracked("wallet"), "wallet")

    def test_parse_class_list(self):
        self.assertEqual(
            parse_class_list("phone, key, banana", ("wallet",)),
            ("phone", "keys"),
        )
        self.assertEqual(parse_class_list("  ", ("wallet",)), ("wallet",))

    def test_yolo_prompts_are_unique(self):
        prompts = yolo_prompts(("phone", "keys"), ("tv", "lamp"))
        self.assertEqual(len(prompts), len(set(prompts)))
        self.assertIn("cell phone", prompts)
        self.assertIn("television", prompts)


if __name__ == "__main__":
    unittest.main()
