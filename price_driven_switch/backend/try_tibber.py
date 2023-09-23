import asyncio

from price_driven_switch.backend.configuration import load_settings_file
from price_driven_switch.backend.switch_logic import (
    limit_power,
    ungrouped_switches_pipeline,
)
from price_driven_switch.backend.tibber_connection import TibberConnection

# loop = asyncio.get_event_loop()
# loop.run_until_complete(TibberConnection().get_current_power())

# power_now = asyncio.run(TibberConnection().get_current_power())

# print(power_now)

settings = load_settings_file("tests/fixtures/settings_test.toml")
switch_states = ungrouped_switches_pipeline(settings, 0.7)

result = limit_power(switch_states, 1.0, 1900)
print(result)
