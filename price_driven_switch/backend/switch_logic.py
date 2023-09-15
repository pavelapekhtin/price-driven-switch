import logging

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
    appliance_df["can_be_on"] = appliance_df["Setpoint"] <= offset_now

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


def get_power_based_states_ungroped(
    switch_states: pd.DataFrame, power_limit: float
) -> pd.DataFrame:
    """
    * Check if total power draw of all "on" appliances is exceeded.
    * If it is, loop throug appliances starting with lowest
    priority, change their switch state to false and do the check again.
    """

    only_on_df = switch_states[switch_states["can_be_on"] == True].copy()

    # check total power draw for all "on"
    def get_power_draw(switch_df: pd.DataFrame) -> float:
        return switch_df[switch_df["can_be_on"] == True]["Power"].sum()

    while get_power_draw(only_on_df) > power_limit:
        # prevent race condition
        if power_limit < 0:
            raise ValueError("Max power level can not be negative.")

        # only_on_df = only_on_df[only_on_df["can_be_on"] == True].copy()
        lowest_prio_on = only_on_df[only_on_df["can_be_on"]]["Priority"].max()

        removal_idx = only_on_df[only_on_df["Priority"] == lowest_prio_on].index
        # Change selected row's value to False
        changed_row = only_on_df.loc[removal_idx]
        changed_row["can_be_on"] = False
        # remove the unwanted row
        only_on_df = only_on_df.drop(removal_idx)
        # add the changed row back
        only_on_df = pd.concat([only_on_df, changed_row])

    return only_on_df
