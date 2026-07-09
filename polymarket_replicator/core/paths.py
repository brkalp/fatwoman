"""Central path definitions for the Polymarket replicator project.

POLYFLOW_RUNTIME can point data/logs/state somewhere else (used by tests and
paper re-runs so live outputs are never touched). Config, changelog and
strategy files always come from the real project root.
"""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ROOT = Path(os.environ.get("POLYFLOW_RUNTIME", PROJECT_ROOT))

DATA_DIR = RUNTIME_ROOT / "data"
BACKTEST_DATA_DIR = DATA_DIR / "backtest"
STATE_DIR = DATA_DIR / "state"
LOG_DIR = RUNTIME_ROOT / "logs"

CONFIG_PATH = Path(os.environ.get("POLYFLOW_CONFIG", PROJECT_ROOT / "config" / "settings.json"))
CHANGELOG_PATH = PROJECT_ROOT / "CHANGELOG.md"
STRATEGY_DIR = PROJECT_ROOT / "strategy"
TASKS_DIR = PROJECT_ROOT / "tasks"
# kill switches - marker files in the runtime root, checked by execution:
# HALT stops all trading, KILL liquidates every position then stays halted,
# DRY forces dry run (no orders booked/sent), PAPER forces paper mode.
HALT_FILE = RUNTIME_ROOT / "HALT"
KILL_FILE = RUNTIME_ROOT / "KILL"
DRY_FILE = RUNTIME_ROOT / "DRY"
PAPER_FILE = RUNTIME_ROOT / "PAPER"

for _d in (DATA_DIR, BACKTEST_DATA_DIR, STATE_DIR, LOG_DIR):
    _d.mkdir(parents=True, exist_ok=True)
