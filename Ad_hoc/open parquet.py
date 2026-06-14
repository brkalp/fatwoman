""" Created on 06-09-2026 21:49:15 @author: ripintheblue """
import logging
import fatwoman_log_setup
from fatwoman_log_setup import script_end_log
script_end_log()

import os
import pandas as pd
from fatwoman_dir_setup import fatwoman_base_path
df0 = pd.read_parquet(os.path.join(fatwoman_base_path, 'Ad_hoc', 'filtered_v2_publish.parquet'))
df = df0.copy()
# df.head()
# df.info()
# df.describe()
# df.columns
df = df.sort_values('timestamp', ascending=False)
# df = df.sort_values('anchor_price', ascending=False)
# df = df[df['ticker'] == 'KCR.HE']
# df['anchor_price'] = df['anchor_price'].round(3)
# df.to_clipboard(excel=True)
df = df[df['sentiment_category'].notna()]
df.to_clipboard(decimal=',')
# count unique columns
# df.nunique()
