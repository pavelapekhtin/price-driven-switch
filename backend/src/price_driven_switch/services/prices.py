from datetime import datetime


class Prices:
    def __init__(self, price_dict: dict) -> None:
        self.price_dict = price_dict

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
        return self._load_prices("today")

    @property
    def tomo_prices(self) -> list[float]:
        return self._load_prices("tomorrow")

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
