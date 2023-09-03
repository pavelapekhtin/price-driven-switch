from datetime import datetime


class Prices:
    def __init__(self, price_dict: dict) -> None:
        self.price_dict = price_dict

    @property
    def offset_now(self) -> float:
        min_price = min(self.today_prices)
        max_price = max(self.today_prices)

        # To prevent division by zero in case all prices are the same
        if max_price == min_price:
            return 0.5  # This assumes that if all prices are the same, the offset is in the middle. You can change this behavior if needed.

        ratio = (self.price_now - min_price) / (max_price - min_price)
        # TODO: change the ratio to offset from mean price

        return ratio

    def get_price_at_offset_today(self, offset: float) -> float:
        return self.get_price_of_the_offset(self.today_prices, offset)

    def get_price_at_offset_tomorrow(self, offset: float) -> float:
        return self.get_price_of_the_offset(self.tomo_prices, offset)

    def get_price_of_the_offset(self, prices: list[float], offset: float) -> float:
        """Takes an offset value between 0 and 1, and returns the corresponding price from today_prices."""
        if prices == []:
            return 0

        if offset < 0 or offset > 1:
            raise ValueError("Offset must be between 0 and 1.")

        min_price = min(prices)
        max_price = max(prices)

        # To prevent division by zero in case all prices are the same
        if max_price == min_price:
            return min_price  # This assumes that if all prices are the same, any offset corresponds to this single price. You can change this behavior if needed.

        # TODO: change the ratio to offset from mean price
        price_from_offset = min_price + (max_price - min_price) * offset
        return price_from_offset

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
