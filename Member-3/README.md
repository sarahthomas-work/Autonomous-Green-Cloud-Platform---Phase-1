\# Member 3 — AGCP Backend and ML Prediction



\## Overview



This module contributes the FastAPI backend and machine-learning prediction workflow for the Autonomous Green Cloud Platform (AGCP).



\## Responsibilities



\- FastAPI application and API routing.

\- LSTM-based CPU utilization prediction.

\- Model and scaler loading.

\- Live prediction using stored CPU telemetry history.

\- Telemetry and threshold-rule evaluation endpoints.

\- Automation-job response integration.

\- Backend unit and API tests.



\## Project Structure



\- `app/` — API routes, schemas, services, and application entry point.

\- `ml\_models/` — trained LSTM model and fitted scaler.

\- `data/` — sample model data and raw telemetry history.

\- `tests/` — backend tests.

\- `telemetry\_pipeline.py` — telemetry pipeline and polling integration.

\- `requirements.txt` — Python dependencies.

\- `pytest.ini` — pytest configuration.



\## Requirements



\- Python 3.11 is recommended to match the development environment.

\- Install the packages listed in `requirements.txt`.



\## Setup



From this directory, create and activate a virtual environment:



```bash

python -m venv venv

```



Windows CMD:



```cmd

venv\\Scripts\\activate

pip install -r requirements.txt

```



\## Run the API



Run the following commands from the `Member-3` directory:



```cmd

uvicorn app.main:app --host 127.0.0.1 --port 8001

```



API documentation: `http://127.0.0.1:8001/docs`



\# Member 3 - AGCP Backend and ML Prediction



\## Overview



This module contributes the FastAPI backend, telemetry integration, LSTM-based CPU prediction, threshold-rule evaluation, and backend tests for the Autonomous Green Cloud Platform (AGCP).



\## Responsibilities



\- FastAPI application and API routes

\- LSTM model integration for CPU utilization prediction

\- Model and scaler loading

\- Prediction using the latest 60 CPU utilization values

\- Live prediction using stored telemetry history

\- Telemetry processing and threshold-rule evaluation

\- Automation job response integration

\- Unit and API tests



\## Project Structure



\- `app/` - API routes, schemas, and backend services

\- `ml\_models/` - Trained LSTM model and fitted scaler

\- `data/` - Sample model data and raw telemetry history

\- `tests/` - Backend unit and API tests

\- `telemetry\_pipeline.py` - Telemetry collection and polling integration

\- `requirements.txt` - Python dependencies

\- `pytest.ini` - Pytest configuration



\## Requirements



\- Python 3.11 recommended

\- Python packages listed in `requirements.txt`



\## Installation



Run these commands from the `Member-3` directory:



```cmd

python -m venv venv

venv\\Scripts\\activate

python -m pip install -r requirements.txt

```



\## Run the API



```cmd

uvicorn app.main:app --host 127.0.0.1 --port 8001

```



API documentation: http://127.0.0.1:8001/docs



Health endpoint: http://127.0.0.1:8001/health



\## Prediction Workflow



The prediction service loads the trained LSTM model and scaler from `ml\_models/`. It requires at least 60 CPU utilization values for a one-step prediction.



The live prediction service reads `data/raw\_telemetry.csv`, filters records by the requested node instance, and uses the latest 60 available CPU values.



\## Testing



Run from the `Member-3` directory:



```cmd

python -m pytest -q

```



The copied backend passed 23 tests in the development environment.



\## Integration Notes



\- Live prediction requires telemetry history containing the `instance` and `cpu\_util` columns.

\- The telemetry poller requires a correctly configured Prometheus endpoint.

\- Rule evaluation can create a pending automation job; this does not confirm that a cloud resource was actually scaled.

\- Configure environment-specific settings locally.

\- Never commit passwords, API keys, `.env` files, or virtual environments.



