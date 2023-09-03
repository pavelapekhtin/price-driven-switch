import os

import pandas as pd
import plotly.graph_objects as go  # type: ignore
import streamlit as st

from price_driven_switch.backend.configuration import load_setpoints, save_api_key
from price_driven_switch.backend.tibber import TibberConnection


def load_setpoints_cached():
    return load_setpoints()


def generate_sliders(vlaues: dict[str, float]) -> dict[str, float]:
    new_dict = vlaues.copy()
    for key, value in new_dict.items():
        slider_value = int(value * 100)
        new_value = st.slider(label=key, min_value=0, max_value=100, value=slider_value)
        new_dict[key] = new_value / 100.0
    return new_dict


def plot_prices(prices_df: pd.DataFrame, offset_prices: dict) -> None:
    if prices_df.empty:
        st.write("Tomorrow's prices are become available after 13:00")
        return

    sorted_offset_prices = sorted(
        offset_prices.items(), key=lambda x: x[1], reverse=True
    )

    line_colors = [
        "#ff0000",
        "#009bfb",
        "#00ff98",
        "#b402c1",
        "#ff8c00",
        "#710202",
        "#0000ff",
        "#ff00ff",
        "#00ffff",
    ]  # Extend this list as needed

    fig = go.Figure()

    # Add bars to the plot
    for i, (key, price) in enumerate(sorted_offset_prices):
        color = line_colors[i % len(line_colors)]  # Use modulo to avoid IndexError

        bar_color = [
            color if bar_price <= price else "rgba(128, 128, 128, 0.3)"
            for bar_price in prices_df["Prices"]
        ]

        fig.add_trace(
            go.Bar(
                x=prices_df.index,
                y=prices_df["Prices"],
                marker_color=bar_color,
                name=key,
                showlegend=False,
            )
        )

        # Add vertical line for the offset price
        fig.add_shape(
            go.layout.Shape(
                type="line",
                xref="x",
                yref="y",
                x0=min(prices_df.index),
                x1=max(prices_df.index),
                y0=price,
                y1=price,
                line=dict(color=color, width=2),
            )
        )
        # Dummy scatter trace for the legend to show the line color
        fig.add_trace(
            go.Scatter(
                x=[None],  # no points to plot
                y=[None],
                mode="lines",
                line=dict(color=color, width=2),
                name=key,
            )
        )

    # Update layout
    tick_labels = list(prices_df.index)
    fig.update_layout(
        yaxis=dict(title="Price (Øre/kWh)"),
        xaxis=dict(tickvals=tick_labels, ticktext=tick_labels, title="Hour"),
    )

    st.plotly_chart(fig)


def check_token(token: str) -> None:
    token_valid = TibberConnection(token).check_token_validity()
    if token_valid:
        st.success("Connected to Tibber API")
    else:
        st.error("Connection Error. Check your API token.")


def token_check_homepage() -> bool:
    token = str(os.environ.get("TIBBER_TOKEN"))
    token_valid = TibberConnection(token).check_token_validity()
    if token_valid:
        return True
    else:
        return False


def api_token_input() -> None:
    with st.container():  # Use a container to encapsulate widgets and avoid key conflicts.
        if os.environ.get("TIBBER_TOKEN"):
            token = st.text_input(
                "Tibber API Token",
                os.environ.get("TIBBER_TOKEN"),
                key="api_token_input_1",
            )
            check_token(token)
            save_api_key(token)
        else:
            token = st.text_input("Tibber API Token")
            check_token(token)
            save_api_key(token)


# Settings page functions


def setpoints_to_dict(setpoints_df: pd.DataFrame) -> dict[str, float]:
    setpoints_dict = {
        row["Appliance Group"]: row["Setpoint"]
        for index, row in setpoints_df.iterrows()
    }
    return setpoints_dict
