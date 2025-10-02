from datetime import datetime

from price_driven_switch.backend.configuration import load_settings_file
from price_driven_switch.backend.grid_rent import add_grid_rent_to_prices


class Prices:
    def __init__(self, price_dict: dict) -> None:
        self.price_dict = price_dict
        self.settings = load_settings_file()

    @property
    def offset_now(self) -> float:
        sorted_prices = sorted(self.today_prices)

        # Find the position of the current price within the sorted list
        position = sorted_prices.index(self.price_now)

        # Determine the offset based on the position
        offset = position / 23

        return offset

    def get_price_at_offset_today(self, offset: float) -> float:
        return self.get_price_of_the_offset(self.today_prices, offset)

    def get_price_at_offset_tomorrow(self, offset: float) -> float:
        return self.get_price_of_the_offset(self.tomo_prices, offset)

    def get_price_of_the_offset(self, prices: list[float], offset: float) -> float:
        """Takes an offset value between 0 and 1, and returns the corresponding price."""
        if not prices:
            return 0

        if offset < 0 or offset > 1:
            raise ValueError("Offset must be between 0 and 1.")

        sorted_prices = sorted(prices)

        # Calculate the index corresponding to the given offset
        index = int(round(offset * 23))

        return sorted_prices[index]

    @property
    def price_now(self) -> float:
        hour_now = self._hour_now()
        today_prices = self.today_prices
        price_now = today_prices[hour_now]
        return price_now

    @property
    def today_prices(self) -> list[float]:
        settings = self.settings.get("Settings", {})

        # If Norgespris is enabled, use fixed prices
        if settings.get("UseNorgespris", False):
            norgespris_rate = settings.get("NorgesprisRate", 50.0)
            # Convert from øre to NOK to match Tibber API format
            base_prices = [norgespris_rate / 100.0] * 24
        else:
            base_prices = self._load_prices("today")

        # Add grid rent if enabled
        if settings.get("IncludeGridRent", True):
            grid_rent_config = settings.get("GridRent", {})
            today_date = datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            return add_grid_rent_to_prices(base_prices, today_date, grid_rent_config)
        return base_prices

    @property
    def tomo_prices(self) -> list[float]:
        settings = self.settings.get("Settings", {})

        # If Norgespris is enabled, use fixed prices
        if settings.get("UseNorgespris", False):
            norgespris_rate = settings.get("NorgesprisRate", 50.0)
            # Convert from øre to NOK to match Tibber API format
            base_prices = [norgespris_rate / 100.0] * 24
        else:
            base_prices = self._load_prices("tomorrow")

        # Add grid rent if enabled
        if settings.get("IncludeGridRent", True):
            grid_rent_config = settings.get("GridRent", {})
            tomorrow_date = datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            # Add one day to get tomorrow
            from datetime import timedelta

            tomorrow_date += timedelta(days=1)
            return add_grid_rent_to_prices(base_prices, tomorrow_date, grid_rent_config)
        return base_prices

    def _load_prices(self, today_tomo: str) -> list[float]:
        api_dict = self.price_dict
        today_energy = (
            api_dict.get("data", {})
            .get("viewer", {})
            .get("homes", [{}])[0]
            .get("currentSubscription", {})
            .get("priceInfo", {})
            .get(today_tomo, [])
        )
        energy_values = [item.get("total") for item in today_energy]
        return energy_values

    def _hour_now(self) -> int:
        return datetime.now().hour
