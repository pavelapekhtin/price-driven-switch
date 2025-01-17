import logging
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest
import toml
from fastapi.testclient import TestClient

from price_driven_switch.__main__ import TibberRealtimeConnection, app

logger = logging.getLogger(__name__)

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
    {
        "power_limit": 1,
        "power_reading": 2100,
        "expected": {"Boiler 1": 1, "Boiler 2": 0, "Floor": 0},
    },
    {
        "power_limit": 1.5,
        "power_reading": 2501,
        "expected": {"Boiler 1": 1, "Boiler 2": 0, "Floor": 0},
    },
    {
        "power_limit": 3,
        "power_reading": 1800,
        "expected": {"Boiler 1": 1, "Boiler 2": 1, "Floor": 1},
    },
    {
        "power_limit": 2.5,
        "power_reading": 2300,
        "expected": {"Boiler 1": 1, "Boiler 2": 1, "Floor": 1},
    },
    {
        "power_limit": 0.5,
        "power_reading": 3000,
        "expected": {"Boiler 1": 0, "Boiler 2": 0, "Floor": 0},
    },
]

TEST_SETTINGS = {
    "Appliances": {
        "Boiler 1": {"Setpoint": 1, "Power": 1.5, "Priority": 3},
        "Boiler 2": {"Setpoint": 1, "Power": 1.0, "Priority": 2},
        "Floor": {"Setpoint": 1, "Power": 0.8, "Priority": 1},
    },
    "Settings": {"MaxPower": 1.0, "Timezone": "Europe/Oslo"},
}


@pytest.mark.parametrize("test_case", test_cases)
@pytest.mark.asyncio
@pytest.mark.e2e
async def test_switch_states_e2e(test_case, tibber_test_token):
    # Create a temporary directory for the test
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create settings.toml in the temp directory
        settings_path = Path(temp_dir) / "settings.toml"
        with open(settings_path, "w") as f:
            toml.dump(TEST_SETTINGS, f)

        # Set environment variable to point to our test settings
        os.environ["SETTINGS_PATH"] = str(settings_path)

        # Setup test client and test instance
        client = TestClient(app)
        test_tibber_instance = TibberRealtimeConnection(tibber_test_token)
        test_tibber_instance.power_reading = test_case["power_reading"]

        # Initialize app state
        app.state.tibber_instance = test_tibber_instance
        app.state.previous_switch_states = pd.DataFrame(
            {
                "Appliance": [],
                "Power": [],
                "Priority": [],
                "on": [],
            }
        )

        # Update TEST_SETTINGS with the correct power limit
        test_settings = TEST_SETTINGS.copy()
        test_settings["Settings"]["MaxPower"] = test_case["power_limit"]

        with (
            patch(
                "price_driven_switch.core.config.load_settings_file",
                return_value=test_settings,
            ),
            patch(
                "price_driven_switch.services.switch_logic.load_settings_file",
                return_value=test_settings,
            ),
            patch(
                "price_driven_switch.core.config.read_power_limit",
                return_value=test_case["power_limit"],
            ),
            patch(
                "price_driven_switch.services.switch_logic.get_price_based_states",
                return_value=pd.DataFrame(
                    {
                        "Appliance": ["Boiler 1", "Boiler 2", "Floor"],
                        "Power": [1.5, 1.0, 0.8],
                        "Priority": [3, 2, 1],
                        "Setpoint": [1, 1, 1],
                        "on": [True, True, True],
                    }
                ).set_index("Appliance"),
            ),
            patch(
                "price_driven_switch.api.routes.switches.offset_now", return_value=0.4
            ),
        ):
            logger.debug(f"Test case: {test_case}")
            logger.debug(f"Test settings: {test_settings}")
            response = client.get("/api")
            logger.debug(f"Response: {response.json()}")

            assert response.status_code == 200
            assert response.json() == test_case["expected"]
