import os

from dotenv import load_dotenv

load_dotenv()

ENVIRONMENT = os.getenv("ENVIRONMENT", "local").lower()
APP_PORT = os.getenv("APP_PORT", 8000)
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_DEBUG = os.getenv("APP_DEBUG", False)
