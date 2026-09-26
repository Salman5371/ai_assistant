import unittest
from assistant.normalization import normalize_command
from assistant.router import route


class NormalizationTests(unittest.TestCase):
    def test_aliases_case_and_punctuation(self):
        for raw, expected in [("  OPEN Chat G P T!!! ", "open chatgpt"), ("Shut Down computer", "shutdown computer"), ("open document folder", "open documents folder"), ("You Tube", "youtube")]:
            self.assertEqual(normalize_command(raw), expected)

    def test_payloads_are_not_normalized(self):
        self.assertEqual(route("remember Meet Alice at 5:30!").payload, "Meet Alice at 5:30!")
        self.assertEqual(route("check password Hello@123").payload, "Hello@123")
