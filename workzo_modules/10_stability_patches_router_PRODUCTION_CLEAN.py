"""WorkZo AI - single-render production router.

Replace workzo_modules/10_stability_patches_router.py with this file.
It renders exactly one page per Streamlit run and never uses query-param links.
"""
from __future__ import annotations

try:
    import streamlit as st
except Exception:
    st = None

PAGE_ALIASES = {
    "home":"dashboard", "main":"dashboard", "dashboard":"dashboard",
    "cv":"improve_cv", "improve":"improve_cv", "improve_cv":"improve_cv", "update_cv":"improve_cv",
    "edit_cv":"cv_preview", "preview_cv":"cv_preview", "cv_preview":"cv_preview", "cv_editor":"cv_preview",
    "cover":"cover_letter", "cover_letter":"cover_letter", "cover_letter_generator":"cover_letter",
    "jobs":"find_jobs", "find_job":"find_jobs", "find_jobs":"find_jobs", "job_match":"find_jobs",
    "understand":"understand_job", "understand_job":"understand_job", "analyze_job":"understand_job",
    "interview":"real_interview", "interview_practice":"real_interview", "real_interview":"real_interview", "start_interview":"real_interview",
    "founder":"founder_dashboard", "founder_dashboard":"founder_dashboard",
    "landing":"landing", "onboarding":"onboarding",
}
APP_PAGES = {"dashboard","improve_cv","cv_preview","cover_letter","find_jobs","understand_job","real_interview","founder_dashboard"}

def _normalize_page(value=None, default="dashboard"):
    raw = str(value or default).strip()
    return PAGE_ALIASES.get(raw, raw if raw in APP_PAGES | {"landing","onboarding"} else default)

def _has_context() -> bool:
    return any(bool(st.session_state.get(k)) for k in ["cv_text","uploaded_cv_text","clean_structured_cv_text","workzo_live_cv_text","structured_cv_json","selected_job_description","current_job_description","job_description"])

def _sync(page: str) -> str:
    page = _normalize_page(page)
    for key in ["page","nav_page","current_page","active_page","selected_page","workzo_active_page"]:
        st.session_state[key] = page
    if page in APP_PAGES:
        st.session_state["onboarding_complete"] = True
    return page

def go_to(page: str, **extra):
    current = _normalize_page(st.session_state.get("page"), "dashboard")
    target = _normalize_page(page)
    if current != target:
        st.session_state.setdefault("wz_nav_stack", []).append(current)
    for k,v in extra.items(): st.session_state[k] = v
    _sync(target)
    try: st.rerun()
    except Exception:
        try: st.experimental_rerun()
        except Exception: pass

def go_back():
    stack = st.session_state.get("wz_nav_stack") or []
    while stack:
        target = _normalize_page(stack.pop())
        if target not in {"landing","onboarding"}:
            st.session_state["wz_nav_stack"] = stack
            _sync(target)
            try: st.rerun()
            except Exception:
                try: st.experimental_rerun()
                except Exception: pass
            return
    go_to("dashboard")

def _workzo_run_router_if_available() -> None:
    if st is None: return
    if "onboarding_complete" not in st.session_state:
        st.session_state["onboarding_complete"] = _has_context()

    requested = _normalize_page(st.session_state.get("page"), "dashboard" if st.session_state.get("onboarding_complete") else "landing")
    if requested in APP_PAGES: st.session_state["onboarding_complete"] = True
    requested = _sync(requested)

    # Render exactly one branch and return immediately.
    if requested == "landing" and not st.session_state.get("onboarding_complete"):
        fn = globals().get("show_landing_page")
        if callable(fn): fn(); return
    if requested == "onboarding" or not st.session_state.get("onboarding_complete"):
        fn = globals().get("show_onboarding")
        if callable(fn): fn(); return

    fn = globals().get("show_dashboard") or globals().get("show_workzo_dashboard")
    if callable(fn):
        fn(); return
    st.error("WorkZo router could not find show_dashboard().")

_workzo_run_router_if_available()
