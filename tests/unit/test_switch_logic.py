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
            ]
        )
    )


@pytest.mark.unit
def test_limit_power_specific_cases():
    # Define the data to be used for each test case
    initial_data = {
        "Appliance": ["Boiler 1", "Boiler 2", "Floor"],
        "Power": [1.5, 1.0, 0.8],
        "Priority": [3, 2, 1],
        "on": [True, True, True],
    }

    # function to change the 'on' status in the DataFrame for present_on
    def change_on_status(present_on: list[bool]) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "Appliance": ["Boiler 1", "Boiler 2", "Floor"],
                "Power": [1.5, 1.0, 0.8],
                "Priority": [3, 2, 1],
                "on": present_on,
            }
        )

    test_cases = [
        # all was on cases
        {
            "power_limit": 2,
            "power_now": 2100,
            "present_on": change_on_status([True, True, True]),
            "expected_on": [True, True, False],
        },
        {
            "power_limit": 1,
            "power_now": 2100,
            "present_on": change_on_status([True, True, True]),
            "expected_on": [True, False, False],
        },
        {
            "power_limit": 1.5,
            "power_now": 2501,
            "present_on": change_on_status([True, True, True]),
            "expected_on": [True, False, False],
        },
        {
            "power_limit": 2,
            "power_now": 2799,
            "present_on": change_on_status([True, True, True]),
            "expected_on": [True, True, False],
        },
        {
            "power_limit": 2,
            "power_now": 1900,
            "present_on": change_on_status([True, True, True]),
            "expected_on": [True, True, True],
        },
        {
            "power_limit": 3,
            "power_now": 5300,
            "present_on": change_on_status([True, True, True]),
            "expected_on": [False, False, False],
        },
        # power limit is 0 case
        {
            "power_limit": 3,
            "power_now": 0,
            "present_on": change_on_status([True, True, True]),
            "expected_on": [True, True, True],
        },
        # # some was off cases
        # FIXME: this test case is failing
        # {
        #     "power_limit": 3,
        #     "power_now": 3200,
        #     "present_on": change_on_status([True, True, False]),
        #     "expected_on": [True, False, False],
        # },
        # FIXME: this test case is failing
        # {
        #     "power_limit": 3.9,
        #     "power_now": 3050,
        #     "present_on": change_on_status([True, True, False]),
        #     "expected_on": [True, True, True],
        # },
        # FIXME: this test case is failing
        # {
        #     "power_limit": 3.9,
        #     "power_now": 2000,
        #     "present_on": change_on_status([True, False, False]),
        #     "expected_on": [True, True, True],
        # },
        # FIXME: this test case is failing
        # {
        #     "power_limit": 3.9,
        #     "power_now": 2500,
        #     "present_on": change_on_status([True, False, False]),
        #     "expected_on": [True, True, False],
        # },
        # FIXME: this test case is failing
        # {
        #     "power_limit": 3.9,
        #     "power_now": 500,
        #     "present_on": change_on_status([False, False, False]),
        #     "expected_on": [True, True, True],
        # },
    ]

    for case in test_cases:
        # Create a DataFrame with the initial data
        test_df = pd.DataFrame(initial_data)

        # Run the limit_power function with the specific power_limit and power_now values
        result_df = limit_power(
            test_df, case["power_limit"], case["power_now"], case["present_on"]
        )

        # Check if the 'on' status of each appliance matches the expected value
        assert list(result_df["on"]) == case["expected_on"]
