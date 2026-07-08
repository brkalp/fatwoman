"""Append a claude note into the project's daily log file, so the .txt
overview shows run times, errors AND claude's observations in one place.

Usage: python scripts/claude_note.py "fixed step 4 dedupe, re-ran paper mode ok"
"""
import _bootstrap  # noqa: F401
import logging
import sys

if __name__ == "__main__":
    note = " ".join(sys.argv[1:]).strip()
    if not note:
        raise SystemExit("usage: claude_note.py <note text>")
    logging.info("CLAUDE NOTE: %s", note, extra={"script": "claude"})
