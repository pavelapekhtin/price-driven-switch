from datetime import datetime, timedelta
from typing import Dict


def calculate_easter_sunday(year: int) -> datetime:
    """
    Calculate Easter Sunday for a given year using Meeus/Jones/Butcher algorithm.

    Args:
        year: The year to calculate Easter for

    Returns:
        datetime object representing Easter Sunday
    """
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    ell = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * ell) // 451
    month = (h + ell - 7 * m + 114) // 31
    day = ((h + ell - 7 * m + 114) % 31) + 1

    return datetime(year, month, day)


def get_easter_holidays(year: int) -> list[datetime]:
    """
    Get all Easter-related holidays for a given year.

    Args:
        year: The year to calculate holidays for

    Returns:
        List of datetime objects for Easter holidays
    """
    easter_sunday = calculate_easter_sunday(year)

    # Maundy Thursday (3 days before Easter Sunday)
    maundy_thursday = easter_sunday - timedelta(days=3)

    # Good Friday (2 days before Easter Sunday)
    good_friday = easter_sunday - timedelta(days=2)

    # Easter Monday (1 day after Easter Sunday)
    easter_monday = easter_sunday + timedelta(days=1)

    # Ascension Day (39 days after Easter Sunday)
    ascension_day = easter_sunday + timedelta(days=39)

    # Pentecost Sunday (49 days after Easter Sunday)
    pentecost_sunday = easter_sunday + timedelta(days=49)

    # Pentecost Monday (50 days after Easter Sunday)
    pentecost_monday = easter_sunday + timedelta(days=50)

    return [
        maundy_thursday,
        good_friday,
        easter_sunday,
        easter_monday,
        ascension_day,
        pentecost_sunday,
        pentecost_monday,
    ]


def is_weekend_or_holiday(date: datetime) -> bool:
    """Check if the given date is a weekend or holiday."""
    # Weekend check (Saturday = 5, Sunday = 6)
    if date.weekday() >= 5:
        return True

    # Fixed Norwegian holidays
    fixed_holidays = [
        (1, 1),  # New Year's Day (Nyttårsdag)
        (5, 1),  # Labor Day (Arbeidernes dag)
        (5, 17),  # Constitution Day (Grunnlovsdagen)
        (12, 25),  # Christmas Day (Juledag)
        (12, 26),  # Boxing Day (Andre juledag)
    ]

    # Check fixed holidays
    if (date.month, date.day) in fixed_holidays:
        return True

    # Check Easter-related holidays (movable feasts)
    easter_holidays = get_easter_holidays(date.year)
    return any(date.date() == holiday.date() for holiday in easter_holidays)


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
    season = "JanMar" if date.month in [1, 2, 3] else "AprDec"

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
