import os
from typing import Any, Dict

import pandas as pd
import plotly.graph_objects as go  # type: ignore
import requests
import streamlit as st
from loguru import logger

from price_driven_switch.backend.configuration import (
    load_settings_file,
    save_api_key,
    save_settings,
    update_max_power,
)
from price_driven_switch.backend.tibber_connection import TibberConnection


def extract_setpoints(input_dict: Dict[str, Any]) -> Dict[str, float]:
    appliances = input_dict.get("Appliances", {})
    setpoint_dict = {
        name: appliance.get("Setpoint", 0.0) for name, appliance in appliances.items()
    }
    return setpoint_dict


def load_setpoints() -> Dict[str, float]:
    return extract_setpoints(load_settings_file())


def generate_sliders(values: Dict[str, float]) -> Dict[str, float]:
    new_dict: Dict[str, float] = values.copy()
    for key, value in new_dict.items():
        slider_value: int = int(value * 24)
        new_value: int = st.slider(
            label=key, min_value=0, max_value=24, value=slider_value
        )
        new_dict[key] = new_value / 24.0
    return new_dict


def update_setpoints(
    original_dict: Dict[str, Any], new_setpoints: Dict[str, float]
) -> Dict[str, Any]:
    if "Appliances" not in original_dict:
        original_dict["Appliances"] = {}

    for appliance_name, new_setpoint in new_setpoints.items():
        if appliance_name in original_dict["Appliances"]:
            original_dict["Appliances"][appliance_name]["Setpoint"] = new_setpoint
        else:
            original_dict["Appliances"][appliance_name] = {"Setpoint": new_setpoint}
    return original_dict


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


async def check_token(token: str | None) -> None:
    token_valid = await TibberConnection(token).check_token_validity()  # type: ignore
    if token_valid:
        st.success("Connected to Tibber API")
    else:
        st.error("Connection Error. Check your API token.")


async def token_check_homepage() -> bool:
    token = str(os.environ.get("TIBBER_TOKEN"))
    token_valid = await TibberConnection(token).check_token_validity()
    if token_valid:
        return True
    else:
        return False


async def api_token_input() -> None:
    with st.container():  # Use a container to encapsulate widgets and avoid key conflicts.
        if os.environ.get("TIBBER_TOKEN"):
            token = st.text_input(
                "Tibber API Token",
                os.environ.get("TIBBER_TOKEN"),
                key="api_token_input_1",
            )
            await check_token(token)
            save_api_key(token)  # type: ignore
        else:
            token = st.text_input("Tibber API Token")
            await check_token(token)
            save_api_key(token)


def power_limit_input() -> None:
    max_power = st.number_input(
        "Power Limit, kW",
        key="max_power_input",
        min_value=0.0,
        step=1.0,
        value=st.session_state.max_power_input,
    )
    logger.debug(f"Max power input: {max_power}")
    logger.debug(f"Max power session: {st.session_state.max_power_input}")
    if load_settings_file().get("Settings", {}).get("MaxPower") != max_power:
        save_settings(update_max_power(load_settings_file(), max_power))  # type: ignore


def fast_api_address() -> str:
    if os.environ.get("RUNNING_IN_DOCKER"):
        return "172.18.0.1/api"
    else:
        return "127.0.0.1:8080"


def get_setpoints_json() -> dict | str:
    url = f"http://{fast_api_address()}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data: dict = response.json()
        return data
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return str(e)


def get_power_reading() -> int | str:
    url = f"http://{fast_api_address()}/subscription_info"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data: dict = response.json()
        return data.get("power_reading", 0)
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return str(e)


def get_subscription_status() -> str:
    url = f"http://{fast_api_address()}/subscription_info"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data: dict = response.json()
        status = data.get("subscription_status", 0)
        if status:
            return "Active"
        else:
            return "Down"
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return str(e)
