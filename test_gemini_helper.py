
from gemini_helper import categorize_transactions

transactions = [
    "NETFLIX MONTHLY SUBSCRIPTION",
    "SHELL GAS STATION"
]

categories = [
    "Groceries",
    "Shopping",
    "Dining",
    "Transport",
    "Subscriptions",
    "Utilities",
    "Income",
    "Healthcare",
    "Other"
]

try:
    result = categorize_transactions(transactions, categories)
    print("Gemini response received:")
    for item in result["suggestions"]:
        print(item)
except Exception as exc:
    print(f"Gemini test failed: {type(exc).__name__}: {exc}")
