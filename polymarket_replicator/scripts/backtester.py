"""Backtester - runs weekly on the current selection logic.

Backtests steps 1-4: for each weekly rebalance date it re-runs user fetch
(with the back-calculated available-user universe), user data fetch and
selection as-of that date, generates a signal snapshot, then measures the
selected cohort's forward one-week returns.

Produces:
- the "Top Polymarket Index": cumulative performance of the strategy's
  selected cohort, plus bucketed performance of all universe traders
  (accuracy quartiles, account-size buckets),
- bt_index_YYYYMMDD_xx.csv with the weekly index series,
- bt_report_YYYYMMDD_xx.html: strategy overview, index chart, constituents
  and key metrics (drawdown, pnl per category, best/worst week).

Bias notes: selection metrics only use data stamped <= as_of (no lookahead);
the holder snapshot is current-day, so a survivorship caveat remains and is
printed in the report.
"""
import _bootstrap  # noqa: F401
import argparse
import html
import logging
from datetime import datetime, timedelta, timezone

import pandas as pd

import s01_user_fetch
import s02_user_data_fetch
import s03_select_users
import s04_signal_generation
from core.config import load_config
from core.io_utils import build_path, day_stamp, read_csv, write_csv
from core.paths import CHANGELOG_PATH
from core.polymarket_api import get_api
from core.versioning import get_version, strategy_file


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--weeks", type=int, help="number of weekly rebalances")
    p.add_argument("--mock", action="store_true")
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

    now = datetime.now(timezone.utc).replace(hour=12, minute=0, second=0, microsecond=0)
    rebalances = [now - timedelta(days=7 * (weeks - i)) for i in range(weeks)]
    logging.info("backtesting %d weekly rebalances: %s .. %s (mock=%s)",
                 weeks, rebalances[0].date(), rebalances[-1].date(), mock_flag)

    index_rows, bucket_frames = [], []
    last_selected, last_universe = pd.DataFrame(), pd.DataFrame()
    cat_cum = {}
    level = 100.0

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

        port_ret = 0.0
        alloc = cfg["portfolio"]["category_allocation"]
        alloc_total = sum(alloc.get(c, 0.1) for c in selected["category"].unique()) or 1
        for r in selected.itertuples():
            port_ret += (alloc.get(r.category, 0.1) / alloc_total) * r.weight \
                        * returns.get(r.proxy_wallet, 0.0)
            cat_cum[r.category] = (cat_cum.get(r.category, 0.0)
                                   + r.weight * returns.get(r.proxy_wallet, 0.0))
        level *= (1 + port_ret)
        index_rows.append({"week_start": reb.date().isoformat(),
                           "n_universe": universe["proxy_wallet"].nunique(),
                           "n_selected": len(selected),
                           "n_signals_at_rebalance": n_signals,
                           "weekly_return": round(port_ret, 5),
                           "index_level": round(level, 3)})
        logging.info("week %s: %d selected, ret %+.2f%%, index %.2f",
                     day, len(selected), port_ret * 100, level)

        bucket_frames.append(_bucket_table(universe, returns))
        last_selected, last_universe = selected, universe

    index_df = pd.DataFrame(index_rows)
    buckets = (pd.concat(bucket_frames).groupby(["dimension", "bucket"],
                                                observed=True)
               .mean().round(5).reset_index()) if bucket_frames else pd.DataFrame()

    stamp = day_stamp()
    write_csv(index_df, build_path("bt_index", stamp, backtest=True))
    report_path = build_path("bt_report", stamp, backtest=True, ext="html")
    report_path.write_text(_render_html(cfg, index_df, buckets, last_selected,
                                        last_universe, cat_cum))
    logging.info("backtest report written: %s", report_path)
    logging.info("index: total return %+.2f%%, max drawdown %.2f%%",
                 level - 100, _index_drawdown(index_df) * 100)
    return report_path


def _index_drawdown(index_df) -> float:
    peak, worst = -1e9, 0.0
    for lvl in index_df["index_level"]:
        peak = max(peak, lvl)
        worst = max(worst, (peak - lvl) / peak)
    return round(worst, 4)


def _svg_chart(index_df, width=720, height=220) -> str:
    levels = list(index_df["index_level"])
    if len(levels) < 2:
        return "<p>not enough data for a chart</p>"
    lo, hi = min(levels), max(levels)
    span = (hi - lo) or 1
    pts = " ".join(
        f"{20 + i * (width - 40) / (len(levels) - 1):.1f},"
        f"{height - 20 - (v - lo) / span * (height - 40):.1f}"
        for i, v in enumerate(levels))
    return (f'<svg width="{width}" height="{height}" '
            f'style="background:#fafafa;border:1px solid #ddd">'
            f'<polyline points="{pts}" fill="none" stroke="#2c7be5" stroke-width="2"/>'
            f'<text x="20" y="16" font-size="12">Top Polymarket Index '
            f'({levels[0]:.1f} → {levels[-1]:.1f})</text></svg>')


def _render_html(cfg, index_df, buckets, selected, universe, cat_cum) -> str:
    def table(df):
        return df.to_html(index=False, border=0) if len(df) else "<p>empty</p>"

    strat = strategy_file()
    strat_txt = strat.read_text() if strat.exists() else "(no strategy file)"
    changelog_head = "\n".join(CHANGELOG_PATH.read_text().splitlines()[:20])
    total_ret = index_df["index_level"].iloc[-1] - 100 if len(index_df) else 0
    cat_rows = "".join(f"<tr><td>{html.escape(c)}</td><td>{v * 100:+.2f}%</td></tr>"
                       for c, v in sorted(cat_cum.items()))
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Backtest report v{get_version()}</title>
<style>body{{font-family:sans-serif;margin:2em;max-width:960px}}
table{{border-collapse:collapse;margin:1em 0}}
td,th{{border:1px solid #ccc;padding:4px 10px;font-size:13px;text-align:right}}
th{{background:#eee}} pre{{background:#f6f6f6;padding:1em;overflow-x:auto}}</style>
</head><body>
<h1>Top Polymarket traders - backtest report (strategy v{get_version()})</h1>
<p>Generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC.
Weekly backtest of steps 1-4 on the current selection logic.</p>

<h2>Key metrics</h2>
<table>
<tr><th>total return</th><td>{total_ret:+.2f}%</td></tr>
<tr><th>max drawdown</th><td>{_index_drawdown(index_df) * 100:.2f}%</td></tr>
<tr><th>best week</th><td>{index_df['weekly_return'].max() * 100:+.2f}%</td></tr>
<tr><th>worst week</th><td>{index_df['weekly_return'].min() * 100:+.2f}%</td></tr>
<tr><th>weeks</th><td>{len(index_df)}</td></tr>
</table>

<h2>Top Polymarket Index</h2>
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
