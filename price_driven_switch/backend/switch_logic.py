import pandas as pd
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


def limit_power(
    switch_states: pd.DataFrame,
    power_limit: float,
    power_now: int,
    current_states_pwr_based: pd.DataFrame,
) -> pd.DataFrame:
    # Fallback to price only if power_now is 0 (i.e. failed to get current power)
    if power_now == 0:
        logger.warning("Failed to get current power, using price only logic")
        return switch_states

    if power_limit == 0:
        logger.info("Power limit is set to 0, using only price logic")
        return switch_states

    power_now_kw = power_now / 1000.0

    # TODO: make log 1 line and with colors
    logger.info(f"Power/Limit now: {power_now_kw} / {power_limit} kW")

    # Find the appliance with the highest priority (lowest 'Priority' value)
    highest_priority_appliance = switch_states.sort_values("Priority").iloc[0]

    # If power_limit is lower than the highest priority appliance, turn everything off
    if power_limit < highest_priority_appliance["Power"]:
        logger.info(
            "Power limit is lower than the highest priority appliance power, turning everything off"
        )
        switch_states["on"] = False
        return switch_states

    # If power_now is already below the limit, no need to turn off anything
    if power_now_kw < power_limit:
        logger.info("Power is already below limit, no need to turn off anything")
        return switch_states

    # Sort DataFrame by 'Priority' in descending order so that lower priorities are turned off first
    sorted_states = switch_states.sort_values("Priority", ascending=False)

    for index, row in sorted_states.iterrows():
        if row["on"]:
            new_power = power_now_kw - row["Power"]
            if new_power < power_limit:
                sorted_states.at[index, "on"] = False
                logger.info(f"Turning off {index} to stay below power limit")
                break
            power_now_kw = new_power
            sorted_states.at[index, "on"] = False
            logger.info(f"Turning off {index} to stay below power limit")

    # Update the original DataFrame to reflect these changes
    switch_states.update(sorted_states)

    return switch_states
