import asyncio
import os
from typing import Optional

import aiohttp
import tibber.const
from dotenv import load_dotenv
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

CURRENT_POWER_QUERY = """
subscription{
  liveMeasurement(homeId:"1bb41b16-0583-4e94-b20b-6482fd6a13d4"){
    power
  }
}
"""


# TODO: add token loading from file

load_dotenv("price_driven_switch/config/.env", verbose=True)
TIBBER_TOKEN = str(os.environ.get("TIBBER_TOKEN"))


class TibberConnection:
    def __init__(self, api_token: str = TIBBER_TOKEN) -> None:
        self.api_token = api_token
        self.first_reading_done = asyncio.Event()

    def get_prices(self) -> dict:
        response = asyncio.run(
            self.connection.execute_async(
                PRICE_NO_TAX_QUERY, headers={"Authorization": self.api_token}
            )
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

    def check_token_validity(self) -> bool:
        try:
            _ = self.get_prices()
        except ConnectionRefusedError:
            return False
        return True

    async def get_current_power(self) -> int:
        power_reading: int | None = None

        def callback(pkg) -> int | None:
            nonlocal power_reading
            data = pkg.get("data")
            if data is None:
                return
            power_reading = data.get("liveMeasurement").get("power")
            self.first_reading_done.set()

        async with aiohttp.ClientSession() as session:
            tibber_connection = tibber.Tibber(
                self.api_token,
                websession=session,
                user_agent="price_driven_switch/0.4.5",
            )
            await tibber_connection.update_info()

        home = tibber_connection.get_homes()[0]
        await home.rt_subscribe(callback)

        # Wait for the first reading
        await self.first_reading_done.wait()

        home.rt_unsubscribe()

        if power_reading is not None:
            return power_reading
        else:
            raise ValueError("Failed to get power reading.")
