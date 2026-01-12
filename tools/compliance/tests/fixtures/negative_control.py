"""
Negative control file containing only safe patterns.
This file verifies the scanner does not produce false positives.
"""

from cryptography.hazmat.primitives import hashes


def encrypt_data(plaintext: bytes, _key: bytes) -> bytes:
    """Encrypt data using cryptographic primitives."""
    digest = hashes.Hash(hashes.SHA256())
    digest.update(plaintext)
    return digest.finalize()


ADAPTED_VALUE = 42
ADAPTABLE_CONFIG = {"mode": "adaptive"}


def get_adapted_results(data: list[int]) -> list[int]:
    """Return adapted results based on input."""
    return [x * 2 for x in data]


SCRIPT_VERSION = "1.0.0"
DESCRIPTION = "A helpful utility module"


def collaborate_on_task(participants: list[str]) -> str:
    """Coordinate collaboration between participants."""
    return ", ".join(participants)


ACCEPTED_FORMATS = ["json", "xml", "yaml"]


def pilot_program(users: list[str]) -> dict[str, bool]:
    """Manage pilot program enrollment."""
    return {user: True for user in users}


# Standard configuration
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3


def generate_report(data: dict[str, int]) -> str:
    """Generate a formatted report from data."""
    lines = [f"{k}: {v}" for k, v in data.items()]
    return "\n".join(lines)


# Exempt file patterns should not trigger
CLAUDE_SHANNON_ENTROPY = 2.5
ANTHROPIC_CONSTANT = 6.022e23
