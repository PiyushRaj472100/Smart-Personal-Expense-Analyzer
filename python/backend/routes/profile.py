from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
from bson import ObjectId
from datetime import datetime
import jwt
import os
from dotenv import load_dotenv

from backend.database import users_col, profiles_col

# ---------------- CONFIG ---------------- #
load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGO = os.getenv("JWT_ALGO", "HS256")

if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET not set in environment")

profile_router = APIRouter()

# ---------------- AUTH DEPENDENCY ---------------- #
def get_current_user(authorization: str = Header(...)):
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise Exception("Invalid auth scheme")
        
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        user = users_col.find_one({"_id": ObjectId(payload["user_id"])})
        
        if not user:
            raise Exception("User not found")
        return user
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# ---------------- SCHEMAS ---------------- #
class ProfileUpdate(BaseModel):
    gender: Optional[str] = None
    company: Optional[str] = None
    annual_income: Optional[float] = None
    family_members: Optional[int] = None
    city: Optional[str] = None
    has_pets: Optional[bool] = None

# ---------------- ROUTES ---------------- #
@profile_router.get("/")
def get_profile(user=Depends(get_current_user)):
    """Get user profile information"""
    profile = profiles_col.find_one({"user_id": str(user["_id"])})
    
    if not profile:
        # Create default profile if doesn't exist
        profile = {
            "user_id": str(user["_id"]),
            "gender": "",
            "company": "",
            "annual_income": user.get("annual_income", 0),
            "family_members": 1,
            "city": "",
            "has_pets": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        profiles_col.insert_one(profile)
    
    profile["_id"] = str(profile["_id"])
    
    # Include user name and email
    profile["name"] = user.get("name", "")
    profile["email"] = user.get("email", "")
    
    return profile

@profile_router.put("/")
def update_profile(data: ProfileUpdate, user=Depends(get_current_user)):
    """Update user profile"""
    update_data = {}
    
    if data.gender is not None:
        update_data["gender"] = data.gender
    if data.company is not None:
        update_data["company"] = data.company
    if data.annual_income is not None:
        update_data["annual_income"] = data.annual_income
        # Also update in users collection
        users_col.update_one(
            {"_id": user["_id"]},
            {"$set": {"annual_income": data.annual_income}}
        )
    if data.family_members is not None:
        update_data["family_members"] = data.family_members
    if data.city is not None:
        update_data["city"] = data.city
    if data.has_pets is not None:
        update_data["has_pets"] = data.has_pets
    
    update_data["updated_at"] = datetime.utcnow()
    
    # Check if profile exists
    existing_profile = profiles_col.find_one({"user_id": str(user["_id"])})
    
    if existing_profile:
        profiles_col.update_one(
            {"user_id": str(user["_id"])},
            {"$set": update_data}
        )
    else:
        update_data["user_id"] = str(user["_id"])
        update_data["created_at"] = datetime.utcnow()
        profiles_col.insert_one(update_data)
    
    return {"message": "Profile updated successfully", "data": update_data}