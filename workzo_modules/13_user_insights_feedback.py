# =========================================================
# WorkZo AI - User Insights, Feedback & Lightweight Analytics
# Non-breaking add-on module
# =========================================================
from __future__ import annotations

import csv
import os
import time
from datetime import datetime, UTC
from pathlib import Path
from typing import Dict, Any, Optional

try:
    import streamlit as st
except Exception:  # Allows syntax check outside Streamlit runtime
    st = None


BASE_DIR = Path.cwd()
ANALYTICS_FILE = BASE_DIR / "workzo_analytics.csv"
FEEDBACK_FILE = BASE_DIR / "workzo_feedback.csv"
USER_PROFILE_FILE = BASE_DIR / "workzo_user_profiles.csv"

# Per-rerun render guards. These prevent duplicate feedback/founder blocks
# when multiple dashboard wrappers call the same helper during one Streamlit run.
_wz_feedback_rendered_guard = False
_wz_founder_message_rendered_guard = False


def _now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _safe_session_get(key: str, default: Any = "") -> Any:
    if st is None:
        return default
    try:
        return st.session_state.get(key, default)
    except Exception:
        return default


def _safe_write_csv(path: Path, row: Dict[str, Any], fieldnames: list[str]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        exists = path.exists()
        with path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not exists:
                writer.writeheader()
            writer.writerow({k: row.get(k, "") for k in fieldnames})
    except Exception:
        # Analytics must never break the app.
        pass


def init_user_insights() -> None:
    """Initialize safe defaults. Call once after module load."""
    if st is None:
        return
    try:
        st.session_state.setdefault("wz_user_identity_done", False)
        st.session_state.setdefault("wz_user_identity_skipped", False)
        st.session_state.setdefault("wz_feedback_open", False)
        st.session_state.setdefault("wz_session_id", str(int(time.time() * 1000)))
    except Exception:
        pass


def get_user_insight_context() -> Dict[str, Any]:
    """Small context snapshot for analytics rows."""
    return {
        "session_id": _safe_session_get("wz_session_id", ""),
        "page": _safe_session_get("page", _safe_session_get("nav_page", "")),
        "country": _safe_session_get("country", _safe_session_get("migration_country", "")),
        "language": _safe_session_get("preferred_language", _safe_session_get("language", "")),
        "career_status": _safe_session_get("user_status", ""),
        "cv_loaded": bool(str(_safe_session_get("cv_text", "") or _safe_session_get("clean_structured_cv_text", "")).strip()),
        "target_role": _safe_session_get("target_role", _safe_session_get("detected_target_role", "")),
    }


def track_event(event_name: str, feature: str = "", metadata: Optional[Dict[str, Any]] = None) -> None:
    """Append a lightweight analytics event to CSV. Safe no-op on failure."""
    metadata = metadata or {}
    ctx = get_user_insight_context()
    row = {
        "timestamp": _now_iso(),
        "session_id": ctx.get("session_id", ""),
        "event_name": event_name,
        "feature": feature,
        "page": ctx.get("page", ""),
        "country": ctx.get("country", ""),
        "language": ctx.get("language", ""),
        "career_status": ctx.get("career_status", ""),
        "target_role": ctx.get("target_role", ""),
        "cv_loaded": ctx.get("cv_loaded", ""),
        "metadata": str(metadata),
    }
    _safe_write_csv(
        ANALYTICS_FILE,
        row,
        ["timestamp", "session_id", "event_name", "feature", "page", "country", "language", "career_status", "target_role", "cv_loaded", "metadata"],
    )


def save_user_identity(name: str, email: str, user_type: str, source: str) -> None:
    if st is None:
        return
    try:
        st.session_state["wz_user_name"] = name.strip()
        st.session_state["wz_user_email"] = email.strip()
        st.session_state["wz_user_type"] = user_type.strip()
        st.session_state["wz_user_source"] = source.strip()
        st.session_state["wz_user_identity_done"] = True
        st.session_state["wz_user_identity_skipped"] = False
    except Exception:
        pass

    row = {
        "timestamp": _now_iso(),
        "session_id": _safe_session_get("wz_session_id", ""),
        "name": name.strip(),
        "email": email.strip(),
        "user_type": user_type.strip(),
        "source": source.strip(),
        "country": _safe_session_get("country", ""),
        "language": _safe_session_get("preferred_language", ""),
    }
    _safe_write_csv(
        USER_PROFILE_FILE,
        row,
        ["timestamp", "session_id", "name", "email", "user_type", "source", "country", "language"],
    )
    track_event("user_identity_submitted", "User Insights", {"user_type": user_type, "source": source, "has_email": bool(email.strip())})


def show_user_identity_prompt(force: bool = False) -> None:
    """Skippable 10-second prompt. Best placed after landing or before onboarding."""
    if st is None:
        return
    init_user_insights()
    try:
        if not force and (st.session_state.get("wz_user_identity_done") or st.session_state.get("wz_user_identity_skipped")):
            return
    except Exception:
        return

    try:
        st.markdown("""
        <style id="wz-user-insights-css">
        .wz-insight-card {
            border: 1px solid rgba(34,211,238,.22);
            background: linear-gradient(135deg, rgba(8,47,73,.52), rgba(15,23,42,.92));
            border-radius: 20px;
            padding: 1rem;
            margin: .75rem 0 1rem;
            box-shadow: 0 12px 32px rgba(2,6,23,.20);
        }
        .wz-insight-title { color:#fff; font-size:1rem; font-weight:900; margin-bottom:.25rem; }
        .wz-insight-copy { color:#cbd5e1; font-size:.9rem; margin:0; }
        </style>
        <div class="wz-insight-card">
            <div class="wz-insight-title">Help us improve WorkZo AI — 10 seconds</div>
            <p class="wz-insight-copy">This is optional, but it helps us understand who is testing the product.</p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("wz_user_identity_form", clear_on_submit=False):
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input("Name (optional)", key="wz_identity_name")
            with c2:
                email = st.text_input("Email (optional but recommended)", key="wz_identity_email")

            user_type = st.selectbox(
                "What best describes you?",
                ["Job seeker", "Student", "Career switcher", "Returning after a career break", "Founder / Maker", "Other"],
                key="wz_identity_user_type",
            )
            source = st.selectbox(
                "Where did you find us?",
                ["LinkedIn", "Indie Hackers", "Friend", "WhatsApp", "Product Hunt", "Reddit", "Other"],
                key="wz_identity_source",
            )
            c_submit, c_skip = st.columns([1, 1])
            submitted = c_submit.form_submit_button("Save and continue", type="primary", use_container_width=True)
            skipped = c_skip.form_submit_button("Skip", use_container_width=True)

        if submitted:
            save_user_identity(name, email, user_type, source)
            st.success("Thanks — this helps improve WorkZo AI.")
            st.rerun()
        if skipped:
            st.session_state["wz_user_identity_skipped"] = True
            track_event("user_identity_skipped", "User Insights")
            st.rerun()
    except Exception:
        pass


def save_feedback(what_tried: str, confused: str, use_again: str, extra: str = "") -> None:
    row = {
        "timestamp": _now_iso(),
        "session_id": _safe_session_get("wz_session_id", ""),
        "page": _safe_session_get("page", _safe_session_get("nav_page", "")),
        "name": _safe_session_get("wz_user_name", ""),
        "email": _safe_session_get("wz_user_email", ""),
        "user_type": _safe_session_get("wz_user_type", ""),
        "what_tried": what_tried,
        "confused": confused,
        "use_again": use_again,
        "extra": extra,
    }
    _safe_write_csv(
        FEEDBACK_FILE,
        row,
        ["timestamp", "session_id", "page", "name", "email", "user_type", "what_tried", "confused", "use_again", "extra"],
    )
    track_event("feedback_submitted", "Feedback", {"use_again": use_again})


def render_feedback_button() -> None:
    """Small feedback section. Streamlit-safe alternative to fragile floating JS.

    Guarded so it can be safely called from dashboard wrappers without showing twice.
    """
    global _wz_feedback_rendered_guard
    if st is None:
        return
    if _wz_feedback_rendered_guard:
        return
    _wz_feedback_rendered_guard = True
    init_user_insights()
    try:
        with st.expander("💬 Give feedback (30 sec)", expanded=False):
            with st.form("wz_feedback_form", clear_on_submit=True):
                what_tried = st.text_area("What did you try?", height=80, placeholder="Example: uploaded CV, improved CV, tried interview practice")
                confused = st.text_area("What confused you?", height=80, placeholder="Example: too many steps, unclear button, result not useful")
                use_again = st.radio("Would you use this again?", ["Yes", "Maybe", "No"], horizontal=True)
                extra = st.text_area("Anything else?", height=70, placeholder="Optional")
                submitted = st.form_submit_button("Send feedback", type="primary", use_container_width=True)
            if submitted:
                save_feedback(what_tried, confused, use_again, extra)
                st.success("Thank you — your feedback was saved.")
    except Exception:
        pass


def render_founder_message(email: str = "") -> None:
    """Human founder note, non-intrusive.

    Guarded so it can be safely called from multiple places without duplication.
    """
    global _wz_founder_message_rendered_guard
    if st is None:
        return
    if _wz_founder_message_rendered_guard:
        return
    _wz_founder_message_rendered_guard = True
    try:
        contact = f" You can also email me at {email}." if email else ""
        st.markdown(f"""
        <div style="border:1px solid rgba(148,163,184,.18); background:rgba(15,23,42,.45); border-radius:16px; padding:.85rem 1rem; color:#cbd5e1; font-size:.88rem; margin-top:1.2rem;">
            <b style="color:#fff;">Thanks for trying WorkZo 🙌</b><br>
            I’m the founder and would love your feedback.{contact}
        </div>
        """, unsafe_allow_html=True)
    except Exception:
        pass


# Convenience wrappers for common product events.
def track_page_visit(page_name: str = "") -> None:
    track_event("page_visit", page_name or str(_safe_session_get("page", "")))


def track_cv_uploaded(source: str = "") -> None:
    track_event("cv_uploaded", "Onboarding/CV", {"source": source})


def track_interview_started(context: str = "") -> None:
    track_event("interview_started", "Interview", {"context": context})


def track_interview_completed(result: str = "") -> None:
    track_event("interview_completed", "Interview", {"result": result})
