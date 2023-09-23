import asyncio

from price_driven_switch.backend.tibber_connection import TibberConnection

# loop = asyncio.get_event_loop()
# loop.run_until_complete(TibberConnection().get_current_power())

print(asyncio.run(TibberConnection().get_current_power()))
