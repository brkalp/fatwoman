""" Created on 07-03-2024 03:30:12 @author: ripintheblue """
import pandas as pd
# from fatwoman_log_setup import script_end_log
from fatwoman_dir_setup import CBOE_Scrape_Data_File, VIX_Scrape_folder
from bokeh.plotting import figure, show, output_file
from bokeh.models import ColumnDataSource, HoverTool, LinearColorMapper, ColorBar
from bokeh.transform import transform
from bokeh.layouts import column
from bokeh.palettes import Viridis256
from bokeh.io import curdoc

os.chdir(VIX_Scrape_folder)
timestamp_format = '%d/%m/%Y'
output_file("last_10_settle_values.html")
last_x_days = 5

# read and filter by monthly & last x days data
df0 = pd.read_csv(CBOE_Scrape_Data_File)
df0['Timestamp'] = pd.to_datetime(df0['Timestamp'], format=timestamp_format)
# monthly contracts
median_per_contract = df0.groupby('Maturity')['Volume'].median()
monthly_contract_list = median_per_contract[median_per_contract > 10].index.tolist()
df1 = df0[df0['Maturity'].isin(monthly_contract_list)] # df1 is filtered on monthly contracts
# last 10 days
daily_last_values = df1.groupby(df1['Timestamp'].dt.date)['Timestamp'].max()
last_10_days_last_values = daily_last_values.sort_values(ascending=False).head(last_x_days)
df2 = df1[df1['Timestamp'].isin(last_10_days_last_values)] # df2 is filtered on last x days
df2['Maturity'] = pd.to_datetime(df2['Maturity'])
df2 = df2.sort_values(by=['Maturity', 'Timestamp'],ascending=[True, True])
# take out matured contracts
df2 = df2[df2['Maturity'] > df2['Timestamp'].max()]

# test values
# df2.pivot_table(index='Maturity', columns='Timestamp', values='Settlement', aggfunc='min')

# only needed columns
df3 = df2[['Maturity','Settlement','Timestamp']].copy()

# color palette
df3['Ts_ord'] = df3['Timestamp'].apply(lambda x: x.toordinal())
mindate, maxdate = df3['Ts_ord'].min(), df3['Ts_ord'].max()
c_mapper = LinearColorMapper(palette=Viridis256, low=mindate, high=maxdate)
df3['color'] = [c_mapper.palette[int((x-mindate)/(maxdate-mindate) * (len(c_mapper.palette) - 1))] for x in df3['Ts_ord']]

# Define the plot
p = figure(x_axis_type='datetime', title="Settlements over Last 10 Days", height=800, width=1300)
p.xaxis.axis_label = 'Maturity Date'
p.yaxis.axis_label = 'Settlement Price'
p.add_layout(ColorBar(color_mapper=c_mapper, label_standoff=12, location=(0,0), title='Timestamp'), 'right')

# Plot each maturity with color mapping
for maturity, group in df3.groupby('Timestamp'):
    color = group['color'].iloc[0]
    label = str(pd.to_datetime(group['Timestamp'].iloc[0]).date())
    p.line('Maturity', 'Settlement', source=ColumnDataSource(group),
           line_width=2, legend_label=label, color = color)
    # plot circle if last date
    if maxdate == group['Ts_ord'].max(): 
        p.circle(x='Maturity', y='Settlement', source=ColumnDataSource(group), size=10, 
            color=transform('Ts_ord', c_mapper), legend_label=label)

# Show the plot
show(p)



