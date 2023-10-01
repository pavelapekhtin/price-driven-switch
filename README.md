# price-driven-switch

## Description

This is a package that allows to control smarthome appliance based on current spot price of electricity. For the time being only Tibber is supported for price data.
The cutoff prices and appliances are configurable via a web interface built with Streamlit.
Appliance on/off states are made available via a get request as a json object.

![Webapp Screenshot](docs/Screenshot%20Webapp.png)

## Installation

This package is meant to be run in docker. However you can run it locally if you want to.

### Docker

* Install docker and docker-compose on your machine. Get it here: [https://docs.docker.com/get-docker/](https://docs.docker.com/get-docker/)

* In a folder of your choice create a docker-compose.yml file and paste the content of [docker-compose.yml](https://github.com/pavelapekhtin/price-driven-switch/blob/main/docker-compose.yml)
. You can change the TZ variable to your timezone. The default is Europe/Oslo.

* Run ```docker-compose up -d``` to start the container.

Tested to work on arm64 and amd64 architectures, if you want to run it on a different architecture you will have to build the image yourself, for this clone the repository, navigate to the repository folder in the terminal and run ```docker compose -f docker-compose.dev.yml up -d```. This will build the containers from local files.

### Local

Navigate to the project folder and run:
```pip install -e .```

To start the web interface run:
```streamlit run price_driven_switch/frontend/1_📊_Dashboard.py```

To start fastapi run:
```uvicorn price_driven_switch/__main__.py:app --reload```

## Usage

On your local network you can access the web interface by going to the address of the machine running the docker container.
If you are running it locally you can access it at [http://localhost](http://localhost) or 127.0.0.1
Once you opened the web interface you should enter your Tibber tokern for the app to work.
Your tibber token can be found at [https://developer.tibber.com/settings/accesstoken](https://developer.tibber.com/settings/accesstoken)
At the Settings page of the webapp you can rename, add and remove appliances and edit their settings.

You can also set the power draw for each appliance and its priority in the settings page.  If your home is equipped with Tibber Pulse or Watty, the app can check if the total power exceeds the set limit and turn off appliances starting with lowest priority to get the total power draw below the limit which comes handy with the new pricing model for the grid use in Norway.

The on/off state of the appliances can be accessed via a get request to the following address:
```http://your-server-address/api/```

The response will be a json object with the name of the appliance and its on/off state where 1 is on and 0 is off.

```json
{
    "Boilers": 1,
    "Floor": 0,
}
```

Use this json to control your appliances via home automation software like Home Assistant, Futurehome or Homebridge.

## Known issues

- For the time being price graphs show Øre/kWh, which might not be the case for your country.
- Saving setpoint slider positions can sometimes not work after first press of the save button.
- The cutoff lines on the price graph change color depending on their relative position to other lines.
- It is not possible to change the time zone in the settings page for the time being. You can still change it in the docker-compose.yml file. ```- TZ=Europe/Oslo```

## To do

- [ ] Add currency selection to settings page.
- [ ] Add timezone selection to settings page.
- [ ] Fix cutoff line colors behaviour.
- [ ] Rework setpoints and appliances value saving.

## Future plans

- [x] Add support for limiting the hourly load.
- Add support for more price providers.
