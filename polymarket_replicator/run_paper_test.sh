#!/usr/bin/env bash
# Paper-account test harness - what claude runs to validate fixes.
#
# Re-runs the whole flow with the offline mock api against a dedicated,
# persistent PAPER account under paper_test/: fills are actually booked,
# account state advances, and the pnl reporter runs. This is intentionally
# NOT a dry run - dry runs skip fill booking and state updates, which is
# exactly where execution bugs live. Live data/, logs/ and the live paper
# account are never touched (everything stays inside paper_test/).
#
#   ./run_paper_test.sh           run steps 1-6 + pytest on the test account
#   ./run_paper_test.sh --reset   wipe and restart the test paper account
set -uo pipefail
PROJ="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="$PROJ"
export POLYFLOW_MOCK=1
export POLYFLOW_RUNTIME="${POLYFLOW_TEST_RUNTIME:-$PROJ/paper_test}"
unset POLYFLOW_DRY_RUN
PY="${POLYFLOW_PYTHON:-python3}"

if [ "${1:-}" = "--reset" ]; then
  rm -rf "$POLYFLOW_RUNTIME"
  echo "test paper account reset: $POLYFLOW_RUNTIME wiped"
fi
mkdir -p "$POLYFLOW_RUNTIME"
echo "=== paper test run against $POLYFLOW_RUNTIME (mock api, real paper fills) ==="

"$PY" "$PROJ/scripts/s01_user_fetch.py" --mock \
  && "$PY" "$PROJ/scripts/s02_user_data_fetch.py" --mock \
  && "$PY" "$PROJ/scripts/s03_select_users.py" --mock \
  && "$PY" "$PROJ/scripts/s04_signal_generation.py" --mock \
  && "$PY" "$PROJ/scripts/s05_trade_execution.py" --mock \
  && "$PY" "$PROJ/scripts/s06_pnl_reporter.py" --mock \
  || { echo "PAPER TEST FAILED: pipeline step exited non-zero"; exit 1; }

"$PY" -m pytest "$PROJ/tests/" -q \
  || { echo "PAPER TEST FAILED: pytest"; exit 1; }

"$PY" - "$POLYFLOW_RUNTIME" <<'EOF'
import csv, json, sys
from pathlib import Path

runtime = Path(sys.argv[1])
execs = sorted((runtime / "data").glob("05_execution_*.csv"))
if execs:
    statuses = {r["status"] for r in csv.DictReader(open(execs[-1]))}
    if "DRY_RUN" in statuses:
        raise SystemExit("PAPER TEST FAILED: execution ran as DRY RUN - "
                         "check execution.dry_run in config; tests must book "
                         "real paper fills")

acct_file = runtime / "data/state/paper_account.json"
if not acct_file.exists():
    raise SystemExit("PAPER TEST FAILED: no paper account was written - "
                     "execution did not book anything")
a = json.loads(acct_file.read_text())
print("=== test paper account after run ===")
print(f"cash {a['cash']:.2f} (start {a['equity_start']:.2f}) | "
      f"realized pnl {a['realized_pnl']:+.2f} | "
      f"{len(a['positions'])} positions | {len(a['open_orders'])} open orders")
for cat, pnl in sorted(a.get("realized_by_category", {}).items()):
    if pnl:
        print(f"  realized {cat}: {pnl:+.2f}")
EOF
echo "=== paper test OK ==="
