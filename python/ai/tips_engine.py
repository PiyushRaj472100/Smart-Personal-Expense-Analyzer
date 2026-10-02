import os
import json
import hashlib
from openai import OpenAI

# In-memory cache for fast dashboard reloads
_tips_cache = {}

def generate_tips(income, total_expense, category_data):
    """
    LLM-powered Tips Engine (RAG architecture for structured context).
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return [
            "Set OPENAI_API_KEY in backend/.env to get AI tips.",
            "Try saving 20% of your income for emergencies.",
            "Review your top spending category to cut costs."
        ]

    # Fast path for new accounts (0ms load time instead of 3s)
    if total_expense == 0:
        return [
            "Welcome! Start by adding your first expense.",
            "A good rule of thumb is to save at least 20% of your income.",
            "Set up your recurring bills right away to track them."
        ]

    # Create a unique hash of the current financial state
    state_hash_str = f"{income}_{total_expense}_{json.dumps(category_data, sort_keys=True)}"
    state_hash = hashlib.md5(state_hash_str.encode()).hexdigest()

    # Check cache first for instant load
    if state_hash in _tips_cache:
        return _tips_cache[state_hash]

    client = OpenAI(api_key=api_key)
    monthly_income = (income / 12) if income else 0
    savings = monthly_income - total_expense
    
    context = {
        "monthly_income": round(monthly_income, 2),
        "total_spent_this_month": round(total_expense, 2),
        "money_saved": round(savings, 2),
        "spending_by_category": category_data
    }
    
    system_prompt = """
    You are an expert personal finance advisor. 
    Review the user's monthly spending data and provide exactly 3 short, 
    highly personalized tips to help them save money or manage better.
    Return a JSON object with a 'tips' key containing an array of strings.
    """
    
    user_prompt = f"Data: {json.dumps(context)}"
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        tips = result.get("tips", [])
        
        # Save to cache
        _tips_cache[state_hash] = tips
        return tips
        
    except Exception as e:
        print(f"LLM Tip Engine Error: {e}")
        return ["Track your expenses regularly to identify patterns."]


def generate_analytics_summary(income, transactions, category_data, period):
    """
    Generates a textual summary of the period.
    """
    if not transactions:
        return "No transactions to analyze."
    
    total_expense = sum(t.get("amount", 0) for t in transactions)
    return f"You spent ₹{total_expense:.2f} across {len(transactions)} transactions this {period}."