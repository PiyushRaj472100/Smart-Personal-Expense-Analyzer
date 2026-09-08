import re
from datetime import datetime
from typing import Dict, Optional

# ---------------- CONFIG ---------------- #

NOISE_WORDS = {
    'ref', 'bal', 'balance', 'avail', 'avl', 'acct', 'account', 'a/c', 
    'dr', 'cr', 'via', 'bank', 'upi', 'transfer', 'user', 'customer', 
    'card', 'inr', 'rs', 'rs.', 'info', 'txn', 'transaction'
}

STOP_WORDS = r'(?:\s+(?:on|via|using|with|ref|bal|balance|avl|avail|a/c|acct|ending|dr|cr|\.|$))'

DATE_PATTERNS = [
    (r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{4})\b', ['%d-%m-%Y', '%d/%m/%Y']),
    (r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{2})\b', ['%d-%m-%y', '%d/%m/%y']),
    (r'\b(\d{1,2}[-\s][A-Za-z]{3}[-\s]\d{2,4})\b', ['%d-%b-%y', '%d-%b-%Y', '%d %b %y', '%d %b %Y'])
]


def _clean_merchant(raw: str) -> Optional[str]:
    """Clean merchant string by removing noise words, bank codes, and punctuation."""
    if not raw:
        return None
    raw = re.sub(r'[/_.-]+$', '', raw).strip()
    words = [w for w in raw.split() if w.lower() not in NOISE_WORDS and not w.isdigit()]
    cleaned = ' '.join(words).strip(' /-_.')
    if len(cleaned) < 2 or cleaned.lower() in NOISE_WORDS:
        return None
    return cleaned.title()


# ---------------- CORE PARSER ---------------- #

def parse_sms(message: str) -> Dict:
    """
    Parse transaction SMS text and extract structured data.
    Works with Indian bank and UPI formats (SBI, HDFC, ICICI, Axis, Paytm, etc.).
    Handles vague micro-transactions (e.g. ₹20 UPI transfers without merchant).
    """
    text = message.strip()
    lower = text.lower()

    # 1. Detect Credit vs Debit
    is_credit = bool(re.search(r'\b(credited|credit|received|refund|deposited)\b', lower))
    is_debit = bool(re.search(r'\b(debited|debit|spent|paid|sent|withdrawn|dr)\b', lower))

    if is_credit and not is_debit:
        return {
            "amount": None,
            "merchant": None,
            "title": "Income",
            "category": None,
            "date": None,
            "is_credit": True,
            "needs_review": False,
            "confidence": 0.0,
            "reason": "Income/credit SMS detected (not an expense debit)"
        }

    # 2. Extract Amount
    amount = None
    amt_match = (
        re.search(r'(?:inr|rs\.?|₹)\s*([\d,]+\.?\d*)', text, re.I) or
        re.search(r'([\d,]+\.?\d*)\s*(?:inr|rs\.?|₹)', text, re.I) or
        re.search(r'debited\s+(?:by|with)?\s*([\d,]+\.?\d*)', text, re.I)
    )
    if amt_match:
        try:
            amount = float(amt_match.group(1).replace(',', ''))
        except ValueError:
            amount = None

    # 3. Extract Merchant / Payee
    merchant = None
    merchant_patterns = [
        # UPI slash format: UPI/DR/123456/MERCHANT NAME/...
        r'upi/(?:dr/)?(?:\d+/)?([^/]+?)(?:/|ref|bal|$)',
        # Standard: paid to X, spent at X, towards X, transfer to X
        r'(?:paid to|spent at|towards|transfer to|to|at)\s+([a-z0-9 &._@-]+?)(?:' + STOP_WORDS + r'|$)',
        r'merchant\s*[:\-]?\s*([a-z0-9 &._-]+)'
    ]
    for pattern in merchant_patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            candidate = _clean_merchant(m.group(1))
            if candidate:
                merchant = candidate
                break

    # 4. Extract Date
    date = None
    for pattern, fmts in DATE_PATTERNS:
        m = re.search(pattern, text)
        if m:
            raw_date = m.group(1).strip()
            for fmt in fmts:
                try:
                    date = datetime.strptime(raw_date, fmt).strftime('%Y-%m-%d')
                    break
                except ValueError:
                    pass
            if date:
                break

    # 5. Handle Unknown Merchant & Micro-transactions (e.g. ₹20 without merchant)
    needs_review = False
    suggested_title = merchant
    suggested_category = None
    confidence = 0.5 if amount else 0.0

    if not merchant:
        needs_review = True
        if amount and amount <= 50:
            # Overwhelmingly chai / street food / local travel
            suggested_title = "Chai / Snacks"
            suggested_category = "Food"
            reason = f"Rs.{amount:g} micro-expense with no merchant; auto-assigned to Food (Chai/Snacks)."
        else:
            suggested_title = "UPI Payment"
            suggested_category = "Other"
            reason = "No merchant found in SMS. Defaulted to UPI Payment."
    else:
        confidence += 0.4
        reason = f"Merchant identified: {merchant}"

    if date:
        confidence += 0.1

    return {
        "amount": amount,
        "merchant": merchant,
        "title": suggested_title or "Expense",
        "category": suggested_category,
        "date": date,
        "is_credit": False,
        "needs_review": needs_review,
        "confidence": round(min(confidence, 0.95), 2),
        "reason": reason
    }
