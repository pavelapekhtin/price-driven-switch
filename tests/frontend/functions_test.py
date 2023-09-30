import pytest

from price_driven_switch.frontend.st_functions import (
    api_token_input,
    extract_setpoints,
    setpoints_to_dict,
)


@pytest.mark.unit
def test_extract_setpoints():
    # Test with valid data
    sample_data = {
        "Appliances": {
            "Boiler 1": {"Setpoint": 0.5, "Power": 1.5, "Priority": 2},
            "Boiler 2": {"Setpoint": 0.7, "Power": 1.0, "Priority": 1},
            "Floor": {"Setpoint": 0.2, "Power": 0.8, "Priority": 3},
        },
        "Settings": {"MaxPower": 1.0, "Timezone": "Europe/Oslo"},
    }
    expected_output = {"Boiler 1": 0.5, "Boiler 2": 0.7, "Floor": 0.2}
    assert extract_setpoints(sample_data) == expected_output

    # Test with empty Appliances dictionary
    empty_appliances_data = {
        "Appliances": {},
        "Settings": {"MaxPower": 1.0, "Timezone": "Europe/Oslo"},
    }
    assert extract_setpoints(empty_appliances_data) == {}

    # Test with missing Setpoint keys
    missing_setpoint_data = {
        "Appliances": {
            "Boiler 1": {"Power": 1.5, "Priority": 2},
            "Boiler 2": {"Setpoint": 0.7, "Power": 1.0, "Priority": 1},
        },
        "Settings": {"MaxPower": 1.0, "Timezone": "Europe/Oslo"},
    }
    expected_missing_setpoint_output = {"Boiler 1": 0.0, "Boiler 2": 0.7}
    assert extract_setpoints(missing_setpoint_data) == expected_missing_setpoint_output

    # Test with entirely missing Appliances key
    missing_appliances_key_data = {
        "Settings": {"MaxPower": 1.0, "Timezone": "Europe/Oslo"}
    }
    assert extract_setpoints(missing_appliances_key_data) == {}
