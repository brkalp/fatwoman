"""Output file naming, latest-file discovery and small json state helpers.

Naming convention (from the whiteboard):
    <step>_<name>_<stamp>_<xx>.csv
where stamp is YYYYMMDD for daily steps (1-3) and YYYYMMDDHHMM for hourly
steps (4-6), and xx is the strategy version read from CHANGELOG.md.
Backtest runs write to data/backtest/ so live files are never mixed up.
"""
import json
import logging
from datetime import datetime, timezone

import pandas as pd

from .paths import BACKTEST_DATA_DIR, DATA_DIR, STATE_DIR
from .versioning import get_version


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def day_stamp(dt=None) -> str:
    return (dt or utcnow()).strftime("%Y%m%d")


def minute_stamp(dt=None) -> str:
    return (dt or utcnow()).strftime("%Y%m%d%H%M")


def data_dir(backtest: bool = False):
    return BACKTEST_DATA_DIR if backtest else DATA_DIR


def build_path(prefix: str, stamp: str, backtest: bool = False, ext: str = "csv"):
    return data_dir(backtest) / f"{prefix}_{stamp}_{get_version()}.{ext}"


def latest_file(prefix: str, backtest: bool = False):
    """Newest file for a step prefix, e.g. latest_file('03_selected_user_list').
    Stamps sort lexicographically, so name-sort == time-sort."""
    files = sorted(data_dir(backtest).glob(f"{prefix}_*.csv"))
    return files[-1] if files else None


def write_csv(df: pd.DataFrame, path) -> None:
    df.to_csv(path, index=False)
    logging.info("wrote %s (%d rows)", path.name, len(df))


def read_csv(path) -> pd.DataFrame:
    return pd.read_csv(path)


# --- tiny json state store (data/state/*.json) -------------------------------

def load_state(name: str, default):
    path = STATE_DIR / f"{name}.json"
    if not path.exists():
        return default
    with open(path) as fh:
        return json.load(fh)


def save_state(name: str, obj) -> None:
    path = STATE_DIR / f"{name}.json"
    with open(path, "w") as fh:
        json.dump(obj, fh, indent=1, default=str)
