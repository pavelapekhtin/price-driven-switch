from datetime import datetime
from unittest.mock import patch

import pytest

from price_driven_switch.backend.prices import Prices


class TestPrices:
    @pytest.mark.unit
    def test_offset_now(self, mock_instance_with_hour) -> None:
        _, instance = mock_instance_with_hour
        assert isinstance(instance.offset_now, float)
        # Since grid rent is disabled in the fixture, offset should be 0 for the lowest price
        assert instance.offset_now == 0

    @pytest.mark.unit
    def test_price_now(
        self, mock_instance_hour_now, prices_instance_fixture, price_now_fixture
    ) -> None:
        instance_fixture = prices_instance_fixture
        # Since grid rent is disabled in the fixture, price should match base price
        assert instance_fixture.price_now == price_now_fixture

    @pytest.mark.unit
    def test_hour_now(self, api_response_fixture) -> None:
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
            assert prices._hour_now() == datetime.now().hour

    @pytest.mark.unit
    def test_today_prices(
        self, base_today_prices_fixture, prices_instance_fixture
    ) -> None:
        instance_fixture = prices_instance_fixture
        assert isinstance(instance_fixture.today_prices, list)
        # Since grid rent is disabled in the fixture, prices should match base prices
        assert instance_fixture.today_prices == base_today_prices_fixture

    @pytest.mark.unit
    def test_tomo_prices(self, prices_instance_fixture) -> None:
        instance_fixture = prices_instance_fixture
        assert isinstance(instance_fixture.tomo_prices, list)

    @pytest.mark.unit
    def test_today_prices_with_grid_rent(self, api_response_fixture) -> None:
        """Test that grid rent is added to today's prices when enabled."""
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
            today_prices = prices.today_prices

            # Should have grid rent added (prices should be higher than base)
            base_prices = prices._load_prices("today")
            assert len(today_prices) == len(base_prices)

            # All prices should be higher due to grid rent
            for i, price in enumerate(today_prices):
                assert price > base_prices[i]

    @pytest.mark.unit
    def test_today_prices_without_grid_rent(self, api_response_fixture) -> None:
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
            today_prices = prices.today_prices
            base_prices = prices._load_prices("today")

            # Should be the same as base prices (no grid rent added)
            assert today_prices == base_prices

    @pytest.mark.unit
    def test_tomo_prices_with_grid_rent(self, api_response_fixture) -> None:
        """Test that grid rent is added to tomorrow's prices when enabled."""
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
            tomo_prices = prices.tomo_prices

            # Should have grid rent added (prices should be higher than base)
            base_prices = prices._load_prices("tomorrow")
            assert len(tomo_prices) == len(base_prices)

            # All prices should be higher due to grid rent
            for i, price in enumerate(tomo_prices):
                assert price > base_prices[i]

    @pytest.mark.unit
    def test_get_price_at_offset_today(self, prices_instance_fixture) -> None:
        """Test getting price at specific offset for today."""
        instance = prices_instance_fixture

        # Test offset 0 (lowest price)
        price_at_0 = instance.get_price_at_offset_today(0.0)
        assert isinstance(price_at_0, float)
        assert price_at_0 >= 0

        # Test offset 1 (highest price)
        price_at_1 = instance.get_price_at_offset_today(1.0)
        assert isinstance(price_at_1, float)
        assert price_at_1 >= price_at_0

    @pytest.mark.unit
    def test_get_price_at_offset_tomorrow(self, prices_instance_fixture) -> None:
        """Test getting price at specific offset for tomorrow."""
        instance = prices_instance_fixture

        # Test offset 0 (lowest price)
        price_at_0 = instance.get_price_at_offset_tomorrow(0.0)
        assert isinstance(price_at_0, float)
        assert price_at_0 >= 0

        # Test offset 1 (highest price)
        price_at_1 = instance.get_price_at_offset_tomorrow(1.0)
        assert isinstance(price_at_1, float)
        assert price_at_1 >= price_at_0

    @pytest.mark.unit
    def test_get_price_of_the_offset_invalid_input(
        self, prices_instance_fixture
    ) -> None:
        """Test that invalid offset values raise ValueError."""
        instance = prices_instance_fixture

        with pytest.raises(ValueError):
            instance.get_price_of_the_offset([1.0, 2.0, 3.0], -0.1)

        with pytest.raises(ValueError):
            instance.get_price_of_the_offset([1.0, 2.0, 3.0], 1.1)
