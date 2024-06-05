""" Created on Wed Sept 2 22:40:15 2023 @author: ripintheblue """
import pandas as pd
import glob
import numpy as np
DIR = r"C:/Users/User/Google Drive/Penguen/Personal analytics/Analysis/Trades/DATA/VIX/"
csvPaths = glob.glob("%s*.csv"%DIR)
FF = 'Futures' # Column name
DATE = 'Trade Date' # Column name
pd.set_option('display.float_format', lambda x: '%.2f' % x)

# https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.memory_usage.html
dtypes = ['int64', 'float64', 'complex128', 'object', 'bool']
data = dict([(t, np.ones(shape=5000, dtype=int).astype(t)) for t in dtypes])
df = pd.DataFrame(data)
df.memory_usage(deep=True)
df['object'].astype('category').memory_usage(deep=True) # significant drop in memory for object types. which is the correct type?
# df.memory_usage()

# custom data
df0 = pd.DataFrame()
for csvPath in csvPaths[0:5]:
    dfx = pd.read_csv(csvPath, parse_dates=[DATE])
    # assign allows method chains df.assign(some_col=some_exp).some_other_method_involving_the_new_column() // min 36
    # this also creates a new object, if needed, instead of editing the existing one
    # use inplace=True if memory intensive
    # or assigning is quite pretty with .fillna('Other'), .fillna(0)
    # or extract(r'(\d)+').fillna('20') which pulls out digits. if missing it will fill 20
    # or astype 
    # or contains('Auto') which makes boolean
    # or replace
    # these are all availalbe with the expressions below, but assign allows multiple columns to be assigned at once
    # also assign can be used in a generator expression
    # you can .pipe.display(lambda df: display(df) or df) in the middle to print the dataframe on the way
    dfx['csvName'] = csvPath
    dfx['Diff'] = (dfx['Settle'] / dfx['Settle'].shift(1)) - 1
    df0 = pd.concat([df0,dfx])
 
df0.dtypes # each dtype gets allocated a portion of memory. int64 is a type of numpy. Pandas use numpy to allocate memory.
# float can be floating numbers or int values with missing values
df0.memory_usage(index=True)
df0.memory_usage(deep = True) # type object takes more memory. these are strings
df0.memory_usage(deep = True).sum()
    #If True, introspect the data deeply by interrogating object dtypes for system-level memory consumption, and include it in the returned values.
df0.describe() # note that non-int columns do not show up 

df0.select_dtypes(int).memory_usage(deep = True)
df0.select_dtypes(int).describe()
np.iinfo(np.int8)
np.iinfo(np.int16)
np.iinfo(int)
df1 = df0.select_dtypes(int).astype({'Total Volume':'int16'})
df1.describe()
df1.memory_usage(deep = True)
# df0.select_dtypes('float64')

df0.select_dtypes('float').describe() #are there ints labeled as floats?
    # note that empty rows do not appear in describe
np.finfo(np.float16) #finfo instead of iinfo
df0.query('Diff.isna()')

# df0.apply('dtype').value_counts() # remembered wrong...
df0['Futures'].memory_usage(deep = True) # 11011
df0['Futures'].value_counts(dropna=False)
df1 = df0.astype({'Futures':'category'})
df1['Futures'].memory_usage(deep = True) # 1804

df2 = df0['Open Interest']
df2.isin({495})
df2.where(df2.isin({495}),'This')
np.select([df2.isin({495})],['This'], 'Other')