# import json

# import pandas as pd
# import pytest
# import streamlit as st
# from price_driven_switch.backend.configuration import save_setpoints
# from price_driven_switch.backend.price_file import PriceFile
# from price_driven_switch.backend.prices import Prices

# from tests.fixtures.price_fixtures import FIXTURE_API_RESPONSE
# from tests.frontend.functions_test import (
#     api_token_input,
#     generate_sliders,
#     load_setpoints_cached,
#     plot_prices,
#     token_check_homepage,
# )

# st.header("TESTING VERSION")


# mock_prices = Prices(FIXTURE_API_RESPONSE)


# def main():
#     # TOKEN CHECK =====================

#     token_check = token_check_homepage()

#     if not token_check:
#         api_token_input()
#         st.write("Enter the API token, hit Enter and refresh the page.")
#         st.stop()

#     prices = mock_prices

#     # SETPOINT SLIDERS ================

#     st.header("Setpoints")

#     slider_values = generate_sliders(load_setpoints_cached())

#     if st.button("Save setpoints"):
#         save_setpoints(slider_values)

#     # PRICE OFFSETS ===================

#     offset_prices_today = {}
#     offset_prices_tomorrow = {}

#     # Use the keys and values (offsets) in loaded_dict to populate offset_prices_today and offset_prices_tomorrow
#     for key, offset in slider_values.items():
#         # Get the price at this offset for today and tomorrow
#         price_today = round(prices.get_price_at_offset_today(offset) * 100)
#         price_tomorrow = round(prices.get_price_at_offset_tomorrow(offset) * 100)

#         # Add these prices to the respective dictionaries
#         offset_prices_today[key] = price_today
#         offset_prices_tomorrow[key] = price_tomorrow

#     # PRICE PLOTS =====================

#     st.header("Power Prices")

#     today_prices = pd.Series(prices.today_prices) * 100
#     tomo_prices = pd.Series(prices.tomo_prices) * 100

#     # Convert the Series into a DataFrame for compatibility with Plotly
#     today_df = pd.DataFrame({"Prices": today_prices})
#     tomo_df = pd.DataFrame({"Prices": tomo_prices})

#     st.subheader("Today")
#     plot_prices(today_df, offset_prices_today)

#     st.subheader("Tomorrow")
#     plot_prices(tomo_df, offset_prices_tomorrow)


# main()
