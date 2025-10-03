# mypy: disable-error-code="index,operator"
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
    logger.info(f"Price only based states: {appliance_df['on'].to_list()!s}")
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

    logger.info("======= Power limiter working ========")
    # fallback case
    if power_limit == 0 or power_now == 0:
        logger.info("Power limit or power now is 0, pirce only logic is used")
        return switch_df

    elif switch_df.equals(prev_states_df) or not check_frames(
        switch_df, prev_states_df, "on"
    ):
        logger.debug("No previous state or previous state is the same as current state")
        if power_now < power_limit * 1000:
            logger.info(
                f"[OK] power below limit {power_now} W < {power_limit * 1000} W, no action"
            )
            return switch_df
        if power_now > power_limit * 1000:
            total_power = power_now

            logger.info(f"[OVER] {power_now - power_limit * 1000} W , reducing power.")
            for priority in range(0, switch_df["Priority"].max() + 1):
                for index, prev_row in switch_df.iterrows():
                    if prev_row["Priority"] == priority and prev_row["on"] is True:
                        total_power = total_power - prev_row["Power"] * 1000
                        switch_df.at[index, "on"] = False
                        logger.info(
                            f"Turning off {index}, power {prev_row['Power']} kW"
                        )
                        logger.debug(f"Estimated total power now {total_power} kW")
                        if total_power < power_limit * 1000:
                            break
                if total_power < power_limit * 1000:
                    break
            return switch_df

    # case of valid pervious state persent
    elif check_frames(switch_df, prev_states_df, "on") and not switch_df.equals(
        prev_states_df
    ):
        logger.info(f"EXISTING STATE: {prev_states_df['on'].to_list()}")
        if power_now < power_limit * 1000:
            power_reserve = power_limit * 1000 - power_now
            logger.info(
                f"[RESERVE] {power_reserve} W, checking if any appliances can be turned on"
            )
            for priority in range(0, prev_states_df["Priority"].max() + 1):
                for index, prev_row in prev_states_df.iterrows():
                    # check if appliance was on in swtich_df but is off in prev_states_df
                    if (
                        (prev_row["Priority"] == priority)
                        and (prev_row["on"] == False)  # noqa: E712
                        and (switch_df.at[index, "on"] == True)  # noqa: E712
                    ):
                        total_power = power_now + prev_row["Power"] * 1000
                        if switch_df.at[index, "Power"] < power_reserve / 1000:
                            prev_states_df.at[index, "on"] = True
                            power_reserve = power_reserve - prev_row["Power"] * 1000
                            logger.info(
                                f"Turning ON {index}, power {prev_row['Power']} kW"
                            )
                            logger.debug(
                                f"Estimated total power now {total_power / 1000} kW"
                            )
                            logger.debug(f"Power reserve now {power_reserve / 1000} kW")
                    if switch_df.at[index, "on"] == False:  # noqa: E712
                        prev_states_df.at[index, "on"] = False
            logger.debug("No more appliances can be turned on")
            return prev_states_df

        else:
            total_power = power_now

            logger.info(f"[OVER] {total_power - power_limit * 1000} W)")
            logger.info(f"Previous state: {prev_states_df['on'].to_list()}")
            for priority in range(0, switch_df["Priority"].max() + 1):
                for index, prev_row in prev_states_df.iterrows():
                    if prev_row["Priority"] == priority and prev_row["on"] is True:
                        total_power = total_power - prev_row["Power"] * 1000
                        prev_states_df.at[index, "on"] = False
                        logger.info(
                            f"Turning OFF {index}, power {prev_row['Power']} kW"
                        )
                        logger.debug(
                            f"Estimated total power now {total_power / 1000} kW"
                        )
                        if total_power < power_limit * 1000:
                            break
                if total_power < power_limit * 1000:
                    break
            return prev_states_df

    logger.error("Code on wrong path, should not be here")
    return switch_df
