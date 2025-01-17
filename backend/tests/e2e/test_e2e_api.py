import pandas as pd
import pytest
from fastapi.testclient import TestClient

from price_driven_switch.__main__ import TibberRealtimeConnection, app

client = TestClient(app)


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_root_endpoint(tibber_test_token):
    # Setup
    test_tibber_instance = TibberRealtimeConnection(tibber_test_token)
    await test_tibber_instance.initialize_tibber()
    await test_tibber_instance.subscribe_to_realtime_data()
    app.state.tibber_instance = test_tibber_instance
    app.state.previous_switch_states = pd.DataFrame(
        {
            "Appliance": [],
            "Power": [],
            "Priority": [],
            "on": [],
        }
    )

    try:
        # Test
        response = client.get("/api")

        # Assert
        assert response.status_code == 200
        assert isinstance(response.json(), dict)
    finally:
        # Cleanup
        await test_tibber_instance.close()


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_subscription_info_endpoint(tibber_test_token):
    # Setup
    test_tibber_instance = TibberRealtimeConnection(tibber_test_token)
    await test_tibber_instance.initialize_tibber()
    await test_tibber_instance.subscribe_to_realtime_data()
    app.state.tibber_instance = test_tibber_instance

    try:
        # Test
        response = client.get("/api/subscription_info")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "power_reading" in data
        assert "subscription_status" in data
        assert isinstance(data["power_reading"], (int, float))
        assert isinstance(data["subscription_status"], bool)
    finally:
        # Cleanup
        await test_tibber_instance.close()


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_get_power_limit():
    response = client.get("/api/settings/power-limit")
    assert response.status_code == 200
    assert isinstance(response.json(), (int, float))
