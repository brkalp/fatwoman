"""Remove duplicate copy-pasted blocks from chat-export CSVs and order
the recommendations by the date they were actually given.

Each row in the source file is: LABEL;text
Rows are grouped into blocks starting at a date-header line, e.g.:
    "2026-01-12 / 08:16 - Monday"
The header's date is what the following recommendation block belongs
to. Blocks are de-duplicated by that date (keeping the first
occurrence) and the output is written in chronological order, with
the parsed date added as its own column.
"""
import csv
import os
import re
from datetime import datetime
from pathlib import Path

from fatwoman_dir_setup import LLM_data_path, db_trades_name, db_trades, db_strategy_daily_returns_name, adhoc_fol
os.chdir(os.path.join(adhoc_fol, 'LLMS', 'daily_request'))

# Source dates use inconsistent separators ("-", "?", em-dash) due to
# encoding issues, so match on digits only and normalize afterward.
HEADER_RE = re.compile(
    r"^(\d{4}).(\d{2}).(\d{2}) / (\d{2}):(\d{2})"
)


def parse_header(text: str):
    """Return (date_str, time_str) if text is a date-header line, else None."""
    m = HEADER_RE.match(text)
    if not m:
        return None
    y, mo, d, hh, mm = m.groups()
    try:
        date_str = datetime(int(y), int(mo), int(d)).strftime("%Y-%m-%d")
    except ValueError:
        return None
    return date_str, f"{hh}:{mm}"


in_dir = Path(r"Y:\15GB\Ad_hoc\LLMS\daily_request")
out_dir = in_dir

for in_path in in_dir.glob("*dirty.csv"):
    out_name = in_path.name.replace("_dirty", "")
    out_name = re.sub(r"^\d+_", "", out_name)
    out_path = out_dir / out_name

    with open(in_path, encoding="cp1252", errors="replace", newline="") as f:
        rows = list(csv.reader(f, delimiter=";"))

    # Split into blocks, each tagged with the date its header refers to.
    blocks = []          # list of (date_str, time_str, [rows])
    current_rows = []
    current_date = None
    current_time = None
    for row in rows:
        text = row[1] if len(row) > 1 else ""
        parsed = parse_header(text)
        if parsed and current_rows:
            blocks.append((current_date, current_time, current_rows))
            current_date, current_time = parsed
            current_rows = [row]
        elif parsed:
            current_date, current_time = parsed
            current_rows = [row]
        else:
            current_rows.append(row)
    if current_rows:
        blocks.append((current_date, current_time, current_rows))

    # Keep first block per date (duplicates = same date copy-pasted again).
    seen_dates = set()
    deduped = []
    removed = 0
    for date_str, time_str, block_rows in blocks:
        if date_str is None:
            deduped.append((date_str, time_str, block_rows))  # leading/undated content, always keep
            continue
        if date_str in seen_dates:
            removed += 1
            continue
        seen_dates.add(date_str)
        deduped.append((date_str, time_str, block_rows))

    # Sort chronologically; undated (leading) content stays first.
    dated = [b for b in deduped if b[0] is not None]
    undated = [b for b in deduped if b[0] is None]
    dated.sort(key=lambda b: (b[0], b[1]))

    out_rows = []
    for date_str, time_str, block_rows in undated + dated:
        for row in block_rows:
            label = row[0] if row else ""
            text = row[1] if len(row) > 1 else ""
            out_rows.append([label, date_str or "", text])

    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["label", "date", "text"])
        writer.writerows(out_rows)

    print(f"{in_path.name}: {len(blocks)} blocks, removed {removed} duplicate-date blocks, "
          f"{len(rows)} rows -> {len(out_rows)} rows")