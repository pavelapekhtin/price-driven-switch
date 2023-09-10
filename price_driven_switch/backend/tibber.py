import asyncio
import os

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

# TODO: add token loading from file

load_dotenv("price_driven_switch/config/.env", verbose=True)
TIBBER_TOKEN = str(os.environ.get("TIBBER_TOKEN"))


class TibberConnection:
    def __init__(self, api_token: str = TIBBER_TOKEN) -> None:
        self.api_token = api_token

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
