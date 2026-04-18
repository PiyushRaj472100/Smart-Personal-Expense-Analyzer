from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import jwt
import re
import os
from bson import ObjectId
from dotenv import load_dotenv

from backend.database import transactions_col, users_col, alerts_col, category_usage_col
from ai.categorizer import categorize_expense_adaptive, learn_from_correction
from ai.anomaly import detect_anomaly

# ---------------- CONFIG ---------------- #
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGO = os.getenv("JWT_ALGO", "HS256")

if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET not set in environment")

transactions_router = APIRouter()


def normalize_category(value):
    if isinstance(value, dict):
        return value.get("category") or value.get("name") or "Other"
    if isinstance(value, str) and value.strip():
        return value.strip()
    return "Other"


def normalize_source(value):
    if isinstance(value, dict):
        return value.get("source") or value.get("name") or "manual"
    if isinstance(value, str) and value.strip():
        return value.strip().lower()
    return "manual"

# ---------------- AUTH ---------------- #
def get_current_user(authorization: str = Header(...)):
    try:
        scheme, token = authorization.split(" ")
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid auth scheme")
        
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        user = users_col.find_one({"_id": ObjectId(payload["user_id"])})
        
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# ---------------- SCHEMAS ---------------- #
class TransactionCreate(BaseModel):
    title: str
    amount: float
    date: str
    category: Optional[str] = None
    source: str = "manual"  # cash / upi / card / netbanking / manual

class SMSInput(BaseModel):
    message: str

class CategoryFeedback(BaseModel):
    transaction_id: str
    correct_category: str

class CategorySuggestion(BaseModel):
    title: str

# ---------------- HELPERS ---------------- #
def parse_sms(message: str):
    """Parse banking SMS to extract transaction details"""
    amount = None
    merchant = None
    date = None
    
    # Amount extraction
    amt_match = re.search(r"(INR|Rs\.?|₹)\s*([\d,]+\.?\d*)", message, re.IGNORECASE)
    if amt_match:
        amount = float(amt_match.group(2).replace(",", ""))
    
    # Merchant extraction
    merchant_match = re.search(r"(?:at|to)\s+([A-Za-z0-9\s&]+?)(?:\s+on|\s+for|$)", message, re.IGNORECASE)
    if merchant_match:
        merchant = merchant_match.group(1).strip()
    
    # Date extraction
    date_match = re.search(r"(\d{2}[-/]\d{2}[-/]\d{4})", message)
    if date_match:
        try:
            date = datetime.strptime(date_match.group(1), "%d-%m-%Y").strftime("%Y-%m-%d")
        except:
            date = datetime.utcnow().strftime("%Y-%m-%d")
    
    return amount, merchant, date

# ---------------- ROUTES ---------------- #

@transactions_router.get("/")
def get_transactions(user=Depends(get_current_user)):
    """Get all transactions for the current user"""
    txns = list(
        transactions_col.find({"user_id": str(user["_id"])})
        .sort("date", -1)
    )
    
    for t in txns:
        t["_id"] = str(t["_id"])
        t["category"] = normalize_category(t.get("category"))
        t["source"] = normalize_source(t.get("source"))
        t["amount"] = float(t.get("amount", 0) or 0)
        if not t.get("date"):
            t["date"] = datetime.utcnow().strftime("%Y-%m-%d")
    
    return {"transactions": txns}

@transactions_router.post("/add")
def add_transaction(data: TransactionCreate, user=Depends(get_current_user)):
    """Add a new transaction manually"""
    # Categorize if not provided
    if not data.category or data.category == "":
        cat_result = categorize_expense_adaptive(data.title)
        category = cat_result.get("category", "Other")
        ask_user = cat_result.get("ask_user", False)
        suggestions = cat_result.get("suggestions", [])
        confidence = cat_result.get("confidence", 0.5)
        reason = cat_result.get("reason", "")
    else:
        category = data.category
        ask_user = False
        suggestions = []
        confidence = 1.0
        reason = "User provided category"
    
    transaction = {
        "user_id": str(user["_id"]),
        "title": data.title,
        "amount": data.amount,
        "category": category,
        "date": data.date,
        "source": data.source,
        "created_at": datetime.utcnow()
    }
    
    result = transactions_col.insert_one(transaction)
    
    # Check for anomalies
    anomaly_result = detect_anomaly(
        user_income=user.get("annual_income", 0),
        amount=data.amount,
        category=category
    )
    
    anomaly_msg = anomaly_result.get("message") if anomaly_result else None
    
    if anomaly_msg:
        alerts_col.insert_one({
            "user_id": str(user["_id"]),
            "type": "warning",
            "message": anomaly_msg,
            "created_at": datetime.utcnow()
        })
    
    response_data = {
        "message": "Transaction added successfully",
        "transaction_id": str(result.inserted_id),
        "category": category,
        "alert": anomaly_msg
    }
    
    # Add categorization feedback if needed
    if ask_user and confidence < 0.5:
        response_data.update({
            "categorization_feedback": {
                "confidence": confidence,
                "reason": reason,
                "suggestions": suggestions,
                "message": f"I'm not sure about the category for '{data.title}'. I categorized it as '{category}' with {confidence*100:.0f}% confidence. Would you like to change it?"
            }
        })
    
    return response_data

@transactions_router.post("/from-sms")
def add_transaction_from_sms(data: SMSInput, user=Depends(get_current_user)):
    """Parse and add transaction from banking SMS"""
    amount, merchant, date = parse_sms(data.message)
    
    if not amount:
        raise HTTPException(status_code=400, detail="Could not extract amount from SMS")
    
    title = merchant or "Unknown Merchant"
    
    # Categorize automatically
    cat_result = categorize_expense_adaptive(title)
    category = cat_result.get("category", "Other")
    
    transaction = {
        "user_id": str(user["_id"]),
        "title": title,
        "amount": amount,
        "category": category,
        "date": date or datetime.utcnow().strftime("%Y-%m-%d"),
        "source": "sms",
        "created_at": datetime.utcnow()
    }
    
    result = transactions_col.insert_one(transaction)
    
    # Check for anomalies
    anomaly_result = detect_anomaly(
        user_income=user.get("annual_income", 0),
        amount=amount,
        category=category
    )
    
    anomaly_msg = anomaly_result.get("message") if anomaly_result else None
    
    if anomaly_msg:
        alerts_col.insert_one({
            "user_id": str(user["_id"]),
            "type": "warning",
            "message": anomaly_msg,
            "created_at": datetime.utcnow()
        })
    
    return {
        "message": "Transaction added from SMS",
        "transaction_id": str(result.inserted_id),
        "title": title,
        "amount": amount,
        "category": category,
        "date": date or datetime.utcnow().strftime("%Y-%m-%d"),
        "alert": anomaly_msg
    }

@transactions_router.delete("/{transaction_id}")
def delete_transaction(transaction_id: str, user=Depends(get_current_user)):
    """Delete a transaction"""
    result = transactions_col.delete_one({
        "_id": ObjectId(transaction_id),
        "user_id": str(user["_id"])
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return {"message": "Transaction deleted successfully"}

@transactions_router.post("/feedback")
def provide_category_feedback(data: CategoryFeedback, user=Depends(get_current_user)):
    """Provide feedback on categorization to improve future accuracy"""
    # Get the transaction
    transaction = transactions_col.find_one({
        "_id": ObjectId(data.transaction_id),
        "user_id": str(user["_id"])
    })
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Learn from the correction
    learn_from_correction(transaction.get("title", ""), data.correct_category)
    
    # Update the transaction category
    transactions_col.update_one(
        {"_id": ObjectId(data.transaction_id)},
        {"$set": {"category": data.correct_category}}
    )
    
    # Track category usage
    track_category_usage(str(user["_id"]), data.correct_category)
    
    # Check if this is a new custom category (not in predefined categories)
    predefined_categories = ["Food", "Grocery", "Health", "Transport", "Shopping", "Entertainment", "Bills", "Other"]
    is_custom_category = data.correct_category not in predefined_categories
    
    message = "Feedback recorded. Categorization will improve over time."
    if is_custom_category:
        message = f"Custom category '{data.correct_category}' created and learned! The system will recognize this in future."
    
    return {
        "message": message,
        "learned": True,
        "is_custom_category": is_custom_category,
        "category": data.correct_category
    }

def track_category_usage(user_id: str, category: str) -> None:
    """Track category usage frequency for smart dropdown"""
    try:
        # Update or create category usage record
        category_usage_col.update_one(
            {"user_id": user_id, "category": category},
            {"$inc": {"usage_count": 1}, "$set": {"last_used": datetime.now()}},
            upsert=True
        )
    except Exception as e:
        print(f"Error tracking category usage: {e}")

@transactions_router.get("/categories")
def get_categories(user=Depends(get_current_user)):
    """Get all available categories with usage frequency for smart dropdown"""
    # Base predefined categories
    categories = {
        "Food": {
            "description": "Prepared food, snacks, restaurants, beverages",
            "examples": ["chips", "kurkure", "biscuit", "tea", "pizza", "burger", "fried rice", "biryani"]
        },
        "Grocery": {
            "description": "Raw ingredients, groceries, vegetables, fruits, cooking items",
            "examples": ["rice", "vegetables", "fruits", "milk", "flour", "dal", "spices", "groceries"]
        },
        "Health": {
            "description": "Medicines, supplements, gym, fitness, medical expenses",
            "examples": ["whey protein", "medicine", "doctor fees", "gym membership", "vitamins"]
        },
        "Transport": {
            "description": "Travel, fuel, transportation services",
            "examples": ["ola", "uber", "metro", "petrol", "auto rickshaw", "bus tickets"]
        },
        "Shopping": {
            "description": "Clothes, electronics, personal items, retail shopping",
            "examples": ["amazon", "flipkart", "clothes", "shoes", "electronics", "cosmetics"]
        },
        "Entertainment": {
            "description": "Movies, games, streaming services, events",
            "examples": ["netflix", "movie tickets", "spotify", "games", "concert"]
        },
        "Bills": {
            "description": "Utilities, rent, EMIs, subscriptions",
            "examples": ["electricity bill", "phone recharge", "rent", "internet", "loan EMI"]
        },
        "Other": {
            "description": "Expenses that don't fit in other categories",
            "examples": ["miscellaneous", "uncategorized items"]
        }
    }
    
    # Add custom categories from learning system
    try:
        from ai.categorizer import load_learned_keywords
        learned_keywords = load_learned_keywords()
        
        for custom_category, keywords in learned_keywords.items():
            if custom_category not in categories:
                categories[custom_category] = {
                    "description": f"Custom category - learned from user feedback",
                    "examples": keywords[:5] if keywords else ["User-defined category"],
                    "is_custom": True
                }
    except Exception as e:
        # If loading fails, just return predefined categories
        pass
    
    # Get usage statistics
    try:
        user_id = str(user["_id"])
        usage_stats = {}
        
        # Fetch category usage for this user
        usage_records = category_usage_col.find({"user_id": user_id}).sort("usage_count", -1)
        
        for record in usage_records:
            usage_stats[record["category"]] = {
                "usage_count": record.get("usage_count", 0),
                "last_used": record.get("last_used")
            }
        
        # Add usage info to categories
        for category_name in categories:
            if category_name in usage_stats:
                categories[category_name]["usage_count"] = usage_stats[category_name]["usage_count"]
                categories[category_name]["last_used"] = usage_stats[category_name]["last_used"]
            else:
                categories[category_name]["usage_count"] = 0
                categories[category_name]["last_used"] = None
                
    except Exception as e:
        # If usage tracking fails, add default usage counts
        for category_name in categories:
            categories[category_name]["usage_count"] = 0
            categories[category_name]["last_used"] = None
    
    return {"categories": categories}

@transactions_router.post("/suggest-category")
def suggest_category(data: CategorySuggestion, user=Depends(get_current_user)):
    """Get category suggestion for a title"""
    result = categorize_expense_adaptive(data.title)
    
    return {
        "title": data.title,
        "suggested_category": result.get("category"),
        "confidence": result.get("confidence"),
        "reason": result.get("reason"),
        "ask_user": result.get("ask_user", False),
        "suggestions": result.get("suggestions", [])
    }