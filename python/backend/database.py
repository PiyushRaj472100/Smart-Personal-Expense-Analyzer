from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load .env from backend directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "smart_expense_analyzer"

if not MONGO_URI:
    raise RuntimeError("MONGO_URI not found in .env")

client_kwargs = {
    "maxPoolSize": 50,
    "minPoolSize": 5,
    "connectTimeoutMS": 8000,
    "socketTimeoutMS": 10000,
    "retryWrites": True,
}

try:
    import certifi
    client_kwargs["tlsCAFile"] = certifi.where()
except ImportError:
    pass

client = MongoClient(MONGO_URI, **client_kwargs)
db = client[DB_NAME]

# Collections
users_col = db["users"]
profiles_col = db["profiles"]
transactions_col = db["transactions"]
alerts_col = db["alerts"]
category_usage_col = db["category_usage"]

# Create background indexes for fast auth lookups
try:
    users_col.create_index("email", unique=True, background=True)
    transactions_col.create_index([("user_id", 1), ("date", -1)], background=True)
except Exception:
    pass
