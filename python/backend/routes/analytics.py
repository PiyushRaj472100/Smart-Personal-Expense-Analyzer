from fastapi import APIRouter, HTTPException, Query, Depends, Header
from datetime import datetime, timedelta
from bson import ObjectId
import jwt
from collections import defaultdict
import os
from dotenv import load_dotenv

from backend.database import users_col, transactions_col
from ai.tips_engine import generate_analytics_summary

# ---------------- CONFIG ---------------- #

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGO = os.getenv("JWT_ALGO", "HS256")

if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET not set in environment")

analytics_router = APIRouter()


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

# ---------------- HELPERS ---------------- #

def get_date_range(period: str):
    now = datetime.utcnow()

    if period == "weekly":
        return now - timedelta(days=7)
    elif period == "yearly":
        return now - timedelta(days=365)
    else:  # monthly
        return now.replace(day=1)

# ---------------- ROUTE ---------------- #

@analytics_router.get("/")
def analytics(
    period: str = Query("monthly", enum=["weekly", "monthly", "yearly"]),
    user=Depends(get_current_user)
):
    """
    Analytics endpoint:
    - category analysis
    - time trends
    - source analysis
    - AI summary
    """

    start_date = get_date_range(period).strftime("%Y-%m-%d")

    txns = list(transactions_col.find({
        "user_id": str(user["_id"]),
        "date": {"$gte": start_date}
    }))

    if not txns:
        return {
            "message": "No transactions found for this period",
            "data": {}
        }

    # ---------------- CATEGORY ANALYSIS ---------------- #
    category_totals = defaultdict(float)
    for t in txns:
        category = normalize_category(t.get("category"))
        amount = float(t.get("amount", 0) or 0)
        category_totals[category] += amount

    category_analysis = [
        {"category": k, "amount": v}
        for k, v in category_totals.items()
    ]

    # ---------------- SOURCE ANALYSIS ---------------- #
    source_totals = defaultdict(float)
    for t in txns:
        source = normalize_source(t.get("source"))
        amount = float(t.get("amount", 0) or 0)
        source_totals[source] += amount

    source_analysis = [
        {"source": k, "amount": v}
        for k, v in source_totals.items()
    ]

    # ---------------- TIME TREND ---------------- #
    time_trend = defaultdict(float)
    for t in txns:
        date_key = t.get("date") or datetime.utcnow().strftime("%Y-%m-%d")
        amount = float(t.get("amount", 0) or 0)
        time_trend[date_key] += amount

    time_trend_data = [
        {"date": k, "amount": v}
        for k, v in sorted(time_trend.items())
    ]

    # ---------------- AI SUMMARY ---------------- #
    summary = generate_analytics_summary(
        income=user["annual_income"],
        transactions=txns,
        category_data=category_totals,
        period=period
    )

    return {
        "period": period,
        "category_analysis": category_analysis,
        "source_analysis": source_analysis,
        "time_trend": time_trend_data,
        "ai_summary": summary
    }
