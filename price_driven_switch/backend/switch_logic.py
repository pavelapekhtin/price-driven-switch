# mypy: disable-error-code="index,operator"
# pyright: reportGeneralTypeIssues=false, reportArgumentType=false, reportOperatorIssue=false
from typing import Any

import pandas as pd

from price_driven_switch.backend.logging_utils import (
    log_if_changed,
    log_switch_decision_summary,
    structured_logger,
)


def load_appliances_df(settings: dict[str, Any]) -> pd.DataFrame:
    """Load appliances from settings.toml into a pandas DataFrame."""
    appliances = settings["Appliances"]
    df = pd.DataFrame.from_dict(appliances, orient="index")  # type: ignore
    df.index.name = "Appliance"
    return df


current_offset: float


def get_price_based_states(
    appliance_df: pd.DataFrame,
    offset_now: float,
) -> pd.DataFrame:
    appliance_df["on"] = appliance_df["Setpoint"] >= offset_now
    structured_logger.log_price_logic_result(appliance_df, offset_now)
    return appliance_df


def set_price_only_based_states(
    settings: dict[str, Any], offset_now: float
) -> pd.DataFrame:
    output = get_price_based_states(load_appliances_df(settings), offset_now)
    return output


def check_frames(df1: pd.DataFrame, df2: pd.DataFrame, ignore_column: str) -> bool:
    # Selecting all columns except the one to ignore
    df1_filtered = df1[df1.columns.difference([ignore_column])]  # type: ignore
    df2_filtered = df2[df2.columns.difference([ignore_column])]  # type: ignore

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
        log_if_changed("[POWER] Power limiting bypassed (zero power or limit)", 60)
        return switch_df

    elif switch_df.equals(prev_states_df) or not check_frames(
        switch_df, prev_states_df, "on"
    ):
        if power_now < power_limit * 1000:
            structured_logger.logger.log_power_limiting_decision(
                power_now, power_limit, "OK"
            )
            return switch_df
        if power_now > power_limit * 1000:
            total_power = power_now
            excess_w = power_now - power_limit * 1000
            structured_logger.logger.log_power_limiting_decision(
                power_now, power_limit, "OVER", f"Reducing power by {excess_w}W"
            )

            for priority in range(0, switch_df["Priority"].max() + 1):
                for index, prev_row in switch_df.iterrows():
                    if prev_row["Priority"] == priority and prev_row["on"] is True:
                        total_power = total_power - prev_row["Power"] * 1000
                        switch_df.at[index, "on"] = False
                        structured_logger.log_appliance_turned_off(
                            str(index),
                            float(prev_row["Power"]),
                            int(prev_row["Priority"]),
                        )
                        if total_power < power_limit * 1000:
                            break
                if total_power < power_limit * 1000:
                    break
            return switch_df

    # case of valid pervious state persent
    elif check_frames(switch_df, prev_states_df, "on") and not switch_df.equals(
        prev_states_df
    ):
        if power_now < power_limit * 1000:
            power_reserve = power_limit * 1000 - power_now
            structured_logger.logger.log_power_limiting_decision(
                power_now,
                power_limit,
                "RESERVE",
                f"Checking if appliances can be turned ON with {power_reserve}W available",
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
                            structured_logger.log_appliance_turned_on(
                                str(index),
                                float(prev_row["Power"]),
                                int(prev_row["Priority"]),
                            )
                    if switch_df.at[index, "on"] == False:  # noqa: E712
                        prev_states_df.at[index, "on"] = False

            # Log final summary for this case
            log_switch_decision_summary(
                switch_df,
                prev_states_df,
                power_now,
                power_limit,
                0.5,  # Default price offset for logging
            )
            return prev_states_df

        else:
            total_power = power_now
            excess_w = total_power - power_limit * 1000
            structured_logger.logger.log_power_limiting_decision(
                power_now,
                power_limit,
                "OVER",
                f"Reducing power by {excess_w}W from existing state",
            )

            for priority in range(0, switch_df["Priority"].max() + 1):
                for index, prev_row in prev_states_df.iterrows():
                    if prev_row["Priority"] == priority and prev_row["on"] is True:
                        total_power = total_power - prev_row["Power"] * 1000
                        prev_states_df.at[index, "on"] = False
                        structured_logger.log_appliance_turned_off(
                            str(index),
                            float(prev_row["Power"]),
                            int(prev_row["Priority"]),
                        )
                        if total_power < power_limit * 1000:
                            break
                if total_power < power_limit * 1000:
                    break
            return prev_states_df

    structured_logger.log_error_state("Unexpected code path in limit_power function")
    return switch_df
