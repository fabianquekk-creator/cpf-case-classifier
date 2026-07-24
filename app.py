import streamlit as st
import pandas as pd
import re
from datetime import datetime

# ── keyword lists ──────────────────────────────────────────────────────────────

WITHIN_30_DAYS_KEYWORDS = [
    "intention to withdraw", "intended to withdraw", "meant to withdraw",
    "wanted to withdraw", "wish to withdraw", "wrongly transferred instead of",
    "made a mistake", "made an error", "did by mistake", "wrongly transferred",
    "wrongly did", "error of transferring", "accidentally transferred",
    "transfer back to my oa", "reverse back to oa", "cancel transaction",
    "cancel the wrong transaction", "not his intention", "not my intention",
    "did not know", "did not realise", "did not realize",
    "realised the mistake", "realized the mistake"
]

UNAUTHORISED_KEYWORDS = [
    "did not do", "did not perform", "did not authorise", "did not authorize",
    "did not instruct", "without my permission", "without my knowledge",
    "unauthorised", "unauthorized", "illegal transfer", "not my instruction",
    "i did not", "i never", "scammed", "scam", "police report", "unlicensed money lender",
    "third party", "someone else", "not aware", "no knowledge of",
    "did not approve", "i was not aware"
]

CHANGE_OF_SCHEME_KEYWORDS = [
    "wrong account", "wrong scheme", "wrongly selected", "mistakenly selected",
    "intended to top up", "meant to top up", "top up to wrong", "topped up wrongly",
    "wrongly top up", "wrongly top-up", "wrongly topped up", "wrong option", "clicked by accident",
    "accidentally top up", "accidentally topped up", "transfer to wrong",
    "wrong account type", "sa instead of ma", "oa instead of sa", "ra instead of ma",
    "ma instead of ra", "medisave instead", "instead of medisave",
    "rstu", "retirement sum topping", "voluntary contribution", "vc instead",
    "mrss", "careshield", "care shield", "reallocate", "reallocation",
    "redistribute", "split into", "3 accounts", "three accounts"
]

TAX_RELIEF_KEYWORDS = [
    "tax relief", "iras", "notice of assessment", "noa",
    "year of assessment", "backdated", "backdate", "tax purpose",
    "income tax", "tax assessment", "tax record", "transmit to iras",
    "qualify for tax", "tax deadline", "31 dec", "31st dec",
    "previous year", "2024 top-up", "2025 top-up", "tax benefit"
]

# ── date extraction ────────────────────────────────────────────────────────────

MONTH_MAP = {
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
    'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
}

def extract_transaction_dates(text, opened_date):
    if not isinstance(text, str):
        return []
    text_lower = text.lower()
    dates_found = []
    reference_year = opened_date.year if opened_date else datetime.now().year

    for match in re.finditer(r'\b(\d{1,2})[\/\-](\d{1,2})(?:[\/\-](\d{2,4}))?\b', text):
        day, month, year = match.group(1), match.group(2), match.group(3)
        try:
            day, month = int(day), int(month)
            if not (1 <= day <= 31 and 1 <= month <= 12):
                continue
            if year:
                year = int(year)
                if year < 100:
                    year += 2000
            else:
                year = reference_year
            dates_found.append(datetime(year, month, day))
        except ValueError:
            continue

    for match in re.finditer(
        r'\b(\d{1,2})\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+(\d{4})\b',
        text_lower
    ):
        try:
            day = int(match.group(1))
            month = MONTH_MAP[match.group(2)[:3]]
            year = int(match.group(3))
            dates_found.append(datetime(year, month, day))
        except ValueError:
            continue

    for match in re.finditer(
        r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+(\d{1,2}),?\s+(\d{4})\b',
        text_lower
    ):
        try:
            month = MONTH_MAP[match.group(1)[:3]]
            day = int(match.group(2))
            year = int(match.group(3))
            dates_found.append(datetime(year, month, day))
        except ValueError:
            continue

    for match in re.finditer(
        r'\b(\d{1,2})\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b',
        text_lower
    ):
        try:
            day = int(match.group(1))
            month = MONTH_MAP[match.group(2)[:3]]
            dates_found.append(datetime(reference_year, month, day))
        except ValueError:
            continue

    return dates_found


def is_within_30_days(text, opened_date):
    if not opened_date:
        return False
    dates = extract_transaction_dates(text, opened_date)
    for d in dates:
        delta = abs((opened_date - d).days)
        if delta <= 30:
            return True
    return False


def matches_keywords(text, keywords):
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in keywords)


def parse_opened_date(date_str):
    if not isinstance(date_str, str):
        return None
    try:
        return datetime.strptime(date_str.strip(), "%d/%m/%Y, %I:%M %p")
    except ValueError:
        pass
    try:
        return datetime.strptime(date_str.strip(), "%d/%m/%Y, %I:%M%p")
    except ValueError:
        pass
    return None


def classify_case(case_details, date_time_opened):
    opened_date = parse_opened_date(str(date_time_opened))
    text = str(case_details) if isinstance(case_details, str) else ""

    if opened_date:
        if is_within_30_days(text, opened_date) or matches_keywords(text, WITHIN_30_DAYS_KEYWORDS):
            return "Within 30 Days"

    if matches_keywords(text, UNAUTHORISED_KEYWORDS):
        return "Unauthorised Transfer"

    if matches_keywords(text, CHANGE_OF_SCHEME_KEYWORDS):
        return "Change of Scheme"

    if matches_keywords(text, TAX_RELIEF_KEYWORDS):
        return "Tax Relief"

    return "Others"

# ── streamlit app ──────────────────────────────────────────────────────────────

st.set_page_config(page_title="Case Classifier", layout="wide")
st.title("CPF Case Classifier")

# ── password protection ────────────────────────────────────────────────────────
password = st.text_input("Enter password to access the app", type="password")
if password != "fabian2026":
    st.warning("Please enter the correct password to continue.")
    st.stop()

# ── important notice ───────────────────────────────────────────────────────────

st.warning("""
**IMPORTANT NOTICE:** This web application is developed as a proof-of-concept prototype.
The information provided here is NOT intended for actual usage and should not be relied upon
for making any decisions, especially those related to financial, legal, or healthcare matters.

Furthermore, please be aware that the LLM may generate inaccurate or incorrect information.
You assume full responsibility for how you use any generated output.

Always consult with qualified professionals for accurate and personalised advice.
""")

DETAILS_COLUMN = "Case Details"
DATE_COLUMN = "Date/Time Opened"

uploaded_file = st.file_uploader("Upload your CSV file", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file, encoding='latin-1')
    st.success(f"Loaded {len(df)} cases.")

    with st.spinner("Classifying cases..."):
        df["Predicted Category"] = df.apply(
            lambda row: classify_case(row[DETAILS_COLUMN], row[DATE_COLUMN]),
            axis=1
        )
    st.success("Classification complete!")

    # ── chart ──────────────────────────────────────────────────────────────────

    st.subheader("Category Breakdown")
    breakdown = df["Predicted Category"].value_counts().reset_index()
    breakdown.columns = ["Category", "Count"]
    st.bar_chart(breakdown.set_index("Category"))

    # ── manual review ──────────────────────────────────────────────────────────

    st.subheader("Review Cases")
    category_filter = st.selectbox(
        "Filter by category",
        ["All"] + sorted(df["Predicted Category"].unique().tolist())
    )

    filtered_df = df if category_filter == "All" else df[df["Predicted Category"] == category_filter]
    st.dataframe(filtered_df, use_container_width=True)

    # ── download ───────────────────────────────────────────────────────────────

    st.subheader("Download Results")
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download classified CSV",
        data=csv,
        file_name="cases_output.csv",
        mime="text/csv"
    )
