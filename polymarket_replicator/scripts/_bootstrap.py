"""Imported first by every script: puts the project root on sys.path and
activates auto-logging via the core package import side effect. Scripts make
no logging setup calls themselves - only logging.info / logging.error."""
import sys
from pathlib import Path

_root = str(Path(__file__).resolve().parents[1])
if _root not in sys.path:
    sys.path.insert(0, _root)

import core  # noqa: F401,E402
