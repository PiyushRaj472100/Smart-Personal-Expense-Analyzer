from fastapi import APIRouter, HTTPException, Depends, Header, File, UploadFile
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import jwt
import re
import os
import csv
import io
from bson import ObjectId
from dotenv import load_dotenv
from functools import lru_cache

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

@lru_cache(maxsize=128)
def get_cached_user(user_id_str: str):
    return users_col.find_one({"_id": ObjectId(user_id_str)})

# ---------------- AUTH ---------------- #
def get_current_user(authorization: str = Header(...)):
    try:
        scheme, token = authorization.split(" ")
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid auth scheme")
        
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        user = get_cached_user(payload["user_id"])
        
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

class CategoryFeedback(BaseModel):
    transaction_id: str
    correct_category: str

class CategorySuggestion(BaseModel):
    title: str

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
    
    # Fetch historical transactions for anomaly detection
    historical_txns = list(transactions_col.find({"user_id": str(user["_id"])}).sort("date", -1).limit(100))
    
    # Fetch profile for anomaly detection context
    from backend.database import profiles_col
    profile = profiles_col.find_one({"user_id": str(user["_id"])}) or {}
    family_members = profile.get("family_members", 1)
    has_pets = profile.get("has_pets", False)
    annual_income = profile.get("annual_income") or user.get("annual_income", 0)

    # Check for anomalies
    anomaly_result = detect_anomaly(
        user_income=annual_income,
        amount=data.amount,
        category=category,
        user_historical_transactions=historical_txns,
        family_members=family_members,
        has_pets=has_pets
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

def _parse_csv_statement(content_str: str):
    lines = content_str.strip().splitlines()
    if not lines:
        return []

    # 1. Detect header row by looking for date + (amount/debit/description/type/particulars)
    header_idx = 0
    for idx, line in enumerate(lines[:25]): # Search first 25 rows for actual table header
        lower_l = line.lower()
        if 'date' in lower_l and any(k in lower_l for k in ['amount', 'debit', 'desc', 'particular', 'type', 'detail', 'paid to']):
            header_idx = idx
            break

    reader = csv.DictReader(io.StringIO('\n'.join(lines[header_idx:])))
    if not reader.fieldnames:
        return []

    raw_headers = {h.strip().lower(): h for h in reader.fieldnames if h}

    def find_key(candidates):
        for c in candidates:
            # Exact match first
            for h, orig in raw_headers.items():
                if h == c:
                    return orig
            # Substring match (e.g. 'amount (inr)' matches 'amount')
            for h, orig in raw_headers.items():
                if c in h:
                    return orig
        return None

    date_key = find_key(['date', 'txn date', 'transaction date', 'time'])
    title_key = find_key(['paid to', 'payee', 'merchant', 'beneficiary', 'receiver', 'to', 'party name', 'name', 'description', 'particular', 'narration', 'detail', 'remarks', 'title'])
    category_key = find_key(['category', 'tag'])
    debit_key = find_key(['debit amount', 'debit', 'withdrawal', 'expense', 'spent'])
    credit_key = find_key(['credit amount', 'credit', 'deposit', 'income', 'received'])
    amount_key = find_key(['amount', 'txn amount', 'transaction amount', 'paid amount'])
    type_key = find_key(['type', 'payment type', 'txn type', 'dr/cr', 'cr/dr', 'transaction type'])
    status_key = find_key(['status', 'payment status', 'txn status'])

    items = []
    for row in reader:
        # Check status (skip failed/declined/reversed transactions from PhonePe/GPay)
        if status_key and row.get(status_key):
            st = str(row[status_key]).strip().upper()
            if any(bad in st for bad in ['FAIL', 'DECLINE', 'REVERS', 'CANCEL', 'BOUNCE']):
                continue

        # Check credit/deposit (skip income/salary/money received)
        if credit_key and row.get(credit_key):
            try:
                c_clean = re.sub(r'[^\d.]', '', str(row[credit_key]))
                if c_clean and float(c_clean) > 0 and (not debit_key or not row.get(debit_key)):
                    continue
            except ValueError:
                pass

        if type_key and row.get(type_key):
            tp = str(row[type_key]).strip().upper()
            if any(c in tp for c in ['CR', 'CREDIT', 'DEPOSIT', 'REFUND', 'RECEIVED']):
                continue

        # Extract debit amount
        amt = None
        amt_raw = None
        if debit_key and row.get(debit_key):
            amt_raw = row[debit_key]
        elif amount_key and row.get(amount_key):
            amt_raw = row[amount_key]

        if amt_raw:
            clean_num = re.sub(r'[^\d.]', '', str(amt_raw))
            if clean_num:
                try:
                    amt = float(clean_num)
                except ValueError:
                    pass

        if not amt or amt <= 0:
            continue

        # Title extraction: Clean PhonePe/UPI prefix and extract person or merchant name
        raw_title = (row.get(title_key) or 'Expense').strip() if title_key else 'Expense'
        clean_title = re.sub(r'^(money sent to|sent to|transferred to|transfer to|paid to|payment to|spent at|payment for|payment towards|debited for|to)\s+', '', raw_title, flags=re.I).strip()
        clean_title = re.sub(r'\s+(via upi|using phonepe|on phonepe|upi)$', '', clean_title, flags=re.I).strip()
        clean_title = re.sub(r'[/_-]+\s*upi.*$', '', clean_title, flags=re.I).strip()
        final_title = clean_title.title() if clean_title else raw_title
        if len(final_title) > 80:
            final_title = final_title[:80]

        # Date normalization (handle 'DD-MM-YYYY HH:MM:SS' timestamps)
        raw_date = (row.get(date_key) or '').strip() if date_key else ''
        raw_date = raw_date.split()[0] if ' ' in raw_date else raw_date
        date_str = None
        if raw_date:
            for fmt in ('%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%d-%m-%y', '%d/%m/%y', '%d-%b-%Y', '%d %b %Y', '%Y/%m/%d', '%b %d, %Y', '%d %b, %Y'):
                try:
                    date_str = datetime.strptime(raw_date, fmt).strftime('%Y-%m-%d')
                    break
                except ValueError:
                    pass
        if not date_str:
            date_str = datetime.utcnow().strftime('%Y-%m-%d')

        cat = str(row[category_key]).strip() if category_key and row.get(category_key) else None
        items.append({'title': final_title, 'raw_title': raw_title, 'amount': amt, 'date': date_str, 'category': cat})

    return items

def _determine_category(clean_title: str, raw_title: str, amount: float) -> str:
    """Intelligently assign category based on merchant, person name, keywords, or micro-amount without asking."""
    # 1. First check existing adaptive learning engine
    cat_res = categorize_expense_adaptive(clean_title)
    cat = cat_res.get("category")
    if cat and cat != "Other":
        return cat

    combined = f"{clean_title} {raw_title}".lower()

    # 2. Comprehensive keyword matcher
    if any(k in combined for k in [
        'chai', 'tea', 'stall', 'canteen', 'cafe', 'dhaba', 'bhojanalaya', 
        'sweets', 'bakery', 'dairy', 'juice', 'shawarma', 'hotel', 'kitchen', 
        'biryani', 'pan shop', 'paan', 'tiffin', 'mess', 'paratha', 'fast food', 
        'street food', 'snack', 'restaurant', 'burger', 'pizza', 'zomato', 
        'swiggy', 'chaayos', 'haldiram', 'mcdonald', 'kfc', 'domino', 'food'
    ]):
        return 'Food'

    if any(k in combined for k in [
        'supermarket', 'mart', 'kirana', 'provision', 'store', 'bazaar', 
        'zepto', 'blinkit', 'instamart', 'bigbasket', 'vegetable', 'sabji', 
        'mandi', 'milk', 'fruits', 'grocery', 'ration'
    ]):
        return 'Grocery'

    if any(k in combined for k in [
        'rapido', 'uber', 'ola', 'auto', 'rickshaw', 'metro', 'fuel', 
        'petrol', 'diesel', 'hpcl', 'bpcl', 'ioc', 'indian oil', 'toll', 
        'fastag', 'bus', 'train', 'flight', 'taxi', 'irctc', 'redbus', 'transport'
    ]):
        return 'Transport'

    if any(k in combined for k in [
        'recharge', 'airtel', 'jio', 'vi', 'vodafone', 'bsnl', 'bescom', 
        'tneb', 'mseb', 'electricity', 'broadband', 'wifi', 'cylinder', 
        'indane', 'hp gas', 'bharat gas', 'bill', 'rent', 'emi', 'insurance', 'loan'
    ]):
        return 'Bills'

    if any(k in combined for k in [
        'pharmacy', 'medical', 'chemist', 'apollo', 'medplus', '1mg', 
        'netmeds', 'dr.', 'doctor', 'clinic', 'hospital', 'pathology', 
        'lab', 'medicine', 'health', 'gym', 'fitness'
    ]):
        return 'Health'

    if any(k in combined for k in [
        'amazon', 'flipkart', 'myntra', 'meesho', 'ajio', 'nykaa', 'dmart', 
        'trends', 'zudio', 'mall', 'clothes', 'fashion', 'shoes', 'electronics', 'shopping'
    ]):
        return 'Shopping'

    if any(k in combined for k in [
        'netflix', 'spotify', 'prime', 'hotstar', 'youtube', 'movie', 
        'cinema', 'gaming', 'bookmyshow', 'pvr', 'inox', 'entertainment'
    ]):
        return 'Entertainment'

    # 3. Micro-transaction rule: <= 50 Rs to ANY person or vendor QR is Chai/Snacks/Local transit
    if amount and amount <= 50:
        return 'Food'

    # 4. Peer-to-Peer payment to an individual person
    if re.search(r'\b(paid to|sent to|transfer to|transferred to|payment to)\b', raw_title, re.I):
        return 'Transfer'

    return 'Other'

@transactions_router.post("/upload-csv")
async def upload_csv_statement(file: UploadFile = File(...), user=Depends(get_current_user)):
    """Upload and bulk import transactions from bank or expense CSV statement"""
    if not file.filename.lower().endswith((".csv", ".txt")):
        raise HTTPException(status_code=400, detail="Only CSV files (.csv) are supported.")

    contents = await file.read()
    try:
        text = contents.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            text = contents.decode("latin1")
        except Exception:
            raise HTTPException(status_code=400, detail="Could not read CSV file encoding.")

    parsed_items = _parse_csv_statement(text)
    if not parsed_items:
        raise HTTPException(
            status_code=400, 
            detail="No valid debit expenses found in CSV. Please ensure the file has Date, Title/Narration, and Debit/Amount columns."
        )

    transactions_to_insert = []
    total_amount = 0.0
    now = datetime.utcnow()
    user_id_str = str(user["_id"])

    for item in parsed_items:
        category = item.get("category")
        if not category or category.lower() in ("other", "none", ""):
            category = _determine_category(item["title"], item.get("raw_title", ""), item["amount"])

        transactions_to_insert.append({
            "user_id": user_id_str,
            "title": item["title"],
            "amount": item["amount"],
            "category": category,
            "date": item["date"],
            "source": "csv_upload",
            "created_at": now
        })
        total_amount += item["amount"]

    if transactions_to_insert:
        transactions_col.insert_many(transactions_to_insert)

    return {
        "message": f"Successfully imported {len(transactions_to_insert)} transactions!",
        "count": len(transactions_to_insert),
        "total_amount": round(total_amount, 2)
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