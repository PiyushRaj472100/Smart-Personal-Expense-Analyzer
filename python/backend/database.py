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

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# Collections
users_col = db["users"]
profiles_col = db["profiles"]
transactions_col = db["transactions"]
alerts_col = db["alerts"]
category_usage_col = db["category_usage"]
