from flows.ticker_management_flow import flow

if __name__ == "__main__":
    flow(date="2025-10-16", ticker="AAPL", notify_users=True)