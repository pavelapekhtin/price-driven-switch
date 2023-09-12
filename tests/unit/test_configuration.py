import logging

import pytest
import toml

from price_driven_switch.backend.configuration import (
    check_setpoints_in_range,
    check_setpoints_toml,
    check_settings_toml,
    load_setpoints,
    load_settings,
)


def test_create_setpoints_file(tmp_path):
    file_path = tmp_path / "setpoints.toml"
    check_setpoints_toml(file_path)

    # Assert the file was created
    assert file_path.exists()

    # Assert the file has the right content
    with open(file_path, "r", encoding="utf-8") as file:
        data = toml.load(file)
    assert data == {"Appliance1": 1, "Appliance2": 1}


def test_setpoints_file_already_exists(tmp_path, caplog):
    # Create a dummy setpoints file
    file_path = tmp_path / "setpoints.toml"
    file_path.touch()

    with caplog.at_level(logging.DEBUG):
        check_setpoints_toml(file_path)

    # Assert that the log message states the file was found
    assert "Setpoints file found at" in caplog.text


def test_load_setpoints() -> None:
    assert load_setpoints("tests/fixtures/test_setpoints.toml") == {
        "Boilers": 0.5,
        "Floor": 0.4,
        "Other": 0.3,
    }


def test_load_setpoints_out_of_range() -> None:
    with pytest.raises(ValueError):
        load_setpoints("tests/fixtures/test_setpoints_out_of_range.toml")


def test_check_setpoint_in_range() -> None:
    setpoints = {"Boilers": 0.5, "Floor": 0.4, "Other": 0.3}
    assert check_setpoints_in_range(setpoints) is None


def test_load_settings() -> None:
    assert load_settings("tests/fixtures/settings_test.toml") == {
        "Appliances": {
            "Boilers": {"Group": "A", "Power": 1.5, "Priority": 2, "Setpoint": 0.5},
            "Floor": {"Group": "B", "Power": 1.0, "Priority": 1, "Setpoint": 0.5},
            "Other": {"Group": "C", "Power": 0.8, "Priority": 3, "Setpoint": 0.5},
        },
        "Timezone": {"TZ": "Europe/Oslo"},
    }


def test_check_settings_toml() -> None:
    test_data_correct = {
        "Appliances": {
            "Boilers": {"Group": "A", "Power": 1.5, "Priority": 2, "Setpoint": 0.5},
            "Floor": {"Group": "B", "Power": 1.0, "Priority": 1, "Setpoint": 0.5},
            "Other": {"Group": "C", "Power": 0.8, "Priority": 3, "Setpoint": 0.5},
        },
        "Timezone": {"TZ": "Europe/Oslo"},
    }
    wrong_structure = {
        "Appliances": {
            "Boilers": {"Group": "A", "Power": 1.5, "Priority": 2, "Setpoint": 0.5},
            "Floor": {"Grou": "B", "Power": 1.0, "Priority": 1, "Setpoint": 0.5},
            "Other": {"Group": "C", "Power": 0.8, "Priority": 3, "Setpoint": 0.5},
        },
        "Timezone": {"TZ": "Europe/Oslo"},
    }
    out_of_range_setpoint = {
        "Appliances": {
            "Boilers": {"Group": "A", "Power": 1.5, "Priority": 2, "Setpoint": 0.5},
            "Flor": {"Group": "B", "Power": 1.0, "Priority": 1, "Setpoint": 1.5},
            "Other": {"Group": "C", "Power": 0.8, "Priority": 3, "Setpoint": 0.5},
        },
        "Timezone": {"TZ": "Europe/Oslo"},
    }
    assert check_settings_toml(test_data_correct) is None
    with pytest.raises(ValueError):
        check_settings_toml(wrong_structure)
    with pytest.raises(ValueError):
        check_settings_toml(out_of_range_setpoint)
