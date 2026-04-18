"""
Anomaly Detection - Detect unusual spending patterns
"""

def detect_anomaly(user_income, amount, category):
    """
    Detect if a transaction is anomalous based on income and category
    Returns alert message if anomaly detected, None otherwise
    """
    monthly_income = user_income / 12 if user_income else 0
    
    if monthly_income == 0:
        return None  # Can't detect anomalies without income data
    
    # Define thresholds for different categories (% of monthly income)
    category_thresholds = {
        "Food & Dining": 0.15,        # 15% of monthly income
        "Food & Groceries": 0.15,
        "Transportation": 0.15,
        "Entertainment": 0.10,        # 10% of monthly income
        "Healthcare": 0.20,           # 20% of monthly income
        "Housing": 0.35,              # 35% of monthly income
        "Utilities": 0.10,
        "Shopping": 0.15,
        "Technology": 0.10,
        "Other": 0.10
    }
    
    # Get threshold for this category (default 10%)
    threshold_percentage = category_thresholds.get(category, 0.10)
    threshold_amount = monthly_income * threshold_percentage
    
    # Check if transaction exceeds threshold
    if amount > threshold_amount:
        percentage_of_income = (amount / monthly_income * 100)
        return {
            "message": f"⚠️ High {category} expense detected: ₹{amount:.2f} ({percentage_of_income:.1f}% of monthly income). This is above the typical threshold."
        }
    
    # Check for very large transactions (>50% of monthly income)
    if amount > monthly_income * 0.5:
        return {
            "message": f"🚨 Unusually large transaction: ₹{amount:.2f}. This is more than 50% of your monthly income!"
        }
    
    return None


def detect_anomaly_summary(user_income, transactions):
    """
    Generate a summary of anomalies across multiple transactions
    """
    if not transactions or user_income == 0:
        return "Insufficient data for anomaly detection."
    
    monthly_income = user_income / 12
    anomalies = []
    
    for t in transactions:
        result = detect_anomaly(user_income, t["amount"], t["category"])
        if result:
            anomalies.append({
                "transaction": t["title"],
                "amount": t["amount"],
                "message": result["message"]
            })
    
    if not anomalies:
        return "✅ No unusual spending patterns detected. Your expenses are within normal ranges."
    
    # Summarize anomalies
    summary = f"⚠️ Found {len(anomalies)} unusual transaction(s):\n"
    for i, anomaly in enumerate(anomalies[:3], 1):  # Show top 3
        summary += f"{i}. {anomaly['transaction']}: ${anomaly['amount']:.2f}\n"
    
    return summary