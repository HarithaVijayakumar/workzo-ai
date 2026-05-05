"""WorkZo AI - stable session-state router.

Replace workzo_modules/10_stability_patches_router.py with this file.
This removes query-param/link based navigation so dashboard buttons do not reload
or fall back to the landing page.
"""
from __future__ import annotations

try:
    import streamlit as st
except Exception:  # allows syntax checks outside Streamlit
    st = None

PAGE_ALIASES = {
    "home": "dashboard",
    "main": "dashboard",
    "dashboard": "dashboard",
    "cv": "improve_cv",
    "cv_documents": "improve_cv",
    "document_tools": "improve_cv",
    "improve": "improve_cv",
    "improve_cv": "improve_cv",
    "update_cv": "improve_cv",
    "edit_cv": "cv_preview",
    "preview_cv": "cv_preview",
    "cv_preview": "cv_preview",
    "cv_editor": "cv_preview",
    "cover": "cover_letter",
    "cover_letter": "cover_letter",
    "cover_letter_generator": "cover_letter",
    "jobs": "find_jobs",
    "find_job": "find_jobs",
    "find_jobs": "find_jobs",
    "job_match": "find_jobs",
    "job_assist": "find_jobs",
    "understand": "understand_job",
    "understand_job": "understand_job",
    "analyze_job": "understand_job",
    "interview": "real_interview",
    "interview_practice": "real_interview",
    "real_interview": "real_interview",
    "start_interview": "real_interview",
    "workobot": "workobot",
    "bot": "workobot",
    "founder": "founder_dashboard",
    "founder_dashboard": "founder_dashboard",
    "landing": "landing",
    "onboarding": "onboarding",
}

APP_PAGES = {
    "dashboard",
    "improve_cv",
    "cv_preview",
    "cover_letter",
    "find_jobs",
    "understand_job",
    "real_interview",
    "workobot",
    "founder_dashboard",
}


def _normalize_page(value: object, default: str = "dashboard") -> str:
    raw = str(value or default).strip()
    return PAGE_ALIASES.get(raw, raw if raw in APP_PAGES | {"landing", "onboarding"} else default)


def _sync_page(page: str) -> str:
    page = _normalize_page(page)
    for key in ["page", "nav_page", "current_page", "active_page", "selected_page", "workzo_active_page"]:
        st.session_state[key] = page
    if page in APP_PAGES:
        st.session_state["onboarding_complete"] = True
    return page


def go_to(page: str, **extra) -> None:
    """Global safe navigation helper for all modules."""
    current = _normalize_page(st.session_state.get("page"), "dashboard")
    target = _normalize_page(page)
    if current != target:
        st.session_state.setdefault("wz_nav_stack", []).append(current)
    for k, v in extra.items():
        st.session_state[k] = v
    _sync_page(target)
    try:
        st.rerun()
    except Exception:
        try:
            st.experimental_rerun()
        except Exception:
            pass


def go_back() -> None:
    stack = st.session_state.get("wz_nav_stack") or []
    while stack:
        target = _normalize_page(stack.pop())
        if target not in {"landing", "onboarding"}:
            st.session_state["wz_nav_stack"] = stack
            _sync_page(target)
            try:
                st.rerun()
            except Exception:
                try:
                    st.experimental_rerun()
                except Exception:
                    pass
            return
    go_to("dashboard")


def go_home() -> None:
    go_to("dashboard")


def _has_user_context() -> bool:
    keys = [
        "cv_text", "uploaded_cv_text", "clean_structured_cv_text", "structured_cv_json",
        "approved_cv_text", "workzo_live_cv_text", "selected_job_description",
        "current_job_description", "job_description",
    ]
    return any(bool(st.session_state.get(k)) for k in keys)


def _workzo_run_router_if_available() -> None:
    """Single source of truth router.

    Important: this intentionally does NOT read query params. Query-param links were
    the reason button clicks sent users back to landing.
    """
    if st is None:
        return

    if "onboarding_complete" not in st.session_state:
        st.session_state["onboarding_complete"] = _has_user_context()

    requested = _normalize_page(st.session_state.get("page"), "dashboard" if st.session_state.get("onboarding_complete") else "landing")

    # App pages should never be blocked by onboarding once a button navigates there.
    if requested in APP_PAGES:
        st.session_state["onboarding_complete"] = True

    _sync_page(requested)

    try:
        if requested == "landing" and not st.session_state.get("onboarding_complete"):
            fn = globals().get("show_landing_page")
            if callable(fn):
                fn()
                return

        if requested == "onboarding" or not st.session_state.get("onboarding_complete"):
            fn = globals().get("show_onboarding")
            if callable(fn):
                fn()
                return

        # All internal feature pages are rendered by show_dashboard(), which reads st.session_state['page'].
        fn = globals().get("show_dashboard") or globals().get("show_workzo_dashboard")
        if callable(fn):
            fn()
            return

        st.error("WorkZo router could not find show_dashboard().")
    except Exception as exc:
        st.error(f"WorkZo router error: {exc}")
        try:
            st.exception(exc)
        except Exception:
            pass


# Run router when this module is executed by app.py.
_workzo_run_router_if_available()
