## 3.3.5 (2024-10-12)

### Fix

- **price-file**: changed price update check to 1:20 pm and corrected frontend typo

## 3.3.2 (2024-05-14)

## 3.3.1 (2024-02-25)

## 3.3.4 (2024-07-07)

## 3.3.3 (2024-05-14)

### Fix

- **build**: bump black version and style edits

## 3.3.1 (2024-05-14)

### Fix

- **build**: bump black version and style edits
- **frontend**: previous update removed released features

## 3.3.0 (2024-02-24)

### Feat

- **configureation**: show app version in Streamlit dashboard

## 3.2.1 (2024-02-24)

### Fix

- **poetry**: bumpt fastapi version

## 3.2.0 (2023-12-16)

### Feat

- **frontend**: added current hour line to today chart

### Fix

- **price_file**: moved noon file check time

## 3.1.4 (2023-12-03)

- **docker**: improved docker image security


## 3.1.3 (2023-12-02)

### Fix

- **frontend**: fixed slider jumpback bug

## 3.1.2 (2023-11-30)

### Fix

- **power_limit**: fixed staying on despite the price in some cases

## 3.1.1 (2023-11-28)

### Fix

- **frontend**: fixed no changes saving after switching page

### Refactor

- **frontend**: log display improvements
- **logs**: more visible status codes

## 3.1.0 (2023-11-28)

### Feat

- **backend**: added more user friendly logs
- **frontend**: previous setpoints and log display on the status page
- **backend**: previous setpoints api route added

## 3.0.1 (2023-11-27)

### Fix

- **frontend**: removed max_power warning from settings page at first run
- **token-input**: container restart after token input no loger required

### Perf

- **frontend**: editing appliances table does not require save button
- **frontend**: sliders do not require a save button anymore

## 3.0.0 (2023-11-26)

### BREAKING CHANGE

- Priority order in appliance list is now reversed. Higher number means higher appliance priority - update your existing settings

### Feat

- **limit_power**: added feedback loop to take the appliances that are already off into account

### Refactor

- **limit_power**: rewrote limit_power logic

## 2.2.4 (2023-11-12)

### Fix

- **tibber**: separated realtime and static API for frontend to work

## 2.2.3 (2023-11-12)

### Fix

- **tibber_connection**: reworked resubscribe mechanism to handle disconnects better

## 2.2.2 (2023-11-05)

### Fix

- **tibber_connection**: resubscribe if subscription is down fixed

## 2.2.0 (2023-11-04)

### Feat

- **setpoints**: slider contrlols numberr of hours

### Fix

- **logging**: loguru deadlock error fixed

### Refactor

- **vscode**: removed linting settings from json

## 2.1.0 (2023-10-07)

### Feat

- **docker**: added neovim and less to container for easy logs viewing etc

### Fix

- **tibber_connection**: pytibber logs intercept

## 2.0.1 (2023-10-07)

### Fix

- **status-page**: do not show real-time info if power logic is disabled

## 2.0.0 (2023-10-07)

### BREAKING CHANGE

- Since streamlit now performs calls to FastAPI on 172.18.0.1 to get Tibber status, a network should be added to docker-compose.yml to reserve this address ffor cross-container communication. Update your local docker-compose file with the code from the file in the repository.

### Feat

- **app**: add subscription status to frontend
- **streamlit**: added power draw to status page
- **streamlit**: add status page

## 1.0.2 (2023-10-01)

### Fix

- **configuration.py**: enabled default settings file creation at first run

## 1.0.1 (2023-10-01)

### Fix

- **main-and-tibber**: changed functions return types for mypy to pass

## 1.0.0 (2023-10-01)

### Fix

- **pyproject.toml**: major_version_zero set to false

## 0.5.0 (2023-10-01)

### BREAKING CHANGE

- Since new logic switches to new settings file structure, if you are updating an existing docker image, you will have to delete the volume that it depends on, since it still holds the old settings file.

### Feat

- **switch-logic**: prepare for release
- **api-output**: api serves switches json that uses price and power logic

### Fix

- **main**: changed get_price pipline to async

## 0.4.5 (2023-09-11)

### Fix

- **ci**: changed context for nginx docker publish

## 0.4.4 (2023-09-10)

### Fix

- **docker**: dotenv path fix

## 0.4.3 (2023-09-10)

### Fix

- **dockerfiles**: dockerfile paths fixes

## 0.4.2 (2023-09-10)

### Fix

- **gh-actions**: muliplatform build take 2

## 0.4.1 (2023-09-10)

### Fix

- **test-and-publish**: removed muliplatform build

## 0.4.0 (2023-09-10)

### Feat

- **test-and-publish.yml**: added arm and amd builds

### Fix

- **nginx.conf**: nginx config name bug fixed

## 0.3.4 (2023-09-09)

## 0.3.5 (2023-09-09)

### Fix

- **nginx**: path fix for config file

## 0.3.4 (2023-09-09)

### Fix

- **nginx**: path fix for config file
- **nginx**: reverting to custom nginx

## 0.3.3 (2023-09-09)

### Fix

- **docker-compose.yml**: paths fixes

## 0.3.2 (2023-09-09)

### Fix

- **nginx.conf,-docker-compose.yml**: fixing the config presist
- **docker-compose.yml**: fixed the user data presistance

## 0.3.1 (2023-09-09)

### Fix

- **test_and_publish.yml**: fix double run of action

## 0.3.0 (2023-09-09)

### Feat

- **docker-compose.yml**: no need to buld the image locally any more

## 0.2.0 (2023-09-09)

### Feat

- **docker**: added docker volumes for local settings

## 0.1.1 (2023-09-09)

### Fix

- **frontend/dashboard**: fixed slider behaviour

## 0.1.0 (2023-09-03)
Initial release