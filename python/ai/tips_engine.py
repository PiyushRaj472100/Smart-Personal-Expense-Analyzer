"""
AI Tips Engine - Generates personalized financial tips
"""

def generate_tips(income, total_expense, category_data):
    """
    Generate personalized tips based on user's financial data
    """
    tips = []
    
    # Calculate monthly income
    monthly_income = income / 12 if income else 0
    
    if monthly_income == 0:
        tips.append("💰 Set your annual income in your profile to get personalized financial advice!")
        return tips
    
    # Calculate savings rate
    savings = monthly_income - total_expense
    savings_rate = (savings / monthly_income * 100) if monthly_income > 0 else 0
    
    # Tip 1: Savings rate advice
    if savings_rate < 10:
        tips.append("⚠️ Your savings rate is below 10%. Try to save at least 20% of your income for a healthy financial future.")
    elif savings_rate < 20:
        tips.append("📊 You're saving {:.1f}% of your income. Try to increase this to 20-30% for better financial security.".format(savings_rate))
    elif savings_rate >= 30:
        tips.append("🎉 Excellent! You're saving {:.1f}% of your income. Keep up the great work!".format(savings_rate))
    else:
        tips.append("✅ Good job! You're saving {:.1f}% of your income. Consider aiming for 30% or more.".format(savings_rate))
    
    # Tip 2: Category-specific advice
    if category_data:
        # Find highest spending category
        top_category = max(category_data.items(), key=lambda x: x[1])
        category_name, category_amount = top_category
        category_percentage = (category_amount / total_expense * 100) if total_expense > 0 else 0
        
        if category_percentage > 40:
            tips.append(f"🔍 {category_name} accounts for {category_percentage:.0f}% of your expenses. Consider ways to reduce spending in this area.")
        
        # Food & Dining advice
        food_total = category_data.get("Food & Dining", 0) + category_data.get("Food & Groceries", 0)
        if food_total > 0:
            food_percentage = (food_total / monthly_income * 100) if monthly_income > 0 else 0
            if food_percentage > 15:
                tips.append(f"🍽️ Food expenses are {food_percentage:.0f}% of your income. Meal planning and cooking at home can help reduce costs.")
        
        # Transportation advice
        transport = category_data.get("Transportation", 0)
        if transport > 0:
            transport_percentage = (transport / monthly_income * 100) if monthly_income > 0 else 0
            if transport_percentage > 15:
                tips.append(f"🚗 Transportation is {transport_percentage:.0f}% of your income. Consider carpooling or public transport to save money.")
        
        # Entertainment advice
        entertainment = category_data.get("Entertainment", 0)
        if entertainment > 0:
            entertainment_percentage = (entertainment / monthly_income * 100) if monthly_income > 0 else 0
            if entertainment_percentage > 10:
                tips.append(f"🎬 Entertainment spending is {entertainment_percentage:.0f}% of your income. Look for free or low-cost activities.")
    
    # Tip 3: General financial advice
    if total_expense > monthly_income:
        tips.append("⚠️ You're spending more than you earn! Review your expenses and create a budget to avoid debt.")
    elif total_expense < monthly_income * 0.5:
        tips.append("💡 You're living well below your means. Consider investing your extra savings for long-term growth.")
    
    # Tip 4: Emergency fund reminder
    if savings_rate > 0:
        emergency_fund_months = (savings / total_expense) if total_expense > 0 else 0
        if emergency_fund_months < 3:
            tips.append("🏦 Build an emergency fund covering 3-6 months of expenses for financial security.")
    
    # If no tips generated, add default tips
    if len(tips) == 0:
        tips.append("💡 Track your expenses regularly to identify spending patterns and opportunities to save.")
        tips.append("📱 Use the SMS parser feature to quickly log transactions from bank messages.")
        tips.append("📊 Check the Analytics page for detailed insights into your spending habits.")
    
    return tips[:5]  # Return maximum 5 tips


def generate_analytics_summary(income, transactions, category_data, period):
    """
    Generate AI summary for analytics page
    """
    if not transactions:
        return "No transactions to analyze for this period."
    
    monthly_income = income / 12 if income else 0
    total_expense = sum(t["amount"] for t in transactions)
    
    summary = []
    
    # Overall spending summary
    summary.append(f"During the {period} period, you spent ${total_expense:.2f} across {len(transactions)} transactions.")
    
    # Top category
    if category_data:
        top_category = max(category_data.items(), key=lambda x: x[1])
        category_name, category_amount = top_category
        summary.append(f"Your highest spending category was {category_name} at ${category_amount:.2f}.")
    
    # Savings rate
    if monthly_income > 0:
        savings_rate = ((monthly_income - total_expense) / monthly_income * 100)
        if savings_rate > 0:
            summary.append(f"You saved approximately {savings_rate:.1f}% of your income.")
        else:
            summary.append("Consider reducing expenses to increase your savings rate.")
    
    return " ".join(summary)