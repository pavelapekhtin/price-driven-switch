import json
from unittest.mock import mock_open, patch

import pytest
from freezegun import freeze_time

from price_driven_switch.backend.price_file import PriceFile
from price_driven_switch.backend.tibber_connection import TibberConnection


class TestPriceFile:
    @pytest.mark.unit
    @freeze_time("2023-05-06 18:25")
    def test_load_price_file(self, json_string_fixture, file_date_fixture):
        mock_tibber = TibberConnection("test_token")
        price_file = PriceFile(mock_tibber)

        with patch(
            "builtins.open", mock_open(read_data=json_string_fixture)
        ) as mock_file:
            file_date, api_dict = price_file._load_price_file()

        mock_file.assert_called_once_with(price_file.path, mode="r", encoding="utf-8")

        # assert file timestamp
        assert file_date == file_date_fixture

        # assert api_dict
        loaded_api_response = json.loads(json_string_fixture).get("api_response")
        assert api_dict == loaded_api_response

    @pytest.mark.unit
    @pytest.mark.asyncio
    @freeze_time("2023-05-06 18:25")
    async def test_check_file_no_file(self, mock_tibber_get_prices):
        mock_tibber = TibberConnection("test_token")
        price_file = PriceFile(mock_tibber)

        with (
            patch("os.path.exists", return_value=False),
            patch(
                "price_driven_switch.backend.price_file.PriceFile._update_price_file"
            ) as mock_update,
        ):
            await price_file._check_file()

        mock_update.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    @freeze_time("2023-05-07 18:25")
    async def test_check_file_out_of_date(self, mock_tibber_get_prices):
        mock_tibber = TibberConnection("test_token")
        price_file = PriceFile(mock_tibber)

        with (
            patch("os.path.exists", return_value=True),
            patch(
                "price_driven_switch.backend.price_file.PriceFile._load_price_file",
                return_value=("2023-05-06 18:25", {}),
            ),
            patch(
                "price_driven_switch.backend.price_file.PriceFile._write_prices_file"
            ) as mock_write,
        ):
            await price_file._check_file()

        mock_write.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    @freeze_time("2023-05-06 19:25")
    async def test_check_file_up_to_date(self, mock_tibber_get_prices):
        mock_tibber = TibberConnection("test_token")
        price_file = PriceFile(mock_tibber)

        with (
            patch("os.path.exists", return_value=True),
            patch(
                "price_driven_switch.backend.price_file.PriceFile._load_price_file",
                return_value=("2023-05-06 18:25", {}),
            ),
            patch(
                "price_driven_switch.backend.price_file.PriceFile._write_prices_file"
            ) as mock_write,
        ):
            await price_file._check_file()

        mock_write.assert_not_called()

    @pytest.mark.unit
    @pytest.mark.asyncio
    @freeze_time("2023-05-06 18:25")
    async def test_load_prices(self, mock_tibber_get_prices):
        mock_tibber = TibberConnection("test_token")
        price_file = PriceFile(mock_tibber)

        with patch(
            "price_driven_switch.backend.price_file.PriceFile._load_price_file",
            return_value=("2023-05-06 18:25", {"some_key": "some_value"}),
        ):
            result = await price_file.load_prices()

        assert result == {"some_key": "some_value"}

    @pytest.mark.unit
    @freeze_time("2021-01-02 00:15")
    def test_check_out_of_date(self):
        mock_tibber = TibberConnection("test_token")
        price_file = PriceFile(mock_tibber)

        assert price_file._check_out_of_date("2021-01-01 23:15") is True
        assert price_file._check_out_of_date("2021-01-01 12:15") is True
        assert price_file._check_out_of_date("2021-01-02 00:05") is False

    @pytest.mark.unit
    @freeze_time("2021-01-01 13:20")
    def test_check_out_of_date_case_2(self):
        mock_tibber = TibberConnection("test_token")
        price_file = PriceFile(mock_tibber)

        assert price_file._check_out_of_date("2020-12-31 23:05") is True
        assert price_file._check_out_of_date("2021-01-01 12:10") is True
        assert price_file._check_out_of_date("2021-01-01 11:15") is True
        assert price_file._check_out_of_date("2021-01-01 13:20") is False
        assert price_file._check_out_of_date("2021-01-01 13:21") is False

    @pytest.mark.unit
    @freeze_time("2021-01-01 12:15")
    def test_check_out_of_date_case_3(self):
        mock_tibber = TibberConnection("test_token")
        price_file = PriceFile(mock_tibber)

        assert price_file._check_out_of_date("2021-01-01 11:15") is False
        assert price_file._check_out_of_date("2020-12-31 23:05") is True

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_price_file(self, mock_tibber_get_prices):
        mock_tibber = TibberConnection("test_token")
        price_file = PriceFile(mock_tibber)

        with (
            patch("builtins.open", mock_open()) as mock_file,
            patch("json.dump") as mock_json_dump,
        ):
            await price_file._update_price_file()

        mock_json_dump.assert_called_once()
        mock_file.assert_called_once_with(price_file.path, mode="w", encoding="utf-8")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_load_prices_from_server(self, mock_tibber_get_prices):
        mock_tibber = TibberConnection("test_token")
        price_file = PriceFile(mock_tibber)

        result = await price_file._load_prices_from_server()
        assert result["api_response"] == mock_tibber_get_prices

    @pytest.mark.unit
    def test_write_prices_file(self, mock_tibber_get_prices):
        mock_tibber = TibberConnection("test_token")
        price_file = PriceFile(mock_tibber)

        api_response = {"some_key": "some_value"}

        with (
            patch("builtins.open", mock_open()) as mock_file,
            patch("json.dump") as mock_json_dump,
        ):
            price_file._write_prices_file(api_response)

        mock_json_dump.assert_called_once_with(api_response, mock_file())
        mock_file.assert_any_call(price_file.path, mode="w", encoding="utf-8")
