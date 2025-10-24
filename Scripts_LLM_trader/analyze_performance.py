""" flow.db
    SELECT COUNT(id),ticker, SUM(profit_made) as all_profit FROM flow GROUP BY ticker ORDER BY COUNT(id) DESC
    
 
 """