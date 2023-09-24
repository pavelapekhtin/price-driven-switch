from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from loguru import logger

from price_driven_switch.__main__ import (
    TibberConnection,
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
@pytest.mark.e2e
async def test_switch_states(test_case, settings_dict_fixture):
    await startup_event()

    try:
        mock_tibber = MagicMock(spec=TibberConnection)
        mock_tibber.power_reading = test_case["power_reading"]
        app.state.tibber_instance = mock_tibber

        with patch(
            "price_driven_switch.__main__.TibberConnection", return_value=mock_tibber
        ) as mock_tibber_main, patch(
            "price_driven_switch.backend.tibber_connection.TibberConnection",
            return_value=mock_tibber,
        ) as mock_tibber_backend:
            await startup_event()
            app.state.tibber_instance = mock_tibber

            with patch(
                "price_driven_switch.__main__.load_settings_file"
            ) as mock_load_settings_file, patch(
                "price_driven_switch.__main__.Prices"
            ) as mock_prices, patch(
                "price_driven_switch.__main__.power_limit",
                return_value=test_case["power_limit"],
            ) as mock_power_limit, patch(
                "price_driven_switch.__main__.offset_now", return_value=0.4
            ) as mock_offset_now:
                mock_load_settings_file.return_value = settings_dict_fixture

                response = client.get("/")

        # Assertions
        mock_tibber_main.assert_called()
        assert response.status_code == 200
        assert response.json() == test_case["expected"]

    finally:
        await shutdown_event()
