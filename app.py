
import streamlit as st
import pandas as pd
from PIL import Image

from modules.ocr import extract_text
from modules.analyzer import analyze_ingredients
from modules.database import load_database


# -------------------- PAGE SETUP --------------------

st.set_page_config(
    page_title="FITS | Ingredient Tracker",
    page_icon="🌿",
    layout="wide",
)


# -------------------- DESIGN --------------------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Outfit:wght@500;600;700&display=swap');

.stApp {
    background: #f5f8f6;
    color: #19372a;
    font-family: 'DM Sans', sans-serif;
}

h1, h2, h3 {
    font-family: 'Outfit', sans-serif !important;
    color: #173d2d;
}

section[data-testid="stSidebar"] {
    background: white;
    border-right: 1px solid #e3ece6;
}

.hero {
    background: linear-gradient(120deg, #123d2d, #287750);
    padding: 32px;
    border-radius: 22px;
    color: white;
    margin-bottom: 24px;
}

.hero h1 {
    color: white !important;
    font-size: 36px;
    margin: 8px 0;
}

.hero p {
    color: #d9eee2;
    margin-bottom: 0;
}

.metric-card {
    background: white;
    border: 1px solid #e3ece6;
    border-radius: 16px;
    padding: 18px;
}

.metric-value {
    font-size: 29px;
    font-weight: 700;
    color: #1c704b;
}

.metric-label {
    color: #718278;
    font-size: 13px;
}

.stButton > button {
    min-height: 44px;
    border-radius: 11px;
    font-weight: 600;
}

.stButton > button[kind="primary"] {
    background: #1d6b49;
    border: none;
}

.stButton > button[kind="primary"]:hover {
    background: #155538;
}

div[data-testid="stFileUploader"] {
    background: white;
    border: 1px dashed #b8d3c3;
    border-radius: 14px;
    padding: 12px;
}

footer {
    visibility: hidden;
}
</style>
""", unsafe_allow_html=True)


# -------------------- SESSION STATE --------------------

defaults = {
    "ingredient_input": "",
    "analysis_result": None,
    "analysis_category": None,
    "ocr_message": "",
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# -------------------- CALLBACKS --------------------

def extract_uploaded_text():
    uploaded = st.session_state.get("uploaded_image")

    if uploaded is None:
        st.session_state.ocr_message = "Please upload an image first."
        return

    try:
        image = Image.open(uploaded).convert("RGB")
        text = extract_text(image)

        if text.strip():
            st.session_state.ingredient_input = text
            st.session_state.ocr_message = "Text extracted. Please review it before analyzing."
        else:
            st.session_state.ocr_message = "No text detected. Try a clearer image."

    except Exception as error:
        st.session_state.ocr_message = f"OCR error: {error}"


def clear_all():
    st.session_state.ingredient_input = ""
    st.session_state.analysis_result = None
    st.session_state.analysis_category = None
    st.session_state.ocr_message = ""


# -------------------- SIDEBAR --------------------

with st.sidebar:
    st.markdown("## 🌿 FITS")
    st.caption("Food & Ingredient Tracker")

    st.divider()

    category = st.radio(
        "Select product category",
        ["Food", "Skincare"],
        horizontal=True,
    )

    st.markdown("""
    <div style="background:#eff7f1;padding:15px;border-radius:13px;">
        <b style="color:#1c704b;">Ingredient intelligence</b>
        <p style="font-size:13px;color:#65796c;margin:8px 0 0;">
        Scan labels and understand ingredient information.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.caption("FITS • Ingredient Analysis")


# -------------------- HEADER --------------------

st.markdown("""
<div class="hero">
    <div style="font-size:12px;letter-spacing:2px;color:#bde5ce;">
        SMART INGREDIENT ANALYSIS
    </div>
    <h1>Know what goes into<br>your everyday products.</h1>
    <p>Scan a label or enter ingredients to explore their safety information.</p>
</div>
""", unsafe_allow_html=True)


# -------------------- INPUT --------------------

left, right = st.columns([1, 1], gap="large")

with left:
    st.markdown("### 📷 Upload product label")

    uploaded_image = st.file_uploader(
        "Choose a label image",
        type=["png", "jpg", "jpeg", "webp"],
        key="uploaded_image",
    )

    if uploaded_image:
        image = Image.open(uploaded_image).convert("RGB")
        st.image(image, use_container_width=True)

with right:
    st.markdown("### ✍️ Ingredient list")

    st.text_area(
        "Ingredient text",
        placeholder="Example: Water, Sugar, Citric Acid...",
        height=210,
        key="ingredient_input",
    )

    st.caption("You can upload an image or enter the ingredients manually.")


# -------------------- ACTIONS --------------------

col1, col2, col3 = st.columns([1.2, 1.3, 0.7])

with col1:
    st.button(
        "✨ Extract text",
        use_container_width=True,
        on_click=extract_uploaded_text,
    )

with col2:
    analyze_clicked = st.button(
        "Analyze ingredients",
        type="primary",
        use_container_width=True,
    )

with col3:
    st.button(
        "Clear",
        use_container_width=True,
        on_click=clear_all,
    )

if st.session_state.ocr_message:
    st.info(st.session_state.ocr_message)


# -------------------- ANALYSIS --------------------

if analyze_clicked:
    text = st.session_state.ingredient_input.strip()

    if not text:
        st.warning("Please upload a label or enter ingredient text.")
    else:
        try:
            with st.spinner("Analyzing ingredients..."):
                database = load_database(category)
                result = analyze_ingredients(text, database)

                st.session_state.analysis_result = result
                st.session_state.analysis_category = category

        except Exception as error:
            st.error(f"Analysis error: {error}")


# -------------------- RESULTS --------------------

result = st.session_state.analysis_result

if result:
    st.divider()
    st.markdown("## 📊 Analysis Report")
    st.caption(f"Category: {st.session_state.analysis_category}")

    ingredients = result.get("ingredients", [])
    matches = result.get("matches", [])

    harmful_count = sum(
        item["status"] == "Harmful" for item in ingredients
    )
    caution_count = sum(
        item["status"] == "Use with Caution" for item in ingredients
    )
    safe_count = sum(
        item["status"] == "Safe" for item in ingredients
    )
    unknown_count = sum(
        item["status"] == "Not Assessed" for item in ingredients
    )

    # Summary metrics
    metrics = [
        ("Total checked", len(ingredients)),
        ("Harmful", harmful_count),
        ("Use with Caution", caution_count),
        ("Safe", safe_count),
        ("Not Assessed", unknown_count),
    ]

    metric_columns = st.columns(5)

    for column, (label, value) in zip(metric_columns, metrics):
        with column:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{value}</div>
                <div class="metric-label">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("### Ingredient details")

    status_icons = {
        "Harmful": "🔴",
        "Use with Caution": "🟠",
        "Safe": "🟢",
        "Not Assessed": "⚪",
    }

    table_rows = []

    for item in ingredients:
        status = item["status"]

        table_rows.append({
            "Ingredient": item["ingredient"],
            "Status": f"{status_icons.get(status, '⚪')} {status}",
            "Reason": item["reason"],
        })

    report_df = pd.DataFrame(table_rows)

    st.dataframe(
        report_df,
        use_container_width=True,
        hide_index=True,
    )

    # Explanations for flagged ingredients
    if matches:
        st.markdown("### Why these ingredients were flagged")

        for item in matches:
            status = item["status"]
            icon = status_icons.get(status, "⚪")

            with st.expander(
                f"{icon} {item['ingredient']} — {status}"
            ):
                st.write(item["reason"])

                if item.get("diabetes_guidance"):
                    st.markdown("**Diabetes guidance**")
                    st.write(item["diabetes_guidance"])

                if item.get("under5_guidance"):
                    st.markdown("**Under-5 guidance**")
                    st.write(item["under5_guidance"])

    # General guidance
    guidance = result.get("guidance", [])

    if guidance:
        st.markdown("### Health guidance")

        for item in guidance:
            st.info(
                f"**{item['group']} — {item['ingredient']}**\n\n"
                f"{item['message']}"
            )

    # Download report
    csv_data = report_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "⬇️ Download ingredient report",
        data=csv_data,
        file_name="fits_analysis_report.csv",
        mime="text/csv",
    )

    st.caption(
        "FITS provides database-based information, not a medical diagnosis. "
        "Ingredient effects depend on amount, usage, and individual factors. "
        "A 'Safe' classification applies only to the reference data and "
        "conditions represented in this project."
    )
