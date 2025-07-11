import datetime
import json
import logging
from typing import Any, Dict, List, Union
from unittest.mock import patch

import pytest

from price_driven_switch.backend.configuration import load_settings_file
from price_driven_switch.backend.prices import Prices
from price_driven_switch.backend.tibber_connection import TibberConnection

FIXTURE_PRICE_RATIO = 0.4
FIXTURE_SETPOINTS = {"Boilers": 0.5, "Floor": 0.4, "Other": 0.3}
FIXTURE_SWITCH_STATES = {"Boilers": 1, "Floor": 1, "Other": 0}

TEST_TOKEN: str = str("5K4MVS-OjfWhK_4yrjOlFe1F6kJXPVf7eQYggo8ebAE")

PATH_TEST_PRICES = "tests/fixtures/fixture_prices_lowval.json"
PATH_TEST_PRICES_LOW = "tests/fixtures/fixture_prices_lowval.json"

# Setpoint fixtures


# Helper function to load JSON data from file
def load_json_fixture(filename: str) -> Dict[str, Any]:
    with open(filename, "r") as f:
        return json.load(f)


# Helper function to extract specific data from loaded JSON data
def extract_data_from_json(json_data: Dict[str, Any]) -> Dict[str, Any]:
    api_response = json_data.get("api_response", {})
    today_prices = [
        x["total"]
        for x in api_response.get("data", {})
        .get("viewer", {})
        .get("homes", [])[0]
        .get("currentSubscription", {})
        .get("priceInfo", {})
        .get("today", [])
    ]
    return api_response, today_prices  # type: ignore


@pytest.fixture
def mock_get_current_price_ratio():
    mock_data = FIXTURE_PRICE_RATIO
    with patch(
        "price_driven_switch.__main__.get_current_price_ratio",
        return_value=mock_data,
    ):
        yield mock_data


@pytest.fixture
def mock_load_setpoints():
    mock_data = FIXTURE_SETPOINTS
    with patch("price_driven_switch.__main__.load_setpoints", return_value=mock_data):
        yield mock_data


@pytest.fixture
def mock_get_switch_states():
    mock_data = FIXTURE_SWITCH_STATES
    with patch(
        "price_driven_switch.__main__.get_switch_states", return_value=mock_data
    ):
        yield mock_data


# Price file fixtures


@pytest.fixture
def mock_tibber_get_prices():
    mock_data = "a"
    with patch(
        "price_driven_switch.backend.tibber_connection.TibberConnection.get_prices",
        return_value=mock_data,
    ):
        yield mock_data


@pytest.fixture
def mock_tibber_get_power():
    mock_data = 2354
    with patch(
        "price_driven_switch.backend.tibber_connection.TibberConnection.get_current_power",
        return_value=mock_data,
    ):
        yield mock_data


# Tibber fixtures


@pytest.fixture
def tibber_test_token():
    yield TEST_TOKEN


@pytest.fixture
def tibber_instance_fixture():
    return TibberConnection(TEST_TOKEN)


# Price logic fixtures


@pytest.fixture
def api_response_fixture() -> Dict[str, Any]:
    json_data = load_json_fixture(PATH_TEST_PRICES)
    api_response, _ = extract_data_from_json(json_data)
    return api_response  # type: ignore


@pytest.fixture
def today_prices_fixture() -> List[float]:
    json_data = load_json_fixture(PATH_TEST_PRICES)
    _, today_prices = extract_data_from_json(json_data)
    return today_prices  # type: ignore


@pytest.fixture
def base_today_prices_fixture() -> List[float]:
    """Fixture for base prices without grid rent (for backward compatibility)."""
    json_data = load_json_fixture(PATH_TEST_PRICES)
    _, today_prices = extract_data_from_json(json_data)
    return today_prices  # type: ignore


@pytest.fixture
def json_string_fixture():
    json_data = load_json_fixture(PATH_TEST_PRICES)
    json_string = json.dumps(json_data)
    return json_string


@pytest.fixture
def file_date_fixture():
    json_data = load_json_fixture(PATH_TEST_PRICES)
    file_date = json_data.get("timestamp")
    return file_date


@pytest.fixture
def price_now_fixture() -> Union[None, float]:
    json_data = load_json_fixture(PATH_TEST_PRICES)
    try:
        # Navigate to the list containing 'total' values for today
        prices_today = json_data["api_response"]["data"]["viewer"]["homes"][0][
            "currentSubscription"
        ]["priceInfo"]["today"]

        # Get the current time in UTC
        current_time_cet = datetime.datetime.now()
        logging.debug(f"Current time in CET: {current_time_cet}")

        # Get the current hour in CET and adjust by 1 to fix the one-hour offset
        current_hour = current_time_cet.hour
        logging.debug(f"Current hour in CET: {current_hour}")

        # Retrieve the 'total' value for the present hour
        price_now = prices_today[current_hour]["total"]

        return price_now
    except (KeyError, IndexError, TypeError):
        # Handle the exceptions as per your requirements
        return None


@pytest.fixture
def prices_instance_fixture(api_response_fixture):
    with patch(
        "price_driven_switch.backend.prices.load_settings_file"
    ) as mock_load_settings:
        mock_load_settings.return_value = {
            "Settings": {
                "IncludeGridRent": False,
                "GridRent": {
                    "JanMar": {"Day": 50.94, "Night": 38.21},
                    "AprDec": {"Day": 59.86, "Night": 47.13},
                },
            }
        }
        return Prices(api_response_fixture)


@pytest.fixture
def mock_hour_now():
    mock_data = 17
    with patch("price_driven_switch.backend.prices.hour_now", return_value=mock_data):
        yield mock_data


@pytest.fixture()
def mock_instance_hour_now():
    mock_data = datetime.datetime.now().hour
    with patch(
        "price_driven_switch.backend.prices.Prices._hour_now",
        return_value=mock_data,
    ):
        yield mock_data


@pytest.fixture
def mock_instance_with_hour(api_response_fixture):
    mock_hour_data = 6
    with (
        patch(
            "price_driven_switch.backend.prices.Prices._hour_now",
            return_value=mock_hour_data,
        ),
        patch(
            "price_driven_switch.backend.prices.load_settings_file"
        ) as mock_load_settings,
    ):
        mock_load_settings.return_value = {
            "Settings": {
                "IncludeGridRent": False,
                "GridRent": {
                    "JanMar": {"Day": 50.94, "Night": 38.21},
                    "AprDec": {"Day": 59.86, "Night": 47.13},
                },
            }
        }
        instance = Prices(api_response_fixture)
        yield mock_hour_data, instance


@pytest.fixture
def settings_dict_fixture():
    return load_settings_file("tests/fixtures/settings_test.toml")


@pytest.fixture
def grid_rent_config_fixture():
    """Fixture for grid rent configuration."""
    return {
        "JanMar": {"Day": 50.94, "Night": 38.21},
        "AprDec": {"Day": 59.86, "Night": 47.13},
    }


@pytest.fixture
def settings_with_grid_rent_fixture():
    """Fixture for settings with grid rent enabled."""
    return {
        "Appliances": {
            "Boiler 1": {"Power": 1.5, "Priority": 2, "Setpoint": 0.5},
            "Boiler 2": {"Power": 1.0, "Priority": 1, "Setpoint": 0.5},
            "Bathroom Floor": {"Power": 0.8, "Priority": 3, "Setpoint": 0.5},
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


@pytest.fixture
def settings_without_grid_rent_fixture():
    """Fixture for settings with grid rent disabled."""
    return {
        "Appliances": {
            "Boiler 1": {"Power": 1.5, "Priority": 2, "Setpoint": 0.5},
            "Boiler 2": {"Power": 1.0, "Priority": 1, "Setpoint": 0.5},
            "Bathroom Floor": {"Power": 0.8, "Priority": 3, "Setpoint": 0.5},
        },
        "Settings": {
            "MaxPower": 5.0,
            "Timezone": "Europe/Oslo",
            "IncludeGridRent": False,
            "GridRent": {
                "JanMar": {"Day": 50.94, "Night": 38.21},
                "AprDec": {"Day": 59.86, "Night": 47.13},
            },
        },
    }
