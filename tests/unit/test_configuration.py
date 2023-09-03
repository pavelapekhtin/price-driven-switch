import logging

import pytest
import toml
from price_driven_switch.backend.configuration import (
    check_setpoints_in_range,
    check_setpoints_toml,
    load_setpoints,
)


def test_create_setpoints_file(tmp_path):
    file_path = tmp_path / "setpoints.toml"
    check_setpoints_toml(file_path)

    # Assert the file was created
    assert file_path.exists()

    # Assert the file has the right content
    with open(file_path, "r") as file:
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
