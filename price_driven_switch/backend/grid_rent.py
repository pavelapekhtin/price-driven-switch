from datetime import datetime, time
from typing import Dict


def is_weekend_or_holiday(date: datetime) -> bool:
    """Check if the given date is a weekend or holiday."""
    # Weekend check (Saturday = 5, Sunday = 6)
    if date.weekday() >= 5:
        return True

    # Norwegian holidays (simplified - you might want to add more)
    holidays = [
        (1, 1),  # New Year's Day
        (5, 1),  # Labor Day
        (5, 17),  # Constitution Day
        (12, 25),  # Christmas Day
        (12, 26),  # Boxing Day
    ]

    return (date.month, date.day) in holidays


def is_night_time(hour: int) -> bool:
    """Check if the given hour is during night time (22:00-06:00)."""
    return hour >= 22 or hour < 6


def get_grid_rent_rate(date: datetime, grid_rent_config: Dict) -> float:
    """
    Get the grid rent rate for a specific date and time.

    Args:
        date: The datetime to check
        grid_rent_config: Configuration from settings (rates in øre/kWh)

    Returns:
        Grid rent rate in øre/kWh
    """
    # Determine season
    if date.month in [1, 2, 3]:  # January - March
        season = "JanMar"
    else:  # April - December
        season = "AprDec"

    # Determine if it's night/weekend or day
    if is_weekend_or_holiday(date) or is_night_time(date.hour):
        rate_type = "Night"
    else:
        rate_type = "Day"

    return grid_rent_config[season][rate_type]


def add_grid_rent_to_prices(
    prices: list[float], date: datetime, grid_rent_config: Dict
) -> list[float]:
    """
    Add grid rent to a list of hourly prices.

    Args:
        prices: List of hourly prices in NOK/kWh (kroner)
        date: The date for the price list (assumes 24 hours starting from this date)
        grid_rent_config: Grid rent configuration from settings (in øre/kWh)

    Returns:
        List of prices with grid rent added (in NOK/kWh)
    """
    if not prices:
        return prices

    result = []
    for hour in range(24):
        # Create datetime for this hour
        hour_datetime = date.replace(hour=hour, minute=0, second=0, microsecond=0)
        grid_rent_rate_ore = get_grid_rent_rate(hour_datetime, grid_rent_config)

        # Convert øre to kroner (divide by 100)
        grid_rent_rate_kroner = grid_rent_rate_ore / 100

        # Add grid rent to the price
        price_with_grid_rent = prices[hour] + grid_rent_rate_kroner
        result.append(price_with_grid_rent)

    return result
