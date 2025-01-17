from fastapi import APIRouter, HTTPException, Request

from price_driven_switch.core.config import PATH_SETTINGS, load_settings_file
from price_driven_switch.services.price_file import PriceFile
from price_driven_switch.services.prices import Prices

router = APIRouter()


@router.get("/prices")
async def get_prices(request: Request):
    try:
        prices = Prices(await PriceFile().load_prices())
        settings = load_settings_file(PATH_SETTINGS)

        offset_prices_today = {}
        offset_prices_tomorrow = {}

        for name, appliance in settings.get("Appliances", {}).items():
            offset = appliance.get("Setpoint", 0.0)
            offset_prices_today[name] = prices.get_price_at_offset_today(offset)
            offset_prices_tomorrow[name] = prices.get_price_at_offset_tomorrow(offset)

        return {
            "today": prices.today_prices,
            "tomorrow": prices.tomo_prices,
            "offset_prices_today": offset_prices_today,
            "offset_prices_tomorrow": offset_prices_tomorrow,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
