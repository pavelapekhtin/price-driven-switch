import pytest
from python_graphql_client import GraphqlClient

from price_driven_switch.backend.tibber import TibberConnection


class TestTibbberConnection:
    @pytest.mark.integration
    def test_get_prices(self, tibber_test_token):
        tibber = TibberConnection(tibber_test_token)
        assert isinstance(tibber.get_prices(), dict)
        assert "data" in tibber.get_prices()

    @pytest.mark.integration
    def test_get_prices_wrong_token_raises(self):
        with pytest.raises(ConnectionRefusedError):
            tibber = TibberConnection("wrong_token")
            tibber.get_prices()

    @pytest.mark.integration
    def test_connection(self, tibber_test_token):
        tibber = TibberConnection(tibber_test_token)
        assert isinstance(tibber.connection, GraphqlClient)

    @pytest.mark.integration
    def test_get_current_power(self, tibber_test_token):
        tibber = TibberConnection(tibber_test_token)
        assert isinstance(tibber.get_current_power(), int)
        assert tibber.get_current_power() > 0

    @pytest.mark.integration
    def test_check_token_validity(self, tibber_test_token):
        tibber = TibberConnection(tibber_test_token)
        assert tibber.check_token_validity() is True

    @pytest.mark.integration
    def test_check_token_validity_wrong(self):
        tibber = TibberConnection("agsga")
        assert tibber.check_token_validity() is False
