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
| `scripts/s05_trade_execution.py` | hourly | limit/day orders (open orders retried hourly), risk caps + cash check, HALT file, max orders/hour, signal expiry, dry run, telegram, fills log |
| `scripts/s06_pnl_reporter.py` | hourly | positions vs expected, open orders, pnl by category → pnl telegram channel; slippage from fills; copy-ledger consistency check |
| `scripts/backtester.py` | weekly | backtests 1-4, Top Polymarket Index vs equal-weight universe benchmark (selection edge), turnover, Sharpe/vol/hit-rate, bucketed trader performance, html report + bt_metrics csv |
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
./run_paper_test.sh            # steps 1-6 + pytest against the persistent
                               # test paper account in paper_test/ (mock api,
                               # real paper fills - NOT a dry run)
./run_paper_test.sh --reset    # restart the test paper account from scratch
```

This is also what the nightly claude run uses to validate its fixes: fills
are booked into the test paper account and the pnl reporter runs, so the
full execution/state path is exercised.

Backtesting a single step: `python scripts/s01_user_fetch.py --backtest --as-of 20260601`
(step 1 back-calculates which users were available at that date; see bias
notes in the backtest report).

Backtest guarantees:

- **Never trades, not even paper.** Steps 1-4 only; all outputs are stored
  aside in `data/backtest/` as `10_backtest[_metrics/_report]_*`, the live
  paper account / execution state / telegram are untouched, and step 5
  refuses `--backtest` outright.
- **Uses your archives when it can.** Each rebalance date first checks for
  that day's step-1 snapshot (holders + prices, accumulated by the daily
  cron); archived weeks have zero survivorship bias and cost zero API
  calls. Only older dates fall back to back-calculation.
- **Three return series**: strategy (weighted, after steps 3-4), selected
  users equal-weight (picking skill without construction), universe
  equal-weight (no-skill baseline; strategy minus this = selection edge).
- **Reproducible when the strategy is unchanged.** Rebalance dates align to
  Monday 12:00 UTC (most recent complete week), so re-runs in the same
  calendar week hit the same windows; pin exactly with
  `python scripts/backtester.py --end 20260622` to reproduce a run later.
  Pinned mock runs are bit-identical; live runs additionally drift with the
  data-api (current-day holder snapshots - see survivorship note).

## Safety & ops

- **Paper by default** (`config/settings.json: mode`). Live CLOB execution
  is deliberately not wired - step 5 forces dry-run outside paper mode.
- **Kill switches** - marker files in the project root, checked hourly:
  | file | effect |
  |---|---|
  | `HALT` | stop - no orders at all, telegram alert |
  | `KILL` | sell every position at market, cancel open orders, stay halted while present |
  | `DRY` | force dry run - api not used, nothing booked |
  | `PAPER` | force paper mode regardless of config |
- **Market orders by default** (`execution.order_type`): fills at the
  current market price, slippage vs the signal price is recorded; `"limit"`
  switches to limit orders with the bps buffer + hourly retry + DAY expiry.
- **Dry run**: `./run_hourly.sh --dry-run`, `execution.dry_run`, or the
  `DRY` file. Dry runs never consume signals - everything stays pending
  for the next real run. Fill-booking errors log loudly (status ERROR).
- **Risk caps**: `execution.max_total_notional`, `max_category_notional`
  (open orders reserve budget), `max_orders_per_hour`, cash-constrained
  buys; sizing caps in `portfolio.*` (`copy_scale` sets replication scale).
- **Signal lifecycle**: FILLED / OPEN / SKIPPED_NO_POSITION / EXPIRED are
  final. Rate-capped, risk-capped and no-cash signals stay pending and
  retry each hour until `execution.signal_max_age_hours`, then expire.
  Open day orders are retried against the market hourly and die next day.
- **Logging** is automatic (core package import side effect + sitecustomize;
  scripts only call `logging.info`). One overview .txt per day:
  `logs/project_one_YYYYMMDD.txt` with run start/end times, key info,
  errors and claude notes.
- **Crontab**: see `crontab.txt` - one daily entry (1-3), one hourly (4-6),
  weekly backtest, nightly claude maintenance.
- **Claude loop**: `run_claude.sh` + `claude/CLAUDE_RUNBOOK.md`; drop change
  requests into `tasks/`. Claude validates every fix with
  `./run_paper_test.sh` (paper fills into `paper_test/`, never dry run).

## State (data/state/)

`paper_account.json` (cash, positions, realized pnl, open orders),
`copied_positions.json` (what we copied per source user - drives
user_out_of_index closes), `executed_signals.json` (dedupe layer 2),
`orders_this_hour.json` (rate limit).
