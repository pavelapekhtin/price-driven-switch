import pandas as pd
from icecream import ic
from loguru import logger


def load_appliances_df(settings: dict) -> pd.DataFrame:
    """Load appliances from settings.toml into a pandas DataFrame."""
    appliances = settings["Appliances"]
    df = pd.DataFrame.from_dict(appliances, orient="index")
    df.index.name = "Appliance"
    return df


current_offset: float


def get_price_based_states(
    appliance_df: pd.DataFrame,
    offset_now: float,
) -> pd.DataFrame:
    appliance_df["on"] = appliance_df["Setpoint"] >= offset_now

    return appliance_df


def set_price_only_based_states(settings: dict, offset_now: float) -> pd.DataFrame:
    output = get_price_based_states(load_appliances_df(settings), offset_now)
    return output


def check_frames(df1: pd.DataFrame, df2: pd.DataFrame, ignore_column: str) -> bool:
    # Selecting all columns except the one to ignore
    df1_filtered = df1[df1.columns.difference([ignore_column])]
    df2_filtered = df2[df2.columns.difference([ignore_column])]

    # Comparing the filtered DataFrames
    return df1_filtered.equals(df2_filtered)


def limit_power(
    switch_states: pd.DataFrame,
    power_limit: float,
    power_now: int,
    prev_states: pd.DataFrame,
) -> pd.DataFrame:
    switch_df = switch_states
    prev_states_df = prev_states

    # fallback case
    if power_limit == 0 or power_now == 0:
        logger.debug("Power limit or power now is 0, power logic disabled")
        return switch_df

    # empty previous state case or wrong df shape
    if prev_states_df.empty or check_frames(switch_df, prev_states_df, "on"):
        logger.debug("Ignoring previous state, empty df or wrong shape")

        # course of action
        # 1. if previous state frame is same as switch states, reduce power
        if switch_df.equals(prev_states_df):
            if power_now < power_limit * 1000:
                logger.debug("Power is below limit, no action required")
                return switch_df
            if power_now > power_limit * 1000:
                total_power = power_now

                logger.debug(
                    f"Power is above limit, reducing power (over: {total_power - power_limit * 1000} kW)"
                )
                for priority in range(0, switch_df["Priority"].max() + 1):
                    for index, row in switch_df.iterrows():
                        if row["Priority"] == priority and row["on"] is True:
                            total_power = total_power - row["Power"] * 1000
                            switch_df.at[index, "on"] = False
                            logger.debug(
                                f"Turning off {row['Appliance']}, power {row['Power']} kW"
                            )
                            logger.debug(f"Estimated total power now {total_power} kW")
                            if total_power < power_limit * 1000:
                                break
                    if total_power < power_limit * 1000:
                        break
                return switch_df
