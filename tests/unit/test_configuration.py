import pytest
import toml
from loguru import logger

from price_driven_switch.backend.configuration import (
    create_default_settings_if_none,
    default_settings_toml,
    ensure_grid_rent_settings,
    get_package_version_from_toml,
    update_max_power,
    validate_settings,
)

captured_logs = []


def sink(message):
    global captured_logs
    captured_logs.append(message)


@pytest.mark.unit
def test_create_setpoints_file(tmp_path):
    file_path = tmp_path / "settings.toml"
    create_default_settings_if_none(file_path)

    # Assert the file was created
    assert file_path.exists()

    # Assert the file has the right content
    with open(file_path, encoding="utf-8") as file:
        data = toml.load(file)
    assert data == default_settings_toml


@pytest.mark.unit
def test_setpoints_file_already_exists(tmp_path):
    global captured_logs
    captured_logs = []

    handler_id = logger.add(sink, format="{message}")

    file_path = tmp_path / "settings.toml"
    file_path.touch()
    create_default_settings_if_none(file_path)

    logger.remove(handler_id)

    found = any("Settings file found at" in log for log in captured_logs)
    assert found, f"Log not found, captured logs were: {captured_logs}"


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


@pytest.mark.unit
def test_get_package_version_from_toml():
    assert isinstance(get_package_version_from_toml(), str)


@pytest.mark.unit
def test_default_settings_include_grid_rent():
    """Test that default settings include grid rent configuration."""
    assert "Settings" in default_settings_toml
    assert "IncludeGridRent" in default_settings_toml["Settings"]
    assert "GridRent" in default_settings_toml["Settings"]

    # Check grid rent structure
    grid_rent = default_settings_toml["Settings"]["GridRent"]
    assert "JanMar" in grid_rent
    assert "AprDec" in grid_rent

    # Check JanMar rates
    assert "Day" in grid_rent["JanMar"]
    assert "Night" in grid_rent["JanMar"]
    assert grid_rent["JanMar"]["Day"] == 50.94
    assert grid_rent["JanMar"]["Night"] == 38.21

    # Check AprDec rates
    assert "Day" in grid_rent["AprDec"]
    assert "Night" in grid_rent["AprDec"]
    assert grid_rent["AprDec"]["Day"] == 59.86
    assert grid_rent["AprDec"]["Night"] == 47.13


@pytest.mark.unit
def test_validate_settings_with_grid_rent():
    """Test that settings validation works with grid rent configuration."""
    test_data_with_grid_rent = {
        "Appliances": {
            "Boilers": {"Group": "A", "Power": 1.5, "Priority": 2, "Setpoint": 0.5},
            "Floor": {"Group": "B", "Power": 1.0, "Priority": 1, "Setpoint": 0.5},
            "Other": {"Group": "C", "Power": 0.8, "Priority": 3, "Setpoint": 0.5},
        },
        "Settings": {
            "MaxPower": 5.0,
            "Timezone": "Europe/Oslo",
            "IncludeGridRent": True,
            "GridRent": {
                "JanMar": {"Day": 50.94, "Night": 38.21},
                "AprDec": {"Day": 59.86, "Night": 47.13},
            },
        },
    }

    # Should not raise any exception
    assert validate_settings(test_data_with_grid_rent) is None


@pytest.mark.unit
def test_validate_settings_without_grid_rent():
    """Test that settings validation works without grid rent configuration."""
    test_data_without_grid_rent = {
        "Appliances": {
            "Boilers": {"Group": "A", "Power": 1.5, "Priority": 2, "Setpoint": 0.5},
            "Floor": {"Group": "B", "Power": 1.0, "Priority": 1, "Setpoint": 0.5},
            "Other": {"Group": "C", "Power": 0.8, "Priority": 3, "Setpoint": 0.5},
        },
        "Settings": {"MaxPower": 5.0, "Timezone": "Europe/Oslo"},
    }

    # Should not raise any exception (grid rent is optional)
    assert validate_settings(test_data_without_grid_rent) is None


@pytest.mark.unit
def test_ensure_grid_rent_settings_complete():
    """Test that ensure_grid_rent_settings doesn't modify complete settings."""
    complete_settings = {
        "Appliances": {
            "Boiler 1": {"Power": 1.5, "Priority": 2, "Setpoint": 0.5},
        },
        "Settings": {
            "MaxPower": 5.0,
            "Timezone": "Europe/Oslo",
            "IncludeGridRent": True,
            "GridRent": {
                "JanMar": {"Day": 50.94, "Night": 38.21},
                "AprDec": {"Day": 59.86, "Night": 47.13},
            },
        },
    }

    result = ensure_grid_rent_settings(complete_settings)
    assert result == complete_settings


@pytest.mark.unit
def test_ensure_grid_rent_settings_missing_include_grid_rent():
    """Test that ensure_grid_rent_settings adds missing IncludeGridRent."""
    settings_missing_include = {
        "Appliances": {
            "Boiler 1": {"Power": 1.5, "Priority": 2, "Setpoint": 0.5},
        },
        "Settings": {
            "MaxPower": 5.0,
            "Timezone": "Europe/Oslo",
            "GridRent": {
                "JanMar": {"Day": 50.94, "Night": 38.21},
                "AprDec": {"Day": 59.86, "Night": 47.13},
            },
        },
    }

    result = ensure_grid_rent_settings(settings_missing_include)
    assert result["Settings"]["IncludeGridRent"] is True
    assert "IncludeGridRent" in result["Settings"]


@pytest.mark.unit
def test_ensure_grid_rent_settings_missing_grid_rent():
    """Test that ensure_grid_rent_settings adds missing GridRent."""
    settings_missing_grid_rent = {
        "Appliances": {
            "Boiler 1": {"Power": 1.5, "Priority": 2, "Setpoint": 0.5},
        },
        "Settings": {
            "MaxPower": 5.0,
            "Timezone": "Europe/Oslo",
            "IncludeGridRent": True,
        },
    }

    result = ensure_grid_rent_settings(settings_missing_grid_rent)
    assert "GridRent" in result["Settings"]
    assert "JanMar" in result["Settings"]["GridRent"]
    assert "AprDec" in result["Settings"]["GridRent"]
    assert result["Settings"]["GridRent"]["JanMar"]["Day"] == 50.94
    assert result["Settings"]["GridRent"]["JanMar"]["Night"] == 38.21
    assert result["Settings"]["GridRent"]["AprDec"]["Day"] == 59.86
    assert result["Settings"]["GridRent"]["AprDec"]["Night"] == 47.13


@pytest.mark.unit
def test_ensure_grid_rent_settings_missing_settings_section():
    """Test that ensure_grid_rent_settings adds Settings section if missing."""
    settings_missing_settings = {
        "Appliances": {
            "Boiler 1": {"Power": 1.5, "Priority": 2, "Setpoint": 0.5},
        },
    }

    result = ensure_grid_rent_settings(settings_missing_settings)
    assert "Settings" in result
    assert "IncludeGridRent" in result["Settings"]
    assert "GridRent" in result["Settings"]


@pytest.mark.unit
def test_ensure_grid_rent_settings_missing_period():
    """Test that ensure_grid_rent_settings adds missing grid rent periods."""
    settings_missing_period = {
        "Appliances": {
            "Boiler 1": {"Power": 1.5, "Priority": 2, "Setpoint": 0.5},
        },
        "Settings": {
            "MaxPower": 5.0,
            "Timezone": "Europe/Oslo",
            "IncludeGridRent": True,
            "GridRent": {
                "JanMar": {"Day": 50.94, "Night": 38.21},
                # Missing AprDec
            },
        },
    }

    result = ensure_grid_rent_settings(settings_missing_period)
    assert "AprDec" in result["Settings"]["GridRent"]
    assert result["Settings"]["GridRent"]["AprDec"]["Day"] == 59.86
    assert result["Settings"]["GridRent"]["AprDec"]["Night"] == 47.13


@pytest.mark.unit
def test_ensure_grid_rent_settings_missing_rate_type():
    """Test that ensure_grid_rent_settings adds missing rate types."""
    settings_missing_rate = {
        "Appliances": {
            "Boiler 1": {"Power": 1.5, "Priority": 2, "Setpoint": 0.5},
        },
        "Settings": {
            "MaxPower": 5.0,
            "Timezone": "Europe/Oslo",
            "IncludeGridRent": True,
            "GridRent": {
                "JanMar": {"Day": 50.94},  # Missing Night
                "AprDec": {"Day": 59.86, "Night": 47.13},
            },
        },
    }

    result = ensure_grid_rent_settings(settings_missing_rate)
    assert "Night" in result["Settings"]["GridRent"]["JanMar"]
    assert result["Settings"]["GridRent"]["JanMar"]["Night"] == 38.21


@pytest.mark.unit
def test_ensure_grid_rent_settings_invalid_grid_rent_structure():
    """Test that ensure_grid_rent_settings replaces invalid GridRent structure."""
    settings_invalid_grid_rent = {
        "Appliances": {
            "Boiler 1": {"Power": 1.5, "Priority": 2, "Setpoint": 0.5},
        },
        "Settings": {
            "MaxPower": 5.0,
            "Timezone": "Europe/Oslo",
            "IncludeGridRent": True,
            "GridRent": "invalid_structure",  # Should be a dict
        },
    }

    result = ensure_grid_rent_settings(settings_invalid_grid_rent)
    assert isinstance(result["Settings"]["GridRent"], dict)
    assert "JanMar" in result["Settings"]["GridRent"]
    assert "AprDec" in result["Settings"]["GridRent"]


@pytest.mark.unit
def test_ensure_grid_rent_settings_invalid_period_structure():
    """Test that ensure_grid_rent_settings replaces invalid period structure."""
    settings_invalid_period = {
        "Appliances": {
            "Boiler 1": {"Power": 1.5, "Priority": 2, "Setpoint": 0.5},
        },
        "Settings": {
            "MaxPower": 5.0,
            "Timezone": "Europe/Oslo",
            "IncludeGridRent": True,
            "GridRent": {
                "JanMar": "invalid_structure",  # Should be a dict
                "AprDec": {"Day": 59.86, "Night": 47.13},
            },
        },
    }

    result = ensure_grid_rent_settings(settings_invalid_period)
    assert isinstance(result["Settings"]["GridRent"]["JanMar"], dict)
    assert "Day" in result["Settings"]["GridRent"]["JanMar"]
    assert "Night" in result["Settings"]["GridRent"]["JanMar"]


@pytest.mark.unit
def test_create_default_settings_if_none_updates_existing_file(tmp_path):
    """Test that create_default_settings_if_none updates existing file with missing grid rent."""
    file_path = tmp_path / "settings.toml"

    # Create a settings file without grid rent
    incomplete_settings = {
        "Appliances": {
            "Boiler 1": {"Power": 1.5, "Priority": 2, "Setpoint": 0.5},
        },
        "Settings": {
            "MaxPower": 5.0,
            "Timezone": "Europe/Oslo",
        },
    }

    with open(file_path, "w", encoding="utf-8") as file:
        toml.dump(incomplete_settings, file)

    # Call the function
    create_default_settings_if_none(file_path)

    # Check that the file was updated
    with open(file_path, encoding="utf-8") as file:
        updated_data = toml.load(file)

    assert "IncludeGridRent" in updated_data["Settings"]
    assert "GridRent" in updated_data["Settings"]
    assert updated_data["Settings"]["IncludeGridRent"] is True
    assert "JanMar" in updated_data["Settings"]["GridRent"]
    assert "AprDec" in updated_data["Settings"]["GridRent"]


@pytest.mark.unit
def test_create_default_settings_if_none_preserves_existing_grid_rent(tmp_path):
    """Test that create_default_settings_if_none preserves existing grid rent settings."""
    file_path = tmp_path / "settings.toml"

    # Create a settings file with custom grid rent
    custom_settings = {
        "Appliances": {
            "Boiler 1": {"Power": 1.5, "Priority": 2, "Setpoint": 0.5},
        },
        "Settings": {
            "MaxPower": 5.0,
            "Timezone": "Europe/Oslo",
            "IncludeGridRent": False,
            "GridRent": {
                "JanMar": {"Day": 60.0, "Night": 40.0},
                "AprDec": {"Day": 70.0, "Night": 50.0},
            },
        },
    }

    with open(file_path, "w", encoding="utf-8") as file:
        toml.dump(custom_settings, file)

    # Call the function
    create_default_settings_if_none(file_path)

    # Check that the file was not changed
    with open(file_path, encoding="utf-8") as file:
        updated_data = toml.load(file)

    assert updated_data == custom_settings
