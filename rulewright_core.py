
import re
import pandas as pd

ALIASES = {
    "description": [
        "description", "merchant", "payee", "details",
        "transaction", "narration", "remarks", "particulars",
        "transaction details", "upi remarks"
    ],
    "date": ["date", "transaction date", "posted date", "value date"],
    "amount": ["amount", "transaction amount", "value"],
    "debit": ["debit", "withdrawal", "withdrawal amount", "dr"],
    "credit": ["credit", "deposit", "deposit amount", "cr"],
}

NOISE = {
    "POS", "DEBIT", "CREDIT", "CARD", "PAYMENT", "PURCHASE",
    "ONLINE", "ACH", "TRANSFER", "REF", "STORE", "USA",
    "INC", "LLC", "CO", "WWW", "COM", "SQ", "SP"
}


def load_csv(file):
    df = pd.read_csv(file)
    lower = {str(c).strip().lower(): c for c in df.columns}

    mapping = {}
    for target, names in ALIASES.items():
        for name in names:
            if name in lower:
                mapping[target] = lower[name]
                break

    if "description" not in mapping:
        raise ValueError(
            "CSV needs a description, merchant, narration, "
            "remarks or particulars column."
        )

    out = pd.DataFrame()
    out["description"] = (
        df[mapping["description"]].fillna("").astype(str).str.strip()
    )

    if "debit" in mapping or "credit" in mapping:
        debit = (
            pd.to_numeric(df[mapping["debit"]], errors="coerce").fillna(0)
            if "debit" in mapping
            else pd.Series(0, index=df.index, dtype=float)
        )
        credit = (
            pd.to_numeric(df[mapping["credit"]], errors="coerce").fillna(0)
            if "credit" in mapping
            else pd.Series(0, index=df.index, dtype=float)
        )
        out["amount"] = credit - debit
    elif "amount" in mapping:
        out["amount"] = pd.to_numeric(
            df[mapping["amount"]], errors="coerce"
        )
    else:
        out["amount"] = float("nan")

    if "date" in mapping:
        out["date"] = df[mapping["date"]]

    return out[out["description"].ne("")].reset_index(drop=True)


def merchant_key(description):
    tokens = re.findall(r"[A-Za-z0-9]+", str(description).upper())
    tokens = [
        token for token in tokens
        if token not in NOISE and not token.isdigit() and len(token) > 1
    ]
    return " ".join(tokens[:3])


def sample_rules(keys, categories):
    return build_rules(keys, categories)


def build_rules(keys, categories):
    rules = []
    seen = set()

    lookup = {
        "COSTCO": "Groceries",
        "WALMART": "Shopping",
        "KROGER": "Groceries",
        "WHOLEFOODS": "Groceries",
        "TRADER": "Groceries",
        "DOORDASH": "Dining",
        "UBER": "Transport",
        "LYFT": "Transport",
        "CHEVRON": "Transport",
        "SHELL": "Transport",
        "NETFLIX": "Subscriptions",
        "SPOTIFY": "Subscriptions",
        "ELECTRIC": "Utilities",
        "PAYROLL": "Income",
        "PHARMACY": "Healthcare",
        "CVS": "Healthcare",
        "AMAZON": "Shopping",
        "AMZN": "Shopping",
        "COFFEE": "Dining",
        "BLUE": "Dining",
    }

    for key in keys:
        if not key or key in seen:
            continue
        seen.add(key)

        first = key.split()[0]
        proposed = lookup.get(first, "Other")

        if proposed not in categories:
            proposed = categories[-1] if categories else "Other"

        rules.append({
            "pattern": key,
            "category": proposed,
            "reason": "Offline demo heuristic; review before use.",
        })

    return rules


def apply_rules(df, rules):
    result = df.copy()
    categories = []

    for desc in result["description"].astype(str):
        tokens = merchant_key(desc)
        token_set = set(tokens.split())
        found = None

        for rule in rules:
            pattern = str(rule.get("pattern", "")).strip()
            if pattern and set(merchant_key(pattern).split()).issubset(token_set):
                found = rule.get("category")
                break

        categories.append(found)

    result["category"] = categories
    return result
