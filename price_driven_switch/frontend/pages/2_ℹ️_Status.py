import streamlit as st

from price_driven_switch.backend.configuration import load_settings_file
from price_driven_switch.frontend.st_functions import (
    get_power_reading,
    get_setpoints_json,
)

if st.button("Refresh"):
    st.rerun()

col1, col2 = st.columns(2)

with col1:
    st.metric(
        label="Power Now, kW",
        value=round(get_power_reading() / 1000, 3)  # type: ignore
        if isinstance(get_power_reading(), int)
        else get_power_reading(),
        delta=round(
            round(get_power_reading() / 1000, 3)  # type: ignore
            - round(load_settings_file().get("Settings", {}).get("MaxPower"), 3),
            3,
        ),
        delta_color="inverse",
    )
with col2:
    st.metric(
        label="Power Limit, kW",
        value=round(load_settings_file().get("Settings", {}).get("MaxPower"), 2),
    )

st.divider()

st.write("Current Setpoints JSON:")
st.json(get_setpoints_json())
