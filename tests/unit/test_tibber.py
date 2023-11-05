import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from python_graphql_client import GraphqlClient

from price_driven_switch.backend.tibber_connection import TibberConnection


class TestTibbberConnection:
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_prices(self, tibber_test_token):
        tibber = TibberConnection(tibber_test_token)
        assert isinstance(await tibber.get_prices(), dict)
        assert "data" in await tibber.get_prices()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_prices_wrong_token_raises(self):
        with pytest.raises(ConnectionRefusedError):
            tibber = TibberConnection("wrong_token")
            await tibber.get_prices()

    @pytest.mark.integration
    def test_connection(self, tibber_test_token):
        tibber = TibberConnection(tibber_test_token)
        assert isinstance(tibber.connection, GraphqlClient)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_current_power(self, tibber_test_token):
        tibber = TibberConnection(tibber_test_token)
        power = await tibber.current_power_subscription(once=True)
        assert isinstance(power, int)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_check_token_validity(self, tibber_test_token):
        tibber = TibberConnection(tibber_test_token)
        assert await tibber.check_token_validity() is True

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_check_token_validity_wrong(self):
        tibber = TibberConnection("agsga")
        assert await tibber.check_token_validity() is False
