from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from python_graphql_client import GraphqlClient

from price_driven_switch.backend.tibber_connection import TibberConnection


class TestTibbberConnection:
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_prices(self, tibber_test_token):
        """Test get_prices with mocked response."""
        mock_response = {
            "data": {
                "viewer": {
                    "homes": [
                        {
                            "currentSubscription": {
                                "priceInfo": {
                                    "today": [{"total": 0.5}],
                                    "tomorrow": [{"total": 0.6}],
                                }
                            }
                        }
                    ]
                }
            }
        }

        with patch.object(
            GraphqlClient, "execute_async", new_callable=AsyncMock
        ) as mock_execute:
            mock_execute.return_value = mock_response
            tibber = TibberConnection(tibber_test_token)
            result = await tibber.get_prices()
            assert isinstance(result, dict)
            assert "data" in result

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_prices_wrong_token_raises(self):
        """Test get_prices with invalid token raises exception."""
        mock_response_with_error = {
            "errors": [{"extensions": {"code": "UNAUTHENTICATED"}}]
        }

        with patch.object(
            GraphqlClient, "execute_async", new_callable=AsyncMock
        ) as mock_execute:
            mock_execute.return_value = mock_response_with_error
            with pytest.raises(ConnectionRefusedError):
                tibber = TibberConnection("wrong_token")
                await tibber.get_prices()

    @pytest.mark.unit
    def test_connection(self, tibber_test_token):
        """Test that connection is properly initialized."""
        tibber = TibberConnection(tibber_test_token)
        assert isinstance(tibber.connection, GraphqlClient)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_check_token_validity(self, tibber_test_token):
        """Test token validity check with valid token."""
        mock_response = {"data": {"viewer": {"homes": [{"id": "test-home-id"}]}}}

        with patch.object(
            GraphqlClient, "execute_async", new_callable=AsyncMock
        ) as mock_execute:
            mock_execute.return_value = mock_response
            tibber = TibberConnection(tibber_test_token)
            result = await tibber.check_token_validity()
            assert result is True

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_check_token_validity_wrong(self):
        """Test token validity check with invalid token."""
        mock_response_with_error = {
            "errors": [{"extensions": {"code": "UNAUTHENTICATED"}}]
        }

        with patch.object(
            GraphqlClient, "execute_async", new_callable=AsyncMock
        ) as mock_execute:
            mock_execute.return_value = mock_response_with_error
            tibber = TibberConnection("agsga")
            result = await tibber.check_token_validity()
            assert result is False
