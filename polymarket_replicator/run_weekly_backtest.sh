#!/usr/bin/env bash
# Weekly backtest of steps 1-4 on the current selection logic; writes the
# Top Polymarket Index csv and the html report into data/backtest/.
set -uo pipefail
PROJ="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="$PROJ"
set -a; [ -f "$PROJ/.env" ] && . "$PROJ/.env"; set +a
PY="${POLYFLOW_PYTHON:-python3}"

"$PY" "$PROJ/scripts/backtester.py" "$@"
