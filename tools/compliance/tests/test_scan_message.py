# pylint: disable=import-error,wrong-import-position,import-outside-toplevel,missing-function-docstring
"""
Unit tests for scan_message.py
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from scan_message import (
    DenylistRule,
    Violation,
    format_violation,
    is_comment_line,
    normalize_text,
    scan_commit_message,
    scan_line,
)


class TestNormalizeText(unittest.TestCase):
    """Tests for NFKC normalization and lowercasing."""

    def test_lowercase_conversion(self) -> None:
        self.assertEqual(normalize_text("ChatGPT"), "chatgpt")

    def test_unicode_normalization(self) -> None:
        fullwidth_a = "\uff21"
        self.assertEqual(normalize_text(fullwidth_a), "a")


class TestIsCommentLine(unittest.TestCase):
    """Tests for git comment line detection."""

    def test_comment_line_detected(self) -> None:
        self.assertTrue(is_comment_line("# This is a comment"))

    def test_comment_with_leading_space(self) -> None:
        self.assertTrue(is_comment_line("  # Indented comment"))

    def test_regular_line_not_comment(self) -> None:
        self.assertFalse(is_comment_line("feat: add feature"))

    def test_hash_in_middle_not_comment(self) -> None:
        self.assertFalse(is_comment_line("fix: resolve issue #123"))


class TestDenylistRule(unittest.TestCase):
    """Tests for DenylistRule class."""

    def test_basic_pattern(self) -> None:
        rule = DenylistRule(r"\bchatgpt\b", "Test rule")
        self.assertIsNotNone(rule.regex.search("chatgpt"))

    def test_case_insensitive(self) -> None:
        rule = DenylistRule(r"\bchatgpt\b", "Test rule")
        self.assertIsNotNone(rule.regex.search("ChatGPT"))


class TestScanLine(unittest.TestCase):
    """Tests for line scanning functionality."""

    def setUp(self) -> None:
        self.rules = [
            DenylistRule(r"\bchatgpt\b", "ChatGPT reference"),
            DenylistRule(r"\bopenai\b", "OpenAI reference"),
        ]

    def test_detects_violation(self) -> None:
        violations = scan_line("Used ChatGPT for this", 1, self.rules)
        self.assertEqual(len(violations), 1)

    def test_no_violation_clean_line(self) -> None:
        violations = scan_line("Clean commit message", 1, self.rules)
        self.assertEqual(len(violations), 0)

    def test_multiple_violations(self) -> None:
        violations = scan_line("ChatGPT and OpenAI mentioned", 1, self.rules)
        self.assertEqual(len(violations), 2)


class TestScanCommitMessage(unittest.TestCase):
    """Tests for commit message scanning."""

    def setUp(self) -> None:
        self.rules = [
            DenylistRule(r"\bchatgpt\b", "ChatGPT reference"),
            DenylistRule(r"\bai\s+assisted\b", "AI assisted reference"),
        ]

    def test_detects_violation_in_message(self) -> None:
        message = "feat: add feature\n\nUsed ChatGPT for implementation"
        violations = scan_commit_message(message, self.rules)
        self.assertEqual(len(violations), 1)

    def test_clean_message_no_violations(self) -> None:
        message = "feat: add authentication\n\nImplement JWT-based auth"
        violations = scan_commit_message(message, self.rules)
        self.assertEqual(len(violations), 0)

    def test_ignores_comment_lines(self) -> None:
        message = "feat: add feature\n# ChatGPT generated\n\nClean body"
        violations = scan_commit_message(message, self.rules)
        self.assertEqual(len(violations), 0)

    def test_multiline_violations(self) -> None:
        message = "ChatGPT feature\n\nAI assisted implementation"
        violations = scan_commit_message(message, self.rules)
        self.assertEqual(len(violations), 2)


class TestFormatViolation(unittest.TestCase):
    """Tests for violation formatting."""

    def test_format_contains_all_fields(self) -> None:
        violation = Violation(
            line_number=2,
            match_text="ChatGPT",
            rule_description="Test rule",
            line_content="Used ChatGPT",
        )
        formatted = format_violation(violation)

        self.assertIn("2", formatted)
        self.assertIn("ChatGPT", formatted)
        self.assertIn("Test rule", formatted)


class TestCommitMessageViolationFixture(unittest.TestCase):
    """Integration tests using commit message violation fixture."""

    def test_fixture_has_violations(self) -> None:
        fixture_path = (
            Path(__file__).parent / "fixtures" / "commit_message_violation.txt"
        )
        if not fixture_path.exists():
            self.skipTest("Commit message fixture not found")

        rules = [
            DenylistRule(r"\bchatgpt\b", "ChatGPT reference"),
            DenylistRule(r"\bclaude\b", "Claude reference"),
            DenylistRule(r"\bai\s+assisted\b", "AI assisted reference"),
        ]

        content = fixture_path.read_text(encoding="utf-8")
        violations = scan_commit_message(content, rules)
        self.assertGreater(len(violations), 0)


class TestMainFunction(unittest.TestCase):
    """Tests for main entry point."""

    def test_missing_argument_returns_error(self) -> None:
        from scan_message import main

        with patch.object(sys, "argv", ["scan_message.py"]):
            result = main()
        self.assertEqual(result, 2)

    def test_nonexistent_file_returns_error(self) -> None:
        from scan_message import main

        with patch.object(sys, "argv", ["scan_message.py", "/nonexistent/file.txt"]):
            result = main()
        self.assertEqual(result, 2)

    def test_clean_message_returns_success(self) -> None:
        from scan_message import main

        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".txt",
            delete=False,
            encoding="utf-8",
        ) as f:
            f.write("feat: add user authentication\n\nClean commit message")
            temp_path = Path(f.name)

        try:
            with patch.object(sys, "argv", ["scan_message.py", str(temp_path)]):
                result = main()
            self.assertEqual(result, 0)
        finally:
            temp_path.unlink()

    def test_violation_returns_failure(self) -> None:
        from scan_message import main

        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".txt",
            delete=False,
            encoding="utf-8",
        ) as f:
            f.write("feat: add feature with ChatGPT")
            temp_path = Path(f.name)

        try:
            with patch.object(sys, "argv", ["scan_message.py", str(temp_path)]):
                result = main()
            self.assertEqual(result, 1)
        finally:
            temp_path.unlink()


if __name__ == "__main__":
    unittest.main()
