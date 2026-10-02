from sklearn.ensemble import IsolationForest
import numpy as np

def detect_anomaly(user_income, amount, category, user_historical_transactions=None, family_members=1, has_pets=False):
    """
    Unsupervised ML Anomaly Detection using Isolation Forest.
    """
    # 1. Fallback for new users with little data
    if not user_historical_transactions or len(user_historical_transactions) < 10:
        monthly_income = user_income / 12 if user_income else 0
        
        # Adjust hardcoded threshold based on dependents
        threshold_multiplier = 0.4 + (0.05 * (family_members - 1))
        if has_pets:
            threshold_multiplier += 0.05
        threshold_multiplier = min(threshold_multiplier, 0.7) # Cap at 70%

        if monthly_income and amount > (monthly_income * threshold_multiplier):
            return {"message": f"🚨 High expense detected: ₹{amount:.2f}. This is over {threshold_multiplier*100:.0f}% of your monthly income."}
        return None

    # 2. Extract historical amounts
    historical_amounts = np.array([t.get("amount", 0) for t in user_historical_transactions]).reshape(-1, 1)
    
    # 3. Train Isolation Forest locally
    # contamination=0.05 assumes ~5% of past expenses are outliers
    model = IsolationForest(contamination=0.05, random_state=42)
    model.fit(historical_amounts)
    
    # 4. Predict anomaly
    new_data = np.array([[amount]])
    prediction = model.predict(new_data)
    
    if prediction[0] == -1:
        return {"message": f"⚠️ ML Alert: ₹{amount:.2f} is highly unusual based on your personal spending history!"}
    
    return None

def detect_anomaly_summary(user_income, transactions):
    """Fallback summary function for analytics"""
    return "Check your dashboard for AI anomaly alerts."