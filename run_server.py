"""Run the FastAPI app programmatically (useful for local testing).

This script sets a sane default DATABASE_URL (sqlite) when not present
and starts uvicorn in the same interpreter so package imports work as
expected during development.
"""
import os
from uvicorn import Config, Server

# Set default DB for local testing if not provided
os.environ.setdefault("DATABASE_URL", "sqlite:///./health_monitor.db")

def main():
    # Import here so PYTHONPATH is already set to the project directory
    from backend.main import app
    config = Config(app=app, host="127.0.0.1", port=8000, log_level="info")
    server = Server(config=config)
    server.run()

if __name__ == '__main__':
    main()
