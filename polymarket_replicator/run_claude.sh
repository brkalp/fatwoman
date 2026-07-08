#!/usr/bin/env bash
# Nightly claude maintenance: reads the daily log and /tasks, fixes bugs,
# re-runs the flow in paper/mock mode to test, updates changelog + strategy
# files, and leaves notes in the daily log via scripts/claude_note.py.
set -uo pipefail
PROJ="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="$PROJ"
set -a; [ -f "$PROJ/.env" ] && . "$PROJ/.env"; set +a

if ! command -v claude >/dev/null 2>&1; then
  echo "claude cli not installed - skipping maintenance run"
  exit 0
fi

cd "$PROJ"
claude -p "Read claude/CLAUDE_RUNBOOK.md in this directory and follow it." \
  --permission-mode acceptEdits \
  --allowedTools "Read,Edit,Write,Glob,Grep,Bash(python*),Bash(./run_*.sh*),Bash(mv*),Bash(ls*)"
