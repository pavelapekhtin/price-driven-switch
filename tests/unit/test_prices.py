from datetime import datetime
from unittest.mock import patch

import pytest

from price_driven_switch.backend.prices import Prices


class TestPrices:
    @pytest.mark.unit
    def test_offset_now(self, mock_instance_with_hour) -> None:
        _mock_hour, instance = mock_instance_with_hour
        assert isinstance(instance.offset_now, float)
        # Hour 6 has price 0.0203, which is tied with hour 5 for lowest price
        # With new logic, hour 5 gets position 0, hour 6 gets position 1
        # This distributes hours evenly even when prices are the same
        assert 0 <= instance.offset_now <= 1
        # Hour 6 should be in the cheapest tier (offset < 0.1)
        assert instance.offset_now < 0.1

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

    @pytest.mark.unit
    def test_today_prices_with_norgespris(self, api_response_fixture) -> None:
        """Test that Norgespris returns fixed prices when enabled."""
        with patch(
            "price_driven_switch.backend.prices.load_settings_file"
        ) as mock_load_settings:
            mock_load_settings.return_value = {
                "Settings": {
                    "UseNorgespris": True,
                    "NorgesprisRate": 50.0,
                    "IncludeGridRent": False,
                }
            }

            prices = Prices(api_response_fixture)
            today_prices = prices.today_prices

            # Should return 24 hours of fixed price in NOK (converted from øre)
            assert len(today_prices) == 24
            assert all(price == 0.50 for price in today_prices)

    @pytest.mark.unit
    def test_tomo_prices_with_norgespris(self, api_response_fixture) -> None:
        """Test that Norgespris returns fixed prices for tomorrow when enabled."""
        with patch(
            "price_driven_switch.backend.prices.load_settings_file"
        ) as mock_load_settings:
            mock_load_settings.return_value = {
                "Settings": {
                    "UseNorgespris": True,
                    "NorgesprisRate": 40.0,
                    "IncludeGridRent": False,
                }
            }

            prices = Prices(api_response_fixture)
            tomo_prices = prices.tomo_prices

            # Should return 24 hours of fixed price in NOK (converted from øre)
            assert len(tomo_prices) == 24
            assert all(price == 0.40 for price in tomo_prices)

    @pytest.mark.unit
    def test_norgespris_with_grid_rent(self, api_response_fixture) -> None:
        """Test that grid rent is added to Norgespris when both are enabled."""
        with (
            patch(
                "price_driven_switch.backend.prices.load_settings_file"
            ) as mock_load_settings,
            patch("price_driven_switch.backend.prices.datetime") as mock_datetime,
        ):
            # Mock a Wednesday in January (day rate applies)
            mock_now = datetime(2024, 1, 3, 12, 0, 0)  # Wednesday noon
            mock_datetime.now.return_value = mock_now

            mock_load_settings.return_value = {
                "Settings": {
                    "UseNorgespris": True,
                    "NorgesprisRate": 50.0,
                    "IncludeGridRent": True,
                    "GridRent": {
                        "JanMar": {"Day": 50.94, "Night": 38.21},
                        "AprDec": {"Day": 59.86, "Night": 47.13},
                    },
                }
            }

            prices = Prices(api_response_fixture)
            today_prices = prices.today_prices

            # Should return Norgespris (50 øre = 0.50 NOK) + grid rent
            assert len(today_prices) == 24
            # All prices should be greater than base norgespris due to grid rent
            assert all(price > 0.50 for price in today_prices)
            # Some hours should have day rate, some night rate
            # At least one price should be different from others due to different grid rent rates
            assert len(set(today_prices)) > 1
