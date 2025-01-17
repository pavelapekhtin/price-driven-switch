from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from price_driven_switch.core.config import (
    PATH_SETTINGS,
    load_settings_file,
    load_tibber_token,
    read_power_limit,
    save_api_key,
)
from price_driven_switch.core.logging import logger
from price_driven_switch.services.tibber_connection import TibberConnection

router = APIRouter()


class ApiKeyUpdate(BaseModel):
    api_key: str


@router.get("/api/settings")
async def get_settings():
    try:
        return load_settings_file(PATH_SETTINGS)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/api/settings/api-key")
async def get_api_key():
    try:
        logger.info(f"GET /settings/api-key: {load_tibber_token()}")
        return {"api_key": load_tibber_token()}
    except Exception as e:
        logger.error(f"Error getting API key: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/api/settings/api-key")
async def set_api_key(data: ApiKeyUpdate):
    try:
        save_api_key(data.api_key)
        logger.info(f"POST /settings/api-key: {data.api_key}")
        return {"message": "API key updated successfully"}
    except Exception as e:
        logger.error(f"Error setting API key: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/api/settings/api-key-status")
async def check_api_key_status():
    try:
        tibber = TibberConnection(api_token=load_tibber_token())
        is_valid = await tibber.check_token_validity()

        if is_valid:
            logger.info(f"GET /settings/api-key-status: {is_valid}")
            return {"status": "ok", "message": "API key is valid"}
        else:
            logger.error(f"GET /settings/api-key-status: {is_valid}")
            return {
                "status": "unauthorized",
                "message": "API key is invalid or unauthorized",
            }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error checking API key status: {str(e)}"
        ) from e


@router.get("/api/settings/appliances")
async def get_appliances(): ...


@router.post("/api/settings/appliances")
async def set_appliances(appliances: dict): ...


@router.get("/api/settings/power-limit")
async def get_power_limit():
    try:
        power_limit = read_power_limit()
        logger.debug(f"GET /settings/power-limit:  {power_limit}")
        return power_limit
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/api/settings/power-limit")
async def set_power_limit(power_limit: float): ...


@router.get("/api/settings/setpoints")
async def get_setpoints(): ...


@router.post("/api/settings/setpoints")
async def set_setpoints(setpoints: dict): ...
