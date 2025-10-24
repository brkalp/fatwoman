""" flow.db
    SELECT COUNT(id),ticker, SUM(profit_made) as all_profit FROM flow GROUP BY ticker ORDER BY COUNT(id) DESC
    
    # order'ın NULL olduğu rowları sayan bir SELECT
    # kaç tane doğru tahmin ettiğine dair bir %
    # kaç kere sat emrinin kaç kere al emrinin tuttuğunu saydır

    
    conn.execute("ATTACH DATABASE 'headlines.sqlite' AS headlines_db;")
    conn.execute("ATTACH DATABASE 'flow.sqlite' AS flow_db;")

 
 """

def get_order_null_ratio()->float:
    pass

def get_profit_all_time()->int:
    pass

def get_profit_last_days(until_day_count:int=3)->list:
    # should return the profits of last 3 days
    pass

def get_EOD_message():
    
    text = f""
    # should have the profit of last 3 days, the ticker analyses of the last 3 days
    pass



