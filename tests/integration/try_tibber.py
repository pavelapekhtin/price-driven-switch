import asyncio


from price_driven_switch.backend.tibber_connection import TibberConnection

# loop = asyncio.get_event_loop()
# loop.run_until_complete(TibberConnection().current_power_subscription())


# async def main():
#     prices = await TibberConnection().get_prices()
#     print(prices)


# if __name__ == "__main__":
#     asyncio.run(main())


# power_now = asyncio.run(TibberConnection().get_current_power())

# print(power_now)

# settings = load_settings_file("tests/fixtures/settings_test.toml")
# switch_states = ungrouped_switches_pipeline(settings, 0.7)

# result = limit_power(switch_states, 2, 2800)
# print(result)

tibber_instance = TibberConnection("5K4MVS-OjfWhK_4yrjOlFe1F6kJXPVf7eQYggo8ebAE")


async def prices():
    prices = await tibber_instance.get_prices()
    print(prices)


loop = asyncio.get_event_loop()
loop.run_until_complete(prices())
