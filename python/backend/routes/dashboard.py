from fastapi import APIRouter, HTTPException, Depends, Header
from datetime import datetime
from bson import ObjectId
import jwt
import os
from dotenv import load_dotenv

from backend.database import users_col, transactions_col, alerts_col
from ai.tips_engine import generate_tips
from ai.anomaly import detect_anomaly_summary

# ---------------- CONFIG ---------------- #
load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGO = os.getenv("JWT_ALGO", "HS256")

if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET not set in environment")

dashboard_router = APIRouter()


def normalize_category(value):
    if isinstance(value, dict):
        return value.get("category") or value.get("name") or "Other"
    if isinstance(value, str) and value.strip():
        return value.strip()
    return "Other"

# ---------------- AUTH ---------------- #
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

# ---------------- ROUTES ---------------- #
@dashboard_router.get("/")
def dashboard(user=Depends(get_current_user)):
    """
    Dashboard overview - matches frontend expectations
    """
    # Income
    annual_income = user.get("annual_income", 0)
    monthly_income = annual_income / 12 if annual_income else 0
    
    # Current month range
    now = datetime.utcnow()
    month_start = now.replace(day=1).strftime("%Y-%m-%d")
    
    # FIXED: Fetch ALL transactions for total expenses (not just current month)
    # This ensures SMS parsed transactions are included regardless of their date
    all_txns = list(transactions_col.find({
        "user_id": str(user["_id"])
    }))
    
    # Calculate total expense from ALL transactions
    total_expense = sum(t["amount"] for t in all_txns)
    
    # Fetch current month transactions for trend analysis
    current_month_txns = [t for t in all_txns if t.get("date", "") >= month_start]
    
    savings = monthly_income - total_expense
    savings_percentage = (savings / monthly_income * 100) if monthly_income > 0 else 0
    
    # Financial Health Score (0-100)
    health_score = calculate_health_score(savings_percentage, total_expense, monthly_income)
    
    # ---------------- CATEGORY BREAKDOWN ---------------- #
    category_data = {}
    for t in all_txns:
        cat = normalize_category(t.get("category"))
        amount = float(t.get("amount", 0) or 0)
        category_data[cat] = category_data.get(cat, 0) + amount
    
    top_categories = [
        {"name": k, "amount": round(v, 2)}
        for k, v in sorted(category_data.items(), key=lambda x: x[1], reverse=True)[:5]
    ]
    
    # ---------------- RECENT TRANSACTIONS ---------------- #
    recent_transactions = list(
        transactions_col.find({"user_id": str(user["_id"])})
        .sort("date", -1)
        .limit(5)
    )
    
    for t in recent_transactions:
        t["_id"] = str(t["_id"])
        t["category"] = normalize_category(t.get("category"))
    
    # ---------------- ALERTS ---------------- #
    recent_alerts = list(
        alerts_col.find({"user_id": str(user["_id"])})
        .sort("created_at", -1)
        .limit(3)
    )
    
    alerts = []
    for alert in recent_alerts:
        alerts.append({
            "type": alert.get("type", "warning"),
            "message": alert.get("message", "")
        })
    
    # ---------------- AI TIPS ---------------- #
    tips = generate_tips(
        income=annual_income,
        total_expense=total_expense,
        category_data=category_data
    )
    
    return {
        "income": round(monthly_income, 2),
        "expenses": round(total_expense, 2),
        "savings": round(savings, 2),
        "savings_percentage": round(savings_percentage, 2),
        "health_score": health_score,
        "top_categories": top_categories,
        "recent_transactions": recent_transactions,
        "alerts": alerts,
        "tips": tips
    }

def calculate_health_score(savings_percentage, total_expense, monthly_income):
    """
    Calculate financial health score (0-100)
    Based on savings rate, spending habits, etc.
    """
    score = 0
    
    # Savings rate (max 50 points)
    if savings_percentage >= 30:
        score += 50
    elif savings_percentage >= 20:
        score += 40
    elif savings_percentage >= 10:
        score += 30
    elif savings_percentage >= 0:
        score += 20
    
    # Spending discipline (max 30 points)
    if monthly_income > 0:
        expense_ratio = (total_expense / monthly_income) * 100
        if expense_ratio <= 50:
            score += 30
        elif expense_ratio <= 70:
            score += 20
        elif expense_ratio <= 90:
            score += 10
    
    # Transaction tracking bonus (max 20 points)
    score += 20  # For using the app
    
    return min(score, 100)