import pytest
from price_driven_switch.backend.tibber import TibberConnection
from python_graphql_client import GraphqlClient


class TestTibbberConnection:
    def test_get_prices(self, tibber_test_token):
        tibber = TibberConnection(tibber_test_token)
        assert isinstance(tibber.get_prices(), dict)
        assert "data" in tibber.get_prices()

    def test_get_prices_wrong_token_raises(self):
        with pytest.raises(ConnectionRefusedError):
            tibber = TibberConnection("wrong_token")
            tibber.get_prices()

    def test_connection(self, tibber_test_token):
        tibber = TibberConnection(tibber_test_token)
        assert isinstance(tibber.connection, GraphqlClient)

    def test_check_token_validity(self, tibber_test_token):
        tibber = TibberConnection(tibber_test_token)
        assert tibber.check_token_validity() is True

    def test_check_token_validity_wrong(self):
        tibber = TibberConnection("agsga")
        assert tibber.check_token_validity() is False
