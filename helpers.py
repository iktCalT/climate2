import datetime
import re
from calendar import month_name
from functools import wraps

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from flask import redirect, render_template, session

# Some assistance functions are written by CS50 staff.
# https://cs50.harvard.edu/x/2024/psets/9/finance/


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


# ChatGPT helped me complete this part. https://chatgpt.com/
def draw_chart(lat: float, lon: float, df: pd.DataFrame, filename=None):
    fig = go.Figure()
    grouped = df.groupby(df.index.month)
    
    color_scale_temp = px.colors.sequential.Hot
    color_scale_precip = px.colors.sequential.Blues
    for month, group in grouped:
        # Line charts for Temperature
        for temp_type in ["temp_mean", "temp_max", "temp_min"]:
            if temp_type not in group:
                continue
            fig.add_trace(
                go.Scatter(
                    x=group.index,
                    y=group[temp_type],
                    mode="lines+markers",
                    name=(
                        f'{temp_type.split("_")[1].title()} Temperature (°C) - '
                        f"{month_name[month]}"
                    ),
                    line=dict(color="red", width=0.5),
                    marker=dict(
                        color=group[temp_type], colorscale=color_scale_temp, size=8
                    ),
                    yaxis="y1",
                )
            )

    # Bar chart for precipitation
    fig.add_trace(
        go.Bar(
            x=df.index,
            y=df["precip"],
            name="Precipitation per day (mm)",
            marker=dict(color=df["precip"], colorscale=color_scale_precip),
            yaxis="y2",
        )
    )

    # Layout and legend
    fig.update_layout(
        xaxis_title='Date',
        yaxis=dict(
            title="Temperature (°C)",
            titlefont=dict(color="red"),
            tickfont=dict(color="red"),
        ),
        yaxis2=dict(
            title="Precipitation per day (mm)",
            titlefont=dict(color="blue"),
            tickfont=dict(color="blue"),
            overlaying="y",
            side="right",
        ),
        template="plotly_white",
    )
    fig.update_layout(
        legend=dict(
            orientation="h", yanchor="bottom", y=1.03, xanchor="left", x=0
        )
    )

    # Save as HTML
    if filename:
        fig.write_html(f"static/location_data/{filename}")
    else:
        fig.write_html(f"static/location_data/{lat}_{lon}.html")


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
