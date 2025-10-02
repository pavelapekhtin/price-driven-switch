from datetime import datetime

from price_driven_switch.backend.configuration import load_settings_file
from price_driven_switch.backend.grid_rent import add_grid_rent_to_prices


class Prices:
    def __init__(self, price_dict: dict) -> None:
        self.price_dict = price_dict
        self.settings = load_settings_file()

    def _interleave_hours(self, hours: list[int]) -> list[int]:
        """Reorder hours to maximize spacing when selected sequentially.

        Uses binary tree traversal to distribute hours evenly.
        Example: [0,1,2,3,4,5,6,7] -> [3,1,5,0,2,4,6,7]
        So selecting first 3 gives [3,1,5] instead of [0,1,2]
        """
        if len(hours) <= 1:
            return hours

        result = []
        queue = [(0, len(hours) - 1)]  # (start, end) pairs

        while queue:
            start, end = queue.pop(0)
            if start > end:
                continue

            # Take the middle element
            mid = (start + end) // 2
            result.append(hours[mid])

            # Add left and right halves to queue
            queue.append((start, mid - 1))
            queue.append((mid + 1, end))

        return result

    @property
    def offset_now(self) -> float:
        hour_now = self._hour_now()
        today_prices = self.today_prices

        # Group hours by price
        from collections import defaultdict

        price_groups: dict[float, list[int]] = defaultdict(list)
        for hour, price in enumerate(today_prices):
            price_groups[price].append(hour)

        # Build sorted list with interleaved hours within each price tier
        sorted_pairs = []
        for price in sorted(price_groups.keys()):
            hours = price_groups[price]
            interleaved = self._interleave_hours(hours)
            for hour in interleaved:
                sorted_pairs.append((hour, price))

        # Find the position of current hour in the sorted list
        position = next(
            i for i, (hour, _) in enumerate(sorted_pairs) if hour == hour_now
        )

        # Determine the offset based on the position
        offset = position / 23

        return offset

    def get_price_at_offset_today(self, offset: float) -> float:
        return self.get_price_of_the_offset(self.today_prices, offset)

    def get_price_at_offset_tomorrow(self, offset: float) -> float:
        return self.get_price_of_the_offset(self.tomo_prices, offset)

    def get_price_of_the_offset(self, prices: list[float], offset: float) -> float:
        """Takes an offset value between 0 and 1, and returns the corresponding price.

        Returns the price that an appliance with this setpoint would see as its threshold.
        With the new offset calculation that distributes hours evenly, this returns
        the price just above the cutoff to show where the ON hours end.
        """
        if not prices:
            return 0

        if offset < 0 or offset > 1:
            raise ValueError("Offset must be between 0 and 1.")

        # Group hours by price and interleave to match offset_now logic
        from collections import defaultdict

        price_groups: dict[float, list[int]] = defaultdict(list)
        for hour, price in enumerate(prices):
            price_groups[price].append(hour)

        # Build sorted list with interleaved hours within each price tier
        sorted_pairs = []
        for price in sorted(price_groups.keys()):
            hours = price_groups[price]
            interleaved = self._interleave_hours(hours)
            for hour in interleaved:
                sorted_pairs.append((hour, price))

        # Calculate the position corresponding to the given offset
        position = int(round(offset * 23))

        # Return the price at this position
        # This represents the threshold: hours with offset < setpoint will be ON
        if position >= len(sorted_pairs):
            position = len(sorted_pairs) - 1

        return sorted_pairs[position][1]

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
