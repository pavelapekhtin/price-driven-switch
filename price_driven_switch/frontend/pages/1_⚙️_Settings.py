import asyncio
import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from price_driven_switch.backend.configuration import (
    load_settings_file,
    save_api_key,
    save_settings,
)
from price_driven_switch.backend.switch_logic import load_appliances_df
from price_driven_switch.frontend.st_functions import (
    api_token_input,
    check_token,
    power_limit_input,
    setpoints_to_dict,
)

load_dotenv()

# setpoint_form = pd.DataFrame(
#     list(load_setpoints().items()), columns=["Appliance Group", "Setpoint"]
# ).copy()
# Initialize session state

if "api_token" not in st.session_state:
    st.session_state.api_token = os.environ.get("TIBBER_TOKEN", "")

if "max_power_input" not in st.session_state:
    st.session_state["max_power_input"] = (
        load_settings_file().get("Settings", {}).get("MaxPower")
    )

st.cache_data(ttl=5)


def main():
    with st.container():
        # Show API Token text input and link it to session_state.api_token
        st.session_state.api_token = st.text_input(
            "Tibber API Token", st.session_state.api_token
        )

        # Async operation
        loop = asyncio.new_event_loop()
        loop.run_until_complete(check_token(st.session_state.api_token))
        loop.close()

        # Save API key
        save_api_key(st.session_state.api_token)

    appliances = load_appliances_df(load_settings_file()).copy()[
        ["Setpoint", "Power", "Priority"]
    ]

    st.text(" ")
    st.subheader("Appliances")

    edited_setpoints = st.data_editor(
        appliances,
        hide_index=False,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Setpoint": st.column_config.NumberColumn(
                required=True, min_value=0, max_value=1, step=0.01, default=0.5
            ),
            "Power": st.column_config.NumberColumn(
                required=True, min_value=1, step=0.01, default=1
            ),
            "Priority": st.column_config.NumberColumn(
                required=True, min_value=1, step=1, default=1
            ),
        },
    )

    power_limit_input()


# new_setpoints = setpoints_to_dict(edited_setpoints)

# if edited_setpoints.equals(setpoint_form) is False:
#     st.button(
#         "Save setpoints",
#         on_click=save_setpoints,
#         args=(new_setpoints,),
#         key="save_setpoints",
#     )

# Show token settings


if __name__ == "__main__":
    main()
