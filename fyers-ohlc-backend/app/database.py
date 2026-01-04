from pymongo import MongoClient
from app.config import settings

# Default to None so other modules can import this file even if Mongo is down
client = None
db = None
ohlc_collection = None
tokens_collection = None

try:
    client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=5000)
    # Force connection
    client.admin.command("ping")

    db = client[settings.DB_NAME]
    ohlc_collection = db["ohlc"]
    tokens_collection = db["tokens"]

    print("✅ MongoDB connected successfully")

except Exception as e:
    # Keep module-level names defined (None) instead of blowing up on import
    print("❌ MongoDB connection failed")
    print(e)


def get_db():
    """
    Get database instance.
    
    Returns the database object for accessing collections.
    """
    if db is None:
        raise Exception("Database not connected. Please check MongoDB connection.")
    return db
