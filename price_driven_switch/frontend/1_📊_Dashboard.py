import asyncio
import os

import pandas as pd
import streamlit as st

from price_driven_switch.backend.configuration import save_settings
from price_driven_switch.backend.price_file import PriceFile
from price_driven_switch.backend.prices import Prices
from price_driven_switch.frontend.st_functions import (
    api_token_input,
    check_token,
    generate_sliders,
    load_setpoints,
    load_settings_file,
    plot_prices,
    save_api_key,
    token_check_homepage,
    update_setpoints,
)

st.sidebar.title("Price Based Controller", anchor="top")

if "api_token" not in st.session_state:
    st.session_state["api_token"] = os.environ.get("TIBBER_TOKEN", "")


async def check():
    token_check = await token_check_homepage()

    while not token_check:
        with st.container():
            # Show API Token text input and link it to session_state.api_token
            st.session_state.api_token = st.text_input(
                "Tibber API Token", st.session_state.api_token
            )

            await check_token(st.session_state.api_token)
            # Save API key
            save_api_key(st.session_state.api_token)  # type: ignore

            st.stop()


async def main():
    prices = Prices(await PriceFile().load_prices())

    # SETPOINT SLIDERS ================

    st.header("Setpoints")

    original_settings = (
        load_settings_file().copy()
    )  # Assuming load_settings_file is your function to load all settings.
    original_setpoints = load_setpoints()

    slider_values = generate_sliders(original_setpoints)

    if original_setpoints != slider_values:
        if st.button("Save Setpoints", use_container_width=True):
            new_settings = original_settings.copy()
            new_settings = update_setpoints(
                new_settings, slider_values
            )  # Assume update_setpoints is imported.
            save_settings(new_settings)
            st.rerun()
    else:
        st.subheader("")

    # PRICE OFFSETS ===================

    offset_prices_today = {}
    offset_prices_tomorrow = {}

    # Use the keys and values (offsets) in loaded_dict to populate offset_prices_today and offset_prices_tomorrow
    for key, offset in slider_values.items():
        # Get the price at this offset for today and tomorrow
        price_today = prices.get_price_at_offset_today(offset) * 100
        price_tomorrow = prices.get_price_at_offset_tomorrow(offset) * 100

        # Add these prices to the respective dictionaries
        offset_prices_today[key] = price_today
        offset_prices_tomorrow[key] = price_tomorrow

    # PRICE PLOTS =====================

    st.header("Power Prices")

    today_prices = pd.Series(prices.today_prices) * 100
    tomo_prices = pd.Series(prices.tomo_prices) * 100

    # Convert the Series into a DataFrame for compatibility with Plotly
    today_df = pd.DataFrame({"Prices": today_prices})
    tomo_df = pd.DataFrame({"Prices": tomo_prices})

    st.subheader("Today")
    plot_prices(today_df, offset_prices_today)

    st.subheader("Tomorrow")
    plot_prices(tomo_df, offset_prices_tomorrow)


if __name__ == "__main__":
    asyncio.run(check())
    asyncio.run(main())
