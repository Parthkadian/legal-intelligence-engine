import os
import time
import requests
import streamlit as st
import fitz  # PyMuPDF

# -----------------------------
# Page config
# -----------------------------
st.set_page_config(
    page_title="Legal Intelligence Engine",
    page_icon="⚖️",
    layout="wide"
)

# -----------------------------
# Backend config
# -----------------------------
API_URL = os.getenv(
    "API_URL",
    "https://legal-intelligence-engine.onrender.com"
)

# -----------------------------
# Basic styling
# -----------------------------
st.markdown(
    """
    <style>
    .main {
        background: linear-gradient(135deg, #031326 0%, #041b34 45%, #06244a 100%);
    }
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 1.5rem;
    }
    .glass-card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 20px;
        padding: 1rem 1.1rem;
        box-shadow: 0 8px 30px rgba(0,0,0,0.25);
    }
    .hero-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #f5f7fb;
        margin-bottom: 0.2rem;
    }
    .hero-sub {
        font-size: 1.1rem;
        color: #c7d2e3;
        margin-bottom: 0.8rem;
    }
    .metric-box {
        background: rgba(0, 255, 170, 0.06);
        border: 1px solid rgba(0, 255, 170, 0.18);
        border-radius: 18px;
        padding: 0.9rem 1rem;
        margin-bottom: 0.8rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# -----------------------------
# Helpers
# -----------------------------
def check_api_health(api_url: str):
    try:
        response = requests.get(f"{api_url}/health", timeout=25)
        response.raise_for_status()
        return True, response.json()
    except Exception as e:
        return False, str(e)


def warm_backend(api_url: str):
    try:
        requests.get(f"{api_url}/health", timeout=25)
        return True
    except Exception:
        return False


def call_backend_with_retry(api_url: str, text: str, retries: int = 2, delay: int = 8):
    text = (text or "").strip()

    if not text:
        return None, "No input text found."

    # keep payload small and safe
    text = text[:3000]

    payload = {"text": text}
    last_error = None

    # warm-up call first
    warm_backend(api_url)

    for attempt in range(1, retries + 1):
        try:
            response = requests.post(
                f"{api_url}/predict",
                json=payload,
                timeout=180
            )
            response.raise_for_status()
            return response.json(), None

        except requests.exceptions.RequestException as e:
            last_error = str(e)
            if attempt < retries:
                time.sleep(delay)
            else:
                return None, f"API request failed after {retries} attempts: {last_error}"

        except Exception as e:
            return None, f"Unexpected error: {str(e)}"

    return None, f"API request failed: {last_error}"


def extract_pdf_text(uploaded_file):
    try:
        pdf_bytes = uploaded_file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        pages = [page.get_text() for page in doc]
        return "\n".join(pages).strip(), None
    except Exception as e:
        return "", str(e)


def render_prediction(result: dict):
    if not result:
        st.error("Empty response received from backend.")
        return

    label = result.get("label", "N/A")
    confidence = result.get("confidence", 0.0)
    probabilities = result.get("probabilities", {})
    top_predictions = result.get("top_predictions", [])
    entities = result.get("entities", [])
    explanation = result.get("explanation", [])
    clauses = result.get("clauses", {})
    risk_score = result.get("risk_score", 0)
    risk_level = result.get("risk_level", "Low")
    insights = result.get("insights", [])
    business_impact = result.get("business_impact", [])
    recommendations = result.get("recommendations", [])
    executive_summary = result.get("executive_summary", {})
    processing_time_ms = result.get("processing_time_ms", 0)

    st.success("Legal analysis completed successfully.")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Document Type", label)
    with c2:
        st.metric("Confidence", f"{confidence:.2%}" if isinstance(confidence, float) else confidence)
    with c3:
        st.metric("Risk Score", risk_score)
    with c4:
        st.metric("Processing Time", f"{processing_time_ms} ms")

    st.markdown("### Executive Summary")
    if executive_summary:
        st.json(executive_summary)
    else:
        st.info("No executive summary available.")

    st.markdown("### Top Predictions")
    if top_predictions:
        for item in top_predictions:
            st.write(f"- **{item.get('label', 'N/A')}** — {item.get('confidence', 0)}")
    else:
        st.info("No top predictions returned.")

    st.markdown("### Probability Breakdown")
    if probabilities:
        st.json(probabilities)
    else:
        st.info("No probability breakdown available.")

    st.markdown("### Entities")
    if entities:
        st.json(entities)
    else:
        st.info("No entities returned.")

    st.markdown("### Explanation")
    if explanation:
        st.json(explanation)
    else:
        st.info("No explanation returned.")

    st.markdown("### Clauses")
    if clauses:
        st.json(clauses)
    else:
        st.info("No clause data returned.")

    st.markdown("### Risk Level")
    st.write(f"**{risk_level}**")

    st.markdown("### Insights")
    if insights:
        for item in insights:
            st.write(f"- {item}")
    else:
        st.info("No insights available.")

    st.markdown("### Business Impact")
    if business_impact:
        for item in business_impact:
            st.write(f"- {item}")
    else:
        st.info("No business impact notes available.")

    st.markdown("### Recommendations")
    if recommendations:
        for item in recommendations:
            st.write(f"- {item}")
    else:
        st.info("No recommendations available.")


# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:
    st.markdown("## Session Metrics")
    st.markdown('<div class="metric-box"><b>Docs Analyzed</b><br>0</div>', unsafe_allow_html=True)
    st.markdown('<div class="metric-box"><b>High Risk Flags</b><br>0</div>', unsafe_allow_html=True)

    st.markdown("## API Status")
    api_ok, api_info = check_api_health(API_URL)

    if api_ok:
        st.success("API is responding correctly")
        st.caption(f"Connected to backend:\n{API_URL}")
    else:
        st.error("API is not reachable")
        st.caption(str(api_info))

    st.markdown("## Prediction History (DB)")
    st.caption("No history in database.")

# -----------------------------
# Main layout
# -----------------------------
left, right = st.columns([1.05, 1.45], gap="large")

with left:
    st.markdown('<div class="hero-title">Ultra-Premium Corporate Legal</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-sub">Document Analysis</div>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

    extracted_text = ""

    if uploaded_file is not None:
        extracted_text, extract_error = extract_pdf_text(uploaded_file)
        if extract_error:
            st.error(f"Failed to extract PDF text: {extract_error}")
        elif extracted_text:
            st.success("PDF text extracted successfully.")
        else:
            st.warning("PDF uploaded, but no readable text was found.")

    text = st.text_area(
        "Document Text",
        value=extracted_text,
        height=280,
        label_visibility="collapsed",
        placeholder="Paste or review extracted legal text here..."
    )

    slack_toggle = st.toggle("🔔 Enable automated Slack Webhooks for High-Risk Alerts", value=False)
    _ = slack_toggle  # placeholder so lint doesn't complain

    if st.button("Run Full Legal Analysis", use_container_width=False):
        if not text.strip():
            st.error("Please upload a PDF or enter some legal text first.")
        else:
            with st.spinner("Warming backend and running legal analysis..."):
                result, error = call_backend_with_retry(API_URL, text, retries=2, delay=10)

            if error:
                st.error(error)
                st.warning("The backend may still be cold-starting on Render. Wait a few seconds and try once more.")
            else:
                render_prediction(result)

    st.markdown(
        """
        <div class="glass-card">
            <h4 style="margin-top:0;">Pipeline flow</h4>
            <div style="color:#c7d2e3;">
                PDF intake → text extraction → classification → explanation → entities → clauses → risk score → insights
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with right:
    st.markdown("### Extracted / Working Text")
    preview_text = text if text.strip() else "Your extracted document text will appear here."
    st.text_area(
        "Working Preview",
        value=preview_text,
        height=520,
        label_visibility="collapsed"
    )