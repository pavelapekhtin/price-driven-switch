from datetime import datetime

import pytest

from price_driven_switch.backend.grid_rent import (
    add_grid_rent_to_prices,
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
