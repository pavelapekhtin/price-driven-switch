import datetime as dt
import json
import os
from pathlib import Path

from price_driven_switch.core.config import CONFIG_DIR
from price_driven_switch.services.tibber_connection import TibberConnection


class PriceFile:
    def __init__(
        self,
        tibber_connection: TibberConnection = TibberConnection(),  # noqa: B008
        path: str | Path = CONFIG_DIR / "prices.json",
    ) -> None:
        self.tibber_connection = tibber_connection
        self.path = path

    async def load_prices(self) -> dict:
        await self._check_file()
        _, api_dict = self._load_price_file()
        return api_dict

    async def _check_file(self) -> None:
        if not os.path.exists(self.path):
            await self._update_price_file()
        else:
            file_date, _ = self._load_price_file()
            if self._check_out_of_date(file_date):
                self._write_prices_file(await self._load_prices_from_server())

    def _check_out_of_date(self, date: str) -> bool:
        file_date = dt.datetime.strptime(date, "%Y-%m-%d %H:%M")
        time_now = dt.datetime.now()

        # Create datetime objects for today's midnight and 1:20 PM based on time_now
        today_midnight = dt.datetime(time_now.year, time_now.month, time_now.day, 0, 0)
        today_1_20_pm = dt.datetime(time_now.year, time_now.month, time_now.day, 13, 20)

        # Check if file_date is before today's midnight
        if file_date < today_midnight:
            return True

        # Check if file_date is before today's 1:20 PM and time_now is past 1:20 PM
        return bool(file_date < today_1_20_pm and time_now >= today_1_20_pm)

    def _load_price_file(self) -> tuple[str, dict]:
        with open(self.path, mode="r", encoding="utf-8") as json_file:
            json_data = json.load(json_file)
            api_response = json_data.get("api_response")
            file_date = json_data.get("timestamp")
            return file_date, api_response

    async def _update_price_file(self) -> None:
        self._write_prices_file(await self._load_prices_from_server())

    async def _load_prices_from_server(self) -> dict:
        api_response = await self.tibber_connection.get_prices()
        file_data = {
            "timestamp": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "api_response": api_response,
        }
        return file_data

    def _write_prices_file(self, api_response: dict) -> None:
        with open(self.path, mode="w", encoding="utf-8") as json_file:
            json.dump(api_response, json_file)
