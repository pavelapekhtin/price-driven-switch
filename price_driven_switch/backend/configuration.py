import logging
import os
import threading
from shutil import move
from tempfile import NamedTemporaryFile
from typing import Any, Dict

import toml
from dotenv import load_dotenv, set_key
from loguru import logger
from pydantic import BaseModel, Field, model_validator

load_dotenv("price_driven_switch/config/.env", verbose=True)

PATH_SETTINGS = "price_driven_switch/config/settings.toml"

default_settings_toml = {
    "Appliances": {
        "Boiler 1": {"Power": 1.5, "Priority": 2, "Setpoint": 0.5},
        "Boiler 2": {"Power": 1.0, "Priority": 1, "Setpoint": 0.5},
        "Bathroom Floor": {"Power": 0.8, "Priority": 3, "Setpoint": 0.5},
    },
    "Settings": {"MaxPower": 0.0, "Timezone": "Europe/Oslo"},
}


class PropagateHandler(logging.Handler):
    def emit(self, record):
        logging.getLogger(record.name).handle(record)


logger.add(PropagateHandler(), format="{message} {extra}")


def create_default_settings_if_none(
    path: str = PATH_SETTINGS,
) -> None:
    if not os.path.exists(path):
        data = default_settings_toml
        with open(path, "w", encoding="utf-8") as file:
            toml.dump(data, file)
            logger.debug(f"Default settings file created at {path}")
    else:
        logger.debug(f"Settings file found at {path}")


class Appliance(BaseModel):
    Power: float
    Priority: int = Field(..., ge=1)
    Setpoint: float = Field(..., ge=0, le=1)  # Setpoint must be between 0 and 1


class Settings(BaseModel):
    MaxPower: float = Field(..., ge=0)
    Timezone: str


class TomlStructure(BaseModel):
    Appliances: Dict[str, Appliance]
    Settings: Settings

    @model_validator(mode="before")
    @classmethod
    def check_timezone_key_exists(cls, values):
        settings = values.get("Settings")
        if settings is None:
            raise ValueError("Missing 'Settings' section in TOML file")

        timezone = settings["Timezone"]
        if timezone is None or timezone == "":
            raise ValueError("Missing or empty 'Timezone' key in 'Settings'")

        return values


def validate_settings(data: dict) -> None:
    try:
        TomlStructure(**data)
    except ValueError as error:
        raise ValueError("Invalid settings.toml file") from error


# for streamlit consistent file updates
debounce_time = 0.5  # seconds
debounce_timer = None
file_lock = threading.Lock()


def load_settings_file(path: str = PATH_SETTINGS) -> dict:
    with file_lock, open(path, mode="r", encoding="utf-8") as toml_file:
        settings = toml.load(toml_file)
        validate_settings(settings)
        return settings


def load_global_settings() -> dict:
    return load_settings_file().get("Settings", {})


def update_max_power(data_dict: Dict[str, Any], new_max_power: float) -> Dict[str, Any]:
    if "Settings" in data_dict:
        data_dict["Settings"]["MaxPower"] = new_max_power
    return data_dict


def save_settings(new_settings: dict, path: str = PATH_SETTINGS) -> None:
    validate_settings(new_settings)
    logger.debug(f"Got settings dict: \n {new_settings}")

    def write():
        logger.debug(f"Saving settings to {path}")
        with file_lock:
            with NamedTemporaryFile("w", delete=False) as tmp:
                toml.dump(new_settings, tmp)
            move(tmp.name, path)

    global debounce_timer
    if debounce_timer:
        debounce_timer.cancel()
    debounce_timer = threading.Timer(debounce_time, write)
    logger.debug(f"Waiting {debounce_time} seconds before saving settings")
    debounce_timer.start()


def save_api_key(api_key: str) -> None:
    set_key("price_driven_switch/config/.env", "TIBBER_TOKEN", api_key)
    os.environ["TIBBER_TOKEN"] = api_key


def get_package_version_from_toml() -> str:
    with open("pyproject.toml", "r", encoding="utf-8") as file:
        data = toml.load(file)
        return data["tool"]["poetry"]["version"]


create_default_settings_if_none()
