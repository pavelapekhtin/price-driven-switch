import logging
from typing import Callable

import pandas as pd


def load_appliances_df(settings: dict) -> pd.DataFrame:
    """Load appliances from settings.toml into a pandas DataFrame."""
    appliances = settings["Appliances"]
    df = pd.DataFrame.from_dict(appliances, orient="index")
    df.index.name = "Appliance"
    return df


def reduce_df_by_groups(appliance_df: pd.DataFrame) -> pd.DataFrame:
    """Reduce DataFrame by grouping appliances by their group."""
    # Separate rows that don't belong to any group
    no_group_df = appliance_df[appliance_df["Group"] == ""].copy()
    no_group_df["Group"] = no_group_df.index  # Set their 'Group' to their index
    no_group_df["Members"] = 1  # Set 'Members' to 1 for appliances without a group

    # Group by 'Group' and aggregate according to your criteria
    agg_funcs = {
        "Setpoint": "max",
        "Power": "sum",
        "Priority": "min",
        "Members": "size",  # Count the number of appliances in each group
    }

    grouped_df = (
        appliance_df[appliance_df["Group"] != ""]
        .assign(Members=1)
        .groupby("Group")
        .agg(agg_funcs)
        .reset_index()
    )

    # Append rows that didn't belong to any group
    final_df = pd.concat([grouped_df, no_group_df]).set_index("Group")

    return final_df


current_offset: float


def get_price_based_states(
    appliance_df: pd.DataFrame,
    offset_now: float,
) -> pd.DataFrame:
    appliance_df["on"] = appliance_df["Setpoint"] <= offset_now

    return appliance_df


def ungrouped_switches_pipeline(settings: dict, offset_now: float) -> pd.DataFrame:
    # TODO: give a sensible name
    output = get_price_based_states(load_appliances_df(settings), offset_now)
    return output


def grouped_switches_pipeline(settings: dict, offset_now: float) -> pd.DataFrame:
    output = get_price_based_states(
        reduce_df_by_groups(load_appliances_df(settings)), offset_now
    )
    return output


def limit_power(
    switch_states: pd.DataFrame, power_limit: float, power_now: int
) -> pd.DataFrame:
    power_now_kW = power_now / 1000.0

    # Find the appliance with the highest priority (lowest 'Priority' value)
    highest_priority_appliance = switch_states.sort_values("Priority").iloc[0]

    # If power_limit is lower than the highest priority appliance, turn everything off
    if power_limit < highest_priority_appliance["Power"]:
        switch_states["on"] = False
        return switch_states

    # If power_now is already below the limit, no need to turn off anything
    if power_now_kW <= power_limit:
        return switch_states

    # Sort DataFrame by 'Priority' in descending order so that lower priorities are turned off first
    sorted_states = switch_states.sort_values("Priority", ascending=False)

    for index, row in sorted_states.iterrows():
        if row["on"]:
            new_power = power_now_kW - row["Power"]
            if new_power <= power_limit:
                sorted_states.at[index, "on"] = False
                break
            power_now_kW = new_power
            sorted_states.at[index, "on"] = False

    # Update the original DataFrame to reflect these changes
    switch_states.update(sorted_states)

    return switch_states
