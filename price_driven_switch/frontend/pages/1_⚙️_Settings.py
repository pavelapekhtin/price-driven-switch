import asyncio
import os

import streamlit as st
from dotenv import load_dotenv

from price_driven_switch.backend.configuration import load_settings_file, save_api_key
from price_driven_switch.frontend.st_functions import (
    appliances_editor,
    check_token,
    power_limit_input,
)

load_dotenv()


if "api_token" not in st.session_state:
    st.session_state["api_token"] = os.environ.get("TIBBER_TOKEN", "")

if "max_power_input" not in st.session_state:
    st.session_state["max_power_input"] = (
        load_settings_file().get("Settings", {}).get("MaxPower")
    )


# if "appliances_editor" not in st.session_state:
#     st.session_state["appliances_editor"] = load_appliances_df(
#         load_settings_file()
#     ).copy()[["Setpoint", "Power", "Priority"]]


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

    load_settings_file().copy()

    st.text(" ")
    st.subheader("Appliances")

    appliances_editor()

    power_limit_input()


if __name__ == "__main__":
    main()
