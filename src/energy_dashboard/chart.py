import math

from typing import Dict

import pandas as pd

from bokeh.embed import components
from bokeh.models import ColumnDataSource
from bokeh.models import NumeralTickFormatter, DatetimeTickFormatter, HoverTool, Range1d
from bokeh.plotting import figure

from energy_dashboard.models import StreamChartDataRequest


def create_context(div, script):
    context = {
        "script": script.replace("\n", " "),
        "div": div.replace("\n", " "),
    }
    return context


def prepare_data(chart_state):
    values = [value for value in chart_state["y_state"]]
    hours = [period for period in chart_state["x_state"]]
    source = ColumnDataSource(data=dict(hours=hours, values=values))
    return source


def create_figure(hours):
    fig = figure(
        x_axis_type="datetime",
        height=500,
        tools="xpan",
        width=1250,
        title=f"MISO - Hour: {max(hours)}",
    )
    return fig


def format_figure(fig, params: StreamChartDataRequest):
    fig.title.align = "left"
    fig.title.text_font_size = "1em"
    fig.yaxis[0].formatter = NumeralTickFormatter(format="0.0a")
    fig.yaxis.axis_label = "Megawatt Hours"
    fig.y_range.start = 50000
    fig.y_range.end = 125000
    fig.xaxis.major_label_orientation = math.pi / 4

    # Convert start_date and end_date from string to datetime
    fig.x_range = Range1d(
        start=pd.Timestamp(params.start_date), end=pd.Timestamp(params.end_date)
    )

    fig.xaxis.ticker.desired_num_ticks = 24
    fig.xaxis.formatter = DatetimeTickFormatter(
        days="%m/%d/%Y, %H:%M:%S",  # Format for day-level ticks
        hours="%m/%d/%Y, %H:%M:%S",  # Format for hour-level ticks
    )
    return fig


def add_line_and_hover(fig, source):
    fig.line(
        x="hours",
        y="values",
        source=source,
        line_width=2,
    )
    hover = HoverTool(
        tooltips=[
            ("Value", "@values{0.00}"),
            ("Hours", "@hours{%F %T}"),
        ],
        formatters={
            "@hours": "datetime",
        },
        mode="vline",
        show_arrow=False,
    )
    fig.add_tools(hover)
    return fig


def create_chart(chart_state: Dict, params: StreamChartDataRequest):
    source = prepare_data(chart_state)
    fig = create_figure(chart_state["x_state"])
    fig = format_figure(fig, params)
    fig = add_line_and_hover(fig, source)
    script, div = components(fig)
    return div, script
