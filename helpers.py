import datetime
import re
from functools import wraps
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from flask import redirect, render_template, session

# Some assistance functions are written by CS50 staff.
# https://cs50.harvard.edu/x/2024/psets/9/finance/

LOCATION_CHART_DIRECTORY = Path("static/location_data")
SEASONS = (
    ("Spring", (3, 4, 5), "#2f855a"),
    ("Summer", (6, 7, 8), "#d69e2e"),
    ("Fall", (9, 10, 11), "#dd6b20"),
    ("Winter", (12, 1, 2), "#3182ce"),
)
CHART_METRICS = (
    ("temp_mean", "Mean temperature", "Temperature (°C)", "#b2182b"),
    ("temp_min", "Minimum temperature", "Temperature (°C)", "#2166ac"),
    ("temp_max", "Maximum temperature", "Temperature (°C)", "#d6604d"),
    ("precip", "Precipitation", "Mean daily precipitation (mm)", "#2166ac"),
)


def apology(message, code=400):
    """Render message as an apology to user."""

    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [
            ("-", "--"),
            (" ", "-"),
            ("_", "__"),
            ("?", "~q"),
            ("%", "~p"),
            ("#", "~h"),
            ("/", "~s"),
            ('"', "''"),
        ]:
            s = s.replace(old, new)
        return s
    return (
        render_template(
            "apology.html",
            top=code,
            bottom=escape(message),
            imgname=session.get("imgname", ""),
        ),
        code,
    )


def _seasonal_history(df, field):
    """Aggregate monthly history into four seasonal values per year."""
    history = df[[field]].copy()
    month_to_season = {
        month: season for season, months, _ in SEASONS for month in months
    }
    history["season"] = history.index.month.map(month_to_season)
    history["year"] = history.index.year + (history.index.month == 12).astype(int)
    return (
        history.groupby(["year", "season"], observed=True)[field]
        .mean()
        .reset_index()
    )


def draw_chart(lat: float, lon: float, df: pd.DataFrame, filename=None):
    """Write an interactive chart with four seasonal lines per selected metric."""
    fig = go.Figure()
    available_metrics = [metric for metric in CHART_METRICS if metric[0] in df]

    for metric_index, (field, _label, _axis_title, _axis_color) in enumerate(
        available_metrics
    ):
        seasonal = _seasonal_history(df, field)
        for season, _months, color in SEASONS:
            values = seasonal[seasonal["season"] == season]
            fig.add_trace(
                go.Scatter(
                    x=values["year"],
                    y=values[field],
                    mode="lines+markers",
                    name=season,
                    legendgroup=season,
                    line=dict(color=color, width=2),
                    marker=dict(color=color, size=6),
                    visible=metric_index == 0,
                    hovertemplate=(
                        f"{season} %{{x}}<br>%{{y:.2f}}<extra></extra>"
                    ),
                )
            )

    buttons = []
    for metric_index, (_field, label, axis_title, axis_color) in enumerate(
        available_metrics
    ):
        first_trace = metric_index * len(SEASONS)
        visible = [
            first_trace <= trace_index < first_trace + len(SEASONS)
            for trace_index in range(len(fig.data))
        ]
        buttons.append(
            dict(
                label=label,
                method="update",
                args=[
                    {"visible": visible},
                    {
                        "title.text": f"Seasonal {label.lower()} at {lat}, {lon}",
                        "yaxis.title.text": axis_title,
                        "yaxis.title.font.color": axis_color,
                        "yaxis.tickfont.color": axis_color,
                    },
                ],
            )
        )

    default_label = available_metrics[0][1] if available_metrics else "Climate data"
    default_axis_title = available_metrics[0][2] if available_metrics else "Value"
    default_axis_color = available_metrics[0][3] if available_metrics else "#18342c"
    fig.update_layout(
        title=dict(text=f"Seasonal {default_label.lower()} at {lat}, {lon}"),
        xaxis=dict(title="Year", dtick=5),
        yaxis=dict(
            title=dict(text=default_axis_title, font=dict(color=default_axis_color)),
            tickfont=dict(color=default_axis_color),
        ),
        hovermode="x unified",
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0
        ),
        margin=dict(t=130),
        template="plotly_white",
        updatemenus=[
            dict(
                active=0,
                buttons=buttons,
                direction="down",
                showactive=True,
                x=0,
                xanchor="left",
                y=1.18,
                yanchor="top",
            )
        ],
    )

    # Save as HTML
    LOCATION_CHART_DIRECTORY.mkdir(parents=True, exist_ok=True)
    output_name = Path(filename).name if filename else f"{lat}_{lon}.html"
    fig.write_html(str(LOCATION_CHART_DIRECTORY / output_name))
    return fig


def is_valid_month(month, start="1950-01", end=None):
    if end is None:
        end = datetime.datetime.today().strftime("%Y-%m")
    try:
        date = datetime.datetime.strptime(month, "%Y-%m")
        start_date = datetime.datetime.strptime(start, "%Y-%m")
        end_date = datetime.datetime.strptime(end, "%Y-%m")
        return start_date <= date <= end_date
    except ValueError:
        return False


def is_valid_username(username):
    return bool(re.match(r"^[a-zA-Z0-9_-]{3,16}$", username))


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


def swap(a, b):
    return b, a
