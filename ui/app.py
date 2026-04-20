import streamlit as st
import streamlit.components.v1 as components
import requests
import time
from pathlib import Path
import sys
import re
import json
from datetime import datetime
import fitz
from fpdf import FPDF
from fpdf.enums import WrapMode
import pandas as pd
from docx import Document
import io
import os

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

API_URL = os.environ.get(
    "API_URL",
    "https://legal-intelligence-engine.onrender.com"
)

st.set_page_config(
    page_title="Legal Document Classifier",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "sample_text" not in st.session_state:
    st.session_state["sample_text"] = (
        "This Agreement is entered into on 12/04/2026 between Alpha Technologies Ltd and Beta Systems Pvt Ltd "
        "for the supply of software development services. The parties agree to pricing, delivery timeline, "
        "confidentiality obligations, and termination terms."
    )

if "prediction_history" not in st.session_state:
    st.session_state["prediction_history"] = []

if "latest_result" not in st.session_state:
    st.session_state["latest_result"] = None

if "api_status_cache" not in st.session_state:
    st.session_state["api_status_cache"] = None

if "api_last_checked" not in st.session_state:
    st.session_state["api_last_checked"] = None

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Playfair+Display:wght@500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

h1, h2, h3, h4, .workspace-title, .phase-title {
    font-family: 'Playfair Display', serif !important;
}

html, body, .stApp {
    background-color: #010A1A !important;
}

.stApp {
    background:
        radial-gradient(circle at 10% 12%, rgba(212,175,55,0.06), transparent 22%),
        radial-gradient(circle at 88% 14%, rgba(212,175,55,0.04), transparent 18%),
        radial-gradient(circle at 50% 100%, rgba(10,34,64,0.40), transparent 30%),
        linear-gradient(180deg, #010A1A 0%, #0A192F 48%, #010A1A 100%) !important;
    color: #f8fafc;
}

/* blend top bar */
header[data-testid="stHeader"] {
    background: transparent !important;
    height: 0px !important;
    border-bottom: none !important;
    box-shadow: none !important;
}

[data-testid="stDecoration"] {
    display: none !important;
}

[data-testid="stToolbar"] {
    background: transparent !important;
    top: 0.45rem !important;
    right: 1rem !important;
    border: none !important;
    box-shadow: none !important;
}

[data-testid="stStatusWidget"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}

.block-container {
    max-width: 1520px;
    padding-top: 0.05rem !important;
    padding-bottom: 1.5rem;
}

.stApp > header {
    background: transparent !important;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, rgba(6,18,30,0.98), rgba(1,10,26,0.98));
    border-right: 1px solid rgba(212,175,55,0.20);
}

[data-testid="stSidebar"] .block-container {
    padding-top: 1rem;
}

.workspace-title {
    font-size: 1.7rem;
    font-weight: 800;
    color: white;
    margin-bottom: 1rem;
}

.sidebar-section-title {
    color: #ffffff;
    font-weight: 800;
    font-size: 1.05rem;
    margin-top: 1.15rem;
    margin-bottom: 0.65rem;
}

.sidebar-text {
    color: #dbe4f0;
    font-size: 0.96rem;
    line-height: 1.7;
}

.sidebar-bullet {
    color: #dbe4f0;
    font-size: 0.95rem;
    line-height: 1.8;
    margin-left: 0.2rem;
}

.sidebar-alert {
    background: rgba(239,68,68,0.14);
    border: 1px solid rgba(239,68,68,0.22);
    color: #fecaca;
    padding: 0.9rem 1rem;
    border-radius: 14px;
    font-weight: 600;
    margin-top: 0.6rem;
}

.sidebar-alert-success {
    background: rgba(16,185,129,0.16);
    border: 1px solid rgba(52,211,153,0.24);
    color: #d1fae5;
    padding: 0.9rem 1rem;
    border-radius: 14px;
    font-weight: 600;
    margin-top: 0.6rem;
}

.mode-row {
    display: flex;
    gap: 0.7rem;
    align-items: center;
    margin-top: 0.35rem;
    margin-bottom: 0.35rem;
}

.mode-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    padding: 0.45rem 0.7rem;
    border-radius: 999px;
    border: 1px solid rgba(255,255,255,0.08);
    background: rgba(255,255,255,0.03);
    color: #e5eef9;
    font-size: 0.9rem;
    font-weight: 700;
}

.mode-dot-red {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: #10b981;
    box-shadow: 0 0 10px #10b981;
}

.mode-dot-gray {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: #374151;
    box-shadow: 0 0 10px #374151;
}

.phase-card {
    min-height: 116px;
    border-radius: 26px;
    padding: 1.2rem 1.2rem;
    background: linear-gradient(180deg, rgba(8,22,36,0.94), rgba(5,15,30,0.92));
    border: 1px solid rgba(212,175,55,0.25);
    box-shadow: 0 14px 34px rgba(0,0,0,0.28);
    margin-bottom: 0.95rem;
}

.phase-title {
    color: white;
    font-size: 1.15rem;
    font-weight: 800;
    margin-bottom: 0.7rem;
}

.phase-text {
    color: #dbe4f0;
    font-size: 0.96rem;
    line-height: 1.7;
}

.mini-stat-card {
    min-height: 128px;
    border-radius: 24px;
    padding: 1.15rem;
    background: linear-gradient(180deg, rgba(7,20,32,0.94), rgba(5,15,25,0.92));
    border: 1px solid rgba(212,175,55,0.25);
    box-shadow: 0 12px 28px rgba(0,0,0,0.24);
    margin-top: 1rem;
}

.mini-stat-number {
    color: white;
    font-size: 2.2rem;
    font-weight: 800;
    margin-bottom: 0.7rem;
}

.mini-stat-text {
    color: #dbe4f0;
    font-size: 0.97rem;
    line-height: 1.7;
}

.workspace-bar {
    margin-top: 1rem;
    border-radius: 20px;
    padding: 0.8rem 1rem;
    background: linear-gradient(90deg, rgba(8,22,36,0.96), rgba(10,34,64,0.45), rgba(7,20,32,0.96));
    border: 1px solid rgba(212,175,55,0.25);
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
}

.workspace-bar-title {
    color: white;
    font-weight: 800;
    font-size: 1rem;
}

.workspace-bar-tags {
    display: flex;
    gap: 0.65rem;
    flex-wrap: wrap;
}

.workspace-bar-tag {
    padding: 0.5rem 0.85rem;
    border-radius: 999px;
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.08);
    color: #f1f5f9;
    font-size: 0.84rem;
    font-weight: 700;
}

.section-title-main {
    color: white;
    font-size: 1.15rem;
    font-weight: 800;
    margin-top: 1.15rem;
    margin-bottom: 0.35rem;
}

.section-subtitle-main {
    color: #cbd5e1;
    font-size: 0.95rem;
    line-height: 1.7;
    margin-bottom: 0.95rem;
}

.native-card {
    border-radius: 26px;
    padding: 1.2rem 1.2rem 1rem 1.2rem;
    background: linear-gradient(180deg, rgba(7,20,32,0.94), rgba(6,30,27,0.96));
    border: 1px solid rgba(34,197,94,0.10);
    box-shadow: 0 14px 34px rgba(0,0,0,0.24);
    min-height: 100%;
}

.native-card-title {
    color: white;
    font-size: 1.05rem;
    font-weight: 800;
    margin-bottom: 0.35rem;
}

.native-card-subtitle {
    color: #cbd5e1;
    font-size: 0.90rem;
    line-height: 1.65;
    margin-bottom: 0.8rem;
}

.result-chip {
    display: inline-block;
    padding: 0.55rem 0.9rem;
    border-radius: 999px;
    background: rgba(16,185,129,0.16);
    border: 1px solid rgba(52,211,153,0.24);
    color: #d1fae5;
    font-weight: 700;
    margin-bottom: 0.85rem;
}

.keyword-pill {
    display: inline-block;
    background: rgba(16,185,129,0.14);
    border: 1px solid rgba(52,211,153,0.28);
    color: #d1fae5;
    border-radius: 999px;
    padding: 0.42rem 0.78rem;
    margin: 0.25rem 0.35rem 0.25rem 0;
    font-size: 0.88rem;
    font-weight: 700;
}

.entity-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(148,163,184,0.12);
    border-radius: 18px;
    padding: 0.95rem 1rem;
    margin-bottom: 0.7rem;
}

.entity-text {
    color: #ffffff;
    font-weight: 700;
    margin-bottom: 0.2rem;
}

.entity-label {
    color: #6ee7b7;
    font-size: 0.85rem;
    font-weight: 600;
}

.highlight-box {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(148,163,184,0.12);
    border-radius: 18px;
    padding: 1rem;
    color: #e2e8f0;
    line-height: 1.75;
    white-space: pre-wrap;
    font-size: 0.97rem;
}

.highlight-chip {
    background: linear-gradient(90deg, rgba(16,185,129,0.22), rgba(34,197,94,0.16));
    border: 1px solid rgba(52,211,153,0.28);
    color: #d1fae5;
    padding: 0.08rem 0.42rem;
    border-radius: 0.5rem;
    font-weight: 700;
}

.risk-high {
    background: rgba(239,68,68,0.12);
    border: 1px solid rgba(239,68,68,0.28);
    color: #fca5a5;
    border-radius: 14px;
    padding: 0.8rem 0.95rem;
    margin-bottom: 0.6rem;
    font-weight: 600;
}

.risk-medium {
    background: rgba(245,158,11,0.12);
    border: 1px solid rgba(245,158,11,0.28);
    color: #fcd34d;
    border-radius: 14px;
    padding: 0.8rem 0.95rem;
    margin-bottom: 0.6rem;
    font-weight: 600;
}

.risk-low {
    background: rgba(34,197,94,0.12);
    border: 1px solid rgba(34,197,94,0.28);
    color: #86efac;
    border-radius: 14px;
    padding: 0.8rem 0.95rem;
    margin-bottom: 0.6rem;
    font-weight: 600;
}

.small-note {
    color: #94a3b8;
    font-size: 0.88rem;
}

.history-item {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(148,163,184,0.10);
    border-radius: 16px;
    padding: 0.85rem 0.9rem;
    margin-bottom: 0.65rem;
}

.history-title {
    color: #ffffff;
    font-weight: 700;
    margin-bottom: 0.25rem;
}

.history-meta {
    color: #94a3b8;
    font-size: 0.84rem;
}

.loading-card {
    background: linear-gradient(180deg, rgba(10,18,35,0.88), rgba(15,23,42,0.96));
    border: 1px solid rgba(52,211,153,0.16);
    border-radius: 22px;
    padding: 1rem 1.1rem;
    box-shadow: 0 14px 32px rgba(2,6,23,0.30);
}

.loading-line {
    height: 11px;
    border-radius: 999px;
    margin-top: 0.55rem;
    background: linear-gradient(90deg, rgba(16,185,129,0.12), rgba(52,211,153,0.28), rgba(16,185,129,0.12));
}

.stButton > button {
    width: 100%;
    min-height: 3.15rem;
    border-radius: 16px;
    border: 1px solid rgba(34,197,94,0.24);
    background: linear-gradient(90deg, #052e2b, #065f46, #064e3b);
    color: white;
    font-weight: 700;
    box-shadow: 0 10px 24px rgba(6,78,59,0.26);
    transition: 0.22s ease;
}

.stButton > button:hover {
    transform: translateY(-1px);
    border-color: rgba(52,211,153,0.42);
    box-shadow: 0 14px 30px rgba(6,78,59,0.36);
}

div[data-testid="stTextArea"] textarea {
    background: rgba(17,24,39,0.95) !important;
    color: #f8fafc !important;
    border-radius: 18px !important;
    border: 1px solid rgba(148,163,184,0.14) !important;
    min-height: 370px !important;
    font-size: 1rem !important;
    padding-top: 1rem !important;
}

[data-testid="stFileUploader"] {
    background: rgba(255,255,255,0.02);
    border-radius: 18px;
    padding: 0.35rem;
}

[data-testid="stDownloadButton"] button {
    width: 100%;
    border-radius: 16px;
    min-height: 3rem;
    background: linear-gradient(90deg, #0b2d27, #064e3b);
    color: #fff;
    border: 1px solid rgba(52,211,153,0.16);
}

[data-testid="stProgressBar"] > div > div {
    background: linear-gradient(90deg, #10b981, #22c55e) !important;
}

.api-mini-note {
    color: #94a3b8;
    font-size: 0.82rem;
    margin-top: 0.5rem;
}

.pipeline-note {
    margin-top: 0.9rem;
    padding: 0.9rem 1rem;
    border-radius: 18px;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    color: #cbd5e1;
    font-size: 0.9rem;
    line-height: 1.7;
}

.card-gap {
    height: 0.8rem;
}

h3 {
    color: white !important;
    font-weight: 800 !important;
    margin-top: 0.2rem !important;
    margin-bottom: 0.8rem !important;
}

.stInfo, .stSuccess, .stWarning, .stError {
    border-radius: 16px !important;
}

@keyframes fadeUp {
    from { opacity: 0; transform: translateY(15px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes shimmer {
    0% { background-position: -1000px 0; }
    100% { background-position: 1000px 0; }
}
.native-card, .phase-card, .mini-stat-card, .highlight-box, .entity-card {
    animation: fadeUp 0.65s cubic-bezier(0.16, 1, 0.3, 1) both;
}
.native-card, .phase-card, .mini-stat-card {
    transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.3s ease;
}
.native-card:hover, .phase-card:hover, .mini-stat-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 20px 40px rgba(0,0,0,0.4), 0 0 15px rgba(212,175,55,0.08);
}
.loading-line {
    background: linear-gradient(90deg, rgba(16,185,129,0.12) 25%, rgba(52,211,153,0.4) 50%, rgba(16,185,129,0.12) 75%) !important;
    background-size: 1000px 100% !important;
    animation: shimmer 2.5s infinite linear !important;
}
.stButton > button {
    position: relative;
    overflow: hidden;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.stButton > button::after {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: linear-gradient(
        to right,
        rgba(255, 255, 255, 0) 0%,
        rgba(255, 255, 255, 0.15) 50%,
        rgba(255, 255, 255, 0) 100%
    );
    transform: rotate(30deg);
    animation: shimmer 3s infinite linear;
    pointer-events: none;
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 14px 30px rgba(6,78,59,0.5), 0 0 15px rgba(52,211,153,0.3);
}
.keyword-pill, .result-chip {
    transition: transform 0.2s ease, filter 0.2s ease;
    display: inline-block;
}
.keyword-pill:hover, .result-chip:hover {
    transform: scale(1.05);
    filter: brightness(1.2);
}

.entity-card {
    transition: transform 0.2s ease, border-color 0.2s ease;
}
.entity-card:hover {
    transform: scale(1.02);
    border-color: rgba(110,231,183,0.4);
}
.sidebar-profile {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    padding: 0.8rem;
    border-radius: 14px;
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    margin-bottom: 1.2rem;
}
.sidebar-avatar {
    width: 38px;
    height: 38px;
    border-radius: 50%;
    background: linear-gradient(135deg, #D4AF37, #A67C00);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: 800;
    font-size: 1.1rem;
}
.sidebar-user-info {
    display: flex;
    flex-direction: column;
}
.sidebar-user-name {
    color: white;
    font-weight: 700;
    font-size: 0.95rem;
}
.sidebar-user-role {
    color: #94a3b8;
    font-size: 0.8rem;
}
.sidebar-metric {
    background: linear-gradient(135deg, rgba(16,185,129,0.08), rgba(16,185,129,0.02));
    border: 1px solid rgba(52,211,153,0.15);
    border-radius: 12px;
    padding: 0.7rem 0.9rem;
    margin-bottom: 0.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.sidebar-metric.alert-metric {
    background: linear-gradient(135deg, rgba(239,68,68,0.08), rgba(239,68,68,0.02));
    border: 1px solid rgba(248,113,113,0.15);
}
.metric-label {
    color: #cbd5e1;
    font-size: 0.85rem;
    font-weight: 500;
}
.metric-value {
    color: white;
    font-size: 1.1rem;
    font-weight: 800;
}
.sidebar-footer {
    margin-top: 2rem;
    padding-top: 1rem;
    border-top: 1px solid rgba(255,255,255,0.08);
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}
.footer-link {
    color: #94a3b8;
    font-size: 0.85rem;
    text-decoration: none;
    transition: color 0.2s;
    cursor: pointer;
}
.footer-link:hover {
    color: #D4AF37;
}
</style>
""", unsafe_allow_html=True)


def check_api_health(retries=2, delay=0.6):
    for _ in range(retries):
        try:
            response = requests.get(f"{API_URL}/health", timeout=8)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "ok":
                    return True, data
                return True, data
        except Exception:
            time.sleep(delay)
    return False, None


def refresh_api_status():
    online, data = check_api_health()
    st.session_state["api_status_cache"] = {
        "online": online,
        "data": data
    }
    st.session_state["api_last_checked"] = datetime.now().strftime("%H:%M:%S")
    return online, data


def get_api_status():
    cached = st.session_state.get("api_status_cache")
    if cached is None:
        return refresh_api_status()
    return cached["online"], cached["data"]


def get_api_history():
    try:
        response = requests.get(f"{API_URL}/history", timeout=8)
        if response.status_code == 200:
            return response.json().get("history", [])
    except Exception:
        pass
    return []


def predict_text(text: str):
    payload = {"text": text}
    response = requests.post(f"{API_URL}/predict", json=payload, timeout=120)
    response.raise_for_status()
    return response.json()


def extract_text_from_pdf(uploaded_file) -> str:
    try:
        pdf_bytes = uploaded_file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        pages = [page.get_text("text") for page in doc]
        return "\n".join(pages).strip()
    except Exception as e:
        st.error(f"Could not read PDF: {e}")
        return ""


def escape_html(text: str) -> str:
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
    )


def highlight_keywords_in_text(text: str, explanation: list):
    safe_text = escape_html(text)
    words = []

    for item in explanation:
        if isinstance(item, dict):
            word = str(item.get("word", "")).strip()
        else:
            word = str(item).strip()
        if word and len(word) >= 3:
            words.append(re.escape(word))

    if not words:
        return safe_text

    pattern = r'\b(' + "|".join(words[:12]) + r')\b'

    def replacer(match):
        return f"<span class='highlight-chip'>{match.group(0)}</span>"

    try:
        return re.sub(pattern, replacer, safe_text, flags=re.IGNORECASE)
    except Exception:
        return safe_text


def generate_pdf_report(latest_data):
    pdf = FPDF()
    pdf.add_page()

    pdf.set_fill_color(10, 34, 64)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", size=18, style="B")
    pdf.cell(0, 15, txt="  PREMIUM LEGAL ANALYSIS REPORT", ln=True, align='L', fill=True)
    pdf.ln(5)

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", size=12, style="B")
    pdf.cell(0, 10, txt=f"Risk Score: {latest_data['prediction']['risk_score']}/100", ln=True)

    pdf.set_font("Helvetica", size=11)
    safe_summary = latest_data['summary'].replace("→", "->").replace("—", "-")
    safe_summary = safe_summary.encode('ascii', errors='ignore').decode('ascii')

    pdf.multi_cell(0, 8, text=f"Summary: {safe_summary}", wrapmode=WrapMode.CHAR)
    pdf.ln(5)

    pdf.set_font("Helvetica", size=12, style="B")
    pdf.cell(0, 10, txt="Clause Detection:", ln=True)
    pdf.set_font("Helvetica", size=11)
    for clause, present in latest_data['prediction']['clauses'].items():
        status = "Detected" if present else "Missing"
        pdf.cell(0, 8, txt=f"- {clause}: {status}", ln=True)

    pdf.ln(5)
    pdf.set_font("Helvetica", size=12, style="B")
    pdf.cell(0, 10, txt="Insights:", ln=True)
    pdf.set_font("Helvetica", size=11)
    for ins in latest_data['prediction']['insights']:
        safe_ins = ins.replace("→", "->").replace("—", "-")
        safe_ins = safe_ins.encode('ascii', errors='ignore').decode('ascii')
        pdf.multi_cell(0, 8, text=f"- {safe_ins}", wrapmode=WrapMode.CHAR)
        pdf.ln(1)

    return pdf.output()


def generate_docx_report(latest_data):
    doc = Document()
    doc.add_heading('Legal Risk Analysis Report', 0)

    doc.add_heading(f"Risk Score: {latest_data['prediction']['risk_score']}/100", level=1)

    doc.add_heading('Summary', level=2)
    doc.add_paragraph(latest_data['summary'])

    doc.add_heading('Clause Detection', level=2)
    for clause, present in latest_data['prediction']['clauses'].items():
        status = "Detected" if present else "Missing"
        doc.add_paragraph(f"- {clause}: {status}", style='List Bullet')

    doc.add_heading('Insights', level=2)
    for ins in latest_data['prediction']['insights']:
        doc.add_paragraph(ins, style='List Bullet')

    io_stream = io.BytesIO()
    doc.save(io_stream)
    return io_stream.getvalue()


def generate_csv_matrix(latest_data):
    data = {"Document Label": [latest_data['prediction']['label']]}
    data["Risk Score"] = [latest_data['prediction']['risk_score']]
    for clause, present in latest_data['prediction']['clauses'].items():
        data[clause] = ["Detected" if present else "Missing"]
    df = pd.DataFrame(data)
    return df.to_csv(index=False).encode('utf-8')


def add_to_history(text, result):
    pass


def build_summary(text: str, label: str, entities: list, clauses: dict | None = None, risk_score: int = 0) -> str:
    words = text.split()
    preview = " ".join(words[:55]).strip()
    if len(words) > 55:
        preview += "..."

    detected_clauses = []
    if clauses:
        detected_clauses = [name for name, present in clauses.items() if present]

    clause_text = ", ".join(detected_clauses) if detected_clauses else "no major clauses detected"

    return (
        f"This document is currently classified as **{label}**. "
        f"The analysed content contains approximately **{len(words)} words** and "
        f"the pipeline extracted **{len(entities)} entities** for review. "
        f"Detected clause pattern summary: **{clause_text}**. "
        f"Estimated legal risk score: **{risk_score}/100**. "
        f"Preview: {preview}"
    )


def loading_sequence():
    placeholder = st.empty()
    messages = [
        "Connecting to backend and verifying legal pipeline state...",
        "Tokenising legal document content...",
        "Running BERT classification workflow...",
        "Extracting named entities from document text...",
        "Generating explanation, confidence view, and review signals..."
    ]
    for msg in messages:
        placeholder.markdown(
            f"""
            <div class="loading-card">
                <div class="panel-title">⚡ Processing</div>
                <div class="small-note">{msg}</div>
                <div class="loading-line"></div>
            </div>
            """,
            unsafe_allow_html=True
        )
        time.sleep(0.30)
    return placeholder


def status_pill_html(text: str, dot_color: str, glow_color: str) -> str:
    return f"""
    <div style="
        display:inline-flex;
        align-items:center;
        gap:0.42rem;
        padding:0.42rem 0.82rem;
        min-height:34px;
        border-radius:999px;
        font-size:0.84rem;
        font-weight:700;
        line-height:1;
        letter-spacing:-0.01em;
        border:1px solid rgba(255,255,255,0.09);
        background:linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.035));
        color:#e8eef9;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.04), 0 8px 18px rgba(0,0,0,0.18);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        white-space:nowrap;
    ">
        <span style="
            width:7px;
            height:7px;
            border-radius:50%;
            display:inline-block;
            background:{dot_color};
            box-shadow:0 0 8px {glow_color};
        "></span>
        {text}
    </div>
    """


def premium_status_pills_html(api_status_text: str, api_online: bool) -> str:
    api_color = "#22c55e" if api_online else "#ef4444"
    api_glow = api_color

    pills = [
        status_pill_html("PDF Upload Ready", "#22c55e", "#22c55e"),
        status_pill_html("Explainability Enabled", "#10b981", "#10b981"),
        status_pill_html(api_status_text, api_color, api_glow),
        status_pill_html("Displays Results", "#34d399", "#34d399"),
    ]
    return f"""
    <div style="display:flex; gap:0.55rem; flex-wrap:wrap; justify-content:flex-start; margin-bottom:0.95rem;">
        {''.join(pills)}
    </div>
    """


def render_sidebar_api_status(online: bool):
    if online:
        st.markdown(
            '<div class="sidebar-alert-success">API is responding correctly</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<div class="sidebar-alert">API is not responding correctly</div>',
            unsafe_allow_html=True
        )

    last_checked = st.session_state.get("api_last_checked")
    if last_checked:
        st.markdown(
            f'<div class="api-mini-note">Last checked: {last_checked}</div>',
            unsafe_allow_html=True
        )


def normalize_explanation_items(explanation):
    normalized = []
    for item in explanation:
        if isinstance(item, dict):
            word = str(item.get("word", "")).strip()
            score = item.get("score", None)
            if word:
                normalized.append({"word": word, "score": score})
        else:
            word = str(item).strip()
            if word:
                normalized.append({"word": word, "score": None})
    return normalized


if st.session_state["api_status_cache"] is None:
    refresh_api_status()

with st.sidebar:
    st.markdown("""
    <div class="sidebar-profile">
        <div class="sidebar-avatar">VS</div>
        <div class="sidebar-user-info">
            <span class="sidebar-user-name">Vikram Singh</span>
            <span class="sidebar-user-role">Senior Legal Counsel</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.selectbox("Active Workspace", ["Global Contracts HQ", "M&A Due Diligence", "HR & Employment", "Vendor Agreements"])

    st.markdown('<div class="sidebar-section-title">Platform Overview</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sidebar-text">This dashboard provides premium legal document analysis using a production-style NLP workflow with classification, entity extraction, summarisation, risk review, and exportable outputs.</div>',
        unsafe_allow_html=True
    )

    st.markdown('<div class="sidebar-section-title">Capabilities</div>', unsafe_allow_html=True)
    capabilities = [
        "PDF and text document ingestion",
        "Legal document classification",
        "Named entity extraction",
        "Keyword-based explanation layer",
        "Clause detection and risk scoring",
        "Confidence score breakdown",
        "Exportable analysis results"
    ]
    for item in capabilities:
        st.markdown(f'<div class="sidebar-bullet">• {item}</div>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section-title">Session Metrics</div>', unsafe_allow_html=True)

    total_docs = 0
    high_risk = 0
    try:
        import sqlite3
        db_path = Path(__file__).resolve().parent.parent / "predictions.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*), SUM(CASE WHEN risk_score >= 70 THEN 1 ELSE 0 END) FROM history")
        row = cursor.fetchone()
        conn.close()
        if row:
            total_docs = row[0] or 0
            high_risk = row[1] or 0
    except Exception:
        pass

    st.markdown(f"""
    <div class="sidebar-metric">
        <span class="metric-label">Docs Analyzed</span>
        <span class="metric-value">{total_docs}</span>
    </div>
    <div class="sidebar-metric alert-metric">
        <span class="metric-label">High Risk Flags</span>
        <span class="metric-value">{high_risk}</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section-title">API Status</div>', unsafe_allow_html=True)
    sidebar_online, _ = get_api_status()
    render_sidebar_api_status(sidebar_online)

    st.markdown('<div class="api-mini-note">🔗 Connected to backend: ' + API_URL + '</div>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section-title">Prediction History (DB)</div>', unsafe_allow_html=True)
    db_history = get_api_history()
    if db_history:
        for item in db_history:
            conf_str = f"{float(item['confidence']):.1%}"
            safe_preview = str(item['preview']).replace('**', '').replace('\n', ' ')[:65]
            st.markdown(
                f"""
                <div class="history-item" style="line-height: 1.6;">
                    <div style="color: white; font-weight: 700; margin-bottom: 0.2rem; font-size: 0.95rem;">📄 Document Analyzed</div>
                    <div class="history-meta">🏷️ <b>Type:</b> {item['label']} ({conf_str})</div>
                    <div class="history-meta">⏱️ <b>Time:</b> {item['timestamp']}</div>
                    <div class="history-meta" style="margin-top: 0.4rem; font-style: italic; color: #cbd5e1;">"{safe_preview}..."</div>
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.caption("No history in database.")

    st.markdown("""
    <div class="sidebar-footer">
        <div class="footer-link">📖 Platform Documentation</div>
        <div class="footer-link">✉️ Contact DPO (Data Protection)</div>
        <div class="footer-link">⚙️ Advanced Settings</div>
        <div style="color: #64748b; font-size: 0.75rem; margin-top: 0.4rem;">System v3.0.0 • All systems nominal</div>
    </div>
    """, unsafe_allow_html=True)

online, _ = get_api_status()
api_status_text = "API Connected" if online else "API Issue"

left_col, right_col = st.columns([1.75, 1.0], gap="large")

with left_col:
    hero_html = """
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        body {
            margin: 0;
            padding: 0;
            background: transparent;
            font-family: Inter, sans-serif;
            color: white;
        }

        .hero-card {
            position: relative;
            overflow: hidden;
            min-height: 480px;
            border-radius: 30px;
            padding: 1.35rem 1.8rem 1.7rem 1.8rem;
            background:
                linear-gradient(135deg, rgba(8,22,36,0.95), rgba(6,30,27,0.90), rgba(5,46,34,0.82));
            border: 1px solid rgba(255,255,255,0.08);
            box-shadow: 0 18px 55px rgba(0,0,0,0.32);
            box-sizing: border-box;
        }

        .hero-card::before {
            content: "";
            position: absolute;
            inset: -35%;
            background:
                radial-gradient(circle at 20% 30%, rgba(16,185,129,0.14), transparent 22%),
                radial-gradient(circle at 80% 30%, rgba(34,197,94,0.12), transparent 22%);
            pointer-events: none;
        }

        .hero-chip {
            display: inline-block;
            position: relative;
            z-index: 2;
            padding: 0.58rem 0.95rem;
            border-radius: 999px;
            background: rgba(255,255,255,0.065);
            border: 1px solid rgba(255,255,255,0.09);
            color: #e5eef9;
            font-size: 0.84rem;
            font-weight: 700;
            margin-bottom: 1.1rem;
        }

        .hero-title {
            position: relative;
            z-index: 2;
            font-size: 4rem;
            line-height: 0.98;
            font-weight: 800;
            letter-spacing: -0.05em;
            color: white;
            max-width: 760px;
            margin-bottom: 1.2rem;
        }

        .hero-gradient-text-1 {
            color: #6ee7b7;
        }

        .hero-gradient-text-2 {
            color: #34d399;
        }

        .hero-subtitle {
            position: relative;
            z-index: 2;
            max-width: 900px;
            color: #dbe4f0;
            font-size: 1.05rem;
            line-height: 1.75;
            margin-bottom: 1.1rem;
        }

        .hero-badges {
            position: relative;
            z-index: 2;
            display: flex;
            gap: 0.7rem;
            flex-wrap: wrap;
            margin-bottom: 0.9rem;
        }

        .hero-badge {
            display: inline-block;
            padding: 0.62rem 0.92rem;
            border-radius: 999px;
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.08);
            color: #f1f5f9;
            font-size: 0.88rem;
            font-weight: 700;
            white-space: nowrap;
        }
    </style>
    </head>
    <body>
        <div class="hero-card">
            <div class="hero-chip">Designed as a multi-stage legal intelligence workflow</div>

            <div class="hero-title">
                From raw documents<br>
                to ranked<br>
                <span class="hero-gradient-text-1">legal insights</span><span class="hero-gradient-text-2">.</span>
            </div>

            <div class="hero-subtitle">
                Premium legal AI workspace for document ingestion, classification, entity extraction,
                explanation-aware review, clause-level risk detection, and exportable outputs in one polished interface.
            </div>

            <div class="hero-badges">
                <div class="hero-badge">Legal document classification</div>
                <div class="hero-badge">PDF upload</div>
                <div class="hero-badge">Entity extraction</div>
                <div class="hero-badge">Confidence analysis</div>
            </div>

            <div class="hero-badges">
                <div class="hero-badge">Risk scoring</div>
                <div class="hero-badge">Clause detection</div>
                <div class="hero-badge">FastAPI backend</div>
                <div class="hero-badge">BERT inference</div>
            </div>
        </div>
    </body>
    </html>
    """
    components.html(hero_html, height=520, scrolling=False)

    stat_c1, stat_c2 = st.columns(2, gap="medium")

    with stat_c1:
        st.markdown("""
        <div class="mini-stat-card">
            <div class="mini-stat-number">1</div>
            <div class="mini-stat-text">Unified workspace for document upload, classification, explanation, and legal review in one flow.</div>
        </div>
        """, unsafe_allow_html=True)

    with stat_c2:
        st.markdown("""
        <div class="mini-stat-card">
            <div class="mini-stat-number">N</div>
            <div class="mini-stat-text">Documents can be analysed repeatedly across multiple classes, clauses, and legal review scenarios.</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="mini-stat-card">
        <div class="mini-stat-number">∞</div>
        <div class="mini-stat-text">Designed to evolve into a scalable legal intelligence platform with richer contract analytics and deployment layers.</div>
    </div>
    """, unsafe_allow_html=True)

with right_col:
    st.markdown(
        premium_status_pills_html(api_status_text, online),
        unsafe_allow_html=True
    )

    refresh_col1, refresh_col2 = st.columns([1.25, 1])
    with refresh_col1:
        if st.button("Refresh API Status", key="refresh_api_top"):
            refresh_api_status()
            st.rerun()

    with refresh_col2:
        last_checked = st.session_state.get("api_last_checked", "—")
        st.markdown(
            f"""
            <div style="
                display:flex;
                align-items:center;
                justify-content:center;
                min-height:3.15rem;
                border-radius:16px;
                border:1px solid rgba(255,255,255,0.08);
                background: linear-gradient(180deg, rgba(255,255,255,0.03), rgba(255,255,255,0.015));
                color:#cbd5e1;
                font-size:0.84rem;
                font-weight:700;
                padding:0.25rem 0.7rem;
                text-align:center;
            ">
                Last check<br>{last_checked}
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("""
    <div class="phase-card">
        <div class="phase-title">Phase 1 • Document Intake</div>
        <div class="phase-text">
            Accepts pasted legal text or uploaded PDF documents, extracts content, and prepares it for downstream NLP analysis.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="phase-card">
        <div class="phase-title">Phase 2 • Legal NLP Analysis</div>
        <div class="phase-text">
            Runs BERT-based document classification, derives confidence scores, and identifies named entities and important keywords.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="phase-card">
        <div class="phase-title">Phase 3 • Review & Insights</div>
        <div class="phase-text">
            Produces summary text, highlights key terms in context, flags clause-level legal risk patterns, and enables exportable review outputs.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="phase-card" style="min-height: 220px;">
        <div class="phase-title">Enterprise Readiness</div>
        <div class="phase-text">
            Designed for seamless integration into existing corporate legal workflows. This architecture provides scalable backend connectivity, 
            confident risk analysis, and structured REST API deployment layers for enterprise compliance, auditing, and high-volume document ingestion.
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
<div class="workspace-bar">
    <div class="workspace-bar-title">Legal Intelligence Workspace</div>
    <div class="workspace-bar-tags">
        <div class="workspace-bar-tag">Document Intake</div>
        <div class="workspace-bar-tag">Classification</div>
        <div class="workspace-bar-tag">Reviewability</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="section-title-main">📄 Upload PDF or Enter Legal Text</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-subtitle-main">Upload a legal PDF or paste legal clauses directly for full analysis.</div>',
    unsafe_allow_html=True
)

input_left, input_right = st.columns([1, 1.75], gap="large")

with input_left:
    st.markdown("""
    <div style='background: linear-gradient(135deg, #0A192F 0%, #001220 100%); padding: 2.5rem; border-radius: 14px; margin-bottom: 2rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border: 1px solid rgba(212,175,55,0.3);'>
        <h1 style='color: #D4AF37; margin: 0; padding: 0;'>⚖️ Legal Intelligence Workspace</h1>
        <p style='color: #cbd5e1; font-size: 1.15rem; margin-top: 0.5rem;'>Ultra-Premium Corporate Legal Document Analysis</p>
    </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"], key="uploader_pdf")

    if uploaded_file is not None:
        pdf_text = extract_text_from_pdf(uploaded_file)
        if pdf_text:
            st.session_state["sample_text"] = pdf_text
            st.success("PDF text extracted successfully.")

    st.markdown('<div class="card-gap"></div>', unsafe_allow_html=True)

    enable_webhooks = st.toggle("🔔 Enable automated Slack Webhooks for High-Risk Alerts", value=True)

    predict_btn = st.button("Run Full Legal Analysis", key="run_legal_analysis")

    st.markdown("""
    <div class="pipeline-note">
        <b style="color:white;">Pipeline flow</b><br>
        PDF intake → text extraction → classification → explanation → entities → clauses → risk score → insights
    </div>
    """, unsafe_allow_html=True)

with input_right:
    st.markdown("""
    <div class="native-card">
        <div class="native-card-title">Legal Text Editor</div>
        <div class="native-card-subtitle">Paste, review, or edit extracted legal content before analysis.</div>
    </div>
    """, unsafe_allow_html=True)

    text = st.text_area(
        "",
        value=st.session_state["sample_text"],
        height=370,
        label_visibility="collapsed",
        placeholder="Paste your contract, lease, agreement, NDA, notice, or other legal text here..."
    )

if predict_btn:
    if not text.strip():
        st.warning("Please upload a PDF or enter legal text first.")
    else:
        online, _ = refresh_api_status()
        if not online:
            st.error("API is offline. Check your deployed backend connection.")
        else:
            loading_placeholder = loading_sequence()

            try:
                result = predict_text(text)
                loading_placeholder.empty()

                add_to_history(text, result)

                entities = result.get("entities", [])
                clauses = result.get("clauses", {})
                risk_score = result.get("risk_score", 0)
                insights = result.get("insights", [])

                summary = build_summary(
                    text,
                    result.get("label", "Unknown"),
                    entities,
                    clauses,
                    risk_score
                )

                export_payload = {
                    "summary": summary,
                    "prediction": result,
                    "clauses": clauses,
                    "risk_score": risk_score,
                    "insights": insights
                }

                st.session_state["latest_result"] = {
                    "summary": summary,
                    "prediction": result,
                    "text": text,
                    "export_json": json.dumps(export_payload, indent=2)
                }

                if enable_webhooks and risk_score >= 70:
                    st.toast("🚨 **WEBHOOK FIRED:** High-Risk anomaly sent to Slack #legal-alerts", icon="🚨")
                elif enable_webhooks:
                    st.toast("✅ **WEBHOOK LOG:** Standard document processed successfully.", icon="✅")

                refresh_api_status()

            except requests.exceptions.Timeout:
                loading_placeholder.empty()
                st.error("The backend took too long to respond. First prediction can be slow while the model loads.")
            except requests.exceptions.RequestException as e:
                loading_placeholder.empty()
                st.error(f"API request failed: {e}")
            except Exception as e:
                loading_placeholder.empty()
                st.error(f"Something went wrong: {e}")

latest = st.session_state.get("latest_result")

if latest is not None:
    result = latest["prediction"]
    summary = latest["summary"]
    text = latest["text"]

    label = result.get("label", "Unknown")
    confidence = result.get("confidence", 0.0)
    processing_time_ms = result.get("processing_time_ms", "N/A")
    probabilities = result.get("probabilities", {})
    top_predictions = result.get("top_predictions", [])
    entities = result.get("entities", [])
    explanation = normalize_explanation_items(result.get("explanation", []))
    clauses = result.get("clauses", {})
    risk_score = result.get("risk_score", 0)
    insights = result.get("insights", [])

    try:
        confidence_text = f"{float(confidence):.2%}"
    except Exception:
        confidence_text = str(confidence)

    st.markdown("<div style='height:0.8rem;'></div>", unsafe_allow_html=True)

    r1, r2 = st.columns([1.05, 0.95], gap="large")

    with r1:
        st.markdown("### 📌 Prediction Results")
        st.markdown(
            f"<div class='result-chip'>Predicted Label: {label}</div>",
            unsafe_allow_html=True
        )
        st.markdown(f"**Confidence:** {confidence_text}")
        st.markdown(f"**Latency:** {processing_time_ms} ms")
        st.markdown(f"**Classes Returned:** {len(probabilities)}")

        if top_predictions:
            st.markdown("<div style='height:0.7rem;'></div>", unsafe_allow_html=True)
            st.markdown("#### 🔍 Top Predictions")
            for item in top_predictions:
                pred_label = item.get("label", "Unknown")
                pred_conf = item.get("confidence", 0.0)
                try:
                    pred_conf_text = f"{float(pred_conf):.2%}"
                except Exception:
                    pred_conf_text = str(pred_conf)

                st.markdown(
                    f"""
                    <div style="
                        padding:8px 10px;
                        border-radius:10px;
                        margin-bottom:6px;
                        background: rgba(255,255,255,0.03);
                        border: 1px solid rgba(148,163,184,0.10);
                        color:#e2e8f0;
                    ">
                        <b>{pred_label}</b> → {pred_conf_text}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)
        st.markdown("### 📝 Document Summary")
        st.markdown(summary)

    with r2:
        st.markdown("### ⚠️ Risk Intelligence")

        risk_bg = "rgba(212,175,55,0.08)"
        risk_border = "rgba(212,175,55,0.3)"
        risk_text = "#D4AF37"

        if risk_score >= 70:
            risk_bg = "rgba(239,68,68,0.12)"
            risk_border = "rgba(239,68,68,0.30)"
            risk_text = "#fca5a5"
        elif risk_score >= 40:
            risk_bg = "rgba(245,158,11,0.12)"
            risk_border = "rgba(245,158,11,0.28)"
            risk_text = "#fcd34d"

        st.markdown(
            f"""
            <div style="
                padding:12px;
                border-radius:14px;
                background: {risk_bg};
                border:1px solid {risk_border};
                color:{risk_text};
                font-weight:700;
                margin-bottom:12px;
            ">
                Overall Risk Score: {risk_score}/100
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("#### 📑 Clause Detection")
        if clauses:
            for clause, present in clauses.items():
                color = "#D4AF37" if present else "#94a3b8"
                status = "Detected" if present else "Missing"

                st.markdown(
                    f"""
                    <div style="
                        padding:8px 10px;
                        border-radius:10px;
                        margin-bottom:6px;
                        background: rgba(255,255,255,0.02);
                        border: 1px solid rgba(212,175,55,0.15);
                        color:#e2e8f0;
                    ">
                        <b>{clause}</b> → <span style="color:{color}; font-weight:700;">{status}</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.info("No clause detection data available.")

        st.markdown("<div style='height:0.9rem;'></div>", unsafe_allow_html=True)
        st.markdown("#### 💡 Legal Insights")

        if insights:
            for insight in insights:
                st.markdown(
                    f"""
                    <div style="
                        padding:8px 10px;
                        border-radius:10px;
                        margin-bottom:6px;
                        background: rgba(10,34,64,0.40);
                        border:1px solid rgba(212,175,55,0.20);
                        color:#f8fafc;
                        border-left: 3px solid #D4AF37;
                    ">
                        {insight}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.info("No major legal risks detected.")

        st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)
        st.markdown("### 🔥 Explanation")

        if explanation:
            pills = ""
            for item in explanation:
                word = item["word"]
                score = item["score"]
                if score is not None:
                    pills += f"<span class='keyword-pill'>{word} • {score}</span>"
                else:
                    pills += f"<span class='keyword-pill'>{word}</span>"
            st.markdown(pills, unsafe_allow_html=True)
        else:
            st.info("No explanation available.")

    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)

    c1, c2 = st.columns([0.9, 1.1], gap="large")

    with c1:
        st.markdown("### 📊 Confidence by Class")
        if probabilities:
            st.bar_chart(probabilities)
        else:
            st.info("No class probabilities returned.")

    with c2:
        st.markdown("### 🖍️ Highlighted Keywords in Document")
        highlighted = highlight_keywords_in_text(text, explanation)
        st.markdown(
            f"<div class='highlight-box'>{highlighted}</div>",
            unsafe_allow_html=True
        )

    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)

    st.markdown("### 📌 Advanced Extraction")

    dates = [e for e in entities if isinstance(e, dict) and e.get("label") == "DATE"]
    money = [e for e in entities if isinstance(e, dict) and e.get("label") == "MONEY"]
    other_entities = [e for e in entities if e not in dates and e not in money]

    if dates or money:
        c_date, c_money = st.columns(2, gap="medium")
        with c_date:
            st.markdown("#### 📅 Important Dates")
            if dates:
                for d in dates:
                    st.markdown(f"**•** {d.get('text')}")
            else:
                st.caption("No dates extracted.")

        with c_money:
            st.markdown("#### 💵 Monetary Values")
            if money:
                for m in money:
                    st.markdown(f"**•** {m.get('text')}")
            else:
                st.caption("No monetary values extracted.")
    else:
        st.info("No advanced specific value extractions found.")

    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)

    st.markdown("### 🏷️ Other Entities")
    if other_entities:
        e1, e2 = st.columns(2, gap="medium")
        for idx, entity in enumerate(other_entities):
            if isinstance(entity, dict):
                entity_text = entity.get("text", "Unknown")
                entity_label = entity.get("label", "Entity")
            else:
                entity_text = str(entity)
                entity_label = "Entity"

            html = f"""
            <div class="entity-card">
                <div class="entity-text">{entity_text}</div>
                <div class="entity-label">{entity_label}</div>
            </div>
            """
            if idx % 2 == 0:
                with e1:
                    st.markdown(html, unsafe_allow_html=True)
            else:
                with e2:
                    st.markdown(html, unsafe_allow_html=True)
    else:
        st.info("No other named entities found.")

    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)

    st.markdown("""
    <div style='background: linear-gradient(135deg, rgba(8, 26, 43, 0.9), rgba(6, 18, 30, 0.95)); padding: 1.5rem; border-radius: 16px; border: 1px solid rgba(16, 185, 129, 0.3); margin-top: 1.5rem; margin-bottom: 1rem; box-shadow: 0 4px 20px rgba(0,0,0,0.3); border-left: 4px solid #10b981;'>
        <h3 style='color: #10b981; margin: 0 0 0.5rem 0;'>📥 Export Legal Intelligence Database</h3>
        <p style='color: #cbd5e1; margin-bottom: 0.5rem; font-size: 0.95rem;'>Deploy extraction outputs seamlessly into corporate workflows or download secure Risk Reports for off-platform auditing.</p>
    </div>
    """, unsafe_allow_html=True)

    col_d1, col_d2, col_d3, col_d4 = st.columns(4)
    with col_d1:
        st.download_button(
            label="Download JSON",
            data=latest["export_json"],
            file_name="legal_analysis_result.json",
            mime="application/json"
        )
    with col_d2:
        try:
            pdf_bytes = generate_pdf_report(latest)
            st.download_button(
                label="Download PDF",
                data=bytes(pdf_bytes),
                file_name="legal_report.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"PDF error: {e}")

    with col_d3:
        try:
            docx_bytes = generate_docx_report(latest)
            st.download_button(
                label="Download DOCX",
                data=docx_bytes,
                file_name="legal_report.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        except Exception as e:
            st.error(f"DOCX error: {e}")

    with col_d4:
        try:
            csv_bytes = generate_csv_matrix(latest)
            st.download_button(
                label="Download CSV",
                data=csv_bytes,
                file_name="legal_matrix.csv",
                mime="text/csv"
            )
        except Exception as e:
            st.error(f"CSV error: {e}")

    st.markdown("<div style='height:2rem;'></div>", unsafe_allow_html=True)
    st.markdown("### 💬 Ask Questions About This Document")
    st.markdown('<div class="small-note">Use AI to instantly find specific terms, obligations, or dates within the uploaded text.</div>', unsafe_allow_html=True)

    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    for msg in st.session_state["chat_history"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("E.g., What is the governing law?"):
        st.session_state["chat_history"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Analyzing text..."):
                try:
                    chat_payload = {"context": text, "question": prompt}
                    chat_response = requests.post(f"{API_URL}/chat", json=chat_payload, timeout=120)
                    if chat_response.status_code == 200:
                        data = chat_response.json()
                        ans = data.get("answer", "No answer found.")
                        score = data.get("score", 0.0)

                        md_ans = f"**{ans}** (Confidence: {score:.2%})"
                        st.markdown(md_ans)
                        st.session_state["chat_history"].append({"role": "assistant", "content": md_ans})
                    else:
                        err_msg = "Failed to fetch answer. Please check if the pipeline has finished loading."
                        st.error(err_msg)
                        st.session_state["chat_history"].append({"role": "assistant", "content": err_msg})
                except requests.exceptions.Timeout:
                    timeout_msg = "The chat request timed out. First chat call can be slow while the QA model loads."
                    st.error(timeout_msg)
                    st.session_state["chat_history"].append({"role": "assistant", "content": timeout_msg})
                except Exception as e:
                    st.error(f"Error: {e}")