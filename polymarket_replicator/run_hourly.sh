#!/usr/bin/env bash
# Hourly trade job: signal generation (4) then execution (5), then the pnl
# reporter (6) - the reporter runs even if there was nothing to execute.
set -uo pipefail
PROJ="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="$PROJ"
set -a; [ -f "$PROJ/.env" ] && . "$PROJ/.env"; set +a
PY="${POLYFLOW_PYTHON:-python3}"

"$PY" "$PROJ/scripts/s04_signal_generation.py" "$@" \
  && "$PY" "$PROJ/scripts/s05_trade_execution.py" "$@"
"$PY" "$PROJ/scripts/s06_pnl_reporter.py" "$@"
