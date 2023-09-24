import pandas as pd
import pytest
from hypothesis import given
from hypothesis import strategies as st

from price_driven_switch.backend.configuration import load_settings_file
from price_driven_switch.backend.switch_logic import limit_power, load_appliances_df


@pytest.mark.unit
def test_load_appliances_df(settings_dict_fixture) -> None:
    assert isinstance(load_appliances_df(settings_dict_fixture), pd.DataFrame)
    assert load_appliances_df(settings_dict_fixture).index.name == "Appliance"
    assert load_appliances_df(settings_dict_fixture).columns.equals(
        pd.Index(
            [
                "Setpoint",
                "Power",
                "Priority",
                "Group",
            ]
        )
    )


@pytest.mark.unit
def test_limit_power_specific_cases():
    # Define the data to be used for each test case
    initial_data = {
        "Appliance": ["Boiler 1", "Boiler 2", "Floor"],
        "Power": [1.5, 1.0, 0.8],
        "Priority": [2, 1, 3],
        "on": [True, True, True],
    }

    test_cases = [
        {"power_limit": 2, "power_now": 2100, "expected_on": [True, True, False]},
        {"power_limit": 1, "power_now": 2100, "expected_on": [False, True, False]},
        {"power_limit": 1.5, "power_now": 2501, "expected_on": [False, True, False]},
        {"power_limit": 2, "power_now": 2800, "expected_on": [True, True, False]},
        {"power_limit": 2, "power_now": 1900, "expected_on": [True, True, True]},
        {"power_limit": 3, "power_now": 5300, "expected_on": [False, False, False]},
    ]

    for case in test_cases:
        # Create a DataFrame with the initial data
        test_df = pd.DataFrame(initial_data)

        # Run the limit_power function with the specific power_limit and power_now values
        result_df = limit_power(test_df, case["power_limit"], case["power_now"])

        # Check if the 'on' status of each appliance matches the expected value
        assert list(result_df["on"]) == case["expected_on"]
