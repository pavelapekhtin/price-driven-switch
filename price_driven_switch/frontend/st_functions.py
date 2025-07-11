import os
from datetime import datetime
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
from price_driven_switch.backend.switch_logic import load_appliances_df
from price_driven_switch.backend.tibber_connection import TibberConnection


def extract_setpoints(input_dict: Dict[str, Any]) -> Dict[str, float]:
    appliances = input_dict.get("Appliances", {})
    setpoint_dict = {
        name: appliance.get("Setpoint", 0.0) for name, appliance in appliances.items()
    }
    return setpoint_dict


def load_setpoints() -> Dict[str, float]:
    return extract_setpoints(load_settings_file())


def change_slider_state(values: Dict[str, float]) -> None:
    st.session_state.slider_values = values


def generate_sliders(values: Dict[str, float]) -> Dict[str, float]:
    new_dict: Dict[str, float] = values.copy()
    for key, value in new_dict.items():
        slider_value: int = int(value * 24)
        new_value: int = st.slider(
            label=key,
            min_value=0,
            max_value=24,
            value=slider_value,
            on_change=change_slider_state,
            args=(st.session_state.slider_values,),
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


def price_sliders() -> None:
    original_settings = (
        load_settings_file().copy()
    )  # Assuming load_settings_file is your function to load all settings.

    slider_values = generate_sliders(load_setpoints())

    new_settings = update_setpoints(original_settings, slider_values)

    save_settings(new_settings)


def plot_prices(prices_df: pd.DataFrame, offset_prices: dict, show_time: bool) -> None:
    if prices_df.empty:
        st.write("Tomorrow's prices become available after 13:00")
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
            color if bar_price < price else "rgba(128, 128, 128, 0.3)"
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
                line={"color": color, "width": 2},
            )
        )
        # Dummy scatter trace for the legend to show the line color
        fig.add_trace(
            go.Scatter(
                x=[None],  # no points to plot
                y=[None],
                mode="lines",
                line={"color": color, "width": 2},
                name=key,
            )
        )

    # Add current time line if show_time is True
    def shape_part(xoffset: float, y0: float, y1: float, color: str, width: int):
        fig.add_shape(
            go.layout.Shape(
                type="line",
                xref="x",
                yref="paper",
                x0=current_hour + xoffset,
                x1=current_hour + xoffset,
                y0=y0,
                y1=y1,
                line={"color": color, "width": width},
            )
        )

    if show_time:
        current_hour = datetime.now().hour
        shape_part(-0.5, -0.12, 1.05, "rgba(255, 0, 0, 1)", 1)  # left border
        shape_part(0.5, -0.12, 1.05, "rgba(255, 0, 0, 1)", 1)  # right border
        shape_part(0, -0.12, 1.05, "rgba(255, 0, 0, 0.1)", 22)  # fill

    # Update layout
    tick_labels = list(prices_df.index)
    fig.update_layout(
        yaxis={"title": "Price (Øre/kWh)"},
        xaxis={"tickvals": tick_labels, "ticktext": tick_labels, "title": "Hour"},
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
    return bool(token_valid)


# Settings page


async def api_token_input() -> None:
    with (
        st.container()
    ):  # Use a container to encapsulate widgets and avoid key conflicts.
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


def change_df_state(df: pd.DataFrame) -> None:
    st.session_state["appliance_editor"] = df


def save_appliances(df: pd.DataFrame) -> None:
    edited_appliances_dict = df.to_dict(orient="index")

    new_settings = load_settings_file().copy()
    new_settings["Appliances"] = edited_appliances_dict

    logger.debug(f"Updated settings: {new_settings}")
    # Save the updated settings
    save_settings(new_settings)


def appliances_editor() -> None:
    initial_df = load_appliances_df(load_settings_file()).copy()

    if "appliance_editor" not in st.session_state:
        st.session_state["appliance_editor"] = initial_df
    appliances_editor_frame = st.session_state["appliance_editor"]
    appliances_editor_frame = st.data_editor(
        appliances_editor_frame,
        hide_index=False,
        num_rows="dynamic",
        use_container_width=True,
        on_change=change_df_state,
        args=(appliances_editor_frame,),
        column_config={
            "Setpoint": st.column_config.NumberColumn(
                required=True, min_value=0, max_value=1, step=0.01, default=0.5
            ),
            "Power": st.column_config.NumberColumn(
                required=True, min_value=1, step=0.01, default=1
            ),
            "Priority": st.column_config.NumberColumn(
                required=True,
                min_value=1,
                step=1,
                default=1,
            ),
        },
    )
    st.session_state["appliance_editor"] = appliances_editor_frame

    save_appliances(appliances_editor_frame)


def power_limit_input() -> None:
    max_power = st.number_input(
        "Power Limit, kW",
        key="max_power_input",
        min_value=0.0,
        step=1.0,
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


def get_prev_setpoints_json() -> dict | str:
    url = f"http://{fast_api_address()}/previous_setpoints"
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


def update_grid_rent_settings(
    original_dict: Dict[str, Any],
    include_grid_rent: bool,
    jan_mar_day: float,
    jan_mar_night: float,
    apr_dec_day: float,
    apr_dec_night: float,
) -> Dict[str, Any]:
    """Update grid rent settings in the configuration."""
    if "Settings" not in original_dict:
        original_dict["Settings"] = {}

    original_dict["Settings"]["IncludeGridRent"] = include_grid_rent
    original_dict["Settings"]["GridRent"] = {
        "JanMar": {"Day": jan_mar_day, "Night": jan_mar_night},
        "AprDec": {"Day": apr_dec_day, "Night": apr_dec_night},
    }

    return original_dict


def grid_rent_configuration() -> None:
    """Display and handle grid rent configuration in the settings page."""
    settings = load_settings_file()
    current_settings = settings.get("Settings", {})

    st.subheader("Grid Rent Configuration")

    # Toggle for including grid rent
    include_grid_rent = st.checkbox(
        "Include Grid Rent in Prices",
        value=current_settings.get("IncludeGridRent", True),
        help="When enabled, grid rent will be added to electricity prices",
    )

    # Grid rent rates configuration
    grid_rent = current_settings.get(
        "GridRent",
        {
            "JanMar": {"Day": 50.94, "Night": 38.21},
            "AprDec": {"Day": 59.86, "Night": 47.13},
        },
    )

    st.write("**Grid Rent Rates (øre/kWh)**")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**January - March**")
        jan_mar_day = st.number_input(
            "Day Rate (06:00-22:00) øre/kWh",
            value=float(grid_rent.get("JanMar", {}).get("Day", 50.94)),
            min_value=0.0,
            step=0.01,
            format="%.2f",
        )
        jan_mar_night = st.number_input(
            "Night/Weekend Rate (22:00-06:00 + weekends) øre/kWh",
            value=float(grid_rent.get("JanMar", {}).get("Night", 38.21)),
            min_value=0.0,
            step=0.01,
            format="%.2f",
        )

    with col2:
        st.write("**April - December**")
        apr_dec_day = st.number_input(
            "Day Rate (06:00-22:00) øre/kWh",
            value=float(grid_rent.get("AprDec", {}).get("Day", 59.86)),
            min_value=0.0,
            step=0.01,
            format="%.2f",
        )
        apr_dec_night = st.number_input(
            "Night/Weekend Rate (22:00-06:00 + weekends) øre/kWh",
            value=float(grid_rent.get("AprDec", {}).get("Night", 47.13)),
            min_value=0.0,
            step=0.01,
            format="%.2f",
        )

    # Save settings if any values changed
    current_grid_rent = current_settings.get("GridRent", {})
    if (
        include_grid_rent != current_settings.get("IncludeGridRent", True)
        or jan_mar_day != current_grid_rent.get("JanMar", {}).get("Day", 50.94)
        or jan_mar_night != current_grid_rent.get("JanMar", {}).get("Night", 38.21)
        or apr_dec_day != current_grid_rent.get("AprDec", {}).get("Day", 59.86)
        or apr_dec_night != current_grid_rent.get("AprDec", {}).get("Night", 47.13)
    ):
        new_settings = update_grid_rent_settings(
            settings.copy(),
            include_grid_rent,
            jan_mar_day,
            jan_mar_night,
            apr_dec_day,
            apr_dec_night,
        )
        save_settings(new_settings)
        st.success("Grid rent settings updated!")
