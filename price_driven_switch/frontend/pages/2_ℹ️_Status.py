import re
from typing import Any

import streamlit as st

from price_driven_switch.backend.configuration import load_settings_file
from price_driven_switch.frontend.st_functions import (
    format_switch_states,
    get_power_reading,
    get_prev_setpoints_json,
    get_setpoints_json,
    get_subscription_status,
)

power_limit = load_settings_file().get("Settings", {}).get("MaxPower")

# Show grid rent status
grid_rent_info = load_settings_file().get("Settings", {}).get("GridRent", {})
include_grid_rent = (
    load_settings_file().get("Settings", {}).get("IncludeGridRent", True)
)

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
            value=(
                round(get_power_reading() / 1000, 3)  # type: ignore
                if isinstance(get_power_reading(), int)
                else get_power_reading()
            ),
            delta=round(
                round(get_power_reading() / 1000, 3)  # type: ignore
                - round(power_limit, 3),
                3,
            )
            if isinstance(get_power_reading(), int)
            else "ERROR: NO DATA",
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


st.subheader("Appliance States")

col1, col2 = st.columns(2)
with col1:
    st.markdown("**🔋 Current Switch States (Power Limited)**")
    current_states = get_setpoints_json()
    with st.container(border=True):
        st.text(format_switch_states(current_states))

with col2:
    st.markdown("**💰 Price Only Switch States**")
    price_only_states = get_prev_setpoints_json()
    with st.container(border=True):
        st.text(format_switch_states(price_only_states))

st.text("")  # Add some spacing

st.divider()


# display logs
st.subheader("Logs")

# Number input for specifying the number of lines to display
log_lines = st.number_input(
    "Number of lines to display",
    key="log_lines_input",
    min_value=12,
    max_value=3000,
    step=50,
    value=12,
)

# Enhanced log filtering options
col1, col2 = st.columns(2)

with col1:
    log_level = st.selectbox(
        "Log level",
        ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        index=1,  # Default to INFO
        help="Minimum log level to display",
    )

with col2:
    category_filter = st.selectbox(
        "Category filter",
        ["ALL", "SWITCH", "SYSTEM", "TIBBER"],
        index=1,  # Default to SWITCH
        help="Filter logs by category: SWITCH (appliance decisions), SYSTEM (errors/config), TIBBER (connection status)",
    )

# Real-time update toggle
auto_refresh = st.checkbox("Auto-refresh logs (every 10 seconds)", value=False)

if auto_refresh:
    st.empty()  # Placeholder for auto-refresh functionality


# Enhanced function to filter and format log lines for better readability
def read_filtered_logs(
    file_path: str, lines_count: Any, level: Any, category_filter: str = "ALL"
) -> str:
    level_order = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    min_level = level_order.index(level)
    filtered_lines: list[str] = []

    # Category patterns for better filtering
    category_patterns = {
        "SWITCH": r"\[(SWITCH|DECISION|PRICE|POWER|SUMMARY)\]",
        "SYSTEM": r"\[(SESSION|CONFIG|ERROR)\]",
        "TIBBER": r"(Tibber|tibber|subscription|power reading)",
        "ALL": r".*",
    }

    category_pattern = category_patterns.get(category_filter, r".*")

    try:
        with open(file_path) as file:
            for line in file:
                # Check log level
                if any(level_name in line for level_name in level_order[min_level:]):
                    # Check category filter
                    if re.search(category_pattern, line, re.IGNORECASE):
                        # Clean up the line for better readability
                        clean_line = clean_log_line(line)
                        if clean_line and not is_duplicate_line(
                            clean_line, filtered_lines
                        ):
                            filtered_lines.append(clean_line)
    except FileNotFoundError:
        return "Log file not found. System may be starting up."
    except Exception as e:
        return f"Error reading log file: {e}"

    return "\n".join(filtered_lines[-lines_count:])


def clean_log_line(line: str) -> str:
    """Clean and format log line for better readability."""
    # Remove timestamp prefix if too verbose, keep only time
    line = re.sub(r"^\d{4}-\d{2}-\d{2} ", "", line)

    # Highlight important sections
    line = re.sub(r"\[(SWITCH|DECISION|PRICE|POWER|SUMMARY|ERROR)\]", r"[\1]", line)

    # Remove excessive whitespace
    line = re.sub(r"\s+", " ", line).strip()

    return line


def is_duplicate_line(line: str, existing_lines: list[str]) -> bool:
    """Check if line is a duplicate of recent entries."""
    if len(existing_lines) < 3:
        return False

    # Check last few lines for exact duplicates
    recent_lines = existing_lines[-3:]
    return line in recent_lines


def format_log_display(log_content: str) -> str:
    """Format log content for better display."""
    if not log_content.strip():
        return "No recent log entries matching the selected criteria."

    lines = log_content.split("\n")
    if len(lines) > 50:
        lines = lines[-50:]  # Keep only last 50 lines

    return "\n".join(lines)


# File path for the log file
log_file_path = "logs/fast_api.log"

# Read and filter log content with enhanced filtering
log_content = read_filtered_logs(log_file_path, log_lines, log_level, category_filter)

# Format log content for better display
formatted_content = format_log_display(log_content)

# Display stats about current logs
if (
    formatted_content
    and formatted_content != "No recent log entries matching the selected criteria."
):
    lines_shown = len([line for line in formatted_content.split("\n") if line.strip()])
    st.caption(f"Showing {lines_shown} log entries matching your criteria")

# Display the filtered log content with better formatting
st.text_area(
    f"Logs ({log_level}+ level, {category_filter} category)",
    formatted_content,
    height=400,
    help="Recent system logs filtered by level and category. Switch logs show appliance state changes and decision reasoning.",
)

# Add quick action buttons
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔄 Refresh Logs"):
        st.rerun()

with col2:
    if st.button("📋 Show All Recent"):
        st.session_state.update(
            {"log_lines_input": 100, "category_filter": "ALL", "log_level": "DEBUG"}
        )
        st.rerun()

with col3:
    if st.button("🔍 Switch Decisions Only"):
        st.session_state.update(
            {"log_lines_input": 50, "category_filter": "SWITCH", "log_level": "INFO"}
        )
        st.rerun()

# Log interpretation help
with st.expander("📖 Log Message Guide"):
    st.markdown("""
    **Key log prefixes:**
    - `[PRICE]` - Price-based switching decisions
    - `[POWER]` - Power limit enforcement
    - `[SWITCH]` - Individual appliance state changes
    - `[DECISION]` - Summary of switching decisions
    - `[SUMMARY]` - System status overview
    - `[ERROR]` - System errors requiring attention

    **Common patterns:**
    - `→ ON/OFF` - Appliance state changes with reason
    - `Power: XXXXw / YYYYw` - Current vs limit power consumption
    - `Price: X.XXX` - Current price offset value
    - `Priority X` - Appliance priority (1=highest)
    """)
