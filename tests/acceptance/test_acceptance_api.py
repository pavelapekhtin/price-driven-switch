from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from price_driven_switch.__main__ import (
    TibberRealtimeConnection,
    app,
    shutdown_event,
    startup_event,
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
    await startup_event()

    try:
        test_tibber_instance = TibberRealtimeConnection(tibber_test_token)
        test_tibber_instance.power_reading = test_case["power_reading"]
        app.state.tibber_instance = test_tibber_instance

        with (
            patch(
                "price_driven_switch.__main__.TibberRealtimeConnection",
                return_value=test_tibber_instance,
            ) as mock_tibber_main,
            patch(
                "price_driven_switch.backend.tibber_connection.TibberRealtimeConnection",
                return_value=test_tibber_instance,
            ),
        ):
            await startup_event()
            app.state.tibber_instance = test_tibber_instance

            with (
                patch(
                    "price_driven_switch.__main__.load_settings_file"
                ) as mock_load_settings_file,
                patch("price_driven_switch.__main__.Prices"),
                patch(
                    "price_driven_switch.__main__.power_limit",
                    return_value=test_case["power_limit"],
                ),
                patch("price_driven_switch.__main__.offset_now", return_value=0.4),
            ):
                mock_load_settings_file.return_value = settings_dict_fixture

                response = client.get("/")

        # Assertions
        mock_tibber_main.assert_called()
        assert response.status_code == 200
        assert response.json() == test_case["expected"]

    finally:
        await shutdown_event()
