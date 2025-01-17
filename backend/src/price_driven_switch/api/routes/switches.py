from fastapi import APIRouter, Request

from price_driven_switch.core.config import read_power_limit
from price_driven_switch.core.logging import logger
from price_driven_switch.services.price_file import PriceFile
from price_driven_switch.services.prices import Prices
from price_driven_switch.services.switch_logic import (
    create_on_status_dict,
    limit_power,
    price_only_switch_states,
)

router = APIRouter()


@router.get("/api/previous_setpoints")
async def previous_setpoints():
    return create_on_status_dict(await price_only_switch_states())


@router.get("/api/offset_now")
async def offset_now():
    return Prices(await PriceFile().load_prices()).offset_now


@router.get("/api")
async def switch_states(request: Request):
    switch_states_async = await price_only_switch_states()
    logger.debug(f"Price only switch dates: {switch_states_async}")
    tibber = request.app.state.tibber_instance
    power_and_price_switch_states = limit_power(
        switch_states=switch_states_async,
        power_limit=read_power_limit(),
        prev_states=request.app.state.previous_switch_states,
        power_now=tibber.power_reading,
    )
    request.app.state.previous_switch_states = power_and_price_switch_states
    logger.debug(f"Previous switch states: {request.app.state.previous_switch_states}")
    return create_on_status_dict(power_and_price_switch_states)
