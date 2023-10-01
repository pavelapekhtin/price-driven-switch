import asyncio
import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from loguru import logger

from price_driven_switch.backend.configuration import (
    load_settings_file,
    save_api_key,
    save_settings,
)
from price_driven_switch.backend.switch_logic import load_appliances_df
from price_driven_switch.frontend.st_functions import check_token, power_limit_input

load_dotenv()


if "api_token" not in st.session_state:
    st.session_state.api_token = os.environ.get("TIBBER_TOKEN", "")

if "max_power_input" not in st.session_state:
    st.session_state["max_power_input"] = (
        load_settings_file().get("Settings", {}).get("MaxPower")
    )


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
        save_api_key(st.session_state.api_token)  # type: ignore

    original_settings = load_settings_file().copy()

    appliances = load_appliances_df(original_settings).copy()[
        ["Setpoint", "Power", "Priority"]
    ]

    st.text(" ")
    st.subheader("Appliances")

    appliance_editor_frame = st.data_editor(
        appliances,
        hide_index=False,
        num_rows="dynamic",
        use_container_width=True,
        key="appliance_editor",
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

    if "appliances_editor" not in st.session_state:
        st.session_state["appliances_editor"] = appliances

    if "save_state" not in st.session_state:
        st.session_state["save_state"] = False

    edited_appliances_dict = appliance_editor_frame.to_dict(orient="index")

    if original_settings["Appliances"] != edited_appliances_dict:
        if st.button("Save Changes", key="save_changes"):
            new_settings = original_settings.copy()
            new_settings["Appliances"] = edited_appliances_dict

            logger.debug(f"Updated settings: {new_settings}")
            # Save the updated settings
            save_settings(new_settings)

    power_limit_input()


if __name__ == "__main__":
    main()
