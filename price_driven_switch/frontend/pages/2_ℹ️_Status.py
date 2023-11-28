from typing import Any

import streamlit as st

from price_driven_switch.backend.configuration import load_settings_file
from price_driven_switch.frontend.st_functions import (
    get_power_reading,
    get_prev_setpoints_json,
    get_setpoints_json,
    get_subscription_status,
)

power_limit = load_settings_file().get("Settings", {}).get("MaxPower")

# show subscription status, power now, power limit if power limit logic is enabled
if power_limit > 0:
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="Subscription Status",
            value=get_subscription_status(),
        )

    with col2:
        st.metric(
            label="Power Now, kW",
            value=round(get_power_reading() / 1000, 3)  # type: ignore
            if isinstance(get_power_reading(), int)
            else get_power_reading(),
            delta=round(
                round(get_power_reading() / 1000, 3)  # type: ignore
                - round(power_limit, 3),
                3,
            ),
            delta_color="inverse",
        )
    with col3:
        st.metric(
            label="Power Limit, kW",
            value=round(power_limit, 2),
        )

    if st.button("Refresh"):
        st.rerun()
else:
    st.write(
        "Power Limit Logic is disabled. Set Max Power above 0 in Settings if you have Tibber Pulse or Watty connceted."
    )

st.divider()

col1, col2 = st.columns(2)
with col1:
    st.write("Current Setpoints JSON:")
    st.json(get_setpoints_json())
with col2:
    st.write("Price only Setpoints JSON:")
    st.json(get_prev_setpoints_json())

st.divider()


# display logs

# Number input for specifying the number of lines to display
log_lines = st.number_input(
    "Number of lines to display",
    key="log_lines_input",
    min_value=10,
    max_value=3000,
    step=50,
    value=10,
)

# Dropdown menu for selecting log level
log_level = st.selectbox(
    "Select log level",
    ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    index=1,  # Default to CRITICAL
)


# Function to filter log lines based on log level
def read_filtered_logs(file_path: str, lines_count: Any, level: Any) -> str:
    level_order = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    min_level = level_order.index(level)
    filtered_lines = []

    with open(file_path, "r") as file:
        for line in file:
            if any(level in line for level in level_order[min_level:]):
                filtered_lines.append(line)

    return "".join(filtered_lines[-lines_count:])


# File path for the log file
log_file_path = "logs/fast_api.log"

# Read and filter log content
log_content = read_filtered_logs(log_file_path, log_lines, log_level)

# Display the filtered log content
st.text_area("Log File Content", log_content, height=300)
