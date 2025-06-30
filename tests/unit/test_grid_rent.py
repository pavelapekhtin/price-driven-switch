from datetime import datetime

import pytest

from price_driven_switch.backend.grid_rent import (
    add_grid_rent_to_prices,
    calculate_easter_sunday,
    get_easter_holidays,
    get_grid_rent_rate,
    is_night_time,
    is_weekend_or_holiday,
)


class TestGridRent:
    @pytest.mark.unit
    def test_is_night_time(self):
        """Test night time detection (22:00-06:00)."""
        # Night hours
        assert is_night_time(22) is True
        assert is_night_time(23) is True
        assert is_night_time(0) is True
        assert is_night_time(5) is True

        # Day hours
        assert is_night_time(6) is False
        assert is_night_time(12) is False
        assert is_night_time(21) is False

    @pytest.mark.unit
    def test_is_weekend_or_holiday(self):
        """Test weekend and holiday detection."""
        # Weekends
        saturday = datetime(2024, 1, 6)  # Saturday
        sunday = datetime(2024, 1, 7)  # Sunday
        assert is_weekend_or_holiday(saturday) is True
        assert is_weekend_or_holiday(sunday) is True

        # Weekdays
        monday = datetime(2024, 1, 8)  # Monday
        friday = datetime(2024, 1, 12)  # Friday
        assert is_weekend_or_holiday(monday) is False
        assert is_weekend_or_holiday(friday) is False

        # Norwegian holidays
        new_year = datetime(2024, 1, 1)  # New Year's Day
        labor_day = datetime(2024, 5, 1)  # Labor Day
        constitution_day = datetime(2024, 5, 17)  # Constitution Day
        christmas = datetime(2024, 12, 25)  # Christmas Day
        boxing_day = datetime(2024, 12, 26)  # Boxing Day

        assert is_weekend_or_holiday(new_year) is True
        assert is_weekend_or_holiday(labor_day) is True
        assert is_weekend_or_holiday(constitution_day) is True
        assert is_weekend_or_holiday(christmas) is True
        assert is_weekend_or_holiday(boxing_day) is True

    @pytest.mark.unit
    def test_get_grid_rent_rate_jan_mar(self):
        """Test grid rent rates for January-March period."""
        grid_rent_config = {
            "JanMar": {"Day": 50.94, "Night": 38.21},
            "AprDec": {"Day": 59.86, "Night": 47.13},
        }

        # January weekday - day rate
        jan_day = datetime(2024, 1, 15, 14, 0, 0)  # Monday 14:00
        assert get_grid_rent_rate(jan_day, grid_rent_config) == 50.94

        # January weekday - night rate
        jan_night = datetime(2024, 1, 15, 23, 0, 0)  # Monday 23:00
        assert get_grid_rent_rate(jan_night, grid_rent_config) == 38.21

        # January weekend - night rate (weekend)
        jan_weekend = datetime(2024, 1, 6, 14, 0, 0)  # Saturday 14:00
        assert get_grid_rent_rate(jan_weekend, grid_rent_config) == 38.21

    @pytest.mark.unit
    def test_get_grid_rent_rate_apr_dec(self):
        """Test grid rent rates for April-December period."""
        grid_rent_config = {
            "JanMar": {"Day": 50.94, "Night": 38.21},
            "AprDec": {"Day": 59.86, "Night": 47.13},
        }

        # April weekday - day rate
        apr_day = datetime(2024, 4, 15, 14, 0, 0)  # Monday 14:00
        assert get_grid_rent_rate(apr_day, grid_rent_config) == 59.86

        # April weekday - night rate
        apr_night = datetime(2024, 4, 15, 23, 0, 0)  # Monday 23:00
        assert get_grid_rent_rate(apr_night, grid_rent_config) == 47.13

        # December weekend - night rate (weekend)
        dec_weekend = datetime(2024, 12, 7, 14, 0, 0)  # Saturday 14:00
        assert get_grid_rent_rate(dec_weekend, grid_rent_config) == 47.13

    @pytest.mark.unit
    def test_add_grid_rent_to_prices_empty_list(self):
        """Test adding grid rent to empty price list."""
        grid_rent_config = {
            "JanMar": {"Day": 50.94, "Night": 38.21},
            "AprDec": {"Day": 59.86, "Night": 47.13},
        }

        empty_prices = []
        test_date = datetime(2024, 1, 15, 0, 0, 0)

        result = add_grid_rent_to_prices(empty_prices, test_date, grid_rent_config)
        assert result == []

    @pytest.mark.unit
    def test_add_grid_rent_to_prices_jan_mar(self):
        """Test adding grid rent to prices for January-March period."""
        grid_rent_config = {
            "JanMar": {"Day": 50.94, "Night": 38.21},
            "AprDec": {"Day": 59.86, "Night": 47.13},
        }

        # Base prices in NOK/kWh
        base_prices = [1.0] * 24  # 1 NOK/kWh for all hours
        test_date = datetime(2024, 1, 15, 0, 0, 0)  # Monday

        result = add_grid_rent_to_prices(base_prices, test_date, grid_rent_config)

        # Check that we have 24 prices
        assert len(result) == 24

        # Check night rates (hours 0-5, 22-23)
        for hour in [0, 1, 2, 3, 4, 5, 22, 23]:
            expected_price = 1.0 + (38.21 / 100)  # Base + night rate in kroner
            assert result[hour] == pytest.approx(expected_price, rel=1e-6)

        # Check day rates (hours 6-21)
        for hour in range(6, 22):
            expected_price = 1.0 + (50.94 / 100)  # Base + day rate in kroner
            assert result[hour] == pytest.approx(expected_price, rel=1e-6)

    @pytest.mark.unit
    def test_add_grid_rent_to_prices_apr_dec(self):
        """Test adding grid rent to prices for April-December period."""
        grid_rent_config = {
            "JanMar": {"Day": 50.94, "Night": 38.21},
            "AprDec": {"Day": 59.86, "Night": 47.13},
        }

        # Base prices in NOK/kWh
        base_prices = [1.0] * 24  # 1 NOK/kWh for all hours
        test_date = datetime(2024, 4, 15, 0, 0, 0)  # Monday

        result = add_grid_rent_to_prices(base_prices, test_date, grid_rent_config)

        # Check that we have 24 prices
        assert len(result) == 24

        # Check night rates (hours 0-5, 22-23)
        for hour in [0, 1, 2, 3, 4, 5, 22, 23]:
            expected_price = 1.0 + (47.13 / 100)  # Base + night rate in kroner
            assert result[hour] == pytest.approx(expected_price, rel=1e-6)

        # Check day rates (hours 6-21)
        for hour in range(6, 22):
            expected_price = 1.0 + (59.86 / 100)  # Base + day rate in kroner
            assert result[hour] == pytest.approx(expected_price, rel=1e-6)

    @pytest.mark.unit
    def test_add_grid_rent_to_prices_weekend(self):
        """Test adding grid rent to prices for weekend (all night rates)."""
        grid_rent_config = {
            "JanMar": {"Day": 50.94, "Night": 38.21},
            "AprDec": {"Day": 59.86, "Night": 47.13},
        }

        # Base prices in NOK/kWh
        base_prices = [1.0] * 24  # 1 NOK/kWh for all hours
        test_date = datetime(2024, 1, 6, 0, 0, 0)  # Saturday

        result = add_grid_rent_to_prices(base_prices, test_date, grid_rent_config)

        # Check that we have 24 prices
        assert len(result) == 24

        # All hours should have night rate (weekend)
        for hour in range(24):
            expected_price = 1.0 + (38.21 / 100)  # Base + night rate in kroner
            assert result[hour] == pytest.approx(expected_price, rel=1e-6)

    @pytest.mark.unit
    def test_add_grid_rent_to_prices_realistic_prices(self):
        """Test adding grid rent to realistic electricity prices."""
        grid_rent_config = {
            "JanMar": {"Day": 50.94, "Night": 38.21},
            "AprDec": {"Day": 59.86, "Night": 47.13},
        }

        # Realistic electricity prices in NOK/kWh
        base_prices = [
            0.8,
            0.7,
            0.6,
            0.5,
            0.4,
            0.3,
            0.4,
            0.5,
            0.6,
            0.7,
            0.8,
            0.9,
            1.0,
            1.1,
            1.2,
            1.3,
            1.4,
            1.5,
            1.6,
            1.7,
            1.8,
            1.9,
            1.0,
            0.9,
        ]
        test_date = datetime(2024, 1, 15, 0, 0, 0)  # Monday

        result = add_grid_rent_to_prices(base_prices, test_date, grid_rent_config)

        # Check that we have 24 prices
        assert len(result) == 24

        # Check a few specific hours
        # Hour 0: night rate
        assert result[0] == pytest.approx(0.8 + (38.21 / 100), rel=1e-6)

        # Hour 6: day rate
        assert result[6] == pytest.approx(0.4 + (50.94 / 100), rel=1e-6)

        # Hour 14: day rate
        assert result[14] == pytest.approx(1.2 + (50.94 / 100), rel=1e-6)

        # Hour 22: night rate
        assert result[22] == pytest.approx(1.0 + (38.21 / 100), rel=1e-6)

    @pytest.mark.unit
    def test_calculate_easter_sunday(self):
        """Test Easter Sunday calculation for various years."""
        # Known Easter Sunday dates
        test_cases = [
            (2024, datetime(2024, 3, 31)),  # Easter Sunday 2024
            (2025, datetime(2025, 4, 20)),  # Easter Sunday 2025
            (2026, datetime(2026, 4, 5)),  # Easter Sunday 2026
            (2027, datetime(2027, 3, 28)),  # Easter Sunday 2027
            (2028, datetime(2028, 4, 16)),  # Easter Sunday 2028
        ]

        for year, expected_date in test_cases:
            result = calculate_easter_sunday(year)
            assert (
                result == expected_date
            ), f"Easter Sunday {year} should be {expected_date}, got {result}"

    @pytest.mark.unit
    def test_get_easter_holidays(self):
        """Test getting all Easter-related holidays for a year."""
        # Test for 2024
        easter_holidays_2024 = get_easter_holidays(2024)

        # Easter Sunday 2024 was March 31
        easter_sunday_2024 = datetime(2024, 3, 31)

        expected_holidays = [
            datetime(2024, 3, 28),  # Maundy Thursday
            datetime(2024, 3, 29),  # Good Friday
            datetime(2024, 3, 31),  # Easter Sunday
            datetime(2024, 4, 1),  # Easter Monday
            datetime(2024, 5, 9),  # Ascension Day
            datetime(2024, 5, 19),  # Pentecost Sunday
            datetime(2024, 5, 20),  # Pentecost Monday
        ]

        assert len(easter_holidays_2024) == len(expected_holidays)
        for expected, actual in zip(expected_holidays, easter_holidays_2024):
            assert actual == expected

    @pytest.mark.unit
    def test_is_weekend_or_holiday_easter_2024(self):
        """Test Easter holiday detection for 2024."""
        # Easter 2024 dates
        easter_dates_2024 = [
            datetime(2024, 3, 28),  # Maundy Thursday
            datetime(2024, 3, 29),  # Good Friday
            datetime(2024, 3, 31),  # Easter Sunday
            datetime(2024, 4, 1),  # Easter Monday
            datetime(2024, 5, 9),  # Ascension Day
            datetime(2024, 5, 19),  # Pentecost Sunday
            datetime(2024, 5, 20),  # Pentecost Monday
        ]

        for date in easter_dates_2024:
            assert is_weekend_or_holiday(date) is True, f"{date} should be a holiday"

    @pytest.mark.unit
    def test_is_weekend_or_holiday_easter_2025(self):
        """Test Easter holiday detection for 2025."""
        # Easter 2025 dates
        easter_dates_2025 = [
            datetime(2025, 4, 17),  # Maundy Thursday
            datetime(2025, 4, 18),  # Good Friday
            datetime(2025, 4, 20),  # Easter Sunday
            datetime(2025, 4, 21),  # Easter Monday
            datetime(2025, 5, 29),  # Ascension Day
            datetime(2025, 6, 8),  # Pentecost Sunday
            datetime(2025, 6, 9),  # Pentecost Monday
        ]

        for date in easter_dates_2025:
            assert is_weekend_or_holiday(date) is True, f"{date} should be a holiday"

    @pytest.mark.unit
    def test_is_weekend_or_holiday_non_holiday_dates(self):
        """Test that regular weekdays are not marked as holidays."""
        # Regular weekdays in 2024
        regular_dates = [
            datetime(2024, 1, 2),  # Tuesday after New Year
            datetime(2024, 1, 3),  # Wednesday
            datetime(2024, 1, 4),  # Thursday
            datetime(2024, 1, 5),  # Friday
            datetime(2024, 3, 27),  # Wednesday before Easter
            datetime(2024, 3, 30),  # Saturday (weekend, should be True)
            datetime(2024, 4, 2),  # Tuesday after Easter Monday
            datetime(2024, 5, 8),  # Wednesday before Ascension
            datetime(2024, 5, 10),  # Friday after Ascension
            datetime(2024, 5, 18),  # Saturday before Pentecost
            datetime(2024, 5, 21),  # Tuesday after Pentecost Monday
        ]

        for date in regular_dates:
            if date.weekday() >= 5:  # Weekend
                assert (
                    is_weekend_or_holiday(date) is True
                ), f"{date} should be a weekend"
            else:
                assert (
                    is_weekend_or_holiday(date) is False
                ), f"{date} should not be a holiday"

    @pytest.mark.unit
    def test_is_weekend_or_holiday_enhanced(self):
        """Test enhanced weekend and holiday detection with Easter holidays."""
        # Weekends
        saturday = datetime(2024, 1, 6)  # Saturday
        sunday = datetime(2024, 1, 7)  # Sunday
        assert is_weekend_or_holiday(saturday) is True
        assert is_weekend_or_holiday(sunday) is True

        # Weekdays
        monday = datetime(2024, 1, 8)  # Monday
        friday = datetime(2024, 1, 12)  # Friday
        assert is_weekend_or_holiday(monday) is False
        assert is_weekend_or_holiday(friday) is False

        # Norwegian fixed holidays
        new_year = datetime(2024, 1, 1)  # New Year's Day
        labor_day = datetime(2024, 5, 1)  # Labor Day
        constitution_day = datetime(2024, 5, 17)  # Constitution Day
        christmas = datetime(2024, 12, 25)  # Christmas Day
        boxing_day = datetime(2024, 12, 26)  # Boxing Day

        assert is_weekend_or_holiday(new_year) is True
        assert is_weekend_or_holiday(labor_day) is True
        assert is_weekend_or_holiday(constitution_day) is True
        assert is_weekend_or_holiday(christmas) is True
        assert is_weekend_or_holiday(boxing_day) is True

        # Easter holidays 2024
        maundy_thursday = datetime(2024, 3, 28)
        good_friday = datetime(2024, 3, 29)
        easter_sunday = datetime(2024, 3, 31)
        easter_monday = datetime(2024, 4, 1)
        ascension_day = datetime(2024, 5, 9)
        pentecost_sunday = datetime(2024, 5, 19)
        pentecost_monday = datetime(2024, 5, 20)

        assert is_weekend_or_holiday(maundy_thursday) is True
        assert is_weekend_or_holiday(good_friday) is True
        assert is_weekend_or_holiday(easter_sunday) is True
        assert is_weekend_or_holiday(easter_monday) is True
        assert is_weekend_or_holiday(ascension_day) is True
        assert is_weekend_or_holiday(pentecost_sunday) is True
        assert is_weekend_or_holiday(pentecost_monday) is True

    @pytest.mark.unit
    def test_get_grid_rent_rate_easter_holidays(self):
        """Test grid rent rates during Easter holidays (should be night rates)."""
        grid_rent_config = {
            "JanMar": {"Day": 50.94, "Night": 38.21},
            "AprDec": {"Day": 59.86, "Night": 47.13},
        }

        # Easter 2024 dates - all should get night rates
        easter_dates_2024 = [
            datetime(2024, 3, 28, 14, 0, 0),  # Maundy Thursday 14:00
            datetime(2024, 3, 29, 14, 0, 0),  # Good Friday 14:00
            datetime(2024, 3, 31, 14, 0, 0),  # Easter Sunday 14:00
            datetime(2024, 4, 1, 14, 0, 0),  # Easter Monday 14:00
            datetime(2024, 5, 9, 14, 0, 0),  # Ascension Day 14:00
            datetime(2024, 5, 19, 14, 0, 0),  # Pentecost Sunday 14:00
            datetime(2024, 5, 20, 14, 0, 0),  # Pentecost Monday 14:00
        ]

        for date in easter_dates_2024:
            if date.month in [1, 2, 3]:
                expected_rate = 38.21  # JanMar night rate
            else:
                expected_rate = 47.13  # AprDec night rate

            result = get_grid_rent_rate(date, grid_rent_config)
            assert (
                result == expected_rate
            ), f"{date} should have night rate {expected_rate}, got {result}"
