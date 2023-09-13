# import pandas as pd
# import streamlit as st
# from price_driven_switch.backend.configuration import load_setpoints, save_setpoints
# from price_driven_switch.frontend.functions import api_token_input, setpoints_to_dict

# api_token_input()

# setpoint_form = pd.DataFrame(
#     list(load_setpoints().items()), columns=["Appliance Group", "Setpoint"]
# ).copy()


# st.text(" ")
# st.subheader("Appliances")

# edited_setpoints = st.data_editor(
#     setpoint_form,
#     hide_index=True,
#     num_rows="dynamic",
#     use_container_width=True,
#     column_config={
#         "Setpoint": st.column_config.NumberColumn(
#             min_value=0, max_value=1, step=0.01, default=0.5
#         ),
#         "Appliance Group": st.column_config.TextColumn(required=True),
#     },
# )

# new_setpoints = setpoints_to_dict(edited_setpoints)

# if edited_setpoints.equals(setpoint_form) is False:
#     st.button(
#         "Save setpoints",
#         on_click=save_setpoints,
#         args=(new_setpoints,),  # prevent running without press
#         key="save_setpoints",
#     )
