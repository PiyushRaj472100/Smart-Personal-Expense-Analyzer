import os
import json
import numpy as np
from openai import OpenAI
from backend.database import db

# LEVEL 1 & 4: Exact Match Database
category_rules_col = db["category_rules"]

# LEVEL 2: Semantic Model (Using OpenAI API to save RAM instead of local PyTorch)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) if os.getenv("OPENAI_API_KEY") else None

def get_embedding(text):
    if not client: return [0]*1536
    response = client.embeddings.create(input=[text], model="text-embedding-3-small")
    return response.data[0].embedding

def cosine_sim(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)) if np.linalg.norm(a) and np.linalg.norm(b) else 0.0

CATEGORIES = {
    "Food": "Restaurant, dining, fast food, coffee shop, swiggy, zomato, cafe, street food, snacks",
    "Grocery": "Supermarket, vegetables, daily needs, milk, kirana, instamart, blinkit, raw ingredients",
    "Transport": "Uber, ola, taxi, bus, train, flight, metro, fuel, petrol, transit",
    "Health": "Hospital, pharmacy, doctor, medicine, clinic, medical, fitness, gym",
    "Shopping": "Amazon, flipkart, clothes, electronics, mall, retail, shoes, apparel, smartphone, phone, mobile, gadgets",
    "Entertainment": "Netflix, movies, cinema, gaming, subscription, spotify, concert",
    "Bills": "Electricity, water bill, recharge, broadband, rent, emi, insurance",
    "Transfer": "Sent to, paid to, transferred, upi payment to person",
}

category_names = list(CATEGORIES.keys())
category_descriptions = list(CATEGORIES.values())

# Lazily cache embeddings so we don't spam the API unless needed
_category_embeddings = None

def get_category_embeddings():
    global _category_embeddings
    if _category_embeddings is None:
        _category_embeddings = [get_embedding(desc) for desc in category_descriptions]
    return _category_embeddings

def categorize_expense_adaptive(text: str) -> dict:
    """Hybrid Categorization Engine (Exact Match -> Semantic -> LLM)"""
    text_clean = text.strip().lower()
    if not text_clean or len(text_clean) < 2:
        return {"category": "Other", "confidence": 0.0, "ask_user": True}

    # LEVEL 1: Exact Match (Fastest & 100% Accurate)
    rule = category_rules_col.find_one({"keyword": text_clean})
    if rule:
        return {
            "category": rule["category"],
            "confidence": 1.0,
            "reason": "Exact match from past learning",
            "ask_user": False
        }

    # LEVEL 2: Semantic Search (OpenAI Embeddings)
    if client:
        transaction_embedding = get_embedding(text)
        cat_embs = get_category_embeddings()
        similarities = [cosine_sim(transaction_embedding, ce) for ce in cat_embs]
        
        best_match_idx = np.argmax(similarities)
        best_score = float(similarities[best_match_idx])
        
        # OpenAI embeddings generally have higher baseline similarity, adjust threshold to ~0.4
        if best_score >= 0.40:
            return {
                "category": category_names[best_match_idx],
                "confidence": round(best_score, 2),
                "reason": f"Semantic match ({best_score:.2f})",
                "ask_user": False
            }

    # LEVEL 3: LLM Reasoning (For complex/ambiguous context)
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        try:
            client = OpenAI(api_key=api_key)
            prompt = f"Categorize the transaction '{text}' into exactly one of these: {', '.join(category_names)}, or 'Other'. Return JSON with key 'category'."
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            result = json.loads(response.choices[0].message.content)
            cat = result.get("category", "Other")
            if cat in category_names:
                return {
                    "category": cat,
                    "confidence": 0.9,
                    "reason": "LLM reasoned categorization",
                    "ask_user": False
                }
        except Exception as e:
            print("LLM Categorization failed:", e)

    # Fallback to Other if all levels fail
    return {
        "category": "Other",
        "confidence": 0.0,
        "reason": f"No strong match found",
        "ask_user": True
    }

def learn_from_correction(text: str, correct_category: str) -> None:
    """LEVEL 4: Active Learning Loop (Saves corrections to Level 1 DB)"""
    text_clean = text.strip().lower()
    if text_clean and correct_category in category_names:
        category_rules_col.update_one(
            {"keyword": text_clean},
            {"$set": {"category": correct_category}},
            upsert=True
        )

def load_learned_keywords() -> dict:
    """Returns learned keywords grouped by category"""
    rules = category_rules_col.find({})
    res = {}
    for r in rules:
        cat = r["category"]
        if cat not in res:
            res[cat] = []
        res[cat].append(r["keyword"])
    return res
