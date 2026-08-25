#!/usr/bin/env python3
"""
PPT Master - Skill Attribution Guard

Fail closed when the Skill attribution bundle is missing or modified. Feature
modules may be installed selectively without failing this check.

Usage:
    python3 scripts/attribution_guard.py

Examples:
    python3 scripts/attribution_guard.py

Dependencies:
    None (only uses standard library)
"""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path


_ERROR_MESSAGE = (
    "PPT Master attribution check failed. Restore SKILL.md, LICENSE, "
    "SPONSORS.md, and SPONSORS_CN.md from the official distribution."
)
_SKILL_DIR = Path(__file__).resolve().parent.parent
_EXACT_METADATA_VALUES = {
    "copyright": '"Copyright (c) 2025-2026 Hugo He"',
    "license": '"MIT"',
    "official_repository": '"https://github.com/hugohe3/ppt-master"',
}
_REQUIRED_METADATA_FIELDS = ("sponsors",)
_REQUIRED_ATTRIBUTION_FILES = ("LICENSE", "SPONSORS.md", "SPONSORS_CN.md")
_LICENSE_DIGEST = "80cefc234c1ec12a8cece4344f16300c634fa03df7891686fcf979e3828f0921"


def _normalized_bytes(path: Path) -> bytes:
    """Return UTF-8 text bytes with platform line endings normalized."""
    data = path.read_bytes()
    if data.startswith(b"\xef\xbb\xbf"):
        raise ValueError("UTF-8 BOM is not allowed")
    text = data.decode("utf-8")
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def _frontmatter(skill_text: str) -> str:
    """Return the opening YAML frontmatter or reject malformed input."""
    if not skill_text.startswith("---\n"):
        raise ValueError("missing frontmatter")
    end = skill_text.find("\n---\n", 4)
    if end < 0:
        raise ValueError("unterminated frontmatter")
    return skill_text[4:end]


def _metadata_is_valid() -> bool:
    """Require fixed identity values and each structural attribution field."""
    skill_text = _normalized_bytes(_SKILL_DIR / "SKILL.md").decode("utf-8")
    metadata = _frontmatter(skill_text)
    return (
        all(
            len(re.findall(
                rf"(?m)^  {re.escape(field)}\s*:\s*{re.escape(value)}\s*$",
                metadata,
            )) == 1
            for field, value in _EXACT_METADATA_VALUES.items()
        )
        and all(
            len(re.findall(rf"(?m)^  {re.escape(field)}\s*:", metadata)) == 1
            for field in _REQUIRED_METADATA_FIELDS
        )
    )


def _protected_files_are_valid() -> bool:
    """Require all attribution paths and the exact MIT license text."""
    for relative_path in _REQUIRED_ATTRIBUTION_FILES:
        path = _SKILL_DIR / relative_path
        if not path.is_file():
            return False
    license_digest = hashlib.sha256(_normalized_bytes(_SKILL_DIR / "LICENSE")).hexdigest()
    return license_digest == _LICENSE_DIGEST


def _integrity_is_valid() -> bool:
    """Validate the local attribution invariants."""
    return _metadata_is_valid() and _protected_files_are_valid()


def require_skill_integrity() -> None:
    """Stop the active command with one generic message on any expected failure."""
    try:
        valid = _integrity_is_valid()
    except (OSError, SyntaxError, UnicodeError, ValueError):
        valid = False
    if valid:
        return
    print(_ERROR_MESSAGE, file=sys.stderr)
    raise SystemExit(78)


def main() -> int:
    """Run the fail-closed Skill attribution gate."""
    require_skill_integrity()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
