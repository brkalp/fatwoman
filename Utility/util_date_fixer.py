
for ticker_symbol in Vol_chain_tickers:
    print(ticker_symbol)
    # data_save_loc_total = Optionchain_loc(ticker_symbol = ticker_symbol, db_type='Total') # os.path.join(Vol_Output_Folder, 'Total_' + ticker_symbol + '_OptionsChain.csv')
    data_save_loc_total = Optionchain_loc(ticker_symbol = ticker_symbol, db_type='Latest') # os.path.join(Vol_Output_Folder, 'Total_' + ticker_symbol + '_OptionsChain.csv')
    total_csv = pd.read_csv(data_save_loc_total, dtype=Optionchain_dtype_dict)
    # print(total_csv.head()['Expiration_Date'])
    total_csv['Expiration_Date'] = pd.to_datetime(total_csv['Expiration_Date'],format='mixed').dt.strftime('%d/%m/%Y')
    # print(total_csv.head()['Expiration_Date'])
    total_csv.to_csv(data_save_loc_total, index = False)