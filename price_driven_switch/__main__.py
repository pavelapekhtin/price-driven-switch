import asyncio
from typing import Dict

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
    "logs/price_driven_switch.log", rotation="1 week", retention="7 days", level="DEBUG"
)

app = FastAPI()

settings = lambda: load_settings_file("price_driven_switch/config/settings.toml")

offset_now = lambda: Prices(PriceFile().load_prices()).offset_now

price_only_switch_states = lambda: set_price_only_based_states(
    settings=settings(), offset_now=offset_now()
)

power_limit = lambda: settings()["Settings"]["MaxPower"]


def create_on_status_dict(switches_df: pd.DataFrame) -> Dict[str, int]:
    on_status_dict = {}
    for appliance, row in switches_df.iterrows():
        on_status_dict[appliance] = 1 if row["on"] else 0
    return on_status_dict


# tibber_instance = None


@app.on_event("startup")
async def startup_event():
    global tibber_instance
    tibber_instance = TibberConnection()
    asyncio.create_task(tibber_instance.current_power_subscription())


@app.get("/")
async def switch_states():
    power_and_price_switch_states = limit_power(
        switch_states=price_only_switch_states(),
        power_limit=power_limit(),
        power_now=tibber_instance.power_reading,
    )
    logger.debug(f"Power now {tibber_instance.power_reading}")
    return create_on_status_dict(power_and_price_switch_states)


if __name__ == "__main__":
    uvicorn.run("__main__:app", port=8080)
