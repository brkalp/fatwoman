#!/usr/bin/env bash
# Daily refresh of the user universe and portfolio list (steps 1-3).
# One cron entry runs all three; a step failure stops the chain.
set -uo pipefail
PROJ="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="$PROJ"
set -a; [ -f "$PROJ/.env" ] && . "$PROJ/.env"; set +a
PY="${POLYFLOW_PYTHON:-python3}"

"$PY" "$PROJ/scripts/s01_user_fetch.py" "$@" \
  && "$PY" "$PROJ/scripts/s02_user_data_fetch.py" "$@" \
  && "$PY" "$PROJ/scripts/s03_select_users.py" "$@"
