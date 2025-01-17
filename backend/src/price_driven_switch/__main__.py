import asyncio
from contextlib import asynccontextmanager

import pandas as pd
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from price_driven_switch.api.routes import prices, settings, subscription, switches
from price_driven_switch.core.logging import setup_logging
from price_driven_switch.services.tibber_connection import TibberRealtimeConnection


@asynccontextmanager
async def lifespan(app: FastAPI):
    """_summary_

    This function is used to create a context manager for the FastAPI app.
    It is used to create a TibberRealtimeConnection instance and store it in the app.state.

    Args:
        app (FastAPI)
    """
    try:
        tibber_instance = TibberRealtimeConnection()
        app.state.tibber_instance = tibber_instance
        app.state.previous_switch_states = pd.DataFrame(
            {
                "Appliance": [],
                "Power": [],
                "Priority": [],
                "on": [],
            }
        )
        task = asyncio.create_task(tibber_instance.subscribe_to_realtime_data())
        yield
    finally:
        await app.state.tibber_instance.close()


app = FastAPI(lifespan=lifespan)
app.include_router(subscription.router)
app.include_router(prices.router)
app.include_router(settings.router)
app.include_router(switches.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Svelte dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# class PowerLimitUpdate(BaseModel):
#     power_limit: float


# class AppliancesUpdate(BaseModel):
#     appliances: dict


# @app.post("/api/update-power-limit")
# async def update_power_limit(data: PowerLimitUpdate):
#     try:
#         settings = load_settings_file(SETTINGS_PATH)
#         settings["Settings"]["MaxPower"] = data.power_limit
#         save_settings(settings)
#         return {"success": True}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @app.get("/api/appliances")
# async def get_appliances():
#     settings = load_settings_file(SETTINGS_PATH)
#     return settings.get("Appliances", {})


# @app.post("/api/update-appliances")
# async def update_appliances(data: AppliancesUpdate):
#     try:
#         settings = load_settings_file(SETTINGS_PATH)
#         settings["Appliances"] = data.appliances
#         save_settings(settings)
#         return {"success": True}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @app.get("/api/logs")
# async def get_logs(lines: int = 12, level: str = "INFO"):
#     try:
#         content = read_filtered_logs("logs/fast_api.log", lines, level)
#         return {"content": content}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @app.get("/api/setpoint-status")
# async def get_setpoint_status():
#     try:
#         return {"current": get_setpoints_json(), "priceOnly": get_prev_setpoints_json()}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @app.get("/api/version")
# async def get_version():
#     try:
#         return get_package_version_from_toml()
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    setup_logging()
    uvicorn.run("__main__:app", port=8080, log_level="error", access_log=False)
