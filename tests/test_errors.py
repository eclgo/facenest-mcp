# -*- coding: utf-8 -*-
"""Error text must be actionable: code -> meaning -> next action -> retry?."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from facenest_mcp import errors  # noqa: E402


class ErrorTextTest(unittest.TestCase):
    def test_read_only_style(self):
        text = errors.format("ERR_MCP_WRITE_OFF", "写入未开启", 403)
        self.assertIn("ERR_MCP_WRITE_OFF", text)
        self.assertIn("HTTP 403", text)
        self.assertIn("Do next:", text)
        self.assertIn("Retry: NO", text)
        self.assertIn("Allow writes", text)
        self.assertIn("写入未开启", text)

    def test_pro_is_not_retryable(self):
        text = errors.format("ERR_PRO_REQUIRED", "", 402)
        self.assertIn("Retry: NO", text)
        self.assertIn("Pro", text)

    def test_session_limit_mentions_reset(self):
        text = errors.format("ERR_MCP_SESSION_LIMIT", "", 429)
        self.assertIn("reset the token", text)

    def test_smart_rules_point_to_enums(self):
        text = errors.format("ERR_SMART_DATE_FORMAT", "bad date", 400)
        self.assertIn("person{", text)
        self.assertIn("last_days", text)
        self.assertIn("Retry: YES", text)

    def test_unknown_code_is_safe(self):
        text = errors.format("ERR_TOTALLY_NEW", "boom", 500)
        self.assertIn("ERR_TOTALLY_NEW", text)
        self.assertIn("stop and tell the user", text)

    def test_smart_album_not_found_is_not_a_rule_error(self):
        """A missing album is not a broken rule - `Do next` must point at facenest_list_smart_albums."""
        text = errors.format("ERR_SMART_NOT_FOUND", "智能相册不存在", 404)
        self.assertIn("does not exist", text)
        self.assertIn("facenest_list_smart_albums", text)
        self.assertNotIn("rule set is invalid", text)

    def test_bad_args_is_retryable(self):
        text = errors.format("ERR_BAD_ARGS", "`limit`=500 is out of range 1..200", 400)
        self.assertIn("ERR_BAD_ARGS", text)
        self.assertIn("Retry: YES", text)
        self.assertIn("out of range", text)

    def test_every_hint_has_three_parts(self):
        for code, (meaning, action, retry) in errors.HINTS.items():
            self.assertTrue(meaning, code)
            self.assertTrue(action, code)
            self.assertIsInstance(retry, bool, code)


if __name__ == "__main__":
    unittest.main()
