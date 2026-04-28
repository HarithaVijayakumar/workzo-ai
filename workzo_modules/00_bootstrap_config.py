# WorkZo modular split v138
# Source: app_workzo_v137_stable_no_feature_change.py, lines 1-2110


import os
import re
import time
import json
import csv
import hashlib
import html
import uuid
import base64
from pathlib import Path
from io import BytesIO
import urllib.parse
import urllib.request
import subprocess
import tempfile
import shutil
from typing import Dict, Optional, List, Tuple

import pdfplumber

try:
    import fitz  # PyMuPDF - fallback PDF extraction
except ImportError:
    fitz = None

try:
    from pdfminer.high_level import extract_text as pdfminer_extract_text
    from pdfminer.layout import LAParams
except ImportError:
    pdfminer_extract_text = None
    LAParams = None
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

try:
    import pycountry
except ImportError:
    pycountry = None

try:
    import geonamescache
except ImportError:
    geonamescache = None

try:
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
except ImportError:
    SimpleDocTemplate = None
    Paragraph = None
    ParagraphStyle = None
    Spacer = None
    getSampleStyleSheet = None
    A4 = None
    mm = None
    Table = None
    TableStyle = None
    KeepTogether = None
    colors = None

try:
    from docx import Document
    from docx.shared import Pt, Inches
    from docx.enum.text import WD_ALIGN_PARAGRAPH
except ImportError:
    Document = None
    Pt = None
    Inches = None
    WD_ALIGN_PARAGRAPH = None


def get_streamlit_secret(key: str, default=None):
    try:
        return st.secrets[key]
    except Exception:
        return default


# =========================================================
# ADVANCED COUNTRY CV TEMPLATE RULES (WorkZo v5.8)
# =========================================================
CV_COUNTRY_RULES = {
    "Germany": {
        "photo": True, "dob": True, "pages": 2,
        "avoid": "Avoid long paragraphs; photo and date of birth are optional and should not be invented.",
        "sections": ["Personal Information", "Professional Summary", "Work Experience", "Education", "Skills", "Languages", "Certifications"]
    },
    "Austria": {
        "photo": True, "dob": False, "pages": 2,
        "avoid": "Do not invent photo, nationality, marital status or visa details.",
        "sections": ["Personal Information", "Professional Summary", "Work Experience", "Education", "Skills", "Languages"]
    },
    "Switzerland": {
        "photo": True, "dob": False, "pages": 2,
        "avoid": "Keep formal and concise; do not invent personal details.",
        "sections": ["Profile", "Work Experience", "Education", "Skills", "Languages", "Certifications"]
    },
    "Canada": {
        "photo": False, "dob": False, "pages": 2,
        "avoid": "Never include photo, date of birth, marital status, nationality, religion, gender, full street address, or sensitive personal details.",
        "sections": ["Professional Summary", "Core Skills", "Professional Experience", "Projects", "Education", "Certifications", "Languages"]
    },
    "United States": {
        "photo": False, "dob": False, "pages": 1,
        "avoid": "Never include photo, date of birth, marital status, nationality, religion, gender, or full personal address.",
        "sections": ["Professional Summary", "Skills", "Professional Experience", "Projects", "Education"]
    },
    "United Kingdom": {
        "photo": False, "dob": False, "pages": 2,
        "avoid": "Do not include photo, date of birth, marital status, nationality, or sensitive personal details.",
        "sections": ["Professional Profile", "Key Skills", "Work Experience", "Education", "Certifications"]
    },
    "Australia": {
        "photo": False, "dob": False, "pages": 3,
        "avoid": "Do not include photo, date of birth, marital status, nationality, or sensitive personal details.",
        "sections": ["Professional Summary", "Key Skills", "Professional Experience", "Projects", "Education", "Certifications"]
    },
    "Netherlands": {
        "photo": False, "dob": False, "pages": 2,
        "avoid": "Keep it direct and concise; avoid unnecessary personal details.",
        "sections": ["Profile", "Work Experience", "Education", "Skills", "Languages"]
    },
    "France": {
        "photo": True, "dob": False, "pages": 2,
        "avoid": "Photo is optional; do not invent personal details.",
        "sections": ["Profil", "Experience professionnelle", "Formation", "Competences", "Langues"]
    },
    "India": {
        "photo": False, "dob": False, "pages": 2,
        "avoid": "Avoid unnecessary personal details; focus on skills, projects, tools, achievements, and education.",
        "sections": ["Professional Summary", "Skills", "Work Experience", "Projects", "Education", "Certifications"]
    },
    "Singapore": {
        "photo": False, "dob": False, "pages": 2,
        "avoid": "Keep it concise and ATS-friendly; avoid sensitive personal details.",
        "sections": ["Professional Summary", "Skills", "Experience", "Education", "Certifications", "Languages"]
    },
}

def get_country_cv_rules(country):
    return CV_COUNTRY_RULES.get(country,{
        "photo":False,
        "dob":False,
        "pages":2,
        "sections":["Professional Summary","Work Experience","Education","Skills"]
    })


# =========================================================
# COUNTRY-SPECIFIC CV HONESTY / COMPLIANCE RULES (WorkZo v11.5)
# =========================================================
COUNTRY_HONESTY_RULES = {
    "United States": {"format_name":"ATS-standard resume","layout":"single_column","recommended_sections":["Professional Summary","Skills","Professional Experience","Projects","Education"],"avoid_fields":["photo","date_of_birth","marital_status","nationality","religion","gender","full_street_address"],"optional_fields":[],"recommended_fields":["city_or_region","linkedin","tools","quantified_achievements"],"notes":"US resumes should avoid personal demographic details and stay highly ATS-friendly."},
    "Canada": {"format_name":"ATS-standard resume","layout":"single_column","recommended_sections":["Professional Summary","Core Skills","Professional Experience","Projects","Education"],"avoid_fields":["photo","date_of_birth","marital_status","nationality","religion","gender","full_street_address"],"optional_fields":[],"recommended_fields":["city_or_region","linkedin","tools","quantified_achievements"],"notes":"Canadian resumes are usually concise and should not include photos or sensitive personal details."},
    "Germany": {"format_name":"Lebenslauf","layout":"single_column_or_clean_two_column","recommended_sections":["Personal Information","Professional Summary","Work Experience","Projects","Education","Skills","Languages"],"avoid_fields":["religion","marital_status","invented_personal_details"],"optional_fields":["photo","date_of_birth","nationality","visa_status"],"recommended_fields":["city","linkedin","languages","certifications_if_available","clear_dates"],"notes":"Photos and DOB are sometimes seen in German CVs but should be optional. Never invent personal details."},
    "Austria": {"format_name":"Lebenslauf","layout":"single_column_or_clean_two_column","recommended_sections":["Personal Information","Professional Summary","Work Experience","Education","Skills","Languages"],"avoid_fields":["religion","marital_status","invented_personal_details"],"optional_fields":["photo","nationality","visa_status"],"recommended_fields":["city","linkedin","languages","clear_dates"],"notes":"Keep it formal, clear, and truthful; personal details are optional and should be user-confirmed."},
    "Switzerland": {"format_name":"Swiss CV","layout":"clean_two_column_allowed","recommended_sections":["Profile","Work Experience","Education","Skills","Languages","Certifications"],"avoid_fields":["invented_personal_details"],"optional_fields":["photo","nationality","work_permit","date_of_birth"],"recommended_fields":["city","languages","work_permit_if_relevant","clear_dates"],"notes":"Swiss CVs may include more personal details than US/UK CVs, but WorkZo should ask before adding them."},
    "United Kingdom": {"format_name":"UK CV","layout":"single_column","recommended_sections":["Personal Statement","Key Skills","Work Experience","Education","Certifications"],"avoid_fields":["photo","date_of_birth","marital_status","nationality","religion","gender"],"optional_fields":[],"recommended_fields":["city_or_region","linkedin","right_to_work_if_relevant"],"notes":"UK CVs should avoid photos and sensitive details; a strong personal statement and key skills section help."},
    "France": {"format_name":"CV francais","layout":"single_column_or_clean_two_column","recommended_sections":["Profil","Experience professionnelle","Formation","Competences","Langues"],"avoid_fields":["invented_personal_details"],"optional_fields":["photo","permit_status"],"recommended_fields":["city","languages","clear_dates"],"notes":"A photo may be seen in France but should be optional; keep content truthful and concise."},
    "India": {"format_name":"ATS-friendly resume","layout":"single_column","recommended_sections":["Professional Summary","Skills","Work Experience","Projects","Education","Certifications"],"avoid_fields":["religion","marital_status","invented_personal_details"],"optional_fields":["city","linkedin"],"recommended_fields":["technical_skills","projects","certifications_if_available","clear_dates"],"notes":"Keep it skills/project-focused. Avoid unnecessary personal information."},
    "default": {"format_name":"ATS-friendly CV","layout":"single_column","recommended_sections":["Professional Summary","Skills","Work Experience","Projects","Education","Languages"],"avoid_fields":["invented_personal_details","sensitive_personal_details"],"optional_fields":["linkedin","city"],"recommended_fields":["clear_dates","quantified_achievements","tools"],"notes":"Use a clean, truthful, ATS-friendly structure unless the country requires another style."}
}

def get_country_honesty_rules(country: str) -> Dict:
    return COUNTRY_HONESTY_RULES.get(str(country or '').strip(), COUNTRY_HONESTY_RULES['default'])

def _has_any(text: str, terms: List[str]) -> bool:
    low = (text or '').lower()
    return any(str(t).lower() in low for t in terms if str(t).strip())

def country_specific_cv_audit(cv_text: str, country: str, structured_profile: Optional[Dict] = None) -> Dict:
    rules = get_country_honesty_rules(country)
    text = cv_text or ''
    low = text.lower()
    missing_recommended, fields_to_remove, ats_risks, suggestions = [], [], [], []
    if not _has_any(low, ['summary', 'profile', 'profil', 'personal statement', 'professional summary']): missing_recommended.append('Professional summary / profile section')
    if not _has_any(low, ['experience', 'work experience', 'professional experience', 'berufserfahrung', 'experience']): missing_recommended.append('Work experience section')
    if not _has_any(low, ['education', 'ausbildung', 'formation']): missing_recommended.append('Education section')
    if not _has_any(low, ['skills', 'kenntnisse', 'competences', 'core skills']): missing_recommended.append('Skills section')
    if ('Languages' in rules.get('recommended_sections', []) or 'languages' in rules.get('recommended_fields', [])) and not _has_any(low, ['language','languages','sprachen','langues','english','german','deutsch']): missing_recommended.append('Languages section')
    for avoid in rules.get('avoid_fields', []):
        if avoid == 'photo' and _has_any(low, ['photo','picture','portrait']): fields_to_remove.append('Photo is not recommended for this country')
        elif avoid == 'date_of_birth' and _has_any(low, ['date of birth','dob','birth date','geburtsdatum']): fields_to_remove.append('Date of birth is not recommended for this country')
        elif avoid == 'marital_status' and _has_any(low, ['marital','married','single','familienstand']): fields_to_remove.append('Marital status is not recommended for this country')
        elif avoid == 'nationality' and _has_any(low, ['nationality','staatsangehorigkeit']): fields_to_remove.append('Nationality is not recommended for this country unless specifically needed')
        elif avoid == 'full_street_address' and re.search(r'\b\d{4,6}\b.*\b(street|straÃe|strasse|weg|road|rd\.?|avenue|ave\.?)\b', low): fields_to_remove.append('Full street address can be shortened to city/region for this country')
    if rules.get('layout') == 'single_column' and _has_any(low, ['sidebar','left column','right column']): ats_risks.append('Use a single-column layout for this country to improve ATS parsing.')
    if not re.search(r'\b(19|20)\d{2}\b', text): ats_risks.append('Dates are unclear or missing. Keep clear years/months for experience and education.')
    if not re.search(r'\d+\s*%|\b\d+\+|\b\d+\s*(users|tickets|clients|projects|reports|dashboards)\b', low): suggestions.append('Add quantified achievements where truthful, such as ticket volume, response-time improvement, dashboards, or projects.')
    optional_prompts = [f"{field.replace('_',' ').title()}: optional for {country}; add only if comfortable and truthful." for field in rules.get('optional_fields', [])]
    return {'country':country or 'General','format_name':rules.get('format_name','ATS-friendly CV'),'layout':rules.get('layout','single_column'),'recommended_sections':rules.get('recommended_sections',[]),'missing_recommended_fields':missing_recommended,'fields_to_remove':fields_to_remove,'optional_country_fields':optional_prompts,'honesty_flags':[],'ats_risks':ats_risks,'suggestions':suggestions,'notes':rules.get('notes','')}

def render_country_specific_honesty_audit(cv_text: str, country: str, structured_profile: Optional[Dict] = None, expanded: bool = False) -> Dict:
    audit = country_specific_cv_audit(cv_text, country, structured_profile)
    with st.expander(f"Country-specific honesty check — {audit.get('country','General')}", expanded=expanded):
        st.markdown(f"**Format guidance:** {html.escape(audit.get('format_name','ATS-friendly CV'))}")
        st.caption(audit.get('notes',''))
        if audit.get('recommended_sections'): st.markdown('**Recommended sections:** ' + ', '.join(audit.get('recommended_sections', [])))
        if audit.get('missing_recommended_fields'):
            st.warning('Missing / weak recommended fields:')
            for item in audit.get('missing_recommended_fields', []): st.markdown(f"- {html.escape(str(item))}")
        if audit.get('fields_to_remove'):
            st.error('Fields to remove or reconsider for this country:')
            for item in audit.get('fields_to_remove', []): st.markdown(f"- {html.escape(str(item))}")
        if audit.get('optional_country_fields'):
            st.info('Optional country fields — user confirmation required:')
            for item in audit.get('optional_country_fields', []): st.markdown(f"- {html.escape(str(item))}")
        if audit.get('ats_risks'):
            st.warning('ATS / parsing risks:')
            for item in audit.get('ats_risks', []): st.markdown(f"- {html.escape(str(item))}")
        if audit.get('suggestions'):
            st.markdown('**Honest improvement suggestions:**')
            for item in audit.get('suggestions', []): st.markdown(f"- {html.escape(str(item))}")
        if not any(audit.get(k) for k in ['missing_recommended_fields','fields_to_remove','ats_risks','suggestions']): st.success('No major country-specific issues detected.')
    return audit

# =========================================================
# PAGE CONFIG + LOGO PATHS
# =========================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_PATH = os.path.join(BASE_DIR, "workzo_icon.png")
LOGO_PATH = os.path.join(BASE_DIR, "logo.png")

# Use the optimized WorkZo favicon/app icon when it exists.
# Keep logo.png as a fallback so older deployments do not break.
PAGE_ICON = ICON_PATH if os.path.exists(ICON_PATH) else (LOGO_PATH if os.path.exists(LOGO_PATH) else "")

st.set_page_config(
    page_title="WorkZo AI",
    page_icon=PAGE_ICON,
    layout="wide"
)

# =========================================================
# LOAD ENV
# =========================================================
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY") or get_streamlit_secret("OPENAI_API_KEY")
if not api_key:
    st.error("OPENAI_API_KEY not found. Please check your .env file or Streamlit secrets.")
    st.stop()

client = OpenAI(api_key=api_key)

# --- AUTO UI TRANSLATION LAYER ---
@st.cache_data(show_spinner=False)
def ai_translate_ui(text, language):
    try:
        if not language or language=="English":
            return text
        prompt=f"Translate the following UI label into {language}. Keep it short. Only return the translation. Text: {text}"
        r=client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"user","content":prompt}],
            temperature=0.2,
        )
        return r.choices[0].message.content.strip()
    except Exception:
        return text


# =========================================================
# RATE LIMITING
# =========================================================
MAX_REQUESTS_PER_HOUR = 25
SCORING_VERSION = "v5.8_antidrift_schema_pipeline"

if "request_count" not in st.session_state:
    st.session_state.request_count = 0

if "first_request_time" not in st.session_state:
    st.session_state.first_request_time = time.time()

if time.time() - st.session_state.first_request_time > 3600:
    st.session_state.request_count = 0
    st.session_state.first_request_time = time.time()

def can_make_request() -> bool:
    return st.session_state.request_count < MAX_REQUESTS_PER_HOUR

# Analytics files (defined early so startup analytics never crash)
ANALYTICS_FILE = os.path.join(BASE_DIR, "workzo_beta_analytics.csv")
FEEDBACK_FILE = os.path.join(BASE_DIR, "workzo_beta_feedback.csv")
ISSUES_FILE = os.path.join(BASE_DIR, "workzo_beta_issues.csv")

# =========================================================
# NAVIGATION / SCROLL HELPERS
# =========================================================
def request_scroll_to_top() -> None:
    """Mark the next render as a fresh page transition.

    No iframe, no components.html, no JavaScript. Streamlit cannot directly
    control the browser viewport natively, so we use a tiny query-param nonce
    to make navigation a fresh state change and render a top anchor first.
    """
    import time as _time
    st.session_state["_workzo_scroll_to_top"] = True
    st.session_state["_workzo_page_nonce"] = str(int(_time.time() * 1000))


def maybe_scroll_to_top() -> None:
    """Native, warning-free page reset marker.

    This removes deprecated st.components.v1.html usage. It also prevents the
    app from creating hidden HTML iframes that were causing warnings and layout
    instability. The top anchor is rendered at the beginning of every page.
    """
    st.markdown('<span id="workzo-page-top"></span>', unsafe_allow_html=True)
    if st.session_state.pop("_workzo_scroll_to_top", False):
        try:
            st.query_params["wz_view"] = st.session_state.get("_workzo_page_nonce", "top")
        except Exception:
            pass


def _is_valid_uuidish(value: str) -> bool:
    return bool(re.fullmatch(r"[a-fA-F0-9-]{24,80}", str(value or "")))


def _inject_persistent_user_id_script(uid: str) -> None:
    """Deprecated browser localStorage bridge removed.

    Keeps a session-only anonymous id without using st.components.v1.html,
    so Streamlit no longer shows the 2026 deprecation warning.
    """
    try:
        st.session_state.setdefault("anonymous_user_id", str(uid or ""))
    except Exception:
        pass




def _ensure_analytics_paths() -> None:
    """Defensive fallback for older patched builds where analytics constants may be missing."""
    global ANALYTICS_FILE, FEEDBACK_FILE, ISSUES_FILE
    try:
        base = BASE_DIR
    except Exception:
        base = os.getcwd()
    ANALYTICS_FILE = globals().get("ANALYTICS_FILE") or os.path.join(base, "workzo_beta_analytics.csv")
    FEEDBACK_FILE = globals().get("FEEDBACK_FILE") or os.path.join(base, "workzo_beta_feedback.csv")
    ISSUES_FILE = globals().get("ISSUES_FILE") or os.path.join(base, "workzo_beta_issues.csv")

_ensure_analytics_paths()

def _has_prior_user_events(uid: str) -> bool:
    if not uid or not os.path.exists(ANALYTICS_FILE):
        return False
    try:
        with open(ANALYTICS_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return any((r.get("anonymous_user_id") or "") == uid for r in reader)
    except Exception:
        return False




def _query_param_value(key: str, default: str = "") -> str:
    """Return a single query-param value safely across Streamlit versions.

    Works with st.query_params (new) and experimental_get_query_params (old).
    Never raises during normal app startup.
    """
    try:
        # New Streamlit API: st.query_params behaves like a mapping.
        params = getattr(st, "query_params", None)
        if params is not None:
            value = params.get(key, default)
            if isinstance(value, list):
                return str(value[0]) if value else default
            return str(value) if value is not None else default
    except Exception:
        pass

    try:
        # Backward-compatible fallback.
        params = st.experimental_get_query_params()
        value = params.get(key, [default])
        if isinstance(value, list):
            return str(value[0]) if value else default
        return str(value) if value is not None else default
    except Exception:
        return default


def get_or_create_anonymous_user_id() -> str:
    url_uid = _query_param_value("wz_uid", "")
    session_uid = st.session_state.get("anonymous_user_id", "")

    if _is_valid_uuidish(url_uid):
        uid = url_uid
    elif _is_valid_uuidish(session_uid):
        uid = session_uid
    else:
        uid = str(uuid.uuid4())

    prior = _has_prior_user_events(uid)
    st.session_state.anonymous_user_id = uid
    st.session_state.is_repeat_user = bool(prior or st.session_state.get("is_repeat_user", False))
    _inject_persistent_user_id_script(uid)
    return uid

def get_or_create_session_id() -> str:
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.session_started_at = time.time()
    return st.session_state.session_id

def init_beta_analytics():
    _ensure_analytics_paths()
    get_or_create_anonymous_user_id()
    get_or_create_session_id()
    if "feature_usage_counts" not in st.session_state:
        st.session_state.feature_usage_counts = {}
    if "analytics_events" not in st.session_state:
        st.session_state.analytics_events = []
    if "last_tracked_page" not in st.session_state:
        st.session_state.last_tracked_page = ""

def safe_analytics_value(value):
    if value is None:
        return ""
    value = str(value)
    if len(value) > 120:
        value = value[:120] + "..."
    return value.replace("\n", " ").replace("\r", " ").strip()

def send_analytics_to_webhook(event: Dict):
    webhook_url = os.getenv("ANALYTICS_WEBHOOK_URL") or get_streamlit_secret("ANALYTICS_WEBHOOK_URL")
    if not webhook_url:
        return
    try:
        data = json.dumps(event).encode("utf-8")
        req = urllib.request.Request(
            webhook_url,
            data=data,
            headers={"Content-Type": "application/json", "User-Agent": "WorkZoAI-Beta"}
        )
        urllib.request.urlopen(req, timeout=4)
    except Exception:
        pass

def track_event(event_name: str, feature: str = "", metadata: Optional[Dict] = None):
    init_beta_analytics()
    metadata = metadata or {}
    session_duration_seconds = int(time.time() - st.session_state.get("session_started_at", time.time()))

    event = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "anonymous_user_id": st.session_state.get("anonymous_user_id", ""),
        "session_id": st.session_state.get("session_id", ""),
        "event_name": safe_analytics_value(event_name),
        "feature": safe_analytics_value(feature),
        "session_duration_seconds": session_duration_seconds,
        "repeat_user": safe_analytics_value(st.session_state.get("is_repeat_user", False)),
        "country": safe_analytics_value(st.session_state.get("country", "")),
        "migration_country": safe_analytics_value(st.session_state.get("migration_country", "")),
        "user_status": safe_analytics_value(st.session_state.get("user_status", "")),
        "preferred_language": safe_analytics_value(st.session_state.get("preferred_language", "")),
        "cv_uploaded": safe_analytics_value(bool(st.session_state.get("cv_text", ""))),
        "metadata": safe_analytics_value(json.dumps(metadata, ensure_ascii=False)),
    }

    st.session_state.analytics_events.append(event)

    if feature:
        st.session_state.feature_usage_counts[feature] = st.session_state.feature_usage_counts.get(feature, 0) + 1

    try:
        file_exists = os.path.exists(ANALYTICS_FILE)
        with open(ANALYTICS_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(event.keys()))
            if not file_exists:
                writer.writeheader()
            writer.writerow(event)
    except Exception:
        pass

    send_analytics_to_webhook(event)

def track_feature_view(feature_name: str):
    if st.session_state.get("last_tracked_page") != feature_name:
        track_event("feature_view", feature_name)
        st.session_state.last_tracked_page = feature_name

def track_button_click(button_name: str, feature: str = "", metadata: Optional[Dict] = None):
    meta = {"button": button_name}
    if metadata:
        meta.update(metadata)
    track_event("button_click", feature or button_name, meta)


def read_csv_rows(file_path: str) -> List[Dict]:
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)
    except Exception:
        return []

def render_founder_dashboard():
    st.markdown("### Founder Analytics Dashboard")
    st.caption("Private beta metrics for Reddit/testing. Numbers are privacy-safe and approximate, but now focused on product decisions.")

    rows = read_csv_rows(ANALYTICS_FILE)
    feedback_rows = read_csv_rows(FEEDBACK_FILE)
    issue_rows = read_csv_rows(ISSUES_FILE) if os.path.exists(ISSUES_FILE) else []

    if not rows:
        st.info("No analytics events recorded yet.")
        return

    # -----------------------------
    # Helpers
    # -----------------------------
    def _safe_int(value, default=0):
        try:
            return int(float(value or 0))
        except Exception:
            return default

    def _event_name(r):
        return (r.get("event_name", "") or "").strip()

    def _feature_name(r):
        return (r.get("feature", "") or "Unknown").strip() or "Unknown"

    def _uid(r):
        return (r.get("anonymous_user_id", "") or "").strip()

    def _sid(r):
        return (r.get("session_id", "") or "").strip()

    def _country(r):
        return (r.get("country", "") or "Unknown").strip() or "Unknown"

    def _status(r):
        return (r.get("user_status", "") or "Unknown").strip() or "Unknown"

    def _count_by(key: str, source_rows=None):
        source_rows = source_rows or rows
        counts = {}
        for r in source_rows:
            value = r.get(key, "") or "Unknown"
            counts[value] = counts.get(value, 0) + 1
        return sorted(counts.items(), key=lambda x: x[1], reverse=True)

    def _count_by_func(fn, source_rows=None):
        source_rows = source_rows or rows
        counts = {}
        for r in source_rows:
            value = fn(r) or "Unknown"
            counts[value] = counts.get(value, 0) + 1
        return sorted(counts.items(), key=lambda x: x[1], reverse=True)

    def _has_event(names):
        names = {n.lower() for n in names}
        return sum(1 for r in rows if _event_name(r).lower() in names)

    def _sessions_with(predicate):
        sessions = set()
        for r in rows:
            sid = _sid(r)
            if sid and predicate(r):
                sessions.add(sid)
        return sessions

    def _users_with(predicate):
        users = set()
        for r in rows:
            uid = _uid(r)
            if uid and predicate(r):
                users.add(uid)
        return users

    # -----------------------------
    # Core counts
    # -----------------------------
    total_events = len(rows)
    unique_users = len({_uid(r) for r in rows if _uid(r)})
    unique_sessions = len({_sid(r) for r in rows if _sid(r)})

    user_sessions = {}
    user_dates = {}
    user_repeat_flags = {}
    for r in rows:
        uid, sid = _uid(r), _sid(r)
        if uid:
            if sid:
                user_sessions.setdefault(uid, set()).add(sid)
            ts = (r.get("timestamp", "") or "").strip()[:10]
            if ts:
                user_dates.setdefault(uid, set()).add(ts)
            if str(r.get("repeat_user", "")).lower() in {"true", "1", "yes"}:
                user_repeat_flags[uid] = True

    returning_user_ids = {
        uid for uid in set(list(user_sessions.keys()) + list(user_dates.keys()) + list(user_repeat_flags.keys()))
        if len(user_sessions.get(uid, set())) > 1 or len(user_dates.get(uid, set())) > 1 or user_repeat_flags.get(uid, False)
    }
    returning_users = len(returning_user_ids)
    return_rate = round((returning_users / unique_users) * 100, 1) if unique_users else 0

    durations = [_safe_int(r.get("session_duration_seconds")) for r in rows]
    avg_event_time = int(sum(durations) / len(durations)) if durations else 0
    max_event_time = max(durations) if durations else 0

    active_sessions = {
        sid for sid in {_sid(r) for r in rows if _sid(r)}
        if max(_safe_int(x.get("session_duration_seconds")) for x in rows if _sid(x) == sid) >= 60
    }

    # -----------------------------
    # Funnel / activation
    # -----------------------------
    onboarding_sessions = _sessions_with(lambda r: "onboarding" in _feature_name(r).lower() or "onboarding" in _event_name(r).lower())
    dashboard_sessions = _sessions_with(lambda r: "dashboard" in _feature_name(r).lower())
    job_assist_sessions = _sessions_with(lambda r: "job assist" in _feature_name(r).lower() or "job_assist" in _event_name(r).lower())
    cv_doc_sessions = _sessions_with(lambda r: "cv" in _feature_name(r).lower() or "document" in _feature_name(r).lower() or "resume" in _feature_name(r).lower())
    workobot_sessions = _sessions_with(lambda r: "work-o-bot" in _feature_name(r).lower() or "workobot" in _feature_name(r).lower())
    prepared_sessions = _sessions_with(lambda r: "application_prepared" in _event_name(r).lower())
    saved_sessions = _sessions_with(lambda r: "application_saved" in _event_name(r).lower())
    button_sessions = _sessions_with(lambda r: "button" in _event_name(r).lower())

    activated_sessions = job_assist_sessions | cv_doc_sessions | workobot_sessions | prepared_sessions
    activation_rate = round((len(activated_sessions) / unique_sessions) * 100, 1) if unique_sessions else 0
    prepared_rate = round((len(prepared_sessions) / unique_sessions) * 100, 1) if unique_sessions else 0

    # -----------------------------
    # Header metrics
    # -----------------------------
    st.markdown("#### Beta health")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Events", total_events)
    c2.metric("Users*", unique_users)
    c3.metric("Sessions", unique_sessions)
    c4.metric("Avg time", f"{avg_event_time // 60}m {avg_event_time % 60}s")

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Returning users*", returning_users, f"{return_rate}%")
    c6.metric("Active sessions", len(active_sessions))
    c7.metric("Activation rate", f"{activation_rate}%")
    c8.metric("Prepared jobs", len(prepared_sessions))

    st.caption("*Returning users are tracked with an anonymous browser ID stored in localStorage and mirrored as wz_uid in the URL. Older analytics may still undercount repeat users until users revisit after this update. Treat trends as more important than exact numbers.")

    st.markdown("#### Retention details")
    r1, r2, r3 = st.columns(3)
    r1.metric("Repeat user IDs", returning_users)
    r2.metric("Users with 2+ sessions", sum(1 for s in user_sessions.values() if len(s) > 1))
    r3.metric("Users active 2+ days", sum(1 for d in user_dates.values() if len(d) > 1))


    # -----------------------------
    # Product decision cards
    # -----------------------------
    st.markdown("#### Founder insights")
    insight_1 = "Users are opening the app, but deeper feature discovery is still low."
    if activation_rate >= 25:
        insight_1 = "Good: users are reaching core features. Now improve completion and repeat usage."
    elif activation_rate >= 10:
        insight_1 = "Some users are reaching core features. Make the main workflow more obvious."

    insight_2 = "Job Assist / Prepare for Job should be highlighted as the main Reddit test flow."
    if len(prepared_sessions) >= 5:
        insight_2 = "Prepare for Job has started getting usage. Watch how many users continue to CV/Cover Letter."

    insight_3 = "Ask Reddit testers to do one clear task: paste a job + upload/create CV + prepare application."
    if feedback_rows:
        insight_3 = "You have feedback. Read repeated complaints before sharing wider."

    i1, i2, i3 = st.columns(3)
    with i1:
        st.markdown(f"<div class='next-action-card'><div class='next-action-label'>Discovery</div><div class='next-action-title'>{html.escape(insight_1)}</div></div>", unsafe_allow_html=True)
    with i2:
        st.markdown(f"<div class='next-action-card'><div class='next-action-label'>Core feature</div><div class='next-action-title'>{html.escape(insight_2)}</div></div>", unsafe_allow_html=True)
    with i3:
        st.markdown(f"<div class='next-action-card'><div class='next-action-label'>Reddit test task</div><div class='next-action-title'>{html.escape(insight_3)}</div></div>", unsafe_allow_html=True)

    # -----------------------------
    # Funnel
    # -----------------------------
    st.markdown("#### User journey funnel")
    funnel_steps = [
        ("Opened app", unique_sessions),
        ("Onboarding", len(onboarding_sessions)),
        ("Dashboard", len(dashboard_sessions)),
        ("Used core feature", len(activated_sessions)),
        ("Prepared application", len(prepared_sessions)),
        ("Saved tracker", len(saved_sessions)),
    ]

    max_funnel = max([v for _, v in funnel_steps] + [1])
    for label, value in funnel_steps:
        pct = round((value / max_funnel) * 100, 1) if max_funnel else 0
        st.markdown(f"**{label}:** {value}")
        st.progress(min(int(pct), 100))

    # -----------------------------
    # Feature usage and events
    # -----------------------------
    st.markdown("#### Feature usage")
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("##### Most used features")
        feature_counts = _count_by_func(_feature_name)
        for feature, count in feature_counts[:12]:
            st.write(f"- **{feature}**: {count}")

        st.markdown("##### Core feature reach")
        st.write(f"- **Job Assist sessions:** {len(job_assist_sessions)}")
        st.write(f"- **CV / Document sessions:** {len(cv_doc_sessions)}")
        st.write(f"- **Work-O-Bot sessions:** {len(workobot_sessions)}")
        st.write(f"- **Prepare for Job completions:** {len(prepared_sessions)}")
        st.write(f"- **Saved applications:** {len(saved_sessions)}")

    with col_b:
        st.markdown("##### Event types")
        for event, count in _count_by_func(_event_name)[:12]:
            st.write(f"- **{event}**: {count}")

        st.markdown("##### Button clicks / engagement")
        st.write(f"- **Sessions with button click:** {len(button_sessions)}")
        st.write(f"- **Max recorded session time:** {max_event_time // 60}m {max_event_time % 60}s")

    # -----------------------------
    # Audience
    # -----------------------------
    st.markdown("#### Audience")
    a1, a2, a3 = st.columns(3)
    with a1:
        st.markdown("##### Countries")
        for country, count in _count_by_func(_country)[:10]:
            st.write(f"- **{country}**: {count}")
    with a2:
        st.markdown("##### Career situations")
        for status, count in _count_by_func(_status)[:10]:
            st.write(f"- **{status}**: {count}")
    with a3:
        st.markdown("##### Languages")
        for lang, count in _count_by("preferred_language")[:10]:
            st.write(f"- **{lang}**: {count}")

    # -----------------------------
    # Completion signals
    # -----------------------------
    st.markdown("#### Value signals")
    v1, v2, v3, v4 = st.columns(4)
    v1.metric("CV uploaded events", sum(1 for r in rows if str(r.get("cv_uploaded", "")).lower() == "true"))
    v2.metric("Application prepared", len(prepared_sessions))
    v3.metric("Tracker saves", len(saved_sessions))
    v4.metric("Feedback responses", len(feedback_rows))

    # -----------------------------
    # Feedback and issues
    # -----------------------------
    st.markdown("#### Feedback quality")
    if feedback_rows:
        avg_rating_values = []
        for r in feedback_rows:
            try:
                avg_rating_values.append(int(float(r.get("rating", 0))))
            except Exception:
                pass
        avg_rating = round(sum(avg_rating_values) / len(avg_rating_values), 1) if avg_rating_values else "—"

        f1, f2, f3 = st.columns(3)
        f1.metric("Feedback responses", len(feedback_rows))
        f2.metric("Average rating", avg_rating)
        f3.metric("Issue reports", len(issue_rows))

        with st.expander("Latest feedback", expanded=False):
            for r in feedback_rows[-15:][::-1]:
                st.markdown(f"""
**Rating:** {r.get('rating','')} / 5  
**Feature:** {r.get('feature','')}  
**Worked well:** {r.get('worked_well','')}  
**Needs improvement:** {r.get('needs_improvement','')}
---
""")
    else:
        st.info("No feedback submitted yet. For Reddit testing, ask users to submit feedback after one full flow.")

    if issue_rows:
        with st.expander("Latest reported problems", expanded=False):
            for r in issue_rows[-15:][::-1]:
                st.markdown(f"""
**Feature:** {r.get('feature','')}  
**Problem:** {r.get('problem','') or r.get('issue','')}  
---
""")

    # -----------------------------
    # Reddit test checklist
    # -----------------------------
    st.markdown("#### Reddit test checklist")
    st.markdown("""
Before posting broadly, check after 24 hours:
- Did at least 20 people open the app?
- Did 5+ people reach Job Assist or Prepare for Job?
- Did at least 2 people prepare an application?
- Did anyone save a tracker item?
- Did anyone submit feedback without being pushed?
- Which feature created the most drop-off?
""")

    # -----------------------------
    # Downloads
    # -----------------------------
    st.markdown("#### Export data")
    d1, d2, d3 = st.columns(3)
    with d1:
        if os.path.exists(ANALYTICS_FILE):
            with open(ANALYTICS_FILE, "rb") as f:
                st.download_button(
                    "Download analytics CSV",
                    data=f.read(),
                    file_name="workzo_beta_analytics.csv",
                    mime="text/csv",
                    key="founder_download_analytics"
                )
    with d2:
        if os.path.exists(FEEDBACK_FILE):
            with open(FEEDBACK_FILE, "rb") as f:
                st.download_button(
                    "Download feedback CSV",
                    data=f.read(),
                    file_name="workzo_beta_feedback.csv",
                    mime="text/csv",
                    key="founder_download_feedback"
                )
    with d3:
        if os.path.exists(ISSUES_FILE):
            with open(ISSUES_FILE, "rb") as f:
                st.download_button(
                    "Download issue reports CSV",
                    data=f.read(),
                    file_name="workzo_beta_issues.csv",
                    mime="text/csv",
                    key="founder_download_issues"
                )

def save_feedback(feature: str, rating: int, worked_well: str, needs_improvement: str):
    init_beta_analytics()

    feedback = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "anonymous_user_id": st.session_state.get("anonymous_user_id", ""),
        "session_id": st.session_state.get("session_id", ""),
        "feature": safe_analytics_value(feature),
        "rating": safe_analytics_value(rating),
        "worked_well": safe_analytics_value(worked_well),
        "needs_improvement": safe_analytics_value(needs_improvement),
        "country": safe_analytics_value(st.session_state.get("country", "")),
        "migration_country": safe_analytics_value(st.session_state.get("migration_country", "")),
        "user_status": safe_analytics_value(st.session_state.get("user_status", "")),
        "preferred_language": safe_analytics_value(st.session_state.get("preferred_language", "")),
    }

    try:
        file_exists = os.path.exists(FEEDBACK_FILE)
        with open(FEEDBACK_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(feedback.keys()))
            if not file_exists:
                writer.writeheader()
            writer.writerow(feedback)
    except Exception:
        pass

    track_event("feedback_submitted", "Feedback", {"feature": feature, "rating": rating})

def render_feedback_collector(current_feature: str = ""):
    with st.expander("Share quick feedback", expanded=False):
        st.caption("Help improve WorkZo. Please do not paste CV text or personal details here.")
        feature = st.selectbox(
            "Which feature are you giving feedback on?",
            ["Overall", "Dashboard", "Job Assist", "Document Tools", "Work-O-Bot", "CV Template Builder", "Translation", "Other"],
            index=0,
            key=f"feedback_feature_{current_feature or 'general'}"
        )
        rating = st.slider("How useful was this?", 1, 5, 4, key=f"feedback_rating_{current_feature or 'general'}")
        worked_well = st.text_area("What worked well?", height=80, key=f"feedback_good_{current_feature or 'general'}")
        needs_improvement = st.text_area("What should improve?", height=80, key=f"feedback_bad_{current_feature or 'general'}")

        if st.button("Submit feedback", key=f"submit_feedback_{current_feature or 'general'}"):
            save_feedback(feature, rating, worked_well, needs_improvement)
            st.success("Thank you — your feedback was saved.")

def save_issue_report(area: str, issue_type: str, description: str):
    init_beta_analytics()
    issue = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "anonymous_user_id": st.session_state.get("anonymous_user_id", ""),
        "session_id": st.session_state.get("session_id", ""),
        "area": safe_analytics_value(area),
        "issue_type": safe_analytics_value(issue_type),
        "description": safe_analytics_value(description),
        "country": safe_analytics_value(st.session_state.get("country", "")),
        "user_status": safe_analytics_value(st.session_state.get("user_status", "")),
        "preferred_language": safe_analytics_value(st.session_state.get("preferred_language", "")),
    }
    try:
        file_exists = os.path.exists(ISSUES_FILE)
        with open(ISSUES_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(issue.keys()))
            if not file_exists:
                writer.writeheader()
            writer.writerow(issue)
    except Exception:
        pass
    track_event("issue_reported", "Issue Reporting", {"area": area, "issue_type": issue_type})

def render_issue_reporter(current_feature: str = ""):
    with st.expander("Report a problem", expanded=False):
        st.caption("Tell us what went wrong. Please do not paste private CV text or personal details.")
        area = st.selectbox(
            "Where did this happen?",
            ["Overall", "Onboarding", "Dashboard", "Job Assist", "CV Builder", "Document Tools", "Work-O-Bot", "Downloads", "Other"],
            index=0,
            key=f"issue_area_{current_feature or 'general'}"
        )
        issue_type = st.selectbox(
            "Issue type",
            ["Bug / error", "Confusing output", "Wrong language", "Too much information", "Download problem", "Job search problem", "Feature suggestion"],
            index=0,
            key=f"issue_type_{current_feature or 'general'}"
        )
        description = st.text_area("What happened?", height=90, key=f"issue_description_{current_feature or 'general'}")
        if st.button("Submit issue", key=f"submit_issue_{current_feature or 'general'}"):
            if description.strip():
                save_issue_report(area, issue_type, description)
                st.success("Thanks — the issue report was saved.")
            else:
                st.warning("Please describe the issue briefly.")

def maybe_render_founder_access():
    founder_pin = os.getenv("FOUNDER_PIN") or get_streamlit_secret("FOUNDER_PIN")

    with st.sidebar.expander(txt("founder_access"), expanded=False):
        if founder_pin:
            entered_pin = st.text_input(txt("founder_pin"), type="password", key="founder_pin_input")
            if entered_pin == founder_pin:
                st.session_state.founder_unlocked = True
                st.success("Founder mode unlocked.")
        else:
            st.caption("FOUNDER_PIN is not configured. For local testing, create a temporary PIN below. Before sharing publicly, add FOUNDER_PIN in Streamlit Secrets.")
            temp_pin = st.text_input("Temporary founder PIN", type="password", key="founder_temp_pin_input")
            if temp_pin and len(temp_pin) >= 4:
                st.session_state.founder_unlocked = True
                st.success("Founder mode unlocked for this session.")

    if st.session_state.get("founder_unlocked"):
        with st.sidebar:
            if st.button(txt("founder_dashboard"), key="open_founder_dashboard"):
                st.session_state.page = txt("founder_dashboard")


def render_beta_analytics_summary():
    init_beta_analytics()
    session_duration_seconds = int(time.time() - st.session_state.get("session_started_at", time.time()))
    minutes = session_duration_seconds // 60
    seconds = session_duration_seconds % 60

    st.markdown("### Beta Analytics")
    st.caption("Privacy-safe usage tracking. CV text, email, phone number, and documents are not stored.")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Session time", f"{minutes}m {seconds}s")
    with c2:
        st.metric("Events this session", len(st.session_state.get("analytics_events", [])))
    with c3:
        st.metric("Features used", len(st.session_state.get("feature_usage_counts", {})))

    if st.session_state.get("feature_usage_counts"):
        st.markdown("#### Feature usage this session")
        for feature, count in sorted(st.session_state.feature_usage_counts.items(), key=lambda x: x[1], reverse=True):
            st.write(f"- **{feature}**: {count}")

    if os.path.exists(ANALYTICS_FILE):
        try:
            with open(ANALYTICS_FILE, "rb") as f:
                st.download_button(
                    "Download beta analytics CSV",
                    data=f.read(),
                    file_name="workzo_beta_analytics.csv",
                    mime="text/csv",
                    key="download_beta_analytics_csv"
                )
        except Exception:
            pass


# =========================================================
# STYLES
# =========================================================
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(180deg, #0b1020 0%, #111827 22%, #0f172a 100%);
    }
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    .beta-badge {
        background: linear-gradient(135deg, #14b8a6, #2563eb);
        color: white;
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 12px;
        display: inline-block;
        font-weight: 600;
    }
    .hero-card {
        background: linear-gradient(135deg, rgba(37,99,235,0.22), rgba(20,184,166,0.16));
        border: 1px solid rgba(148,163,184,0.18);
        border-radius: 24px;
        padding: 20px 22px;
        box-shadow: 0 12px 35px rgba(2,6,23,0.25);
        margin-bottom: 14px;
    }
    .glass-card {
        border: 1px solid rgba(148,163,184,0.16);
        border-radius: 20px;
        padding: 16px;
        background: rgba(15,23,42,0.55);
        backdrop-filter: blur(8px);
        box-shadow: 0 8px 24px rgba(2,6,23,0.18);
        margin-bottom: 12px;
    }
    .metric-card {
        border: 1px solid rgba(148,163,184,0.16);
        border-radius: 20px;
        padding: 16px;
        background: linear-gradient(180deg, rgba(30,41,59,0.86), rgba(15,23,42,0.74));
        min-height: 116px;
        box-shadow: 0 8px 24px rgba(2,6,23,0.18);
    }
    .metric-label {
        color: #94a3b8;
        font-size: 0.92rem;
        margin-bottom: 8px;
    }
    .metric-value {
        color: white;
        font-size: 1.8rem;
        font-weight: 700;
        line-height: 1.1;
        margin-bottom: 6px;
    }
    .metric-foot {
        color: #cbd5e1;
        font-size: 0.9rem;
    }
    .card {
        border: 1px solid rgba(148,163,184,0.16);
        border-radius: 18px;
        padding: 16px;
        background: rgba(15,23,42,0.58);
        margin-bottom: 12px;
    }
    .section-title {
        font-size: 1.05rem;
        font-weight: 700;
        margin-bottom: 8px;
        color: #f8fafc;
    }
    .small-muted {
        color: #94a3b8;
        font-size: 0.95rem;
    }
    .pill {
        display: inline-block;
        padding: 6px 10px;
        border-radius: 999px;
        background: rgba(37,99,235,0.12);
        border: 1px solid rgba(96,165,250,0.18);
        color: #dbeafe;
        margin-right: 6px;
        margin-bottom: 6px;
        font-size: 0.9rem;
    }
    .feature-tile {
        border: 1px solid rgba(148,163,184,0.16);
        border-radius: 18px;
        padding: 16px;
        min-height: 140px;
        background: rgba(15,23,42,0.58);
        margin-bottom: 10px;
    }
    .feature-title {
        font-size: 1rem;
        font-weight: 700;
        color: #f8fafc;
        margin-bottom: 6px;
    }
    .feature-copy {
        color: #cbd5e1;
        font-size: 0.92rem;
        line-height: 1.45;
    }
    .workflow-step {
        border: 1px solid rgba(148,163,184,0.16);
        border-radius: 16px;
        padding: 12px 14px;
        background: rgba(30,41,59,0.5);
        margin-bottom: 8px;
    }
    .nav-help-card {
        border: 1px solid rgba(148,163,184,0.16);
        border-radius: 16px;
        padding: 12px 14px;
        background: rgba(15,23,42,0.55);
        margin-bottom: 8px;
        color: #cbd5e1;
        font-size: 0.92rem;
        line-height: 1.45;
    }
    .nav-help-card b { color: #f8fafc; }
    .next-action-card {
        border: 1px solid rgba(20,184,166,0.28);
        border-radius: 20px;
        padding: 18px 18px;
        background: linear-gradient(135deg, rgba(20,184,166,0.18), rgba(37,99,235,0.14));
        box-shadow: 0 10px 28px rgba(2,6,23,0.20);
        margin: 14px 0 16px 0;
    }
    .next-action-label {
        color: #99f6e4;
        font-size: 0.88rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-bottom: 6px;
    }
    .next-action-title {
        color: #f8fafc;
        font-size: 1.25rem;
        font-weight: 800;
        margin-bottom: 6px;
    }
    .next-action-copy {
        color: #dbeafe;
        font-size: 0.98rem;
        line-height: 1.45;
    }

    .choice-card {
        border: 1px solid rgba(148,163,184,0.16);
        border-radius: 18px;
        padding: 16px;
        min-height: 104px;
        background: rgba(15,23,42,0.58);
        margin-bottom: 10px;
    }
    .choice-card-title {
        font-size: 1rem;
        font-weight: 700;
        color: #f8fafc;
        margin-bottom: 6px;
    }
    .choice-card-copy {
        color: #cbd5e1;
        font-size: 0.92rem;
        line-height: 1.45;
    }
    div[data-testid="stFileUploader"] {
        margin-top: 0px;
    }
    div[data-testid="stButton"] > button {
        border-radius: 14px;
        border: 1px solid rgba(96,165,250,0.18);
    }

    .workzo-top-line {
        height: 1px;
        background: rgba(148,163,184,0.16);
        margin: 8px 0 18px 0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(15,23,42,0.35);
        border-radius: 16px;
        padding: 6px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 12px;
        padding: 8px 14px;
    }
    section[data-testid="stSidebar"] {
        border-right: 1px solid rgba(148,163,184,0.14);
    }
    section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] {
        gap: 0.6rem;
    }

    header[data-testid="stHeader"] {
        background: transparent !important;
        height: 0rem !important;
    }
    div[data-testid="stToolbar"] {
        display: none !important;
    }
    div[data-testid="stDecoration"] {
        display: none !important;
    }

    /* Cleaner sidebar scrolling and progress display */
    section[data-testid="stSidebar"] {
        border-right: 1px solid rgba(148,163,184,0.16);
    }
    section[data-testid="stSidebar"] ::-webkit-scrollbar {
        width: 7px;
    }
    section[data-testid="stSidebar"] ::-webkit-scrollbar-track {
        background: transparent;
    }
    section[data-testid="stSidebar"] ::-webkit-scrollbar-thumb {
        background: rgba(148,163,184,0.32);
        border-radius: 999px;
    }
    section[data-testid="stSidebar"] ::-webkit-scrollbar-thumb:hover {
        background: rgba(148,163,184,0.52);
    }
    section[data-testid="stSidebar"] div[data-testid="stProgress"] > div {
        height: 8px;
        border-radius: 999px;
    }
    .dashboard-equal-card {
        min-height: 260px;
    }

    /* WorkZo v8.9 dashboard polish */
    .workzo-section-title {
        font-size: 1.35rem;
        font-weight: 800;
        color: #f8fafc;
        margin: 22px 0 12px 0;
        letter-spacing: -0.01em;
    }
    .workzo-mini-title {
        font-size: 0.95rem;
        font-weight: 750;
        color: #e2e8f0;
        margin-bottom: 8px;
        line-height: 1.35;
    }
    .workzo-text {
        color: #f8fafc;
        font-size: 0.98rem;
        line-height: 1.55;
    }
    .workzo-muted-title {
        color: #94a3b8;
        font-size: 0.82rem;
        font-weight: 750;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin: 12px 0 6px 0;
    }
    .resume-insights-line {
        border-top: 1px solid rgba(148,163,184,0.18);
        border-bottom: 1px solid rgba(148,163,184,0.12);
        padding: 14px 0 12px 0;
        margin: 8px 0 18px 0;
    }
    .resume-insights-line ul {
        margin-top: 4px;
        padding-left: 1.15rem;
    }
    .resume-insights-line li {
        margin-bottom: 6px;
        line-height: 1.45;
    }
    .sidebar-progress-label {
        color: #cbd5e1;
        font-size: 0.82rem;
        margin-top: -6px;
    }


    /* WorkZo v9.4 SaaS polish */
    .workzo-sidebar-section-label {
        color: #94a3b8;
        font-size: 0.72rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin: 18px 0 6px 0;
    }
    .workzo-sidebar-chip {
        display: block;
        border: 1px solid rgba(148,163,184,0.16);
        background: rgba(15,23,42,0.46);
        border-radius: 12px;
        padding: 8px 10px;
        margin: 5px 0;
        color: #cbd5e1;
        font-size: 0.84rem;
        line-height: 1.25;
    }
    .workzo-sidebar-muted {
        color: #94a3b8;
        font-size: 0.82rem;
        line-height: 1.35;
        margin: 4px 0 8px 0;
    }
    .compact-job-link-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 8px;
        margin-top: 8px;
    }
    .compact-job-link {
        display: block;
        border: 1px solid rgba(148,163,184,0.16);
        background: rgba(15,23,42,0.48);
        border-radius: 12px;
        padding: 9px 11px;
        color: #e2e8f0 !important;
        text-decoration: none !important;
        font-size: 0.9rem;
        font-weight: 650;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .compact-job-link:hover {
        border-color: rgba(20,184,166,0.45);
        background: rgba(20,184,166,0.10);
        color: #ffffff !important;
    }
    .workzo-saas-page-card {
        border: 1px solid rgba(148,163,184,0.12);
        background: rgba(15,23,42,0.38);
        border-radius: 26px;
        padding: 18px 20px;
        margin-bottom: 16px;
    }


    /* WorkZo v9.5 polished dashboard layout */
    .workzo-brand-title-row { padding: 2px 0 10px 0; }
    .workzo-brand-title { font-size: 2.25rem; font-weight: 900; letter-spacing: 0.03em; color: #f8fafc; line-height: 1.05; }
    .workzo-brand-subtitle { font-size: 1.05rem; font-weight: 750; color: #e2e8f0; margin-top: 6px; }
    .workzo-brand-caption { font-size: 0.9rem; color: #94a3b8; margin-top: 4px; }
    .workzo-logo-fallback { font-size: 2.1rem; line-height: 1; }
    .workzo-dashboard-hero-compact { border: 1px solid rgba(20,184,166,0.24); border-radius: 22px; padding: 18px 20px; background: linear-gradient(135deg, rgba(37,99,235,0.22), rgba(20,184,166,0.14)); margin: 12px 0 16px 0; box-shadow: 0 14px 40px rgba(2,6,23,0.22); }
    .workzo-hero-kicker { font-size: 0.78rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.08em; color: #93c5fd; margin-bottom: 6px; }
    .workzo-hero-title { font-size: 1.45rem; font-weight: 850; color: #f8fafc; margin-bottom: 8px; }
    .workzo-chip-row { display:flex; flex-wrap:wrap; gap:8px; margin-top:10px; }
    .workzo-dashboard-chip { border: 1px solid rgba(96,165,250,0.22); background: rgba(37,99,235,0.16); color:#dbeafe; border-radius: 999px; padding: 6px 10px; font-size: 0.86rem; font-weight: 650; }
    .workzo-quick-actions { display:grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap:10px; margin: 10px 0 18px 0; }
    .workzo-saas-mini-card { border: 1px solid rgba(148,163,184,0.14); background: rgba(15,23,42,0.42); border-radius: 18px; padding: 12px 14px; min-height: 68px; }
    .workzo-saas-mini-card b { color:#f8fafc; font-size:0.95rem; }
    .workzo-saas-mini-card div { color:#94a3b8; font-size:0.82rem; margin-top:3px; }
    .workzo-sidebar-brand { font-size: 1.05rem; font-weight: 850; color:#f8fafc; letter-spacing:0.02em; padding: 6px 0 0 0; }
    .workzo-sidebar-version { color:#94a3b8; font-size:0.78rem; margin:2px 0 12px 0; }
    .compact-job-link-grid { grid-template-columns: repeat(auto-fit, minmax(125px, 1fr)); gap: 6px; }
    .compact-job-link { padding: 7px 9px; border-radius: 10px; font-size: 0.82rem; }

    /* WorkZo v9.6 cleanup: remove duplicate dashboard/profile emphasis and make sidebar nav compact */
    .workzo-dashboard-hero-compact { padding: 20px 22px !important; margin-bottom: 16px !important; }
    .workzo-hero-title { font-size: 1.45rem !important; line-height: 1.25 !important; }
    section[data-testid="stSidebar"] div[data-testid="stButton"] > button {
        justify-content: flex-start;
        text-align: left;
        min-height: 38px;
        padding: 8px 12px;
        font-size: 0.92rem;
    }
    section[data-testid="stSidebar"] div[data-testid="stButton"] > button[kind="secondary"] {
        background: rgba(15,23,42,0.38);
    }

    .workzo-action-card {
        border: 1px solid rgba(148,163,184,0.18);
        border-radius: 18px;
        padding: 16px;
        min-height: 118px;
        background: rgba(15,23,42,0.58);
        margin-bottom: 8px;
    }
    .workzo-action-card.active {
        border-color: rgba(20,184,166,0.55);
        background: linear-gradient(135deg, rgba(20,184,166,0.16), rgba(37,99,235,0.12));
    }
    .workzo-action-title { color:#f8fafc; font-size:1rem; font-weight:800; margin-bottom:6px; }
    .workzo-action-copy { color:#cbd5e1; font-size:0.9rem; line-height:1.4; }
    .workzo-mini-note { color:#94a3b8; font-size:0.86rem; margin: 4px 0 10px 0; }


    .workzo-sidebar-profile-card { border: 1px solid rgba(148,163,184,0.16); background: rgba(15,23,42,0.34); border-radius: 16px; padding: 10px; margin-bottom: 10px; }

    /* WorkZo v9.9 sidebar polish */

    /* WorkZo compact buttons + visible brand logo */
    div.stButton > button, div.stDownloadButton > button {
        min-height: 2.15rem !important;
        padding: 0.35rem 0.65rem !important;
        font-size: 0.86rem !important;
        border-radius: 0.62rem !important;
    }
    section[data-testid="stSidebar"] div.stButton > button {
        min-height: 2.05rem !important;
        padding: 0.30rem 0.55rem !important;
        font-size: 0.84rem !important;
    }
    .workzo-sidebar-logo { width:38px; height:38px; border-radius:12px; object-fit:contain; background:#0f172a; box-shadow:0 8px 20px rgba(0,0,0,.24); }
    .workzo-sidebar-logo-fallback { width:38px; height:38px; border-radius:12px; display:flex; align-items:center; justify-content:center; font-weight:950; color:#ffffff; background:linear-gradient(135deg,#2563eb,#14b8a6); box-shadow:0 8px 20px rgba(0,0,0,.24); }

    .workzo-sidebar-brand-wrap {
        border: 1px solid rgba(20,184,166,0.22);
        background: linear-gradient(135deg, rgba(37,99,235,0.18), rgba(20,184,166,0.10));
        border-radius: 18px;
        padding: 14px 14px;
        margin: 8px 0 16px 0;
    }
    .workzo-sidebar-brand { font-size: 1.25rem !important; font-weight: 900 !important; letter-spacing: 0.03em; }
    .workzo-sidebar-version { margin-bottom: 0 !important; }
    .workzo-sidebar-chip {
        border-radius: 14px !important;
        padding: 10px 12px !important;
        background: rgba(15,23,42,0.60) !important;
        border: 1px solid rgba(148,163,184,0.18) !important;
    }
    .workzo-profile-chip-label { color:#94a3b8; font-size:0.70rem; font-weight:800; text-transform:uppercase; letter-spacing:0.07em; display:block; margin-bottom:2px; }
    .workzo-profile-chip-value { color:#f8fafc; font-size:0.92rem; font-weight:650; display:block; }
    .workzo-sidebar-section-label { margin-top: 20px !important; }
    .workzo-sidebar-footer-note { color:#94a3b8; font-size:0.78rem; line-height:1.35; margin-top: 10px; }

    /* WorkZo v9.12: prevent long job URLs from overflowing cards */
    .stMarkdown a, .card a, .workzo-job-link {
        overflow-wrap: anywhere !important;
        word-break: break-word !important;
    }
    .workzo-link-button {
        display: inline-block;
        max-width: 100%;
        white-space: normal;
        overflow-wrap: anywhere;
    }


    /* WorkZo v9.27 premium SaaS header + scalable icon */
    .workzo-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 18px;
        padding: 18px 24px;
        margin: 4px 0 24px 0;
        border-radius: 24px;
        background: radial-gradient(circle at top left, rgba(20,214,201,0.22), transparent 32%), linear-gradient(135deg, rgba(6,26,58,0.96), rgba(8,29,58,0.92));
        border: 1px solid rgba(20,214,201,0.20);
        box-shadow: 0 16px 42px rgba(2,6,23,0.36);
    }
    .workzo-brand {
        display: flex;
        align-items: center;
        gap: 15px;
        min-width: 0;
    }
    .workzo-logo {
        width: 62px;
        height: 62px;
        border-radius: 18px;
        object-fit: cover;
        flex: 0 0 auto;
        box-shadow: 0 10px 26px rgba(0,214,201,0.18);
    }
    .workzo-title {
        font-size: 1.95rem;
        font-weight: 900;
        color: #ffffff;
        margin: 0;
        line-height: 1.05;
        letter-spacing: -0.02em;
    }
    .workzo-title span {
        background: linear-gradient(135deg, #00D6C9, #38BDF8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .workzo-subtitle {
        color: #BFD7FF;
        font-size: 0.95rem;
        font-weight: 600;
        margin-top: 4px;
        line-height: 1.25;
    }
    .workzo-beta {
        background: rgba(0,214,201,0.14);
        border: 1px solid rgba(0,214,201,0.26);
        color: #5FFBF1;
        padding: 8px 14px;
        border-radius: 999px;
        font-size: 0.82rem;
        font-weight: 800;
        letter-spacing: 0.04em;
        white-space: nowrap;
    }
    @media (max-width: 760px) {
        .workzo-header { padding: 15px 16px; border-radius: 20px; }
        .workzo-logo { width: 52px; height: 52px; border-radius: 16px; }
        .workzo-title { font-size: 1.45rem; }
        .workzo-subtitle { font-size: 0.82rem; }
        .workzo-beta { display: none; }
    }

    /* WorkZo v10.2: landing workspace + connected product flow */
    .workzo-landing-hero { position: relative; overflow: hidden; border-radius: 30px; padding: 54px 46px; margin: 12px 0 28px 0; background: radial-gradient(circle at 78% 24%, rgba(56,189,248,0.22), transparent 28%), radial-gradient(circle at 18% 8%, rgba(20,214,201,0.20), transparent 24%), linear-gradient(135deg, rgba(3,16,42,0.98), rgba(8,30,68,0.96)); border: 1px solid rgba(96,165,250,0.22); box-shadow: 0 28px 70px rgba(2,6,23,0.45); }
    .workzo-landing-hero:after { content: ''; position:absolute; inset:0; opacity:.22; pointer-events:none; background-image: linear-gradient(120deg, transparent 0 30%, rgba(56,189,248,.12) 30% 31%, transparent 31% 100%); background-size: 72px 72px; }
    .workzo-landing-hero > * { position: relative; z-index: 1; }
    .workzo-kicker { color:#5FFBF1; font-size:.82rem; font-weight:900; letter-spacing:.12em; text-transform:uppercase; margin-bottom:14px; }
    .workzo-landing-title { color:white; font-size:3.2rem; line-height:1.05; font-weight:950; max-width:760px; letter-spacing:-.04em; margin-bottom:18px; }
    .workzo-landing-copy { color:#cbd5e1; font-size:1.08rem; line-height:1.65; max-width:760px; margin-bottom:24px; }
    .workzo-landing-steps { display:grid; grid-template-columns: repeat(auto-fit, minmax(145px, 1fr)); gap:10px; margin-top:24px; }
    .workzo-landing-step { border:1px solid rgba(148,163,184,.18); background:rgba(15,23,42,.56); border-radius:18px; padding:13px 14px; color:#e2e8f0; font-weight:750; }
    .workzo-landing-step span { color:#5FFBF1; font-size:.78rem; display:block; margin-bottom:4px; text-transform:uppercase; letter-spacing:.06em; }
    @media (max-width:760px){ .workzo-landing-hero{padding:34px 22px;} .workzo-landing-title{font-size:2.1rem;} .workzo-landing-copy{font-size:.98rem;} }

    /* WorkZo v11.9: sample demo CTA */
    .workzo-sample-demo-card {
        border: 1px solid rgba(20,214,201,0.26);
        background: linear-gradient(135deg, rgba(20,214,201,0.12), rgba(37,99,235,0.10));
        border-radius: 20px;
        padding: 16px 18px;
        margin: 10px 0 18px 0;
        box-shadow: 0 12px 30px rgba(2,6,23,0.18);
    }



    /* WorkZo v12.2: clickable header + equal resume option cards */
    .workzo-home-link {
        text-decoration: none !important;
        cursor: pointer;
        transition: transform .18s ease, opacity .18s ease;
    }
    .workzo-home-link:hover {
        transform: translateY(-1px);
        opacity: .94;
    }
    .workzo-home-link:hover .workzo-title {
        text-decoration: none !important;
    }
    /* Make multi-line choice buttons look like same-size SaaS cards. */
    div[data-testid="stButton"] > button:has(p) {
        min-height: 118px !important;
        height: 118px !important;
        width: 100% !important;
        white-space: normal !important;
        text-align: center !important;
        justify-content: center !important;
        align-items: center !important;
        padding: 18px 20px !important;
        transition: transform .18s ease, border-color .18s ease, background .18s ease;
    }
    div[data-testid="stButton"] > button:has(p):hover {
        transform: translateY(-3px);
        border-color: rgba(56,189,248,0.72) !important;
        background: rgba(20,184,166,0.08) !important;
    }
    @media (max-width: 760px) {
        div[data-testid="stButton"] > button:has(p) {
            min-height: 104px !important;
            height: auto !important;
        }
    }


    /* WorkZo v13.0: compact buttons and fixed resume choice cards */
    div[data-testid="stButton"] > button {
        min-height: 40px !important;
        height: auto !important;
        padding: 0.45rem 0.9rem !important;
        border-radius: 12px !important;
        font-size: 0.95rem !important;
        line-height: 1.25 !important;
    }
    .workzo-resume-choice-card {
        min-height: 112px;
        height: 112px;
        border: 1px solid rgba(148,163,184,0.18);
        border-radius: 18px;
        padding: 16px;
        background: rgba(15,23,42,0.58);
        text-align: center;
        display: flex;
        flex-direction: column;
        justify-content: center;
        transition: transform .16s ease, border-color .16s ease, background .16s ease;
    }
    .workzo-resume-choice-card:hover {
        transform: translateY(-2px);
        border-color: rgba(20,214,201,0.55);
        background: rgba(20,214,201,0.08);
    }
    .workzo-resume-choice-title { color:#f8fafc; font-weight:800; font-size:1.02rem; margin-bottom:8px; }
    .workzo-resume-choice-copy { color:#cbd5e1; font-size:0.93rem; line-height:1.35; }
    .workzo-start-button-wrapper div[data-testid="stButton"] > button {
        min-height: 52px !important;
        max-width: 360px !important;
        margin: 0 auto !important;
        display: block !important;
        font-size: 1.02rem !important;
    }

    /* Equal height for the three resume choice buttons only-style multi-line buttons. */
    div[data-testid="stButton"] > button:has(p) {
        min-height: 92px !important;
        height: 92px !important;
        width: 100% !important;
        white-space: pre-line !important;
        text-align: center !important;
        justify-content: center !important;
    }


    /* WorkZo v13.3 cleanup: compact dashboard nav, clean sample CTA, better resume cards */
    .workzo-demo-note {
        border: 1px solid rgba(148,163,184,0.18);
        background: rgba(15,23,42,0.48);
        border-radius: 16px;
        padding: 14px 16px;
        color: #cbd5e1;
        line-height: 1.45;
        min-height: 74px;
    }
    .workzo-progress-card {
        border: 1px solid rgba(148,163,184,0.18);
        border-radius: 18px;
        padding: 14px 14px;
        background: rgba(15,23,42,0.58);
        min-height: 126px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        margin-bottom: 8px;
    }
    .workzo-progress-card.done {
        border-color: rgba(20,184,166,0.50);
        background: linear-gradient(135deg, rgba(20,184,166,0.14), rgba(37,99,235,0.10));
    }
    .workzo-progress-title { color:#f8fafc; font-size:1rem; font-weight:850; margin-bottom:5px; }
    .workzo-progress-status { color:#cbd5e1; font-size:0.88rem; }
    .workzo-resume-mode-card {
        border: 1px solid rgba(148,163,184,0.18);
        border-radius: 18px;
        padding: 16px 14px;
        min-height: 104px;
        background: rgba(15,23,42,0.58);
        text-align: center;
        display: flex;
        flex-direction: column;
        justify-content: center;
        gap: 7px;
        transition: transform .16s ease, border-color .16s ease, background .16s ease;
    }
    .workzo-resume-mode-card.active {
        border-color: rgba(20,184,166,0.58);
        background: linear-gradient(135deg, rgba(20,184,166,0.12), rgba(37,99,235,0.08));
    }
    .workzo-resume-mode-card:hover {
        transform: translateY(-2px);
        border-color: rgba(56,189,248,0.55);
    }
    .workzo-resume-mode-title { color:#f8fafc; font-weight:850; font-size:1rem; }
    .workzo-resume-mode-copy { color:#cbd5e1; font-size:0.90rem; line-height:1.35; }
    div[data-testid="stButton"] > button {
        min-height: 38px !important;
        padding: 0.45rem 0.85rem !important;
    }


    /* WorkZo final compactness fix: buttons must not become giant cards */
    div[data-testid="stButton"] > button,
    div.stButton > button,
    div[data-testid="stDownloadButton"] > button,
    div.stDownloadButton > button {
        min-height: 34px !important;
        height: auto !important;
        width: auto !important;
        max-width: 260px !important;
        padding: 0.36rem 0.75rem !important;
        border-radius: 10px !important;
        font-size: 0.88rem !important;
        line-height: 1.15 !important;
        white-space: nowrap !important;
        justify-content: center !important;
        text-align: center !important;
    }
    div[data-testid="stButton"] > button:has(p) {
        min-height: 34px !important;
        height: auto !important;
        width: auto !important;
        max-width: 260px !important;
        padding: 0.36rem 0.75rem !important;
        white-space: nowrap !important;
        transform: none !important;
    }
    .workzo-resume-mode-card { min-height: 94px !important; margin-bottom: 8px !important; }
    .workzo-progress-card { min-height: 96px !important; margin-bottom: 8px !important; }
    .workzo-progress-title { font-size: 0.96rem !important; }
    .workzo-logo { object-fit: contain !important; background: #0f172a !important; padding: 0 !important; }


    /* WorkZo v15.0 final UI sizing fixes */
    div[data-testid="stButton"] > button,
    div.stButton > button,
    div[data-testid="stDownloadButton"] > button,
    div.stDownloadButton > button,
    div[data-testid="stLinkButton"] > a {
        min-height: 38px !important;
        height: auto !important;
        padding: 0.42rem 0.85rem !important;
        border-radius: 11px !important;
        font-size: 0.92rem !important;
        line-height: 1.2 !important;
        white-space: nowrap !important;
    }
    .workzo-start-button-wrapper div[data-testid="stButton"] > button {
        min-height: 52px !important;
        max-width: 360px !important;
        padding: 0.75rem 1.25rem !important;
        font-size: 1.05rem !important;
        border-radius: 14px !important;
        display: block !important;
        margin: 0 auto !important;
    }
    .workzo-resume-button-row div[data-testid="stButton"] > button {
        width: 100% !important;
        max-width: none !important;
        min-height: 42px !important;
    }
    .workzo-action-grid div[data-testid="stButton"] > button,
    .workzo-progress-action div[data-testid="stButton"] > button {
        width: 100% !important;
        max-width: none !important;
    }
    .workzo-progress-done { color:#22c55e; font-weight:900; margin-left:6px; }
    .workzo-step-pill {
        border:1px solid rgba(148,163,184,0.22); border-radius:14px;
        padding:12px 14px; background:rgba(15,23,42,0.48); min-height:64px;
    }
    .workzo-step-pill.done { border-color:rgba(34,197,94,.45); background:rgba(34,197,94,.08); }
    .workzo-step-pill .state { color:#cbd5e1; font-size:.88rem; margin-top:4px; }

</style>
""", unsafe_allow_html=True)

# =========================================================
# UI LANGUAGE TEXT
# =========================================================
UI_TEXT = {
    "English": {
        "title": "Your 360-degree AI Career Assistant",
        "subtitle": "AI-powered career support based on your country and CV.",
        "onboarding_title": "Welcome to WorkZo",
        "onboarding_subtitle": "Start with your country and CV. WorkZo will build the rest from there.",
        "country": "Select a Country",
        "ui_language": "App Language",
        "response_language": "AI Response Language",
        "resume_input": "Resume Input",
        "upload_cv": "Upload CV",
        "create_cv": "Create CV",
        "upload_resume": "Upload your CV",
        "create_resume": "Create your CV",
        "full_name": "Full Name",
        "email": "Email",
        "phone": "Phone Number",
        "summary": "Professional Summary",
        "skills": "Skills",
        "experience": "Work Experience",
        "education": "Education",
        "continue": "Continue to Dashboard",
        "edit_setup": "Edit Onboarding",
        "dashboard": "Dashboard",
        "actions": "Explore tools",
        "understand_job": "Understand Job",
        "improve_cv": "Improve CV",
        "career_communication": "Career Communication",
        "find_jobs": "Find Jobs",
        "mock_interview": "Mock Interview",
        "skill_gap": "Skill Gap",
        "career_roadmap": "Career Roadmap",
        "job_assist": "Job Assist",
        "document_tools": "Document Tools",
        "cv_translator": "CV Translator",
        "cover_letter_generator": "Cover Letter Generator",
        "cover_letter_translator": "Cover Letter Translator",
        "workobot": "Work-O-Bot",
        "workobot_sub": "AI career and language coach",
        "workobot_desc_short": "Mock interviews, career insights, skill gaps, communication practice, and Work-O-Bot chat.",
        "go_workobot": "Open Work-O-Bot",
        "cv_documents": "CV & Documents",
        "interview_practice": "Interview Practice",
        "career_insights": "Career Insights",
        "navigation_help": "Where to find what",
        "dashboard_desc_short": "Start here: scores, next steps, and recommended actions.",
        "job_assist_desc_short": "Find jobs or understand a job description before applying.",
        "cv_documents_desc_short": "Improve CV, make cover letters, translate documents, and use country CV templates.",
        "interview_practice_desc_short": "Practice interview answers, mock questions, and speaking preparation.",
        "career_insights_desc_short": "Check skill gaps, roadmap, country readiness, and next best step.",
        "preferred_language_help": "One language for the app, AI replies, and generated documents.",
        "start_actions_title": "What would you like to do today?",
        "go_job_assist": "Analyze a Job / Find Jobs",
        "go_cv_documents": "Improve CV / Documents",
        "go_interview": "Practice Interview",
        "go_career_insights": "See Career Insights",
        "start_here_intro": "Your dashboard shows a stable resume analysis, ATS readiness, and extracted profile. Use the menu on the left for deeper tools.",
        "detected_role": "Likely Current Role",
        "detected_summary": "Professional Summary",
        "detected_skills": "Key Skills",
        "suggested_roles": "Suggested Roles",
        "resume_loaded": "Resume Loaded",
        "yes": "Yes",
        "no": "No",
        "not_analyzed": "Not analyzed yet",
        "warn_country": "Please select a country.",
        "warn_upload_cv": "Please upload your CV before continuing.",
        "warn_full_name": "Please enter your full name.",
        "warn_summary": "Please enter your professional summary.",
        "warn_skills": "Please enter your skills.",
        "warn_experience": "Please enter your work experience.",
        "warn_education": "Please enter your education.",
        "unsupported_file": "Unsupported file type.",
        "ai_unavailable": "AI service unavailable",
        "job_desc": "Paste the job description",
        "your_cv": "Your CV",
        "target_job": "Paste target job description",
        "job_title": "Job title",
        "background": "Short background about yourself",
        "preferred_location": "Preferred city or region",
        "target_role": "Target role",
        "current_role": "Your current role",
        "current_profile": "Your current profile / CV",
        "interview_language": "Interview language",
        "language_support_task": "Support task",
        "enter_text": "Enter your text",
        "improve": "Improve",
        "analyze": "Analyze",
        "generate": "Generate",
        "translate": "Translate",
        "job_fit_analysis": "Job Fit Analysis",
        "career_comm_result": "Career Communication Feedback",
        "search_queries": "Suggested search links",
        "platform_hint": "These links open search pages. Later, you can replace them with local job portals.",
        "translator_source": "Source Language",
        "translator_target": "Target Language",
        "cover_letter_input": "Paste your cover letter",
        "cv_input": "Paste your CV",
        "copy_ready": "Copy-ready output",
        "resume_score": "Resume Score",
        "ats_score": "ATS Score",
        "strengths": "Top Strengths",
        "improvements": "Top Improvements",
        "job_fit_score": "Job Fit",
        "skill_gap_score": "Skill Gap",
        "interview_score": "Interview",
        "resume_insights": "Resume Insights",
        "update_resume": "Update My Resume",
        "top_countries_fit": "Country Fit Summary",
        "country_fit_note": "Likely strongest markets based on CV language, profile, and transferability.",
        "detected_country": "Detected Country",
        "refresh_resume": "Re-analyze Resume",
        "save_resume": "Save as My New Resume",
        "document_hub_caption": "Keep all writing and translation tools in one place.",
        "quick_prompts": "Quick prompts",
        "chat_mode": "Mode",
        "chat_placeholder": "Ask Work-O-Bot anything...",
        "clear_chat": "Clear Chat",
        "preferred_language": "Select a Language",
        "user_status": "Current Career Situation",
        "fresh_graduate": "Fresh graduate / entry level",
        "student_thesis_internship": "Student / Thesis / Internship seeker",
        "career_changer": "Career changer",
        "migrant": "Planning to migrate / applying abroad",
        "local_jobseeker": "Looking for jobs locally",
        "experienced": "Experienced professional",
        "returning": "Returning after a career break",
        "guided_cv_builder": "Guided CV Builder",
        "generate_cv": "Generate CV with AI",
        "extra_cv_info": "Would you like to add more information?",
        "country_readiness": "Country Readiness",
        "next_steps": "What should you do next?",
        "cv_template_builder": "Country-Specific Resume Builder",
        "migration_country": "Which country do you want to move/apply to?",
        "chosen_country_resume_score": "Resume readiness for chosen country",
    },
    "German": {
        "title": "Dein 360-degree KI-Karriereassistent",
        "subtitle": "KI-gestutzte Karrierehilfe basierend auf deinem Land und deinem Lebenslauf.",
        "onboarding_title": "Willkommen bei WorkZo",
        "onboarding_subtitle": "Starte mit deinem Land und deinem Lebenslauf. WorkZo erstellt den Rest daraus.",
        "country": "Land auswahlen",
        "ui_language": "App-Sprache",
        "response_language": "Antwortsprache der KI",
        "resume_input": "Lebenslauf-Eingabe",
        "upload_cv": "Lebenslauf hochladen",
        "create_cv": "Lebenslauf erstellen",
        "upload_resume": "Lebenslauf hochladen",
        "create_resume": "Lebenslauf erstellen",
        "full_name": "Vollstandiger Name",
        "email": "E-Mail",
        "phone": "Telefonnummer",
        "summary": "Berufliche Zusammenfassung",
        "skills": "Kenntnisse",
        "experience": "Berufserfahrung",
        "education": "Ausbildung",
        "continue": "Zum Dashboard",
        "edit_setup": "Onboarding bearbeiten",
        "dashboard": "Dashboard",
        "actions": "Tools erkunden",
        "understand_job": "Stelle verstehen",
        "improve_cv": "Lebenslauf verbessern",
        "career_communication": "Karrierekommunikation",
        "find_jobs": "Jobs finden",
        "mock_interview": "Vorstellungsgesprach",
        "skill_gap": "Kompetenzlucke",
        "career_roadmap": "Karriereplan",
        "job_assist": "Job-Assistent",
        "document_tools": "Dokument-Tools",
        "cv_translator": "Lebenslauf übersetzen",
        "cover_letter_generator": "Anschreiben erstellen",
        "cover_letter_translator": "Anschreiben übersetzen",
        "workobot": "Work-O-Bot",
        "workobot_sub": "KI-Karriere- und Sprachcoach",
        "workobot_desc_short": "Mock-Interviews, Karriere-Einblicke, Kompetenzlücken, Kommunikationstraining und Work-O-Bot Chat.",
        "go_workobot": "Work-O-Bot öffnen",
        "cv_documents": "Lebenslauf & Dokumente",
        "interview_practice": "Interviewtraining",
        "career_insights": "Karriere-Einblicke",
        "navigation_help": "Wo finde ich was?",
        "dashboard_desc_short": "Starte hier: Scores, nachste Schritte und empfohlene Aktionen.",
        "job_assist_desc_short": "Finde Jobs oder verstehe eine Stellenbeschreibung vor der Bewerbung.",
        "cv_documents_desc_short": "Verbessere Lebenslauf, erstelle Anschreiben, übersetze Dokumente und nutze Länder-Vorlagen.",
        "interview_practice_desc_short": "Ube Interviewantworten, Mock-Fragen und mundliche Vorbereitung.",
        "career_insights_desc_short": "Prufe Kompetenzlücken, Roadmap, Länder-Eignung und nachsten besten Schritt.",
        "preferred_language_help": "Eine Sprache fur App, KI-Antworten und Dokumente.",
        "start_actions_title": "Was mochtest du heute tun?",
        "go_job_assist": "Job analysieren / Jobs finden",
        "go_cv_documents": "CV / Dokumente verbessern",
        "go_interview": "Interview uben",
        "go_career_insights": "Karriere-Einblicke ansehen",
        "start_here_intro": "Dein Dashboard zeigt eine stabile Lebenslaufanalyse, ATS-Bereitschaft und extrahierte Profildaten. Nutze das linke Menu fur weitere Tools.",
        "detected_role": "Wahrscheinliche aktuelle Rolle",
        "detected_summary": "Berufliche Zusammenfassung",
        "detected_skills": "Wichtige Kenntnisse",
        "suggested_roles": "Vorgeschlagene Rollen",
        "resume_loaded": "Lebenslauf geladen",
        "yes": "Ja",
        "no": "Nein",
        "not_analyzed": "Noch nicht analysiert",
        "warn_country": "Bitte wahle ein Land.",
        "warn_upload_cv": "Bitte lade deinen Lebenslauf hoch.",
        "warn_full_name": "Bitte gib deinen vollstandigen Namen ein.",
        "warn_summary": "Bitte gib deine berufliche Zusammenfassung ein.",
        "warn_skills": "Bitte gib deine Kenntnisse ein.",
        "warn_experience": "Bitte gib deine Berufserfahrung ein.",
        "warn_education": "Bitte gib deine Ausbildung ein.",
        "unsupported_file": "Nicht unterstutzter Dateityp.",
        "ai_unavailable": "KI-Dienst nicht verfugbar",
        "job_desc": "Stellenbeschreibung einfugen",
        "your_cv": "Dein Lebenslauf",
        "target_job": "Ziel-Stellenbeschreibung einfugen",
        "job_title": "Berufsbezeichnung",
        "background": "Kurzer Hintergrund uber dich",
        "preferred_location": "Bevorzugte Stadt oder Region",
        "target_role": "Zielrolle",
        "current_role": "Deine aktuelle Rolle",
        "current_profile": "Dein aktuelles Profil / Lebenslauf",
        "interview_language": "Sprache des Interviews",
        "enter_text": "Text eingeben",
        "improve": "Verbessern",
        "analyze": "Analysieren",
        "generate": "Erstellen",
        "translate": "Ubersetzen",
        "job_fit_analysis": "Job-Fit-Analyse",
        "career_comm_result": "Feedback zur Karrierekommunikation",
        "search_queries": "Vorgeschlagene Suchlinks",
        "platform_hint": "Diese Links öffnen Suchseiten. Spater kannst du lokale Jobportale nutzen.",
        "translator_source": "Ausgangssprache",
        "translator_target": "Zielsprache",
        "cover_letter_input": "Anschreiben einfugen",
        "cv_input": "Lebenslauf einfugen",
        "copy_ready": "Kopierfertige Ausgabe",
        "resume_score": "Lebenslauf-Score",
        "ats_score": "ATS-Score",
        "strengths": "Top-Starken",
        "improvements": "Top-Verbesserungen",
        "job_fit_score": "Job-Fit",
        "skill_gap_score": "Kompetenzlucke",
        "interview_score": "Interview",
        "resume_insights": "Lebenslauf-Einblicke",
        "update_resume": "Lebenslauf aktualisieren",
        "top_countries_fit": "Top-Länder fur diesen Lebenslauf",
        "country_fit_note": "Wahrscheinlich die starksten Markte basierend auf Sprache, Profil und Ubertragbarkeit.",
        "detected_country": "Erkanntes Land",
        "refresh_resume": "Lebenslauf neu analysieren",
        "save_resume": "Als neuen Lebenslauf speichern",
        "document_hub_caption": "Alle Schreib- und Ubersetzungstools an einem Ort.",
        "quick_prompts": "Schnellstarts",
        "chat_mode": "Modus",
        "chat_placeholder": "Frag Work-O-Bot etwas...",
        "clear_chat": "Chat loschen",
        "preferred_language": "Sprache auswahlen",
        "user_status": "Aktuelle Karrieresituation",
        "fresh_graduate": "Absolvent/in / Berufseinsteiger/in",
        "student_thesis_internship": "Student/in / Abschlussarbeit / Praktikum",
        "career_changer": "Quereinsteiger/in",
        "migrant": "Migration / Bewerbung im Ausland geplant",
        "local_jobseeker": "Jobsuche im aktuellen Land",
        "experienced": "Erfahrene Fachkraft",
        "returning": "Ruckkehr nach Karrierepause",
        "guided_cv_builder": "Gefuhrter Lebenslauf-Builder",
        "generate_cv": "Lebenslauf mit KI erstellen",
        "extra_cv_info": "Mochtest du weitere Informationen hinzufugen?",
        "country_readiness": "Länder-Eignung",
        "next_steps": "Was solltest du als Nachstes tun?",
        "cv_template_builder": "Länderspezifischer Lebenslauf-Builder",
        "migration_country": "In welches Land mochtest du ziehen/dich bewerben?",
        "chosen_country_resume_score": "Lebenslauf-Eignung fur das gewahlte Land",
    },
    "Dutch": {
        "title": "Jouw 360-degree AI-carriereassistent",
        "subtitle": "AI-ondersteuning gebaseerd op jouw land en cv.",
        "onboarding_title": "Welkom bij WorkZo",
        "onboarding_subtitle": "Begin met je land en cv. WorkZo bouwt de rest daarop.",
        "country": "Selecteer een land",
        "ui_language": "App-taal",
        "response_language": "AI-antwoordtaal",
        "resume_input": "CV-invoer",
        "upload_cv": "CV uploaden",
        "create_cv": "CV maken",
        "upload_resume": "Upload je CV",
        "create_resume": "Maak je CV",
        "full_name": "Volledige naam",
        "email": "E-mail",
        "phone": "Telefoonnummer",
        "summary": "Professionele samenvatting",
        "skills": "Vaardigheden",
        "experience": "Werkervaring",
        "education": "Opleiding",
        "continue": "Ga naar dashboard",
        "edit_setup": "Onboarding bewerken",
        "dashboard": "Dashboard",
        "actions": "Tools verkennen",
        "understand_job": "Vacature begrijpen",
        "improve_cv": "CV verbeteren",
        "career_communication": "Carrierecommunicatie",
        "find_jobs": "Banen vinden",
        "mock_interview": "Proefinterview",
        "skill_gap": "Vaardigheidskloof",
        "career_roadmap": "Carriereplan",
        "job_assist": "Jobhulp",
        "document_tools": "Documenttools",
        "cv_translator": "CV vertalen",
        "cover_letter_generator": "Motivatiebrief maken",
        "cover_letter_translator": "Motivatiebrief vertalen",
        "workobot": "Work-O-Bot",
        "workobot_sub": "AI carriere- en taalcoach",
        "workobot_desc_short": "Mock-interviews, carriere-inzichten, skill gaps, communicatie-oefening en Work-O-Bot chat.",
        "go_workobot": "Open Work-O-Bot",
        "cv_documents": "CV & Documenten",
        "interview_practice": "Interview oefenen",
        "career_insights": "Carriere-inzichten",
        "navigation_help": "Waar vind je wat",
        "dashboard_desc_short": "Begin hier: scores, volgende stappen en aanbevolen acties.",
        "job_assist_desc_short": "Vind banen of begrijp een vacaturetekst voordat je solliciteert.",
        "cv_documents_desc_short": "Verbeter je CV, maak brieven, vertaal documenten en gebruik landen-CV-templates.",
        "interview_practice_desc_short": "Oefen interviewantwoorden, mockvragen en spreekvoorbereiding.",
        "career_insights_desc_short": "Bekijk skill gaps, roadmap, landenfit en volgende beste stap.",
        "preferred_language_help": "Een taal voor app, AI-antwoorden en documenten.",
        "start_actions_title": "Wat wil je vandaag doen?",
        "go_job_assist": "Vacature analyseren / banen vinden",
        "go_cv_documents": "CV / documenten verbeteren",
        "go_interview": "Interview oefenen",
        "go_career_insights": "Carriere-inzichten bekijken",
        "start_here_intro": "Je dashboard toont een stabiele cv-analyse, ATS-gereedheid en geÃ«xtraheerde profielgegevens. Gebruik daarna het linkermenu voor meer tools.",
        "detected_role": "Waarschijnlijke huidige rol",
        "detected_summary": "Professionele samenvatting",
        "detected_skills": "Belangrijkste vaardigheden",
        "suggested_roles": "Voorgestelde rollen",
        "resume_loaded": "CV geladen",
        "yes": "Ja",
        "no": "Nee",
        "not_analyzed": "Nog niet geanalyseerd",
        "warn_country": "Selecteer een land.",
        "warn_upload_cv": "Upload je cv voordat je doorgaat.",
        "warn_full_name": "Voer je volledige naam in.",
        "warn_summary": "Voer je professionele samenvatting in.",
        "warn_skills": "Voer je vaardigheden in.",
        "warn_experience": "Voer je werkervaring in.",
        "warn_education": "Voer je opleiding in.",
        "unsupported_file": "Niet-ondersteund bestandstype.",
        "ai_unavailable": "AI-service niet beschikbaar",
        "job_desc": "Plak de vacaturetekst",
        "your_cv": "Jouw CV",
        "target_job": "Plak de doelvacature",
        "job_title": "Functietitel",
        "background": "Korte achtergrond over jezelf",
        "preferred_location": "Voorkeursstad of regio",
        "target_role": "Doelrol",
        "current_role": "Je huidige rol",
        "current_profile": "Je huidige profiel / CV",
        "interview_language": "Taal van het interview",
        "enter_text": "Voer je tekst in",
        "improve": "Verbeter",
        "analyze": "Analyseer",
        "generate": "Genereer",
        "translate": "Vertaal",
        "job_fit_analysis": "Vacaturematch-analyse",
        "career_comm_result": "Feedback op carrierecommunicatie",
        "search_queries": "Voorgestelde zoeklinks",
        "platform_hint": "Deze links openen zoekpagina's. Later kun je lokale vacatureplatforms gebruiken.",
        "translator_source": "Brontaal",
        "translator_target": "Doeltaal",
        "cover_letter_input": "Plak je motivatiebrief",
        "cv_input": "Plak je cv",
        "copy_ready": "Kopieerklare output",
        "resume_score": "CV-score",
        "ats_score": "ATS-score",
        "strengths": "Topsterktes",
        "improvements": "Topverbeteringen",
        "job_fit_score": "Vacaturematch",
        "skill_gap_score": "Vaardigheidskloof",
        "interview_score": "Interview",
        "resume_insights": "CV-inzichten",
        "update_resume": "CV bijwerken",
        "top_countries_fit": "Toplanden voor dit CV",
        "country_fit_note": "Waarschijnlijk de sterkste markten op basis van taal, profiel en overdraagbaarheid.",
        "detected_country": "Gedetecteerd land",
        "refresh_resume": "CV opnieuw analyseren",
        "save_resume": "Opslaan als nieuw CV",
        "document_hub_caption": "Houd al je schrijf- en vertaaltools op een plek.",
        "quick_prompts": "Snelle prompts",
        "chat_mode": "Modus",
        "chat_placeholder": "Vraag Work-O-Bot iets...",
        "clear_chat": "Chat wissen",
    }
}

# =========================================================
# WorkZo single CV source of truth
# Added to prevent preview / edit / translation / PDF mismatch.
# =========================================================
def get_workzo_cv_text() -> str:
    """Return the latest CV text from one source of truth.

    Active editor/widget keys are checked before the master key so Preview,
    PDF download, and Translation do not read stale AI-generated text.
    """
    import streamlit as st
    priority_keys = [
        "cv_editor_area", "cv_editor",
        "improve_update_cv_source_v92", "country_template_cv_v51",
        "improved_cv_edit_buffer_v92", "country_cv_edit_buffer",
        "workzo_final_cv_text", "edited_cv", "edited_improved_cv_text",
        "final_cv_text", "editable_cv_text", "translated_cv_text",
        "generated_country_cv_text", "improved_cv_text_v92", "improved_cv_text",
        "clean_structured_cv_text", "approved_cv_text", "structured_cv_text",
        "cv_text", "uploaded_cv_text",
    ]
    for key in priority_keys:
        value = st.session_state.get(key, "")
        if isinstance(value, str) and value.strip():
            text = value.strip()
            st.session_state["workzo_final_cv_text"] = text
            st.session_state["cv_text"] = text
            st.session_state["final_cv_text"] = text
            return text
    return ""


def set_workzo_cv_text(text: str, *, sync_editor: bool = True) -> str:
    """Set the one CV source used by editor, preview, translation and downloads."""
    import streamlit as st
    text = str(text or "").strip()
    st.session_state["workzo_final_cv_text"] = text
    st.session_state["cv_text"] = text
    st.session_state["final_cv_text"] = text
    st.session_state["clean_structured_cv_text"] = text
    if sync_editor:
        st.session_state["cv_editor"] = text
        st.session_state["cv_editor_area"] = text
    return text


# --- WorkZo v6 real UI overrides: fixed buttons + scroll + cards ---
st.markdown("""
<style>
/* Default buttons: readable and aligned to their containers */
div[data-testid="stButton"] > button,
div.stButton > button,
div[data-testid="stDownloadButton"] > button,
div.stDownloadButton > button,
div[data-testid="stLinkButton"] > a {
    min-height: 44px !important;
    width: 100% !important;
    max-width: 100% !important;
    padding: 0.62rem 1rem !important;
    border-radius: 12px !important;
    font-size: 0.98rem !important;
    line-height: 1.2 !important;
    white-space: normal !important;
    text-align: center !important;
}
/* Hero Start Now only: larger CTA */
.workzo-start-button-wrapper div[data-testid="stButton"] > button {
    min-height: 62px !important;
    padding: 0.95rem 1.45rem !important;
    font-size: 1.12rem !important;
    border-radius: 16px !important;
    font-weight: 800 !important;
}
.workzo-progress-done { color:#22c55e; font-weight:900; margin-left:8px; }
.workzo-dashboard-chip { white-space: normal !important; }
.block-container { padding-top: 1rem !important; }

/* WorkZo v12 primary CTA visible fix */
button[kind="primary"], div[data-testid="stButton"] button[data-testid="baseButton-primary"] {
    min-height:64px!important; min-width:260px!important; padding:1rem 2rem!important; font-size:1.18rem!important; border-radius:16px!important; font-weight:850!important;
}
</style>
""", unsafe_allow_html=True)

# --- WorkZo v13 onboarding button fix: consistent card action buttons ---
st.markdown("""
<style>
/* Make normal WorkZo buttons readable and consistent across new Streamlit versions */
div[data-testid="stButton"] > button,
div[data-testid="stButton"] button,
button[data-testid="baseButton-secondary"],
button[data-testid="baseButton-primary"],
div[data-testid="stDownloadButton"] > button,
div[data-testid="stDownloadButton"] button {
    min-height: 46px !important;
    padding: 0.65rem 1.15rem !important;
    border-radius: 12px !important;
    font-size: 1rem !important;
    font-weight: 700 !important;
    line-height: 1.2 !important;
    white-space: normal !important;
}

/* Resume input page: buttons below the three cards should match the card/column width */
.workzo-resume-button-row {
    width: 100% !important;
    margin-top: 0.75rem !important;
}
.workzo-resume-button-row + div[data-testid="stButton"],
.workzo-resume-button-row ~ div[data-testid="stButton"],
div[data-testid="column"] div[data-testid="stButton"] > button {
    width: 100% !important;
    max-width: 100% !important;
}

/* Hero Start Now only: keep this as the large CTA */
.workzo-start-button-wrapper {
    display: flex !important;
    justify-content: center !important;
    margin-top: 1.8rem !important;
}
.workzo-start-button-wrapper div[data-testid="stButton"] {
    width: auto !important;
}
.workzo-start-button-wrapper div[data-testid="stButton"] > button,
.workzo-start-button-wrapper button[data-testid="baseButton-primary"] {
    width: auto !important;
    min-width: 210px !important;
    min-height: 58px !important;
    padding: 0.95rem 2.25rem !important;
    font-size: 1.15rem !important;
    border-radius: 16px !important;
    font-weight: 850 !important;
}
</style>
""", unsafe_allow_html=True)


# =========================================================
# WorkZo v14 CV onboarding button alignment fix
# =========================================================
st.markdown("""
<style>
/* Make the CV input choice buttons align with the cards above them.
   Streamlit renders buttons outside the HTML card, so we make the
   button fill its column width and keep the card/button visually paired. */
div[data-testid="stButton"] > button {
    width: 100% !important;
    max-width: none !important;
}

/* Keep the landing Start Now CTA from becoming full-page width. */
button[kind="primary"],
button[data-testid="baseButton-primary"] {
    max-width: 360px !important;
    width: auto !important;
    min-width: 160px !important;
    min-height: 52px !important;
    padding: 0.75rem 1.5rem !important;
    border-radius: 14px !important;
    font-size: 1.05rem !important;
}

.workzo-resume-mode-card {
    margin-bottom: 10px !important;
    min-height: 112px !important;
}

/* Selected CV input card state */
.workzo-resume-mode-card.active {
    border-color: rgba(20,184,166,0.85) !important;
    box-shadow: 0 0 0 1px rgba(20,184,166,0.20), 0 14px 35px rgba(8,47,73,0.25) !important;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# WorkZo v15 final visual stabilizer
# =========================================================
st.markdown("""
<style>
/* Keep the one hero CTA visually strong. Streamlit cannot style by text reliably,
   so all primary buttons are large and product-like. */
div[data-testid="stButton"] button[data-testid="baseButton-primary"],
button[data-testid="baseButton-primary"],
button[kind="primary"] {
    min-height: 64px !important;
    min-width: 260px !important;
    padding: 1rem 2.3rem !important;
    border-radius: 16px !important;
    font-size: 1.18rem !important;
    font-weight: 850 !important;
}
/* Normal action buttons: aligned, readable, and not tiny. */
div[data-testid="stButton"], div.stButton {
    width: 100% !important;
}
div[data-testid="stButton"] > button,
div.stButton > button,
div[data-testid="stDownloadButton"] > button,
div.stDownloadButton > button,
div[data-testid="stLinkButton"] > a {
    width: 100% !important;
    max-width: 100% !important;
    min-height: 48px !important;
    padding: 0.70rem 1rem !important;
    border-radius: 13px !important;
    font-size: 1.02rem !important;
    font-weight: 700 !important;
    line-height: 1.2 !important;
    white-space: normal !important;
    text-align: center !important;
}
/* Keep widgets from beginning too far down after page rerun. */
.block-container { padding-top: 1rem !important; }
.workzo-progress-done { color:#22c55e !important; font-weight:900 !important; margin-left:8px !important; }
</style>
""", unsafe_allow_html=True)
