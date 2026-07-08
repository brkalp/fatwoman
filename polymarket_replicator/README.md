# Project one - replicate top Polymarket traders

Finds consistently good traders in the biggest Polymarket markets, forms a
"top trader index" per category, and replicates their trades hourly at our
own scale (paper mode by default). Self-contained: nothing outside this
directory is read or written.

## Flow

```
daily (one cron entry)                      hourly (one cron entry)
┌─────────────┐  ┌───────────────┐  ┌──────────────┐  ┌──────────────────┐  ┌────────────────┐  ┌──────────────┐
│ 1 user fetch│→│ 2 user data    │→│ 3 select     │→ │ 4 signal          │→│ 5 trade        │→│ 6 pnl        │
│  universe   │  │  size/pnl/dd/  │  │  users       │  │  generation       │  │  execution     │  │  reporter    │
│             │  │  accuracy      │  │  (the index) │  │  (sizing, dedupe) │  │  (risk, halt)  │  │  (telegram)  │
└─────────────┘  └───────────────┘  └──────────────┘  └──────────────────┘  └────────────────┘  └──────────────┘
      01_...csv         02_...csv          03_...csv     04_users_trade_list     05_...csv           06_...csv
                                                         04_trade_plan
weekly: scripts/backtester.py backtests 1-4 → Top Polymarket Index + html report
nightly: run_claude.sh → claude reads logs + /tasks, fixes bugs, tests in paper mode
```

Every output file is `data/<step>_<name>_<stamp>_<xx>.csv` - stamp is
`YYYYMMDD` for daily steps, `YYYYMMDDHHMM` for hourly ones, `xx` is the
strategy version read from `CHANGELOG.md` (strategy text in
`strategy/STRATEGY_xx.md`).

## Scripts

| script | cron | what it does |
|---|---|---|
| `scripts/s01_user_fetch.py` | daily | top 10 markets/category + 100 biggest events → top 100 holders each |
| `scripts/s02_user_data_fetch.py` | daily | account size, past trades, daily pnl, drawdown, accuracy per user |
| `scripts/s03_select_users.py` | daily | **key logic**: filter + score, top N users per category with weights |
| `scripts/s04_signal_generation.py` | hourly | replicate trades, size positions, dedupe vs latest plan, close users out of the index; labels reasons |
| `scripts/s05_trade_execution.py` | hourly | limit/day orders, risk caps, HALT file, max orders/hour, dry run, telegram, fills log |
| `scripts/s06_pnl_reporter.py` | hourly | positions vs expected, open orders, pnl by category → pnl telegram channel; slippage from fills |
| `scripts/backtester.py` | weekly | backtests 1-4, Top Polymarket Index, bucketed trader performance, html report |
| `scripts/claude_note.py` | - | append a claude note into the daily log .txt |

## Running

```bash
pip install -r requirements.txt
cp .env.example .env          # telegram tokens etc (optional)
./run_daily.sh                # steps 1-3
./run_hourly.sh               # steps 4-6
./run_weekly_backtest.sh      # backtest + html report in data/backtest/
```

Offline / paper test without touching APIs or live data:

```bash
POLYFLOW_MOCK=1 POLYFLOW_RUNTIME=/tmp/polyflow_test ./run_daily.sh --mock
POLYFLOW_MOCK=1 POLYFLOW_RUNTIME=/tmp/polyflow_test ./run_hourly.sh --mock
python -m pytest tests/ -q
```

Backtesting a single step: `python scripts/s01_user_fetch.py --backtest --as-of 20260601`
(step 1 back-calculates which users were available at that date; see bias
notes in the backtest report).

## Safety & ops

- **Paper by default** (`config/settings.json: mode`). Live CLOB execution
  is deliberately not wired - step 5 forces dry-run outside paper mode.
- **HALT file**: `touch HALT` in the project root → step 5 refuses to trade
  and pings telegram. Remove the file to resume.
- **Dry run**: `./run_hourly.sh --dry-run` or `execution.dry_run` in config.
- **Risk caps**: `execution.max_total_notional`, `max_category_notional`,
  `max_orders_per_hour`; sizing caps in `portfolio.*`.
- **Logging** is automatic (core package import side effect + sitecustomize;
  scripts only call `logging.info`). One overview .txt per day:
  `logs/project_one_YYYYMMDD.txt` with run start/end times, key info,
  errors and claude notes.
- **Crontab**: see `crontab.txt` - one daily entry (1-3), one hourly (4-6),
  weekly backtest, nightly claude maintenance.
- **Claude loop**: `run_claude.sh` + `claude/CLAUDE_RUNBOOK.md`; drop change
  requests into `tasks/`.

## State (data/state/)

`paper_account.json` (cash, positions, realized pnl, open orders),
`copied_positions.json` (what we copied per source user - drives
user_out_of_index closes), `executed_signals.json` (dedupe layer 2),
`orders_this_hour.json` (rate limit).
