"""Tests for the workflow logging helper."""
from __future__ import annotations

import logging
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from workflow.log_setup import _SESSION_HANDLERS, get_logger, truncate_for_log


class TruncateForLogTests(unittest.TestCase):
    def test_short_content_passes_through(self):
        self.assertEqual(truncate_for_log("hello"), "hello")

    def test_empty_content_passes_through(self):
        self.assertEqual(truncate_for_log(""), "")

    def test_long_content_is_truncated_with_marker(self):
        body = "x" * 5000
        out = truncate_for_log(body, limit=200)
        self.assertLess(len(out), len(body))
        self.assertIn("[truncated", out)
        # head + tail are preserved so JSON head/tail debugging still works
        self.assertTrue(out.startswith("x" * 100))
        self.assertTrue(out.rstrip().endswith("x" * 100))

    def test_raw_env_disables_truncation(self):
        body = "y" * 5000
        with patch.dict(os.environ, {"RICER_LOG_RAW": "1"}):
            self.assertEqual(truncate_for_log(body, limit=200), body)


class GetLoggerTests(unittest.TestCase):
    def setUp(self):
        # Clear cached handlers between tests so each one gets a fresh
        # session-file handler. Loggers themselves are also reset so the
        # handler-dedup tag check stays meaningful.
        _SESSION_HANDLERS.clear()
        for name in list(logging.Logger.manager.loggerDict):
            if name.startswith("ricer."):
                logging.Logger.manager.loggerDict.pop(name, None)

    def test_logger_attaches_console_handler_only_without_state(self):
        log = get_logger("unit-test")
        console_handlers = [h for h in log.handlers if isinstance(h, logging.StreamHandler)
                            and not isinstance(h, logging.FileHandler)]
        file_handlers = [h for h in log.handlers if isinstance(h, logging.FileHandler)]
        self.assertEqual(len(console_handlers), 1)
        self.assertEqual(file_handlers, [])

    def test_logger_does_not_duplicate_console_handler_on_second_call(self):
        log_a = get_logger("dedup")
        log_b = get_logger("dedup")
        self.assertIs(log_a, log_b)
        console_handlers = [h for h in log_a.handlers if getattr(h, "_ricer_console", False)]
        self.assertEqual(len(console_handlers), 1)

    def test_logger_writes_to_session_file_when_session_dir_present(self):
        with tempfile.TemporaryDirectory() as td:
            state = {"session_dir": td}
            log = get_logger("session-test", state)
            log.debug("disk-write check")
            for h in log.handlers:
                h.flush()
            log_path = Path(td) / "workflow.log"
            self.assertTrue(log_path.exists(), "workflow.log was not created")
            contents = log_path.read_text(encoding="utf-8")
            self.assertIn("disk-write check", contents)
            self.assertIn("ricer.session-test", contents)

    def test_off_disables_file_handler(self):
        with tempfile.TemporaryDirectory() as td:
            state = {"session_dir": td}
            with patch.dict(os.environ, {"RICER_LOG_FILE": "OFF"}):
                log = get_logger("off-test", state)
            file_handlers = [h for h in log.handlers if isinstance(h, logging.FileHandler)]
            self.assertEqual(file_handlers, [])
            self.assertFalse((Path(td) / "workflow.log").exists())


if __name__ == "__main__":
    unittest.main()
