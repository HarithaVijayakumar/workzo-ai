"""WorkZo AI - stable session-state router v145.

Fixes:
- Fresh app open shows Landing, not Dashboard, even if old CV/session state exists.
- Landing -> Onboarding -> Real Interview flow is preserved.
- Old Work-O-Bot/interview aliases route to Real Interview only after onboarding/start.
- Query-param/stale session routes no longer bypass landing/onboarding.
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
    "work-o-bot": "workobot",
    "work_o_bot": "workobot",
    "bot": "workobot",
    "prepare_job": "prepare_job",
    "prepare_this_job": "prepare_job",
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
    "founder_dashboard",
    "workobot",
    "prepare_job",
}

PUBLIC_PAGES = {"landing", "onboarding"}


def _normalize_page(value: object, default: str = "dashboard") -> str:
    raw = str(value or default).strip().lower()
    return PAGE_ALIASES.get(raw, raw if raw in APP_PAGES | PUBLIC_PAGES else default)


def _set_query_page(page: str) -> None:
    try:
        st.query_params["page"] = page
    except Exception:
        pass


def _sync_page(page: str, *, mark_onboarded: bool = True) -> str:
    page = _normalize_page(page)
    for key in ["page", "nav_page", "current_page", "active_page", "selected_page", "workzo_active_page"]:
        st.session_state[key] = page
    if mark_onboarded and page in APP_PAGES:
        st.session_state["onboarding_complete"] = True
    return page


def _clear_stale_route_flags() -> None:
    for key in [
        "_wz_force_page",
        "_wz_force_workobot",
        "_wz_allow_workobot_route",
        "workobot_mode",
        "start_real_interview_now",
        "current_page",
        "active_page",
        "selected_page",
        "workzo_active_page",
    ]:
        try:
            st.session_state.pop(key, None)
        except Exception:
            pass


def _force_landing_first_run_if_needed() -> bool:
    """Return True when this run was forced to landing.

    This fixes the user's issue: previous testing leaves cv_text/onboarding_complete/page=dashboard
    in Streamlit session_state, so the app appears to skip landing/onboarding. We intentionally
    reset the route once after this router version loads. After the user clicks through landing,
    the route is no longer reset.
    """
    if st.session_state.get("_wz145_landing_route_checked"):
        return False

    st.session_state["_wz145_landing_route_checked"] = True

    # If a button explicitly queued navigation before the router executes, respect it.
    if st.session_state.get("_workzo_pending_nav"):
        return False

    # Always restore the public start on the first run of this router version.
    # This ignores stale CV/test/demo data that previously made _has_user_context() skip landing.
    _clear_stale_route_flags()
    st.session_state["onboarding_complete"] = False
    _sync_page("landing", mark_onboarded=False)
    _set_query_page("landing")
    return True


def go_to(page: str, **extra) -> None:
    """Global safe navigation helper for all modules."""
    if st is None:
        return
    current = _normalize_page(st.session_state.get("page"), "landing")
    target = _normalize_page(page)

    if current != target:
        st.session_state.setdefault("wz_nav_stack", []).append(current)

    for k, v in extra.items():
        st.session_state[k] = v

    # Clicking into onboarding means the user started the flow, but onboarding is not complete yet.
    if target in PUBLIC_PAGES:
        st.session_state["onboarding_complete"] = False
        _sync_page(target, mark_onboarded=False)
    else:
        st.session_state["onboarding_complete"] = True
        _sync_page(target, mark_onboarded=True)

    _set_query_page(target)
    try:
        st.rerun()
    except Exception:
        try:
            st.experimental_rerun()
        except Exception:
            pass


def queue_navigation(page: str) -> None:
    target = _normalize_page(page)
    st.session_state["_workzo_pending_nav"] = target


def sync_navigation_state(page: str) -> None:
    target = _normalize_page(page)
    if target in PUBLIC_PAGES:
        st.session_state["onboarding_complete"] = False
        _sync_page(target, mark_onboarded=False)
    else:
        st.session_state["onboarding_complete"] = True
        _sync_page(target, mark_onboarded=True)
    _set_query_page(target)


def consume_pending_navigation() -> None:
    target = st.session_state.pop("_workzo_pending_nav", None)
    if target:
        sync_navigation_state(target)


def go_back() -> None:
    stack = st.session_state.get("wz_nav_stack") or []
    while stack:
        target = _normalize_page(stack.pop(), "landing")
        if target:
            st.session_state["wz_nav_stack"] = stack
            sync_navigation_state(target)
            try:
                st.rerun()
            except Exception:
                pass
            return
    go_to("landing")


def go_home() -> None:
    go_to("real_interview")


def finish_onboarding_to_interview(**extra) -> None:
    """Canonical post-onboarding destination."""
    for k, v in extra.items():
        st.session_state[k] = v
    st.session_state["onboarding_complete"] = True
    st.session_state["_wz_started_real_interview_flow"] = True
    st.session_state["_wz154_after_onboarding_main"] = True
    for _k in ["workobot_mode", "start_real_interview_now", "_wz_force_workobot", "_wz_allow_workobot_route"]:
        try:
            st.session_state.pop(_k, None)
        except Exception:
            pass
    _sync_page("real_interview", mark_onboarded=True)
    _set_query_page("real_interview")
    try:
        st.rerun()
    except Exception:
        pass


def _render_requested_page(requested: str) -> None:
    if requested == "landing":
        fn = globals().get("show_landing_page") or globals().get("show_landing")
        if callable(fn):
            fn()
            return

    if requested == "onboarding":
        fn = globals().get("show_onboarding")
        if callable(fn):
            fn()
            return

    # Internal pages are rendered by dashboard router.
    fn = globals().get("show_dashboard") or globals().get("show_workzo_dashboard")
    if callable(fn):
        fn()
        return

    st.error("WorkZo router could not find the required page renderer.")


def _workzo_run_router_if_available() -> None:
    """Single source of truth router."""
    if st is None:
        return

    try:
        # Final safety: reset stale dashboard/workobot route once after this router loads.
        if _force_landing_first_run_if_needed():
            _render_requested_page("landing")
            return

        consume_pending_navigation()

        requested = _normalize_page(
            st.session_state.get("page") or st.session_state.get("nav_page"),
            "landing" if not st.session_state.get("onboarding_complete") else "dashboard",
        )

        # If onboarding is not complete, block stale internal pages.
        if requested in APP_PAGES and not st.session_state.get("onboarding_complete"):
            requested = "landing"

        if requested in PUBLIC_PAGES:
            _sync_page(requested, mark_onboarded=False)
        else:
            _sync_page(requested, mark_onboarded=True)

        _render_requested_page(requested)

    except Exception as exc:
        st.error(f"WorkZo router error: {exc}")
        try:
            st.exception(exc)
        except Exception:
            pass


# Run router when this module is executed by app.py.
_workzo_run_router_if_available()
