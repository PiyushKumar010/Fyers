from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    FYERS_CLIENT_ID = os.getenv("FYERS_CLIENT_ID")
    FYERS_SECRET_KEY = os.getenv("FYERS_SECRET_KEY")
    FYERS_REDIRECT_URI = os.getenv("FYERS_REDIRECT_URI")

    MONGO_URI = os.getenv("MONGO_URI")
    DB_NAME = os.getenv("DB_NAME")
    # Seconds before expiry to attempt refresh (default 60s)
    REFRESH_BUFFER_SECONDS = int(os.getenv("REFRESH_BUFFER_SECONDS", "60"))
    # How often to check when no expiry info is available (default 300s)
    REFRESH_CHECK_INTERVAL = int(os.getenv("REFRESH_CHECK_INTERVAL", "300"))
    # Optionally disable background token refresher for debugging
    DISABLE_TOKEN_REFRESHER = os.getenv("DISABLE_TOKEN_REFRESHER", "false").lower() in ("1", "true", "yes")
    
    # Disable storing live market data in MongoDB (default: True - don't store live data)
    DISABLE_LIVE_DATA_STORAGE = os.getenv("DISABLE_LIVE_DATA_STORAGE", "true").lower() in ("1", "true", "yes")
    
    # Number of days to consider as "live" data (data within this many days won't be stored)
    LIVE_DATA_THRESHOLD_DAYS = int(os.getenv("LIVE_DATA_THRESHOLD_DAYS", "1"))

settings = Settings()
