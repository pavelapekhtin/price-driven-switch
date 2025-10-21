from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from price_driven_switch.__main__ import (
    TibberRealtimeConnection,
    app,
)

client = TestClient(app)

test_cases = [
    {
        "power_limit": 2,
        "power_reading": 2100,
        "expected": {"Boiler 1": 1, "Boiler 2": 1, "Floor": 0},
    },
    {
        "power_limit": 2,
        "power_reading": 9100,
        "expected": {"Boiler 1": 0, "Boiler 2": 0, "Floor": 0},
    },
]


@pytest.mark.parametrize("test_case", test_cases)
@pytest.mark.asyncio
@pytest.mark.integration
async def test_switch_states(test_case, settings_dict_fixture, tibber_test_token):
    test_tibber_instance = TibberRealtimeConnection(tibber_test_token)
    test_tibber_instance.power_reading = test_case["power_reading"]

    with (
        patch(
            "price_driven_switch.__main__.tibber_instance",
            test_tibber_instance,
        ),
        patch(
            "price_driven_switch.__main__.load_settings_file",
            return_value=settings_dict_fixture,
        ),
        patch("price_driven_switch.__main__.Prices"),
        patch(
            "price_driven_switch.__main__.power_limit",
            return_value=test_case["power_limit"],
        ),
        patch("price_driven_switch.__main__.offset_now", return_value=0.4),
    ):
        response = client.get("/api/")

    # Assertions
    assert response.status_code == 200
    assert response.json() == test_case["expected"]


@pytest.mark.asyncio
async def test_appliance_list_endpoint():
    """Test that /appliances returns URL-safe names with underscores."""
    with patch(
        "price_driven_switch.__main__.get_appliance_names",
        return_value=["Boiler 1", "Boiler 2", "Bathroom Floor"],
    ):
        response = client.get("/appliances")

    assert response.status_code == 200
    expected_appliances = ["Boiler_1", "Boiler_2", "Bathroom_Floor"]
    assert response.json() == {"appliances": expected_appliances}


@pytest.mark.asyncio
async def test_individual_appliance_endpoint():
    """Test individual appliance endpoint with underscore format."""
    test_tibber_instance = TibberRealtimeConnection()
    test_tibber_instance.power_reading = 1000

    with (
        patch("price_driven_switch.__main__.tibber_instance", test_tibber_instance),
        patch("price_driven_switch.__main__.load_settings_file") as mock_settings,
        patch("price_driven_switch.__main__.Prices"),
        patch("price_driven_switch.__main__.power_limit", return_value=5.0),
        patch("price_driven_switch.__main__.offset_now", return_value=0.4),
    ):
        # Mock settings with "Boiler 1" appliance
        mock_settings.return_value = {
            "Appliances": {"Boiler 1": {"Power": 1.5, "Priority": 1, "Setpoint": 0.3}}
        }

        # Test underscore format endpoint
        response = client.get("/appliance/Boiler_1")

    assert response.status_code == 200
    assert response.json() in [0, 1]  # Should return either 0 or 1


@pytest.mark.asyncio
async def test_individual_appliance_previous_endpoint():
    """Test individual appliance previous state endpoint with underscore format."""
    with (
        patch("price_driven_switch.__main__.load_settings_file") as mock_settings,
        patch("price_driven_switch.__main__.Prices"),
        patch("price_driven_switch.__main__.offset_now", return_value=0.4),
    ):
        # Mock settings with "Boiler 1" appliance
        mock_settings.return_value = {
            "Appliances": {"Boiler 1": {"Power": 1.5, "Priority": 1, "Setpoint": 0.3}}
        }

        # Test underscore format endpoint for previous state
        response = client.get("/appliance/Boiler_1/previous")

    assert response.status_code == 200
    assert response.json() in [0, 1]  # Should return either 0 or 1


@pytest.mark.asyncio
async def test_nonexistent_appliance_error():
    """Test 404 error for non-existent appliance."""
    with (
        patch("price_driven_switch.__main__.load_settings_file") as mock_settings,
        patch("price_driven_switch.__main__.Prices"),
        patch("price_driven_switch.__main__.offset_now", return_value=0.4),
    ):
        # Mock settings with only "Boiler 1"
        mock_settings.return_value = {
            "Appliances": {"Boiler 1": {"Power": 1.5, "Priority": 1, "Setpoint": 0.3}},
            "Settings": {"MaxPower": 5.0},
        }

        response = client.get("/appliance/NonExistent_Appliance")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_root_endpoint():
    """Test that root endpoint provides API information."""
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "endpoints" in data
    assert data["endpoints"]["all_states"] == "/api/"
    assert data["endpoints"]["appliances"] == "/appliances"
