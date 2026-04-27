
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
from typing import Dict, Optional, List, Tuple

import pdfplumber
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
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
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
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
        "sections": ["Profil", "Expérience professionnelle", "Formation", "Compétences", "Langues"]
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
# PAGE CONFIG + LOGO PATHS
# =========================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_PATH = os.path.join(BASE_DIR, "workzo_icon.png")
LOGO_PATH = os.path.join(BASE_DIR, "logo.png")

# Use the optimized WorkZo favicon/app icon when it exists.
# Keep logo.png as a fallback so older deployments do not break.
PAGE_ICON = ICON_PATH if os.path.exists(ICON_PATH) else (LOGO_PATH if os.path.exists(LOGO_PATH) else "🚀")

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
SCORING_VERSION = "v5.5"

if "request_count" not in st.session_state:
    st.session_state.request_count = 0

if "first_request_time" not in st.session_state:
    st.session_state.first_request_time = time.time()

if time.time() - st.session_state.first_request_time > 3600:
    st.session_state.request_count = 0
    st.session_state.first_request_time = time.time()

def can_make_request() -> bool:
    return st.session_state.request_count < MAX_REQUESTS_PER_HOUR
ISSUES_FILE = os.path.join(BASE_DIR, "workzo_beta_issues.csv")

# =========================================================
# NAVIGATION / SCROLL HELPERS
# =========================================================
def request_scroll_to_top() -> None:
    """Ask the next rerun to force the browser viewport to the top."""
    st.session_state["_workzo_scroll_to_top"] = True


def maybe_scroll_to_top() -> None:
    """Force Streamlit's parent page and scroll containers back to the top.
    This prevents pages from opening in the middle after a button click or upload.
    """
    if not st.session_state.pop("_workzo_scroll_to_top", False):
        return
    components.html(
        """
        <script>
        const forceTop = () => {
            const doc = window.parent.document;
            const targets = [
                window.parent,
                doc.documentElement,
                doc.body,
                doc.querySelector('section.main'),
                doc.querySelector('[data-testid="stAppViewContainer"]'),
                doc.querySelector('[data-testid="stMain"]'),
                doc.querySelector('[data-testid="stMainBlockContainer"]')
            ].filter(Boolean);
            for (const t of targets) {
                try {
                    if (typeof t.scrollTo === 'function') {
                        t.scrollTo({ top: 0, left: 0, behavior: 'auto' });
                    }
                    t.scrollTop = 0;
                } catch(e) {}
            }
        };
        forceTop();
        setTimeout(forceTop, 50);
        setTimeout(forceTop, 150);
        setTimeout(forceTop, 350);
        setTimeout(forceTop, 700);
        </script>
        """,
        height=0,
        width=0,
    )


def update_url_page(page_key: str) -> None:
    """Keep the current app page in the browser URL so Back/Forward works inside WorkZo."""
    try:
        st.query_params["page"] = page_key
    except Exception:
        pass


def read_url_page(default: str = "dashboard") -> str:
    try:
        value = st.query_params.get("page", default)
        if isinstance(value, list):
            value = value[0] if value else default
        return value or default
    except Exception:
        return default


def sync_navigation_state(page_key: str) -> None:
    """Store the selected page, update the URL, and always start the new page from the top."""
    st.session_state.page = page_key
    st.session_state.nav_page = page_key
    st.session_state.nav_change_nonce = st.session_state.get("nav_change_nonce", 0) + 1
    update_url_page(page_key)
    request_scroll_to_top()

def queue_navigation(page_key: str) -> None:
    """Button callback used by dashboard navigation cards."""
    st.session_state._workzo_pending_nav = page_key
    request_scroll_to_top()

def consume_pending_navigation() -> None:
    page_key = st.session_state.pop("_workzo_pending_nav", None)
    if page_key:
        sync_navigation_state(page_key)

def go_home() -> None:
    queue_navigation("dashboard")


def register_request() -> None:
    st.session_state.request_count += 1


# =========================================================
# BETA ANALYTICS - PRIVACY SAFE
# =========================================================
ANALYTICS_FILE = os.path.join(BASE_DIR, "workzo_beta_analytics.csv")
FEEDBACK_FILE = os.path.join(BASE_DIR, "workzo_beta_feedback.csv")

def get_or_create_anonymous_user_id() -> str:
    if "anonymous_user_id" not in st.session_state:
        st.session_state.anonymous_user_id = str(uuid.uuid4())
        st.session_state.is_repeat_user = False
    return st.session_state.anonymous_user_id

def get_or_create_session_id() -> str:
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.session_started_at = time.time()
    return st.session_state.session_id

def init_beta_analytics():
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
    for r in rows:
        uid, sid = _uid(r), _sid(r)
        if uid and sid:
            user_sessions.setdefault(uid, set()).add(sid)
    returning_users = sum(1 for sessions in user_sessions.values() if len(sessions) > 1)
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

    st.caption("*User and returning-user counts are approximate in Streamlit because users can refresh, change browser, or clear sessions. Treat trends as more important than exact numbers.")

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
    with st.expander("🐞 Report a problem", expanded=False):
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

</style>
""", unsafe_allow_html=True)

# =========================================================
# UI LANGUAGE TEXT
# =========================================================
UI_TEXT = {
    "English": {
        "title": "Your 360° AI Career Assistant",
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
        "title": "Dein 360° KI-Karriereassistent",
        "subtitle": "KI-gestützte Karrierehilfe basierend auf deinem Land und deinem Lebenslauf.",
        "onboarding_title": "Willkommen bei WorkZo",
        "onboarding_subtitle": "Starte mit deinem Land und deinem Lebenslauf. WorkZo erstellt den Rest daraus.",
        "country": "Land auswählen",
        "ui_language": "App-Sprache",
        "response_language": "Antwortsprache der KI",
        "resume_input": "Lebenslauf-Eingabe",
        "upload_cv": "Lebenslauf hochladen",
        "create_cv": "Lebenslauf erstellen",
        "upload_resume": "Lebenslauf hochladen",
        "create_resume": "Lebenslauf erstellen",
        "full_name": "Vollständiger Name",
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
        "mock_interview": "Vorstellungsgespräch",
        "skill_gap": "Kompetenzlücke",
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
        "dashboard_desc_short": "Starte hier: Scores, nächste Schritte und empfohlene Aktionen.",
        "job_assist_desc_short": "Finde Jobs oder verstehe eine Stellenbeschreibung vor der Bewerbung.",
        "cv_documents_desc_short": "Verbessere Lebenslauf, erstelle Anschreiben, übersetze Dokumente und nutze Länder-Vorlagen.",
        "interview_practice_desc_short": "Übe Interviewantworten, Mock-Fragen und mündliche Vorbereitung.",
        "career_insights_desc_short": "Prüfe Kompetenzlücken, Roadmap, Länder-Eignung und nächsten besten Schritt.",
        "preferred_language_help": "Eine Sprache für App, KI-Antworten und Dokumente.",
        "start_actions_title": "Was möchtest du heute tun?",
        "go_job_assist": "Job analysieren / Jobs finden",
        "go_cv_documents": "CV / Dokumente verbessern",
        "go_interview": "Interview üben",
        "go_career_insights": "Karriere-Einblicke ansehen",
        "start_here_intro": "Dein Dashboard zeigt eine stabile Lebenslaufanalyse, ATS-Bereitschaft und extrahierte Profildaten. Nutze das linke Menü für weitere Tools.",
        "detected_role": "Wahrscheinliche aktuelle Rolle",
        "detected_summary": "Berufliche Zusammenfassung",
        "detected_skills": "Wichtige Kenntnisse",
        "suggested_roles": "Vorgeschlagene Rollen",
        "resume_loaded": "Lebenslauf geladen",
        "yes": "Ja",
        "no": "Nein",
        "not_analyzed": "Noch nicht analysiert",
        "warn_country": "Bitte wähle ein Land.",
        "warn_upload_cv": "Bitte lade deinen Lebenslauf hoch.",
        "warn_full_name": "Bitte gib deinen vollständigen Namen ein.",
        "warn_summary": "Bitte gib deine berufliche Zusammenfassung ein.",
        "warn_skills": "Bitte gib deine Kenntnisse ein.",
        "warn_experience": "Bitte gib deine Berufserfahrung ein.",
        "warn_education": "Bitte gib deine Ausbildung ein.",
        "unsupported_file": "Nicht unterstützter Dateityp.",
        "ai_unavailable": "KI-Dienst nicht verfügbar",
        "job_desc": "Stellenbeschreibung einfügen",
        "your_cv": "Dein Lebenslauf",
        "target_job": "Ziel-Stellenbeschreibung einfügen",
        "job_title": "Berufsbezeichnung",
        "background": "Kurzer Hintergrund über dich",
        "preferred_location": "Bevorzugte Stadt oder Region",
        "target_role": "Zielrolle",
        "current_role": "Deine aktuelle Rolle",
        "current_profile": "Dein aktuelles Profil / Lebenslauf",
        "interview_language": "Sprache des Interviews",
        "enter_text": "Text eingeben",
        "improve": "Verbessern",
        "analyze": "Analysieren",
        "generate": "Erstellen",
        "translate": "Übersetzen",
        "job_fit_analysis": "Job-Fit-Analyse",
        "career_comm_result": "Feedback zur Karrierekommunikation",
        "search_queries": "Vorgeschlagene Suchlinks",
        "platform_hint": "Diese Links öffnen Suchseiten. Später kannst du lokale Jobportale nutzen.",
        "translator_source": "Ausgangssprache",
        "translator_target": "Zielsprache",
        "cover_letter_input": "Anschreiben einfügen",
        "cv_input": "Lebenslauf einfügen",
        "copy_ready": "Kopierfertige Ausgabe",
        "resume_score": "Lebenslauf-Score",
        "ats_score": "ATS-Score",
        "strengths": "Top-Stärken",
        "improvements": "Top-Verbesserungen",
        "job_fit_score": "Job-Fit",
        "skill_gap_score": "Kompetenzlücke",
        "interview_score": "Interview",
        "resume_insights": "Lebenslauf-Einblicke",
        "update_resume": "Lebenslauf aktualisieren",
        "top_countries_fit": "Top-Länder für diesen Lebenslauf",
        "country_fit_note": "Wahrscheinlich die stärksten Märkte basierend auf Sprache, Profil und Übertragbarkeit.",
        "detected_country": "Erkanntes Land",
        "refresh_resume": "Lebenslauf neu analysieren",
        "save_resume": "Als neuen Lebenslauf speichern",
        "document_hub_caption": "Alle Schreib- und Übersetzungstools an einem Ort.",
        "quick_prompts": "Schnellstarts",
        "chat_mode": "Modus",
        "chat_placeholder": "Frag Work-O-Bot etwas...",
        "clear_chat": "Chat löschen",
        "preferred_language": "Sprache auswählen",
        "user_status": "Aktuelle Karrieresituation",
        "fresh_graduate": "Absolvent/in / Berufseinsteiger/in",
        "student_thesis_internship": "Student/in / Abschlussarbeit / Praktikum",
        "career_changer": "Quereinsteiger/in",
        "migrant": "Migration / Bewerbung im Ausland geplant",
        "local_jobseeker": "Jobsuche im aktuellen Land",
        "experienced": "Erfahrene Fachkraft",
        "returning": "Rückkehr nach Karrierepause",
        "guided_cv_builder": "Geführter Lebenslauf-Builder",
        "generate_cv": "Lebenslauf mit KI erstellen",
        "extra_cv_info": "Möchtest du weitere Informationen hinzufügen?",
        "country_readiness": "Länder-Eignung",
        "next_steps": "Was solltest du als Nächstes tun?",
        "cv_template_builder": "Länderspezifischer Lebenslauf-Builder",
        "migration_country": "In welches Land möchtest du ziehen/dich bewerben?",
        "chosen_country_resume_score": "Lebenslauf-Eignung für das gewählte Land",
    },
    "Dutch": {
        "title": "Jouw 360° AI-carrièreassistent",
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
        "career_communication": "Carrièrecommunicatie",
        "find_jobs": "Banen vinden",
        "mock_interview": "Proefinterview",
        "skill_gap": "Vaardigheidskloof",
        "career_roadmap": "Carrièreplan",
        "job_assist": "Jobhulp",
        "document_tools": "Documenttools",
        "cv_translator": "CV vertalen",
        "cover_letter_generator": "Motivatiebrief maken",
        "cover_letter_translator": "Motivatiebrief vertalen",
        "workobot": "Work-O-Bot",
        "workobot_sub": "AI carrière- en taalcoach",
        "workobot_desc_short": "Mock-interviews, carrière-inzichten, skill gaps, communicatie-oefening en Work-O-Bot chat.",
        "go_workobot": "Open Work-O-Bot",
        "cv_documents": "CV & Documenten",
        "interview_practice": "Interview oefenen",
        "career_insights": "Carrière-inzichten",
        "navigation_help": "Waar vind je wat",
        "dashboard_desc_short": "Begin hier: scores, volgende stappen en aanbevolen acties.",
        "job_assist_desc_short": "Vind banen of begrijp een vacaturetekst voordat je solliciteert.",
        "cv_documents_desc_short": "Verbeter je CV, maak brieven, vertaal documenten en gebruik landen-CV-templates.",
        "interview_practice_desc_short": "Oefen interviewantwoorden, mockvragen en spreekvoorbereiding.",
        "career_insights_desc_short": "Bekijk skill gaps, roadmap, landenfit en volgende beste stap.",
        "preferred_language_help": "Eén taal voor app, AI-antwoorden en documenten.",
        "start_actions_title": "Wat wil je vandaag doen?",
        "go_job_assist": "Vacature analyseren / banen vinden",
        "go_cv_documents": "CV / documenten verbeteren",
        "go_interview": "Interview oefenen",
        "go_career_insights": "Carrière-inzichten bekijken",
        "start_here_intro": "Je dashboard toont een stabiele cv-analyse, ATS-gereedheid en geëxtraheerde profielgegevens. Gebruik daarna het linkermenu voor meer tools.",
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
        "career_comm_result": "Feedback op carrièrecommunicatie",
        "search_queries": "Voorgestelde zoeklinks",
        "platform_hint": "Deze links openen zoekpagina’s. Later kun je lokale vacatureplatforms gebruiken.",
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
        "document_hub_caption": "Houd al je schrijf- en vertaaltools op één plek.",
        "quick_prompts": "Snelle prompts",
        "chat_mode": "Modus",
        "chat_placeholder": "Vraag Work-O-Bot iets...",
        "clear_chat": "Chat wissen",
    }
}

def ui_lang() -> str:
    # Keep the user's selected language even when we do not have a manual UI_TEXT dictionary for it.
    # This allows French, Portuguese, Spanish, etc. to use the automatic translation fallback.
    return st.session_state.get("preferred_language", st.session_state.get("ui_language", "English")) or "English"

def ui_label(text: str) -> str:
    """Translate a visible UI phrase automatically when the selected language is not English."""
    lang = ui_lang()
    return ai_translate_ui(text, lang) if lang != "English" else text

def txt(key: str) -> str:
    lang = ui_lang()

    # 1) Use a manually curated translation if available.
    val = UI_TEXT.get(lang, {}).get(key)
    if val:
        return val

    # 2) If the selected language is not manually supported, translate from the English label.
    english_val = UI_TEXT.get("English", {}).get(key)
    if english_val:
        return ai_translate_ui(english_val, lang)

    # 3) Last fallback: translate a cleaned version of the key.
    readable_key = str(key).replace("_", " ").strip()
    return ai_translate_ui(readable_key, lang)



# =========================================================
# STUDENT / THESIS / INTERNSHIP CAREER PATH
# =========================================================
STUDENT_STATUS_INTERNAL = "Student / Thesis / Internship seeker"

STUDENT_JOB_KEYWORDS_BY_COUNTRY = {
    "germany": ["Praktikum", "Werkstudent", "Abschlussarbeit", "Bachelorarbeit", "Masterarbeit", "Thesis", "Trainee"],
    "austria": ["Praktikum", "Werkstudent", "Abschlussarbeit", "Bachelorarbeit", "Masterarbeit", "Trainee"],
    "switzerland": ["Praktikum", "Werkstudent", "Internship", "Thesis", "Trainee"],
    "netherlands": ["Stage", "Afstudeerstage", "Werkstudent", "Internship", "Traineeship"],
    "the netherlands": ["Stage", "Afstudeerstage", "Werkstudent", "Internship", "Traineeship"],
    "belgium": ["Stage", "Internship", "Student job", "Thesis", "Traineeship"],
    "france": ["Stage", "Alternance", "Apprentissage", "Internship", "Trainee"],
    "spain": ["Prácticas", "Becario", "Internship", "Trainee"],
    "italy": ["Tirocinio", "Stage", "Internship", "Trainee"],
    "portugal": ["Estágio", "Internship", "Trainee"],
    "united kingdom": ["Placement Year", "Internship", "Graduate Intern", "Industrial Placement", "Sandwich Placement"],
    "uk": ["Placement Year", "Internship", "Graduate Intern", "Industrial Placement", "Sandwich Placement"],
    "ireland": ["Internship", "Graduate Intern", "Placement", "Trainee"],
    "united states": ["Internship", "Co-op", "Student Intern", "New Grad", "Campus"],
    "usa": ["Internship", "Co-op", "Student Intern", "New Grad", "Campus"],
    "canada": ["Internship", "Co-op", "Student Intern", "New Grad", "Campus"],
    "india": ["Internship", "Trainee", "Fresher Internship", "Graduate Trainee", "Campus"],
    "australia": ["Internship", "Vacation Program", "Graduate Program", "Student Intern"],
    "new zealand": ["Internship", "Graduate Program", "Student Intern"],
    "singapore": ["Internship", "Traineeship", "Graduate Intern", "Student Intern"],
    "default": ["Internship", "Student Intern", "Thesis", "Placement", "Working Student", "Trainee", "Graduate Intern"],
}

def is_student_thesis_status(user_status: str) -> bool:
    status = (user_status or "").lower()
    return any(x in status for x in ["student / thesis", "thesis", "internship seeker", "praktikum", "placement", "afstudeer", "abschlussarbeit", "werkstudent", "stagezoeker"])

def get_student_job_keywords(country_name: str) -> List[str]:
    country = (country_name or st.session_state.get("migration_country") or st.session_state.get("country") or "").strip().lower()
    return STUDENT_JOB_KEYWORDS_BY_COUNTRY.get(country, STUDENT_JOB_KEYWORDS_BY_COUNTRY["default"])

def render_student_opportunity_guidance(country_name: str):
    keywords = get_student_job_keywords(country_name)
    st.markdown(f"### {txt('student_opportunities')}")
    st.caption(txt("student_guidance_caption"))
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**{txt('student_search_keywords')}**")
        st.markdown(" ".join([f"<span class='pill'>{html.escape(k)}</span>" for k in keywords[:8]]), unsafe_allow_html=True)
    with c2:
        st.markdown(f"**{txt('student_cv_tips')}**")
        st.markdown("- Put education, thesis topic, and projects near the top.\n- Add tools, coursework, and university/research projects.\n- Use student-friendly role titles instead of only full-time junior roles.\n- Keep the CV focused on learning potential and practical proof.")

LANG_EXTRA = {
    "English": {
        "navigation": "Navigation", "workflow_progress": "Workflow progress", "suggested_workflow": "Suggested workflow",
        "workflow_upload_cv": "1. Upload CV", "workflow_understand_job": "2. Understand a job", "workflow_improve_cv": "3. Improve CV", "workflow_apply_smarter": "4. Apply smarter",
        "career_command_center": "Your Career Dashboard", "career_move_organized": "Everything you need to plan your next career step",
        "country_label": "Country", "status_label": "Status", "not_specified": "Not specified",
        "metric_resume_quality": "Overall quality and clarity", "metric_ats_friendly": "How scanner-friendly your resume looks", "metric_detected_resume": "Detected from your current resume",
        "target_roles": "Target roles", "metric_role_cluster": "Suggested role cluster options", "what_next": "What you should do next",
        "next_default_1": "Improve the weakest CV sections first.", "next_default_2": "Use Job Assist after your CV is ready.", "next_default_3": "Tailor the CV for each job description.",
        "next_migrate_1": "Adapt your CV to the target-country format.", "next_migrate_2": "Add local role keywords and remove country-inappropriate details.", "next_migrate_3": "Use Document Tools → Country CV Template before applying.",
        "next_graduate_1": "Add 1–2 portfolio projects.", "next_graduate_2": "Highlight tools, coursework, internships, and projects.", "next_graduate_3": "Target entry-level, trainee, or junior roles.",
        "next_changer_1": "Connect your previous experience to the target role.", "next_changer_2": "Add proof projects and bridge skills.", "next_changer_3": "Avoid applying directly to senior roles in the new field.",
        "country_cv_readiness": "Country CV readiness", "status_guidance": "Status guidance", "target_country_label": "Target country", "judge_market": "WorkZo will judge your CV against this market.", "use_country_template": "Use the Country CV Template tool if the format does not match the target country.",
        "job_assist_desc": "Understand a role, find live jobs, and see where you realistically fit before applying.", "document_tools_desc": "Improve your CV, generate a cover letter, translate documents, and update your resume faster.", "workobot_desc": "Country-aware coaching for interviews, communication, mock questions, and next steps.",
        "standout_next_best_step": "Standout feature: Next Best Step", "next_best_caption": "A personalized action center based on your resume, country, and role direction.", "generate_next_best_step": "Generate My Next Best Step", "building_action_center": "Building your action center...", "refreshing": "Refreshing...", "dashboard_updated": "Dashboard updated.",
        "next_best_empty": "Generate a personalized action center to see your best immediate goal, weekly priorities, role cluster, and the message you should send today.",
        "founder_dashboard": "Founder Dashboard", "founder_access": "Founder access", "founder_pin": "Founder PIN", "open_job": "Open job", "job_summary_first": "Top matches first. Click any job card to open the posting.", "details_later": "Show details", "country_fit_summary": "Country fit summary", "country_fit_details": "Country-fit details", "view_details": "View details", "no_founder_pin": "Add FOUNDER_PIN in secrets to unlock founder analytics.", "recommended_next_step": "Recommended Next Step", "next_action_upload_title": "Upload your CV first", "next_action_upload_desc": "WorkZo needs your CV to calculate scores and guide your next career step.", "next_action_upload_button": "Upload CV", "next_action_improve_title": "Improve your CV for ATS", "next_action_improve_desc": "Your ATS score can improve. Start by strengthening keywords, structure, and country-specific formatting.", "next_action_improve_button": "Improve My CV", "next_action_job_title": "Analyze a job before applying", "next_action_job_desc": "Your CV is ready. Paste a job description or find matching jobs to understand your fit.", "next_action_job_button": "Go to Job Assist", "next_action_interview_title": "Practice for your next interview", "next_action_interview_desc": "You have started job preparation. Now practice answers based on your profile and target role.", "next_action_interview_button": "Practice Interview"
    },
    "German": {
        "navigation": "Navigation", "workflow_progress": "Workflow-Fortschritt", "suggested_workflow": "Empfohlener Ablauf",
        "workflow_upload_cv": "1. Lebenslauf hochladen", "workflow_understand_job": "2. Stelle verstehen", "workflow_improve_cv": "3. Lebenslauf verbessern", "workflow_apply_smarter": "4. Gezielter bewerben",
        "career_command_center": "Karriere-Kommandozentrale", "career_move_organized": "Dein nächster Karriereschritt, klar organisiert",
        "country_label": "Land", "status_label": "Status", "not_specified": "Nicht angegeben",
        "metric_resume_quality": "Gesamtqualität und Klarheit", "metric_ats_friendly": "Wie ATS-freundlich dein Lebenslauf wirkt", "metric_detected_resume": "Aus deinem aktuellen Lebenslauf erkannt",
        "target_roles": "Zielrollen", "metric_role_cluster": "Vorgeschlagene Rollen-Cluster", "what_next": "Was du als Nächstes tun solltest",
        "next_default_1": "Verbessere zuerst die schwächsten Lebenslaufbereiche.", "next_default_2": "Nutze den Job-Assistenten, sobald dein Lebenslauf bereit ist.", "next_default_3": "Passe den Lebenslauf an jede Stellenbeschreibung an.",
        "next_migrate_1": "Passe deinen Lebenslauf an das Format des Ziellandes an.", "next_migrate_2": "Ergänze lokale Rollen-Keywords und entferne unpassende Angaben.", "next_migrate_3": "Nutze vor der Bewerbung Dokument-Tools → Lebenslauf-Vorlage nach Land.",
        "next_graduate_1": "Füge 1–2 Portfolio-Projekte hinzu.", "next_graduate_2": "Betone Tools, Kurse, Praktika und Projekte.", "next_graduate_3": "Bewirb dich gezielt auf Einstiegs-, Trainee- oder Junior-Rollen.",
        "next_changer_1": "Verbinde deine bisherige Erfahrung klar mit der Zielrolle.", "next_changer_2": "Füge Nachweisprojekte und Brückenkompetenzen hinzu.", "next_changer_3": "Bewirb dich im neuen Bereich nicht direkt auf Senior-Rollen.",
        "country_cv_readiness": "Lebenslauf-Eignung für das Zielland", "status_guidance": "Hinweise zu deiner Situation", "target_country_label": "Zielland", "judge_market": "WorkZo bewertet deinen Lebenslauf für diesen Arbeitsmarkt.", "use_country_template": "Nutze die Lebenslauf-Vorlage nach Land, wenn das Format nicht zum Zielland passt.",
        "job_assist_desc": "Verstehe eine Rolle, finde Live-Jobs und erkenne realistisch, wo du vor der Bewerbung passt.", "document_tools_desc": "Verbessere deinen Lebenslauf, erstelle ein Anschreiben, übersetze Dokumente und aktualisiere deine Bewerbung schneller.", "workobot_desc": "Länderspezifisches Coaching für Interviews, Kommunikation, Übungsfragen und nächste Schritte.",
        "standout_next_best_step": "Besondere Funktion: Nächster bester Schritt", "next_best_caption": "Ein personalisiertes Aktionszentrum basierend auf deinem Lebenslauf, Land und deiner Rollenrichtung.", "generate_next_best_step": "Meinen nächsten besten Schritt erstellen", "building_action_center": "Aktionszentrum wird erstellt...", "refreshing": "Aktualisiere...", "dashboard_updated": "Dashboard aktualisiert.",
        "next_best_empty": "Erstelle ein personalisiertes Aktionszentrum, um dein wichtigstes Sofortziel, Wochenprioritäten, Rollen-Cluster und die heutige Nachricht zu sehen.",
        "founder_dashboard": "Founder-Dashboard", "founder_access": "Founder-Zugang", "founder_pin": "Founder-PIN", "open_job": "Job öffnen", "job_summary_first": "Beste Treffer zuerst. Klicke auf eine Jobkarte, um die Anzeige zu öffnen.", "details_later": "Details anzeigen", "country_fit_summary": "Beste Länder für diesen Lebenslauf", "country_fit_details": "Details zur Länder-Eignung", "view_details": "Details anzeigen", "no_founder_pin": "Füge FOUNDER_PIN in Secrets hinzu, um Founder Analytics zu öffnen.", "recommended_next_step": "Empfohlener nächster Schritt", "next_action_upload_title": "Lade zuerst deinen Lebenslauf hoch", "next_action_upload_desc": "WorkZo braucht deinen Lebenslauf, um Scores zu berechnen und deinen nächsten Karriereschritt zu empfehlen.", "next_action_upload_button": "Lebenslauf hochladen", "next_action_improve_title": "Verbessere deinen Lebenslauf für ATS", "next_action_improve_desc": "Dein ATS-Score kann besser werden. Stärke zuerst Keywords, Struktur und länderspezifisches Format.", "next_action_improve_button": "Lebenslauf verbessern", "next_action_job_title": "Analysiere eine Stelle vor der Bewerbung", "next_action_job_desc": "Dein Lebenslauf ist bereit. Füge eine Stellenbeschreibung ein oder finde passende Jobs.", "next_action_job_button": "Zum Job-Assistenten", "next_action_interview_title": "Übe für dein nächstes Interview", "next_action_interview_desc": "Du hast mit der Bewerbungsvorbereitung begonnen. Übe jetzt Antworten passend zu Profil und Zielrolle.", "next_action_interview_button": "Interview üben"
    },
    "Dutch": {
        "navigation": "Navigatie", "workflow_progress": "Workflowvoortgang", "suggested_workflow": "Aanbevolen workflow",
        "workflow_upload_cv": "1. CV uploaden", "workflow_understand_job": "2. Vacature begrijpen", "workflow_improve_cv": "3. CV verbeteren", "workflow_apply_smarter": "4. Slimmer solliciteren",
        "career_command_center": "Carrière-commandocentrum", "career_move_organized": "Je volgende carrièremove, helder georganiseerd",
        "country_label": "Land", "status_label": "Status", "not_specified": "Niet opgegeven",
        "metric_resume_quality": "Algemene kwaliteit en duidelijkheid", "metric_ats_friendly": "Hoe ATS-vriendelijk je cv is", "metric_detected_resume": "Gedetecteerd uit je huidige cv",
        "target_roles": "Doelrollen", "metric_role_cluster": "Voorgestelde rolclusters", "what_next": "Wat je nu moet doen",
        "next_default_1": "Verbeter eerst de zwakste cv-onderdelen.", "next_default_2": "Gebruik Jobhulp zodra je cv klaar is.", "next_default_3": "Pas je cv aan voor elke vacaturetekst.",
        "next_migrate_1": "Pas je cv aan aan het format van het doelland.", "next_migrate_2": "Voeg lokale rolkeywords toe en verwijder ongepaste gegevens.", "next_migrate_3": "Gebruik Documenttools → Country CV Template voordat je solliciteert.",
        "next_graduate_1": "Voeg 1–2 portfolio-projecten toe.", "next_graduate_2": "Benadruk tools, cursussen, stages en projecten.", "next_graduate_3": "Richt je op starters-, trainee- of juniorrollen.",
        "next_changer_1": "Koppel je eerdere ervaring aan de doelrol.", "next_changer_2": "Voeg bewijsprojecten en brugvaardigheden toe.", "next_changer_3": "Solliciteer niet direct op seniorrollen in het nieuwe vakgebied.",
        "country_cv_readiness": "CV-gereedheid voor doelland", "status_guidance": "Advies voor je situatie", "target_country_label": "Doelland", "judge_market": "WorkZo beoordeelt je cv voor deze arbeidsmarkt.", "use_country_template": "Gebruik de Country CV Template-tool als het format niet past bij het doelland.",
        "job_assist_desc": "Begrijp een rol, vind live vacatures en zie realistisch waar je past voordat je solliciteert.", "document_tools_desc": "Verbeter je cv, maak een motivatiebrief, vertaal documenten en werk je sollicitatie sneller bij.", "workobot_desc": "Landbewuste coaching voor interviews, communicatie, oefenvragen en vervolgstappen.",
        "standout_next_best_step": "Sterke functie: Volgende beste stap", "next_best_caption": "Een persoonlijk actiecentrum gebaseerd op je cv, land en rolrichting.", "generate_next_best_step": "Maak mijn volgende beste stap", "building_action_center": "Actiecentrum wordt gemaakt...", "refreshing": "Vernieuwen...", "dashboard_updated": "Dashboard bijgewerkt.",
        "next_best_empty": "Maak een persoonlijk actiecentrum om je beste directe doel, weekprioriteiten, rolcluster en het bericht dat je vandaag moet sturen te zien.",
        "founder_dashboard": "Founder dashboard",
        "founder_access": "Founder access",
        "founder_pin": "Founder PIN",
        "open_job": "Open job",
        "job_summary_first": "Best matches first. Click a job card to open it.",
        "details_later": "Show details",
        "country_fit_summary": "Country fit",
        "country_fit_details": "Country fit details",
        "view_details": "View details",
        "no_founder_pin": "Add FOUNDER_PIN in secrets to unlock founder analytics.",
        "recommended_next_step": "Recommended next step",
        "next_action_upload_title": "Upload your CV first",
        "next_action_upload_desc": "WorkZo needs your CV to calculate scores and guide your next career step.",
        "next_action_upload_button": "Upload CV",
        "next_action_improve_title": "Improve your CV for ATS",
        "next_action_improve_desc": "Your ATS score can improve. Start with keywords, structure and country-specific formatting.",
        "next_action_improve_button": "Improve my CV",
        "next_action_job_title": "Analyze a job before applying",
        "next_action_job_desc": "Your CV is ready. Paste a job description or find matching jobs.",
        "next_action_job_button": "Go to Job Help",
        "next_action_interview_title": "Practice for your next interview",
        "next_action_interview_desc": "Practice answers based on your profile and target role.",
        "next_action_interview_button": "Practice interview"
    }
}
for _lang, _items in LANG_EXTRA.items():
    UI_TEXT.setdefault(_lang, {}).update(_items)

# =========================================================
# UI LOCALIZATION CLEANUP PATCH (WorkZo v8.1)
# Fixes mixed English/German/Dutch labels in onboarding and CV builder.
# =========================================================
UI_LOCALIZATION_PATCH = {
    "English": {
        "select_optional": "Select one option",
        "beta_privacy_note": "⚠️ WorkZo AI is currently in Beta. Some results may not be perfect yet. Your feedback helps improve the tool. Privacy note: WorkZo collects anonymous usage data such as features used, selected country/status, and session duration. It does not store your CV text, email, phone number, address, or personal documents.",
        "language_help": "This language is used for the app, AI replies, and generated documents.",
        "status_help": "Optional. Select this only if it matches your current situation.",
        "resume_choice_caption": "Choose one option to add your resume. You can upload an existing CV or create one with the guided builder.",
        "upload_cv_title": "Upload CV",
        "upload_cv_desc": "Best if you already have a PDF or text CV.",
        "create_cv_title": "Create CV",
        "create_cv_desc": "Best if you want WorkZo to build a CV from your details.",
        "choose_resume_continue": "Please choose Upload CV or Create CV to continue.",
        "file_too_large": "File too large. Please upload a CV under 5 MB.",
        "upload_cv_instruction": "Please upload a PDF or TXT CV using the Upload CV option above.",
        "guided_cv_caption": "Add what you know. WorkZo will generate a cleaner CV and ask what is missing.",
        "location": "Location",
        "languages_label": "Languages",
        "cert_courses": "Certifications / Courses",
        "projects_label": "Projects",
        "pdf_read_error": "PDF read error",
    },
    "German": {
        "select_optional": "Option auswählen",
        "beta_privacy_note": "⚠️ WorkZo AI ist aktuell in der Beta-Version. Manche Ergebnisse sind möglicherweise noch nicht perfekt. Dein Feedback hilft, das Tool zu verbessern. Datenschutzhinweis: WorkZo erfasst anonyme Nutzungsdaten wie verwendete Funktionen, ausgewähltes Land/Status und Sitzungsdauer. Dein Lebenslauftext, deine E-Mail, Telefonnummer, Adresse oder persönliche Dokumente werden nicht gespeichert.",
        "language_help": "Diese Sprache wird für die App, KI-Antworten und erstellte Dokumente verwendet.",
        "status_help": "Optional. Wähle dies nur aus, wenn es zu deiner aktuellen Situation passt.",
        "resume_choice_caption": "Wähle eine Option aus, um deinen Lebenslauf hinzuzufügen. Du kannst einen vorhandenen Lebenslauf hochladen oder mit dem geführten Builder einen neuen erstellen.",
        "upload_cv_title": "Lebenslauf hochladen",
        "upload_cv_desc": "Ideal, wenn du bereits einen PDF- oder Text-Lebenslauf hast.",
        "create_cv_title": "Lebenslauf erstellen",
        "create_cv_desc": "Ideal, wenn WorkZo aus deinen Angaben einen Lebenslauf erstellen soll.",
        "choose_resume_continue": "Bitte wähle Lebenslauf hochladen oder Lebenslauf erstellen, um fortzufahren.",
        "file_too_large": "Die Datei ist zu groß. Bitte lade einen Lebenslauf unter 5 MB hoch.",
        "upload_cv_instruction": "Bitte lade oben über die Option Lebenslauf hochladen eine PDF- oder TXT-Datei hoch.",
        "guided_cv_caption": "Füge hinzu, was du weißt. WorkZo erstellt daraus einen klareren Lebenslauf und ergänzt fehlende Punkte.",
        "location": "Standort",
        "languages_label": "Sprachen",
        "cert_courses": "Zertifikate / Kurse",
        "projects_label": "Projekte",
        "pdf_read_error": "PDF-Lesefehler",
        "career_command_center": "Dein Karriere-Dashboard",
        "career_move_organized": "Alles, was du für deinen nächsten Karriereschritt brauchst",
    },
    "Dutch": {
        "preferred_language": "Taal selecteren",
        "user_status": "Huidige carrièresituatie",
        "fresh_graduate": "Afgestudeerd / starter",
        "student_thesis_internship": "Student / scriptie / stagezoeker",
        "career_changer": "Carrièreswitcher",
        "migrant": "Verhuizen / solliciteren in het buitenland",
        "local_jobseeker": "Lokaal werk zoeken",
        "experienced": "Ervaren professional",
        "returning": "Terugkeer na loopbaanpauze",
        "guided_cv_builder": "Begeleide CV-builder",
        "generate_cv": "CV genereren met AI",
        "extra_cv_info": "Wil je extra informatie toevoegen?",
        "country_readiness": "Landgeschiktheid",
        "next_steps": "Wat moet je nu doen?",
        "cv_template_builder": "Landspecifieke CV-builder",
        "migration_country": "Naar welk land wil je verhuizen/solliciteren?",
        "chosen_country_resume_score": "CV-gereedheid voor gekozen land",
        "select_optional": "Selecteer een optie",
        "beta_privacy_note": "⚠️ WorkZo AI is momenteel in bèta. Sommige resultaten zijn mogelijk nog niet perfect. Jouw feedback helpt om de tool te verbeteren. Privacyverklaring: WorkZo verzamelt anonieme gebruiksgegevens zoals gebruikte functies, gekozen land/status en sessieduur. Je CV-tekst, e-mail, telefoonnummer, adres of persoonlijke documenten worden niet opgeslagen.",
        "language_help": "Deze taal wordt gebruikt voor de app, AI-antwoorden en gegenereerde documenten.",
        "status_help": "Optioneel. Selecteer dit alleen als het past bij je huidige situatie.",
        "resume_choice_caption": "Kies één optie om je CV toe te voegen. Je kunt een bestaand CV uploaden of er een maken met de begeleide builder.",
        "upload_cv_title": "CV uploaden",
        "upload_cv_desc": "Beste keuze als je al een PDF- of tekst-CV hebt.",
        "create_cv_title": "CV maken",
        "create_cv_desc": "Beste keuze als je wilt dat WorkZo een CV maakt op basis van jouw gegevens.",
        "choose_resume_continue": "Kies CV uploaden of CV maken om door te gaan.",
        "file_too_large": "Bestand is te groot. Upload een CV kleiner dan 5 MB.",
        "upload_cv_instruction": "Upload hierboven een PDF- of TXT-CV via de optie CV uploaden.",
        "guided_cv_caption": "Voeg toe wat je weet. WorkZo maakt er een duidelijker CV van en vult ontbrekende punten aan.",
        "location": "Locatie",
        "languages_label": "Talen",
        "cert_courses": "Certificaten / Cursussen",
        "projects_label": "Projecten",
        "pdf_read_error": "PDF-leesfout",
    },
}
for _lang, _items in UI_LOCALIZATION_PATCH.items():
    UI_TEXT.setdefault(_lang, {}).update(_items)

# =========================================================
# ONBOARDING GLOBAL UX PATCH (WorkZo v9.7)
# =========================================================
ONBOARDING_GLOBAL_TEXT = {
    "English": {
        "app_info_help": "WorkZo analyzes your resume, adapts it to your selected country, suggests jobs, identifies skill gaps, and helps you prepare for interviews.",
        "privacy_short": "⚠️ WorkZo AI is currently in Beta. Some results may not be perfect yet. Your feedback helps improve the tool. Privacy note: WorkZo collects anonymous usage data such as features used, selected country/status, and session duration. It does not store your CV text, email, phone number, address, or personal documents.",
        "detected_country_hint": "Suggested country based on your location",
        "resume_choice_caption": "Choose how you want to start. You can upload a CV, create one with AI, or paste a LinkedIn profile link.",
        "upload_cv_desc": "Upload an existing PDF or TXT CV.",
        "create_cv_desc": "Enter rough notes or broken English. WorkZo will turn them into a professional CV.",
        "linkedin_cv_title": "Import LinkedIn",
        "linkedin_cv_desc": "Paste your LinkedIn profile link and add any extra notes.",
        "linkedin_profile_link": "LinkedIn Profile Link",
        "linkedin_extra_details": "Optional: paste LinkedIn About / Experience text or extra notes",
        "linkedin_instruction": "Public LinkedIn pages are often restricted. For best results, paste your LinkedIn link plus your About, Experience, Skills, or key notes.",
        "choose_resume_continue": "Choose one resume option to continue.",
        "upload_cv_instruction": "Upload your CV",
        "guided_cv_caption": "Write in keywords or broken English if needed. WorkZo will clean, expand, and translate it based on your selected language.",
        "suggested_skills": "Suggested skills",
        "education_level": "Education level",
        "target_role_optional": "Target role / job title",
        "generated_language_note": "Generated CV language",
        "select_upload": "Upload CV",
        "select_create": "Create CV",
        "select_linkedin": "Import LinkedIn"
    },
    "German": {
        "app_info_help": "WorkZo analysiert deinen Lebenslauf, passt ihn an das gewählte Land an, schlägt Jobs vor, erkennt Kompetenzlücken und hilft bei der Interviewvorbereitung.",
        "privacy_short": "Beta-Datenschutz: Anonyme Nutzung wird erfasst, aber Lebenslauftext und persönliche Dokumente werden nicht gespeichert.",
        "detected_country_hint": "Vorgeschlagenes Land basierend auf deinem Standort",
        "resume_choice_caption": "Wähle, wie du starten möchtest: CV hochladen, mit KI erstellen oder LinkedIn-Profil einfügen.",
        "upload_cv_desc": "Lade einen vorhandenen PDF- oder TXT-Lebenslauf hoch.",
        "create_cv_desc": "Gib grobe Notizen oder fehlerhaftes Englisch ein. WorkZo erstellt daraus einen professionellen Lebenslauf.",
        "linkedin_cv_title": "LinkedIn importieren",
        "linkedin_cv_desc": "Füge deinen LinkedIn-Profillink ein und ergänze Notizen.",
        "linkedin_profile_link": "LinkedIn-Profillink",
        "linkedin_extra_details": "Optional: LinkedIn-Info / Erfahrung oder zusätzliche Notizen einfügen",
        "linkedin_instruction": "Öffentliche LinkedIn-Seiten sind oft eingeschränkt. Für beste Ergebnisse: Link plus Info, Erfahrung, Skills oder Stichpunkte einfügen.",
        "guided_cv_caption": "Schreibe bei Bedarf Stichwörter oder fehlerhaftes Englisch. WorkZo bereinigt, erweitert und übersetzt es passend zur gewählten Sprache.",
        "suggested_skills": "Vorgeschlagene Fähigkeiten",
        "education_level": "Bildungsniveau",
        "target_role_optional": "Zielrolle / Berufsbezeichnung",
        "generated_language_note": "Sprache des generierten Lebenslaufs",
        "select_upload": "Upload auswählen",
        "select_create": "Erstellen auswählen",
        "select_linkedin": "LinkedIn auswählen"
    },
    "Dutch": {
        "app_info_help": "WorkZo analyseert je CV, past het aan je geselecteerde land aan, suggereert banen, vindt vaardigheidskloven en helpt met interviewvoorbereiding.",
        "privacy_short": "Bèta-privacy: anoniem gebruik wordt bijgehouden, maar CV-tekst en persoonlijke documenten worden niet opgeslagen.",
        "detected_country_hint": "Voorgesteld land op basis van je locatie",
        "resume_choice_caption": "Kies hoe je wilt starten: CV uploaden, met AI maken of LinkedIn-profiel plakken.",
        "upload_cv_desc": "Upload een bestaand PDF- of TXT-CV.",
        "create_cv_desc": "Voer ruwe notities of gebroken Engels in. WorkZo maakt er een professioneel CV van.",
        "linkedin_cv_title": "LinkedIn importeren",
        "linkedin_cv_desc": "Plak je LinkedIn-profiel en voeg extra notities toe.",
        "linkedin_profile_link": "LinkedIn-profiel link",
        "linkedin_extra_details": "Optioneel: plak LinkedIn Over / Ervaring of extra notities",
        "linkedin_instruction": "Openbare LinkedIn-pagina's zijn vaak beperkt. Plak voor het beste resultaat de link plus Over, Ervaring, Skills of kernpunten.",
        "guided_cv_caption": "Schrijf desnoods trefwoorden of gebroken Engels. WorkZo maakt het netter, breidt het uit en vertaalt het naar je gekozen taal.",
        "suggested_skills": "Voorgestelde vaardigheden",
        "education_level": "Opleidingsniveau",
        "target_role_optional": "Doelrol / functietitel",
        "generated_language_note": "Taal van gegenereerd CV",
        "select_upload": "Upload selecteren",
        "select_create": "Maken selecteren",
        "select_linkedin": "LinkedIn selecteren"
    },
}
for _lang, _items in ONBOARDING_GLOBAL_TEXT.items():
    UI_TEXT.setdefault(_lang, {}).update(_items)

# =========================================================
# DYNAMIC COUNTRY + LANGUAGE DATA
# =========================================================
def get_country_options() -> List[str]:
    if pycountry:
        countries = sorted({c.name for c in pycountry.countries if getattr(c, "name", None)})
    else:
        countries = [
            "Afghanistan", "Albania", "Algeria", "Argentina", "Australia", "Austria", "Bangladesh",
            "Belgium", "Brazil", "Bulgaria", "Canada", "Chile", "China", "Colombia", "Croatia",
            "Czechia", "Denmark", "Egypt", "Estonia", "Finland", "France", "Germany", "Greece",
            "Hungary", "India", "Indonesia", "Ireland", "Italy", "Japan", "Kenya", "Malaysia",
            "Mexico", "Netherlands", "New Zealand", "Nigeria", "Norway", "Pakistan", "Philippines",
            "Poland", "Portugal", "Romania", "Saudi Arabia", "Singapore", "South Africa", "South Korea",
            "Spain", "Sri Lanka", "Sweden", "Switzerland", "Thailand", "Turkey", "United Arab Emirates",
            "United Kingdom", "United States", "Vietnam"
        ]
    return countries

def get_language_options() -> List[str]:
    priority_languages = [
        "English", "German", "French", "Portuguese", "Spanish", "Dutch", "Italian",
        "Arabic", "Hindi", "Bengali", "Chinese", "Japanese", "Korean", "Tamil",
        "Telugu", "Malayalam", "Kannada", "Marathi", "Urdu", "Turkish", "Polish",
        "Romanian", "Swedish", "Norwegian", "Danish", "Finnish", "Greek", "Russian",
        "Ukrainian", "Indonesian", "Malay", "Thai", "Vietnamese"
    ]
    if pycountry:
        all_languages = sorted({
            getattr(lang, "name", "").strip()
            for lang in pycountry.languages
            if getattr(lang, "name", None)
            and len(getattr(lang, "name", "")) > 1
            and "sign language" not in getattr(lang, "name", "").lower()
        })
        languages = list(dict.fromkeys(priority_languages + all_languages))
    else:
        languages = priority_languages
    return languages

def get_geo_defaults() -> Tuple[str, str]:
    """
    Best-effort IP-based suggestion. Gracefully falls back.
    """
    if "geo_country_suggestion" in st.session_state and "geo_language_suggestion" in st.session_state:
        return st.session_state.geo_country_suggestion, st.session_state.geo_language_suggestion

    fallback_country = "Germany"
    fallback_language = "English"

    try:
        req = urllib.request.Request(
            "https://ipapi.co/json/",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=3) as response:
            payload = json.loads(response.read().decode("utf-8"))
            country_name = payload.get("country_name") or fallback_country

            languages_raw = payload.get("languages", "")
            first_lang_code = languages_raw.split(",")[0].split("-")[0].strip() if languages_raw else ""

            language_name = fallback_language
            if pycountry and first_lang_code:
                lang_obj = pycountry.languages.get(alpha_2=first_lang_code)
                if lang_obj and getattr(lang_obj, "name", None):
                    language_name = lang_obj.name

            st.session_state.geo_country_suggestion = country_name
            st.session_state.geo_language_suggestion = language_name
            return country_name, language_name
    except Exception:
        st.session_state.geo_country_suggestion = fallback_country
        st.session_state.geo_language_suggestion = fallback_language
        return fallback_country, fallback_language



def get_country_code(country_name: str) -> str:
    if not country_name or not pycountry:
        return ""
    try:
        obj = pycountry.countries.get(name=country_name)
        if obj and getattr(obj, "alpha_2", None):
            return obj.alpha_2
    except Exception:
        pass

    try:
        matches = pycountry.countries.search_fuzzy(country_name)
        if matches and getattr(matches[0], "alpha_2", None):
            return matches[0].alpha_2
    except Exception:
        pass
    return ""

@st.cache_data(show_spinner=False)
def get_local_city_index() -> Dict[str, List[str]]:
    """
    Local city index for fast suggestions. Uses geonamescache when available.
    """
    index: Dict[str, List[Tuple[str, int]]] = {}
    if not geonamescache:
        return {}

    try:
        gc = geonamescache.GeonamesCache(min_city_population=5000)
    except TypeError:
        gc = geonamescache.GeonamesCache()

    cities = gc.get_cities()

    for city in cities.values():
        name = (city.get("name") or "").strip()
        country_code = (city.get("countrycode") or "").strip().upper()
        population = int(city.get("population") or 0)

        if not name or not country_code:
            continue
        if population < 5000:
            continue

        index.setdefault(country_code, []).append((name, population))

    final_index: Dict[str, List[str]] = {}
    for code, rows in index.items():
        rows = sorted(rows, key=lambda x: (-x[1], x[0].lower()))
        seen = set()
        names = []
        for name, _ in rows:
            k = name.casefold()
            if k not in seen:
                seen.add(k)
                names.append(name)
        final_index[code] = names
    return final_index

@st.cache_data(show_spinner=False, ttl=86400)
def fetch_country_cities(country_name: str) -> List[str]:
    """
    Country-level city list with two layers:
    1) local geonamescache data when installed
    2) CountriesNow public API fallback for global coverage
    """
    country_code = get_country_code(country_name)
    merged: List[str] = []

    local_index = get_local_city_index()
    if country_code and country_code in local_index:
        merged.extend(local_index[country_code])

    urls = [
        "https://countriesnow.space/api/v0.1/countries/cities/q?country=" + urllib.parse.quote(country_name),
        "https://countriesnow.space/api/v0.1/countries/cities?country=" + urllib.parse.quote(country_name),
    ]

    for url in urls:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as response:
                payload = json.loads(response.read().decode("utf-8"))
                data = payload.get("data", [])
                if isinstance(data, list):
                    merged.extend([str(x).strip() for x in data if str(x).strip()])
                if merged:
                    break
        except Exception:
            continue

    deduped = []
    seen = set()
    for city in merged:
        k = city.casefold()
        if k not in seen:
            seen.add(k)
            deduped.append(city)

    return deduped

def fetch_city_suggestions(query: str, country_name: str = "", limit: int = 20) -> List[str]:
    query = (query or "").strip()
    cities = fetch_country_cities(country_name) if country_name else []

    if not cities:
        return []

    if not query:
        return cities[:limit]

    q = query.casefold()
    starts = [c for c in cities if c.casefold().startswith(q)]
    contains = [c for c in cities if q in c.casefold() and c not in starts]
    return (starts + contains)[:limit]

def http_get_json(url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 12) -> Dict:
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))

@st.cache_data(show_spinner=False, ttl=900)
def fetch_arbeitnow_jobs(query: str, location: str = "", limit: int = 15) -> List[Dict]:
    url = "https://www.arbeitnow.com/api/job-board-api"
    try:
        payload = http_get_json(url)
    except Exception:
        return []

    items = payload.get("data", []) if isinstance(payload, dict) else []
    q = (query or "").casefold()
    loc = (location or "").casefold()
    if loc.startswith("anywhere in "):
        loc = ""
    results = []

    for item in items:
        title = str(item.get("title", "")).strip()
        company = str(item.get("company_name", "")).strip()
        job_location = str(item.get("location", "")).strip()
        description = str(item.get("description", "")).strip()
        tags = ", ".join(item.get("tags", [])[:5]) if isinstance(item.get("tags"), list) else ""
        remote = bool(item.get("remote", False))
        url_apply = item.get("url") or item.get("job_url") or ""

        haystack = " ".join([title, company, job_location, description, tags]).casefold()
        if q and q not in haystack:
            continue
        if loc and loc not in haystack and not remote:
            continue

        results.append({
            "source": "Arbeitnow",
            "title": title,
            "company": company,
            "location": job_location or ("Remote" if remote else "Germany"),
            "remote": remote,
            "url": url_apply,
            "summary": tags or (description[:220] + "..." if description else "")
        })
        if len(results) >= limit:
            break

    return results

@st.cache_data(show_spinner=False, ttl=900)
def fetch_arbeitsagentur_jobs(query: str, location: str = "", limit: int = 15) -> List[Dict]:
    client_id = (os.getenv("BA_JOBS_API_KEY") or get_streamlit_secret("BA_JOBS_API_KEY") or "c003a37f-024f-462a-b36d-b001be4cd24a")
    normalized_location = "" if str(location or "").lower().startswith("anywhere in ") else (location or "")
    params = {
        "was": query or "",
        "wo": normalized_location,
        "size": str(limit),
    }
    url = "https://jobsuche.api.bund.dev/pc/v4/app/jobs?" + urllib.parse.urlencode(params)

    try:
        payload = http_get_json(url, headers={"X-API-Key": client_id, "User-Agent": "Mozilla/5.0"}, timeout=12)
    except Exception:
        return []

    raw_items = []
    if isinstance(payload, dict):
        for key in ["stellenangebote", "jobOffers", "jobs", "data"]:
            value = payload.get(key)
            if isinstance(value, list):
                raw_items = value
                break

    results = []
    for item in raw_items:
        title = str(item.get("beruf") or item.get("titel") or item.get("title") or "").strip()
        employer = item.get("arbeitgeber") or item.get("company") or {}
        if isinstance(employer, dict):
            company = str(employer.get("name") or employer.get("firma") or "").strip()
        else:
            company = str(employer or "").strip()

        location_value = item.get("arbeitsort") or item.get("arbeitsorte") or item.get("location") or {}
        if isinstance(location_value, list) and location_value:
            first_loc = location_value[0]
            if isinstance(first_loc, dict):
                place = ", ".join([str(first_loc.get("ort") or "").strip(), str(first_loc.get("region") or "").strip()]).strip(", ")
            else:
                place = str(first_loc)
        elif isinstance(location_value, dict):
            place = ", ".join([str(location_value.get("ort") or "").strip(), str(location_value.get("region") or "").strip()]).strip(", ")
        else:
            place = str(location_value or "").strip()

        refnr = str(item.get("refnr") or item.get("referenznummer") or "").strip()
        detail_url = f"https://www.arbeitsagentur.de/jobsuche/jobdetail/{urllib.parse.quote(refnr)}" if refnr else "https://www.arbeitsagentur.de/jobsuche/"
        summary = str(item.get("eintrittsdatum") or item.get("aktuelleVeroeffentlichungsdatum") or item.get("modifikationsTimestamp") or "").strip()

        if title:
            results.append({
                "source": "Bundesagentur für Arbeit",
                "title": title,
                "company": company or "Employer not shown",
                "location": place or (location or "Germany"),
                "remote": False,
                "url": detail_url,
                "summary": summary
            })
        if len(results) >= limit:
            break

    return results

def get_status_job_modifiers(user_status: str, country_name: str = "") -> List[str]:
    status = (user_status or "").lower()
    if is_student_thesis_status(user_status):
        return get_student_job_keywords(country_name)
    if any(x in status for x in ["fresh", "graduate", "absolvent", "entry level"]):
        return ["junior", "entry level", "trainee", "graduate", "internship", "no experience"]
    if any(x in status for x in ["career changer", "quereinsteiger", "changer"]):
        return ["junior", "career changer", "entry level", "trainee", "quereinsteiger"]
    if any(x in status for x in ["apply online", "remote", "online"]):
        return ["remote", "online", "work from home", "hybrid", "junior", "entry level"]
    if any(x in status for x in ["returning", "break", "pause"]):
        return ["returnship", "part time", "junior", "entry level", "back to work"]
    if any(x in status for x in ["experienced", "senior"]):
        return ["experienced", "specialist", "senior"]
    return ["junior", "entry level", "specialist"]

def build_live_job_queries(roles: List[str], user_status: str, max_queries: int = 18, country_name: str = "") -> List[str]:
    base_roles = [r.strip() for r in roles if r and r.strip()]
    if not base_roles:
        base_roles = ["Data Analyst", "IT Support", "Customer Support", "Business Analyst"]
    modifiers = get_status_job_modifiers(user_status, country_name)
    queries: List[str] = []
    for role in base_roles[:6]:
        if role not in queries:
            queries.append(role)
        for modifier in modifiers[:5]:
            candidate = f"{modifier} {role}"
            if candidate not in queries:
                queries.append(candidate)
        for modifier in ["remote", "online", "hybrid"]:
            candidate = f"{role} {modifier}"
            if candidate not in queries:
                queries.append(candidate)
        if len(queries) >= max_queries:
            break
    return queries[:max_queries]

def score_job_for_user(job: Dict, user_status: str, roles: List[str], country_name: str = "") -> int:
    text = " ".join([str(job.get(k, "")) for k in ["title", "summary", "company", "location", "source"]]).lower()
    score = 0
    for role in roles:
        role_words = [w for w in re.findall(r"[a-zA-Z]+", role.lower()) if len(w) > 2]
        score += sum(6 for w in role_words if w in text)
    for mod in get_status_job_modifiers(user_status, country_name):
        if mod.lower() in text:
            score += 12
    status = (user_status or "").lower()
    if any(x in status for x in ["fresh", "graduate", "student", "career changer", "returning"]):
        if any(x in text for x in ["senior", "lead", "principal", "manager"]):
            score -= 20
        if any(x in text for x in ["junior", "entry", "trainee", "intern", "working student", "graduate"]):
            score += 20
    if job.get("remote"):
        score += 5
    return score

def sort_jobs_for_user(jobs: List[Dict], user_status: str, roles: List[str], country_name: str = "") -> List[Dict]:
    return sorted(jobs, key=lambda job: score_job_for_user(job, user_status, roles, country_name), reverse=True)

def fetch_live_jobs_for_germany(roles: List[str], location: str = "", user_status: str = "") -> List[Dict]:
    results: List[Dict] = []
    search_queries = build_live_job_queries(roles, user_status, max_queries=8, country_name="Germany")

    # German job boards often use German role keywords. Add broad local-language fallbacks
    # so live search does not return only 0-3 results for English role titles.
    german_fallback_queries = [
        "Junior", "Quereinsteiger", "Berufseinsteiger", "Trainee", "Praktikum",
        "Werkstudent", "Abschlussarbeit", "Bachelorarbeit", "Masterarbeit", "Thesis",
        "Datenanalyst", "Data Analyst", "Business Analyst", "IT Support",
        "IT Support Mitarbeiter", "Helpdesk", "Kundenservice", "Customer Support",
        "Sachbearbeiter", "Backoffice", "Service Desk"
    ]
    for q in german_fallback_queries:
        if q not in search_queries:
            search_queries.append(q)

    for query in search_queries[:12]:
        results.extend(fetch_arbeitsagentur_jobs(query, location, limit=10))
        results.extend(fetch_arbeitnow_jobs(query, location, limit=10))

    # If a city search is too narrow, broaden once to the whole country.
    if len(results) < 12 and location and location.lower() not in {"germany", "anywhere in germany"}:
        for query in search_queries[:18]:
            results.extend(fetch_arbeitsagentur_jobs(query, "", limit=25))
            results.extend(fetch_arbeitnow_jobs(query, "", limit=25))

    deduped = []
    seen = set()
    for item in results:
        key = (item.get("source", "") + "|" + item.get("title", "") + "|" + item.get("company", "") + "|" + item.get("location", "")).casefold()
        if key not in seen:
            seen.add(key)
            deduped.append(item)
    return sort_jobs_for_user(deduped, user_status, roles, "Germany")[:35]


def render_live_jobs(jobs: List[Dict], country_name: str = "", max_visible: int = 30, roles: Optional[List[str]] = None, cv_text: str = ""):
    """Render live jobs without making users feel there are '0 jobs in a country'.

    Important UX change:
    - If strong profile matches are not found, show the best available broader live jobs instead of a hard zero.
    - If live APIs return nothing, clearly explain that live sources are limited and guide users to platform links.
    """
    roles = roles or []
    country_lower = (country_name or "").strip().lower()
    adzuna_ready = bool(os.getenv("ADZUNA_APP_ID") or get_streamlit_secret("ADZUNA_APP_ID")) and bool(os.getenv("ADZUNA_APP_KEY") or get_streamlit_secret("ADZUNA_APP_KEY"))

    original_jobs = list(jobs or [])
    filtered_jobs = [job for job in original_jobs if job_location_relevant(job, country_name)]

    # Do not throw away all jobs just because a source gives a weak/empty location.
    # This was the main reason users saw "0 jobs in Germany", which feels unbelievable.
    if country_name and filtered_jobs:
        jobs = filtered_jobs
    elif country_lower == "germany" and original_jobs:
        jobs = original_jobs
    else:
        jobs = filtered_jobs if country_name else original_jobs

    title = f"Live job openings in {country_name}" if country_name else "Live job openings"
    st.markdown(f"### {title}")
    st.caption("WorkZo ranks live results by profile fit. If strong matches are limited, broader jobs are shown so users can still continue the journey.")

    if not jobs:
        with st.container():
            st.markdown("""
<div class='card' style='border-color:rgba(96,165,250,0.32); background:rgba(37,99,235,0.14);'>
  <div class='section-title'>Live sources did not return jobs for this exact search</div>
  <div class='small-muted' style='color:#cbd5e1;'>This does not mean there are no jobs. It usually means the free live-source/API coverage is limited or the search is too narrow.</div>
  <ul style='margin-top:10px; color:#e2e8f0;'>
    <li><b>Broaden the role:</b> try IT Support, Data Analyst, Customer Support, Service Desk.</li>
    <li><b>Broaden the location:</b> search the whole country first.</li>
    <li><b>Next step:</b> open platform links below, copy one job description, then use Understand Job.</li>
  </ul>
</div>
""", unsafe_allow_html=True)
        if not adzuna_ready and country_lower != "germany":
            st.caption("Tip for founder: add ADZUNA_APP_ID and ADZUNA_APP_KEY in Streamlit secrets to improve global live-job coverage.")
        return

    ranked_jobs = []
    for job in jobs:
        score, reasons = estimate_job_match_score(job, roles, cv_text)
        job = dict(job)
        job["_match_score"] = score
        job["_match_reasons"] = reasons
        ranked_jobs.append(job)

    ranked_jobs.sort(key=lambda x: x.get("_match_score", 0), reverse=True)

    strong_jobs = [job for job in ranked_jobs if job.get("_match_score", 0) >= 70]
    possible_jobs = [job for job in ranked_jobs if 45 <= job.get("_match_score", 0) < 70]
    weak_jobs = [job for job in ranked_jobs if job.get("_match_score", 0) < 45]

    visible_jobs = (strong_jobs + possible_jobs)[:max_visible]
    showing_broader_results = False
    if not visible_jobs and ranked_jobs:
        # Instead of showing "0", show the best available lower-fit jobs with a clear warning.
        visible_jobs = ranked_jobs[:min(max_visible, 8)]
        showing_broader_results = True

    if showing_broader_results:
        st.warning("No strong profile matches were found, so WorkZo is showing broader live results. Use them as search leads, then paste a job description into Understand Job.")
    else:
        st.caption(f"Showing {len(visible_jobs)} relevant/broader openings. Hidden weak matches: {len(weak_jobs)}.")

    def render_clickable_job_card(job: Dict, compact: bool = False):
        summary = (job.get("summary", "") or "—")
        limit = 130 if compact else 190
        if len(summary) > limit:
            summary = summary[:limit].rsplit(" ", 1)[0] + "..."
        url = job.get("url") or "#"
        title_html = html.escape(str(job.get("title", "Role")))
        company_html = html.escape(str(job.get("company", "Employer not shown")))
        location = str(job.get("location", "") or "Location not shown")
        source = str(job.get("source", "") or "Job source")
        meta_html = html.escape(f"{location} • {source}")
        summary_html = html.escape(summary)
        match_score = int(job.get("_match_score", 0) or 0)
        reasons = job.get("_match_reasons", []) or []
        reason_html = "".join([f"<span class='pill'>✓ {html.escape(str(r))}</span>" for r in reasons[:3]])
        badge_label = f"{match_score}% fit" if match_score >= 45 else f"{match_score}% broad"
        job_html = f"""
<a href="{html.escape(url, quote=True)}" target="_blank" style="text-decoration:none; color:inherit;">
  <div class="card" style="cursor:pointer; transition:0.15s; border-color:rgba(96,165,250,0.32);">
    <div style="display:flex; justify-content:space-between; gap:12px; align-items:flex-start;">
      <div>
        <div class="section-title">{title_html}</div>
        <div><strong>{company_html}</strong></div>
        <div class="small-muted">{meta_html}</div>
      </div>
      <div class="beta-badge">{badge_label}</div>
    </div>
    <div style="margin-top:8px; color:#cbd5e1;">{summary_html}</div>
    <div style="margin-top:10px;">{reason_html}</div>
    <div style="margin-top:10px; font-size:0.9rem; color:#93c5fd;">↗ Open job</div>
  </div>
</a>
"""
        st.markdown(job_html, unsafe_allow_html=True)

    top_jobs = visible_jobs[:5]
    remaining_jobs = visible_jobs[5:]
    for job in top_jobs:
        render_clickable_job_card(job)

    if remaining_jobs:
        with st.expander(f"Show {len(remaining_jobs)} more live results", expanded=False):
            for job in remaining_jobs:
                render_clickable_job_card(job, compact=True)

def country_to_indeed_domain(country_name: str) -> str:
    country = (country_name or "").strip().lower()
    domain_map = {
        "germany": "de.indeed.com", "netherlands": "nl.indeed.com", "the netherlands": "nl.indeed.com",
        "united kingdom": "uk.indeed.com", "uk": "uk.indeed.com", "ireland": "ie.indeed.com",
        "united states": "www.indeed.com", "usa": "www.indeed.com", "canada": "ca.indeed.com",
        "india": "in.indeed.com", "australia": "au.indeed.com", "new zealand": "nz.indeed.com",
        "france": "fr.indeed.com", "spain": "es.indeed.com", "italy": "it.indeed.com",
        "austria": "at.indeed.com", "switzerland": "ch.indeed.com", "belgium": "be.indeed.com",
        "sweden": "se.indeed.com", "denmark": "dk.indeed.com", "norway": "no.indeed.com",
        "finland": "fi.indeed.com", "poland": "pl.indeed.com", "singapore": "sg.indeed.com",
        "south africa": "za.indeed.com", "brazil": "br.indeed.com", "mexico": "mx.indeed.com",
        "japan": "jp.indeed.com", "united arab emirates": "ae.indeed.com"
    }
    return domain_map.get(country, "www.indeed.com")


def get_country_linkedin_geo(country_name: str) -> str:
    # LinkedIn works globally without geoId; country name in location is enough for broad matching.
    return urllib.parse.quote(country_name or "")


@st.cache_data(show_spinner=False, ttl=1800)
def fetch_remotive_jobs(query: str, location: str = "", limit: int = 20) -> List[Dict]:
    """Free remote-job API fallback. Useful for global/online job seekers."""
    q = (query or "").strip()
    if not q:
        return []
    url = "https://remotive.com/api/remote-jobs?" + urllib.parse.urlencode({"search": q, "limit": str(limit)})
    try:
        payload = http_get_json(url, timeout=12)
    except Exception:
        return []
    items = payload.get("jobs", []) if isinstance(payload, dict) else []
    results: List[Dict] = []
    for item in items[:limit]:
        title = str(item.get("title", "")).strip()
        company = str(item.get("company_name", "")).strip()
        url_apply = str(item.get("url", "")).strip()
        category = str(item.get("category", "")).strip()
        candidate_required_location = str(item.get("candidate_required_location", "Remote")).strip()
        description = re.sub(r"<[^>]+>", " ", str(item.get("description", "")))
        description = re.sub(r"\s+", " ", description).strip()
        if title:
            results.append({
                "source": "Remotive",
                "title": title,
                "company": company or "Employer not shown",
                "location": candidate_required_location or "Remote / Worldwide",
                "remote": True,
                "url": url_apply,
                "summary": category or (description[:220] + "..." if description else "Remote role")
            })
    return results


def get_global_job_search_query(role: str, country_name: str, location: str, user_status: str = "") -> str:
    role = (role or "jobs").strip()
    loc = (location or country_name or "").strip()
    status = (user_status or "").lower()
    modifiers = []
    if is_student_thesis_status(user_status):
        modifiers.extend(get_student_job_keywords(country_name)[:3])
    elif any(x in status for x in ["fresh", "graduate"]):
        modifiers.extend(["entry level", "junior", "graduate"])
    elif any(x in status for x in ["career changer", "quereinsteiger"]):
        modifiers.extend(["career changer", "junior"])
    elif any(x in status for x in ["online", "remote"]):
        modifiers.extend(["remote", "online"])
    elif any(x in status for x in ["experienced", "senior"]):
        modifiers.extend(["experienced"])
    prefix = " ".join(modifiers[:2])
    return " ".join([prefix, role, "jobs", loc]).strip()

def get_job_board_links(country_name: str, location: str, role: str = "", user_status: str = "") -> List[Tuple[str, str]]:

    country_name = (country_name or "").strip()
    location = (location or country_name or "").strip()
    role = (role or "jobs").strip()
    country = country_name.lower()
    q_text = get_global_job_search_query(role, country_name, location, user_status)
    q = urllib.parse.quote(q_text)
    loc_q = urllib.parse.quote(location or country_name)
    role_q = urllib.parse.quote(role)
    indeed_domain = country_to_indeed_domain(country_name)

    boards: List[Tuple[str, str]] = [
        ("LinkedIn Jobs", f"https://www.linkedin.com/jobs/search/?keywords={q}&location={loc_q}"),
        ("Indeed", f"https://{indeed_domain}/jobs?q={q}&l={loc_q}"),
        ("Google Jobs", f"https://www.google.com/search?q={q}"),
    ]

    if country == "germany":
        boards.extend([
            ("StepStone Germany", f"https://www.stepstone.de/jobs/{role_q}/in-{loc_q}"),
            ("XING Jobs", f"https://www.xing.com/jobs/search?keywords={role_q}&location={loc_q}"),
            ("Bundesagentur für Arbeit", f"https://www.arbeitsagentur.de/jobsuche/suche?was={role_q}&wo={loc_q}"),
        ])
    elif country in {"netherlands", "the netherlands"}:
        boards.extend([
            ("National Vacaturebank", f"https://www.nationalevacaturebank.nl/vacatures/zoekterm/{role_q}"),
            ("Werk.nl", f"https://www.werk.nl/werkzoekenden/vacatures/?q={role_q}"),
            ("Iamexpat Jobs", f"https://www.iamexpat.nl/career/jobs-netherlands?search={role_q}"),
        ])
    elif country in {"united kingdom", "uk"}:
        boards.extend([
            ("Reed", f"https://www.reed.co.uk/jobs/{role_q}-jobs-in-{loc_q}"),
            ("Totaljobs", f"https://www.totaljobs.com/jobs/{role_q}/in-{loc_q}"),
            ("CV-Library", f"https://www.cv-library.co.uk/{role_q}-jobs-in-{loc_q}"),
        ])
    elif country in {"united states", "usa"}:
        boards.extend([
            ("USAJobs", f"https://www.usajobs.gov/Search/Results?k={role_q}&l={loc_q}"),
            ("Dice Tech Jobs", f"https://www.dice.com/jobs?q={role_q}&location={loc_q}"),
            ("ZipRecruiter", f"https://www.ziprecruiter.com/jobs-search?search={role_q}&location={loc_q}"),
        ])
    elif country == "india":
        boards.extend([
            ("Naukri", f"https://www.naukri.com/{role_q}-jobs-in-{loc_q}"),
            ("Foundit", f"https://www.foundit.in/search/{role_q}-jobs-in-{loc_q}"),
            ("TimesJobs", f"https://www.timesjobs.com/candidate/job-search.html?searchType=personalizedSearch&txtKeywords={role_q}&txtLocation={loc_q}"),
        ])
    elif country == "canada":
        boards.extend([
            ("Job Bank Canada", f"https://www.jobbank.gc.ca/jobsearch/jobsearch?searchstring={role_q}&locationstring={loc_q}"),
            ("Workopolis", f"https://www.workopolis.com/jobsearch/{role_q}-jobs/{loc_q}"),
        ])
    elif country == "australia":
        boards.extend([
            ("Seek Australia", f"https://www.seek.com.au/{role_q}-jobs/in-{loc_q}"),
            ("Jora Australia", f"https://au.jora.com/{role_q}-jobs-in-{loc_q}"),
        ])
    else:
        boards.extend([
            ("Glassdoor", f"https://www.glassdoor.com/Job/jobs.htm?sc.keyword={role_q}&locT=N&locId=&locKeyword={loc_q}"),
            ("Remote OK", f"https://remoteok.com/remote-{role_q}-jobs"),
            ("Remotive", f"https://remotive.com/remote-jobs/search?search={role_q}"),
        ])

    # Always include remote/global sources because some users apply internationally.
    boards.extend([
        ("Remotive Remote Jobs", f"https://remotive.com/remote-jobs/search?search={role_q}"),
        ("Remote OK", f"https://remoteok.com/remote-{role_q}-jobs"),
    ])

    deduped = []
    seen = set()
    for label, url in boards:
        key = (label + url).lower()
        if key not in seen:
            seen.add(key)
            deduped.append((label, url))
    return deduped

def render_job_board_search_cards(country_name: str, location: str, roles: List[str], user_status: str = ""):
    st.markdown("### Continue searching on job platforms")
    st.caption("Open broader searches, then paste one promising job description into Understand Job to check your fit.")
    for role in roles[:3]:
        with st.expander(f"{role} — search links", expanded=False):
            links = get_job_board_links(country_name, location, role, user_status)[:5]
            compact_links = []
            for label, url in links:
                safe_label = html.escape(label)
                safe_url = html.escape(url, quote=True)
                compact_links.append(
                    f'<a class="compact-job-link" href="{safe_url}" target="_blank" rel="noopener noreferrer">↗ {safe_label}</a>'
                )
            st.markdown(
                "<div class='compact-job-link-grid'>" + "".join(compact_links) + "</div>",
                unsafe_allow_html=True
            )


def job_location_relevant(job: Dict, country_name: str) -> bool:
    """Return True when a live job result is relevant for the selected country."""
    country = (country_name or "").strip().lower()
    if not country:
        return True

    loc = str(job.get("location", "") or "").lower()
    source = str(job.get("source", "") or "").lower()
    title = str(job.get("title", "") or "").lower()
    summary = str(job.get("summary", "") or "").lower()
    text = f"{title} {summary} {loc} {source}"

    # Germany-specific sources sometimes return empty/short location fields.
    # Trust local German sources unless the text clearly points to another country.
    if country == "germany" and ("arbeitsagentur" in source or "arbeitnow" in source):
        other_markers = ["united states", "usa", "india", "canada", "united kingdom", "uk", "australia", "france", "spain", "portugal", "netherlands"]
        if not any(marker in text for marker in other_markers):
            return True

    aliases = {
        "germany": ["germany", "deutschland", "berlin", "munich", "münchen", "hamburg", "frankfurt", "cologne", "köln", "stuttgart", "düsseldorf", "remote in germany"],
        "united states": ["united states", "usa", "u.s.", "remote in us", "remote in usa"],
        "usa": ["united states", "usa", "u.s.", "remote in us", "remote in usa"],
        "united kingdom": ["united kingdom", "uk", "england", "london", "remote in uk"],
        "uk": ["united kingdom", "uk", "england", "london", "remote in uk"],
        "india": ["india", "bangalore", "bengaluru", "chennai", "mumbai", "pune", "hyderabad", "delhi"],
        "canada": ["canada", "toronto", "vancouver", "montreal", "remote in canada"],
        "france": ["france", "paris", "remote in france"],
        "netherlands": ["netherlands", "amsterdam", "rotterdam", "remote in netherlands"],
        "the netherlands": ["netherlands", "amsterdam", "rotterdam", "remote in netherlands"],
        "australia": ["australia", "sydney", "melbourne", "remote in australia"],
        "portugal": ["portugal", "lisbon", "porto", "remote in portugal"],
        "spain": ["spain", "madrid", "barcelona", "remote in spain"],
        "italy": ["italy", "milan", "rome", "remote in italy"],
    }

    country_terms = aliases.get(country, [country])
    if any(term in text for term in country_terms):
        return True

    global_remote_terms = ["remote worldwide", "worldwide", "global remote", "remote - worldwide", "europe remote", "remote europe", "emea remote"]
    if any(term in text for term in global_remote_terms):
        return True

    other_country_markers = ["usa", "united states", "india", "canada", "united kingdom", "uk", "australia", "france", "spain", "portugal", "netherlands"]
    if "remote" in text and not any(term in text for term in country_terms):
        if any(marker in text for marker in other_country_markers if marker not in country_terms):
            return False

    return False


def estimate_job_match_score(job: Dict, roles: List[str], cv_text: str = "") -> Tuple[int, List[str]]:
    """Stricter profile-aware job matching.

    The score compares five areas instead of simple keyword counting:
    1) job-title fit, 2) skills/tools fit, 3) experience level,
    4) language requirements, and 5) location/work-mode fit.
    Jobs below 50% are hidden in render_live_jobs.
    """
    job_text = " ".join(str(job.get(k, "")) for k in ["title", "company", "summary", "category", "location", "source"]).lower()
    title_text = str(job.get("title", "") or "").lower()
    location_text = str(job.get("location", "") or "").lower()
    cv_lower = (cv_text or "").lower()
    reasons: List[str] = []

    def contains_any(text: str, terms: List[str]) -> bool:
        return any(term in text for term in terms)

    def token_set(text: str) -> set:
        stop = {"and", "the", "for", "with", "from", "your", "you", "are", "job", "role", "specialist", "engineer", "manager"}
        return {w for w in re.findall(r"[a-zA-Z][a-zA-Z+#.]{1,}", text.lower()) if w not in stop and len(w) > 2}

    # -------------------------
    # 1) Language requirement gate
    # -------------------------
    language_terms = {
        "Japanese": ["japanese", "japanisch"],
        "Spanish": ["spanish", "spanisch"],
        "French": ["french", "französisch", "franzoesisch"],
        "Portuguese": ["portuguese", "portugiesisch"],
        "Dutch": ["dutch", "niederländisch", "niederlaendisch"],
        "German": ["german", "deutsch"],
        "English": ["english", "englisch"],
        "Italian": ["italian", "italienisch"],
        "Arabic": ["arabic", "arabisch"],
        "Hindi": ["hindi"],
        "Chinese": ["chinese", "mandarin", "chinesisch"],
    }
    missing_languages: List[str] = []
    matched_languages: List[str] = []
    for lang, terms in language_terms.items():
        hard_required = any(
            f"{t} speaking" in job_text or f"{t}-speaking" in job_text or
            f"fluent {t}" in job_text or f"native {t}" in job_text or
            f"{t} speaker" in job_text or f"language: {t}" in job_text or
            f"{t} required" in job_text or f"{t} mandatory" in job_text
            for t in terms
        )
        if hard_required:
            if any(t in cv_lower for t in terms):
                matched_languages.append(lang)
            else:
                missing_languages.append(lang)

    # -------------------------
    # 2) Job-title fit, with role families
    # -------------------------
    role_families = {
        "technical_support": ["technical support", "it support", "support engineer", "service desk", "helpdesk", "help desk", "application support", "support specialist", "customer support engineer"],
        "data": ["data analyst", "business intelligence", "bi analyst", "reporting analyst", "analytics", "tableau", "power bi", "sql analyst"],
        "customer_success": ["customer success", "customer support", "client support", "customer care", "account support", "implementation specialist"],
        "software": ["software engineer", "developer", "frontend", "backend", "full stack", "java developer", "python developer"],
        "sales_marketing": ["sales", "marketing", "seo", "content", "business development"],
    }

    cv_family_scores = {family: 0 for family in role_families}
    job_family_scores = {family: 0 for family in role_families}
    for family, terms in role_families.items():
        cv_family_scores[family] = sum(1 for t in terms if t in cv_lower)
        job_family_scores[family] = sum(1 for t in terms if t in job_text)

    selected_role_text = " ".join(roles or []).lower()
    selected_tokens = token_set(selected_role_text)
    title_tokens = token_set(title_text)
    title_overlap = len(selected_tokens & title_tokens) / max(1, len(selected_tokens)) if selected_tokens else 0

    title_score = 0
    if selected_role_text and any(role.lower().strip() and role.lower().strip() in title_text for role in roles[:6]):
        title_score = 30
        reasons.append("Strong job-title fit")
    elif title_overlap >= 0.65:
        title_score = 24
        reasons.append("Relevant job title")
    else:
        shared_family = [f for f in role_families if cv_family_scores[f] and job_family_scores[f]]
        if shared_family:
            title_score = 18
            family_label = shared_family[0].replace("_", " ").title()
            reasons.append(f"Same role family: {family_label}")
        elif title_overlap >= 0.35:
            title_score = 12
            reasons.append("Partial title fit")

    # -------------------------
    # 3) Skills and tools fit
    # -------------------------
    skill_terms = [
        "python", "sql", "excel", "tableau", "power bi", "pandas", "matplotlib", "seaborn", "gcp", "aws", "api", "rest api",
        "data analysis", "data visualization", "machine learning", "generative ai", "a/b testing", "dashboard", "reporting",
        "technical support", "it support", "customer support", "service desk", "helpdesk", "troubleshooting", "ticket", "tickets",
        "itsm", "itil", "manageengine", "servicedesk plus", "zoho", "crm", "saas", "windows", "linux", "network", "hardware", "software",
        "communication", "documentation", "knowledge base", "customer-facing", "stakeholder", "problem solving"
    ]
    cv_skills = {s for s in skill_terms if s in cv_lower}
    job_skills = {s for s in skill_terms if s in job_text}
    matched_skills = sorted(cv_skills & job_skills)
    skill_score = min(28, len(matched_skills) * 5)
    if matched_skills:
        reasons.append("Skills fit: " + ", ".join([s.title() for s in matched_skills[:3]]))

    # Boost transferable support/data combinations, but do not over-score unrelated titles.
    if any(t in cv_lower for t in ["technical support", "it support", "customer support", "servicedesk", "service desk"]) and any(t in job_text for t in ["technical support", "it support", "customer support", "service desk", "helpdesk"]):
        skill_score += 8
        if "Support background" not in reasons:
            reasons.append("Support background fits")
    if any(t in cv_lower for t in ["python", "sql", "tableau", "data analysis"]) and any(t in job_text for t in ["data analyst", "sql", "tableau", "power bi", "reporting", "analytics"]):
        skill_score += 6
        reasons.append("Data tools fit")
    skill_score = min(32, skill_score)

    # -------------------------
    # 4) Experience/seniority fit
    # -------------------------
    seniority_score = 12
    senior_terms = ["senior", "lead", "principal", "head of", "director", "team lead", "manager"]
    entry_terms = ["junior", "entry", "trainee", "graduate", "associate", "fresher", "1st level", "first level", "level 1"]
    mid_terms = ["specialist", "engineer", "analyst", "consultant", "2nd level", "second level"]

    if contains_any(job_text, senior_terms):
        seniority_score = 2
        reasons.append("Seniority may be too high")
    elif contains_any(job_text, entry_terms):
        seniority_score = 16
        reasons.append("Realistic seniority")
    elif contains_any(job_text, mid_terms):
        seniority_score = 13
        reasons.append("Mid-level fit possible")

    # -------------------------
    # 5) Location/work-mode fit
    # -------------------------
    location_score = 8
    if contains_any(job_text, ["remote", "hybrid", "home office", "work from home"]):
        location_score = 10
        reasons.append("Flexible work option")
    elif location_text:
        location_score = 7

    # Language fit score. Missing hard-required languages are a strong penalty and score cap.
    language_score = 8
    if matched_languages:
        language_score = 10
        reasons.append("Language fit: " + ", ".join(matched_languages[:2]))
    if missing_languages:
        language_score = 0
        reasons.append("Missing required language: " + ", ".join(missing_languages[:2]))

    raw_score = title_score + skill_score + seniority_score + location_score + language_score

    # Penalize if title and skills both look weak.
    if title_score < 12 and skill_score < 10:
        raw_score -= 18
        reasons.append("Weak profile fit")
    elif title_score < 12:
        raw_score -= 8

    # Hard cap for missing required languages such as Japanese-speaking roles.
    if missing_languages:
        raw_score = min(raw_score, 34 if title_score < 20 else 46)

    # Do not let generic remote/customer jobs look like strong matches without real skill/title fit.
    if title_score < 18 and skill_score < 16:
        raw_score = min(raw_score, 49)

    score = max(5, min(96, int(raw_score)))
    if not reasons:
        reasons.append("Review requirements before applying")
    return score, reasons[:4]


def build_role_suggestions(user_titles: List[str], detected_roles_text: str, current_role: str) -> List[str]:
    roles: List[str] = []
    for role in user_titles:
        role = role.strip()
        if role and role not in roles:
            roles.append(role)

    if detected_roles_text:
        for line in detected_roles_text.splitlines():
            candidate = line.replace("-", "").strip()
            if candidate and candidate not in roles:
                roles.append(candidate)

    if current_role and current_role.strip() and current_role.strip() not in roles:
        roles.append(current_role.strip())

    fallback = [
        "Data Analyst",
        "Business Analyst",
        "Reporting Analyst",
        "Operations Analyst",
        "IT Support Specialist",
    ]
    for role in fallback:
        if len(roles) >= 5:
            break
        if role not in roles:
            roles.append(role)

    return roles[:5]

def get_country_market_hint(country_name: str) -> str:
    country = (country_name or "").strip().lower()
    if country == "germany":
        return "German language helps strongly for many local roles, but English-speaking jobs exist in tech, startups, analytics, product, and international companies."
    if country in {"netherlands", "the netherlands"}:
        return "English-speaking roles are more common than in many EU markets, especially in tech, operations, and international business functions."
    if country in {"austria", "switzerland"}:
        return "Local language is often important, especially for customer-facing and traditional companies."
    if country in {"canada", "united states", "united kingdom", "ireland", "australia", "new zealand"}:
        return "English-first roles are common, but local resume style and market positioning still matter."
    return "Target roles with transferable skills first, then adapt your CV and search keywords to local market expectations."


ADZUNA_COUNTRY_CODES = {
    "australia": "au",
    "austria": "at",
    "belgium": "be",
    "brazil": "br",
    "canada": "ca",
    "france": "fr",
    "germany": "de",
    "india": "in",
    "italy": "it",
    "mexico": "mx",
    "netherlands": "nl",
    "the netherlands": "nl",
    "new zealand": "nz",
    "poland": "pl",
    "singapore": "sg",
    "south africa": "za",
    "spain": "es",
    "switzerland": "ch",
    "united kingdom": "gb",
    "uk": "gb",
    "united states": "us",
    "usa": "us",
}

@st.cache_data(show_spinner=False, ttl=900)
def fetch_adzuna_jobs(query: str, country_name: str, location: str = "", limit: int = 24) -> List[Dict]:
    country_code = ADZUNA_COUNTRY_CODES.get((country_name or "").strip().lower())
    app_id = os.getenv("ADZUNA_APP_ID") or get_streamlit_secret("ADZUNA_APP_ID")
    app_key = os.getenv("ADZUNA_APP_KEY") or get_streamlit_secret("ADZUNA_APP_KEY")

    if not country_code or not app_id or not app_key:
        return []

    results: List[Dict] = []
    seen = set()

    for page_no in range(1, 6):
        params = {
            "app_id": app_id,
            "app_key": app_key,
            "results_per_page": "12",
            "what_phrase": query or "",
            "where": location or "",
            "sort_by": "date",
            "content-type": "application/json",
            "max_days_old": "30",
        }

        url = f"https://api.adzuna.com/v1/api/jobs/{country_code}/search/{page_no}?" + urllib.parse.urlencode(params)

        try:
            payload = http_get_json(url, timeout=12)
        except Exception:
            continue

        items = payload.get("results", []) if isinstance(payload, dict) else []
        if not items:
            continue

        for item in items:
            title = str(item.get("title", "")).strip()
            company_obj = item.get("company") or {}
            company = str(company_obj.get("display_name") if isinstance(company_obj, dict) else company_obj or "").strip()

            location_obj = item.get("location") or {}
            if isinstance(location_obj, dict):
                display_loc = str(location_obj.get("display_name") or "").strip()
            else:
                display_loc = str(location_obj or "").strip()

            redirect_url = str(item.get("redirect_url", "")).strip()
            description = str(item.get("description", "")).strip()
            contract = str(item.get("contract_type", "")).strip()
            salary_min = item.get("salary_min")
            salary_max = item.get("salary_max")
            salary_text = ""
            if salary_min or salary_max:
                salary_text = f"Salary: {salary_min or '—'} to {salary_max or '—'}"

            summary_parts = [x for x in [contract, salary_text, (description[:200] + "...") if description else ""] if x]
            summary = " • ".join(summary_parts)

            key = (title + "|" + company + "|" + display_loc).casefold()
            if title and key not in seen:
                seen.add(key)
                results.append({
                    "source": "Adzuna",
                    "title": title,
                    "company": company or "Employer not shown",
                    "location": display_loc or (location or country_name),
                    "remote": False,
                    "url": redirect_url,
                    "summary": summary
                })
            if len(results) >= limit:
                return results[:limit]

    return results[:limit]

def fetch_live_jobs_global(country_name: str, roles: List[str], location: str = "", user_status: str = "") -> List[Dict]:
    results: List[Dict] = []
    country_lower = (country_name or "").strip().lower()
    search_queries = build_live_job_queries(roles, user_status, max_queries=10, country_name=country_name)

    # Germany has two additional free sources.
    if country_lower == "germany":
        results.extend(fetch_live_jobs_for_germany(roles, location, user_status))

    # Adzuna supports many countries when API keys are configured.
    for query in search_queries:
        results.extend(fetch_adzuna_jobs(query, country_name, location, limit=30))

    # Free global remote source. This keeps worldwide job search useful even without Adzuna keys.
    for query in search_queries[:10]:
        results.extend(fetch_remotive_jobs(query, location, limit=20))

    # Broaden location if exact city/country query produces too few results.
    if len(results) < 15 and location and location.strip().lower() != (country_name or "").strip().lower():
        for query in search_queries[:12]:
            results.extend(fetch_adzuna_jobs(query, country_name, "", limit=30))
            results.extend(fetch_remotive_jobs(query, "", limit=20))

    deduped: List[Dict] = []
    seen = set()
    for item in results:
        key = (item.get("source", "") + "|" + item.get("title", "") + "|" + item.get("company", "") + "|" + item.get("location", "") + "|" + item.get("url", "")).casefold()
        if key not in seen:
            seen.add(key)
            deduped.append(item)

    return sort_jobs_for_user(deduped, user_status, roles, country_name)[:40]


def fallback_job_search_plan(country_name: str, location: str, roles: List[str], cv_text: str) -> Dict:
    best_titles = []
    for role in roles[:5]:
        best_titles.append({
            "title": role,
            "fit_reason": "This matches the transferable skills and positioning suggested by your resume.",
            "seniority": "Junior to Mid-level",
            "english_realistic": "Depends on country and company type"
        })

    search_terms = []
    for role in roles[:4]:
        search_terms.extend([
            f"{role} jobs in {location}",
            f"{role} {country_name} English speaking",
            f"{role} remote {country_name}",
        ])

    return {
        "best_match_titles": best_titles,
        "search_terms": search_terms[:12],
        "market_strategy": [
            get_country_market_hint(country_name),
            f"Start with roles closest to your current profile and apply broadly in {location or country_name}.",
            "Prioritize companies with international teams, clear English-language postings, and realistic entry requirements."
        ],
        "best_live_matches": [],
        "priority_plan": [
            "Apply first to the 10 closest-fit roles.",
            "Use 2 to 3 tailored CV versions for your top role clusters.",
            "Track applications and improve search keywords every 3 to 4 days."
        ],
        "resume_positioning": [
            "Keep your headline aligned to the target role.",
            "Highlight measurable achievements and relevant tools.",
            "Move the most market-relevant skills higher in the CV."
        ],
        "fastest_route": [
            "Apply to 10 to 15 realistic roles this week.",
            "Tailor your CV headline and summary for each role cluster.",
            "Use LinkedIn, Indeed, and the strongest local job board for your country.",
            "Message 3 recruiters or hiring managers where possible.",
            "Practice short interview answers through Work-O-Bot."
        ]
    }

def generate_job_search_plan(country_name: str, location: str, roles: List[str], cv_text: str, live_jobs: List[Dict]) -> Dict:
    prompt = f"""
Return ONLY valid JSON. Do not use markdown.

JSON format:
{{
  "best_match_titles": [
    {{
      "title": "string",
      "fit_reason": "string",
      "seniority": "string",
      "english_realistic": "string"
    }}
  ],
  "search_terms": ["string"],
  "market_strategy": ["string"],
  "best_live_matches": ["string"],
  "priority_plan": ["string"],
  "resume_positioning": ["string"],
  "fastest_route": ["string"]
}}

Country: {country_name}
Preferred location: {location}
Target roles: {roles}

Candidate CV:
{cv_text}

Live jobs:
{live_jobs[:8]}

Rules:
- Be realistic about seniority. Do not suggest mid-senior if the CV does not support it.
- Prefer entry-level or junior recommendations when direct experience is limited.
- Fill every array with useful content.
- best_match_titles must contain exactly 3 items.
- search_terms must contain 4 to 6 items and avoid repetitive variations.
- market_strategy must contain 3 short bullets.
- priority_plan must contain 3 short bullets.
- resume_positioning must contain 3 short bullets.
- fastest_route must contain 3 short bullets.
"""
    result = run_ai_prompt(prompt, force_language=st.session_state.get("preferred_language", "English"), json_mode=True)
    if result.startswith("ERROR:"):
        return fallback_job_search_plan(country_name, location, roles, cv_text)

    try:
        parsed = safe_json_loads(result)
        if not isinstance(parsed, dict) or not parsed.get("best_match_titles"):
            return fallback_job_search_plan(country_name, location, roles, cv_text)
        return parsed
    except Exception:
        return fallback_job_search_plan(country_name, location, roles, cv_text)

def render_job_plan(plan: Dict):
    st.markdown("### Roles That Fit Your Profile")
    titles = plan.get("best_match_titles", [])
    if isinstance(titles, list) and titles:
        st.markdown("""
<div class='next-action-card' style='margin-top:6px;'>
  <div class='next-action-label'>Recommended search direction</div>
  <div class='next-action-title'>Choose a role → open job boards → paste one job description → tailor your CV</div>
  <div class='next-action-copy'>WorkZo is strongest when you use it as a journey, not a one-time job list.</div>
</div>
""", unsafe_allow_html=True)
        cols = st.columns(min(3, len(titles[:3])))
        for i, item in enumerate(titles[:3]):
            with cols[i]:
                if isinstance(item, dict):
                    title = str(item.get("title", "Role"))
                    seniority = str(item.get("seniority", "—"))
                    english_realistic = str(item.get("english_realistic", "—"))
                    fit_reason = str(item.get("fit_reason", "—"))
                    keywords = item.get("keywords_to_use", []) or item.get("cv_keywords", []) or []
                    improve_next = item.get("improve_next", "") or item.get("gap", "") or "Add stronger role-specific keywords."
                    fit_score = item.get("fit_score", "") or item.get("score", "") or ""
                    if len(fit_reason) > 170:
                        fit_reason = fit_reason[:170].rsplit(" ", 1)[0] + "..."
                    keyword_text = ", ".join([str(x) for x in keywords[:4]]) if isinstance(keywords, list) else str(keywords)
                    score_html = f"<span class='beta-badge'>{html.escape(str(fit_score))}% role fit</span>" if str(fit_score).strip().isdigit() else ""
                    st.markdown(f"""
<div class='card' style='border-color:rgba(20,184,166,0.28); min-height:300px;'>
  <div class='section-title'>{i+1}. {html.escape(title)}</div>
  <div style='margin:8px 0;'>{score_html}</div>
  <div class='small-muted'>{html.escape(seniority)} • {html.escape(english_realistic)}</div>
  <div style='margin-top:12px;'><b>Why it fits:</b> {html.escape(fit_reason)}</div>
  <div style='margin-top:12px;'><b>Use in CV:</b> {html.escape(keyword_text or title)}</div>
  <div style='margin-top:12px;'><b>Improve next:</b> {html.escape(str(improve_next))}</div>
</div>
""", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='card'><div class='section-title'>{i+1}. {html.escape(str(item))}</div></div>", unsafe_allow_html=True)
    else:
        st.info(txt("no_roles_generated"))

    with st.expander("Search strategy", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"#### {txt('best_search_terms')}")
            for item in plan.get("search_terms", [])[:7]:
                st.markdown(f"- {html.escape(str(item))}")
        with col2:
            st.markdown(f"#### {txt('resume_positioning')}")
            for item in plan.get("resume_positioning", [])[:5]:
                st.markdown(f"- {html.escape(str(item))}")
        with col3:
            st.markdown(f"#### {txt('fastest_route')}")
            for item in plan.get("fastest_route", [])[:5]:
                st.markdown(f"- {html.escape(str(item))}")

    with st.expander("More market strategy", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"#### {txt('market_strategy')}")
            for item in plan.get("market_strategy", [])[:6]:
                st.markdown(f"- {html.escape(str(item))}")
            st.markdown(f"#### {txt('priority_plan')}")
            for item in plan.get("priority_plan", [])[:5]:
                st.markdown(f"- {html.escape(str(item))}")
        with col2:
            best_live = plan.get("best_live_matches", [])
            if best_live:
                st.markdown(f"#### {txt('best_live_matches')}")
                for item in best_live[:5]:
                    item_text = str(item)
                    url_match = re.search(r"https?://\S+", item_text)
                    if url_match:
                        url = url_match.group(0).rstrip(").,]")
                        label = item_text.replace(url_match.group(0), "").strip(" -–—") or "Open job"
                        st.markdown(
                            f"- **{html.escape(label)}** — "
                            f"<a class='workzo-link-button' href='{html.escape(url, quote=True)}' target='_blank'>Open job</a>",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(f"- {html.escape(item_text)}")
            else:
                st.caption("Open the platform search links below to find current postings, then paste one job description into Understand Job.")

def analyze_cv_text_features(cv_text: str) -> Dict:
    text = cv_text or ""
    lower = text.lower()
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    words = re.findall(r"\S+", text)
    word_count = len(words)

    heading_patterns = {
        "professional_summary_present": r"(professional summary|summary|profile|about me|objective)",
        "work_experience_present": r"(work experience|experience|employment history|professional experience)",
        "skills_present": r"(^|\n)(skills|technical skills|core skills|competencies)\b",
        "education_present": r"(education|academic background|qualifications)",
    }

    email_present = bool(re.search(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", text, re.I))
    phone_present = bool(re.search(r"(\+?\d[\d\s\-()]{7,}\d)", text))
    linkedin_present = "linkedin.com" in lower
    contact_info_present = email_present or phone_present

    bullet_lines = [l for l in lines if l.startswith(("•", "-", "*"))]
    bullet_points_count = len(bullet_lines)
    bullet_points_present = bullet_points_count >= 2

    date_ranges_present = bool(re.search(r"(19\d{2}|20\d{2}).{0,10}(19\d{2}|20\d{2}|present|current|heute|till date)", lower, re.I))
    years_mentions = re.findall(r"(\d{1,2})\+?\s+(years|year|yrs)", lower)
    years_count = len(years_mentions)

    quantified_patterns = [
        r"\d+%",
        r"€\s?\d+",
        r"\$\s?\d+",
        r"\b\d+[+,]?\s+(users|clients|projects|tickets|years|months|team members|stakeholders)\b",
        r"\b(increased|reduced|improved|managed|supported|led)\b.{0,20}\d+",
    ]
    quantified_hits = 0
    for p in quantified_patterns:
        quantified_hits += len(re.findall(p, lower, re.I))
    quantified_achievements_present = quantified_hits > 0

    short_lines = sum(1 for l in lines if len(l) < 80)
    long_lines = sum(1 for l in lines if len(l) > 140)
    section_heading_hits = sum(1 for pattern in heading_patterns.values() if re.search(pattern, lower, re.I | re.M))
    clear_formatting = len(lines) >= 8 and short_lines >= 5 and long_lines <= max(2, len(lines) // 8)
    plain_text_readable = len(lines) >= 5 and word_count > 60 and long_lines <= max(3, len(lines) // 6)
    standard_headings_present = section_heading_hits >= 2

    action_verbs = [
        "developed", "analyzed", "managed", "led", "created", "built", "improved",
        "supported", "optimized", "designed", "implemented", "coordinated",
        "resolved", "delivered", "maintained", "automated"
    ]
    action_verb_hits = sum(1 for verb in action_verbs if verb in lower)

    skills_line_count = 0
    for l in lines:
        if "," in l and len(l.split(",")) >= 3:
            skills_line_count += 1

    contact_score = 1.0 if contact_info_present else 0.0
    summary_score = 1.0 if re.search(heading_patterns["professional_summary_present"], lower, re.I) else 0.0
    experience_score = 1.0 if re.search(heading_patterns["work_experience_present"], lower, re.I) else 0.0
    skills_score = min(1.0, 0.35 + 0.2 * skills_line_count) if re.search(heading_patterns["skills_present"], lower, re.I | re.M) else 0.0
    education_score = 1.0 if re.search(heading_patterns["education_present"], lower, re.I) else 0.0
    quantified_score = min(1.0, quantified_hits / 4) if quantified_hits else 0.0
    bullet_score = min(1.0, bullet_points_count / 8) if bullet_points_count else 0.0
    date_score = min(1.0, max(1, years_count) / 4) if date_ranges_present or years_count else 0.0
    formatting_score = 1.0 if clear_formatting else (0.55 if plain_text_readable else 0.2)

    if word_count < 120:
        grammar_quality = "weak"
    elif word_count < 220:
        grammar_quality = "average"
    else:
        grammar_quality = "good"

    features = {
        "contact_info_present": contact_info_present,
        "professional_summary_present": bool(re.search(heading_patterns["professional_summary_present"], lower, re.I)),
        "work_experience_present": bool(re.search(heading_patterns["work_experience_present"], lower, re.I)),
        "skills_present": bool(re.search(heading_patterns["skills_present"], lower, re.I | re.M)),
        "education_present": bool(re.search(heading_patterns["education_present"], lower, re.I)),
        "quantified_achievements_present": quantified_achievements_present,
        "clear_formatting": clear_formatting,
        "grammar_quality": grammar_quality,
        "standard_headings_present": standard_headings_present,
        "plain_text_readable": plain_text_readable,
        "bullet_points_present": bullet_points_present,
        "date_ranges_present": date_ranges_present,
        "word_count": word_count,
        "long_lines": long_lines,
        "bullet_points_count": bullet_points_count,
        "quantified_hits": quantified_hits,
        "action_verb_hits": action_verb_hits,
        "linkedin_present": linkedin_present,
        "section_heading_hits": section_heading_hits,
        "contact_score": contact_score,
        "summary_score": summary_score,
        "experience_score": experience_score,
        "skills_score": skills_score,
        "education_score": education_score,
        "quantified_score": quantified_score,
        "bullet_score": bullet_score,
        "date_score": date_score,
        "formatting_score": formatting_score,
    }
    return features


# =========================================================
# CV CLEANING + STRUCTURING
# =========================================================
def join_spaced_caps(match):
    return match.group(0).replace(" ", "")

def clean_cv_text(raw_text: str) -> str:
    """
    Fix common PDF extraction problems before WorkZo shows or sends CV text to AI.
    Keeps contact details, headings, and profile text from being merged into one line.
    """
    if not raw_text:
        return ""

    text = raw_text.replace("\x00", " ").replace("\r", "\n")
    text = re.sub(r"\b(?:[A-Z]\s){2,}[A-Z]\b", join_spaced_caps, text)

    replacements = {
        "VIZUALIZATION": "VISUALIZATION",
        "Scrapping": "Scraping",
        "Analisys": "Analysis",
        "suppoprt": "support",
        "Engince": "Engine",
        "knowlegde": "knowledge",
    }
    for wrong, right in replacements.items():
        text = re.sub(wrong, right, text, flags=re.I)

    text = re.sub(r"([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})", r"\n\1\n", text, flags=re.I)
    text = re.sub(r"(\+?\d[\d\s\-()]{7,}\d)", r"\n\1\n", text)
    text = re.sub(r"(linkedin\.com/\S+)", r"\n\1\n", text, flags=re.I)

    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
    text = re.sub(r"\b(and|with|in|using|after|before|through|for)([a-zA-Z])", r"\1 \2", text, flags=re.I)
    text = re.sub(r"([a-zA-Z])(and|with|in|using|after|before|through|for)\b", r"\1 \2", text, flags=re.I)
    text = re.sub(r"(Würzburg|Wuerzburg|Germany|Deutschland)\s+(SQL|Python|Tableau|Power BI|Over|Ex-|Experienced|Skilled)", r"\1\n\2", text, flags=re.I)
    text = re.sub(r"(Bootcamp|School|University|College)\s+(Resolved|Provided|Improved|Automated|Built|Managed|Handled)", r"\1\n\2", text, flags=re.I)

    headings = [
        "PROFILE", "PROFESSIONAL SUMMARY", "SUMMARY", "OBJECTIVE", "WORK EXPERIENCE", "EXPERIENCE",
        "EMPLOYMENT HISTORY", "PROJECTS", "SKILLS", "TECHNICAL SKILLS", "EDUCATION", "CERTIFICATIONS",
        "LANGUAGES", "TOOLS", "CONTACT", "ACHIEVEMENTS"
    ]
    for h in headings:
        text = re.sub(rf"\s+({re.escape(h)})\s+", rf"\n\1\n", text, flags=re.I)

    text = re.sub(r"(\b\d{5}\b\s+[^\n,]+(?:,\s*[^\n]+)?)(\s+(?:Over|Ex-|Experienced|Skilled|Motivated|Passionate)\b)", r"\1\n\2", text)

    text = re.sub(r"[ \t]+", " ", text)
    lines = [line.strip() for line in text.splitlines()]
    cleaned = []
    for line in lines:
        if not line:
            if cleaned and cleaned[-1] != "":
                cleaned.append("")
            continue
        cleaned.append(line)
    text = "\n".join(cleaned)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def build_created_cv_text(full_name, email, phone, location, summary, skills, experience, education, projects="", certifications="", languages="", extra_info="") -> str:
    return f"""
Name: {full_name}
Email: {email}
Phone: {phone}
Location: {location}

Professional Summary:
{summary}

Skills:
{skills}

Work Experience:
{experience}

Projects:
{projects}

Certifications:
{certifications}

Education:
{education}

Languages:
{languages}

Additional Information:
{extra_info}
""".strip()

def generate_cv_from_user_details(cv_details: str, target_country: str, user_status: str) -> str:
    prompt = build_quality_prompt(
        task="Create a complete professional CV from the user's raw details.",
        user_input=cv_details,
        expected_structure="""
Return:
1. Full CV
2. Missing Information to Improve It
3. Resume Score Estimate
4. ATS Improvement Suggestions
5. Questions to Ask the User Next
"""
    )
    prompt += f"""

Target country: {target_country}
User status: {user_status}
Selected output language: {st.session_state.get("preferred_language", "English")}

Rules:
- Build a clean, ATS-friendly CV.
- The user may write broken English, short notes, or keywords. Convert them into polished professional resume wording.
- Translate the CV headings and content fully into the selected output language. Do not mix languages.
- Use only information the user provided.
- Do not invent employers, dates, degrees, tools, or achievements.
- If details are missing, add a clear section called "Missing Information to Improve It" in the selected output language.
- Make the CV suitable for the target country where possible.
"""
    return run_ai_prompt(prompt)

def organize_cv_for_display(cv_text: str) -> str:
    return clean_cv_text(cv_text)


def build_clean_cv_from_messy_extraction(raw_cv_text: str, target_country: str, user_status: str) -> str:
    """Turn messy two-column/table PDF extraction into a clean structured CV profile.

    This is intentionally different from preserving the original layout. WorkZo only needs the
    real career facts, then it can generate/update a clean CV in the correct template.
    """
    cleaned_raw = clean_cv_text(raw_cv_text)
    if not cleaned_raw.strip():
        return ""
    if len(cleaned_raw) < 500:
        return cleaned_raw

    prompt = f"""
The following CV text may come from a two-column/table PDF. The reading order may be wrong.
Your task is NOT to preserve the layout. Extract the useful facts and rebuild a clean, structured CV profile.

Target country: {target_country}
Career status: {user_status}
Preferred language: {st.session_state.get('preferred_language', 'English')}

Rules:
- Use only facts present in the raw CV text.
- Do not invent employers, dates, degrees, certifications, languages, tools, percentages, or achievements.
- Fix broken PDF words such as "in ternal" → "internal", "You Tube" → "YouTube", "for m" → "form", "In dian" → "Indian".
- Put details in the correct section even if the source order is mixed.
- Remove duplicate repeated contact/profile lines.
- Keep bullet points concise and ATS-friendly.
- If a detail is unclear, keep it under "Details to Confirm" instead of guessing.

Return ONLY this clean structure:

FULL NAME:
TARGET / CURRENT ROLE:
CONTACT:
PROFESSIONAL SUMMARY:
CORE SKILLS:
WORK EXPERIENCE:
PROJECTS:
EDUCATION:
CERTIFICATIONS:
LANGUAGES:
TOOLS / TECHNOLOGIES:
DETAILS TO CONFIRM:

Raw extracted CV text:
{cleaned_raw[:12000]}
"""
    structured = run_ai_prompt(
        prompt,
        system_addition="You are an expert CV parser. Convert messy extracted CV text into clean structured career facts before any scoring or rewriting.",
        force_language=st.session_state.get("preferred_language", "English")
    )
    if structured and not structured.startswith("ERROR:") and len(structured) > 400:
        return clean_cv_text(structured)
    return cleaned_raw

def infer_relevant_roles_from_cv(cv_text: str) -> List[str]:
    text = (cv_text or "").lower()
    roles: List[str] = []
    def add(role: str):
        if role not in roles:
            roles.append(role)
    if any(x in text for x in ["technical support", "it support", "service desk", "helpdesk", "troubleshoot", "tickets"]):
        add("IT Support Specialist")
        add("Technical Support Engineer")
        add("Service Desk Analyst")
        add("Customer Support Specialist")
    if any(x in text for x in ["sql", "python", "tableau", "power bi", "data analysis", "data visualization", "bootcamp"]):
        add("Junior Data Analyst")
        add("Business Intelligence Analyst")
        add("Reporting Analyst")
    if any(x in text for x in ["customer success", "onboarding", "saas", "client"]):
        add("Customer Success Associate")
    return roles[:6]

def build_job_matching_profile(cv_text: str) -> str:
    cleaned = clean_cv_text(cv_text)
    roles = infer_relevant_roles_from_cv(cleaned)
    skill_bank = ["Python", "SQL", "Tableau", "Power BI", "Excel", "Data Visualization", "Machine Learning", "Technical Support", "IT Support", "Service Desk", "Customer Support", "ITSM", "Zoho", "ManageEngine", "GCP", "Matplotlib", "Seaborn"]
    found_skills = [sk for sk in skill_bank if sk.lower() in cleaned.lower()]
    summary_bits = []
    if "technical support" in cleaned.lower() or "it support" in cleaned.lower():
        summary_bits.append("Experience in technical support, customer-facing troubleshooting, ticket handling, and user support.")
    if any(x in cleaned.lower() for x in ["data science", "data analyst", "sql", "python", "tableau"]):
        summary_bits.append("Data/analytics transition profile with Python, SQL, visualization, and bootcamp/project experience.")
    if not summary_bits:
        summary_bits.append(cleaned[:500])
    lines = ["MATCH-READY CV SUMMARY", ""]
    if roles:
        lines += ["Target roles that fit this profile:", *[f"- {r}" for r in roles[:5]], ""]
    lines += ["Professional profile:", *[f"- {b}" for b in summary_bits], ""]
    if found_skills:
        lines += ["Key skills/tools:", "- " + ", ".join(found_skills[:12]), ""]
    lines += ["Note:", "- This clean summary is used only for matching jobs. It avoids messy PDF line extraction."]
    return "\n".join(lines).strip()

# =========================================================
# SESSION STATE
# =========================================================
country_options = get_country_options()
language_options = get_language_options()
geo_country_default, geo_language_default = get_geo_defaults()

defaults = {
    "page": "landing",
    "onboarding_complete": False,
    "country": geo_country_default if geo_country_default in country_options else "Germany",
    "preferred_language": geo_language_default if geo_language_default in language_options else "English",
    "ui_language": geo_language_default if geo_language_default in language_options else "English",
    "response_language": geo_language_default if geo_language_default in language_options else "English",
    "user_status": "Career changer",
    "migration_country": geo_country_default if geo_country_default in country_options else "Germany",
    "career_goal": "",
    "cv_mode": "Upload CV",
    "cv_text": "",
    "dashboard_action": "Dashboard",
    "nav_page": "dashboard",

    # extracted dashboard profile
    "profile_summary": "",
    "current_role_detected": "",
    "key_skills_detected": "",
    "suggested_roles_detected": "",
    "best_fit_countries_detected": "",
    "next_actions_detected": "",
    "country_cv_readiness": "",
    "status_guidance": "",
    "cv_profile_raw": "",

    # dashboard analysis
    "cv_score_value": None,
    "ats_score_value": None,
    "country_readiness_score_value": None,
    "resume_strengths": "",
    "resume_improvements": "",
    "latest_resume_dashboard_analysis": "",
    "dashboard_cv_hash": "",

    # other scores
    "job_fit_score_value": None,
    "skill_gap_score_value": None,
    "interview_score_value": None,

    # outputs
    "latest_job_analysis": "",
    "latest_cv_analysis": "",
    "latest_interview": "",
    "latest_skill_gap": "",
    "latest_cover_letter": "",
    "latest_cv_translation": "",
    "latest_cover_letter_translation": "",

    # work-o-bot
    "workobot_mode": "General Help",
    "workobot_messages": [
        {
            "role": "assistant",
            "content": txt("workobot_intro") if "workobot_intro" in UI_TEXT.get(ui_lang(), {}) else "Hi, I’m Work-O-Bot. I can help with interview prep, career communication, and skill gap guidance."
        }
    ],

    # cache
    "dashboard_cache": {},
    "next_best_step_result": "",
    "ai_quality_style": "coach",
    "target_role_context": "",
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

init_beta_analytics()
track_event("app_open", "App")

# =========================================================
# HELPERS
# =========================================================
def google_search_url(query: str) -> str:
    return "https://www.google.com/search?q=" + urllib.parse.quote(query)

def extract_pdf_text(uploaded_file) -> str:
    text = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()

def safe_json_loads(raw: str) -> Dict:
    cleaned = raw.strip()

    # remove ```json fences if present
    cleaned = re.sub(r"^```json\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"^```\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise


# =========================================================
# AI QUALITY LAYER
# =========================================================
def get_user_status_context() -> str:
    return st.session_state.get("user_status", "Not specified")

def get_target_country_context() -> str:
    """Return the real application market. If applying abroad, target market overrides current country."""
    return st.session_state.get("migration_country") or st.session_state.get("country", "Not specified")

def get_target_role_context() -> str:
    return st.session_state.get("target_role_context", "") or st.session_state.get("current_role_detected", "") or "Not specified"

def compact_cv_context(max_chars: int = 3500) -> str:
    cv = st.session_state.get("cv_text", "") or ""
    cv = re.sub(r"\s+", " ", cv).strip()
    return cv[:max_chars] + ("..." if len(cv) > max_chars else "")

def clean_context_value(value, fallback: str = "Not available") -> str:
    value = str(value or "").strip()
    return value if value else fallback

def build_career_intelligence_layer(max_cv_chars: int = 4500) -> str:
    """
    Central context layer used before every AI call.
    This makes WorkZo's answers specific, country-aware, and less generic.
    """
    country = clean_context_value(st.session_state.get("country"), "Not selected")
    target_country = clean_context_value(st.session_state.get("migration_country") or st.session_state.get("country"), country)
    language = clean_context_value(st.session_state.get("preferred_language"), "English")
    user_status = clean_context_value(st.session_state.get("user_status"), "Not selected")
    target_role = clean_context_value(get_target_role_context(), "Not specified")

    return f"""
CAREER INTELLIGENCE LAYER
User selected country: {country}
Target / application country: {target_country}
Preferred output language: {language}
Current career situation: {user_status}
Target role or role direction: {target_role}
Career goal: {clean_context_value(st.session_state.get("career_goal"))}

AI-extracted profile summary:
{clean_context_value(st.session_state.get("profile_summary"))}

AI-extracted current role:
{clean_context_value(st.session_state.get("current_role_detected"))}

AI-extracted key skills:
{clean_context_value(st.session_state.get("key_skills_detected"))}

Detected resume strengths:
{clean_context_value(st.session_state.get("resume_strengths"))}

Detected resume improvements:
{clean_context_value(st.session_state.get("resume_improvements"))}

Current scores:
- Resume score: {clean_context_value(st.session_state.get("cv_score_value"), "Not calculated")}
- ATS score: {clean_context_value(st.session_state.get("ats_score_value"), "Not calculated")}
- Country readiness score: {clean_context_value(st.session_state.get("country_readiness_score_value"), "Not calculated")}

CV / profile text excerpt:
{compact_cv_context(max_cv_chars) or "No CV text available"}
""".strip()

def workzo_expert_context() -> str:
    return build_career_intelligence_layer()

SUPPORTED_UI_LANGUAGES = {"English", "German", "Dutch"}

def normalize_answer_language(language: str) -> str:
    language = (language or "English").strip()
    return language if language else "English"

def language_guard_rules(answer_lang: str) -> str:
    answer_lang = normalize_answer_language(answer_lang)
    if answer_lang == "German":
        return """
STRICT LANGUAGE MODE: German.
- Write the final answer completely in natural German.
- Do not mix English sentence starters, headings, explanations, or filler words.
- Allowed English only: company names, software/tool names, job titles when commonly used, URLs, email addresses, code, and exact keywords from a job ad/CV.
- Use German career terms where natural: Lebenslauf, Anschreiben, Berufserfahrung, Kenntnisse, Fähigkeiten, Ausbildung, Bewerbungsunterlagen.
- If you accidentally produce English headings or mixed English/German, rewrite the whole answer in German before returning it.
""".strip()
    if answer_lang == "Dutch":
        return """
STRICT LANGUAGE MODE: Dutch.
- Write the final answer completely in natural Dutch.
- Do not mix English sentence starters, headings, explanations, or filler words.
- Allowed English only: company names, software/tool names, job titles when commonly used, URLs, email addresses, code, and exact keywords from a job ad/CV.
- Use Dutch career terms where natural: cv, motivatiebrief, werkervaring, vaardigheden, opleiding, sollicitatie.
- If you accidentally produce English headings or mixed English/Dutch, rewrite the whole answer in Dutch before returning it.
""".strip()
    if answer_lang == "English":
        return """
STRICT LANGUAGE MODE: English.
- Write the final answer completely in English.
- Do not switch into German, Dutch, or another language unless the user specifically asks for a translation example.
""".strip()
    return f"""
STRICT LANGUAGE MODE: {answer_lang}.
- Write the final answer completely in natural {answer_lang}.
- Do not mix English sentence starters, headings, explanations, or filler words unless they are exact job titles, software/tool names, company names, URLs, email addresses, code, or keywords copied from the user's CV/job ad.
- Translate all guidance, headings, labels, and conclusions into {answer_lang}.
- If you accidentally produce mixed-language output, rewrite the whole answer in {answer_lang} before returning it.
""".strip()

def quality_system_prompt(answer_lang: str, system_addition: str = "") -> str:
    return f"""
You are WorkZo AI, a senior international career strategist, resume consultant, ATS specialist, interview coach, and job-search advisor.

Your job is NOT to give generic AI advice. Your job is to give precise, personalized, practical guidance based on:
- the user's CV/profile
- the user's status: fresh graduate, migrant, career changer, experienced professional, etc.
- the target country and local hiring expectations
- the user's target role and current experience level

{language_guard_rules(answer_lang)}

Quality rules:
1. Be specific. Avoid generic sentences like "improve your skills" unless you say exactly which skill, why it matters, and what to do next.
2. Use the user's actual CV/profile details whenever available. Reference concrete roles, tools, skills, industries, projects, and gaps from the provided context.
3. Be honest about weak fit, missing experience, language gaps, unrealistic seniority, or template mismatch.
4. Give prioritized actions: what to do first, second, third.
5. For migration/country-specific topics, mention local CV expectations, language expectations, and role-market fit.
6. For fresh graduates, focus on portfolio projects, internships, entry-level roles, keywords, and proof of skill.
7. For career changers, focus on transferable skills, bridge roles, portfolio proof, and realistic role titles.
8. For experienced users, focus on positioning, measurable achievements, leadership/impact, and market fit.
9. Keep output structured with useful headings and concise bullets. Prefer 3-5 strong points over long generic lists.
10. Never invent employers, degrees, certifications, dates, or achievements.
11. If information is missing, clearly say what is missing and give a best-effort recommendation.
12. End with a clear "Next best action" when appropriate.
13. Every answer must feel like it was written for this user, this country, and this career situation.
14. Do not give generic advice such as "network more", "improve your resume", or "learn more skills" without converting it into a concrete action.

Use this context where relevant:
{workzo_expert_context()}

{system_addition}
""".strip()

def build_quality_prompt(task: str, user_input: str, expected_structure: str = "") -> str:
    return f"""
Task: {task}

{build_career_intelligence_layer()}

User input:
{user_input}

Expected output structure:
{expected_structure}

Advanced output rules:
- Start with the most useful answer first, not a long introduction.
- Give practical, tailored, country-aware, and status-aware advice.
- Avoid generic advice. Mention concrete skills, role titles, keywords, CV sections, or actions wherever possible.
- Keep the answer easy to scan with short sections and bullets.
- When useful, include a short "Why this matters" and a "Next best action".
- Follow the selected preferred language strictly. Do not mix languages.
""".strip()


def run_ai_prompt(
    prompt: str,
    system_addition: str = "",
    force_language: str = None,
    force_english: bool = False,
    json_mode: bool = False
) -> str:
    if not can_make_request():
        return "ERROR: Usage limit reached. Please try again later."

    register_request()

    if force_english:
        answer_lang = "English"
    elif force_language:
        answer_lang = normalize_answer_language(force_language)
    else:
        answer_lang = normalize_answer_language(st.session_state.get("preferred_language", "English"))

    strict_system_addition = f"""
{system_addition}

FINAL OUTPUT LANGUAGE: {answer_lang}
You must obey STRICT LANGUAGE MODE. Before you answer, internally check that every heading, bullet, explanation, and closing sentence is in {answer_lang}.
Do not mention this language check to the user.
""".strip()

    system_prompt = quality_system_prompt(answer_lang, strict_system_addition)
    model_name = os.getenv("WORKZO_AI_MODEL") or get_streamlit_secret("WORKZO_AI_MODEL", "gpt-4o-mini")

    try:
        enhanced_user_prompt = f"""
{build_career_intelligence_layer()}

USER REQUEST / FEATURE TASK:
{prompt}

Response requirements:
- Do not answer generically. Use the career intelligence layer above.
- Give the strongest 3-5 insights only unless the task explicitly asks for more.
- Convert broad advice into exact actions the user can take.
- If a CV, job description, target role, or country detail is missing, say that clearly and provide the best next step.
""".strip()

        kwargs = {
            "model": model_name,
            "temperature": 0.2,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": enhanced_user_prompt}
            ]
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        res = client.chat.completions.create(**kwargs)
        return (res.choices[0].message.content or "").strip()
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {str(e)}"

def render_error_or_success(result: str):
    if result.startswith("ERROR:"):
        st.error(txt("ai_unavailable"))
        st.caption(result)
        return False
    return True

def parse_score(text: str) -> Optional[int]:
    if not text:
        return None

    match = re.search(r'(\d{1,3})\s*/\s*100', text)
    if match:
        value = int(match.group(1))
        if 0 <= value <= 100:
            return value

    match = re.search(r'(?<!\d)(\d{1,3})(?!\d)', text)
    if match:
        value = int(match.group(1))
        if 0 <= value <= 100:
            return value

    return None

def numbered_sections_to_markdown(text: str) -> Dict[str, str]:
    """Parse AI sections like `1. Title`, `### 1. Title`, or `**1. Title**`.
    This prevents the same full response appearing in every expander.
    """
    text = text or ""
    sections = {}
    pattern = r'(?m)^\s*(?:#{1,6}\s*)?(?:\*\*)?(\d+)\.\s*(.+?)(?:\*\*)?\s*$'
    matches = list(re.finditer(pattern, text))
    if not matches:
        return {"Result": text.strip()}

    for i, match in enumerate(matches):
        title = match.group(2).strip()
        title = title.replace("**", "").replace("__", "").strip().rstrip(":")
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        body = re.sub(r"^[-–—\s]+", "", body).strip()
        sections[title] = body
    return sections

def render_section_cards(result: str, default_expand: bool = False):
    if not render_error_or_success(result):
        return
    sections = numbered_sections_to_markdown(result)
    for title, body in sections.items():
        with st.expander(title, expanded=default_expand):
            st.write(body if body else "—")


# =========================================================
# UNDERSTAND JOB - COMPACT DECISION ASSISTANT UI
# =========================================================
def safe_json_loads(text: str):
    """Parse AI JSON even if the model wraps it in markdown."""
    if not text:
        return None
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"\s*```$", "", cleaned).strip()
    try:
        return json.loads(cleaned)
    except Exception:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                return None
    return None


def clamp_score_value(value, default: int = 0) -> int:
    try:
        score = int(float(value))
    except Exception:
        score = default
    return max(0, min(100, score))


def verdict_from_score(score: int) -> str:
    if score >= 80:
        return "Strong apply"
    if score >= 60:
        return "Apply, but tailor first"
    if score >= 40:
        return "Possible, but risky"
    return "Skip or improve first"


def render_list_items(items, empty_text: str = "—"):
    if isinstance(items, str):
        items = [items]
    if not items:
        st.write(empty_text)
        return
    for item in items:
        if str(item).strip():
            st.markdown(f"- {str(item).strip()}")


def render_requirement_checklist(requirements):
    if not isinstance(requirements, list) or not requirements:
        st.info("No requirement checklist was generated.")
        return
    st.markdown("#### Requirement checklist")
    for req in requirements:
        if not isinstance(req, dict):
            continue
        requirement = str(req.get("requirement", "Requirement")).strip()
        status = str(req.get("status", "Partial")).strip()
        evidence = str(req.get("evidence", "")).strip()
        status_lower = status.lower()
        icon = "✅" if "strong" in status_lower or "match" in status_lower else "❌" if "missing" in status_lower or "gap" in status_lower else "🟡"
        st.markdown(f"**{icon} {requirement}**  ")
        if evidence:
            st.caption(evidence)


def render_understand_job_analysis(data: dict):
    """Render Understand Job as a compact decision assistant instead of a long report."""
    if not isinstance(data, dict):
        st.warning("The job analysis could not be structured. Please try again.")
        return

    fit_score = clamp_score_value(data.get("fit_score", 0))
    skill_score = clamp_score_value(data.get("skill_match", 0))
    exp_score = clamp_score_value(data.get("experience_match", 0))
    lang_score = clamp_score_value(data.get("language_match", 0))
    keyword_score = clamp_score_value(data.get("keyword_match", 0))
    verdict = str(data.get("verdict") or verdict_from_score(fit_score)).strip()
    main_reason = str(data.get("main_reason") or "Review the match breakdown before applying.").strip()

    st.markdown("### Job Fit Summary")
    st.markdown(f"""
<div class='next-action-card'>
  <div class='next-action-label'>Decision assistant</div>
  <div class='next-action-title'>Job Fit: {fit_score}/100 — {html.escape(verdict)}</div>
  <div class='next-action-copy'>{html.escape(main_reason)}</div>
</div>
""", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Skill match", f"{skill_score}/100")
    c2.metric("Experience match", f"{exp_score}/100")
    c3.metric("Language match", f"{lang_score}/100")
    c4.metric("Keyword match", f"{keyword_score}/100")

    comparison = data.get("cv_job_comparison", {}) if isinstance(data.get("cv_job_comparison"), dict) else {}
    if comparison:
        st.markdown("### CV vs Job")
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.markdown("**Job asks for**")
            render_list_items(comparison.get("job_asks_for", []))
        with col_b:
            st.markdown("**Your CV shows**")
            render_list_items(comparison.get("cv_shows", []))
        with col_c:
            st.markdown("**Main gaps**")
            render_list_items(comparison.get("main_gaps", []))

    render_requirement_checklist(data.get("requirement_checklist", []))

    col_gap, col_tailor = st.columns(2)
    with col_gap:
        with st.expander("Gaps & Risks", expanded=True):
            render_list_items(data.get("gaps_and_risks", []))
    with col_tailor:
        with st.expander("How to Tailor Your CV", expanded=True):
            st.markdown("**Suggested CV bullets**")
            render_list_items(data.get("tailored_cv_bullets", []))

    with st.expander("Interview Preparation", expanded=False):
        st.markdown("**Likely interview focus**")
        render_list_items(data.get("interview_focus", []))
        questions = data.get("interview_questions", [])
        if questions:
            st.markdown("**Sample interview questions**")
            for idx, q in enumerate(questions, 1):
                st.markdown(f"{idx}. {q}")

    salary_note = str(data.get("salary_estimate_note", "")).strip()
    if salary_note:
        with st.expander("Salary estimate — optional", expanded=False):
            st.write(salary_note)
            st.caption("Approximate only. Verify with local salary sources and the employer.")

    st.markdown("### Next Best Action")
    st.info(str(data.get("next_best_action") or "Tailor your CV before applying.").strip())



def normalize_resume_dates(text_value: str) -> str:
    """Repair PDF/AI date splits and protect resume date ranges from ugly line breaks."""
    text_value = text_value or ""
    text_value = text_value.replace("\r\n", "\n").replace("\r", "\n")

    # Collapse dates split across lines, including blank lines:
    # 10/
    # 2018 - 01
    # /2020  -> 10/2018 - 01/2020
    for _ in range(4):
        text_value = re.sub(r"(\b\d{1,2})\s*/\s*\n+\s*(\d{4}\b)", r"\1/\2", text_value)
        text_value = re.sub(r"(\b\d{1,2})\s*\n+\s*/\s*(\d{4}\b)", r"\1/\2", text_value)
        text_value = re.sub(r"(\b\d{1,2}/\d{4})\s*\n+\s*[-–—]\s*\n+\s*(\d{1,2}/\d{4}\b)", r"\1 - \2", text_value)
        text_value = re.sub(r"(\b\d{1,2}/\d{4})\s*[-–—]\s*\n+\s*(\d{1,2}/\d{4}\b)", r"\1 - \2", text_value)
        text_value = re.sub(r"(\b\d{4})\s*\n+\s*[-–—]\s*\n+\s*(\d{4}|Present|Current|Heute|Now)\b", r"\1 - \2", text_value, flags=re.I)
        text_value = re.sub(r"(\b\d{4})\s*[-–—]\s*\n+\s*(\d{4}|Present|Current|Heute|Now)\b", r"\1 - \2", text_value, flags=re.I)

    # Fix slash spacing and range spacing inside a single line.
    text_value = re.sub(r"\b(\d{1,2})\s*/\s*(\d{4})\b", r"\1/\2", text_value)
    text_value = re.sub(r"\b(\d{1,2}/\d{4})\s*[-–—]\s*(\d{1,2}/\d{4}|Present|Current|Heute|Now)\b", r"\1 - \2", text_value, flags=re.I)
    text_value = re.sub(r"\b(\d{4})\s*[-–—]\s*(\d{4}|Present|Current|Heute|Now)\b", r"\1 - \2", text_value, flags=re.I)

    text_value = re.sub(r"\bBer\s+l\s+in\b", "Berlin", text_value, flags=re.IGNORECASE)
    return text_value


def make_minimal_pdf_from_text(title: str, body: str) -> bytes:
    """Create a valid simple PDF without external libraries, used as a safe fallback."""
    def esc_pdf(txt: str) -> str:
        txt = (txt or "").encode("latin-1", "replace").decode("latin-1")
        return txt.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    cleaned = strip_markdown_for_resume(body)
    lines = []
    for raw in cleaned.splitlines():
        line = raw.strip()
        if line:
            while len(line) > 95:
                cut = line.rfind(" ", 0, 95)
                if cut < 35:
                    cut = 95
                lines.append(line[:cut].strip())
                line = line[cut:].strip()
            lines.append(line)
        else:
            lines.append("")
    pages = []
    current = []
    for line in lines:
        current.append(line)
        if len(current) >= 48:
            pages.append(current)
            current = []
    if current or not pages:
        pages.append(current)
    page_ids = []
    content_objects = []
    page_objects = []
    next_obj_id = 4
    for page_lines in pages:
        content_id = next_obj_id
        page_id = next_obj_id + 1
        next_obj_id += 2
        page_ids.append(page_id)
        stream_lines = ["BT", "/F1 10 Tf", "50 800 Td", "14 TL"]
        first = True
        for line in page_lines:
            if not first:
                stream_lines.append("T*")
            first = False
            if line:
                stream_lines.append(f"({esc_pdf(line)}) Tj")
            else:
                stream_lines.append("T*")
        stream_lines.append("ET")
        stream = "\n".join(stream_lines).encode("latin-1", "replace")
        content_objects.append((content_id, f"<< /Length {len(stream)} >>\nstream\n".encode("latin-1") + stream + b"\nendstream"))
        page_objects.append((page_id, f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 3 0 R >> >> /Contents {content_id} 0 R >>".encode("latin-1")))
    all_objects = [
        (1, b"<< /Type /Catalog /Pages 2 0 R >>"),
        (2, f"<< /Type /Pages /Kids [{' '.join(f'{pid} 0 R' for pid in page_ids)}] /Count {len(page_ids)} >>".encode("latin-1")),
        (3, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"),
    ] + content_objects + page_objects
    all_objects.sort(key=lambda x: x[0])
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = {0: 0}
    for obj_id, content in all_objects:
        offsets[obj_id] = len(pdf)
        pdf.extend(f"{obj_id} 0 obj\n".encode("latin-1"))
        pdf.extend(content)
        pdf.extend(b"\nendobj\n")
    xref_pos = len(pdf)
    max_id = max(offsets)
    pdf.extend(f"xref\n0 {max_id+1}\n".encode("latin-1"))
    pdf.extend(b"0000000000 65535 f \n")
    for i in range(1, max_id+1):
        pdf.extend(f"{offsets.get(i, 0):010d} 00000 n \n".encode("latin-1"))
    pdf.extend(f"trailer\n<< /Size {max_id+1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF".encode("latin-1"))
    return bytes(pdf)

def strip_markdown_for_resume(text_value: str) -> str:
    """Remove AI markdown artifacts so the downloadable CV looks like a real resume, not a chat response."""
    text_value = normalize_resume_dates(text_value or "")
    cleaned_lines = []
    for raw in text_value.splitlines():
        line = raw.strip()
        if not line:
            cleaned_lines.append("")
            continue
        line = re.sub(r"^#{1,6}\s*", "", line)
        line = line.replace("**", "").replace("__", "")
        line = re.sub(r"^\s*[-*]\s+", "- ", line)
        line = re.sub(r"\[([^\]]+)\]\(([^\)]+)\)", r"\1: \2", line)
        cleaned_lines.append(line)
    cleaned = "\n".join(cleaned_lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned

def country_resume_rules_text(country: str) -> str:
    rules = get_country_cv_rules(country)
    return f"""
Country style rules for {country}:
- Recommended length: about {rules.get('pages', 2)} page(s), depending on experience.
- Recommended sections: {', '.join(rules.get('sections', []))}.
- Photo: {'allowed/optional' if rules.get('photo') else 'do not include'}.
- Date of birth / sensitive personal details: {'allowed only if user already provided and it is appropriate' if rules.get('dob') else 'do not include'}.
- Important exclusions: {rules.get('avoid', 'Avoid sensitive personal details and do not invent information.')}.
""".strip()

def make_docx_from_cv_text(title: str, cv_text: str, template_name: str = "ATS Resume", target_country: str = "") -> bytes:
    """Create a real editable DOCX resume. Falls back to TXT bytes if python-docx is unavailable."""
    cleaned = strip_markdown_for_resume(cv_text)
    if Document is None:
        return cleaned.encode("utf-8")

    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(0.55)
    section.bottom_margin = Inches(0.55)
    section.left_margin = Inches(0.65)
    section.right_margin = Inches(0.65)

    style = doc.styles["Normal"]
    style.font.name = "Arial"
    style.font.size = Pt(10.5)

    lines = [line.rstrip() for line in cleaned.splitlines()]
    first_written = False
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        heading_candidate = line.upper() == line and len(line) <= 45 and not line.startswith("-")
        if not first_written:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(line)
            run.bold = True
            run.font.size = Pt(18)
            first_written = True
        elif line.startswith("- "):
            p = doc.add_paragraph(style=None)
            p.style = doc.styles["List Bullet"]
            p.add_run(line[2:].strip())
        elif heading_candidate or line.endswith(":"):
            p = doc.add_paragraph()
            run = p.add_run(line.rstrip(":"))
            run.bold = True
            run.font.size = Pt(12)
        else:
            doc.add_paragraph(line)

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()


def _cv_flowables_for_pdf(text_value: str, styles, title: str = ""):
    """Convert a CV section into ReportLab flowables with neat bullets."""
    flow = []
    if title:
        flow.append(Paragraph(title.upper(), styles["section"]))
    text_value = normalize_resume_dates(text_value or "")
    for raw in text_value.splitlines():
        line = raw.strip()
        if not line:
            flow.append(Spacer(1, 3))
            continue
        safe = html.escape(line)
        if line.startswith(("- ", "• ", "* ")):
            flow.append(Paragraph(safe.lstrip("-•* ").strip(), styles["bullet"], bulletText="•"))
        elif line.upper() == line and len(line) <= 48 and not re.search(r"\d", line):
            flow.append(Paragraph(safe.title() if len(line) < 8 else safe, styles["mini_heading"]))
        else:
            flow.append(Paragraph(safe, styles["body"]))
    if not text_value.strip():
        flow.append(Paragraph("—", styles["muted"]))
    return flow


def make_styled_pdf_from_cv_text(title: str, cv_text: str, template_name: str = "ATS Resume", target_country: str = "") -> bytes:
    """Create a designed, template-based PDF resume that matches the visual preview style."""
    cleaned = strip_markdown_for_resume(normalize_resume_dates(cv_text))
    if SimpleDocTemplate is None or Table is None or TableStyle is None or colors is None:
        return make_minimal_pdf_from_text(title, cleaned)

    data = parse_cv_sections_for_template(cleaned)
    header_lines = [x.strip() for x in data.get("header", "").splitlines() if x.strip()]
    name = header_lines[0] if header_lines else "Your Name"
    role = header_lines[1] if len(header_lines) > 1 else f"CV for {target_country or 'Selected Country'}"
    contact = " | ".join(header_lines[2:]) if len(header_lines) > 2 else ""
    style_key = resolve_template_style(template_name)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=26, leftMargin=26, topMargin=24, bottomMargin=24)

    base = getSampleStyleSheet()
    styles = {
        "name": ParagraphStyle("WZName", parent=base["Title"], fontName="Helvetica-Bold", fontSize=24, leading=28, textColor=colors.HexColor("#111827"), spaceAfter=4),
        "role": ParagraphStyle("WZRole", parent=base["BodyText"], fontName="Helvetica", fontSize=11, leading=14, textColor=colors.HexColor("#334155"), spaceAfter=6),
        "contact": ParagraphStyle("WZContact", parent=base["BodyText"], fontName="Helvetica", fontSize=8.7, leading=11, textColor=colors.HexColor("#475569"), spaceAfter=8),
        "section": ParagraphStyle("WZSection", parent=base["Heading4"], fontName="Helvetica-Bold", fontSize=9.7, leading=12, textColor=colors.HexColor("#111827"), spaceBefore=8, spaceAfter=5),
        "mini_heading": ParagraphStyle("WZMiniHeading", parent=base["BodyText"], fontName="Helvetica-Bold", fontSize=9.2, leading=12, textColor=colors.HexColor("#111827"), spaceBefore=3, spaceAfter=3),
        "body": ParagraphStyle("WZBody", parent=base["BodyText"], fontName="Helvetica", fontSize=9.2, leading=12.2, textColor=colors.HexColor("#111827"), spaceAfter=3),
        "bullet": ParagraphStyle("WZBullet", parent=base["BodyText"], fontName="Helvetica", fontSize=9.1, leading=12.1, textColor=colors.HexColor("#111827"), leftIndent=10, firstLineIndent=0, spaceAfter=3),
        "muted": ParagraphStyle("WZMuted", parent=base["BodyText"], fontName="Helvetica", fontSize=8.5, leading=11, textColor=colors.HexColor("#64748b")),
    }

    story = []
    if style_key == "Creative Modern":
        header = [[Paragraph(html.escape(name), ParagraphStyle("CMName", parent=styles["name"], textColor=colors.white)),
                   Paragraph(html.escape(role), ParagraphStyle("CMRole", parent=styles["role"], textColor=colors.white))]]
        header_tbl = Table(header, colWidths=[doc.width * .64, doc.width * .36])
        header_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#1d4ed8")),
            ("BOX", (0,0), (-1,-1), 0, colors.HexColor("#1d4ed8")),
            ("LEFTPADDING", (0,0), (-1,-1), 18), ("RIGHTPADDING", (0,0), (-1,-1), 18),
            ("TOPPADDING", (0,0), (-1,-1), 18), ("BOTTOMPADDING", (0,0), (-1,-1), 16),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ]))
        story.append(header_tbl)
        if contact:
            story.append(Paragraph(html.escape(contact), styles["contact"]))
    else:
        story.append(Paragraph(html.escape(name), styles["name"]))
        story.append(Paragraph(html.escape(role), styles["role"]))
        if contact:
            story.append(Paragraph(html.escape(contact), styles["contact"]))
        story.append(Table([[""]], colWidths=[doc.width], rowHeights=[2], style=TableStyle([("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#1f2937"))])))
        story.append(Spacer(1, 10))

    sidebar_flow = []
    main_flow = []

    if style_key in ["German-Style Lebenslauf", "Executive Slate"]:
        sidebar_flow += _cv_flowables_for_pdf(data.get("skills"), styles, "Skills")
        sidebar_flow += _cv_flowables_for_pdf(data.get("languages"), styles, "Languages")
        sidebar_flow += _cv_flowables_for_pdf(data.get("education"), styles, "Education")
        sidebar_flow += _cv_flowables_for_pdf(data.get("certifications"), styles, "Certifications")
        main_flow += _cv_flowables_for_pdf(data.get("summary"), styles, "Profile")
        main_flow += _cv_flowables_for_pdf(data.get("experience"), styles, "Experience")
        main_flow += _cv_flowables_for_pdf(data.get("projects"), styles, "Projects")
        main_flow += _cv_flowables_for_pdf(data.get("other"), styles, "Additional")
        left_bg = colors.HexColor("#eef2f7")
    elif style_key == "Career Pivot":
        sidebar_flow += _cv_flowables_for_pdf(data.get("skills"), styles, "Transferable Skills")
        sidebar_flow += _cv_flowables_for_pdf(data.get("education"), styles, "Education")
        sidebar_flow += _cv_flowables_for_pdf(data.get("languages"), styles, "Languages")
        main_flow += _cv_flowables_for_pdf(data.get("summary"), styles, "Career Change Profile")
        main_flow += _cv_flowables_for_pdf(data.get("projects"), styles, "Relevant Projects")
        main_flow += _cv_flowables_for_pdf(data.get("experience"), styles, "Experience Reframed")
        main_flow += _cv_flowables_for_pdf(data.get("certifications"), styles, "Certifications")
        left_bg = colors.HexColor("#f3e8ff")
    elif style_key == "Graduate Portfolio":
        sidebar_flow += _cv_flowables_for_pdf(data.get("education"), styles, "Education")
        sidebar_flow += _cv_flowables_for_pdf(data.get("skills"), styles, "Technical Skills")
        sidebar_flow += _cv_flowables_for_pdf(data.get("languages"), styles, "Languages")
        main_flow += _cv_flowables_for_pdf(data.get("summary"), styles, "Career Objective")
        main_flow += _cv_flowables_for_pdf(data.get("projects"), styles, "Projects")
        main_flow += _cv_flowables_for_pdf(data.get("experience"), styles, "Experience")
        main_flow += _cv_flowables_for_pdf(data.get("certifications"), styles, "Certifications")
        left_bg = colors.HexColor("#e0f2fe")
    elif style_key == "Creative Modern":
        main_flow += _cv_flowables_for_pdf(data.get("summary"), styles, "Profile")
        main_flow += _cv_flowables_for_pdf(data.get("experience"), styles, "Experience")
        main_flow += _cv_flowables_for_pdf(data.get("projects"), styles, "Projects")
        sidebar_flow += _cv_flowables_for_pdf(data.get("skills"), styles, "Skills")
        sidebar_flow += _cv_flowables_for_pdf(data.get("education"), styles, "Education")
        sidebar_flow += _cv_flowables_for_pdf(data.get("certifications"), styles, "Certifications")
        sidebar_flow += _cv_flowables_for_pdf(data.get("languages"), styles, "Languages")
        left_bg = colors.HexColor("#ecfeff")
    else:
        # Premium ATS layout: still scanner-friendly, but no longer visually plain.
        main_flow += _cv_flowables_for_pdf(data.get("summary"), styles, "Professional Summary")
        main_flow += _cv_flowables_for_pdf(data.get("skills"), styles, "Core Skills")
        main_flow += _cv_flowables_for_pdf(data.get("experience"), styles, "Professional Experience")
        main_flow += _cv_flowables_for_pdf(data.get("projects"), styles, "Projects")
        main_flow += _cv_flowables_for_pdf(data.get("education"), styles, "Education")
        main_flow += _cv_flowables_for_pdf(data.get("certifications"), styles, "Certifications")
        main_flow += _cv_flowables_for_pdf(data.get("languages"), styles, "Languages")

        accent = colors.HexColor("#2563eb")
        if str(target_country).lower() in ["germany", "austria", "switzerland"]:
            accent = colors.HexColor("#111827")
        elif str(target_country).lower() in ["india", "singapore"]:
            accent = colors.HexColor("#0f766e")
        elif str(target_country).lower() in ["canada", "united states", "usa", "united kingdom", "uk", "australia"]:
            accent = colors.HexColor("#1d4ed8")

        premium_box = Table([[main_flow]], colWidths=[doc.width], hAlign="LEFT")
        premium_box.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), colors.white),
            ("BOX", (0,0), (-1,-1), 0.7, colors.HexColor("#dbe3ef")),
            ("LEFTPADDING", (0,0), (-1,-1), 18),
            ("RIGHTPADDING", (0,0), (-1,-1), 18),
            ("TOPPADDING", (0,0), (-1,-1), 16),
            ("BOTTOMPADDING", (0,0), (-1,-1), 16),
            ("VALIGN", (0,0), (-1,-1), "TOP"),
        ]))
        story.append(premium_box)
        story.append(Spacer(1, 6))
        try:
            doc.build(story)
            buffer.seek(0)
            data_pdf = buffer.getvalue()
            return data_pdf if data_pdf.startswith(b"%PDF") else make_minimal_pdf_from_text(title, cleaned)
        except Exception:
            return make_minimal_pdf_from_text(title, cleaned)

    table = Table([[sidebar_flow, main_flow]], colWidths=[doc.width * 0.34, doc.width * 0.66], hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (0,0), left_bg),
        ("BACKGROUND", (1,0), (1,0), colors.white),
        ("LEFTPADDING", (0,0), (0,0), 14), ("RIGHTPADDING", (0,0), (0,0), 14),
        ("TOPPADDING", (0,0), (-1,-1), 16), ("BOTTOMPADDING", (0,0), (-1,-1), 16),
        ("LEFTPADDING", (1,0), (1,0), 18), ("RIGHTPADDING", (1,0), (1,0), 12),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("BOX", (0,0), (-1,-1), 0.5, colors.HexColor("#e5e7eb")),
    ]))
    story.append(table)

    try:
        doc.build(story)
        buffer.seek(0)
        data_pdf = buffer.getvalue()
        if not data_pdf.startswith(b"%PDF"):
            return make_minimal_pdf_from_text(title, cleaned)
        return data_pdf
    except Exception:
        return make_minimal_pdf_from_text(title, cleaned)

def make_pdf_from_text(title: str, body: str) -> bytes:
    """
    Create a simple PDF from generated CV text.
    Falls back to encoded text if reportlab is unavailable, but Streamlit label will show dependency need.
    """
    if SimpleDocTemplate is None:
        return make_minimal_pdf_from_text(title, body)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=42, leftMargin=42, topMargin=42, bottomMargin=42)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(title, styles["Title"]))
    story.append(Spacer(1, 12))

    for raw_line in body.splitlines():
        line = raw_line.strip()
        if not line:
            story.append(Spacer(1, 8))
            continue
        safe_line = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if line.endswith(":") or line.isupper():
            story.append(Paragraph(f"<b>{safe_line}</b>", styles["Heading3"]))
        else:
            story.append(Paragraph(safe_line, styles["BodyText"]))
            story.append(Spacer(1, 4))

    try:
        doc.build(story)
        buffer.seek(0)
        data = buffer.getvalue()
        if not data.startswith(b"%PDF"):
            return make_minimal_pdf_from_text(title, body)
        return data
    except Exception:
        return make_minimal_pdf_from_text(title, body)

def get_section_text(result: str, names: List[str], fallback_to_full: bool = False) -> str:
    sections = numbered_sections_to_markdown(result)
    lower_map = {k.lower().strip(): v for k, v in sections.items()}
    for name in names:
        value = sections.get(name, "").strip()
        if value:
            return value
        value = lower_map.get(name.lower().strip(), "").strip()
        if value:
            return value
    return result.strip() if fallback_to_full else ""


def show_gauge(score: Optional[int], title: str):
    if score is None:
        st.info(txt("not_analyzed"))
        return

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={"text": title},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"thickness": 0.35},
            "steps": [
                {"range": [0, 40], "color": "#f8d7da"},
                {"range": [40, 70], "color": "#fff3cd"},
                {"range": [70, 100], "color": "#d1e7dd"},
            ],
        }
    ))
    fig.update_layout(height=260, margin=dict(l=20, r=20, t=50, b=20))
    st.plotly_chart(fig, use_container_width=True)

def make_cv_hash(cv_text: str, country: str) -> str:
    raw = f"{SCORING_VERSION}||{country.strip()}||{st.session_state.get('migration_country', '').strip()}||{st.session_state.get('user_status', '').strip()}||{cv_text.strip()}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()

def bool_score(flag: bool, points: int) -> int:
    return points if flag else 0

def score_band(score: int) -> str:
    if score < 40:
        return "Weak"
    if score < 60:
        return "Needs improvement"
    if score < 76:
        return "Good base"
    if score < 86:
        return "Strong"
    return "Excellent"


def calculate_resume_score(features: Dict) -> int:
    """
    Honest resume quality score.
    A basic or messy CV should land around 35–60, not 85–95.
    Scores above 85 require strong structure, measurable achievements, clear sections, and enough detail.
    """
    word_count = int(features.get("word_count", 0) or 0)
    score = 0
    score += round(features.get("contact_score", 0) * 8)
    score += round(features.get("summary_score", 0) * 10)
    score += round(features.get("experience_score", 0) * 18)
    score += round(features.get("skills_score", 0) * 12)
    score += round(features.get("education_score", 0) * 8)
    score += round(features.get("quantified_score", 0) * 18)
    score += round(features.get("bullet_score", 0) * 10)
    score += round(features.get("date_score", 0) * 8)
    score += round(features.get("formatting_score", 0) * 8)

    action_verb_hits = int(features.get("action_verb_hits", 0) or 0)
    score += min(6, action_verb_hits)

    # Strong penalties for CVs that look complete but lack proof or structure.
    if word_count < 80:
        score = min(score, 35)
    elif word_count < 120:
        score = min(score, 45)
    elif word_count < 180:
        score = min(score, 58)

    if not features.get("work_experience_present", False):
        score = min(score, 55)
    if not features.get("skills_present", False):
        score = min(score, 62)
    if not features.get("professional_summary_present", False):
        score = min(score, 72)
    if not features.get("contact_info_present", False):
        score = min(score, 70)
    if not features.get("bullet_points_present", False):
        score = min(score, 74)
    if not features.get("quantified_achievements_present", False):
        score = min(score, 76)
    if int(features.get("section_heading_hits", 0) or 0) < 3:
        score = min(score, 78)

    long_lines = int(features.get("long_lines", 0) or 0)
    if long_lines > 6:
        score -= 10
    elif long_lines > 3:
        score -= 5

    # Reserve very high scores for genuinely strong CVs.
    if not (features.get("quantified_achievements_present") and features.get("bullet_points_present") and int(features.get("section_heading_hits", 0) or 0) >= 4 and word_count >= 280):
        score = min(score, 84)

    return max(10, min(int(score), 94))


def calculate_ats_score(features: Dict) -> int:
    """
    Honest ATS-readiness score.
    ATS score is about readable structure, standard headings, keywords, dates, and simple formatting.
    High scores require clear headings, skills, experience, dates, bullets, and readable text.
    """
    word_count = int(features.get("word_count", 0) or 0)
    score = 0
    score += 18 if features.get("standard_headings_present", False) else 4
    score += round(features.get("contact_score", 0) * 8)
    score += 14 if features.get("plain_text_readable", False) else 2
    score += round(features.get("skills_score", 0) * 14)
    score += round(features.get("experience_score", 0) * 16)
    score += round(features.get("education_score", 0) * 7)
    score += round(features.get("bullet_score", 0) * 9)
    score += round(features.get("date_score", 0) * 9)
    score += min(5, int(features.get("action_verb_hits", 0) or 0))

    if word_count < 80:
        score = min(score, 32)
    elif word_count < 120:
        score = min(score, 42)
    elif word_count < 180:
        score = min(score, 55)

    if not features.get("standard_headings_present", False):
        score = min(score, 62)
    if not features.get("work_experience_present", False):
        score = min(score, 55)
    if not features.get("skills_present", False):
        score = min(score, 60)
    if not features.get("date_ranges_present", False):
        score = min(score, 70)
    if not features.get("plain_text_readable", False):
        score = min(score, 64)
    if not features.get("bullet_points_present", False):
        score = min(score, 72)

    long_lines = int(features.get("long_lines", 0) or 0)
    if long_lines > 6:
        score -= 12
    elif long_lines > 3:
        score -= 6

    if not (features.get("standard_headings_present") and features.get("skills_present") and features.get("date_ranges_present") and features.get("plain_text_readable") and word_count >= 260):
        score = min(score, 82)

    return max(10, min(int(score), 94))


def calculate_country_readiness_score(features: Dict, target_country: str, user_status: str) -> int:
    """
    Resume readiness for selected migration/target country.
    This is intentionally stricter than the general resume score.
    """
    base = calculate_resume_score(features)

    score = int(base * 0.72)

    # Country-template/readability signals
    if features.get("contact_info_present", False):
        score += 6
    if features.get("standard_headings_present", False):
        score += 8
    if features.get("plain_text_readable", False):
        score += 8
    if features.get("date_ranges_present", False):
        score += 5
    if features.get("skills_present", False):
        score += 5
    if features.get("quantified_achievements_present", False):
        score += 6

    country = (target_country or "").lower()
    status = (user_status or "").lower()

    # Migrating users need stronger country adaptation.
    if "migrate" in status or "abroad" in status:
        score -= 5

    # Local language/country expectations: not exact, but useful early signal.
    cv_raw = (st.session_state.get("cv_text", "") or "").lower()
    if country in {"germany", "austria", "switzerland"}:
        if "german" in cv_raw or "deutsch" in cv_raw:
            score += 5
        else:
            score -= 6
    if country in {"united kingdom", "united states", "canada", "australia", "ireland"}:
        if "english" in cv_raw:
            score += 4

    if not features.get("work_experience_present", False):
        score -= 8
    if int(features.get("word_count", 0)) < 180:
        score -= 6

    return max(25, min(score, 92))

def analyze_resume_dashboard_stable(cv_text: str, force_refresh: bool = False):
    cv_key = make_cv_hash(cv_text, st.session_state.country)
    fallback_cache = build_rule_based_dashboard_cache(cv_text)

    if not force_refresh and cv_key in st.session_state.dashboard_cache:
        cached = st.session_state.dashboard_cache[cv_key]
        apply_dashboard_cache(cached)
        return

    prompt = f"""
Analyze this CV like a senior international career advisor and return ONLY valid JSON.
Do not add markdown, explanations, or code fences.

The analysis must be personalized to the user status and target country.
Do not give generic strengths like "good communication" unless the CV actually shows it.

JSON format:
{{
  "professional_summary": "short paragraph",
  "current_or_likely_role": "role name",
  "key_skills": ["skill1", "skill2", "skill3", "skill4", "skill5"],
  "suggested_roles": ["role1", "role2", "role3"],
  "best_fit_countries": ["Country - specific reason based on CV evidence", "Country - specific reason based on CV evidence", "Country - specific reason based on CV evidence"],
  "country_cv_readiness": "short country-specific verdict on whether this CV fits the target country",
  "status_guidance": "short advice based on the user's career status",
  "next_actions": ["action1", "action2", "action3", "action4"],
  "strengths": ["specific strength from CV", "specific strength from CV", "specific strength from CV", "specific strength from CV"],
  "improvements": ["specific improvement", "specific improvement", "specific improvement", "specific improvement"],
  "next_best_actions": ["action1", "action2", "action3"],
  "country_readiness_notes": ["note1", "note2", "note3"]
}}

Rules:
- Be concise, practical, and specific.
- Consider the user's status from onboarding.
- Include next_best_actions that tell the user exactly what to do next.
- Include country_readiness_notes for the chosen country.
- For best_fit_countries, suggest only the top 3 countries where this CV/profile is likely to be competitive.
- Do not give generic country names. Each reason must mention a specific CV signal such as role background, language, tools, domain, education, or transferable experience.
- Include the selected target country if it is realistic; otherwise explain why another market fits better.
- Keep each country reason under 18 words.
- Do not generate any numeric score.
- Do not add keys outside this JSON structure.
- Return valid JSON only.
- Keep the JSON keys exactly in English, but write all JSON values in the selected AI response language.
- Do not mix languages inside the JSON values.

Country context: {st.session_state.country}
User status: {st.session_state.get('user_status', 'Not specified')}
Career goal: {st.session_state.get('career_goal', 'Not specified')}

CV:
{cv_text}
"""
    result = run_ai_prompt(prompt, force_language=st.session_state.get("preferred_language", "English"), json_mode=True)

    if result.startswith("ERROR:"):
        st.session_state.dashboard_cache[cv_key] = fallback_cache
        apply_dashboard_cache(fallback_cache)
        st.session_state.dashboard_cv_hash = cv_key
        return

    try:
        parsed = safe_json_loads(result)
    except Exception:
        st.session_state.dashboard_cache[cv_key] = fallback_cache
        apply_dashboard_cache(fallback_cache)
        st.session_state.dashboard_cv_hash = cv_key
        return

    features = analyze_cv_text_features(cv_text)

    cached = {
        "profile_summary": parsed.get("professional_summary", "").strip(),
        "current_role_detected": parsed.get("current_or_likely_role", "").strip(),
        "key_skills_detected": parsed.get("key_skills", []),
        "suggested_roles_detected": parsed.get("suggested_roles", []),
        "best_fit_countries_detected": parsed.get("best_fit_countries", []),
        "country_cv_readiness": parsed.get("country_cv_readiness", ""),
        "status_guidance": parsed.get("status_guidance", ""),
        "next_actions_detected": parsed.get("next_actions", []),
        "resume_strengths": parsed.get("strengths", []),
        "resume_improvements": parsed.get("improvements", []),
        "next_best_actions_detected": parsed.get("next_best_actions", []),
        "country_readiness_notes_detected": parsed.get("country_readiness_notes", []),
        "country_readiness_score_value": calculate_country_readiness_score(features, st.session_state.get("migration_country") or st.session_state.country, st.session_state.get("user_status", "")),
        "cv_profile_raw": json.dumps({"ai_extract": parsed, "text_features": features}, indent=2),
        "cv_score_value": calculate_resume_score(features),
        "ats_score_value": calculate_ats_score(features),
    }

    st.session_state.dashboard_cache[cv_key] = cached
    apply_dashboard_cache(cached)
    st.session_state.dashboard_cv_hash = cv_key

def apply_dashboard_cache(cached: Dict):
    st.session_state.profile_summary = cached.get("profile_summary", "")
    st.session_state.current_role_detected = cached.get("current_role_detected", "")

    skills = cached.get("key_skills_detected", [])
    roles = cached.get("suggested_roles_detected", [])
    strengths = cached.get("resume_strengths", [])
    improvements = cached.get("resume_improvements", [])
    best_fit_countries = cached.get("best_fit_countries_detected", [])
    next_best_actions = cached.get("next_best_actions_detected", [])
    country_readiness_notes = cached.get("country_readiness_notes_detected", [])
    next_actions = cached.get("next_actions_detected", [])

    st.session_state.key_skills_detected = "\n".join([f"- {x}" for x in skills]) if isinstance(skills, list) else str(skills)
    st.session_state.suggested_roles_detected = "\n".join([f"- {x}" for x in roles]) if isinstance(roles, list) else str(roles)
    st.session_state.resume_strengths = "\n".join([f"- {x}" for x in strengths]) if isinstance(strengths, list) else str(strengths)
    st.session_state.resume_improvements = country_aware_resume_improvements("\n".join([f"- {x}" for x in improvements]) if isinstance(improvements, list) else str(improvements))
    st.session_state.best_fit_countries_detected = "\n".join([f"- {x}" for x in best_fit_countries]) if isinstance(best_fit_countries, list) else str(best_fit_countries)
    st.session_state.next_best_step_result = "\n".join([f"- {x}" for x in next_best_actions]) if isinstance(next_best_actions, list) else str(next_best_actions)
    st.session_state.country_readiness_notes = "\n".join([f"- {x}" for x in country_readiness_notes]) if isinstance(country_readiness_notes, list) else str(country_readiness_notes)

    st.session_state.cv_profile_raw = cached.get("cv_profile_raw", "")
    st.session_state.cv_score_value = cached.get("cv_score_value")
    st.session_state.ats_score_value = cached.get("ats_score_value")
    st.session_state.country_readiness_score_value = cached.get("country_readiness_score_value")

def reset_onboarding():
    preserve = {
        "request_count": st.session_state.request_count,
        "first_request_time": st.session_state.first_request_time,
        "ui_language": st.session_state.ui_language,
        "response_language": st.session_state.response_language,
        "dashboard_cache": st.session_state.dashboard_cache,
        "geo_country_suggestion": st.session_state.get("geo_country_suggestion", "Germany"),
        "geo_language_suggestion": st.session_state.get("geo_language_suggestion", "English"),
    }
    for key in list(st.session_state.keys()):
        del st.session_state[key]

    for key, value in defaults.items():
        st.session_state[key] = value

    for key, value in preserve.items():
        st.session_state[key] = value

    st.session_state.page = "onboarding"
    st.session_state.onboarding_complete = False

def set_new_resume_and_refresh(new_resume_text: str):
    st.session_state.cv_text = new_resume_text.strip()

    st.session_state.profile_summary = ""
    st.session_state.current_role_detected = ""
    st.session_state.key_skills_detected = ""
    st.session_state.suggested_roles_detected = ""
    st.session_state.best_fit_countries_detected = ""
    st.session_state.next_actions_detected = ""
    st.session_state.country_cv_readiness = ""
    st.session_state.status_guidance = ""
    st.session_state.cv_profile_raw = ""
    st.session_state.cv_score_value = None
    st.session_state.ats_score_value = None
    st.session_state.resume_strengths = ""
    st.session_state.resume_improvements = ""

    analyze_resume_dashboard_stable(st.session_state.cv_text, force_refresh=True)





def build_rule_based_dashboard_cache(cv_text: str) -> Dict:
    """Create honest dashboard scores and basic insights without waiting for AI.
    This prevents empty dashboard cards when the AI analysis fails or JSON parsing breaks.
    """
    features = analyze_cv_text_features(cv_text or "")
    resume_score = calculate_resume_score(features)
    ats_score = calculate_ats_score(features)
    country_score = calculate_country_readiness_score(
        features,
        st.session_state.get("migration_country") or st.session_state.get("country", ""),
        st.session_state.get("user_status", ""),
    )

    strengths = []
    improvements = []
    if features.get("contact_info_present"):
        strengths.append("Contact information is present")
    else:
        improvements.append("Add clear contact information")
    if features.get("skills_present"):
        strengths.append("Skills section is visible")
    else:
        improvements.append("Add a dedicated skills section")
    if features.get("work_experience_present"):
        strengths.append("Work experience section is included")
    else:
        improvements.append("Add a clear work experience section")
    if features.get("bullet_points_present"):
        strengths.append("Uses bullet points for readability")
    else:
        improvements.append("Use bullet points under each role or project")
    if features.get("quantified_achievements_present"):
        strengths.append("Includes measurable achievements")
    else:
        improvements.append("Add numbers such as tickets handled, projects, users, revenue, or percentage improvements")
    if features.get("standard_headings_present"):
        strengths.append("Uses standard resume headings")
    else:
        improvements.append("Use standard headings like Summary, Experience, Skills, Education")
    if features.get("date_ranges_present"):
        strengths.append("Includes dates or experience duration")
    else:
        improvements.append("Add dates for education and work experience")

    while len(strengths) < 3:
        strengths.append("Resume text was successfully read")
    while len(improvements) < 3:
        improvements.append("Add more specific role keywords for your target job")

    word_count = int(features.get("word_count", 0) or 0)
    profile_summary = (
        f"WorkZo read about {word_count} words from your resume. "
        f"The current resume looks {score_band(resume_score).lower()} and needs clearer proof, structure, or role targeting."
    )

    cached = {
        "profile_summary": profile_summary,
        "current_role_detected": "Not detected yet",
        "key_skills_detected": [],
        "suggested_roles_detected": [],
        "best_fit_countries_detected": [],
        "country_cv_readiness": f"{score_band(country_score)} for {st.session_state.get('migration_country') or st.session_state.get('country', 'selected country')}",
        "status_guidance": "Improve the weakest resume sections first, then analyze one target job description.",
        "next_actions_detected": [
            "Fix missing resume sections first",
            "Add measurable achievements",
            "Paste a target job description in Job Assist",
        ],
        "resume_strengths": strengths[:4],
        "resume_improvements": improvements[:4],
        "next_best_actions_detected": [],
        "country_readiness_notes_detected": [],
        "country_readiness_score_value": country_score,
        "cv_profile_raw": json.dumps({"rule_based_features": features}, indent=2),
        "cv_score_value": resume_score,
        "ats_score_value": ats_score,
    }
    return cached


def ensure_dashboard_analysis() -> None:
    """Guarantee dashboard never shows empty scores/insights after a resume is uploaded."""
    cv_text = str(st.session_state.get("cv_text", "") or "").strip()
    if not cv_text:
        return
    if st.session_state.get("cv_score_value") is not None and st.session_state.get("ats_score_value") is not None and st.session_state.get("profile_summary"):
        return
    cached = build_rule_based_dashboard_cache(cv_text)
    apply_dashboard_cache(cached)
    try:
        st.session_state.dashboard_cache[make_cv_hash(cv_text, st.session_state.get("country", ""))] = cached
    except Exception:
        pass

def render_metric_card(label: str, value: str, foot: str = ""):
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-foot">{foot}</div>
    </div>
    """, unsafe_allow_html=True)


def render_feature_tile(icon: str, title: str, copy: str):
    st.markdown(f"""
    <div class="feature-tile">
        <div style="font-size:1.45rem; margin-bottom:8px;">{icon}</div>
        <div class="feature-title">{title}</div>
        <div class="feature-copy">{copy}</div>
    </div>
    """, unsafe_allow_html=True)


def generate_next_best_steps(cv_text: str, country_name: str, current_role: str, suggested_roles: str, user_status: str = "", career_goal: str = "") -> str:
    prompt = f"""
Country: {country_name}
User status: {user_status or 'Not specified'}
Career goal: {career_goal or 'Not specified'}
Current role: {current_role or 'Not clear'}
Suggested roles:
{suggested_roles}
Candidate CV:
{cv_text}

Create a personalized action center. Adapt the advice based on the user status:
st.info("⚠️ WorkZo AI is currently in Beta. Some results may not be perfect yet. Your feedback helps improve the tool.")

- Fresh graduate: portfolio projects, internships, entry-level search, skills proof.
- Career changer: transferable skills, bridge role, portfolio, realistic job titles.
- Migrating to another country: country CV format, language expectations, local job titles, application documents.
- Returning after career break: confidence positioning, gap explanation, restart strategy.
- Experienced professional: positioning, seniority, specialization, leadership proof.

Return in this exact structure:
1. Resume Readiness Verdict
2. Best Immediate Goal
3. This Week's 3 Priority Actions
4. Best Role Cluster to Target
5. One Resume Fix That Will Help Most
6. One Skill or Proof to Build Next
7. Country-Specific Advice
8. One Message to Send Today

Keep it practical, specific, and motivating.
"""
    result = run_ai_prompt(prompt)
    return result

# =========================================================
# HEADER
# =========================================================
def image_to_data_uri(path: str) -> str:
    try:
        if path and os.path.exists(path):
            encoded = base64.b64encode(Path(path).read_bytes()).decode("utf-8")
            return f"data:image/png;base64,{encoded}"
    except Exception:
        return ""
    return ""

def render_workzo_header() -> None:
    """Premium SaaS-style product header for WorkZo."""
    logo_src = image_to_data_uri(ICON_PATH) or image_to_data_uri(LOGO_PATH)
    logo_html = f'<img src="{logo_src}" class="workzo-logo" alt="WorkZo AI logo">' if logo_src else '<div class="workzo-logo-fallback">🚀</div>'
    subtitle = html.escape(txt("title"))
    st.markdown(f"""
    <div class="workzo-header">
        <div class="workzo-brand">
            {logo_html}
            <div>
                <div class="workzo-title">WorkZo <span>AI</span></div>
                <div class="workzo-subtitle">{subtitle}</div>
            </div>
        </div>
        <div class="workzo-beta">BETA</div>
    </div>
    """, unsafe_allow_html=True)

maybe_scroll_to_top()
render_workzo_header()

def show_landing_page():
    """First page: product introduction before onboarding."""
    maybe_scroll_to_top()
    st.markdown("""
    <div class="workzo-landing-hero">
      <div class="workzo-kicker">AI CAREER WORKSPACE</div>
      <div class="workzo-landing-title">WorkZo AI helps you move from CV to application with less guessing.</div>
      <div class="workzo-landing-copy">WorkZo helps job seekers upload or create a CV, understand job descriptions, improve resumes, prepare for interviews, and apply with more confidence — all in one guided career workspace.</div>
      <div class="workzo-landing-steps">
        <div class="workzo-landing-step"><span>Step 1</span>Add details</div>
        <div class="workzo-landing-step"><span>Step 2</span>Score CV + ATS</div>
        <div class="workzo-landing-step"><span>Step 3</span>Improve or roast</div>
        <div class="workzo-landing-step"><span>Step 4</span>Find + understand jobs</div>
        <div class="workzo-landing-step"><span>Step 5</span>Prepare + apply</div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("🚀 Start now", type="primary", use_container_width=True, key="landing_start_now"):
            st.session_state.page = "onboarding"
            st.session_state.nav_page = "dashboard"
            request_scroll_to_top()
            st.rerun()
    with c2:
        if st.button("I already added my CV", use_container_width=True, key="landing_go_dashboard"):
            if st.session_state.get("onboarding_complete"):
                sync_navigation_state("dashboard")
            else:
                st.session_state.page = "onboarding"
                request_scroll_to_top()
            st.rerun()
    st.markdown("### Built as one connected workspace")
    st.markdown("""
- **One profile:** your CV, country, language, job description, scores, and edits stay connected in this session.
- **Change once, update everywhere:** CV edits can refresh Dashboard, ATS score, Job Assist, Prepare for Job, and Work-O-Bot context.
- **Future login/subscription-ready:** later, this same workspace can be saved to a database so users can return, edit, rescore, and continue applications.
    """)

# =========================================================
# ONBOARDING
# =========================================================

POPULAR_SKILLS = [
    "Python", "SQL", "Power BI", "Tableau", "Excel", "Data Analysis", "Pandas", "Machine Learning",
    "Customer Support", "Technical Support", "Troubleshooting", "CRM", "SaaS", "IT Support", "Help Desk",
    "Project Management", "Communication", "Problem Solving", "Sales", "Marketing", "SEO", "Java",
    "JavaScript", "React", "AWS", "Azure", "Google Cloud", "Docker", "Linux", "System Administration",
    "Testing", "Agile", "Scrum", "Leadership", "Public Speaking", "Photoshop", "Figma", "Canva"
]
EDUCATION_LEVELS = [
    "", "High School", "Diploma", "Bachelor's Degree", "Master's Degree", "PhD",
    "Bootcamp", "Vocational Training", "Certificate Course", "Self-taught"
]

def render_resume_choice_card(icon: str, title: str, desc: str, active: bool = False):
    active_class = " active" if active else ""
    st.markdown(f"""
    <div class="workzo-action-card{active_class}">
        <div class="workzo-action-title">{html.escape(icon)} {html.escape(title)}</div>
        <div class="workzo-action-copy">{html.escape(desc)}</div>
    </div>
    """, unsafe_allow_html=True)

def show_onboarding():
    maybe_scroll_to_top()
    st.subheader(txt("onboarding_title"), help=txt("app_info_help"))
    st.caption(txt("onboarding_subtitle"))

    language_list = language_options if language_options else ["English", "German", "Dutch"]
    lang_default = st.session_state.get("preferred_language", "English")
    if lang_default not in language_list:
        lang_default = "English" if "English" in language_list else language_list[0]

    preferred_language = st.selectbox(
        txt("preferred_language"),
        language_list,
        index=language_list.index(lang_default),
        key="onboarding_preferred_language",
        help=txt("language_help")
    )
    set_single_preferred_language(preferred_language)

    country_index = country_options.index(st.session_state.country) if st.session_state.country in country_options else 0
    country = st.selectbox(
        txt("country"),
        country_options,
        index=country_index,
        key="onboarding_country",
        help=f"{txt('detected_country_hint')}: {geo_country_default}"
    )

    status_options = [
        txt("select_optional"),
        txt("student_thesis_internship"),
        txt("local_jobseeker"),
        txt("fresh_graduate"),
        txt("career_changer"),
        txt("migrant"),
        txt("experienced"),
        txt("returning"),
    ]
    status_display = st.selectbox(
        txt("user_status"),
        status_options,
        index=0,
        key="onboarding_user_status",
        format_func=lambda value: value,
        help=txt("status_help")
    )
    status_map = {
        txt("student_thesis_internship"): STUDENT_STATUS_INTERNAL,
        txt("local_jobseeker"): "Looking for jobs locally",
        txt("fresh_graduate"): "Fresh graduate / entry level",
        txt("career_changer"): "Career changer",
        txt("migrant"): "Planning to migrate / applying abroad",
        txt("experienced"): "Experienced professional",
        txt("returning"): "Returning after a career break",
    }
    user_status = "" if status_display == txt("select_optional") else status_map.get(status_display, status_display).strip()

    migration_country = ""
    if "migrate" in user_status.lower() or "abroad" in user_status.lower():
        migration_default = st.session_state.get("migration_country") or st.session_state.get("country") or "Germany"
        migration_index = country_options.index(migration_default) if migration_default in country_options else 0
        migration_country = st.selectbox(
            txt("migration_country"),
            country_options,
            index=migration_index
        )

    st.markdown(f"### {txt('resume_input')}")
    st.caption(txt("resume_choice_caption"))

    if "cv_mode" not in st.session_state:
        st.session_state.cv_mode = ""

    st.markdown(
        f"<div class='workzo-mini-note'>ℹ️ {html.escape(txt('privacy_short'))}</div>",
        unsafe_allow_html=True
    )

    c_upload, c_create, c_linkedin = st.columns(3)
    with c_upload:
        render_resume_choice_card("📄", txt("upload_cv_title"), txt("upload_cv_desc"), st.session_state.get("cv_mode") == "Upload CV")
        if st.button(txt("select_upload"), key="choose_upload_cv", use_container_width=True):
            st.session_state.cv_mode = "Upload CV"
            st.rerun()
    with c_create:
        render_resume_choice_card("✍️", txt("create_cv_title"), txt("create_cv_desc"), st.session_state.get("cv_mode") == "Create CV")
        if st.button(txt("select_create"), key="choose_create_cv", use_container_width=True):
            st.session_state.cv_mode = "Create CV"
            st.rerun()
    with c_linkedin:
        render_resume_choice_card("🔗", txt("linkedin_cv_title"), txt("linkedin_cv_desc"), st.session_state.get("cv_mode") == "LinkedIn")
        if st.button(txt("select_linkedin"), key="choose_linkedin_cv", use_container_width=True):
            st.session_state.cv_mode = "LinkedIn"
            st.rerun()

    cv_mode = st.session_state.get("cv_mode", "")

    if not cv_mode:
        st.info(txt("choose_resume_continue"))
        return

    if cv_mode == "Upload CV":
        uploaded_direct = st.file_uploader(
            txt("upload_cv_instruction"),
            type=["pdf", "txt"],
            key="upload_cv_direct",
            label_visibility="collapsed"
        )
        if uploaded_direct is not None:
            st.session_state.uploaded_file_direct = uploaded_direct
            st.success(ui_label("CV uploaded successfully. You can continue to the dashboard."))

    with st.form("onboarding_form_v49"):
        cv_text_input = ""
        full_name = ""
        email = ""
        phone = ""
        location = ""
        summary = ""
        skills = ""
        experience = ""
        projects = ""
        certifications = ""
        education = ""
        languages = ""
        extra_info = ""
        linkedin_url = ""
        linkedin_notes = ""
        target_role = ""

        if cv_mode == "Upload CV":
            uploaded_file = st.session_state.get("uploaded_file_direct")

            if uploaded_file is not None:
                if uploaded_file.size > 5 * 1024 * 1024:
                    st.error(txt("file_too_large"))
                elif uploaded_file.type == "text/plain":
                    cv_text_input = organize_cv_for_display(uploaded_file.read().decode("utf-8", errors="ignore"))
                elif uploaded_file.type == "application/pdf":
                    try:
                        cv_text_input = organize_cv_for_display(extract_pdf_text(uploaded_file))
                    except Exception as e:
                        st.error(f"{txt('pdf_read_error')}: {e}")
                else:
                    st.error(txt("unsupported_file"))
            else:
                st.caption(ui_label("Choose a PDF or TXT file above to continue."))

        elif cv_mode == "LinkedIn":
            st.markdown(f"#### {txt('linkedin_cv_title')}")
            st.caption(txt("linkedin_instruction"))
            linkedin_url = st.text_input(txt("linkedin_profile_link"), placeholder="https://www.linkedin.com/in/your-profile")
            linkedin_notes = st.text_area(
                txt("linkedin_extra_details"),
                placeholder="Example: About: customer support engineer with SaaS experience. Experience: Zoho, 4 years, ticket support, product troubleshooting. Skills: SQL, Python, CRM.",
                height=160
            )
            target_role = st.text_input(txt("target_role_optional"), placeholder="Example: Data Analyst, IT Support Specialist, Customer Success Manager")
            if linkedin_url.strip() or linkedin_notes.strip() or target_role.strip():
                cv_text_input = f"""
LinkedIn Profile Link: {linkedin_url}
Target Role: {target_role}
LinkedIn / Profile Notes:
{linkedin_notes}
""".strip()

        else:
            st.markdown(f"#### {txt('guided_cv_builder')}")
            st.caption(txt("guided_cv_caption"))
            st.caption(f"{txt('generated_language_note')}: {preferred_language}")

            c1, c2 = st.columns(2)
            with c1:
                full_name = st.text_input(txt("full_name"), placeholder="Example: Alex Morgan")
                email = st.text_input(txt("email"), placeholder="Example: alex.morgan@email.com")
                phone = st.text_input(txt("phone"), placeholder="Example: +1 555 123 4567")
                location = st.text_input(txt("location"), placeholder="Example: Toronto, Canada")
            with c2:
                target_role = st.text_input(txt("target_role_optional"), placeholder="Example: Data Analyst / IT Support Specialist")
                education_level = st.selectbox(txt("education_level"), EDUCATION_LEVELS, index=0, key="onboarding_education_level")
                selected_skills = st.multiselect(txt("suggested_skills"), POPULAR_SKILLS, key="onboarding_suggested_skills")
                languages = st.text_area(txt("languages_label"), placeholder="Example: English fluent, French intermediate, Portuguese native")

            summary = st.text_area(txt("summary"), placeholder="Example: Customer support professional with SaaS experience, interested in data and technology roles.")
            skills = st.text_area(txt("skills"), placeholder="Example: SQL, Excel, Python, customer support, problem solving, CRM tools")
            if selected_skills:
                skills = ", ".join(dict.fromkeys([x.strip() for x in (skills.split(",") if skills else [])] + selected_skills))
            experience = st.text_area(txt("experience"), placeholder="Example: Technical Support Associate, ABC Software, 2020–2024 — handled customer tickets and troubleshooting.")
            projects = st.text_area(txt("projects_label"), placeholder="Example: Built a dashboard to track monthly sales and customer trends.")
            certifications = st.text_area(txt("cert_courses"), placeholder="Example: Google Data Analytics Certificate, Excel Advanced, AWS basics")
            education = st.text_area(txt("education"), placeholder="Example: Bachelor of Computer Science, University of Toronto, 2020–2024")
            if education_level and education_level not in education:
                education = f"{education}\nEducation level: {education_level}".strip()
            extra_info = st.text_area(txt("extra_cv_info"), placeholder="Example: Target role: Junior Data Analyst. Open to remote/hybrid roles. Prefer English-speaking teams.")
            if target_role and target_role not in extra_info:
                extra_info = f"Target role: {target_role}\n{extra_info}".strip()

            if any([full_name.strip(), email.strip(), phone.strip(), location.strip(), summary.strip(), skills.strip(), experience.strip(), projects.strip(), certifications.strip(), education.strip(), languages.strip(), extra_info.strip()]):
                cv_text_input = build_created_cv_text(
                    full_name, email, phone, location, summary, skills, experience, education, projects, certifications, languages, extra_info
                )

        submitted = st.form_submit_button(txt("continue"))

        if submitted:
            track_button_click("Continue to Dashboard", "Onboarding", {"cv_mode": cv_mode, "selected_status": user_status})
            if not country:
                st.warning(txt("warn_country"))
                return

            if cv_mode == "Upload CV":
                if not cv_text_input.strip():
                    st.warning(txt("warn_upload_cv"))
                    return
            else:
                if cv_mode == "Create CV" and not full_name.strip():
                    st.warning(txt("warn_full_name"))
                    return
                if not cv_text_input.strip():
                    st.warning("Please enter at least a few details so WorkZo can build your CV.")
                    return

                with st.spinner("Creating your CV draft with AI..."):
                    ai_cv = generate_cv_from_user_details(cv_text_input, migration_country if migration_country else country, user_status)
                    if ai_cv and not ai_cv.startswith("ERROR:"):
                        st.session_state.created_cv_ai_output = ai_cv
                        cv_text_input = ai_cv

            st.session_state.country = country
            st.session_state.user_status = user_status
            st.session_state.migration_country = migration_country if migration_country else country
            st.session_state.cv_mode = cv_mode
            if cv_mode == "Upload CV":
                st.session_state.raw_cv_extraction = cv_text_input
                with st.spinner("Structuring your CV into clean sections..."):
                    cv_text_input = build_clean_cv_from_messy_extraction(cv_text_input, st.session_state.migration_country, user_status)
                st.session_state.structured_cv_profile = cv_text_input
            st.session_state.cv_text = clean_cv_text(cv_text_input)
            track_event("cv_ready", "Onboarding", {"cv_mode": cv_mode, "user_status": user_status, "target_country": st.session_state.get("migration_country", country)})
            st.session_state.onboarding_complete = True
            sync_navigation_state("dashboard")

            with st.spinner("Reading your resume and preparing dashboard..."):
                analyze_resume_dashboard_stable(st.session_state.cv_text, force_refresh=True)

            request_scroll_to_top()
            st.session_state.nav_page = "dashboard"
            st.rerun()

# =========================================================
# =========================================================
# WORK-O-BOT
# =========================================================
def workobot_intro_message() -> str:
    return """Hi, I'm Work-O-Bot 🤖

I can help you with:
• CV improvement
• Interview preparation
• Job search strategy
• Skill gap analysis
• Career change guidance
• Work-related language practice

Ask me anything about your career."""


def workobot_context_snapshot() -> str:
    """Small private context packet so Work-O-Bot can answer like a personalized career coach."""
    cv_text = st.session_state.get("cv_text", "") or st.session_state.get("cv_profile_raw", "") or ""
    cv_excerpt = cv_text[:3500] if cv_text else "No CV text loaded."
    try:
        target_country = get_advice_country()
    except Exception:
        target_country = st.session_state.get("migration_country", st.session_state.get("country", ""))
    return f"""
User profile context:
- Current country: {st.session_state.get('country', '')}
- Target market / advice country: {target_country}
- Career status: {st.session_state.get('user_status', '')}
- Preferred language: {st.session_state.get('preferred_language', 'English')}
- Detected role: {st.session_state.get('current_role_detected', '')}
- Detected skills: {st.session_state.get('key_skills_detected', '')}
- Suggested roles: {st.session_state.get('suggested_roles_detected', '')}
- Resume score: {st.session_state.get('cv_score_value', '')}
- ATS score: {st.session_state.get('ats_score_value', '')}
- Latest job analysis available: {'Yes' if st.session_state.get('latest_job_analysis') else 'No'}
- Latest CV analysis available: {'Yes' if st.session_state.get('latest_cv_analysis') else 'No'}

CV / profile excerpt:
{cv_excerpt}
""".strip()


def infer_workobot_intent(user_message: str) -> str:
    text = (user_message or "").lower()
    if any(x in text for x in ["interview", "mock", "question", "answer", "vorstellung", "gespräch"]):
        return "Interview coach"
    if any(x in text for x in ["cv", "resume", "lebenslauf", "ats", "summary", "bullet"]):
        return "CV coach"
    if any(x in text for x in ["german", "deutsch", "b1", "b2", "language", "sprechen"]):
        return "Work-language coach"
    if any(x in text for x in ["skill", "gap", "learn", "course", "roadmap"]):
        return "Skill gap strategist"
    if any(x in text for x in ["email", "linkedin", "message", "hr", "recruiter", "reply"]):
        return "Career communication coach"
    if any(x in text for x in ["job", "apply", "application", "salary", "role", "career"]):
        return "Job search strategist"
    return "General career coach"


def run_workobot(user_message: str, mode: str = "Auto"):
    if not can_make_request():
        return "I’m sorry, the hourly AI usage limit has been reached. Please try again later."

    register_request()
    answer_lang = normalize_answer_language(st.session_state.get("preferred_language", "English"))
    intent = infer_workobot_intent(user_message)
    model_name = os.getenv("WORKZO_AI_MODEL") or get_streamlit_secret("WORKZO_AI_MODEL", "gpt-4o-mini")

    system_prompt = f"""
You are Work-O-Bot, the AI career coach inside WorkZo AI.

Your role: {intent}

You help users with:
- job search strategy
- CV and ATS improvement
- interview preparation and mock interview feedback
- career change planning
- language practice for work
- skill gap analysis
- HR, recruiter, LinkedIn, and professional communication

User context:
{workobot_context_snapshot()}

Rules:
1. Be honest, practical, and supportive.
2. Use the user's CV/profile context when relevant.
3. Never invent experience, employers, dates, degrees, certifications, achievements, or language level.
4. If the user asks something vague, answer with a best first step and ask only one useful follow-up question.
5. Give structured answers with short headings and bullets.
6. When relevant, include exact examples the user can copy.
7. If the user practices an interview or language answer, give: corrected version, stronger version, and one practice task.
8. If the user asks about jobs, mention realistic role level, target-country fit, and risks.
9. If the user asks about CV, give safe-to-use wording and mark anything that should be used only if true.
10. End with one clear next best action.
11. Answer fully in {answer_lang}. Do not mix languages unless the user asks for translation or language practice.
""".strip()

    history = []
    for msg in st.session_state.get("workobot_messages", [])[-10:]:
        role = msg.get("role", "assistant")
        content = msg.get("content", "")
        if role in ["user", "assistant"] and content:
            history.append({"role": role, "content": content})

    messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": user_message}]

    try:
        res = client.chat.completions.create(
            model=model_name,
            temperature=0.25,
            messages=messages,
        )
        return (res.choices[0].message.content or "").strip()
    except Exception as e:
        return f"I couldn’t answer right now because the AI service is unavailable. ({type(e).__name__})"


def show_workobot():
    st.subheader(txt("workobot"))
    st.caption("Personal AI career coach based on your CV, country, target market, and selected language.")

    if "workobot_messages" not in st.session_state or not st.session_state.workobot_messages:
        st.session_state.workobot_messages = [{"role": "assistant", "content": workobot_intro_message()}]

    top_left, top_right = st.columns([5, 1])
    with top_left:
        st.markdown("### Try asking:")
    with top_right:
        if st.button("Clear Chat", key="workobot_clear_chat", use_container_width=True):
            st.session_state.workobot_messages = [{"role": "assistant", "content": workobot_intro_message()}]
            st.rerun()

    quick_prompts = get_country_specific_quick_prompts(st.session_state.get("country", ""))
    qp_cols = st.columns(4)
    quick_prompt = None
    for i, col in enumerate(qp_cols):
        label, prompt = quick_prompts[i]
        with col:
            if st.button(label, use_container_width=True, key=f"workobot_quick_{i}_{st.session_state.get('country','global')}"):
                quick_prompt = prompt

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    for msg in st.session_state.workobot_messages:
        with st.chat_message(msg.get("role", "assistant")):
            st.write(msg.get("content", ""))

    user_input = st.chat_input("Ask Work-O-Bot anything about your career...")
    final_input = quick_prompt or user_input

    if final_input:
        st.session_state.workobot_messages.append({"role": "user", "content": final_input})
        with st.chat_message("user"):
            st.write(final_input)

        with st.chat_message("assistant"):
            with st.spinner("Work-O-Bot is thinking..."):
                reply = run_workobot(final_input)
                st.write(reply)

        st.session_state.workobot_messages.append({"role": "assistant", "content": reply})

    st.markdown("---")
    st.caption("Work-O-Bot can use your uploaded CV/profile, chosen country, target market, and recent job/CV analysis to give more personalized guidance.")

def get_country_specific_quick_prompts(country_name: str):
    country = (country_name or "").strip().lower()

    if country == "germany":
        return [
            ("B1/B2 mock questions", "Give me a German B1/B2 mock test practice set with example questions and answers."),
            ("Career communication", "Help me improve my career communication with 3 examples relevant to Germany."),
            ("Skill gap help", "Based on my CV and the German market, what skill gap should I fix first?"),
            ("German for interviews", "Give me German interview questions and sample answers for my profile."),
        ]

    if country == "india":
        return [
            ("Interview questions", "Give me interview questions and strong sample answers for roles relevant to my profile in India."),
            ("HR communication", "Help me improve HR and recruiter communication with 3 examples relevant to India."),
            ("Skill gap help", "Based on my CV and the Indian market, what skill gap should I fix first?"),
            ("Job search plan", "Give me a practical interview and job search plan for my profile in India."),
        ]

    return [
        ("Interview questions", f"Give me interview questions and strong sample answers for roles relevant to my profile in {country_name}."),
        ("Career communication", f"Help me improve my career communication with 3 examples relevant to {country_name}."),
        ("Skill gap help", f"Based on my CV and the {country_name} market, what skill gap should I fix first?"),
        ("Job search plan", f"Give me a practical interview and job search plan for my profile in {country_name}."),
    ]

def extract_best_effort_cover_letter_sections(result: str):
    sections = numbered_sections_to_markdown(result)
    normalized = {k.strip().lower(): v.strip() for k, v in sections.items()}

    def first_match(candidates):
        for key, value in normalized.items():
            for candidate in candidates:
                if candidate in key and value:
                    return value
        return ""

    full_letter = first_match(["full cover letter", "cover letter", "letter"])
    short_email = first_match(["short email", "email version", "email"])
    tips = first_match(["customization tips", "tips", "customisation tips"])

    if not full_letter and sections:
        full_letter = next((v.strip() for v in sections.values() if v.strip()), "")

    return sections, full_letter, short_email, tips




# =========================================================
# VISUAL CV TEMPLATE PREVIEW
# =========================================================
def parse_cv_sections_for_template(cv_text: str) -> Dict[str, str]:
    """
    Lightweight parser to organize generated CV text into visual preview sections.
    It works best with the AI-generated CV draft but also handles plain text.
    """
    sections = {
        "header": "",
        "summary": "",
        "skills": "",
        "experience": "",
        "projects": "",
        "education": "",
        "certifications": "",
        "languages": "",
        "other": "",
    }

    text = clean_cv_text(normalize_resume_dates(cv_text))
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return sections

    sections["header"] = "\n".join(lines[:4])
    current = "summary"

    heading_map = {
        "summary": ["summary", "profile", "professional profile", "career objective", "objective"],
        "skills": ["skills", "core skills", "technical skills", "kenntnisse"],
        "experience": ["experience", "work experience", "professional experience", "berufserfahrung"],
        "projects": ["projects", "project", "projekte"],
        "education": ["education", "ausbildung", "academic"],
        "certifications": ["certification", "certifications", "courses", "training", "weiterbildung"],
        "languages": ["languages", "sprachen"],
    }

    bucket_lines = {k: [] for k in sections if k != "header"}

    for line in lines[4:]:
        normalized = re.sub(r"[^a-zA-Z ]", "", line).strip().lower()
        matched = False
        for key, labels in heading_map.items():
            if normalized in labels or any(normalized.startswith(label) for label in labels):
                current = key
                matched = True
                break
        if not matched:
            bucket_lines.setdefault(current, []).append(line)

    for key, vals in bucket_lines.items():
        sections[key] = "\n".join(vals).strip()

    return sections

def html_escape(text_value: str) -> str:
    return (text_value or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def protect_dates_for_html(escaped_line: str) -> str:
    """Keep dates such as 10/2018 - 01/2020 on one visual line in the CV preview."""
    date_pattern = r"(\b(?:\d{1,2}/\d{4}|\d{4})\s*-\s*(?:\d{1,2}/\d{4}|\d{4}|Present|Current|Heute|Now)\b)"
    return re.sub(date_pattern, r"<span class='cv-date'>\1</span>", escaped_line, flags=re.I)

def lines_to_html(text_value: str) -> str:
    normalized = normalize_resume_dates(text_value or "")
    lines = [html_escape(x.strip()) for x in normalized.splitlines() if x.strip()]
    if not lines:
        return "<p style='color:#64748b;'>—</p>"
    html = ""
    for line in lines:
        line = protect_dates_for_html(line)
        if line.startswith(("-", "•", "*")):
            html += f"<li>{line.lstrip('-•* ').strip()}</li>"
        else:
            html += f"<p>{line}</p>"
    if "<li>" in html:
        html = html.replace("<li>", "<ul><li>", 1)
        html = html[::-1].replace(">il/<", ">lu/<>il/<", 1)[::-1]
    return html


def resolve_template_style(template_name: str) -> str:
    """Map template names to visibly different preview/download layouts."""
    name = (template_name or "").lower()
    if any(x in name for x in ["career change", "pivot", "returning", "newcomer"]):
        return "Career Pivot"
    if any(x in name for x in ["graduate", "student", "intern", "thesis", "fresher", "stage", "werkstudent", "entry-level"]):
        return "Graduate Portfolio"
    if any(x in name for x in ["ats", "one-page", "one page", "minimal", "no photo"]):
        return "Minimal ATS"
    if any(x in name for x in ["modern", "portfolio", "netherlands", "dutch", "singapore"]):
        return "Creative Modern"
    if any(x in name for x in ["german", "lebenslauf", "austria", "swiss", "dach", "france", "french", "classique"]):
        return "German-Style Lebenslauf"
    if any(x in name for x in ["professional", "resume", "canadian", "canada", "australia", "uk", "us", "usa"]):
        return "Executive Slate"
    return "Minimal ATS"

def build_visual_cv_html(cv_text: str, template_name: str, target_country: str) -> str:
    style_key = resolve_template_style(template_name)
    data = parse_cv_sections_for_template(cv_text)
    header_lines = [x.strip() for x in data.get("header", "").splitlines() if x.strip()]
    name = header_lines[0] if header_lines else "Your Name"
    title = header_lines[1] if len(header_lines) > 1 else f"CV for {target_country}"
    contact = " · ".join(header_lines[2:]) if len(header_lines) > 2 else ""

    summary = lines_to_html(data.get("summary"))
    skills = lines_to_html(data.get("skills"))
    experience = lines_to_html(data.get("experience"))
    projects = lines_to_html(data.get("projects"))
    education = lines_to_html(data.get("education"))
    certifications = lines_to_html(data.get("certifications"))
    languages = lines_to_html(data.get("languages"))
    other = lines_to_html(data.get("other"))

    base_css = """
    <style>
      .cv-page {
        width: 794px;
        min-height: 1123px;
        margin: 0 auto 24px auto;
        background: white;
        color: #111827;
        box-shadow: 0 18px 50px rgba(0,0,0,0.35);
        border-radius: 8px;
        overflow: hidden;
        font-family: Arial, Helvetica, sans-serif;
      }
      .cv-page p { margin: 0 0 7px 0; line-height: 1.38; font-size: 13px; }
      .cv-page ul { margin: 0 0 8px 18px; padding: 0; }
      .cv-page li { font-size: 13px; margin-bottom: 5px; line-height: 1.35; }
      .cv-date { white-space: nowrap; display: inline-block; word-break: keep-all; overflow-wrap: normal; }
      .cv-section-title { font-size: 12px; letter-spacing: 1.4px; text-transform: uppercase; font-weight: 800; margin: 16px 0 8px; }
      .cv-small { color:#64748b; font-size:12px; }
      @media (max-width: 850px) {
        .cv-page { width: 100%; min-height: auto; border-radius: 0; }
      }
    </style>
    """

    if style_key in ["Executive Slate", "German-Style Lebenslauf"]:
        return base_css + f"""
        <div class="cv-page">
          <div style="padding:42px 46px 20px; border-bottom:4px solid #1f2937;">
            <div style="font-size:34px; font-weight:800; letter-spacing:1px;">{html_escape(name)}</div>
            <div style="font-size:15px; color:#334155; margin-top:6px;">{html_escape(title)}</div>
            <div class="cv-small" style="margin-top:10px;">{html_escape(contact)}</div>
          </div>
          <div style="display:grid; grid-template-columns: 36% 64%;">
            <aside style="background:#f1f5f9; padding:26px 28px; min-height:900px;">
              <div class="cv-section-title">Skills</div>{skills}
              <div class="cv-section-title">Languages</div>{languages}
              <div class="cv-section-title">Education</div>{education}
              <div class="cv-section-title">Certifications</div>{certifications}
            </aside>
            <main style="padding:26px 32px;">
              <div class="cv-section-title">Profile</div>{summary}
              <div class="cv-section-title">Experience</div>{experience}
              <div class="cv-section-title">Projects</div>{projects}
              <div class="cv-section-title">Additional</div>{other}
            </main>
          </div>
        </div>
        """

    if style_key == "Minimal ATS":
        return base_css + f"""
        <div class="cv-page" style="padding:46px 56px;">
          <div style="border-bottom:2px solid #e5e7eb; padding-bottom:14px;">
            <div style="font-size:31px; font-weight:800;">{html_escape(name)}</div>
            <div style="font-size:15px; margin-top:5px;">{html_escape(title)}</div>
            <div class="cv-small" style="margin-top:8px;">{html_escape(contact)}</div>
          </div>
          <div class="cv-section-title">Professional Summary</div>{summary}
          <div class="cv-section-title">Core Skills</div>{skills}
          <div class="cv-section-title">Professional Experience</div>{experience}
          <div class="cv-section-title">Projects</div>{projects}
          <div class="cv-section-title">Education</div>{education}
          <div class="cv-section-title">Certifications</div>{certifications}
          <div class="cv-section-title">Languages</div>{languages}
        </div>
        """

    if style_key == "Creative Modern":
        return base_css + f"""
        <div class="cv-page">
          <div style="background:linear-gradient(135deg,#2563eb,#14b8a6); color:white; padding:42px 46px;">
            <div style="font-size:35px; font-weight:900;">{html_escape(name)}</div>
            <div style="font-size:16px; margin-top:6px; opacity:.95;">{html_escape(title)}</div>
            <div style="font-size:12px; margin-top:10px; opacity:.9;">{html_escape(contact)}</div>
          </div>
          <div style="padding:30px 42px; display:grid; grid-template-columns: 1.2fr .8fr; gap:30px;">
            <main>
              <div class="cv-section-title" style="color:#2563eb;">Profile</div>{summary}
              <div class="cv-section-title" style="color:#2563eb;">Experience</div>{experience}
              <div class="cv-section-title" style="color:#2563eb;">Projects</div>{projects}
            </main>
            <aside style="border-left:1px solid #e5e7eb; padding-left:24px;">
              <div class="cv-section-title" style="color:#0f766e;">Skills</div>{skills}
              <div class="cv-section-title" style="color:#0f766e;">Education</div>{education}
              <div class="cv-section-title" style="color:#0f766e;">Certifications</div>{certifications}
              <div class="cv-section-title" style="color:#0f766e;">Languages</div>{languages}
            </aside>
          </div>
        </div>
        """

    if style_key == "Career Pivot":
        return base_css + f"""
        <div class="cv-page" style="padding:42px 50px;">
          <div style="background:#f8fafc; border-left:6px solid #7c3aed; padding:20px 24px; margin-bottom:22px;">
            <div style="font-size:32px; font-weight:900;">{html_escape(name)}</div>
            <div style="font-size:15px; color:#4c1d95; margin-top:6px;">{html_escape(title)}</div>
            <div class="cv-small" style="margin-top:8px;">{html_escape(contact)}</div>
          </div>
          <div class="cv-section-title" style="color:#7c3aed;">Career Change Profile</div>{summary}
          <div class="cv-section-title" style="color:#7c3aed;">Transferable + Target Skills</div>{skills}
          <div class="cv-section-title" style="color:#7c3aed;">Relevant Projects / Training</div>{projects}
          <div class="cv-section-title" style="color:#7c3aed;">Previous Experience Reframed</div>{experience}
          <div style="display:grid; grid-template-columns:1fr 1fr; gap:24px;">
            <div><div class="cv-section-title" style="color:#7c3aed;">Education</div>{education}</div>
            <div><div class="cv-section-title" style="color:#7c3aed;">Languages</div>{languages}</div>
          </div>
        </div>
        """

    # Graduate Portfolio
    return base_css + f"""
    <div class="cv-page">
      <div style="padding:38px 46px; border-bottom:1px solid #e5e7eb;">
        <div style="font-size:33px; font-weight:900;">{html_escape(name)}</div>
        <div style="font-size:15px; color:#0369a1; margin-top:6px;">{html_escape(title)}</div>
        <div class="cv-small" style="margin-top:8px;">{html_escape(contact)}</div>
      </div>
      <div style="padding:28px 42px;">
        <div class="cv-section-title" style="color:#0369a1;">Career Objective</div>{summary}
        <div class="cv-section-title" style="color:#0369a1;">Education</div>{education}
        <div class="cv-section-title" style="color:#0369a1;">Projects</div>{projects}
        <div class="cv-section-title" style="color:#0369a1;">Technical Skills</div>{skills}
        <div class="cv-section-title" style="color:#0369a1;">Experience</div>{experience}
        <div class="cv-section-title" style="color:#0369a1;">Certifications & Languages</div>{certifications}{languages}
      </div>
    </div>
    """


def get_cv_template_options(target_country: str, user_status: str) -> Dict[str, str]:
    """Return templates that are genuinely different by country expectations."""
    country = (target_country or "").strip().lower()
    status = (user_status or "").strip().lower()

    country_templates = {
        "germany": {
            "German Lebenslauf - Structured": "German-style CV: clear sections, reverse chronology, languages, education, skills, and optional professional photo/personal details only if the user chooses.",
            "German ATS - No Photo": "Modern German application CV without photo/date of birth; safer for international companies and online portals.",
            "German Student / Werkstudent CV": "Best for students, thesis roles, internships, Praktikum, Werkstudent, Bachelorarbeit or Masterarbeit applications.",
        },
        "austria": {
            "Austria Lebenslauf - Structured": "Austrian-style CV with clear chronology, education, experience, skills, and language levels.",
            "DACH ATS - No Photo": "Clean DACH-market CV for online applications and international employers.",
            "Austria Student / Internship CV": "Education-first CV for Praktikum, trainee, thesis and junior opportunities.",
        },
        "switzerland": {
            "Swiss Professional CV": "Structured Swiss CV with strong profile, reverse chronology, languages and skills; concise and formal.",
            "Swiss International ATS": "Clean no-photo ATS version for multinational Swiss companies.",
            "Swiss Student / Internship CV": "Student-friendly CV for internships, thesis roles and graduate programmes.",
        },
        "united states": {
            "US One-Page Resume": "US resume style: one page, no photo, no date of birth, impact bullets, keywords and measurable results.",
            "US ATS Resume": "ATS-first American resume for online applications with simple formatting and strong keyword alignment.",
            "US Entry-Level Resume": "Education/projects-first resume for students, new grads and early-career applicants.",
        },
        "united kingdom": {
            "UK Two-Page CV": "UK CV style: professional profile, key skills, reverse chronology, no photo and no personal data.",
            "UK ATS CV": "Clean UK CV for job boards and recruiters, focused on evidence, skills and achievements.",
            "UK Graduate CV": "Graduate-friendly UK CV focused on education, projects, placements and transferable skills.",
        },
        "canada": {
            "Canadian Professional Resume": "Balanced Canadian resume: no photo, no date of birth, achievement-focused, recruiter-friendly, usually 1–2 pages.",
            "Canadian ATS Keyword Resume": "Strict ATS Canadian resume with simple formatting, strong keywords, skills and measurable impact bullets.",
            "Canadian Newcomer / Career Pivot Resume": "Useful for immigrants, newcomers, and career changers: highlights transferable experience and Canadian-style wording.",
        },
        "india": {
            "India Professional Resume": "Indian market resume with profile, skills, projects, experience and education; suitable for job portals.",
            "India ATS Resume": "Clean Naukri/LinkedIn-style resume with keywords, tools, achievements and project proof.",
            "India Fresher Resume": "Fresher-focused resume emphasizing education, projects, internships, tools and certifications.",
        },
        "france": {
            "France CV - Classique": "French-style CV with Profil, Expérience, Formation, Compétences and Langues; concise and structured.",
            "France ATS - International": "No-photo international French-market CV for online applications and multinational companies.",
            "France Stage / Alternance CV": "Student CV for stage, alternance, apprentissage and junior roles.",
        },
        "netherlands": {
            "Netherlands CV - Direct": "Dutch-style CV: direct, skills-focused, concise, no unnecessary personal details.",
            "Netherlands ATS CV": "Clean ATS CV for Dutch job portals and international companies.",
            "Netherlands Internship / Stage CV": "Stage/afstudeerstage focused CV for students and graduates.",
        },
        "australia": {
            "Australia Resume": "Australian resume style: 2–3 pages if needed, no photo, achievement-focused and recruiter-friendly.",
            "Australia ATS Resume": "Clean ATS version for Seek/LinkedIn-style applications.",
            "Australia Graduate Resume": "Graduate-program format with education, projects, placements and skills.",
        },
        "singapore": {
            "Singapore Professional Resume": "Concise Singapore-market resume with profile, skills, experience and education.",
            "Singapore ATS Resume": "ATS-friendly format for job portals and multinational employers.",
            "Singapore Graduate Resume": "Graduate/internship-oriented format with education, projects, internships and tools.",
        },
        "portugal": {
            "Portugal CV - Europass Friendly": "Portuguese-market CV with clear profile, experience, education, skills and language levels.",
            "Portugal ATS CV": "Clean no-photo CV for Portuguese job portals and international companies.",
            "Portugal Internship CV": "Education/project-first CV for estágio, trainee and junior applications.",
        },
        "brazil": {
            "Brazil Professional CV": "Brazilian-market currículo with objective/profile, experience, education, skills and courses.",
            "Brazil ATS CV": "Simple keyword-rich CV for online applications and recruiters.",
            "Brazil Entry-Level CV": "Education, projects, internships, tools and courses first.",
        },
        "spain": {
            "Spain CV - Profesional": "Spanish-market CV with perfil, experiencia, formación, competencias and idiomas.",
            "Spain ATS CV": "Clean no-photo CV for portals and international employers.",
            "Spain Internship CV": "CV for prácticas, becario, trainee and junior roles.",
        },
        "italy": {
            "Italy CV - Professionale": "Italian-market CV with profile, experience, education, skills and languages.",
            "Italy ATS CV": "Clean ATS-friendly CV for Italian portals and international companies.",
            "Italy Internship CV": "Student format for tirocinio, stage and graduate roles.",
        },
        "united arab emirates": {
            "UAE Professional CV": "Gulf-market CV with clear summary, skills, experience, education and certifications.",
            "UAE ATS Resume": "ATS-friendly CV for UAE portals and multinational employers.",
            "UAE Career Pivot CV": "Highlights transferable experience, tools and measurable impact for market transitions.",
        },
        "uae": {
            "UAE Professional CV": "Gulf-market CV with clear summary, skills, experience, education and certifications.",
            "UAE ATS Resume": "ATS-friendly CV for UAE portals and multinational employers.",
            "UAE Career Pivot CV": "Highlights transferable experience, tools and measurable impact for market transitions.",
        },
    }

    templates = country_templates.get(country, {
        "International ATS CV": "Safe global CV format: no photo, no sensitive personal details, clean sections and ATS-friendly layout.",
        "International Professional CV": "General professional CV for global applications with summary, skills, experience, education and projects.",
        "International Graduate CV": "Student/new graduate version focused on education, projects, internships and certifications.",
    })

    def priority(item):
        name = item[0].lower()
        if any(x in status for x in ["student", "thesis", "internship", "graduate", "entry"]):
            return 0 if any(x in name for x in ["student", "intern", "graduate", "fresher", "stage", "werkstudent"]) else 1
        if any(x in status for x in ["career changer", "returning", "break"]):
            return 0 if any(x in name for x in ["ats", "newcomer", "international"]) else 1
        return 0

    return dict(sorted(templates.items(), key=priority))

def get_template_instructions(template_name: str, target_country: str) -> str:
    country = (target_country or "the selected country").strip()
    name = (template_name or "").lower()
    country_rules = get_country_cv_rules(country)
    base = f"""
Target country: {country}
STRICT COUNTRY RULE: This CV must be written for {country} only. Do not mention Germany, DACH, the USA, Canada, or any other country unless it is the selected target country.
Recommended length: about {country_rules.get('pages', 2)} page(s), unless the user's experience requires otherwise.
Recommended sections: {', '.join(country_rules.get('sections', []))}.
Photo commonly expected: {'Yes' if country_rules.get('photo') else 'No'}.
Date of birth/personal details commonly expected: {'Yes' if country_rules.get('dob') else 'No'}.
Important exclusions: {country_rules.get('avoid', 'Avoid sensitive personal details and do not invent information.')}.
"""

    if any(x in name for x in ["german", "lebenslauf", "austria", "swiss", "dach"]):
        return base + """
Use a DACH-style structured CV with clear chronology, languages, education and professional experience.
Keep it formal, concise and readable. Do not invent photo, date of birth, nationality, marital status or visa details.
"""
    if any(x in name for x in ["us", "canadian", "canada", "australia", "uk", "ats", "one-page", "one page"]):
        return base + """
Use a clean ATS-friendly resume/CV. Avoid photo, date of birth, marital status, nationality and other sensitive personal details.
Prioritize achievements, action verbs, measurable impact and job-specific keywords.
"""
    if any(x in name for x in ["france", "french", "classique"]):
        return base + """
Use a concise French-market structure: Profil, Expérience professionnelle, Formation, Compétences, Langues.
Keep wording direct and professional. Photo is optional; do not invent personal details.
"""
    if any(x in name for x in ["netherlands", "dutch"]):
        return base + """
Use a direct Dutch-market CV: concise profile, skills, work experience, education and languages.
Avoid unnecessary personal details and keep achievements easy to scan.
"""
    if any(x in name for x in ["india", "fresher"]):
        return base + """
Use an Indian job-portal friendly resume with strong skills, projects, education, experience and certifications.
For freshers, place education, projects and tools high on the page.
"""
    if any(x in name for x in ["student", "intern", "graduate", "stage", "werkstudent", "thesis"]):
        return base + """
Use a student/graduate CV format. Put education, thesis/internship/project work, tools, coursework and learning proof near the top.
Avoid senior-sounding claims unless the CV proves them.
"""

    return base + """
Use a safe international ATS CV structure with summary, skills, experience, education, projects, certifications and languages.
Do not invent any personal details, employers, dates or achievements.
"""

def build_template_sample_cv(template_name: str, target_country: str) -> str:
    style = resolve_template_style(template_name)
    if style == "Graduate Portfolio":
        return f"""
Alex Morgan
Graduate Data Analyst Candidate
alex.morgan@email.com · Toronto, ON · linkedin.com/in/alexmorgan

Career Objective
Entry-level candidate with hands-on coursework, portfolio projects and strong motivation to build practical experience in {target_country}.

Education
Bachelor of Science in Computer Science | Example University | 2024
- Relevant coursework: databases, statistics, programming and data visualization.

Projects
- Sales Dashboard Project: built a dashboard using SQL and Tableau to identify monthly trends.
- Customer Sentiment Project: analyzed comments with Python and presented findings clearly.

Technical Skills
- Python, SQL, Excel, Tableau, data cleaning, reporting

Experience
Student Assistant | Example Organization | 2023-2024
- Supported data entry, documentation and team coordination.

Languages
English - Professional
""".strip()
    if style == "Career Pivot":
        return f"""
Alex Morgan
Customer Support Specialist transitioning to Data Analyst
alex.morgan@email.com · Toronto, ON · linkedin.com/in/alexmorgan

Career Change Profile
Customer-facing technical professional moving into data analysis, combining problem-solving, stakeholder communication and practical analytics training.

Transferable + Target Skills
- Customer troubleshooting, stakeholder communication, SQL, Python, Excel, dashboards

Relevant Projects / Training
- Data Analysis Bootcamp: completed projects using Python, SQL and visualization tools.
- Support Metrics Analysis: analyzed ticket trends and created improvement recommendations.

Previous Experience Reframed
Technical Support Specialist | Example Company | 2020-2024
- Resolved technical issues, documented patterns and collaborated with product teams to improve user experience.

Education
Professional Certificate in Data Analytics | 2024

Languages
English - Professional
""".strip()
    if style == "Minimal ATS":
        return f"""
Alex Morgan
Data Analyst
alex.morgan@email.com · Toronto, ON · linkedin.com/in/alexmorgan

Professional Summary
Data-focused professional with experience in reporting, customer insights and process improvement. Skilled in turning business questions into clear analysis and practical recommendations.

Core Skills
- SQL, Python, Excel, Tableau, data cleaning, reporting, stakeholder communication

Professional Experience
Data Analyst | Example Company | 2022-2024
- Built weekly reports that helped the team monitor service performance and identify recurring issues.
- Cleaned and analyzed customer data to support process improvement decisions.

Projects
- Operations Dashboard: created KPI dashboard for ticket volume, resolution time and customer trends.

Education
Bachelor of Science | Example University | 2020

Certifications
Data Analytics Certificate | 2024

Languages
English - Professional
""".strip()
    return f"""
Alex Morgan
Data & Operations Professional
alex.morgan@email.com · Toronto, ON · linkedin.com/in/alexmorgan

Profile
Results-oriented professional with experience improving service processes, analyzing operational information and communicating insights to non-technical teams.

Skills
- Data analysis, SQL, Python, Excel, Tableau, documentation, customer communication

Experience
Operations Analyst | Example Company | 2021-2024
- Improved reporting clarity by organizing recurring metrics into a reusable dashboard.
- Partnered with internal teams to identify process gaps and document practical solutions.

Projects
- Customer Trend Report: analyzed support data and summarized top improvement areas.

Education
Bachelor's Degree | Example University | 2020

Languages
English - Professional
""".strip()

def render_cv_template_preview(template_name: str, target_country: str, user_status: str):
    st.markdown("### Template Preview")
    template_description = get_cv_template_options(target_country, user_status).get(template_name, "")
    visual_style = resolve_template_style(template_name)
    st.markdown(f"""
<div class="glass-card">
  <div class="section-title">{html_escape(template_name)}</div>
  <div class="small-muted">Target country: {html_escape(target_country)} • Layout style: {html_escape(visual_style)}</div>
  <br>
  <div>{html_escape(template_description)}</div>
</div>
""", unsafe_allow_html=True)

    sample_cv = build_template_sample_cv(template_name, target_country)
    st.components.v1.html(build_visual_cv_html(sample_cv, template_name, target_country), height=620, scrolling=True)

    with st.expander("What this template includes", expanded=False):
        st.markdown(get_template_instructions(template_name, target_country))

def generate_country_cv_template(cv_text: str, target_country: str, user_status: str, template_name: str = "ATS Classic") -> str:
    selected_country = (target_country or "International").strip()
    template_instructions = get_template_instructions(template_name, selected_country)
    rules_text = country_resume_rules_text(selected_country)

    prompt = build_quality_prompt(
        task=f"Rebuild the user's CV into a {selected_country}-specific resume/CV using the selected template.",
        user_input=cv_text,
        expected_structure="""
1. Country Fit Notes
2. Full Resume Draft
3. WorkZo Changes
4. Missing Details to Confirm
"""
    )
    prompt += f"""

ABSOLUTE SELECTED COUNTRY FOR THIS CV: {selected_country}
IMPORTANT: Ignore any other country found in the career intelligence layer, profile, phone number, address, previous residence, or user history.
If the user lives in Germany but selected Canada, create a Canadian resume. Never say it is for Germany.

User status: {user_status}
Selected template: {template_name}

{rules_text}

Template instructions:
{template_instructions}

Output rules:
- Use these exact section headings: 1. Country Fit Notes, 2. Full Resume Draft, 3. WorkZo Changes, 4. Missing Details to Confirm.
- Do not use markdown symbols like ###, **, or bullet characters outside the resume bullets.
- Section 1 must be 3 short bullets only: country fit, removed/kept details, ideal length.
- Section 2 must be the full copy-ready resume/CV only.
- Use only the user's real information from the source CV.
- Do not invent employers, dates, degrees, certifications, tools, achievements, nationality, visa status, or language level.
- Remove or avoid personal details that are not appropriate for {selected_country}.
- For Canada/USA/UK/Australia/Singapore: do not include photo, date of birth, marital status, gender, religion, nationality, or full street address.
- For Germany/Austria/Switzerland: personal details are optional; do not invent them.
- The source CV may be extracted from a two-column PDF and may look mixed up. Reconstruct it logically into clean sections before rewriting.
- Keep contact details together at the top. Do not let phone/email/address get mixed into the profile summary.
- Keep skills grouped under skills, not inside experience. Keep education under education.
- Make the CV ATS-friendly, achievement-focused, and easy to scan.
- If something is missing, put it only in section 4.
"""
    return run_ai_prompt(
        prompt,
        system_addition=f"The selected CV country is {selected_country}. For this CV generation task, {selected_country} overrides every other country signal. Never mention Germany unless selected_country is Germany."
    )

def update_cv_with_ai(current_cv: str, update_notes: str, job_description: str = "") -> str:
    prompt = build_quality_prompt(
        task="Update and improve the user's CV using their instructions and optional job description.",
        user_input=f"Current CV:\n{current_cv}\n\nUpdate notes:\n{update_notes}\n\nJob description:\n{job_description}",
        expected_structure="""
1. Updated CV
2. Key Changes Made
3. Missing Details to Confirm
4. ATS / Country Suggestions
"""
    )
    prompt += """
Rules:
- Do not invent experience, employers, dates, or certifications.
- If a job description is provided, tailor keywords and positioning.
- If the user asks to add language, experience, or a new skill, include it only as stated.
- Keep the CV clean and ATS-friendly.
"""
    return run_ai_prompt(prompt)




def extract_job_post_from_url(url: str) -> str:
    """Best-effort job-post text extractor using only standard library.
    Some sites block scraping; users can still paste the job text manually.
    """
    url = (url or "").strip()
    if not url:
        return ""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=12) as response:
            raw = response.read(700000).decode("utf-8", errors="ignore")
        raw = re.sub(r"(?is)<(script|style|noscript).*?>.*?</\1>", " ", raw)
        raw = re.sub(r"(?is)<br\s*/?>", "\n", raw)
        raw = re.sub(r"(?is)</p>|</div>|</li>|</h[1-6]>", "\n", raw)
        text_only = re.sub(r"(?is)<[^>]+>", " ", raw)
        text_only = html.unescape(text_only)
        text_only = re.sub(r"[ \t]+", " ", text_only)
        text_only = re.sub(r"\n\s*\n+", "\n", text_only).strip()
        return text_only[:12000]
    except Exception:
        return ""

def combine_job_link_and_text(job_url: str, pasted_text: str) -> str:
    pasted_text = (pasted_text or "").strip()
    job_url = (job_url or "").strip()
    extracted = extract_job_post_from_url(job_url) if job_url else ""
    if extracted and pasted_text:
        return f"Job post link: {job_url}\n\nExtracted from link:\n{extracted}\n\nExtra details pasted by user:\n{pasted_text}"
    if extracted:
        return f"Job post link: {job_url}\n\nExtracted from link:\n{extracted}"
    return pasted_text



def is_applying_abroad_status(status: str) -> bool:
    status_l = (status or "").lower()
    return any(x in status_l for x in ["abroad", "migrate", "migration", "move/apply"])

def active_application_country() -> str:
    country = st.session_state.get("country") or "selected country"
    target = st.session_state.get("migration_country") or country
    if is_applying_abroad_status(st.session_state.get("user_status", "")):
        return target
    return target or country

def onboarding_country_for_cv() -> str:
    """Country selected on the onboarding page. Builder-only country choices must not affect this."""
    return st.session_state.get("country") or st.session_state.get("onboarding_country") or "International"

def country_aware_resume_improvements(text: str) -> str:
    target = (active_application_country() or "").strip()
    if not text or target.lower() in {"germany", "deutschland"}:
        return text
    lines = [line for line in str(text).splitlines() if line.strip()]
    cleaned = []
    for line in lines:
        low = line.lower()
        if "german" in low or "germany" in low or "deutsch" in low:
            continue
        cleaned.append(line)
    if len(cleaned) < 3:
        cleaned.append(f"- Adapt your resume wording and keywords for the {target} job market")
        cleaned.append("- Highlight technical support, customer-facing experience, tools, and measurable achievements")
        cleaned.append("- Add relevant projects, certifications, and role-specific keywords only if true")
    return "\n".join(cleaned[:4])

def target_market_guidance(country_name: str) -> str:
    country = (country_name or "").strip().lower()
    if country in {"india", "bharat"}:
        return "For India, focus on clear technical skills, project proof, role keywords, certifications, concise summary, and measurable impact. English is usually suitable for IT/data roles unless the job asks for another language."
    if country in {"germany", "deutschland"}:
        return "For Germany, use a structured CV, clear language level, relevant tools, measurable achievements, and local role keywords."
    if country in {"united states", "usa", "canada", "united kingdom", "uk", "australia"}:
        return "Use an ATS-friendly resume, avoid unnecessary personal details, and focus on achievements, tools, keywords, and impact."
    return f"Adapt the CV to {country_name}: use local role keywords, clear skills, measurable impact, and only truthful experience."

# =========================================================
# DOCUMENT TOOLS
# =========================================================

def show_document_tools():
    # Snapshot global country context so the Country-Specific Resume Builder can never leak changes across the app.
    _main_country_snapshot = st.session_state.get("country")
    _main_migration_snapshot = st.session_state.get("migration_country")

    st.subheader(txt("document_tools"))
    st.caption(txt("document_hub_caption"))

    tabs = st.tabs([
        ui_label("Improve / Update CV"),
        txt("cv_template_builder"),
        ui_label("Cover Letter Generator + Language"),
    ])

    # -----------------------------------------------------
    # 1. Improve / Update CV
    # -----------------------------------------------------
    with tabs[0]:
        st.markdown(f"### {ui_label('Improve / Update CV')}")
        st.caption(ui_label("Tailor your existing CV to a job description, update details, preview it in a country-aware template, then download it."))

        # Improve / Update CV uses the country chosen during onboarding, not the temporary country selected in the Country-Specific Resume Builder.
        selected_country_for_cv = onboarding_country_for_cv()
        user_status_for_template = st.session_state.get("user_status", "Not specified")
        template_options = get_cv_template_options(selected_country_for_cv, user_status_for_template)
        template_names = list(template_options.keys()) if template_options else ["ATS Classic"]

        col_a, col_b = st.columns(2)
        with col_a:
            selected_template = st.selectbox(
                ui_label("CV template style"),
                template_names,
                index=0,
                key="improve_cv_template_style_v92",
                help=ui_label("This uses the country selected during onboarding. Country-Specific Resume Builder choices do not affect this tab.")
            )
        with col_b:
            output_language = st.selectbox(
                ui_label("CV language"),
                language_options,
                index=language_options.index(st.session_state.get("preferred_language", "English")) if st.session_state.get("preferred_language", "English") in language_options else 0,
                key="improve_cv_output_language_v92"
            )

        with st.expander(ui_label("View / edit current CV used for tailoring"), expanded=False):
            current_cv = st.text_area(
                txt("your_cv"),
                value=organize_cv_for_display(st.session_state.get("cv_text", "")),
                height=260,
                key="improve_update_cv_source_v92",
            )

        job_desc_cv = st.text_area(
            ui_label("Paste the job description"),
            height=210,
            key="improve_cv_for_job_desc",
            placeholder=ui_label("Paste the job description here. If you came from Understand Job, it should already be filled."),
        )

        update_notes = st.text_area(
            ui_label("Optional updates to include"),
            height=120,
            key="improve_update_cv_notes_v92",
            placeholder=ui_label("Example: Add B1 German, new certificate, new project, updated phone number, or career break note."),
        )

        if st.button(ui_label("Generate Improved CV"), key="btn_generate_improved_cv_v92"):
            job_desc_combined = (job_desc_cv or "").strip()
            notes_combined = (update_notes or "").strip()
            if not current_cv.strip():
                st.warning(ui_label("Please provide your CV."))
            elif not job_desc_combined.strip() and not notes_combined.strip():
                st.warning(ui_label("Please paste a job description or add update notes."))
            else:
                with st.spinner(ui_label("Building a clean, truthful, downloadable CV...")):
                    rules_text = country_resume_rules_text(selected_country_for_cv)
                    template_instructions = get_template_instructions(selected_template, selected_country_for_cv)
                    prompt = f"""
{workzo_expert_context()}

TASK
Rewrite the user's existing CV into a clean, professional, job-targeted CV.

SELECTED COUNTRY / TARGET MARKET: {selected_country_for_cv}
SELECTED TEMPLATE: {selected_template}
OUTPUT LANGUAGE: {output_language}

COUNTRY RULES:
{rules_text}

TEMPLATE INSTRUCTIONS:
{template_instructions}

STRICT TRUTHFULNESS RULES:
- Do not invent experience, tools, certifications, employers, language levels, cloud work, integrations, dates, or achievements.
- Only reframe what is already present in the CV or clearly provided in the update notes.
- If the job description asks for a missing skill, include it only when supported by the CV or update notes.
- Do not write placeholders like [Your City] or [LinkedIn Profile] unless the original CV has no information. Prefer omitting missing personal details.
- Do not move phone number, email, or location into the Professional Summary.
- Do not merge unrelated sections together.
- Keep the CV ATS-friendly and easy to read.
- Use bullet points for skills and experience.
- Make it suitable for the selected country/target market.
- Write the final CV fully in {output_language}.

RETURN THIS EXACT STRUCTURE:

1. Tailoring Summary
- Fit level:
- Main improvement:
- Changes made:

2. Full Tailored CV
Start with:
Candidate Name
Target Job Title
Phone | Email | Location | LinkedIn if available

Then use only relevant sections from this list:
PROFESSIONAL SUMMARY
CORE SKILLS
PROFESSIONAL EXPERIENCE
PROJECTS
EDUCATION
CERTIFICATIONS
LANGUAGES

Formatting rules for Full Tailored CV:
- Do not include markdown tables.
- Do not include placeholder brackets.
- Each section heading must be on its own line.
- Keep summary as one short paragraph.
- Keep bullets concise and truthful.
- Keep contact details in the header only.
- Never split email/phone/address into the wrong section.
- Dates must stay on one line in a consistent format, for example: 10/2018 - 01/2020 or 2018 - 2020.
- Never split month/year dates across multiple lines.
- Never output dates as separate lines like 10/ then 2018 - 01 then /2020. Always write the full date range on one line.
- Use spaces around the dash: 10/2018 - 01/2020.

3. Changes Made
- List the practical edits made.

4. Details to Confirm
- List missing details the user may want to add.

CURRENT CV:
{current_cv}

JOB DESCRIPTION:
{job_desc_combined if job_desc_combined else "No job description provided."}

USER UPDATE NOTES:
{notes_combined if notes_combined else "No extra update notes provided."}
"""
                    result = run_ai_prompt(prompt, force_language=output_language)
                    if render_error_or_success(result):
                        full_cv = get_section_text(
                            result,
                            ["Full Tailored CV", "Full Improved CV", "Improved CV", "Full CV", "Updated CV"],
                            fallback_to_full=False
                        )
                        if not full_cv or len(full_cv.strip()) < 120:
                            full_cv = result
                        clean_cv = strip_markdown_for_resume(full_cv)
                        st.session_state.improved_cv_result_v92 = result
                        st.session_state.improved_cv_text_v92 = clean_cv
                        st.session_state.improved_cv_edit_buffer_v92 = clean_cv
                        st.session_state.improved_cv_template_v92 = selected_template
                        st.session_state.improved_cv_country_v92 = selected_country_for_cv
                        st.session_state.improved_cv_language_v92 = output_language
                        st.session_state["prepare_cv_tailored"] = True
                        st.success(ui_label("Improved CV generated. Review and edit it below."))

        if st.session_state.get("improved_cv_text_v92"):
            result = st.session_state.get("improved_cv_result_v92", "")
            with st.expander(ui_label("Tailoring summary"), expanded=False):
                summary = get_section_text(result, ["Tailoring Summary", "Changes Made", "Details to Confirm"], fallback_to_full=False)
                st.write(summary if summary else ui_label("Review the improved CV below."))

            st.markdown(f"### {ui_label('Preview Improved CV')}")
            edited_improved_cv = st.text_area(
                ui_label("Edit the CV text here"),
                value=st.session_state.get("improved_cv_edit_buffer_v92", st.session_state.get("improved_cv_text_v92", "")),
                height=420,
                key="improved_cv_editable_text_v92"
            )

            if st.button(ui_label("Update Preview with Edited Details"), key="btn_update_improved_cv_preview_v92"):
                st.session_state.improved_cv_text_v92 = strip_markdown_for_resume(edited_improved_cv)
                st.session_state.improved_cv_edit_buffer_v92 = st.session_state.improved_cv_text_v92
                st.session_state["prepare_cv_tailored"] = True
                st.success(ui_label("Preview updated with your edits."))
                st.rerun()

            preview_cv = st.session_state.get("improved_cv_text_v92", "")
            preview_template = st.session_state.get("improved_cv_template_v92", selected_template)
            preview_country = st.session_state.get("improved_cv_country_v92", selected_country_for_cv)

            st.components.v1.html(
                build_visual_cv_html(preview_cv, preview_template, preview_country),
                height=850,
                scrolling=True
            )

            safe_country = re.sub(r"[^a-z0-9]+", "_", str(preview_country).lower()).strip("_") or "country"
            safe_template = re.sub(r"[^a-z0-9]+", "_", str(preview_template).lower()).strip("_") or "template"
            safe_file_base = f"workzo_improved_{safe_country}_{safe_template}_cv"
            clean_download_cv = strip_markdown_for_resume(preview_cv)

            pdf_data = make_styled_pdf_from_cv_text(
                f"WorkZo Improved CV - {preview_country}",
                clean_download_cv,
                preview_template,
                preview_country
            )

            dl_col1, dl_col2, dl_col3 = st.columns(3)
            with dl_col1:
                st.download_button(
                    label=ui_label("Download CV as PDF"),
                    data=pdf_data,
                    file_name=f"{safe_file_base}.pdf",
                    mime="application/pdf",
                    key="download_improved_cv_pdf_v92",
                    on_click=track_event,
                    args=("cv_downloaded", "CV & Documents", {"format": "pdf"})
                )
            with dl_col2:
                st.download_button(
                    label=ui_label("Download CV as TXT"),
                    data=clean_download_cv.encode("utf-8"),
                    file_name=f"{safe_file_base}.txt",
                    mime="text/plain",
                    key="download_improved_cv_txt_v92",
                    on_click=track_event,
                    args=("cv_downloaded", "CV & Documents", {"format": "txt"})
                )
            with dl_col3:
                if st.button(ui_label("Save as Dashboard Resume"), key="save_improved_cv_dashboard_v92"):
                    set_new_resume_and_refresh(clean_download_cv)
                    st.success(ui_label("Saved as your dashboard resume."))
                    st.rerun()

    # -----------------------------------------------------
    # 2. Country CV Template Builder
    # -----------------------------------------------------
    with tabs[1]:
        st.markdown(f"### {txt('cv_template_builder')}")
        st.caption(ui_label("Choose a country and template. WorkZo will rebuild your resume in the style expected for that job market."))
        st.markdown("""
        <div class='next-action-card'>
            <div class='next-action-label'>Country-specific builder</div>
            <div class='next-action-title'>Build a resume for one selected job market</div>
            <div class='next-action-copy'>Experiment with Switzerland, Germany, India, the USA, or any other target market without changing your main onboarding country.</div>
        </div>
        """, unsafe_allow_html=True)

        # This country selector is local to this tab only. It must not update onboarding country, target market, dashboard, or Job Assist.
        _builder_default_country = onboarding_country_for_cv()
        target_country = st.selectbox(
            "Target CV country",
            country_options,
            index=country_options.index(_builder_default_country) if _builder_default_country in country_options else 0,
            key="country_specific_builder_only_country_v25"
        )
        st.session_state["country_specific_builder_country"] = target_country
        if _main_country_snapshot is not None:
            st.session_state["country"] = _main_country_snapshot
        if _main_migration_snapshot is not None:
            st.session_state["migration_country"] = _main_migration_snapshot
        # Country-specific builder selection is local to this tab only. Do not overwrite onboarding/target-market state.

        user_status_for_template = st.session_state.get("user_status", "Not specified")
        template_options = get_cv_template_options(target_country, user_status_for_template)
        template_names = list(template_options.keys())

        selected_template = st.selectbox(
            "Choose resume template style",
            template_names,
            index=0,
            key="country_cv_template_choice_v51",
            help="Templates are suggested based on the target country and your career situation."
        )

        render_cv_template_preview(selected_template, target_country, user_status_for_template)

        cv_template_input = st.text_area(
            "Source CV / profile text (auto-cleaned from uploaded CV)",
            value=organize_cv_for_display(st.session_state.cv_text),
            height=260,
            key="country_template_cv_v51"
        )

        if st.button("Generate Resume in Selected Template", key="btn_country_cv_template_preview_v51"):
            track_button_click("Generate Country CV Template", "Document Tools", {"template": selected_template, "target_country": target_country})
            if not cv_template_input.strip():
                st.warning("Please provide your CV.")
            else:
                with st.spinner("Building country-specific CV in selected template..."):
                    result = generate_country_cv_template(
                        cv_template_input,
                        target_country,
                        user_status_for_template,
                        selected_template
                    )
                    if render_error_or_success(result):
                        full_cv = get_section_text(result, ["Full Resume Draft", "Full Country-Specific CV Draft", "Rebuilt CV in Target Country Style", "Full CV"], fallback_to_full=True)
                        st.session_state.generated_country_cv_result = result
                        st.session_state.generated_country_cv_text = strip_markdown_for_resume(full_cv)
                        st.session_state.generated_country_cv_template = selected_template
                        st.session_state.generated_country_cv_country = target_country

        if st.session_state.get("generated_country_cv_text"):
            st.markdown("### Edit Resume Text")
            edited_cv = st.text_area(
                "Make changes here, then click Update Preview below",
                value=st.session_state.get("country_cv_edit_buffer", st.session_state.generated_country_cv_text),
                height=360,
                key="country_cv_editable_text_v51"
            )
            if st.button("Update Preview with Edited Resume", key="btn_update_country_cv_preview_v77"):
                st.session_state.generated_country_cv_text = strip_markdown_for_resume(edited_cv)
                st.session_state.country_cv_edit_buffer = st.session_state.generated_country_cv_text
                st.success("Preview updated with your edits.")
                st.rerun()

            preview_cv = st.session_state.generated_country_cv_text
            st.markdown("### Visual Resume Preview")
            st.components.v1.html(
                build_visual_cv_html(
                    preview_cv,
                    st.session_state.get("generated_country_cv_template", selected_template),
                    st.session_state.get("generated_country_cv_country", target_country)
                ),
                height=850,
                scrolling=True
            )

            result = st.session_state.get("generated_country_cv_result", "")
            with st.expander("Template / Country Fit Notes", expanded=False):
                notes = get_section_text(result, ["Country Fit Notes", "Template and Country Fit Notes", "Country CV Format Notes"])
                st.write(notes)

            with st.expander("What WorkZo changed", expanded=False):
                changes = get_section_text(result, ["WorkZo Changes", "What Was Changed"])
                st.write(changes)

            with st.expander("Missing details to confirm", expanded=False):
                missing = get_section_text(result, ["Missing Details to Confirm"])
                st.write(missing)

            download_country = st.session_state.get('generated_country_cv_country', target_country)
            download_template = st.session_state.get('generated_country_cv_template', selected_template)
            clean_download_cv = strip_markdown_for_resume(st.session_state.generated_country_cv_text)
            safe_file_base = f"workzo_{download_country.lower().replace(' ', '_')}_{download_template.lower().replace(' ', '_')}_cv"

            pdf_data = make_styled_pdf_from_cv_text(
                f"WorkZo CV - {download_country} - {download_template}",
                clean_download_cv,
                download_template,
                download_country
            )
            docx_data = make_docx_from_cv_text(
                f"WorkZo CV - {download_country} - {download_template}",
                clean_download_cv,
                download_template,
                download_country
            )

            dl_col1, dl_col2, dl_col3 = st.columns(3)
            with dl_col1:
                st.download_button(
                    label="Download Resume as PDF",
                    data=pdf_data,
                    file_name=f"{safe_file_base}.pdf",
                    mime="application/pdf",
                    key="download_country_cv_pdf_v77"
                )
            with dl_col2:
                st.download_button(
                    label="Download Resume as TXT",
                    data=clean_download_cv.encode("utf-8"),
                    file_name=f"{safe_file_base}.txt",
                    mime="text/plain",
                    key="download_country_cv_txt_v77"
                )
            with dl_col3:
                if Document is not None:
                    st.download_button(
                        label="Download Resume as DOCX",
                        data=docx_data,
                        file_name=f"{safe_file_base}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key="download_country_cv_docx_v77"
                    )

    # -----------------------------------------------------
    # 3. Cover Letter Generator
    # -----------------------------------------------------
    with tabs[2]:
        company_name = st.text_input("Company Name", key="doc_tools_company_name")
        role_name = st.text_input(txt("target_role"), key="doc_tools_role_name")
        cover_letter_language = st.selectbox(
            "Cover letter language",
            language_options,
            index=language_options.index(st.session_state.get("preferred_language", "English")) if st.session_state.get("preferred_language", "English") in language_options else 0,
            key="cover_letter_language_v60"
        )
        job_desc_letter = st.text_area("Paste the job description", height=220, key="doc_tools_job_desc")

        if st.button(txt("generate"), key="btn_cover_letter_v49"):
            track_button_click("Generate Cover Letter", "Document Tools")
            job_desc_letter_combined = (job_desc_letter or "").strip()
            if not role_name.strip() or not job_desc_letter_combined.strip():
                st.warning("Please enter a target role and paste the job description.")
            elif not st.session_state.cv_text.strip():
                st.warning("Please upload or create a CV first.")
            else:
                with st.spinner("Generating cover letter..."):
                    prompt = f"""
{txt('country_label')}: {st.session_state.country}
Target role: {role_name}
Company: {company_name if company_name.strip() else "Not specified"}

Candidate CV:
{st.session_state.cv_text}

Job description:
{job_desc_letter_combined}

Write a strong, personalized professional cover letter in {cover_letter_language}.

Quality requirements:
- Use the candidate's actual CV details.
- Connect 3 to 5 specific candidate strengths to the job description.
- Avoid generic sentences.
- Sound natural, confident, and human.
- Keep it suitable for the selected country and role level.
- Write the final cover letter and email version fully in {cover_letter_language}.

Return in this exact structure:

1. Full Cover Letter
2. Short Email Version
3. 3 Customization Tips

Important:
- Do not leave any section empty.
- Write complete content for each section.
"""
                    result = run_ai_prompt(prompt, force_language=cover_letter_language)
                    if render_error_or_success(result):
                        if not result.strip():
                            st.error("Cover letter generation returned an empty response. Please try again.")
                        else:
                            st.session_state.latest_cover_letter = result
                            render_section_cards(result, default_expand=True)

                            sections = numbered_sections_to_markdown(result)
                            full_letter = sections.get("Full Cover Letter", "").strip()
                            short_email = sections.get("Short Email Version", "").strip()

                            if full_letter:
                                st.markdown("### Full Cover Letter")
                                st.text_area("Generated Cover Letter", value=full_letter, height=320)
                                st.download_button(
                                    "Download Cover Letter as TXT",
                                    data=full_letter,
                                    file_name="cover_letter.txt",
                                    mime="text/plain",
                                    key="download_cover_letter_txt_v49"
                                )
                            if short_email:
                                st.markdown("### Short Email Version")
                                st.text_area("Generated Short Email", value=short_email, height=180)



def render_country_fit_cards(country_text: str):
    rows = []
    for raw in str(country_text or "").splitlines():
        item = raw.strip().lstrip("-• ").strip()
        if item:
            rows.append(item)
    if not rows:
        st.info(txt("not_analyzed"))
        return

    st.caption(txt("country_fit_note"))
    for item in rows[:3]:
        if " - " in item:
            country, reason = item.split(" - ", 1)
        elif ":" in item:
            country, reason = item.split(":", 1)
        else:
            country, reason = item, ""
        reason = reason.strip()
        if len(reason) > 120:
            reason = reason[:120].rsplit(" ", 1)[0] + "..."
        card_html = f"""
<div class="card">
  <div class="section-title">{html.escape(country.strip())}</div>
  <div class="small-muted">{html.escape(reason or txt('view_details'))}</div>
</div>
"""
        st.markdown(card_html, unsafe_allow_html=True)

    if len(rows) > 3:
        with st.expander(txt("country_fit_details"), expanded=False):
            for item in rows[3:]:
                st.markdown(f"- {item}")

# =========================================================
# DASHBOARD
# =========================================================
# DASHBOARD
# =========================================================
def get_nav_items() -> List[Tuple[str, str, str]]:
    return [
        ("dashboard", "🏠 " + txt("dashboard"), txt("dashboard_desc_short")),
        ("job_assist", "🔎 " + txt("job_assist"), txt("job_assist_desc_short")),
        ("cv_documents", "📄 " + txt("cv_documents"), txt("cv_documents_desc_short")),
        ("workobot", "🤖 " + txt("workobot"), txt("workobot_desc_short")),
    ]

def set_single_preferred_language(language: str):
    """Preferred Language is the only visible language setting.
    It controls app labels where supported, AI replies, and generated documents.
    """
    language = language or "English"
    st.session_state.preferred_language = language
    st.session_state.ui_language = language if language in UI_TEXT else "English"
    st.session_state.response_language = language

def go_to_nav(page_key: str):
    queue_navigation(page_key)
    st.rerun()

def get_recommended_next_action() -> Dict[str, str]:
    """Return one clear SaaS-style next action for the dashboard."""
    cv_uploaded = bool(str(st.session_state.get("cv_text", "")).strip())
    ats_score = st.session_state.get("ats_score_value")
    latest_job = bool(str(st.session_state.get("latest_job_analysis", "")).strip())

    try:
        ats_score_number = int(ats_score or 0)
    except Exception:
        ats_score_number = 0

    if not cv_uploaded:
        return {"title": txt("next_action_upload_title"), "desc": txt("next_action_upload_desc"), "button": txt("next_action_upload_button"), "target": "onboarding"}
    if ats_score_number and ats_score_number < 75:
        return {"title": txt("next_action_improve_title"), "desc": txt("next_action_improve_desc"), "button": txt("next_action_improve_button"), "target": "cv_documents"}
    if not latest_job:
        return {"title": txt("next_action_job_title"), "desc": txt("next_action_job_desc"), "button": txt("next_action_job_button"), "target": "job_assist"}
    return {"title": txt("next_action_interview_title"), "desc": txt("next_action_interview_desc"), "button": txt("next_action_interview_button"), "target": "workobot"}

def render_recommended_next_action():
    action = get_recommended_next_action()
    st.markdown(f"""
    <div class='next-action-card'>
        <div class='next-action-label'>{txt('recommended_next_step')}</div>
        <div class='next-action-title'>{html.escape(action['title'])}</div>
        <div class='next-action-copy'>{html.escape(action['desc'])}</div>
    </div>
    """, unsafe_allow_html=True)
    if action["target"] == "onboarding":
        if st.button(action["button"], use_container_width=True, key="dashboard_recommended_next_action"):
            track_button_click(action["button"], "Dashboard")
            reset_onboarding()
            st.rerun()
    else:
        st.button(
            action["button"],
            use_container_width=True,
            key="dashboard_recommended_next_action",
            on_click=queue_navigation,
            args=(action["target"],),
        )

def show_dashboard():
    consume_pending_navigation()
    maybe_scroll_to_top()
    with st.sidebar:
        st.markdown("""
        <div class='workzo-sidebar-brand-wrap'>
            <div class='workzo-sidebar-brand'>WORKZO AI</div>
            <div class='workzo-sidebar-version'>Beta V10.1 · guided workspace</div>
        </div>
        """, unsafe_allow_html=True)
        st.button("🏠 Dashboard", key="sidebar_dashboard_home_button", use_container_width=True, on_click=queue_navigation, args=("dashboard",))

        st.markdown("<div class='workzo-sidebar-section-label'>Profile</div>", unsafe_allow_html=True)
        country_sidebar = html.escape(str(st.session_state.get('country', txt('not_specified')) or txt('not_specified')))
        st.markdown(f"<div class='workzo-sidebar-chip'><span class='workzo-profile-chip-label'>Country</span><span class='workzo-profile-chip-value'>🌍 {country_sidebar}</span></div>", unsafe_allow_html=True)
        user_status_sidebar = str(st.session_state.get('user_status', txt('not_specified')) or txt('not_specified'))
        if user_status_sidebar.strip():
            st.markdown(f"<div class='workzo-sidebar-chip'><span class='workzo-profile-chip-label'>Career status</span><span class='workzo-profile-chip-value'>💼 {html.escape(user_status_sidebar)}</span></div>", unsafe_allow_html=True)
        resume_status = "Resume uploaded" if str(st.session_state.get("cv_text", "")).strip() else "No resume yet"
        st.markdown(f"<div class='workzo-sidebar-chip'><span class='workzo-profile-chip-label'>Resume</span><span class='workzo-profile-chip-value'>📄 {html.escape(resume_status)}</span></div>", unsafe_allow_html=True)
        if st.session_state.get("migration_country") and st.session_state.get("migration_country") != st.session_state.country:
            st.markdown(f"<div class='workzo-sidebar-chip'><span class='workzo-profile-chip-label'>Target market</span><span class='workzo-profile-chip-value'>🎯 {html.escape(str(st.session_state.migration_country))}</span></div>", unsafe_allow_html=True)

        st.markdown("<div class='workzo-sidebar-section-label'>Settings</div>", unsafe_allow_html=True)
        language_list = language_options if language_options else ["English", "German", "Dutch"]
        current_language = st.session_state.get("preferred_language", "English")
        if current_language not in language_list:
            current_language = "English" if "English" in language_list else language_list[0]
        preferred = st.selectbox(
            txt("preferred_language"),
            language_list,
            index=language_list.index(current_language),
            key="sidebar_preferred_language",
            help=txt("preferred_language_help")
        )
        set_single_preferred_language(preferred)

        st.markdown("<div class='workzo-sidebar-section-label'>Navigation</div>", unsafe_allow_html=True)
        nav_items = get_nav_items()
        # Dashboard is already available as the main Home button above, so it is not repeated here.
        nav_items = [item for item in nav_items if item[0] != "dashboard"]
        nav_labels = {key: label for key, label, _ in nav_items}
        nav_descriptions = {key: desc for key, _, desc in nav_items}
        nav_keys = [key for key, _, _ in nav_items]
        if st.session_state.get("founder_unlocked") and "founder_dashboard" not in nav_keys:
            nav_keys.append("founder_dashboard")
            nav_labels["founder_dashboard"] = "🔐 " + txt("founder_dashboard")
            nav_descriptions["founder_dashboard"] = "Private founder analytics and feedback."

        page_key = st.session_state.get("nav_page", st.session_state.get("page", "dashboard"))
        if page_key not in ["dashboard"] + nav_keys:
            page_key = "dashboard"

        if st.session_state.get("last_tracked_page") != page_key:
            track_event("page_view", nav_labels.get(page_key, page_key), {"page": page_key})
            st.session_state["last_tracked_page"] = page_key

        for nav_key in nav_keys:
            is_active = page_key == nav_key
            label = nav_labels.get(nav_key, nav_key)
            button_label = label + ("  ✓" if is_active else "")
            if st.button(
                button_label,
                key=f"sidebar_nav_button_{nav_key}",
                use_container_width=True,
                on_click=queue_navigation,
                args=(nav_key,),
            ):
                pass

        track_feature_view(nav_labels.get(page_key, txt("dashboard") if page_key == "dashboard" else page_key))
        current_desc = txt("dashboard_desc_short") if page_key == "dashboard" else nav_descriptions.get(page_key, "")
        st.markdown(f"<div class='workzo-sidebar-muted'>{html.escape(current_desc)}</div>", unsafe_allow_html=True)

        st.markdown("<div class='workzo-sidebar-section-label'>Admin</div>", unsafe_allow_html=True)
        founder_pin = os.getenv("FOUNDER_PIN") or get_streamlit_secret("FOUNDER_PIN")
        with st.expander(txt("founder_access"), expanded=False):
            if founder_pin:
                entered_pin = st.text_input(txt("founder_pin"), type="password", key="founder_pin_input_sidebar")
                if entered_pin == founder_pin:
                    st.session_state.founder_unlocked = True
                    st.success("Founder mode unlocked.")
                    sync_navigation_state("founder_dashboard")
            else:
                st.caption("FOUNDER_PIN is not configured. For local testing, create a temporary PIN below. Before public testing, add FOUNDER_PIN in Streamlit Secrets.")
                temp_pin = st.text_input("Temporary founder PIN", type="password", key="founder_temp_pin_sidebar")
                if temp_pin and len(temp_pin) >= 4:
                    st.session_state.founder_unlocked = True
                    st.success("Founder mode unlocked for this session.")
                    sync_navigation_state("founder_dashboard")

        st.markdown("---")
        if st.button(txt("edit_setup"), use_container_width=True, key="sidebar_edit_onboarding_button"):
            reset_onboarding()
            request_scroll_to_top()
            st.rerun()

    if page_key == "dashboard":
        ensure_dashboard_analysis()

        # WorkZo v10.1: calmer SaaS dashboard with scores first, clear next step, progress, and a connected workflow.
        cv_ready = bool(str(st.session_state.get("cv_text", "")).strip())
        job_ready = bool(str(st.session_state.get("last_understand_job_description", "") or st.session_state.get("improve_cv_for_job_desc", "") or st.session_state.get("last_prepare_job_description", "")).strip())
        improved_ready = bool(str(st.session_state.get("improved_cv_text", "") or st.session_state.get("latest_improved_cv", "") or st.session_state.get("final_cv_text", "")).strip())
        prepared_ready = bool(str(st.session_state.get("latest_application_prep", "") or st.session_state.get("latest_cover_letter", "")).strip())
        workflow_steps_done = [cv_ready, job_ready, improved_ready, prepared_ready]
        application_readiness = int(round((sum(workflow_steps_done) / len(workflow_steps_done)) * 100)) if workflow_steps_done else 0
        resume_score = int(st.session_state.cv_score_value or 0)
        ats_score = int(st.session_state.ats_score_value or 0)

        st.markdown(f"""
        <div class="workzo-dashboard-hero-compact">
            <div class="workzo-hero-kicker">{html.escape(ui_label('Career workspace'))}</div>
            <div class="workzo-hero-title">{html.escape(ui_label('One guided journey: Add details → Score → Improve → Find job → Prepare'))}</div>
            <div class="next-action-copy">{html.escape(ui_label('Your CV, country, language, job description, scores, and edits are reused across the app. Later, login/subscription can save this same workspace permanently.'))}</div>
            <div class="workzo-chip-row">
                <span class="workzo-dashboard-chip">🌍 {html.escape(str(st.session_state.get('country', 'Not specified')))}</span>
                <span class="workzo-dashboard-chip">🗣️ {html.escape(str(st.session_state.get('preferred_language', 'English')))}</span>
                <span class="workzo-dashboard-chip">📄 {html.escape('CV ready' if cv_ready else 'CV missing')}</span>
                <span class="workzo-dashboard-chip">🎯 {html.escape('Job added' if job_ready else 'Job not added')}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        score_col1, score_col2, score_col3 = st.columns([1, 1, 1.15])
        with score_col1:
            render_metric_card(txt("resume_score"), str(st.session_state.cv_score_value or "—"), f"{score_band(resume_score)} · {txt('metric_resume_quality')}" if resume_score else txt("metric_resume_quality"))
        with score_col2:
            render_metric_card(txt("ats_score"), str(st.session_state.ats_score_value or "—"), f"{score_band(ats_score)} · {txt('metric_ats_friendly')}" if ats_score else txt("metric_ats_friendly"))
        with score_col3:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-label'>{html.escape(ui_label('Application Readiness'))}</div>
                <div class='metric-value'>{application_readiness}%</div>
                <div class='metric-foot'>{html.escape(ui_label('Progress from CV to prepared application'))}</div>
            </div>
            """, unsafe_allow_html=True)
            st.progress(application_readiness)

        st.markdown(f"### {html.escape(ui_label('Your next best step'))}")
        render_recommended_next_action()

        st.markdown(f"### {html.escape(ui_label('Application progress'))}")
        progress_cols = st.columns(4)
        progress_items = [
            ("1", ui_label("CV added"), cv_ready, "dashboard"),
            ("2", ui_label("Job analyzed"), job_ready, "job_assist"),
            ("3", ui_label("CV improved"), improved_ready, "cv_documents"),
            ("4", ui_label("Prepared to apply"), prepared_ready, "job_assist"),
        ]
        for col, (num, title, done, target) in zip(progress_cols, progress_items):
            with col:
                icon = "✅" if done else "⬜"
                active_class = "active" if done else ""
                st.markdown(f"""
                <div class='workzo-action-card {active_class}'>
                    <div class='workzo-action-title'>{icon} {html.escape(num)}. {html.escape(title)}</div>
                    <div class='workzo-action-copy'>{html.escape(ui_label('Completed') if done else ui_label('Still pending'))}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown(f"### {html.escape(ui_label('Main workflow'))}")
        flow_cols = st.columns(4)
        flow_steps = [
            ("1", ui_label("Upload / edit CV"), ui_label("Check or update the resume text WorkZo uses everywhere."), "dashboard", cv_ready),
            ("2", ui_label("Analyze a job"), ui_label("Paste a job description before applying."), "job_assist", job_ready),
            ("3", ui_label("Improve CV"), ui_label("Choose normal or roast feedback, edit, then rescore."), "cv_documents", improved_ready),
            ("4", ui_label("Prepare to apply"), ui_label("Cover letter, interview practice, and application tracker."), "job_assist", prepared_ready),
        ]
        for col, (num, title, copy, target, done) in zip(flow_cols, flow_steps):
            with col:
                done_badge = " ✅" if done else ""
                active_class = "active" if done else ""
                st.markdown(f"""
                <div class='workzo-action-card {active_class}'>
                    <div class='workzo-action-title'>{html.escape(num)}. {html.escape(title)}{done_badge}</div>
                    <div class='workzo-action-copy'>{html.escape(copy)}</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button(ui_label("Open") + " →", key=f"dashboard_flow_v101_{target}_{num}", use_container_width=True):
                    if target == "dashboard":
                        reset_onboarding()
                        request_scroll_to_top()
                        st.rerun()
                    else:
                        queue_navigation(target)
                        st.rerun()

        with st.expander("💬 " + ui_label("Ask Work-O-Bot on this page"), expanded=False):
            st.caption(ui_label("Use this when you feel lost, want interview practice, or need help understanding your scores."))
            bot_question = st.text_input(ui_label("Ask a quick question"), key="dashboard_inline_workobot_question", placeholder=ui_label("Example: What should I improve first?"))
            if st.button(ui_label("Ask Work-O-Bot"), key="dashboard_inline_workobot_button"):
                if bot_question.strip():
                    with st.spinner(ui_label("Thinking...")):
                        context = f"""
User country: {st.session_state.get('country','')}
Preferred language: {st.session_state.get('preferred_language','English')}
Resume score: {st.session_state.get('cv_score_value','')}
ATS score: {st.session_state.get('ats_score_value','')}
Profile summary: {st.session_state.get('profile_summary','')}
Question: {bot_question}
"""
                        answer = run_ai_prompt(
                            system_prompt="You are Work-O-Bot, a practical career assistant. Answer briefly, with bold key points and clear next steps.",
                            user_input=context,
                            temperature=0.4,
                        )
                        st.markdown(answer)
                else:
                    st.warning(ui_label("Please enter a question."))
            if st.button(ui_label("Open full Work-O-Bot"), key="dashboard_open_full_workobot"):
                queue_navigation("workobot")
                st.rerun()

        st.markdown(f"### {html.escape(ui_label('Key insights'))}")
        insight_col, improve_col = st.columns([1.15, 1], gap="large")
        with insight_col:
            st.markdown(f"""
            <div class='glass-card'>
                <div class='workzo-mini-title'>{html.escape(txt('detected_summary'))}</div>
                <div class='workzo-text'><b>{html.escape(st.session_state.profile_summary or txt('not_analyzed'))}</b></div>
            </div>
            """, unsafe_allow_html=True)
            if st.session_state.key_skills_detected:
                with st.expander(ui_label("View detected skills"), expanded=False):
                    st.markdown(st.session_state.key_skills_detected)
        with improve_col:
            improvement_text = country_aware_resume_improvements(st.session_state.resume_improvements) if st.session_state.resume_improvements else html.escape(txt('not_analyzed'))
            st.markdown(f"""
            <div class='glass-card'>
                <div class='workzo-mini-title'>{html.escape(ui_label('Fix first'))}</div>
                <div class='workzo-text'>{improvement_text}</div>
            </div>
            """, unsafe_allow_html=True)

        with st.expander(txt('navigation_help'), expanded=False):
            h1, h2, h3 = st.columns(3)
            with h1:
                st.markdown(f"<div class='nav-help-card'><b>🔎 {txt('job_assist')}</b><br>{txt('job_assist_desc_short')}</div>", unsafe_allow_html=True)
                st.button(txt("go_job_assist"), use_container_width=True, key="dash_go_job_assist", on_click=queue_navigation, args=("job_assist",))
            with h2:
                st.markdown(f"<div class='nav-help-card'><b>📄 {txt('cv_documents')}</b><br>{txt('cv_documents_desc_short')}</div>", unsafe_allow_html=True)
                st.button(txt("go_cv_documents"), use_container_width=True, key="dash_go_cv_docs", on_click=queue_navigation, args=("cv_documents",))
            with h3:
                st.markdown(f"<div class='nav-help-card'><b>🤖 {txt('workobot')}</b><br>{txt('workobot_desc_short')}</div>", unsafe_allow_html=True)
                st.button(txt("go_workobot"), use_container_width=True, key="dash_go_workobot", on_click=queue_navigation, args=("workobot",))


    elif page_key == "cv_documents":
        show_document_tools()

    elif page_key == "job_assist":
        st.subheader(txt("job_assist"))

        # Persistent Job Assist mode with a tab-like UI.
        # Native st.tabs reset to the first tab after rerun, so this uses stable session state keys
        # while keeping the same clean Find Jobs | Understand Job style.
        st.markdown("""
        <style>
        div[data-testid="stRadio"] > div[role="radiogroup"] {
            display: flex;
            gap: 22px;
            border-bottom: 1px solid rgba(148,163,184,0.22);
            padding-bottom: 0px;
            margin-bottom: 28px;
        }
        div[data-testid="stRadio"] label {
            background: transparent !important;
            border: none !important;
            padding: 0 0 12px 0 !important;
            margin-right: 8px !important;
            color: #f8fafc !important;
            font-weight: 650 !important;
        }
        div[data-testid="stRadio"] label:has(input:checked) {
            color: #ff4b4b !important;
            border-bottom: 2px solid #ff4b4b !important;
        }
        div[data-testid="stRadio"] label > div:first-child {
            display: none !important;
        }
        </style>
        """, unsafe_allow_html=True)

        job_assist_mode_labels = {
            "find": txt("find_jobs"),
            "understand": txt("understand_job"),
            "prepare": "Prepare for this Job",
        }
        if "job_assist_mode_key" not in st.session_state or st.session_state.job_assist_mode_key not in job_assist_mode_labels:
            st.session_state.job_assist_mode_key = "find"

        job_assist_mode = st.radio(
            "Job Assist mode",
            ["find", "understand", "prepare"],
            horizontal=True,
            format_func=lambda mode: job_assist_mode_labels.get(mode, mode),
            label_visibility="collapsed",
            key="job_assist_mode_key"
        )

        if job_assist_mode == "find":
            st.markdown(f"### {txt('find_jobs')}")
            st.caption("Choose your country, focus, and location. WorkZo will suggest the closest career paths, rank jobs, and show where to search more.")

            target_country_options = country_options
            country_index = target_country_options.index(st.session_state.country) if st.session_state.country in target_country_options else 0
            search_country = st.selectbox("Country for job search", target_country_options, index=country_index, key="job_assist_search_country")

            job_search_focus = st.selectbox(
                "Job search focus",
                [
                    "Based on my career status",
                    "Student / Thesis / Internship",
                    "Freshers / entry-level",
                    "Apply online / remote",
                    "Career changer friendly",
                    "Experienced roles"
                ],
                key="job_search_focus",
                help="This helps WorkZo search with the right seniority and job keywords."
            )

            location_options = [f"Anywhere in {search_country}"] + fetch_country_cities(search_country)
            final_location = st.selectbox(
                txt("preferred_location"),
                options=location_options,
                index=0,
                help="This box is searchable. Start typing the city name inside this dropdown.",
                key="job_assist_location"
            )
            if final_location.startswith("Anywhere in "):
                final_location = search_country

            with st.expander("Review CV used for matching", expanded=False):
                cv_for_jobs = st.text_area(txt("your_cv"), value=build_job_matching_profile(st.session_state.cv_text), height=260, key="job_assist_cv")
            target_titles = st.text_input(
                "Optional target job titles",
                placeholder="Example: Data Analyst, Junior IT Support, Customer Success",
                key="job_assist_target_titles",
                help="Leave this empty and WorkZo will use roles detected from your CV. Add 2–4 titles for better matching."
            )
            job_status_for_search = st.session_state.get('user_status', 'Not specified')
            if job_search_focus == "Student / Thesis / Internship":
                job_status_for_search = STUDENT_STATUS_INTERNAL
            elif job_search_focus == "Freshers / entry-level":
                job_status_for_search = "Fresh graduate / entry level"
            elif job_search_focus == "Apply online / remote":
                job_status_for_search = "Apply online / remote"
            elif job_search_focus == "Career changer friendly":
                job_status_for_search = "Career changer"
            elif job_search_focus == "Experienced roles":
                job_status_for_search = "Experienced professional"
            st.caption(f"Matching for: {job_status_for_search} • {search_country}")
            if is_student_thesis_status(job_status_for_search):
                render_student_opportunity_guidance(search_country)

            if st.button("Find Matching Jobs", key="btn_find_jobs_v42"):
                track_button_click("Find Jobs", "Job Assist")
                if not cv_for_jobs.strip():
                    st.warning("Please provide your CV.")
                else:
                    with st.spinner("Finding roles and jobs that match your profile..."):
                        roles_from_input = [x.strip() for x in target_titles.split(",") if x.strip()]
                        inferred_roles = infer_relevant_roles_from_cv(cv_for_jobs or st.session_state.cv_text)
                        roles_from_input = build_role_suggestions(
                            roles_from_input + inferred_roles,
                            st.session_state.suggested_roles_detected,
                            st.session_state.current_role_detected
                        )

                        live_jobs = fetch_live_jobs_global(search_country, roles_from_input[:4], final_location, job_status_for_search)

                        plan = generate_job_search_plan(
                            search_country,
                            final_location,
                            roles_from_input,
                            cv_for_jobs,
                            live_jobs
                        )
                        render_job_plan(plan)

                        render_live_jobs(live_jobs, search_country, max_visible=18, roles=roles_from_input[:4], cv_text=cv_for_jobs)

                        render_job_board_search_cards(search_country, final_location, roles_from_input, job_status_for_search)

        elif job_assist_mode == "understand":
            st.markdown(f"### {txt('understand_job')}")
            st.caption("Paste a job description and WorkZo will help you decide whether to apply, what matches, what is missing, and how to tailor your CV.")

            job_desc = st.text_area("Paste the job description", key="job_desc_v42", height=220)

            if st.button(txt("analyze"), key="btn_understand_job_v42"):
                # Keep existing Understand Job tab; do not set radio widget key after creation.
                track_button_click("Understand Job", "Job Assist")
                job_desc_combined = (job_desc or "").strip()
                if not job_desc_combined.strip():
                    st.warning("Please paste the job description.")
                else:
                    with st.spinner("Analyzing fit, requirements, gaps, and tailoring advice..."):
                        prompt = f"""
Country: {st.session_state.country}
Preferred language: {st.session_state.get('preferred_language', 'English')}
Career situation: {st.session_state.get('user_status', 'Not specified')}
Candidate CV:
{st.session_state.cv_text}

Analyze this job description for the candidate as a practical decision assistant.

Return ONLY valid JSON with this exact schema:
{{
  "fit_score": 0,
  "skill_match": 0,
  "experience_match": 0,
  "language_match": 0,
  "keyword_match": 0,
  "verdict": "Strong apply / Apply, but tailor first / Possible, but risky / Skip or improve first",
  "main_reason": "one clear sentence explaining the score",
  "cv_job_comparison": {{
    "job_asks_for": ["3-5 short items"],
    "cv_shows": ["3-5 short items"],
    "main_gaps": ["2-4 short items"]
  }},
  "requirement_checklist": [
    {{"requirement": "requirement name", "status": "Strong match / Partial match / Missing", "evidence": "short explanation"}}
  ],
  "gaps_and_risks": ["specific risks only"],
  "tailored_cv_bullets": ["ready-to-paste CV bullet 1", "ready-to-paste CV bullet 2", "ready-to-paste CV bullet 3"],
  "interview_focus": ["topic 1", "topic 2", "topic 3"],
  "interview_questions": ["question 1", "question 2", "question 3", "question 4", "question 5"],
  "salary_estimate_note": "Clearly say this is approximate only. If unsure, say to verify locally.",
  "next_best_action": "one clear action before applying"
}}

Scoring rules:
- Be honest and strict. Do not give a high score just because the user has some experience.
- 80-100 = strong direct match.
- 60-79 = possible match but needs tailoring.
- 40-59 = risky or weak match.
- Below 40 = not recommended unless the user improves first.
- Language requirements must be consistent with the CV/session data. Do not switch between A1, A2, and B1 unless the CV says so.
- If salary is uncertain, keep it cautious and optional.
- Output every heading/value in the preferred language where possible, but keep JSON keys exactly as requested.

Job description:
{job_desc_combined}
"""
                        result = run_ai_prompt(prompt, json_mode=True)
                        if render_error_or_success(result):
                            st.session_state.latest_job_analysis = result
                            data = safe_json_loads(result)
                            if isinstance(data, dict):
                                st.session_state.job_fit_score_value = clamp_score_value(data.get("fit_score", 0))
                                st.session_state.last_understand_job_description = job_desc_combined
                                render_understand_job_analysis(data)

                                st.markdown("---")
                                st.markdown("### Next step")
                                st.caption("Use this job description to tailor your CV in the CV & Documents section.")
                                if st.button("Improve CV for this Job", key="btn_understand_to_improve_cv_after_analysis"):
                                    st.session_state["improve_cv_for_job_desc"] = st.session_state.get("last_understand_job_description", job_desc_combined)
                                    st.session_state["document_tools_mode"] = "Improve CV for a Job"
                                    queue_navigation("cv_documents")
                                    st.rerun()
                            else:
                                st.session_state.job_fit_score_value = parse_score(result)
                                if st.session_state.job_fit_score_value is not None:
                                    show_gauge(st.session_state.job_fit_score_value, txt("job_fit_score"))
                                st.markdown(f"### {txt('job_fit_analysis')}")
                                render_section_cards(result, default_expand=False)


        elif job_assist_mode == "prepare":
            st.markdown("### AI Job Application Assistant")
            st.caption("Paste a job description. WorkZo will prepare your CV, cover letter focus, interview plan, skill roadmap, and country-specific application guidance.")

            default_prepare_job = st.session_state.get("last_understand_job_description", "") or st.session_state.get("improve_cv_for_job_desc", "")

            def _guess_company_from_job_description(text):
                text = text or ""
                patterns = [
                    r"(?im)^\s*(?:company|employer|organization|organisation)\s*[:\-]\s*(.+)$",
                    r"(?im)^\s*(?:about|über)\s+([A-Z][A-Za-z0-9&.,\- ]{2,60})\s*$",
                    r"(?im)^\s*([A-Z][A-Za-z0-9&.,\- ]{2,60})\s+is\s+(?:looking|seeking|hiring)",
                    r"(?im)^\s*we\s+at\s+([A-Z][A-Za-z0-9&.,\- ]{2,60})\s+",
                ]
                for pat in patterns:
                    m = re.search(pat, text)
                    if m:
                        value = re.sub(r"\s+", " ", m.group(1)).strip(" -|•")
                        if 2 <= len(value) <= 70:
                            return value
                return ""

            guessed_company = _guess_company_from_job_description(default_prepare_job)
            company_col, role_col = st.columns(2)
            with company_col:
                target_company = st.text_input(
                    "Target company",
                    value=st.session_state.get("prepare_target_company", guessed_company),
                    placeholder="Example: Siemens, SAP, HubSpot",
                    key="prepare_target_company"
                )
            with role_col:
                target_job_title = st.text_input(
                    "Target job title",
                    value=st.session_state.get("prepare_target_job_title", ""),
                    placeholder="Example: Technical Support Engineer",
                    key="prepare_target_job_title"
                )

            job_desc_prepare = st.text_area(
                "Paste the job description",
                value=default_prepare_job,
                key="job_desc_prepare_v928",
                height=240
            )

            candidate_country = st.session_state.get("country", "Not specified")
            target_market = st.session_state.get("migration_country") or candidate_country
            preferred_language = st.session_state.get("preferred_language", "English")
            cv_text_for_prepare = st.session_state.get("cv_text", "")

            def _readiness_level(score):
                try:
                    score = int(score)
                except Exception:
                    score = 0
                if score >= 85:
                    return "Ready to apply"
                if score >= 70:
                    return "Good, tailor before applying"
                if score >= 50:
                    return "Possible, but improve first"
                return "Not ready yet"

            def _country_guidance(country_name):
                country_key = (country_name or "").strip().lower()
                guidance = {
                    "germany": {
                        "resume": "Use a structured Lebenslauf, clear language levels, reverse chronology, tools, achievements, and role keywords.",
                        "interview": "Expect direct questions, practical examples, technical/problem-solving discussion, and clear motivation.",
                        "platforms": ["LinkedIn", "StepStone", "Indeed", "XING", "Arbeitsagentur"],
                        "communication": "Professional, direct, factual, and concise. Avoid overclaiming."
                    },
                    "canada": {
                        "resume": "Use an achievement-focused 1–2 page resume. Avoid photo, date of birth, marital status, and sensitive personal details.",
                        "interview": "Expect behavioral questions and STAR-based answers about teamwork, ownership, and customer impact.",
                        "platforms": ["LinkedIn", "Indeed", "Job Bank", "Glassdoor"],
                        "communication": "Friendly, collaborative, confident, and evidence-based."
                    },
                    "india": {
                        "resume": "Highlight skills, projects, tools, certifications, measurable achievements, and role keywords clearly.",
                        "interview": "Expect technical screening, role-specific questions, project discussion, and HR/motivation round.",
                        "platforms": ["LinkedIn", "Naukri", "Indeed", "Foundit"],
                        "communication": "Clear, confident, skills-focused, and achievement-oriented."
                    },
                    "netherlands": {
                        "resume": "Keep the CV concise, direct, and skills-focused. English CVs are often acceptable for international roles.",
                        "interview": "Expect direct communication, practical problem-solving, and culture-fit questions.",
                        "platforms": ["LinkedIn", "Indeed NL", "Glassdoor", "Nationale Vacaturebank"],
                        "communication": "Direct, honest, concise, and practical."
                    },
                    "switzerland": {
                        "resume": "Use a polished, formal CV with clear language skills, experience, education, and concise achievements.",
                        "interview": "Expect structured interviews, professionalism, and strong focus on reliability and fit.",
                        "platforms": ["LinkedIn", "Jobs.ch", "Indeed", "JobScout24"],
                        "communication": "Formal, precise, respectful, and evidence-based."
                    },
                    "united states": {
                        "resume": "Use a concise resume with achievements and keywords. Avoid photo, DOB, marital status, and sensitive personal details.",
                        "interview": "Expect behavioral and role-specific questions, often using STAR stories.",
                        "platforms": ["LinkedIn", "Indeed", "Glassdoor", "ZipRecruiter"],
                        "communication": "Confident, concise, outcome-focused, and impact-oriented."
                    },
                    "united kingdom": {
                        "resume": "Use a clean 1–2 page CV focused on profile, key skills, experience, and achievements. Avoid unnecessary personal data.",
                        "interview": "Expect competency-based questions, motivation, and examples of problem solving.",
                        "platforms": ["LinkedIn", "Indeed", "Reed", "Totaljobs"],
                        "communication": "Professional, polite, clear, and example-driven."
                    },
                }
                return guidance.get(country_key, {
                    "resume": "Use a clean, ATS-friendly resume with a clear summary, relevant skills, measurable achievements, and country-appropriate details.",
                    "interview": "Prepare examples for your experience, motivation, problem solving, teamwork, and role-specific skills.",
                    "platforms": ["LinkedIn", "Indeed", "Google Jobs", "Local job boards"],
                    "communication": "Clear, honest, professional, and tailored to the role."
                })

            if st.button("Prepare my full application", key="btn_prepare_full_application_v928", use_container_width=True):
                track_button_click("Prepare my full application", "AI Job Application Assistant")
                if not job_desc_prepare.strip():
                    st.warning("Please paste the job description first.")
                elif not cv_text_for_prepare.strip():
                    st.warning("Please upload or create your CV first.")
                elif not can_make_request():
                    st.warning("Usage limit reached. Please try again later.")
                else:
                    with st.spinner("Preparing your job application package..."):
                        register_request()
                        country_rules = get_country_cv_rules(target_market)
                        country_guidance = _country_guidance(target_market)
                        prompt = f"""
You are WorkZo AI, an honest AI Job Application Assistant.

User context:
- Current country: {candidate_country}
- Target company: {target_company or "Not specified"}
- Target job title: {target_job_title or "Not specified"}
- Target market/country: {target_market}
- Preferred output language: {preferred_language}
- Career status: {st.session_state.get("user_status", "Not specified")}

Target country resume rules:
{json.dumps(country_rules, ensure_ascii=False)}

Country-specific guidance:
Resume style: {country_guidance["resume"]}
Interview style: {country_guidance["interview"]}
Job platforms: {", ".join(country_guidance["platforms"])}
Communication style: {country_guidance["communication"]}

Candidate CV:
{cv_text_for_prepare}

Target company:
{target_company or "Not specified"}

Target job title:
{target_job_title or "Not specified"}

Job description:
{job_desc_prepare}

Create a complete application preparation guide. Be honest, practical, and do not invent experience.

Return in this exact structure and do not create extra random headings:

1. Application Readiness Score
Give one score from 0 to 100 and label it:
- 85-100 Ready to apply
- 70-84 Good, tailor before applying
- 50-69 Possible, but improve first
- below 50 Not ready yet

Also give this breakdown:
- CV relevance
- Skills match
- Experience level match
- Language requirement match
- Country fit

2. Job Fit Analysis
Explain whether the user should apply, tailor first, or skip. Include the strongest match and biggest risk.

3. Application Strategy
Give copy-ready CV improvements, cover letter focus, and LinkedIn/profile positioning.
Separate:
- Safe to use
- Use only if true
- Do not add unless proven

4. Interview Preparation
Give 7 likely interview questions and short answer guidance. Mention that the user can practice these in a live voice mock interview.

5. Skill Gap Roadmap
Give exactly top 3 gaps. For each gap include:
- Why it matters
- 7-day practice plan
- What to add to CV only if true

6. Country Career Guide for {target_market}
Include resume format, interview expectations, job platforms, and communication style.

7. Final Application Checklist
Give 6 practical checklist items before applying.

Keep it structured, clear, non-repetitive, and useful.
"""
                        prep_result = run_ai_prompt(prompt)
                        if render_error_or_success(prep_result):
                            st.session_state.latest_application_prep = prep_result
                            st.session_state.last_prepare_job_description = job_desc_prepare
                            st.session_state.application_ready_flag = True
                            track_event("application_prepared", "AI Job Application Assistant", {"target_market": target_market})

            latest_prep = st.session_state.get("latest_application_prep", "")
            if latest_prep:
                st.markdown("### Your Application Preparation Guide")
                def _extract_application_readiness(text):
                    text = text or ""
                    patterns = [
                        r"(?im)^\s*(?:[-•*]\s*)?Score\s*[:\-]\s*(\d{1,3})(?:\s*/\s*100|\s*%)?",
                        r"(?im)^\s*(?:[-•*]\s*)?Application readiness(?: score)?\s*[:\-]\s*(\d{1,3})(?:\s*/\s*100|\s*%)?",
                        r"(?im)^\s*(?:\d+\.\s*)?Application Readiness Score\s*\n\s*(?:[-•*]\s*)?Score\s*[:\-]\s*(\d{1,3})",
                    ]
                    for pat in patterns:
                        m = re.search(pat, text, re.IGNORECASE)
                        if m:
                            return max(0, min(100, int(m.group(1))))
                    m = re.search(r"(?im)readiness[^\n]{0,80}?(\d{2,3})(?:\s*/\s*100|\s*%)", text)
                    if m:
                        return max(0, min(100, int(m.group(1))))
                    return None

                readiness_score = _extract_application_readiness(latest_prep)
                if readiness_score is not None:
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.metric("Application readiness", f"{int(readiness_score)}%")
                    with c2:
                        st.metric("Status", _readiness_level(readiness_score))
                    with c3:
                        st.metric("Target company", target_company or "Not specified")
                    st.caption(f"Target market: {target_market}")

                st.markdown("### Fast Application Plan")
                plan_cols = st.columns(5)
                cv_tailored_done = bool(
                    st.session_state.get("prepare_cv_tailored")
                    or st.session_state.get("improved_cv_text_v92")
                    or st.session_state.get("cv_tailored_for_prepare")
                )
                cover_done = bool(st.session_state.get("latest_cover_letter") or st.session_state.get("cover_letter_job_desc"))
                interview_done = bool(st.session_state.get("prepare_interview_started"))
                quick_steps = [
                    ("Understand job", True),
                    ("Tailor CV", cv_tailored_done),
                    ("Cover letter", cover_done),
                    ("Interview practice", interview_done),
                    ("Ready to apply", bool(readiness_score and readiness_score >= 85 and cv_tailored_done and cover_done)),
                ]
                for col, (label, done) in zip(plan_cols, quick_steps):
                    with col:
                        st.markdown(("✅ " if done else "⬜ ") + label)

                st.markdown("### AI Advice for This Job")
                st.markdown("""
<div class="next-action-card">
<div class="next-action-title">Connect your existing experience to the job — do not try to look perfect.</div>
<div class="next-action-copy">
Focus on transferable experience, measurable achievements, job-specific keywords, country expectations, and honest gaps you are already improving.
</div>
</div>
""", unsafe_allow_html=True)

                guidance = _country_guidance(target_market)
                st.markdown("### Country Career Guide")
                g1, g2 = st.columns(2)
                with g1:
                    st.markdown(f"**Resume format**  \n{guidance['resume']}")
                    st.markdown(f"**Interview style**  \n{guidance['interview']}")
                with g2:
                    st.markdown(f"**Job platforms**  \n{', '.join(guidance['platforms'])}")
                    st.markdown(f"**Communication style**  \n{guidance['communication']}")

                def _extract_prep_section(text, *possible_headings):
                    """Extract a section from the AI response even when the model slightly changes headings."""
                    all_headings = [
                        "Application Readiness Score",
                        "Application Readiness",
                        "Readiness Score",
                        "Job Fit Analysis",
                        "Job Fit Summary",
                        "Fit Summary",
                        "Application Strategy",
                        "CV Changes Needed",
                        "CV Improvements for this Job",
                        "Cover Letter Focus",
                        "Suggested Cover Letter Focus",
                        "Interview Preparation",
                        "Likely Interview Questions",
                        "Voice Interview Preparation",
                        "Skill Gap Roadmap",
                        "Skill Gap Advice",
                        "Country Career Guide",
                        "Country-Specific Career Guidance",
                        "Country-Specific Advice",
                        "Final Application Checklist",
                        "Application Checklist",
                    ]
                    text = text or ""
                    for heading in possible_headings:
                        pattern = (
                            r"(?is)(?:^|\n)\s*(?:\d+\.\s*)?"
                            + re.escape(heading)
                            + r"\s*[:\-]?\s*\n(.*?)(?=\n\s*(?:\d+\.\s*)?(?:"
                            + "|".join(re.escape(h) for h in all_headings if h != heading)
                            + r")\s*[:\-]?\s*\n|\Z)"
                        )
                        m = re.search(pattern, text)
                        if m and m.group(1).strip():
                            return m.group(1).strip()

                        # fallback: heading on same line with content after colon
                        pattern_inline = r"(?is)(?:^|\n)\s*(?:\d+\.\s*)?" + re.escape(heading) + r"\s*[:\-]\s*(.*?)(?=\n\s*(?:\d+\.\s*)?(?:" + "|".join(re.escape(h) for h in all_headings if h != heading) + r")\s*[:\-]?|\Z)"
                        m2 = re.search(pattern_inline, text)
                        if m2 and m2.group(1).strip():
                            return m2.group(1).strip()
                    return ""

                job_fit_text = _extract_prep_section(latest_prep, "Job Fit Analysis", "Job Fit Summary", "Fit Summary")
                app_strategy_text = _extract_prep_section(latest_prep, "Application Strategy", "CV Changes Needed", "CV Improvements for this Job")
                cover_text = _extract_prep_section(latest_prep, "Cover Letter Focus", "Suggested Cover Letter Focus")
                interview_text = _extract_prep_section(latest_prep, "Interview Preparation", "Likely Interview Questions", "Voice Interview Preparation")
                skill_text = _extract_prep_section(latest_prep, "Skill Gap Roadmap", "Skill Gap Advice")
                checklist_text = _extract_prep_section(latest_prep, "Final Application Checklist", "Application Checklist")

                st.markdown("### Preparation Details")
                fit_tab, strategy_tab, interview_tab, roadmap_tab = st.tabs([
                    "Job Fit",
                    "Application Strategy",
                    "Voice Interview Prep",
                    "Skill Roadmap & Checklist",
                ])

                with fit_tab:
                    st.markdown(job_fit_text or _extract_prep_section(latest_prep, "Application Readiness Score", "Application Readiness", "Readiness Score") or latest_prep[:1500])
                    readiness_breakdown_text = _extract_prep_section(latest_prep, "Application Readiness Score", "Application Readiness", "Readiness Score")
                    if readiness_breakdown_text:
                        st.markdown("#### Readiness breakdown")
                        st.markdown(readiness_breakdown_text)

                with strategy_tab:
                    st.markdown(app_strategy_text or cover_text or "Use the Next actions above to improve your CV and generate a cover letter for this role.")
                    if cover_text:
                        st.markdown("#### Cover letter focus")
                        st.markdown(cover_text)

                with interview_tab:
                    st.markdown("#### Voice Mock Interview")
                    st.info("WorkZo is preparing this as a live voice assistant. For now, use these questions to practice, and the next version can add microphone-based speaking practice.")
                    st.markdown(interview_text or "Prepare answers for role fit, technical skills, problem solving, communication, motivation, and country-specific expectations.")
                    if st.button("🎤 Start voice mock interview setup", key="voice_mock_interview_setup", use_container_width=True):
                        st.session_state["workobot_prefill"] = "Act as a live voice interview coach. Ask me one interview question at a time for the job I prepared for. After each answer, give short feedback and the next question."
                        queue_navigation("workobot")
                        st.rerun()

                with roadmap_tab:
                    st.markdown("#### Top Skill Gaps")
                    st.markdown(skill_text or "Focus on the top role requirements that are missing or weak in your CV. Build proof through small projects, certifications, or practical examples.")
                    st.markdown("#### Application Checklist")
                    if checklist_text:
                        st.markdown(checklist_text)
                    else:
                        st.markdown("""
- Tailor your CV for this job.
- Generate a job-specific cover letter.
- Prepare 5–7 interview answers.
- Check country-specific application expectations.
- Review job platform/application instructions.
- Save the application in your tracker.
""")

                with st.expander("View full AI-generated preparation guide", expanded=False):
                    st.markdown(latest_prep)


                st.markdown("### Next actions")
                n1, n2, n3, n4 = st.columns(4)
                with n1:
                    if st.button("⚡ Improve CV", key="prep_to_cv_documents", use_container_width=True):
                        st.session_state["improve_cv_for_job_desc"] = st.session_state.get("last_prepare_job_description", job_desc_prepare)
                        st.session_state["prepare_cv_tailored"] = True
                        st.session_state["document_tools_mode"] = "Improve / Update CV"
                        queue_navigation("cv_documents")
                        st.rerun()
                with n2:
                    if st.button("🎤 Voice interview", key="prep_to_workobot", use_container_width=True):
                        st.session_state["workobot_prefill"] = "Act as a live voice interview coach. Ask me one interview question at a time for the job I just prepared for. After each answer, give feedback and continue."
                        queue_navigation("workobot")
                        st.rerun()
                with n3:
                    if st.button("✉ Cover letter", key="prep_to_cover_letter", use_container_width=True):
                        st.session_state["cover_letter_job_desc"] = st.session_state.get("last_prepare_job_description", job_desc_prepare)
                        st.session_state["document_tools_mode"] = "Cover Letter Generator + Language"
                        queue_navigation("cv_documents")
                        st.rerun()
                with n4:
                    if st.button("📋 Save tracker", key="save_prepared_job_to_tracker", use_container_width=True):
                        if "application_tracker" not in st.session_state:
                            st.session_state.application_tracker = []
                        title_guess = (target_job_title or "").strip() or "Prepared job"
                        if title_guess == "Prepared job":
                            m = re.search(r"(?i)(job title|role|position)[:\\-]\\s*(.+)", job_desc_prepare[:1000])
                            if m:
                                title_guess = m.group(2).strip()[:80]
                        company_guess = (target_company or "").strip() or _guess_company_from_job_description(job_desc_prepare) or "Company not specified"
                        tracker_title = f"{company_guess} — {title_guess}" if company_guess else title_guess
                        st.session_state.application_tracker.append({
                            "title": tracker_title,
                            "company": company_guess,
                            "job_title": title_guess,
                            "country": target_market,
                            "status": "Preparing",
                            "date": time.strftime("%Y-%m-%d")
                        })
                        track_event("application_saved", "Application Tracker", {"title": tracker_title, "company": company_guess, "country": target_market})
                        st.success("Saved to your application tracker.")

                if st.button("✅ Mark CV as tailored", key="mark_prepare_cv_tailored_manual", use_container_width=True):
                    st.session_state["prepare_cv_tailored"] = True
                    st.success("CV tailoring step marked as complete.")
                    st.rerun()

            st.markdown("### Application Tracker")
            tracker = st.session_state.get("application_tracker", [])
            if tracker:
                for i, item in enumerate(tracker):
                    c1, c2, c3 = st.columns([2, 1, 1])
                    with c1:
                        st.write(f"**{item.get('title', 'Job')}**")
                        st.caption(f"{item.get('country','')} • Added {item.get('date','')}")
                    with c2:
                        status_options = ["Preparing", "Applied", "Interview", "Offer", "Rejected"]
                        current_status = item.get("status", "Preparing")
                        if current_status not in status_options:
                            current_status = "Preparing"
                        tracker[i]["status"] = st.selectbox(
                            "Status",
                            status_options,
                            index=status_options.index(current_status),
                            key=f"tracker_status_{i}",
                            label_visibility="collapsed"
                        )
                    with c3:
                        if st.button("Remove", key=f"remove_tracker_{i}"):
                            st.session_state.application_tracker.pop(i)
                            st.rerun()
            else:
                st.info("No saved applications yet. Prepare a job and save it here.")

    elif page_key == "founder_dashboard":
        if st.session_state.get("founder_unlocked"):
            render_founder_dashboard()
        else:
            st.warning(txt("no_founder_pin"))

    elif page_key in ["workobot", "interview_practice", "career_insights"]:
        # Single Work-O-Bot view. Removed duplicate tabs/buttons to keep the page simple.
        show_workobot()
    render_feedback_collector(nav_labels.get(page_key, page_key) if isinstance(page_key, str) else "General")
    render_issue_reporter(nav_labels.get(page_key, page_key) if isinstance(page_key, str) else "General")

    st.divider()
    st.caption("WORKZO AI V9.33 • Beta • Founder Analytics Improved")
    st.caption("⚠️ WorkZo AI is currently in Beta. Some results may not be perfect yet. Your feedback helps improve the tool. CV text and personal documents are not stored in analytics.")

# =========================================================
# ROUTER
# =========================================================
# Read browser URL page so Back/Forward returns to the previous WorkZo page instead of feeling broken.
url_page = read_url_page(st.session_state.get("page", "landing"))
valid_pages = {"landing", "dashboard", "job_assist", "cv_documents", "workobot", "founder_dashboard", "onboarding"}

# Before onboarding is complete, keep users on the landing page unless they click Start now.
if url_page in valid_pages and st.session_state.get("onboarding_complete"):
    st.session_state.page = url_page
    st.session_state.nav_page = "dashboard" if url_page in ["onboarding", "landing"] else url_page

if st.session_state.page == "landing":
    show_landing_page()
elif not st.session_state.onboarding_complete or st.session_state.page == "onboarding":
    show_onboarding()
else:
    show_dashboard()



