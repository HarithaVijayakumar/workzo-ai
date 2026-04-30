"""
WorkZo Core Stability Layer
Place this file in: workzo_modules/workzo_core_stability.py
Then load it EARLY in app.py, right after 00_bootstrap_config.py and before other modules.

Recommended MODULE_ORDER:
    00_bootstrap_config.py
    workzo_core_stability.py
    01_ui_language_geo.py
    ...rest of modules
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict

try:
    import streamlit as st
except Exception:  # allows syntax checks outside Streamlit
    st = None

BASE_DIR = Path(__file__).resolve().parent
STATE_FILE = BASE_DIR / "workzo_local_state.json"

PERSIST_KEYS = [
    "cv_text", "clean_structured_cv_text", "approved_cv_text", "structured_cv_json",
    "cv_score_value", "ats_score_value", "application_readiness_value", "job_fit_score_value",
    "country", "migration_country", "preferred_language", "ui_language", "response_language",
    "user_status", "target_role", "current_job_description", "last_understand_job_description",
    "improve_cv_for_job_desc", "last_prepare_job_description", "target_company_website",
    "latest_job_analysis", "latest_application_prep", "latest_cover_letter", "nav_page", "page",
]

DEFAULT_TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "English": {
        "dashboard": "Dashboard", "cv_documents": "CV Documents", "job_assist": "Job Assist",
        "workobot": "Work-O-Bot", "preferred_language": "Preferred language",
        "edit_setup": "Edit setup", "find_jobs": "Find Jobs", "understand_job": "Understand Job",
        "prepare_for_this_job": "Prepare for this Job", "upload_cv": "Upload CV",
        "create_cv": "Create CV", "import_linkedin": "Import LinkedIn",
        "welcome_to_workzo": "Welcome to WorkZo", "career_situation": "Current career situation",
    },
    "German": {
        "dashboard": "Dashboard", "cv_documents": "CV-Dokumente", "job_assist": "Job-Assistent",
        "workobot": "Work-O-Bot", "preferred_language": "Bevorzugte Sprache",
        "edit_setup": "Setup bearbeiten", "find_jobs": "Jobs finden", "understand_job": "Job verstehen",
        "prepare_for_this_job": "Für diesen Job vorbereiten", "upload_cv": "Lebenslauf hochladen",
        "create_cv": "Lebenslauf erstellen", "import_linkedin": "LinkedIn importieren",
        "welcome_to_workzo": "Willkommen bei WorkZo", "career_situation": "Aktuelle Karrieresituation",
    },
    "Dutch": {
        "dashboard": "Dashboard", "cv_documents": "CV-documenten", "job_assist": "Jobassistent",
        "workobot": "Work-O-Bot", "preferred_language": "Voorkeurstaal",
        "edit_setup": "Instellingen bewerken", "find_jobs": "Banen zoeken", "understand_job": "Vacature begrijpen",
        "prepare_for_this_job": "Voorbereiden op deze baan", "upload_cv": "CV uploaden",
        "create_cv": "CV maken", "import_linkedin": "LinkedIn importeren",
        "welcome_to_workzo": "Welkom bij WorkZo", "career_situation": "Huidige carrièresituatie",
    },
}


def _safe_json(value: Any) -> Any:
    try:
        json.dumps(value)
        return value
    except Exception:
        return str(value)


def load_workzo_state() -> None:
    if st is None or not STATE_FILE.exists():
        return
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            for key, value in data.items():
                if key in PERSIST_KEYS and key not in st.session_state:
                    st.session_state[key] = value
    except Exception:
        pass


def save_workzo_state() -> None:
    if st is None:
        return
    try:
        data = {k: _safe_json(st.session_state.get(k)) for k in PERSIST_KEYS if k in st.session_state}
        STATE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def sync_language(language: str | None = None) -> str:
    if st is None:
        return "English"
    lang = language or st.session_state.get("preferred_language") or st.session_state.get("ui_language") or "English"
    st.session_state["preferred_language"] = lang
    st.session_state["ui_language"] = lang
    st.session_state["response_language"] = lang
    save_workzo_state()
    return lang


def txt(key: str, default: str | None = None) -> str:
    if st is None:
        return default or key
    lang = st.session_state.get("preferred_language", "English")
    table = globals().get("UI_TEXT", {}) or DEFAULT_TRANSLATIONS
    if not isinstance(table, dict):
        table = DEFAULT_TRANSLATIONS
    return table.get(lang, table.get("English", {})).get(key, DEFAULT_TRANSLATIONS.get(lang, {}).get(key, default or key))


def queue_navigation(page_key: str) -> None:
    if st is None:
        return
    st.session_state["page"] = page_key
    st.session_state["nav_page"] = page_key
    request_scroll_to_top()
    save_workzo_state()


def request_scroll_to_top() -> None:
    if st is not None:
        st.session_state["_workzo_scroll_to_top"] = True
        st.session_state["_workzo_page_nonce"] = str(int(time.time() * 1000))


def maybe_scroll_to_top() -> None:
    if st is None:
        return
    st.markdown('<div id="workzo-page-top"></div>', unsafe_allow_html=True)
    if st.session_state.pop("_workzo_scroll_to_top", False):
        try:
            st.query_params["wz_top"] = st.session_state.get("_workzo_page_nonce", "top")
        except Exception:
            pass


def can_make_request() -> bool:
    if st is None:
        return True
    limit = int(os.getenv("WORKZO_MAX_REQUESTS_PER_HOUR", "25"))
    now = time.time()
    first = float(st.session_state.get("first_request_time", now))
    if now - first > 3600:
        st.session_state["first_request_time"] = now
        st.session_state["request_count"] = 0
    return int(st.session_state.get("request_count", 0)) < limit


def register_request() -> None:
    if st is not None:
        st.session_state["request_count"] = int(st.session_state.get("request_count", 0)) + 1
        save_workzo_state()


def workzo_stage_flags() -> Dict[str, bool]:
    if st is None:
        return {}
    cv_ready = bool(str(st.session_state.get("cv_text") or st.session_state.get("clean_structured_cv_text") or "").strip())
    job_ready = bool(str(st.session_state.get("current_job_description") or st.session_state.get("last_understand_job_description") or "").strip())
    cv_improved = bool(str(st.session_state.get("improved_cv_text") or st.session_state.get("final_cv_text") or "").strip())
    prepared = bool(str(st.session_state.get("latest_application_prep") or st.session_state.get("latest_cover_letter") or "").strip())
    return {"cv_ready": cv_ready, "job_ready": job_ready, "cv_improved": cv_improved, "prepared": prepared}


def recommended_next_page() -> str:
    flags = workzo_stage_flags()
    try:
        resume = int(st.session_state.get("cv_score_value") or 0)
        ats = int(st.session_state.get("ats_score_value") or 0)
    except Exception:
        resume = ats = 0
    if not flags.get("cv_ready"):
        return "onboarding"
    if resume and ats and (resume < 75 or ats < 75):
        return "cv_documents"
    if not flags.get("job_ready"):
        return "job_assist"
    if not flags.get("cv_improved"):
        return "cv_documents"
    return "workobot"


def init_workzo_core() -> None:
    if st is None:
        return
    globals().setdefault("UI_TEXT", DEFAULT_TRANSLATIONS)
    load_workzo_state()
    sync_language(st.session_state.get("preferred_language", "English"))
    st.session_state.setdefault("page", st.session_state.get("nav_page", "dashboard"))
    st.session_state.setdefault("nav_page", st.session_state.get("page", "dashboard"))
    st.session_state.setdefault("request_count", 0)
    st.session_state.setdefault("first_request_time", time.time())


# Run immediately when loaded by app.py exec().
init_workzo_core()
