import asyncio
import json
import os
import random

import websockets
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
        websocket_url = "wss://api.tibber.com/v1-beta/gql/subscriptions"
        user_agent = "YourPlatform/YourVersion com.yourapp/YourAppVersion"

        async with websockets.connect(
            websocket_url, extra_headers={"User-Agent": user_agent}
        ) as ws:
            await ws.send(
                json.dumps(
                    {
                        "type": "connection_init",
                        "payload": {"Authorization": self.api_token},
                    }
                )
            )

            await ws.send(
                json.dumps(
                    {
                        "id": "1",
                        "type": "start",
                        "payload": {"query": CURRENT_POWER_QUERY},
                    }
                )
            )

            retry_count = 0
            while True:
                try:
                    message = await ws.recv()
                    message_data = json.loads(message)

                    if "data" in message_data:
                        current_power = message_data["data"]["liveMeasurement"]["power"]
                        print(f"Current Power: {current_power}")
                        return current_power

                    elif "errors" in message_data:
                        if (
                            message_data["errors"][0]["extensions"]["code"]
                            == "UNAUTHENTICATED"
                        ):
                            print("Authentication failed. Retrying with new token.")
                            # Re-run the authorization process here and break the loop if needed
                            break

                    else:
                        print("Unknown message type.")

                except websockets.exceptions.ConnectionClosed as e:
                    print("Connection closed:", e)

                    # Implement jitter and exponential backoff
                    retry_count += 1
                    sleep_time = (2**retry_count) + random.uniform(
                        0, 0.2 * (2**retry_count)
                    )

                    if e.code == 1001:  # Tibber websocket API restart
                        sleep_time = random.uniform(1, 60)

                    print(f"Retrying in {sleep_time} seconds.")
                    await asyncio.sleep(sleep_time)

                except Exception as e:
                    print("An error occurred:", e)
                    break
