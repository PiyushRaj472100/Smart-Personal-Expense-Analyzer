from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
import hashlib
import jwt
import os
from dotenv import load_dotenv

from backend.database import users_col, profiles_col

# Load .env correctly
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(os.path.dirname(BASE_DIR), ".env")
load_dotenv(ENV_PATH)


JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGO = os.getenv("JWT_ALGO", "HS256")

if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET missing in .env")

auth_router = APIRouter()

# ------------------ SCHEMAS ------------------

class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    annual_income: float


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ------------------ HELPERS ------------------

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def create_token(user_id: str):
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)


# ------------------ ROUTES ------------------

@auth_router.post("/signup")
def signup(data: SignupRequest):
    try:
        if users_col.find_one({"email": data.email}):
            raise HTTPException(status_code=400, detail="User already exists")

        user = {
            "name": data.name,
            "email": data.email,
            "password": hash_password(data.password),
            "annual_income": data.annual_income,
            "created_at": datetime.utcnow()
        }

        result = users_col.insert_one(user)

        profiles_col.insert_one({
            "user_id": str(result.inserted_id),
            "annual_income": data.annual_income,
            "updated_at": datetime.utcnow()
        })

        return {"message": "User registered successfully"}

    except Exception as e:
        print("SIGNUP ERROR:", e)
        raise HTTPException(status_code=500, detail=str(e))

@auth_router.post("/login")
def login(data: LoginRequest):
    user = users_col.find_one({"email": data.email})

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if user["password"] != hash_password(data.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token(str(user["_id"]))

    return {
        "token": token,
        "user": {
            "name": user["name"],
            "email": user["email"],
            "annual_income": user["annual_income"]
        }
    }
