# Strategy changelog

The newest `## xx` entry in this file is the strategy version. Every output
file carries it as the `_xx` suffix, and `strategy/STRATEGY_xx.md` describes
the logic of that version. Claude bumps the version here (and adds a matching
strategy file) whenever it changes strategy logic.

## 02 - 2026-07-08
- Audit pass. Execution lifecycle reworked: still-open limit orders are
  retried each hour before new orders; rate-capped / risk-capped / no-cash
  signals stay pending and retry until execution.signal_max_age_hours, then
  EXPIRE; dry runs no longer consume signals; open orders reserve risk
  budget; buys are cash-constrained; closes are capped to the shares copied
  from the signalling user (user_out_of_index no longer closes other users'
  copies). Sizing scale moved to config (portfolio.copy_scale).
- Backtester: equal-weight universe benchmark + selection edge, constituent
  turnover, vol/Sharpe/hit-rate metrics, bt_metrics csv for tracking across
  versions, dual-line chart, config snapshot in the html report.
- Logging: per-filter selection attrition, per-category universe summary,
  per-reason plan notionals, execution status/exposure summary, copy-ledger
  vs account consistency check in the pnl reporter.

## 01 - 2026-07-08
- Initial flow generated from the whiteboard spec: user fetch, user data
  fetch, user selection, signal generation, hourly execution (paper mode),
  pnl reporter, weekly backtester, shared auto-logging, crontab, claude
  maintenance loop.
