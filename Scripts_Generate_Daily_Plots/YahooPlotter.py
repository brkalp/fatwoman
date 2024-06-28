""" Created on 10-28-2023 17:06:42 @author: ripintheblue """
import fatwoman_log_setup
from fatwoman_log_setup import script_end_log
from fatwoman_dir_setup import YahooDownload_Output_File, YahooDownload_Outputs_SEK, YahooPlotter_Output_File
import logging
import pandas as pd
import numpy as np
from bokeh.layouts import gridplot
import datetime
from bokeh.plotting import figure, show, output_notebook, output_file
from bokeh.models import DatetimeTickFormatter, HoverTool, ColumnDataSource, NumeralTickFormatter, FixedTicker, Label
from bokeh.themes import built_in_themes
from bokeh.io import curdoc
from bokeh.models import BoxSelectTool, CustomJS, LabelSet
import socket
import os

curdoc().theme = 'night_sky'

logging.info('Reading %s' %YahooDownload_Output_File)
print('Reading %s' %YahooDownload_Output_File)

output_file(YahooPlotter_Output_File)
df0 = pd.read_csv(YahooDownload_Output_File)
df1 = df0.tail(45).set_index('Date') # last 45 days are taken into account
df1.index = pd.to_datetime(df1.index)

df2 = pd.read_csv(YahooDownload_Outputs_SEK)
df2 = df2.tail(45).set_index('Date') # last 45 days are taken into account
df2.index = pd.to_datetime(df2.index)

red_color_list = [
    'VIX',
    'SP500',
    'LongTermBond',
    'USDSEK',
    'OMX',
    'BIST'
    ]

plots = []
for col in df1.columns:
    # variables to plot
    # logging.info('Attempt at %s' %(col))
    print('Attempt at %s' %(col), end = ' ')

    # main settings
    p = figure(width=370, height=270, title=col, x_axis_type="datetime", min_border=40,tools="reset,save")

    col_data = df1[col]
    first_non_nan_value = col_data.loc[col_data.first_valid_index()] # col_data.iloc[0]
    col_return = (col_data / first_non_nan_value - 1) * 100
    total_return = col_return.dropna().iloc[-1] if len(col_return.dropna()) > 0 else 0
    source_data = ColumnDataSource(data={'x': df1.index,'y': col_data,'return': col_return})
    
    # Add line and dots
    color = 'red' if col in red_color_list else 'blue'
    line = p.line('x', 'y', source=source_data, line_width=4, line_color=color)  # Set line color to blue
    p.circle('x', 'y', source=source_data, size=6, color=color)  # Set circle color to red

    # Format the numbers in plots
    # p.xaxis.formatter = DatetimeTickFormatter(days=["%d-%b"], months=["%d-%b"], years=["%Y"])
    p.yaxis.formatter = NumeralTickFormatter(format="0.00") if col_data.max() < 100 else NumeralTickFormatter(format="0")

    # Formatting y axis - split into 5
    finite_values = col_data.dropna().values
    if len(finite_values) > 0: p.yaxis.ticker = FixedTicker(ticks=list(np.linspace(np.min(finite_values), np.max(finite_values), 5)))

    # Adding Mouse Hover
    hover = HoverTool(mode='vline')
    hover.tooltips = [("Price", "@y{0.2f}"),("Date", "@x{%d-%b}"),("% Ret", "@return{0.2f}%")]
    hover.formatters = {"@x": "datetime"}
    hover.renderers = [line]
    p.add_tools(hover)
    
    # Add CustomJS to compute return based on selection
    box_select = BoxSelectTool(dimensions='width')
    p.add_tools(box_select)
    p.toolbar.active_drag = box_select  # Set the BoxSelectTool as the active drag tool
    label_source = ColumnDataSource(data=dict(x=[], y=[], text=[]))
    # labels = LabelSet(x='x', y='y', text='text', level='glyph',
    #               x_offset=5, y_offset=5, source=label_source, render_mode='canvas',
    #               text_font_style="bold", text_color="white")
    labels = LabelSet(x='x', y='y', text='text', level='glyph',
              x_offset=5, y_offset=5, source=label_source,
              text_font_style="bold", text_color="white")

    p.add_layout(labels)
    
    # Add CustomJS to compute return based on selection
    callback = CustomJS(args=dict(source=source_data, label_source=label_source), code="""
        const indices = source.selected.indices;
        if (indices.length == 0) return;

        let data = source.data;
        let start_price = data['y'][indices[0]];
        let end_price = data['y'][indices[indices.length - 1]];

        let ret = ((end_price / start_price) - 1) * 100;

        // Update the label data source
        label_source.data = {'x': [data['x'][indices[indices.length - 1]]], 
                             'y': [data['y'][indices[indices.length - 1]]], 
                             'text': [ret.toFixed(2) + '%']};
        label_source.change.emit();
    """)
    source_data.selected.js_on_change('indices', callback)
  
    
    # Putting Total Return print into plot
    label = Label(x=6, y=9, x_units='screen', y_units='screen',
                    text=f' {total_return:.2f}%', 
                    text_font_size='10pt', text_align='left', text_color='white')

    p.add_layout(label)
    
    # Finish the plot
    plots.append(p)
    # logging.info('OK')
    print('OK!', end=' ')

grid = gridplot(plots, ncols=3)
logging.info('Saving %s' %YahooPlotter_Output_File)
print('Saving %s' %YahooPlotter_Output_File)
show(grid)

today_date = datetime.datetime.now().strftime("%d %B %Y")

with open(YahooPlotter_Output_File, "r") as file:
    original_content = file.read()

# Re-open the file in write mode to modify it
with open(YahooPlotter_Output_File, "w") as file:
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
