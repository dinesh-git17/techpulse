#!/usr/bin/env python3
# pylint: disable=too-few-public-methods,duplicate-code
"""
Protocol Zero Content Scanner

Scans repository files for forbidden AI attribution patterns.
Exit codes: 0 (clean), 1 (violations found), 2 (script error)
"""

from __future__ import annotations

import os
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

    __slots__ = ("pattern", "regex", "description", "exceptions")

    def __init__(
        self,
        pattern: str,
        description: str,
        exceptions: list[str] | None = None,
    ) -> None:
        self.pattern = pattern
        self.description = description
        self.exceptions = exceptions or []
        self.regex = re.compile(pattern, re.IGNORECASE)


class AllowlistPattern:
    """A single allowlist pattern for legitimate code constructs."""

    __slots__ = ("pattern", "regex", "description")

    def __init__(self, pattern: str, description: str) -> None:
        self.pattern = pattern
        self.description = description
        self.regex = re.compile(pattern, re.IGNORECASE)


class Violation:
    """A detected policy violation with location and match details."""

    __slots__ = ("file_path", "line_number", "match_text", "rule_description")

    def __init__(
        self,
        file_path: str,
        line_number: int,
        match_text: str,
        rule_description: str,
    ) -> None:
        self.file_path = file_path
        self.line_number = line_number
        self.match_text = match_text
        self.rule_description = rule_description


class Config:
    """Scanner configuration with denylist rules and file filters."""

    __slots__ = (
        "denylist",
        "extensions_to_scan",
        "ignore_dirs",
        "allowlist_files",
        "allowlist_patterns",
    )

    def __init__(
        self,
        denylist: list[DenylistRule],
        extensions_to_scan: set[str],
        ignore_dirs: set[str],
        allowlist_files: set[str],
        allowlist_patterns: list[AllowlistPattern],
    ) -> None:
        self.denylist = denylist
        self.extensions_to_scan = extensions_to_scan
        self.ignore_dirs = ignore_dirs
        self.allowlist_files = allowlist_files
        self.allowlist_patterns = allowlist_patterns


def load_config(config_path: Path) -> Config:  # pylint: disable=too-many-locals
    """Load and parse the configuration file."""
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

    denylist: list[DenylistRule] = []
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
        exceptions = entry.get("exceptions", [])

        if not isinstance(exceptions, list):
            print(
                f"ERROR: Denylist entry {idx} 'exceptions' must be a list",
                file=sys.stderr,
            )
            sys.exit(EXIT_ERROR)

        try:
            rule = DenylistRule(pattern, str(description), exceptions)
            denylist.append(rule)
        except re.error as e:
            print(
                f"ERROR: Invalid regex in denylist entry {idx}: {e}",
                file=sys.stderr,
            )
            sys.exit(EXIT_ERROR)

    extensions_raw = raw_config.get("extensions_to_scan", [])
    if not isinstance(extensions_raw, list):
        print("ERROR: 'extensions_to_scan' must be a list", file=sys.stderr)
        sys.exit(EXIT_ERROR)
    extensions_to_scan = {str(ext) for ext in extensions_raw}

    ignore_dirs_raw = raw_config.get("ignore_dirs", [])
    if not isinstance(ignore_dirs_raw, list):
        print("ERROR: 'ignore_dirs' must be a list", file=sys.stderr)
        sys.exit(EXIT_ERROR)
    ignore_dirs = {str(d) for d in ignore_dirs_raw}

    allowlist_raw = raw_config.get("allowlist", {})
    if not isinstance(allowlist_raw, dict):
        print("ERROR: 'allowlist' must be a mapping", file=sys.stderr)
        sys.exit(EXIT_ERROR)
    allowlist_files_raw = allowlist_raw.get("files", [])
    if not isinstance(allowlist_files_raw, list):
        print("ERROR: 'allowlist.files' must be a list", file=sys.stderr)
        sys.exit(EXIT_ERROR)
    allowlist_files = {str(f) for f in allowlist_files_raw}

    allowlist_patterns_raw = allowlist_raw.get("patterns", [])
    if not isinstance(allowlist_patterns_raw, list):
        print("ERROR: 'allowlist.patterns' must be a list", file=sys.stderr)
        sys.exit(EXIT_ERROR)

    allowlist_patterns: list[AllowlistPattern] = []
    for idx, entry in enumerate(allowlist_patterns_raw):
        if not isinstance(entry, dict):
            print(
                f"ERROR: Allowlist pattern entry {idx} must be a mapping",
                file=sys.stderr,
            )
            sys.exit(EXIT_ERROR)

        pattern = entry.get("pattern")
        if not isinstance(pattern, str):
            print(
                f"ERROR: Allowlist pattern entry {idx} missing 'pattern' string",
                file=sys.stderr,
            )
            sys.exit(EXIT_ERROR)

        description = entry.get("description", "Unnamed allowlist pattern")

        try:
            allowlist_pattern = AllowlistPattern(pattern, str(description))
            allowlist_patterns.append(allowlist_pattern)
        except re.error as e:
            print(
                f"ERROR: Invalid regex in allowlist pattern entry {idx}: {e}",
                file=sys.stderr,
            )
            sys.exit(EXIT_ERROR)

    return Config(
        denylist, extensions_to_scan, ignore_dirs, allowlist_files, allowlist_patterns
    )


def normalize_text(text: str) -> str:
    """Apply NFKC normalization and lowercase for consistent matching."""
    return unicodedata.normalize("NFKC", text).lower()


def _is_allowlisted(line: str, allowlist_patterns: list[AllowlistPattern]) -> bool:
    """Check if line contains an allowlisted pattern."""
    normalized_line = normalize_text(line)
    for pattern in allowlist_patterns:
        if pattern.regex.search(normalized_line):
            return True
    return False


def scan_line(
    line: str,
    line_number: int,
    file_path: str,
    filename: str,
    rules: list[DenylistRule],
    allowlist_patterns: list[AllowlistPattern],
) -> list[Violation]:
    """Scan a single line for violations, reporting all matches."""
    violations: list[Violation] = []
    normalized_line = normalize_text(line)

    for rule in rules:
        if filename in rule.exceptions:
            continue

        for match in rule.regex.finditer(normalized_line):
            original_start = match.start()
            original_end = match.end()
            matched_text = line[original_start:original_end]

            if _is_allowlisted(line, allowlist_patterns):
                continue

            violations.append(
                Violation(
                    file_path=file_path,
                    line_number=line_number,
                    match_text=matched_text,
                    rule_description=rule.description,
                )
            )

    return violations


def scan_file(
    file_path: Path,
    relative_path: str,
    rules: list[DenylistRule],
    allowlist_patterns: list[AllowlistPattern],
) -> list[Violation]:
    """Scan a single file for violations."""
    violations: list[Violation] = []
    filename = file_path.name

    try:
        with file_path.open("r", encoding="utf-8") as f:
            for line_number, line in enumerate(f, start=1):
                line_violations = scan_line(
                    line.rstrip("\n\r"),
                    line_number,
                    relative_path,
                    filename,
                    rules,
                    allowlist_patterns,
                )
                violations.extend(line_violations)
    except UnicodeDecodeError:
        print(
            f"WARNING: Skipping file due to encoding error: {relative_path}",
            file=sys.stderr,
        )
    except OSError as e:
        print(
            f"WARNING: Skipping file due to read error: {relative_path} ({e})",
            file=sys.stderr,
        )

    return violations


def should_scan_file(file_path: Path, extensions: set[str]) -> bool:
    """Check if file should be scanned based on extension."""
    return file_path.suffix in extensions


def _should_ignore_dir(
    dir_name: str,
    dir_path: Path,
    root_path: Path,
    ignore_dirs: set[str],
) -> bool:
    """Check if directory should be ignored by name or relative path."""
    if dir_name in ignore_dirs:
        return True
    if dir_path.is_symlink():
        return True
    try:
        relative_dir = str(dir_path.relative_to(root_path))
        if relative_dir in ignore_dirs:
            return True
    except ValueError:
        pass
    return False


def walk_directory(
    root_path: Path,
    config: Config,
) -> list[Violation]:
    """Walk directory tree and scan matching files."""
    violations: list[Violation] = []

    for dirpath, dirnames, filenames in os.walk(root_path, followlinks=False):
        current_dir = Path(dirpath)

        dirnames[:] = [
            d
            for d in dirnames
            if not _should_ignore_dir(
                d, Path(dirpath, d), root_path, config.ignore_dirs
            )
        ]

        for filename in filenames:
            file_path = current_dir / filename

            if file_path.is_symlink():
                continue

            if not should_scan_file(file_path, config.extensions_to_scan):
                continue

            try:
                relative_path = str(file_path.relative_to(root_path))
            except ValueError:
                relative_path = str(file_path)

            if relative_path in config.allowlist_files:
                continue

            file_violations = scan_file(
                file_path, relative_path, config.denylist, config.allowlist_patterns
            )
            violations.extend(file_violations)

    return violations


def format_violation(violation: Violation) -> str:
    """Format a single violation for display."""
    return f"""[PROTOCOL ZERO VIOLATION]
------------------------------------------------------------
FILE:    {violation.file_path}
LINE:    {violation.line_number}
MATCH:   "{violation.match_text}"
RULE:    {violation.rule_description}
------------------------------------------------------------
Action: Remove the attribution and retry.
"""


def main() -> int:
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: scan_content.py <directory>", file=sys.stderr)
        return EXIT_ERROR

    target_dir = Path(sys.argv[1])

    if not target_dir.exists():
        print(f"ERROR: Directory does not exist: {target_dir}", file=sys.stderr)
        return EXIT_ERROR

    if not target_dir.is_dir():
        print(f"ERROR: Path is not a directory: {target_dir}", file=sys.stderr)
        return EXIT_ERROR

    script_dir = Path(__file__).parent.resolve()
    config_path = script_dir / "config.yaml"
    config = load_config(config_path)

    violations = walk_directory(target_dir.resolve(), config)

    if violations:
        for violation in violations:
            print(format_violation(violation))

        print(f"\nTotal violations found: {len(violations)}")
        return EXIT_VIOLATION

    print("Protocol Zero scan complete. No violations found.")
    return EXIT_SUCCESS


if __name__ == "__main__":
    sys.exit(main())
