# Strategy v01 - Replicate top Polymarket traders

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
              * copy_fraction * 100  (scaled, capped at max_position_per_market,
              dropped below min_ticket).

## Execution (step 5, hourly, paper by default)
Limit orders at signal price +/- 80 bps buffer, DAY time-in-force. Risk caps:
total notional 8k, per-category 2.5k, max 20 orders/hour. HALT file stops
everything. Fills feed the pnl reporter.

## Exits
- Trader sells -> we close proportionally ("user_close_trade").
- Trader drops out of the index -> close all his copied positions
  ("user_out_of_index").

## Known biases
Backtests re-derive the available user set as-of each rebalance date, but the
holder snapshot itself is current-day (survivorship). Activity/pnl series are
filtered to <= as_of (no lookahead on selection metrics).
