# price-driven-switch

## Description

This is a package that allows to control smarthome appliance based on current spot price of electricity. For the time being only Tibber is supported for price data.
The cutoff prices and appliances are configurable via a web interface built with Streamlit.
Appliance on/off states are made available via a get request as a json object.

![Webapp Screenshot](docs/Screenshot%20Webapp.png)

## Installation

This package is meant to be run in docker. However you can run it locally if you want to.

### Docker

Clone the repository and run:
```docker-compose up -d```

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
At the Settings page of the webapp you can rename, add and remove appliances.

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

- Add support for more price providers.
- Add support for limiting the hourly load.
