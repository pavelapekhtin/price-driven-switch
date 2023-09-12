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
    grouped_appl: pd.DataFrame,
    offset_now: float,
) -> pd.DataFrame:
    grouped_appl["ok_price"] = grouped_appl["Setpoint"] <= offset_now

    return grouped_appl
