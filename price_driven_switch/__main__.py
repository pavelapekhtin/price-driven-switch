import asyncio
import os
import sys
from collections.abc import AsyncGenerator, Hashable
from contextlib import asynccontextmanager

import pandas as pd
import uvicorn
from fastapi import FastAPI, HTTPException, Path
from loguru import logger

from price_driven_switch.backend.configuration import load_settings_file
from price_driven_switch.backend.price_file import PriceFile
from price_driven_switch.backend.prices import Prices
from price_driven_switch.backend.switch_logic import (
    limit_power,
    set_price_only_based_states,
)
from price_driven_switch.backend.tibber_connection import TibberRealtimeConnection

# Configure logger based on environment
logger.remove()  # Remove default handler
if os.environ.get("RUNNING_IN_DOCKER"):
    # In Docker, log to stdout with immediate flushing
    logger.add(
        sys.stdout,
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        enqueue=False,
    )
else:
    # Outside Docker, log to file
    logger.add(
        "logs/fast_api.log",
        rotation="1 week",
        retention="7 days",
        level="DEBUG",
        enqueue=False,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    )
logger.add(
    "logs/fast_api.log",
    rotation="1 week",
    retention="7 days",
    level="DEBUG",
    enqueue=False,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup
    global tibber_instance
    logger.info("Starting Tibber realtime connection initialization...")
    tibber_instance = TibberRealtimeConnection()
    global task
    task = asyncio.create_task(tibber_instance.subscribe_to_realtime_data())
    logger.info("Tibber realtime subscription task created successfully")

    yield

    # Shutdown
    await tibber_instance.close()  # Gracefully close the Tibber connection


app = FastAPI(lifespan=lifespan)

SETTINGS_PATH = "price_driven_switch/config/settings.toml"

# Global variables for application state
tibber_instance: TibberRealtimeConnection | None = None
task: asyncio.Task | None = None

# TODO: ensure its empty at startup and add logic int the power_limit to use power based then
previous_switch_states: pd.DataFrame = pd.DataFrame(
    {
        "Appliance": [],
        "Power": [],
        "Priority": [],
        "on": [],
    }
)


async def offset_now() -> float:
    return Prices(await PriceFile().load_prices()).offset_now


async def price_only_switch_states() -> pd.DataFrame:
    return set_price_only_based_states(
        settings=load_settings_file(SETTINGS_PATH), offset_now=await offset_now()
    )


def power_limit() -> float:
    return load_settings_file(SETTINGS_PATH)["Settings"]["MaxPower"]


def create_on_status_dict(switches_df: pd.DataFrame) -> dict[Hashable | None, int]:
    on_status_dict = {}
    for appliance, row in switches_df.iterrows():
        on_status_dict[appliance] = 1 if bool(row["on"]) else 0
    return on_status_dict


def get_appliance_names() -> list[str]:
    """Get list of all appliance names from settings."""
    settings = load_settings_file(SETTINGS_PATH)
    return list(settings["Appliances"].keys())


def appliance_name_to_url_safe(name: str) -> str:
    """Convert appliance name to URL-safe format by replacing spaces with underscores."""
    return name.replace(" ", "_")


def url_safe_to_appliance_name(url_name: str) -> str:
    """Convert URL-safe name back to appliance name by replacing underscores with spaces."""
    return url_name.replace("_", " ")


def get_individual_appliance_state(appliance_name: str, switches_df: pd.DataFrame) -> int:
    """Get on/off state for a specific appliance."""
    if appliance_name not in switches_df.index:
        raise HTTPException(status_code=404, detail=f"Appliance '{appliance_name}' not found")

    row = switches_df.loc[appliance_name]
    return 1 if bool(row["on"]) else 0



@app.get("/")
async def root() -> dict[str, str | dict[str, str]]:
    """Root endpoint providing API information."""
    return {
        "message": "Price-Driven Switch API",
        "endpoints": {
            "all_states": "/api/",
            "appliances": "/appliances",
            "individual": "/appliance/{name}",
            "subscription": "/subscription_info"
        }
    }


@app.get("/api/")
async def switch_states() -> dict[Hashable | None, int]:
    switch_states_async = await price_only_switch_states()
    global previous_switch_states
    power_reading = tibber_instance.power_reading if tibber_instance else 0
    power_and_price_switch_states = limit_power(
        switch_states=switch_states_async,
        power_limit=power_limit(),
        prev_states=previous_switch_states,
        power_now=power_reading,
    )
    previous_switch_states = power_and_price_switch_states
    return create_on_status_dict(power_and_price_switch_states)


@app.get("/subscription_info")
async def subscription_info() -> dict[str, int | str]:
    if tibber_instance:
        return {
            "power_reading": tibber_instance.power_reading,
            "subscription_status": tibber_instance.subscription_status,
        }
    return {
        "power_reading": 0,
        "subscription_status": "Not connected",
    }


@app.get("/previous_setpoints")
async def previous_setpoints() -> dict[Hashable | None, int]:
    return create_on_status_dict(await price_only_switch_states())


@app.get("/appliances")
async def list_appliances() -> dict[str, list[str]]:
    """List all available appliances with URL-safe names."""
    appliance_names = get_appliance_names()
    url_safe_names = [appliance_name_to_url_safe(name) for name in appliance_names]
    return {"appliances": url_safe_names}


@app.get("/appliance/{appliance_name}")
async def get_appliance_state(appliance_name: str = Path(..., description="URL-safe name of the appliance")) -> int:
    """Get on/off state for a specific appliance by URL-safe name."""
    # Convert URL-safe name back to actual appliance name
    actual_appliance_name = url_safe_to_appliance_name(appliance_name)

    switch_states_async = await price_only_switch_states()
    global previous_switch_states
    power_reading = tibber_instance.power_reading if tibber_instance else 0
    power_and_price_switch_states = limit_power(
        switch_states=switch_states_async,
        power_limit=power_limit(),
        prev_states=previous_switch_states,
        power_now=power_reading,
    )
    previous_switch_states = power_and_price_switch_states

    return get_individual_appliance_state(actual_appliance_name, power_and_price_switch_states)


@app.get("/appliance/{appliance_name}/previous")
async def get_appliance_previous_state(appliance_name: str = Path(..., description="URL-safe name of the appliance")) -> int:
    """Get previous price-only on/off state for a specific appliance by URL-safe name."""
    # Convert URL-safe name back to actual appliance name
    actual_appliance_name = url_safe_to_appliance_name(appliance_name)

    price_only_states = await price_only_switch_states()
    return get_individual_appliance_state(actual_appliance_name, price_only_states)



if __name__ == "__main__":
    uvicorn.run("__main__:app", port=8080)
