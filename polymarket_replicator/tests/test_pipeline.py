"""End-to-end (mock mode) and unit tests for the replicator flow.

The pipeline runs as real subprocesses - the same way cron runs it - inside
an isolated POLYFLOW_RUNTIME, so live data/ and logs/ are never touched.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

PROJ = Path(__file__).resolve().parents[1]
SCRIPTS = PROJ / "scripts"


# --- unit tests -------------------------------------------------------------

def test_version_parsing():
    sys.path.insert(0, str(PROJ))
    from core.versioning import get_version
    v = get_version()
    assert len(v) == 2 and v.isdigit() and v >= "01"


def test_max_drawdown():
    sys.path.insert(0, str(PROJ))
    from core.metrics import max_drawdown
    assert max_drawdown([], 100) == 0.0
    assert max_drawdown([10, -20, 5], 100) == pytest.approx(20 / 110, abs=1e-4)
    assert max_drawdown([5, 5, 5], 100) == 0.0


def test_selection_logic():
    sys.path.insert(0, str(PROJ))
    sys.path.insert(0, str(SCRIPTS))
    from s03_select_users import select
    df = pd.DataFrame([
        # passes, best score
        dict(proxy_wallet="a", user_name="a", category="Crypto", account_size=50_000,
             n_trades_30d=40, accuracy=0.7, max_drawdown=0.1, total_pnl_30d=5000),
        # fails accuracy
        dict(proxy_wallet="b", user_name="b", category="Crypto", account_size=50_000,
             n_trades_30d=40, accuracy=0.4, max_drawdown=0.1, total_pnl_30d=5000),
        # fails account size
        dict(proxy_wallet="c", user_name="c", category="Crypto", account_size=500,
             n_trades_30d=40, accuracy=0.7, max_drawdown=0.1, total_pnl_30d=5000),
        # passes, lower score
        dict(proxy_wallet="d", user_name="d", category="Crypto", account_size=20_000,
             n_trades_30d=15, accuracy=0.6, max_drawdown=0.3, total_pnl_30d=100),
    ])
    cfg = dict(users_per_category=3, min_account_size=10_000, min_trades_30d=10,
               min_accuracy=0.55, max_drawdown=0.35, min_total_pnl_30d=0)
    picked = select(df, cfg)
    assert list(picked["proxy_wallet"]) == ["a", "d"]
    assert picked["weight"].sum() == pytest.approx(1.0)
    assert picked.iloc[0]["score"] > picked.iloc[1]["score"]


# --- end-to-end pipeline in mock mode ---------------------------------------

@pytest.fixture(scope="module")
def runtime(tmp_path_factory):
    home = tmp_path_factory.mktemp("polyflow_runtime")
    env = dict(os.environ, POLYFLOW_MOCK="1", POLYFLOW_RUNTIME=str(home),
               PYTHONPATH=str(PROJ))
    return home, env


def _run(script, env, *args):
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / script), *args],
        env=env, capture_output=True, text=True, timeout=600)
    assert proc.returncode == 0, f"{script} failed:\n{proc.stdout}\n{proc.stderr}"
    return proc


def _latest(home, prefix):
    files = sorted((home / "data").glob(f"{prefix}_*.csv"))
    assert files, f"no output for {prefix}"
    return pd.read_csv(files[-1])


def test_e2e_daily_steps(runtime):
    home, env = runtime
    _run("s01_user_fetch.py", env)
    uni = _latest(home, "01_polymarket_top_users_by_category")
    assert {"category", "proxy_wallet", "holding_usdc"} <= set(uni.columns)
    assert uni["category"].nunique() >= 5 and len(uni) > 500

    _run("s02_user_data_fetch.py", env)
    data = _latest(home, "02_user_data")
    assert {"account_size", "accuracy", "max_drawdown", "total_pnl_30d"} <= set(data.columns)
    assert data["proxy_wallet"].is_unique

    _run("s03_select_users.py", env)
    sel = _latest(home, "03_selected_user_list")
    assert len(sel) > 0
    assert (sel.groupby("category").size() <= 3).all()
    assert sel.groupby("category")["weight"].sum().round(6).eq(1.0).all()


def test_e2e_hourly_steps_and_dedupe(runtime):
    home, env = runtime
    _run("s04_signal_generation.py", env)
    plan1 = _latest(home, "04_trade_plan")
    trades = _latest(home, "04_users_trade_list")
    assert {"signal_id", "reason", "my_notional_usdc", "side"} <= set(plan1.columns)
    assert len(trades) >= len(plan1)
    assert set(plan1["reason"]) <= {"user_open_trade", "user_close_trade",
                                    "user_out_of_index"}

    # same hour, second run: mock trades are identical -> full dedupe (the
    # merged plan holds exactly the same signal ids, nothing new generated)
    _run("s04_signal_generation.py", env)
    plan2 = _latest(home, "04_trade_plan")
    assert set(plan2["signal_id"]) == set(plan1["signal_id"]), \
        "dedupe failed - duplicate signals generated"
    assert plan2["signal_id"].is_unique

    _run("s05_trade_execution.py", env)
    ex = _latest(home, "05_execution")
    assert {"status", "fill_price", "slippage_bps"} <= set(ex.columns)
    account = json.loads((home / "data/state/paper_account.json").read_text())
    filled_buys = ex[(ex["status"] == "FILLED") & (ex["side"] == "BUY")]
    if len(filled_buys):
        assert account["cash"] < account["equity_start"]
        assert len(account["positions"]) > 0

    # risk cap: category notionals never exceed the config limit
    cfg = json.loads((PROJ / "config/settings.json").read_text())
    by_cat = {}
    for pos in account["positions"].values():
        by_cat[pos["category"]] = (by_cat.get(pos["category"], 0)
                                   + pos["shares"] * pos["avg_price"])
    assert all(v <= cfg["execution"]["max_category_notional"] * 1.05
               for v in by_cat.values())

    _run("s06_pnl_reporter.py", env)
    rep = _latest(home, "06_report")
    assert {"pnl", "execution"} <= set(rep["section"])


def test_halt_file_blocks_execution(runtime):
    home, env = runtime
    (home / "HALT").touch()
    try:
        before = len(list((home / "data").glob("05_execution_*.csv")))
        _run("s05_trade_execution.py", env)
        after = len(list((home / "data").glob("05_execution_*.csv")))
        assert before == after, "HALT file did not stop execution"
    finally:
        (home / "HALT").unlink()


def test_backtester(runtime):
    home, env = runtime
    _run("backtester.py", env, "--weeks", "3")
    idx_files = sorted((home / "data/backtest").glob("bt_index_*.csv"))
    html_files = sorted((home / "data/backtest").glob("bt_report_*.html"))
    assert idx_files and html_files
    idx = pd.read_csv(idx_files[-1])
    assert len(idx) == 3
    assert (idx["index_level"] > 0).all()
    report = html_files[-1].read_text()
    assert "Top Polymarket Index" in report and "Bias notes" in report
