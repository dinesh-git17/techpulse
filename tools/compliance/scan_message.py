#!/usr/bin/env python3
# pylint: disable=too-few-public-methods,duplicate-code
"""
Protocol Zero Commit Message Scanner

Validates commit messages against forbidden AI attribution patterns.
Exit codes: 0 (clean), 1 (violations found), 2 (script error)
"""

from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import TextIO

try:
    import yaml
except ImportError:

    class YAMLLoader:
        """Fallback YAML loader when PyYAML is unavailable."""

        @staticmethod
        def safe_load(stream: TextIO) -> dict[str, object]:
            """Raise error indicating PyYAML is required."""
            raise SystemExit(
                "ERROR: PyYAML not available and fallback not implemented.\n"
                "This script requires PyYAML or a config.json alternative."
            )

    yaml = YAMLLoader()


EXIT_SUCCESS = 0
EXIT_VIOLATION = 1
EXIT_ERROR = 2


class DenylistRule:
    """A single denylist rule with compiled regex pattern."""

    __slots__ = ("pattern", "regex", "description")

    def __init__(self, pattern: str, description: str) -> None:
        self.pattern = pattern
        self.description = description
        self.regex = re.compile(pattern, re.IGNORECASE)


class Violation:
    """A detected policy violation with line context."""

    __slots__ = ("line_number", "match_text", "rule_description", "line_content")

    def __init__(
        self,
        line_number: int,
        match_text: str,
        rule_description: str,
        line_content: str,
    ) -> None:
        self.line_number = line_number
        self.match_text = match_text
        self.rule_description = rule_description
        self.line_content = line_content


def load_denylist(config_path: Path) -> list[DenylistRule]:
    """Load denylist rules from configuration file."""
    if not config_path.exists():
        print(f"ERROR: Configuration file not found: {config_path}", file=sys.stderr)
        sys.exit(EXIT_ERROR)

    try:
        with config_path.open("r", encoding="utf-8") as f:
            raw_config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"ERROR: Malformed YAML in config file: {e}", file=sys.stderr)
        sys.exit(EXIT_ERROR)
    except OSError as e:
        print(f"ERROR: Cannot read config file: {e}", file=sys.stderr)
        sys.exit(EXIT_ERROR)

    if not isinstance(raw_config, dict):
        print("ERROR: Config file must contain a YAML mapping", file=sys.stderr)
        sys.exit(EXIT_ERROR)

    denylist_raw = raw_config.get("denylist", [])
    if not isinstance(denylist_raw, list):
        print("ERROR: 'denylist' must be a list", file=sys.stderr)
        sys.exit(EXIT_ERROR)

    rules: list[DenylistRule] = []
    for idx, entry in enumerate(denylist_raw):
        if not isinstance(entry, dict):
            print(f"ERROR: Denylist entry {idx} must be a mapping", file=sys.stderr)
            sys.exit(EXIT_ERROR)

        pattern = entry.get("pattern")
        if not isinstance(pattern, str):
            print(
                f"ERROR: Denylist entry {idx} missing 'pattern' string",
                file=sys.stderr,
            )
            sys.exit(EXIT_ERROR)

        description = entry.get("description", "Unnamed rule")

        try:
            rule = DenylistRule(pattern, str(description))
            rules.append(rule)
        except re.error as e:
            print(
                f"ERROR: Invalid regex in denylist entry {idx}: {e}",
                file=sys.stderr,
            )
            sys.exit(EXIT_ERROR)

    return rules


def normalize_text(text: str) -> str:
    """Apply NFKC normalization and lowercase for consistent matching."""
    return unicodedata.normalize("NFKC", text).lower()


def is_comment_line(line: str) -> bool:
    """Check if line is a git commit comment (starts with #)."""
    return line.lstrip().startswith("#")


def scan_line(
    line: str,
    line_number: int,
    rules: list[DenylistRule],
) -> list[Violation]:
    """Scan a single line for violations."""
    violations: list[Violation] = []
    normalized_line = normalize_text(line)

    for rule in rules:
        for match in rule.regex.finditer(normalized_line):
            original_start = match.start()
            original_end = match.end()
            matched_text = line[original_start:original_end]

            violations.append(
                Violation(
                    line_number=line_number,
                    match_text=matched_text,
                    rule_description=rule.description,
                    line_content=line.strip(),
                )
            )

    return violations


def scan_commit_message(content: str, rules: list[DenylistRule]) -> list[Violation]:
    """Scan commit message content for violations."""
    violations: list[Violation] = []
    lines = content.splitlines()

    for line_number, line in enumerate(lines, start=1):
        if is_comment_line(line):
            continue

        line_violations = scan_line(line, line_number, rules)
        violations.extend(line_violations)

    return violations


def format_violation(violation: Violation) -> str:
    """Format a single violation for display."""
    return f"""  Line {violation.line_number}: "{violation.match_text}"
    Rule: {violation.rule_description}
    Context: {violation.line_content}"""


def main() -> int:
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: scan_message.py <commit_message_file>", file=sys.stderr)
        return EXIT_ERROR

    message_file = Path(sys.argv[1])

    if not message_file.exists():
        print(f"ERROR: File does not exist: {message_file}", file=sys.stderr)
        return EXIT_ERROR

    if not message_file.is_file():
        print(f"ERROR: Path is not a file: {message_file}", file=sys.stderr)
        return EXIT_ERROR

    script_dir = Path(__file__).parent.resolve()
    config_path = script_dir / "config.yaml"
    rules = load_denylist(config_path)

    try:
        content = message_file.read_text(encoding="utf-8")
    except OSError as e:
        print(f"ERROR: Cannot read commit message file: {e}", file=sys.stderr)
        return EXIT_ERROR

    violations = scan_commit_message(content, rules)

    if violations:
        print("[PROTOCOL ZERO VIOLATION]")
        print("=" * 60)
        print("COMMIT REJECTED: AI attribution detected in commit message")
        print("=" * 60)
        print()
        print("Violations found:")
        for violation in violations:
            print(format_violation(violation))
            print()
        print("-" * 60)
        print("Action: Remove AI attribution references and retry commit.")
        return EXIT_VIOLATION

    return EXIT_SUCCESS


if __name__ == "__main__":
    sys.exit(main())
