import streamlit as st

from price_driven_switch.backend.configuration import load_settings_file
from price_driven_switch.frontend.st_functions import get_setpoints_json

st.metric(
    label="Power Limit", value=load_settings_file().get("Settings", {}).get("MaxPower")
)

st.write("Current Setpoints JSON:")
st.json(get_setpoints_json())
