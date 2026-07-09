"""Backtester - runs weekly on the current selection logic.

Backtests steps 1-4: for each weekly rebalance date it re-runs user fetch
(with the back-calculated available-user universe), user data fetch and
selection as-of that date, generates a signal snapshot, then measures the
selected cohort's forward one-week returns.

Produces:
- the "Top Polymarket Index": cumulative performance of the strategy's
  selected cohort, benchmarked against the equal-weight universe (the
  difference is the selection edge - if it isn't positive, the selection
  logic adds nothing over just copying everyone),
- constituent turnover per rebalance,
- bucketed performance of all universe traders (accuracy quartiles,
  account-size buckets),
- bt_index_YYYYMMDD_xx.csv   weekly series (index, benchmark, edge, turnover)
- bt_metrics_YYYYMMDD_xx.csv one-row summary for tracking across versions
- bt_report_YYYYMMDD_xx.html strategy overview, chart, constituents, config

Isolation: a backtest never executes anything - not even paper. Steps 1-4
only; every output is stored aside in data/backtest/, and the live paper
account, execution state and telegram are never touched (step 5 refuses
--backtest outright).

Reproducibility: rebalance dates are aligned to Monday 12:00 UTC (most
recent complete week), so with an unchanged strategy a re-run inside the
same calendar week reproduces the same windows - in mock mode the outcome
is bit-identical. Pin the window exactly with --end YYYYMMDD to reproduce
a run any time later. In live mode the data-api itself drifts (current-day
holder snapshots - see survivorship note), so only pinned mock runs are
fully deterministic.

Bias notes: selection metrics only use data stamped <= as_of (no lookahead);
the holder snapshot is current-day, so a survivorship caveat remains and is
printed in the report.
"""
import _bootstrap  # noqa: F401
import html
import json
import logging
from datetime import datetime, timedelta, timezone

import pandas as pd

import s01_user_fetch
import s02_user_data_fetch
import s03_select_users
import s04_signal_generation
from core.cli import make_parser
from core.config import load_config
from core.io_utils import build_path, day_stamp, read_csv, write_csv
from core.paths import CHANGELOG_PATH
from core.polymarket_api import get_api
from core.versioning import get_version, strategy_file


def parse_args(argv=None):
    p = make_parser(__doc__)
    p.add_argument("--weeks", type=int, help="number of weekly rebalances")
    p.add_argument("--end", help="last rebalance date YYYYMMDD - pins the "
                                 "window so a run can be reproduced exactly "
                                 "(default: most recent Monday with a "
                                 "complete forward week)")
    return p.parse_args(argv)


def _step_args(step, **kw):
    return step.parse_args(
        [a for k, v in kw.items() if v not in (None, False)
         for a in ([f"--{k.replace('_', '-')}"] if v is True
                   else [f"--{k.replace('_', '-')}", str(v)])])


def _bucket_table(universe: pd.DataFrame, returns: dict) -> pd.DataFrame:
    df = universe.copy()
    df["fwd_return"] = df["proxy_wallet"].map(returns)
    df = df.dropna(subset=["fwd_return"])
    if len(df) < 8:
        return pd.DataFrame()
    df["accuracy_bucket"] = pd.qcut(df["accuracy"].rank(method="first"), 4,
                                    labels=["q1_low", "q2", "q3", "q4_high"])
    df["size_bucket"] = pd.cut(df["account_size"], [0, 1e4, 1e5, 1e12],
                               labels=["<10k", "10k-100k", ">100k"])
    acc = df.groupby("accuracy_bucket", observed=True)["fwd_return"].mean()
    size = df.groupby("size_bucket", observed=True)["fwd_return"].mean()
    out = pd.concat([acc.rename("avg_weekly_return").reset_index()
                        .rename(columns={"accuracy_bucket": "bucket"})
                        .assign(dimension="accuracy"),
                     size.rename("avg_weekly_return").reset_index()
                        .rename(columns={"size_bucket": "bucket"})
                        .assign(dimension="account_size")])
    return out[["dimension", "bucket", "avg_weekly_return"]]


def run(args):
    cfg = load_config()
    if args.mock:
        cfg["mock_api"] = True
    weeks = args.weeks or cfg["backtest"]["weeks"]
    mock_flag = bool(cfg.get("mock_api"))

    if args.end:
        from core.cli import parse_as_of
        last_reb = parse_as_of(args.end).replace(hour=12)
        anchor_note = f"pinned by --end {args.end}"
    else:
        # most recent Monday 12:00 UTC whose forward week is complete:
        # deterministic within a calendar week, so an unchanged strategy
        # reproduces the same windows on re-run
        anchor = (datetime.now(timezone.utc).replace(hour=12, minute=0,
                                                     second=0, microsecond=0)
                  - timedelta(days=7))
        last_reb = anchor - timedelta(days=anchor.weekday())
        anchor_note = "week-aligned default (pin with --end to reproduce later)"
    rebalances = [last_reb - timedelta(days=7 * (weeks - 1 - i))
                  for i in range(weeks)]
    logging.info("backtesting %d weekly rebalances: %s .. %s (%s, mock=%s, v%s)",
                 weeks, rebalances[0].date(), rebalances[-1].date(),
                 anchor_note, mock_flag, get_version())

    index_rows, bucket_frames = [], []
    last_selected, last_universe = pd.DataFrame(), pd.DataFrame()
    prev_wallets: set = set()
    cat_cum = {}
    level, bench_level = 100.0, 100.0

    for reb in rebalances:
        day = reb.strftime("%Y%m%d")
        f1 = s01_user_fetch.run(_step_args(s01_user_fetch, backtest=True,
                                           as_of=day, mock=mock_flag))
        f2 = s02_user_data_fetch.run(_step_args(s02_user_data_fetch, backtest=True,
                                                as_of=day, mock=mock_flag, input=f1))
        f3 = s03_select_users.run(_step_args(s03_select_users, backtest=True,
                                             as_of=day, input=f2))
        plan_file = s04_signal_generation.run(
            _step_args(s04_signal_generation, backtest=True,
                       as_of=reb.strftime("%Y%m%d%H%M"), mock=mock_flag))
        n_signals = len(read_csv(plan_file))

        selected, universe = read_csv(f3), read_csv(f2)
        api = get_api(cfg, as_of=reb + timedelta(days=7))
        returns = {}
        for w in set(universe["proxy_wallet"]):
            try:
                returns[w] = api.user_weekly_return(w, reb)
            except Exception as exc:  # noqa: BLE001
                logging.error("weekly return failed for %s: %s", w, exc)

        # strategy return: category-allocation and user-weight weighted
        port_ret = 0.0
        alloc = cfg["portfolio"]["category_allocation"]
        alloc_total = sum(alloc.get(c, 0.1)
                          for c in selected["category"].unique()) or 1
        for r in selected.itertuples():
            port_ret += (alloc.get(r.category, 0.1) / alloc_total) * r.weight \
                        * returns.get(r.proxy_wallet, 0.0)
            cat_cum[r.category] = (cat_cum.get(r.category, 0.0)
                                   + r.weight * returns.get(r.proxy_wallet, 0.0))

        # benchmark: equal-weight average of the whole available universe
        bench_ret = (sum(returns.values()) / len(returns)) if returns else 0.0
        level *= (1 + port_ret)
        bench_level *= (1 + bench_ret)

        wallets = set(selected["proxy_wallet"])
        turnover = (1 - len(wallets & prev_wallets) / len(wallets)
                    if wallets and prev_wallets else 0.0)
        prev_wallets = wallets

        index_rows.append({"week_start": reb.date().isoformat(),
                           "n_universe": universe["proxy_wallet"].nunique(),
                           "n_selected": len(selected),
                           "n_signals_at_rebalance": n_signals,
                           "weekly_return": round(port_ret, 5),
                           "universe_return": round(bench_ret, 5),
                           "selection_edge": round(port_ret - bench_ret, 5),
                           "turnover": round(turnover, 3),
                           "index_level": round(level, 3),
                           "universe_level": round(bench_level, 3)})
        logging.info("week %s: %d selected, strat %+.2f%% vs universe %+.2f%% "
                     "(edge %+.2f%%), turnover %.0f%%, index %.2f",
                     day, len(selected), port_ret * 100, bench_ret * 100,
                     (port_ret - bench_ret) * 100, turnover * 100, level)

        bucket_frames.append(_bucket_table(universe, returns))
        last_selected, last_universe = selected, universe

    index_df = pd.DataFrame(index_rows)
    buckets = (pd.concat(bucket_frames).groupby(["dimension", "bucket"],
                                                observed=True)
               .mean().round(5).reset_index()) if bucket_frames else pd.DataFrame()

    metrics = _metrics(index_df)
    for k, v in metrics.items():
        logging.info("metric %-22s: %s", k, v)

    stamp = day_stamp()
    write_csv(index_df, build_path("bt_index", stamp, backtest=True))
    write_csv(pd.DataFrame([{"run_date": stamp, "version": get_version(),
                             "weeks": weeks, **metrics}]),
              build_path("bt_metrics", stamp, backtest=True))
    report_path = build_path("bt_report", stamp, backtest=True, ext="html")
    report_path.write_text(_render_html(cfg, index_df, buckets, last_selected,
                                        last_universe, cat_cum, metrics))
    logging.info("backtest report written: %s", report_path)
    return report_path


def _metrics(index_df: pd.DataFrame) -> dict:
    if index_df.empty:
        return {}
    rets = index_df["weekly_return"]
    vol = float(rets.std(ddof=0))
    return {
        "total_return_pct": round(float(index_df["index_level"].iloc[-1]) - 100, 2),
        "universe_return_pct": round(float(index_df["universe_level"].iloc[-1]) - 100, 2),
        "cum_selection_edge_pct": round(float(index_df["selection_edge"].sum()) * 100, 2),
        "max_drawdown_pct": round(_drawdown(index_df["index_level"]) * 100, 2),
        "weekly_vol_pct": round(vol * 100, 2),
        "sharpe_annualized": round(float(rets.mean()) / vol * (52 ** 0.5), 2) if vol else None,
        "hit_rate": round(float((rets > 0).mean()), 2),
        "avg_turnover": round(float(index_df["turnover"].mean()), 3),
        "best_week_pct": round(float(rets.max()) * 100, 2),
        "worst_week_pct": round(float(rets.min()) * 100, 2),
    }


def _drawdown(levels) -> float:
    peak, worst = -1e9, 0.0
    for lvl in levels:
        peak = max(peak, lvl)
        worst = max(worst, (peak - lvl) / peak)
    return round(worst, 4)


def _svg_chart(index_df, width=720, height=240) -> str:
    strat = list(index_df["index_level"])
    bench = list(index_df["universe_level"])
    if len(strat) < 2:
        return "<p>not enough data for a chart</p>"
    lo = min(strat + bench)
    hi = max(strat + bench)
    span = (hi - lo) or 1

    def line(vals):
        return " ".join(
            f"{20 + i * (width - 40) / (len(vals) - 1):.1f},"
            f"{height - 20 - (v - lo) / span * (height - 40):.1f}"
            for i, v in enumerate(vals))

    return (f'<svg width="{width}" height="{height}" '
            f'style="background:#fafafa;border:1px solid #ddd">'
            f'<polyline points="{line(bench)}" fill="none" stroke="#999" '
            f'stroke-width="1.5" stroke-dasharray="5,4"/>'
            f'<polyline points="{line(strat)}" fill="none" stroke="#2c7be5" '
            f'stroke-width="2"/>'
            f'<text x="20" y="16" font-size="12" fill="#2c7be5">Top Polymarket '
            f'Index {strat[0]:.1f} → {strat[-1]:.1f}</text>'
            f'<text x="320" y="16" font-size="12" fill="#777">universe '
            f'equal-weight {bench[0]:.1f} → {bench[-1]:.1f}</text></svg>')


def _render_html(cfg, index_df, buckets, selected, universe, cat_cum,
                 metrics) -> str:
    def table(df):
        return df.to_html(index=False, border=0) if len(df) else "<p>empty</p>"

    strat = strategy_file()
    strat_txt = strat.read_text() if strat.exists() else "(no strategy file)"
    changelog_head = "\n".join(CHANGELOG_PATH.read_text().splitlines()[:25])
    metric_rows = "".join(f"<tr><th>{html.escape(str(k))}</th><td>{v}</td></tr>"
                          for k, v in metrics.items())
    cat_rows = "".join(f"<tr><td>{html.escape(c)}</td><td>{v * 100:+.2f}%</td></tr>"
                       for c, v in sorted(cat_cum.items()))
    cfg_snapshot = json.dumps({k: cfg[k] for k in
                               ("selection", "portfolio", "execution", "universe")},
                              indent=1)
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Backtest report v{get_version()}</title>
<style>body{{font-family:sans-serif;margin:2em;max-width:960px}}
table{{border-collapse:collapse;margin:1em 0}}
td,th{{border:1px solid #ccc;padding:4px 10px;font-size:13px;text-align:right}}
th{{background:#eee}} pre{{background:#f6f6f6;padding:1em;overflow-x:auto}}</style>
</head><body>
<h1>Top Polymarket traders - backtest report (strategy v{get_version()})</h1>
<p>Generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC.
Weekly backtest of steps 1-4 on the current selection logic, benchmarked
against the equal-weight universe.</p>

<h2>Key metrics</h2>
<table>{metric_rows}</table>

<h2>Top Polymarket Index vs universe</h2>
{_svg_chart(index_df)}
{table(index_df)}

<h2>PnL per category (cumulative, weight-adjusted)</h2>
<table><tr><th>category</th><th>cum pnl</th></tr>{cat_rows}</table>

<h2>Bucketed trader performance (whole universe)</h2>
{table(buckets)}

<h2>Current index constituents (latest rebalance)</h2>
{table(selected[['category', 'user_name', 'proxy_wallet', 'account_size',
                 'accuracy', 'max_drawdown', 'total_pnl_30d', 'score', 'weight']]
       if len(selected) else selected)}

<h2>Config snapshot</h2>
<pre>{html.escape(cfg_snapshot)}</pre>

<h2>Strategy</h2>
<pre>{html.escape(strat_txt)}</pre>

<h2>Changelog (head)</h2>
<pre>{html.escape(changelog_head)}</pre>

<h2>Bias notes</h2>
<p><b>Lookahead:</b> selection metrics are computed from data stamped &lt;=
each rebalance date. <b>Survivorship:</b> the holder universe is a
current-day snapshot filtered to wallets already active at the rebalance
date; wallets that died and vanished from today's holder lists are missing,
so historical index returns are likely overstated.</p>
</body></html>"""


if __name__ == "__main__":
    run(parse_args())
