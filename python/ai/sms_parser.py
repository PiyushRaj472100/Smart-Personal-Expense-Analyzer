import re
from datetime import datetime
from typing import Dict, Optional

# ---------------- REGEX PATTERNS ---------------- #

AMOUNT_PATTERNS = [
    r"(?:INR|Rs\.?|₹)\s*([\d,]+\.?\d*)",
    r"([\d,]+\.?\d*)\s*(?:INR|Rs\.?|₹)"
]

MERCHANT_PATTERNS = [
    r"(?:at|to|paid to|spent at)\s+([A-Za-z0-9 &._-]+)",
    r"merchant\s*[:\-]?\s*([A-Za-z0-9 &._-]+)"
]

DATE_PATTERNS = [
    r"(\d{2}-\d{2}-\d{4})",
    r"(\d{2}/\d{2}/\d{4})"
]

# ---------------- CORE PARSER ---------------- #

def parse_sms(message: str) -> Dict:
    """
    Parse transaction SMS text and extract structured data.

    Returns:
    {
        amount: float | None,
        merchant: str | None,
        date: str | None,
        confidence: float,
        reason: str
    }
    """

    text = message.lower()

    amount = _extract_amount(text)
    merchant = _extract_merchant(text)
    date = _extract_date(text)

    confidence = 0.0
    reasons = []

    if amount is not None:
        confidence += 0.4
        reasons.append("Amount detected")

    if merchant:
        confidence += 0.3
        reasons.append("Merchant detected")

    if date:
        confidence += 0.2
        reasons.append("Date detected")

    if confidence == 0:
        reasons.append("No reliable transaction data found")

    return {
        "amount": amount,
        "merchant": merchant,
        "date": date,
        "confidence": round(min(confidence, 0.95), 2),
        "reason": ", ".join(reasons)
    }

# ---------------- HELPERS ---------------- #

def _extract_amount(text: str) -> Optional[float]:
    for pattern in AMOUNT_PATTERNS:
        match = re.search(pattern, text)
        if match:
            try:
                return float(match.group(1).replace(",", ""))
            except ValueError:
                return None
    return None


def _extract_merchant(text: str) -> Optional[str]:
    for pattern in MERCHANT_PATTERNS:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip().title()
    return None


def _extract_date(text: str) -> Optional[str]:
    for pattern in DATE_PATTERNS:
        match = re.search(pattern, text)
        if match:
            try:
                return datetime.strptime(
                    match.group(1).replace("/", "-"),
                    "%d-%m-%Y"
                ).strftime("%Y-%m-%d")
            except ValueError:
                return None
    return None
