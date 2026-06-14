""" Created on 06-11-2026 20:09:22 @author: ripintheblue """
import logging
import datetime
import fatwoman_log_setup
from fatwoman_api_setup import ALPACA_KEYS
from fatwoman_log_setup import script_end_log
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetPortfolioHistoryRequest
from telegram_bot import tg_bot
 
PAPER = True
today = datetime.date.today()
today_str = today.strftime("%Y-%m-%d")
sections = [f"-- PnL Report {today_str} --"]
 
for account_name, (key, secret) in ALPACA_KEYS.items():
    client    = TradingClient(key, secret, paper=PAPER)
    account   = client.get_account()
    equity    = float(account.equity)
    daily_pnl = equity - float(account.last_equity)
    positions = client.get_all_positions()
    total_pos = sum(float(p.market_value) for p in positions)
 
    pos_lines = "\n".join(
        f"  {p.symbol}: {float(p.unrealized_plpc)*100:+.2f}% | {float(p.market_value)/equity*100:.1f}% of pf"
        for p in positions
    ) or "  No open positions."
 
    hist = client.get_portfolio_history(history_filter=GetPortfolioHistoryRequest(period="5D", timeframe="1D"))
    hist_lines = " | ".join(
        f"{datetime.datetime.fromtimestamp(ts).strftime('%a')}: {pct*100:+.2f}%"
        for ts, pct in zip(hist.timestamp, hist.profit_loss_pct)
        if pct is not None
    )
 
    sections.append(
        f"\n[{account_name}]\n"
        f"Account: ${equity:,.2f} | Positions: ${total_pos:,.2f} | Daily PnL: ${daily_pnl:+.2f}\n"
        f"Last 5D: {hist_lines}\n"
        f"{pos_lines}"
    )
 
daily_profits = "\n".join(
    for i in range(4, -1, -1)
)
 
tg_bot.notify_listeners("\n".join(sections))
logging.info("PnL report sent.")
script_end_log()