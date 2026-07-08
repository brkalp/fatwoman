"""Shared command-line options. Every step accepts the same flags so the
run_*.sh wrappers can pass arguments through to all scripts uniformly
(e.g. --dry-run reaches step 5 without crashing steps 4 and 6)."""
import argparse
from datetime import datetime, timezone


def make_parser(description: str) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--backtest", action="store_true",
                   help="write outputs to data/backtest/, stamp with --as-of")
    p.add_argument("--as-of",
                   help="historical stamp: YYYYMMDD (daily) or YYYYMMDDHHMM (hourly)")
    p.add_argument("--mock", action="store_true", help="force the offline mock api")
    p.add_argument("--dry-run", action="store_true",
                   help="step 5 only: log orders without booking or consuming them")
    p.add_argument("--input", help="explicit input csv (default: latest)")
    return p


def parse_as_of(value):
    if not value:
        return None
    fmt = "%Y%m%d%H%M" if len(value) == 12 else "%Y%m%d"
    return datetime.strptime(value, fmt).replace(tzinfo=timezone.utc)
