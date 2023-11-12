import asyncio
from typing import Hashable

import pandas as pd
import uvicorn
from fastapi import FastAPI
from loguru import logger

from price_driven_switch.backend.configuration import load_settings_file
from price_driven_switch.backend.price_file import PriceFile
from price_driven_switch.backend.prices import Prices
from price_driven_switch.backend.switch_logic import (
    limit_power,
    set_price_only_based_states,
)
from price_driven_switch.backend.tibber_connection import TibberConnection

logger.add(
    "logs/fast_api.log",
    rotation="1 week",
    retention="7 days",
    level="INFO",
    enqueue=False,
)

app = FastAPI()

SETTINGS_PATH = "price_driven_switch/config/settings.toml"


async def offset_now():
    return Prices(await PriceFile().load_prices()).offset_now


async def price_only_switch_states():
    return set_price_only_based_states(
        settings=load_settings_file(SETTINGS_PATH), offset_now=await offset_now()
    )


power_limit = lambda: load_settings_file(SETTINGS_PATH)["Settings"]["MaxPower"]


def create_on_status_dict(switches_df: pd.DataFrame) -> dict[Hashable | None, int]:
    on_status_dict = {}
    for appliance, row in switches_df.iterrows():
        on_status_dict[appliance] = 1 if row["on"] else 0
    return on_status_dict


@app.on_event("startup")
async def startup_event():
    global tibber_instance
    try:
        tibber_instance = TibberConnection()
        global task
        task = asyncio.create_task(tibber_instance.subscribe_to_realtime_data())
    except Exception as e:
        logger.error(f"Failed to start Tibber real-time subscription: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    await tibber_instance.close()  # Gracefully close the Tibber connection


@app.get("/")
async def switch_states():
    switch_states_async = await price_only_switch_states()
    power_and_price_switch_states = limit_power(
        switch_states=switch_states_async,
        power_limit=power_limit(),
        power_now=tibber_instance.power_reading,
    )
    return create_on_status_dict(power_and_price_switch_states)


@app.get("/subscription_info")
async def subscription_info():
    return {
        "power_reading": tibber_instance.power_reading,
        "subscription_status": tibber_instance.subscription_status,
    }


if __name__ == "__main__":
    uvicorn.run("__main__:app", port=8080)
