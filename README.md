# health_monitor (starter)

Project scaffold for a health monitoring system with the following structure:

- backend/: FastAPI app and DB models
- ml/: LSTM training and inference stubs
- simulator/: simple script to simulate ESP8266 sensor data and POST to backend
- frontend/: React starter app (Day 4)
- esp32/: placeholder Arduino firmware

Quick start (macOS / zsh):

1. Activate the venv:

   source health_monitor/.venv/bin/activate

2. Install minimal dependencies:

   pip install -r health_monitor/requirements.txt

3. Run backend (example):

   uvicorn backend.main:app --reload --port 8000

4. Run simulator to send fake data:

   python health_monitor/simulator/simulate.py --url http://localhost:8000/ingest --delay 2 --count 10

Notes:
- This is a starter scaffold. Fill in model training, database credentials, and production configuration as needed.
