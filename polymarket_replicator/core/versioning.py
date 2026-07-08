"""Strategy version handling.

Every output file carries a `_xx` suffix. `xx` is the newest version number
found in CHANGELOG.md (entries look like `## 03 - 2026-07-08 - note`).
The strategy description for version xx lives in strategy/STRATEGY_xx.md.
"""
import re
from .paths import CHANGELOG_PATH, STRATEGY_DIR

_VERSION_RE = re.compile(r"^##\s*(\d{2})\b", re.MULTILINE)


def get_version() -> str:
    """Return the latest two-digit strategy version from the changelog."""
    try:
        text = CHANGELOG_PATH.read_text()
    except FileNotFoundError:
        return "00"
    versions = _VERSION_RE.findall(text)
    if not versions:
        return "00"
    return max(versions)


def strategy_file():
    """Path of the strategy markdown matching the current version."""
    return STRATEGY_DIR / f"STRATEGY_{get_version()}.md"
