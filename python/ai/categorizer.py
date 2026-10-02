from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Load model globally so it's fast on subsequent requests
model = SentenceTransformer('all-MiniLM-L6-v2')

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
category_embeddings = model.encode(category_descriptions)

def categorize_expense_adaptive(text: str) -> dict:
    """Zero-shot semantic categorization using Sentence-Transformers."""
    if not text or len(text.strip()) < 2:
        return {"category": "Other", "confidence": 0.0, "ask_user": True}
        
    transaction_embedding = model.encode([text])
    similarities = cosine_similarity(transaction_embedding, category_embeddings)[0]
    
    best_match_idx = np.argmax(similarities)
    best_score = float(similarities[best_match_idx])
    
    # If the semantic similarity is too low, default to 'Other'
    if best_score < 0.25:
        return {
            "category": "Other",
            "confidence": round(best_score, 2),
            "reason": f"Semantic match too low ({best_score:.2f})",
            "ask_user": True
        }
        
    return {
        "category": category_names[best_match_idx],
        "confidence": round(best_score, 2),
        "reason": f"Semantic similarity match ({best_score:.2f})",
        "ask_user": False
    }

def learn_from_correction(title: str, correct_category: str) -> None:
    """Adaptive learning is less necessary with semantic search, 
    but kept for API compatibility with transactions.py"""
    pass
