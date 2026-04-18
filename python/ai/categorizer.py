from typing import Dict, List, Tuple
import json
import os

# ---------------- CONFIG ---------------- #

CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "Food": [
        "zomato", "swiggy", "restaurant", "food", "pizza", "burger",
        "chips", "biscuit", "bread", "tea", "coffee", "juice",
        "noodles", "chocolate", "ice cream", "cake", "pastry", "sandwich",
        "dosa", "idli", "sambar", "curry", "meal", "lunch", "dinner",
        "breakfast", "snacks", "cold drink", "water bottle",
        "kurkure", "lay", "lays", "popcorn", "samosa", "vada", "puff",
        "cookies", "candy", "gums", "mint", "fries", "momos", "spring roll",
        "fried rice", "biryani", "pulao", "pasta", "macaroni", "ready to eat",
        "takeaway", "delivery", "ordered", "cafe", "mess", "canteen"
    ],
    "Grocery": [
        "grocery", "vegetables", "fruits", "meat", "fish", "egg", "rice",
        "flour", "atta", "dal", "lentils", "spices", "oil", "ghee", "butter",
        "sugar", "salt", "onion", "tomato", "potato", "garlic", "ginger",
        "milk", "curd", "yogurt", "cheese", "paneer", "beans", "lentils"
    ],
    "Health": [
        "medicine", "doctor", "hospital", "clinic", "pharmacy", "medical",
        "whey protein", "protein", "supplement", "vitamin", "gym", "fitness",
        "yoga", "health checkup", "dental", "eye", "surgery", "treatment"
    ],
    "Transport": [
        "uber", "ola", "metro", "fuel", "bus", "train", "cab", "taxi",
        "auto", "rickshaw", "petrol", "diesel", "cng", "parking", "toll",
        "flight", "airport", "ticket", "booking"
    ],
    "Shopping": [
        "amazon", "flipkart", "myntra", "shopping", "store", "mall",
        "clothes", "shirt", "pants", "shoes", "electronics", "mobile",
        "laptop", "watch", "bag", "cosmetics", "perfume", "jewelry"
    ],
    "Entertainment": [
        "netflix", "spotify", "movie", "cinema", "prime", "hotstar",
        "youtube", "games", "gaming", "concert", "event", "theatre"
    ],
    "Bills": [
        "electricity", "water", "gas", "rent", "recharge", "phone",
        "internet", "wifi", "mobile bill", "credit card", "loan", "emi",
        "insurance", "tax", "maintenance", "society"
    ]
}

DEFAULT_CATEGORY = "Other"

# ---------------- CORE LOGIC ---------------- #

def categorize_expense(text: str) -> Dict:
    """
    Categorize expense text using enhanced rule-based NLP.
    Returns category, confidence, and explanation.
    """

    text_lower = text.lower()
    scores: Dict[str, int] = {}
    matched_keywords: Dict[str, List[str]] = {}

    # Count keyword matches per category with partial matching
    for category, keywords in CATEGORY_KEYWORDS.items():
        matches = []
        for kw in keywords:
            # Exact match
            if kw in text_lower:
                matches.append(kw)
            # Partial word matching for better detection
            elif any(word in text_lower.split() for word in kw.split() if len(word) > 2):
                if kw not in matches:
                    matches.append(kw)
        
        if matches:
            # Prioritize exact matches and longer phrases
            exact_matches = sum(1 for kw in matches if kw in text_lower)
            score = len(matches) + (exact_matches * 0.5)
            
            # Special handling for Food vs Grocery
            if category == "Grocery" and "Food" in scores:
                # If it's a prepared food item, prioritize Food over Grocery
                food_keywords = ["fried", "cooked", "prepared", "ready", "biryani", "pulao", "fried rice"]
                if any(kw in text_lower for kw in food_keywords):
                    score *= 0.5  # Reduce grocery score for prepared foods
            
            if category == "Food" and "Grocery" in scores:
                # If it's a raw ingredient, prioritize Grocery over Food
                grocery_keywords = ["raw", "uncooked", "flour", "atta", "dal", "spices"]
                if any(kw in text_lower for kw in grocery_keywords):
                    score *= 0.5  # Reduce food score for raw ingredients
            
            scores[category] = score
            matched_keywords[category] = matches

    # If no keywords matched, try basic pattern matching
    if not scores:
        # Basic pattern detection for common items
        patterns = {
            "Food": ["eat", "food", "meal", "snack", "drink"],
            "Health": ["health", "med", "fit", "protein"],
            "Transport": ["go", "travel", "move", "ride"]
        }
        
        for category, pattern_list in patterns.items():
            for pattern in pattern_list:
                if pattern in text_lower:
                    scores[category] = 1
                    matched_keywords[category] = [f"pattern: {pattern}"]
                    break

    # If still no matches, try to suggest categories based on common patterns
    if not scores:
        # Try to identify patterns and suggest categories
        suggestions = []
        
        # Check for gym/fitness related terms
        if any(word in text_lower for word in ["gym", "workout", "exercise", "training"]):
            suggestions.append("Health")
        
        # Check for food patterns
        if any(word in text_lower for word in ["eat", "drink", "meal", "taste"]):
            suggestions.append("Food")
        
        # Check for transport patterns  
        if any(word in text_lower for word in ["go", "travel", "move", "ride", "trip"]):
            suggestions.append("Transport")
        
        if suggestions:
            return {
                "category": suggestions[0],  # Use first suggestion
                "confidence": 0.35,
                "reason": f"Suggested based on patterns: {', '.join(suggestions)}",
                "suggestions": suggestions,
                "ask_user": True
            }
        
        return {
            "category": DEFAULT_CATEGORY,
            "confidence": 0.25,
            "reason": "No matching keywords found",
            "ask_user": True
        }

    # Pick category with highest score
    best_category = max(scores, key=scores.get)
    best_score = scores[best_category]

    # Enhanced confidence calculation
    total_keywords = len(CATEGORY_KEYWORDS[best_category])
    base_confidence = 0.5
    score_confidence = best_score / max(total_keywords, 1)
    confidence = min(0.95, base_confidence + (score_confidence * 0.4))

    # Boost confidence for exact matches
    exact_matches = sum(1 for kw in matched_keywords[best_category] if kw in text_lower)
    if exact_matches > 0:
        confidence = min(0.95, confidence + 0.1)

    return {
        "category": best_category,
        "confidence": round(confidence, 2),
        "reason": f"Matched keywords: {', '.join(matched_keywords[best_category])}",
        "ask_user": False
    }


# ---------------- ADAPTIVE LEARNING ---------------- #

LEARNING_FILE = "learned_keywords.json"

def load_learned_keywords() -> Dict[str, List[str]]:
    """Load learned keywords from file."""
    if os.path.exists(LEARNING_FILE):
        try:
            with open(LEARNING_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_learned_keywords(learned: Dict[str, List[str]]) -> None:
    """Save learned keywords to file."""
    try:
        with open(LEARNING_FILE, 'w') as f:
            json.dump(learned, f, indent=2)
    except:
        pass

def learn_from_correction(title: str, correct_category: str) -> None:
    """
    Learn from user corrections to improve future categorization.
    """
    # Extract keywords from the title
    keywords = extract_keywords(title)
    
    # Load existing learned keywords
    learned_keywords = load_learned_keywords()
    
    # Add keywords to the correct category
    if correct_category not in learned_keywords:
        learned_keywords[correct_category] = []
    
    # Add new keywords (avoid duplicates)
    for keyword in keywords:
        if keyword not in learned_keywords[correct_category]:
            learned_keywords[correct_category].append(keyword)
    
    # AI-powered keyword expansion for new categories
    expanded_keywords = expand_category_keywords(correct_category, keywords)
    for keyword in expanded_keywords:
        if keyword not in learned_keywords[correct_category]:
            learned_keywords[correct_category].append(keyword)
    
    # Save updated keywords
    save_learned_keywords(learned_keywords)
    
    print(f"Learned {len(keywords)} keywords + {len(expanded_keywords)} expanded keywords for category '{correct_category}'")

def extract_keywords(text: str) -> List[str]:
    """
    Extract keywords from the given text.
    """
    words = text.lower().split()
    keywords = []
    
    for word in words:
        if len(word) > 2 and word not in ["the", "and", "for", "with", "from"]:
            keywords.append(word)
    
    return keywords

def expand_category_keywords(category: str, initial_keywords: List[str]) -> List[str]:
    """
    AI-powered keyword expansion based on category and initial keywords.
    """
    # Category-specific keyword expansion rules
    category_expansions = {
        "Sports": ["bat", "ball", "football", "cricket", "tennis", "basketball", "hockey", "golf", "sport", "game", "match", "tournament", "player", "team", "equipment", "gear", "bowl", "wicket", "stadium", "coach", "training"],
        "Gadgets": ["phone", "mobile", "laptop", "computer", "tablet", "headphone", "speaker", "charger", "cable", "mouse", "keyboard", "monitor", "camera", "gadget", "device", "tech", "electronic"],
        "Stationery": ["pen", "pencil", "notebook", "paper", "book", "file", "folder", "stapler", "clip", "marker", "highlighter", "eraser", "ruler", "glue", "tape", "scissors", "stationery", "office"],
        "Pet Supplies": ["dog", "cat", "pet", "food", "toy", "bed", "collar", "leash", "cage", "aquarium", "fish", "bird", "feed", "treat", "grooming", "vet", "supplies"],
        "Furniture": ["chair", "table", "sofa", "bed", "desk", "shelf", "cabinet", "drawer", "mirror", "lamp", "cushion", "mattress", "wardrobe", "furniture", "home", "decor"],
        "Cosmetics": ["makeup", "lipstick", "foundation", "mascara", "eyeliner", "powder", "cream", "lotion", "perfume", "cosmetic", "beauty", "skincare", "face", "lip", "eye"],
        "Automotive": ["car", "bike", "motorcycle", "tire", "oil", "battery", "brake", "engine", "parts", "accessories", "auto", "vehicle", "repair", "maintenance", "garage"],
        "Clothing": ["shirt", "pants", "dress", "jeans", "t-shirt", "jacket", "coat", "shoes", "sneakers", "boots", "clothing", "apparel", "fashion", "wear", "outfit"],
        "Education": ["course", "book", "tuition", "class", "lesson", "training", "workshop", "seminar", "education", "study", "exam", "certification", "degree", "college", "school"],
        "Travel": ["ticket", "flight", "hotel", "booking", "trip", "vacation", "holiday", "travel", "tour", "cruise", "visa", "passport", "luggage", "resort"],
        "Entertainment": ["movie", "music", "game", "concert", "show", "theater", "streaming", "subscription", "entertainment", "fun", "play", "event", "ticket"]
    }
    
    expanded_keywords = []
    
    # Get category-specific expansions
    if category in category_expansions:
        expanded_keywords.extend(category_expansions[category])
    
    # Add related keywords based on initial keywords
    for keyword in initial_keywords:
        keyword_lower = keyword.lower()
        
        # Sports-related expansions
        if any(sport in keyword_lower for sport in ["bat", "ball", "sport", "game"]):
            expanded_keywords.extend(["cricket", "football", "tennis", "hockey", "basketball", "golf", "match", "tournament", "player", "team", "equipment"])
        
        # Tech-related expansions
        if any(tech in keyword_lower for tech in ["phone", "computer", "electronic", "device"]):
            expanded_keywords.extend(["mobile", "laptop", "tablet", "gadget", "tech", "digital", "smart", "device"])
        
        # Office-related expansions
        if any(office in keyword_lower for office in ["pen", "paper", "book", "file"]):
            expanded_keywords.extend(["stationery", "office", "work", "business", "document", "writing"])
    
    # Remove duplicates and initial keywords
    expanded_keywords = list(set(expanded_keywords) - set(initial_keywords))
    
    return expanded_keywords[:10]  # Limit to 10 most relevant keywords

def categorize_expense_adaptive(text: str) -> Dict:
    """
    Enhanced categorization with adaptive learning.
    """
    # First try standard categorization
    result = categorize_expense(text)
    
    # If confidence is low, try learned keywords
    if result["confidence"] < 0.6:
        learned = load_learned_keywords()
        text_lower = text.lower()
        
        learned_scores = {}
        learned_matches = {}
        
        for category, keywords in learned.items():
            matches = [kw for kw in keywords if kw in text_lower]
            if matches:
                learned_scores[category] = len(matches)
                learned_matches[category] = matches
        
        if learned_scores:
            best_learned = max(learned_scores, key=learned_scores.get)
            # Use learned category if it has better confidence
            learned_confidence = min(0.9, 0.6 + (learned_scores[best_learned] * 0.1))
            if learned_confidence > result["confidence"]:
                result = {
                    "category": best_learned,
                    "confidence": round(learned_confidence, 2),
                    "reason": f"Learned keywords: {', '.join(learned_matches[best_learned])}",
                    "ask_user": False
                }
    
    return result
