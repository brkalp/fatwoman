# Strategy v03 - Replicate top Polymarket traders

## Idea
Build a "top Polymarket trader index": find consistently profitable traders
in the biggest markets, select the best few per category, and replicate their
trades at our own scale, hourly.

## Universe (step 1)
Per category (Politics, Finance, Crypto, Sports, Tech, Culture, Geopolitics):
the 10 biggest open markets by volume, plus markets from the 100 biggest
events. From each market, harvest the top 100 holders.

## Selection (step 3)
Filters: account size >= 10k, >= 10 trades in 30d, accuracy >= 55%,
max drawdown <= 35%, non-negative 30d pnl. Score = mean of min-max normalized
(accuracy, 30d pnl / account, -drawdown). Top 3 users per category; weight
within category proportional to score.

## Sizing (step 4)
copy_fraction = trade_usdc / trader_account_size.
my_notional = equity * category_allocation * user_weight_in_category
              * copy_fraction * copy_scale (config, 100; capped at
              max_position_per_market, dropped below min_ticket).

## Execution (step 5, hourly, paper by default)
MARKET orders by default: fill at the current market price, slippage vs the
signal price is recorded (execution.order_type "limit" switches to limit
orders at signal +/- 80 bps, DAY time-in-force). Risk caps: total notional
8k, per-category 2.5k (open orders reserve budget), max 20 orders/hour,
cash-constrained buys.

Kill switches (files in the runtime root): HALT stops trading; KILL sells
every position at market and stays halted while present; DRY forces dry run
(api not used); PAPER forces paper mode. Fill-booking errors are logged
loudly (status ERROR), never silent.

Signal lifecycle: FILLED / OPEN / SKIPPED_NO_POSITION / EXPIRED are final.
Open day orders are retried against the market every hour and expire next
day. Rate-capped, risk-capped and no-cash signals stay pending and retry
hourly until signal_max_age_hours (3h), then EXPIRE. Dry runs never consume
signals. Fills feed the pnl reporter.

## Exits
- Trader sells -> we close proportionally, capped at the shares copied from
  that trader ("user_close_trade").
- Trader drops out of the index -> close the shares copied from him
  ("user_out_of_index") - other traders' copies in the same market stay on.

## Known biases
Backtests prefer archived step-1 daily snapshots (holders + prices as they
were - no survivorship) and only fall back to back-calculating availability
from the current-day API for dates before collection started; the fallback
keeps a survivorship caveat. Activity/pnl series are filtered to <= as_of
(no lookahead on selection metrics).
