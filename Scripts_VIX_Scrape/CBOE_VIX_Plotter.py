""" Created on 07-03-2024 03:30:12 @author: ripintheblue """
import fatwoman_log_setup
from fatwoman_log_setup import script_end_log
import logging
import pandas as pd
# from fatwoman_log_setup import script_end_log
from fatwoman_dir_setup import CBOE_Scrape_Data_File, VIX_Scrape_folder, CBOE_Scrape_timestamp_format, CBOE_Plotter_Output_File
from bokeh.plotting import figure, show, output_file
from bokeh.models import ColumnDataSource, HoverTool, LinearColorMapper, ColorBar
from bokeh.transform import transform
from bokeh.layouts import column
from bokeh.palettes import Viridis256
from bokeh.io import curdoc
from bokeh.models import HoverTool
import datetime
import os
curdoc().theme = 'night_sky'

os.chdir(VIX_Scrape_folder)
timestamp_format = CBOE_Scrape_timestamp_format
last_x_days = 10
output_file(CBOE_Plotter_Output_File)

# read and filter by monthly & last x days data
df0 = pd.read_csv(CBOE_Scrape_Data_File)
df0 = df0[df0['Maturity'] != 'VIX'].copy()
# dfvix = df0[df0['Maturity'] == 'VIX']
df0['Timestamp'] = pd.to_datetime(df0['Timestamp'], format=timestamp_format) 
df0['Maturity'] = pd.to_datetime(df0['Maturity'], format='%m/%d/%Y') #CBOE_RAW_timestamp_format = '%m/%d/%Y'
# data operations
 # last days
daily_last_values = df0.groupby(df0['Timestamp'].dt.date)['Timestamp'].max()
last_10_days_last_values = daily_last_values.sort_values(ascending=False).head(last_x_days) # last days
df1 = df0[df0['Timestamp'].isin(last_10_days_last_values)] # last days
# Low volume contracts
median_per_contract = df1.groupby('Maturity')['Volume'].mean() # monthly contracts
monthly_contract_list = median_per_contract[median_per_contract >= 1].index.tolist() # monthly contracts
df2 = df1[df1['Maturity'].isin(monthly_contract_list)] # df1 is filtered on monthly contracts
# Sorting and cleaning matured
df2 = df2.sort_values(by=['Maturity', 'Timestamp'],ascending=[True, True])
df2 = df2[df2['Maturity'] > df2['Timestamp'].max()] # take out matured contracts
df3 = df2[['Maturity','Settlement','Timestamp']].copy() # only needed columns


# Plotting
# color palette
df3['Ts_ord'] = df3['Timestamp'].apply(lambda x: x.toordinal())
mindate, maxdate = df3['Ts_ord'].min(), df3['Ts_ord'].max()
df3['color'] ='blue'
# Define the plot
p = figure(x_axis_type='datetime', title="VIX term structure over Last %s Days" %last_x_days, height=600, width=1000)
xaxis = df3['Maturity'].unique()

# axis
p.yaxis.axis_label = 'Volatility'
p.xaxis.axis_label = 'Maturity of futures'
# unique_maturities = df2['Maturity'].unique()

# Define the hover tool
hover = HoverTool(tooltips=[
        ("Settlement", "@Settlement"),
        ("Timestamp", "@Timestamp{%F}")
    ], formatters={
        '@Timestamp': 'datetime'  # Use the datetime formatter
    })
p.add_tools(hover)


base_alpha = 0.1
alpha_inc = (1 - base_alpha) / len(df3['Timestamp'].unique())
alpha_inc_temp = 0
# Plot each maturity with color mapping
for maturity, group in df3.groupby('Timestamp'):
    alpha = base_alpha + alpha_inc_temp
    color = group['color'].iloc[0]
    Ts_ord = group['Ts_ord'].iloc[0]
    label = str(pd.to_datetime(group['Timestamp'].iloc[0]).date())
    line_size = 2
    circle_size = 10
    if mindate == Ts_ord: color = 'yellow'
    if maxdate == Ts_ord: color = 'red'; line_size = 5; circle_size = 12
    p.line('Maturity', 'Settlement', source=ColumnDataSource(group), color = color, line_width=line_size, legend_label=label, alpha=alpha)
    p.circle(x='Maturity', y='Settlement', source=ColumnDataSource(group), size=circle_size, color=color, legend_label=label, alpha=alpha)
    alpha_inc_temp += alpha_inc

show(p)
today_date = datetime.datetime.now().strftime("%d %B %Y")
with open(CBOE_Plotter_Output_File, "r") as file:
    original_content = file.read()

# Re-open the file in write mode to modify it
with open(CBOE_Plotter_Output_File, "w") as file:
    # Append new style at the end
    file.write("""
    <style>
    body {
        background-color: #000000;
    }
    </style>
    """)
    # Write new content (title with today's date) at the beginning
    file.write(f"<h1 style='color: white; text-align: left; font-size: 20px;'>{today_date}</h1>")
    # Write back the original content
    file.write(original_content)

script_end_log()




# test values
# df2.pivot_table(index='Maturity', columns='Timestamp', values='Settlement', aggfunc='min')
# p.add_layout(ColorBar(color_mapper=c_mapper, label_standoff=12, location=(0,0), title='Timestamp'), 'right') no need

# c_mapper = LinearColorMapper(palette=Viridis256, low=mindate, high=maxdate)
# df3['color'] = [c_mapper.palette[int((mindate-x)/(maxdate-mindate) * (len(c_mapper.palette) - 1))] for x in df3['Ts_ord']]