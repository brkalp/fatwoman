"""Shared performance metrics used by step 2, step 6 and the backtester."""


def max_drawdown(pnl_series, base: float) -> float:
    """Max peak-to-trough drawdown of cumulative pnl, as a fraction of base
    equity. Returns 0.0 for empty input or non-positive base."""
    if not pnl_series or base <= 0:
        return 0.0
    equity = base
    peak = base
    worst = 0.0
    for pnl in pnl_series:
        equity += pnl
        peak = max(peak, equity)
        if peak > 0:
            worst = max(worst, (peak - equity) / peak)
    return round(worst, 4)


def total(series) -> float:
    return round(sum(series), 2)
