""" Created on 07-03-2024 03:30:12 @author: ripintheblue """
import pandas as pd
# from fatwoman_log_setup import script_end_log
from fatwoman_dir_setup import CBOE_Scrape_Data_File
from bokeh.plotting import figure, show, output_file
from bokeh.models import ColumnDataSource, HoverTool, LinearColorMapper
from bokeh.layouts import column
from bokeh.palettes import Viridis256
from bokeh.io import curdoc

# Assuming CBOE_Scrape_Data_File is defined elsewhere or replace with a direct filename

df = pd.read_csv(CBOE_Scrape_Data_File)  # Replace with your file path

# different plots
# Converting Volume to numeric and filtering
df['Volume'] = pd.to_numeric(df['Volume'], errors='coerce')
filtered_df = df[df['Volume'] > 5]

# Converting timestamp to datetime
filtered_df['timestamp'] = pd.to_datetime(filtered_df['timestamp'], format='%d/%m/%Y %H:%M')

# Sorting by timestamp and getting the last 10 records per contract
filtered_df['Maturity'] = pd.to_datetime(filtered_df['Maturity'], errors='coerce')
last_10_per_contract = filtered_df.groupby('Maturity').apply(lambda x: x.nlargest(10, 'timestamp')).reset_index(drop=True)

# Converting Settlement to numeric
last_10_per_contract['Settlement'] = pd.to_numeric(last_10_per_contract['Settlement'], errors='coerce')

# Output to HTML file
output_file("last_10_settle_values.html")

# Creating Bokeh plots
plots = []

for maturity in last_10_per_contract['Maturity'].unique():
    contract_data = last_10_per_contract[last_10_per_contract['Maturity'] == maturity]
    source = ColumnDataSource(contract_data)
    
    p = figure(x_axis_type='datetime', title=f'Contract: {maturity}', height=300, width=800)
    p.line(x='timestamp', y='Settlement', source=source, line_width=2, legend_label=str(maturity))
    p.circle(x='timestamp', y='Settlement', source=source, size=5)
    
    p.xaxis.axis_label = 'Timestamp'
    p.yaxis.axis_label = 'Settlement'
    
    plots.append(p)

show(column(*plots))
# # Read data
# df = pd.read_csv(CBOE_Scrape_Data_File)  # Replace with your file path

# # Convert Volume to numeric and filter
# df['Volume'] = pd.to_numeric(df['Volume'], errors='coerce')
# filtered_df = df[df['Volume'] > 5]

# # Convert timestamp to datetime
# filtered_df['timestamp'] = pd.to_datetime(filtered_df['timestamp'], format='%d/%m/%Y %H:%M')

# # Sort by timestamp and select the last 10 records per contract
# filtered_df['Maturity'] = pd.to_datetime(filtered_df['Maturity'], errors='coerce')
# filtered_df = filtered_df.sort_values('timestamp', ascending=False)
# last_10_per_contract = filtered_df.groupby('Maturity').head(10).reset_index(drop=True)

# # Convert Settlement to numeric
# last_10_per_contract['Settlement'] = pd.to_numeric(last_10_per_contract['Settlement'], errors='coerce')

# # Convert timestamps to numeric values for color mapping
# last_10_per_contract['timestamp_numeric'] = last_10_per_contract['timestamp'].astype('int64') / 10**9

# # Prepare the output HTML file
# output_file("last_10_settle_values.html")

# # Create a Bokeh plot with dark theme if needed
# dark_theme = True
# p = figure(title='Settlement Values Over Time by Maturity', height=600, width=1000, x_axis_type='datetime')

# # Create a color mapper
# color_mapper = LinearColorMapper(palette=Viridis256, low=min(last_10_per_contract['timestamp_numeric']), high=max(last_10_per_contract['timestamp_numeric']))

# # Plot each line with points
# for maturity in last_10_per_contract['Maturity'].unique():
#     contract_data = last_10_per_contract[last_10_per_contract['Maturity'] == maturity]
#     source = ColumnDataSource(contract_data)
    
#     p.line('Maturity', 'Settlement', source=source, line_width=2, color='navy', legend_label=str(maturity))
#     p.circle('Maturity', 'Settlement', source=source, size=5, color={'field': 'timestamp_numeric', 'transform': color_mapper})

# # Configure hover tool
# hover = HoverTool(tooltips=[
#     ("Maturity", "@Maturity{%F}"),
#     ("Last", "@Last"),
#     ("Change", "@Change"),
#     ("High", "@High"),
#     ("Low", "@Low"),
#     ("Settlement", "@Settlement"),
#     ("Volume", "@Volume"),
#     ("Timestamp", "@timestamp{%F %T}")
# ], formatters={'@Maturity': 'datetime', '@timestamp': 'datetime'})
# p.add_tools(hover)

# # Apply dark theme if selected
# if dark_theme:
#     p.background_fill_color = "#2F2F2F"
#     p.border_fill_color = "#2F2F2F"
#     p.outline_line_color = "#444444"
#     p.xaxis.axis_label_text_color = "#EDEDED"
#     p.yaxis.axis_label_text_color = "#EDEDED"
#     p.xaxis.major_label_text_color = "#EDEDED"
#     p.yaxis.major_label_text_color = "#EDEDED"
#     p.title.text_color = "#EDEDED"
#     p.legend.label_text_color = "#EDEDED"
#     p.legend.background_fill_color = "#2F2F2F"
#     p.legend.border_line_color = "#444444"
#     p.legend.title_text_color = "#EDEDED"

# p.xaxis.axis_label = 'Maturity'
# p.yaxis.axis_label = 'Settlement'
# p.legend.title = 'Maturity'
# p.legend.location = 'top_right'

# # Display the plot
# show(p)

# # Same plot
# # Converting Volume to numeric and filtering
# df['Volume'] = pd.to_numeric(df['Volume'], errors='coerce')
# filtered_df = df[df['Volume'] > 5]

# # Converting timestamp to datetime
# filtered_df['timestamp'] = pd.to_datetime(filtered_df['timestamp'])

# # Sorting by timestamp and getting the last 10 records per contract
# filtered_df['Maturity'] = pd.to_datetime(filtered_df['Maturity'], errors='coerce')
# last_10_per_contract = filtered_df.groupby('Maturity').apply(lambda x: x.nlargest(10, 'timestamp')).reset_index(drop=True)

# # Converting Settlement to numeric
# last_10_per_contract['Settlement'] = pd.to_numeric(last_10_per_contract['Settlement'], errors='coerce')

# # Output to HTML file
# output_file("last_10_settle_values.html")

# # Creating a Bokeh plot
# p = figure(x_axis_type='datetime', title='Settlement Values Over Time by Maturity', height=600, width=1000)

# colors = Category10[10]

# for i, maturity in enumerate(last_10_per_contract['Maturity'].unique()):
#     contract_data = last_10_per_contract[last_10_per_contract['Maturity'] == maturity]
#     source = ColumnDataSource(contract_data)
    
#     p.line(x='timestamp', y='Settlement', source=source, line_width=2, color=colors[i % len(colors)], legend_label=str(maturity))
#     p.circle(x='timestamp', y='Settlement', source=source, size=5, color=colors[i % len(colors)])

# p.xaxis.axis_label = 'Timestamp'
# p.yaxis.axis_label = 'Settlement'
# p.legend.title = 'Maturity'
# p.legend.location = 'top_left'

# show(p)