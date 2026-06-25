""" Created on 06-19-2026 15:59:56 @author: ripintheblue """

"""
Cleans raw ChatGPT trade-recommendation CSV exports into a tidy table.

Input files: one column of "CATEGORY<sep>text" lines (sep is ';' or '\t'),
cp1252-encoded, mixing real recs with chat noise (prompts, corrections,
scheduling confirmations). Output: one row per ticker recommendation.

Usage:
    python clean_trade_csv.py file1.csv file2.csv ... -o cleaned.csv
"""
import os
import re
import sys
from pathlib import Path

import pandas as pd

BASE_DIR = Path(r"Y:\15GB\Ad_hoc\LLMS")
FILENAMES = [
    '2025-12-05_to_2026-05-19_longeq.csv',
    '2026-01-04_to_2026-05-19_longall.csv',
    '2026-01-04_to_2026-05-19_short.csv',
    '2026-05-27 - daily long.csv',
    '2026-05-27 - buy eq.csv',
    '2026-05-27 - short.csv',
    '2025-10-14 to 11-19.csv',
    '2025-11-19 to 11-25.csv'
]

# Date line, time optional: "YYYY-MM-DD / HH:MM - Weekday" or "YYYY-MM-DD - Weekday"
DATE_RE = re.compile(
    r"(\d{4})[-?](\d{2})[-?](\d{2})(?:\s*/\s*(\d{2}):(\d{2}))?\s*-\s*(\w+)"
)
# Ticker line: SYMBOL <dash> rest. Symbol = caps/digits/.=/&_ only, 1-12 chars.
REC_RE = re.compile(
    r"^([A-Z][A-Z0-9.=/&_]{0,11})\s*[-\u2013\u2014]\s*(.+)$"
)
NAME_DESC_RE = re.compile(r"^(.*?)\(([^()]*)\)\s*$")

SKIP_PREFIXES = ("Recs:", "ChatGPT", "Thought for", "Prev days return")
# Lines that open a "previous day performance" block - everything in this
# block (tickers with % returns, Avg, S&P500) is not a new recommendation.
PERF_BLOCK_START = "Perf (prev recs):"
NBSP = "\xa0"
ENDASH_MOJIBAKE = "\x96"


def load_rows(path: Path):
    raw = path.read_bytes()
    text = raw.decode("cp1252", errors="replace")
    text = text.replace(ENDASH_MOJIBAKE, "\u2013").replace(NBSP, " ")
    lines = [l for l in text.split("\r\n") if l.strip()]
    if not lines:
        return
    # Delimiter by majority count over the whole file, not just line 1:
    # some exports have a stray tab-delimited header row followed by
    # semicolon-delimited data, which fooled the old first-line check.
    delim = ";" if text.count(";") >= text.count("\t") else "\t"
    # Some exports are 3-column ("label;date;text") instead of 2-column
    # ("label;text"). Detect and skip the header, drop the date column.
    has_date_col = lines[0].lower().startswith(f"label{delim}date{delim}text")
    if has_date_col:
        lines = lines[1:]
    for line in lines:
        category, _, remainder = line.partition(delim)
        if has_date_col:
            _, _, remainder = remainder.partition(delim)
        yield category.strip(), remainder.strip()


def parse_file(path: Path):
    """Yield dict rows: date, time, strategy, ticker, reasoning."""
    strategy = path.stem
    cur_date = cur_time = None
    in_perf_block = False
    for category, text in load_rows(path):
        if not text:
            continue
        strategy = category.strip().lower()

        m = DATE_RE.search(text)
        if m:
            y, mo, d, hh, mm = m.group(1), m.group(2), m.group(3), m.group(4), m.group(5)
            cur_date = f"{y}-{mo}-{d}"
            cur_time = f"{hh}:{mm}" if hh else None
            in_perf_block = False
            continue

        if text.startswith(PERF_BLOCK_START):
            in_perf_block = True
            continue
        if text.startswith("Recs:"):
            in_perf_block = False
            continue
        if in_perf_block or text.startswith(SKIP_PREFIXES) or cur_date is None:
            continue

        m = REC_RE.match(text)
        if not m:
            continue  # chat noise: corrections, follow-up prompts, etc.
        ticker, rest = m.group(1), m.group(2).strip()

        nd = NAME_DESC_RE.match(rest)
        if nd:
            name, rationale = nd.group(1).strip(" -\u2013\u2014"), nd.group(2).strip()
            reasoning = f"{name} ({rationale})" if rationale else name
        else:
            reasoning = rest

        yield {
            "date": cur_date,
            "time": cur_time,
            "strategy": strategy,
            "ticker": ticker,
            "reasoning": reasoning,
        }


def build_df() -> pd.DataFrame:
    fields = ["date", "time", "strategy", "ticker", "reasoning"]
    rows = []
    for name in FILENAMES:
        path = BASE_DIR / name
        if not path.exists():
            print(f"Missing file, skipping: {path}", file=sys.stderr)
            continue
        rows.extend(parse_file(path))
    return pd.DataFrame(rows, columns=fields)


df = build_df()
print(df)
df.to_csv(os.path.join(BASE_DIR, "cleaned_recs.csv"), index=False, sep=";")