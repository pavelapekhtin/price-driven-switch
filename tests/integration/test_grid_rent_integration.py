from datetime import datetime
from unittest.mock import patch

import pytest

from price_driven_switch.backend.grid_rent import (
    add_grid_rent_to_prices,
    get_grid_rent_rate,
)
from price_driven_switch.backend.prices import Prices


class TestGridRentIntegration:
    @pytest.mark.integration
    def test_grid_rent_with_real_prices(self, api_response_fixture):
        """Test grid rent integration with real price data."""
        grid_rent_config = {
            "JanMar": {"Day": 50.94, "Night": 38.21},
            "AprDec": {"Day": 59.86, "Night": 47.13},
        }

        # Test with January date
        jan_date = datetime(2024, 1, 15, 0, 0, 0)  # Monday

        # Get base prices from the fixture
        prices = Prices(api_response_fixture)
        base_prices = prices._load_prices("today")

        # Add grid rent
        prices_with_grid_rent = add_grid_rent_to_prices(
            base_prices, jan_date, grid_rent_config
        )

        # Verify results
        assert len(prices_with_grid_rent) == len(base_prices)

        # All prices should be higher due to grid rent
        for i, price in enumerate(prices_with_grid_rent):
            assert price > base_prices[i]

            # Verify the increase is reasonable (grid rent should be 0.38-0.51 NOK/kWh)
            increase = price - base_prices[i]
            assert 0.38 <= increase <= 0.51

    @pytest.mark.integration
    def test_grid_rent_seasonal_differences(self, api_response_fixture):
        """Test that grid rent rates differ between seasons."""
        grid_rent_config = {
            "JanMar": {"Day": 50.94, "Night": 38.21},
            "AprDec": {"Day": 59.86, "Night": 47.13},
        }

        # Test January (JanMar rates)
        jan_date = datetime(2024, 1, 15, 14, 0, 0)  # Monday 14:00 (day rate)
        jan_rate = get_grid_rent_rate(jan_date, grid_rent_config)

        # Test April (AprDec rates)
        apr_date = datetime(2024, 4, 15, 14, 0, 0)  # Monday 14:00 (day rate)
        apr_rate = get_grid_rent_rate(apr_date, grid_rent_config)

        # April rates should be higher than January rates
        assert apr_rate > jan_rate
        assert apr_rate == 59.86
        assert jan_rate == 50.94

    @pytest.mark.integration
    def test_grid_rent_day_night_differences(self, api_response_fixture):
        """Test that grid rent rates differ between day and night."""
        grid_rent_config = {
            "JanMar": {"Day": 50.94, "Night": 38.21},
            "AprDec": {"Day": 59.86, "Night": 47.13},
        }

        # Test January day rate
        jan_day = datetime(2024, 1, 15, 14, 0, 0)  # Monday 14:00 (day rate)
        jan_day_rate = get_grid_rent_rate(jan_day, grid_rent_config)

        # Test January night rate
        jan_night = datetime(2024, 1, 15, 23, 0, 0)  # Monday 23:00 (night rate)
        jan_night_rate = get_grid_rent_rate(jan_night, grid_rent_config)

        # Day rate should be higher than night rate
        assert jan_day_rate > jan_night_rate
        assert jan_day_rate == 50.94
        assert jan_night_rate == 38.21

    @pytest.mark.integration
    def test_grid_rent_weekend_rates(self, api_response_fixture):
        """Test that weekends use night rates regardless of time."""
        grid_rent_config = {
            "JanMar": {"Day": 50.94, "Night": 38.21},
            "AprDec": {"Day": 59.86, "Night": 47.13},
        }

        # Test Saturday during day hours
        saturday_day = datetime(2024, 1, 6, 14, 0, 0)  # Saturday 14:00
        saturday_day_rate = get_grid_rent_rate(saturday_day, grid_rent_config)

        # Test Saturday during night hours
        saturday_night = datetime(2024, 1, 6, 23, 0, 0)  # Saturday 23:00
        saturday_night_rate = get_grid_rent_rate(saturday_night, grid_rent_config)

        # Both should use night rate (weekend)
        assert saturday_day_rate == saturday_night_rate
        assert saturday_day_rate == 38.21

    @pytest.mark.integration
    def test_prices_class_with_grid_rent_integration(self, api_response_fixture):
        """Test that the Prices class correctly integrates grid rent."""
        with patch(
            "price_driven_switch.backend.prices.load_settings_file"
        ) as mock_load_settings:
            mock_load_settings.return_value = {
                "Settings": {
                    "IncludeGridRent": True,
                    "GridRent": {
                        "JanMar": {"Day": 50.94, "Night": 38.21},
                        "AprDec": {"Day": 59.86, "Night": 47.13},
                    },
                }
            }

            prices = Prices(api_response_fixture)

            # Test today's prices
            today_prices = prices.today_prices
            base_today_prices = prices._load_prices("today")

            assert len(today_prices) == len(base_today_prices)

            # All prices should be higher due to grid rent
            for i, price in enumerate(today_prices):
                assert price > base_today_prices[i]

            # Test tomorrow's prices
            tomo_prices = prices.tomo_prices
            base_tomo_prices = prices._load_prices("tomorrow")

            assert len(tomo_prices) == len(base_tomo_prices)

            # All prices should be higher due to grid rent
            for i, price in enumerate(tomo_prices):
                assert price > base_tomo_prices[i]

    @pytest.mark.integration
    def test_grid_rent_disabled_integration(self, api_response_fixture):
        """Test that grid rent is not added when disabled."""
        with patch(
            "price_driven_switch.backend.prices.load_settings_file"
        ) as mock_load_settings:
            mock_load_settings.return_value = {
                "Settings": {
                    "IncludeGridRent": False,
                    "GridRent": {
                        "JanMar": {"Day": 50.94, "Night": 38.21},
                        "AprDec": {"Day": 59.86, "Night": 47.13},
                    },
                }
            }

            prices = Prices(api_response_fixture)

            # Test today's prices
            today_prices = prices.today_prices
            base_today_prices = prices._load_prices("today")

            # Should be the same as base prices (no grid rent added)
            assert today_prices == base_today_prices

            # Test tomorrow's prices
            tomo_prices = prices.tomo_prices
            base_tomo_prices = prices._load_prices("tomorrow")

            # Should be the same as base prices (no grid rent added)
            assert tomo_prices == base_tomo_prices
