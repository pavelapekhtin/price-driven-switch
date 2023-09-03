import uvicorn
from fastapi import FastAPI
from price_driven_switch.backend.configuration import load_setpoints
from price_driven_switch.backend.price_file import PriceFile
from price_driven_switch.backend.prices import Prices

app = FastAPI()

get_price_dict = lambda: Prices(PriceFile().load_prices()).price_dict


def get_current_price_ratio(price_dict: dict) -> float:
    prices = Prices(price_dict)
    return prices.offset_now


def check_on_off(setpoint: float, curr_price_ratio: float) -> bool:
    return setpoint >= curr_price_ratio


def get_switch_states(price_dict: dict) -> dict[str, int]:
    price_ratio: float = get_current_price_ratio(price_dict)
    setpoints: dict[str, float] = load_setpoints()

    switch_states_dict: dict = {}
    for key, _ in setpoints.items():
        state = 1 if check_on_off(setpoints[key], price_ratio) is True else 0
        switch_states_dict[key] = state
    return switch_states_dict


@app.get("/")
def switch_states():
    return get_switch_states(get_price_dict())


if __name__ == "__main__":
    uvicorn.run("__main__:app", port=8080)
