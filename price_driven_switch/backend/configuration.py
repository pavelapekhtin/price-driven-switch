# mypy: disable-error-code="index"
import logging
import os
import threading
from copy import deepcopy
from shutil import move
from tempfile import NamedTemporaryFile
from typing import Any

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
    "Settings": {
        "MaxPower": 0.0,
        "Timezone": "Europe/Oslo",
        "IncludeGridRent": True,
        "GridRent": {
            "JanMar": {"Day": 50.94, "Night": 38.21},
            "AprDec": {"Day": 59.86, "Night": 47.13},
        },
    },
}

# Default grid rent settings to add if missing
default_grid_rent_settings = {
    "IncludeGridRent": True,
    "GridRent": {
        "JanMar": {"Day": 50.94, "Night": 38.21},
        "AprDec": {"Day": 59.86, "Night": 47.13},
    },
}


class PropagateHandler(logging.Handler):
    def emit(self, record) -> None:  # noqa: ANN001
        logging.getLogger(record.name).handle(record)


logger.add(PropagateHandler(), format="{message} {extra}")


def ensure_grid_rent_settings(data: dict) -> dict:
    """
    Ensure grid rent settings are present in the settings data.
    If they are missing, add them with default values.

    Args:
        data: The settings data dictionary

    Returns:
        Updated data dictionary with grid rent settings ensured
    """
    # Create a deep copy to avoid modifying the original
    data_copy = deepcopy(data)

    if "Settings" not in data_copy:
        data_copy["Settings"] = {}

    settings = data_copy["Settings"]
    if not isinstance(settings, dict):
        settings = {}
        data_copy["Settings"] = settings

    updated = False

    # Check if IncludeGridRent is missing
    if "IncludeGridRent" not in settings:
        settings["IncludeGridRent"] = default_grid_rent_settings["IncludeGridRent"]
        logger.info("Added missing IncludeGridRent setting with default value")
        updated = True

    # Check if GridRent is missing
    if "GridRent" not in settings:
        settings["GridRent"] = default_grid_rent_settings["GridRent"]
        logger.info("Added missing GridRent settings with default values")
        updated = True
    else:
        # Check if GridRent has the required structure
        grid_rent = settings["GridRent"]
        if not isinstance(grid_rent, dict):
            settings["GridRent"] = default_grid_rent_settings["GridRent"]
            logger.info("Replaced invalid GridRent structure with default values")
            updated = True
        else:
            # Check for required periods
            for period in ["JanMar", "AprDec"]:
                if period not in grid_rent:
                    grid_rent[period] = default_grid_rent_settings["GridRent"][period]
                    logger.info(f"Added missing {period} grid rent settings")
                    updated = True
                else:
                    # Check for required rate types
                    period_rates = grid_rent[period]
                    if not isinstance(period_rates, dict):
                        grid_rent[period] = default_grid_rent_settings["GridRent"][
                            period
                        ]
                        logger.info(
                            f"Replaced invalid {period} structure with default values"
                        )
                        updated = True
                    else:
                        for rate_type in ["Day", "Night"]:
                            if rate_type not in period_rates:
                                period_rates[rate_type] = default_grid_rent_settings[
                                    "GridRent"
                                ][period][rate_type]
                                logger.info(f"Added missing {period} {rate_type} rate")
                                updated = True

    if updated:
        logger.info("Grid rent settings have been updated with missing values")

    return data_copy


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
        # Check and update existing file for missing grid rent settings
        try:
            with open(path, encoding="utf-8") as file:
                data = toml.load(file)

            # Ensure grid rent settings are present
            updated_data = ensure_grid_rent_settings(data)

            # Save back if changes were made
            if updated_data != data:
                with open(path, "w", encoding="utf-8") as file:
                    toml.dump(updated_data, file)
                logger.info(
                    f"Updated settings file at {path} with missing grid rent settings"
                )
        except Exception as e:
            logger.warning(f"Could not check/update grid rent settings in {path}: {e}")


class Appliance(BaseModel):
    Power: float
    Priority: int = Field(..., ge=1)
    Setpoint: float = Field(..., ge=0, le=1)  # Setpoint must be between 0 and 1


class Settings(BaseModel):
    MaxPower: float = Field(..., ge=0)
    Timezone: str
    IncludeGridRent: bool = True
    GridRent: dict[str, dict[str, float]] = Field(
        default={
            "JanMar": {"Day": 50.94, "Night": 38.21},
            "AprDec": {"Day": 59.86, "Night": 47.13},
        }
    )
    UseNorgespris: bool = False
    NorgesprisRate: float = Field(default=50.0, ge=0)


class TomlStructure(BaseModel):
    Appliances: dict[str, Appliance]
    Settings: Settings

    @model_validator(mode="before")
    @classmethod
    def check_timezone_key_exists(cls, values: str) -> Any:
        settings = values.get("Settings")  # type: ignore
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
    with file_lock, open(path, encoding="utf-8") as toml_file:
        settings = toml.load(toml_file)
        # Ensure grid rent settings are present
        settings = ensure_grid_rent_settings(settings)
        validate_settings(settings)
        return settings


def load_global_settings() -> dict:
    return load_settings_file().get("Settings", {})


def update_max_power(data_dict: dict[str, Any], new_max_power: float) -> dict[str, Any]:
    if "Settings" in data_dict:
        data_dict["Settings"]["MaxPower"] = new_max_power
    return data_dict


def save_settings(new_settings: dict, path: str = PATH_SETTINGS) -> None:
    # Ensure grid rent settings are present before saving
    new_settings = ensure_grid_rent_settings(new_settings)
    validate_settings(new_settings)
    logger.debug(f"Got settings dict: \n {new_settings}")

    def write() -> None:
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
    with open("pyproject.toml", encoding="utf-8") as file:
        data = toml.load(file)
        return data["project"]["version"]


create_default_settings_if_none()
