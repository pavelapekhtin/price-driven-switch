import logging
import os
from shutil import move
from tempfile import NamedTemporaryFile

import toml
from dotenv import load_dotenv, set_key

load_dotenv()

PATH_SETPOINTS = "price_driven_switch/config/setpoints.toml"

# TODO:  allow setting currency and calculation method (% of range or based on mean)
# TODO:  allow setting this in the frontend


def check_setpoints_toml(
    path: str = PATH_SETPOINTS,
) -> None:
    if not os.path.exists(path):
        data = {"Appliance1": 1, "Appliance2": 1}
        with open(path, "w", encoding="utf-8") as file:
            toml.dump(data, file)
            logging.debug("Default setpoints file created at %s", path)
    else:
        logging.debug("Setpoints file found at %s", path)


def check_setpoints_in_range(setpoints: dict[str, float]) -> None:
    for key, value in setpoints.items():
        if value < 0 or value > 1:
            raise ValueError(f"Setpoint {key} is out of range (0-1)")


def load_setpoints(path: str = PATH_SETPOINTS) -> dict[str, float]:
    with open(path, mode="r", encoding="utf-8") as toml_file:
        setpoints = toml.load(toml_file)
        check_setpoints_in_range(setpoints)
        return setpoints


def save_setpoints(new_setpoints: dict[str, float], path: str = PATH_SETPOINTS) -> None:
    with NamedTemporaryFile("w", delete=False) as tmp:
        toml.dump(new_setpoints, tmp)
    move(tmp.name, path)


def save_api_key(api_key: str) -> None:
    set_key(".env", "TIBBER_TOKEN", api_key)
    os.environ["TIBBER_TOKEN"] = api_key
