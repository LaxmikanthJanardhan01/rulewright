import pandas as pd
from rulewright_core import merchant_key, build_rules, apply_rules

def test_merchant_key_removes_noise():
    assert merchant_key("POS DEBIT COSTCO WHOLESALE #0442") == "COSTCO WHOLESALE"

def test_rules_are_deduplicated():
    rules = build_rules(["COSTCO WHOLESALE", "COSTCO WHOLESALE"], ["Groceries", "Other"])
    assert len(rules) == 1

def test_apply_rules_categorizes():
    df = pd.DataFrame({"description": ["COSTCO WHOLESALE", "UNKNOWN SHOP"], "amount": [-10, -5]})
    rules = [{"pattern": "COSTCO WHOLESALE", "category": "Groceries"}]
    out = apply_rules(df, rules)
    assert out.loc[0, "category"] == "Groceries"
    assert pd.isna(out.loc[1, "category"])
from io import StringIO
from rulewright_core import load_csv


def test_load_csv_standard_columns():
    csv_data = StringIO(
        "date,description,amount\n"
        "2026-10-01,UPI COFFEE,-120\n"
        "2026-10-02,SALARY,25000\n"
    )

    df = load_csv(csv_data)

    assert list(df["description"]) == ["UPI COFFEE", "SALARY"]
    assert list(df["amount"]) == [-120, 25000]


def test_load_csv_separate_debit_credit():
    csv_data = StringIO(
        "Date,Narration,Debit,Credit\n"
        "2026-10-01,UPI COFFEE,120,\n"
        "2026-10-02,SALARY,,25000\n"
    )

    df = load_csv(csv_data)

    assert list(df["amount"]) == [-120, 25000]