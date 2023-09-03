from unittest.mock import patch

import pytest
from price_driven_switch.backend.prices import Prices

from tests.fixtures.price_fixtures import (
    FIXTURE_API_RESPONSE,
    FIXTURE_TODAY_PRICES,
    JSON_STRING_FIXTURE,
)

# FIXTURE_JSON_OUTPUT = '{"Boilers": 1, "Floor": 1, "Other": 0}'  # FIXME: not in use

FIXTURE_PRICE_RATIO = 0.4
FIXTURE_SETPOINTS = {"Boilers": 0.5, "Floor": 0.4, "Other": 0.3}
FIXTURE_SWITCH_STATES = {"Boilers": 1, "Floor": 1, "Other": 0}

TEST_TOKEN: str = str("5K4MVS-OjfWhK_4yrjOlFe1F6kJXPVf7eQYggo8ebAE")

# Setpoint fixtures


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
def api_response_fixture():
    return FIXTURE_API_RESPONSE


@pytest.fixture
def today_prices_fixture():
    return FIXTURE_TODAY_PRICES


@pytest.fixture
def json_string_fixture():
    return JSON_STRING_FIXTURE


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
