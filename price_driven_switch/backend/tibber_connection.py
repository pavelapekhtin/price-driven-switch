import asyncio
import os

import aiohttp
import tibber.const
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


class TibberConnection:
    def __init__(self, api_token: str = TIBBER_TOKEN) -> None:
        self.api_token = api_token
        self.power_reading: int = 0

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

    def callback(self, pkg) -> None:
        data = pkg.get("data")
        if data is not None:
            self.power_reading = data.get("liveMeasurement", {}).get("power")
        else:
            self.power_reading = 0

    async def current_power_subscription(self, once: bool = False) -> int | None:
        async with aiohttp.ClientSession() as session:
            tibber_connection = tibber.Tibber(
                self.api_token, websession=session, user_agent="change_this"
            )
            await tibber_connection.update_info()

        home = tibber_connection.get_homes()[0]
        try:
            await home.rt_subscribe(callback=self.callback)
            if once:
                await asyncio.sleep(10)  # Wait for the first callback
                return self.power_reading
            while True:
                await asyncio.sleep(10)
        except asyncio.CancelledError:
            logger.info("Real-time subscription is being cancelled.")
        finally:
            asyncio.ensure_future(self._unsubscribe(home))

    async def _unsubscribe(self, home):
        logger.info("Unsubscribing from Tibber real-time data.")
        home.rt_unsubscribe()
