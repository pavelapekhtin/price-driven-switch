import os

import aiohttp
import tibber
from dotenv import load_dotenv
from loguru import logger
from python_graphql_client import GraphqlClient  # type: ignore

TIBBER_API_ENDPOINT = "https://api.tibber.com/v1-beta/gql"

PRICE_NO_TAX_QUERY = """
{ 
    viewer {
        homes {
        currentSubscription{
            priceInfo{
            today {
                total
            }
            tomorrow {
                total
            }
            }
        }
        }
    }
}
"""

load_dotenv("price_driven_switch/config/.env", verbose=True)
TIBBER_TOKEN = str(os.environ.get("TIBBER_TOKEN"))

logger.add(
    "./logs/tibber_connection.log",
    rotation="1 week",
    retention="7 days",
    level="INFO",
)


class TibberConnection:
    def __init__(self, api_token: str = TIBBER_TOKEN) -> None:
        self.api_token = api_token
        self.power_reading: int = 0
        self.subscription_status: bool = False
        self.tibber_connection = None
        self.home = None

    async def initialize_tibber(self) -> None:
        async with aiohttp.ClientSession() as session:
            self.tibber_connection = tibber.Tibber(
                self.api_token, websession=session, user_agent="price_driven_switch"
            )
            await self.tibber_connection.update_info()
            self.home = self.tibber_connection.get_homes()[0]

    def _update_callback(self, data: dict) -> None:
        live_measurement = data.get("data", {}).get("liveMeasurement")
        if live_measurement:
            self.power_reading = live_measurement.get("power")
            self.subscription_status = True
            logger.debug(f"Power reading: {self.power_reading}")
            logger.debug(f"Subscription status: {self.subscription_status}")
        else:
            self.subscription_status = False

    async def subscribe_to_realtime_data(self) -> None:
        if self.home is None:
            await self.initialize_tibber()

        await self.home.rt_subscribe(self._update_callback)  # type: ignore
        logger.info("Subscribed to realtime data")

    async def close(self):
        # Add logic here to gracefully close any connections or sessions
        if self.tibber_connection:
            logger.debug("Disconnecting from Tibber realtime subscription")
            await self.tibber_connection.rt_disconnect()

    async def get_prices(self) -> dict:
        response = await self.connection.execute_async(
            PRICE_NO_TAX_QUERY, headers={"Authorization": self.api_token}
        )
        try:
            _ = response["errors"]  #  Check if there are any errors in the response
            if response["errors"][0]["extensions"]["code"] == "UNAUTHENTICATED":
                raise ConnectionRefusedError(
                    "Authentication failed. Check your Tibber API token."
                )
        except KeyError:  # no errors in response
            pass

        return response

    @property
    def connection(self) -> GraphqlClient:
        return GraphqlClient(endpoint=TIBBER_API_ENDPOINT)

    async def check_token_validity(self) -> bool:
        try:
            _ = await self.get_prices()
        except ConnectionRefusedError:
            return False
        return True
