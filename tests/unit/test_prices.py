from datetime import datetime

import pytest

from price_driven_switch.backend.prices import Prices


class TestPrices:
    @pytest.mark.unit
    def test_offset_now(self, mock_instance_with_hour) -> None:
        _, instance = mock_instance_with_hour
        assert isinstance(instance.offset_now, float)
        assert instance.offset_now == 0

    @pytest.mark.unit
    def test_price_now(
        self, mock_instance_hour_now, prices_instance_fixture, price_now_fixture
    ) -> None:
        instance_fixture = prices_instance_fixture
        assert instance_fixture.price_now == price_now_fixture

    @pytest.mark.unit
    def test_hour_now(self, api_response_fixture) -> None:
        prices = Prices(api_response_fixture)
        assert prices._hour_now() == datetime.now().hour

    @pytest.mark.unit
    def test_today_prices(self, today_prices_fixture, prices_instance_fixture) -> None:
        instance_fixture = prices_instance_fixture
        assert isinstance(instance_fixture.today_prices, list)
        assert instance_fixture.today_prices == today_prices_fixture

    @pytest.mark.unit
    def test_tomo_prices(self, prices_instance_fixture) -> None:
        instance_fixture = prices_instance_fixture
        assert isinstance(instance_fixture.tomo_prices, list)
