# WorkZo AI - dashboard module patched for modular loader stability
import os
import re
import json
import time
import html
from typing import Any, Dict, List, Optional, Tuple

try:
    import streamlit as st
except Exception:  # Allows syntax checks outside Streamlit runtime
    st = None

def score_band(score):
    try:
        score = int(score or 0)
    except Exception:
        score = 0

    if score >= 85:
        return "Excellent"
    if score >= 75:
        return "Good"
    if score >= 60:
        return "Needs improvement"
    if score > 0:
        return "Weak"
    return "Not scored"

# =========================================================
# WorkZo split-module fallback: dashboard analysis
# Added by fix_workzo_dashboard_analysis.py
# Purpose: keep dashboard working when ensure_dashboard_analysis was
# left behind during modular split.
# =========================================================

def ensure_dashboard_analysis():
    """Ensure dashboard score/analysis exists without breaking existing features.

    Uses the stronger existing analysis function when available. Falls back to a
    deterministic lightweight score so the dashboard can render instead of
    crashing. This function does not overwrite a valid existing analysis.
    """
    import re
    import streamlit as st
    import json
    from typing import List, Tuple, Dict, Optional


    existing = st.session_state.get("dashboard_analysis") or st.session_state.get("resume_analysis")
    if isinstance(existing, dict) and existing:
        st.session_state["dashboard_analysis"] = existing
        # Never lower already-computed scores when user clicks Home/navigation.
        if existing.get("resume_score") is not None:
            st.session_state["cv_score_value"] = max(int(st.session_state.get("cv_score_value") or 0), int(existing.get("resume_score") or 0))
        if existing.get("ats_score") is not None:
            st.session_state["ats_score_value"] = max(int(st.session_state.get("ats_score_value") or 0), int(existing.get("ats_score") or 0))
        return existing

    cv_text = str(
        st.session_state.get("cv_text")
        or st.session_state.get("clean_structured_cv_text")
        or st.session_state.get("approved_cv_text")
        or ""
    )

    # Prefer the app's real analysis functions if they exist in the shared exec namespace.
    try:
        fn = globals().get("analyze_resume_dashboard_stable")
        if callable(fn) and cv_text.strip():
            result = fn(cv_text)
            if isinstance(result, dict) and result:
                st.session_state["dashboard_analysis"] = result
                if result.get("resume_score") is not None:
                    st.session_state["cv_score_value"] = max(int(st.session_state.get("cv_score_value") or 0), int(result.get("resume_score") or 0))
                if result.get("ats_score") is not None:
                    st.session_state["ats_score_value"] = max(int(st.session_state.get("ats_score_value") or 0), int(result.get("ats_score") or 0))
                return result
    except Exception:
        pass

    try:
        fn = globals().get("build_rule_based_dashboard_cache")
        if callable(fn) and cv_text.strip():
            result = fn(cv_text)
            if isinstance(result, dict) and result:
                st.session_state["dashboard_analysis"] = result
                if result.get("resume_score") is not None:
                    st.session_state["cv_score_value"] = max(int(st.session_state.get("cv_score_value") or 0), int(result.get("resume_score") or 0))
                if result.get("ats_score") is not None:
                    st.session_state["ats_score_value"] = max(int(st.session_state.get("ats_score_value") or 0), int(result.get("ats_score") or 0))
                return result
    except Exception:
        pass

    # Deterministic fallback. Conservative scores: avoids fake 90+ numbers.
    text_lower = cv_text.lower()
    sections = ["experience", "education", "skills", "summary", "projects"]
    section_hits = sum(1 for s in sections if s in text_lower)
    has_email = bool(re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", cv_text))
    has_phone = bool(re.search(r"(?:\+\d{1,3}[\s-]?)?(?:\(?\d+\)?[\s-]?){6,}", cv_text))
    quantified = len(re.findall(r"\b\d+\s*%|\b\d+\+|\b\d+\s*(years?|yrs?|months?)\b", cv_text, flags=re.I))
    bullet_count = len(re.findall(r"(^|\n)\s*[-•*]\s+", cv_text))
    keyword_hits = sum(1 for k in ["python", "sql", "tableau", "power bi", "support", "analysis", "dashboard", "cloud", "api", "itil", "itsm"] if k in text_lower)

    resume_score = 45 + section_hits * 5 + min(quantified, 5) * 3 + min(bullet_count, 10) + min(keyword_hits, 8)
    ats_score = 50 + section_hits * 6 + (8 if has_email else 0) + (6 if has_phone else 0) + min(keyword_hits * 2, 16)
    resume_score = max(35, min(88, int(resume_score)))
    ats_score = max(35, min(88, int(ats_score)))

    result = {
        "resume_score": resume_score,
        "ats_score": ats_score,
        "detected_role": st.session_state.get("target_role", "Not analyzed yet"),
        "professional_summary": "Upload or review your structured CV to improve this analysis." if not cv_text.strip() else "Resume analysis generated from available CV text.",
        "strengths": ["Core CV sections detected"] if section_hits else [],
        "improvements": ["Review extracted CV details", "Tailor CV to a specific job description"],
        "suggested_roles": [],
    }
    st.session_state["dashboard_analysis"] = result
    st.session_state["resume_analysis"] = result
    st.session_state["cv_score_value"] = max(int(st.session_state.get("cv_score_value") or 0), int(result.get("resume_score", resume_score) or 0))
    st.session_state["ats_score_value"] = max(int(st.session_state.get("ats_score_value") or 0), int(result.get("ats_score", ats_score) or 0))
    return result

# WorkZo modular split v138
# Source: app_workzo_v137_stable_no_feature_change.py, lines 9820-10802


def render_metric_card(title, value, subtitle=""):
    """Render a compact dashboard metric card used by show_dashboard()."""
    import html as _html
    import streamlit as st

    safe_title = _html.escape(str(title or ""))
    safe_value = _html.escape(str(value or "—"))
    safe_subtitle = _html.escape(str(subtitle or ""))
    st.markdown(
        f"""
        <div class="metric-card" style="
            padding: 18px;
            border-radius: 16px;
            background: #ffffff;
            border: 1px solid #e5e7eb;
            box-shadow: 0 4px 14px rgba(0,0,0,0.06);
            margin-bottom: 12px;
        ">
            <div class="metric-label" style="font-size: 14px; color: #6b7280; margin-bottom: 6px;">
                {safe_title}
            </div>
            <div class="metric-value" style="font-size: 28px; font-weight: 700; color: #111827;">
                {safe_value}
            </div>
            <div class="metric-foot" style="font-size: 13px; color: #6b7280; margin-top: 6px;">
                {safe_subtitle}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def get_nav_items() -> List[Tuple[str, str, str]]:
    return [
        ("dashboard", "" + txt("dashboard"), txt("dashboard_desc_short")),
        ("job_assist", "" + txt("job_assist"), txt("job_assist_desc_short")),
        ("cv_documents", txt("cv_documents"), txt("cv_documents_desc_short")),
        ("workobot", txt("workobot"), txt("workobot_desc_short")),
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
        logo_src = None
        try:
            logo_src = image_to_data_uri(ICON_PATH) or image_to_data_uri(LOGO_PATH)
        except Exception:
            logo_src = None
        if logo_src:
            st.markdown(f"""
            <div class='workzo-sidebar-brand-wrap'>
                <img src='{logo_src}' class='workzo-sidebar-logo' alt='WorkZo AI logo'>
                <div>
                    <div class='workzo-sidebar-brand'>WORKZO AI</div>
                    <div class='workzo-sidebar-version'>Beta V10.1 · guided workspace</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class='workzo-sidebar-brand-wrap'>
                <div class='workzo-sidebar-logo-fallback'>WZ</div>
                <div>
                    <div class='workzo-sidebar-brand'>WORKZO AI</div>
                    <div class='workzo-sidebar-version'>Beta V10.1 · guided workspace</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        st.button("Dashboard", key="sidebar_dashboard_home_button", use_container_width=True, on_click=queue_navigation, args=("dashboard",))

        st.markdown("<div class='workzo-sidebar-section-label'>Profile</div>", unsafe_allow_html=True)
        country_sidebar = html.escape(str(st.session_state.get('country', txt('not_specified')) or txt('not_specified')))
        st.markdown(f"<div class='workzo-sidebar-chip'><span class='workzo-profile-chip-label'>{html.escape(ui_label('Country'))}</span><span class='workzo-profile-chip-value'> {country_sidebar}</span></div>", unsafe_allow_html=True)
        user_status_sidebar = str(st.session_state.get('user_status', txt('not_specified')) or txt('not_specified'))
        if user_status_sidebar.strip():
            st.markdown(f"<div class='workzo-sidebar-chip'><span class='workzo-profile-chip-label'>{html.escape(ui_label('Career status'))}</span><span class='workzo-profile-chip-value'> {html.escape(user_status_sidebar)}</span></div>", unsafe_allow_html=True)
        resume_status = ui_label("Resume uploaded") if str(st.session_state.get("cv_text", "")).strip() else ui_label("No resume yet")
        st.markdown(f"<div class='workzo-sidebar-chip'><span class='workzo-profile-chip-label'>{html.escape(ui_label('Resume'))}</span><span class='workzo-profile-chip-value'> {html.escape(resume_status)}</span></div>", unsafe_allow_html=True)
        if st.session_state.get("migration_country") and st.session_state.get("migration_country") != st.session_state.country:
            st.markdown(f"<div class='workzo-sidebar-chip'><span class='workzo-profile-chip-label'>{html.escape(ui_label('Target market'))}</span><span class='workzo-profile-chip-value'> {html.escape(str(st.session_state.migration_country))}</span></div>", unsafe_allow_html=True)

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
            nav_labels["founder_dashboard"] = "" + txt("founder_dashboard")
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
        computed_readiness = int(round((sum(workflow_steps_done) / len(workflow_steps_done)) * 100)) if workflow_steps_done else 0
        application_readiness = max(int(st.session_state.get("application_readiness_value") or 0), computed_readiness)
        st.session_state["application_readiness_value"] = application_readiness
        resume_score = int(st.session_state.get("cv_score_value") or 0)
        ats_score = int(st.session_state.get("ats_score_value") or 0)

        st.markdown(f"""
        <div class="workzo-dashboard-hero-compact">
            <div class="workzo-hero-kicker">{html.escape(ui_label('Career workspace'))}</div>
            <div class="workzo-hero-title">{html.escape(ui_label('One guided journey: Add details → Score → Improve → Find job → Prepare'))}</div>
            <div class="next-action-copy">{html.escape(ui_label('Your CV, country, language, job description, scores, and edits are reused across the app. Later, login/subscription can save this same workspace permanently.'))}</div>
            <div class="workzo-chip-row">
                <span class="workzo-dashboard-chip"> {html.escape(str(st.session_state.get('country', 'Not specified')))}</span>
                <span class="workzo-dashboard-chip">{html.escape(str(st.session_state.get('preferred_language', 'English')))}</span>
                <span class="workzo-dashboard-chip">{html.escape('CV ready' if cv_ready else 'CV missing')}</span>
                <span class="workzo-dashboard-chip"> {html.escape('Job added' if job_ready else 'Job not added')}</span>
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

        # Personalized next-step plan: uses the same profile context as the tools.
        try:
            if callable(globals().get("workzo_sync_user_profile")):
                workzo_sync_user_profile()
        except Exception:
            pass
        target_country_plan = st.session_state.get("user_profile", {}).get("target_country") or st.session_state.get("country", "")
        target_role_plan = st.session_state.get("target_role") or st.session_state.get("detected_target_role") or ui_label("your target role")
        next_steps = []
        if not cv_ready:
            next_steps.append(ui_label("Add or import your CV first."))
        if cv_ready and not improved_ready:
            next_steps.append(ui_label(f"Improve your CV for {target_country_plan} and {target_role_plan}."))
        if not job_ready:
            next_steps.append(ui_label(f"Analyze one real job description for {target_country_plan}."))
        if not prepared_ready:
            next_steps.append(ui_label("Generate interview and application preparation notes."))
        next_steps.append(ui_label("Apply to a small set of matching roles and track what works."))
        plan_html = "".join(f"<li>{html.escape(str(step))}</li>" for step in next_steps[:5])
        st.markdown(f"""
        <div class='next-action-card'>
            <div class='next-action-label'>{html.escape(ui_label('Your next best career move'))}</div>
            <div class='next-action-title'>{html.escape(str(target_role_plan))} · {html.escape(str(target_country_plan))}</div>
            <div class='next-action-copy'><ol>{plan_html}</ol></div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"### {html.escape(ui_label('Application progress'))}")
        st.caption(ui_label("Move step by step, or jump to the part you want to work on."))
        progress_cols = st.columns(4)
        progress_items = [
            ("1", ui_label("CV added"), cv_ready, "onboarding", ui_label("Edit CV")),
            ("2", ui_label("Job analyzed"), job_ready, "job_assist", ui_label("Analyze job")),
            ("3", ui_label("CV improved"), improved_ready, "cv_documents", ui_label("Improve CV")),
            ("4", ui_label("Prepared to apply"), prepared_ready, "job_assist", ui_label("Prepare")),
        ]
        for col, (num, title, done, target, button_text) in zip(progress_cols, progress_items):
            with col:
                active_class = "done" if done else ""
                status_text = ui_label("Completed") if done else ui_label("Still pending")
                st.markdown(f"""
                <div class='workzo-progress-card {active_class}'>
                    <div>
                        <div class='workzo-progress-title'>{'✅ ' if done else ''}{html.escape(num)}. {html.escape(title)}</div>
                        <div class='workzo-progress-status'>{html.escape(status_text)}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button(button_text, key=f"dashboard_progress_nav_{num}_{target}", use_container_width=False):
                    if target == "onboarding":
                        st.session_state.page = "onboarding"
                        st.session_state.nav_page = "onboarding"
                        request_scroll_to_top()
                        st.rerun()
                    else:
                        queue_navigation(target)
                        st.rerun()



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
        
    /* WorkZo v11.1: use resume option cards as direct buttons */
    div[data-testid="stButton"] > button {
        white-space: pre-line !important;
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
            st.markdown("""
<div class='next-action-card' style='margin-top:4px;'>
  <div class='next-action-label'>Career search assistant</div>
  <div class='next-action-title'>Find fewer, better jobs — then tailor your CV for the best one</div>
  <div class='next-action-copy'>WorkZo expands your search terms, scans live sources, ranks matches, and shows a reality check before you apply.</div>
</div>
""", unsafe_allow_html=True)

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
                help="Leave this empty and WorkZo will use roles detected from your CV. Add 2-4 titles for better matching."
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
                    normalized_location = normalize_location_for_job_search(final_location, search_country)
                    with st.status("Building your curated job search...", expanded=True) as status:
                        st.write("Reading your CV and expanding realistic role titles...")
                        expansion = generate_job_query_expansion(cv_for_jobs or st.session_state.cv_text, search_country, normalized_location, job_status_for_search, target_titles)
                        st.session_state["latest_job_query_expansion"] = expansion

                        roles_from_input = build_role_suggestions(
                            expansion.get("job_titles", []) + [x.strip() for x in target_titles.split(",") if x.strip()],
                            st.session_state.get("suggested_roles_detected", []),
                            st.session_state.get("current_role_detected", "")
                        )

                        st.write("Scanning live sources with precise title + hard-skill queries...")
                        precise_search_roles = expansion.get("search_queries", [])[:8] or roles_from_input[:6]
                        live_jobs = fetch_live_jobs_global(search_country, precise_search_roles, normalized_location, job_status_for_search)

                        st.write("Ranking jobs by CV fit, seniority risk, and verified skills...")
                        curated_jobs = curate_job_matches(live_jobs, cv_for_jobs, expansion, search_country, job_status_for_search, limit=18)
                        st.session_state["latest_curated_jobs"] = curated_jobs

                        st.write("Preparing strategy and next steps...")
                        plan = generate_job_search_plan(
                            search_country,
                            normalized_location,
                            roles_from_input,
                            cv_for_jobs,
                            curated_jobs
                        )
                        status.update(label="Curated job search ready", state="complete", expanded=False)

                    render_query_expansion_panel(expansion)
                    render_job_plan(plan)
                    render_curated_job_matches(curated_jobs, search_country)
                    render_job_board_search_cards(search_country, normalized_location, expansion.get("search_queries", [])[:6] or roles_from_input, job_status_for_search)

        elif job_assist_mode == "understand":
            st.markdown(f"### {txt('understand_job')}")
            st.caption("Paste a job description and WorkZo will help you decide whether to apply, what matches, what is missing, and how to tailor your CV.")

            # Keep the pasted job description when users move to Improve CV and come back.
            if not st.session_state.get("job_desc_v42") and st.session_state.get("last_understand_job_description"):
                st.session_state["job_desc_v42"] = st.session_state.get("last_understand_job_description", "")
            job_desc = st.text_area("Paste the job description", key="job_desc_v42", height=220)

            # Show cached analysis so the page does not feel reset after reruns/navigation.
            cached_analysis = st.session_state.get("latest_job_analysis")
            if cached_analysis and st.session_state.get("last_understand_job_description") == (job_desc or "").strip():
                try:
                    cached_data = safe_json_loads(cached_analysis) if isinstance(cached_analysis, str) else cached_analysis
                except Exception:
                    cached_data = {}
                if isinstance(cached_data, dict) and cached_data:
                    render_understand_job_analysis(cached_data)
                    st.markdown("---")
                    st.markdown("### Next step")
                    st.caption("Use this job description to tailor your CV in the CV & Documents section.")
                    if st.button("Improve CV for this Job", key="btn_understand_to_improve_cv_cached"):
                        st.session_state["improve_cv_for_job_desc"] = st.session_state.get("last_understand_job_description", (job_desc or "").strip())
                        st.session_state["document_tools_mode"] = "Improve CV for a Job"
                        sync_navigation_state("cv_documents")
                        st.rerun()

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
                                    sync_navigation_state("cv_documents")
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
                    r"(?im)^\s*(?:about|uber)\s+([A-Z][A-Za-z0-9&.,\- ]{2,60})\s*$",
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
                        "resume": "Use an achievement-focused 1-2 page resume. Avoid photo, date of birth, marital status, and sensitive personal details.",
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
                        "resume": "Use a clean 1-2 page CV focused on profile, key skills, experience, and achievements. Avoid unnecessary personal data.",
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

6. Market Smart Guide for {target_market}
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
                        st.markdown(f"<div class='workzo-step-pill {'done' if done else ''}'><b>{'✅ ' if done else 'Pending '}{label}</b><div class='state'>{'Completed' if done else 'Next step pending'}</div></div>", unsafe_allow_html=True)

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
                st.markdown("### Market Smart Guide")
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
                        "Market Smart Guide",
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
                    if st.button("Start interview practice", key="voice_mock_interview_setup", use_container_width=True):
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
- Prepare 5-7 interview answers.
- Check country-specific application expectations.
- Review job platform/application instructions.
- Save the application in your tracker.
""")

                with st.expander("View full AI-generated preparation guide", expanded=False):
                    st.markdown(latest_prep)


                st.markdown("### Next actions")
                st.caption("Recommended order: tailor your CV, create a cover letter, save the application, apply for the role, then start interview practice when HR responds.")
                st.markdown("<div class='workzo-action-grid'>", unsafe_allow_html=True)
                n1, n2, n3, n4 = st.columns(4)
                with n1:
                    if st.button("Improve CV", key="prep_to_cv_documents", use_container_width=True):
                        st.session_state["improve_cv_for_job_desc"] = st.session_state.get("last_prepare_job_description", job_desc_prepare)
                        st.session_state["prepare_cv_tailored"] = True
                        st.session_state["document_tools_mode"] = "Improve / Update CV"
                        queue_navigation("cv_documents")
                        st.rerun()
                with n2:
                    if st.button("Interview practice", key="prep_to_workobot", use_container_width=True):
                        st.session_state["workobot_prefill"] = "Act as a live voice interview coach. Ask me one interview question at a time for the job I just prepared for. After each answer, give feedback and continue."
                        queue_navigation("workobot")
                        st.rerun()
                with n3:
                    if st.button(" Cover letter", key="prep_to_cover_letter", use_container_width=True):
                        st.session_state["cover_letter_job_desc"] = st.session_state.get("last_prepare_job_description", job_desc_prepare)
                        st.session_state["document_tools_mode"] = "Cover Letter Generator + Language"
                        queue_navigation("cv_documents")
                        st.rerun()
                with n4:
                    if st.button("Save tracker", key="save_prepared_job_to_tracker", use_container_width=True):
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
                with n4:
                    if st.button("Interview practice after HR reply", key="prep_to_workobot", use_container_width=True):
                        st.session_state["workobot_prefill"] = "Act as a realistic employer interviewer for the prepared job. Ask role-specific questions based on my CV and the job description. Keep questions in my selected language. Ask one question at a time."
                        st.session_state["prepare_interview_started"] = True
                        queue_navigation("workobot")
                        st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

                if st.button("✅ Mark CV as tailored", key="mark_prepare_cv_tailored_manual", use_container_width=False):
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
    st.caption("WORKZO AI V11.2 • Beta • Stable Scores + Editable CV Source")
    st.caption("⚠️ WorkZo AI is currently in Beta. Some results may not be perfect yet. Your feedback helps improve the tool. CV text and personal documents are not stored in analytics.")

# =========================================================

# =========================================================
# WORKZO V11.7 - JD-SPECIFIC INTERVIEW ASSISTANT
# =========================================================
