import logging

import pytest
import toml

from price_driven_switch.backend.configuration import (
    create_default_settings_if_none,
    default_settings_toml,
    update_max_power,
    validate_settings,
)


@pytest.mark.unit
def test_create_setpoints_file(tmp_path):
    file_path = tmp_path / "settings.toml"
    create_default_settings_if_none(file_path)

    # Assert the file was created
    assert file_path.exists()

    # Assert the file has the right content
    with open(file_path, "r", encoding="utf-8") as file:
        data = toml.load(file)
    assert data == default_settings_toml


@pytest.mark.unit
def test_setpoints_file_already_exists(tmp_path, caplog):
    # Create a dummy setpoints file
    file_path = tmp_path / "setpoints.toml"
    file_path.touch()

    with caplog.at_level(logging.DEBUG):
        create_default_settings_if_none(file_path)

    # Assert that the log message states the file was found
    assert "Settings file found at" in caplog.text


@pytest.mark.unit
def test_check_settings_toml() -> None:
    test_data_correct = {
        "Appliances": {
            "Boilers": {"Group": "A", "Power": 1.5, "Priority": 2, "Setpoint": 0.5},
            "Floor": {"Group": "B", "Power": 1.0, "Priority": 1, "Setpoint": 0.5},
            "Other": {"Group": "C", "Power": 0.8, "Priority": 3, "Setpoint": 0.5},
        },
        "Settings": {"MaxPower": 5.0, "Timezone": "Europe/Oslo"},
    }
    wrong_structure = {
        "Appliances": {
            "Boilers": {"Group": "A", "Power": 1.5, "Priority": 2, "Setpoint": 0.5},
            "Floor": {"Grou": "B", "Power": 1.0, "Priority": 1, "Setpoint": 0.5},
            "Other": {"Group": "C", "Power": 0.8, "Priority": 3, "Setpoint": 0.5},
        },
        "Settings": {"MaxPower": 5.0, "Timezone": "Europe/Oslo"},
    }
    out_of_range_setpoint = {
        "Appliances": {
            "Boilers": {"Group": "A", "Power": 1.5, "Priority": 2, "Setpoint": 0.5},
            "Flor": {"Group": "B", "Power": 1.0, "Priority": 1, "Setpoint": 1.5},
            "Other": {"Group": "C", "Power": 0.8, "Priority": 3, "Setpoint": 0.5},
        },
        "Settings": {"MaxPower": 5.0, "Timezone": "Europe/Oslo"},
    }
    missing_timezone = {
        "Appliances": {
            "Boilers": {"Group": "A", "Power": 1.5, "Priority": 2, "Setpoint": 0.5},
            "Floor": {"Group": "B", "Power": 1.0, "Priority": 1, "Setpoint": 0.5},
            "Other": {"Group": "C", "Power": 0.8, "Priority": 3, "Setpoint": 0.5},
        },
        "Settings": {"MaxPower": 5.0},
    }
    assert validate_settings(test_data_correct) is None

    with pytest.raises(ValueError):
        validate_settings(wrong_structure)
        validate_settings(out_of_range_setpoint)
        validate_settings(missing_timezone)


@pytest.mark.unit
def test_update_max_power():
    # Test with valid data
    sample_data = {
        "Appliances": {
            "Boiler 1": {"Setpoint": 0.5, "Power": 1.5, "Priority": 2},
            "Boiler 2": {"Setpoint": 0.5, "Power": 1.0, "Priority": 1},
            "Floor": {"Setpoint": 0.5, "Power": 0.8, "Priority": 3},
        },
        "Settings": {"MaxPower": 1.0, "Timezone": "Europe/Oslo"},
    }
    new_max_power = 1.5
    updated_data = update_max_power(sample_data, new_max_power)
    assert updated_data["Settings"]["MaxPower"] == new_max_power

    # Test with missing 'Settings' key
    sample_data_missing_settings = {
        "Appliances": {
            "Boiler 1": {"Setpoint": 0.5, "Power": 1.5, "Priority": 2},
            "Boiler 2": {"Setpoint": 0.5, "Power": 1.0, "Priority": 1},
            "Floor": {"Setpoint": 0.5, "Power": 0.8, "Priority": 3},
        }
    }
    updated_data_missing_settings = update_max_power(
        sample_data_missing_settings, new_max_power
    )
    assert "Settings" not in updated_data_missing_settings
