## 2.0.0 (2023-10-07)

### BREAKING CHANGE

- Since streamlit now performs calls to FastAPI on 172.18.0.1 to get Tibber status, a network should be added to docker-compose.yml to reserve this address ffor cross-container communication. Update your local docker-compose file with the code fromt the file in the repository.

### Feat

- **app**: add subscription status to frontend
- **streamlit**: added power draw to status page
- **streamlit**: add status page

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