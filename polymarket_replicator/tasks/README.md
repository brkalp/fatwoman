# /tasks - flow improvement queue for claude

Drop a `*.md` file here describing what you want changed, e.g.

    tasks/tighten_selection.md
    "Raise min accuracy to 0.60 and only 2 users per category. Backtest it."

The nightly claude run (see `run_claude.sh` / `claude/CLAUDE_RUNBOOK.md`)
picks tasks up, implements them, re-runs the flow in paper mode to test,
updates CHANGELOG.md + strategy/STRATEGY_xx.md if strategy logic changed,
and moves the finished task file into `tasks/done/`.
