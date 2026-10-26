
import streamlit as st
import pandas as pd

from rulewright_core import (
    load_csv,
    merchant_key,
    build_rules,
    apply_rules,
)
from gemini_helper import categorize_transactions


st.set_page_config(page_title="Rulewright", layout="wide")
st.title("Rulewright")
st.caption("Categorize transactions using offline rules or AI suggestions.")

st.info(
    "Use fictional data for demos. Gemini sends transaction descriptions "
    "to an external service. Avoid uploading sensitive financial information."
)

uploaded = st.file_uploader("Upload transaction CSV", type=["csv"])

if uploaded is not None:
    try:
        df = load_csv(uploaded)
    except Exception as exc:
        st.error(f"Could not read CSV: {exc}")
        st.stop()
else:
    st.write("Or use the fictional sample ledger.")
    if st.button("Load sample transactions"):
        st.session_state["use_sample"] = True

    if st.session_state.get("use_sample"):
        try:
            df = load_csv("data/sample_transactions.csv")
        except Exception as exc:
            st.error(f"Could not load sample transactions: {exc}")
            st.stop()
    else:
        st.stop()

if "description" not in df.columns:
    st.error("CSV must contain a description column.")
    st.stop()

# Assign stable row IDs so duplicate descriptions remain separate transactions.
df = df.reset_index(drop=True).copy()
df["_source_row"] = range(len(df))

st.subheader("Transaction preview")
st.dataframe(df.drop(columns=["_source_row"]).head(12), use_container_width=True)
st.write(f"Loaded **{len(df)}** transactions.")

default_categories = (
    "Groceries, Dining, Transport, Shopping, Utilities, "
    "Subscriptions, Healthcare, Income, Other"
)
categories_text = st.text_input("Categories (comma-separated)", default_categories)
categories = list(dict.fromkeys(
    item.strip() for item in categories_text.split(",") if item.strip()
))

if not categories:
    st.warning("Enter at least one category.")
    st.stop()

st.divider()
st.subheader("1. Offline categorization")

if st.button("Build rules (offline demo)", type="primary"):
    keys = [merchant_key(x) for x in df["description"].astype(str)]
    st.session_state["rules"] = build_rules(keys, categories)
    st.session_state["ledger"] = df.copy()
    st.session_state.pop("result", None)

if "rules" in st.session_state:
    rules_df = pd.DataFrame(st.session_state["rules"])
    edited_rules = st.data_editor(
        rules_df,
        num_rows="dynamic",
        use_container_width=True,
        key="rules_editor",
    )

    if st.button("Categorize with offline rules"):
        result = apply_rules(
            st.session_state["ledger"],
            edited_rules.to_dict("records"),
        )
        st.session_state["result"] = result

    if "result" in st.session_state:
        result = st.session_state["result"]
        matched = int(result["category"].notna().sum())

        c1, c2, c3 = st.columns(3)
        c1.metric("Transactions", len(result))
        c2.metric("Categorized", matched)
        c3.metric("Coverage", f"{matched / max(len(result), 1):.1%}")

        st.dataframe(result, use_container_width=True)
        st.download_button(
            "Download categorized CSV",
            result.to_csv(index=False),
            "categorized_transactions.csv",
            "text/csv",
        )
        st.download_button(
            "Download rules JSON",
            edited_rules.to_json(orient="records", indent=2),
            "rules.json",
            "application/json",
        )

st.divider()
st.subheader("2. Gemini AI suggestions")
st.warning(
    "Transaction descriptions are sent to Google Gemini when you request "
    "AI suggestions. Use fictional data for testing."
)

confirm_ai = st.checkbox(
    "I understand that transaction descriptions will be sent to Gemini."
)

if st.button("Suggest categories with Gemini", disabled=not confirm_ai):
    descriptions = df["description"].fillna("").astype(str).tolist()

    if not any(x.strip() for x in descriptions):
        st.warning("No transaction descriptions were found.")
    elif len(descriptions) > 100:
        st.warning("For this demo, process 100 or fewer transactions at a time.")
    else:
        try:
            with st.spinner("Gemini is suggesting categories..."):
                response = categorize_transactions(descriptions, categories)

            suggestions_df = pd.DataFrame(response.get("suggestions", []))

            if suggestions_df.empty:
                st.warning("Gemini returned no suggestions.")
            else:
                if "description" not in suggestions_df.columns:
                    st.error("AI response is missing transaction descriptions.")
                    st.stop()

                if "category" not in suggestions_df.columns:
                    suggestions_df["category"] = (
                        "Other" if "Other" in categories else categories[-1]
                    )

                fallback_category = (
                    "Other" if "Other" in categories else categories[-1]
                )
                suggestions_df["category"] = suggestions_df["category"].where(
                    suggestions_df["category"].isin(categories),
                    fallback_category,
                )

                if "reason" not in suggestions_df.columns:
                    suggestions_df["reason"] = ""

                # Match AI rows to source transactions using description
                # and occurrence number, preserving duplicate transactions.
                source = df.copy()
                source["_match_key"] = (
                    source["description"].fillna("").astype(str)
                    .str.strip().str.casefold()
                )
                source["_occurrence"] = source.groupby(
                    "_match_key", sort=False
                ).cumcount()

                suggestions_df["_match_key"] = (
                    suggestions_df["description"].fillna("").astype(str)
                    .str.strip().str.casefold()
                )
                suggestions_df["_occurrence"] = suggestions_df.groupby(
                    "_match_key", sort=False
                ).cumcount()

                source_fields = ["_match_key", "_occurrence", "_source_row"]
                if "date" in source.columns:
                    source_fields.append("date")
                if "amount" in source.columns:
                    source_fields.append("amount")

                suggestions_df = suggestions_df.merge(
                    source[source_fields],
                    on=["_match_key", "_occurrence"],
                    how="left",
                    validate="one_to_one",
                    suffixes=("", "_source"),
                )

                suggestions_df.drop(
                    columns=["_match_key", "_occurrence"], inplace=True
                )
                suggestions_df["approved"] = False
                st.session_state["ai_review"] = suggestions_df.copy()
                st.success(
                    "Suggestions received. Review the category and amount, "
                    "then approve the transactions you want to export."
                )

        except Exception as exc:
            st.error(f"Gemini request failed: {type(exc).__name__}: {exc}")

if "ai_review" in st.session_state:
    st.subheader("3. Review and approve AI suggestions")

    review_df = st.data_editor(
        st.session_state["ai_review"],
        use_container_width=True,
        num_rows="fixed",
        key="ai_review_editor",
        column_config={
            "category": st.column_config.SelectboxColumn(
                "Category",
                options=categories,
                required=True,
            ),
            "approved": st.column_config.CheckboxColumn(
                "Approved",
                help="Tick only after reviewing the category.",
            ),
            "_source_row": None,
        },
    )

    st.session_state["ai_review"] = review_df.copy()
    approved_df = review_df[
        review_df["approved"].fillna(False).astype(bool)
    ].copy()

    st.write(f"Approved: **{len(approved_df)} / {len(review_df)}** suggestions")

    if not approved_df.empty:
        st.subheader("4. Final approved transaction ledger")

        matched = approved_df[
            approved_df["_source_row"].notna()
        ].copy()

        if len(matched) != len(approved_df):
            st.warning(
                "Some AI suggestions could not be matched to the original "
                "transactions. Review those rows before relying on the export."
            )

        if not matched.empty:
            row_ids = matched["_source_row"].astype(int).tolist()
            final_df = df.iloc[row_ids].copy().reset_index(drop=True)

            final_df["category"] = matched["category"].tolist()
            final_df["approved"] = True

            if "reason" in matched.columns:
                final_df["ai_reason"] = matched["reason"].tolist()

            final_df.drop(columns=["_source_row"], errors="ignore", inplace=True)

            st.write(f"Matched approved transactions: **{len(final_df)}**")
            st.dataframe(final_df, use_container_width=True)

            st.download_button(
                "Download final approved ledger CSV",
                final_df.to_csv(index=False),
                "rulewright_final_approved_ledger.csv",
                "text/csv",
            )
