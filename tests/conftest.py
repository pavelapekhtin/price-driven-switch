import datetime
import json
from typing import Any, Dict, List, Tuple, Union
from unittest.mock import patch

import pytest
import pytz

from price_driven_switch.backend.prices import Prices

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
        "price_driven_switch.backend.tibber.TibberConnection.get_prices",
        return_value=mock_data,
    ):
        yield mock_data


# Tibber fixtures


@pytest.fixture
def tibber_test_token():
    yield TEST_TOKEN


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
        current_time_utc = datetime.datetime.now(datetime.timezone.utc)

        # Convert to Central European Time (CET)
        cet = pytz.timezone("Europe/Berlin")
        current_time_cet = current_time_utc.astimezone(cet)

        # Get the current hour in CET and adjust by 1 to fix the one-hour offset
        current_hour = current_time_cet.hour + 1

        # Check if the hour goes out of range (e.g., from 23 to 24)
        if current_hour >= len(prices_today):
            current_hour = 0  # Loop back to the first hour if needed

        # Retrieve the 'total' value for the present hour
        price_now = prices_today[current_hour]["total"]

        return price_now
    except (KeyError, IndexError, TypeError):
        # Handle the exceptions as per your requirements
        return None


@pytest.fixture
def prices_instance_fixture(api_response_fixture):
    return Prices(api_response_fixture)


@pytest.fixture
def mock_hour_now():
    mock_data = 17
    with patch("price_driven_switch.backend.prices.hour_now", return_value=mock_data):
        yield mock_data


@pytest.fixture
def mock_instance_hour_now():
    mock_data = 17
    with patch(
        "price_driven_switch.backend.prices.Prices._hour_now",
        return_value=mock_data,
    ):
        yield mock_data


@pytest.fixture
def mock_instance_with_hour(api_response_fixture):
    mock_hour_data = 6
    with patch(
        "price_driven_switch.backend.prices.Prices._hour_now",
        return_value=mock_hour_data,
    ):
        instance = Prices(api_response_fixture)
        yield mock_hour_data, instance
