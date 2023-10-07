import streamlit as st

from price_driven_switch.backend.configuration import load_settings_file
from price_driven_switch.frontend.st_functions import (
    get_power_reading,
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

st.write("Current Setpoints JSON:")
st.json(get_setpoints_json())
