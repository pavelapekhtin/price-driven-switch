import logging
import os
from shutil import move
from tempfile import NamedTemporaryFile
from typing import Dict

import toml
from dotenv import load_dotenv, set_key
from pydantic import BaseModel, Field, model_validator

load_dotenv("price_driven_switch/config/.env", verbose=True)

PATH_SETTINGS = "price_driven_switch/config/settings.toml"

default_settings_toml = {
    "Appliances": {
        "Boilers": {"Power": 1.5, "Priority": 2, "Setpoint": 0.5},
        "Floor": {"Power": 1.0, "Priority": 1, "Setpoint": 0.5},
        "Other": {"Power": 0.8, "Priority": 3, "Setpoint": 0.5},
    },
    "Settings": {"MaxPower": 5.0, "Timezone": "Europe/Oslo"},
}


def create_default_settings_if_none(
    path: str = PATH_SETTINGS,
) -> None:
    if not os.path.exists(path):
        data = default_settings_toml
        with open(path, "w", encoding="utf-8") as file:
            toml.dump(data, file)
            logging.debug("Default settings file created at %s", path)
    else:
        logging.debug("Settings file found at %s", path)


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


def load_settings_file(path: str = PATH_SETTINGS) -> dict:
    with open(path, mode="r", encoding="utf-8") as toml_file:
        settings = toml.load(toml_file)
        validate_settings(settings)
        return settings


def load_global_settings() -> dict:
    return load_settings_file().get("Settings", {})


def save_settings(
    new_settings: dict, path: str = "price_driven_switch/config/settings.toml"
) -> None:
    validate_settings(new_settings)
    with NamedTemporaryFile("w", delete=False) as tmp:
        toml.dump(new_settings, tmp)
    move(tmp.name, path)


def save_api_key(api_key: str) -> None:
    set_key("price_driven_switch/config/.env", "TIBBER_TOKEN", api_key)
    os.environ["TIBBER_TOKEN"] = api_key
