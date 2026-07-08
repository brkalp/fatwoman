# Strategy changelog

The newest `## xx` entry in this file is the strategy version. Every output
file carries it as the `_xx` suffix, and `strategy/STRATEGY_xx.md` describes
the logic of that version. Claude bumps the version here (and adds a matching
strategy file) whenever it changes strategy logic.

## 01 - 2026-07-08
- Initial flow generated from the whiteboard spec: user fetch, user data
  fetch, user selection, signal generation, hourly execution (paper mode),
  pnl reporter, weekly backtester, shared auto-logging, crontab, claude
  maintenance loop.
