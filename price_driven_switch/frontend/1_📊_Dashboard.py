import asyncio
import os

import pandas as pd
import streamlit as st

from price_driven_switch.backend.configuration import (
    get_package_version_from_toml,
    save_settings,
)
from price_driven_switch.backend.price_file import PriceFile
from price_driven_switch.backend.prices import Prices
from price_driven_switch.frontend.st_functions import (
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
st.sidebar.caption(f"Version: {get_package_version_from_toml()}")

if "api_token" not in st.session_state:
    st.session_state["api_token"] = os.environ.get("TIBBER_TOKEN", "")

if "slider_values" not in st.session_state:
    st.session_state["slider_values"] = load_setpoints()


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

    slider_values = generate_sliders(st.session_state.slider_values)

    new_settings = update_setpoints(
        original_settings, slider_values
    )  # Assume update_setpoints is imported.

    if load_setpoints() != slider_values:
        save_settings(new_settings)  # type: ignore

    st.session_state.slider_values = slider_values

    # PRICE PLOTS =====================

    st.header("Power Prices")

    # Show pricing mode status
    settings = load_settings_file()
    use_norgespris = settings.get("Settings", {}).get("UseNorgespris", False)
    include_grid_rent = settings.get("Settings", {}).get("IncludeGridRent", True)

    if use_norgespris and include_grid_rent:
        norgespris_rate = settings.get("Settings", {}).get("NorgesprisRate", 50.0)
        st.info(f"📌 Norgespris ({norgespris_rate:.1f} øre/kWh) + grid rent")
    elif use_norgespris:
        norgespris_rate = settings.get("Settings", {}).get("NorgesprisRate", 50.0)
        st.info(f"📌 Norgespris ({norgespris_rate:.1f} øre/kWh) only")
    elif include_grid_rent:
        st.info("🔌 Spot price + grid rent")
    else:
        st.info("⚠️ Spot price only")

    today_prices_list = prices.today_prices
    tomo_prices_list = prices.tomo_prices

    today_prices_df = pd.DataFrame({"Prices": pd.Series(today_prices_list) * 100})
    tomo_prices_df = pd.DataFrame({"Prices": pd.Series(tomo_prices_list) * 100})

    st.subheader("Today")
    plot_prices(today_prices_df, slider_values, today_prices_list, show_time=True)

    st.subheader("Tomorrow")
    plot_prices(tomo_prices_df, slider_values, tomo_prices_list, show_time=False)


if __name__ == "__main__":
    asyncio.run(check())
    asyncio.run(main())
