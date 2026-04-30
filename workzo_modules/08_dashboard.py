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
    """Preferred Language controls app labels, AI replies, and generated documents."""
    language = str(language or "English").strip() or "English"
    st.session_state.preferred_language = language
    st.session_state.language = language
    st.session_state.ui_language = language
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
        _prev_language = st.session_state.get("preferred_language", "English")
        preferred = st.selectbox(
            txt("preferred_language"),
            language_list,
            index=language_list.index(current_language),
            key="sidebar_preferred_language",
            help=txt("preferred_language_help")
        )
        set_single_preferred_language(preferred)
        if preferred != _prev_language:
            try:
                st.query_params["wz_lang"] = preferred
            except Exception:
                pass
            st.rerun()

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



        st.markdown("<div class='workzo-sidebar-section-label'>Company Context</div>", unsafe_allow_html=True)
        with st.expander("🏢 Company context", expanded=False):
            st.caption("Optional: paste the company website. WorkZo will use it for cover letters, mock tests, and interview preparation.")
            _current_company_url = str(st.session_state.get("target_company_website") or st.session_state.get("company_website") or "")
            _sidebar_company_url = st.text_input(
                "Company website",
                value=_current_company_url,
                placeholder="https://company.com",
                key="target_company_website_sidebar",
            )
            if _sidebar_company_url.strip() != _current_company_url.strip():
                st.session_state["company_website"] = _sidebar_company_url.strip()
                st.session_state["company_website"] = _sidebar_company_url.strip()
            if st.session_state.get("target_company_website"):
                st.caption("Saved for AI outputs in this session.")
            if st.button("Clear company context", key="clear_company_context_sidebar", use_container_width=True):
                for _k in ["target_company_website", "company_website", "target_company_context", "company_context_enabled"]:
                    st.session_state.pop(_k, None)
                st.rerun()

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

        # WorkZo Command Center: simple, smart, action-oriented dashboard.
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

        target_country_plan = st.session_state.get("migration_country") or st.session_state.get("country", "Not specified")
        target_role_plan = st.session_state.get("target_role") or st.session_state.get("detected_target_role") or st.session_state.get("current_role_detected") or ui_label("your target role")
        company_context = st.session_state.get("target_company_website", "")

        # Decide one clear next action. This replaces long feature lists.
        if not cv_ready:
            next_title = ui_label("Add your CV first")
            next_desc = ui_label("Upload or create your CV so WorkZo can score it, improve it, and match jobs.")
            next_button = ui_label("Start setup")
            next_target = "onboarding"
        elif ats_score and ats_score < 75:
            next_title = ui_label("Improve your CV before applying")
            next_desc = ui_label("Your ATS score needs work. Start with a cleaner, job-focused CV.")
            next_button = ui_label("Improve CV")
            next_target = "cv_documents"
        elif not job_ready:
            next_title = ui_label("Paste one real job description")
            next_desc = ui_label("WorkZo can compare your CV with the job and tell you whether to apply or tailor first.")
            next_button = ui_label("Understand a Job")
            next_target = "job_assist"
        elif not prepared_ready:
            next_title = ui_label("Prepare your application")
            next_desc = ui_label("Generate cover-letter focus, interview questions, and application strategy for this job.")
            next_button = ui_label("Prepare Application")
            next_target = "job_assist"
        else:
            next_title = ui_label("Practice and apply")
            next_desc = ui_label("Your application flow is ready. Use Work-O-Bot to practice answers or prepare messages.")
            next_button = ui_label("Open Work-O-Bot")
            next_target = "workobot"

        st.markdown(f"""
        <style>
        .wz-command-hero {{
            border: 1px solid rgba(20,184,166,0.28);
            border-radius: 24px;
            padding: 22px 24px;
            background: linear-gradient(135deg, rgba(37,99,235,0.24), rgba(20,184,166,0.14));
            box-shadow: 0 16px 44px rgba(2,6,23,0.26);
            margin: 10px 0 18px 0;
        }}
        .wz-command-kicker {{ color:#93c5fd; font-size:.78rem; font-weight:850; text-transform:uppercase; letter-spacing:.08em; margin-bottom:6px; }}
        .wz-command-title {{ color:#f8fafc; font-size:1.55rem; font-weight:900; line-height:1.22; margin-bottom:8px; }}
        .wz-command-copy {{ color:#dbeafe; font-size:.98rem; line-height:1.48; max-width:920px; }}
        .wz-smart-card {{ border:1px solid rgba(148,163,184,.16); border-radius:20px; padding:16px; background:rgba(15,23,42,.55); min-height:132px; margin-bottom:12px; }}
        .wz-smart-card.active {{ border-color:rgba(20,184,166,.45); background:linear-gradient(135deg, rgba(20,184,166,.16), rgba(37,99,235,.12)); }}
        .wz-smart-label {{ color:#94a3b8; font-size:.75rem; font-weight:850; text-transform:uppercase; letter-spacing:.07em; margin-bottom:6px; }}
        .wz-smart-title {{ color:#f8fafc; font-size:1.05rem; font-weight:850; margin-bottom:6px; }}
        .wz-smart-copy {{ color:#cbd5e1; font-size:.9rem; line-height:1.42; }}
        .wz-step-pill {{ border:1px solid rgba(148,163,184,.14); background:rgba(15,23,42,.42); border-radius:16px; padding:12px; min-height:88px; }}
        .wz-step-pill.done {{ border-color:rgba(20,184,166,.42); background:rgba(20,184,166,.11); }}
        .wz-step-title {{ color:#f8fafc; font-weight:800; font-size:.92rem; }}
        .wz-step-state {{ color:#94a3b8; font-size:.82rem; margin-top:5px; }}
        </style>
        <div class="wz-command-hero">
            <div class="wz-command-kicker">{html.escape(ui_label('Command Center'))}</div>
            <div class="wz-command-title">{html.escape(ui_label('Your next best career move, simplified'))}</div>
            <div class="wz-command-copy">
                {html.escape(ui_label('WorkZo uses your CV, selected country, language, job description, and company context to guide one clear next step instead of showing too many tools at once.'))}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Top KPI row: immediate signal, not long explanation.
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            render_metric_card(ui_label("Career Health"), f"{application_readiness}%", ui_label("Overall application readiness"))
        with k2:
            render_metric_card(txt("resume_score"), str(resume_score or "—"), score_band(resume_score) if resume_score else ui_label("Needs CV analysis"))
        with k3:
            render_metric_card(txt("ats_score"), str(ats_score or "—"), score_band(ats_score) if ats_score else ui_label("ATS check pending"))
        with k4:
            role_short = str(target_role_plan or ui_label("Not detected"))[:32]
            render_metric_card(ui_label("Target Role"), role_short, str(target_country_plan or "")[:36])

        st.markdown(f"""
        <div class="wz-smart-card active">
            <div class="wz-smart-label">{html.escape(ui_label('Next best action'))}</div>
            <div class="wz-smart-title">{html.escape(str(next_title))}</div>
            <div class="wz-smart-copy">{html.escape(str(next_desc))}</div>
        </div>
        """, unsafe_allow_html=True)

        if st.button(next_button, key="wz_command_center_next_action", use_container_width=True):
            track_button_click(str(next_button), "Dashboard Command Center")
            if next_target == "onboarding":
                st.session_state.page = "onboarding"
                st.session_state.nav_page = "onboarding"
                request_scroll_to_top()
            elif next_target == "job_assist" and not job_ready:
                st.session_state["job_assist_mode_key"] = "understand"
                queue_navigation("job_assist")
            elif next_target == "job_assist":
                st.session_state["job_assist_mode_key"] = "prepare"
                queue_navigation("job_assist")
            else:
                queue_navigation(next_target)
            st.rerun()

        st.markdown(f"### {html.escape(ui_label('Smart actions'))}")
        st.caption(ui_label("Choose one action. WorkZo reuses your existing CV, country, language, and company context."))
        a1, a2, a3, a4 = st.columns(4)
        with a1:
            st.markdown(f"""
            <div class="wz-smart-card">
                <div class="wz-smart-label">CV</div>
                <div class="wz-smart-title">{html.escape(ui_label('Improve CV'))}</div>
                <div class="wz-smart-copy">{html.escape(ui_label('Make your CV cleaner, more ATS-friendly, and job-specific.'))}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(ui_label("Open CV Tools"), key="wz_action_cv", use_container_width=True):
                queue_navigation("cv_documents")
                st.rerun()
        with a2:
            st.markdown(f"""
            <div class="wz-smart-card">
                <div class="wz-smart-label">Jobs</div>
                <div class="wz-smart-title">{html.escape(ui_label('Find Jobs'))}</div>
                <div class="wz-smart-copy">{html.escape(ui_label('Search global roles using your CV and selected country.'))}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(ui_label("Find Jobs"), key="wz_action_jobs", use_container_width=True):
                st.session_state["job_assist_mode_key"] = "find"
                queue_navigation("job_assist")
                st.rerun()
        with a3:
            st.markdown(f"""
            <div class="wz-smart-card">
                <div class="wz-smart-label">Application</div>
                <div class="wz-smart-title">{html.escape(ui_label('Cover Letter'))}</div>
                <div class="wz-smart-copy">{html.escape(ui_label('Generate a focused cover letter based on your CV and job description.'))}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(ui_label("Create Cover Letter"), key="wz_action_cover", use_container_width=True):
                st.session_state["document_tools_mode"] = "Cover Letter Generator + Language"
                queue_navigation("cv_documents")
                st.rerun()
        with a4:
            st.markdown(f"""
            <div class="wz-smart-card">
                <div class="wz-smart-label">Coach</div>
                <div class="wz-smart-title">Work-O-Bot</div>
                <div class="wz-smart-copy">{html.escape(ui_label('Practice answers, messages, German/English, and career communication.'))}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(ui_label("Practice"), key="wz_action_workobot", use_container_width=True):
                queue_navigation("workobot")
                st.rerun()

        st.markdown(f"### {html.escape(ui_label('Application flow'))}")
        f1, f2, f3, f4 = st.columns(4)
        flow = [
            (f1, ui_label("CV added"), cv_ready),
            (f2, ui_label("Job analyzed"), job_ready),
            (f3, ui_label("CV improved"), improved_ready),
            (f4, ui_label("Ready to apply"), prepared_ready),
        ]
        for col, label, done in flow:
            with col:
                st.markdown(f"""
                <div class="wz-step-pill {'done' if done else ''}">
                    <div class="wz-step-title">{'✅ ' if done else '⬜ '}{html.escape(str(label))}</div>
                    <div class="wz-step-state">{html.escape(ui_label('Completed') if done else ui_label('Pending'))}</div>
                </div>
                """, unsafe_allow_html=True)

        if company_context:
            st.info(ui_label("Company context is active. Cover letters and preparation can use the company website you added in the toolbox."))
        else:
            st.caption(ui_label("Tip: Add a company website in the left toolbox to make cover letters and preparation more company-specific."))


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
                        "Market Smart Guide",
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
                    st.markdown("#### Real Interview Simulation")
                    st.info("Use this after applying or when HR invites you for an interview. WorkZo will practice the exact interview using your CV and this job description.")
                    st.markdown(interview_text or "Prepare answers for role fit, technical skills, problem solving, communication, motivation, and country-specific expectations.")
                    if st.button("Start Real Interview Simulation", key="real_interview_setup_from_prepare", use_container_width=True):
                        st.session_state["real_interview_jd"] = st.session_state.get("last_prepare_job_description", job_desc_prepare)
                        st.session_state["real_interview_company"] = target_company or ""
                        st.session_state["prepare_interview_started"] = True
                        st.session_state["workobot_prefill"] = "Start Real Interview Simulation for my prepared job. Use my CV and the saved job description. Ask one question at a time and give specific feedback."
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
                st.caption("Recommended order: tailor your CV, create a cover letter, save the application, apply for the role, then start Work-O-Bot when HR responds.")
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
                    if st.button("Cover letter", key="prep_to_cover_letter", use_container_width=True):
                        st.session_state["cover_letter_job_desc"] = st.session_state.get("last_prepare_job_description", job_desc_prepare)
                        st.session_state["document_tools_mode"] = "Cover Letter Generator + Language"
                        queue_navigation("cv_documents")
                        st.rerun()
                with n3:
                    if st.button("Save tracker", key="save_prepared_job_to_tracker", use_container_width=True):
                        if "application_tracker" not in st.session_state:
                            st.session_state.application_tracker = []
                        title_guess = (target_job_title or "").strip() or "Prepared job"
                        if title_guess == "Prepared job":
                            m = re.search(r"(?i)(job title|role|position)[:\-]\s*(.+)", job_desc_prepare[:1000])
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
                    if st.button("Interview after HR reply", key="prep_to_real_interview_after_hr", use_container_width=True):
                        st.session_state["real_interview_jd"] = st.session_state.get("last_prepare_job_description", job_desc_prepare)
                        st.session_state["real_interview_company"] = target_company or ""
                        st.session_state["workobot_prefill"] = "Start Real Interview Simulation for my prepared job. Use my CV and the saved job description."
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

    elif page_key in ["workobot", "workobot", "career_insights"]:
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

# =========================================================
# WorkZo v15 dashboard score stabilizer
# =========================================================
def _wz15_restore_best_scores():
    try:
        import streamlit as st
        for key in ["cv_score_value", "ats_score_value", "application_readiness_value"]:
            best_key = "_best_" + key
            cur = int(st.session_state.get(key) or 0)
            best = int(st.session_state.get(best_key) or 0)
            if cur < best:
                st.session_state[key] = best
            else:
                st.session_state[best_key] = cur
    except Exception:
        pass
try:
    _wz15_old_show_dashboard = show_dashboard
    def show_dashboard():
        _wz15_restore_best_scores()
        result = _wz15_old_show_dashboard()
        _wz15_restore_best_scores()
        return result
except Exception:
    pass

# =========================================================
# WorkZo v19 - simplified product dashboard override
# Purpose: one clear dashboard purpose, 3 primary cards, stable scores,
# and cleaner sidebar navigation.
# =========================================================
def _wz19_int_score(*keys, default=0):
    try:
        for key in keys:
            val = st.session_state.get(key)
            if val is not None and str(val).strip() != "":
                return max(0, min(100, int(float(val))))
    except Exception:
        pass
    return default


def _wz19_preserve_best_scores():
    """Do not let Home/Dashboard navigation reduce already-computed scores."""
    try:
        for key in ["cv_score_value", "resume_score", "ats_score_value", "application_readiness_value", "interview_score"]:
            cur = _wz19_int_score(key, default=0)
            best_key = "_best_" + key
            best = _wz19_int_score(best_key, default=0)
            if cur < best:
                st.session_state[key] = best
            else:
                st.session_state[best_key] = cur
    except Exception:
        pass


def _wz19_go(page_key: str):
    """Navigation helper that keeps state stable and nudges Streamlit to start at top."""
    try:
        _wz19_preserve_best_scores()
        st.session_state["page"] = page_key
        st.session_state["nav_page"] = page_key
        st.session_state["scroll_anchor"] = "top"
        st.session_state["_wz_top_counter"] = int(st.session_state.get("_wz_top_counter", 0)) + 1
        try:
            st.query_params["page"] = page_key
            st.query_params["top"] = str(st.session_state["_wz_top_counter"])
        except Exception:
            pass
        st.rerun()
    except Exception:
        st.session_state["page"] = page_key
        st.session_state["nav_page"] = page_key
        st.rerun()


def _wz19_current_name():
    for key in ["user_name", "full_name", "candidate_name"]:
        value = str(st.session_state.get(key, "") or "").strip()
        if value:
            return value.split()[0]
    try:
        cv = st.session_state.get("structured_cv_json") or st.session_state.get("workzo_live_cv_structured") or {}
        name = str(cv.get("full_name") or cv.get("name") or "").strip()
        if name:
            return name.split()[0]
    except Exception:
        pass
    return "there"


def _wz19_render_sidebar(page_key: str):
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
                    <div class='workzo-sidebar-version'>Guided career workspace</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class='workzo-sidebar-brand-wrap'>
                <div class='workzo-sidebar-logo-fallback'>WZ</div>
                <div>
                    <div class='workzo-sidebar-brand'>WORKZO AI</div>
                    <div class='workzo-sidebar-version'>Guided career workspace</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div class='workzo-sidebar-section-label'>Navigation</div>", unsafe_allow_html=True)
        nav = [
            ("dashboard", "Dashboard"),
            ("cv_documents", "My CV"),
            ("job_assist", "Job Match"),
            ("workobot", "Work-O-Bot"),
        ]
        # Founder analytics hidden in v26.
        for key, label in nav:
            shown = label + ("  ✓" if page_key == key else "")
            if st.button(shown, key=f"wz19_sidebar_{key}", use_container_width=True):
                _wz19_go(key)

        st.markdown("<div class='workzo-sidebar-section-label'>Settings</div>", unsafe_allow_html=True)
        try:
            language_list = language_options if language_options else ["English", "German", "Dutch"]
            current_language = st.session_state.get("preferred_language", "English")
            if current_language not in language_list:
                current_language = "English" if "English" in language_list else language_list[0]
            preferred = st.selectbox(
                txt("preferred_language"),
                language_list,
                index=language_list.index(current_language),
                key="wz19_sidebar_preferred_language",
            )
            set_single_preferred_language(preferred)
        except Exception:
            pass

        if st.button("Edit setup", key="wz19_edit_setup", use_container_width=True):
            try:
                reset_onboarding()
            except Exception:
                st.session_state["onboarding_complete"] = False
            _wz19_go("onboarding")


def _wz19_recommendation(cv_score: int, ats_score: int, interview_score: int):
    if not str(st.session_state.get("cv_text", "") or "").strip():
        return "Upload or create your CV first so WorkZo can guide the next steps.", "Add My CV", "cv_documents"
    if ats_score < 60:
        return "Your CV needs stronger job alignment. Compare it with a job description and fix only truthful missing keywords.", "Fix CV Match", "cv_documents"
    if interview_score < 70:
        return "Your CV is improving. The next best step is Work-O-Bot based on your CV and the job description.", "Start Practice", "workobot"
    return "You look ready to apply. Find relevant roles and track the ones you apply for.", "Find Jobs", "job_assist"


def _wz19_dashboard_home():
    _wz19_preserve_best_scores()
    name = _wz19_current_name()
    cv_score = _wz19_int_score("cv_score_value", "resume_score", default=0)
    ats_score = _wz19_int_score("ats_score_value", default=0)
    interview_score = _wz19_int_score("interview_score", "interview_readiness", default=40)
    has_job = bool(str(st.session_state.get("last_understand_job_description", "") or st.session_state.get("improve_cv_for_job_desc", "") or st.session_state.get("last_prepare_job_description", "")).strip())

    st.markdown("<div id='top'></div>", unsafe_allow_html=True)
    st.markdown("""
    <style>
    .wz19-hero {border:1px solid rgba(148,163,184,.25); border-radius:22px; padding:28px; background:linear-gradient(135deg, rgba(99,102,241,.10), rgba(20,184,166,.08)); margin-bottom:22px;}
    .wz19-title {font-size:30px; font-weight:800; margin-bottom:4px; color:#f8fafc;}
    .wz19-sub {font-size:16px; color:#cbd5e1; margin-bottom:18px;}
    .wz19-card {border:1px solid rgba(148,163,184,.25); border-radius:18px; padding:20px; min-height:190px; background:rgba(15,23,42,.35);}
    .wz19-card h3 {margin-top:0; font-size:20px;}
    .wz19-card p {color:#cbd5e1; min-height:72px;}
    .wz19-reco {border:1px solid rgba(34,197,94,.30); border-radius:18px; padding:18px; background:rgba(34,197,94,.08); margin-top:10px;}
    .wz19-small-muted {color:#94a3b8; font-size:13px;}
    div[data-testid="stButton"] > button {border-radius:12px; font-weight:650; min-height:42px;}
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class='wz19-hero'>
      <div class='wz19-title'>👋 Welcome back, {html.escape(name)}</div>
      <div class='wz19-sub'>Let’s move you closer to your next job.</div>
    </div>
    """, unsafe_allow_html=True)

    m1, m2, m3 = st.columns(3)
    m1.metric("CV Strength", f"{cv_score}%" if cv_score else "Not analyzed")
    m2.metric("Job Match", f"{ats_score}%" if has_job or ats_score else "Not analyzed")
    m3.metric("Interview Readiness", f"{interview_score}%")
    st.progress(max(cv_score, ats_score, interview_score, 1) / 100)

    if st.button("Continue Your Journey", key="wz19_continue_journey", use_container_width=True):
        msg, label, target = _wz19_recommendation(cv_score, ats_score, interview_score)
        _wz19_go(target)

    st.divider()
    st.subheader("What do you need today?")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""<div class='wz19-card'><h3>🟦 Get More Interviews</h3><p>Analyze your CV against a job, improve ATS alignment, and fix missing keywords honestly.</p></div>""", unsafe_allow_html=True)
        if st.button("Improve My CV", key="wz19_improve_cv", use_container_width=True):
            st.session_state["cv_documents_mode"] = "improve_cv"
            _wz19_go("cv_documents")
    with c2:
        st.markdown("""<div class='wz19-card'><h3>🟩 Prepare for Interview</h3><p>Practice the exact interview using your CV and the job description, then improve your answers.</p></div>""", unsafe_allow_html=True)
        if st.button("Start Work-O-Bot", key="wz19_interview", use_container_width=True):
            st.session_state["workobot_mode"] = "real_interview_simulation"
            _wz21_go("workobot")
    with c3:
        st.markdown("""<div class='wz19-card'><h3>🟧 Find Relevant Jobs</h3><p>Find better-matched roles, review job fit, and save opportunities to your tracker.</p></div>""", unsafe_allow_html=True)
        if st.button("Find Jobs", key="wz19_find_jobs", use_container_width=True):
            _wz19_go("job_assist")

    st.divider()
    st.subheader("🔍 What WorkZo suggests for you")
    reco, btn, target = _wz19_recommendation(cv_score, ats_score, interview_score)
    st.markdown(f"<div class='wz19-reco'>{html.escape(reco)}</div>", unsafe_allow_html=True)
    if st.button(btn, key="wz19_reco_button", use_container_width=True):
        _wz19_go(target)

    st.divider()
    st.subheader("📊 Your progress")
    p1, p2 = st.columns(2)
    p1.write(f"CV Score: **{cv_score or 0} → Target: 85**")
    p2.write(f"Interview Readiness: **{interview_score or 0} → Target: 80**")
    last_cv = st.session_state.get("last_resume_score") or st.session_state.get("_last_cv_score_value")
    if last_cv:
        st.caption(f"Last CV score: {last_cv} • Now: {cv_score}")
    if st.button("Continue Improving", key="wz19_continue_improving", use_container_width=True):
        _wz19_go("cv_documents")


def show_dashboard():
    """WorkZo v19 simplified dashboard router.

    Keeps the dashboard focused on one purpose and routes deeper tools into their flows.
    """
    try:
        _wz19_preserve_best_scores()
    except Exception:
        pass
    page_key = st.session_state.get("nav_page", st.session_state.get("page", "dashboard")) or "dashboard"
    aliases = {"improve_cv": "cv_documents", "jobs": "job_assist", "interview": "workobot", "prepare_job": "job_assist"}
    page_key = aliases.get(page_key, page_key)
    if page_key in ["landing", "onboarding"]:
        page_key = "dashboard"
    st.session_state["page"] = page_key
    st.session_state["nav_page"] = page_key

    _wz19_render_sidebar(page_key)

    if page_key == "dashboard":
        _wz19_dashboard_home()
    elif page_key == "cv_documents":
        st.markdown("<div id='top'></div>", unsafe_allow_html=True)
        show_document_tools()
    elif page_key == "job_assist":
        st.markdown("<div id='top'></div>", unsafe_allow_html=True)
        # Reuse the original full Job Assist page from v18 to avoid breaking existing functionality.
        try:
            _wz15_old_show_dashboard()
        except Exception:
            st.error("Job Match page could not load. Please check the dashboard module.")
    elif page_key in ["workobot", "workobot", "career_insights"]:
        st.markdown("<div id='top'></div>", unsafe_allow_html=True)
        show_workobot()
    elif page_key == "founder_dashboard":
        st.markdown("<div id='top'></div>", unsafe_allow_html=True)
        if st.session_state.get("founder_unlocked"):
            render_founder_dashboard()
        else:
            st.warning("Founder access is locked.")
    else:
        _wz19_dashboard_home()

    try:
        _wz19_preserve_best_scores()
        render_feedback_collector(page_key)
        render_issue_reporter(page_key)
    except Exception:
        pass
    st.divider()
    st.caption("WORKZO AI • Beta • Guided career workspace")
    st.caption("⚠️ WorkZo AI is currently in Beta. Some results may not be perfect yet. Your feedback helps improve the tool.")

# =========================================================
# WorkZo v20 - simplified dashboard + standalone Job Match final override
# =========================================================
def _wz20_clean_text(value):
    try:
        text = str(value or "")
        for a, b in {"ðŸŽ¤":"", "ðŸ“‹":"", "ðŸ”´":"", "ðŸŸ¢":"", "Ã¢â‚¬â€œ":"-", "â€“":"-", "â€”":"-", "â€¢":"-", "Â":"", "�":""}.items():
            text = text.replace(a, b)
        return re.sub(r"\s+", " ", text).strip()
    except Exception:
        return str(value or "")

def _wz20_extract_keywords(text, limit=16):
    stop = set("the and for with from this that your you are will can have has about into role job our their they a an to in of on at as is be by or we us it do does did what who why how".split())
    words = re.findall(r"[A-Za-z][A-Za-z+#.-]{2,}", str(text or "").lower())
    out = []
    for word in words:
        if word not in stop and word not in out:
            out.append(word)
        if len(out) >= limit:
            break
    return out

def _wz20_job_match_score(cv_text, jd_text):
    cv = str(cv_text or "").lower()
    keywords = _wz20_extract_keywords(jd_text, 18)
    if not keywords:
        return 0, [], []
    matched = [k for k in keywords if k in cv]
    missing = [k for k in keywords if k not in cv]
    return int(round(100 * len(matched) / max(1, len(keywords)))), matched, missing

def _wz20_render_job_assist_page():
    st.markdown("<div id='top'></div>", unsafe_allow_html=True)
    st.markdown("## AI Job Application Assistant")
    st.caption("Paste a job description. WorkZo will prepare your CV focus, cover letter direction, interview plan, and market guidance.")

    c1, c2 = st.columns(2)
    with c1:
        target_company = st.text_input("Target company", value=st.session_state.get("target_company", ""), key="wz20_target_company")
    with c2:
        target_title = st.text_input("Target job title", value=st.session_state.get("target_job_title", ""), key="wz20_target_job_title")
    company_website = st.text_input("Company website / careers page (optional)", value=st.session_state.get("target_company_website", ""), key="wz20_company_website", help="Optional but recommended. WorkZo uses this to make CV advice, cover letters, and Work-O-Bot more company-specific.")

    default_jd = st.session_state.get("last_prepare_job_description") or st.session_state.get("last_understand_job_description") or st.session_state.get("improve_cv_for_job_desc") or ""
    jd = st.text_area("Paste the job description", value=default_jd, height=230, key="wz20_job_desc")
    cv_text = st.session_state.get("cv_text") or st.session_state.get("workzo_live_cv_text") or ""

    if not str(cv_text).strip():
        st.warning("Add your CV first so WorkZo can compare it with the job.")

    if st.button("Analyze job match", key="wz20_analyze_job_match", use_container_width=True):
        st.session_state["target_company"] = target_company
        st.session_state["target_job_title"] = target_title
        st.session_state["company_website"] = company_website
        st.session_state["company_context"] = _wz26_fetch_company_context(target_company, company_website)
        st.session_state["last_prepare_job_description"] = jd
        st.session_state["last_understand_job_description"] = jd
        st.session_state["improve_cv_for_job_desc"] = jd
        score, matched, missing = _wz20_job_match_score(cv_text, jd)
        st.session_state["ats_score_value"] = score
        st.session_state["latest_job_analysis"] = {"score": score, "matched": matched, "missing": missing, "company": target_company, "title": target_title, "company_website": company_website, "company_context": st.session_state.get("company_context", "")}
        try:
            _wz19_preserve_best_scores()
        except Exception:
            pass
        st.success("Job match analyzed. Review the guidance below.")

    analysis = st.session_state.get("latest_job_analysis") or {}
    score = int(analysis.get("score") or st.session_state.get("ats_score_value") or 0)
    matched = analysis.get("matched") or []
    missing = analysis.get("missing") or []

    if jd:
        st.divider()
        st.subheader("Job Match Summary")
        m1, m2, m3 = st.columns(3)
        m1.metric("Job Match", f"{score}%" if score else "Run analysis")
        m2.metric("Matched keywords", len(matched))
        m3.metric("Missing keywords", len(missing))
        if analysis.get("company_context"):
            st.caption("Company context is saved and reused for CV tailoring, cover letters, and Work-O-Bot.")

        if score and score < 75:
            st.warning("Your match is not yet strong. Improve the CV only with truthful keywords and examples from your real experience.")
            st.markdown("**Missing keywords to consider if true:** " + (", ".join(_wz20_clean_text(x) for x in missing[:10]) or "No clear missing keywords found."))
            st.markdown("""
**How to improve it honestly:**
- Add missing tools or skills only if you can explain them in an interview.
- Rewrite 2-3 bullet points to mirror the job language.
- Add measurable support, customer, or project examples where possible.
- Do not invent metrics, tools, or responsibilities.
""")
        elif score:
            st.success("Good match. Next step: tailor the CV and prepare a short interview story for this role.")

        st.subheader("Next best actions")
        a, b, c = st.columns(3)
        with a:
            if st.button("Improve CV for this job", key="wz20_go_improve_cv", use_container_width=True):
                st.session_state["cv_documents_mode"] = "improve_cv"
                _wz19_go("cv_documents")
        with b:
            if st.button("Create cover letter", key="wz20_go_cover", use_container_width=True):
                st.session_state["cv_documents_mode"] = "cover_letter"
                st.session_state["cover_letter_job_desc"] = jd
                st.session_state["target_company"] = target_company
                st.session_state["company_website"] = company_website
                st.session_state["company_context"] = _wz26_fetch_company_context(target_company, company_website)
                _wz19_go("cv_documents")
        with c:
            if st.button("Practice interview", key="wz20_go_interview", use_container_width=True):
                st.session_state["workobot_mode"] = "real_interview_simulation"
                st.session_state["real_interview_jd"] = jd
                st.session_state["real_interview_company"] = target_company
                st.session_state["company_website"] = company_website
                st.session_state["company_context"] = _wz26_fetch_company_context(target_company, company_website)
                _wz21_go("workobot")

        with st.expander("Market Smart Guide", expanded=False):
            country = st.session_state.get("country") or st.session_state.get("target_country") or "your target market"
            st.write(f"WorkZo adapts CV wording, interview preparation, and job advice for **{country}** when country information is available.")

def show_dashboard():
    """WorkZo v20 final dashboard router: no duplicate sidebar, standalone Job Match."""
    try:
        _wz19_preserve_best_scores()
    except Exception:
        pass
    page_key = st.session_state.get("nav_page", st.session_state.get("page", "dashboard")) or "dashboard"
    if page_key in ["landing", "onboarding"]:
        page_key = "dashboard"
    st.session_state["page"] = page_key
    st.session_state["nav_page"] = page_key

    _wz19_render_sidebar(page_key)

    if page_key == "dashboard":
        _wz19_dashboard_home()
    elif page_key == "cv_documents":
        st.markdown("<div id='top'></div>", unsafe_allow_html=True)
        show_document_tools()
    elif page_key == "job_assist":
        _wz20_render_job_assist_page()
    elif page_key in ["workobot", "workobot", "career_insights"]:
        st.markdown("<div id='top'></div>", unsafe_allow_html=True)
        show_workobot()
    elif page_key == "founder_dashboard":
        st.markdown("<div id='top'></div>", unsafe_allow_html=True)
        if st.session_state.get("founder_unlocked"):
            render_founder_dashboard()
        else:
            st.warning("Founder access is locked.")
    else:
        _wz19_dashboard_home()

    try:
        _wz19_preserve_best_scores()
        render_feedback_collector(page_key)
        render_issue_reporter(page_key)
    except Exception:
        pass
    st.divider()
    st.caption("WORKZO AI • Beta • Guided career workspace")

# =========================================================
# WorkZo v21 - visible Work-O-Bot + clean sidebar final override
# =========================================================
def _wz21_go(page_key: str):
    """Single reliable navigation helper.

    Earlier builds changed only session_state. On the next rerun the router
    re-read the old ?page= query parameter and sent the user back, which made
    every navigation button feel broken. This updates both session_state and
    URL state before rerun.
    """
    aliases = {
        "improve_cv": "cv_documents",
        "jobs": "job_assist",
        "interview": "workobot",
        "prepare_job": "job_assist",
    }
    page_key = aliases.get(page_key, page_key)
    st.session_state["page"] = page_key
    st.session_state["nav_page"] = page_key
    st.session_state["scroll_to_top_next"] = True
    st.session_state["_workzo_scroll_to_top"] = True
    try:
        st.query_params["page"] = page_key
        st.query_params["wz_top"] = str(st.session_state.get("nav_change_nonce", 0) + 1)
    except Exception:
        pass
    st.rerun()


def _wz21_render_sidebar(page_key: str):
    """Clean final sidebar: no duplicate settings/profile blocks."""
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
                    <div class='workzo-sidebar-version'>Guided career workspace</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("### WorkZo AI")

        st.markdown("<div class='workzo-sidebar-section-label'>Navigation</div>", unsafe_allow_html=True)
        nav = [
            ("dashboard", "Dashboard"),
            ("cv_documents", "My CV"),
            ("job_assist", "Job Match"),
            ("workobot", "Work-O-Bot"),
            ("workobot", "Work-O-Bot"),
        ]
        # Founder analytics hidden in v26.
        for key, label in nav:
            if st.button(label + ("  ✓" if page_key == key else ""), key=f"wz21_sidebar_{key}", use_container_width=True):
                _wz21_go(key)

        st.markdown("<div class='workzo-sidebar-section-label'>Profile</div>", unsafe_allow_html=True)
        st.caption(f"Country: {st.session_state.get('country') or st.session_state.get('target_country') or 'Not set'}")
        st.caption("Resume uploaded" if str(st.session_state.get("cv_text", "")).strip() else "CV missing")

        st.markdown("<div class='workzo-sidebar-section-label'>Settings</div>", unsafe_allow_html=True)
        try:
            language_list = language_options if language_options else ["English", "German", "Dutch"]
            current_language = st.session_state.get("preferred_language", "English")
            if current_language not in language_list:
                current_language = "English" if "English" in language_list else language_list[0]
            preferred = st.selectbox(
                "Language",
                language_list,
                index=language_list.index(current_language),
                key="wz21_sidebar_preferred_language",
            )
            set_single_preferred_language(preferred)
        except Exception:
            pass

        if st.button("Edit setup", key="wz21_edit_setup", use_container_width=True):
            try:
                reset_onboarding()
            except Exception:
                st.session_state["onboarding_complete"] = False
            _wz21_go("onboarding")


def _wz21_render_interview_practice_page():
    """Make speaking/Work-O-Bot discoverable as its own page."""
    st.markdown("<div id='top'></div>", unsafe_allow_html=True)
    st.markdown("## 🎤 Real Interview Simulation")
    st.caption("Practice the exact interview for the job you are applying to — using your CV and the job description.")
    st.info("Use this after applying or when HR invites you for an interview. WorkZo asks tailored questions and gives specific feedback so you can improve and try again.")
    if "render_real_interview_simulation" in globals():
        render_real_interview_simulation()
    elif "show_workobot" in globals():
        st.warning("Interview simulator could not be opened directly, so WorkZo opened the coaching assistant instead.")
        show_workobot()
    else:
        st.error("Interview practice is not available yet. Please check 09_interview_assistant.py is loaded.")


def show_dashboard():
    """WorkZo v21 final dashboard router: clean sidebar + visible Work-O-Bot."""
    try:
        _wz19_preserve_best_scores()
    except Exception:
        pass
    page_key = st.session_state.get("nav_page", st.session_state.get("page", "dashboard")) or "dashboard"
    if page_key in ["landing", "onboarding"]:
        page_key = "dashboard"
    st.session_state["page"] = page_key
    st.session_state["nav_page"] = page_key

    _wz21_render_sidebar(page_key)

    if page_key == "dashboard":
        _wz19_dashboard_home()
    elif page_key == "cv_documents":
        st.markdown("<div id='top'></div>", unsafe_allow_html=True)
        show_document_tools()
    elif page_key == "job_assist":
        _wz20_render_job_assist_page()
    elif page_key == "workobot":
        _wz21_render_interview_practice_page()
    elif page_key == "workobot":
        st.markdown("<div id='top'></div>", unsafe_allow_html=True)
        show_workobot()
    elif page_key == "founder_dashboard":
        st.markdown("<div id='top'></div>", unsafe_allow_html=True)
        if st.session_state.get("founder_unlocked"):
            render_founder_dashboard()
        else:
            st.warning("Founder access is locked.")
    else:
        _wz19_dashboard_home()

    try:
        _wz19_preserve_best_scores()
        render_feedback_collector(page_key)
        render_issue_reporter(page_key)
    except Exception:
        pass
    st.divider()
    st.caption("WORKZO AI • Beta • Guided career workspace")


# =========================================================
# WorkZo v24 - separate Work-O-Bot and Work-O-Bot final override
# =========================================================
def _wz24_render_sidebar(page_key: str):
    """Final sidebar: Work-O-Bot and Work-O-Bot are separate features."""
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
                    <div class='workzo-sidebar-version'>Guided career workspace</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("### WorkZo AI")

        st.markdown("<div class='workzo-sidebar-section-label'>Navigation</div>", unsafe_allow_html=True)
        nav = [
            ("dashboard", "Dashboard"),
            ("cv_documents", "My CV"),
            ("job_assist", "Job Match"),
            ("workobot", "Work-O-Bot"),
            ("workobot", "Work-O-Bot"),
        ]
        # Founder analytics hidden in v26.
        for key, label in nav:
            if st.button(label + ("  ✓" if page_key == key else ""), key=f"wz24_sidebar_{key}", use_container_width=True):
                _wz21_go(key)

        st.markdown("<div class='workzo-sidebar-section-label'>Profile</div>", unsafe_allow_html=True)
        st.caption(f"Country: {st.session_state.get('country') or st.session_state.get('target_country') or 'Not set'}")
        st.caption("Resume uploaded" if str(st.session_state.get("cv_text", "")).strip() else "CV missing")

        st.markdown("<div class='workzo-sidebar-section-label'>Settings</div>", unsafe_allow_html=True)
        try:
            language_list = language_options if language_options else ["English", "German", "Dutch"]
            current_language = st.session_state.get("preferred_language", "English")
            if current_language not in language_list:
                current_language = "English" if "English" in language_list else language_list[0]
            preferred = st.selectbox("Language", language_list, index=language_list.index(current_language), key="wz24_sidebar_preferred_language")
            set_single_preferred_language(preferred)
        except Exception:
            pass

        if st.button("Edit setup", key="wz24_edit_setup", use_container_width=True):
            try:
                reset_onboarding()
            except Exception:
                st.session_state["onboarding_complete"] = False
            _wz21_go("onboarding")


def _wz24_render_workobot_page():
    """Standalone typed career assistant. Interview simulation stays on Work-O-Bot page."""
    st.markdown("<div id='top'></div>", unsafe_allow_html=True)
    st.markdown("## 🤖 Work-O-Bot")
    st.caption("Ask career questions, CV doubts, job-search questions, HR messages, or language-practice questions. For mock interviews, use Work-O-Bot.")
    try:
        show_workobot()
    except Exception as exc:
        st.error("Work-O-Bot could not load.")
        st.exception(exc)


def _wz24_dashboard_home():
    _wz19_preserve_best_scores()
    name = _wz19_current_name()
    cv_score = _wz19_int_score("cv_score_value", "resume_score", default=0)
    ats_score = _wz19_int_score("ats_score_value", default=0)
    interview_score = _wz19_int_score("interview_score", "interview_readiness", default=40)
    has_job = bool(str(st.session_state.get("last_understand_job_description", "") or st.session_state.get("improve_cv_for_job_desc", "") or st.session_state.get("last_prepare_job_description", "")).strip())

    st.markdown("<div id='top'></div>", unsafe_allow_html=True)
    st.markdown("""
    <style>
    .wz19-hero {border:1px solid rgba(148,163,184,.25); border-radius:22px; padding:28px; background:linear-gradient(135deg, rgba(99,102,241,.10), rgba(20,184,166,.08)); margin-bottom:22px;}
    .wz19-title {font-size:30px; font-weight:800; margin-bottom:4px; color:#f8fafc;}
    .wz19-sub {font-size:16px; color:#cbd5e1; margin-bottom:18px;}
    .wz19-card {border:1px solid rgba(148,163,184,.25); border-radius:18px; padding:20px; min-height:190px; background:rgba(15,23,42,.35);}
    .wz19-card h3 {margin-top:0; font-size:20px;}
    .wz19-card p {color:#cbd5e1; min-height:72px;}
    .wz19-reco {border:1px solid rgba(34,197,94,.30); border-radius:18px; padding:18px; background:rgba(34,197,94,.08); margin-top:10px;}
    div[data-testid="stButton"] > button {border-radius:12px; font-weight:650; min-height:42px;}
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class='wz19-hero'>
      <div class='wz19-title'>👋 Welcome back, {html.escape(name)}</div>
      <div class='wz19-sub'>Let’s move you closer to your next job.</div>
    </div>
    """, unsafe_allow_html=True)

    m1, m2, m3 = st.columns(3)
    m1.metric("CV Strength", f"{cv_score}%" if cv_score else "Not analyzed")
    m2.metric("Job Match", f"{ats_score}%" if has_job or ats_score else "Not analyzed")
    m3.metric("Interview Readiness", f"{interview_score}%")
    st.progress(max(cv_score, ats_score, interview_score, 1) / 100)

    if st.button("Continue Your Journey", key="wz24_continue_journey", use_container_width=True):
        _, _, target = _wz19_recommendation(cv_score, ats_score, interview_score)
        _wz21_go(target)

    st.divider()
    st.subheader("What do you need today?")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""<div class='wz19-card'><h3>🟦 Get More Interviews</h3><p>Analyze your CV against a job, improve ATS alignment, and fix missing keywords honestly.</p></div>""", unsafe_allow_html=True)
        if st.button("Improve My CV", key="wz24_improve_cv", use_container_width=True):
            st.session_state["cv_documents_mode"] = "improve_cv"
            _wz21_go("cv_documents")
    with c2:
        st.markdown("""<div class='wz19-card'><h3>🟩 Prepare for Interview</h3><p>Practice the exact interview using your CV and the job description, then improve your answers.</p></div>""", unsafe_allow_html=True)
        if st.button("Start Work-O-Bot", key="wz24_interview", use_container_width=True):
            _wz21_go("workobot")
    with c3:
        st.markdown("""<div class='wz19-card'><h3>🟧 Find Relevant Jobs</h3><p>Find better-matched roles, review job fit, and save opportunities to your tracker.</p></div>""", unsafe_allow_html=True)
        if st.button("Find Jobs", key="wz24_find_jobs", use_container_width=True):
            _wz21_go("job_assist")

    st.divider()
    st.subheader("🔍 What WorkZo suggests for you")
    reco, btn, target = _wz19_recommendation(cv_score, ats_score, interview_score)
    st.markdown(f"<div class='wz19-reco'>{html.escape(reco)}</div>", unsafe_allow_html=True)
    if st.button(btn, key="wz24_reco_button", use_container_width=True):
        _wz21_go(target)

    st.divider()

    # Application progress tracker only. No navigation or other dashboard logic changed.
    cv_ready = bool(str(st.session_state.get("cv_text", "")).strip())
    improved_ready = bool(str(
        st.session_state.get("improved_cv_text", "")
        or st.session_state.get("latest_improved_cv", "")
        or st.session_state.get("final_cv_text", "")
        or st.session_state.get("prepare_cv_tailored", "")
        or st.session_state.get("improved_cv_text_v92", "")
    ).strip())
    job_ready = bool(str(
        st.session_state.get("last_understand_job_description", "")
        or st.session_state.get("improve_cv_for_job_desc", "")
        or st.session_state.get("last_prepare_job_description", "")
        or st.session_state.get("latest_job_analysis", "")
        or st.session_state.get("latest_curated_jobs", "")
    ).strip())
    prepared_ready = bool(str(
        st.session_state.get("latest_application_prep", "")
        or st.session_state.get("latest_cover_letter", "")
        or st.session_state.get("cover_letter_job_desc", "")
        or st.session_state.get("application_ready_flag", "")
    ).strip())

    progress_steps = [
        {"title": "1. CV uploaded", "desc_done": "completed", "desc_next": "Upload or create your CV", "done": cv_ready, "icon_done": "✅", "icon_next": "○"},
        {"title": "2. CV improved", "desc_done": "completed", "desc_next": "Improve or tailor your CV", "done": improved_ready, "icon_done": "✅", "icon_next": "➜"},
        {"title": "3. Job matched", "desc_done": "completed", "desc_next": "Find matching jobs", "done": job_ready, "icon_done": "✅", "icon_next": "○"},
        {"title": "4. Prepared for job", "desc_done": "completed", "desc_next": "Prepare cover letter and interview notes", "done": prepared_ready, "icon_done": "✅", "icon_next": "○"},
    ]
    next_index = 0
    for i, step in enumerate(progress_steps):
        if not step["done"]:
            next_index = i
            break
    else:
        next_index = len(progress_steps) - 1

    st.markdown("""
    <style>
    .wz-progress-wrap {
        margin-top: 4px;
        padding: 2px 0 8px 0;
    }
    .wz-progress-title {
        color: #f8fafc;
        font-size: 1.55rem;
        font-weight: 900;
        line-height: 1.15;
        margin-bottom: 16px;
        text-transform: lowercase;
    }
    .wz-progress-sub {
        color: #9ca3af;
        font-size: .94rem;
        font-weight: 650;
        margin-bottom: 24px;
    }
    .wz-progress-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 20px;
        margin-bottom: 10px;
    }
    .wz-progress-card {
        min-height: 112px;
        border-radius: 22px;
        border: 1px solid rgba(148,163,184,.18);
        background: rgba(15,23,42,.34);
        padding: 24px 24px 18px 24px;
    }
    .wz-progress-card.done {
        border-color: rgba(52,211,153,.70);
        background: linear-gradient(135deg, rgba(20,184,166,.23), rgba(15,23,42,.42));
    }
    .wz-progress-card.active {
        border-color: rgba(59,130,246,.82);
        background: linear-gradient(135deg, rgba(37,99,235,.23), rgba(15,23,42,.42));
    }
    .wz-progress-head {
        display: flex;
        align-items: center;
        gap: 12px;
        color: #f8fafc;
        font-size: 1rem;
        font-weight: 900;
        margin-bottom: 18px;
    }
    .wz-progress-icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 28px;
        min-width: 28px;
        color: #64748b;
        font-size: 1.35rem;
        line-height: 1;
    }
    .wz-progress-card.done .wz-progress-icon { color: #34d399; }
    .wz-progress-card.active .wz-progress-icon { color: #3b82f6; font-size: 1.7rem; }
    .wz-progress-desc {
        color: #cbd5e1;
        font-size: .95rem;
        line-height: 1.45;
        font-weight: 600;
    }
    .wz-progress-card.done .wz-progress-desc { color: #34d399; font-weight: 800; }
    .wz-progress-card.active .wz-progress-desc { color: #93c5fd; }
    .wz-progress-note {
        display: flex;
        align-items: center;
        gap: 10px;
        color: #9ca3af;
        font-size: .9rem;
        font-weight: 700;
        margin-top: 18px;
    }
    .wz-progress-info {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 20px;
        height: 20px;
        border-radius: 999px;
        border: 2px solid #64748b;
        color: #94a3b8;
        font-size: .78rem;
        font-weight: 900;
    }
    @media (max-width: 900px) {
        .wz-progress-grid { grid-template-columns: 1fr; gap: 12px; }
        .wz-progress-card { min-height: auto; }
    }
    </style>
    """, unsafe_allow_html=True)

    cards_html = []
    for i, step in enumerate(progress_steps):
        state_class = "done" if step["done"] else ("active" if i == next_index else "")
        icon = step["icon_done"] if step["done"] else step["icon_next"]
        desc = step["desc_done"] if step["done"] else step["desc_next"]
        cards_html.append(f"""
        <div class="wz-progress-card {state_class}">
            <div class="wz-progress-head">
                <span class="wz-progress-icon">{html.escape(icon)}</span>
                <span>{html.escape(step['title'])}</span>
            </div>
            <div class="wz-progress-desc">{html.escape(desc)}</div>
        </div>
        """)

    st.markdown(f"""
    <div class="wz-progress-wrap">
        <div class="wz-progress-title">application progress</div>
        <div class="wz-progress-sub">Visual tracker only. Use Smart actions above to continue.</div>
        <div class="wz-progress-grid">
            {''.join(cards_html)}
        </div>
        <div class="wz-progress-note"><span class="wz-progress-info">i</span><span>Scores are guidance only. WorkZo should not invent skills, company facts, language level, salary, or experience.</span></div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    help_col, bot_col = st.columns([2, 1])
    with help_col:
        st.subheader("Need help or have a question?")
        st.caption("Use Work-O-Bot for general career questions, HR messages, CV doubts, job-search advice, or language practice.")
    with bot_col:
        if st.button("Ask Work-O-Bot", key="wz24_ask_workobot", use_container_width=True):
            _wz21_go("workobot")


def show_dashboard():
    """WorkZo v24 final router: Work-O-Bot and Work-O-Bot are separate."""
    try:
        _wz19_preserve_best_scores()
    except Exception:
        pass
    page_key = st.session_state.get("nav_page", st.session_state.get("page", "dashboard")) or "dashboard"
    aliases = {"improve_cv": "cv_documents", "jobs": "job_assist", "interview": "workobot", "prepare_job": "job_assist"}
    page_key = aliases.get(page_key, page_key)
    if page_key in ["landing", "onboarding"]:
        page_key = "dashboard"
    st.session_state["page"] = page_key
    st.session_state["nav_page"] = page_key

    _wz24_render_sidebar(page_key)

    if page_key == "dashboard":
        _wz24_dashboard_home()
    elif page_key == "cv_documents":
        st.markdown("<div id='top'></div>", unsafe_allow_html=True)
        show_document_tools()
    elif page_key == "job_assist":
        _wz20_render_job_assist_page()
    elif page_key == "workobot":
        _wz21_render_interview_practice_page()
    elif page_key == "workobot":
        _wz24_render_workobot_page()
    elif page_key == "founder_dashboard":
        st.markdown("<div id='top'></div>", unsafe_allow_html=True)
        if st.session_state.get("founder_unlocked"):
            render_founder_dashboard()
        else:
            st.warning("Founder access is locked.")
    else:
        _wz24_dashboard_home()

    try:
        _wz19_preserve_best_scores()
        render_feedback_collector(page_key)
        render_issue_reporter(page_key)
    except Exception:
        pass
    st.divider()
    st.caption("WORKZO AI • Beta • Guided career workspace")



# =========================================================
# WorkZo v26 - company context helper + founder analytics hidden
# =========================================================
def _wz26_fetch_company_context(company_name: str = "", company_website: str = "") -> str:
    company_name = str(company_name or "").strip()
    company_website = str(company_website or "").strip()
    cached_key = f"_wz26_company_context::{company_name}::{company_website}"
    if cached_key in st.session_state:
        return st.session_state.get(cached_key, "")
    context = ""
    if company_website:
        url = company_website if company_website.startswith(("http://", "https://")) else "https://" + company_website
        try:
            import requests, re as _re
            r = requests.get(url, timeout=3, headers={"User-Agent": "WorkZoAI/1.0"})
            if r.ok:
                txt0 = _re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", " ", r.text, flags=_re.I)
                txt0 = _re.sub(r"<[^>]+>", " ", txt0)
                txt0 = _re.sub(r"\s+", " ", txt0).strip()
                context = txt0[:1800]
        except Exception:
            context = ""
    if not context and company_name:
        context = f"Company name provided by user: {company_name}. If public company details are not known, avoid inventing facts and ask the user to paste company details."
    st.session_state[cached_key] = context
    return context

# =========================================================
# WorkZo v25 - navigation top fix + faster dashboard + Work-O-Bot visible
# =========================================================
def _wz25_scroll_to_top_if_needed(force: bool = False):
    """Scroll to top only after navigation; avoids running script on every rerun."""
    try:
        should_scroll = force or bool(st.session_state.pop("_workzo_scroll_to_top", False)) or bool(st.session_state.pop("scroll_to_top_next", False))
        if not should_scroll:
            return
        script = """
        <script>
        const scrollTop = () => {
          try { window.parent.scrollTo({top: 0, left: 0, behavior: 'instant'}); } catch(e) {}
          try { window.parent.document.querySelector('[data-testid="stAppViewContainer"]').scrollTo({top:0,left:0,behavior:'instant'}); } catch(e) {}
          try { window.parent.document.querySelector('section.main').scrollTo({top:0,left:0,behavior:'instant'}); } catch(e) {}
          try { window.parent.document.querySelector('.main').scrollTo({top:0,left:0,behavior:'instant'}); } catch(e) {}
        };
        scrollTop(); setTimeout(scrollTop, 50); setTimeout(scrollTop, 200);
        </script>
        """
        if hasattr(st, "iframe"):
            st.iframe(srcdoc=script, height=0, width=0)
        else:
            import streamlit.components.v1 as components
            components.html(script, height=0, width=0)
    except Exception:
        pass


def _wz25_go(page_key: str):
    aliases = {
        "improve_cv": "cv_documents",
        "jobs": "job_assist",
        "interview": "workobot",
        "prepare_job": "job_assist",
        "bot": "workobot",
        "work-o-bot": "workobot",
    }
    page_key = aliases.get(page_key, page_key)
    st.session_state["page"] = page_key
    st.session_state["nav_page"] = page_key
    st.session_state["_workzo_scroll_to_top"] = True
    st.session_state["scroll_to_top_next"] = True
    try:
        st.session_state["nav_change_nonce"] = int(st.session_state.get("nav_change_nonce", 0)) + 1
    except Exception:
        st.session_state["nav_change_nonce"] = 1
    try:
        st.query_params["page"] = page_key
        st.query_params["wz_top"] = str(st.session_state.get("nav_change_nonce", 1))
    except Exception:
        pass
    st.rerun()

# Override older helpers so old buttons also use reliable navigation.
_wz21_go = _wz25_go
_wz19_go = _wz25_go
go_to_nav = _wz25_go


def _wz25_render_sidebar(page_key: str):
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
                    <div class='workzo-sidebar-version'>Guided career workspace</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("### WorkZo AI")

        st.markdown("<div class='workzo-sidebar-section-label'>Navigation</div>", unsafe_allow_html=True)
        nav = [
            ("dashboard", "Dashboard"),
            ("cv_documents", "My CV"),
            ("job_assist", "Job Match"),
            ("workobot", "Work-O-Bot"),
            ("workobot", "Work-O-Bot"),
        ]
        # Founder analytics hidden in v26.
        for key, label in nav:
            if st.button(label + (" ✓" if page_key == key else ""), key=f"wz25_sidebar_{key}", use_container_width=True):
                _wz25_go(key)

        st.markdown("<div class='workzo-sidebar-section-label'>Profile</div>", unsafe_allow_html=True)
        st.caption(f"Country: {st.session_state.get('country') or st.session_state.get('target_country') or 'Not set'}")
        st.caption("Resume uploaded" if str(st.session_state.get("cv_text", "")).strip() else "CV missing")

        st.markdown("<div class='workzo-sidebar-section-label'>Settings</div>", unsafe_allow_html=True)
        try:
            language_list = language_options if language_options else ["English", "German", "Dutch"]
            current_language = st.session_state.get("preferred_language", "English")
            if current_language not in language_list:
                current_language = "English" if "English" in language_list else language_list[0]
            preferred = st.selectbox("Language", language_list, index=language_list.index(current_language), key="wz25_sidebar_preferred_language")
            set_single_preferred_language(preferred)
        except Exception:
            pass

        if st.button("Edit setup", key="wz25_edit_setup", use_container_width=True):
            try:
                reset_onboarding()
            except Exception:
                st.session_state["onboarding_complete"] = False
            _wz25_go("onboarding")


def _wz25_dashboard_home():
    _wz19_preserve_best_scores()
    name = _wz19_current_name()
    cv_score = _wz19_int_score("cv_score_value", "resume_score", default=0)
    ats_score = _wz19_int_score("ats_score_value", default=0)
    interview_score = _wz19_int_score("interview_score", "interview_readiness", default=40)
    has_job = bool(str(st.session_state.get("last_understand_job_description", "") or st.session_state.get("improve_cv_for_job_desc", "") or st.session_state.get("last_prepare_job_description", "")).strip())

    st.markdown("<div id='workzo-page-top'></div>", unsafe_allow_html=True)
    st.markdown("""
    <style>
    .wz25-hero {border:1px solid rgba(148,163,184,.25); border-radius:22px; padding:28px; background:linear-gradient(135deg, rgba(99,102,241,.10), rgba(20,184,166,.08)); margin-bottom:22px;}
    .wz25-title {font-size:30px; font-weight:800; margin-bottom:4px; color:#f8fafc;}
    .wz25-sub {font-size:16px; color:#cbd5e1; margin-bottom:0;}
    .wz25-card {border:1px solid rgba(148,163,184,.25); border-radius:18px; padding:20px; min-height:190px; background:rgba(15,23,42,.35);}
    .wz25-card h3 {margin-top:0; font-size:20px;}
    .wz25-card p {color:#cbd5e1; min-height:72px;}
    .wz25-reco {border:1px solid rgba(34,197,94,.30); border-radius:18px; padding:18px; background:rgba(34,197,94,.08); margin-top:10px;}
    div[data-testid="stButton"] > button {border-radius:12px; font-weight:650; min-height:42px;}
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class='wz25-hero'>
      <div class='wz25-title'>👋 Welcome back, {html.escape(name)}</div>
      <div class='wz25-sub'>Let’s move you closer to your next job.</div>
    </div>
    """, unsafe_allow_html=True)

    m1, m2, m3 = st.columns(3)
    m1.metric("CV Strength", f"{cv_score}%" if cv_score else "Not analyzed")
    m2.metric("Job Match", f"{ats_score}%" if has_job or ats_score else "Not analyzed")
    m3.metric("Interview Readiness", f"{interview_score}%")
    st.caption("Progress updates after you improve your CV, analyze a job, or complete Work-O-Bot.")

    if st.button("Continue Your Journey", key="wz25_continue_journey", use_container_width=False):
        _, _, target = _wz19_recommendation(cv_score, ats_score, interview_score)
        _wz25_go(target)

    st.divider()
    st.subheader("What do you need today?")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""<div class='wz25-card'><h3>🟦 Get More Interviews</h3><p>Analyze your CV against a job, improve ATS alignment, and fix missing keywords honestly.</p></div>""", unsafe_allow_html=True)
        if st.button("Improve My CV", key="wz25_improve_cv", use_container_width=True):
            st.session_state["cv_documents_mode"] = "improve_cv"
            _wz25_go("cv_documents")
    with c2:
        st.markdown("""<div class='wz25-card'><h3>🟩 Prepare for Interview</h3><p>Practice the exact interview using your CV and the job description, then improve your answers.</p></div>""", unsafe_allow_html=True)
        if st.button("Start Work-O-Bot", key="wz25_interview", use_container_width=True):
            _wz25_go("workobot")
    with c3:
        st.markdown("""<div class='wz25-card'><h3>🟧 Find Relevant Jobs</h3><p>Find better-matched roles, review job fit, and save opportunities to your tracker.</p></div>""", unsafe_allow_html=True)
        if st.button("Find Jobs", key="wz25_find_jobs", use_container_width=True):
            _wz25_go("job_assist")

    st.divider()
    st.subheader("🔍 What WorkZo suggests for you")
    reco, btn, target = _wz19_recommendation(cv_score, ats_score, interview_score)
    st.markdown(f"<div class='wz25-reco'>{html.escape(reco)}</div>", unsafe_allow_html=True)
    if st.button(btn, key="wz25_reco_button", use_container_width=True):
        _wz25_go(target)

    st.divider()
    help_col, bot_col = st.columns([2, 1])
    with help_col:
        st.subheader("Need help or have a question?")
        st.caption("Use Work-O-Bot for typed career questions, HR messages, CV doubts, job-search advice, or language practice.")
    with bot_col:
        if st.button("Ask Work-O-Bot", key="wz25_ask_workobot", use_container_width=True):
            _wz25_go("workobot")


def _wz25_render_workobot_page():
    st.markdown("<div id='workzo-page-top'></div>", unsafe_allow_html=True)
    st.markdown("## 🤖 Work-O-Bot")
    st.caption("Typed career assistant for CV doubts, job-search questions, HR messages, and language practice. Use Work-O-Bot for mock interviews.")
    try:
        show_workobot()
    except Exception as exc:
        st.error("Work-O-Bot could not load.")
        st.exception(exc)


def show_dashboard():
    try:
        _wz19_preserve_best_scores()
    except Exception:
        pass
    page_key = st.session_state.get("nav_page", st.session_state.get("page", "dashboard")) or "dashboard"
    aliases = {"improve_cv": "cv_documents", "jobs": "job_assist", "interview": "workobot", "prepare_job": "job_assist", "bot": "workobot"}
    page_key = aliases.get(page_key, page_key)
    if page_key in ["landing", "onboarding"]:
        page_key = "dashboard"
    st.session_state["page"] = page_key
    st.session_state["nav_page"] = page_key

    _wz25_scroll_to_top_if_needed()
    _wz25_render_sidebar(page_key)

    if page_key == "dashboard":
        _wz25_dashboard_home()
    elif page_key == "cv_documents":
        st.markdown("<div id='workzo-page-top'></div>", unsafe_allow_html=True)
        show_document_tools()
    elif page_key == "job_assist":
        st.markdown("<div id='workzo-page-top'></div>", unsafe_allow_html=True)
        _wz20_render_job_assist_page()
    elif page_key == "workobot":
        st.markdown("<div id='workzo-page-top'></div>", unsafe_allow_html=True)
        _wz21_render_interview_practice_page()
    elif page_key == "workobot":
        _wz25_render_workobot_page()
    elif page_key == "founder_dashboard":
        _wz25_dashboard_home()
    else:
        _wz25_dashboard_home()

    try:
        _wz19_preserve_best_scores()
        render_feedback_collector(page_key)
        render_issue_reporter(page_key)
    except Exception:
        pass
    st.divider()
    st.caption("WORKZO AI • Beta • Guided career workspace")


# =========================================================
# WorkZo v27 - FINAL lightweight dashboard/sidebar/navigation override
# =========================================================
def _wz27_force_top():
    try:
        st.markdown("<div id='workzo-page-top'></div>", unsafe_allow_html=True)
        script = """
        <script>
        function wzTop(){
          try { window.parent.scrollTo(0,0); } catch(e) {}
          try { window.parent.document.documentElement.scrollTop = 0; } catch(e) {}
          try { window.parent.document.body.scrollTop = 0; } catch(e) {}
          try { window.parent.document.querySelector('[data-testid="stAppViewContainer"]').scrollTop = 0; } catch(e) {}
          try { window.parent.document.querySelector('section.main').scrollTop = 0; } catch(e) {}
          try { window.parent.document.querySelector('.main').scrollTop = 0; } catch(e) {}
          try { window.parent.document.getElementById('workzo-page-top').scrollIntoView({block:'start', behavior:'instant'}); } catch(e) {}
        }
        wzTop(); setTimeout(wzTop, 30); setTimeout(wzTop, 120); setTimeout(wzTop, 300);
        </script>
        """
        iframe_fn = getattr(st, 'iframe', None)
        if iframe_fn:
            iframe_fn(srcdoc=script, height=0, width=0)
        else:
            try:
                import streamlit.components.v1 as components
                components.html(script, height=0, width=0)
            except Exception:
                pass
    except Exception:
        pass


def _wz27_go(page_key: str):
    aliases = {
        'home': 'dashboard', 'improve_cv': 'cv_documents', 'my_cv': 'cv_documents',
        'jobs': 'job_assist', 'job_match': 'job_assist', 'prepare_job': 'job_assist',
        'interview': 'workobot', 'bot': 'workobot', 'work-o-bot': 'workobot',
        'founder_dashboard': 'dashboard',
    }
    page_key = aliases.get(str(page_key or 'dashboard'), str(page_key or 'dashboard'))
    st.session_state['page'] = page_key
    st.session_state['nav_page'] = page_key
    st.session_state['_workzo_scroll_to_top'] = True
    try:
        n = int(st.session_state.get('nav_change_nonce', 0)) + 1
        st.session_state['nav_change_nonce'] = n
        st.query_params['page'] = page_key
        st.query_params['top'] = str(n)
    except Exception:
        pass
    st.rerun()

_wz25_go = _wz27_go
_wz24_go = _wz27_go
_wz21_go = _wz27_go
_wz19_go = _wz27_go
go_to_nav = _wz27_go


def _wz27_score(*keys, default=0):
    for k in keys:
        try:
            v = st.session_state.get(k)
            if v is not None and str(v).strip() != '':
                return max(0, min(100, int(float(v))))
        except Exception:
            pass
    return default


def _wz27_sidebar(page_key: str):
    with st.sidebar:
        try:
            logo_src = image_to_data_uri(ICON_PATH) or image_to_data_uri(LOGO_PATH)
        except Exception:
            logo_src = None
        if logo_src:
            st.markdown(f"""
            <div style='border:1px solid rgba(20,184,166,.35);border-radius:18px;padding:16px;margin-bottom:16px;background:rgba(15,23,42,.65)'>
                <img src='{logo_src}' style='width:44px;height:44px;border-radius:12px;margin-bottom:10px;'>
                <div style='font-weight:800;font-size:20px;letter-spacing:.04em'>WORKZO AI</div>
                <div style='font-size:12px;color:#94a3b8'>Guided career workspace</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown('### WorkZo AI')
        st.markdown('##### Navigation')
        nav = [('dashboard','Dashboard'),('cv_documents','My CV'),('job_assist','Job Match'),('workobot','Work-O-Bot')]
        for key, label in nav:
            marker = ' ✓' if page_key == key else ''
            if st.button(label + marker, key=f'wz27_nav_{key}', use_container_width=True):
                _wz27_go(key)
        st.markdown('##### Profile')
        st.caption(f"Country: {st.session_state.get('country') or st.session_state.get('target_country') or 'Not set'}")
        st.caption('Resume uploaded' if str(st.session_state.get('cv_text','')).strip() else 'CV missing')
        st.markdown('##### Settings')
        try:
            language_list = language_options if language_options else ['English', 'German', 'Dutch']
            current = st.session_state.get('preferred_language', 'English')
            if current not in language_list:
                current = 'English' if 'English' in language_list else language_list[0]
            chosen = st.selectbox('Language', language_list, index=language_list.index(current), key='wz27_language')
            set_single_preferred_language(chosen)
        except Exception:
            pass
        if st.button('Edit setup', key='wz27_edit_setup', use_container_width=True):
            try:
                reset_onboarding()
            except Exception:
                st.session_state['onboarding_complete'] = False
            _wz27_go('onboarding')


def _wz27_dashboard_home():
    cv_score = _wz27_score('cv_score_value','resume_score', default=75 if str(st.session_state.get('cv_text','')).strip() else 0)
    has_job_text = str(st.session_state.get('current_job_description','') or st.session_state.get('last_understand_job_description','') or st.session_state.get('improve_cv_for_job_desc','')).strip()
    ats_score = _wz27_score('ats_score_value','job_match_score', default=70 if has_job_text else 0)
    interview_score = _wz27_score('interview_score','interview_readiness', default=40)
    name = st.session_state.get('user_name') or st.session_state.get('candidate_name') or 'there'
    st.markdown("""
    <style>
      .wz27-hero{border:1px solid rgba(148,163,184,.22);border-radius:24px;padding:28px;background:linear-gradient(135deg,rgba(30,64,175,.16),rgba(20,184,166,.10));margin-bottom:22px;}
      .wz27-title{font-size:30px;font-weight:850;color:#f8fafc;margin-bottom:4px;}
      .wz27-sub{font-size:16px;color:#cbd5e1;}
      .wz27-card{border:1px solid rgba(148,163,184,.22);border-radius:18px;padding:20px;min-height:180px;background:rgba(15,23,42,.38);}
      .wz27-card h3{font-size:20px;margin-top:0;}
      .wz27-card p{color:#cbd5e1;min-height:70px;}
      .wz27-reco{border:1px solid rgba(34,197,94,.28);border-radius:16px;padding:16px;background:rgba(34,197,94,.08);}
      div[data-testid="stButton"] > button{border-radius:12px;min-height:42px;font-weight:650;}
    </style>
    """, unsafe_allow_html=True)
    st.markdown(f"""
    <div class='wz27-hero'>
      <div class='wz27-title'>👋 Welcome back, {html.escape(str(name))}</div>
      <div class='wz27-sub'>Let’s move you closer to your next job.</div>
    </div>
    """, unsafe_allow_html=True)
    c1,c2,c3 = st.columns(3)
    c1.metric('CV Strength', f'{cv_score}%' if cv_score else 'Not analyzed')
    c2.metric('Job Match', f'{ats_score}%' if ats_score else 'Not analyzed')
    c3.metric('Interview Readiness', f'{interview_score}%')
    st.caption('Scores update after you improve a CV, analyze a job, or complete Work-O-Bot.')
    if st.button('Continue Your Journey', key='wz27_continue', use_container_width=False):
        if not cv_score: _wz27_go('cv_documents')
        elif not ats_score: _wz27_go('job_assist')
        elif interview_score < 70: _wz27_go('workobot')
        else: _wz27_go('job_assist')
    st.divider()
    st.subheader('What do you need today?')
    a,b,c = st.columns(3)
    with a:
        st.markdown("<div class='wz27-card'><h3>🟦 Get More Interviews</h3><p>Improve your CV for a job description, strengthen ATS alignment, and keep changes honest.</p></div>", unsafe_allow_html=True)
        if st.button('Improve My CV', key='wz27_improve', use_container_width=True):
            st.session_state['cv_documents_mode']='improve_cv'; _wz27_go('cv_documents')
    with b:
        st.markdown("<div class='wz27-card'><h3>🟩 Prepare for Interview</h3><p>Practice interview questions based only on your CV, job description, and company context.</p></div>", unsafe_allow_html=True)
        if st.button('Start Work-O-Bot', key='wz27_interview', use_container_width=True):
            _wz27_go('workobot')
    with c:
        st.markdown("<div class='wz27-card'><h3>🟧 Find Relevant Jobs</h3><p>Find better-matched jobs, understand fit, and use the job details across your application.</p></div>", unsafe_allow_html=True)
        if st.button('Find Jobs', key='wz27_jobs', use_container_width=True):
            _wz27_go('job_assist')
    st.divider()
    st.subheader('What WorkZo suggests for you')
    if not cv_score:
        reco, target = 'Add or create your CV first. WorkZo needs this to personalize every feature.', 'cv_documents'
    elif not ats_score:
        reco, target = 'Paste a job description and company website so WorkZo can analyze your match.', 'job_assist'
    elif ats_score < 75:
        reco, target = 'Your job match can improve. Strengthen only truthful keywords from the JD.', 'cv_documents'
    elif interview_score < 70:
        reco, target = 'Practice the real interview using your CV and the job description before applying.', 'workobot'
    else:
        reco, target = 'You look ready to apply. Prepare a focused cover letter and track your application.', 'job_assist'
    st.markdown(f"<div class='wz27-reco'>{html.escape(reco)}</div>", unsafe_allow_html=True)
    if st.button('Do this next', key='wz27_next', use_container_width=True):
        _wz27_go(target)
    st.divider()
    st.subheader('Need help?')
    st.caption('Work-O-Bot is for typed questions: CV doubts, HR messages, career decisions, job search, and language practice.')
    if st.button('Ask Work-O-Bot', key='wz27_bot', use_container_width=False):
        _wz27_go('workobot')


def _wz27_job_assist_page():
    st.markdown('## AI Job Application Assistant')
    st.caption('Paste a job description and company website. WorkZo uses this context across CV improvement, cover letter, and Work-O-Bot without inventing facts.')
    col1, col2 = st.columns(2)
    with col1:
        st.text_input('Target company', value=st.session_state.get('target_company',''), key='wz27_target_company')
    with col2:
        st.text_input('Company website / careers page', value=st.session_state.get('target_company_website',''), key='wz27_company_website', help='Optional, but recommended for company-aware cover letters and interview questions.')
    st.session_state['target_company'] = st.session_state.get('wz27_target_company','')
    st.session_state['company_website'] = st.session_state.get('wz27_company_website','')
    try:
        _wz20_render_job_assist_page()
    except Exception as exc:
        st.error('Job Match page could not load. Showing a safe basic version instead.')
        jd = st.text_area('Paste the job description', value=st.session_state.get('current_job_description',''), height=220, key='wz27_safe_jd')
        if jd.strip():
            st.session_state['current_job_description'] = jd
            st.session_state['last_understand_job_description'] = jd
        if st.button('Use this job for CV + Work-O-Bot', key='wz27_use_job', use_container_width=True):
            _wz27_go('cv_documents')


def _wz27_workobot_page():
    st.markdown('## Work-O-Bot')
    st.caption('Typed assistant for career questions, CV doubts, HR messages, job search, and language practice. Use Work-O-Bot for mock interviews.')
    try:
        show_workobot()
    except Exception as exc:
        st.error('Work-O-Bot could not load.')
        st.exception(exc)


def show_dashboard():
    page_key = st.session_state.get('nav_page') or st.session_state.get('page') or 'dashboard'
    page_key = {'landing':'dashboard','onboarding':'dashboard','founder_dashboard':'dashboard','bot':'workobot','interview':'workobot','jobs':'job_assist','improve_cv':'cv_documents'}.get(page_key, page_key)
    st.session_state['page'] = page_key
    st.session_state['nav_page'] = page_key
    _wz27_force_top()
    _wz27_sidebar(page_key)
    if page_key == 'dashboard':
        _wz27_dashboard_home()
    elif page_key == 'cv_documents':
        show_document_tools()
    elif page_key == 'job_assist':
        _wz27_job_assist_page()
    elif page_key == 'workobot':
        try:
            _wz21_render_interview_practice_page()
        except Exception:
            if 'show_interview_simulation' in globals():
                show_interview_simulation()
            else:
                st.error('Work-O-Bot could not load.')
    elif page_key == 'workobot':
        _wz27_workobot_page()
    else:
        _wz27_dashboard_home()
    st.divider()
    st.caption('WORKZO AI • Beta • Guided career workspace')

# =========================================================
# WorkZo v28 - hard final UX/stability override
# Fixes: dashboard progress bar removal, reliable top scroll,
# visible Work-O-Bot, no founder analytics, lighter/faster dashboard.
# =========================================================
def _wz28_top(force: bool = True):
    try:
        st.markdown("<div id='workzo-top-anchor'></div>", unsafe_allow_html=True)
        js = """
        <script>
        function workzoTop(){
          const doc = window.parent.document;
          try { window.parent.scrollTo(0,0); } catch(e) {}
          try { doc.documentElement.scrollTop = 0; } catch(e) {}
          try { doc.body.scrollTop = 0; } catch(e) {}
          const selectors = ['[data-testid="stAppViewContainer"]','section.main','.main','.block-container'];
          for (const s of selectors){ try { const el = doc.querySelector(s); if(el){ el.scrollTop = 0; } } catch(e) {} }
          try { doc.getElementById('workzo-top-anchor').scrollIntoView({block:'start'}); } catch(e) {}
        }
        workzoTop(); setTimeout(workzoTop, 20); setTimeout(workzoTop, 120); setTimeout(workzoTop, 350);
        </script>
        """
        if hasattr(st, 'iframe'):
            st.iframe(srcdoc=js, height=1, width=1)
        else:
            try:
                import streamlit.components.v1 as components
                components.html(js, height=1, width=1)
            except Exception:
                pass
    except Exception:
        pass


def _wz28_css():
    st.markdown("""
    <style>
      .wz28-hide-progress [data-testid="stProgress"] {display:none !important;}
      div[data-testid="stButton"] > button{border-radius:12px;min-height:42px;font-weight:650;}
      .wz28-hero{border:1px solid rgba(148,163,184,.22);border-radius:24px;padding:28px;background:linear-gradient(135deg,rgba(30,64,175,.14),rgba(20,184,166,.10));margin-bottom:22px;}
      .wz28-title{font-size:30px;font-weight:850;color:#f8fafc;margin-bottom:4px;}
      .wz28-sub{font-size:16px;color:#cbd5e1;}
      .wz28-card{border:1px solid rgba(148,163,184,.22);border-radius:18px;padding:20px;min-height:178px;background:rgba(15,23,42,.38);}
      .wz28-card h3{font-size:20px;margin-top:0;}
      .wz28-card p{color:#cbd5e1;min-height:68px;}
      .wz28-reco{border:1px solid rgba(34,197,94,.28);border-radius:16px;padding:16px;background:rgba(34,197,94,.08);}
      .wz28-sidebar-card{border:1px solid rgba(20,184,166,.35);border-radius:18px;padding:16px;margin-bottom:16px;background:rgba(15,23,42,.65);}
      .wz28-sidebar-logo{width:44px;height:44px;border-radius:12px;margin-bottom:10px;}
      .wz28-sidebar-brand{font-weight:800;font-size:20px;letter-spacing:.04em;}
      .wz28-sidebar-small{font-size:12px;color:#94a3b8;}
    </style>
    """, unsafe_allow_html=True)


def _wz28_go(page_key: str):
    aliases = {
        'home':'dashboard','landing':'dashboard','onboarding':'dashboard',
        'my_cv':'cv_documents','improve_cv':'cv_documents','cv':'cv_documents',
        'jobs':'job_assist','job_match':'job_assist','prepare_job':'job_assist',
        'interview':'workobot','speaking_practice':'workobot',
        'bot':'workobot','work-o-bot':'workobot','work_o_bot':'workobot',
        'founder_dashboard':'dashboard','founder':'dashboard',
    }
    page_key = aliases.get(str(page_key or 'dashboard'), str(page_key or 'dashboard'))
    st.session_state['page'] = page_key
    st.session_state['nav_page'] = page_key
    st.session_state['_workzo_scroll_to_top'] = True
    try:
        nonce = int(st.session_state.get('nav_change_nonce', 0)) + 1
        st.session_state['nav_change_nonce'] = nonce
        st.query_params['page'] = page_key
        st.query_params['top'] = str(nonce)
    except Exception:
        pass
    st.rerun()

_wz27_go = _wz28_go
_wz25_go = _wz28_go
_wz24_go = _wz28_go
_wz21_go = _wz28_go
_wz19_go = _wz28_go
go_to_nav = _wz28_go


def _wz28_score(*keys, default=0):
    for k in keys:
        try:
            v = st.session_state.get(k)
            if v is not None and str(v).strip() != '':
                return max(0, min(100, int(float(v))))
        except Exception:
            pass
    return default


def _wz28_sidebar(page_key: str):
    with st.sidebar:
        try:
            logo_src = image_to_data_uri(ICON_PATH) or image_to_data_uri(LOGO_PATH)
        except Exception:
            logo_src = None
        if logo_src:
            st.markdown(f"""
            <div class='wz28-sidebar-card'>
                <img src='{logo_src}' class='wz28-sidebar-logo' alt='WorkZo AI logo'>
                <div class='wz28-sidebar-brand'>WORKZO AI</div>
                <div class='wz28-sidebar-small'>Guided career workspace</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown('### WorkZo AI')
        st.markdown('##### Navigation')
        nav = [('dashboard','Dashboard'),('cv_documents','My CV'),('job_assist','Job Match'),('workobot','Work-O-Bot')]
        for key, label in nav:
            if st.button(label + (' ✓' if page_key == key else ''), key=f'wz28_nav_{key}', use_container_width=True):
                _wz28_go(key)
        st.markdown('##### Profile')
        st.caption(f"Country: {st.session_state.get('country') or st.session_state.get('target_country') or 'Not set'}")
        st.caption('Resume uploaded' if str(st.session_state.get('cv_text','')).strip() else 'CV missing')
        st.markdown('##### Settings')
        try:
            language_list = language_options if language_options else ['English', 'German', 'Dutch']
            current = st.session_state.get('preferred_language') or st.session_state.get('language') or 'English'
            if current not in language_list:
                current = 'English' if 'English' in language_list else language_list[0]
            chosen = st.selectbox('Language', language_list, index=language_list.index(current), key='wz28_language')
            set_single_preferred_language(chosen)
            st.session_state['preferred_language'] = chosen
            st.session_state['language'] = chosen
        except Exception:
            pass
        if st.button('Edit setup', key='wz28_edit_setup', use_container_width=True):
            try:
                reset_onboarding()
            except Exception:
                st.session_state['onboarding_complete'] = False
            _wz28_go('onboarding')


def _wz28_dashboard_home():
    _wz28_css()
    cv_exists = bool(str(st.session_state.get('cv_text','')).strip() or st.session_state.get('structured_cv_json'))
    job_exists = bool(str(st.session_state.get('current_job_description','') or st.session_state.get('last_understand_job_description','') or st.session_state.get('improve_cv_for_job_desc','')).strip())
    cv_score = _wz28_score('cv_score_value','resume_score', default=75 if cv_exists else 0)
    ats_score = _wz28_score('ats_score_value','job_match_score', default=70 if job_exists else 0)
    interview_score = _wz28_score('interview_score','interview_readiness', default=40)
    name = st.session_state.get('user_name') or st.session_state.get('candidate_name') or 'there'
    st.markdown("<div class='wz28-hide-progress'>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class='wz28-hero'>
      <div class='wz28-title'>Welcome back, {html.escape(str(name))}</div>
      <div class='wz28-sub'>Let’s move you closer to your next job.</div>
    </div>
    """, unsafe_allow_html=True)
    c1,c2,c3 = st.columns(3)
    c1.metric('CV Strength', f'{cv_score}%' if cv_score else 'Not analyzed')
    c2.metric('Job Match', f'{ats_score}%' if ats_score else 'Not analyzed')
    c3.metric('Interview Readiness', f'{interview_score}%')
    st.caption('No progress bar here: use the cards below for the next best action.')
    if st.button('Continue Your Journey', key='wz28_continue', use_container_width=False):
        if not cv_exists: _wz28_go('cv_documents')
        elif not job_exists: _wz28_go('job_assist')
        elif interview_score < 70: _wz28_go('workobot')
        else: _wz28_go('job_assist')
    st.divider()
    st.subheader('What do you need today?')
    a,b,c = st.columns(3)
    with a:
        st.markdown("<div class='wz28-card'><h3>Get More Interviews</h3><p>Improve your CV for a job description, strengthen ATS alignment, and keep changes honest.</p></div>", unsafe_allow_html=True)
        if st.button('Improve My CV', key='wz28_improve', use_container_width=True):
            st.session_state['cv_documents_mode']='improve_cv'; _wz28_go('cv_documents')
    with b:
        st.markdown("<div class='wz28-card'><h3>Prepare for Interview</h3><p>Practice questions based only on your CV, job description, company context, country, and chosen language.</p></div>", unsafe_allow_html=True)
        if st.button('Start Work-O-Bot', key='wz28_interview', use_container_width=True):
            _wz28_go('workobot')
    with c:
        st.markdown("<div class='wz28-card'><h3>Find Relevant Jobs</h3><p>Analyze a job, add company website context, and reuse it for CV, cover letter, and interview preparation.</p></div>", unsafe_allow_html=True)
        if st.button('Find Jobs', key='wz28_jobs', use_container_width=True):
            _wz28_go('job_assist')
    st.divider()
    st.subheader('What WorkZo suggests for you')
    if not cv_exists:
        reco, target = 'Add or create your CV first. WorkZo needs this to personalize every feature.', 'cv_documents'
    elif not job_exists:
        reco, target = 'Paste a job description and company website so WorkZo can analyze your match.', 'job_assist'
    elif ats_score < 75:
        reco, target = 'Your job match can improve. Add only truthful keywords from the job description.', 'cv_documents'
    elif interview_score < 70:
        reco, target = 'Practice the real interview using your CV, job description, and selected language.', 'workobot'
    else:
        reco, target = 'You look ready to apply. Prepare a focused cover letter and track your application.', 'job_assist'
    st.markdown(f"<div class='wz28-reco'>{html.escape(reco)}</div>", unsafe_allow_html=True)
    if st.button('Do this next', key='wz28_next', use_container_width=True):
        _wz28_go(target)
    st.divider()
    st.subheader('Need help?')
    st.caption('Work-O-Bot is a separate typed assistant for career questions, HR messages, CV doubts, job search, and language practice.')
    if st.button('Ask Work-O-Bot', key='wz28_bot', use_container_width=False):
        _wz28_go('workobot')
    st.markdown('</div>', unsafe_allow_html=True)


def _wz28_job_assist_page():
    _wz28_css()
    st.markdown('## AI Job Application Assistant')
    st.caption('Paste a job description and company website. WorkZo reuses this context for CV improvement, cover letters, and Work-O-Bot.')
    col1, col2 = st.columns(2)
    with col1:
        company = st.text_input('Target company', value=st.session_state.get('target_company',''), key='wz28_target_company')
    with col2:
        website = st.text_input('Company website / careers page', value=st.session_state.get('target_company_website',''), key='wz28_company_website')
    st.session_state['target_company'] = company
    st.session_state['company_website'] = website
    if website:
        st.info('Company website saved. WorkZo will use it for CV advice, cover letters, and interview questions without inventing facts.')
    try:
        _wz20_render_job_assist_page()
    except Exception:
        jd = st.text_area('Paste the job description', value=st.session_state.get('current_job_description',''), height=220, key='wz28_safe_jd')
        if jd.strip():
            st.session_state['current_job_description'] = jd
            st.session_state['last_understand_job_description'] = jd
        if st.button('Use this job for CV + Work-O-Bot', key='wz28_use_job', use_container_width=True):
            _wz28_go('cv_documents')


def _wz28_workobot_page():
    _wz28_css()
    st.markdown('## Work-O-Bot')
    st.caption('Typed assistant for career questions, CV doubts, HR messages, job search, and language practice. Work-O-Bot is separate.')
    try:
        show_workobot()
    except Exception as exc:
        st.error('Work-O-Bot could not load.')
        st.exception(exc)


def show_dashboard():
    page_key = st.session_state.get('nav_page') or st.session_state.get('page') or 'dashboard'
    page_key = {'landing':'dashboard','onboarding':'dashboard','founder_dashboard':'dashboard','founder':'dashboard','bot':'workobot','interview':'workobot','jobs':'job_assist','improve_cv':'cv_documents'}.get(page_key, page_key)
    if page_key not in {'dashboard','cv_documents','job_assist','workobot','workobot'}:
        page_key = 'dashboard'
    st.session_state['page'] = page_key
    st.session_state['nav_page'] = page_key
    _wz28_top(True)
    _wz28_sidebar(page_key)
    if page_key == 'dashboard':
        _wz28_dashboard_home()
    elif page_key == 'cv_documents':
        _wz28_css(); show_document_tools()
    elif page_key == 'job_assist':
        _wz28_job_assist_page()
    elif page_key == 'workobot':
        _wz28_css()
        try:
            _wz21_render_interview_practice_page()
        except Exception:
            if 'show_interview_simulation' in globals():
                show_interview_simulation()
            else:
                st.error('Work-O-Bot could not load.')
    elif page_key == 'workobot':
        _wz28_workobot_page()
    st.caption('WORKZO AI • Beta • Guided career workspace')

# =========================================================
# WorkZo v29 - final UX cleanup: reliable top scroll, clean sidebar,
# no duplicate interview wrapper.
# =========================================================
def _wz29_force_top():
    try:
        st.markdown("<div id='workzo-page-top'></div>", unsafe_allow_html=True)
        js = """
        <script>
        function wzTop(){
          try { window.parent.scrollTo(0,0); } catch(e) {}
          try { window.parent.document.documentElement.scrollTop = 0; } catch(e) {}
          try { window.parent.document.body.scrollTop = 0; } catch(e) {}
          const sels = ['section.main','[data-testid="stAppViewContainer"]','[data-testid="stMain"]','.main','.block-container'];
          for (const s of sels) { try { const el = window.parent.document.querySelector(s); if (el) { el.scrollTop = 0; } } catch(e) {} }
        }
        wzTop(); setTimeout(wzTop, 40); setTimeout(wzTop, 160); setTimeout(wzTop, 450);
        </script>
        """
        import streamlit.components.v1 as components
        components.html(js, height=0, width=0)
    except Exception:
        pass

def _wz28_top(force: bool = True):
    _wz29_force_top()

def _wz29_clean_css():
    st.markdown("""
    <style>
      section[data-testid="stSidebar"] .block-container{padding-top:1.2rem;padding-left:1rem;padding-right:1rem;}
      .wz29-side-card{border:1px solid rgba(20,184,166,.35);border-radius:18px;padding:15px;margin:4px 0 18px;background:linear-gradient(135deg,rgba(8,47,73,.72),rgba(15,23,42,.80));}
      .wz29-side-logo{width:46px;height:46px;border-radius:12px;margin-bottom:10px;}
      .wz29-side-brand{font-size:20px;font-weight:850;letter-spacing:.03em;color:#fff;}
      .wz29-side-sub{font-size:13px;color:#94a3b8;margin-top:3px;}
      .wz29-side-label{font-size:12px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:#94a3b8;margin:16px 0 8px;}
      section[data-testid="stSidebar"] div[data-testid="stButton"] > button{min-height:42px;border-radius:12px;justify-content:flex-start;font-weight:650;}
    </style>
    """, unsafe_allow_html=True)

def _wz28_sidebar(page_key: str):
    _wz29_clean_css()
    with st.sidebar:
        try:
            logo_src = image_to_data_uri(ICON_PATH) or image_to_data_uri(LOGO_PATH)
        except Exception:
            logo_src = None
        if logo_src:
            st.markdown(f"""
            <div class='wz29-side-card'>
                <img src='{logo_src}' class='wz29-side-logo' alt='WorkZo AI logo'>
                <div class='wz29-side-brand'>WORKZO AI</div>
                <div class='wz29-side-sub'>Guided career workspace</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("### WorkZo AI")
        st.markdown("<div class='wz29-side-label'>Navigation</div>", unsafe_allow_html=True)
        nav = [('dashboard','Dashboard'),('cv_documents','My CV'),('job_assist','Job Match'),('workobot','Work-O-Bot')]
        for key, label in nav:
            if st.button(label + (' ✓' if page_key == key else ''), key=f'wz29_nav_{key}', use_container_width=True):
                _wz28_go(key)
        st.markdown("<div class='wz29-side-label'>Settings</div>", unsafe_allow_html=True)
        try:
            language_list = language_options if language_options else ['English','German','Dutch']
            current = st.session_state.get('preferred_language') or st.session_state.get('language') or 'English'
            if current not in language_list:
                current = 'English' if 'English' in language_list else language_list[0]
            chosen = st.selectbox('Language', language_list, index=language_list.index(current), key='wz29_language')
            set_single_preferred_language(chosen)
            st.session_state['preferred_language'] = chosen
            st.session_state['language'] = chosen
        except Exception:
            pass
        if st.button('Edit setup', key='wz29_edit_setup', use_container_width=True):
            try:
                reset_onboarding()
            except Exception:
                st.session_state['onboarding_complete'] = False
            _wz28_go('onboarding')

def _wz21_render_interview_practice_page():
    _wz29_force_top()
    if 'render_real_interview_simulation' in globals():
        render_real_interview_simulation()
    else:
        st.error('Work-O-Bot could not load. Please check 09_interview_assistant.py.')

# =========================================================
# WorkZo v30 - shared job/company context + cleaner centered sidebar
# =========================================================
def _wz30_get_job_context() -> dict:
    return {
        'company': st.session_state.get('target_company') or st.session_state.get('real_interview_company') or st.session_state.get('prepare_target_company') or '',
        'role': st.session_state.get('target_role') or st.session_state.get('target_job_title') or st.session_state.get('prepare_target_role') or '',
        'website': st.session_state.get('target_company_website') or '',
        'job_description': st.session_state.get('current_job_description') or st.session_state.get('last_understand_job_description') or st.session_state.get('job_description') or st.session_state.get('improve_cv_for_job_desc') or '',
    }

def _wz30_set_job_context(company='', role='', website='', job_description='') -> None:
    st.session_state['target_company'] = str(company or '').strip()
    st.session_state['real_interview_company'] = str(company or '').strip()
    st.session_state['prepare_target_company'] = str(company or '').strip()
    st.session_state['target_role'] = str(role or '').strip()
    st.session_state['target_job_title'] = str(role or '').strip()
    st.session_state['prepare_target_role'] = str(role or '').strip()
    st.session_state['company_website'] = str(website or '').strip()
    jd = str(job_description or '').strip()
    st.session_state['current_job_description'] = jd
    st.session_state['last_understand_job_description'] = jd
    st.session_state['job_description'] = jd
    st.session_state['improve_cv_for_job_desc'] = jd
    st.session_state['last_prepare_job_description'] = jd

def _wz30_saved_application_contexts() -> list:
    apps = st.session_state.get('saved_application_contexts')
    return apps if isinstance(apps, list) else []

def _wz30_save_application_context(company, role, website, jd) -> None:
    company = str(company or '').strip(); role = str(role or '').strip(); website = str(website or '').strip(); jd = str(jd or '').strip()
    if not any([company, role, website, jd]):
        return
    label = ' — '.join([x for x in [company or 'Company not specified', role or 'Role not specified'] if x])
    item = {'label': label, 'company': company, 'role': role, 'website': website, 'job_description': jd}
    apps = [a for a in _wz30_saved_application_contexts() if not (a.get('company') == company and a.get('role') == role and a.get('website') == website)]
    apps.insert(0, item)
    st.session_state['saved_application_contexts'] = apps[:12]

def _wz30_context_manager(prefix='wz30') -> dict:
    ctx = _wz30_get_job_context()
    saved = _wz30_saved_application_contexts()
    if saved:
        labels = ['Use current / new company'] + [a.get('label', 'Saved company') for a in saved]
        choice = st.selectbox('Saved company/job details', labels, key=f'{prefix}_saved_choice')
        if choice != labels[0]:
            item = saved[labels.index(choice)-1]
            _wz30_set_job_context(item.get('company',''), item.get('role',''), item.get('website',''), item.get('job_description',''))
            ctx = _wz30_get_job_context()
            st.info('Loaded saved company/job details. You can edit them below.')
    c1, c2 = st.columns(2)
    with c1:
        company = st.text_input('Target company', value=ctx.get('company',''), key=f'{prefix}_company')
    with c2:
        role = st.text_input('Target role', value=ctx.get('role',''), key=f'{prefix}_role')
    website = st.text_input('Company website / careers page', value=ctx.get('website',''), key=f'{prefix}_website', help='Paste once. WorkZo reuses it for CV, cover letter, job match, and Work-O-Bot.')
    jd = st.text_area('Paste the job description', value=ctx.get('job_description',''), height=210, key=f'{prefix}_jd')
    _wz30_set_job_context(company, role, website, jd)
    c3, c4 = st.columns(2)
    with c3:
        if st.button('Save this company/job', key=f'{prefix}_save', use_container_width=True):
            _wz30_save_application_context(company, role, website, jd)
            st.success('Saved. You can load it later when applying to multiple companies.')
    with c4:
        if st.button('Start new company', key=f'{prefix}_new', use_container_width=True):
            _wz30_set_job_context('', '', '', '')
            for k in [f'{prefix}_company', f'{prefix}_role', f'{prefix}_website', f'{prefix}_jd']:
                st.session_state[k] = ''
            st.rerun()
    return _wz30_get_job_context()

def _wz29_clean_css():
    st.markdown("""
    <style>
      section[data-testid="stSidebar"] .block-container{padding-top:1.2rem;padding-left:1rem;padding-right:1rem;}
      .wz29-side-card{border:1px solid rgba(20,184,166,.35);border-radius:18px;padding:15px;margin:4px 0 18px;background:linear-gradient(135deg,rgba(8,47,73,.72),rgba(15,23,42,.80));}
      .wz29-side-logo{width:46px;height:46px;border-radius:12px;margin-bottom:10px;}
      .wz29-side-brand{font-size:20px;font-weight:850;letter-spacing:.03em;color:#fff;}
      .wz29-side-sub{font-size:13px;color:#94a3b8;margin-top:3px;}
      .wz29-side-label{font-size:12px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:#94a3b8;margin:18px 0 8px;text-align:left;}
      section[data-testid="stSidebar"] div[data-testid="stButton"]{display:flex;justify-content:center;}
      section[data-testid="stSidebar"] div[data-testid="stButton"] > button{width:200px !important;min-width:200px !important;max-width:200px !important;min-height:42px;border-radius:12px;justify-content:center;text-align:center;font-weight:650;margin:4px auto;}
    </style>
    """, unsafe_allow_html=True)

def _wz28_sidebar(page_key: str):
    _wz29_clean_css()
    with st.sidebar:
        try:
            logo_src = image_to_data_uri(ICON_PATH) or image_to_data_uri(LOGO_PATH)
        except Exception:
            logo_src = None
        if logo_src:
            st.markdown(f"""
            <div class='wz29-side-card'>
                <img src='{logo_src}' class='wz29-side-logo' alt='WorkZo AI logo'>
                <div class='wz29-side-brand'>WORKZO AI</div>
                <div class='wz29-side-sub'>Guided career workspace</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown('### WorkZo AI')
        st.markdown("<div class='wz29-side-label'>Navigation</div>", unsafe_allow_html=True)
        nav = [('dashboard','Dashboard'),('cv_documents','My CV'),('job_assist','Job Match'),('workobot','Work-O-Bot')]
        for key, label in nav:
            if st.button(label + (' ✓' if page_key == key else ''), key=f'wz30_nav_{key}', use_container_width=False):
                _wz28_go(key)
        st.markdown("<div class='wz29-side-label'>Settings</div>", unsafe_allow_html=True)
        try:
            language_list = language_options if language_options else ['English','German','Dutch']
            current = st.session_state.get('preferred_language') or st.session_state.get('language') or 'English'
            if current not in language_list:
                current = 'English' if 'English' in language_list else language_list[0]
            chosen = st.selectbox('Language', language_list, index=language_list.index(current), key='wz30_language')
            set_single_preferred_language(chosen)
            st.session_state['preferred_language'] = chosen
            st.session_state['language'] = chosen
        except Exception:
            pass
        if st.button('Edit setup', key='wz30_edit_setup', use_container_width=False):
            try:
                reset_onboarding()
            except Exception:
                st.session_state['onboarding_complete'] = False
            _wz28_go('onboarding')

def _wz28_job_assist_page():
    _wz28_css()
    st.markdown('## AI Job Application Assistant')
    st.caption('Add company, role, website, and job description once. WorkZo reuses this context across CV improvement, cover letter, Job Match, and Work-O-Bot.')
    ctx = _wz30_context_manager('wz30_job')
    if ctx.get('website'):
        st.info('Company website saved. WorkZo will use it without inventing company facts.')
    try:
        _wz20_render_job_assist_page()
    except Exception:
        st.warning('Using simplified Job Match view.')
        if st.button('Use this job for CV + Work-O-Bot', key='wz30_use_job', use_container_width=True):
            _wz28_go('cv_documents')


# =========================================================
# WorkZo v31 - Smart Command Center dashboard
# - Separate Resume Score, ATS Score, Job Fit, Interview Readiness
# - Visual rate cards
# - Smart next action based on score/state
# - No confusing generic "Job Match 90%" without a job description
# =========================================================
def _wz31_clamp_score(value, default=0):
    try:
        if value is None or str(value).strip() == "":
            return int(default)
        return max(0, min(100, int(float(value))))
    except Exception:
        return int(default or 0)


def _wz31_get_score(*keys, default=0):
    for key in keys:
        try:
            value = st.session_state.get(key)
            if value is not None and str(value).strip() != "":
                return _wz31_clamp_score(value, default)
        except Exception:
            pass
    return _wz31_clamp_score(default, 0)


def _wz31_score_label(score):
    score = _wz31_clamp_score(score)
    if score >= 85:
        return "Excellent"
    if score >= 75:
        return "Good"
    if score >= 60:
        return "Needs improvement"
    if score > 0:
        return "Weak"
    return "Not analyzed"


def _wz31_escape(value):
    try:
        return html.escape(str(value or ""))
    except Exception:
        return str(value or "")


def _wz31_css():
    st.markdown("""
    <style>
      .wz31-hero{
        border:1px solid rgba(20,184,166,.30);
        border-radius:28px;
        padding:30px 34px;
        margin:8px 0 24px 0;
        background:radial-gradient(circle at top left,rgba(20,184,166,.20),transparent 35%),linear-gradient(135deg,rgba(30,64,175,.28),rgba(8,47,73,.24));
        box-shadow:0 18px 50px rgba(2,6,23,.28);
      }
      .wz31-kicker{color:#93c5fd;font-size:.78rem;font-weight:850;letter-spacing:.12em;text-transform:uppercase;margin-bottom:8px;}
      .wz31-title{color:#fff;font-size:2rem;font-weight:900;line-height:1.12;margin-bottom:8px;}
      .wz31-sub{color:#dbeafe;font-size:1.02rem;line-height:1.5;max-width:900px;}
      .wz31-chip-row{display:flex;gap:8px;flex-wrap:wrap;margin-top:16px;}
      .wz31-chip{border:1px solid rgba(96,165,250,.28);background:rgba(37,99,235,.18);border-radius:999px;color:#dbeafe;font-size:.84rem;font-weight:700;padding:7px 11px;}
      .wz31-next{
        border:1px solid rgba(45,212,191,.32);
        border-radius:22px;
        padding:20px 22px;
        background:linear-gradient(135deg,rgba(20,184,166,.18),rgba(37,99,235,.14));
        margin:12px 0 22px 0;
      }
      .wz31-next-label{color:#99f6e4;font-size:.78rem;font-weight:900;letter-spacing:.1em;text-transform:uppercase;margin-bottom:6px;}
      .wz31-next-title{color:#fff;font-size:1.25rem;font-weight:900;margin-bottom:5px;}
      .wz31-next-copy{color:#cbd5e1;font-size:.95rem;line-height:1.5;}
      .wz31-rate-card{
        border:1px solid rgba(148,163,184,.18);
        border-radius:22px;
        padding:18px 18px 16px 18px;
        background:linear-gradient(180deg,rgba(30,41,59,.82),rgba(15,23,42,.72));
        min-height:168px;
        box-shadow:0 12px 30px rgba(2,6,23,.18);
        margin-bottom:14px;
      }
      .wz31-rate-head{display:flex;justify-content:space-between;align-items:flex-start;gap:10px;margin-bottom:10px;}
      .wz31-rate-title{color:#e2e8f0;font-size:.95rem;font-weight:850;line-height:1.25;}
      .wz31-rate-badge{border:1px solid rgba(148,163,184,.25);border-radius:999px;padding:4px 8px;color:#cbd5e1;font-size:.72rem;font-weight:800;white-space:nowrap;}
      .wz31-score{color:#fff;font-size:2.15rem;font-weight:950;line-height:1;margin:8px 0 10px;}
      .wz31-bar-bg{height:10px;border-radius:999px;background:rgba(148,163,184,.20);overflow:hidden;margin:7px 0 9px;}
      .wz31-bar-fill{height:10px;border-radius:999px;background:linear-gradient(90deg,#38bdf8,#2dd4bf);}
      .wz31-rate-copy{color:#94a3b8;font-size:.84rem;line-height:1.45;margin-top:8px;}
      .wz31-actions{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px;margin:14px 0 22px;}
      .wz31-action-card{border:1px solid rgba(148,163,184,.16);border-radius:22px;padding:18px;background:rgba(15,23,42,.56);min-height:148px;}
      .wz31-action-title{color:#fff;font-size:1.05rem;font-weight:900;margin-bottom:8px;}
      .wz31-action-copy{color:#aebbd0;font-size:.9rem;line-height:1.45;}
      .wz31-flow{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px;margin-top:10px;}
      .wz31-step{border:1px solid rgba(148,163,184,.16);border-radius:18px;padding:13px 14px;background:rgba(15,23,42,.46);}
      .wz31-step.done{border-color:rgba(45,212,191,.42);background:rgba(20,184,166,.12);}
      .wz31-step-title{color:#fff;font-weight:850;font-size:.92rem;}
      .wz31-step-sub{color:#94a3b8;font-size:.78rem;margin-top:3px;}
    </style>
    """, unsafe_allow_html=True)


def _wz31_rate_card(title, score, subtitle, *, missing=False):
    score = _wz31_clamp_score(score)
    label = "Add details" if missing else _wz31_score_label(score)
    shown = "—" if missing or score <= 0 else f"{score}%"
    fill = 0 if missing else score
    st.markdown(f"""
    <div class='wz31-rate-card'>
      <div class='wz31-rate-head'>
        <div class='wz31-rate-title'>{_wz31_escape(title)}</div>
        <div class='wz31-rate-badge'>{_wz31_escape(label)}</div>
      </div>
      <div class='wz31-score'>{_wz31_escape(shown)}</div>
      <div class='wz31-bar-bg'><div class='wz31-bar-fill' style='width:{fill}%;'></div></div>
      <div class='wz31-rate-copy'>{_wz31_escape(subtitle)}</div>
    </div>
    """, unsafe_allow_html=True)


def _wz31_pick_next_action(cv_exists, job_exists, resume_score, ats_score, job_fit_score, interview_score):
    if not cv_exists:
        return {
            "title": "Add your CV first",
            "copy": "WorkZo needs your CV to score it, suggest matching roles, and personalize every next step.",
            "button": "Add / Create CV",
            "target": "cv_documents",
        }
    if resume_score < 75 or ats_score < 75:
        return {
            "title": "Improve your CV before applying",
            "copy": "Your resume or ATS score still needs work. Fix structure, keywords, and clarity before spending time on applications.",
            "button": "Improve CV",
            "target": "cv_documents",
        }
    if not job_exists:
        return {
            "title": "Find or paste a real job next",
            "copy": "Your CV looks ready. Now choose a real job description so WorkZo can check job fit and tailor your application.",
            "button": "Find / Analyze Jobs",
            "target": "job_assist",
        }
    if job_fit_score and job_fit_score < 70:
        return {
            "title": "Tailor CV to this job first",
            "copy": "The current job fit is not strong enough yet. Add only truthful job-relevant keywords and stronger matching bullets.",
            "button": "Tailor CV for Job",
            "target": "cv_documents",
        }
    if interview_score < 75:
        return {
            "title": "Practice for the interview",
            "copy": "Your CV and ATS look good. Use Work-O-Bot to practice job-specific answers based on your CV, job description, company, and language.",
            "button": "Practice with Work-O-Bot",
            "target": "workobot",
        }
    return {
        "title": "Ready to apply",
        "copy": "Your scores look strong. Generate a focused cover letter, save this application, and apply.",
        "button": "Prepare Application",
        "target": "job_assist",
    }


def _wz31_action_card(title, copy, button, target, key, extra_state=None):
    st.markdown(f"""
    <div class='wz31-action-card'>
      <div class='wz31-action-title'>{_wz31_escape(title)}</div>
      <div class='wz31-action-copy'>{_wz31_escape(copy)}</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button(button, key=key, use_container_width=True):
        if isinstance(extra_state, dict):
            for k, v in extra_state.items():
                st.session_state[k] = v
        _wz28_go(target)


def _wz28_dashboard_home():
    _wz28_css()
    _wz31_css()
    cv_exists = bool(str(st.session_state.get('cv_text','')).strip() or st.session_state.get('structured_cv_json'))
    job_text = str(st.session_state.get('current_job_description','') or st.session_state.get('last_understand_job_description','') or st.session_state.get('improve_cv_for_job_desc','') or st.session_state.get('job_description','')).strip()
    job_exists = bool(job_text)
    company = str(st.session_state.get('target_company') or st.session_state.get('prepare_target_company') or '').strip()
    country = str(st.session_state.get('country') or st.session_state.get('target_country') or 'Not set')
    language = str(st.session_state.get('preferred_language') or st.session_state.get('language') or 'English')
    role = str(st.session_state.get('target_role') or st.session_state.get('target_job_title') or st.session_state.get('detected_target_role') or 'Target role not set')

    resume_score = _wz31_get_score('cv_score_value', 'resume_score', 'resume_quality_score', default=75 if cv_exists else 0)
    ats_score = _wz31_get_score('ats_score_value', 'ats_score', default=70 if cv_exists else 0)
    job_fit_score = _wz31_get_score('job_fit_score_value', 'job_match_score', 'latest_job_fit_score', default=0)
    if job_exists and job_fit_score <= 0:
        job_fit_score = _wz31_get_score('ats_score_value', default=60)
    interview_score = _wz31_get_score('interview_score', 'interview_readiness', default=0)
    if interview_score <= 0:
        if cv_exists and job_exists and resume_score >= 75 and ats_score >= 75:
            interview_score = 65
        elif cv_exists:
            interview_score = 45
        else:
            interview_score = 20

    next_action = _wz31_pick_next_action(cv_exists, job_exists, resume_score, ats_score, job_fit_score, interview_score)

    st.markdown(f"""
    <div class='wz31-hero'>
      <div class='wz31-kicker'>WorkZo Command Center</div>
      <div class='wz31-title'>Your next best move is clear.</div>
      <div class='wz31-sub'>WorkZo reads your CV, country, language, job description, and company context, then recommends what to do next instead of showing every feature at once.</div>
      <div class='wz31-chip-row'>
        <span class='wz31-chip'>{_wz31_escape(country)}</span>
        <span class='wz31-chip'>{_wz31_escape(language)}</span>
        <span class='wz31-chip'>{'CV ready' if cv_exists else 'CV missing'}</span>
        <span class='wz31-chip'>{'Job added' if job_exists else 'Job not added'}</span>
        <span class='wz31-chip'>{_wz31_escape(company or 'Company not added')}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class='wz31-next'>
      <div class='wz31-next-label'>Recommended next step</div>
      <div class='wz31-next-title'>{_wz31_escape(next_action['title'])}</div>
      <div class='wz31-next-copy'>{_wz31_escape(next_action['copy'])}</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button(next_action['button'], key='wz31_primary_next_action', use_container_width=True):
        if next_action['target'] == 'cv_documents' and job_exists:
            st.session_state['document_tools_mode'] = 'Improve CV for a Job'
        _wz28_go(next_action['target'])

    st.markdown('### Readiness overview')
    r1, r2, r3, r4 = st.columns(4)
    with r1:
        _wz31_rate_card('Resume Score', resume_score, 'Clarity, structure, achievements, and overall CV quality.', missing=not cv_exists)
    with r2:
        _wz31_rate_card('ATS Score', ats_score, 'Scanner-friendly formatting, keywords, sections, and parsing safety.', missing=not cv_exists)
    with r3:
        _wz31_rate_card('Job Fit', job_fit_score, 'Fit for the current pasted job description. Add a job before trusting this score.', missing=not job_exists)
    with r4:
        _wz31_rate_card('Interview Readiness', interview_score, 'How ready you are to explain this CV and job fit clearly.', missing=not cv_exists)

    st.markdown('### Smart actions')
    a1, a2, a3, a4 = st.columns(4)
    with a1:
        _wz31_action_card('Improve CV', 'Use this when Resume or ATS score is below 75, or when you want to tailor for one job.', 'Open CV Tools', 'cv_documents', 'wz31_open_cv', {'document_tools_mode':'Improve CV for a Job' if job_exists else 'Improve / Update CV'})
    with a2:
        _wz31_action_card('Find / Analyze Jobs', 'Use this when your CV score is good and you need real jobs or a job-fit check.', 'Open Job Assist', 'job_assist', 'wz31_open_jobs')
    with a3:
        _wz31_action_card('Cover Letter', 'Use company, job description, and CV context to write a focused cover letter.', 'Create Cover Letter', 'cv_documents', 'wz31_open_cover', {'document_tools_mode':'Cover Letter Generator + Language'})
    with a4:
        _wz31_action_card('Work-O-Bot', 'Ask career questions or practice interview answers in your selected language.', 'Ask Work-O-Bot', 'workobot', 'wz31_open_bot')

    st.markdown('### Application flow')
    improved_ready = bool(str(st.session_state.get('improved_cv_text','') or st.session_state.get('latest_improved_cv','') or st.session_state.get('final_cv_text','')).strip())
    cover_ready = bool(str(st.session_state.get('latest_cover_letter','') or st.session_state.get('cover_letter_text','')).strip())
    flow = [
        ('1. CV added', cv_exists),
        ('2. Resume + ATS checked', bool(cv_exists and resume_score > 0 and ats_score > 0)),
        ('3. Job added', job_exists),
        ('4. CV tailored', improved_ready or (job_exists and resume_score >= 75 and ats_score >= 75)),
        ('5. Cover letter / prep', cover_ready),
    ]
    html_steps = []
    for label, done in flow:
        html_steps.append(f"<div class='wz31-step {'done' if done else ''}'><div class='wz31-step-title'>{'✅ ' if done else '○ '}{_wz31_escape(label)}</div><div class='wz31-step-sub'>{'Complete' if done else 'Next step pending'}</div></div>")
    st.markdown("<div class='wz31-flow'>" + "".join(html_steps) + "</div>", unsafe_allow_html=True)

    st.caption('Scores are guidance only. WorkZo should not invent skills, company facts, language level, salary, or experience.')

# =========================================================
# WorkZo v32 - smarter dashboard, score memory, no dashboard job-fit card
# =========================================================
def _wz32_force_scroll_top():
    try:
        st.markdown('<span id="workzo-page-top"></span>', unsafe_allow_html=True)
        script = """
        <script>
        const scrollTop = () => {
          try { window.parent.scrollTo(0,0); } catch(e) {}
          try { window.scrollTo(0,0); } catch(e) {}
          try {
            const doc = window.parent.document;
            const candidates = [
              doc.querySelector('section.main'),
              doc.querySelector('div[data-testid="stAppViewContainer"]'),
              doc.querySelector('.main'),
              doc.scrollingElement,
              doc.documentElement,
              doc.body
            ].filter(Boolean);
            candidates.forEach(el => { try { el.scrollTop = 0; } catch(e) {} });
          } catch(e) {}
        };
        scrollTop(); setTimeout(scrollTop, 80); setTimeout(scrollTop, 250);
        </script>
        """
        if hasattr(st, 'iframe'):
            st.iframe(srcdoc=script, height=1, width=1)
        else:
            st.markdown(script, unsafe_allow_html=True)
    except Exception:
        pass

def _wz32_remember_best_scores():
    try:
        for key in ['cv_score_value', 'ats_score_value', 'application_readiness_value', 'job_fit_score_value', 'interview_score']:
            cur = st.session_state.get(key)
            if cur is None or str(cur).strip() == '':
                continue
            try:
                cur_i = max(0, min(100, int(float(cur))))
            except Exception:
                continue
            best_key = '_best_' + key
            best_i = int(st.session_state.get(best_key) or 0)
            if cur_i > best_i:
                st.session_state[best_key] = cur_i
    except Exception:
        pass

def _wz32_restore_best_scores():
    try:
        for key in ['cv_score_value', 'ats_score_value', 'application_readiness_value', 'job_fit_score_value', 'interview_score']:
            best_key = '_best_' + key
            best = int(st.session_state.get(best_key) or 0)
            cur = st.session_state.get(key)
            try:
                cur_i = int(float(cur or 0))
            except Exception:
                cur_i = 0
            if best > 0 and cur_i <= 0:
                st.session_state[key] = best
            elif cur_i > best:
                st.session_state[best_key] = cur_i
    except Exception:
        pass

def _wz32_flow_step(label, done, current=False, note=''):
    # Keep this HTML on one line. Leading spaces/newlines can make Streamlit
    # render later cards as a code block instead of HTML.
    cls = 'done' if done else ('current' if current else '')
    icon = '✅' if done else ('➜' if current else '○')
    state = 'Complete' if done else ('Recommended now' if current else 'Pending')
    style = 'border-color:rgba(96,165,250,.55);background:rgba(37,99,235,.14);' if current and not done else ''
    return f"<div class='wz31-step {cls}' style='{style}'><div class='wz31-step-title'>{icon} {_wz31_escape(label)}</div><div class='wz31-step-sub'>{_wz31_escape(note or state)}</div></div>"

def _wz32_pick_current_step(cv_exists, resume_score, ats_score, job_exists, improved_ready, cover_ready):
    if not cv_exists:
        return 0
    if resume_score < 75 or ats_score < 75:
        return 1
    if not job_exists:
        return 2
    if not improved_ready:
        return 3
    if not cover_ready:
        return 4
    return 5

def _wz32_dashboard_home():
    _wz32_restore_best_scores()
    _wz32_force_scroll_top()
    _wz28_css()
    _wz31_css()
    st.markdown("""
    <style>
      .workzo-header{margin-bottom:14px!important;}
      .wz31-hero{margin-top:0!important;margin-bottom:18px!important;}
      .wz31-flow{grid-template-columns:repeat(auto-fit,minmax(185px,1fr));}
      .wz31-step{min-height:86px;}
      .wz32-explain{color:#94a3b8;font-size:.9rem;margin:-4px 0 14px;}
    </style>
    """, unsafe_allow_html=True)

    cv_exists = bool(str(st.session_state.get('cv_text','')).strip() or st.session_state.get('structured_cv_json'))
    job_text = str(st.session_state.get('current_job_description','') or st.session_state.get('last_understand_job_description','') or st.session_state.get('improve_cv_for_job_desc','') or st.session_state.get('job_description','')).strip()
    job_exists = bool(job_text)
    company = str(st.session_state.get('target_company') or st.session_state.get('prepare_target_company') or '').strip()
    country = str(st.session_state.get('country') or st.session_state.get('target_country') or 'Not set')
    language = str(st.session_state.get('preferred_language') or st.session_state.get('language') or 'English')

    resume_score = _wz31_get_score('cv_score_value', 'resume_score', 'resume_quality_score', '_best_cv_score_value', default=0)
    ats_score = _wz31_get_score('ats_score_value', 'ats_score', '_best_ats_score_value', default=0)
    if cv_exists and resume_score <= 0:
        resume_score = int(st.session_state.get('_best_cv_score_value') or 75)
    if cv_exists and ats_score <= 0:
        ats_score = int(st.session_state.get('_best_ats_score_value') or 70)
    interview_score = _wz31_get_score('interview_score', 'interview_readiness', '_best_interview_score', default=0)
    if interview_score <= 0:
        if cv_exists and job_exists and resume_score >= 75 and ats_score >= 75:
            interview_score = 65
        elif cv_exists:
            interview_score = 45
        else:
            interview_score = 0

    improved_ready = bool(str(st.session_state.get('improved_cv_text','') or st.session_state.get('latest_improved_cv','') or st.session_state.get('final_cv_text','')).strip())
    cover_ready = bool(str(st.session_state.get('latest_cover_letter','') or st.session_state.get('cover_letter_text','')).strip())
    next_action = _wz31_pick_next_action(cv_exists, job_exists, resume_score, ats_score, _wz31_get_score('job_fit_score_value','_best_job_fit_score_value', default=0), interview_score)

    st.markdown(f"""
    <div class='wz31-hero'>
      <div class='wz31-kicker'>WorkZo Command Center</div>
      <div class='wz31-title'>Your next best move is clear.</div>
      <div class='wz31-sub'>WorkZo recommends the next step based on your CV strength, ATS readiness, job context, and application progress.</div>
      <div class='wz31-chip-row'>
        <span class='wz31-chip'>{_wz31_escape(country)}</span>
        <span class='wz31-chip'>{_wz31_escape(language)}</span>
        <span class='wz31-chip'>{'CV ready' if cv_exists else 'CV missing'}</span>
        <span class='wz31-chip'>{'Job added' if job_exists else 'Job not added'}</span>
        <span class='wz31-chip'>{_wz31_escape(company or 'Company not added')}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class='wz31-next'>
      <div class='wz31-next-label'>Recommended next step</div>
      <div class='wz31-next-title'>{_wz31_escape(next_action['title'])}</div>
      <div class='wz31-next-copy'>{_wz31_escape(next_action['copy'])}</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button(next_action['button'], key='wz32_primary_next_action', use_container_width=True):
        if next_action['target'] == 'cv_documents' and job_exists:
            st.session_state['document_tools_mode'] = 'Improve CV for a Job'
        _wz28_go(next_action['target'])

    st.markdown('### Readiness overview')
    st.markdown("<div class='wz32-explain'>Job Fit is now shown inside Understand Job after a job description is analyzed.</div>", unsafe_allow_html=True)
    r1, r2, r3 = st.columns(3)
    with r1:
        _wz31_rate_card('Resume Score', resume_score, 'Clarity, structure, achievements, and overall CV quality.', missing=not cv_exists)
    with r2:
        _wz31_rate_card('ATS Score', ats_score, 'Scanner-friendly formatting, keywords, sections, and parsing safety.', missing=not cv_exists)
    with r3:
        _wz31_rate_card('Interview Readiness', interview_score, 'How ready you are to explain this CV and job fit clearly.', missing=not cv_exists)

    st.markdown('### Smart actions')
    a1, a2, a3, a4 = st.columns(4)
    with a1:
        _wz31_action_card('Improve CV', 'Use this when Resume or ATS score is below 75, or when you want to tailor for one job.', 'Open CV Tools', 'cv_documents', 'wz32_open_cv', {'document_tools_mode':'Improve CV for a Job' if job_exists else 'Improve / Update CV'})
    with a2:
        _wz31_action_card('Job Match', 'Find jobs or analyze a pasted job description when your CV and ATS scores are ready.', 'Open Job Match', 'job_assist', 'wz32_open_jobs')
    with a3:
        _wz31_action_card('Cover Letter', 'Use company, job description, and CV context to write a focused cover letter.', 'Create Cover Letter', 'cv_documents', 'wz32_open_cover', {'document_tools_mode':'Cover Letter Generator + Language'})
    with a4:
        _wz31_action_card('Work-O-Bot', 'Ask career questions or practice interview answers in your selected language.', 'Ask Work-O-Bot', 'workobot', 'wz32_open_bot')

    # Persist only safe progress flags. Do not store CV text or job descriptions.
    if cv_exists:
        st.session_state['_wz_has_cv'] = True
    if improved_ready:
        st.session_state['_wz_cv_improved'] = True
    if bool(st.session_state.get('latest_curated_jobs') or st.session_state.get('latest_job_query_expansion')):
        st.session_state['_wz_job_found'] = True
    if job_exists or st.session_state.get('latest_job_analysis'):
        st.session_state['_wz_job_analyzed'] = True
    prepared_ready = bool(cover_ready or str(st.session_state.get('latest_application_prep','') or st.session_state.get('latest_cover_letter','')).strip())
    if prepared_ready:
        st.session_state['_wz_prepared'] = True

    # Use restored memory after refresh, but never invent private CV/job text.
    cv_done = bool(cv_exists or st.session_state.get('_wz_has_cv'))
    improved_done = bool(improved_ready or st.session_state.get('_wz_cv_improved'))
    job_done = bool(job_exists or st.session_state.get('_wz_job_found') or st.session_state.get('_wz_job_analyzed'))
    prep_done = bool(prepared_ready or st.session_state.get('_wz_prepared'))

    st.markdown('### Application progress')
    st.caption('Move step by step. Each card is checked only after that action is actually done.')

    # Current recommendation: the first unfinished step becomes highlighted.
    if not cv_done:
        current_key = 'cv'
    elif resume_score < 75 or ats_score < 75 or not improved_done:
        current_key = 'improve'
    elif not job_done:
        current_key = 'job'
    elif not prep_done:
        current_key = 'prepare'
    else:
        current_key = 'done'

    progress_items = [
        ('cv', '1. CV uploaded', cv_done, 'CV added' if cv_done else 'Upload or create your CV', 'Edit onboarding', 'onboarding', {}),
        ('improve', '2. CV improved', improved_done, 'Improved / tailored' if improved_done else 'Improve Resume + ATS score', 'Improve CV', 'cv_documents', {'document_tools_mode':'Improve / Update CV'}),
        ('job', '3. Job matched', job_done, 'Job found or analyzed' if job_done else 'Find jobs or analyze one JD', 'Job Match', 'job_assist', {'job_assist_mode_key':'find'}),
        ('prepare', '4. Prepared for job', prep_done, 'Cover letter / prep done' if prep_done else 'Prepare cover letter and interview notes', 'Prepare', 'job_assist', {'job_assist_mode_key':'prepare'}),
    ]

    cols = st.columns(4)
    for idx, (step_key, label, done, note, button_label, target, extra_state) in enumerate(progress_items):
        with cols[idx]:
            st.markdown(_wz32_flow_step(label, done, current_key == step_key, note), unsafe_allow_html=True)
    try:
        readiness = int(round((sum([cv_done, improved_done, job_done, prep_done]) / 4) * 100))
        st.session_state['application_readiness_value'] = max(int(st.session_state.get('application_readiness_value') or 0), readiness)
    except Exception:
        pass

    st.caption('Scores are guidance only. WorkZo should not invent skills, company facts, language level, salary, or experience.')
    _wz32_remember_best_scores()
    try:
        if callable(globals().get('workzo_save_light_memory')):
            workzo_save_light_memory()
    except Exception:
        pass

# Replace dashboard home with v32 smart version.
_wz28_dashboard_home = _wz32_dashboard_home

# Put Job Fit where it belongs: inside Understand Job analysis.
try:
    _wz32_old_render_understand_job_analysis = render_understand_job_analysis
    def render_understand_job_analysis(data):
        try:
            score = 0
            if isinstance(data, dict):
                score = _wz31_clamp_score(data.get('fit_score') or data.get('job_fit') or data.get('match_score') or 0)
                if score:
                    st.session_state['job_fit_score_value'] = score
                    _wz32_remember_best_scores()
            if score:
                st.markdown('### Job Fit')
                _wz31_rate_card('Job Fit', score, 'Fit for this specific pasted job description. Use this only after reviewing the requirement checklist.', missing=False)
        except Exception:
            pass
        return _wz32_old_render_understand_job_analysis(data)
except Exception:
    pass

# Keep scores alive when returning home or switching pages.
try:
    _wz32_old_show_dashboard = show_dashboard
    def show_dashboard():
        _wz32_restore_best_scores()
        try:
            _wz32_force_scroll_top()
        except Exception:
            pass
        result = _wz32_old_show_dashboard()
        _wz32_remember_best_scores()
        _wz32_restore_best_scores()
        return result
except Exception:
    pass


# =========================================================
# WorkZo v35 - stable startup command center
# Fixes: clean application progress, smaller header gap, score memory,
# edit setup routing, language sync, and old Job Assist layout routing.
# =========================================================
import json as _wz35_json
import os as _wz35_os
import time as _wz35_time
import html as _wz35_html


def _wz35_escape(value):
    try:
        return _wz35_html.escape(str(value or ""))
    except Exception:
        return str(value or "")


def _wz35_qp_get(key, default=""):
    try:
        v = st.query_params.get(key, default)
        if isinstance(v, list):
            return v[0] if v else default
        return v or default
    except Exception:
        return default


def _wz35_get_uid():
    """Persistent-enough anonymous browser id using URL query params.
    This is used only for non-sensitive UI state such as scores/language.
    """
    try:
        uid = _wz35_qp_get("wz_uid", "") or st.session_state.get("anonymous_user_id", "")
        if not uid:
            import uuid as _uuid
            uid = str(_uuid.uuid4())
        st.session_state["anonymous_user_id"] = uid
        try:
            if not _wz35_qp_get("wz_uid", ""):
                st.query_params["wz_uid"] = uid
        except Exception:
            pass
        return uid
    except Exception:
        return "local"


def _wz35_state_file():
    try:
        base = globals().get("BASE_DIR") or _wz35_os.getcwd()
        safe_uid = "".join(ch for ch in str(_wz35_get_uid()) if ch.isalnum() or ch in "-_")[:80]
        return _wz35_os.path.join(base, f"workzo_ui_state_{safe_uid}.json")
    except Exception:
        return "workzo_ui_state_local.json"


def _wz35_save_state():
    """Save non-sensitive state only. Do not store full CV text or documents."""
    try:
        keys = [
            "cv_score_value", "ats_score_value", "application_readiness_value",
            "job_fit_score_value", "interview_score", "country", "preferred_language",
            "ui_language", "response_language", "language", "target_company_website",
            "target_company", "prepare_target_company", "nav_page", "page",
            "last_understand_job_description", "current_job_description", "job_description",
            "improved_cv_text", "latest_improved_cv", "latest_cover_letter", "latest_application_prep",
            "_workzo_has_cv", "_best_cv_score_value", "_best_ats_score_value", "_best_application_readiness_value",
        ]
        data = {}
        for k in keys:
            v = st.session_state.get(k)
            if isinstance(v, (str, int, float, bool)) or v is None:
                # keep job description short enough for context, not full private docs
                if k in ["last_understand_job_description", "current_job_description", "job_description"] and isinstance(v, str):
                    v = v[:5000]
                data[k] = v
        cv_present = bool(str(st.session_state.get("cv_text", "")).strip() or st.session_state.get("structured_cv_json"))
        data["_workzo_has_cv"] = bool(cv_present or st.session_state.get("_workzo_has_cv"))
        with open(_wz35_state_file(), "w", encoding="utf-8") as f:
            _wz35_json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _wz35_load_state():
    try:
        path = _wz35_state_file()
        if not _wz35_os.path.exists(path):
            return
        with open(path, "r", encoding="utf-8") as f:
            data = _wz35_json.load(f)
        if not isinstance(data, dict):
            return
        for k, v in data.items():
            if k not in st.session_state or st.session_state.get(k) in [None, "", 0]:
                st.session_state[k] = v
        # restore best scores into active score keys when missing
        for key in ["cv_score_value", "ats_score_value", "application_readiness_value"]:
            best = int(st.session_state.get("_best_" + key) or 0)
            cur = int(st.session_state.get(key) or 0)
            if best > cur:
                st.session_state[key] = best
    except Exception:
        pass


def _wz35_remember_scores():
    try:
        for key in ["cv_score_value", "ats_score_value", "application_readiness_value", "job_fit_score_value", "interview_score"]:
            try:
                cur = int(float(st.session_state.get(key) or 0))
            except Exception:
                cur = 0
            if cur > 0:
                best_key = "_best_" + key
                st.session_state[best_key] = max(cur, int(st.session_state.get(best_key) or 0))
    except Exception:
        pass


def _wz35_force_scroll_top():
    try:
        st.markdown('<span id="workzo-page-top"></span>', unsafe_allow_html=True)
        script = """
        <script>
        const wzScrollTop = () => {
          try { window.scrollTo(0,0); } catch(e) {}
          try { window.parent.scrollTo(0,0); } catch(e) {}
          try {
            const d = window.parent.document;
            [d.scrollingElement, d.documentElement, d.body,
             d.querySelector('section.main'),
             d.querySelector('div[data-testid="stAppViewContainer"]'),
             d.querySelector('.main')].filter(Boolean).forEach(el => { try { el.scrollTop = 0; } catch(e) {} });
          } catch(e) {}
        };
        wzScrollTop(); setTimeout(wzScrollTop, 50); setTimeout(wzScrollTop, 250); setTimeout(wzScrollTop, 700);
        </script>
        """
        if hasattr(st, "iframe"):
            st.iframe(srcdoc=script, height=1, width=1)
        else:
            st.markdown(script, unsafe_allow_html=True)
    except Exception:
        pass


def _wz35_sync_language(value=None):
    try:
        lang = value or st.session_state.get("preferred_language") or st.session_state.get("language") or "English"
        st.session_state["preferred_language"] = lang
        st.session_state["language"] = lang
        st.session_state["response_language"] = lang
        try:
            st.session_state["ui_language"] = lang if "UI_TEXT" in globals() and lang in UI_TEXT else "English"
        except Exception:
            st.session_state["ui_language"] = lang
        if callable(globals().get("set_single_preferred_language")):
            try:
                set_single_preferred_language(lang)
            except Exception:
                pass
    except Exception:
        pass


def _wz35_go(page, extra=None):
    try:
        if isinstance(extra, dict):
            for k, v in extra.items():
                st.session_state[k] = v
        st.session_state["page"] = page
        st.session_state["nav_page"] = page
        try:
            st.query_params["page"] = page
            st.query_params["wz_top"] = str(int(_wz35_time.time() * 1000))
        except Exception:
            pass
        try:
            request_scroll_to_top()
        except Exception:
            pass
        _wz35_save_state()
        st.rerun()
    except Exception:
        pass


def _wz35_score(*keys, default=0):
    for key in keys:
        try:
            value = st.session_state.get(key)
            if value not in [None, ""]:
                n = int(float(value))
                if n > 0:
                    return max(0, min(100, n))
        except Exception:
            pass
    return default


def _wz35_css():
    try:
        st.markdown("""
        <style>
        .block-container{padding-top:.55rem!important;max-width:1220px!important;}
        .workzo-header{margin-top:4px!important;margin-bottom:12px!important;}
        .wz35-hero{border:1px solid rgba(20,184,166,.28);border-radius:24px;padding:20px 24px;background:linear-gradient(135deg,rgba(20,184,166,.16),rgba(37,99,235,.14));box-shadow:0 12px 35px rgba(2,6,23,.22);margin:10px 0 18px;}
        .wz35-kicker{color:#93c5fd;text-transform:uppercase;letter-spacing:.08em;font-weight:850;font-size:.78rem;margin-bottom:7px;}
        .wz35-title{color:#fff;font-weight:900;font-size:1.75rem;line-height:1.18;margin-bottom:7px;}
        .wz35-sub{color:#dbeafe;font-size:.98rem;line-height:1.45;}
        .wz35-chip-row{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px;}
        .wz35-chip{border:1px solid rgba(96,165,250,.26);background:rgba(37,99,235,.16);color:#dbeafe;border-radius:999px;padding:6px 11px;font-weight:700;font-size:.84rem;}
        .wz35-next{border:1px solid rgba(45,212,191,.34);background:linear-gradient(135deg,rgba(20,184,166,.18),rgba(15,23,42,.58));border-radius:20px;padding:17px 18px;margin:12px 0 18px;}
        .wz35-next-label{color:#99f6e4;font-size:.78rem;text-transform:uppercase;letter-spacing:.07em;font-weight:850;margin-bottom:4px;}
        .wz35-next-title{font-size:1.25rem;color:#fff;font-weight:900;margin-bottom:5px;}
        .wz35-next-copy{color:#cbd5e1;font-size:.96rem;line-height:1.45;}
        .wz35-rate{border:1px solid rgba(148,163,184,.17);background:linear-gradient(180deg,rgba(30,41,59,.78),rgba(15,23,42,.72));border-radius:20px;padding:18px;min-height:160px;}
        .wz35-rate-title{color:#fff;font-weight:900;font-size:1rem;display:flex;justify-content:space-between;gap:8px;}
        .wz35-rate-value{color:#fff;font-size:2rem;font-weight:900;margin:12px 0 8px;}
        .wz35-bar{height:10px;border-radius:999px;background:rgba(148,163,184,.20);overflow:hidden;margin:6px 0 12px;}
        .wz35-fill{height:100%;border-radius:999px;background:linear-gradient(90deg,#38bdf8,#2dd4bf);}
        .wz35-rate-copy{color:#bfdbfe;font-size:.9rem;line-height:1.4;}
        .wz35-action{border:1px solid rgba(148,163,184,.16);background:rgba(15,23,42,.52);border-radius:20px;padding:18px;min-height:150px;}
        .wz35-action-title{color:#fff;font-weight:900;font-size:1.06rem;margin-bottom:8px;}
        .wz35-action-copy{color:#bfdbfe;font-size:.93rem;line-height:1.45;min-height:62px;}
        .wz35-flow-card{border:1px solid rgba(148,163,184,.17);background:rgba(15,23,42,.50);border-radius:18px;padding:16px 18px;min-height:108px;}
        .wz35-flow-card.done{border-color:rgba(45,212,191,.45);background:rgba(20,184,166,.13);}
        .wz35-flow-card.current{border-color:rgba(96,165,250,.58);background:rgba(37,99,235,.14);}
        .wz35-flow-title{font-weight:900;color:#fff;font-size:.96rem;line-height:1.35;}
        .wz35-flow-note{color:#bfdbfe;font-size:.84rem;margin-top:8px;line-height:1.35;}
        </style>
        """, unsafe_allow_html=True)
    except Exception:
        pass


def _wz35_rate_card(title, score, copy, missing=False):
    if missing or not score:
        value = "—"
        width = 0
    else:
        value = f"{int(score)}%"
        width = max(0, min(100, int(score)))
    st.markdown(f"""
    <div class='wz35-rate'>
      <div class='wz35-rate-title'><span>{_wz35_escape(title)}</span></div>
      <div class='wz35-rate-value'>{_wz35_escape(value)}</div>
      <div class='wz35-bar'><div class='wz35-fill' style='width:{width}%;'></div></div>
      <div class='wz35-rate-copy'>{_wz35_escape(copy)}</div>
    </div>
    """, unsafe_allow_html=True)


def _wz35_action_card(title, copy, button, target, key, extra=None):
    st.markdown(f"""
    <div class='wz35-action'>
      <div class='wz35-action-title'>{_wz35_escape(title)}</div>
      <div class='wz35-action-copy'>{_wz35_escape(copy)}</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button(button, key=key, use_container_width=True):
        _wz35_go(target, extra)


def _wz35_flow_card(label, done, current, note):
    cls = "done" if done else ("current" if current else "")
    icon = "✅" if done else ("➜" if current else "○")
    st.markdown(f"""
    <div class='wz35-flow-card {cls}'>
      <div class='wz35-flow-title'>{icon} {_wz35_escape(label)}</div>
      <div class='wz35-flow-note'>{_wz35_escape(note)}</div>
    </div>
    """, unsafe_allow_html=True)


def _wz35_next_action(cv_exists, resume_score, ats_score, job_exists, improved_ready, prepared_ready):
    if not cv_exists:
        return {"title":"Start with your CV", "copy":"Upload or create your CV first so WorkZo can score it and guide the next steps.", "button":"Add CV", "target":"onboarding", "extra":{}}
    if resume_score < 75 or ats_score < 75:
        return {"title":"Improve your CV first", "copy":"Your Resume or ATS score needs improvement. Fix structure, keywords, and role alignment before applying widely.", "button":"Open CV Tools", "target":"cv_documents", "extra":{"document_tools_mode":"Improve / Update CV"}}
    if not job_exists:
        return {"title":"Find or analyze a job next", "copy":"Your CV is ready enough. Now find matching roles or paste one job description for a fit check.", "button":"Open Job Assist", "target":"job_assist", "extra":{"job_assist_mode_key":"find"}}
    if not improved_ready:
        return {"title":"Tailor your CV for this job", "copy":"You have job context. Now tailor the CV to this specific role before creating application materials.", "button":"Improve CV for Job", "target":"cv_documents", "extra":{"document_tools_mode":"Improve CV for a Job"}}
    if not prepared_ready:
        return {"title":"Prepare the application", "copy":"Create a focused cover letter and preparation notes using the company, CV, and job description.", "button":"Prepare Application", "target":"job_assist", "extra":{"job_assist_mode_key":"prepare"}}
    return {"title":"Ready to apply", "copy":"Your core application flow is complete. Apply, save the tracker item, and practice answers in Work-O-Bot.", "button":"Practice with Work-O-Bot", "target":"workobot", "extra":{}}


def _wz35_sidebar(page_key):
    with st.sidebar:
        try:
            logo_src = image_to_data_uri(ICON_PATH) or image_to_data_uri(LOGO_PATH)
        except Exception:
            logo_src = None
        if logo_src:
            st.markdown(f"""
            <div class='workzo-sidebar-brand-wrap'>
              <img src='{logo_src}' class='workzo-sidebar-logo' alt='WorkZo AI logo'>
              <div><div class='workzo-sidebar-brand'>WORKZO AI</div><div class='workzo-sidebar-version'>Beta · guided workspace</div></div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("### WorkZo AI")
        navs = [("dashboard", txt("dashboard")), ("cv_documents", txt("cv_documents")), ("job_assist", txt("job_assist")), ("workobot", "Work-O-Bot")]
        for key, label in navs:
            text = label + ("  ✓" if page_key == key else "")
            if st.button(text, key=f"wz35_nav_{key}", use_container_width=True):
                _wz35_go(key)
        st.markdown(f"<div class='workzo-sidebar-section-label'>{html.escape(txt('company_context'))}</div>", unsafe_allow_html=True)
        with st.expander("🏢 " + txt("company_website"), expanded=False):
            company_url = st.text_input(txt("company_website"), key="target_company_website", placeholder="https://company.com")
            if company_url:
                st.caption(ui_label("Used for cover letters and job/interview preparation context."))
        st.markdown(f"<div class='workzo-sidebar-section-label'>{html.escape(txt('language'))}</div>", unsafe_allow_html=True)
        try:
            langs = language_options if "language_options" in globals() and language_options else ["English", "German", "Dutch", "French", "Spanish", "Portuguese"]
        except Exception:
            langs = ["English", "German", "Dutch", "French", "Spanish", "Portuguese"]
        cur = st.session_state.get("preferred_language") or st.session_state.get("language") or "English"
        if cur not in langs:
            cur = "English" if "English" in langs else langs[0]
        def _wz39_language_changed():
            _new_lang = st.session_state.get("wz39_preferred_language", cur)
            try:
                if callable(globals().get("workzo_set_language_everywhere")):
                    workzo_set_language_everywhere(_new_lang)
                else:
                    set_single_preferred_language(_new_lang)
                st.query_params["wz_lang"] = _new_lang
            except Exception:
                pass
        if st.session_state.get("wz39_preferred_language") != cur:
            st.session_state["wz39_preferred_language"] = cur
        chosen = st.selectbox(txt("preferred_language"), langs, index=langs.index(cur), key="wz39_preferred_language", on_change=_wz39_language_changed)
        _wz35_sync_language(chosen)
        st.markdown("---")
        if st.button(txt("edit_setup"), key="wz35_edit_setup", use_container_width=True):
            st.session_state["onboarding_complete"] = False
            st.session_state["page"] = "onboarding"
            st.session_state["nav_page"] = "onboarding"
            try:
                st.query_params["page"] = "onboarding"
            except Exception:
                pass
            _wz35_save_state()
            st.rerun()


def _wz35_dashboard_home():
    _wz35_load_state()
    _wz35_remember_scores()
    _wz35_force_scroll_top()
    _wz35_css()

    cv_exists = bool(str(st.session_state.get("cv_text", "")).strip() or st.session_state.get("structured_cv_json") or st.session_state.get("_workzo_has_cv"))
    if cv_exists:
        st.session_state["_workzo_has_cv"] = True
    job_text = str(st.session_state.get("current_job_description", "") or st.session_state.get("last_understand_job_description", "") or st.session_state.get("improve_cv_for_job_desc", "") or st.session_state.get("job_description", "")).strip()
    job_exists = bool(job_text)
    improved_ready = bool(str(st.session_state.get("improved_cv_text", "") or st.session_state.get("latest_improved_cv", "") or st.session_state.get("final_cv_text", "")).strip())
    prepared_ready = bool(str(st.session_state.get("latest_application_prep", "") or st.session_state.get("latest_cover_letter", "") or st.session_state.get("cover_letter_text", "")).strip())
    resume_score = _wz35_score("cv_score_value", "resume_score", "resume_quality_score", "_best_cv_score_value", default=76 if cv_exists else 0)
    ats_score = _wz35_score("ats_score_value", "ats_score", "_best_ats_score_value", default=70 if cv_exists else 0)
    interview_score = _wz35_score("interview_score", "interview_readiness", "_best_interview_score", default=65 if cv_exists and job_exists and resume_score >= 75 and ats_score >= 75 else (40 if cv_exists else 0))

    country = st.session_state.get("country") or st.session_state.get("target_country") or "Not set"
    language = st.session_state.get("preferred_language") or st.session_state.get("language") or "English"
    company = st.session_state.get("prepare_target_company") or st.session_state.get("target_company") or st.session_state.get("target_company_website") or ui_label("Company not added")
    next_action = _wz35_next_action(cv_exists, resume_score, ats_score, job_exists, improved_ready, prepared_ready)

    st.markdown(f"""
    <div class='wz35-hero'>
      <div class='wz35-kicker'>{_wz35_escape(txt('workzo_command_center'))}</div>
      <div class='wz35-title'>{_wz35_escape(txt('next_best_move_clear'))}</div>
      <div class='wz35-sub'>{_wz35_escape(txt('next_best_move_copy'))}</div>
      <div class='wz35-chip-row'>
        <span class='wz35-chip'>{_wz35_escape(country)}</span>
        <span class='wz35-chip'>{_wz35_escape(language)}</span>
        <span class='wz35-chip'>{_wz35_escape(ui_label('CV ready') if cv_exists else ui_label('CV missing'))}</span>
        <span class='wz35-chip'>{_wz35_escape(ui_label('Job added') if job_exists else ui_label('Job not added'))}</span>
        <span class='wz35-chip'>{_wz35_escape(company)}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class='wz35-next'>
      <div class='wz35-next-label'>{_wz35_escape(txt('recommended_next_step'))}</div>
      <div class='wz35-next-title'>{_wz35_escape(next_action['title'])}</div>
      <div class='wz35-next-copy'>{_wz35_escape(next_action['copy'])}</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button(next_action["button"], key="wz35_primary_action", use_container_width=True):
        _wz35_go(next_action["target"], next_action.get("extra"))

    st.markdown("### " + txt("readiness_overview"))
    c1, c2, c3 = st.columns(3)
    with c1:
        _wz35_rate_card(txt("resume_score"), resume_score, ui_label("Clarity, structure, achievements, and overall CV quality."), missing=not cv_exists)
    with c2:
        _wz35_rate_card(txt("ats_score"), ats_score, ui_label("Scanner-friendly formatting, role keywords, sections, and parsing safety."), missing=not cv_exists)
    with c3:
        _wz35_rate_card(txt("interview_readiness"), interview_score, ui_label("How ready you are to explain your CV and job fit clearly."), missing=not cv_exists)

    st.markdown("### " + txt("smart_actions"))
    a1, a2, a3, a4 = st.columns(4)
    with a1:
        _wz35_action_card(txt("improve_cv"), ui_label("Use this when Resume or ATS score is below 75, or when tailoring for one job."), txt("open_cv_tools"), "cv_documents", "wz35_action_cv", {"document_tools_mode":"Improve CV for a Job" if job_exists else "Improve / Update CV"})
    with a2:
        _wz35_action_card(txt("job_match"), ui_label("Search jobs for the selected country, then analyze one job description for fit."), txt("open_job_assist"), "job_assist", "wz35_action_jobs", {"job_assist_mode_key":"find"})
    with a3:
        _wz35_action_card(txt("cover_letter"), ui_label("Use CV, job description, and company context to create a focused cover letter."), txt("create_cover_letter"), "cv_documents", "wz35_action_cover", {"document_tools_mode":"Cover Letter Generator + Language"})
    with a4:
        _wz35_action_card("Work-O-Bot", ui_label("Ask career questions or practice interview answers in your selected language."), txt("ask_workobot"), "workobot", "wz35_action_bot")

    st.markdown("### " + txt("application_progress"))
    st.caption(ui_label("Move step by step, or jump to the part you want to work on."))
    score_checked = bool(cv_exists and resume_score > 0 and ats_score > 0)
    if not cv_exists:
        current = 0
    elif not score_checked or resume_score < 75 or ats_score < 75:
        current = 1
    elif not job_exists:
        current = 2
    elif not improved_ready:
        current = 3
    elif not prepared_ready:
        current = 4
    else:
        current = 5
    flow = [
        ("1. " + txt("cv_added"), cv_exists, txt("completed") if cv_exists else ui_label("Upload or create CV"), txt("edit_setup"), "cv_documents", {"document_tools_mode":"Improve / Update CV"}),
        ("2. " + txt("resume_ats_checked"), score_checked and resume_score >= 75 and ats_score >= 75, ui_label("Good") if score_checked and resume_score >= 75 and ats_score >= 75 else ui_label("Improve scores above 75"), txt("improve_cv"), "cv_documents", {"document_tools_mode":"Improve / Update CV"}),
        ("3. " + txt("job_analyzed"), job_exists, txt("completed") if job_exists else ui_label("Paste/analyze one job"), txt("understand_job"), "job_assist", {"job_assist_mode_key":"understand"}),
        ("4. " + txt("cv_improved"), improved_ready, txt("completed") if improved_ready else ui_label("Tailor CV to the job"), txt("improve_cv"), "cv_documents", {"document_tools_mode":"Improve CV for a Job" if job_exists else "Improve / Update CV"}),
        ("5. " + txt("prepared_to_apply"), prepared_ready, txt("completed") if prepared_ready else ui_label("Prepare application"), txt("prepare_this_job"), "job_assist", {"job_assist_mode_key":"prepare"}),
    ]
    cols = st.columns(5)
    for i, (label, done, note, button, target, extra) in enumerate(flow):
        with cols[i]:
            _wz35_flow_card(label, done, current == i, note)
    st.caption(ui_label("Scores are guidance only. WorkZo should not invent skills, company facts, language level, salary, or experience."))
    _wz35_remember_scores()
    _wz35_save_state()


# Final clean router. This avoids older dashboard wrappers that printed raw HTML.
def show_dashboard():
    _wz35_load_state()
    _wz35_sync_language()
    _wz35_force_scroll_top()
    page_key = st.session_state.get("nav_page") or st.session_state.get("page") or "dashboard"
    page_key = {"landing":"dashboard", "bot":"workobot", "interview":"workobot", "jobs":"job_assist", "improve_cv":"cv_documents"}.get(page_key, page_key)
    if page_key == "interview_practice":
        page_key = "workobot"
    if page_key not in {"dashboard", "cv_documents", "job_assist", "workobot"}:
        page_key = "dashboard"
    st.session_state["page"] = page_key
    st.session_state["nav_page"] = page_key
    try:
        _wz28_top(True)
    except Exception:
        pass
    _wz35_sidebar(page_key)
    if page_key == "dashboard":
        _wz35_dashboard_home()
    elif page_key == "cv_documents":
        _wz35_css()
        show_document_tools()
    elif page_key == "job_assist":
        _wz35_css()
        # Use the older Job Assist page layout if available.
        try:
            _wz28_job_assist_page()
        except Exception:
            st.subheader(txt("job_assist"))
            tab1, tab2, tab3 = st.tabs([txt("find_jobs"), txt("understand_job"), txt("prepare_this_job")])
            with tab1:
                st.info("Job search module could not be loaded.")
            with tab2:
                st.info("Understand Job module could not be loaded.")
            with tab3:
                st.info("Prepare module could not be loaded.")
    elif page_key == "workobot":
        _wz35_css()
        show_workobot()
    _wz35_remember_scores()
    _wz35_save_state()

# =========================================================
# WorkZo v36 LANGUAGE SYNC + SMART CONTEXT PATCH
# Dashboard language dropdown now updates the whole app consistently.
# Smart stage flags allow features to adapt based on CV/ATS/job situation.
# =========================================================
def _wz36_sync_language_from_widgets():
    """Sync language from the newest visible selector. Sidebar wins over old onboarding keys."""
    try:
        candidate_keys = [
            "wz39_preferred_language", "sidebar_preferred_language", "wz35_preferred_language", "wz24_sidebar_preferred_language",
            "wz25_sidebar_preferred_language", "wz21_sidebar_preferred_language", "wz19_sidebar_preferred_language",
            "onboarding_preferred_language",
        ]
        current = st.session_state.get("preferred_language") or st.session_state.get("language") or "English"
        chosen = current
        for k in candidate_keys:
            val = st.session_state.get(k)
            if isinstance(val, str) and val.strip():
                chosen = val.strip()
                break
        if callable(globals().get("workzo_set_language_everywhere")):
            workzo_set_language_everywhere(chosen)
        else:
            set_single_preferred_language(chosen)
        return chosen != current
    except Exception:
        return False


def _wz36_smart_context_flags():
    try:
        cv_exists = bool(str(st.session_state.get("cv_text", "")).strip() or st.session_state.get("structured_cv_json"))
        jd_exists = bool(str(st.session_state.get("current_job_description", "") or st.session_state.get("last_understand_job_description", "") or st.session_state.get("job_description", "")).strip())
        resume_score = int(st.session_state.get("cv_score_value") or st.session_state.get("resume_score") or 0)
        ats_score = int(st.session_state.get("ats_score_value") or st.session_state.get("ats_score") or 0)
        if not cv_exists:
            stage = "need_cv"
        elif resume_score and ats_score and (resume_score < 75 or ats_score < 75):
            stage = "improve_cv"
        elif not jd_exists:
            stage = "find_or_analyze_job"
        else:
            stage = "prepare_application"
        st.session_state["workzo_smart_stage"] = stage
        st.session_state["workzo_context_is_ready"] = bool(cv_exists and resume_score >= 75 and ats_score >= 75)
    except Exception:
        pass

try:
    _wz36_previous_show_dashboard = show_dashboard
    def show_dashboard():
        lang_changed = _wz36_sync_language_from_widgets()
        _wz36_smart_context_flags()
        if lang_changed:
            try:
                st.query_params["wz_lang"] = st.session_state.get("preferred_language", "English")
            except Exception:
                pass
        return _wz36_previous_show_dashboard()
except Exception:
    pass


# =========================================================
# WorkZo v38 final language + Work-O-Bot safety patch
# =========================================================
def _wz38_sync_language_now():
    try:
        # Prefer active sidebar/dashboard selector; onboarding key is only fallback.
        for _k in ["wz39_preferred_language", "sidebar_preferred_language", "wz35_preferred_language", "wz24_sidebar_preferred_language", "onboarding_preferred_language"]:
            _val = st.session_state.get(_k)
            if isinstance(_val, str) and _val.strip():
                if callable(globals().get("workzo_set_language_everywhere")):
                    workzo_set_language_everywhere(_val.strip())
                else:
                    set_single_preferred_language(_val.strip())
                return _val.strip()
        _lang = st.session_state.get("preferred_language") or st.session_state.get("language") or "English"
        if callable(globals().get("workzo_set_language_everywhere")):
            workzo_set_language_everywhere(_lang)
        else:
            set_single_preferred_language(_lang)
        return _lang
    except Exception:
        return "English"

try:
    _wz38_previous_show_dashboard = show_dashboard
    def show_dashboard():
        _before = st.session_state.get("preferred_language") or st.session_state.get("language") or "English"
        _after = _wz38_sync_language_now()
        # If user changed language through a sidebar selector, rerun once so all labels refresh.
        if _after != _before and not st.session_state.get("_wz38_language_rerun_done"):
            st.session_state["_wz38_language_rerun_done"] = True
            st.rerun()
        st.session_state["_wz38_language_rerun_done"] = False
        return _wz38_previous_show_dashboard()
except Exception:
    pass


# =========================================================
# WorkZo v40 - translate final dashboard literals used by smart cards
# =========================================================
def _wz35_next_action(cv_exists, resume_score, ats_score, job_exists, improved_ready, prepared_ready):
    if not cv_exists:
        return {"title":ui_label("Start with your CV"), "copy":ui_label("Upload or create your CV first so WorkZo can score it and guide the next steps."), "button":ui_label("Add CV"), "target":"onboarding", "extra":{}}
    if resume_score < 75 or ats_score < 75:
        return {"title":ui_label("Improve your CV first"), "copy":ui_label("Your Resume or ATS score needs improvement. Fix structure, keywords, and role alignment before applying widely."), "button":txt("open_cv_tools"), "target":"cv_documents", "extra":{"document_tools_mode":"Improve / Update CV"}}
    if not job_exists:
        return {"title":ui_label("Find or analyze a job next"), "copy":ui_label("Your CV is ready enough. Now find matching roles or paste one job description for a fit check."), "button":txt("open_job_assist"), "target":"job_assist", "extra":{"job_assist_mode_key":"find"}}
    if not improved_ready:
        return {"title":ui_label("Tailor your CV for this job"), "copy":ui_label("You have job context. Now tailor the CV to this specific role before creating application materials."), "button":ui_label("Improve CV for Job"), "target":"cv_documents", "extra":{"document_tools_mode":"Improve CV for a Job"}}
    if not prepared_ready:
        return {"title":ui_label("Prepare the application"), "copy":ui_label("Create a focused cover letter and preparation notes using the company, CV, and job description."), "button":txt("prepare_this_job"), "target":"job_assist", "extra":{"job_assist_mode_key":"prepare"}}
    return {"title":ui_label("Ready to apply"), "copy":ui_label("Your core application flow is complete. Apply, save the tracker item, and practice answers in Work-O-Bot."), "button":txt("ask_workobot"), "target":"workobot", "extra":{}}

# Make score guidance translatable wherever the final dashboard uses it.
try:
    if "UI_TEXT" in globals():
        UI_TEXT.setdefault("German", {}).update({
            "readiness_overview": "Bereitschaftsübersicht",
            "smart_actions": "Smarte Aktionen",
            "open_cv_tools": "CV-Tools öffnen",
            "open_job_assist": "Job Assist öffnen",
            "create_cover_letter": "Cover Letter erstellen",
            "ask_workobot": "Work-O-Bot fragen",
        })
        UI_TEXT.setdefault("French", {}).update({
            "readiness_overview": "Vue d’ensemble de la préparation",
            "smart_actions": "Actions intelligentes",
            "open_cv_tools": "Ouvrir les outils CV",
            "open_job_assist": "Ouvrir l’assistant emploi",
            "create_cover_letter": "Créer une lettre de motivation",
            "ask_workobot": "Demander à Work-O-Bot",
        })
except Exception:
    pass


# =========================================================
# WorkZo v41 - final dashboard language sync
# =========================================================
def _wz41_sync_language_from_any_widget():
    try:
        for _k in ["wz39_preferred_language", "sidebar_preferred_language", "wz35_preferred_language", "wz40_mobile_preferred_language", "wz30_language", "wz29_language", "wz28_language", "wz27_language", "onboarding_preferred_language", "preferred_language", "language"]:
            _v = st.session_state.get(_k)
            if isinstance(_v, str) and _v.strip():
                if callable(globals().get("workzo_set_language_everywhere")):
                    return workzo_set_language_everywhere(_v.strip())
                st.session_state["preferred_language"] = _v.strip()
                st.session_state["language"] = _v.strip()
                st.session_state["ui_language"] = _v.strip()
                st.session_state["response_language"] = _v.strip()
                return _v.strip()
    except Exception:
        pass
    return st.session_state.get("preferred_language", "English")

try:
    _wz41_previous_show_dashboard = show_dashboard
    def show_dashboard():
        _wz41_sync_language_from_any_widget()
        return _wz41_previous_show_dashboard()
except Exception:
    pass

# =========================================================

# =========================================================

# =========================================================
# WorkZo v45 - mobile top navigation, desktop left sidebar
# Desktop users keep the native left toolbox. Mobile users get a top nav so
# content is not squeezed by the Streamlit sidebar.
# =========================================================
def _wz45_render_mobile_top_nav():
    try:
        import time as _time
        import html as _html
        lang = str(st.session_state.get("preferred_language", "English") or "English")
        labels = {
            "English": {"tools": "Tools / Navigation", "dashboard": "Dashboard", "cv": "CV Documents", "jobs": "Job Assist", "bot": "Work-O-Bot"},
            "German": {"tools": "Tools / Navigation", "dashboard": "Dashboard", "cv": "Lebenslauf & Dokumente", "jobs": "Job-Assistent", "bot": "Work-O-Bot"},
            "French": {"tools": "Outils / navigation", "dashboard": "Tableau de bord", "cv": "CV & documents", "jobs": "Assistant emploi", "bot": "Work-O-Bot"},
            "Dutch": {"tools": "Tools / navigatie", "dashboard": "Dashboard", "cv": "CV & documenten", "jobs": "Jobassistent", "bot": "Work-O-Bot"},
            "Spanish": {"tools": "Herramientas / navegación", "dashboard": "Panel", "cv": "CV y documentos", "jobs": "Asistente de empleo", "bot": "Work-O-Bot"},
        }
        t = labels.get(lang, labels["English"])
        nonce = str(int(_time.time() * 1000))
        def link(page, text):
            return f"<a class='wz45-mobile-link' href='?page={page}&wz_top={nonce}'>{_html.escape(text)}</a>"
        st.markdown(
            f"""
            <style>
            /* WorkZo v46: show this top toolbox ONLY on mobile.
               Desktop keeps the real Streamlit left sidebar toolbox. */
            .wz45-mobile-topnav {{ display: none !important; }}
            @media (max-width: 700px) {{
                .wz45-mobile-topnav {{
                    display: block !important;
                    position: sticky !important;
                    top: 0 !important;
                    z-index: 9999 !important;
                    margin: 0 0 0.75rem 0 !important;
                    padding: 0.75rem !important;
                    border: 1px solid rgba(20,184,166,0.24) !important;
                    border-radius: 18px !important;
                    background: linear-gradient(135deg, rgba(15,23,42,0.98), rgba(8,47,73,0.92)) !important;
                    box-shadow: 0 10px 28px rgba(2,6,23,0.30) !important;
                }}
                .wz45-mobile-title {{ color: #f8fafc !important; font-weight: 850 !important; font-size: 0.95rem !important; margin-bottom: 0.5rem !important; }}
                .wz45-mobile-links {{ display: grid !important; grid-template-columns: repeat(2, minmax(0, 1fr)) !important; gap: 0.45rem !important; }}
                .wz45-mobile-link {{
                    display: block !important;
                    text-align: center !important;
                    color: #e0f2fe !important;
                    text-decoration: none !important;
                    border: 1px solid rgba(96,165,250,0.26) !important;
                    background: rgba(37,99,235,0.16) !important;
                    border-radius: 999px !important;
                    padding: 0.48rem 0.55rem !important;
                    font-weight: 700 !important;
                    font-size: 0.86rem !important;
                    white-space: nowrap !important;
                }}
            }}
            </style>
            <div class="wz45-mobile-topnav">
                <div class="wz45-mobile-title">☰ {_html.escape(t['tools'])}</div>
                <div class="wz45-mobile-links">
                    {link('dashboard', '🏠 ' + t['dashboard'])}
                    {link('cv_documents', '📄 ' + t['cv'])}
                    {link('job_assist', '🎯 ' + t['jobs'])}
                    {link('workobot', '🤖 ' + t['bot'])}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    except Exception:
        pass

try:
    _wz45_previous_show_dashboard = show_dashboard
    def show_dashboard():
        _wz45_render_mobile_top_nav()
        return _wz45_previous_show_dashboard()
except Exception:
    pass


# =========================================================
# WorkZo v48 dashboard responsive toolbox guard
# The mobile top menu is rendered, but CSS shows it only on phones.
# =========================================================
try:
    st.markdown("""
    <style id="workzo-v48-dashboard-topnav-guard">
    .wz45-mobile-topnav { display: none !important; }
    @media (min-width: 701px) {
        .wz45-mobile-topnav {
            display: none !important;
            visibility: hidden !important;
            height: 0 !important;
            overflow: hidden !important;
            margin: 0 !important;
            padding: 0 !important;
            border: 0 !important;
        }
    }
    @media (max-width: 700px) {
        .wz45-mobile-topnav { display: block !important; visibility: visible !important; height: auto !important; }
    }
    </style>
    """, unsafe_allow_html=True)
except Exception:
    pass


# =========================================================
# WorkZo v49 memory + progress stabilization wrapper
# Keeps safe dashboard progress after refresh and saves status flags continuously.
# =========================================================
def _wz49_detect_and_save_progress_flags():
    try:
        if st.session_state.get('cv_text') or st.session_state.get('structured_cv_json') or st.session_state.get('approved_structured_cv_json'):
            st.session_state['_wz_has_cv'] = True
        if st.session_state.get('improved_cv_text') or st.session_state.get('latest_improved_cv') or st.session_state.get('final_cv_text'):
            st.session_state['_wz_cv_improved'] = True
        if st.session_state.get('latest_curated_jobs') or st.session_state.get('latest_job_query_expansion'):
            st.session_state['_wz_job_found'] = True
        if st.session_state.get('latest_job_analysis') or st.session_state.get('last_understand_job_description') or st.session_state.get('current_job_description'):
            st.session_state['_wz_job_analyzed'] = True
        if st.session_state.get('latest_application_prep') or st.session_state.get('latest_cover_letter') or st.session_state.get('cover_letter_text'):
            st.session_state['_wz_prepared'] = True
        for a, b in [('cv_score_value','_best_cv_score_value'), ('ats_score_value','_best_ats_score_value'), ('job_fit_score_value','_best_job_fit_score_value')]:
            try:
                cur = int(float(st.session_state.get(a) or 0))
                best = int(float(st.session_state.get(b) or 0))
                if cur > best:
                    st.session_state[b] = cur
                elif best > 0 and cur <= 0:
                    st.session_state[a] = best
            except Exception:
                pass
        if callable(globals().get('workzo_save_light_memory')):
            workzo_save_light_memory()
    except Exception:
        pass

try:
    _wz49_previous_show_dashboard = show_dashboard
    def show_dashboard():
        try:
            if callable(globals().get('workzo_load_light_memory')):
                workzo_load_light_memory()
        except Exception:
            pass
        _wz49_detect_and_save_progress_flags()
        result = _wz49_previous_show_dashboard()
        _wz49_detect_and_save_progress_flags()
        return result
except Exception:
    pass

# =========================================================
# WorkZo v50 FINAL PROGRESS + FOUNDER ANALYTICS PATCH
# Fixes false green checks by using explicit completion conditions:
# 1 CV uploaded, 2 CV improved, 3 Job matched, 4 Prepared for job.
# Adds founder tracking events for each progress transition.
# =========================================================

def _wz50_bool_text(*keys):
    try:
        return any(bool(str(st.session_state.get(k, '') or '').strip()) for k in keys)
    except Exception:
        return False


def _wz50_has_list(key):
    try:
        v = st.session_state.get(key)
        return isinstance(v, list) and len(v) > 0
    except Exception:
        return False


def _wz50_progress_state():
    """Return strict progress state. Do not mark steps done merely because a score exists."""
    cv_uploaded = bool(
        str(st.session_state.get('cv_text', '') or '').strip()
        or st.session_state.get('structured_cv_json')
        or st.session_state.get('approved_structured_cv_json')
        or st.session_state.get('_workzo_has_cv')
        or st.session_state.get('_wz_progress_cv_uploaded')
    )
    if cv_uploaded:
        st.session_state['_wz_progress_cv_uploaded'] = True
        st.session_state['_workzo_has_cv'] = True

    cv_improved = bool(
        _wz50_bool_text('improved_cv_text', 'latest_improved_cv', 'final_cv_text', 'workzo_latest_tailored_cv')
        or st.session_state.get('_wz_progress_cv_improved')
    )
    if _wz50_bool_text('improved_cv_text', 'latest_improved_cv', 'final_cv_text', 'workzo_latest_tailored_cv'):
        st.session_state['_wz_progress_cv_improved'] = True
        cv_improved = True

    # Job match/finding is NOT the same as merely having a pasted job description.
    # It becomes complete only after live job search/curation exists, or an explicit progress flag was set.
    job_matched = bool(
        _wz50_has_list('latest_curated_jobs')
        or _wz50_has_list('latest_live_jobs')
        or _wz50_has_list('job_search_results')
        or bool(st.session_state.get('latest_job_query_expansion'))
        or st.session_state.get('_wz_progress_job_matched')
    )
    if _wz50_has_list('latest_curated_jobs') or _wz50_has_list('latest_live_jobs') or _wz50_has_list('job_search_results') or bool(st.session_state.get('latest_job_query_expansion')):
        st.session_state['_wz_progress_job_matched'] = True
        job_matched = True

    prepared = bool(
        _wz50_bool_text('latest_application_prep', 'latest_cover_letter', 'cover_letter_text', 'generated_cover_letter', 'saved_application_prep')
        or st.session_state.get('_wz_progress_prepared')
    )
    if _wz50_bool_text('latest_application_prep', 'latest_cover_letter', 'cover_letter_text', 'generated_cover_letter', 'saved_application_prep'):
        st.session_state['_wz_progress_prepared'] = True
        prepared = True

    return {
        'cv_uploaded': bool(cv_uploaded),
        'cv_improved': bool(cv_improved),
        'job_matched': bool(job_matched),
        'prepared': bool(prepared),
    }


def _wz50_track_progress(progress):
    """Founder-safe analytics: track progress flags only, no CV/job text."""
    try:
        previous = st.session_state.get('_wz50_last_progress_snapshot') or {}
        if not isinstance(previous, dict):
            previous = {}
        for key, done in progress.items():
            if done and not previous.get(key):
                if callable(globals().get('track_event')):
                    track_event('progress_step_completed', 'Application Progress', {'step': key})
        if previous != progress and callable(globals().get('track_event')):
            track_event('progress_snapshot', 'Application Progress', progress)
        st.session_state['_wz50_last_progress_snapshot'] = dict(progress)
    except Exception:
        pass


def _wz50_save_state():
    """Save safe UI memory. Do not persist CV text, job descriptions, or generated documents."""
    try:
        keys = [
            'cv_score_value', 'ats_score_value', 'application_readiness_value',
            'job_fit_score_value', 'interview_score', 'country', 'preferred_language',
            'ui_language', 'response_language', 'language', 'target_company_website',
            'target_company', 'prepare_target_company', 'nav_page', 'page',
            '_workzo_has_cv', '_wz_progress_cv_uploaded', '_wz_progress_cv_improved',
            '_wz_progress_job_matched', '_wz_progress_prepared',
            '_best_cv_score_value', '_best_ats_score_value', '_best_application_readiness_value',
        ]
        data = {}
        for k in keys:
            v = st.session_state.get(k)
            if isinstance(v, (str, int, float, bool)) or v is None:
                data[k] = v
        progress = _wz50_progress_state()
        data.update({
            '_wz_progress_cv_uploaded': progress['cv_uploaded'],
            '_wz_progress_cv_improved': progress['cv_improved'],
            '_wz_progress_job_matched': progress['job_matched'],
            '_wz_progress_prepared': progress['prepared'],
        })
        with open(_wz35_state_file(), 'w', encoding='utf-8') as f:
            _wz35_json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _wz50_load_state():
    """Load safe UI memory. Ignore old false-progress flags from earlier builds."""
    try:
        path = _wz35_state_file()
        if not _wz35_os.path.exists(path):
            return
        with open(path, 'r', encoding='utf-8') as f:
            data = _wz35_json.load(f)
        if not isinstance(data, dict):
            return
        allowed = {
            'cv_score_value', 'ats_score_value', 'application_readiness_value',
            'job_fit_score_value', 'interview_score', 'country', 'preferred_language',
            'ui_language', 'response_language', 'language', 'target_company_website',
            'target_company', 'prepare_target_company', 'nav_page', 'page',
            '_workzo_has_cv', '_wz_progress_cv_uploaded', '_wz_progress_cv_improved',
            '_wz_progress_job_matched', '_wz_progress_prepared',
            '_best_cv_score_value', '_best_ats_score_value', '_best_application_readiness_value',
        }
        for k, v in data.items():
            if k in allowed and (k not in st.session_state or st.session_state.get(k) in [None, '', 0, False]):
                st.session_state[k] = v
        for key in ['cv_score_value', 'ats_score_value', 'application_readiness_value']:
            try:
                best = int(st.session_state.get('_best_' + key) or 0)
                cur = int(st.session_state.get(key) or 0)
                if best > cur:
                    st.session_state[key] = best
            except Exception:
                pass
    except Exception:
        pass

# Rebind the older helper names so the rest of the file uses v50 memory.
_wz35_save_state = _wz50_save_state
_wz35_load_state = _wz50_load_state


def _wz50_sidebar(page_key):
    with st.sidebar:
        try:
            logo_src = image_to_data_uri(ICON_PATH) or image_to_data_uri(LOGO_PATH)
        except Exception:
            logo_src = None
        if logo_src:
            st.markdown(f"""
            <div class='workzo-sidebar-brand-wrap'>
              <img src='{logo_src}' class='workzo-sidebar-logo' alt='WorkZo AI logo'>
              <div><div class='workzo-sidebar-brand'>WORKZO AI</div><div class='workzo-sidebar-version'>Beta · guided workspace</div></div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown('### WorkZo AI')

        navs = [('dashboard', txt('dashboard')), ('cv_documents', txt('cv_documents')), ('job_assist', txt('job_assist')), ('workobot', 'Work-O-Bot')]
        for key, label in navs:
            text = str(label) + ('  ✓' if page_key == key else '')
            if st.button(text, key=f'wz50_nav_{key}', use_container_width=True):
                _wz35_go(key)

        st.markdown(f"<div class='workzo-sidebar-section-label'>{html.escape(txt('company_context'))}</div>", unsafe_allow_html=True)
        with st.expander('🏢 ' + txt('company_website'), expanded=False):
            company_url = st.text_input(txt('company_website'), key='target_company_website', placeholder='https://company.com')
            if company_url:
                st.caption(ui_label('Used for cover letters and job/interview preparation context.'))

        st.markdown(f"<div class='workzo-sidebar-section-label'>{html.escape(txt('language'))}</div>", unsafe_allow_html=True)
        try:
            langs = language_options if 'language_options' in globals() and language_options else ['English', 'German', 'Dutch', 'French', 'Spanish', 'Portuguese']
        except Exception:
            langs = ['English', 'German', 'Dutch', 'French', 'Spanish', 'Portuguese']
        cur = st.session_state.get('preferred_language') or st.session_state.get('language') or 'English'
        if cur not in langs:
            cur = 'English' if 'English' in langs else langs[0]
        chosen = st.selectbox(txt('preferred_language'), langs, index=langs.index(cur), key='wz50_preferred_language')
        _wz35_sync_language(chosen)

        st.markdown('---')
        if st.button(txt('edit_setup'), key='wz50_edit_setup', use_container_width=True):
            st.session_state['onboarding_complete'] = False
            st.session_state['page'] = 'onboarding'
            st.session_state['nav_page'] = 'onboarding'
            try:
                st.query_params['page'] = 'onboarding'
            except Exception:
                pass
            _wz50_save_state()
            st.rerun()

        with st.expander('Founder analytics', expanded=False):
            founder_pin = None
            try:
                founder_pin = (os.getenv('FOUNDER_PIN') or get_streamlit_secret('FOUNDER_PIN'))
            except Exception:
                founder_pin = os.getenv('FOUNDER_PIN') if 'os' in globals() else None
            if founder_pin:
                pin = st.text_input('Founder PIN', type='password', key='wz50_founder_pin')
                if pin == founder_pin:
                    st.session_state['founder_unlocked'] = True
                    st.success('Founder mode unlocked.')
            else:
                st.caption('FOUNDER_PIN not configured. Temporary founder access for local testing.')
                if st.text_input('Temporary founder PIN', type='password', key='wz50_temp_pin'):
                    st.session_state['founder_unlocked'] = True
            if st.session_state.get('founder_unlocked'):
                if st.button('Open founder analytics', key='wz50_founder_nav', use_container_width=True):
                    _wz35_go('founder_dashboard')


def _wz50_current_step(progress):
    if not progress['cv_uploaded']:
        return 0
    if not progress['cv_improved']:
        return 1
    if not progress['job_matched']:
        return 2
    if not progress['prepared']:
        return 3
    return 4


def _wz50_dashboard_home():
    _wz50_load_state()
    _wz35_remember_scores()
    _wz35_force_scroll_top()
    _wz35_css()

    progress = _wz50_progress_state()
    _wz50_track_progress(progress)

    cv_exists = progress['cv_uploaded']
    resume_score = _wz35_score('cv_score_value', 'resume_score', 'resume_quality_score', '_best_cv_score_value', default=76 if cv_exists else 0)
    ats_score = _wz35_score('ats_score_value', 'ats_score', '_best_ats_score_value', default=70 if cv_exists else 0)
    interview_score = _wz35_score('interview_score', 'interview_readiness', '_best_interview_score', default=40 if cv_exists else 0)
    country = st.session_state.get('country') or st.session_state.get('target_country') or 'Not set'
    language = st.session_state.get('preferred_language') or st.session_state.get('language') or 'English'

    # Smart next action uses strict progress, not accidental score presence.
    if not progress['cv_uploaded']:
        next_action = {'title':'Start with your CV', 'copy':'Upload or create your CV first so WorkZo can guide the next steps.', 'button':'Add CV', 'target':'onboarding', 'extra':{}}
    elif not progress['cv_improved']:
        next_action = {'title':'Improve your CV', 'copy':'Make your CV stronger before job matching. Tailor structure, keywords, and achievements.', 'button':'Improve CV', 'target':'cv_documents', 'extra':{'document_tools_mode':'Improve / Update CV'}}
    elif not progress['job_matched']:
        next_action = {'title':'Find matching jobs', 'copy':'Search jobs for your selected country and choose one role to analyze.', 'button':'Open Job Match', 'target':'job_assist', 'extra':{'job_assist_mode_key':'find'}}
    elif not progress['prepared']:
        next_action = {'title':'Prepare for this job', 'copy':'Create cover letter/application prep and practice your strongest answers.', 'button':'Prepare this job', 'target':'job_assist', 'extra':{'job_assist_mode_key':'prepare'}}
    else:
        next_action = {'title':'Ready to apply', 'copy':'Your core application flow is complete. Apply, track the result, and practice with Work-O-Bot.', 'button':'Practice with Work-O-Bot', 'target':'workobot', 'extra':{}}

    st.markdown(f"""
    <div class='wz35-hero'>
      <div class='wz35-kicker'>{_wz35_escape(txt('workzo_command_center'))}</div>
      <div class='wz35-title'>{_wz35_escape(txt('next_best_move_clear'))}</div>
      <div class='wz35-sub'>{_wz35_escape(txt('next_best_move_copy'))}</div>
      <div class='wz35-chip-row'>
        <span class='wz35-chip'>{_wz35_escape(country)}</span>
        <span class='wz35-chip'>{_wz35_escape(language)}</span>
        <span class='wz35-chip'>{_wz35_escape(ui_label('CV ready') if progress['cv_uploaded'] else ui_label('CV missing'))}</span>
        <span class='wz35-chip'>{_wz35_escape(ui_label('CV improved') if progress['cv_improved'] else ui_label('CV not improved'))}</span>
        <span class='wz35-chip'>{_wz35_escape(ui_label('Job matched') if progress['job_matched'] else ui_label('Job not matched'))}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class='wz35-next'>
      <div class='wz35-next-label'>{_wz35_escape(txt('recommended_next_step'))}</div>
      <div class='wz35-next-title'>{_wz35_escape(next_action['title'])}</div>
      <div class='wz35-next-copy'>{_wz35_escape(next_action['copy'])}</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button(next_action['button'], key='wz50_primary_action', use_container_width=True):
        _wz35_go(next_action['target'], next_action.get('extra'))

    st.markdown('### ' + txt('readiness_overview'))
    c1, c2, c3 = st.columns(3)
    with c1:
        _wz35_rate_card(txt('resume_score'), resume_score, ui_label('Clarity, structure, achievements, and overall CV quality.'), missing=not cv_exists)
    with c2:
        _wz35_rate_card(txt('ats_score'), ats_score, ui_label('Scanner-friendly formatting, role keywords, sections, and parsing safety.'), missing=not cv_exists)
    with c3:
        _wz35_rate_card(txt('interview_readiness'), interview_score, ui_label('How ready you are to explain your CV and job fit clearly.'), missing=not cv_exists)

    st.markdown('### ' + txt('smart_actions'))
    a1, a2, a3, a4 = st.columns(4)
    with a1:
        _wz35_action_card(txt('improve_cv'), ui_label('Use this to improve your CV or tailor it to a specific job.'), txt('open_cv_tools'), 'cv_documents', 'wz50_action_cv', {'document_tools_mode':'Improve / Update CV'})
    with a2:
        _wz35_action_card(txt('job_match'), ui_label('Search jobs for the selected country, then analyze one job description for fit.'), txt('open_job_assist'), 'job_assist', 'wz50_action_jobs', {'job_assist_mode_key':'find'})
    with a3:
        _wz35_action_card(txt('cover_letter'), ui_label('Use CV, job description, and company context to create a focused cover letter.'), txt('create_cover_letter'), 'cv_documents', 'wz50_action_cover', {'document_tools_mode':'Cover Letter Generator + Language'})
    with a4:
        _wz35_action_card('Work-O-Bot', ui_label('Ask career questions or practice interview answers in your selected language.'), txt('ask_workobot'), 'workobot', 'wz50_action_bot')

    st.markdown('### ' + txt('application_progress'))
    st.caption(ui_label('Checks appear only after each action is actually completed.'))
    current = _wz50_current_step(progress)
    flow = [
        ('1. CV uploaded', progress['cv_uploaded'], txt('completed') if progress['cv_uploaded'] else ui_label('Upload or create CV'), txt('edit_setup'), 'onboarding', {}),
        ('2. CV improved', progress['cv_improved'], txt('completed') if progress['cv_improved'] else ui_label('Improve or tailor your CV'), txt('improve_cv'), 'cv_documents', {'document_tools_mode':'Improve / Update CV'}),
        ('3. Job matched', progress['job_matched'], txt('completed') if progress['job_matched'] else ui_label('Find matching jobs'), txt('open_job_assist'), 'job_assist', {'job_assist_mode_key':'find'}),
        ('4. Prepared for job', progress['prepared'], txt('completed') if progress['prepared'] else ui_label('Prepare cover letter and interview notes'), txt('prepare_this_job'), 'job_assist', {'job_assist_mode_key':'prepare'}),
    ]
    cols = st.columns(4)
    for i, (label, done, note, button, target, extra) in enumerate(flow):
        with cols[i]:
            _wz35_flow_card(label, done, current == i, note)
    st.caption(ui_label('Scores are guidance only. WorkZo should not invent skills, company facts, language level, salary, or experience.'))
    _wz35_remember_scores()
    _wz50_save_state()


def show_dashboard():
    _wz50_load_state()
    _wz35_sync_language()
    _wz35_force_scroll_top()
    page_key = st.session_state.get('nav_page') or st.session_state.get('page') or 'dashboard'
    page_key = {'landing':'dashboard', 'bot':'workobot', 'interview':'workobot', 'jobs':'job_assist', 'improve_cv':'cv_documents'}.get(page_key, page_key)
    if page_key == 'interview_practice':
        page_key = 'workobot'
    if page_key not in {'dashboard', 'cv_documents', 'job_assist', 'workobot', 'founder_dashboard'}:
        page_key = 'dashboard'
    st.session_state['page'] = page_key
    st.session_state['nav_page'] = page_key
    try:
        _wz28_top(True)
    except Exception:
        pass
    _wz50_sidebar(page_key)

    if page_key == 'dashboard':
        _wz50_dashboard_home()
    elif page_key == 'cv_documents':
        _wz35_css()
        show_document_tools()
    elif page_key == 'job_assist':
        _wz35_css()
        try:
            _wz28_job_assist_page()
        except Exception:
            st.subheader(txt('job_assist'))
            tab1, tab2, tab3 = st.tabs([txt('find_jobs'), txt('understand_job'), txt('prepare_this_job')])
            with tab1: st.info('Job search module could not be loaded.')
            with tab2: st.info('Understand Job module could not be loaded.')
            with tab3: st.info('Prepare module could not be loaded.')
    elif page_key == 'workobot':
        _wz35_css()
        show_workobot()
    elif page_key == 'founder_dashboard':
        _wz35_css()
        if st.session_state.get('founder_unlocked') and callable(globals().get('render_founder_dashboard')):
            render_founder_dashboard()
        else:
            st.warning('Founder mode is locked. Enter the Founder PIN in the sidebar.')

    _wz35_remember_scores()
    _wz50_save_state()


# =========================================================
# WorkZo v51 - Enable classic Job Assist and disable AI Job Application Assistant
# This final override intentionally runs last.
# - Restores Job Assist: Find Jobs | Understand Job | Prepare this Job
# - Removes the AI Job Application Assistant wrapper from the active route
# - Keeps existing dashboard, sidebar, memory, progress, Work-O-Bot, and CV tools
# =========================================================
def _wz51_safe_label(text_value, fallback=None):
    try:
        if callable(globals().get("txt")):
            translated = txt(str(text_value))
            if translated and translated != str(text_value):
                return translated
    except Exception:
        pass
    try:
        if callable(globals().get("ui_label")):
            return ui_label(str(fallback or text_value))
    except Exception:
        pass
    return str(fallback or text_value)


def _wz51_go(page_key, extra=None):
    try:
        if extra:
            for k, v in extra.items():
                st.session_state[k] = v
        st.session_state["page"] = page_key
        st.session_state["nav_page"] = page_key
        if callable(globals().get("request_scroll_to_top")):
            request_scroll_to_top()
        st.rerun()
    except Exception:
        st.session_state["page"] = page_key
        st.session_state["nav_page"] = page_key


def _wz51_extract_roles_from_cv(cv_text):
    cv_text = str(cv_text or "")
    roles = []
    for key in ["target_role", "detected_target_role", "current_role_detected"]:
        val = st.session_state.get(key)
        if isinstance(val, str) and val.strip():
            roles.append(val.strip())
    first_lines = [x.strip() for x in cv_text.splitlines() if x.strip()][:8]
    for line in first_lines:
        low = line.lower()
        if any(word in low for word in ["engineer", "developer", "analyst", "scientist", "support", "manager", "consultant", "specialist", "designer"]):
            clean = re.sub(r"[|•].*$", "", line).strip(" -–—")
            if 3 <= len(clean) <= 70:
                roles.append(clean)
    # sensible fallback
    if not roles:
        roles = ["Data Analyst", "IT Support Specialist", "Customer Support Specialist"]
    deduped = []
    seen = set()
    for r in roles:
        k = r.casefold()
        if k not in seen:
            seen.add(k)
            deduped.append(r)
    return deduped[:6]


def _wz51_simple_job_card(job, idx=0):
    title = html.escape(str(job.get("title") or job.get("job_title") or "Job opening"))
    company = html.escape(str(job.get("company") or job.get("employer_name") or "Company not listed"))
    location = html.escape(str(job.get("location") or job.get("job_location") or "Location not listed"))
    source = html.escape(str(job.get("source") or job.get("publisher") or "Live source"))
    url = str(job.get("url") or job.get("redirect_url") or job.get("job_apply_link") or "")
    st.markdown(f"""
    <div class='next-action-card' style='margin:10px 0;'>
      <div class='next-action-label'>{source}</div>
      <div class='next-action-title'>{title}</div>
      <div class='next-action-copy'>{company} · {location}</div>
    </div>
    """, unsafe_allow_html=True)
    if url:
        st.link_button(_wz51_safe_label("View job", "View job"), url, use_container_width=False)


def _wz51_render_find_jobs():
    """Smarter Job Assist > Find Jobs page. Only Job Assist is changed in this v53 patch."""
    st.markdown("### " + _wz51_safe_label("find_jobs", "Find Jobs"))

    cv_text = str(st.session_state.get("cv_text") or st.session_state.get("clean_structured_cv_text") or "")
    user_country = str(st.session_state.get("country") or st.session_state.get("migration_country") or "").strip() or "Global"
    suggested_roles = _wz51_extract_roles_from_cv(cv_text)
    default_titles = ", ".join(suggested_roles[:3]) or str(st.session_state.get("target_role") or "")

    # Safe defaults BEFORE widgets render. Do not overwrite widget keys later.
    if "job_assist_target_titles" not in st.session_state:
        st.session_state["job_assist_target_titles"] = default_titles
    if "job_assist_location_text" not in st.session_state:
        st.session_state["job_assist_location_text"] = "" if user_country == "Global" else user_country

    st.markdown(f"""
    <div class='next-action-card' style='margin-top:4px;'>
      <div class='next-action-label'>{html.escape(_wz51_safe_label('Smart job search', 'Smart job search'))}</div>
      <div class='next-action-title'>{html.escape(_wz51_safe_label('Search by role + location, then analyze the best job', 'Search by role + location, then analyze the best job'))}</div>
      <div class='next-action-copy'>{html.escape(_wz51_safe_label('WorkZo uses your CV, target role, selected country, and preferred location to find better matches. Add a city, country, or Remote — not a long sentence.', 'WorkZo uses your CV, target role, selected country, and preferred location to find better matches. Add a city, country, or Remote — not a long sentence.'))}</div>
    </div>
    """, unsafe_allow_html=True)

    a, b = st.columns([1.15, 0.85])
    with a:
        target_titles = st.text_input(
            _wz51_safe_label("Target job titles", "Target job titles"),
            placeholder="Data Analyst, IT Support, Customer Success",
            key="job_assist_target_titles",
            help=_wz51_safe_label("Use 1-3 role titles. WorkZo will search around these titles instead of using your full CV text.", "Use 1-3 role titles. WorkZo will search around these titles instead of using your full CV text."),
        )
    with b:
        location = st.text_input(
            _wz51_safe_label("Preferred location", "Preferred location"),
            placeholder=f"{user_country}, Remote, Berlin, Chennai...",
            key="job_assist_location_text",
            help=_wz51_safe_label("Examples: Germany, Remote, Berlin, Chennai, London. This replaces the old country dropdown.", "Examples: Germany, Remote, Berlin, Chennai, London. This replaces the old country dropdown."),
        )

    roles_preview = [x.strip() for x in re.split(r"[,;\n/]", target_titles or "") if x.strip()]
    if not roles_preview and suggested_roles:
        roles_preview = suggested_roles[:3]
    role_chips = "".join(f"<span class='workzo-dashboard-chip'>{html.escape(r)}</span>" for r in roles_preview[:4]) or f"<span class='workzo-dashboard-chip'>{html.escape(_wz51_safe_label('Add a target title', 'Add a target title'))}</span>"
    loc_chip = html.escape(str(location or user_country or "Global"))
    st.markdown(f"""
    <div class='workzo-mini-note' style='margin: 8px 0 14px 0;'>
        {_wz51_safe_label('Search context', 'Search context')}: {role_chips}
        <span class='workzo-dashboard-chip'>📍 {loc_chip}</span>
    </div>
    """, unsafe_allow_html=True)

    with st.expander(_wz51_safe_label("Review CV signals used for matching", "Review CV signals used for matching"), expanded=False):
        try:
            cv_profile = build_job_matching_profile(cv_text) if callable(globals().get("build_job_matching_profile")) else cv_text
        except Exception:
            cv_profile = cv_text
        st.text_area(_wz51_safe_label("CV matching profile", "CV matching profile"), value=cv_profile, height=220, key="job_assist_cv_review_v53")

    find_col, tip_col = st.columns([0.45, 1])
    with find_col:
        find_clicked = st.button(_wz51_safe_label("Find smart matches", "Find smart matches"), key="btn_find_jobs_v53", use_container_width=True)
    with tip_col:
        st.caption(_wz51_safe_label("Tip: after finding jobs, open one job and use Understand Job before improving your CV.", "Tip: after finding jobs, open one job and use Understand Job before improving your CV."))

    if find_clicked:
        roles = [x.strip() for x in re.split(r"[,;\n/]", target_titles or "") if x.strip()] or suggested_roles
        if not roles:
            st.warning(_wz51_safe_label("Please add at least one target job title.", "Please add at least one target job title."))
        else:
            search_location = (location or user_country or "").strip()
            # Store search memory in non-widget keys only.
            st.session_state["last_job_search_target_titles"] = ", ".join(roles[:6])
            st.session_state["last_job_search_location_text"] = search_location
            st.session_state["last_job_search_country"] = user_country
            try:
                if callable(globals().get("track_button_click")):
                    track_button_click("Find Jobs", "Job Assist", {"country": user_country, "location": search_location, "roles": roles[:3]})
            except Exception:
                pass

            with st.status(_wz51_safe_label("Searching and ranking jobs...", "Searching and ranking jobs..."), expanded=True) as status:
                st.write(_wz51_safe_label("Building focused search terms from your CV and target titles...", "Building focused search terms from your CV and target titles..."))
                jobs = []
                try:
                    if callable(globals().get("fetch_live_jobs_global")):
                        jobs = fetch_live_jobs_global(user_country, roles, search_location or user_country, st.session_state.get("user_status", "")) or []
                except Exception as exc:
                    st.warning(f"Live job source error: {exc}")
                st.write(_wz51_safe_label("Ranking results for your CV and location...", "Ranking results for your CV and location..."))
                try:
                    if jobs and callable(globals().get("curate_job_matches")):
                        jobs = curate_job_matches(jobs, cv_text, {"job_titles": roles, "search_queries": roles, "location": search_location}, user_country, st.session_state.get("user_status", ""), limit=25)
                except Exception:
                    pass
                st.session_state["latest_curated_jobs"] = jobs
                st.session_state["workzo_progress_job_matched"] = bool(jobs)
                status.update(label=_wz51_safe_label("Job search complete", "Job search complete"), state="complete", expanded=False)

    jobs = st.session_state.get("latest_curated_jobs") or []
    last_titles = st.session_state.get("last_job_search_target_titles") or target_titles or default_titles or "jobs"
    last_location = st.session_state.get("last_job_search_location_text") or location or user_country

    if jobs:
        st.markdown("#### " + _wz51_safe_label("Best matches found", "Best matches found"))
        st.caption(_wz51_safe_label("Open the most relevant job, then paste its description in Understand Job to get a real fit score.", "Open the most relevant job, then paste its description in Understand Job to get a real fit score."))
        try:
            if callable(globals().get("render_curated_job_matches")):
                render_curated_job_matches(jobs, user_country)
            else:
                for i, job in enumerate(jobs[:12]):
                    _wz51_simple_job_card(job, i)
        except Exception:
            for i, job in enumerate(jobs[:12]):
                _wz51_simple_job_card(job, i)
    else:
        st.info(_wz51_safe_label("No saved job results yet. Search with a specific role title and preferred location.", "No saved job results yet. Search with a specific role title and preferred location."))
        role_for_link = (last_titles or "jobs").split(",")[0].strip()
        q = urllib.parse.quote_plus(f"{role_for_link} {last_location}")
        st.markdown("#### " + _wz51_safe_label("Quick search links", "Quick search links"))
        st.caption(_wz51_safe_label("Use these if live APIs return too few jobs during testing.", "Use these if live APIs return too few jobs during testing."))
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.link_button("LinkedIn", f"https://www.linkedin.com/jobs/search/?keywords={q}")
        with c2: st.link_button("Indeed", f"https://www.indeed.com/jobs?q={q}")
        with c3: st.link_button("Google Jobs", f"https://www.google.com/search?q={q}+jobs")
        with c4: st.link_button("Wellfound", f"https://wellfound.com/jobs?query={q}")

def _wz51_keyword_match(cv_text, jd):
    cv_low = str(cv_text or "").lower()
    words = re.findall(r"[a-zA-Z][a-zA-Z+#.\-]{2,}", str(jd or "").lower())
    stop = set("the and with for you are this that from will have has job role team work experience skills our your in on of to a an is as be or by at it we they candidate looking required preferred ability good strong".split())
    keys = []
    for w in words:
        if w not in stop and w not in keys:
            keys.append(w)
    keys = keys[:40]
    matched = [k for k in keys if k in cv_low]
    missing = [k for k in keys if k not in cv_low]
    score = int(round((len(matched) / max(len(keys), 1)) * 100)) if keys else 0
    return score, matched, missing


def _wz51_render_understand_job():
    st.markdown("### " + _wz51_safe_label("understand_job", "Understand Job"))
    st.caption(_wz51_safe_label("Paste a job description. WorkZo checks fit, risks, missing keywords, and next actions.", "Paste a job description. WorkZo checks fit, risks, missing keywords, and next actions."))
    default_jd = st.session_state.get("last_understand_job_description") or st.session_state.get("current_job_description") or st.session_state.get("improve_cv_for_job_desc") or ""
    jd = st.text_area(_wz51_safe_label("Paste the job description", "Paste the job description"), value=default_jd, height=260, key="job_desc_v51_understand")
    if st.button(_wz51_safe_label("Analyze Job Fit", "Analyze Job Fit"), key="btn_understand_job_v51", use_container_width=True):
        if not jd.strip():
            st.warning(_wz51_safe_label("Please paste a job description first.", "Please paste a job description first."))
        else:
            cv_text = str(st.session_state.get("cv_text") or st.session_state.get("clean_structured_cv_text") or "")
            score, matched, missing = _wz51_keyword_match(cv_text, jd)
            st.session_state["current_job_description"] = jd
            st.session_state["last_understand_job_description"] = jd
            st.session_state["improve_cv_for_job_desc"] = jd
            st.session_state["latest_job_analysis"] = {"score": score, "matched": matched, "missing": missing, "source": "job_assist_v51"}
            st.session_state["job_fit_score_value"] = score
            st.session_state["workzo_progress_job_matched"] = True
            try:
                if callable(globals().get("track_event")):
                    track_event("job_analyzed", "Job Assist", {"fit_score": score})
            except Exception:
                pass
            st.success(_wz51_safe_label("Job analyzed. You can now tailor the CV or prepare the application.", "Job analyzed. You can now tailor the CV or prepare the application."))

    analysis = st.session_state.get("latest_job_analysis") or {}
    if jd.strip() or analysis:
        score = int(analysis.get("score") or st.session_state.get("job_fit_score_value") or 0)
        matched = analysis.get("matched") or []
        missing = analysis.get("missing") or []
        st.markdown("#### " + _wz51_safe_label("Job Fit", "Job Fit"))
        c1, c2, c3 = st.columns(3)
        c1.metric(_wz51_safe_label("Fit score", "Fit score"), f"{score}%" if score else "—")
        c2.metric(_wz51_safe_label("Matched keywords", "Matched keywords"), len(matched))
        c3.metric(_wz51_safe_label("Missing keywords", "Missing keywords"), len(missing))
        if missing:
            st.warning(_wz51_safe_label("Missing or weak keywords. Add them only if they are truthful.", "Missing or weak keywords. Add them only if they are truthful."))
            st.write(", ".join([html.escape(str(x)) for x in missing[:15]]))
        if matched:
            st.success(_wz51_safe_label("Your CV already shows some relevant signals.", "Your CV already shows some relevant signals."))
        a, b = st.columns(2)
        with a:
            if st.button(_wz51_safe_label("Improve CV for this job", "Improve CV for this job"), key="wz51_understand_improve", use_container_width=True):
                _wz51_go("cv_documents", {"document_tools_mode": "Improve CV for a Job", "improve_cv_for_job_desc": jd})
        with b:
            if st.button(_wz51_safe_label("Prepare for this job", "Prepare for this job"), key="wz51_understand_prepare", use_container_width=True):
                st.session_state["job_assist_mode_key"] = "prepare"
                st.rerun()


def _wz51_render_prepare_job():
    st.markdown("### " + _wz51_safe_label("prepare_this_job", "Prepare for this Job"))
    st.caption(_wz51_safe_label("Create a focused application and interview preparation plan from your CV and job context.", "Create a focused application and interview preparation plan from your CV and job context."))
    c1, c2 = st.columns(2)
    with c1:
        company = st.text_input(_wz51_safe_label("Target company", "Target company"), value="", key="wz51_target_company_clean", placeholder=_wz51_safe_label("Example: Siemens, SAP, Google", "Example: Siemens, SAP, Google"))
    with c2:
        role = st.text_input(_wz51_safe_label("Target role", "Target role"), value="", key="wz51_target_role_clean", placeholder=_wz51_safe_label("Example: Data Analyst, IT Support", "Example: Data Analyst, IT Support"))
    website = st.text_input(_wz51_safe_label("Company website / careers page", "Company website / careers page"), value="", key="wz51_company_website_clean", placeholder="https://company.com")
    jd = st.text_area(_wz51_safe_label("Job description", "Job description"), value=st.session_state.get("last_understand_job_description", ""), height=220, key="wz51_prepare_jd")
    if st.button(_wz51_safe_label("Prepare application", "Prepare application"), key="wz51_prepare_application", use_container_width=True):
        st.session_state["target_company"] = company.strip()
        st.session_state["target_job_title"] = role.strip()
        # Do not write to st.session_state["target_company_website"] here.
        # That key is also used by an existing Streamlit widget elsewhere,
        # so modifying it after widget creation causes StreamlitAPIException.
        st.session_state["company_website"] = website.strip()
        st.session_state["wz51_saved_company_website"] = website.strip()
        st.session_state["current_job_description"] = jd.strip()
        st.session_state["last_prepare_job_description"] = jd.strip()
        cv_text = str(st.session_state.get("cv_text") or st.session_state.get("clean_structured_cv_text") or "")
        prompt = f"""
You are WorkZo AI. Create a practical, honest job application preparation plan.
Do not invent company facts, skills, salary, language level, or experience.
Preferred language: {st.session_state.get('preferred_language','English')}
Country: {st.session_state.get('country','')}
Company: {company}
Role: {role}
Website: {website}
CV summary/text:
{cv_text[:4000]}
Job description:
{jd[:4000]}
Return concise sections: application focus, CV tailoring points, cover letter angle, interview stories, risks/missing proof, next actions.
"""
        result = ""
        try:
            if callable(globals().get("run_ai_prompt")):
                result = run_ai_prompt(prompt)
        except Exception as exc:
            result = f"Preparation could not use AI right now. Review CV-job alignment manually. Error: {exc}"
        if not result:
            result = "Application focus: tailor your CV to the job description, prepare 3 examples using STAR, and write a cover letter using only truthful company/context details."
        st.session_state["latest_application_prep"] = result
        st.session_state["workzo_progress_prepared"] = True
        try:
            if callable(globals().get("track_event")):
                track_event("application_prepared", "Job Assist", {"company": company, "role": role})
        except Exception:
            pass
        st.success(_wz51_safe_label("Preparation created.", "Preparation created."))
    if st.session_state.get("latest_application_prep"):
        st.markdown("#### " + _wz51_safe_label("Preparation plan", "Preparation plan"))
        st.markdown(str(st.session_state.get("latest_application_prep")))


def _wz51_render_job_assist_page():
    try:
        _wz35_css()
    except Exception:
        pass
    st.subheader(_wz51_safe_label("job_assist", "Job Assist"))
    mode_labels = {
        "find": _wz51_safe_label("find_jobs", "Find Jobs"),
        "understand": _wz51_safe_label("understand_job", "Understand Job"),
        "prepare": _wz51_safe_label("prepare_this_job", "Prepare for this Job"),
    }
    if st.session_state.get("job_assist_mode_key") not in mode_labels:
        st.session_state["job_assist_mode_key"] = "find"
    mode = st.radio(
        "Job Assist mode",
        ["find", "understand", "prepare"],
        horizontal=True,
        format_func=lambda x: mode_labels.get(x, x),
        key="job_assist_mode_key",
        label_visibility="collapsed",
    )
    st.divider()
    if mode == "find":
        _wz51_render_find_jobs()
    elif mode == "understand":
        _wz51_render_understand_job()
    else:
        _wz51_render_prepare_job()


# Final v51 router override: keeps Dashboard/CV/Work-O-Bot but uses classic Job Assist.
def show_dashboard():
    try:
        _wz35_load_state()
    except Exception:
        pass
    try:
        _wz35_sync_language()
    except Exception:
        pass
    try:
        _wz35_force_scroll_top()
    except Exception:
        pass

    page_key = st.session_state.get("nav_page") or st.session_state.get("page") or "dashboard"
    page_key = {"landing":"dashboard", "bot":"workobot", "interview":"workobot", "jobs":"job_assist", "improve_cv":"cv_documents"}.get(page_key, page_key)
    if page_key == "interview_practice":
        page_key = "workobot"
    if page_key not in {"dashboard", "cv_documents", "job_assist", "workobot", "founder_dashboard"}:
        page_key = "dashboard"
    st.session_state["page"] = page_key
    st.session_state["nav_page"] = page_key

    try:
        _wz28_top(True)
    except Exception:
        pass
    try:
        _wz35_sidebar(page_key)
    except Exception:
        pass

    if page_key == "dashboard":
        _wz35_dashboard_home()
    elif page_key == "cv_documents":
        try:
            _wz35_css()
        except Exception:
            pass
        show_document_tools()
    elif page_key == "job_assist":
        _wz51_render_job_assist_page()
    elif page_key == "workobot":
        try:
            _wz35_css()
        except Exception:
            pass
        show_workobot()
    elif page_key == "founder_dashboard":
        if st.session_state.get("founder_unlocked") and callable(globals().get("render_founder_dashboard")):
            render_founder_dashboard()
        else:
            st.warning("Founder dashboard is locked.")

    try:
        _wz35_remember_scores()
        _wz35_save_state()
    except Exception:
        pass
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
    """Preferred Language controls app labels, AI replies, and generated documents."""
    language = str(language or "English").strip() or "English"
    st.session_state.preferred_language = language
    st.session_state.language = language
    st.session_state.ui_language = language
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
        _prev_language = st.session_state.get("preferred_language", "English")
        preferred = st.selectbox(
            txt("preferred_language"),
            language_list,
            index=language_list.index(current_language),
            key="sidebar_preferred_language",
            help=txt("preferred_language_help")
        )
        set_single_preferred_language(preferred)
        if preferred != _prev_language:
            try:
                st.query_params["wz_lang"] = preferred
            except Exception:
                pass
            st.rerun()

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



        st.markdown("<div class='workzo-sidebar-section-label'>Company Context</div>", unsafe_allow_html=True)
        with st.expander("🏢 Company context", expanded=False):
            st.caption("Optional: paste the company website. WorkZo will use it for cover letters, mock tests, and interview preparation.")
            _current_company_url = str(st.session_state.get("target_company_website") or st.session_state.get("company_website") or "")
            _sidebar_company_url = st.text_input(
                "Company website",
                value=_current_company_url,
                placeholder="https://company.com",
                key="target_company_website_sidebar",
            )
            if _sidebar_company_url.strip() != _current_company_url.strip():
                st.session_state["company_website"] = _sidebar_company_url.strip()
                st.session_state["company_website"] = _sidebar_company_url.strip()
            if st.session_state.get("target_company_website"):
                st.caption("Saved for AI outputs in this session.")
            if st.button("Clear company context", key="clear_company_context_sidebar", use_container_width=True):
                for _k in ["target_company_website", "company_website", "target_company_context", "company_context_enabled"]:
                    st.session_state.pop(_k, None)
                st.rerun()

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

        # WorkZo Command Center: simple, smart, action-oriented dashboard.
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

        target_country_plan = st.session_state.get("migration_country") or st.session_state.get("country", "Not specified")
        target_role_plan = st.session_state.get("target_role") or st.session_state.get("detected_target_role") or st.session_state.get("current_role_detected") or ui_label("your target role")
        company_context = st.session_state.get("target_company_website", "")

        # Decide one clear next action. This replaces long feature lists.
        if not cv_ready:
            next_title = ui_label("Add your CV first")
            next_desc = ui_label("Upload or create your CV so WorkZo can score it, improve it, and match jobs.")
            next_button = ui_label("Start setup")
            next_target = "onboarding"
        elif ats_score and ats_score < 75:
            next_title = ui_label("Improve your CV before applying")
            next_desc = ui_label("Your ATS score needs work. Start with a cleaner, job-focused CV.")
            next_button = ui_label("Improve CV")
            next_target = "cv_documents"
        elif not job_ready:
            next_title = ui_label("Paste one real job description")
            next_desc = ui_label("WorkZo can compare your CV with the job and tell you whether to apply or tailor first.")
            next_button = ui_label("Understand a Job")
            next_target = "job_assist"
        elif not prepared_ready:
            next_title = ui_label("Prepare your application")
            next_desc = ui_label("Generate cover-letter focus, interview questions, and application strategy for this job.")
            next_button = ui_label("Prepare Application")
            next_target = "job_assist"
        else:
            next_title = ui_label("Practice and apply")
            next_desc = ui_label("Your application flow is ready. Use Work-O-Bot to practice answers or prepare messages.")
            next_button = ui_label("Open Work-O-Bot")
            next_target = "workobot"

        st.markdown(f"""
        <style>
        .wz-command-hero {{
            border: 1px solid rgba(20,184,166,0.28);
            border-radius: 24px;
            padding: 22px 24px;
            background: linear-gradient(135deg, rgba(37,99,235,0.24), rgba(20,184,166,0.14));
            box-shadow: 0 16px 44px rgba(2,6,23,0.26);
            margin: 10px 0 18px 0;
        }}
        .wz-command-kicker {{ color:#93c5fd; font-size:.78rem; font-weight:850; text-transform:uppercase; letter-spacing:.08em; margin-bottom:6px; }}
        .wz-command-title {{ color:#f8fafc; font-size:1.55rem; font-weight:900; line-height:1.22; margin-bottom:8px; }}
        .wz-command-copy {{ color:#dbeafe; font-size:.98rem; line-height:1.48; max-width:920px; }}
        .wz-smart-card {{ border:1px solid rgba(148,163,184,.16); border-radius:20px; padding:16px; background:rgba(15,23,42,.55); min-height:132px; margin-bottom:12px; }}
        .wz-smart-card.active {{ border-color:rgba(20,184,166,.45); background:linear-gradient(135deg, rgba(20,184,166,.16), rgba(37,99,235,.12)); }}
        .wz-smart-label {{ color:#94a3b8; font-size:.75rem; font-weight:850; text-transform:uppercase; letter-spacing:.07em; margin-bottom:6px; }}
        .wz-smart-title {{ color:#f8fafc; font-size:1.05rem; font-weight:850; margin-bottom:6px; }}
        .wz-smart-copy {{ color:#cbd5e1; font-size:.9rem; line-height:1.42; }}
        .wz-step-pill {{ border:1px solid rgba(148,163,184,.14); background:rgba(15,23,42,.42); border-radius:16px; padding:12px; min-height:88px; }}
        .wz-step-pill.done {{ border-color:rgba(20,184,166,.42); background:rgba(20,184,166,.11); }}
        .wz-step-title {{ color:#f8fafc; font-weight:800; font-size:.92rem; }}
        .wz-step-state {{ color:#94a3b8; font-size:.82rem; margin-top:5px; }}
        </style>
        <div class="wz-command-hero">
            <div class="wz-command-kicker">{html.escape(ui_label('Command Center'))}</div>
            <div class="wz-command-title">{html.escape(ui_label('Your next best career move, simplified'))}</div>
            <div class="wz-command-copy">
                {html.escape(ui_label('WorkZo uses your CV, selected country, language, job description, and company context to guide one clear next step instead of showing too many tools at once.'))}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Top KPI row: immediate signal, not long explanation.
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            render_metric_card(ui_label("Career Health"), f"{application_readiness}%", ui_label("Overall application readiness"))
        with k2:
            render_metric_card(txt("resume_score"), str(resume_score or "—"), score_band(resume_score) if resume_score else ui_label("Needs CV analysis"))
        with k3:
            render_metric_card(txt("ats_score"), str(ats_score or "—"), score_band(ats_score) if ats_score else ui_label("ATS check pending"))
        with k4:
            role_short = str(target_role_plan or ui_label("Not detected"))[:32]
            render_metric_card(ui_label("Target Role"), role_short, str(target_country_plan or "")[:36])

        st.markdown(f"""
        <div class="wz-smart-card active">
            <div class="wz-smart-label">{html.escape(ui_label('Next best action'))}</div>
            <div class="wz-smart-title">{html.escape(str(next_title))}</div>
            <div class="wz-smart-copy">{html.escape(str(next_desc))}</div>
        </div>
        """, unsafe_allow_html=True)

        if st.button(next_button, key="wz_command_center_next_action", use_container_width=True):
            track_button_click(str(next_button), "Dashboard Command Center")
            if next_target == "onboarding":
                st.session_state.page = "onboarding"
                st.session_state.nav_page = "onboarding"
                request_scroll_to_top()
            elif next_target == "job_assist" and not job_ready:
                st.session_state["job_assist_mode_key"] = "understand"
                queue_navigation("job_assist")
            elif next_target == "job_assist":
                st.session_state["job_assist_mode_key"] = "prepare"
                queue_navigation("job_assist")
            else:
                queue_navigation(next_target)
            st.rerun()

        st.markdown(f"### {html.escape(ui_label('Smart actions'))}")
        st.caption(ui_label("Choose one action. WorkZo reuses your existing CV, country, language, and company context."))
        a1, a2, a3, a4 = st.columns(4)
        with a1:
            st.markdown(f"""
            <div class="wz-smart-card">
                <div class="wz-smart-label">CV</div>
                <div class="wz-smart-title">{html.escape(ui_label('Improve CV'))}</div>
                <div class="wz-smart-copy">{html.escape(ui_label('Make your CV cleaner, more ATS-friendly, and job-specific.'))}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(ui_label("Open CV Tools"), key="wz_action_cv", use_container_width=True):
                queue_navigation("cv_documents")
                st.rerun()
        with a2:
            st.markdown(f"""
            <div class="wz-smart-card">
                <div class="wz-smart-label">Jobs</div>
                <div class="wz-smart-title">{html.escape(ui_label('Find Jobs'))}</div>
                <div class="wz-smart-copy">{html.escape(ui_label('Search global roles using your CV and selected country.'))}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(ui_label("Find Jobs"), key="wz_action_jobs", use_container_width=True):
                st.session_state["job_assist_mode_key"] = "find"
                queue_navigation("job_assist")
                st.rerun()
        with a3:
            st.markdown(f"""
            <div class="wz-smart-card">
                <div class="wz-smart-label">Application</div>
                <div class="wz-smart-title">{html.escape(ui_label('Cover Letter'))}</div>
                <div class="wz-smart-copy">{html.escape(ui_label('Generate a focused cover letter based on your CV and job description.'))}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(ui_label("Create Cover Letter"), key="wz_action_cover", use_container_width=True):
                st.session_state["document_tools_mode"] = "Cover Letter Generator + Language"
                queue_navigation("cv_documents")
                st.rerun()
        with a4:
            st.markdown(f"""
            <div class="wz-smart-card">
                <div class="wz-smart-label">Coach</div>
                <div class="wz-smart-title">Work-O-Bot</div>
                <div class="wz-smart-copy">{html.escape(ui_label('Practice answers, messages, German/English, and career communication.'))}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(ui_label("Practice"), key="wz_action_workobot", use_container_width=True):
                queue_navigation("workobot")
                st.rerun()

        st.markdown(f"### {html.escape(ui_label('Application flow'))}")
        f1, f2, f3, f4 = st.columns(4)
        flow = [
            (f1, ui_label("CV added"), cv_ready),
            (f2, ui_label("Job analyzed"), job_ready),
            (f3, ui_label("CV improved"), improved_ready),
            (f4, ui_label("Ready to apply"), prepared_ready),
        ]
        for col, label, done in flow:
            with col:
                st.markdown(f"""
                <div class="wz-step-pill {'done' if done else ''}">
                    <div class="wz-step-title">{'✅ ' if done else '⬜ '}{html.escape(str(label))}</div>
                    <div class="wz-step-state">{html.escape(ui_label('Completed') if done else ui_label('Pending'))}</div>
                </div>
                """, unsafe_allow_html=True)

        if company_context:
            st.info(ui_label("Company context is active. Cover letters and preparation can use the company website you added in the toolbox."))
        else:
            st.caption(ui_label("Tip: Add a company website in the left toolbox to make cover letters and preparation more company-specific."))


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
                        "Market Smart Guide",
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
                    st.markdown("#### Real Interview Simulation")
                    st.info("Use this after applying or when HR invites you for an interview. WorkZo will practice the exact interview using your CV and this job description.")
                    st.markdown(interview_text or "Prepare answers for role fit, technical skills, problem solving, communication, motivation, and country-specific expectations.")
                    if st.button("Start Real Interview Simulation", key="real_interview_setup_from_prepare", use_container_width=True):
                        st.session_state["real_interview_jd"] = st.session_state.get("last_prepare_job_description", job_desc_prepare)
                        st.session_state["real_interview_company"] = target_company or ""
                        st.session_state["prepare_interview_started"] = True
                        st.session_state["workobot_prefill"] = "Start Real Interview Simulation for my prepared job. Use my CV and the saved job description. Ask one question at a time and give specific feedback."
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
                st.caption("Recommended order: tailor your CV, create a cover letter, save the application, apply for the role, then start Work-O-Bot when HR responds.")
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
                    if st.button("Cover letter", key="prep_to_cover_letter", use_container_width=True):
                        st.session_state["cover_letter_job_desc"] = st.session_state.get("last_prepare_job_description", job_desc_prepare)
                        st.session_state["document_tools_mode"] = "Cover Letter Generator + Language"
                        queue_navigation("cv_documents")
                        st.rerun()
                with n3:
                    if st.button("Save tracker", key="save_prepared_job_to_tracker", use_container_width=True):
                        if "application_tracker" not in st.session_state:
                            st.session_state.application_tracker = []
                        title_guess = (target_job_title or "").strip() or "Prepared job"
                        if title_guess == "Prepared job":
                            m = re.search(r"(?i)(job title|role|position)[:\-]\s*(.+)", job_desc_prepare[:1000])
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
                    if st.button("Interview after HR reply", key="prep_to_real_interview_after_hr", use_container_width=True):
                        st.session_state["real_interview_jd"] = st.session_state.get("last_prepare_job_description", job_desc_prepare)
                        st.session_state["real_interview_company"] = target_company or ""
                        st.session_state["workobot_prefill"] = "Start Real Interview Simulation for my prepared job. Use my CV and the saved job description."
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

    elif page_key in ["workobot", "workobot", "career_insights"]:
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

# =========================================================
# WorkZo v15 dashboard score stabilizer
# =========================================================
def _wz15_restore_best_scores():
    try:
        import streamlit as st
        for key in ["cv_score_value", "ats_score_value", "application_readiness_value"]:
            best_key = "_best_" + key
            cur = int(st.session_state.get(key) or 0)
            best = int(st.session_state.get(best_key) or 0)
            if cur < best:
                st.session_state[key] = best
            else:
                st.session_state[best_key] = cur
    except Exception:
        pass
try:
    _wz15_old_show_dashboard = show_dashboard
    def show_dashboard():
        _wz15_restore_best_scores()
        result = _wz15_old_show_dashboard()
        _wz15_restore_best_scores()
        return result
except Exception:
    pass

# =========================================================
# WorkZo v19 - simplified product dashboard override
# Purpose: one clear dashboard purpose, 3 primary cards, stable scores,
# and cleaner sidebar navigation.
# =========================================================
def _wz19_int_score(*keys, default=0):
    try:
        for key in keys:
            val = st.session_state.get(key)
            if val is not None and str(val).strip() != "":
                return max(0, min(100, int(float(val))))
    except Exception:
        pass
    return default


def _wz19_preserve_best_scores():
    """Do not let Home/Dashboard navigation reduce already-computed scores."""
    try:
        for key in ["cv_score_value", "resume_score", "ats_score_value", "application_readiness_value", "interview_score"]:
            cur = _wz19_int_score(key, default=0)
            best_key = "_best_" + key
            best = _wz19_int_score(best_key, default=0)
            if cur < best:
                st.session_state[key] = best
            else:
                st.session_state[best_key] = cur
    except Exception:
        pass


def _wz19_go(page_key: str):
    """Navigation helper that keeps state stable and nudges Streamlit to start at top."""
    try:
        _wz19_preserve_best_scores()
        st.session_state["page"] = page_key
        st.session_state["nav_page"] = page_key
        st.session_state["scroll_anchor"] = "top"
        st.session_state["_wz_top_counter"] = int(st.session_state.get("_wz_top_counter", 0)) + 1
        try:
            st.query_params["page"] = page_key
            st.query_params["top"] = str(st.session_state["_wz_top_counter"])
        except Exception:
            pass
        st.rerun()
    except Exception:
        st.session_state["page"] = page_key
        st.session_state["nav_page"] = page_key
        st.rerun()


def _wz19_current_name():
    for key in ["user_name", "full_name", "candidate_name"]:
        value = str(st.session_state.get(key, "") or "").strip()
        if value:
            return value.split()[0]
    try:
        cv = st.session_state.get("structured_cv_json") or st.session_state.get("workzo_live_cv_structured") or {}
        name = str(cv.get("full_name") or cv.get("name") or "").strip()
        if name:
            return name.split()[0]
    except Exception:
        pass
    return "there"


def _wz19_render_sidebar(page_key: str):
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
                    <div class='workzo-sidebar-version'>Guided career workspace</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class='workzo-sidebar-brand-wrap'>
                <div class='workzo-sidebar-logo-fallback'>WZ</div>
                <div>
                    <div class='workzo-sidebar-brand'>WORKZO AI</div>
                    <div class='workzo-sidebar-version'>Guided career workspace</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div class='workzo-sidebar-section-label'>Navigation</div>", unsafe_allow_html=True)
        nav = [
            ("dashboard", "Dashboard"),
            ("cv_documents", "My CV"),
            ("job_assist", "Job Match"),
            ("workobot", "Work-O-Bot"),
        ]
        # Founder analytics hidden in v26.
        for key, label in nav:
            shown = label + ("  ✓" if page_key == key else "")
            if st.button(shown, key=f"wz19_sidebar_{key}", use_container_width=True):
                _wz19_go(key)

        st.markdown("<div class='workzo-sidebar-section-label'>Settings</div>", unsafe_allow_html=True)
        try:
            language_list = language_options if language_options else ["English", "German", "Dutch"]
            current_language = st.session_state.get("preferred_language", "English")
            if current_language not in language_list:
                current_language = "English" if "English" in language_list else language_list[0]
            preferred = st.selectbox(
                txt("preferred_language"),
                language_list,
                index=language_list.index(current_language),
                key="wz19_sidebar_preferred_language",
            )
            set_single_preferred_language(preferred)
        except Exception:
            pass

        if st.button("Edit setup", key="wz19_edit_setup", use_container_width=True):
            try:
                reset_onboarding()
            except Exception:
                st.session_state["onboarding_complete"] = False
            _wz19_go("onboarding")


def _wz19_recommendation(cv_score: int, ats_score: int, interview_score: int):
    if not str(st.session_state.get("cv_text", "") or "").strip():
        return "Upload or create your CV first so WorkZo can guide the next steps.", "Add My CV", "cv_documents"
    if ats_score < 60:
        return "Your CV needs stronger job alignment. Compare it with a job description and fix only truthful missing keywords.", "Fix CV Match", "cv_documents"
    if interview_score < 70:
        return "Your CV is improving. The next best step is Work-O-Bot based on your CV and the job description.", "Start Practice", "workobot"
    return "You look ready to apply. Find relevant roles and track the ones you apply for.", "Find Jobs", "job_assist"


def _wz19_dashboard_home():
    _wz19_preserve_best_scores()
    name = _wz19_current_name()
    cv_score = _wz19_int_score("cv_score_value", "resume_score", default=0)
    ats_score = _wz19_int_score("ats_score_value", default=0)
    interview_score = _wz19_int_score("interview_score", "interview_readiness", default=40)
    has_job = bool(str(st.session_state.get("last_understand_job_description", "") or st.session_state.get("improve_cv_for_job_desc", "") or st.session_state.get("last_prepare_job_description", "")).strip())

    st.markdown("<div id='top'></div>", unsafe_allow_html=True)
    st.markdown("""
    <style>
    .wz19-hero {border:1px solid rgba(148,163,184,.25); border-radius:22px; padding:28px; background:linear-gradient(135deg, rgba(99,102,241,.10), rgba(20,184,166,.08)); margin-bottom:22px;}
    .wz19-title {font-size:30px; font-weight:800; margin-bottom:4px; color:#f8fafc;}
    .wz19-sub {font-size:16px; color:#cbd5e1; margin-bottom:18px;}
    .wz19-card {border:1px solid rgba(148,163,184,.25); border-radius:18px; padding:20px; min-height:190px; background:rgba(15,23,42,.35);}
    .wz19-card h3 {margin-top:0; font-size:20px;}
    .wz19-card p {color:#cbd5e1; min-height:72px;}
    .wz19-reco {border:1px solid rgba(34,197,94,.30); border-radius:18px; padding:18px; background:rgba(34,197,94,.08); margin-top:10px;}
    .wz19-small-muted {color:#94a3b8; font-size:13px;}
    div[data-testid="stButton"] > button {border-radius:12px; font-weight:650; min-height:42px;}
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class='wz19-hero'>
      <div class='wz19-title'>👋 Welcome back, {html.escape(name)}</div>
      <div class='wz19-sub'>Let’s move you closer to your next job.</div>
    </div>
    """, unsafe_allow_html=True)

    m1, m2, m3 = st.columns(3)
    m1.metric("CV Strength", f"{cv_score}%" if cv_score else "Not analyzed")
    m2.metric("Job Match", f"{ats_score}%" if has_job or ats_score else "Not analyzed")
    m3.metric("Interview Readiness", f"{interview_score}%")
    st.progress(max(cv_score, ats_score, interview_score, 1) / 100)

    if st.button("Continue Your Journey", key="wz19_continue_journey", use_container_width=True):
        msg, label, target = _wz19_recommendation(cv_score, ats_score, interview_score)
        _wz19_go(target)

    st.divider()
    st.subheader("What do you need today?")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""<div class='wz19-card'><h3>🟦 Get More Interviews</h3><p>Analyze your CV against a job, improve ATS alignment, and fix missing keywords honestly.</p></div>""", unsafe_allow_html=True)
        if st.button("Improve My CV", key="wz19_improve_cv", use_container_width=True):
            st.session_state["cv_documents_mode"] = "improve_cv"
            _wz19_go("cv_documents")
    with c2:
        st.markdown("""<div class='wz19-card'><h3>🟩 Prepare for Interview</h3><p>Practice the exact interview using your CV and the job description, then improve your answers.</p></div>""", unsafe_allow_html=True)
        if st.button("Start Work-O-Bot", key="wz19_interview", use_container_width=True):
            st.session_state["workobot_mode"] = "real_interview_simulation"
            _wz21_go("workobot")
    with c3:
        st.markdown("""<div class='wz19-card'><h3>🟧 Find Relevant Jobs</h3><p>Find better-matched roles, review job fit, and save opportunities to your tracker.</p></div>""", unsafe_allow_html=True)
        if st.button("Find Jobs", key="wz19_find_jobs", use_container_width=True):
            _wz19_go("job_assist")

    st.divider()
    st.subheader("🔍 What WorkZo suggests for you")
    reco, btn, target = _wz19_recommendation(cv_score, ats_score, interview_score)
    st.markdown(f"<div class='wz19-reco'>{html.escape(reco)}</div>", unsafe_allow_html=True)
    if st.button(btn, key="wz19_reco_button", use_container_width=True):
        _wz19_go(target)

    st.divider()
    st.subheader("📊 Your progress")
    p1, p2 = st.columns(2)
    p1.write(f"CV Score: **{cv_score or 0} → Target: 85**")
    p2.write(f"Interview Readiness: **{interview_score or 0} → Target: 80**")
    last_cv = st.session_state.get("last_resume_score") or st.session_state.get("_last_cv_score_value")
    if last_cv:
        st.caption(f"Last CV score: {last_cv} • Now: {cv_score}")
    if st.button("Continue Improving", key="wz19_continue_improving", use_container_width=True):
        _wz19_go("cv_documents")


def show_dashboard():
    """WorkZo v19 simplified dashboard router.

    Keeps the dashboard focused on one purpose and routes deeper tools into their flows.
    """
    try:
        _wz19_preserve_best_scores()
    except Exception:
        pass
    page_key = st.session_state.get("nav_page", st.session_state.get("page", "dashboard")) or "dashboard"
    aliases = {"improve_cv": "cv_documents", "jobs": "job_assist", "interview": "workobot", "prepare_job": "job_assist"}
    page_key = aliases.get(page_key, page_key)
    if page_key in ["landing", "onboarding"]:
        page_key = "dashboard"
    st.session_state["page"] = page_key
    st.session_state["nav_page"] = page_key

    _wz19_render_sidebar(page_key)

    if page_key == "dashboard":
        _wz19_dashboard_home()
    elif page_key == "cv_documents":
        st.markdown("<div id='top'></div>", unsafe_allow_html=True)
        show_document_tools()
    elif page_key == "job_assist":
        st.markdown("<div id='top'></div>", unsafe_allow_html=True)
        # Reuse the original full Job Assist page from v18 to avoid breaking existing functionality.
        try:
            _wz15_old_show_dashboard()
        except Exception:
            st.error("Job Match page could not load. Please check the dashboard module.")
    elif page_key in ["workobot", "workobot", "career_insights"]:
        st.markdown("<div id='top'></div>", unsafe_allow_html=True)
        show_workobot()
    elif page_key == "founder_dashboard":
        st.markdown("<div id='top'></div>", unsafe_allow_html=True)
        if st.session_state.get("founder_unlocked"):
            render_founder_dashboard()
        else:
            st.warning("Founder access is locked.")
    else:
        _wz19_dashboard_home()

    try:
        _wz19_preserve_best_scores()
        render_feedback_collector(page_key)
        render_issue_reporter(page_key)
    except Exception:
        pass
    st.divider()
    st.caption("WORKZO AI • Beta • Guided career workspace")
    st.caption("⚠️ WorkZo AI is currently in Beta. Some results may not be perfect yet. Your feedback helps improve the tool.")

# =========================================================
# WorkZo v20 - simplified dashboard + standalone Job Match final override
# =========================================================
def _wz20_clean_text(value):
    try:
        text = str(value or "")
        for a, b in {"ðŸŽ¤":"", "ðŸ“‹":"", "ðŸ”´":"", "ðŸŸ¢":"", "Ã¢â‚¬â€œ":"-", "â€“":"-", "â€”":"-", "â€¢":"-", "Â":"", "�":""}.items():
            text = text.replace(a, b)
        return re.sub(r"\s+", " ", text).strip()
    except Exception:
        return str(value or "")

def _wz20_extract_keywords(text, limit=16):
    stop = set("the and for with from this that your you are will can have has about into role job our their they a an to in of on at as is be by or we us it do does did what who why how".split())
    words = re.findall(r"[A-Za-z][A-Za-z+#.-]{2,}", str(text or "").lower())
    out = []
    for word in words:
        if word not in stop and word not in out:
            out.append(word)
        if len(out) >= limit:
            break
    return out

def _wz20_job_match_score(cv_text, jd_text):
    cv = str(cv_text or "").lower()
    keywords = _wz20_extract_keywords(jd_text, 18)
    if not keywords:
        return 0, [], []
    matched = [k for k in keywords if k in cv]
    missing = [k for k in keywords if k not in cv]
    return int(round(100 * len(matched) / max(1, len(keywords)))), matched, missing

def _wz20_render_job_assist_page():
    st.markdown("<div id='top'></div>", unsafe_allow_html=True)
    st.markdown("## AI Job Application Assistant")
    st.caption("Paste a job description. WorkZo will prepare your CV focus, cover letter direction, interview plan, and market guidance.")

    c1, c2 = st.columns(2)
    with c1:
        target_company = st.text_input("Target company", value=st.session_state.get("target_company", ""), key="wz20_target_company")
    with c2:
        target_title = st.text_input("Target job title", value=st.session_state.get("target_job_title", ""), key="wz20_target_job_title")
    company_website = st.text_input("Company website / careers page (optional)", value=st.session_state.get("target_company_website", ""), key="wz20_company_website", help="Optional but recommended. WorkZo uses this to make CV advice, cover letters, and Work-O-Bot more company-specific.")

    default_jd = st.session_state.get("last_prepare_job_description") or st.session_state.get("last_understand_job_description") or st.session_state.get("improve_cv_for_job_desc") or ""
    jd = st.text_area("Paste the job description", value=default_jd, height=230, key="wz20_job_desc")
    cv_text = st.session_state.get("cv_text") or st.session_state.get("workzo_live_cv_text") or ""

    if not str(cv_text).strip():
        st.warning("Add your CV first so WorkZo can compare it with the job.")

    if st.button("Analyze job match", key="wz20_analyze_job_match", use_container_width=True):
        st.session_state["target_company"] = target_company
        st.session_state["target_job_title"] = target_title
        st.session_state["company_website"] = company_website
        st.session_state["company_context"] = _wz26_fetch_company_context(target_company, company_website)
        st.session_state["last_prepare_job_description"] = jd
        st.session_state["last_understand_job_description"] = jd
        st.session_state["improve_cv_for_job_desc"] = jd
        score, matched, missing = _wz20_job_match_score(cv_text, jd)
        st.session_state["ats_score_value"] = score
        st.session_state["latest_job_analysis"] = {"score": score, "matched": matched, "missing": missing, "company": target_company, "title": target_title, "company_website": company_website, "company_context": st.session_state.get("company_context", "")}
        try:
            _wz19_preserve_best_scores()
        except Exception:
            pass
        st.success("Job match analyzed. Review the guidance below.")

    analysis = st.session_state.get("latest_job_analysis") or {}
    score = int(analysis.get("score") or st.session_state.get("ats_score_value") or 0)
    matched = analysis.get("matched") or []
    missing = analysis.get("missing") or []

    if jd:
        st.divider()
        st.subheader("Job Match Summary")
        m1, m2, m3 = st.columns(3)
        m1.metric("Job Match", f"{score}%" if score else "Run analysis")
        m2.metric("Matched keywords", len(matched))
        m3.metric("Missing keywords", len(missing))
        if analysis.get("company_context"):
            st.caption("Company context is saved and reused for CV tailoring, cover letters, and Work-O-Bot.")

        if score and score < 75:
            st.warning("Your match is not yet strong. Improve the CV only with truthful keywords and examples from your real experience.")
            st.markdown("**Missing keywords to consider if true:** " + (", ".join(_wz20_clean_text(x) for x in missing[:10]) or "No clear missing keywords found."))
            st.markdown("""
**How to improve it honestly:**
- Add missing tools or skills only if you can explain them in an interview.
- Rewrite 2-3 bullet points to mirror the job language.
- Add measurable support, customer, or project examples where possible.
- Do not invent metrics, tools, or responsibilities.
""")
        elif score:
            st.success("Good match. Next step: tailor the CV and prepare a short interview story for this role.")

        st.subheader("Next best actions")
        a, b, c = st.columns(3)
        with a:
            if st.button("Improve CV for this job", key="wz20_go_improve_cv", use_container_width=True):
                st.session_state["cv_documents_mode"] = "improve_cv"
                _wz19_go("cv_documents")
        with b:
            if st.button("Create cover letter", key="wz20_go_cover", use_container_width=True):
                st.session_state["cv_documents_mode"] = "cover_letter"
                st.session_state["cover_letter_job_desc"] = jd
                st.session_state["target_company"] = target_company
                st.session_state["company_website"] = company_website
                st.session_state["company_context"] = _wz26_fetch_company_context(target_company, company_website)
                _wz19_go("cv_documents")
        with c:
            if st.button("Practice interview", key="wz20_go_interview", use_container_width=True):
                st.session_state["workobot_mode"] = "real_interview_simulation"
                st.session_state["real_interview_jd"] = jd
                st.session_state["real_interview_company"] = target_company
                st.session_state["company_website"] = company_website
                st.session_state["company_context"] = _wz26_fetch_company_context(target_company, company_website)
                _wz21_go("workobot")

        with st.expander("Market Smart Guide", expanded=False):
            country = st.session_state.get("country") or st.session_state.get("target_country") or "your target market"
            st.write(f"WorkZo adapts CV wording, interview preparation, and job advice for **{country}** when country information is available.")

def show_dashboard():
    """WorkZo v20 final dashboard router: no duplicate sidebar, standalone Job Match."""
    try:
        _wz19_preserve_best_scores()
    except Exception:
        pass
    page_key = st.session_state.get("nav_page", st.session_state.get("page", "dashboard")) or "dashboard"
    if page_key in ["landing", "onboarding"]:
        page_key = "dashboard"
    st.session_state["page"] = page_key
    st.session_state["nav_page"] = page_key

    _wz19_render_sidebar(page_key)

    if page_key == "dashboard":
        _wz19_dashboard_home()
    elif page_key == "cv_documents":
        st.markdown("<div id='top'></div>", unsafe_allow_html=True)
        show_document_tools()
    elif page_key == "job_assist":
        _wz20_render_job_assist_page()
    elif page_key in ["workobot", "workobot", "career_insights"]:
        st.markdown("<div id='top'></div>", unsafe_allow_html=True)
        show_workobot()
    elif page_key == "founder_dashboard":
        st.markdown("<div id='top'></div>", unsafe_allow_html=True)
        if st.session_state.get("founder_unlocked"):
            render_founder_dashboard()
        else:
            st.warning("Founder access is locked.")
    else:
        _wz19_dashboard_home()

    try:
        _wz19_preserve_best_scores()
        render_feedback_collector(page_key)
        render_issue_reporter(page_key)
    except Exception:
        pass
    st.divider()
    st.caption("WORKZO AI • Beta • Guided career workspace")

# =========================================================
# WorkZo v21 - visible Work-O-Bot + clean sidebar final override
# =========================================================
def _wz21_go(page_key: str):
    """Single reliable navigation helper.

    Earlier builds changed only session_state. On the next rerun the router
    re-read the old ?page= query parameter and sent the user back, which made
    every navigation button feel broken. This updates both session_state and
    URL state before rerun.
    """
    aliases = {
        "improve_cv": "cv_documents",
        "jobs": "job_assist",
        "interview": "workobot",
        "prepare_job": "job_assist",
    }
    page_key = aliases.get(page_key, page_key)
    st.session_state["page"] = page_key
    st.session_state["nav_page"] = page_key
    st.session_state["scroll_to_top_next"] = True
    st.session_state["_workzo_scroll_to_top"] = True
    try:
        st.query_params["page"] = page_key
        st.query_params["wz_top"] = str(st.session_state.get("nav_change_nonce", 0) + 1)
    except Exception:
        pass
    st.rerun()


def _wz21_render_sidebar(page_key: str):
    """Clean final sidebar: no duplicate settings/profile blocks."""
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
                    <div class='workzo-sidebar-version'>Guided career workspace</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("### WorkZo AI")

        st.markdown("<div class='workzo-sidebar-section-label'>Navigation</div>", unsafe_allow_html=True)
        nav = [
            ("dashboard", "Dashboard"),
            ("cv_documents", "My CV"),
            ("job_assist", "Job Match"),
            ("workobot", "Work-O-Bot"),
            ("workobot", "Work-O-Bot"),
        ]
        # Founder analytics hidden in v26.
        for key, label in nav:
            if st.button(label + ("  ✓" if page_key == key else ""), key=f"wz21_sidebar_{key}", use_container_width=True):
                _wz21_go(key)

        st.markdown("<div class='workzo-sidebar-section-label'>Profile</div>", unsafe_allow_html=True)
        st.caption(f"Country: {st.session_state.get('country') or st.session_state.get('target_country') or 'Not set'}")
        st.caption("Resume uploaded" if str(st.session_state.get("cv_text", "")).strip() else "CV missing")

        st.markdown("<div class='workzo-sidebar-section-label'>Settings</div>", unsafe_allow_html=True)
        try:
            language_list = language_options if language_options else ["English", "German", "Dutch"]
            current_language = st.session_state.get("preferred_language", "English")
            if current_language not in language_list:
                current_language = "English" if "English" in language_list else language_list[0]
            preferred = st.selectbox(
                "Language",
                language_list,
                index=language_list.index(current_language),
                key="wz21_sidebar_preferred_language",
            )
            set_single_preferred_language(preferred)
        except Exception:
            pass

        if st.button("Edit setup", key="wz21_edit_setup", use_container_width=True):
            try:
                reset_onboarding()
            except Exception:
                st.session_state["onboarding_complete"] = False
            _wz21_go("onboarding")


def _wz21_render_interview_practice_page():
    """Make speaking/Work-O-Bot discoverable as its own page."""
    st.markdown("<div id='top'></div>", unsafe_allow_html=True)
    st.markdown("## 🎤 Real Interview Simulation")
    st.caption("Practice the exact interview for the job you are applying to — using your CV and the job description.")
    st.info("Use this after applying or when HR invites you for an interview. WorkZo asks tailored questions and gives specific feedback so you can improve and try again.")
    if "render_real_interview_simulation" in globals():
        render_real_interview_simulation()
    elif "show_workobot" in globals():
        st.warning("Interview simulator could not be opened directly, so WorkZo opened the coaching assistant instead.")
        show_workobot()
    else:
        st.error("Interview practice is not available yet. Please check 09_interview_assistant.py is loaded.")


def show_dashboard():
    """WorkZo v21 final dashboard router: clean sidebar + visible Work-O-Bot."""
    try:
        _wz19_preserve_best_scores()
    except Exception:
        pass
    page_key = st.session_state.get("nav_page", st.session_state.get("page", "dashboard")) or "dashboard"
    if page_key in ["landing", "onboarding"]:
        page_key = "dashboard"
    st.session_state["page"] = page_key
    st.session_state["nav_page"] = page_key

    _wz21_render_sidebar(page_key)

    if page_key == "dashboard":
        _wz19_dashboard_home()
    elif page_key == "cv_documents":
        st.markdown("<div id='top'></div>", unsafe_allow_html=True)
        show_document_tools()
    elif page_key == "job_assist":
        _wz20_render_job_assist_page()
    elif page_key == "workobot":
        _wz21_render_interview_practice_page()
    elif page_key == "workobot":
        st.markdown("<div id='top'></div>", unsafe_allow_html=True)
        show_workobot()
    elif page_key == "founder_dashboard":
        st.markdown("<div id='top'></div>", unsafe_allow_html=True)
        if st.session_state.get("founder_unlocked"):
            render_founder_dashboard()
        else:
            st.warning("Founder access is locked.")
    else:
        _wz19_dashboard_home()

    try:
        _wz19_preserve_best_scores()
        render_feedback_collector(page_key)
        render_issue_reporter(page_key)
    except Exception:
        pass
    st.divider()
    st.caption("WORKZO AI • Beta • Guided career workspace")


# =========================================================
# WorkZo v24 - separate Work-O-Bot and Work-O-Bot final override
# =========================================================
def _wz24_render_sidebar(page_key: str):
    """Final sidebar: Work-O-Bot and Work-O-Bot are separate features."""
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
                    <div class='workzo-sidebar-version'>Guided career workspace</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("### WorkZo AI")

        st.markdown("<div class='workzo-sidebar-section-label'>Navigation</div>", unsafe_allow_html=True)
        nav = [
            ("dashboard", "Dashboard"),
            ("cv_documents", "My CV"),
            ("job_assist", "Job Match"),
            ("workobot", "Work-O-Bot"),
            ("workobot", "Work-O-Bot"),
        ]
        # Founder analytics hidden in v26.
        for key, label in nav:
            if st.button(label + ("  ✓" if page_key == key else ""), key=f"wz24_sidebar_{key}", use_container_width=True):
                _wz21_go(key)

        st.markdown("<div class='workzo-sidebar-section-label'>Profile</div>", unsafe_allow_html=True)
        st.caption(f"Country: {st.session_state.get('country') or st.session_state.get('target_country') or 'Not set'}")
        st.caption("Resume uploaded" if str(st.session_state.get("cv_text", "")).strip() else "CV missing")

        st.markdown("<div class='workzo-sidebar-section-label'>Settings</div>", unsafe_allow_html=True)
        try:
            language_list = language_options if language_options else ["English", "German", "Dutch"]
            current_language = st.session_state.get("preferred_language", "English")
            if current_language not in language_list:
                current_language = "English" if "English" in language_list else language_list[0]
            preferred = st.selectbox("Language", language_list, index=language_list.index(current_language), key="wz24_sidebar_preferred_language")
            set_single_preferred_language(preferred)
        except Exception:
            pass

        if st.button("Edit setup", key="wz24_edit_setup", use_container_width=True):
            try:
                reset_onboarding()
            except Exception:
                st.session_state["onboarding_complete"] = False
            _wz21_go("onboarding")


def _wz24_render_workobot_page():
    """Standalone typed career assistant. Interview simulation stays on Work-O-Bot page."""
    st.markdown("<div id='top'></div>", unsafe_allow_html=True)
    st.markdown("## 🤖 Work-O-Bot")
    st.caption("Ask career questions, CV doubts, job-search questions, HR messages, or language-practice questions. For mock interviews, use Work-O-Bot.")
    try:
        show_workobot()
    except Exception as exc:
        st.error("Work-O-Bot could not load.")
        st.exception(exc)


def _wz24_dashboard_home():
    _wz19_preserve_best_scores()
    name = _wz19_current_name()
    cv_score = _wz19_int_score("cv_score_value", "resume_score", default=0)
    ats_score = _wz19_int_score("ats_score_value", default=0)
    interview_score = _wz19_int_score("interview_score", "interview_readiness", default=40)
    has_job = bool(str(st.session_state.get("last_understand_job_description", "") or st.session_state.get("improve_cv_for_job_desc", "") or st.session_state.get("last_prepare_job_description", "")).strip())

    st.markdown("<div id='top'></div>", unsafe_allow_html=True)
    st.markdown("""
    <style>
    .wz19-hero {border:1px solid rgba(148,163,184,.25); border-radius:22px; padding:28px; background:linear-gradient(135deg, rgba(99,102,241,.10), rgba(20,184,166,.08)); margin-bottom:22px;}
    .wz19-title {font-size:30px; font-weight:800; margin-bottom:4px; color:#f8fafc;}
    .wz19-sub {font-size:16px; color:#cbd5e1; margin-bottom:18px;}
    .wz19-card {border:1px solid rgba(148,163,184,.25); border-radius:18px; padding:20px; min-height:190px; background:rgba(15,23,42,.35);}
    .wz19-card h3 {margin-top:0; font-size:20px;}
    .wz19-card p {color:#cbd5e1; min-height:72px;}
    .wz19-reco {border:1px solid rgba(34,197,94,.30); border-radius:18px; padding:18px; background:rgba(34,197,94,.08); margin-top:10px;}
    div[data-testid="stButton"] > button {border-radius:12px; font-weight:650; min-height:42px;}
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class='wz19-hero'>
      <div class='wz19-title'>👋 Welcome back, {html.escape(name)}</div>
      <div class='wz19-sub'>Let’s move you closer to your next job.</div>
    </div>
    """, unsafe_allow_html=True)

    m1, m2, m3 = st.columns(3)
    m1.metric("CV Strength", f"{cv_score}%" if cv_score else "Not analyzed")
    m2.metric("Job Match", f"{ats_score}%" if has_job or ats_score else "Not analyzed")
    m3.metric("Interview Readiness", f"{interview_score}%")
    st.progress(max(cv_score, ats_score, interview_score, 1) / 100)

    if st.button("Continue Your Journey", key="wz24_continue_journey", use_container_width=True):
        _, _, target = _wz19_recommendation(cv_score, ats_score, interview_score)
        _wz21_go(target)

    st.divider()
    st.subheader("What do you need today?")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""<div class='wz19-card'><h3>🟦 Get More Interviews</h3><p>Analyze your CV against a job, improve ATS alignment, and fix missing keywords honestly.</p></div>""", unsafe_allow_html=True)
        if st.button("Improve My CV", key="wz24_improve_cv", use_container_width=True):
            st.session_state["cv_documents_mode"] = "improve_cv"
            _wz21_go("cv_documents")
    with c2:
        st.markdown("""<div class='wz19-card'><h3>🟩 Prepare for Interview</h3><p>Practice the exact interview using your CV and the job description, then improve your answers.</p></div>""", unsafe_allow_html=True)
        if st.button("Start Work-O-Bot", key="wz24_interview", use_container_width=True):
            _wz21_go("workobot")
    with c3:
        st.markdown("""<div class='wz19-card'><h3>🟧 Find Relevant Jobs</h3><p>Find better-matched roles, review job fit, and save opportunities to your tracker.</p></div>""", unsafe_allow_html=True)
        if st.button("Find Jobs", key="wz24_find_jobs", use_container_width=True):
            _wz21_go("job_assist")

    st.divider()
    st.subheader("🔍 What WorkZo suggests for you")
    reco, btn, target = _wz19_recommendation(cv_score, ats_score, interview_score)
    st.markdown(f"<div class='wz19-reco'>{html.escape(reco)}</div>", unsafe_allow_html=True)
    if st.button(btn, key="wz24_reco_button", use_container_width=True):
        _wz21_go(target)

    st.divider()
    help_col, bot_col = st.columns([2, 1])
    with help_col:
        st.subheader("Need help or have a question?")
        st.caption("Use Work-O-Bot for general career questions, HR messages, CV doubts, job-search advice, or language practice.")
    with bot_col:
        if st.button("Ask Work-O-Bot", key="wz24_ask_workobot", use_container_width=True):
            _wz21_go("workobot")


def show_dashboard():
    """WorkZo v24 final router: Work-O-Bot and Work-O-Bot are separate."""
    try:
        _wz19_preserve_best_scores()
    except Exception:
        pass
    page_key = st.session_state.get("nav_page", st.session_state.get("page", "dashboard")) or "dashboard"
    aliases = {"improve_cv": "cv_documents", "jobs": "job_assist", "interview": "workobot", "prepare_job": "job_assist"}
    page_key = aliases.get(page_key, page_key)
    if page_key in ["landing", "onboarding"]:
        page_key = "dashboard"
    st.session_state["page"] = page_key
    st.session_state["nav_page"] = page_key

    _wz24_render_sidebar(page_key)

    if page_key == "dashboard":
        _wz24_dashboard_home()
    elif page_key == "cv_documents":
        st.markdown("<div id='top'></div>", unsafe_allow_html=True)
        show_document_tools()
    elif page_key == "job_assist":
        _wz20_render_job_assist_page()
    elif page_key == "workobot":
        _wz21_render_interview_practice_page()
    elif page_key == "workobot":
        _wz24_render_workobot_page()
    elif page_key == "founder_dashboard":
        st.markdown("<div id='top'></div>", unsafe_allow_html=True)
        if st.session_state.get("founder_unlocked"):
            render_founder_dashboard()
        else:
            st.warning("Founder access is locked.")
    else:
        _wz24_dashboard_home()

    try:
        _wz19_preserve_best_scores()
        render_feedback_collector(page_key)
        render_issue_reporter(page_key)
    except Exception:
        pass
    st.divider()
    st.caption("WORKZO AI • Beta • Guided career workspace")



# =========================================================
# WorkZo v26 - company context helper + founder analytics hidden
# =========================================================
def _wz26_fetch_company_context(company_name: str = "", company_website: str = "") -> str:
    company_name = str(company_name or "").strip()
    company_website = str(company_website or "").strip()
    cached_key = f"_wz26_company_context::{company_name}::{company_website}"
    if cached_key in st.session_state:
        return st.session_state.get(cached_key, "")
    context = ""
    if company_website:
        url = company_website if company_website.startswith(("http://", "https://")) else "https://" + company_website
        try:
            import requests, re as _re
            r = requests.get(url, timeout=3, headers={"User-Agent": "WorkZoAI/1.0"})
            if r.ok:
                txt0 = _re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", " ", r.text, flags=_re.I)
                txt0 = _re.sub(r"<[^>]+>", " ", txt0)
                txt0 = _re.sub(r"\s+", " ", txt0).strip()
                context = txt0[:1800]
        except Exception:
            context = ""
    if not context and company_name:
        context = f"Company name provided by user: {company_name}. If public company details are not known, avoid inventing facts and ask the user to paste company details."
    st.session_state[cached_key] = context
    return context

# =========================================================
# WorkZo v25 - navigation top fix + faster dashboard + Work-O-Bot visible
# =========================================================
def _wz25_scroll_to_top_if_needed(force: bool = False):
    """Scroll to top only after navigation; avoids running script on every rerun."""
    try:
        should_scroll = force or bool(st.session_state.pop("_workzo_scroll_to_top", False)) or bool(st.session_state.pop("scroll_to_top_next", False))
        if not should_scroll:
            return
        script = """
        <script>
        const scrollTop = () => {
          try { window.parent.scrollTo({top: 0, left: 0, behavior: 'instant'}); } catch(e) {}
          try { window.parent.document.querySelector('[data-testid="stAppViewContainer"]').scrollTo({top:0,left:0,behavior:'instant'}); } catch(e) {}
          try { window.parent.document.querySelector('section.main').scrollTo({top:0,left:0,behavior:'instant'}); } catch(e) {}
          try { window.parent.document.querySelector('.main').scrollTo({top:0,left:0,behavior:'instant'}); } catch(e) {}
        };
        scrollTop(); setTimeout(scrollTop, 50); setTimeout(scrollTop, 200);
        </script>
        """
        if hasattr(st, "iframe"):
            st.iframe(srcdoc=script, height=0, width=0)
        else:
            import streamlit.components.v1 as components
            components.html(script, height=0, width=0)
    except Exception:
        pass


def _wz25_go(page_key: str):
    aliases = {
        "improve_cv": "cv_documents",
        "jobs": "job_assist",
        "interview": "workobot",
        "prepare_job": "job_assist",
        "bot": "workobot",
        "work-o-bot": "workobot",
    }
    page_key = aliases.get(page_key, page_key)
    st.session_state["page"] = page_key
    st.session_state["nav_page"] = page_key
    st.session_state["_workzo_scroll_to_top"] = True
    st.session_state["scroll_to_top_next"] = True
    try:
        st.session_state["nav_change_nonce"] = int(st.session_state.get("nav_change_nonce", 0)) + 1
    except Exception:
        st.session_state["nav_change_nonce"] = 1
    try:
        st.query_params["page"] = page_key
        st.query_params["wz_top"] = str(st.session_state.get("nav_change_nonce", 1))
    except Exception:
        pass
    st.rerun()

# Override older helpers so old buttons also use reliable navigation.
_wz21_go = _wz25_go
_wz19_go = _wz25_go
go_to_nav = _wz25_go


def _wz25_render_sidebar(page_key: str):
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
                    <div class='workzo-sidebar-version'>Guided career workspace</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("### WorkZo AI")

        st.markdown("<div class='workzo-sidebar-section-label'>Navigation</div>", unsafe_allow_html=True)
        nav = [
            ("dashboard", "Dashboard"),
            ("cv_documents", "My CV"),
            ("job_assist", "Job Match"),
            ("workobot", "Work-O-Bot"),
            ("workobot", "Work-O-Bot"),
        ]
        # Founder analytics hidden in v26.
        for key, label in nav:
            if st.button(label + (" ✓" if page_key == key else ""), key=f"wz25_sidebar_{key}", use_container_width=True):
                _wz25_go(key)

        st.markdown("<div class='workzo-sidebar-section-label'>Profile</div>", unsafe_allow_html=True)
        st.caption(f"Country: {st.session_state.get('country') or st.session_state.get('target_country') or 'Not set'}")
        st.caption("Resume uploaded" if str(st.session_state.get("cv_text", "")).strip() else "CV missing")

        st.markdown("<div class='workzo-sidebar-section-label'>Settings</div>", unsafe_allow_html=True)
        try:
            language_list = language_options if language_options else ["English", "German", "Dutch"]
            current_language = st.session_state.get("preferred_language", "English")
            if current_language not in language_list:
                current_language = "English" if "English" in language_list else language_list[0]
            preferred = st.selectbox("Language", language_list, index=language_list.index(current_language), key="wz25_sidebar_preferred_language")
            set_single_preferred_language(preferred)
        except Exception:
            pass

        if st.button("Edit setup", key="wz25_edit_setup", use_container_width=True):
            try:
                reset_onboarding()
            except Exception:
                st.session_state["onboarding_complete"] = False
            _wz25_go("onboarding")


def _wz25_dashboard_home():
    _wz19_preserve_best_scores()
    name = _wz19_current_name()
    cv_score = _wz19_int_score("cv_score_value", "resume_score", default=0)
    ats_score = _wz19_int_score("ats_score_value", default=0)
    interview_score = _wz19_int_score("interview_score", "interview_readiness", default=40)
    has_job = bool(str(st.session_state.get("last_understand_job_description", "") or st.session_state.get("improve_cv_for_job_desc", "") or st.session_state.get("last_prepare_job_description", "")).strip())

    st.markdown("<div id='workzo-page-top'></div>", unsafe_allow_html=True)
    st.markdown("""
    <style>
    .wz25-hero {border:1px solid rgba(148,163,184,.25); border-radius:22px; padding:28px; background:linear-gradient(135deg, rgba(99,102,241,.10), rgba(20,184,166,.08)); margin-bottom:22px;}
    .wz25-title {font-size:30px; font-weight:800; margin-bottom:4px; color:#f8fafc;}
    .wz25-sub {font-size:16px; color:#cbd5e1; margin-bottom:0;}
    .wz25-card {border:1px solid rgba(148,163,184,.25); border-radius:18px; padding:20px; min-height:190px; background:rgba(15,23,42,.35);}
    .wz25-card h3 {margin-top:0; font-size:20px;}
    .wz25-card p {color:#cbd5e1; min-height:72px;}
    .wz25-reco {border:1px solid rgba(34,197,94,.30); border-radius:18px; padding:18px; background:rgba(34,197,94,.08); margin-top:10px;}
    div[data-testid="stButton"] > button {border-radius:12px; font-weight:650; min-height:42px;}
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class='wz25-hero'>
      <div class='wz25-title'>👋 Welcome back, {html.escape(name)}</div>
      <div class='wz25-sub'>Let’s move you closer to your next job.</div>
    </div>
    """, unsafe_allow_html=True)

    m1, m2, m3 = st.columns(3)
    m1.metric("CV Strength", f"{cv_score}%" if cv_score else "Not analyzed")
    m2.metric("Job Match", f"{ats_score}%" if has_job or ats_score else "Not analyzed")
    m3.metric("Interview Readiness", f"{interview_score}%")
    st.caption("Progress updates after you improve your CV, analyze a job, or complete Work-O-Bot.")

    if st.button("Continue Your Journey", key="wz25_continue_journey", use_container_width=False):
        _, _, target = _wz19_recommendation(cv_score, ats_score, interview_score)
        _wz25_go(target)

    st.divider()
    st.subheader("What do you need today?")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""<div class='wz25-card'><h3>🟦 Get More Interviews</h3><p>Analyze your CV against a job, improve ATS alignment, and fix missing keywords honestly.</p></div>""", unsafe_allow_html=True)
        if st.button("Improve My CV", key="wz25_improve_cv", use_container_width=True):
            st.session_state["cv_documents_mode"] = "improve_cv"
            _wz25_go("cv_documents")
    with c2:
        st.markdown("""<div class='wz25-card'><h3>🟩 Prepare for Interview</h3><p>Practice the exact interview using your CV and the job description, then improve your answers.</p></div>""", unsafe_allow_html=True)
        if st.button("Start Work-O-Bot", key="wz25_interview", use_container_width=True):
            _wz25_go("workobot")
    with c3:
        st.markdown("""<div class='wz25-card'><h3>🟧 Find Relevant Jobs</h3><p>Find better-matched roles, review job fit, and save opportunities to your tracker.</p></div>""", unsafe_allow_html=True)
        if st.button("Find Jobs", key="wz25_find_jobs", use_container_width=True):
            _wz25_go("job_assist")

    st.divider()
    st.subheader("🔍 What WorkZo suggests for you")
    reco, btn, target = _wz19_recommendation(cv_score, ats_score, interview_score)
    st.markdown(f"<div class='wz25-reco'>{html.escape(reco)}</div>", unsafe_allow_html=True)
    if st.button(btn, key="wz25_reco_button", use_container_width=True):
        _wz25_go(target)

    st.divider()
    help_col, bot_col = st.columns([2, 1])
    with help_col:
        st.subheader("Need help or have a question?")
        st.caption("Use Work-O-Bot for typed career questions, HR messages, CV doubts, job-search advice, or language practice.")
    with bot_col:
        if st.button("Ask Work-O-Bot", key="wz25_ask_workobot", use_container_width=True):
            _wz25_go("workobot")


def _wz25_render_workobot_page():
    st.markdown("<div id='workzo-page-top'></div>", unsafe_allow_html=True)
    st.markdown("## 🤖 Work-O-Bot")
    st.caption("Typed career assistant for CV doubts, job-search questions, HR messages, and language practice. Use Work-O-Bot for mock interviews.")
    try:
        show_workobot()
    except Exception as exc:
        st.error("Work-O-Bot could not load.")
        st.exception(exc)


def show_dashboard():
    try:
        _wz19_preserve_best_scores()
    except Exception:
        pass
    page_key = st.session_state.get("nav_page", st.session_state.get("page", "dashboard")) or "dashboard"
    aliases = {"improve_cv": "cv_documents", "jobs": "job_assist", "interview": "workobot", "prepare_job": "job_assist", "bot": "workobot"}
    page_key = aliases.get(page_key, page_key)
    if page_key in ["landing", "onboarding"]:
        page_key = "dashboard"
    st.session_state["page"] = page_key
    st.session_state["nav_page"] = page_key

    _wz25_scroll_to_top_if_needed()
    _wz25_render_sidebar(page_key)

    if page_key == "dashboard":
        _wz25_dashboard_home()
    elif page_key == "cv_documents":
        st.markdown("<div id='workzo-page-top'></div>", unsafe_allow_html=True)
        show_document_tools()
    elif page_key == "job_assist":
        st.markdown("<div id='workzo-page-top'></div>", unsafe_allow_html=True)
        _wz20_render_job_assist_page()
    elif page_key == "workobot":
        st.markdown("<div id='workzo-page-top'></div>", unsafe_allow_html=True)
        _wz21_render_interview_practice_page()
    elif page_key == "workobot":
        _wz25_render_workobot_page()
    elif page_key == "founder_dashboard":
        _wz25_dashboard_home()
    else:
        _wz25_dashboard_home()

    try:
        _wz19_preserve_best_scores()
        render_feedback_collector(page_key)
        render_issue_reporter(page_key)
    except Exception:
        pass
    st.divider()
    st.caption("WORKZO AI • Beta • Guided career workspace")


# =========================================================
# WorkZo v27 - FINAL lightweight dashboard/sidebar/navigation override
# =========================================================
def _wz27_force_top():
    try:
        st.markdown("<div id='workzo-page-top'></div>", unsafe_allow_html=True)
        script = """
        <script>
        function wzTop(){
          try { window.parent.scrollTo(0,0); } catch(e) {}
          try { window.parent.document.documentElement.scrollTop = 0; } catch(e) {}
          try { window.parent.document.body.scrollTop = 0; } catch(e) {}
          try { window.parent.document.querySelector('[data-testid="stAppViewContainer"]').scrollTop = 0; } catch(e) {}
          try { window.parent.document.querySelector('section.main').scrollTop = 0; } catch(e) {}
          try { window.parent.document.querySelector('.main').scrollTop = 0; } catch(e) {}
          try { window.parent.document.getElementById('workzo-page-top').scrollIntoView({block:'start', behavior:'instant'}); } catch(e) {}
        }
        wzTop(); setTimeout(wzTop, 30); setTimeout(wzTop, 120); setTimeout(wzTop, 300);
        </script>
        """
        iframe_fn = getattr(st, 'iframe', None)
        if iframe_fn:
            iframe_fn(srcdoc=script, height=0, width=0)
        else:
            try:
                import streamlit.components.v1 as components
                components.html(script, height=0, width=0)
            except Exception:
                pass
    except Exception:
        pass


def _wz27_go(page_key: str):
    aliases = {
        'home': 'dashboard', 'improve_cv': 'cv_documents', 'my_cv': 'cv_documents',
        'jobs': 'job_assist', 'job_match': 'job_assist', 'prepare_job': 'job_assist',
        'interview': 'workobot', 'bot': 'workobot', 'work-o-bot': 'workobot',
        'founder_dashboard': 'dashboard',
    }
    page_key = aliases.get(str(page_key or 'dashboard'), str(page_key or 'dashboard'))
    st.session_state['page'] = page_key
    st.session_state['nav_page'] = page_key
    st.session_state['_workzo_scroll_to_top'] = True
    try:
        n = int(st.session_state.get('nav_change_nonce', 0)) + 1
        st.session_state['nav_change_nonce'] = n
        st.query_params['page'] = page_key
        st.query_params['top'] = str(n)
    except Exception:
        pass
    st.rerun()

_wz25_go = _wz27_go
_wz24_go = _wz27_go
_wz21_go = _wz27_go
_wz19_go = _wz27_go
go_to_nav = _wz27_go


def _wz27_score(*keys, default=0):
    for k in keys:
        try:
            v = st.session_state.get(k)
            if v is not None and str(v).strip() != '':
                return max(0, min(100, int(float(v))))
        except Exception:
            pass
    return default


def _wz27_sidebar(page_key: str):
    with st.sidebar:
        try:
            logo_src = image_to_data_uri(ICON_PATH) or image_to_data_uri(LOGO_PATH)
        except Exception:
            logo_src = None
        if logo_src:
            st.markdown(f"""
            <div style='border:1px solid rgba(20,184,166,.35);border-radius:18px;padding:16px;margin-bottom:16px;background:rgba(15,23,42,.65)'>
                <img src='{logo_src}' style='width:44px;height:44px;border-radius:12px;margin-bottom:10px;'>
                <div style='font-weight:800;font-size:20px;letter-spacing:.04em'>WORKZO AI</div>
                <div style='font-size:12px;color:#94a3b8'>Guided career workspace</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown('### WorkZo AI')
        st.markdown('##### Navigation')
        nav = [('dashboard','Dashboard'),('cv_documents','My CV'),('job_assist','Job Match'),('workobot','Work-O-Bot')]
        for key, label in nav:
            marker = ' ✓' if page_key == key else ''
            if st.button(label + marker, key=f'wz27_nav_{key}', use_container_width=True):
                _wz27_go(key)
        st.markdown('##### Profile')
        st.caption(f"Country: {st.session_state.get('country') or st.session_state.get('target_country') or 'Not set'}")
        st.caption('Resume uploaded' if str(st.session_state.get('cv_text','')).strip() else 'CV missing')
        st.markdown('##### Settings')
        try:
            language_list = language_options if language_options else ['English', 'German', 'Dutch']
            current = st.session_state.get('preferred_language', 'English')
            if current not in language_list:
                current = 'English' if 'English' in language_list else language_list[0]
            chosen = st.selectbox('Language', language_list, index=language_list.index(current), key='wz27_language')
            set_single_preferred_language(chosen)
        except Exception:
            pass
        if st.button('Edit setup', key='wz27_edit_setup', use_container_width=True):
            try:
                reset_onboarding()
            except Exception:
                st.session_state['onboarding_complete'] = False
            _wz27_go('onboarding')


def _wz27_dashboard_home():
    cv_score = _wz27_score('cv_score_value','resume_score', default=75 if str(st.session_state.get('cv_text','')).strip() else 0)
    has_job_text = str(st.session_state.get('current_job_description','') or st.session_state.get('last_understand_job_description','') or st.session_state.get('improve_cv_for_job_desc','')).strip()
    ats_score = _wz27_score('ats_score_value','job_match_score', default=70 if has_job_text else 0)
    interview_score = _wz27_score('interview_score','interview_readiness', default=40)
    name = st.session_state.get('user_name') or st.session_state.get('candidate_name') or 'there'
    st.markdown("""
    <style>
      .wz27-hero{border:1px solid rgba(148,163,184,.22);border-radius:24px;padding:28px;background:linear-gradient(135deg,rgba(30,64,175,.16),rgba(20,184,166,.10));margin-bottom:22px;}
      .wz27-title{font-size:30px;font-weight:850;color:#f8fafc;margin-bottom:4px;}
      .wz27-sub{font-size:16px;color:#cbd5e1;}
      .wz27-card{border:1px solid rgba(148,163,184,.22);border-radius:18px;padding:20px;min-height:180px;background:rgba(15,23,42,.38);}
      .wz27-card h3{font-size:20px;margin-top:0;}
      .wz27-card p{color:#cbd5e1;min-height:70px;}
      .wz27-reco{border:1px solid rgba(34,197,94,.28);border-radius:16px;padding:16px;background:rgba(34,197,94,.08);}
      div[data-testid="stButton"] > button{border-radius:12px;min-height:42px;font-weight:650;}
    </style>
    """, unsafe_allow_html=True)
    st.markdown(f"""
    <div class='wz27-hero'>
      <div class='wz27-title'>👋 Welcome back, {html.escape(str(name))}</div>
      <div class='wz27-sub'>Let’s move you closer to your next job.</div>
    </div>
    """, unsafe_allow_html=True)
    c1,c2,c3 = st.columns(3)
    c1.metric('CV Strength', f'{cv_score}%' if cv_score else 'Not analyzed')
    c2.metric('Job Match', f'{ats_score}%' if ats_score else 'Not analyzed')
    c3.metric('Interview Readiness', f'{interview_score}%')
    st.caption('Scores update after you improve a CV, analyze a job, or complete Work-O-Bot.')
    if st.button('Continue Your Journey', key='wz27_continue', use_container_width=False):
        if not cv_score: _wz27_go('cv_documents')
        elif not ats_score: _wz27_go('job_assist')
        elif interview_score < 70: _wz27_go('workobot')
        else: _wz27_go('job_assist')
    st.divider()
    st.subheader('What do you need today?')
    a,b,c = st.columns(3)
    with a:
        st.markdown("<div class='wz27-card'><h3>🟦 Get More Interviews</h3><p>Improve your CV for a job description, strengthen ATS alignment, and keep changes honest.</p></div>", unsafe_allow_html=True)
        if st.button('Improve My CV', key='wz27_improve', use_container_width=True):
            st.session_state['cv_documents_mode']='improve_cv'; _wz27_go('cv_documents')
    with b:
        st.markdown("<div class='wz27-card'><h3>🟩 Prepare for Interview</h3><p>Practice interview questions based only on your CV, job description, and company context.</p></div>", unsafe_allow_html=True)
        if st.button('Start Work-O-Bot', key='wz27_interview', use_container_width=True):
            _wz27_go('workobot')
    with c:
        st.markdown("<div class='wz27-card'><h3>🟧 Find Relevant Jobs</h3><p>Find better-matched jobs, understand fit, and use the job details across your application.</p></div>", unsafe_allow_html=True)
        if st.button('Find Jobs', key='wz27_jobs', use_container_width=True):
            _wz27_go('job_assist')
    st.divider()
    st.subheader('What WorkZo suggests for you')
    if not cv_score:
        reco, target = 'Add or create your CV first. WorkZo needs this to personalize every feature.', 'cv_documents'
    elif not ats_score:
        reco, target = 'Paste a job description and company website so WorkZo can analyze your match.', 'job_assist'
    elif ats_score < 75:
        reco, target = 'Your job match can improve. Strengthen only truthful keywords from the JD.', 'cv_documents'
    elif interview_score < 70:
        reco, target = 'Practice the real interview using your CV and the job description before applying.', 'workobot'
    else:
        reco, target = 'You look ready to apply. Prepare a focused cover letter and track your application.', 'job_assist'
    st.markdown(f"<div class='wz27-reco'>{html.escape(reco)}</div>", unsafe_allow_html=True)
    if st.button('Do this next', key='wz27_next', use_container_width=True):
        _wz27_go(target)
    st.divider()
    st.subheader('Need help?')
    st.caption('Work-O-Bot is for typed questions: CV doubts, HR messages, career decisions, job search, and language practice.')
    if st.button('Ask Work-O-Bot', key='wz27_bot', use_container_width=False):
        _wz27_go('workobot')


def _wz27_job_assist_page():
    st.markdown('## AI Job Application Assistant')
    st.caption('Paste a job description and company website. WorkZo uses this context across CV improvement, cover letter, and Work-O-Bot without inventing facts.')
    col1, col2 = st.columns(2)
    with col1:
        st.text_input('Target company', value=st.session_state.get('target_company',''), key='wz27_target_company')
    with col2:
        st.text_input('Company website / careers page', value=st.session_state.get('target_company_website',''), key='wz27_company_website', help='Optional, but recommended for company-aware cover letters and interview questions.')
    st.session_state['target_company'] = st.session_state.get('wz27_target_company','')
    st.session_state['company_website'] = st.session_state.get('wz27_company_website','')
    try:
        _wz20_render_job_assist_page()
    except Exception as exc:
        st.error('Job Match page could not load. Showing a safe basic version instead.')
        jd = st.text_area('Paste the job description', value=st.session_state.get('current_job_description',''), height=220, key='wz27_safe_jd')
        if jd.strip():
            st.session_state['current_job_description'] = jd
            st.session_state['last_understand_job_description'] = jd
        if st.button('Use this job for CV + Work-O-Bot', key='wz27_use_job', use_container_width=True):
            _wz27_go('cv_documents')


def _wz27_workobot_page():
    st.markdown('## Work-O-Bot')
    st.caption('Typed assistant for career questions, CV doubts, HR messages, job search, and language practice. Use Work-O-Bot for mock interviews.')
    try:
        show_workobot()
    except Exception as exc:
        st.error('Work-O-Bot could not load.')
        st.exception(exc)


def show_dashboard():
    page_key = st.session_state.get('nav_page') or st.session_state.get('page') or 'dashboard'
    page_key = {'landing':'dashboard','onboarding':'dashboard','founder_dashboard':'dashboard','bot':'workobot','interview':'workobot','jobs':'job_assist','improve_cv':'cv_documents'}.get(page_key, page_key)
    st.session_state['page'] = page_key
    st.session_state['nav_page'] = page_key
    _wz27_force_top()
    _wz27_sidebar(page_key)
    if page_key == 'dashboard':
        _wz27_dashboard_home()
    elif page_key == 'cv_documents':
        show_document_tools()
    elif page_key == 'job_assist':
        _wz27_job_assist_page()
    elif page_key == 'workobot':
        try:
            _wz21_render_interview_practice_page()
        except Exception:
            if 'show_interview_simulation' in globals():
                show_interview_simulation()
            else:
                st.error('Work-O-Bot could not load.')
    elif page_key == 'workobot':
        _wz27_workobot_page()
    else:
        _wz27_dashboard_home()
    st.divider()
    st.caption('WORKZO AI • Beta • Guided career workspace')

# =========================================================
# WorkZo v28 - hard final UX/stability override
# Fixes: dashboard progress bar removal, reliable top scroll,
# visible Work-O-Bot, no founder analytics, lighter/faster dashboard.
# =========================================================
def _wz28_top(force: bool = True):
    try:
        st.markdown("<div id='workzo-top-anchor'></div>", unsafe_allow_html=True)
        js = """
        <script>
        function workzoTop(){
          const doc = window.parent.document;
          try { window.parent.scrollTo(0,0); } catch(e) {}
          try { doc.documentElement.scrollTop = 0; } catch(e) {}
          try { doc.body.scrollTop = 0; } catch(e) {}
          const selectors = ['[data-testid="stAppViewContainer"]','section.main','.main','.block-container'];
          for (const s of selectors){ try { const el = doc.querySelector(s); if(el){ el.scrollTop = 0; } } catch(e) {} }
          try { doc.getElementById('workzo-top-anchor').scrollIntoView({block:'start'}); } catch(e) {}
        }
        workzoTop(); setTimeout(workzoTop, 20); setTimeout(workzoTop, 120); setTimeout(workzoTop, 350);
        </script>
        """
        if hasattr(st, 'iframe'):
            st.iframe(srcdoc=js, height=1, width=1)
        else:
            try:
                import streamlit.components.v1 as components
                components.html(js, height=1, width=1)
            except Exception:
                pass
    except Exception:
        pass


def _wz28_css():
    st.markdown("""
    <style>
      .wz28-hide-progress [data-testid="stProgress"] {display:none !important;}
      div[data-testid="stButton"] > button{border-radius:12px;min-height:42px;font-weight:650;}
      .wz28-hero{border:1px solid rgba(148,163,184,.22);border-radius:24px;padding:28px;background:linear-gradient(135deg,rgba(30,64,175,.14),rgba(20,184,166,.10));margin-bottom:22px;}
      .wz28-title{font-size:30px;font-weight:850;color:#f8fafc;margin-bottom:4px;}
      .wz28-sub{font-size:16px;color:#cbd5e1;}
      .wz28-card{border:1px solid rgba(148,163,184,.22);border-radius:18px;padding:20px;min-height:178px;background:rgba(15,23,42,.38);}
      .wz28-card h3{font-size:20px;margin-top:0;}
      .wz28-card p{color:#cbd5e1;min-height:68px;}
      .wz28-reco{border:1px solid rgba(34,197,94,.28);border-radius:16px;padding:16px;background:rgba(34,197,94,.08);}
      .wz28-sidebar-card{border:1px solid rgba(20,184,166,.35);border-radius:18px;padding:16px;margin-bottom:16px;background:rgba(15,23,42,.65);}
      .wz28-sidebar-logo{width:44px;height:44px;border-radius:12px;margin-bottom:10px;}
      .wz28-sidebar-brand{font-weight:800;font-size:20px;letter-spacing:.04em;}
      .wz28-sidebar-small{font-size:12px;color:#94a3b8;}
    </style>
    """, unsafe_allow_html=True)


def _wz28_go(page_key: str):
    aliases = {
        'home':'dashboard','landing':'dashboard','onboarding':'dashboard',
        'my_cv':'cv_documents','improve_cv':'cv_documents','cv':'cv_documents',
        'jobs':'job_assist','job_match':'job_assist','prepare_job':'job_assist',
        'interview':'workobot','speaking_practice':'workobot',
        'bot':'workobot','work-o-bot':'workobot','work_o_bot':'workobot',
        'founder_dashboard':'dashboard','founder':'dashboard',
    }
    page_key = aliases.get(str(page_key or 'dashboard'), str(page_key or 'dashboard'))
    st.session_state['page'] = page_key
    st.session_state['nav_page'] = page_key
    st.session_state['_workzo_scroll_to_top'] = True
    try:
        nonce = int(st.session_state.get('nav_change_nonce', 0)) + 1
        st.session_state['nav_change_nonce'] = nonce
        st.query_params['page'] = page_key
        st.query_params['top'] = str(nonce)
    except Exception:
        pass
    st.rerun()

_wz27_go = _wz28_go
_wz25_go = _wz28_go
_wz24_go = _wz28_go
_wz21_go = _wz28_go
_wz19_go = _wz28_go
go_to_nav = _wz28_go


def _wz28_score(*keys, default=0):
    for k in keys:
        try:
            v = st.session_state.get(k)
            if v is not None and str(v).strip() != '':
                return max(0, min(100, int(float(v))))
        except Exception:
            pass
    return default


def _wz28_sidebar(page_key: str):
    with st.sidebar:
        try:
            logo_src = image_to_data_uri(ICON_PATH) or image_to_data_uri(LOGO_PATH)
        except Exception:
            logo_src = None
        if logo_src:
            st.markdown(f"""
            <div class='wz28-sidebar-card'>
                <img src='{logo_src}' class='wz28-sidebar-logo' alt='WorkZo AI logo'>
                <div class='wz28-sidebar-brand'>WORKZO AI</div>
                <div class='wz28-sidebar-small'>Guided career workspace</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown('### WorkZo AI')
        st.markdown('##### Navigation')
        nav = [('dashboard','Dashboard'),('cv_documents','My CV'),('job_assist','Job Match'),('workobot','Work-O-Bot')]
        for key, label in nav:
            if st.button(label + (' ✓' if page_key == key else ''), key=f'wz28_nav_{key}', use_container_width=True):
                _wz28_go(key)
        st.markdown('##### Profile')
        st.caption(f"Country: {st.session_state.get('country') or st.session_state.get('target_country') or 'Not set'}")
        st.caption('Resume uploaded' if str(st.session_state.get('cv_text','')).strip() else 'CV missing')
        st.markdown('##### Settings')
        try:
            language_list = language_options if language_options else ['English', 'German', 'Dutch']
            current = st.session_state.get('preferred_language') or st.session_state.get('language') or 'English'
            if current not in language_list:
                current = 'English' if 'English' in language_list else language_list[0]
            chosen = st.selectbox('Language', language_list, index=language_list.index(current), key='wz28_language')
            set_single_preferred_language(chosen)
            st.session_state['preferred_language'] = chosen
            st.session_state['language'] = chosen
        except Exception:
            pass
        if st.button('Edit setup', key='wz28_edit_setup', use_container_width=True):
            try:
                reset_onboarding()
            except Exception:
                st.session_state['onboarding_complete'] = False
            _wz28_go('onboarding')


def _wz28_dashboard_home():
    _wz28_css()
    cv_exists = bool(str(st.session_state.get('cv_text','')).strip() or st.session_state.get('structured_cv_json'))
    job_exists = bool(str(st.session_state.get('current_job_description','') or st.session_state.get('last_understand_job_description','') or st.session_state.get('improve_cv_for_job_desc','')).strip())
    cv_score = _wz28_score('cv_score_value','resume_score', default=75 if cv_exists else 0)
    ats_score = _wz28_score('ats_score_value','job_match_score', default=70 if job_exists else 0)
    interview_score = _wz28_score('interview_score','interview_readiness', default=40)
    name = st.session_state.get('user_name') or st.session_state.get('candidate_name') or 'there'
    st.markdown("<div class='wz28-hide-progress'>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class='wz28-hero'>
      <div class='wz28-title'>Welcome back, {html.escape(str(name))}</div>
      <div class='wz28-sub'>Let’s move you closer to your next job.</div>
    </div>
    """, unsafe_allow_html=True)
    c1,c2,c3 = st.columns(3)
    c1.metric('CV Strength', f'{cv_score}%' if cv_score else 'Not analyzed')
    c2.metric('Job Match', f'{ats_score}%' if ats_score else 'Not analyzed')
    c3.metric('Interview Readiness', f'{interview_score}%')
    st.caption('No progress bar here: use the cards below for the next best action.')
    if st.button('Continue Your Journey', key='wz28_continue', use_container_width=False):
        if not cv_exists: _wz28_go('cv_documents')
        elif not job_exists: _wz28_go('job_assist')
        elif interview_score < 70: _wz28_go('workobot')
        else: _wz28_go('job_assist')
    st.divider()
    st.subheader('What do you need today?')
    a,b,c = st.columns(3)
    with a:
        st.markdown("<div class='wz28-card'><h3>Get More Interviews</h3><p>Improve your CV for a job description, strengthen ATS alignment, and keep changes honest.</p></div>", unsafe_allow_html=True)
        if st.button('Improve My CV', key='wz28_improve', use_container_width=True):
            st.session_state['cv_documents_mode']='improve_cv'; _wz28_go('cv_documents')
    with b:
        st.markdown("<div class='wz28-card'><h3>Prepare for Interview</h3><p>Practice questions based only on your CV, job description, company context, country, and chosen language.</p></div>", unsafe_allow_html=True)
        if st.button('Start Work-O-Bot', key='wz28_interview', use_container_width=True):
            _wz28_go('workobot')
    with c:
        st.markdown("<div class='wz28-card'><h3>Find Relevant Jobs</h3><p>Analyze a job, add company website context, and reuse it for CV, cover letter, and interview preparation.</p></div>", unsafe_allow_html=True)
        if st.button('Find Jobs', key='wz28_jobs', use_container_width=True):
            _wz28_go('job_assist')
    st.divider()
    st.subheader('What WorkZo suggests for you')
    if not cv_exists:
        reco, target = 'Add or create your CV first. WorkZo needs this to personalize every feature.', 'cv_documents'
    elif not job_exists:
        reco, target = 'Paste a job description and company website so WorkZo can analyze your match.', 'job_assist'
    elif ats_score < 75:
        reco, target = 'Your job match can improve. Add only truthful keywords from the job description.', 'cv_documents'
    elif interview_score < 70:
        reco, target = 'Practice the real interview using your CV, job description, and selected language.', 'workobot'
    else:
        reco, target = 'You look ready to apply. Prepare a focused cover letter and track your application.', 'job_assist'
    st.markdown(f"<div class='wz28-reco'>{html.escape(reco)}</div>", unsafe_allow_html=True)
    if st.button('Do this next', key='wz28_next', use_container_width=True):
        _wz28_go(target)
    st.divider()
    st.subheader('Need help?')
    st.caption('Work-O-Bot is a separate typed assistant for career questions, HR messages, CV doubts, job search, and language practice.')
    if st.button('Ask Work-O-Bot', key='wz28_bot', use_container_width=False):
        _wz28_go('workobot')
    st.markdown('</div>', unsafe_allow_html=True)


def _wz28_job_assist_page():
    _wz28_css()
    st.markdown('## AI Job Application Assistant')
    st.caption('Paste a job description and company website. WorkZo reuses this context for CV improvement, cover letters, and Work-O-Bot.')
    col1, col2 = st.columns(2)
    with col1:
        company = st.text_input('Target company', value=st.session_state.get('target_company',''), key='wz28_target_company')
    with col2:
        website = st.text_input('Company website / careers page', value=st.session_state.get('target_company_website',''), key='wz28_company_website')
    st.session_state['target_company'] = company
    st.session_state['company_website'] = website
    if website:
        st.info('Company website saved. WorkZo will use it for CV advice, cover letters, and interview questions without inventing facts.')
    try:
        _wz20_render_job_assist_page()
    except Exception:
        jd = st.text_area('Paste the job description', value=st.session_state.get('current_job_description',''), height=220, key='wz28_safe_jd')
        if jd.strip():
            st.session_state['current_job_description'] = jd
            st.session_state['last_understand_job_description'] = jd
        if st.button('Use this job for CV + Work-O-Bot', key='wz28_use_job', use_container_width=True):
            _wz28_go('cv_documents')


def _wz28_workobot_page():
    _wz28_css()
    st.markdown('## Work-O-Bot')
    st.caption('Typed assistant for career questions, CV doubts, HR messages, job search, and language practice. Work-O-Bot is separate.')
    try:
        show_workobot()
    except Exception as exc:
        st.error('Work-O-Bot could not load.')
        st.exception(exc)


def show_dashboard():
    page_key = st.session_state.get('nav_page') or st.session_state.get('page') or 'dashboard'
    page_key = {'landing':'dashboard','onboarding':'dashboard','founder_dashboard':'dashboard','founder':'dashboard','bot':'workobot','interview':'workobot','jobs':'job_assist','improve_cv':'cv_documents'}.get(page_key, page_key)
    if page_key not in {'dashboard','cv_documents','job_assist','workobot','workobot'}:
        page_key = 'dashboard'
    st.session_state['page'] = page_key
    st.session_state['nav_page'] = page_key
    _wz28_top(True)
    _wz28_sidebar(page_key)
    if page_key == 'dashboard':
        _wz28_dashboard_home()
    elif page_key == 'cv_documents':
        _wz28_css(); show_document_tools()
    elif page_key == 'job_assist':
        _wz28_job_assist_page()
    elif page_key == 'workobot':
        _wz28_css()
        try:
            _wz21_render_interview_practice_page()
        except Exception:
            if 'show_interview_simulation' in globals():
                show_interview_simulation()
            else:
                st.error('Work-O-Bot could not load.')
    elif page_key == 'workobot':
        _wz28_workobot_page()
    st.caption('WORKZO AI • Beta • Guided career workspace')

# =========================================================
# WorkZo v29 - final UX cleanup: reliable top scroll, clean sidebar,
# no duplicate interview wrapper.
# =========================================================
def _wz29_force_top():
    try:
        st.markdown("<div id='workzo-page-top'></div>", unsafe_allow_html=True)
        js = """
        <script>
        function wzTop(){
          try { window.parent.scrollTo(0,0); } catch(e) {}
          try { window.parent.document.documentElement.scrollTop = 0; } catch(e) {}
          try { window.parent.document.body.scrollTop = 0; } catch(e) {}
          const sels = ['section.main','[data-testid="stAppViewContainer"]','[data-testid="stMain"]','.main','.block-container'];
          for (const s of sels) { try { const el = window.parent.document.querySelector(s); if (el) { el.scrollTop = 0; } } catch(e) {} }
        }
        wzTop(); setTimeout(wzTop, 40); setTimeout(wzTop, 160); setTimeout(wzTop, 450);
        </script>
        """
        import streamlit.components.v1 as components
        components.html(js, height=0, width=0)
    except Exception:
        pass

def _wz28_top(force: bool = True):
    _wz29_force_top()

def _wz29_clean_css():
    st.markdown("""
    <style>
      section[data-testid="stSidebar"] .block-container{padding-top:1.2rem;padding-left:1rem;padding-right:1rem;}
      .wz29-side-card{border:1px solid rgba(20,184,166,.35);border-radius:18px;padding:15px;margin:4px 0 18px;background:linear-gradient(135deg,rgba(8,47,73,.72),rgba(15,23,42,.80));}
      .wz29-side-logo{width:46px;height:46px;border-radius:12px;margin-bottom:10px;}
      .wz29-side-brand{font-size:20px;font-weight:850;letter-spacing:.03em;color:#fff;}
      .wz29-side-sub{font-size:13px;color:#94a3b8;margin-top:3px;}
      .wz29-side-label{font-size:12px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:#94a3b8;margin:16px 0 8px;}
      section[data-testid="stSidebar"] div[data-testid="stButton"] > button{min-height:42px;border-radius:12px;justify-content:flex-start;font-weight:650;}
    </style>
    """, unsafe_allow_html=True)

def _wz28_sidebar(page_key: str):
    _wz29_clean_css()
    with st.sidebar:
        try:
            logo_src = image_to_data_uri(ICON_PATH) or image_to_data_uri(LOGO_PATH)
        except Exception:
            logo_src = None
        if logo_src:
            st.markdown(f"""
            <div class='wz29-side-card'>
                <img src='{logo_src}' class='wz29-side-logo' alt='WorkZo AI logo'>
                <div class='wz29-side-brand'>WORKZO AI</div>
                <div class='wz29-side-sub'>Guided career workspace</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("### WorkZo AI")
        st.markdown("<div class='wz29-side-label'>Navigation</div>", unsafe_allow_html=True)
        nav = [('dashboard','Dashboard'),('cv_documents','My CV'),('job_assist','Job Match'),('workobot','Work-O-Bot')]
        for key, label in nav:
            if st.button(label + (' ✓' if page_key == key else ''), key=f'wz29_nav_{key}', use_container_width=True):
                _wz28_go(key)
        st.markdown("<div class='wz29-side-label'>Settings</div>", unsafe_allow_html=True)
        try:
            language_list = language_options if language_options else ['English','German','Dutch']
            current = st.session_state.get('preferred_language') or st.session_state.get('language') or 'English'
            if current not in language_list:
                current = 'English' if 'English' in language_list else language_list[0]
            chosen = st.selectbox('Language', language_list, index=language_list.index(current), key='wz29_language')
            set_single_preferred_language(chosen)
            st.session_state['preferred_language'] = chosen
            st.session_state['language'] = chosen
        except Exception:
            pass
        if st.button('Edit setup', key='wz29_edit_setup', use_container_width=True):
            try:
                reset_onboarding()
            except Exception:
                st.session_state['onboarding_complete'] = False
            _wz28_go('onboarding')

def _wz21_render_interview_practice_page():
    _wz29_force_top()
    if 'render_real_interview_simulation' in globals():
        render_real_interview_simulation()
    else:
        st.error('Work-O-Bot could not load. Please check 09_interview_assistant.py.')

# =========================================================
# WorkZo v30 - shared job/company context + cleaner centered sidebar
# =========================================================
def _wz30_get_job_context() -> dict:
    return {
        'company': st.session_state.get('target_company') or st.session_state.get('real_interview_company') or st.session_state.get('prepare_target_company') or '',
        'role': st.session_state.get('target_role') or st.session_state.get('target_job_title') or st.session_state.get('prepare_target_role') or '',
        'website': st.session_state.get('target_company_website') or '',
        'job_description': st.session_state.get('current_job_description') or st.session_state.get('last_understand_job_description') or st.session_state.get('job_description') or st.session_state.get('improve_cv_for_job_desc') or '',
    }

def _wz30_set_job_context(company='', role='', website='', job_description='') -> None:
    st.session_state['target_company'] = str(company or '').strip()
    st.session_state['real_interview_company'] = str(company or '').strip()
    st.session_state['prepare_target_company'] = str(company or '').strip()
    st.session_state['target_role'] = str(role or '').strip()
    st.session_state['target_job_title'] = str(role or '').strip()
    st.session_state['prepare_target_role'] = str(role or '').strip()
    st.session_state['company_website'] = str(website or '').strip()
    jd = str(job_description or '').strip()
    st.session_state['current_job_description'] = jd
    st.session_state['last_understand_job_description'] = jd
    st.session_state['job_description'] = jd
    st.session_state['improve_cv_for_job_desc'] = jd
    st.session_state['last_prepare_job_description'] = jd

def _wz30_saved_application_contexts() -> list:
    apps = st.session_state.get('saved_application_contexts')
    return apps if isinstance(apps, list) else []

def _wz30_save_application_context(company, role, website, jd) -> None:
    company = str(company or '').strip(); role = str(role or '').strip(); website = str(website or '').strip(); jd = str(jd or '').strip()
    if not any([company, role, website, jd]):
        return
    label = ' — '.join([x for x in [company or 'Company not specified', role or 'Role not specified'] if x])
    item = {'label': label, 'company': company, 'role': role, 'website': website, 'job_description': jd}
    apps = [a for a in _wz30_saved_application_contexts() if not (a.get('company') == company and a.get('role') == role and a.get('website') == website)]
    apps.insert(0, item)
    st.session_state['saved_application_contexts'] = apps[:12]

def _wz30_context_manager(prefix='wz30') -> dict:
    ctx = _wz30_get_job_context()
    saved = _wz30_saved_application_contexts()
    if saved:
        labels = ['Use current / new company'] + [a.get('label', 'Saved company') for a in saved]
        choice = st.selectbox('Saved company/job details', labels, key=f'{prefix}_saved_choice')
        if choice != labels[0]:
            item = saved[labels.index(choice)-1]
            _wz30_set_job_context(item.get('company',''), item.get('role',''), item.get('website',''), item.get('job_description',''))
            ctx = _wz30_get_job_context()
            st.info('Loaded saved company/job details. You can edit them below.')
    c1, c2 = st.columns(2)
    with c1:
        company = st.text_input('Target company', value=ctx.get('company',''), key=f'{prefix}_company')
    with c2:
        role = st.text_input('Target role', value=ctx.get('role',''), key=f'{prefix}_role')
    website = st.text_input('Company website / careers page', value=ctx.get('website',''), key=f'{prefix}_website', help='Paste once. WorkZo reuses it for CV, cover letter, job match, and Work-O-Bot.')
    jd = st.text_area('Paste the job description', value=ctx.get('job_description',''), height=210, key=f'{prefix}_jd')
    _wz30_set_job_context(company, role, website, jd)
    c3, c4 = st.columns(2)
    with c3:
        if st.button('Save this company/job', key=f'{prefix}_save', use_container_width=True):
            _wz30_save_application_context(company, role, website, jd)
            st.success('Saved. You can load it later when applying to multiple companies.')
    with c4:
        if st.button('Start new company', key=f'{prefix}_new', use_container_width=True):
            _wz30_set_job_context('', '', '', '')
            for k in [f'{prefix}_company', f'{prefix}_role', f'{prefix}_website', f'{prefix}_jd']:
                st.session_state[k] = ''
            st.rerun()
    return _wz30_get_job_context()

def _wz29_clean_css():
    st.markdown("""
    <style>
      section[data-testid="stSidebar"] .block-container{padding-top:1.2rem;padding-left:1rem;padding-right:1rem;}
      .wz29-side-card{border:1px solid rgba(20,184,166,.35);border-radius:18px;padding:15px;margin:4px 0 18px;background:linear-gradient(135deg,rgba(8,47,73,.72),rgba(15,23,42,.80));}
      .wz29-side-logo{width:46px;height:46px;border-radius:12px;margin-bottom:10px;}
      .wz29-side-brand{font-size:20px;font-weight:850;letter-spacing:.03em;color:#fff;}
      .wz29-side-sub{font-size:13px;color:#94a3b8;margin-top:3px;}
      .wz29-side-label{font-size:12px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:#94a3b8;margin:18px 0 8px;text-align:left;}
      section[data-testid="stSidebar"] div[data-testid="stButton"]{display:flex;justify-content:center;}
      section[data-testid="stSidebar"] div[data-testid="stButton"] > button{width:200px !important;min-width:200px !important;max-width:200px !important;min-height:42px;border-radius:12px;justify-content:center;text-align:center;font-weight:650;margin:4px auto;}
    </style>
    """, unsafe_allow_html=True)

def _wz28_sidebar(page_key: str):
    _wz29_clean_css()
    with st.sidebar:
        try:
            logo_src = image_to_data_uri(ICON_PATH) or image_to_data_uri(LOGO_PATH)
        except Exception:
            logo_src = None
        if logo_src:
            st.markdown(f"""
            <div class='wz29-side-card'>
                <img src='{logo_src}' class='wz29-side-logo' alt='WorkZo AI logo'>
                <div class='wz29-side-brand'>WORKZO AI</div>
                <div class='wz29-side-sub'>Guided career workspace</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown('### WorkZo AI')
        st.markdown("<div class='wz29-side-label'>Navigation</div>", unsafe_allow_html=True)
        nav = [('dashboard','Dashboard'),('cv_documents','My CV'),('job_assist','Job Match'),('workobot','Work-O-Bot')]
        for key, label in nav:
            if st.button(label + (' ✓' if page_key == key else ''), key=f'wz30_nav_{key}', use_container_width=False):
                _wz28_go(key)
        st.markdown("<div class='wz29-side-label'>Settings</div>", unsafe_allow_html=True)
        try:
            language_list = language_options if language_options else ['English','German','Dutch']
            current = st.session_state.get('preferred_language') or st.session_state.get('language') or 'English'
            if current not in language_list:
                current = 'English' if 'English' in language_list else language_list[0]
            chosen = st.selectbox('Language', language_list, index=language_list.index(current), key='wz30_language')
            set_single_preferred_language(chosen)
            st.session_state['preferred_language'] = chosen
            st.session_state['language'] = chosen
        except Exception:
            pass
        if st.button('Edit setup', key='wz30_edit_setup', use_container_width=False):
            try:
                reset_onboarding()
            except Exception:
                st.session_state['onboarding_complete'] = False
            _wz28_go('onboarding')

def _wz28_job_assist_page():
    _wz28_css()
    st.markdown('## AI Job Application Assistant')
    st.caption('Add company, role, website, and job description once. WorkZo reuses this context across CV improvement, cover letter, Job Match, and Work-O-Bot.')
    ctx = _wz30_context_manager('wz30_job')
    if ctx.get('website'):
        st.info('Company website saved. WorkZo will use it without inventing company facts.')
    try:
        _wz20_render_job_assist_page()
    except Exception:
        st.warning('Using simplified Job Match view.')
        if st.button('Use this job for CV + Work-O-Bot', key='wz30_use_job', use_container_width=True):
            _wz28_go('cv_documents')


# =========================================================
# WorkZo v31 - Smart Command Center dashboard
# - Separate Resume Score, ATS Score, Job Fit, Interview Readiness
# - Visual rate cards
# - Smart next action based on score/state
# - No confusing generic "Job Match 90%" without a job description
# =========================================================
def _wz31_clamp_score(value, default=0):
    try:
        if value is None or str(value).strip() == "":
            return int(default)
        return max(0, min(100, int(float(value))))
    except Exception:
        return int(default or 0)


def _wz31_get_score(*keys, default=0):
    for key in keys:
        try:
            value = st.session_state.get(key)
            if value is not None and str(value).strip() != "":
                return _wz31_clamp_score(value, default)
        except Exception:
            pass
    return _wz31_clamp_score(default, 0)


def _wz31_score_label(score):
    score = _wz31_clamp_score(score)
    if score >= 85:
        return "Excellent"
    if score >= 75:
        return "Good"
    if score >= 60:
        return "Needs improvement"
    if score > 0:
        return "Weak"
    return "Not analyzed"


def _wz31_escape(value):
    try:
        return html.escape(str(value or ""))
    except Exception:
        return str(value or "")


def _wz31_css():
    st.markdown("""
    <style>
      .wz31-hero{
        border:1px solid rgba(20,184,166,.30);
        border-radius:28px;
        padding:30px 34px;
        margin:8px 0 24px 0;
        background:radial-gradient(circle at top left,rgba(20,184,166,.20),transparent 35%),linear-gradient(135deg,rgba(30,64,175,.28),rgba(8,47,73,.24));
        box-shadow:0 18px 50px rgba(2,6,23,.28);
      }
      .wz31-kicker{color:#93c5fd;font-size:.78rem;font-weight:850;letter-spacing:.12em;text-transform:uppercase;margin-bottom:8px;}
      .wz31-title{color:#fff;font-size:2rem;font-weight:900;line-height:1.12;margin-bottom:8px;}
      .wz31-sub{color:#dbeafe;font-size:1.02rem;line-height:1.5;max-width:900px;}
      .wz31-chip-row{display:flex;gap:8px;flex-wrap:wrap;margin-top:16px;}
      .wz31-chip{border:1px solid rgba(96,165,250,.28);background:rgba(37,99,235,.18);border-radius:999px;color:#dbeafe;font-size:.84rem;font-weight:700;padding:7px 11px;}
      .wz31-next{
        border:1px solid rgba(45,212,191,.32);
        border-radius:22px;
        padding:20px 22px;
        background:linear-gradient(135deg,rgba(20,184,166,.18),rgba(37,99,235,.14));
        margin:12px 0 22px 0;
      }
      .wz31-next-label{color:#99f6e4;font-size:.78rem;font-weight:900;letter-spacing:.1em;text-transform:uppercase;margin-bottom:6px;}
      .wz31-next-title{color:#fff;font-size:1.25rem;font-weight:900;margin-bottom:5px;}
      .wz31-next-copy{color:#cbd5e1;font-size:.95rem;line-height:1.5;}
      .wz31-rate-card{
        border:1px solid rgba(148,163,184,.18);
        border-radius:22px;
        padding:18px 18px 16px 18px;
        background:linear-gradient(180deg,rgba(30,41,59,.82),rgba(15,23,42,.72));
        min-height:168px;
        box-shadow:0 12px 30px rgba(2,6,23,.18);
        margin-bottom:14px;
      }
      .wz31-rate-head{display:flex;justify-content:space-between;align-items:flex-start;gap:10px;margin-bottom:10px;}
      .wz31-rate-title{color:#e2e8f0;font-size:.95rem;font-weight:850;line-height:1.25;}
      .wz31-rate-badge{border:1px solid rgba(148,163,184,.25);border-radius:999px;padding:4px 8px;color:#cbd5e1;font-size:.72rem;font-weight:800;white-space:nowrap;}
      .wz31-score{color:#fff;font-size:2.15rem;font-weight:950;line-height:1;margin:8px 0 10px;}
      .wz31-bar-bg{height:10px;border-radius:999px;background:rgba(148,163,184,.20);overflow:hidden;margin:7px 0 9px;}
      .wz31-bar-fill{height:10px;border-radius:999px;background:linear-gradient(90deg,#38bdf8,#2dd4bf);}
      .wz31-rate-copy{color:#94a3b8;font-size:.84rem;line-height:1.45;margin-top:8px;}
      .wz31-actions{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px;margin:14px 0 22px;}
      .wz31-action-card{border:1px solid rgba(148,163,184,.16);border-radius:22px;padding:18px;background:rgba(15,23,42,.56);min-height:148px;}
      .wz31-action-title{color:#fff;font-size:1.05rem;font-weight:900;margin-bottom:8px;}
      .wz31-action-copy{color:#aebbd0;font-size:.9rem;line-height:1.45;}
      .wz31-flow{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px;margin-top:10px;}
      .wz31-step{border:1px solid rgba(148,163,184,.16);border-radius:18px;padding:13px 14px;background:rgba(15,23,42,.46);}
      .wz31-step.done{border-color:rgba(45,212,191,.42);background:rgba(20,184,166,.12);}
      .wz31-step-title{color:#fff;font-weight:850;font-size:.92rem;}
      .wz31-step-sub{color:#94a3b8;font-size:.78rem;margin-top:3px;}
    </style>
    """, unsafe_allow_html=True)


def _wz31_rate_card(title, score, subtitle, *, missing=False):
    score = _wz31_clamp_score(score)
    label = "Add details" if missing else _wz31_score_label(score)
    shown = "—" if missing or score <= 0 else f"{score}%"
    fill = 0 if missing else score
    st.markdown(f"""
    <div class='wz31-rate-card'>
      <div class='wz31-rate-head'>
        <div class='wz31-rate-title'>{_wz31_escape(title)}</div>
        <div class='wz31-rate-badge'>{_wz31_escape(label)}</div>
      </div>
      <div class='wz31-score'>{_wz31_escape(shown)}</div>
      <div class='wz31-bar-bg'><div class='wz31-bar-fill' style='width:{fill}%;'></div></div>
      <div class='wz31-rate-copy'>{_wz31_escape(subtitle)}</div>
    </div>
    """, unsafe_allow_html=True)


def _wz31_pick_next_action(cv_exists, job_exists, resume_score, ats_score, job_fit_score, interview_score):
    if not cv_exists:
        return {
            "title": "Add your CV first",
            "copy": "WorkZo needs your CV to score it, suggest matching roles, and personalize every next step.",
            "button": "Add / Create CV",
            "target": "cv_documents",
        }
    if resume_score < 75 or ats_score < 75:
        return {
            "title": "Improve your CV before applying",
            "copy": "Your resume or ATS score still needs work. Fix structure, keywords, and clarity before spending time on applications.",
            "button": "Improve CV",
            "target": "cv_documents",
        }
    if not job_exists:
        return {
            "title": "Find or paste a real job next",
            "copy": "Your CV looks ready. Now choose a real job description so WorkZo can check job fit and tailor your application.",
            "button": "Find / Analyze Jobs",
            "target": "job_assist",
        }
    if job_fit_score and job_fit_score < 70:
        return {
            "title": "Tailor CV to this job first",
            "copy": "The current job fit is not strong enough yet. Add only truthful job-relevant keywords and stronger matching bullets.",
            "button": "Tailor CV for Job",
            "target": "cv_documents",
        }
    if interview_score < 75:
        return {
            "title": "Practice for the interview",
            "copy": "Your CV and ATS look good. Use Work-O-Bot to practice job-specific answers based on your CV, job description, company, and language.",
            "button": "Practice with Work-O-Bot",
            "target": "workobot",
        }
    return {
        "title": "Ready to apply",
        "copy": "Your scores look strong. Generate a focused cover letter, save this application, and apply.",
        "button": "Prepare Application",
        "target": "job_assist",
    }


def _wz31_action_card(title, copy, button, target, key, extra_state=None):
    st.markdown(f"""
    <div class='wz31-action-card'>
      <div class='wz31-action-title'>{_wz31_escape(title)}</div>
      <div class='wz31-action-copy'>{_wz31_escape(copy)}</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button(button, key=key, use_container_width=True):
        if isinstance(extra_state, dict):
            for k, v in extra_state.items():
                st.session_state[k] = v
        _wz28_go(target)


def _wz28_dashboard_home():
    _wz28_css()
    _wz31_css()
    cv_exists = bool(str(st.session_state.get('cv_text','')).strip() or st.session_state.get('structured_cv_json'))
    job_text = str(st.session_state.get('current_job_description','') or st.session_state.get('last_understand_job_description','') or st.session_state.get('improve_cv_for_job_desc','') or st.session_state.get('job_description','')).strip()
    job_exists = bool(job_text)
    company = str(st.session_state.get('target_company') or st.session_state.get('prepare_target_company') or '').strip()
    country = str(st.session_state.get('country') or st.session_state.get('target_country') or 'Not set')
    language = str(st.session_state.get('preferred_language') or st.session_state.get('language') or 'English')
    role = str(st.session_state.get('target_role') or st.session_state.get('target_job_title') or st.session_state.get('detected_target_role') or 'Target role not set')

    resume_score = _wz31_get_score('cv_score_value', 'resume_score', 'resume_quality_score', default=75 if cv_exists else 0)
    ats_score = _wz31_get_score('ats_score_value', 'ats_score', default=70 if cv_exists else 0)
    job_fit_score = _wz31_get_score('job_fit_score_value', 'job_match_score', 'latest_job_fit_score', default=0)
    if job_exists and job_fit_score <= 0:
        job_fit_score = _wz31_get_score('ats_score_value', default=60)
    interview_score = _wz31_get_score('interview_score', 'interview_readiness', default=0)
    if interview_score <= 0:
        if cv_exists and job_exists and resume_score >= 75 and ats_score >= 75:
            interview_score = 65
        elif cv_exists:
            interview_score = 45
        else:
            interview_score = 20

    next_action = _wz31_pick_next_action(cv_exists, job_exists, resume_score, ats_score, job_fit_score, interview_score)

    st.markdown(f"""
    <div class='wz31-hero'>
      <div class='wz31-kicker'>WorkZo Command Center</div>
      <div class='wz31-title'>Your next best move is clear.</div>
      <div class='wz31-sub'>WorkZo reads your CV, country, language, job description, and company context, then recommends what to do next instead of showing every feature at once.</div>
      <div class='wz31-chip-row'>
        <span class='wz31-chip'>{_wz31_escape(country)}</span>
        <span class='wz31-chip'>{_wz31_escape(language)}</span>
        <span class='wz31-chip'>{'CV ready' if cv_exists else 'CV missing'}</span>
        <span class='wz31-chip'>{'Job added' if job_exists else 'Job not added'}</span>
        <span class='wz31-chip'>{_wz31_escape(company or 'Company not added')}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class='wz31-next'>
      <div class='wz31-next-label'>Recommended next step</div>
      <div class='wz31-next-title'>{_wz31_escape(next_action['title'])}</div>
      <div class='wz31-next-copy'>{_wz31_escape(next_action['copy'])}</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button(next_action['button'], key='wz31_primary_next_action', use_container_width=True):
        if next_action['target'] == 'cv_documents' and job_exists:
            st.session_state['document_tools_mode'] = 'Improve CV for a Job'
        _wz28_go(next_action['target'])

    st.markdown('### Readiness overview')
    r1, r2, r3, r4 = st.columns(4)
    with r1:
        _wz31_rate_card('Resume Score', resume_score, 'Clarity, structure, achievements, and overall CV quality.', missing=not cv_exists)
    with r2:
        _wz31_rate_card('ATS Score', ats_score, 'Scanner-friendly formatting, keywords, sections, and parsing safety.', missing=not cv_exists)
    with r3:
        _wz31_rate_card('Job Fit', job_fit_score, 'Fit for the current pasted job description. Add a job before trusting this score.', missing=not job_exists)
    with r4:
        _wz31_rate_card('Interview Readiness', interview_score, 'How ready you are to explain this CV and job fit clearly.', missing=not cv_exists)

    st.markdown('### Smart actions')
    a1, a2, a3, a4 = st.columns(4)
    with a1:
        _wz31_action_card('Improve CV', 'Use this when Resume or ATS score is below 75, or when you want to tailor for one job.', 'Open CV Tools', 'cv_documents', 'wz31_open_cv', {'document_tools_mode':'Improve CV for a Job' if job_exists else 'Improve / Update CV'})
    with a2:
        _wz31_action_card('Find / Analyze Jobs', 'Use this when your CV score is good and you need real jobs or a job-fit check.', 'Open Job Assist', 'job_assist', 'wz31_open_jobs')
    with a3:
        _wz31_action_card('Cover Letter', 'Use company, job description, and CV context to write a focused cover letter.', 'Create Cover Letter', 'cv_documents', 'wz31_open_cover', {'document_tools_mode':'Cover Letter Generator + Language'})
    with a4:
        _wz31_action_card('Work-O-Bot', 'Ask career questions or practice interview answers in your selected language.', 'Ask Work-O-Bot', 'workobot', 'wz31_open_bot')

    st.markdown('### Application flow')
    improved_ready = bool(str(st.session_state.get('improved_cv_text','') or st.session_state.get('latest_improved_cv','') or st.session_state.get('final_cv_text','')).strip())
    cover_ready = bool(str(st.session_state.get('latest_cover_letter','') or st.session_state.get('cover_letter_text','')).strip())
    flow = [
        ('1. CV added', cv_exists),
        ('2. Resume + ATS checked', bool(cv_exists and resume_score > 0 and ats_score > 0)),
        ('3. Job added', job_exists),
        ('4. CV tailored', improved_ready or (job_exists and resume_score >= 75 and ats_score >= 75)),
        ('5. Cover letter / prep', cover_ready),
    ]
    html_steps = []
    for label, done in flow:
        html_steps.append(f"<div class='wz31-step {'done' if done else ''}'><div class='wz31-step-title'>{'✅ ' if done else '○ '}{_wz31_escape(label)}</div><div class='wz31-step-sub'>{'Complete' if done else 'Next step pending'}</div></div>")
    st.markdown("<div class='wz31-flow'>" + "".join(html_steps) + "</div>", unsafe_allow_html=True)

    st.caption('Scores are guidance only. WorkZo should not invent skills, company facts, language level, salary, or experience.')

# =========================================================
# WorkZo v32 - smarter dashboard, score memory, no dashboard job-fit card
# =========================================================
def _wz32_force_scroll_top():
    try:
        st.markdown('<span id="workzo-page-top"></span>', unsafe_allow_html=True)
        script = """
        <script>
        const scrollTop = () => {
          try { window.parent.scrollTo(0,0); } catch(e) {}
          try { window.scrollTo(0,0); } catch(e) {}
          try {
            const doc = window.parent.document;
            const candidates = [
              doc.querySelector('section.main'),
              doc.querySelector('div[data-testid="stAppViewContainer"]'),
              doc.querySelector('.main'),
              doc.scrollingElement,
              doc.documentElement,
              doc.body
            ].filter(Boolean);
            candidates.forEach(el => { try { el.scrollTop = 0; } catch(e) {} });
          } catch(e) {}
        };
        scrollTop(); setTimeout(scrollTop, 80); setTimeout(scrollTop, 250);
        </script>
        """
        if hasattr(st, 'iframe'):
            st.iframe(srcdoc=script, height=1, width=1)
        else:
            st.markdown(script, unsafe_allow_html=True)
    except Exception:
        pass

def _wz32_remember_best_scores():
    try:
        for key in ['cv_score_value', 'ats_score_value', 'application_readiness_value', 'job_fit_score_value', 'interview_score']:
            cur = st.session_state.get(key)
            if cur is None or str(cur).strip() == '':
                continue
            try:
                cur_i = max(0, min(100, int(float(cur))))
            except Exception:
                continue
            best_key = '_best_' + key
            best_i = int(st.session_state.get(best_key) or 0)
            if cur_i > best_i:
                st.session_state[best_key] = cur_i
    except Exception:
        pass

def _wz32_restore_best_scores():
    try:
        for key in ['cv_score_value', 'ats_score_value', 'application_readiness_value', 'job_fit_score_value', 'interview_score']:
            best_key = '_best_' + key
            best = int(st.session_state.get(best_key) or 0)
            cur = st.session_state.get(key)
            try:
                cur_i = int(float(cur or 0))
            except Exception:
                cur_i = 0
            if best > 0 and cur_i <= 0:
                st.session_state[key] = best
            elif cur_i > best:
                st.session_state[best_key] = cur_i
    except Exception:
        pass

def _wz32_flow_step(label, done, current=False, note=''):
    # Keep this HTML on one line. Leading spaces/newlines can make Streamlit
    # render later cards as a code block instead of HTML.
    cls = 'done' if done else ('current' if current else '')
    icon = '✅' if done else ('➜' if current else '○')
    state = 'Complete' if done else ('Recommended now' if current else 'Pending')
    style = 'border-color:rgba(96,165,250,.55);background:rgba(37,99,235,.14);' if current and not done else ''
    return f"<div class='wz31-step {cls}' style='{style}'><div class='wz31-step-title'>{icon} {_wz31_escape(label)}</div><div class='wz31-step-sub'>{_wz31_escape(note or state)}</div></div>"

def _wz32_pick_current_step(cv_exists, resume_score, ats_score, job_exists, improved_ready, cover_ready):
    if not cv_exists:
        return 0
    if resume_score < 75 or ats_score < 75:
        return 1
    if not job_exists:
        return 2
    if not improved_ready:
        return 3
    if not cover_ready:
        return 4
    return 5

def _wz32_dashboard_home():
    _wz32_restore_best_scores()
    _wz32_force_scroll_top()
    _wz28_css()
    _wz31_css()
    st.markdown("""
    <style>
      .workzo-header{margin-bottom:14px!important;}
      .wz31-hero{margin-top:0!important;margin-bottom:18px!important;}
      .wz31-flow{grid-template-columns:repeat(auto-fit,minmax(185px,1fr));}
      .wz31-step{min-height:86px;}
      .wz32-explain{color:#94a3b8;font-size:.9rem;margin:-4px 0 14px;}
    </style>
    """, unsafe_allow_html=True)

    cv_exists = bool(str(st.session_state.get('cv_text','')).strip() or st.session_state.get('structured_cv_json'))
    job_text = str(st.session_state.get('current_job_description','') or st.session_state.get('last_understand_job_description','') or st.session_state.get('improve_cv_for_job_desc','') or st.session_state.get('job_description','')).strip()
    job_exists = bool(job_text)
    company = str(st.session_state.get('target_company') or st.session_state.get('prepare_target_company') or '').strip()
    country = str(st.session_state.get('country') or st.session_state.get('target_country') or 'Not set')
    language = str(st.session_state.get('preferred_language') or st.session_state.get('language') or 'English')

    resume_score = _wz31_get_score('cv_score_value', 'resume_score', 'resume_quality_score', '_best_cv_score_value', default=0)
    ats_score = _wz31_get_score('ats_score_value', 'ats_score', '_best_ats_score_value', default=0)
    if cv_exists and resume_score <= 0:
        resume_score = int(st.session_state.get('_best_cv_score_value') or 75)
    if cv_exists and ats_score <= 0:
        ats_score = int(st.session_state.get('_best_ats_score_value') or 70)
    interview_score = _wz31_get_score('interview_score', 'interview_readiness', '_best_interview_score', default=0)
    if interview_score <= 0:
        if cv_exists and job_exists and resume_score >= 75 and ats_score >= 75:
            interview_score = 65
        elif cv_exists:
            interview_score = 45
        else:
            interview_score = 0

    improved_ready = bool(str(st.session_state.get('improved_cv_text','') or st.session_state.get('latest_improved_cv','') or st.session_state.get('final_cv_text','')).strip())
    cover_ready = bool(str(st.session_state.get('latest_cover_letter','') or st.session_state.get('cover_letter_text','')).strip())
    next_action = _wz31_pick_next_action(cv_exists, job_exists, resume_score, ats_score, _wz31_get_score('job_fit_score_value','_best_job_fit_score_value', default=0), interview_score)

    st.markdown(f"""
    <div class='wz31-hero'>
      <div class='wz31-kicker'>WorkZo Command Center</div>
      <div class='wz31-title'>Your next best move is clear.</div>
      <div class='wz31-sub'>WorkZo recommends the next step based on your CV strength, ATS readiness, job context, and application progress.</div>
      <div class='wz31-chip-row'>
        <span class='wz31-chip'>{_wz31_escape(country)}</span>
        <span class='wz31-chip'>{_wz31_escape(language)}</span>
        <span class='wz31-chip'>{'CV ready' if cv_exists else 'CV missing'}</span>
        <span class='wz31-chip'>{'Job added' if job_exists else 'Job not added'}</span>
        <span class='wz31-chip'>{_wz31_escape(company or 'Company not added')}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class='wz31-next'>
      <div class='wz31-next-label'>Recommended next step</div>
      <div class='wz31-next-title'>{_wz31_escape(next_action['title'])}</div>
      <div class='wz31-next-copy'>{_wz31_escape(next_action['copy'])}</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button(next_action['button'], key='wz32_primary_next_action', use_container_width=True):
        if next_action['target'] == 'cv_documents' and job_exists:
            st.session_state['document_tools_mode'] = 'Improve CV for a Job'
        _wz28_go(next_action['target'])

    st.markdown('### Readiness overview')
    st.markdown("<div class='wz32-explain'>Job Fit is now shown inside Understand Job after a job description is analyzed.</div>", unsafe_allow_html=True)
    r1, r2, r3 = st.columns(3)
    with r1:
        _wz31_rate_card('Resume Score', resume_score, 'Clarity, structure, achievements, and overall CV quality.', missing=not cv_exists)
    with r2:
        _wz31_rate_card('ATS Score', ats_score, 'Scanner-friendly formatting, keywords, sections, and parsing safety.', missing=not cv_exists)
    with r3:
        _wz31_rate_card('Interview Readiness', interview_score, 'How ready you are to explain this CV and job fit clearly.', missing=not cv_exists)

    st.markdown('### Smart actions')
    a1, a2, a3, a4 = st.columns(4)
    with a1:
        _wz31_action_card('Improve CV', 'Use this when Resume or ATS score is below 75, or when you want to tailor for one job.', 'Open CV Tools', 'cv_documents', 'wz32_open_cv', {'document_tools_mode':'Improve CV for a Job' if job_exists else 'Improve / Update CV'})
    with a2:
        _wz31_action_card('Job Match', 'Find jobs or analyze a pasted job description when your CV and ATS scores are ready.', 'Open Job Match', 'job_assist', 'wz32_open_jobs')
    with a3:
        _wz31_action_card('Cover Letter', 'Use company, job description, and CV context to write a focused cover letter.', 'Create Cover Letter', 'cv_documents', 'wz32_open_cover', {'document_tools_mode':'Cover Letter Generator + Language'})
    with a4:
        _wz31_action_card('Work-O-Bot', 'Ask career questions or practice interview answers in your selected language.', 'Ask Work-O-Bot', 'workobot', 'wz32_open_bot')

    # Persist only safe progress flags. Do not store CV text or job descriptions.
    if cv_exists:
        st.session_state['_wz_has_cv'] = True
    if improved_ready:
        st.session_state['_wz_cv_improved'] = True
    if bool(st.session_state.get('latest_curated_jobs') or st.session_state.get('latest_job_query_expansion')):
        st.session_state['_wz_job_found'] = True
    if job_exists or st.session_state.get('latest_job_analysis'):
        st.session_state['_wz_job_analyzed'] = True
    prepared_ready = bool(cover_ready or str(st.session_state.get('latest_application_prep','') or st.session_state.get('latest_cover_letter','')).strip())
    if prepared_ready:
        st.session_state['_wz_prepared'] = True

    # Use restored memory after refresh, but never invent private CV/job text.
    cv_done = bool(cv_exists or st.session_state.get('_wz_has_cv'))
    improved_done = bool(improved_ready or st.session_state.get('_wz_cv_improved'))
    job_done = bool(job_exists or st.session_state.get('_wz_job_found') or st.session_state.get('_wz_job_analyzed'))
    prep_done = bool(prepared_ready or st.session_state.get('_wz_prepared'))

    st.markdown('### Application progress')
    st.caption('Move step by step. Each card is checked only after that action is actually done.')

    # Current recommendation: the first unfinished step becomes highlighted.
    if not cv_done:
        current_key = 'cv'
    elif resume_score < 75 or ats_score < 75 or not improved_done:
        current_key = 'improve'
    elif not job_done:
        current_key = 'job'
    elif not prep_done:
        current_key = 'prepare'
    else:
        current_key = 'done'

    progress_items = [
        ('cv', '1. CV uploaded', cv_done, 'CV added' if cv_done else 'Upload or create your CV', 'Edit onboarding', 'onboarding', {}),
        ('improve', '2. CV improved', improved_done, 'Improved / tailored' if improved_done else 'Improve Resume + ATS score', 'Improve CV', 'cv_documents', {'document_tools_mode':'Improve / Update CV'}),
        ('job', '3. Job matched', job_done, 'Job found or analyzed' if job_done else 'Find jobs or analyze one JD', 'Job Match', 'job_assist', {'job_assist_mode_key':'find'}),
        ('prepare', '4. Prepared for job', prep_done, 'Cover letter / prep done' if prep_done else 'Prepare cover letter and interview notes', 'Prepare', 'job_assist', {'job_assist_mode_key':'prepare'}),
    ]

    cols = st.columns(4)
    for idx, (step_key, label, done, note, button_label, target, extra_state) in enumerate(progress_items):
        with cols[idx]:
            st.markdown(_wz32_flow_step(label, done, current_key == step_key, note), unsafe_allow_html=True)
    try:
        readiness = int(round((sum([cv_done, improved_done, job_done, prep_done]) / 4) * 100))
        st.session_state['application_readiness_value'] = max(int(st.session_state.get('application_readiness_value') or 0), readiness)
    except Exception:
        pass

    st.caption('Scores are guidance only. WorkZo should not invent skills, company facts, language level, salary, or experience.')
    _wz32_remember_best_scores()
    try:
        if callable(globals().get('workzo_save_light_memory')):
            workzo_save_light_memory()
    except Exception:
        pass

# Replace dashboard home with v32 smart version.
_wz28_dashboard_home = _wz32_dashboard_home

# Put Job Fit where it belongs: inside Understand Job analysis.
try:
    _wz32_old_render_understand_job_analysis = render_understand_job_analysis
    def render_understand_job_analysis(data):
        try:
            score = 0
            if isinstance(data, dict):
                score = _wz31_clamp_score(data.get('fit_score') or data.get('job_fit') or data.get('match_score') or 0)
                if score:
                    st.session_state['job_fit_score_value'] = score
                    _wz32_remember_best_scores()
            if score:
                st.markdown('### Job Fit')
                _wz31_rate_card('Job Fit', score, 'Fit for this specific pasted job description. Use this only after reviewing the requirement checklist.', missing=False)
        except Exception:
            pass
        return _wz32_old_render_understand_job_analysis(data)
except Exception:
    pass

# Keep scores alive when returning home or switching pages.
try:
    _wz32_old_show_dashboard = show_dashboard
    def show_dashboard():
        _wz32_restore_best_scores()
        try:
            _wz32_force_scroll_top()
        except Exception:
            pass
        result = _wz32_old_show_dashboard()
        _wz32_remember_best_scores()
        _wz32_restore_best_scores()
        return result
except Exception:
    pass


# =========================================================
# WorkZo v35 - stable startup command center
# Fixes: clean application progress, smaller header gap, score memory,
# edit setup routing, language sync, and old Job Assist layout routing.
# =========================================================
import json as _wz35_json
import os as _wz35_os
import time as _wz35_time
import html as _wz35_html


def _wz35_escape(value):
    try:
        return _wz35_html.escape(str(value or ""))
    except Exception:
        return str(value or "")


def _wz35_qp_get(key, default=""):
    try:
        v = st.query_params.get(key, default)
        if isinstance(v, list):
            return v[0] if v else default
        return v or default
    except Exception:
        return default


def _wz35_get_uid():
    """Persistent-enough anonymous browser id using URL query params.
    This is used only for non-sensitive UI state such as scores/language.
    """
    try:
        uid = _wz35_qp_get("wz_uid", "") or st.session_state.get("anonymous_user_id", "")
        if not uid:
            import uuid as _uuid
            uid = str(_uuid.uuid4())
        st.session_state["anonymous_user_id"] = uid
        try:
            if not _wz35_qp_get("wz_uid", ""):
                st.query_params["wz_uid"] = uid
        except Exception:
            pass
        return uid
    except Exception:
        return "local"


def _wz35_state_file():
    try:
        base = globals().get("BASE_DIR") or _wz35_os.getcwd()
        safe_uid = "".join(ch for ch in str(_wz35_get_uid()) if ch.isalnum() or ch in "-_")[:80]
        return _wz35_os.path.join(base, f"workzo_ui_state_{safe_uid}.json")
    except Exception:
        return "workzo_ui_state_local.json"


def _wz35_save_state():
    """Save non-sensitive state only. Do not store full CV text or documents."""
    try:
        keys = [
            "cv_score_value", "ats_score_value", "application_readiness_value",
            "job_fit_score_value", "interview_score", "country", "preferred_language",
            "ui_language", "response_language", "language", "target_company_website",
            "target_company", "prepare_target_company", "nav_page", "page",
            "last_understand_job_description", "current_job_description", "job_description",
            "improved_cv_text", "latest_improved_cv", "latest_cover_letter", "latest_application_prep",
            "_workzo_has_cv", "_best_cv_score_value", "_best_ats_score_value", "_best_application_readiness_value",
        ]
        data = {}
        for k in keys:
            v = st.session_state.get(k)
            if isinstance(v, (str, int, float, bool)) or v is None:
                # keep job description short enough for context, not full private docs
                if k in ["last_understand_job_description", "current_job_description", "job_description"] and isinstance(v, str):
                    v = v[:5000]
                data[k] = v
        cv_present = bool(str(st.session_state.get("cv_text", "")).strip() or st.session_state.get("structured_cv_json"))
        data["_workzo_has_cv"] = bool(cv_present or st.session_state.get("_workzo_has_cv"))
        with open(_wz35_state_file(), "w", encoding="utf-8") as f:
            _wz35_json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _wz35_load_state():
    try:
        path = _wz35_state_file()
        if not _wz35_os.path.exists(path):
            return
        with open(path, "r", encoding="utf-8") as f:
            data = _wz35_json.load(f)
        if not isinstance(data, dict):
            return
        for k, v in data.items():
            if k not in st.session_state or st.session_state.get(k) in [None, "", 0]:
                st.session_state[k] = v
        # restore best scores into active score keys when missing
        for key in ["cv_score_value", "ats_score_value", "application_readiness_value"]:
            best = int(st.session_state.get("_best_" + key) or 0)
            cur = int(st.session_state.get(key) or 0)
            if best > cur:
                st.session_state[key] = best
    except Exception:
        pass


def _wz35_remember_scores():
    try:
        for key in ["cv_score_value", "ats_score_value", "application_readiness_value", "job_fit_score_value", "interview_score"]:
            try:
                cur = int(float(st.session_state.get(key) or 0))
            except Exception:
                cur = 0
            if cur > 0:
                best_key = "_best_" + key
                st.session_state[best_key] = max(cur, int(st.session_state.get(best_key) or 0))
    except Exception:
        pass


def _wz35_force_scroll_top():
    try:
        st.markdown('<span id="workzo-page-top"></span>', unsafe_allow_html=True)
        script = """
        <script>
        const wzScrollTop = () => {
          try { window.scrollTo(0,0); } catch(e) {}
          try { window.parent.scrollTo(0,0); } catch(e) {}
          try {
            const d = window.parent.document;
            [d.scrollingElement, d.documentElement, d.body,
             d.querySelector('section.main'),
             d.querySelector('div[data-testid="stAppViewContainer"]'),
             d.querySelector('.main')].filter(Boolean).forEach(el => { try { el.scrollTop = 0; } catch(e) {} });
          } catch(e) {}
        };
        wzScrollTop(); setTimeout(wzScrollTop, 50); setTimeout(wzScrollTop, 250); setTimeout(wzScrollTop, 700);
        </script>
        """
        if hasattr(st, "iframe"):
            st.iframe(srcdoc=script, height=1, width=1)
        else:
            st.markdown(script, unsafe_allow_html=True)
    except Exception:
        pass


def _wz35_sync_language(value=None):
    try:
        lang = value or st.session_state.get("preferred_language") or st.session_state.get("language") or "English"
        st.session_state["preferred_language"] = lang
        st.session_state["language"] = lang
        st.session_state["response_language"] = lang
        try:
            st.session_state["ui_language"] = lang if "UI_TEXT" in globals() and lang in UI_TEXT else "English"
        except Exception:
            st.session_state["ui_language"] = lang
        if callable(globals().get("set_single_preferred_language")):
            try:
                set_single_preferred_language(lang)
            except Exception:
                pass
    except Exception:
        pass


def _wz35_go(page, extra=None):
    try:
        if isinstance(extra, dict):
            for k, v in extra.items():
                st.session_state[k] = v
        st.session_state["page"] = page
        st.session_state["nav_page"] = page
        try:
            st.query_params["page"] = page
            st.query_params["wz_top"] = str(int(_wz35_time.time() * 1000))
        except Exception:
            pass
        try:
            request_scroll_to_top()
        except Exception:
            pass
        _wz35_save_state()
        st.rerun()
    except Exception:
        pass


def _wz35_score(*keys, default=0):
    for key in keys:
        try:
            value = st.session_state.get(key)
            if value not in [None, ""]:
                n = int(float(value))
                if n > 0:
                    return max(0, min(100, n))
        except Exception:
            pass
    return default


def _wz35_css():
    try:
        st.markdown("""
        <style>
        .block-container{padding-top:.55rem!important;max-width:1220px!important;}
        .workzo-header{margin-top:4px!important;margin-bottom:12px!important;}
        .wz35-hero{border:1px solid rgba(20,184,166,.28);border-radius:24px;padding:20px 24px;background:linear-gradient(135deg,rgba(20,184,166,.16),rgba(37,99,235,.14));box-shadow:0 12px 35px rgba(2,6,23,.22);margin:10px 0 18px;}
        .wz35-kicker{color:#93c5fd;text-transform:uppercase;letter-spacing:.08em;font-weight:850;font-size:.78rem;margin-bottom:7px;}
        .wz35-title{color:#fff;font-weight:900;font-size:1.75rem;line-height:1.18;margin-bottom:7px;}
        .wz35-sub{color:#dbeafe;font-size:.98rem;line-height:1.45;}
        .wz35-chip-row{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px;}
        .wz35-chip{border:1px solid rgba(96,165,250,.26);background:rgba(37,99,235,.16);color:#dbeafe;border-radius:999px;padding:6px 11px;font-weight:700;font-size:.84rem;}
        .wz35-next{border:1px solid rgba(45,212,191,.34);background:linear-gradient(135deg,rgba(20,184,166,.18),rgba(15,23,42,.58));border-radius:20px;padding:17px 18px;margin:12px 0 18px;}
        .wz35-next-label{color:#99f6e4;font-size:.78rem;text-transform:uppercase;letter-spacing:.07em;font-weight:850;margin-bottom:4px;}
        .wz35-next-title{font-size:1.25rem;color:#fff;font-weight:900;margin-bottom:5px;}
        .wz35-next-copy{color:#cbd5e1;font-size:.96rem;line-height:1.45;}
        .wz35-rate{border:1px solid rgba(148,163,184,.17);background:linear-gradient(180deg,rgba(30,41,59,.78),rgba(15,23,42,.72));border-radius:20px;padding:18px;min-height:160px;}
        .wz35-rate-title{color:#fff;font-weight:900;font-size:1rem;display:flex;justify-content:space-between;gap:8px;}
        .wz35-rate-value{color:#fff;font-size:2rem;font-weight:900;margin:12px 0 8px;}
        .wz35-bar{height:10px;border-radius:999px;background:rgba(148,163,184,.20);overflow:hidden;margin:6px 0 12px;}
        .wz35-fill{height:100%;border-radius:999px;background:linear-gradient(90deg,#38bdf8,#2dd4bf);}
        .wz35-rate-copy{color:#bfdbfe;font-size:.9rem;line-height:1.4;}
        .wz35-action{border:1px solid rgba(148,163,184,.16);background:rgba(15,23,42,.52);border-radius:20px;padding:18px;min-height:150px;}
        .wz35-action-title{color:#fff;font-weight:900;font-size:1.06rem;margin-bottom:8px;}
        .wz35-action-copy{color:#bfdbfe;font-size:.93rem;line-height:1.45;min-height:62px;}
        .wz35-flow-card{border:1px solid rgba(148,163,184,.17);background:rgba(15,23,42,.50);border-radius:18px;padding:16px 18px;min-height:108px;}
        .wz35-flow-card.done{border-color:rgba(45,212,191,.45);background:rgba(20,184,166,.13);}
        .wz35-flow-card.current{border-color:rgba(96,165,250,.58);background:rgba(37,99,235,.14);}
        .wz35-flow-title{font-weight:900;color:#fff;font-size:.96rem;line-height:1.35;}
        .wz35-flow-note{color:#bfdbfe;font-size:.84rem;margin-top:8px;line-height:1.35;}
        </style>
        """, unsafe_allow_html=True)
    except Exception:
        pass


def _wz35_rate_card(title, score, copy, missing=False):
    if missing or not score:
        value = "—"
        width = 0
    else:
        value = f"{int(score)}%"
        width = max(0, min(100, int(score)))
    st.markdown(f"""
    <div class='wz35-rate'>
      <div class='wz35-rate-title'><span>{_wz35_escape(title)}</span></div>
      <div class='wz35-rate-value'>{_wz35_escape(value)}</div>
      <div class='wz35-bar'><div class='wz35-fill' style='width:{width}%;'></div></div>
      <div class='wz35-rate-copy'>{_wz35_escape(copy)}</div>
    </div>
    """, unsafe_allow_html=True)


def _wz35_action_card(title, copy, button, target, key, extra=None):
    st.markdown(f"""
    <div class='wz35-action'>
      <div class='wz35-action-title'>{_wz35_escape(title)}</div>
      <div class='wz35-action-copy'>{_wz35_escape(copy)}</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button(button, key=key, use_container_width=True):
        _wz35_go(target, extra)


def _wz35_flow_card(label, done, current, note):
    cls = "done" if done else ("current" if current else "")
    icon = "✅" if done else ("➜" if current else "○")
    st.markdown(f"""
    <div class='wz35-flow-card {cls}'>
      <div class='wz35-flow-title'>{icon} {_wz35_escape(label)}</div>
      <div class='wz35-flow-note'>{_wz35_escape(note)}</div>
    </div>
    """, unsafe_allow_html=True)


def _wz35_next_action(cv_exists, resume_score, ats_score, job_exists, improved_ready, prepared_ready):
    if not cv_exists:
        return {"title":"Start with your CV", "copy":"Upload or create your CV first so WorkZo can score it and guide the next steps.", "button":"Add CV", "target":"onboarding", "extra":{}}
    if resume_score < 75 or ats_score < 75:
        return {"title":"Improve your CV first", "copy":"Your Resume or ATS score needs improvement. Fix structure, keywords, and role alignment before applying widely.", "button":"Open CV Tools", "target":"cv_documents", "extra":{"document_tools_mode":"Improve / Update CV"}}
    if not job_exists:
        return {"title":"Find or analyze a job next", "copy":"Your CV is ready enough. Now find matching roles or paste one job description for a fit check.", "button":"Open Job Assist", "target":"job_assist", "extra":{"job_assist_mode_key":"find"}}
    if not improved_ready:
        return {"title":"Tailor your CV for this job", "copy":"You have job context. Now tailor the CV to this specific role before creating application materials.", "button":"Improve CV for Job", "target":"cv_documents", "extra":{"document_tools_mode":"Improve CV for a Job"}}
    if not prepared_ready:
        return {"title":"Prepare the application", "copy":"Create a focused cover letter and preparation notes using the company, CV, and job description.", "button":"Prepare Application", "target":"job_assist", "extra":{"job_assist_mode_key":"prepare"}}
    return {"title":"Ready to apply", "copy":"Your core application flow is complete. Apply, save the tracker item, and practice answers in Work-O-Bot.", "button":"Practice with Work-O-Bot", "target":"workobot", "extra":{}}


def _wz35_sidebar(page_key):
    with st.sidebar:
        try:
            logo_src = image_to_data_uri(ICON_PATH) or image_to_data_uri(LOGO_PATH)
        except Exception:
            logo_src = None
        if logo_src:
            st.markdown(f"""
            <div class='workzo-sidebar-brand-wrap'>
              <img src='{logo_src}' class='workzo-sidebar-logo' alt='WorkZo AI logo'>
              <div><div class='workzo-sidebar-brand'>WORKZO AI</div><div class='workzo-sidebar-version'>Beta · guided workspace</div></div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("### WorkZo AI")
        navs = [("dashboard", txt("dashboard")), ("cv_documents", txt("cv_documents")), ("job_assist", txt("job_assist")), ("workobot", "Work-O-Bot")]
        for key, label in navs:
            text = label + ("  ✓" if page_key == key else "")
            if st.button(text, key=f"wz35_nav_{key}", use_container_width=True):
                _wz35_go(key)
        st.markdown(f"<div class='workzo-sidebar-section-label'>{html.escape(txt('company_context'))}</div>", unsafe_allow_html=True)
        with st.expander("🏢 " + txt("company_website"), expanded=False):
            company_url = st.text_input(txt("company_website"), key="target_company_website", placeholder="https://company.com")
            if company_url:
                st.caption(ui_label("Used for cover letters and job/interview preparation context."))
        st.markdown(f"<div class='workzo-sidebar-section-label'>{html.escape(txt('language'))}</div>", unsafe_allow_html=True)
        try:
            langs = language_options if "language_options" in globals() and language_options else ["English", "German", "Dutch", "French", "Spanish", "Portuguese"]
        except Exception:
            langs = ["English", "German", "Dutch", "French", "Spanish", "Portuguese"]
        cur = st.session_state.get("preferred_language") or st.session_state.get("language") or "English"
        if cur not in langs:
            cur = "English" if "English" in langs else langs[0]
        def _wz39_language_changed():
            _new_lang = st.session_state.get("wz39_preferred_language", cur)
            try:
                if callable(globals().get("workzo_set_language_everywhere")):
                    workzo_set_language_everywhere(_new_lang)
                else:
                    set_single_preferred_language(_new_lang)
                st.query_params["wz_lang"] = _new_lang
            except Exception:
                pass
        if st.session_state.get("wz39_preferred_language") != cur:
            st.session_state["wz39_preferred_language"] = cur
        chosen = st.selectbox(txt("preferred_language"), langs, index=langs.index(cur), key="wz39_preferred_language", on_change=_wz39_language_changed)
        _wz35_sync_language(chosen)
        st.markdown("---")
        if st.button(txt("edit_setup"), key="wz35_edit_setup", use_container_width=True):
            st.session_state["onboarding_complete"] = False
            st.session_state["page"] = "onboarding"
            st.session_state["nav_page"] = "onboarding"
            try:
                st.query_params["page"] = "onboarding"
            except Exception:
                pass
            _wz35_save_state()
            st.rerun()


def _wz35_dashboard_home():
    _wz35_load_state()
    _wz35_remember_scores()
    _wz35_force_scroll_top()
    _wz35_css()

    cv_exists = bool(str(st.session_state.get("cv_text", "")).strip() or st.session_state.get("structured_cv_json") or st.session_state.get("_workzo_has_cv"))
    if cv_exists:
        st.session_state["_workzo_has_cv"] = True
    job_text = str(st.session_state.get("current_job_description", "") or st.session_state.get("last_understand_job_description", "") or st.session_state.get("improve_cv_for_job_desc", "") or st.session_state.get("job_description", "")).strip()
    job_exists = bool(job_text)
    improved_ready = bool(str(st.session_state.get("improved_cv_text", "") or st.session_state.get("latest_improved_cv", "") or st.session_state.get("final_cv_text", "")).strip())
    prepared_ready = bool(str(st.session_state.get("latest_application_prep", "") or st.session_state.get("latest_cover_letter", "") or st.session_state.get("cover_letter_text", "")).strip())
    resume_score = _wz35_score("cv_score_value", "resume_score", "resume_quality_score", "_best_cv_score_value", default=76 if cv_exists else 0)
    ats_score = _wz35_score("ats_score_value", "ats_score", "_best_ats_score_value", default=70 if cv_exists else 0)
    interview_score = _wz35_score("interview_score", "interview_readiness", "_best_interview_score", default=65 if cv_exists and job_exists and resume_score >= 75 and ats_score >= 75 else (40 if cv_exists else 0))

    country = st.session_state.get("country") or st.session_state.get("target_country") or "Not set"
    language = st.session_state.get("preferred_language") or st.session_state.get("language") or "English"
    company = st.session_state.get("prepare_target_company") or st.session_state.get("target_company") or st.session_state.get("target_company_website") or ui_label("Company not added")
    next_action = _wz35_next_action(cv_exists, resume_score, ats_score, job_exists, improved_ready, prepared_ready)

    st.markdown(f"""
    <div class='wz35-hero'>
      <div class='wz35-kicker'>{_wz35_escape(txt('workzo_command_center'))}</div>
      <div class='wz35-title'>{_wz35_escape(txt('next_best_move_clear'))}</div>
      <div class='wz35-sub'>{_wz35_escape(txt('next_best_move_copy'))}</div>
      <div class='wz35-chip-row'>
        <span class='wz35-chip'>{_wz35_escape(country)}</span>
        <span class='wz35-chip'>{_wz35_escape(language)}</span>
        <span class='wz35-chip'>{_wz35_escape(ui_label('CV ready') if cv_exists else ui_label('CV missing'))}</span>
        <span class='wz35-chip'>{_wz35_escape(ui_label('Job added') if job_exists else ui_label('Job not added'))}</span>
        <span class='wz35-chip'>{_wz35_escape(company)}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class='wz35-next'>
      <div class='wz35-next-label'>{_wz35_escape(txt('recommended_next_step'))}</div>
      <div class='wz35-next-title'>{_wz35_escape(next_action['title'])}</div>
      <div class='wz35-next-copy'>{_wz35_escape(next_action['copy'])}</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button(next_action["button"], key="wz35_primary_action", use_container_width=True):
        _wz35_go(next_action["target"], next_action.get("extra"))

    st.markdown("### " + txt("readiness_overview"))
    c1, c2, c3 = st.columns(3)
    with c1:
        _wz35_rate_card(txt("resume_score"), resume_score, ui_label("Clarity, structure, achievements, and overall CV quality."), missing=not cv_exists)
    with c2:
        _wz35_rate_card(txt("ats_score"), ats_score, ui_label("Scanner-friendly formatting, role keywords, sections, and parsing safety."), missing=not cv_exists)
    with c3:
        _wz35_rate_card(txt("interview_readiness"), interview_score, ui_label("How ready you are to explain your CV and job fit clearly."), missing=not cv_exists)

    st.markdown("### " + txt("smart_actions"))
    a1, a2, a3, a4 = st.columns(4)
    with a1:
        _wz35_action_card(txt("improve_cv"), ui_label("Use this when Resume or ATS score is below 75, or when tailoring for one job."), txt("open_cv_tools"), "cv_documents", "wz35_action_cv", {"document_tools_mode":"Improve CV for a Job" if job_exists else "Improve / Update CV"})
    with a2:
        _wz35_action_card(txt("job_match"), ui_label("Search jobs for the selected country, then analyze one job description for fit."), txt("open_job_assist"), "job_assist", "wz35_action_jobs", {"job_assist_mode_key":"find"})
    with a3:
        _wz35_action_card(txt("cover_letter"), ui_label("Use CV, job description, and company context to create a focused cover letter."), txt("create_cover_letter"), "cv_documents", "wz35_action_cover", {"document_tools_mode":"Cover Letter Generator + Language"})
    with a4:
        _wz35_action_card("Work-O-Bot", ui_label("Ask career questions or practice interview answers in your selected language."), txt("ask_workobot"), "workobot", "wz35_action_bot")

    st.markdown("### " + txt("application_progress"))
    st.caption(ui_label("Move step by step, or jump to the part you want to work on."))
    score_checked = bool(cv_exists and resume_score > 0 and ats_score > 0)
    if not cv_exists:
        current = 0
    elif not score_checked or resume_score < 75 or ats_score < 75:
        current = 1
    elif not job_exists:
        current = 2
    elif not improved_ready:
        current = 3
    elif not prepared_ready:
        current = 4
    else:
        current = 5
    flow = [
        ("1. " + txt("cv_added"), cv_exists, txt("completed") if cv_exists else ui_label("Upload or create CV"), txt("edit_setup"), "cv_documents", {"document_tools_mode":"Improve / Update CV"}),
        ("2. " + txt("resume_ats_checked"), score_checked and resume_score >= 75 and ats_score >= 75, ui_label("Good") if score_checked and resume_score >= 75 and ats_score >= 75 else ui_label("Improve scores above 75"), txt("improve_cv"), "cv_documents", {"document_tools_mode":"Improve / Update CV"}),
        ("3. " + txt("job_analyzed"), job_exists, txt("completed") if job_exists else ui_label("Paste/analyze one job"), txt("understand_job"), "job_assist", {"job_assist_mode_key":"understand"}),
        ("4. " + txt("cv_improved"), improved_ready, txt("completed") if improved_ready else ui_label("Tailor CV to the job"), txt("improve_cv"), "cv_documents", {"document_tools_mode":"Improve CV for a Job" if job_exists else "Improve / Update CV"}),
        ("5. " + txt("prepared_to_apply"), prepared_ready, txt("completed") if prepared_ready else ui_label("Prepare application"), txt("prepare_this_job"), "job_assist", {"job_assist_mode_key":"prepare"}),
    ]
    cols = st.columns(5)
    for i, (label, done, note, button, target, extra) in enumerate(flow):
        with cols[i]:
            _wz35_flow_card(label, done, current == i, note)
    st.caption(ui_label("Scores are guidance only. WorkZo should not invent skills, company facts, language level, salary, or experience."))
    _wz35_remember_scores()
    _wz35_save_state()


# Final clean router. This avoids older dashboard wrappers that printed raw HTML.
def show_dashboard():
    _wz35_load_state()
    _wz35_sync_language()
    _wz35_force_scroll_top()
    page_key = st.session_state.get("nav_page") or st.session_state.get("page") or "dashboard"
    page_key = {"landing":"dashboard", "bot":"workobot", "interview":"workobot", "jobs":"job_assist", "improve_cv":"cv_documents"}.get(page_key, page_key)
    if page_key == "interview_practice":
        page_key = "workobot"
    if page_key not in {"dashboard", "cv_documents", "job_assist", "workobot"}:
        page_key = "dashboard"
    st.session_state["page"] = page_key
    st.session_state["nav_page"] = page_key
    try:
        _wz28_top(True)
    except Exception:
        pass
    _wz35_sidebar(page_key)
    if page_key == "dashboard":
        _wz35_dashboard_home()
    elif page_key == "cv_documents":
        _wz35_css()
        show_document_tools()
    elif page_key == "job_assist":
        _wz35_css()
        # Use the older Job Assist page layout if available.
        try:
            _wz28_job_assist_page()
        except Exception:
            st.subheader(txt("job_assist"))
            tab1, tab2, tab3 = st.tabs([txt("find_jobs"), txt("understand_job"), txt("prepare_this_job")])
            with tab1:
                st.info("Job search module could not be loaded.")
            with tab2:
                st.info("Understand Job module could not be loaded.")
            with tab3:
                st.info("Prepare module could not be loaded.")
    elif page_key == "workobot":
        _wz35_css()
        show_workobot()
    _wz35_remember_scores()
    _wz35_save_state()

# =========================================================
# WorkZo v36 LANGUAGE SYNC + SMART CONTEXT PATCH
# Dashboard language dropdown now updates the whole app consistently.
# Smart stage flags allow features to adapt based on CV/ATS/job situation.
# =========================================================
def _wz36_sync_language_from_widgets():
    """Sync language from the newest visible selector. Sidebar wins over old onboarding keys."""
    try:
        candidate_keys = [
            "wz39_preferred_language", "sidebar_preferred_language", "wz35_preferred_language", "wz24_sidebar_preferred_language",
            "wz25_sidebar_preferred_language", "wz21_sidebar_preferred_language", "wz19_sidebar_preferred_language",
            "onboarding_preferred_language",
        ]
        current = st.session_state.get("preferred_language") or st.session_state.get("language") or "English"
        chosen = current
        for k in candidate_keys:
            val = st.session_state.get(k)
            if isinstance(val, str) and val.strip():
                chosen = val.strip()
                break
        if callable(globals().get("workzo_set_language_everywhere")):
            workzo_set_language_everywhere(chosen)
        else:
            set_single_preferred_language(chosen)
        return chosen != current
    except Exception:
        return False


def _wz36_smart_context_flags():
    try:
        cv_exists = bool(str(st.session_state.get("cv_text", "")).strip() or st.session_state.get("structured_cv_json"))
        jd_exists = bool(str(st.session_state.get("current_job_description", "") or st.session_state.get("last_understand_job_description", "") or st.session_state.get("job_description", "")).strip())
        resume_score = int(st.session_state.get("cv_score_value") or st.session_state.get("resume_score") or 0)
        ats_score = int(st.session_state.get("ats_score_value") or st.session_state.get("ats_score") or 0)
        if not cv_exists:
            stage = "need_cv"
        elif resume_score and ats_score and (resume_score < 75 or ats_score < 75):
            stage = "improve_cv"
        elif not jd_exists:
            stage = "find_or_analyze_job"
        else:
            stage = "prepare_application"
        st.session_state["workzo_smart_stage"] = stage
        st.session_state["workzo_context_is_ready"] = bool(cv_exists and resume_score >= 75 and ats_score >= 75)
    except Exception:
        pass

try:
    _wz36_previous_show_dashboard = show_dashboard
    def show_dashboard():
        lang_changed = _wz36_sync_language_from_widgets()
        _wz36_smart_context_flags()
        if lang_changed:
            try:
                st.query_params["wz_lang"] = st.session_state.get("preferred_language", "English")
            except Exception:
                pass
        return _wz36_previous_show_dashboard()
except Exception:
    pass


# =========================================================
# WorkZo v38 final language + Work-O-Bot safety patch
# =========================================================
def _wz38_sync_language_now():
    try:
        # Prefer active sidebar/dashboard selector; onboarding key is only fallback.
        for _k in ["wz39_preferred_language", "sidebar_preferred_language", "wz35_preferred_language", "wz24_sidebar_preferred_language", "onboarding_preferred_language"]:
            _val = st.session_state.get(_k)
            if isinstance(_val, str) and _val.strip():
                if callable(globals().get("workzo_set_language_everywhere")):
                    workzo_set_language_everywhere(_val.strip())
                else:
                    set_single_preferred_language(_val.strip())
                return _val.strip()
        _lang = st.session_state.get("preferred_language") or st.session_state.get("language") or "English"
        if callable(globals().get("workzo_set_language_everywhere")):
            workzo_set_language_everywhere(_lang)
        else:
            set_single_preferred_language(_lang)
        return _lang
    except Exception:
        return "English"

try:
    _wz38_previous_show_dashboard = show_dashboard
    def show_dashboard():
        _before = st.session_state.get("preferred_language") or st.session_state.get("language") or "English"
        _after = _wz38_sync_language_now()
        # If user changed language through a sidebar selector, rerun once so all labels refresh.
        if _after != _before and not st.session_state.get("_wz38_language_rerun_done"):
            st.session_state["_wz38_language_rerun_done"] = True
            st.rerun()
        st.session_state["_wz38_language_rerun_done"] = False
        return _wz38_previous_show_dashboard()
except Exception:
    pass


# =========================================================
# WorkZo v40 - translate final dashboard literals used by smart cards
# =========================================================
def _wz35_next_action(cv_exists, resume_score, ats_score, job_exists, improved_ready, prepared_ready):
    if not cv_exists:
        return {"title":ui_label("Start with your CV"), "copy":ui_label("Upload or create your CV first so WorkZo can score it and guide the next steps."), "button":ui_label("Add CV"), "target":"onboarding", "extra":{}}
    if resume_score < 75 or ats_score < 75:
        return {"title":ui_label("Improve your CV first"), "copy":ui_label("Your Resume or ATS score needs improvement. Fix structure, keywords, and role alignment before applying widely."), "button":txt("open_cv_tools"), "target":"cv_documents", "extra":{"document_tools_mode":"Improve / Update CV"}}
    if not job_exists:
        return {"title":ui_label("Find or analyze a job next"), "copy":ui_label("Your CV is ready enough. Now find matching roles or paste one job description for a fit check."), "button":txt("open_job_assist"), "target":"job_assist", "extra":{"job_assist_mode_key":"find"}}
    if not improved_ready:
        return {"title":ui_label("Tailor your CV for this job"), "copy":ui_label("You have job context. Now tailor the CV to this specific role before creating application materials."), "button":ui_label("Improve CV for Job"), "target":"cv_documents", "extra":{"document_tools_mode":"Improve CV for a Job"}}
    if not prepared_ready:
        return {"title":ui_label("Prepare the application"), "copy":ui_label("Create a focused cover letter and preparation notes using the company, CV, and job description."), "button":txt("prepare_this_job"), "target":"job_assist", "extra":{"job_assist_mode_key":"prepare"}}
    return {"title":ui_label("Ready to apply"), "copy":ui_label("Your core application flow is complete. Apply, save the tracker item, and practice answers in Work-O-Bot."), "button":txt("ask_workobot"), "target":"workobot", "extra":{}}

# Make score guidance translatable wherever the final dashboard uses it.
try:
    if "UI_TEXT" in globals():
        UI_TEXT.setdefault("German", {}).update({
            "readiness_overview": "Bereitschaftsübersicht",
            "smart_actions": "Smarte Aktionen",
            "open_cv_tools": "CV-Tools öffnen",
            "open_job_assist": "Job Assist öffnen",
            "create_cover_letter": "Cover Letter erstellen",
            "ask_workobot": "Work-O-Bot fragen",
        })
        UI_TEXT.setdefault("French", {}).update({
            "readiness_overview": "Vue d’ensemble de la préparation",
            "smart_actions": "Actions intelligentes",
            "open_cv_tools": "Ouvrir les outils CV",
            "open_job_assist": "Ouvrir l’assistant emploi",
            "create_cover_letter": "Créer une lettre de motivation",
            "ask_workobot": "Demander à Work-O-Bot",
        })
except Exception:
    pass


# =========================================================
# WorkZo v41 - final dashboard language sync
# =========================================================
def _wz41_sync_language_from_any_widget():
    try:
        for _k in ["wz39_preferred_language", "sidebar_preferred_language", "wz35_preferred_language", "wz40_mobile_preferred_language", "wz30_language", "wz29_language", "wz28_language", "wz27_language", "onboarding_preferred_language", "preferred_language", "language"]:
            _v = st.session_state.get(_k)
            if isinstance(_v, str) and _v.strip():
                if callable(globals().get("workzo_set_language_everywhere")):
                    return workzo_set_language_everywhere(_v.strip())
                st.session_state["preferred_language"] = _v.strip()
                st.session_state["language"] = _v.strip()
                st.session_state["ui_language"] = _v.strip()
                st.session_state["response_language"] = _v.strip()
                return _v.strip()
    except Exception:
        pass
    return st.session_state.get("preferred_language", "English")

try:
    _wz41_previous_show_dashboard = show_dashboard
    def show_dashboard():
        _wz41_sync_language_from_any_widget()
        return _wz41_previous_show_dashboard()
except Exception:
    pass

# =========================================================

# =========================================================

# =========================================================
# WorkZo v45 - mobile top navigation, desktop left sidebar
# Desktop users keep the native left toolbox. Mobile users get a top nav so
# content is not squeezed by the Streamlit sidebar.
# =========================================================
def _wz45_render_mobile_top_nav():
    try:
        import time as _time
        import html as _html
        lang = str(st.session_state.get("preferred_language", "English") or "English")
        labels = {
            "English": {"tools": "Tools / Navigation", "dashboard": "Dashboard", "cv": "CV Documents", "jobs": "Job Assist", "bot": "Work-O-Bot"},
            "German": {"tools": "Tools / Navigation", "dashboard": "Dashboard", "cv": "Lebenslauf & Dokumente", "jobs": "Job-Assistent", "bot": "Work-O-Bot"},
            "French": {"tools": "Outils / navigation", "dashboard": "Tableau de bord", "cv": "CV & documents", "jobs": "Assistant emploi", "bot": "Work-O-Bot"},
            "Dutch": {"tools": "Tools / navigatie", "dashboard": "Dashboard", "cv": "CV & documenten", "jobs": "Jobassistent", "bot": "Work-O-Bot"},
            "Spanish": {"tools": "Herramientas / navegación", "dashboard": "Panel", "cv": "CV y documentos", "jobs": "Asistente de empleo", "bot": "Work-O-Bot"},
        }
        t = labels.get(lang, labels["English"])
        nonce = str(int(_time.time() * 1000))
        def link(page, text):
            return f"<a class='wz45-mobile-link' href='?page={page}&wz_top={nonce}'>{_html.escape(text)}</a>"
        st.markdown(
            f"""
            <style>
            /* WorkZo v46: show this top toolbox ONLY on mobile.
               Desktop keeps the real Streamlit left sidebar toolbox. */
            .wz45-mobile-topnav {{ display: none !important; }}
            @media (max-width: 700px) {{
                .wz45-mobile-topnav {{
                    display: block !important;
                    position: sticky !important;
                    top: 0 !important;
                    z-index: 9999 !important;
                    margin: 0 0 0.75rem 0 !important;
                    padding: 0.75rem !important;
                    border: 1px solid rgba(20,184,166,0.24) !important;
                    border-radius: 18px !important;
                    background: linear-gradient(135deg, rgba(15,23,42,0.98), rgba(8,47,73,0.92)) !important;
                    box-shadow: 0 10px 28px rgba(2,6,23,0.30) !important;
                }}
                .wz45-mobile-title {{ color: #f8fafc !important; font-weight: 850 !important; font-size: 0.95rem !important; margin-bottom: 0.5rem !important; }}
                .wz45-mobile-links {{ display: grid !important; grid-template-columns: repeat(2, minmax(0, 1fr)) !important; gap: 0.45rem !important; }}
                .wz45-mobile-link {{
                    display: block !important;
                    text-align: center !important;
                    color: #e0f2fe !important;
                    text-decoration: none !important;
                    border: 1px solid rgba(96,165,250,0.26) !important;
                    background: rgba(37,99,235,0.16) !important;
                    border-radius: 999px !important;
                    padding: 0.48rem 0.55rem !important;
                    font-weight: 700 !important;
                    font-size: 0.86rem !important;
                    white-space: nowrap !important;
                }}
            }}
            </style>
            <div class="wz45-mobile-topnav">
                <div class="wz45-mobile-title">☰ {_html.escape(t['tools'])}</div>
                <div class="wz45-mobile-links">
                    {link('dashboard', '🏠 ' + t['dashboard'])}
                    {link('cv_documents', '📄 ' + t['cv'])}
                    {link('job_assist', '🎯 ' + t['jobs'])}
                    {link('workobot', '🤖 ' + t['bot'])}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    except Exception:
        pass

try:
    _wz45_previous_show_dashboard = show_dashboard
    def show_dashboard():
        _wz45_render_mobile_top_nav()
        return _wz45_previous_show_dashboard()
except Exception:
    pass


# =========================================================
# WorkZo v48 dashboard responsive toolbox guard
# The mobile top menu is rendered, but CSS shows it only on phones.
# =========================================================
try:
    st.markdown("""
    <style id="workzo-v48-dashboard-topnav-guard">
    .wz45-mobile-topnav { display: none !important; }
    @media (min-width: 701px) {
        .wz45-mobile-topnav {
            display: none !important;
            visibility: hidden !important;
            height: 0 !important;
            overflow: hidden !important;
            margin: 0 !important;
            padding: 0 !important;
            border: 0 !important;
        }
    }
    @media (max-width: 700px) {
        .wz45-mobile-topnav { display: block !important; visibility: visible !important; height: auto !important; }
    }
    </style>
    """, unsafe_allow_html=True)
except Exception:
    pass


# =========================================================
# WorkZo v49 memory + progress stabilization wrapper
# Keeps safe dashboard progress after refresh and saves status flags continuously.
# =========================================================
def _wz49_detect_and_save_progress_flags():
    try:
        if st.session_state.get('cv_text') or st.session_state.get('structured_cv_json') or st.session_state.get('approved_structured_cv_json'):
            st.session_state['_wz_has_cv'] = True
        if st.session_state.get('improved_cv_text') or st.session_state.get('latest_improved_cv') or st.session_state.get('final_cv_text'):
            st.session_state['_wz_cv_improved'] = True
        if st.session_state.get('latest_curated_jobs') or st.session_state.get('latest_job_query_expansion'):
            st.session_state['_wz_job_found'] = True
        if st.session_state.get('latest_job_analysis') or st.session_state.get('last_understand_job_description') or st.session_state.get('current_job_description'):
            st.session_state['_wz_job_analyzed'] = True
        if st.session_state.get('latest_application_prep') or st.session_state.get('latest_cover_letter') or st.session_state.get('cover_letter_text'):
            st.session_state['_wz_prepared'] = True
        for a, b in [('cv_score_value','_best_cv_score_value'), ('ats_score_value','_best_ats_score_value'), ('job_fit_score_value','_best_job_fit_score_value')]:
            try:
                cur = int(float(st.session_state.get(a) or 0))
                best = int(float(st.session_state.get(b) or 0))
                if cur > best:
                    st.session_state[b] = cur
                elif best > 0 and cur <= 0:
                    st.session_state[a] = best
            except Exception:
                pass
        if callable(globals().get('workzo_save_light_memory')):
            workzo_save_light_memory()
    except Exception:
        pass

try:
    _wz49_previous_show_dashboard = show_dashboard
    def show_dashboard():
        try:
            if callable(globals().get('workzo_load_light_memory')):
                workzo_load_light_memory()
        except Exception:
            pass
        _wz49_detect_and_save_progress_flags()
        result = _wz49_previous_show_dashboard()
        _wz49_detect_and_save_progress_flags()
        return result
except Exception:
    pass

# =========================================================
# WorkZo v50 FINAL PROGRESS + FOUNDER ANALYTICS PATCH
# Fixes false green checks by using explicit completion conditions:
# 1 CV uploaded, 2 CV improved, 3 Job matched, 4 Prepared for job.
# Adds founder tracking events for each progress transition.
# =========================================================

def _wz50_bool_text(*keys):
    try:
        return any(bool(str(st.session_state.get(k, '') or '').strip()) for k in keys)
    except Exception:
        return False


def _wz50_has_list(key):
    try:
        v = st.session_state.get(key)
        return isinstance(v, list) and len(v) > 0
    except Exception:
        return False


def _wz50_progress_state():
    """Return strict progress state. Do not mark steps done merely because a score exists."""
    cv_uploaded = bool(
        str(st.session_state.get('cv_text', '') or '').strip()
        or st.session_state.get('structured_cv_json')
        or st.session_state.get('approved_structured_cv_json')
        or st.session_state.get('_workzo_has_cv')
        or st.session_state.get('_wz_progress_cv_uploaded')
    )
    if cv_uploaded:
        st.session_state['_wz_progress_cv_uploaded'] = True
        st.session_state['_workzo_has_cv'] = True

    cv_improved = bool(
        _wz50_bool_text('improved_cv_text', 'latest_improved_cv', 'final_cv_text', 'workzo_latest_tailored_cv')
        or st.session_state.get('_wz_progress_cv_improved')
    )
    if _wz50_bool_text('improved_cv_text', 'latest_improved_cv', 'final_cv_text', 'workzo_latest_tailored_cv'):
        st.session_state['_wz_progress_cv_improved'] = True
        cv_improved = True

    # Job match/finding is NOT the same as merely having a pasted job description.
    # It becomes complete only after live job search/curation exists, or an explicit progress flag was set.
    job_matched = bool(
        _wz50_has_list('latest_curated_jobs')
        or _wz50_has_list('latest_live_jobs')
        or _wz50_has_list('job_search_results')
        or bool(st.session_state.get('latest_job_query_expansion'))
        or st.session_state.get('_wz_progress_job_matched')
    )
    if _wz50_has_list('latest_curated_jobs') or _wz50_has_list('latest_live_jobs') or _wz50_has_list('job_search_results') or bool(st.session_state.get('latest_job_query_expansion')):
        st.session_state['_wz_progress_job_matched'] = True
        job_matched = True

    prepared = bool(
        _wz50_bool_text('latest_application_prep', 'latest_cover_letter', 'cover_letter_text', 'generated_cover_letter', 'saved_application_prep')
        or st.session_state.get('_wz_progress_prepared')
    )
    if _wz50_bool_text('latest_application_prep', 'latest_cover_letter', 'cover_letter_text', 'generated_cover_letter', 'saved_application_prep'):
        st.session_state['_wz_progress_prepared'] = True
        prepared = True

    return {
        'cv_uploaded': bool(cv_uploaded),
        'cv_improved': bool(cv_improved),
        'job_matched': bool(job_matched),
        'prepared': bool(prepared),
    }


def _wz50_track_progress(progress):
    """Founder-safe analytics: track progress flags only, no CV/job text."""
    try:
        previous = st.session_state.get('_wz50_last_progress_snapshot') or {}
        if not isinstance(previous, dict):
            previous = {}
        for key, done in progress.items():
            if done and not previous.get(key):
                if callable(globals().get('track_event')):
                    track_event('progress_step_completed', 'Application Progress', {'step': key})
        if previous != progress and callable(globals().get('track_event')):
            track_event('progress_snapshot', 'Application Progress', progress)
        st.session_state['_wz50_last_progress_snapshot'] = dict(progress)
    except Exception:
        pass


def _wz50_save_state():
    """Save safe UI memory. Do not persist CV text, job descriptions, or generated documents."""
    try:
        keys = [
            'cv_score_value', 'ats_score_value', 'application_readiness_value',
            'job_fit_score_value', 'interview_score', 'country', 'preferred_language',
            'ui_language', 'response_language', 'language', 'target_company_website',
            'target_company', 'prepare_target_company', 'nav_page', 'page',
            '_workzo_has_cv', '_wz_progress_cv_uploaded', '_wz_progress_cv_improved',
            '_wz_progress_job_matched', '_wz_progress_prepared',
            '_best_cv_score_value', '_best_ats_score_value', '_best_application_readiness_value',
        ]
        data = {}
        for k in keys:
            v = st.session_state.get(k)
            if isinstance(v, (str, int, float, bool)) or v is None:
                data[k] = v
        progress = _wz50_progress_state()
        data.update({
            '_wz_progress_cv_uploaded': progress['cv_uploaded'],
            '_wz_progress_cv_improved': progress['cv_improved'],
            '_wz_progress_job_matched': progress['job_matched'],
            '_wz_progress_prepared': progress['prepared'],
        })
        with open(_wz35_state_file(), 'w', encoding='utf-8') as f:
            _wz35_json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _wz50_load_state():
    """Load safe UI memory. Ignore old false-progress flags from earlier builds."""
    try:
        path = _wz35_state_file()
        if not _wz35_os.path.exists(path):
            return
        with open(path, 'r', encoding='utf-8') as f:
            data = _wz35_json.load(f)
        if not isinstance(data, dict):
            return
        allowed = {
            'cv_score_value', 'ats_score_value', 'application_readiness_value',
            'job_fit_score_value', 'interview_score', 'country', 'preferred_language',
            'ui_language', 'response_language', 'language', 'target_company_website',
            'target_company', 'prepare_target_company', 'nav_page', 'page',
            '_workzo_has_cv', '_wz_progress_cv_uploaded', '_wz_progress_cv_improved',
            '_wz_progress_job_matched', '_wz_progress_prepared',
            '_best_cv_score_value', '_best_ats_score_value', '_best_application_readiness_value',
        }
        for k, v in data.items():
            if k in allowed and (k not in st.session_state or st.session_state.get(k) in [None, '', 0, False]):
                st.session_state[k] = v
        for key in ['cv_score_value', 'ats_score_value', 'application_readiness_value']:
            try:
                best = int(st.session_state.get('_best_' + key) or 0)
                cur = int(st.session_state.get(key) or 0)
                if best > cur:
                    st.session_state[key] = best
            except Exception:
                pass
    except Exception:
        pass

# Rebind the older helper names so the rest of the file uses v50 memory.
_wz35_save_state = _wz50_save_state
_wz35_load_state = _wz50_load_state


def _wz50_sidebar(page_key):
    with st.sidebar:
        try:
            logo_src = image_to_data_uri(ICON_PATH) or image_to_data_uri(LOGO_PATH)
        except Exception:
            logo_src = None
        if logo_src:
            st.markdown(f"""
            <div class='workzo-sidebar-brand-wrap'>
              <img src='{logo_src}' class='workzo-sidebar-logo' alt='WorkZo AI logo'>
              <div><div class='workzo-sidebar-brand'>WORKZO AI</div><div class='workzo-sidebar-version'>Beta · guided workspace</div></div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown('### WorkZo AI')

        navs = [('dashboard', txt('dashboard')), ('cv_documents', txt('cv_documents')), ('job_assist', txt('job_assist')), ('workobot', 'Work-O-Bot')]
        for key, label in navs:
            text = str(label) + ('  ✓' if page_key == key else '')
            if st.button(text, key=f'wz50_nav_{key}', use_container_width=True):
                _wz35_go(key)

        st.markdown(f"<div class='workzo-sidebar-section-label'>{html.escape(txt('company_context'))}</div>", unsafe_allow_html=True)
        with st.expander('🏢 ' + txt('company_website'), expanded=False):
            company_url = st.text_input(txt('company_website'), key='target_company_website', placeholder='https://company.com')
            if company_url:
                st.caption(ui_label('Used for cover letters and job/interview preparation context.'))

        st.markdown(f"<div class='workzo-sidebar-section-label'>{html.escape(txt('language'))}</div>", unsafe_allow_html=True)
        try:
            langs = language_options if 'language_options' in globals() and language_options else ['English', 'German', 'Dutch', 'French', 'Spanish', 'Portuguese']
        except Exception:
            langs = ['English', 'German', 'Dutch', 'French', 'Spanish', 'Portuguese']
        cur = st.session_state.get('preferred_language') or st.session_state.get('language') or 'English'
        if cur not in langs:
            cur = 'English' if 'English' in langs else langs[0]
        chosen = st.selectbox(txt('preferred_language'), langs, index=langs.index(cur), key='wz50_preferred_language')
        _wz35_sync_language(chosen)

        st.markdown('---')
        if st.button(txt('edit_setup'), key='wz50_edit_setup', use_container_width=True):
            st.session_state['onboarding_complete'] = False
            st.session_state['page'] = 'onboarding'
            st.session_state['nav_page'] = 'onboarding'
            try:
                st.query_params['page'] = 'onboarding'
            except Exception:
                pass
            _wz50_save_state()
            st.rerun()

        with st.expander('Founder analytics', expanded=False):
            founder_pin = None
            try:
                founder_pin = (os.getenv('FOUNDER_PIN') or get_streamlit_secret('FOUNDER_PIN'))
            except Exception:
                founder_pin = os.getenv('FOUNDER_PIN') if 'os' in globals() else None
            if founder_pin:
                pin = st.text_input('Founder PIN', type='password', key='wz50_founder_pin')
                if pin == founder_pin:
                    st.session_state['founder_unlocked'] = True
                    st.success('Founder mode unlocked.')
            else:
                st.caption('FOUNDER_PIN not configured. Temporary founder access for local testing.')
                if st.text_input('Temporary founder PIN', type='password', key='wz50_temp_pin'):
                    st.session_state['founder_unlocked'] = True
            if st.session_state.get('founder_unlocked'):
                if st.button('Open founder analytics', key='wz50_founder_nav', use_container_width=True):
                    _wz35_go('founder_dashboard')


def _wz50_current_step(progress):
    if not progress['cv_uploaded']:
        return 0
    if not progress['cv_improved']:
        return 1
    if not progress['job_matched']:
        return 2
    if not progress['prepared']:
        return 3
    return 4


def _wz50_dashboard_home():
    _wz50_load_state()
    _wz35_remember_scores()
    _wz35_force_scroll_top()
    _wz35_css()

    progress = _wz50_progress_state()
    _wz50_track_progress(progress)

    cv_exists = progress['cv_uploaded']
    resume_score = _wz35_score('cv_score_value', 'resume_score', 'resume_quality_score', '_best_cv_score_value', default=76 if cv_exists else 0)
    ats_score = _wz35_score('ats_score_value', 'ats_score', '_best_ats_score_value', default=70 if cv_exists else 0)
    interview_score = _wz35_score('interview_score', 'interview_readiness', '_best_interview_score', default=40 if cv_exists else 0)
    country = st.session_state.get('country') or st.session_state.get('target_country') or 'Not set'
    language = st.session_state.get('preferred_language') or st.session_state.get('language') or 'English'

    # Smart next action uses strict progress, not accidental score presence.
    if not progress['cv_uploaded']:
        next_action = {'title':'Start with your CV', 'copy':'Upload or create your CV first so WorkZo can guide the next steps.', 'button':'Add CV', 'target':'onboarding', 'extra':{}}
    elif not progress['cv_improved']:
        next_action = {'title':'Improve your CV', 'copy':'Make your CV stronger before job matching. Tailor structure, keywords, and achievements.', 'button':'Improve CV', 'target':'cv_documents', 'extra':{'document_tools_mode':'Improve / Update CV'}}
    elif not progress['job_matched']:
        next_action = {'title':'Find matching jobs', 'copy':'Search jobs for your selected country and choose one role to analyze.', 'button':'Open Job Match', 'target':'job_assist', 'extra':{'job_assist_mode_key':'find'}}
    elif not progress['prepared']:
        next_action = {'title':'Prepare for this job', 'copy':'Create cover letter/application prep and practice your strongest answers.', 'button':'Prepare this job', 'target':'job_assist', 'extra':{'job_assist_mode_key':'prepare'}}
    else:
        next_action = {'title':'Ready to apply', 'copy':'Your core application flow is complete. Apply, track the result, and practice with Work-O-Bot.', 'button':'Practice with Work-O-Bot', 'target':'workobot', 'extra':{}}

    st.markdown(f"""
    <div class='wz35-hero'>
      <div class='wz35-kicker'>{_wz35_escape(txt('workzo_command_center'))}</div>
      <div class='wz35-title'>{_wz35_escape(txt('next_best_move_clear'))}</div>
      <div class='wz35-sub'>{_wz35_escape(txt('next_best_move_copy'))}</div>
      <div class='wz35-chip-row'>
        <span class='wz35-chip'>{_wz35_escape(country)}</span>
        <span class='wz35-chip'>{_wz35_escape(language)}</span>
        <span class='wz35-chip'>{_wz35_escape(ui_label('CV ready') if progress['cv_uploaded'] else ui_label('CV missing'))}</span>
        <span class='wz35-chip'>{_wz35_escape(ui_label('CV improved') if progress['cv_improved'] else ui_label('CV not improved'))}</span>
        <span class='wz35-chip'>{_wz35_escape(ui_label('Job matched') if progress['job_matched'] else ui_label('Job not matched'))}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class='wz35-next'>
      <div class='wz35-next-label'>{_wz35_escape(txt('recommended_next_step'))}</div>
      <div class='wz35-next-title'>{_wz35_escape(next_action['title'])}</div>
      <div class='wz35-next-copy'>{_wz35_escape(next_action['copy'])}</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button(next_action['button'], key='wz50_primary_action', use_container_width=True):
        _wz35_go(next_action['target'], next_action.get('extra'))

    st.markdown('### ' + txt('readiness_overview'))
    c1, c2, c3 = st.columns(3)
    with c1:
        _wz35_rate_card(txt('resume_score'), resume_score, ui_label('Clarity, structure, achievements, and overall CV quality.'), missing=not cv_exists)
    with c2:
        _wz35_rate_card(txt('ats_score'), ats_score, ui_label('Scanner-friendly formatting, role keywords, sections, and parsing safety.'), missing=not cv_exists)
    with c3:
        _wz35_rate_card(txt('interview_readiness'), interview_score, ui_label('How ready you are to explain your CV and job fit clearly.'), missing=not cv_exists)

    st.markdown('### ' + txt('smart_actions'))
    a1, a2, a3, a4 = st.columns(4)
    with a1:
        _wz35_action_card(txt('improve_cv'), ui_label('Use this to improve your CV or tailor it to a specific job.'), txt('open_cv_tools'), 'cv_documents', 'wz50_action_cv', {'document_tools_mode':'Improve / Update CV'})
    with a2:
        _wz35_action_card(txt('job_match'), ui_label('Search jobs for the selected country, then analyze one job description for fit.'), txt('open_job_assist'), 'job_assist', 'wz50_action_jobs', {'job_assist_mode_key':'find'})
    with a3:
        _wz35_action_card(txt('cover_letter'), ui_label('Use CV, job description, and company context to create a focused cover letter.'), txt('create_cover_letter'), 'cv_documents', 'wz50_action_cover', {'document_tools_mode':'Cover Letter Generator + Language'})
    with a4:
        _wz35_action_card('Work-O-Bot', ui_label('Ask career questions or practice interview answers in your selected language.'), txt('ask_workobot'), 'workobot', 'wz50_action_bot')

    st.markdown('### ' + txt('application_progress'))
    st.caption(ui_label('Visual tracker only. Use Smart actions above to continue.'))
    score_checked = bool(resume_score or ats_score)
    flow = [
        ('1. CV added', progress['cv_uploaded'], txt('completed') if progress['cv_uploaded'] else ui_label('Add or upload CV')),
        ('2. Resume + ATS checked', score_checked, ui_label('Good') if score_checked else ui_label('Check resume quality')),
        ('3. Job analyzed', progress['job_matched'], txt('completed') if progress['job_matched'] else ui_label('Paste/analyze one job')),
        ('4. CV improved', progress['cv_improved'], txt('completed') if progress['cv_improved'] else ui_label('Tailor CV to the job')),
        ('5. Prepared to apply', progress['prepared'], txt('completed') if progress['prepared'] else ui_label('Prepare application')),
    ]
    try:
        current = next((i for i, (_, done, _) in enumerate(flow) if not done), len(flow) - 1)
    except Exception:
        current = 0
    cols = st.columns(5)
    for i, (label, done, note) in enumerate(flow):
        with cols[i]:
            _wz35_flow_card(label, done, (not done and current == i), note)
    st.caption(ui_label('Scores are guidance only. WorkZo should not invent skills, company facts, language level, salary, or experience.'))
    _wz35_remember_scores()
    _wz50_save_state()


def show_dashboard():
    _wz50_load_state()
    _wz35_sync_language()
    _wz35_force_scroll_top()
    page_key = st.session_state.get('nav_page') or st.session_state.get('page') or 'dashboard'
    page_key = {'landing':'dashboard', 'bot':'workobot', 'interview':'workobot', 'jobs':'job_assist', 'improve_cv':'cv_documents'}.get(page_key, page_key)
    if page_key == 'interview_practice':
        page_key = 'workobot'
    if page_key not in {'dashboard', 'cv_documents', 'job_assist', 'workobot', 'founder_dashboard'}:
        page_key = 'dashboard'
    st.session_state['page'] = page_key
    st.session_state['nav_page'] = page_key
    try:
        _wz28_top(True)
    except Exception:
        pass
    _wz50_sidebar(page_key)

    if page_key == 'dashboard':
        _wz50_dashboard_home()
    elif page_key == 'cv_documents':
        _wz35_css()
        show_document_tools()
    elif page_key == 'job_assist':
        _wz35_css()
        try:
            _wz28_job_assist_page()
        except Exception:
            st.subheader(txt('job_assist'))
            tab1, tab2, tab3 = st.tabs([txt('find_jobs'), txt('understand_job'), txt('prepare_this_job')])
            with tab1: st.info('Job search module could not be loaded.')
            with tab2: st.info('Understand Job module could not be loaded.')
            with tab3: st.info('Prepare module could not be loaded.')
    elif page_key == 'workobot':
        _wz35_css()
        show_workobot()
    elif page_key == 'founder_dashboard':
        _wz35_css()
        if st.session_state.get('founder_unlocked') and callable(globals().get('render_founder_dashboard')):
            render_founder_dashboard()
        else:
            st.warning('Founder mode is locked. Enter the Founder PIN in the sidebar.')

    _wz35_remember_scores()
    _wz50_save_state()


# =========================================================
# WorkZo v51 - Enable classic Job Assist and disable AI Job Application Assistant
# This final override intentionally runs last.
# - Restores Job Assist: Find Jobs | Understand Job | Prepare this Job
# - Removes the AI Job Application Assistant wrapper from the active route
# - Keeps existing dashboard, sidebar, memory, progress, Work-O-Bot, and CV tools
# =========================================================
def _wz51_safe_label(text_value, fallback=None):
    try:
        if callable(globals().get("txt")):
            translated = txt(str(text_value))
            if translated and translated != str(text_value):
                return translated
    except Exception:
        pass
    try:
        if callable(globals().get("ui_label")):
            return ui_label(str(fallback or text_value))
    except Exception:
        pass
    return str(fallback or text_value)


def _wz51_go(page_key, extra=None):
    try:
        if extra:
            for k, v in extra.items():
                st.session_state[k] = v
        st.session_state["page"] = page_key
        st.session_state["nav_page"] = page_key
        if callable(globals().get("request_scroll_to_top")):
            request_scroll_to_top()
        st.rerun()
    except Exception:
        st.session_state["page"] = page_key
        st.session_state["nav_page"] = page_key


def _wz51_extract_roles_from_cv(cv_text):
    cv_text = str(cv_text or "")
    roles = []
    for key in ["target_role", "detected_target_role", "current_role_detected"]:
        val = st.session_state.get(key)
        if isinstance(val, str) and val.strip():
            roles.append(val.strip())
    first_lines = [x.strip() for x in cv_text.splitlines() if x.strip()][:8]
    for line in first_lines:
        low = line.lower()
        if any(word in low for word in ["engineer", "developer", "analyst", "scientist", "support", "manager", "consultant", "specialist", "designer"]):
            clean = re.sub(r"[|•].*$", "", line).strip(" -–—")
            if 3 <= len(clean) <= 70:
                roles.append(clean)
    # sensible fallback
    if not roles:
        roles = ["Data Analyst", "IT Support Specialist", "Customer Support Specialist"]
    deduped = []
    seen = set()
    for r in roles:
        k = r.casefold()
        if k not in seen:
            seen.add(k)
            deduped.append(r)
    return deduped[:6]


def _wz51_simple_job_card(job, idx=0):
    title = html.escape(str(job.get("title") or job.get("job_title") or "Job opening"))
    company = html.escape(str(job.get("company") or job.get("employer_name") or "Company not listed"))
    location = html.escape(str(job.get("location") or job.get("job_location") or "Location not listed"))
    source = html.escape(str(job.get("source") or job.get("publisher") or "Live source"))
    url = str(job.get("url") or job.get("redirect_url") or job.get("job_apply_link") or "")
    st.markdown(f"""
    <div class='next-action-card' style='margin:10px 0;'>
      <div class='next-action-label'>{source}</div>
      <div class='next-action-title'>{title}</div>
      <div class='next-action-copy'>{company} · {location}</div>
    </div>
    """, unsafe_allow_html=True)
    if url:
        st.link_button(_wz51_safe_label("View job", "View job"), url, use_container_width=False)


def _wz51_render_find_jobs():
    """Smarter Job Assist > Find Jobs page. Only Job Assist is changed in this v54 patch."""
    st.markdown("### " + _wz51_safe_label("find_jobs", "Find Jobs"))

    cv_text = str(st.session_state.get("cv_text") or st.session_state.get("clean_structured_cv_text") or "")
    user_country = str(st.session_state.get("country") or st.session_state.get("migration_country") or "").strip() or "Global"
    suggested_roles = _wz51_extract_roles_from_cv(cv_text)
    default_titles = ", ".join(suggested_roles[:3]) or str(st.session_state.get("target_role") or "")

    def _wz54_country_options():
        countries = []
        try:
            countries.extend([str(x) for x in (globals().get("country_options") or []) if str(x).strip()])
        except Exception:
            pass
        try:
            pc = globals().get("pycountry")
            if pc is not None:
                countries.extend([c.name for c in pc.countries if getattr(c, "name", "")])
        except Exception:
            pass
        fallback = ["Global", "Germany", "India", "United States", "United Kingdom", "Canada", "Australia", "Netherlands", "France", "Austria", "Switzerland", "Singapore", "United Arab Emirates", "Ireland", "Spain", "Italy", "Sweden", "Denmark", "Norway", "Finland", "Belgium", "Poland", "Portugal", "New Zealand", "South Africa"]
        countries.extend(fallback)
        clean = []
        seen = set()
        for c in countries:
            c = str(c).strip()
            if not c:
                continue
            key = c.casefold()
            if key not in seen:
                seen.add(key)
                clean.append(c)
        return ["Global"] + sorted([c for c in clean if c.casefold() != "global"], key=lambda x: x.lower())

    def _wz54_city_options(country_name: str):
        try:
            fn = globals().get("fetch_country_cities")
            if callable(fn):
                cities = fn(country_name) or []
                return [str(c).strip() for c in cities if str(c).strip()]
        except Exception:
            pass
        return []

    def _wz54_country_aliases(country_name: str):
        low = (country_name or "").strip().lower()
        aliases = {low}
        mapping = {
            "germany": ["germany", "deutschland", "de"],
            "india": ["india", "in"],
            "united states": ["united states", "usa", "u.s.", "u.s.a.", "us"],
            "united kingdom": ["united kingdom", "uk", "great britain", "england"],
            "canada": ["canada", "ca"],
            "australia": ["australia", "au"],
            "netherlands": ["netherlands", "holland", "nl"],
            "france": ["france", "fr"],
            "austria": ["austria", "at"],
            "switzerland": ["switzerland", "ch", "schweiz", "suisse"],
            "singapore": ["singapore", "sg"],
        }
        aliases.update(mapping.get(low, []))
        return {a for a in aliases if a}

    def _wz54_filter_jobs(jobs, country_name, city_name=""):
        if not jobs or not country_name or country_name == "Global":
            return jobs or []
        selected_aliases = _wz54_country_aliases(country_name)
        city = (city_name or "").strip().lower()
        common_wrong = {
            "germany", "deutschland", "india", "united states", "usa", "u.s.", "u.s.a.", "canada", "united kingdom", "uk", "australia", "netherlands", "france", "austria", "switzerland", "singapore"
        } - selected_aliases
        filtered = []
        for job in jobs:
            try:
                loc = str(job.get("location") or job.get("job_location") or job.get("candidate_required_location") or "")
                title = str(job.get("title") or job.get("job_title") or "")
                company = str(job.get("company") or job.get("employer_name") or "")
                summary = str(job.get("summary") or job.get("description") or "")
                hay = " ".join([loc, title, company, summary]).lower()
                loc_low = loc.lower()
                if any(w and w in loc_low for w in common_wrong):
                    continue
                if city and city in hay:
                    filtered.append(job); continue
                if any(a and a in hay for a in selected_aliases):
                    filtered.append(job); continue
                if "remote" in loc_low and not any(w and w in loc_low for w in common_wrong):
                    filtered.append(job); continue
            except Exception:
                continue
        return filtered

    # Safe defaults BEFORE widgets render. Do not overwrite widget keys later.
    if "job_assist_target_titles" not in st.session_state:
        st.session_state["job_assist_target_titles"] = default_titles
    if "job_assist_preferred_country_v54" not in st.session_state:
        st.session_state["job_assist_preferred_country_v54"] = user_country if user_country else "Global"
    if "job_assist_region_city_text_v54" not in st.session_state:
        st.session_state["job_assist_region_city_text_v54"] = ""

    st.markdown(f"""
    <div class='next-action-card' style='margin-top:4px;'>
      <div class='next-action-label'>{html.escape(_wz51_safe_label('Smart job search', 'Smart job search'))}</div>
      <div class='next-action-title'>{html.escape(_wz51_safe_label('Search by role + country + city, then analyze the best job', 'Search by role + country + city, then analyze the best job'))}</div>
      <div class='next-action-copy'>{html.escape(_wz51_safe_label('WorkZo uses your CV signals and location context to find tighter matches. Choose the country, then add a city/region only if needed.', 'WorkZo uses your CV signals and location context to find tighter matches. Choose the country, then add a city/region only if needed.'))}</div>
    </div>
    """, unsafe_allow_html=True)

    countries = _wz54_country_options()
    current_country = st.session_state.get("job_assist_preferred_country_v54") or user_country or "Global"
    if current_country not in countries:
        countries.insert(1, current_country)

    row1a, row1b = st.columns([1.05, 0.95])
    with row1a:
        target_titles = st.text_input(
            _wz51_safe_label("Target job titles", "Target job titles"),
            placeholder="Data Analyst, IT Support, Customer Success",
            key="job_assist_target_titles",
            help=_wz51_safe_label("Use 1-3 role titles. WorkZo will search around these titles instead of using your full CV text.", "Use 1-3 role titles. WorkZo will search around these titles instead of using your full CV text."),
        )
    with row1b:
        preferred_country = st.selectbox(
            _wz51_safe_label("Preferred country", "Preferred country"),
            countries,
            index=countries.index(current_country) if current_country in countries else 0,
            key="job_assist_preferred_country_v54",
            help=_wz51_safe_label("Choose the country where you want to search jobs.", "Choose the country where you want to search jobs."),
        )

    cities = _wz54_city_options(preferred_country) if preferred_country != "Global" else []
    city_text = st.text_input(
        _wz51_safe_label("Region / city", "Region / city"),
        placeholder="Berlin, Chennai, Frankfurt, Remote...",
        key="job_assist_region_city_text_v54",
        help=_wz51_safe_label("Start typing a city/region. Suggestions appear when available.", "Start typing a city/region. Suggestions appear when available."),
    )
    city_query = (city_text or "").strip().lower()
    final_city = city_text.strip()
    if city_query and cities:
        matches = [c for c in cities if c.lower().startswith(city_query)][:12]
        if matches:
            city_choice = st.selectbox(
                _wz51_safe_label("City suggestions", "City suggestions"),
                [city_text.strip()] + matches,
                index=0,
                key="job_assist_city_suggestion_v54",
                help=_wz51_safe_label("Select a suggestion or keep your typed value.", "Select a suggestion or keep your typed value."),
            )
            final_city = city_choice.strip()

    roles_preview = [x.strip() for x in re.split(r"[,;\n/]", target_titles or "") if x.strip()]
    if not roles_preview and suggested_roles:
        roles_preview = suggested_roles[:3]
    role_chips = "".join(f"<span class='workzo-dashboard-chip'>{html.escape(r)}</span>" for r in roles_preview[:4]) or f"<span class='workzo-dashboard-chip'>{html.escape(_wz51_safe_label('Add a target title', 'Add a target title'))}</span>"
    location_label = ", ".join([x for x in [final_city, preferred_country if preferred_country != "Global" else ""] if x]) or "Global"
    st.markdown(f"""
    <div class='workzo-mini-note' style='margin: 8px 0 14px 0;'>
        {_wz51_safe_label('Search context', 'Search context')}: {role_chips}
        <span class='workzo-dashboard-chip'>📍 {html.escape(location_label)}</span>
    </div>
    """, unsafe_allow_html=True)

    with st.expander(_wz51_safe_label("Review CV signals used for matching", "Review CV signals used for matching"), expanded=False):
        try:
            cv_profile = build_job_matching_profile(cv_text) if callable(globals().get("build_job_matching_profile")) else cv_text
        except Exception:
            cv_profile = cv_text
        st.text_area(_wz51_safe_label("CV matching profile", "CV matching profile"), value=cv_profile, height=220, key="job_assist_cv_review_v54")

    find_col, tip_col = st.columns([0.45, 1])
    with find_col:
        find_clicked = st.button(_wz51_safe_label("Find smart matches", "Find smart matches"), key="btn_find_jobs_v54", use_container_width=True)
    with tip_col:
        st.caption(_wz51_safe_label("Tip: after finding jobs, open one job and use Understand Job before improving your CV.", "Tip: after finding jobs, open one job and use Understand Job before improving your CV."))

    if find_clicked:
        roles = [x.strip() for x in re.split(r"[,;\n/]", target_titles or "") if x.strip()] or suggested_roles
        if not roles:
            st.warning(_wz51_safe_label("Please add at least one target job title.", "Please add at least one target job title."))
        else:
            search_location = ", ".join([x for x in [final_city, preferred_country if preferred_country != "Global" else ""] if x]).strip() or preferred_country
            # Store search memory in non-widget keys only.
            st.session_state["last_job_search_target_titles"] = ", ".join(roles[:6])
            st.session_state["last_job_search_location_text"] = search_location
            st.session_state["last_job_search_country"] = preferred_country
            try:
                if callable(globals().get("track_button_click")):
                    track_button_click("Find Jobs", "Job Assist", {"country": preferred_country, "location": search_location, "roles": roles[:3]})
            except Exception:
                pass

            with st.status(_wz51_safe_label("Searching and ranking jobs...", "Searching and ranking jobs..."), expanded=True) as status:
                st.write(_wz51_safe_label("Building focused search terms from your CV and target titles...", "Building focused search terms from your CV and target titles..."))
                jobs = []
                try:
                    if callable(globals().get("fetch_live_jobs_global")):
                        jobs = fetch_live_jobs_global(preferred_country, roles, search_location or preferred_country, st.session_state.get("user_status", "")) or []
                except Exception as exc:
                    st.warning(f"Live job source error: {exc}")
                jobs = _wz54_filter_jobs(jobs, preferred_country, final_city)
                st.write(_wz51_safe_label("Ranking results for your CV and location...", "Ranking results for your CV and location..."))
                try:
                    if jobs and callable(globals().get("curate_job_matches")):
                        jobs = curate_job_matches(jobs, cv_text, {"job_titles": roles, "search_queries": roles, "location": search_location}, preferred_country, st.session_state.get("user_status", ""), limit=25)
                        jobs = _wz54_filter_jobs(jobs, preferred_country, final_city)
                except Exception:
                    pass
                st.session_state["latest_curated_jobs"] = jobs
                st.session_state["workzo_progress_job_matched"] = bool(jobs)
                status.update(label=_wz51_safe_label("Job search complete", "Job search complete"), state="complete", expanded=False)

    jobs = st.session_state.get("latest_curated_jobs") or []
    last_titles = st.session_state.get("last_job_search_target_titles") or target_titles or default_titles or "jobs"
    last_location = st.session_state.get("last_job_search_location_text") or location_label

    if jobs:
        st.markdown("#### " + _wz51_safe_label("Best matches found", "Best matches found"))
        st.caption(_wz51_safe_label("Open the most relevant job, then paste its description in Understand Job to get a real fit score.", "Open the most relevant job, then paste its description in Understand Job to get a real fit score."))
        try:
            if callable(globals().get("render_curated_job_matches")):
                render_curated_job_matches(jobs, preferred_country)
            else:
                for i, job in enumerate(jobs[:12]):
                    _wz51_simple_job_card(job, i)
        except Exception:
            for i, job in enumerate(jobs[:12]):
                _wz51_simple_job_card(job, i)
    else:
        st.info(_wz51_safe_label("No saved job results yet. Search with a specific role title and preferred country/city.", "No saved job results yet. Search with a specific role title and preferred country/city."))
        role_for_link = (last_titles or "jobs").split(",")[0].strip()
        q = urllib.parse.quote_plus(f"{role_for_link} {last_location}")
        st.markdown("#### " + _wz51_safe_label("Quick search links", "Quick search links"))
        st.caption(_wz51_safe_label("Use these if live APIs return too few jobs during testing.", "Use these if live APIs return too few jobs during testing."))
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.link_button("LinkedIn", f"https://www.linkedin.com/jobs/search/?keywords={q}")
        with c2: st.link_button("Indeed", f"https://www.indeed.com/jobs?q={q}")
        with c3: st.link_button("Google Jobs", f"https://www.google.com/search?q={q}+jobs")
        with c4: st.link_button("RemoteOK", f"https://remoteok.com/remote-{urllib.parse.quote_plus(role_for_link)}-jobs")

def _wz51_render_understand_job():
    st.markdown("### " + _wz51_safe_label("understand_job", "Understand Job"))
    st.caption(_wz51_safe_label("Paste a job description. WorkZo checks fit, risks, missing keywords, and next actions.", "Paste a job description. WorkZo checks fit, risks, missing keywords, and next actions."))
    default_jd = st.session_state.get("last_understand_job_description") or st.session_state.get("current_job_description") or st.session_state.get("improve_cv_for_job_desc") or ""
    jd = st.text_area(_wz51_safe_label("Paste the job description", "Paste the job description"), value=default_jd, height=260, key="job_desc_v51_understand")
    if st.button(_wz51_safe_label("Analyze Job Fit", "Analyze Job Fit"), key="btn_understand_job_v51", use_container_width=True):
        if not jd.strip():
            st.warning(_wz51_safe_label("Please paste a job description first.", "Please paste a job description first."))
        else:
            cv_text = str(st.session_state.get("cv_text") or st.session_state.get("clean_structured_cv_text") or "")
            score, matched, missing = _wz51_keyword_match(cv_text, jd)
            st.session_state["current_job_description"] = jd
            st.session_state["last_understand_job_description"] = jd
            st.session_state["improve_cv_for_job_desc"] = jd
            st.session_state["latest_job_analysis"] = {"score": score, "matched": matched, "missing": missing, "source": "job_assist_v51"}
            st.session_state["job_fit_score_value"] = score
            st.session_state["workzo_progress_job_matched"] = True
            try:
                if callable(globals().get("track_event")):
                    track_event("job_analyzed", "Job Assist", {"fit_score": score})
            except Exception:
                pass
            st.success(_wz51_safe_label("Job analyzed. You can now tailor the CV or prepare the application.", "Job analyzed. You can now tailor the CV or prepare the application."))

    analysis = st.session_state.get("latest_job_analysis") or {}
    if jd.strip() or analysis:
        score = int(analysis.get("score") or st.session_state.get("job_fit_score_value") or 0)
        matched = analysis.get("matched") or []
        missing = analysis.get("missing") or []
        st.markdown("#### " + _wz51_safe_label("Job Fit", "Job Fit"))
        c1, c2, c3 = st.columns(3)
        c1.metric(_wz51_safe_label("Fit score", "Fit score"), f"{score}%" if score else "—")
        c2.metric(_wz51_safe_label("Matched keywords", "Matched keywords"), len(matched))
        c3.metric(_wz51_safe_label("Missing keywords", "Missing keywords"), len(missing))
        if missing:
            st.warning(_wz51_safe_label("Missing or weak keywords. Add them only if they are truthful.", "Missing or weak keywords. Add them only if they are truthful."))
            st.write(", ".join([html.escape(str(x)) for x in missing[:15]]))
        if matched:
            st.success(_wz51_safe_label("Your CV already shows some relevant signals.", "Your CV already shows some relevant signals."))
        a, b = st.columns(2)
        with a:
            if st.button(_wz51_safe_label("Improve CV for this job", "Improve CV for this job"), key="wz51_understand_improve", use_container_width=True):
                _wz51_go("cv_documents", {"document_tools_mode": "Improve CV for a Job", "improve_cv_for_job_desc": jd})
        with b:
            if st.button(_wz51_safe_label("Prepare for this job", "Prepare for this job"), key="wz51_understand_prepare", use_container_width=True):
                st.session_state["job_assist_mode_key"] = "prepare"
                st.rerun()


def _wz51_render_prepare_job():
    st.markdown("### " + _wz51_safe_label("prepare_this_job", "Prepare for this Job"))
    st.caption(_wz51_safe_label("Create a focused application and interview preparation plan from your CV and job context.", "Create a focused application and interview preparation plan from your CV and job context."))
    c1, c2 = st.columns(2)
    with c1:
        company = st.text_input(_wz51_safe_label("Target company", "Target company"), value="", key="wz51_target_company_clean", placeholder=_wz51_safe_label("Example: Siemens, SAP, Google", "Example: Siemens, SAP, Google"))
    with c2:
        role = st.text_input(_wz51_safe_label("Target role", "Target role"), value="", key="wz51_target_role_clean", placeholder=_wz51_safe_label("Example: Data Analyst, IT Support", "Example: Data Analyst, IT Support"))
    website = st.text_input(_wz51_safe_label("Company website / careers page", "Company website / careers page"), value="", key="wz51_company_website_clean", placeholder="https://company.com")
    jd = st.text_area(_wz51_safe_label("Job description", "Job description"), value=st.session_state.get("last_understand_job_description", ""), height=220, key="wz51_prepare_jd")
    if st.button(_wz51_safe_label("Prepare application", "Prepare application"), key="wz51_prepare_application", use_container_width=True):
        st.session_state["target_company"] = company.strip()
        st.session_state["target_job_title"] = role.strip()
        st.session_state["company_website"] = website.strip()
        st.session_state["current_job_description"] = jd.strip()
        st.session_state["last_prepare_job_description"] = jd.strip()
        cv_text = str(st.session_state.get("cv_text") or st.session_state.get("clean_structured_cv_text") or "")
        prompt = f"""
You are WorkZo AI. Create a practical, honest job application preparation plan.
Do not invent company facts, skills, salary, language level, or experience.
Preferred language: {st.session_state.get('preferred_language','English')}
Country: {st.session_state.get('country','')}
Company: {company}
Role: {role}
Website: {website}
CV summary/text:
{cv_text[:4000]}
Job description:
{jd[:4000]}
Return concise sections: application focus, CV tailoring points, cover letter angle, interview stories, risks/missing proof, next actions.
"""
        result = ""
        try:
            if callable(globals().get("run_ai_prompt")):
                result = run_ai_prompt(prompt)
        except Exception as exc:
            result = f"Preparation could not use AI right now. Review CV-job alignment manually. Error: {exc}"
        if not result:
            result = "Application focus: tailor your CV to the job description, prepare 3 examples using STAR, and write a cover letter using only truthful company/context details."
        st.session_state["latest_application_prep"] = result
        st.session_state["workzo_progress_prepared"] = True
        try:
            if callable(globals().get("track_event")):
                track_event("application_prepared", "Job Assist", {"company": company, "role": role})
        except Exception:
            pass
        st.success(_wz51_safe_label("Preparation created.", "Preparation created."))
    if st.session_state.get("latest_application_prep"):
        st.markdown("#### " + _wz51_safe_label("Preparation plan", "Preparation plan"))
        st.markdown(str(st.session_state.get("latest_application_prep")))


def _wz51_render_job_assist_page():
    try:
        _wz35_css()
    except Exception:
        pass
    st.subheader(_wz51_safe_label("job_assist", "Job Assist"))
    mode_labels = {
        "find": _wz51_safe_label("find_jobs", "Find Jobs"),
        "understand": _wz51_safe_label("understand_job", "Understand Job"),
        "prepare": _wz51_safe_label("prepare_this_job", "Prepare for this Job"),
    }
    if st.session_state.get("job_assist_mode_key") not in mode_labels:
        st.session_state["job_assist_mode_key"] = "find"
    mode = st.radio(
        "Job Assist mode",
        ["find", "understand", "prepare"],
        horizontal=True,
        format_func=lambda x: mode_labels.get(x, x),
        key="job_assist_mode_key",
        label_visibility="collapsed",
    )
    st.divider()
    if mode == "find":
        _wz51_render_find_jobs()
    elif mode == "understand":
        _wz51_render_understand_job()
    else:
        _wz51_render_prepare_job()


# Final v51 router override: keeps Dashboard/CV/Work-O-Bot but uses classic Job Assist.
def show_dashboard():
    try:
        _wz35_load_state()
    except Exception:
        pass
    try:
        _wz35_sync_language()
    except Exception:
        pass
    try:
        _wz35_force_scroll_top()
    except Exception:
        pass

    page_key = st.session_state.get("nav_page") or st.session_state.get("page") or "dashboard"
    page_key = {"landing":"dashboard", "bot":"workobot", "interview":"workobot", "jobs":"job_assist", "improve_cv":"cv_documents"}.get(page_key, page_key)
    if page_key == "interview_practice":
        page_key = "workobot"
    if page_key not in {"dashboard", "cv_documents", "job_assist", "workobot", "founder_dashboard"}:
        page_key = "dashboard"
    st.session_state["page"] = page_key
    st.session_state["nav_page"] = page_key

    try:
        _wz28_top(True)
    except Exception:
        pass
    try:
        _wz35_sidebar(page_key)
    except Exception:
        pass

    if page_key == "dashboard":
        _wz35_dashboard_home()
    elif page_key == "cv_documents":
        try:
            _wz35_css()
        except Exception:
            pass
        show_document_tools()
    elif page_key == "job_assist":
        _wz51_render_job_assist_page()
    elif page_key == "workobot":
        try:
            _wz35_css()
        except Exception:
            pass
        show_workobot()
    elif page_key == "founder_dashboard":
        if st.session_state.get("founder_unlocked") and callable(globals().get("render_founder_dashboard")):
            render_founder_dashboard()
        else:
            st.warning("Founder dashboard is locked.")

    try:
        _wz35_remember_scores()
        _wz35_save_state()
    except Exception:
        pass
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
    """Preferred Language controls app labels, AI replies, and generated documents."""
    language = str(language or "English").strip() or "English"
    st.session_state.preferred_language = language
    st.session_state.language = language
    st.session_state.ui_language = language
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
        _prev_language = st.session_state.get("preferred_language", "English")
        preferred = st.selectbox(
            txt("preferred_language"),
            language_list,
            index=language_list.index(current_language),
            key="sidebar_preferred_language",
            help=txt("preferred_language_help")
        )
        set_single_preferred_language(preferred)
        if preferred != _prev_language:
            try:
                st.query_params["wz_lang"] = preferred
            except Exception:
                pass
            st.rerun()

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



        st.markdown("<div class='workzo-sidebar-section-label'>Company Context</div>", unsafe_allow_html=True)
        with st.expander("🏢 Company context", expanded=False):
            st.caption("Optional: paste the company website. WorkZo will use it for cover letters, mock tests, and interview preparation.")
            _current_company_url = str(st.session_state.get("target_company_website") or st.session_state.get("company_website") or "")
            _sidebar_company_url = st.text_input(
                "Company website",
                value=_current_company_url,
                placeholder="https://company.com",
                key="target_company_website_sidebar",
            )
            if _sidebar_company_url.strip() != _current_company_url.strip():
                st.session_state["company_website"] = _sidebar_company_url.strip()
                st.session_state["company_website"] = _sidebar_company_url.strip()
            if st.session_state.get("target_company_website"):
                st.caption("Saved for AI outputs in this session.")
            if st.button("Clear company context", key="clear_company_context_sidebar", use_container_width=True):
                for _k in ["target_company_website", "company_website", "target_company_context", "company_context_enabled"]:
                    st.session_state.pop(_k, None)
                st.rerun()

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

        # WorkZo Command Center: simple, smart, action-oriented dashboard.
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

        target_country_plan = st.session_state.get("migration_country") or st.session_state.get("country", "Not specified")
        target_role_plan = st.session_state.get("target_role") or st.session_state.get("detected_target_role") or st.session_state.get("current_role_detected") or ui_label("your target role")
        company_context = st.session_state.get("target_company_website", "")

        # Decide one clear next action. This replaces long feature lists.
        if not cv_ready:
            next_title = ui_label("Add your CV first")
            next_desc = ui_label("Upload or create your CV so WorkZo can score it, improve it, and match jobs.")
            next_button = ui_label("Start setup")
            next_target = "onboarding"
        elif ats_score and ats_score < 75:
            next_title = ui_label("Improve your CV before applying")
            next_desc = ui_label("Your ATS score needs work. Start with a cleaner, job-focused CV.")
            next_button = ui_label("Improve CV")
            next_target = "cv_documents"
        elif not job_ready:
            next_title = ui_label("Paste one real job description")
            next_desc = ui_label("WorkZo can compare your CV with the job and tell you whether to apply or tailor first.")
            next_button = ui_label("Understand a Job")
            next_target = "job_assist"
        elif not prepared_ready:
            next_title = ui_label("Prepare your application")
            next_desc = ui_label("Generate cover-letter focus, interview questions, and application strategy for this job.")
            next_button = ui_label("Prepare Application")
            next_target = "job_assist"
        else:
            next_title = ui_label("Practice and apply")
            next_desc = ui_label("Your application flow is ready. Use Work-O-Bot to practice answers or prepare messages.")
            next_button = ui_label("Open Work-O-Bot")
            next_target = "workobot"

        st.markdown(f"""
        <style>
        .wz-command-hero {{
            border: 1px solid rgba(20,184,166,0.28);
            border-radius: 24px;
            padding: 22px 24px;
            background: linear-gradient(135deg, rgba(37,99,235,0.24), rgba(20,184,166,0.14));
            box-shadow: 0 16px 44px rgba(2,6,23,0.26);
            margin: 10px 0 18px 0;
        }}
        .wz-command-kicker {{ color:#93c5fd; font-size:.78rem; font-weight:850; text-transform:uppercase; letter-spacing:.08em; margin-bottom:6px; }}
        .wz-command-title {{ color:#f8fafc; font-size:1.55rem; font-weight:900; line-height:1.22; margin-bottom:8px; }}
        .wz-command-copy {{ color:#dbeafe; font-size:.98rem; line-height:1.48; max-width:920px; }}
        .wz-smart-card {{ border:1px solid rgba(148,163,184,.16); border-radius:20px; padding:16px; background:rgba(15,23,42,.55); min-height:132px; margin-bottom:12px; }}
        .wz-smart-card.active {{ border-color:rgba(20,184,166,.45); background:linear-gradient(135deg, rgba(20,184,166,.16), rgba(37,99,235,.12)); }}
        .wz-smart-label {{ color:#94a3b8; font-size:.75rem; font-weight:850; text-transform:uppercase; letter-spacing:.07em; margin-bottom:6px; }}
        .wz-smart-title {{ color:#f8fafc; font-size:1.05rem; font-weight:850; margin-bottom:6px; }}
        .wz-smart-copy {{ color:#cbd5e1; font-size:.9rem; line-height:1.42; }}
        .wz-step-pill {{ border:1px solid rgba(148,163,184,.14); background:rgba(15,23,42,.42); border-radius:16px; padding:12px; min-height:88px; }}
        .wz-step-pill.done {{ border-color:rgba(20,184,166,.42); background:rgba(20,184,166,.11); }}
        .wz-step-title {{ color:#f8fafc; font-weight:800; font-size:.92rem; }}
        .wz-step-state {{ color:#94a3b8; font-size:.82rem; margin-top:5px; }}
        </style>
        <div class="wz-command-hero">
            <div class="wz-command-kicker">{html.escape(ui_label('Command Center'))}</div>
            <div class="wz-command-title">{html.escape(ui_label('Your next best career move, simplified'))}</div>
            <div class="wz-command-copy">
                {html.escape(ui_label('WorkZo uses your CV, selected country, language, job description, and company context to guide one clear next step instead of showing too many tools at once.'))}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Top KPI row: immediate signal, not long explanation.
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            render_metric_card(ui_label("Career Health"), f"{application_readiness}%", ui_label("Overall application readiness"))
        with k2:
            render_metric_card(txt("resume_score"), str(resume_score or "—"), score_band(resume_score) if resume_score else ui_label("Needs CV analysis"))
        with k3:
            render_metric_card(txt("ats_score"), str(ats_score or "—"), score_band(ats_score) if ats_score else ui_label("ATS check pending"))
        with k4:
            role_short = str(target_role_plan or ui_label("Not detected"))[:32]
            render_metric_card(ui_label("Target Role"), role_short, str(target_country_plan or "")[:36])

        st.markdown(f"""
        <div class="wz-smart-card active">
            <div class="wz-smart-label">{html.escape(ui_label('Next best action'))}</div>
            <div class="wz-smart-title">{html.escape(str(next_title))}</div>
            <div class="wz-smart-copy">{html.escape(str(next_desc))}</div>
        </div>
        """, unsafe_allow_html=True)

        if st.button(next_button, key="wz_command_center_next_action", use_container_width=True):
            track_button_click(str(next_button), "Dashboard Command Center")
            if next_target == "onboarding":
                st.session_state.page = "onboarding"
                st.session_state.nav_page = "onboarding"
                request_scroll_to_top()
            elif next_target == "job_assist" and not job_ready:
                st.session_state["job_assist_mode_key"] = "understand"
                queue_navigation("job_assist")
            elif next_target == "job_assist":
                st.session_state["job_assist_mode_key"] = "prepare"
                queue_navigation("job_assist")
            else:
                queue_navigation(next_target)
            st.rerun()

        st.markdown(f"### {html.escape(ui_label('Smart actions'))}")
        st.caption(ui_label("Choose one action. WorkZo reuses your existing CV, country, language, and company context."))
        a1, a2, a3, a4 = st.columns(4)
        with a1:
            st.markdown(f"""
            <div class="wz-smart-card">
                <div class="wz-smart-label">CV</div>
                <div class="wz-smart-title">{html.escape(ui_label('Improve CV'))}</div>
                <div class="wz-smart-copy">{html.escape(ui_label('Make your CV cleaner, more ATS-friendly, and job-specific.'))}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(ui_label("Open CV Tools"), key="wz_action_cv", use_container_width=True):
                queue_navigation("cv_documents")
                st.rerun()
        with a2:
            st.markdown(f"""
            <div class="wz-smart-card">
                <div class="wz-smart-label">Jobs</div>
                <div class="wz-smart-title">{html.escape(ui_label('Find Jobs'))}</div>
                <div class="wz-smart-copy">{html.escape(ui_label('Search global roles using your CV and selected country.'))}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(ui_label("Find Jobs"), key="wz_action_jobs", use_container_width=True):
                st.session_state["job_assist_mode_key"] = "find"
                queue_navigation("job_assist")
                st.rerun()
        with a3:
            st.markdown(f"""
            <div class="wz-smart-card">
                <div class="wz-smart-label">Application</div>
                <div class="wz-smart-title">{html.escape(ui_label('Cover Letter'))}</div>
                <div class="wz-smart-copy">{html.escape(ui_label('Generate a focused cover letter based on your CV and job description.'))}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(ui_label("Create Cover Letter"), key="wz_action_cover", use_container_width=True):
                st.session_state["document_tools_mode"] = "Cover Letter Generator + Language"
                queue_navigation("cv_documents")
                st.rerun()
        with a4:
            st.markdown(f"""
            <div class="wz-smart-card">
                <div class="wz-smart-label">Coach</div>
                <div class="wz-smart-title">Work-O-Bot</div>
                <div class="wz-smart-copy">{html.escape(ui_label('Practice answers, messages, German/English, and career communication.'))}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(ui_label("Practice"), key="wz_action_workobot", use_container_width=True):
                queue_navigation("workobot")
                st.rerun()

        st.markdown(f"### {html.escape(ui_label('Application flow'))}")
        f1, f2, f3, f4 = st.columns(4)
        flow = [
            (f1, ui_label("CV added"), cv_ready),
            (f2, ui_label("Job analyzed"), job_ready),
            (f3, ui_label("CV improved"), improved_ready),
            (f4, ui_label("Ready to apply"), prepared_ready),
        ]
        for col, label, done in flow:
            with col:
                st.markdown(f"""
                <div class="wz-step-pill {'done' if done else ''}">
                    <div class="wz-step-title">{'✅ ' if done else '⬜ '}{html.escape(str(label))}</div>
                    <div class="wz-step-state">{html.escape(ui_label('Completed') if done else ui_label('Pending'))}</div>
                </div>
                """, unsafe_allow_html=True)

        if company_context:
            st.info(ui_label("Company context is active. Cover letters and preparation can use the company website you added in the toolbox."))
        else:
            st.caption(ui_label("Tip: Add a company website in the left toolbox to make cover letters and preparation more company-specific."))


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
                        "Market Smart Guide",
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
                    st.markdown("#### Real Interview Simulation")
                    st.info("Use this after applying or when HR invites you for an interview. WorkZo will practice the exact interview using your CV and this job description.")
                    st.markdown(interview_text or "Prepare answers for role fit, technical skills, problem solving, communication, motivation, and country-specific expectations.")
                    if st.button("Start Real Interview Simulation", key="real_interview_setup_from_prepare", use_container_width=True):
                        st.session_state["real_interview_jd"] = st.session_state.get("last_prepare_job_description", job_desc_prepare)
                        st.session_state["real_interview_company"] = target_company or ""
                        st.session_state["prepare_interview_started"] = True
                        st.session_state["workobot_prefill"] = "Start Real Interview Simulation for my prepared job. Use my CV and the saved job description. Ask one question at a time and give specific feedback."
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
                st.caption("Recommended order: tailor your CV, create a cover letter, save the application, apply for the role, then start Work-O-Bot when HR responds.")
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
                    if st.button("Cover letter", key="prep_to_cover_letter", use_container_width=True):
                        st.session_state["cover_letter_job_desc"] = st.session_state.get("last_prepare_job_description", job_desc_prepare)
                        st.session_state["document_tools_mode"] = "Cover Letter Generator + Language"
                        queue_navigation("cv_documents")
                        st.rerun()
                with n3:
                    if st.button("Save tracker", key="save_prepared_job_to_tracker", use_container_width=True):
                        if "application_tracker" not in st.session_state:
                            st.session_state.application_tracker = []
                        title_guess = (target_job_title or "").strip() or "Prepared job"
                        if title_guess == "Prepared job":
                            m = re.search(r"(?i)(job title|role|position)[:\-]\s*(.+)", job_desc_prepare[:1000])
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
                    if st.button("Interview after HR reply", key="prep_to_real_interview_after_hr", use_container_width=True):
                        st.session_state["real_interview_jd"] = st.session_state.get("last_prepare_job_description", job_desc_prepare)
                        st.session_state["real_interview_company"] = target_company or ""
                        st.session_state["workobot_prefill"] = "Start Real Interview Simulation for my prepared job. Use my CV and the saved job description."
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

    elif page_key in ["workobot", "workobot", "career_insights"]:
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

# =========================================================
# WorkZo v15 dashboard score stabilizer
# =========================================================
def _wz15_restore_best_scores():
    try:
        import streamlit as st
        for key in ["cv_score_value", "ats_score_value", "application_readiness_value"]:
            best_key = "_best_" + key
            cur = int(st.session_state.get(key) or 0)
            best = int(st.session_state.get(best_key) or 0)
            if cur < best:
                st.session_state[key] = best
            else:
                st.session_state[best_key] = cur
    except Exception:
        pass
try:
    _wz15_old_show_dashboard = show_dashboard
    def show_dashboard():
        _wz15_restore_best_scores()
        result = _wz15_old_show_dashboard()
        _wz15_restore_best_scores()
        return result
except Exception:
    pass

# =========================================================
# WorkZo v19 - simplified product dashboard override
# Purpose: one clear dashboard purpose, 3 primary cards, stable scores,
# and cleaner sidebar navigation.
# =========================================================
def _wz19_int_score(*keys, default=0):
    try:
        for key in keys:
            val = st.session_state.get(key)
            if val is not None and str(val).strip() != "":
                return max(0, min(100, int(float(val))))
    except Exception:
        pass
    return default


def _wz19_preserve_best_scores():
    """Do not let Home/Dashboard navigation reduce already-computed scores."""
    try:
        for key in ["cv_score_value", "resume_score", "ats_score_value", "application_readiness_value", "interview_score"]:
            cur = _wz19_int_score(key, default=0)
            best_key = "_best_" + key
            best = _wz19_int_score(best_key, default=0)
            if cur < best:
                st.session_state[key] = best
            else:
                st.session_state[best_key] = cur
    except Exception:
        pass


def _wz19_go(page_key: str):
    """Navigation helper that keeps state stable and nudges Streamlit to start at top."""
    try:
        _wz19_preserve_best_scores()
        st.session_state["page"] = page_key
        st.session_state["nav_page"] = page_key
        st.session_state["scroll_anchor"] = "top"
        st.session_state["_wz_top_counter"] = int(st.session_state.get("_wz_top_counter", 0)) + 1
        try:
            st.query_params["page"] = page_key
            st.query_params["top"] = str(st.session_state["_wz_top_counter"])
        except Exception:
            pass
        st.rerun()
    except Exception:
        st.session_state["page"] = page_key
        st.session_state["nav_page"] = page_key
        st.rerun()


def _wz19_current_name():
    for key in ["user_name", "full_name", "candidate_name"]:
        value = str(st.session_state.get(key, "") or "").strip()
        if value:
            return value.split()[0]
    try:
        cv = st.session_state.get("structured_cv_json") or st.session_state.get("workzo_live_cv_structured") or {}
        name = str(cv.get("full_name") or cv.get("name") or "").strip()
        if name:
            return name.split()[0]
    except Exception:
        pass
    return "there"


def _wz19_render_sidebar(page_key: str):
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
                    <div class='workzo-sidebar-version'>Guided career workspace</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class='workzo-sidebar-brand-wrap'>
                <div class='workzo-sidebar-logo-fallback'>WZ</div>
                <div>
                    <div class='workzo-sidebar-brand'>WORKZO AI</div>
                    <div class='workzo-sidebar-version'>Guided career workspace</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div class='workzo-sidebar-section-label'>Navigation</div>", unsafe_allow_html=True)
        nav = [
            ("dashboard", "Dashboard"),
            ("cv_documents", "My CV"),
            ("job_assist", "Job Match"),
            ("workobot", "Work-O-Bot"),
        ]
        # Founder analytics hidden in v26.
        for key, label in nav:
            shown = label + ("  ✓" if page_key == key else "")
            if st.button(shown, key=f"wz19_sidebar_{key}", use_container_width=True):
                _wz19_go(key)

        st.markdown("<div class='workzo-sidebar-section-label'>Settings</div>", unsafe_allow_html=True)
        try:
            language_list = language_options if language_options else ["English", "German", "Dutch"]
            current_language = st.session_state.get("preferred_language", "English")
            if current_language not in language_list:
                current_language = "English" if "English" in language_list else language_list[0]
            preferred = st.selectbox(
                txt("preferred_language"),
                language_list,
                index=language_list.index(current_language),
                key="wz19_sidebar_preferred_language",
            )
            set_single_preferred_language(preferred)
        except Exception:
            pass

        if st.button("Edit setup", key="wz19_edit_setup", use_container_width=True):
            try:
                reset_onboarding()
            except Exception:
                st.session_state["onboarding_complete"] = False
            _wz19_go("onboarding")


def _wz19_recommendation(cv_score: int, ats_score: int, interview_score: int):
    if not str(st.session_state.get("cv_text", "") or "").strip():
        return "Upload or create your CV first so WorkZo can guide the next steps.", "Add My CV", "cv_documents"
    if ats_score < 60:
        return "Your CV needs stronger job alignment. Compare it with a job description and fix only truthful missing keywords.", "Fix CV Match", "cv_documents"
    if interview_score < 70:
        return "Your CV is improving. The next best step is Work-O-Bot based on your CV and the job description.", "Start Practice", "workobot"
    return "You look ready to apply. Find relevant roles and track the ones you apply for.", "Find Jobs", "job_assist"


def _wz19_dashboard_home():
    _wz19_preserve_best_scores()
    name = _wz19_current_name()
    cv_score = _wz19_int_score("cv_score_value", "resume_score", default=0)
    ats_score = _wz19_int_score("ats_score_value", default=0)
    interview_score = _wz19_int_score("interview_score", "interview_readiness", default=40)
    has_job = bool(str(st.session_state.get("last_understand_job_description", "") or st.session_state.get("improve_cv_for_job_desc", "") or st.session_state.get("last_prepare_job_description", "")).strip())

    st.markdown("<div id='top'></div>", unsafe_allow_html=True)
    st.markdown("""
    <style>
    .wz19-hero {border:1px solid rgba(148,163,184,.25); border-radius:22px; padding:28px; background:linear-gradient(135deg, rgba(99,102,241,.10), rgba(20,184,166,.08)); margin-bottom:22px;}
    .wz19-title {font-size:30px; font-weight:800; margin-bottom:4px; color:#f8fafc;}
    .wz19-sub {font-size:16px; color:#cbd5e1; margin-bottom:18px;}
    .wz19-card {border:1px solid rgba(148,163,184,.25); border-radius:18px; padding:20px; min-height:190px; background:rgba(15,23,42,.35);}
    .wz19-card h3 {margin-top:0; font-size:20px;}
    .wz19-card p {color:#cbd5e1; min-height:72px;}
    .wz19-reco {border:1px solid rgba(34,197,94,.30); border-radius:18px; padding:18px; background:rgba(34,197,94,.08); margin-top:10px;}
    .wz19-small-muted {color:#94a3b8; font-size:13px;}
    div[data-testid="stButton"] > button {border-radius:12px; font-weight:650; min-height:42px;}
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class='wz19-hero'>
      <div class='wz19-title'>👋 Welcome back, {html.escape(name)}</div>
      <div class='wz19-sub'>Let’s move you closer to your next job.</div>
    </div>
    """, unsafe_allow_html=True)

    m1, m2, m3 = st.columns(3)
    m1.metric("CV Strength", f"{cv_score}%" if cv_score else "Not analyzed")
    m2.metric("Job Match", f"{ats_score}%" if has_job or ats_score else "Not analyzed")
    m3.metric("Interview Readiness", f"{interview_score}%")
    st.progress(max(cv_score, ats_score, interview_score, 1) / 100)

    if st.button("Continue Your Journey", key="wz19_continue_journey", use_container_width=True):
        msg, label, target = _wz19_recommendation(cv_score, ats_score, interview_score)
        _wz19_go(target)

    st.divider()
    st.subheader("What do you need today?")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""<div class='wz19-card'><h3>🟦 Get More Interviews</h3><p>Analyze your CV against a job, improve ATS alignment, and fix missing keywords honestly.</p></div>""", unsafe_allow_html=True)
        if st.button("Improve My CV", key="wz19_improve_cv", use_container_width=True):
            st.session_state["cv_documents_mode"] = "improve_cv"
            _wz19_go("cv_documents")
    with c2:
        st.markdown("""<div class='wz19-card'><h3>🟩 Prepare for Interview</h3><p>Practice the exact interview using your CV and the job description, then improve your answers.</p></div>""", unsafe_allow_html=True)
        if st.button("Start Work-O-Bot", key="wz19_interview", use_container_width=True):
            st.session_state["workobot_mode"] = "real_interview_simulation"
            _wz21_go("workobot")
    with c3:
        st.markdown("""<div class='wz19-card'><h3>🟧 Find Relevant Jobs</h3><p>Find better-matched roles, review job fit, and save opportunities to your tracker.</p></div>""", unsafe_allow_html=True)
        if st.button("Find Jobs", key="wz19_find_jobs", use_container_width=True):
            _wz19_go("job_assist")

    st.divider()
    st.subheader("🔍 What WorkZo suggests for you")
    reco, btn, target = _wz19_recommendation(cv_score, ats_score, interview_score)
    st.markdown(f"<div class='wz19-reco'>{html.escape(reco)}</div>", unsafe_allow_html=True)
    if st.button(btn, key="wz19_reco_button", use_container_width=True):
        _wz19_go(target)

    st.divider()
    st.subheader("📊 Your progress")
    p1, p2 = st.columns(2)
    p1.write(f"CV Score: **{cv_score or 0} → Target: 85**")
    p2.write(f"Interview Readiness: **{interview_score or 0} → Target: 80**")
    last_cv = st.session_state.get("last_resume_score") or st.session_state.get("_last_cv_score_value")
    if last_cv:
        st.caption(f"Last CV score: {last_cv} • Now: {cv_score}")
    if st.button("Continue Improving", key="wz19_continue_improving", use_container_width=True):
        _wz19_go("cv_documents")


def show_dashboard():
    """WorkZo v19 simplified dashboard router.

    Keeps the dashboard focused on one purpose and routes deeper tools into their flows.
    """
    try:
        _wz19_preserve_best_scores()
    except Exception:
        pass
    page_key = st.session_state.get("nav_page", st.session_state.get("page", "dashboard")) or "dashboard"
    aliases = {"improve_cv": "cv_documents", "jobs": "job_assist", "interview": "workobot", "prepare_job": "job_assist"}
    page_key = aliases.get(page_key, page_key)
    if page_key in ["landing", "onboarding"]:
        page_key = "dashboard"
    st.session_state["page"] = page_key
    st.session_state["nav_page"] = page_key

    _wz19_render_sidebar(page_key)

    if page_key == "dashboard":
        _wz19_dashboard_home()
    elif page_key == "cv_documents":
        st.markdown("<div id='top'></div>", unsafe_allow_html=True)
        show_document_tools()
    elif page_key == "job_assist":
        st.markdown("<div id='top'></div>", unsafe_allow_html=True)
        # Reuse the original full Job Assist page from v18 to avoid breaking existing functionality.
        try:
            _wz15_old_show_dashboard()
        except Exception:
            st.error("Job Match page could not load. Please check the dashboard module.")
    elif page_key in ["workobot", "workobot", "career_insights"]:
        st.markdown("<div id='top'></div>", unsafe_allow_html=True)
        show_workobot()
    elif page_key == "founder_dashboard":
        st.markdown("<div id='top'></div>", unsafe_allow_html=True)
        if st.session_state.get("founder_unlocked"):
            render_founder_dashboard()
        else:
            st.warning("Founder access is locked.")
    else:
        _wz19_dashboard_home()

    try:
        _wz19_preserve_best_scores()
        render_feedback_collector(page_key)
        render_issue_reporter(page_key)
    except Exception:
        pass
    st.divider()
    st.caption("WORKZO AI • Beta • Guided career workspace")
    st.caption("⚠️ WorkZo AI is currently in Beta. Some results may not be perfect yet. Your feedback helps improve the tool.")

# =========================================================
# WorkZo v20 - simplified dashboard + standalone Job Match final override
# =========================================================
def _wz20_clean_text(value):
    try:
        text = str(value or "")
        for a, b in {"ðŸŽ¤":"", "ðŸ“‹":"", "ðŸ”´":"", "ðŸŸ¢":"", "Ã¢â‚¬â€œ":"-", "â€“":"-", "â€”":"-", "â€¢":"-", "Â":"", "�":""}.items():
            text = text.replace(a, b)
        return re.sub(r"\s+", " ", text).strip()
    except Exception:
        return str(value or "")

def _wz20_extract_keywords(text, limit=16):
    stop = set("the and for with from this that your you are will can have has about into role job our their they a an to in of on at as is be by or we us it do does did what who why how".split())
    words = re.findall(r"[A-Za-z][A-Za-z+#.-]{2,}", str(text or "").lower())
    out = []
    for word in words:
        if word not in stop and word not in out:
            out.append(word)
        if len(out) >= limit:
            break
    return out

def _wz20_job_match_score(cv_text, jd_text):
    cv = str(cv_text or "").lower()
    keywords = _wz20_extract_keywords(jd_text, 18)
    if not keywords:
        return 0, [], []
    matched = [k for k in keywords if k in cv]
    missing = [k for k in keywords if k not in cv]
    return int(round(100 * len(matched) / max(1, len(keywords)))), matched, missing

def _wz20_render_job_assist_page():
    st.markdown("<div id='top'></div>", unsafe_allow_html=True)
    st.markdown("## AI Job Application Assistant")
    st.caption("Paste a job description. WorkZo will prepare your CV focus, cover letter direction, interview plan, and market guidance.")

    c1, c2 = st.columns(2)
    with c1:
        target_company = st.text_input("Target company", value=st.session_state.get("target_company", ""), key="wz20_target_company")
    with c2:
        target_title = st.text_input("Target job title", value=st.session_state.get("target_job_title", ""), key="wz20_target_job_title")
    company_website = st.text_input("Company website / careers page (optional)", value=st.session_state.get("target_company_website", ""), key="wz20_company_website", help="Optional but recommended. WorkZo uses this to make CV advice, cover letters, and Work-O-Bot more company-specific.")

    default_jd = st.session_state.get("last_prepare_job_description") or st.session_state.get("last_understand_job_description") or st.session_state.get("improve_cv_for_job_desc") or ""
    jd = st.text_area("Paste the job description", value=default_jd, height=230, key="wz20_job_desc")
    cv_text = st.session_state.get("cv_text") or st.session_state.get("workzo_live_cv_text") or ""

    if not str(cv_text).strip():
        st.warning("Add your CV first so WorkZo can compare it with the job.")

    if st.button("Analyze job match", key="wz20_analyze_job_match", use_container_width=True):
        st.session_state["target_company"] = target_company
        st.session_state["target_job_title"] = target_title
        st.session_state["company_website"] = company_website
        st.session_state["company_context"] = _wz26_fetch_company_context(target_company, company_website)
        st.session_state["last_prepare_job_description"] = jd
        st.session_state["last_understand_job_description"] = jd
        st.session_state["improve_cv_for_job_desc"] = jd
        score, matched, missing = _wz20_job_match_score(cv_text, jd)
        st.session_state["ats_score_value"] = score
        st.session_state["latest_job_analysis"] = {"score": score, "matched": matched, "missing": missing, "company": target_company, "title": target_title, "company_website": company_website, "company_context": st.session_state.get("company_context", "")}
        try:
            _wz19_preserve_best_scores()
        except Exception:
            pass
        st.success("Job match analyzed. Review the guidance below.")

    analysis = st.session_state.get("latest_job_analysis") or {}
    score = int(analysis.get("score") or st.session_state.get("ats_score_value") or 0)
    matched = analysis.get("matched") or []
    missing = analysis.get("missing") or []

    if jd:
        st.divider()
        st.subheader("Job Match Summary")
        m1, m2, m3 = st.columns(3)
        m1.metric("Job Match", f"{score}%" if score else "Run analysis")
        m2.metric("Matched keywords", len(matched))
        m3.metric("Missing keywords", len(missing))
        if analysis.get("company_context"):
            st.caption("Company context is saved and reused for CV tailoring, cover letters, and Work-O-Bot.")

        if score and score < 75:
            st.warning("Your match is not yet strong. Improve the CV only with truthful keywords and examples from your real experience.")
            st.markdown("**Missing keywords to consider if true:** " + (", ".join(_wz20_clean_text(x) for x in missing[:10]) or "No clear missing keywords found."))
            st.markdown("""
**How to improve it honestly:**
- Add missing tools or skills only if you can explain them in an interview.
- Rewrite 2-3 bullet points to mirror the job language.
- Add measurable support, customer, or project examples where possible.
- Do not invent metrics, tools, or responsibilities.
""")
        elif score:
            st.success("Good match. Next step: tailor the CV and prepare a short interview story for this role.")

        st.subheader("Next best actions")
        a, b, c = st.columns(3)
        with a:
            if st.button("Improve CV for this job", key="wz20_go_improve_cv", use_container_width=True):
                st.session_state["cv_documents_mode"] = "improve_cv"
                _wz19_go("cv_documents")
        with b:
            if st.button("Create cover letter", key="wz20_go_cover", use_container_width=True):
                st.session_state["cv_documents_mode"] = "cover_letter"
                st.session_state["cover_letter_job_desc"] = jd
                st.session_state["target_company"] = target_company
                st.session_state["company_website"] = company_website
                st.session_state["company_context"] = _wz26_fetch_company_context(target_company, company_website)
                _wz19_go("cv_documents")
        with c:
            if st.button("Practice interview", key="wz20_go_interview", use_container_width=True):
                st.session_state["workobot_mode"] = "real_interview_simulation"
                st.session_state["real_interview_jd"] = jd
                st.session_state["real_interview_company"] = target_company
                st.session_state["company_website"] = company_website
                st.session_state["company_context"] = _wz26_fetch_company_context(target_company, company_website)
                _wz21_go("workobot")

        with st.expander("Market Smart Guide", expanded=False):
            country = st.session_state.get("country") or st.session_state.get("target_country") or "your target market"
            st.write(f"WorkZo adapts CV wording, interview preparation, and job advice for **{country}** when country information is available.")

def show_dashboard():
    """WorkZo v20 final dashboard router: no duplicate sidebar, standalone Job Match."""
    try:
        _wz19_preserve_best_scores()
    except Exception:
        pass
    page_key = st.session_state.get("nav_page", st.session_state.get("page", "dashboard")) or "dashboard"
    if page_key in ["landing", "onboarding"]:
        page_key = "dashboard"
    st.session_state["page"] = page_key
    st.session_state["nav_page"] = page_key

    _wz19_render_sidebar(page_key)

    if page_key == "dashboard":
        _wz19_dashboard_home()
    elif page_key == "cv_documents":
        st.markdown("<div id='top'></div>", unsafe_allow_html=True)
        show_document_tools()
    elif page_key == "job_assist":
        _wz20_render_job_assist_page()
    elif page_key in ["workobot", "workobot", "career_insights"]:
        st.markdown("<div id='top'></div>", unsafe_allow_html=True)
        show_workobot()
    elif page_key == "founder_dashboard":
        st.markdown("<div id='top'></div>", unsafe_allow_html=True)
        if st.session_state.get("founder_unlocked"):
            render_founder_dashboard()
        else:
            st.warning("Founder access is locked.")
    else:
        _wz19_dashboard_home()

    try:
        _wz19_preserve_best_scores()
        render_feedback_collector(page_key)
        render_issue_reporter(page_key)
    except Exception:
        pass
    st.divider()
    st.caption("WORKZO AI • Beta • Guided career workspace")

# =========================================================
# WorkZo v21 - visible Work-O-Bot + clean sidebar final override
# =========================================================
def _wz21_go(page_key: str):
    """Single reliable navigation helper.

    Earlier builds changed only session_state. On the next rerun the router
    re-read the old ?page= query parameter and sent the user back, which made
    every navigation button feel broken. This updates both session_state and
    URL state before rerun.
    """
    aliases = {
        "improve_cv": "cv_documents",
        "jobs": "job_assist",
        "interview": "workobot",
        "prepare_job": "job_assist",
    }
    page_key = aliases.get(page_key, page_key)
    st.session_state["page"] = page_key
    st.session_state["nav_page"] = page_key
    st.session_state["scroll_to_top_next"] = True
    st.session_state["_workzo_scroll_to_top"] = True
    try:
        st.query_params["page"] = page_key
        st.query_params["wz_top"] = str(st.session_state.get("nav_change_nonce", 0) + 1)
    except Exception:
        pass
    st.rerun()


def _wz21_render_sidebar(page_key: str):
    """Clean final sidebar: no duplicate settings/profile blocks."""
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
                    <div class='workzo-sidebar-version'>Guided career workspace</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("### WorkZo AI")

        st.markdown("<div class='workzo-sidebar-section-label'>Navigation</div>", unsafe_allow_html=True)
        nav = [
            ("dashboard", "Dashboard"),
            ("cv_documents", "My CV"),
            ("job_assist", "Job Match"),
            ("workobot", "Work-O-Bot"),
            ("workobot", "Work-O-Bot"),
        ]
        # Founder analytics hidden in v26.
        for key, label in nav:
            if st.button(label + ("  ✓" if page_key == key else ""), key=f"wz21_sidebar_{key}", use_container_width=True):
                _wz21_go(key)

        st.markdown("<div class='workzo-sidebar-section-label'>Profile</div>", unsafe_allow_html=True)
        st.caption(f"Country: {st.session_state.get('country') or st.session_state.get('target_country') or 'Not set'}")
        st.caption("Resume uploaded" if str(st.session_state.get("cv_text", "")).strip() else "CV missing")

        st.markdown("<div class='workzo-sidebar-section-label'>Settings</div>", unsafe_allow_html=True)
        try:
            language_list = language_options if language_options else ["English", "German", "Dutch"]
            current_language = st.session_state.get("preferred_language", "English")
            if current_language not in language_list:
                current_language = "English" if "English" in language_list else language_list[0]
            preferred = st.selectbox(
                "Language",
                language_list,
                index=language_list.index(current_language),
                key="wz21_sidebar_preferred_language",
            )
            set_single_preferred_language(preferred)
        except Exception:
            pass

        if st.button("Edit setup", key="wz21_edit_setup", use_container_width=True):
            try:
                reset_onboarding()
            except Exception:
                st.session_state["onboarding_complete"] = False
            _wz21_go("onboarding")


def _wz21_render_interview_practice_page():
    """Make speaking/Work-O-Bot discoverable as its own page."""
    st.markdown("<div id='top'></div>", unsafe_allow_html=True)
    st.markdown("## 🎤 Real Interview Simulation")
    st.caption("Practice the exact interview for the job you are applying to — using your CV and the job description.")
    st.info("Use this after applying or when HR invites you for an interview. WorkZo asks tailored questions and gives specific feedback so you can improve and try again.")
    if "render_real_interview_simulation" in globals():
        render_real_interview_simulation()
    elif "show_workobot" in globals():
        st.warning("Interview simulator could not be opened directly, so WorkZo opened the coaching assistant instead.")
        show_workobot()
    else:
        st.error("Interview practice is not available yet. Please check 09_interview_assistant.py is loaded.")


def show_dashboard():
    """WorkZo v21 final dashboard router: clean sidebar + visible Work-O-Bot."""
    try:
        _wz19_preserve_best_scores()
    except Exception:
        pass
    page_key = st.session_state.get("nav_page", st.session_state.get("page", "dashboard")) or "dashboard"
    if page_key in ["landing", "onboarding"]:
        page_key = "dashboard"
    st.session_state["page"] = page_key
    st.session_state["nav_page"] = page_key

    _wz21_render_sidebar(page_key)

    if page_key == "dashboard":
        _wz19_dashboard_home()
    elif page_key == "cv_documents":
        st.markdown("<div id='top'></div>", unsafe_allow_html=True)
        show_document_tools()
    elif page_key == "job_assist":
        _wz20_render_job_assist_page()
    elif page_key == "workobot":
        _wz21_render_interview_practice_page()
    elif page_key == "workobot":
        st.markdown("<div id='top'></div>", unsafe_allow_html=True)
        show_workobot()
    elif page_key == "founder_dashboard":
        st.markdown("<div id='top'></div>", unsafe_allow_html=True)
        if st.session_state.get("founder_unlocked"):
            render_founder_dashboard()
        else:
            st.warning("Founder access is locked.")
    else:
        _wz19_dashboard_home()

    try:
        _wz19_preserve_best_scores()
        render_feedback_collector(page_key)
        render_issue_reporter(page_key)
    except Exception:
        pass
    st.divider()
    st.caption("WORKZO AI • Beta • Guided career workspace")


# =========================================================
# WorkZo v24 - separate Work-O-Bot and Work-O-Bot final override
# =========================================================
def _wz24_render_sidebar(page_key: str):
    """Final sidebar: Work-O-Bot and Work-O-Bot are separate features."""
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
                    <div class='workzo-sidebar-version'>Guided career workspace</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("### WorkZo AI")

        st.markdown("<div class='workzo-sidebar-section-label'>Navigation</div>", unsafe_allow_html=True)
        nav = [
            ("dashboard", "Dashboard"),
            ("cv_documents", "My CV"),
            ("job_assist", "Job Match"),
            ("workobot", "Work-O-Bot"),
            ("workobot", "Work-O-Bot"),
        ]
        # Founder analytics hidden in v26.
        for key, label in nav:
            if st.button(label + ("  ✓" if page_key == key else ""), key=f"wz24_sidebar_{key}", use_container_width=True):
                _wz21_go(key)

        st.markdown("<div class='workzo-sidebar-section-label'>Profile</div>", unsafe_allow_html=True)
        st.caption(f"Country: {st.session_state.get('country') or st.session_state.get('target_country') or 'Not set'}")
        st.caption("Resume uploaded" if str(st.session_state.get("cv_text", "")).strip() else "CV missing")

        st.markdown("<div class='workzo-sidebar-section-label'>Settings</div>", unsafe_allow_html=True)
        try:
            language_list = language_options if language_options else ["English", "German", "Dutch"]
            current_language = st.session_state.get("preferred_language", "English")
            if current_language not in language_list:
                current_language = "English" if "English" in language_list else language_list[0]
            preferred = st.selectbox("Language", language_list, index=language_list.index(current_language), key="wz24_sidebar_preferred_language")
            set_single_preferred_language(preferred)
        except Exception:
            pass

        if st.button("Edit setup", key="wz24_edit_setup", use_container_width=True):
            try:
                reset_onboarding()
            except Exception:
                st.session_state["onboarding_complete"] = False
            _wz21_go("onboarding")


def _wz24_render_workobot_page():
    """Standalone typed career assistant. Interview simulation stays on Work-O-Bot page."""
    st.markdown("<div id='top'></div>", unsafe_allow_html=True)
    st.markdown("## 🤖 Work-O-Bot")
    st.caption("Ask career questions, CV doubts, job-search questions, HR messages, or language-practice questions. For mock interviews, use Work-O-Bot.")
    try:
        show_workobot()
    except Exception as exc:
        st.error("Work-O-Bot could not load.")
        st.exception(exc)


def _wz24_dashboard_home():
    _wz19_preserve_best_scores()
    name = _wz19_current_name()
    cv_score = _wz19_int_score("cv_score_value", "resume_score", default=0)
    ats_score = _wz19_int_score("ats_score_value", default=0)
    interview_score = _wz19_int_score("interview_score", "interview_readiness", default=40)
    has_job = bool(str(st.session_state.get("last_understand_job_description", "") or st.session_state.get("improve_cv_for_job_desc", "") or st.session_state.get("last_prepare_job_description", "")).strip())

    st.markdown("<div id='top'></div>", unsafe_allow_html=True)
    st.markdown("""
    <style>
    .wz19-hero {border:1px solid rgba(148,163,184,.25); border-radius:22px; padding:28px; background:linear-gradient(135deg, rgba(99,102,241,.10), rgba(20,184,166,.08)); margin-bottom:22px;}
    .wz19-title {font-size:30px; font-weight:800; margin-bottom:4px; color:#f8fafc;}
    .wz19-sub {font-size:16px; color:#cbd5e1; margin-bottom:18px;}
    .wz19-card {border:1px solid rgba(148,163,184,.25); border-radius:18px; padding:20px; min-height:190px; background:rgba(15,23,42,.35);}
    .wz19-card h3 {margin-top:0; font-size:20px;}
    .wz19-card p {color:#cbd5e1; min-height:72px;}
    .wz19-reco {border:1px solid rgba(34,197,94,.30); border-radius:18px; padding:18px; background:rgba(34,197,94,.08); margin-top:10px;}
    div[data-testid="stButton"] > button {border-radius:12px; font-weight:650; min-height:42px;}
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class='wz19-hero'>
      <div class='wz19-title'>👋 Welcome back, {html.escape(name)}</div>
      <div class='wz19-sub'>Let’s move you closer to your next job.</div>
    </div>
    """, unsafe_allow_html=True)

    m1, m2, m3 = st.columns(3)
    m1.metric("CV Strength", f"{cv_score}%" if cv_score else "Not analyzed")
    m2.metric("Job Match", f"{ats_score}%" if has_job or ats_score else "Not analyzed")
    m3.metric("Interview Readiness", f"{interview_score}%")
    st.progress(max(cv_score, ats_score, interview_score, 1) / 100)

    if st.button("Continue Your Journey", key="wz24_continue_journey", use_container_width=True):
        _, _, target = _wz19_recommendation(cv_score, ats_score, interview_score)
        _wz21_go(target)

    st.divider()
    st.subheader("What do you need today?")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""<div class='wz19-card'><h3>🟦 Get More Interviews</h3><p>Analyze your CV against a job, improve ATS alignment, and fix missing keywords honestly.</p></div>""", unsafe_allow_html=True)
        if st.button("Improve My CV", key="wz24_improve_cv", use_container_width=True):
            st.session_state["cv_documents_mode"] = "improve_cv"
            _wz21_go("cv_documents")
    with c2:
        st.markdown("""<div class='wz19-card'><h3>🟩 Prepare for Interview</h3><p>Practice the exact interview using your CV and the job description, then improve your answers.</p></div>""", unsafe_allow_html=True)
        if st.button("Start Work-O-Bot", key="wz24_interview", use_container_width=True):
            _wz21_go("workobot")
    with c3:
        st.markdown("""<div class='wz19-card'><h3>🟧 Find Relevant Jobs</h3><p>Find better-matched roles, review job fit, and save opportunities to your tracker.</p></div>""", unsafe_allow_html=True)
        if st.button("Find Jobs", key="wz24_find_jobs", use_container_width=True):
            _wz21_go("job_assist")

    st.divider()
    st.subheader("🔍 What WorkZo suggests for you")
    reco, btn, target = _wz19_recommendation(cv_score, ats_score, interview_score)
    st.markdown(f"<div class='wz19-reco'>{html.escape(reco)}</div>", unsafe_allow_html=True)
    if st.button(btn, key="wz24_reco_button", use_container_width=True):
        _wz21_go(target)

    st.divider()
    help_col, bot_col = st.columns([2, 1])
    with help_col:
        st.subheader("Need help or have a question?")
        st.caption("Use Work-O-Bot for general career questions, HR messages, CV doubts, job-search advice, or language practice.")
    with bot_col:
        if st.button("Ask Work-O-Bot", key="wz24_ask_workobot", use_container_width=True):
            _wz21_go("workobot")


def show_dashboard():
    """WorkZo v24 final router: Work-O-Bot and Work-O-Bot are separate."""
    try:
        _wz19_preserve_best_scores()
    except Exception:
        pass
    page_key = st.session_state.get("nav_page", st.session_state.get("page", "dashboard")) or "dashboard"
    aliases = {"improve_cv": "cv_documents", "jobs": "job_assist", "interview": "workobot", "prepare_job": "job_assist"}
    page_key = aliases.get(page_key, page_key)
    if page_key in ["landing", "onboarding"]:
        page_key = "dashboard"
    st.session_state["page"] = page_key
    st.session_state["nav_page"] = page_key

    _wz24_render_sidebar(page_key)

    if page_key == "dashboard":
        _wz24_dashboard_home()
    elif page_key == "cv_documents":
        st.markdown("<div id='top'></div>", unsafe_allow_html=True)
        show_document_tools()
    elif page_key == "job_assist":
        _wz20_render_job_assist_page()
    elif page_key == "workobot":
        _wz21_render_interview_practice_page()
    elif page_key == "workobot":
        _wz24_render_workobot_page()
    elif page_key == "founder_dashboard":
        st.markdown("<div id='top'></div>", unsafe_allow_html=True)
        if st.session_state.get("founder_unlocked"):
            render_founder_dashboard()
        else:
            st.warning("Founder access is locked.")
    else:
        _wz24_dashboard_home()

    try:
        _wz19_preserve_best_scores()
        render_feedback_collector(page_key)
        render_issue_reporter(page_key)
    except Exception:
        pass
    st.divider()
    st.caption("WORKZO AI • Beta • Guided career workspace")



# =========================================================
# WorkZo v26 - company context helper + founder analytics hidden
# =========================================================
def _wz26_fetch_company_context(company_name: str = "", company_website: str = "") -> str:
    company_name = str(company_name or "").strip()
    company_website = str(company_website or "").strip()
    cached_key = f"_wz26_company_context::{company_name}::{company_website}"
    if cached_key in st.session_state:
        return st.session_state.get(cached_key, "")
    context = ""
    if company_website:
        url = company_website if company_website.startswith(("http://", "https://")) else "https://" + company_website
        try:
            import requests, re as _re
            r = requests.get(url, timeout=3, headers={"User-Agent": "WorkZoAI/1.0"})
            if r.ok:
                txt0 = _re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", " ", r.text, flags=_re.I)
                txt0 = _re.sub(r"<[^>]+>", " ", txt0)
                txt0 = _re.sub(r"\s+", " ", txt0).strip()
                context = txt0[:1800]
        except Exception:
            context = ""
    if not context and company_name:
        context = f"Company name provided by user: {company_name}. If public company details are not known, avoid inventing facts and ask the user to paste company details."
    st.session_state[cached_key] = context
    return context

# =========================================================
# WorkZo v25 - navigation top fix + faster dashboard + Work-O-Bot visible
# =========================================================
def _wz25_scroll_to_top_if_needed(force: bool = False):
    """Scroll to top only after navigation; avoids running script on every rerun."""
    try:
        should_scroll = force or bool(st.session_state.pop("_workzo_scroll_to_top", False)) or bool(st.session_state.pop("scroll_to_top_next", False))
        if not should_scroll:
            return
        script = """
        <script>
        const scrollTop = () => {
          try { window.parent.scrollTo({top: 0, left: 0, behavior: 'instant'}); } catch(e) {}
          try { window.parent.document.querySelector('[data-testid="stAppViewContainer"]').scrollTo({top:0,left:0,behavior:'instant'}); } catch(e) {}
          try { window.parent.document.querySelector('section.main').scrollTo({top:0,left:0,behavior:'instant'}); } catch(e) {}
          try { window.parent.document.querySelector('.main').scrollTo({top:0,left:0,behavior:'instant'}); } catch(e) {}
        };
        scrollTop(); setTimeout(scrollTop, 50); setTimeout(scrollTop, 200);
        </script>
        """
        if hasattr(st, "iframe"):
            st.iframe(srcdoc=script, height=0, width=0)
        else:
            import streamlit.components.v1 as components
            components.html(script, height=0, width=0)
    except Exception:
        pass


def _wz25_go(page_key: str):
    aliases = {
        "improve_cv": "cv_documents",
        "jobs": "job_assist",
        "interview": "workobot",
        "prepare_job": "job_assist",
        "bot": "workobot",
        "work-o-bot": "workobot",
    }
    page_key = aliases.get(page_key, page_key)
    st.session_state["page"] = page_key
    st.session_state["nav_page"] = page_key
    st.session_state["_workzo_scroll_to_top"] = True
    st.session_state["scroll_to_top_next"] = True
    try:
        st.session_state["nav_change_nonce"] = int(st.session_state.get("nav_change_nonce", 0)) + 1
    except Exception:
        st.session_state["nav_change_nonce"] = 1
    try:
        st.query_params["page"] = page_key
        st.query_params["wz_top"] = str(st.session_state.get("nav_change_nonce", 1))
    except Exception:
        pass
    st.rerun()

# Override older helpers so old buttons also use reliable navigation.
_wz21_go = _wz25_go
_wz19_go = _wz25_go
go_to_nav = _wz25_go


def _wz25_render_sidebar(page_key: str):
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
                    <div class='workzo-sidebar-version'>Guided career workspace</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("### WorkZo AI")

        st.markdown("<div class='workzo-sidebar-section-label'>Navigation</div>", unsafe_allow_html=True)
        nav = [
            ("dashboard", "Dashboard"),
            ("cv_documents", "My CV"),
            ("job_assist", "Job Match"),
            ("workobot", "Work-O-Bot"),
            ("workobot", "Work-O-Bot"),
        ]
        # Founder analytics hidden in v26.
        for key, label in nav:
            if st.button(label + (" ✓" if page_key == key else ""), key=f"wz25_sidebar_{key}", use_container_width=True):
                _wz25_go(key)

        st.markdown("<div class='workzo-sidebar-section-label'>Profile</div>", unsafe_allow_html=True)
        st.caption(f"Country: {st.session_state.get('country') or st.session_state.get('target_country') or 'Not set'}")
        st.caption("Resume uploaded" if str(st.session_state.get("cv_text", "")).strip() else "CV missing")

        st.markdown("<div class='workzo-sidebar-section-label'>Settings</div>", unsafe_allow_html=True)
        try:
            language_list = language_options if language_options else ["English", "German", "Dutch"]
            current_language = st.session_state.get("preferred_language", "English")
            if current_language not in language_list:
                current_language = "English" if "English" in language_list else language_list[0]
            preferred = st.selectbox("Language", language_list, index=language_list.index(current_language), key="wz25_sidebar_preferred_language")
            set_single_preferred_language(preferred)
        except Exception:
            pass

        if st.button("Edit setup", key="wz25_edit_setup", use_container_width=True):
            try:
                reset_onboarding()
            except Exception:
                st.session_state["onboarding_complete"] = False
            _wz25_go("onboarding")


def _wz25_dashboard_home():
    _wz19_preserve_best_scores()
    name = _wz19_current_name()
    cv_score = _wz19_int_score("cv_score_value", "resume_score", default=0)
    ats_score = _wz19_int_score("ats_score_value", default=0)
    interview_score = _wz19_int_score("interview_score", "interview_readiness", default=40)
    has_job = bool(str(st.session_state.get("last_understand_job_description", "") or st.session_state.get("improve_cv_for_job_desc", "") or st.session_state.get("last_prepare_job_description", "")).strip())

    st.markdown("<div id='workzo-page-top'></div>", unsafe_allow_html=True)
    st.markdown("""
    <style>
    .wz25-hero {border:1px solid rgba(148,163,184,.25); border-radius:22px; padding:28px; background:linear-gradient(135deg, rgba(99,102,241,.10), rgba(20,184,166,.08)); margin-bottom:22px;}
    .wz25-title {font-size:30px; font-weight:800; margin-bottom:4px; color:#f8fafc;}
    .wz25-sub {font-size:16px; color:#cbd5e1; margin-bottom:0;}
    .wz25-card {border:1px solid rgba(148,163,184,.25); border-radius:18px; padding:20px; min-height:190px; background:rgba(15,23,42,.35);}
    .wz25-card h3 {margin-top:0; font-size:20px;}
    .wz25-card p {color:#cbd5e1; min-height:72px;}
    .wz25-reco {border:1px solid rgba(34,197,94,.30); border-radius:18px; padding:18px; background:rgba(34,197,94,.08); margin-top:10px;}
    div[data-testid="stButton"] > button {border-radius:12px; font-weight:650; min-height:42px;}
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class='wz25-hero'>
      <div class='wz25-title'>👋 Welcome back, {html.escape(name)}</div>
      <div class='wz25-sub'>Let’s move you closer to your next job.</div>
    </div>
    """, unsafe_allow_html=True)

    m1, m2, m3 = st.columns(3)
    m1.metric("CV Strength", f"{cv_score}%" if cv_score else "Not analyzed")
    m2.metric("Job Match", f"{ats_score}%" if has_job or ats_score else "Not analyzed")
    m3.metric("Interview Readiness", f"{interview_score}%")
    st.caption("Progress updates after you improve your CV, analyze a job, or complete Work-O-Bot.")

    if st.button("Continue Your Journey", key="wz25_continue_journey", use_container_width=False):
        _, _, target = _wz19_recommendation(cv_score, ats_score, interview_score)
        _wz25_go(target)

    st.divider()
    st.subheader("What do you need today?")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""<div class='wz25-card'><h3>🟦 Get More Interviews</h3><p>Analyze your CV against a job, improve ATS alignment, and fix missing keywords honestly.</p></div>""", unsafe_allow_html=True)
        if st.button("Improve My CV", key="wz25_improve_cv", use_container_width=True):
            st.session_state["cv_documents_mode"] = "improve_cv"
            _wz25_go("cv_documents")
    with c2:
        st.markdown("""<div class='wz25-card'><h3>🟩 Prepare for Interview</h3><p>Practice the exact interview using your CV and the job description, then improve your answers.</p></div>""", unsafe_allow_html=True)
        if st.button("Start Work-O-Bot", key="wz25_interview", use_container_width=True):
            _wz25_go("workobot")
    with c3:
        st.markdown("""<div class='wz25-card'><h3>🟧 Find Relevant Jobs</h3><p>Find better-matched roles, review job fit, and save opportunities to your tracker.</p></div>""", unsafe_allow_html=True)
        if st.button("Find Jobs", key="wz25_find_jobs", use_container_width=True):
            _wz25_go("job_assist")

    st.divider()
    st.subheader("🔍 What WorkZo suggests for you")
    reco, btn, target = _wz19_recommendation(cv_score, ats_score, interview_score)
    st.markdown(f"<div class='wz25-reco'>{html.escape(reco)}</div>", unsafe_allow_html=True)
    if st.button(btn, key="wz25_reco_button", use_container_width=True):
        _wz25_go(target)

    st.divider()
    help_col, bot_col = st.columns([2, 1])
    with help_col:
        st.subheader("Need help or have a question?")
        st.caption("Use Work-O-Bot for typed career questions, HR messages, CV doubts, job-search advice, or language practice.")
    with bot_col:
        if st.button("Ask Work-O-Bot", key="wz25_ask_workobot", use_container_width=True):
            _wz25_go("workobot")


def _wz25_render_workobot_page():
    st.markdown("<div id='workzo-page-top'></div>", unsafe_allow_html=True)
    st.markdown("## 🤖 Work-O-Bot")
    st.caption("Typed career assistant for CV doubts, job-search questions, HR messages, and language practice. Use Work-O-Bot for mock interviews.")
    try:
        show_workobot()
    except Exception as exc:
        st.error("Work-O-Bot could not load.")
        st.exception(exc)


def show_dashboard():
    try:
        _wz19_preserve_best_scores()
    except Exception:
        pass
    page_key = st.session_state.get("nav_page", st.session_state.get("page", "dashboard")) or "dashboard"
    aliases = {"improve_cv": "cv_documents", "jobs": "job_assist", "interview": "workobot", "prepare_job": "job_assist", "bot": "workobot"}
    page_key = aliases.get(page_key, page_key)
    if page_key in ["landing", "onboarding"]:
        page_key = "dashboard"
    st.session_state["page"] = page_key
    st.session_state["nav_page"] = page_key

    _wz25_scroll_to_top_if_needed()
    _wz25_render_sidebar(page_key)

    if page_key == "dashboard":
        _wz25_dashboard_home()
    elif page_key == "cv_documents":
        st.markdown("<div id='workzo-page-top'></div>", unsafe_allow_html=True)
        show_document_tools()
    elif page_key == "job_assist":
        st.markdown("<div id='workzo-page-top'></div>", unsafe_allow_html=True)
        _wz20_render_job_assist_page()
    elif page_key == "workobot":
        st.markdown("<div id='workzo-page-top'></div>", unsafe_allow_html=True)
        _wz21_render_interview_practice_page()
    elif page_key == "workobot":
        _wz25_render_workobot_page()
    elif page_key == "founder_dashboard":
        _wz25_dashboard_home()
    else:
        _wz25_dashboard_home()

    try:
        _wz19_preserve_best_scores()
        render_feedback_collector(page_key)
        render_issue_reporter(page_key)
    except Exception:
        pass
    st.divider()
    st.caption("WORKZO AI • Beta • Guided career workspace")


# =========================================================
# WorkZo v27 - FINAL lightweight dashboard/sidebar/navigation override
# =========================================================
def _wz27_force_top():
    try:
        st.markdown("<div id='workzo-page-top'></div>", unsafe_allow_html=True)
        script = """
        <script>
        function wzTop(){
          try { window.parent.scrollTo(0,0); } catch(e) {}
          try { window.parent.document.documentElement.scrollTop = 0; } catch(e) {}
          try { window.parent.document.body.scrollTop = 0; } catch(e) {}
          try { window.parent.document.querySelector('[data-testid="stAppViewContainer"]').scrollTop = 0; } catch(e) {}
          try { window.parent.document.querySelector('section.main').scrollTop = 0; } catch(e) {}
          try { window.parent.document.querySelector('.main').scrollTop = 0; } catch(e) {}
          try { window.parent.document.getElementById('workzo-page-top').scrollIntoView({block:'start', behavior:'instant'}); } catch(e) {}
        }
        wzTop(); setTimeout(wzTop, 30); setTimeout(wzTop, 120); setTimeout(wzTop, 300);
        </script>
        """
        iframe_fn = getattr(st, 'iframe', None)
        if iframe_fn:
            iframe_fn(srcdoc=script, height=0, width=0)
        else:
            try:
                import streamlit.components.v1 as components
                components.html(script, height=0, width=0)
            except Exception:
                pass
    except Exception:
        pass


def _wz27_go(page_key: str):
    aliases = {
        'home': 'dashboard', 'improve_cv': 'cv_documents', 'my_cv': 'cv_documents',
        'jobs': 'job_assist', 'job_match': 'job_assist', 'prepare_job': 'job_assist',
        'interview': 'workobot', 'bot': 'workobot', 'work-o-bot': 'workobot',
        'founder_dashboard': 'dashboard',
    }
    page_key = aliases.get(str(page_key or 'dashboard'), str(page_key or 'dashboard'))
    st.session_state['page'] = page_key
    st.session_state['nav_page'] = page_key
    st.session_state['_workzo_scroll_to_top'] = True
    try:
        n = int(st.session_state.get('nav_change_nonce', 0)) + 1
        st.session_state['nav_change_nonce'] = n
        st.query_params['page'] = page_key
        st.query_params['top'] = str(n)
    except Exception:
        pass
    st.rerun()

_wz25_go = _wz27_go
_wz24_go = _wz27_go
_wz21_go = _wz27_go
_wz19_go = _wz27_go
go_to_nav = _wz27_go


def _wz27_score(*keys, default=0):
    for k in keys:
        try:
            v = st.session_state.get(k)
            if v is not None and str(v).strip() != '':
                return max(0, min(100, int(float(v))))
        except Exception:
            pass
    return default


def _wz27_sidebar(page_key: str):
    with st.sidebar:
        try:
            logo_src = image_to_data_uri(ICON_PATH) or image_to_data_uri(LOGO_PATH)
        except Exception:
            logo_src = None
        if logo_src:
            st.markdown(f"""
            <div style='border:1px solid rgba(20,184,166,.35);border-radius:18px;padding:16px;margin-bottom:16px;background:rgba(15,23,42,.65)'>
                <img src='{logo_src}' style='width:44px;height:44px;border-radius:12px;margin-bottom:10px;'>
                <div style='font-weight:800;font-size:20px;letter-spacing:.04em'>WORKZO AI</div>
                <div style='font-size:12px;color:#94a3b8'>Guided career workspace</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown('### WorkZo AI')
        st.markdown('##### Navigation')
        nav = [('dashboard','Dashboard'),('cv_documents','My CV'),('job_assist','Job Match'),('workobot','Work-O-Bot')]
        for key, label in nav:
            marker = ' ✓' if page_key == key else ''
            if st.button(label + marker, key=f'wz27_nav_{key}', use_container_width=True):
                _wz27_go(key)
        st.markdown('##### Profile')
        st.caption(f"Country: {st.session_state.get('country') or st.session_state.get('target_country') or 'Not set'}")
        st.caption('Resume uploaded' if str(st.session_state.get('cv_text','')).strip() else 'CV missing')
        st.markdown('##### Settings')
        try:
            language_list = language_options if language_options else ['English', 'German', 'Dutch']
            current = st.session_state.get('preferred_language', 'English')
            if current not in language_list:
                current = 'English' if 'English' in language_list else language_list[0]
            chosen = st.selectbox('Language', language_list, index=language_list.index(current), key='wz27_language')
            set_single_preferred_language(chosen)
        except Exception:
            pass
        if st.button('Edit setup', key='wz27_edit_setup', use_container_width=True):
            try:
                reset_onboarding()
            except Exception:
                st.session_state['onboarding_complete'] = False
            _wz27_go('onboarding')


def _wz27_dashboard_home():
    cv_score = _wz27_score('cv_score_value','resume_score', default=75 if str(st.session_state.get('cv_text','')).strip() else 0)
    has_job_text = str(st.session_state.get('current_job_description','') or st.session_state.get('last_understand_job_description','') or st.session_state.get('improve_cv_for_job_desc','')).strip()
    ats_score = _wz27_score('ats_score_value','job_match_score', default=70 if has_job_text else 0)
    interview_score = _wz27_score('interview_score','interview_readiness', default=40)
    name = st.session_state.get('user_name') or st.session_state.get('candidate_name') or 'there'
    st.markdown("""
    <style>
      .wz27-hero{border:1px solid rgba(148,163,184,.22);border-radius:24px;padding:28px;background:linear-gradient(135deg,rgba(30,64,175,.16),rgba(20,184,166,.10));margin-bottom:22px;}
      .wz27-title{font-size:30px;font-weight:850;color:#f8fafc;margin-bottom:4px;}
      .wz27-sub{font-size:16px;color:#cbd5e1;}
      .wz27-card{border:1px solid rgba(148,163,184,.22);border-radius:18px;padding:20px;min-height:180px;background:rgba(15,23,42,.38);}
      .wz27-card h3{font-size:20px;margin-top:0;}
      .wz27-card p{color:#cbd5e1;min-height:70px;}
      .wz27-reco{border:1px solid rgba(34,197,94,.28);border-radius:16px;padding:16px;background:rgba(34,197,94,.08);}
      div[data-testid="stButton"] > button{border-radius:12px;min-height:42px;font-weight:650;}
    </style>
    """, unsafe_allow_html=True)
    st.markdown(f"""
    <div class='wz27-hero'>
      <div class='wz27-title'>👋 Welcome back, {html.escape(str(name))}</div>
      <div class='wz27-sub'>Let’s move you closer to your next job.</div>
    </div>
    """, unsafe_allow_html=True)
    c1,c2,c3 = st.columns(3)
    c1.metric('CV Strength', f'{cv_score}%' if cv_score else 'Not analyzed')
    c2.metric('Job Match', f'{ats_score}%' if ats_score else 'Not analyzed')
    c3.metric('Interview Readiness', f'{interview_score}%')
    st.caption('Scores update after you improve a CV, analyze a job, or complete Work-O-Bot.')
    if st.button('Continue Your Journey', key='wz27_continue', use_container_width=False):
        if not cv_score: _wz27_go('cv_documents')
        elif not ats_score: _wz27_go('job_assist')
        elif interview_score < 70: _wz27_go('workobot')
        else: _wz27_go('job_assist')
    st.divider()
    st.subheader('What do you need today?')
    a,b,c = st.columns(3)
    with a:
        st.markdown("<div class='wz27-card'><h3>🟦 Get More Interviews</h3><p>Improve your CV for a job description, strengthen ATS alignment, and keep changes honest.</p></div>", unsafe_allow_html=True)
        if st.button('Improve My CV', key='wz27_improve', use_container_width=True):
            st.session_state['cv_documents_mode']='improve_cv'; _wz27_go('cv_documents')
    with b:
        st.markdown("<div class='wz27-card'><h3>🟩 Prepare for Interview</h3><p>Practice interview questions based only on your CV, job description, and company context.</p></div>", unsafe_allow_html=True)
        if st.button('Start Work-O-Bot', key='wz27_interview', use_container_width=True):
            _wz27_go('workobot')
    with c:
        st.markdown("<div class='wz27-card'><h3>🟧 Find Relevant Jobs</h3><p>Find better-matched jobs, understand fit, and use the job details across your application.</p></div>", unsafe_allow_html=True)
        if st.button('Find Jobs', key='wz27_jobs', use_container_width=True):
            _wz27_go('job_assist')
    st.divider()
    st.subheader('What WorkZo suggests for you')
    if not cv_score:
        reco, target = 'Add or create your CV first. WorkZo needs this to personalize every feature.', 'cv_documents'
    elif not ats_score:
        reco, target = 'Paste a job description and company website so WorkZo can analyze your match.', 'job_assist'
    elif ats_score < 75:
        reco, target = 'Your job match can improve. Strengthen only truthful keywords from the JD.', 'cv_documents'
    elif interview_score < 70:
        reco, target = 'Practice the real interview using your CV and the job description before applying.', 'workobot'
    else:
        reco, target = 'You look ready to apply. Prepare a focused cover letter and track your application.', 'job_assist'
    st.markdown(f"<div class='wz27-reco'>{html.escape(reco)}</div>", unsafe_allow_html=True)
    if st.button('Do this next', key='wz27_next', use_container_width=True):
        _wz27_go(target)
    st.divider()
    st.subheader('Need help?')
    st.caption('Work-O-Bot is for typed questions: CV doubts, HR messages, career decisions, job search, and language practice.')
    if st.button('Ask Work-O-Bot', key='wz27_bot', use_container_width=False):
        _wz27_go('workobot')


def _wz27_job_assist_page():
    st.markdown('## AI Job Application Assistant')
    st.caption('Paste a job description and company website. WorkZo uses this context across CV improvement, cover letter, and Work-O-Bot without inventing facts.')
    col1, col2 = st.columns(2)
    with col1:
        st.text_input('Target company', value=st.session_state.get('target_company',''), key='wz27_target_company')
    with col2:
        st.text_input('Company website / careers page', value=st.session_state.get('target_company_website',''), key='wz27_company_website', help='Optional, but recommended for company-aware cover letters and interview questions.')
    st.session_state['target_company'] = st.session_state.get('wz27_target_company','')
    st.session_state['company_website'] = st.session_state.get('wz27_company_website','')
    try:
        _wz20_render_job_assist_page()
    except Exception as exc:
        st.error('Job Match page could not load. Showing a safe basic version instead.')
        jd = st.text_area('Paste the job description', value=st.session_state.get('current_job_description',''), height=220, key='wz27_safe_jd')
        if jd.strip():
            st.session_state['current_job_description'] = jd
            st.session_state['last_understand_job_description'] = jd
        if st.button('Use this job for CV + Work-O-Bot', key='wz27_use_job', use_container_width=True):
            _wz27_go('cv_documents')


def _wz27_workobot_page():
    st.markdown('## Work-O-Bot')
    st.caption('Typed assistant for career questions, CV doubts, HR messages, job search, and language practice. Use Work-O-Bot for mock interviews.')
    try:
        show_workobot()
    except Exception as exc:
        st.error('Work-O-Bot could not load.')
        st.exception(exc)


def show_dashboard():
    page_key = st.session_state.get('nav_page') or st.session_state.get('page') or 'dashboard'
    page_key = {'landing':'dashboard','onboarding':'dashboard','founder_dashboard':'dashboard','bot':'workobot','interview':'workobot','jobs':'job_assist','improve_cv':'cv_documents'}.get(page_key, page_key)
    st.session_state['page'] = page_key
    st.session_state['nav_page'] = page_key
    _wz27_force_top()
    _wz27_sidebar(page_key)
    if page_key == 'dashboard':
        _wz27_dashboard_home()
    elif page_key == 'cv_documents':
        show_document_tools()
    elif page_key == 'job_assist':
        _wz27_job_assist_page()
    elif page_key == 'workobot':
        try:
            _wz21_render_interview_practice_page()
        except Exception:
            if 'show_interview_simulation' in globals():
                show_interview_simulation()
            else:
                st.error('Work-O-Bot could not load.')
    elif page_key == 'workobot':
        _wz27_workobot_page()
    else:
        _wz27_dashboard_home()
    st.divider()
    st.caption('WORKZO AI • Beta • Guided career workspace')

# =========================================================
# WorkZo v28 - hard final UX/stability override
# Fixes: dashboard progress bar removal, reliable top scroll,
# visible Work-O-Bot, no founder analytics, lighter/faster dashboard.
# =========================================================
def _wz28_top(force: bool = True):
    try:
        st.markdown("<div id='workzo-top-anchor'></div>", unsafe_allow_html=True)
        js = """
        <script>
        function workzoTop(){
          const doc = window.parent.document;
          try { window.parent.scrollTo(0,0); } catch(e) {}
          try { doc.documentElement.scrollTop = 0; } catch(e) {}
          try { doc.body.scrollTop = 0; } catch(e) {}
          const selectors = ['[data-testid="stAppViewContainer"]','section.main','.main','.block-container'];
          for (const s of selectors){ try { const el = doc.querySelector(s); if(el){ el.scrollTop = 0; } } catch(e) {} }
          try { doc.getElementById('workzo-top-anchor').scrollIntoView({block:'start'}); } catch(e) {}
        }
        workzoTop(); setTimeout(workzoTop, 20); setTimeout(workzoTop, 120); setTimeout(workzoTop, 350);
        </script>
        """
        if hasattr(st, 'iframe'):
            st.iframe(srcdoc=js, height=1, width=1)
        else:
            try:
                import streamlit.components.v1 as components
                components.html(js, height=1, width=1)
            except Exception:
                pass
    except Exception:
        pass


def _wz28_css():
    st.markdown("""
    <style>
      .wz28-hide-progress [data-testid="stProgress"] {display:none !important;}
      div[data-testid="stButton"] > button{border-radius:12px;min-height:42px;font-weight:650;}
      .wz28-hero{border:1px solid rgba(148,163,184,.22);border-radius:24px;padding:28px;background:linear-gradient(135deg,rgba(30,64,175,.14),rgba(20,184,166,.10));margin-bottom:22px;}
      .wz28-title{font-size:30px;font-weight:850;color:#f8fafc;margin-bottom:4px;}
      .wz28-sub{font-size:16px;color:#cbd5e1;}
      .wz28-card{border:1px solid rgba(148,163,184,.22);border-radius:18px;padding:20px;min-height:178px;background:rgba(15,23,42,.38);}
      .wz28-card h3{font-size:20px;margin-top:0;}
      .wz28-card p{color:#cbd5e1;min-height:68px;}
      .wz28-reco{border:1px solid rgba(34,197,94,.28);border-radius:16px;padding:16px;background:rgba(34,197,94,.08);}
      .wz28-sidebar-card{border:1px solid rgba(20,184,166,.35);border-radius:18px;padding:16px;margin-bottom:16px;background:rgba(15,23,42,.65);}
      .wz28-sidebar-logo{width:44px;height:44px;border-radius:12px;margin-bottom:10px;}
      .wz28-sidebar-brand{font-weight:800;font-size:20px;letter-spacing:.04em;}
      .wz28-sidebar-small{font-size:12px;color:#94a3b8;}
    </style>
    """, unsafe_allow_html=True)


def _wz28_go(page_key: str):
    aliases = {
        'home':'dashboard','landing':'dashboard','onboarding':'dashboard',
        'my_cv':'cv_documents','improve_cv':'cv_documents','cv':'cv_documents',
        'jobs':'job_assist','job_match':'job_assist','prepare_job':'job_assist',
        'interview':'workobot','speaking_practice':'workobot',
        'bot':'workobot','work-o-bot':'workobot','work_o_bot':'workobot',
        'founder_dashboard':'dashboard','founder':'dashboard',
    }
    page_key = aliases.get(str(page_key or 'dashboard'), str(page_key or 'dashboard'))
    st.session_state['page'] = page_key
    st.session_state['nav_page'] = page_key
    st.session_state['_workzo_scroll_to_top'] = True
    try:
        nonce = int(st.session_state.get('nav_change_nonce', 0)) + 1
        st.session_state['nav_change_nonce'] = nonce
        st.query_params['page'] = page_key
        st.query_params['top'] = str(nonce)
    except Exception:
        pass
    st.rerun()

_wz27_go = _wz28_go
_wz25_go = _wz28_go
_wz24_go = _wz28_go
_wz21_go = _wz28_go
_wz19_go = _wz28_go
go_to_nav = _wz28_go


def _wz28_score(*keys, default=0):
    for k in keys:
        try:
            v = st.session_state.get(k)
            if v is not None and str(v).strip() != '':
                return max(0, min(100, int(float(v))))
        except Exception:
            pass
    return default


def _wz28_sidebar(page_key: str):
    with st.sidebar:
        try:
            logo_src = image_to_data_uri(ICON_PATH) or image_to_data_uri(LOGO_PATH)
        except Exception:
            logo_src = None
        if logo_src:
            st.markdown(f"""
            <div class='wz28-sidebar-card'>
                <img src='{logo_src}' class='wz28-sidebar-logo' alt='WorkZo AI logo'>
                <div class='wz28-sidebar-brand'>WORKZO AI</div>
                <div class='wz28-sidebar-small'>Guided career workspace</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown('### WorkZo AI')
        st.markdown('##### Navigation')
        nav = [('dashboard','Dashboard'),('cv_documents','My CV'),('job_assist','Job Match'),('workobot','Work-O-Bot')]
        for key, label in nav:
            if st.button(label + (' ✓' if page_key == key else ''), key=f'wz28_nav_{key}', use_container_width=True):
                _wz28_go(key)
        st.markdown('##### Profile')
        st.caption(f"Country: {st.session_state.get('country') or st.session_state.get('target_country') or 'Not set'}")
        st.caption('Resume uploaded' if str(st.session_state.get('cv_text','')).strip() else 'CV missing')
        st.markdown('##### Settings')
        try:
            language_list = language_options if language_options else ['English', 'German', 'Dutch']
            current = st.session_state.get('preferred_language') or st.session_state.get('language') or 'English'
            if current not in language_list:
                current = 'English' if 'English' in language_list else language_list[0]
            chosen = st.selectbox('Language', language_list, index=language_list.index(current), key='wz28_language')
            set_single_preferred_language(chosen)
            st.session_state['preferred_language'] = chosen
            st.session_state['language'] = chosen
        except Exception:
            pass
        if st.button('Edit setup', key='wz28_edit_setup', use_container_width=True):
            try:
                reset_onboarding()
            except Exception:
                st.session_state['onboarding_complete'] = False
            _wz28_go('onboarding')


def _wz28_dashboard_home():
    _wz28_css()
    cv_exists = bool(str(st.session_state.get('cv_text','')).strip() or st.session_state.get('structured_cv_json'))
    job_exists = bool(str(st.session_state.get('current_job_description','') or st.session_state.get('last_understand_job_description','') or st.session_state.get('improve_cv_for_job_desc','')).strip())
    cv_score = _wz28_score('cv_score_value','resume_score', default=75 if cv_exists else 0)
    ats_score = _wz28_score('ats_score_value','job_match_score', default=70 if job_exists else 0)
    interview_score = _wz28_score('interview_score','interview_readiness', default=40)
    name = st.session_state.get('user_name') or st.session_state.get('candidate_name') or 'there'
    st.markdown("<div class='wz28-hide-progress'>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class='wz28-hero'>
      <div class='wz28-title'>Welcome back, {html.escape(str(name))}</div>
      <div class='wz28-sub'>Let’s move you closer to your next job.</div>
    </div>
    """, unsafe_allow_html=True)
    c1,c2,c3 = st.columns(3)
    c1.metric('CV Strength', f'{cv_score}%' if cv_score else 'Not analyzed')
    c2.metric('Job Match', f'{ats_score}%' if ats_score else 'Not analyzed')
    c3.metric('Interview Readiness', f'{interview_score}%')
    st.caption('No progress bar here: use the cards below for the next best action.')
    if st.button('Continue Your Journey', key='wz28_continue', use_container_width=False):
        if not cv_exists: _wz28_go('cv_documents')
        elif not job_exists: _wz28_go('job_assist')
        elif interview_score < 70: _wz28_go('workobot')
        else: _wz28_go('job_assist')
    st.divider()
    st.subheader('What do you need today?')
    a,b,c = st.columns(3)
    with a:
        st.markdown("<div class='wz28-card'><h3>Get More Interviews</h3><p>Improve your CV for a job description, strengthen ATS alignment, and keep changes honest.</p></div>", unsafe_allow_html=True)
        if st.button('Improve My CV', key='wz28_improve', use_container_width=True):
            st.session_state['cv_documents_mode']='improve_cv'; _wz28_go('cv_documents')
    with b:
        st.markdown("<div class='wz28-card'><h3>Prepare for Interview</h3><p>Practice questions based only on your CV, job description, company context, country, and chosen language.</p></div>", unsafe_allow_html=True)
        if st.button('Start Work-O-Bot', key='wz28_interview', use_container_width=True):
            _wz28_go('workobot')
    with c:
        st.markdown("<div class='wz28-card'><h3>Find Relevant Jobs</h3><p>Analyze a job, add company website context, and reuse it for CV, cover letter, and interview preparation.</p></div>", unsafe_allow_html=True)
        if st.button('Find Jobs', key='wz28_jobs', use_container_width=True):
            _wz28_go('job_assist')
    st.divider()
    st.subheader('What WorkZo suggests for you')
    if not cv_exists:
        reco, target = 'Add or create your CV first. WorkZo needs this to personalize every feature.', 'cv_documents'
    elif not job_exists:
        reco, target = 'Paste a job description and company website so WorkZo can analyze your match.', 'job_assist'
    elif ats_score < 75:
        reco, target = 'Your job match can improve. Add only truthful keywords from the job description.', 'cv_documents'
    elif interview_score < 70:
        reco, target = 'Practice the real interview using your CV, job description, and selected language.', 'workobot'
    else:
        reco, target = 'You look ready to apply. Prepare a focused cover letter and track your application.', 'job_assist'
    st.markdown(f"<div class='wz28-reco'>{html.escape(reco)}</div>", unsafe_allow_html=True)
    if st.button('Do this next', key='wz28_next', use_container_width=True):
        _wz28_go(target)
    st.divider()
    st.subheader('Need help?')
    st.caption('Work-O-Bot is a separate typed assistant for career questions, HR messages, CV doubts, job search, and language practice.')
    if st.button('Ask Work-O-Bot', key='wz28_bot', use_container_width=False):
        _wz28_go('workobot')
    st.markdown('</div>', unsafe_allow_html=True)


def _wz28_job_assist_page():
    _wz28_css()
    st.markdown('## AI Job Application Assistant')
    st.caption('Paste a job description and company website. WorkZo reuses this context for CV improvement, cover letters, and Work-O-Bot.')
    col1, col2 = st.columns(2)
    with col1:
        company = st.text_input('Target company', value=st.session_state.get('target_company',''), key='wz28_target_company')
    with col2:
        website = st.text_input('Company website / careers page', value=st.session_state.get('target_company_website',''), key='wz28_company_website')
    st.session_state['target_company'] = company
    st.session_state['company_website'] = website
    if website:
        st.info('Company website saved. WorkZo will use it for CV advice, cover letters, and interview questions without inventing facts.')
    try:
        _wz20_render_job_assist_page()
    except Exception:
        jd = st.text_area('Paste the job description', value=st.session_state.get('current_job_description',''), height=220, key='wz28_safe_jd')
        if jd.strip():
            st.session_state['current_job_description'] = jd
            st.session_state['last_understand_job_description'] = jd
        if st.button('Use this job for CV + Work-O-Bot', key='wz28_use_job', use_container_width=True):
            _wz28_go('cv_documents')


def _wz28_workobot_page():
    _wz28_css()
    st.markdown('## Work-O-Bot')
    st.caption('Typed assistant for career questions, CV doubts, HR messages, job search, and language practice. Work-O-Bot is separate.')
    try:
        show_workobot()
    except Exception as exc:
        st.error('Work-O-Bot could not load.')
        st.exception(exc)


def show_dashboard():
    page_key = st.session_state.get('nav_page') or st.session_state.get('page') or 'dashboard'
    page_key = {'landing':'dashboard','onboarding':'dashboard','founder_dashboard':'dashboard','founder':'dashboard','bot':'workobot','interview':'workobot','jobs':'job_assist','improve_cv':'cv_documents'}.get(page_key, page_key)
    if page_key not in {'dashboard','cv_documents','job_assist','workobot','workobot'}:
        page_key = 'dashboard'
    st.session_state['page'] = page_key
    st.session_state['nav_page'] = page_key
    _wz28_top(True)
    _wz28_sidebar(page_key)
    if page_key == 'dashboard':
        _wz28_dashboard_home()
    elif page_key == 'cv_documents':
        _wz28_css(); show_document_tools()
    elif page_key == 'job_assist':
        _wz28_job_assist_page()
    elif page_key == 'workobot':
        _wz28_css()
        try:
            _wz21_render_interview_practice_page()
        except Exception:
            if 'show_interview_simulation' in globals():
                show_interview_simulation()
            else:
                st.error('Work-O-Bot could not load.')
    elif page_key == 'workobot':
        _wz28_workobot_page()
    st.caption('WORKZO AI • Beta • Guided career workspace')

# =========================================================
# WorkZo v29 - final UX cleanup: reliable top scroll, clean sidebar,
# no duplicate interview wrapper.
# =========================================================
def _wz29_force_top():
    try:
        st.markdown("<div id='workzo-page-top'></div>", unsafe_allow_html=True)
        js = """
        <script>
        function wzTop(){
          try { window.parent.scrollTo(0,0); } catch(e) {}
          try { window.parent.document.documentElement.scrollTop = 0; } catch(e) {}
          try { window.parent.document.body.scrollTop = 0; } catch(e) {}
          const sels = ['section.main','[data-testid="stAppViewContainer"]','[data-testid="stMain"]','.main','.block-container'];
          for (const s of sels) { try { const el = window.parent.document.querySelector(s); if (el) { el.scrollTop = 0; } } catch(e) {} }
        }
        wzTop(); setTimeout(wzTop, 40); setTimeout(wzTop, 160); setTimeout(wzTop, 450);
        </script>
        """
        import streamlit.components.v1 as components
        components.html(js, height=0, width=0)
    except Exception:
        pass

def _wz28_top(force: bool = True):
    _wz29_force_top()

def _wz29_clean_css():
    st.markdown("""
    <style>
      section[data-testid="stSidebar"] .block-container{padding-top:1.2rem;padding-left:1rem;padding-right:1rem;}
      .wz29-side-card{border:1px solid rgba(20,184,166,.35);border-radius:18px;padding:15px;margin:4px 0 18px;background:linear-gradient(135deg,rgba(8,47,73,.72),rgba(15,23,42,.80));}
      .wz29-side-logo{width:46px;height:46px;border-radius:12px;margin-bottom:10px;}
      .wz29-side-brand{font-size:20px;font-weight:850;letter-spacing:.03em;color:#fff;}
      .wz29-side-sub{font-size:13px;color:#94a3b8;margin-top:3px;}
      .wz29-side-label{font-size:12px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:#94a3b8;margin:16px 0 8px;}
      section[data-testid="stSidebar"] div[data-testid="stButton"] > button{min-height:42px;border-radius:12px;justify-content:flex-start;font-weight:650;}
    </style>
    """, unsafe_allow_html=True)

def _wz28_sidebar(page_key: str):
    _wz29_clean_css()
    with st.sidebar:
        try:
            logo_src = image_to_data_uri(ICON_PATH) or image_to_data_uri(LOGO_PATH)
        except Exception:
            logo_src = None
        if logo_src:
            st.markdown(f"""
            <div class='wz29-side-card'>
                <img src='{logo_src}' class='wz29-side-logo' alt='WorkZo AI logo'>
                <div class='wz29-side-brand'>WORKZO AI</div>
                <div class='wz29-side-sub'>Guided career workspace</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("### WorkZo AI")
        st.markdown("<div class='wz29-side-label'>Navigation</div>", unsafe_allow_html=True)
        nav = [('dashboard','Dashboard'),('cv_documents','My CV'),('job_assist','Job Match'),('workobot','Work-O-Bot')]
        for key, label in nav:
            if st.button(label + (' ✓' if page_key == key else ''), key=f'wz29_nav_{key}', use_container_width=True):
                _wz28_go(key)
        st.markdown("<div class='wz29-side-label'>Settings</div>", unsafe_allow_html=True)
        try:
            language_list = language_options if language_options else ['English','German','Dutch']
            current = st.session_state.get('preferred_language') or st.session_state.get('language') or 'English'
            if current not in language_list:
                current = 'English' if 'English' in language_list else language_list[0]
            chosen = st.selectbox('Language', language_list, index=language_list.index(current), key='wz29_language')
            set_single_preferred_language(chosen)
            st.session_state['preferred_language'] = chosen
            st.session_state['language'] = chosen
        except Exception:
            pass
        if st.button('Edit setup', key='wz29_edit_setup', use_container_width=True):
            try:
                reset_onboarding()
            except Exception:
                st.session_state['onboarding_complete'] = False
            _wz28_go('onboarding')

def _wz21_render_interview_practice_page():
    _wz29_force_top()
    if 'render_real_interview_simulation' in globals():
        render_real_interview_simulation()
    else:
        st.error('Work-O-Bot could not load. Please check 09_interview_assistant.py.')

# =========================================================
# WorkZo v30 - shared job/company context + cleaner centered sidebar
# =========================================================
def _wz30_get_job_context() -> dict:
    return {
        'company': st.session_state.get('target_company') or st.session_state.get('real_interview_company') or st.session_state.get('prepare_target_company') or '',
        'role': st.session_state.get('target_role') or st.session_state.get('target_job_title') or st.session_state.get('prepare_target_role') or '',
        'website': st.session_state.get('target_company_website') or '',
        'job_description': st.session_state.get('current_job_description') or st.session_state.get('last_understand_job_description') or st.session_state.get('job_description') or st.session_state.get('improve_cv_for_job_desc') or '',
    }

def _wz30_set_job_context(company='', role='', website='', job_description='') -> None:
    st.session_state['target_company'] = str(company or '').strip()
    st.session_state['real_interview_company'] = str(company or '').strip()
    st.session_state['prepare_target_company'] = str(company or '').strip()
    st.session_state['target_role'] = str(role or '').strip()
    st.session_state['target_job_title'] = str(role or '').strip()
    st.session_state['prepare_target_role'] = str(role or '').strip()
    st.session_state['company_website'] = str(website or '').strip()
    jd = str(job_description or '').strip()
    st.session_state['current_job_description'] = jd
    st.session_state['last_understand_job_description'] = jd
    st.session_state['job_description'] = jd
    st.session_state['improve_cv_for_job_desc'] = jd
    st.session_state['last_prepare_job_description'] = jd

def _wz30_saved_application_contexts() -> list:
    apps = st.session_state.get('saved_application_contexts')
    return apps if isinstance(apps, list) else []

def _wz30_save_application_context(company, role, website, jd) -> None:
    company = str(company or '').strip(); role = str(role or '').strip(); website = str(website or '').strip(); jd = str(jd or '').strip()
    if not any([company, role, website, jd]):
        return
    label = ' — '.join([x for x in [company or 'Company not specified', role or 'Role not specified'] if x])
    item = {'label': label, 'company': company, 'role': role, 'website': website, 'job_description': jd}
    apps = [a for a in _wz30_saved_application_contexts() if not (a.get('company') == company and a.get('role') == role and a.get('website') == website)]
    apps.insert(0, item)
    st.session_state['saved_application_contexts'] = apps[:12]

def _wz30_context_manager(prefix='wz30') -> dict:
    ctx = _wz30_get_job_context()
    saved = _wz30_saved_application_contexts()
    if saved:
        labels = ['Use current / new company'] + [a.get('label', 'Saved company') for a in saved]
        choice = st.selectbox('Saved company/job details', labels, key=f'{prefix}_saved_choice')
        if choice != labels[0]:
            item = saved[labels.index(choice)-1]
            _wz30_set_job_context(item.get('company',''), item.get('role',''), item.get('website',''), item.get('job_description',''))
            ctx = _wz30_get_job_context()
            st.info('Loaded saved company/job details. You can edit them below.')
    c1, c2 = st.columns(2)
    with c1:
        company = st.text_input('Target company', value=ctx.get('company',''), key=f'{prefix}_company')
    with c2:
        role = st.text_input('Target role', value=ctx.get('role',''), key=f'{prefix}_role')
    website = st.text_input('Company website / careers page', value=ctx.get('website',''), key=f'{prefix}_website', help='Paste once. WorkZo reuses it for CV, cover letter, job match, and Work-O-Bot.')
    jd = st.text_area('Paste the job description', value=ctx.get('job_description',''), height=210, key=f'{prefix}_jd')
    _wz30_set_job_context(company, role, website, jd)
    c3, c4 = st.columns(2)
    with c3:
        if st.button('Save this company/job', key=f'{prefix}_save', use_container_width=True):
            _wz30_save_application_context(company, role, website, jd)
            st.success('Saved. You can load it later when applying to multiple companies.')
    with c4:
        if st.button('Start new company', key=f'{prefix}_new', use_container_width=True):
            _wz30_set_job_context('', '', '', '')
            for k in [f'{prefix}_company', f'{prefix}_role', f'{prefix}_website', f'{prefix}_jd']:
                st.session_state[k] = ''
            st.rerun()
    return _wz30_get_job_context()

def _wz29_clean_css():
    st.markdown("""
    <style>
      section[data-testid="stSidebar"] .block-container{padding-top:1.2rem;padding-left:1rem;padding-right:1rem;}
      .wz29-side-card{border:1px solid rgba(20,184,166,.35);border-radius:18px;padding:15px;margin:4px 0 18px;background:linear-gradient(135deg,rgba(8,47,73,.72),rgba(15,23,42,.80));}
      .wz29-side-logo{width:46px;height:46px;border-radius:12px;margin-bottom:10px;}
      .wz29-side-brand{font-size:20px;font-weight:850;letter-spacing:.03em;color:#fff;}
      .wz29-side-sub{font-size:13px;color:#94a3b8;margin-top:3px;}
      .wz29-side-label{font-size:12px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:#94a3b8;margin:18px 0 8px;text-align:left;}
      section[data-testid="stSidebar"] div[data-testid="stButton"]{display:flex;justify-content:center;}
      section[data-testid="stSidebar"] div[data-testid="stButton"] > button{width:200px !important;min-width:200px !important;max-width:200px !important;min-height:42px;border-radius:12px;justify-content:center;text-align:center;font-weight:650;margin:4px auto;}
    </style>
    """, unsafe_allow_html=True)

def _wz28_sidebar(page_key: str):
    _wz29_clean_css()
    with st.sidebar:
        try:
            logo_src = image_to_data_uri(ICON_PATH) or image_to_data_uri(LOGO_PATH)
        except Exception:
            logo_src = None
        if logo_src:
            st.markdown(f"""
            <div class='wz29-side-card'>
                <img src='{logo_src}' class='wz29-side-logo' alt='WorkZo AI logo'>
                <div class='wz29-side-brand'>WORKZO AI</div>
                <div class='wz29-side-sub'>Guided career workspace</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown('### WorkZo AI')
        st.markdown("<div class='wz29-side-label'>Navigation</div>", unsafe_allow_html=True)
        nav = [('dashboard','Dashboard'),('cv_documents','My CV'),('job_assist','Job Match'),('workobot','Work-O-Bot')]
        for key, label in nav:
            if st.button(label + (' ✓' if page_key == key else ''), key=f'wz30_nav_{key}', use_container_width=False):
                _wz28_go(key)
        st.markdown("<div class='wz29-side-label'>Settings</div>", unsafe_allow_html=True)
        try:
            language_list = language_options if language_options else ['English','German','Dutch']
            current = st.session_state.get('preferred_language') or st.session_state.get('language') or 'English'
            if current not in language_list:
                current = 'English' if 'English' in language_list else language_list[0]
            chosen = st.selectbox('Language', language_list, index=language_list.index(current), key='wz30_language')
            set_single_preferred_language(chosen)
            st.session_state['preferred_language'] = chosen
            st.session_state['language'] = chosen
        except Exception:
            pass
        if st.button('Edit setup', key='wz30_edit_setup', use_container_width=False):
            try:
                reset_onboarding()
            except Exception:
                st.session_state['onboarding_complete'] = False
            _wz28_go('onboarding')

def _wz28_job_assist_page():
    _wz28_css()
    st.markdown('## AI Job Application Assistant')
    st.caption('Add company, role, website, and job description once. WorkZo reuses this context across CV improvement, cover letter, Job Match, and Work-O-Bot.')
    ctx = _wz30_context_manager('wz30_job')
    if ctx.get('website'):
        st.info('Company website saved. WorkZo will use it without inventing company facts.')
    try:
        _wz20_render_job_assist_page()
    except Exception:
        st.warning('Using simplified Job Match view.')
        if st.button('Use this job for CV + Work-O-Bot', key='wz30_use_job', use_container_width=True):
            _wz28_go('cv_documents')


# =========================================================
# WorkZo v31 - Smart Command Center dashboard
# - Separate Resume Score, ATS Score, Job Fit, Interview Readiness
# - Visual rate cards
# - Smart next action based on score/state
# - No confusing generic "Job Match 90%" without a job description
# =========================================================
def _wz31_clamp_score(value, default=0):
    try:
        if value is None or str(value).strip() == "":
            return int(default)
        return max(0, min(100, int(float(value))))
    except Exception:
        return int(default or 0)


def _wz31_get_score(*keys, default=0):
    for key in keys:
        try:
            value = st.session_state.get(key)
            if value is not None and str(value).strip() != "":
                return _wz31_clamp_score(value, default)
        except Exception:
            pass
    return _wz31_clamp_score(default, 0)


def _wz31_score_label(score):
    score = _wz31_clamp_score(score)
    if score >= 85:
        return "Excellent"
    if score >= 75:
        return "Good"
    if score >= 60:
        return "Needs improvement"
    if score > 0:
        return "Weak"
    return "Not analyzed"


def _wz31_escape(value):
    try:
        return html.escape(str(value or ""))
    except Exception:
        return str(value or "")


def _wz31_css():
    st.markdown("""
    <style>
      .wz31-hero{
        border:1px solid rgba(20,184,166,.30);
        border-radius:28px;
        padding:30px 34px;
        margin:8px 0 24px 0;
        background:radial-gradient(circle at top left,rgba(20,184,166,.20),transparent 35%),linear-gradient(135deg,rgba(30,64,175,.28),rgba(8,47,73,.24));
        box-shadow:0 18px 50px rgba(2,6,23,.28);
      }
      .wz31-kicker{color:#93c5fd;font-size:.78rem;font-weight:850;letter-spacing:.12em;text-transform:uppercase;margin-bottom:8px;}
      .wz31-title{color:#fff;font-size:2rem;font-weight:900;line-height:1.12;margin-bottom:8px;}
      .wz31-sub{color:#dbeafe;font-size:1.02rem;line-height:1.5;max-width:900px;}
      .wz31-chip-row{display:flex;gap:8px;flex-wrap:wrap;margin-top:16px;}
      .wz31-chip{border:1px solid rgba(96,165,250,.28);background:rgba(37,99,235,.18);border-radius:999px;color:#dbeafe;font-size:.84rem;font-weight:700;padding:7px 11px;}
      .wz31-next{
        border:1px solid rgba(45,212,191,.32);
        border-radius:22px;
        padding:20px 22px;
        background:linear-gradient(135deg,rgba(20,184,166,.18),rgba(37,99,235,.14));
        margin:12px 0 22px 0;
      }
      .wz31-next-label{color:#99f6e4;font-size:.78rem;font-weight:900;letter-spacing:.1em;text-transform:uppercase;margin-bottom:6px;}
      .wz31-next-title{color:#fff;font-size:1.25rem;font-weight:900;margin-bottom:5px;}
      .wz31-next-copy{color:#cbd5e1;font-size:.95rem;line-height:1.5;}
      .wz31-rate-card{
        border:1px solid rgba(148,163,184,.18);
        border-radius:22px;
        padding:18px 18px 16px 18px;
        background:linear-gradient(180deg,rgba(30,41,59,.82),rgba(15,23,42,.72));
        min-height:168px;
        box-shadow:0 12px 30px rgba(2,6,23,.18);
        margin-bottom:14px;
      }
      .wz31-rate-head{display:flex;justify-content:space-between;align-items:flex-start;gap:10px;margin-bottom:10px;}
      .wz31-rate-title{color:#e2e8f0;font-size:.95rem;font-weight:850;line-height:1.25;}
      .wz31-rate-badge{border:1px solid rgba(148,163,184,.25);border-radius:999px;padding:4px 8px;color:#cbd5e1;font-size:.72rem;font-weight:800;white-space:nowrap;}
      .wz31-score{color:#fff;font-size:2.15rem;font-weight:950;line-height:1;margin:8px 0 10px;}
      .wz31-bar-bg{height:10px;border-radius:999px;background:rgba(148,163,184,.20);overflow:hidden;margin:7px 0 9px;}
      .wz31-bar-fill{height:10px;border-radius:999px;background:linear-gradient(90deg,#38bdf8,#2dd4bf);}
      .wz31-rate-copy{color:#94a3b8;font-size:.84rem;line-height:1.45;margin-top:8px;}
      .wz31-actions{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px;margin:14px 0 22px;}
      .wz31-action-card{border:1px solid rgba(148,163,184,.16);border-radius:22px;padding:18px;background:rgba(15,23,42,.56);min-height:148px;}
      .wz31-action-title{color:#fff;font-size:1.05rem;font-weight:900;margin-bottom:8px;}
      .wz31-action-copy{color:#aebbd0;font-size:.9rem;line-height:1.45;}
      .wz31-flow{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px;margin-top:10px;}
      .wz31-step{border:1px solid rgba(148,163,184,.16);border-radius:18px;padding:13px 14px;background:rgba(15,23,42,.46);}
      .wz31-step.done{border-color:rgba(45,212,191,.42);background:rgba(20,184,166,.12);}
      .wz31-step-title{color:#fff;font-weight:850;font-size:.92rem;}
      .wz31-step-sub{color:#94a3b8;font-size:.78rem;margin-top:3px;}
    </style>
    """, unsafe_allow_html=True)


def _wz31_rate_card(title, score, subtitle, *, missing=False):
    score = _wz31_clamp_score(score)
    label = "Add details" if missing else _wz31_score_label(score)
    shown = "—" if missing or score <= 0 else f"{score}%"
    fill = 0 if missing else score
    st.markdown(f"""
    <div class='wz31-rate-card'>
      <div class='wz31-rate-head'>
        <div class='wz31-rate-title'>{_wz31_escape(title)}</div>
        <div class='wz31-rate-badge'>{_wz31_escape(label)}</div>
      </div>
      <div class='wz31-score'>{_wz31_escape(shown)}</div>
      <div class='wz31-bar-bg'><div class='wz31-bar-fill' style='width:{fill}%;'></div></div>
      <div class='wz31-rate-copy'>{_wz31_escape(subtitle)}</div>
    </div>
    """, unsafe_allow_html=True)


def _wz31_pick_next_action(cv_exists, job_exists, resume_score, ats_score, job_fit_score, interview_score):
    if not cv_exists:
        return {
            "title": "Add your CV first",
            "copy": "WorkZo needs your CV to score it, suggest matching roles, and personalize every next step.",
            "button": "Add / Create CV",
            "target": "cv_documents",
        }
    if resume_score < 75 or ats_score < 75:
        return {
            "title": "Improve your CV before applying",
            "copy": "Your resume or ATS score still needs work. Fix structure, keywords, and clarity before spending time on applications.",
            "button": "Improve CV",
            "target": "cv_documents",
        }
    if not job_exists:
        return {
            "title": "Find or paste a real job next",
            "copy": "Your CV looks ready. Now choose a real job description so WorkZo can check job fit and tailor your application.",
            "button": "Find / Analyze Jobs",
            "target": "job_assist",
        }
    if job_fit_score and job_fit_score < 70:
        return {
            "title": "Tailor CV to this job first",
            "copy": "The current job fit is not strong enough yet. Add only truthful job-relevant keywords and stronger matching bullets.",
            "button": "Tailor CV for Job",
            "target": "cv_documents",
        }
    if interview_score < 75:
        return {
            "title": "Practice for the interview",
            "copy": "Your CV and ATS look good. Use Work-O-Bot to practice job-specific answers based on your CV, job description, company, and language.",
            "button": "Practice with Work-O-Bot",
            "target": "workobot",
        }
    return {
        "title": "Ready to apply",
        "copy": "Your scores look strong. Generate a focused cover letter, save this application, and apply.",
        "button": "Prepare Application",
        "target": "job_assist",
    }


def _wz31_action_card(title, copy, button, target, key, extra_state=None):
    st.markdown(f"""
    <div class='wz31-action-card'>
      <div class='wz31-action-title'>{_wz31_escape(title)}</div>
      <div class='wz31-action-copy'>{_wz31_escape(copy)}</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button(button, key=key, use_container_width=True):
        if isinstance(extra_state, dict):
            for k, v in extra_state.items():
                st.session_state[k] = v
        _wz28_go(target)


def _wz28_dashboard_home():
    _wz28_css()
    _wz31_css()
    cv_exists = bool(str(st.session_state.get('cv_text','')).strip() or st.session_state.get('structured_cv_json'))
    job_text = str(st.session_state.get('current_job_description','') or st.session_state.get('last_understand_job_description','') or st.session_state.get('improve_cv_for_job_desc','') or st.session_state.get('job_description','')).strip()
    job_exists = bool(job_text)
    company = str(st.session_state.get('target_company') or st.session_state.get('prepare_target_company') or '').strip()
    country = str(st.session_state.get('country') or st.session_state.get('target_country') or 'Not set')
    language = str(st.session_state.get('preferred_language') or st.session_state.get('language') or 'English')
    role = str(st.session_state.get('target_role') or st.session_state.get('target_job_title') or st.session_state.get('detected_target_role') or 'Target role not set')

    resume_score = _wz31_get_score('cv_score_value', 'resume_score', 'resume_quality_score', default=75 if cv_exists else 0)
    ats_score = _wz31_get_score('ats_score_value', 'ats_score', default=70 if cv_exists else 0)
    job_fit_score = _wz31_get_score('job_fit_score_value', 'job_match_score', 'latest_job_fit_score', default=0)
    if job_exists and job_fit_score <= 0:
        job_fit_score = _wz31_get_score('ats_score_value', default=60)
    interview_score = _wz31_get_score('interview_score', 'interview_readiness', default=0)
    if interview_score <= 0:
        if cv_exists and job_exists and resume_score >= 75 and ats_score >= 75:
            interview_score = 65
        elif cv_exists:
            interview_score = 45
        else:
            interview_score = 20

    next_action = _wz31_pick_next_action(cv_exists, job_exists, resume_score, ats_score, job_fit_score, interview_score)

    st.markdown(f"""
    <div class='wz31-hero'>
      <div class='wz31-kicker'>WorkZo Command Center</div>
      <div class='wz31-title'>Your next best move is clear.</div>
      <div class='wz31-sub'>WorkZo reads your CV, country, language, job description, and company context, then recommends what to do next instead of showing every feature at once.</div>
      <div class='wz31-chip-row'>
        <span class='wz31-chip'>{_wz31_escape(country)}</span>
        <span class='wz31-chip'>{_wz31_escape(language)}</span>
        <span class='wz31-chip'>{'CV ready' if cv_exists else 'CV missing'}</span>
        <span class='wz31-chip'>{'Job added' if job_exists else 'Job not added'}</span>
        <span class='wz31-chip'>{_wz31_escape(company or 'Company not added')}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class='wz31-next'>
      <div class='wz31-next-label'>Recommended next step</div>
      <div class='wz31-next-title'>{_wz31_escape(next_action['title'])}</div>
      <div class='wz31-next-copy'>{_wz31_escape(next_action['copy'])}</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button(next_action['button'], key='wz31_primary_next_action', use_container_width=True):
        if next_action['target'] == 'cv_documents' and job_exists:
            st.session_state['document_tools_mode'] = 'Improve CV for a Job'
        _wz28_go(next_action['target'])

    st.markdown('### Readiness overview')
    r1, r2, r3, r4 = st.columns(4)
    with r1:
        _wz31_rate_card('Resume Score', resume_score, 'Clarity, structure, achievements, and overall CV quality.', missing=not cv_exists)
    with r2:
        _wz31_rate_card('ATS Score', ats_score, 'Scanner-friendly formatting, keywords, sections, and parsing safety.', missing=not cv_exists)
    with r3:
        _wz31_rate_card('Job Fit', job_fit_score, 'Fit for the current pasted job description. Add a job before trusting this score.', missing=not job_exists)
    with r4:
        _wz31_rate_card('Interview Readiness', interview_score, 'How ready you are to explain this CV and job fit clearly.', missing=not cv_exists)

    st.markdown('### Smart actions')
    a1, a2, a3, a4 = st.columns(4)
    with a1:
        _wz31_action_card('Improve CV', 'Use this when Resume or ATS score is below 75, or when you want to tailor for one job.', 'Open CV Tools', 'cv_documents', 'wz31_open_cv', {'document_tools_mode':'Improve CV for a Job' if job_exists else 'Improve / Update CV'})
    with a2:
        _wz31_action_card('Find / Analyze Jobs', 'Use this when your CV score is good and you need real jobs or a job-fit check.', 'Open Job Assist', 'job_assist', 'wz31_open_jobs')
    with a3:
        _wz31_action_card('Cover Letter', 'Use company, job description, and CV context to write a focused cover letter.', 'Create Cover Letter', 'cv_documents', 'wz31_open_cover', {'document_tools_mode':'Cover Letter Generator + Language'})
    with a4:
        _wz31_action_card('Work-O-Bot', 'Ask career questions or practice interview answers in your selected language.', 'Ask Work-O-Bot', 'workobot', 'wz31_open_bot')

    st.markdown('### Application flow')
    improved_ready = bool(str(st.session_state.get('improved_cv_text','') or st.session_state.get('latest_improved_cv','') or st.session_state.get('final_cv_text','')).strip())
    cover_ready = bool(str(st.session_state.get('latest_cover_letter','') or st.session_state.get('cover_letter_text','')).strip())
    flow = [
        ('1. CV added', cv_exists),
        ('2. Resume + ATS checked', bool(cv_exists and resume_score > 0 and ats_score > 0)),
        ('3. Job added', job_exists),
        ('4. CV tailored', improved_ready or (job_exists and resume_score >= 75 and ats_score >= 75)),
        ('5. Cover letter / prep', cover_ready),
    ]
    html_steps = []
    for label, done in flow:
        html_steps.append(f"<div class='wz31-step {'done' if done else ''}'><div class='wz31-step-title'>{'✅ ' if done else '○ '}{_wz31_escape(label)}</div><div class='wz31-step-sub'>{'Complete' if done else 'Next step pending'}</div></div>")
    st.markdown("<div class='wz31-flow'>" + "".join(html_steps) + "</div>", unsafe_allow_html=True)

    st.caption('Scores are guidance only. WorkZo should not invent skills, company facts, language level, salary, or experience.')

# =========================================================
# WorkZo v32 - smarter dashboard, score memory, no dashboard job-fit card
# =========================================================
def _wz32_force_scroll_top():
    try:
        st.markdown('<span id="workzo-page-top"></span>', unsafe_allow_html=True)
        script = """
        <script>
        const scrollTop = () => {
          try { window.parent.scrollTo(0,0); } catch(e) {}
          try { window.scrollTo(0,0); } catch(e) {}
          try {
            const doc = window.parent.document;
            const candidates = [
              doc.querySelector('section.main'),
              doc.querySelector('div[data-testid="stAppViewContainer"]'),
              doc.querySelector('.main'),
              doc.scrollingElement,
              doc.documentElement,
              doc.body
            ].filter(Boolean);
            candidates.forEach(el => { try { el.scrollTop = 0; } catch(e) {} });
          } catch(e) {}
        };
        scrollTop(); setTimeout(scrollTop, 80); setTimeout(scrollTop, 250);
        </script>
        """
        if hasattr(st, 'iframe'):
            st.iframe(srcdoc=script, height=1, width=1)
        else:
            st.markdown(script, unsafe_allow_html=True)
    except Exception:
        pass

def _wz32_remember_best_scores():
    try:
        for key in ['cv_score_value', 'ats_score_value', 'application_readiness_value', 'job_fit_score_value', 'interview_score']:
            cur = st.session_state.get(key)
            if cur is None or str(cur).strip() == '':
                continue
            try:
                cur_i = max(0, min(100, int(float(cur))))
            except Exception:
                continue
            best_key = '_best_' + key
            best_i = int(st.session_state.get(best_key) or 0)
            if cur_i > best_i:
                st.session_state[best_key] = cur_i
    except Exception:
        pass

def _wz32_restore_best_scores():
    try:
        for key in ['cv_score_value', 'ats_score_value', 'application_readiness_value', 'job_fit_score_value', 'interview_score']:
            best_key = '_best_' + key
            best = int(st.session_state.get(best_key) or 0)
            cur = st.session_state.get(key)
            try:
                cur_i = int(float(cur or 0))
            except Exception:
                cur_i = 0
            if best > 0 and cur_i <= 0:
                st.session_state[key] = best
            elif cur_i > best:
                st.session_state[best_key] = cur_i
    except Exception:
        pass

def _wz32_flow_step(label, done, current=False, note=''):
    # Keep this HTML on one line. Leading spaces/newlines can make Streamlit
    # render later cards as a code block instead of HTML.
    cls = 'done' if done else ('current' if current else '')
    icon = '✅' if done else ('➜' if current else '○')
    state = 'Complete' if done else ('Recommended now' if current else 'Pending')
    style = 'border-color:rgba(96,165,250,.55);background:rgba(37,99,235,.14);' if current and not done else ''
    return f"<div class='wz31-step {cls}' style='{style}'><div class='wz31-step-title'>{icon} {_wz31_escape(label)}</div><div class='wz31-step-sub'>{_wz31_escape(note or state)}</div></div>"

def _wz32_pick_current_step(cv_exists, resume_score, ats_score, job_exists, improved_ready, cover_ready):
    if not cv_exists:
        return 0
    if resume_score < 75 or ats_score < 75:
        return 1
    if not job_exists:
        return 2
    if not improved_ready:
        return 3
    if not cover_ready:
        return 4
    return 5

def _wz32_dashboard_home():
    _wz32_restore_best_scores()
    _wz32_force_scroll_top()
    _wz28_css()
    _wz31_css()
    st.markdown("""
    <style>
      .workzo-header{margin-bottom:14px!important;}
      .wz31-hero{margin-top:0!important;margin-bottom:18px!important;}
      .wz31-flow{grid-template-columns:repeat(auto-fit,minmax(185px,1fr));}
      .wz31-step{min-height:86px;}
      .wz32-explain{color:#94a3b8;font-size:.9rem;margin:-4px 0 14px;}
    </style>
    """, unsafe_allow_html=True)

    cv_exists = bool(str(st.session_state.get('cv_text','')).strip() or st.session_state.get('structured_cv_json'))
    job_text = str(st.session_state.get('current_job_description','') or st.session_state.get('last_understand_job_description','') or st.session_state.get('improve_cv_for_job_desc','') or st.session_state.get('job_description','')).strip()
    job_exists = bool(job_text)
    company = str(st.session_state.get('target_company') or st.session_state.get('prepare_target_company') or '').strip()
    country = str(st.session_state.get('country') or st.session_state.get('target_country') or 'Not set')
    language = str(st.session_state.get('preferred_language') or st.session_state.get('language') or 'English')

    resume_score = _wz31_get_score('cv_score_value', 'resume_score', 'resume_quality_score', '_best_cv_score_value', default=0)
    ats_score = _wz31_get_score('ats_score_value', 'ats_score', '_best_ats_score_value', default=0)
    if cv_exists and resume_score <= 0:
        resume_score = int(st.session_state.get('_best_cv_score_value') or 75)
    if cv_exists and ats_score <= 0:
        ats_score = int(st.session_state.get('_best_ats_score_value') or 70)
    interview_score = _wz31_get_score('interview_score', 'interview_readiness', '_best_interview_score', default=0)
    if interview_score <= 0:
        if cv_exists and job_exists and resume_score >= 75 and ats_score >= 75:
            interview_score = 65
        elif cv_exists:
            interview_score = 45
        else:
            interview_score = 0

    improved_ready = bool(str(st.session_state.get('improved_cv_text','') or st.session_state.get('latest_improved_cv','') or st.session_state.get('final_cv_text','')).strip())
    cover_ready = bool(str(st.session_state.get('latest_cover_letter','') or st.session_state.get('cover_letter_text','')).strip())
    next_action = _wz31_pick_next_action(cv_exists, job_exists, resume_score, ats_score, _wz31_get_score('job_fit_score_value','_best_job_fit_score_value', default=0), interview_score)

    st.markdown(f"""
    <div class='wz31-hero'>
      <div class='wz31-kicker'>WorkZo Command Center</div>
      <div class='wz31-title'>Your next best move is clear.</div>
      <div class='wz31-sub'>WorkZo recommends the next step based on your CV strength, ATS readiness, job context, and application progress.</div>
      <div class='wz31-chip-row'>
        <span class='wz31-chip'>{_wz31_escape(country)}</span>
        <span class='wz31-chip'>{_wz31_escape(language)}</span>
        <span class='wz31-chip'>{'CV ready' if cv_exists else 'CV missing'}</span>
        <span class='wz31-chip'>{'Job added' if job_exists else 'Job not added'}</span>
        <span class='wz31-chip'>{_wz31_escape(company or 'Company not added')}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class='wz31-next'>
      <div class='wz31-next-label'>Recommended next step</div>
      <div class='wz31-next-title'>{_wz31_escape(next_action['title'])}</div>
      <div class='wz31-next-copy'>{_wz31_escape(next_action['copy'])}</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button(next_action['button'], key='wz32_primary_next_action', use_container_width=True):
        if next_action['target'] == 'cv_documents' and job_exists:
            st.session_state['document_tools_mode'] = 'Improve CV for a Job'
        _wz28_go(next_action['target'])

    st.markdown('### Readiness overview')
    st.markdown("<div class='wz32-explain'>Job Fit is now shown inside Understand Job after a job description is analyzed.</div>", unsafe_allow_html=True)
    r1, r2, r3 = st.columns(3)
    with r1:
        _wz31_rate_card('Resume Score', resume_score, 'Clarity, structure, achievements, and overall CV quality.', missing=not cv_exists)
    with r2:
        _wz31_rate_card('ATS Score', ats_score, 'Scanner-friendly formatting, keywords, sections, and parsing safety.', missing=not cv_exists)
    with r3:
        _wz31_rate_card('Interview Readiness', interview_score, 'How ready you are to explain this CV and job fit clearly.', missing=not cv_exists)

    st.markdown('### Smart actions')
    a1, a2, a3, a4 = st.columns(4)
    with a1:
        _wz31_action_card('Improve CV', 'Use this when Resume or ATS score is below 75, or when you want to tailor for one job.', 'Open CV Tools', 'cv_documents', 'wz32_open_cv', {'document_tools_mode':'Improve CV for a Job' if job_exists else 'Improve / Update CV'})
    with a2:
        _wz31_action_card('Job Match', 'Find jobs or analyze a pasted job description when your CV and ATS scores are ready.', 'Open Job Match', 'job_assist', 'wz32_open_jobs')
    with a3:
        _wz31_action_card('Cover Letter', 'Use company, job description, and CV context to write a focused cover letter.', 'Create Cover Letter', 'cv_documents', 'wz32_open_cover', {'document_tools_mode':'Cover Letter Generator + Language'})
    with a4:
        _wz31_action_card('Work-O-Bot', 'Ask career questions or practice interview answers in your selected language.', 'Ask Work-O-Bot', 'workobot', 'wz32_open_bot')

    # Persist only safe progress flags. Do not store CV text or job descriptions.
    if cv_exists:
        st.session_state['_wz_has_cv'] = True
    if improved_ready:
        st.session_state['_wz_cv_improved'] = True
    if bool(st.session_state.get('latest_curated_jobs') or st.session_state.get('latest_job_query_expansion')):
        st.session_state['_wz_job_found'] = True
    if job_exists or st.session_state.get('latest_job_analysis'):
        st.session_state['_wz_job_analyzed'] = True
    prepared_ready = bool(cover_ready or str(st.session_state.get('latest_application_prep','') or st.session_state.get('latest_cover_letter','')).strip())
    if prepared_ready:
        st.session_state['_wz_prepared'] = True

    # Use restored memory after refresh, but never invent private CV/job text.
    cv_done = bool(cv_exists or st.session_state.get('_wz_has_cv'))
    improved_done = bool(improved_ready or st.session_state.get('_wz_cv_improved'))
    job_done = bool(job_exists or st.session_state.get('_wz_job_found') or st.session_state.get('_wz_job_analyzed'))
    prep_done = bool(prepared_ready or st.session_state.get('_wz_prepared'))

    st.markdown('### Application progress')
    st.caption('Move step by step. Each card is checked only after that action is actually done.')

    # Current recommendation: the first unfinished step becomes highlighted.
    if not cv_done:
        current_key = 'cv'
    elif resume_score < 75 or ats_score < 75 or not improved_done:
        current_key = 'improve'
    elif not job_done:
        current_key = 'job'
    elif not prep_done:
        current_key = 'prepare'
    else:
        current_key = 'done'

    progress_items = [
        ('cv', '1. CV uploaded', cv_done, 'CV added' if cv_done else 'Upload or create your CV', 'Edit onboarding', 'onboarding', {}),
        ('improve', '2. CV improved', improved_done, 'Improved / tailored' if improved_done else 'Improve Resume + ATS score', 'Improve CV', 'cv_documents', {'document_tools_mode':'Improve / Update CV'}),
        ('job', '3. Job matched', job_done, 'Job found or analyzed' if job_done else 'Find jobs or analyze one JD', 'Job Match', 'job_assist', {'job_assist_mode_key':'find'}),
        ('prepare', '4. Prepared for job', prep_done, 'Cover letter / prep done' if prep_done else 'Prepare cover letter and interview notes', 'Prepare', 'job_assist', {'job_assist_mode_key':'prepare'}),
    ]

    cols = st.columns(4)
    for idx, (step_key, label, done, note, button_label, target, extra_state) in enumerate(progress_items):
        with cols[idx]:
            st.markdown(_wz32_flow_step(label, done, current_key == step_key, note), unsafe_allow_html=True)
    try:
        readiness = int(round((sum([cv_done, improved_done, job_done, prep_done]) / 4) * 100))
        st.session_state['application_readiness_value'] = max(int(st.session_state.get('application_readiness_value') or 0), readiness)
    except Exception:
        pass

    st.caption('Scores are guidance only. WorkZo should not invent skills, company facts, language level, salary, or experience.')
    _wz32_remember_best_scores()
    try:
        if callable(globals().get('workzo_save_light_memory')):
            workzo_save_light_memory()
    except Exception:
        pass

# Replace dashboard home with v32 smart version.
_wz28_dashboard_home = _wz32_dashboard_home

# Put Job Fit where it belongs: inside Understand Job analysis.
try:
    _wz32_old_render_understand_job_analysis = render_understand_job_analysis
    def render_understand_job_analysis(data):
        try:
            score = 0
            if isinstance(data, dict):
                score = _wz31_clamp_score(data.get('fit_score') or data.get('job_fit') or data.get('match_score') or 0)
                if score:
                    st.session_state['job_fit_score_value'] = score
                    _wz32_remember_best_scores()
            if score:
                st.markdown('### Job Fit')
                _wz31_rate_card('Job Fit', score, 'Fit for this specific pasted job description. Use this only after reviewing the requirement checklist.', missing=False)
        except Exception:
            pass
        return _wz32_old_render_understand_job_analysis(data)
except Exception:
    pass

# Keep scores alive when returning home or switching pages.
try:
    _wz32_old_show_dashboard = show_dashboard
    def show_dashboard():
        _wz32_restore_best_scores()
        try:
            _wz32_force_scroll_top()
        except Exception:
            pass
        result = _wz32_old_show_dashboard()
        _wz32_remember_best_scores()
        _wz32_restore_best_scores()
        return result
except Exception:
    pass


# =========================================================
# WorkZo v35 - stable startup command center
# Fixes: clean application progress, smaller header gap, score memory,
# edit setup routing, language sync, and old Job Assist layout routing.
# =========================================================
import json as _wz35_json
import os as _wz35_os
import time as _wz35_time
import html as _wz35_html


def _wz35_escape(value):
    try:
        return _wz35_html.escape(str(value or ""))
    except Exception:
        return str(value or "")


def _wz35_qp_get(key, default=""):
    try:
        v = st.query_params.get(key, default)
        if isinstance(v, list):
            return v[0] if v else default
        return v or default
    except Exception:
        return default


def _wz35_get_uid():
    """Persistent-enough anonymous browser id using URL query params.
    This is used only for non-sensitive UI state such as scores/language.
    """
    try:
        uid = _wz35_qp_get("wz_uid", "") or st.session_state.get("anonymous_user_id", "")
        if not uid:
            import uuid as _uuid
            uid = str(_uuid.uuid4())
        st.session_state["anonymous_user_id"] = uid
        try:
            if not _wz35_qp_get("wz_uid", ""):
                st.query_params["wz_uid"] = uid
        except Exception:
            pass
        return uid
    except Exception:
        return "local"


def _wz35_state_file():
    try:
        base = globals().get("BASE_DIR") or _wz35_os.getcwd()
        safe_uid = "".join(ch for ch in str(_wz35_get_uid()) if ch.isalnum() or ch in "-_")[:80]
        return _wz35_os.path.join(base, f"workzo_ui_state_{safe_uid}.json")
    except Exception:
        return "workzo_ui_state_local.json"


def _wz35_save_state():
    """Save non-sensitive state only. Do not store full CV text or documents."""
    try:
        keys = [
            "cv_score_value", "ats_score_value", "application_readiness_value",
            "job_fit_score_value", "interview_score", "country", "preferred_language",
            "ui_language", "response_language", "language", "target_company_website",
            "target_company", "prepare_target_company", "nav_page", "page",
            "last_understand_job_description", "current_job_description", "job_description",
            "improved_cv_text", "latest_improved_cv", "latest_cover_letter", "latest_application_prep",
            "_workzo_has_cv", "_best_cv_score_value", "_best_ats_score_value", "_best_application_readiness_value",
        ]
        data = {}
        for k in keys:
            v = st.session_state.get(k)
            if isinstance(v, (str, int, float, bool)) or v is None:
                # keep job description short enough for context, not full private docs
                if k in ["last_understand_job_description", "current_job_description", "job_description"] and isinstance(v, str):
                    v = v[:5000]
                data[k] = v
        cv_present = bool(str(st.session_state.get("cv_text", "")).strip() or st.session_state.get("structured_cv_json"))
        data["_workzo_has_cv"] = bool(cv_present or st.session_state.get("_workzo_has_cv"))
        with open(_wz35_state_file(), "w", encoding="utf-8") as f:
            _wz35_json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _wz35_load_state():
    try:
        path = _wz35_state_file()
        if not _wz35_os.path.exists(path):
            return
        with open(path, "r", encoding="utf-8") as f:
            data = _wz35_json.load(f)
        if not isinstance(data, dict):
            return
        for k, v in data.items():
            if k not in st.session_state or st.session_state.get(k) in [None, "", 0]:
                st.session_state[k] = v
        # restore best scores into active score keys when missing
        for key in ["cv_score_value", "ats_score_value", "application_readiness_value"]:
            best = int(st.session_state.get("_best_" + key) or 0)
            cur = int(st.session_state.get(key) or 0)
            if best > cur:
                st.session_state[key] = best
    except Exception:
        pass


def _wz35_remember_scores():
    try:
        for key in ["cv_score_value", "ats_score_value", "application_readiness_value", "job_fit_score_value", "interview_score"]:
            try:
                cur = int(float(st.session_state.get(key) or 0))
            except Exception:
                cur = 0
            if cur > 0:
                best_key = "_best_" + key
                st.session_state[best_key] = max(cur, int(st.session_state.get(best_key) or 0))
    except Exception:
        pass


def _wz35_force_scroll_top():
    try:
        st.markdown('<span id="workzo-page-top"></span>', unsafe_allow_html=True)
        script = """
        <script>
        const wzScrollTop = () => {
          try { window.scrollTo(0,0); } catch(e) {}
          try { window.parent.scrollTo(0,0); } catch(e) {}
          try {
            const d = window.parent.document;
            [d.scrollingElement, d.documentElement, d.body,
             d.querySelector('section.main'),
             d.querySelector('div[data-testid="stAppViewContainer"]'),
             d.querySelector('.main')].filter(Boolean).forEach(el => { try { el.scrollTop = 0; } catch(e) {} });
          } catch(e) {}
        };
        wzScrollTop(); setTimeout(wzScrollTop, 50); setTimeout(wzScrollTop, 250); setTimeout(wzScrollTop, 700);
        </script>
        """
        if hasattr(st, "iframe"):
            st.iframe(srcdoc=script, height=1, width=1)
        else:
            st.markdown(script, unsafe_allow_html=True)
    except Exception:
        pass


def _wz35_sync_language(value=None):
    try:
        lang = value or st.session_state.get("preferred_language") or st.session_state.get("language") or "English"
        st.session_state["preferred_language"] = lang
        st.session_state["language"] = lang
        st.session_state["response_language"] = lang
        try:
            st.session_state["ui_language"] = lang if "UI_TEXT" in globals() and lang in UI_TEXT else "English"
        except Exception:
            st.session_state["ui_language"] = lang
        if callable(globals().get("set_single_preferred_language")):
            try:
                set_single_preferred_language(lang)
            except Exception:
                pass
    except Exception:
        pass


def _wz35_go(page, extra=None):
    try:
        if isinstance(extra, dict):
            for k, v in extra.items():
                st.session_state[k] = v
        st.session_state["page"] = page
        st.session_state["nav_page"] = page
        try:
            st.query_params["page"] = page
            st.query_params["wz_top"] = str(int(_wz35_time.time() * 1000))
        except Exception:
            pass
        try:
            request_scroll_to_top()
        except Exception:
            pass
        _wz35_save_state()
        st.rerun()
    except Exception:
        pass


def _wz35_score(*keys, default=0):
    for key in keys:
        try:
            value = st.session_state.get(key)
            if value not in [None, ""]:
                n = int(float(value))
                if n > 0:
                    return max(0, min(100, n))
        except Exception:
            pass
    return default


def _wz35_css():
    try:
        st.markdown("""
        <style>
        .block-container{padding-top:.55rem!important;max-width:1220px!important;}
        .workzo-header{margin-top:4px!important;margin-bottom:12px!important;}
        .wz35-hero{border:1px solid rgba(20,184,166,.28);border-radius:24px;padding:20px 24px;background:linear-gradient(135deg,rgba(20,184,166,.16),rgba(37,99,235,.14));box-shadow:0 12px 35px rgba(2,6,23,.22);margin:10px 0 18px;}
        .wz35-kicker{color:#93c5fd;text-transform:uppercase;letter-spacing:.08em;font-weight:850;font-size:.78rem;margin-bottom:7px;}
        .wz35-title{color:#fff;font-weight:900;font-size:1.75rem;line-height:1.18;margin-bottom:7px;}
        .wz35-sub{color:#dbeafe;font-size:.98rem;line-height:1.45;}
        .wz35-chip-row{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px;}
        .wz35-chip{border:1px solid rgba(96,165,250,.26);background:rgba(37,99,235,.16);color:#dbeafe;border-radius:999px;padding:6px 11px;font-weight:700;font-size:.84rem;}
        .wz35-next{border:1px solid rgba(45,212,191,.34);background:linear-gradient(135deg,rgba(20,184,166,.18),rgba(15,23,42,.58));border-radius:20px;padding:17px 18px;margin:12px 0 18px;}
        .wz35-next-label{color:#99f6e4;font-size:.78rem;text-transform:uppercase;letter-spacing:.07em;font-weight:850;margin-bottom:4px;}
        .wz35-next-title{font-size:1.25rem;color:#fff;font-weight:900;margin-bottom:5px;}
        .wz35-next-copy{color:#cbd5e1;font-size:.96rem;line-height:1.45;}
        .wz35-rate{border:1px solid rgba(148,163,184,.17);background:linear-gradient(180deg,rgba(30,41,59,.78),rgba(15,23,42,.72));border-radius:20px;padding:18px;min-height:160px;}
        .wz35-rate-title{color:#fff;font-weight:900;font-size:1rem;display:flex;justify-content:space-between;gap:8px;}
        .wz35-rate-value{color:#fff;font-size:2rem;font-weight:900;margin:12px 0 8px;}
        .wz35-bar{height:10px;border-radius:999px;background:rgba(148,163,184,.20);overflow:hidden;margin:6px 0 12px;}
        .wz35-fill{height:100%;border-radius:999px;background:linear-gradient(90deg,#38bdf8,#2dd4bf);}
        .wz35-rate-copy{color:#bfdbfe;font-size:.9rem;line-height:1.4;}
        .wz35-action{border:1px solid rgba(148,163,184,.16);background:rgba(15,23,42,.52);border-radius:20px;padding:18px;min-height:150px;}
        .wz35-action-title{color:#fff;font-weight:900;font-size:1.06rem;margin-bottom:8px;}
        .wz35-action-copy{color:#bfdbfe;font-size:.93rem;line-height:1.45;min-height:62px;}
        .wz35-flow-card{border:1px solid rgba(148,163,184,.17);background:rgba(15,23,42,.50);border-radius:18px;padding:16px 18px;min-height:108px;}
        .wz35-flow-card.done{border-color:rgba(45,212,191,.45);background:rgba(20,184,166,.13);}
        .wz35-flow-card.current{border-color:rgba(96,165,250,.58);background:rgba(37,99,235,.14);}
        .wz35-flow-title{font-weight:900;color:#fff;font-size:.96rem;line-height:1.35;}
        .wz35-flow-note{color:#bfdbfe;font-size:.84rem;margin-top:8px;line-height:1.35;}
        </style>
        """, unsafe_allow_html=True)
    except Exception:
        pass


def _wz35_rate_card(title, score, copy, missing=False):
    if missing or not score:
        value = "—"
        width = 0
    else:
        value = f"{int(score)}%"
        width = max(0, min(100, int(score)))
    st.markdown(f"""
    <div class='wz35-rate'>
      <div class='wz35-rate-title'><span>{_wz35_escape(title)}</span></div>
      <div class='wz35-rate-value'>{_wz35_escape(value)}</div>
      <div class='wz35-bar'><div class='wz35-fill' style='width:{width}%;'></div></div>
      <div class='wz35-rate-copy'>{_wz35_escape(copy)}</div>
    </div>
    """, unsafe_allow_html=True)


def _wz35_action_card(title, copy, button, target, key, extra=None):
    st.markdown(f"""
    <div class='wz35-action'>
      <div class='wz35-action-title'>{_wz35_escape(title)}</div>
      <div class='wz35-action-copy'>{_wz35_escape(copy)}</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button(button, key=key, use_container_width=True):
        _wz35_go(target, extra)


def _wz35_flow_card(label, done, current, note):
    cls = "done" if done else ("current" if current else "")
    icon = "✅" if done else ("➜" if current else "○")
    st.markdown(f"""
    <div class='wz35-flow-card {cls}'>
      <div class='wz35-flow-title'>{icon} {_wz35_escape(label)}</div>
      <div class='wz35-flow-note'>{_wz35_escape(note)}</div>
    </div>
    """, unsafe_allow_html=True)


def _wz35_next_action(cv_exists, resume_score, ats_score, job_exists, improved_ready, prepared_ready):
    if not cv_exists:
        return {"title":"Start with your CV", "copy":"Upload or create your CV first so WorkZo can score it and guide the next steps.", "button":"Add CV", "target":"onboarding", "extra":{}}
    if resume_score < 75 or ats_score < 75:
        return {"title":"Improve your CV first", "copy":"Your Resume or ATS score needs improvement. Fix structure, keywords, and role alignment before applying widely.", "button":"Open CV Tools", "target":"cv_documents", "extra":{"document_tools_mode":"Improve / Update CV"}}
    if not job_exists:
        return {"title":"Find or analyze a job next", "copy":"Your CV is ready enough. Now find matching roles or paste one job description for a fit check.", "button":"Open Job Assist", "target":"job_assist", "extra":{"job_assist_mode_key":"find"}}
    if not improved_ready:
        return {"title":"Tailor your CV for this job", "copy":"You have job context. Now tailor the CV to this specific role before creating application materials.", "button":"Improve CV for Job", "target":"cv_documents", "extra":{"document_tools_mode":"Improve CV for a Job"}}
    if not prepared_ready:
        return {"title":"Prepare the application", "copy":"Create a focused cover letter and preparation notes using the company, CV, and job description.", "button":"Prepare Application", "target":"job_assist", "extra":{"job_assist_mode_key":"prepare"}}
    return {"title":"Ready to apply", "copy":"Your core application flow is complete. Apply, save the tracker item, and practice answers in Work-O-Bot.", "button":"Practice with Work-O-Bot", "target":"workobot", "extra":{}}


def _wz35_sidebar(page_key):
    with st.sidebar:
        try:
            logo_src = image_to_data_uri(ICON_PATH) or image_to_data_uri(LOGO_PATH)
        except Exception:
            logo_src = None
        if logo_src:
            st.markdown(f"""
            <div class='workzo-sidebar-brand-wrap'>
              <img src='{logo_src}' class='workzo-sidebar-logo' alt='WorkZo AI logo'>
              <div><div class='workzo-sidebar-brand'>WORKZO AI</div><div class='workzo-sidebar-version'>Beta · guided workspace</div></div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("### WorkZo AI")
        navs = [("dashboard", txt("dashboard")), ("cv_documents", txt("cv_documents")), ("job_assist", txt("job_assist")), ("workobot", "Work-O-Bot")]
        for key, label in navs:
            text = label + ("  ✓" if page_key == key else "")
            if st.button(text, key=f"wz35_nav_{key}", use_container_width=True):
                _wz35_go(key)
        st.markdown(f"<div class='workzo-sidebar-section-label'>{html.escape(txt('company_context'))}</div>", unsafe_allow_html=True)
        with st.expander("🏢 " + txt("company_website"), expanded=False):
            company_url = st.text_input(txt("company_website"), key="target_company_website", placeholder="https://company.com")
            if company_url:
                st.caption(ui_label("Used for cover letters and job/interview preparation context."))
        st.markdown(f"<div class='workzo-sidebar-section-label'>{html.escape(txt('language'))}</div>", unsafe_allow_html=True)
        try:
            langs = language_options if "language_options" in globals() and language_options else ["English", "German", "Dutch", "French", "Spanish", "Portuguese"]
        except Exception:
            langs = ["English", "German", "Dutch", "French", "Spanish", "Portuguese"]
        cur = st.session_state.get("preferred_language") or st.session_state.get("language") or "English"
        if cur not in langs:
            cur = "English" if "English" in langs else langs[0]
        def _wz39_language_changed():
            _new_lang = st.session_state.get("wz39_preferred_language", cur)
            try:
                if callable(globals().get("workzo_set_language_everywhere")):
                    workzo_set_language_everywhere(_new_lang)
                else:
                    set_single_preferred_language(_new_lang)
                st.query_params["wz_lang"] = _new_lang
            except Exception:
                pass
        if st.session_state.get("wz39_preferred_language") != cur:
            st.session_state["wz39_preferred_language"] = cur
        chosen = st.selectbox(txt("preferred_language"), langs, index=langs.index(cur), key="wz39_preferred_language", on_change=_wz39_language_changed)
        _wz35_sync_language(chosen)
        st.markdown("---")
        if st.button(txt("edit_setup"), key="wz35_edit_setup", use_container_width=True):
            st.session_state["onboarding_complete"] = False
            st.session_state["page"] = "onboarding"
            st.session_state["nav_page"] = "onboarding"
            try:
                st.query_params["page"] = "onboarding"
            except Exception:
                pass
            _wz35_save_state()
            st.rerun()


def _wz35_dashboard_home():
    _wz35_load_state()
    _wz35_remember_scores()
    _wz35_force_scroll_top()
    _wz35_css()

    cv_exists = bool(str(st.session_state.get("cv_text", "")).strip() or st.session_state.get("structured_cv_json") or st.session_state.get("_workzo_has_cv"))
    if cv_exists:
        st.session_state["_workzo_has_cv"] = True
    job_text = str(st.session_state.get("current_job_description", "") or st.session_state.get("last_understand_job_description", "") or st.session_state.get("improve_cv_for_job_desc", "") or st.session_state.get("job_description", "")).strip()
    job_exists = bool(job_text)
    improved_ready = bool(str(st.session_state.get("improved_cv_text", "") or st.session_state.get("latest_improved_cv", "") or st.session_state.get("final_cv_text", "")).strip())
    prepared_ready = bool(str(st.session_state.get("latest_application_prep", "") or st.session_state.get("latest_cover_letter", "") or st.session_state.get("cover_letter_text", "")).strip())
    resume_score = _wz35_score("cv_score_value", "resume_score", "resume_quality_score", "_best_cv_score_value", default=76 if cv_exists else 0)
    ats_score = _wz35_score("ats_score_value", "ats_score", "_best_ats_score_value", default=70 if cv_exists else 0)
    interview_score = _wz35_score("interview_score", "interview_readiness", "_best_interview_score", default=65 if cv_exists and job_exists and resume_score >= 75 and ats_score >= 75 else (40 if cv_exists else 0))

    country = st.session_state.get("country") or st.session_state.get("target_country") or "Not set"
    language = st.session_state.get("preferred_language") or st.session_state.get("language") or "English"
    company = st.session_state.get("prepare_target_company") or st.session_state.get("target_company") or st.session_state.get("target_company_website") or ui_label("Company not added")
    next_action = _wz35_next_action(cv_exists, resume_score, ats_score, job_exists, improved_ready, prepared_ready)

    st.markdown(f"""
    <div class='wz35-hero'>
      <div class='wz35-kicker'>{_wz35_escape(txt('workzo_command_center'))}</div>
      <div class='wz35-title'>{_wz35_escape(txt('next_best_move_clear'))}</div>
      <div class='wz35-sub'>{_wz35_escape(txt('next_best_move_copy'))}</div>
      <div class='wz35-chip-row'>
        <span class='wz35-chip'>{_wz35_escape(country)}</span>
        <span class='wz35-chip'>{_wz35_escape(language)}</span>
        <span class='wz35-chip'>{_wz35_escape(ui_label('CV ready') if cv_exists else ui_label('CV missing'))}</span>
        <span class='wz35-chip'>{_wz35_escape(ui_label('Job added') if job_exists else ui_label('Job not added'))}</span>
        <span class='wz35-chip'>{_wz35_escape(company)}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class='wz35-next'>
      <div class='wz35-next-label'>{_wz35_escape(txt('recommended_next_step'))}</div>
      <div class='wz35-next-title'>{_wz35_escape(next_action['title'])}</div>
      <div class='wz35-next-copy'>{_wz35_escape(next_action['copy'])}</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button(next_action["button"], key="wz35_primary_action", use_container_width=True):
        _wz35_go(next_action["target"], next_action.get("extra"))

    st.markdown("### " + txt("readiness_overview"))
    c1, c2, c3 = st.columns(3)
    with c1:
        _wz35_rate_card(txt("resume_score"), resume_score, ui_label("Clarity, structure, achievements, and overall CV quality."), missing=not cv_exists)
    with c2:
        _wz35_rate_card(txt("ats_score"), ats_score, ui_label("Scanner-friendly formatting, role keywords, sections, and parsing safety."), missing=not cv_exists)
    with c3:
        _wz35_rate_card(txt("interview_readiness"), interview_score, ui_label("How ready you are to explain your CV and job fit clearly."), missing=not cv_exists)

    st.markdown("### " + txt("smart_actions"))
    a1, a2, a3, a4 = st.columns(4)
    with a1:
        _wz35_action_card(txt("improve_cv"), ui_label("Use this when Resume or ATS score is below 75, or when tailoring for one job."), txt("open_cv_tools"), "cv_documents", "wz35_action_cv", {"document_tools_mode":"Improve CV for a Job" if job_exists else "Improve / Update CV"})
    with a2:
        _wz35_action_card(txt("job_match"), ui_label("Search jobs for the selected country, then analyze one job description for fit."), txt("open_job_assist"), "job_assist", "wz35_action_jobs", {"job_assist_mode_key":"find"})
    with a3:
        _wz35_action_card(txt("cover_letter"), ui_label("Use CV, job description, and company context to create a focused cover letter."), txt("create_cover_letter"), "cv_documents", "wz35_action_cover", {"document_tools_mode":"Cover Letter Generator + Language"})
    with a4:
        _wz35_action_card("Work-O-Bot", ui_label("Ask career questions or practice interview answers in your selected language."), txt("ask_workobot"), "workobot", "wz35_action_bot")

    st.markdown("### " + txt("application_progress"))
    st.caption(ui_label("Visual tracker only. Use Smart actions above to continue."))

    # Application progress should show only the 4 real user journey steps.
    # Default behavior: only CV uploaded gets the green tick after onboarding/CV exists.
    progress_cv_uploaded = bool(cv_exists)
    progress_cv_improved = bool(improved_ready or st.session_state.get("workzo_progress_cv_improved"))
    progress_job_matched = bool(job_exists or st.session_state.get("workzo_progress_job_matched"))
    progress_prepared = bool(prepared_ready or st.session_state.get("workzo_progress_prepared"))

    flow = [
        ("1. CV uploaded", progress_cv_uploaded, txt("completed") if progress_cv_uploaded else ui_label("Upload or create CV")),
        ("2. CV improved", progress_cv_improved, txt("completed") if progress_cv_improved else ui_label("Improve or tailor your CV")),
        ("3. Job matched", progress_job_matched, txt("completed") if progress_job_matched else ui_label("Find matching jobs")),
        ("4. Prepared for job", progress_prepared, txt("completed") if progress_prepared else ui_label("Prepare cover letter and interview notes")),
    ]
    try:
        current = next((i for i, (_, done, _) in enumerate(flow) if not done), len(flow) - 1)
    except Exception:
        current = 0
    cols = st.columns(4)
    for i, (label, done, note) in enumerate(flow):
        with cols[i]:
            _wz35_flow_card(label, done, (not done and current == i), note)

    st.caption(ui_label("Scores are guidance only. WorkZo should not invent skills, company facts, language level, salary, or experience."))
    _wz35_remember_scores()
    _wz35_save_state()


# Final clean router. This avoids older dashboard wrappers that printed raw HTML.
def show_dashboard():
    _wz35_load_state()
    _wz35_sync_language()
    _wz35_force_scroll_top()
    page_key = st.session_state.get("nav_page") or st.session_state.get("page") or "dashboard"
    page_key = {"landing":"dashboard", "bot":"workobot", "interview":"workobot", "jobs":"job_assist", "improve_cv":"cv_documents"}.get(page_key, page_key)
    if page_key == "interview_practice":
        page_key = "workobot"
    if page_key not in {"dashboard", "cv_documents", "job_assist", "workobot"}:
        page_key = "dashboard"
    st.session_state["page"] = page_key
    st.session_state["nav_page"] = page_key
    try:
        _wz28_top(True)
    except Exception:
        pass
    _wz35_sidebar(page_key)
    if page_key == "dashboard":
        _wz35_dashboard_home()
    elif page_key == "cv_documents":
        _wz35_css()
        show_document_tools()
    elif page_key == "job_assist":
        _wz35_css()
        # Use the older Job Assist page layout if available.
        try:
            _wz28_job_assist_page()
        except Exception:
            st.subheader(txt("job_assist"))
            tab1, tab2, tab3 = st.tabs([txt("find_jobs"), txt("understand_job"), txt("prepare_this_job")])
            with tab1:
                st.info("Job search module could not be loaded.")
            with tab2:
                st.info("Understand Job module could not be loaded.")
            with tab3:
                st.info("Prepare module could not be loaded.")
    elif page_key == "workobot":
        _wz35_css()
        show_workobot()
    _wz35_remember_scores()
    _wz35_save_state()

# =========================================================
# WorkZo v36 LANGUAGE SYNC + SMART CONTEXT PATCH
# Dashboard language dropdown now updates the whole app consistently.
# Smart stage flags allow features to adapt based on CV/ATS/job situation.
# =========================================================
def _wz36_sync_language_from_widgets():
    """Sync language from the newest visible selector. Sidebar wins over old onboarding keys."""
    try:
        candidate_keys = [
            "wz39_preferred_language", "sidebar_preferred_language", "wz35_preferred_language", "wz24_sidebar_preferred_language",
            "wz25_sidebar_preferred_language", "wz21_sidebar_preferred_language", "wz19_sidebar_preferred_language",
            "onboarding_preferred_language",
        ]
        current = st.session_state.get("preferred_language") or st.session_state.get("language") or "English"
        chosen = current
        for k in candidate_keys:
            val = st.session_state.get(k)
            if isinstance(val, str) and val.strip():
                chosen = val.strip()
                break
        if callable(globals().get("workzo_set_language_everywhere")):
            workzo_set_language_everywhere(chosen)
        else:
            set_single_preferred_language(chosen)
        return chosen != current
    except Exception:
        return False


def _wz36_smart_context_flags():
    try:
        cv_exists = bool(str(st.session_state.get("cv_text", "")).strip() or st.session_state.get("structured_cv_json"))
        jd_exists = bool(str(st.session_state.get("current_job_description", "") or st.session_state.get("last_understand_job_description", "") or st.session_state.get("job_description", "")).strip())
        resume_score = int(st.session_state.get("cv_score_value") or st.session_state.get("resume_score") or 0)
        ats_score = int(st.session_state.get("ats_score_value") or st.session_state.get("ats_score") or 0)
        if not cv_exists:
            stage = "need_cv"
        elif resume_score and ats_score and (resume_score < 75 or ats_score < 75):
            stage = "improve_cv"
        elif not jd_exists:
            stage = "find_or_analyze_job"
        else:
            stage = "prepare_application"
        st.session_state["workzo_smart_stage"] = stage
        st.session_state["workzo_context_is_ready"] = bool(cv_exists and resume_score >= 75 and ats_score >= 75)
    except Exception:
        pass

try:
    _wz36_previous_show_dashboard = show_dashboard
    def show_dashboard():
        lang_changed = _wz36_sync_language_from_widgets()
        _wz36_smart_context_flags()
        if lang_changed:
            try:
                st.query_params["wz_lang"] = st.session_state.get("preferred_language", "English")
            except Exception:
                pass
        return _wz36_previous_show_dashboard()
except Exception:
    pass


# =========================================================
# WorkZo v38 final language + Work-O-Bot safety patch
# =========================================================
def _wz38_sync_language_now():
    try:
        # Prefer active sidebar/dashboard selector; onboarding key is only fallback.
        for _k in ["wz39_preferred_language", "sidebar_preferred_language", "wz35_preferred_language", "wz24_sidebar_preferred_language", "onboarding_preferred_language"]:
            _val = st.session_state.get(_k)
            if isinstance(_val, str) and _val.strip():
                if callable(globals().get("workzo_set_language_everywhere")):
                    workzo_set_language_everywhere(_val.strip())
                else:
                    set_single_preferred_language(_val.strip())
                return _val.strip()
        _lang = st.session_state.get("preferred_language") or st.session_state.get("language") or "English"
        if callable(globals().get("workzo_set_language_everywhere")):
            workzo_set_language_everywhere(_lang)
        else:
            set_single_preferred_language(_lang)
        return _lang
    except Exception:
        return "English"

try:
    _wz38_previous_show_dashboard = show_dashboard
    def show_dashboard():
        _before = st.session_state.get("preferred_language") or st.session_state.get("language") or "English"
        _after = _wz38_sync_language_now()
        # If user changed language through a sidebar selector, rerun once so all labels refresh.
        if _after != _before and not st.session_state.get("_wz38_language_rerun_done"):
            st.session_state["_wz38_language_rerun_done"] = True
            st.rerun()
        st.session_state["_wz38_language_rerun_done"] = False
        return _wz38_previous_show_dashboard()
except Exception:
    pass


# =========================================================
# WorkZo v40 - translate final dashboard literals used by smart cards
# =========================================================
def _wz35_next_action(cv_exists, resume_score, ats_score, job_exists, improved_ready, prepared_ready):
    if not cv_exists:
        return {"title":ui_label("Start with your CV"), "copy":ui_label("Upload or create your CV first so WorkZo can score it and guide the next steps."), "button":ui_label("Add CV"), "target":"onboarding", "extra":{}}
    if resume_score < 75 or ats_score < 75:
        return {"title":ui_label("Improve your CV first"), "copy":ui_label("Your Resume or ATS score needs improvement. Fix structure, keywords, and role alignment before applying widely."), "button":txt("open_cv_tools"), "target":"cv_documents", "extra":{"document_tools_mode":"Improve / Update CV"}}
    if not job_exists:
        return {"title":ui_label("Find or analyze a job next"), "copy":ui_label("Your CV is ready enough. Now find matching roles or paste one job description for a fit check."), "button":txt("open_job_assist"), "target":"job_assist", "extra":{"job_assist_mode_key":"find"}}
    if not improved_ready:
        return {"title":ui_label("Tailor your CV for this job"), "copy":ui_label("You have job context. Now tailor the CV to this specific role before creating application materials."), "button":ui_label("Improve CV for Job"), "target":"cv_documents", "extra":{"document_tools_mode":"Improve CV for a Job"}}
    if not prepared_ready:
        return {"title":ui_label("Prepare the application"), "copy":ui_label("Create a focused cover letter and preparation notes using the company, CV, and job description."), "button":txt("prepare_this_job"), "target":"job_assist", "extra":{"job_assist_mode_key":"prepare"}}
    return {"title":ui_label("Ready to apply"), "copy":ui_label("Your core application flow is complete. Apply, save the tracker item, and practice answers in Work-O-Bot."), "button":txt("ask_workobot"), "target":"workobot", "extra":{}}

# Make score guidance translatable wherever the final dashboard uses it.
try:
    if "UI_TEXT" in globals():
        UI_TEXT.setdefault("German", {}).update({
            "readiness_overview": "Bereitschaftsübersicht",
            "smart_actions": "Smarte Aktionen",
            "open_cv_tools": "CV-Tools öffnen",
            "open_job_assist": "Job Assist öffnen",
            "create_cover_letter": "Cover Letter erstellen",
            "ask_workobot": "Work-O-Bot fragen",
        })
        UI_TEXT.setdefault("French", {}).update({
            "readiness_overview": "Vue d’ensemble de la préparation",
            "smart_actions": "Actions intelligentes",
            "open_cv_tools": "Ouvrir les outils CV",
            "open_job_assist": "Ouvrir l’assistant emploi",
            "create_cover_letter": "Créer une lettre de motivation",
            "ask_workobot": "Demander à Work-O-Bot",
        })
except Exception:
    pass


# =========================================================
# WorkZo v41 - final dashboard language sync
# =========================================================
def _wz41_sync_language_from_any_widget():
    try:
        for _k in ["wz39_preferred_language", "sidebar_preferred_language", "wz35_preferred_language", "wz40_mobile_preferred_language", "wz30_language", "wz29_language", "wz28_language", "wz27_language", "onboarding_preferred_language", "preferred_language", "language"]:
            _v = st.session_state.get(_k)
            if isinstance(_v, str) and _v.strip():
                if callable(globals().get("workzo_set_language_everywhere")):
                    return workzo_set_language_everywhere(_v.strip())
                st.session_state["preferred_language"] = _v.strip()
                st.session_state["language"] = _v.strip()
                st.session_state["ui_language"] = _v.strip()
                st.session_state["response_language"] = _v.strip()
                return _v.strip()
    except Exception:
        pass
    return st.session_state.get("preferred_language", "English")

try:
    _wz41_previous_show_dashboard = show_dashboard
    def show_dashboard():
        _wz41_sync_language_from_any_widget()
        return _wz41_previous_show_dashboard()
except Exception:
    pass

# =========================================================

# =========================================================

# =========================================================
# WorkZo v45 - mobile top navigation, desktop left sidebar
# Desktop users keep the native left toolbox. Mobile users get a top nav so
# content is not squeezed by the Streamlit sidebar.
# =========================================================
def _wz45_render_mobile_top_nav():
    try:
        import time as _time
        import html as _html
        lang = str(st.session_state.get("preferred_language", "English") or "English")
        labels = {
            "English": {"tools": "Tools / Navigation", "dashboard": "Dashboard", "cv": "CV Documents", "jobs": "Job Assist", "bot": "Work-O-Bot"},
            "German": {"tools": "Tools / Navigation", "dashboard": "Dashboard", "cv": "Lebenslauf & Dokumente", "jobs": "Job-Assistent", "bot": "Work-O-Bot"},
            "French": {"tools": "Outils / navigation", "dashboard": "Tableau de bord", "cv": "CV & documents", "jobs": "Assistant emploi", "bot": "Work-O-Bot"},
            "Dutch": {"tools": "Tools / navigatie", "dashboard": "Dashboard", "cv": "CV & documenten", "jobs": "Jobassistent", "bot": "Work-O-Bot"},
            "Spanish": {"tools": "Herramientas / navegación", "dashboard": "Panel", "cv": "CV y documentos", "jobs": "Asistente de empleo", "bot": "Work-O-Bot"},
        }
        t = labels.get(lang, labels["English"])
        nonce = str(int(_time.time() * 1000))
        def link(page, text):
            return f"<a class='wz45-mobile-link' href='?page={page}&wz_top={nonce}'>{_html.escape(text)}</a>"
        st.markdown(
            f"""
            <style>
            /* WorkZo v46: show this top toolbox ONLY on mobile.
               Desktop keeps the real Streamlit left sidebar toolbox. */
            .wz45-mobile-topnav {{ display: none !important; }}
            @media (max-width: 700px) {{
                .wz45-mobile-topnav {{
                    display: block !important;
                    position: sticky !important;
                    top: 0 !important;
                    z-index: 9999 !important;
                    margin: 0 0 0.75rem 0 !important;
                    padding: 0.75rem !important;
                    border: 1px solid rgba(20,184,166,0.24) !important;
                    border-radius: 18px !important;
                    background: linear-gradient(135deg, rgba(15,23,42,0.98), rgba(8,47,73,0.92)) !important;
                    box-shadow: 0 10px 28px rgba(2,6,23,0.30) !important;
                }}
                .wz45-mobile-title {{ color: #f8fafc !important; font-weight: 850 !important; font-size: 0.95rem !important; margin-bottom: 0.5rem !important; }}
                .wz45-mobile-links {{ display: grid !important; grid-template-columns: repeat(2, minmax(0, 1fr)) !important; gap: 0.45rem !important; }}
                .wz45-mobile-link {{
                    display: block !important;
                    text-align: center !important;
                    color: #e0f2fe !important;
                    text-decoration: none !important;
                    border: 1px solid rgba(96,165,250,0.26) !important;
                    background: rgba(37,99,235,0.16) !important;
                    border-radius: 999px !important;
                    padding: 0.48rem 0.55rem !important;
                    font-weight: 700 !important;
                    font-size: 0.86rem !important;
                    white-space: nowrap !important;
                }}
            }}
            </style>
            <div class="wz45-mobile-topnav">
                <div class="wz45-mobile-title">☰ {_html.escape(t['tools'])}</div>
                <div class="wz45-mobile-links">
                    {link('dashboard', '🏠 ' + t['dashboard'])}
                    {link('cv_documents', '📄 ' + t['cv'])}
                    {link('job_assist', '🎯 ' + t['jobs'])}
                    {link('workobot', '🤖 ' + t['bot'])}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    except Exception:
        pass

try:
    _wz45_previous_show_dashboard = show_dashboard
    def show_dashboard():
        _wz45_render_mobile_top_nav()
        return _wz45_previous_show_dashboard()
except Exception:
    pass


# =========================================================
# WorkZo v48 dashboard responsive toolbox guard
# The mobile top menu is rendered, but CSS shows it only on phones.
# =========================================================
try:
    st.markdown("""
    <style id="workzo-v48-dashboard-topnav-guard">
    .wz45-mobile-topnav { display: none !important; }
    @media (min-width: 701px) {
        .wz45-mobile-topnav {
            display: none !important;
            visibility: hidden !important;
            height: 0 !important;
            overflow: hidden !important;
            margin: 0 !important;
            padding: 0 !important;
            border: 0 !important;
        }
    }
    @media (max-width: 700px) {
        .wz45-mobile-topnav { display: block !important; visibility: visible !important; height: auto !important; }
    }
    </style>
    """, unsafe_allow_html=True)
except Exception:
    pass


# =========================================================
# WorkZo v49 memory + progress stabilization wrapper
# Keeps safe dashboard progress after refresh and saves status flags continuously.
# =========================================================
def _wz49_detect_and_save_progress_flags():
    try:
        if st.session_state.get('cv_text') or st.session_state.get('structured_cv_json') or st.session_state.get('approved_structured_cv_json'):
            st.session_state['_wz_has_cv'] = True
        if st.session_state.get('improved_cv_text') or st.session_state.get('latest_improved_cv') or st.session_state.get('final_cv_text'):
            st.session_state['_wz_cv_improved'] = True
        if st.session_state.get('latest_curated_jobs') or st.session_state.get('latest_job_query_expansion'):
            st.session_state['_wz_job_found'] = True
        if st.session_state.get('latest_job_analysis') or st.session_state.get('last_understand_job_description') or st.session_state.get('current_job_description'):
            st.session_state['_wz_job_analyzed'] = True
        if st.session_state.get('latest_application_prep') or st.session_state.get('latest_cover_letter') or st.session_state.get('cover_letter_text'):
            st.session_state['_wz_prepared'] = True
        for a, b in [('cv_score_value','_best_cv_score_value'), ('ats_score_value','_best_ats_score_value'), ('job_fit_score_value','_best_job_fit_score_value')]:
            try:
                cur = int(float(st.session_state.get(a) or 0))
                best = int(float(st.session_state.get(b) or 0))
                if cur > best:
                    st.session_state[b] = cur
                elif best > 0 and cur <= 0:
                    st.session_state[a] = best
            except Exception:
                pass
        if callable(globals().get('workzo_save_light_memory')):
            workzo_save_light_memory()
    except Exception:
        pass

try:
    _wz49_previous_show_dashboard = show_dashboard
    def show_dashboard():
        try:
            if callable(globals().get('workzo_load_light_memory')):
                workzo_load_light_memory()
        except Exception:
            pass
        _wz49_detect_and_save_progress_flags()
        result = _wz49_previous_show_dashboard()
        _wz49_detect_and_save_progress_flags()
        return result
except Exception:
    pass

# =========================================================
# WorkZo v50 FINAL PROGRESS + FOUNDER ANALYTICS PATCH
# Fixes false green checks by using explicit completion conditions:
# 1 CV uploaded, 2 CV improved, 3 Job matched, 4 Prepared for job.
# Adds founder tracking events for each progress transition.
# =========================================================

def _wz50_bool_text(*keys):
    try:
        return any(bool(str(st.session_state.get(k, '') or '').strip()) for k in keys)
    except Exception:
        return False


def _wz50_has_list(key):
    try:
        v = st.session_state.get(key)
        return isinstance(v, list) and len(v) > 0
    except Exception:
        return False


def _wz50_progress_state():
    """Return strict progress state. Do not mark steps done merely because a score exists."""
    cv_uploaded = bool(
        str(st.session_state.get('cv_text', '') or '').strip()
        or st.session_state.get('structured_cv_json')
        or st.session_state.get('approved_structured_cv_json')
        or st.session_state.get('_workzo_has_cv')
        or st.session_state.get('_wz_progress_cv_uploaded')
    )
    if cv_uploaded:
        st.session_state['_wz_progress_cv_uploaded'] = True
        st.session_state['_workzo_has_cv'] = True

    cv_improved = bool(
        _wz50_bool_text('improved_cv_text', 'latest_improved_cv', 'final_cv_text', 'workzo_latest_tailored_cv')
        or st.session_state.get('_wz_progress_cv_improved')
    )
    if _wz50_bool_text('improved_cv_text', 'latest_improved_cv', 'final_cv_text', 'workzo_latest_tailored_cv'):
        st.session_state['_wz_progress_cv_improved'] = True
        cv_improved = True

    # Job match/finding is NOT the same as merely having a pasted job description.
    # It becomes complete only after live job search/curation exists, or an explicit progress flag was set.
    job_matched = bool(
        _wz50_has_list('latest_curated_jobs')
        or _wz50_has_list('latest_live_jobs')
        or _wz50_has_list('job_search_results')
        or bool(st.session_state.get('latest_job_query_expansion'))
        or st.session_state.get('_wz_progress_job_matched')
    )
    if _wz50_has_list('latest_curated_jobs') or _wz50_has_list('latest_live_jobs') or _wz50_has_list('job_search_results') or bool(st.session_state.get('latest_job_query_expansion')):
        st.session_state['_wz_progress_job_matched'] = True
        job_matched = True

    prepared = bool(
        _wz50_bool_text('latest_application_prep', 'latest_cover_letter', 'cover_letter_text', 'generated_cover_letter', 'saved_application_prep')
        or st.session_state.get('_wz_progress_prepared')
    )
    if _wz50_bool_text('latest_application_prep', 'latest_cover_letter', 'cover_letter_text', 'generated_cover_letter', 'saved_application_prep'):
        st.session_state['_wz_progress_prepared'] = True
        prepared = True

    return {
        'cv_uploaded': bool(cv_uploaded),
        'cv_improved': bool(cv_improved),
        'job_matched': bool(job_matched),
        'prepared': bool(prepared),
    }


def _wz50_track_progress(progress):
    """Founder-safe analytics: track progress flags only, no CV/job text."""
    try:
        previous = st.session_state.get('_wz50_last_progress_snapshot') or {}
        if not isinstance(previous, dict):
            previous = {}
        for key, done in progress.items():
            if done and not previous.get(key):
                if callable(globals().get('track_event')):
                    track_event('progress_step_completed', 'Application Progress', {'step': key})
        if previous != progress and callable(globals().get('track_event')):
            track_event('progress_snapshot', 'Application Progress', progress)
        st.session_state['_wz50_last_progress_snapshot'] = dict(progress)
    except Exception:
        pass


def _wz50_save_state():
    """Save safe UI memory. Do not persist CV text, job descriptions, or generated documents."""
    try:
        keys = [
            'cv_score_value', 'ats_score_value', 'application_readiness_value',
            'job_fit_score_value', 'interview_score', 'country', 'preferred_language',
            'ui_language', 'response_language', 'language', 'target_company_website',
            'target_company', 'prepare_target_company', 'nav_page', 'page',
            '_workzo_has_cv', '_wz_progress_cv_uploaded', '_wz_progress_cv_improved',
            '_wz_progress_job_matched', '_wz_progress_prepared',
            '_best_cv_score_value', '_best_ats_score_value', '_best_application_readiness_value',
        ]
        data = {}
        for k in keys:
            v = st.session_state.get(k)
            if isinstance(v, (str, int, float, bool)) or v is None:
                data[k] = v
        progress = _wz50_progress_state()
        data.update({
            '_wz_progress_cv_uploaded': progress['cv_uploaded'],
            '_wz_progress_cv_improved': progress['cv_improved'],
            '_wz_progress_job_matched': progress['job_matched'],
            '_wz_progress_prepared': progress['prepared'],
        })
        with open(_wz35_state_file(), 'w', encoding='utf-8') as f:
            _wz35_json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _wz50_load_state():
    """Load safe UI memory. Ignore old false-progress flags from earlier builds."""
    try:
        path = _wz35_state_file()
        if not _wz35_os.path.exists(path):
            return
        with open(path, 'r', encoding='utf-8') as f:
            data = _wz35_json.load(f)
        if not isinstance(data, dict):
            return
        allowed = {
            'cv_score_value', 'ats_score_value', 'application_readiness_value',
            'job_fit_score_value', 'interview_score', 'country', 'preferred_language',
            'ui_language', 'response_language', 'language', 'target_company_website',
            'target_company', 'prepare_target_company', 'nav_page', 'page',
            '_workzo_has_cv', '_wz_progress_cv_uploaded', '_wz_progress_cv_improved',
            '_wz_progress_job_matched', '_wz_progress_prepared',
            '_best_cv_score_value', '_best_ats_score_value', '_best_application_readiness_value',
        }
        for k, v in data.items():
            if k in allowed and (k not in st.session_state or st.session_state.get(k) in [None, '', 0, False]):
                st.session_state[k] = v
        for key in ['cv_score_value', 'ats_score_value', 'application_readiness_value']:
            try:
                best = int(st.session_state.get('_best_' + key) or 0)
                cur = int(st.session_state.get(key) or 0)
                if best > cur:
                    st.session_state[key] = best
            except Exception:
                pass
    except Exception:
        pass

# Rebind the older helper names so the rest of the file uses v50 memory.
_wz35_save_state = _wz50_save_state
_wz35_load_state = _wz50_load_state


def _wz50_sidebar(page_key):
    with st.sidebar:
        try:
            logo_src = image_to_data_uri(ICON_PATH) or image_to_data_uri(LOGO_PATH)
        except Exception:
            logo_src = None
        if logo_src:
            st.markdown(f"""
            <div class='workzo-sidebar-brand-wrap'>
              <img src='{logo_src}' class='workzo-sidebar-logo' alt='WorkZo AI logo'>
              <div><div class='workzo-sidebar-brand'>WORKZO AI</div><div class='workzo-sidebar-version'>Beta · guided workspace</div></div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown('### WorkZo AI')

        navs = [('dashboard', txt('dashboard')), ('cv_documents', txt('cv_documents')), ('job_assist', txt('job_assist')), ('workobot', 'Work-O-Bot')]
        for key, label in navs:
            text = str(label) + ('  ✓' if page_key == key else '')
            if st.button(text, key=f'wz50_nav_{key}', use_container_width=True):
                _wz35_go(key)

        st.markdown(f"<div class='workzo-sidebar-section-label'>{html.escape(txt('company_context'))}</div>", unsafe_allow_html=True)
        with st.expander('🏢 ' + txt('company_website'), expanded=False):
            company_url = st.text_input(txt('company_website'), key='target_company_website', placeholder='https://company.com')
            if company_url:
                st.caption(ui_label('Used for cover letters and job/interview preparation context.'))

        st.markdown(f"<div class='workzo-sidebar-section-label'>{html.escape(txt('language'))}</div>", unsafe_allow_html=True)
        try:
            langs = language_options if 'language_options' in globals() and language_options else ['English', 'German', 'Dutch', 'French', 'Spanish', 'Portuguese']
        except Exception:
            langs = ['English', 'German', 'Dutch', 'French', 'Spanish', 'Portuguese']
        cur = st.session_state.get('preferred_language') or st.session_state.get('language') or 'English'
        if cur not in langs:
            cur = 'English' if 'English' in langs else langs[0]
        chosen = st.selectbox(txt('preferred_language'), langs, index=langs.index(cur), key='wz50_preferred_language')
        _wz35_sync_language(chosen)

        st.markdown('---')
        if st.button(txt('edit_setup'), key='wz50_edit_setup', use_container_width=True):
            st.session_state['onboarding_complete'] = False
            st.session_state['page'] = 'onboarding'
            st.session_state['nav_page'] = 'onboarding'
            try:
                st.query_params['page'] = 'onboarding'
            except Exception:
                pass
            _wz50_save_state()
            st.rerun()

        with st.expander('Founder analytics', expanded=False):
            founder_pin = None
            try:
                founder_pin = (os.getenv('FOUNDER_PIN') or get_streamlit_secret('FOUNDER_PIN'))
            except Exception:
                founder_pin = os.getenv('FOUNDER_PIN') if 'os' in globals() else None
            if founder_pin:
                pin = st.text_input('Founder PIN', type='password', key='wz50_founder_pin')
                if pin == founder_pin:
                    st.session_state['founder_unlocked'] = True
                    st.success('Founder mode unlocked.')
            else:
                st.caption('FOUNDER_PIN not configured. Temporary founder access for local testing.')
                if st.text_input('Temporary founder PIN', type='password', key='wz50_temp_pin'):
                    st.session_state['founder_unlocked'] = True
            if st.session_state.get('founder_unlocked'):
                if st.button('Open founder analytics', key='wz50_founder_nav', use_container_width=True):
                    _wz35_go('founder_dashboard')


def _wz50_current_step(progress):
    if not progress['cv_uploaded']:
        return 0
    if not progress['cv_improved']:
        return 1
    if not progress['job_matched']:
        return 2
    if not progress['prepared']:
        return 3
    return 4


def _wz50_dashboard_home():
    _wz50_load_state()
    _wz35_remember_scores()
    _wz35_force_scroll_top()
    _wz35_css()

    progress = _wz50_progress_state()
    _wz50_track_progress(progress)

    cv_exists = progress['cv_uploaded']
    resume_score = _wz35_score('cv_score_value', 'resume_score', 'resume_quality_score', '_best_cv_score_value', default=76 if cv_exists else 0)
    ats_score = _wz35_score('ats_score_value', 'ats_score', '_best_ats_score_value', default=70 if cv_exists else 0)
    interview_score = _wz35_score('interview_score', 'interview_readiness', '_best_interview_score', default=40 if cv_exists else 0)
    country = st.session_state.get('country') or st.session_state.get('target_country') or 'Not set'
    language = st.session_state.get('preferred_language') or st.session_state.get('language') or 'English'

    # Smart next action uses strict progress, not accidental score presence.
    if not progress['cv_uploaded']:
        next_action = {'title':'Start with your CV', 'copy':'Upload or create your CV first so WorkZo can guide the next steps.', 'button':'Add CV', 'target':'onboarding', 'extra':{}}
    elif not progress['cv_improved']:
        next_action = {'title':'Improve your CV', 'copy':'Make your CV stronger before job matching. Tailor structure, keywords, and achievements.', 'button':'Improve CV', 'target':'cv_documents', 'extra':{'document_tools_mode':'Improve / Update CV'}}
    elif not progress['job_matched']:
        next_action = {'title':'Find matching jobs', 'copy':'Search jobs for your selected country and choose one role to analyze.', 'button':'Open Job Match', 'target':'job_assist', 'extra':{'job_assist_mode_key':'find'}}
    elif not progress['prepared']:
        next_action = {'title':'Prepare for this job', 'copy':'Create cover letter/application prep and practice your strongest answers.', 'button':'Prepare this job', 'target':'job_assist', 'extra':{'job_assist_mode_key':'prepare'}}
    else:
        next_action = {'title':'Ready to apply', 'copy':'Your core application flow is complete. Apply, track the result, and practice with Work-O-Bot.', 'button':'Practice with Work-O-Bot', 'target':'workobot', 'extra':{}}

    st.markdown(f"""
    <div class='wz35-hero'>
      <div class='wz35-kicker'>{_wz35_escape(txt('workzo_command_center'))}</div>
      <div class='wz35-title'>{_wz35_escape(txt('next_best_move_clear'))}</div>
      <div class='wz35-sub'>{_wz35_escape(txt('next_best_move_copy'))}</div>
      <div class='wz35-chip-row'>
        <span class='wz35-chip'>{_wz35_escape(country)}</span>
        <span class='wz35-chip'>{_wz35_escape(language)}</span>
        <span class='wz35-chip'>{_wz35_escape(ui_label('CV ready') if progress['cv_uploaded'] else ui_label('CV missing'))}</span>
        <span class='wz35-chip'>{_wz35_escape(ui_label('CV improved') if progress['cv_improved'] else ui_label('CV not improved'))}</span>
        <span class='wz35-chip'>{_wz35_escape(ui_label('Job matched') if progress['job_matched'] else ui_label('Job not matched'))}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class='wz35-next'>
      <div class='wz35-next-label'>{_wz35_escape(txt('recommended_next_step'))}</div>
      <div class='wz35-next-title'>{_wz35_escape(next_action['title'])}</div>
      <div class='wz35-next-copy'>{_wz35_escape(next_action['copy'])}</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button(next_action['button'], key='wz50_primary_action', use_container_width=True):
        _wz35_go(next_action['target'], next_action.get('extra'))

    st.markdown('### ' + txt('readiness_overview'))
    c1, c2, c3 = st.columns(3)
    with c1:
        _wz35_rate_card(txt('resume_score'), resume_score, ui_label('Clarity, structure, achievements, and overall CV quality.'), missing=not cv_exists)
    with c2:
        _wz35_rate_card(txt('ats_score'), ats_score, ui_label('Scanner-friendly formatting, role keywords, sections, and parsing safety.'), missing=not cv_exists)
    with c3:
        _wz35_rate_card(txt('interview_readiness'), interview_score, ui_label('How ready you are to explain your CV and job fit clearly.'), missing=not cv_exists)

    st.markdown('### ' + txt('smart_actions'))
    a1, a2, a3, a4 = st.columns(4)
    with a1:
        _wz35_action_card(txt('improve_cv'), ui_label('Use this to improve your CV or tailor it to a specific job.'), txt('open_cv_tools'), 'cv_documents', 'wz50_action_cv', {'document_tools_mode':'Improve / Update CV'})
    with a2:
        _wz35_action_card(txt('job_match'), ui_label('Search jobs for the selected country, then analyze one job description for fit.'), txt('open_job_assist'), 'job_assist', 'wz50_action_jobs', {'job_assist_mode_key':'find'})
    with a3:
        _wz35_action_card(txt('cover_letter'), ui_label('Use CV, job description, and company context to create a focused cover letter.'), txt('create_cover_letter'), 'cv_documents', 'wz50_action_cover', {'document_tools_mode':'Cover Letter Generator + Language'})
    with a4:
        _wz35_action_card('Work-O-Bot', ui_label('Ask career questions or practice interview answers in your selected language.'), txt('ask_workobot'), 'workobot', 'wz50_action_bot')

    st.markdown('### ' + txt('application_progress'))
    st.caption(ui_label('Visual tracker only. Use Smart actions above to continue.'))
    flow = [
        ('1. CV uploaded', progress['cv_uploaded'], txt('completed') if progress['cv_uploaded'] else ui_label('Add or upload CV')),
        ('2. CV improved', progress['cv_improved'], txt('completed') if progress['cv_improved'] else ui_label('Improve or tailor your CV')),
        ('3. Job matched', progress['job_matched'], txt('completed') if progress['job_matched'] else ui_label('Find matching jobs')),
        ('4. Prepared for job', progress['prepared'], txt('completed') if progress['prepared'] else ui_label('Prepare cover letter and interview notes')),
    ]
    try:
        current = next((i for i, (_, done, _) in enumerate(flow) if not done), len(flow) - 1)
    except Exception:
        current = 0
    cols = st.columns(4)
    for i, (label, done, note) in enumerate(flow):
        with cols[i]:
            _wz35_flow_card(label, done, (not done and current == i), note)
    st.caption(ui_label('Scores are guidance only. WorkZo should not invent skills, company facts, language level, salary, or experience.'))
    _wz35_remember_scores()
    _wz50_save_state()


def show_dashboard():
    _wz50_load_state()
    _wz35_sync_language()
    _wz35_force_scroll_top()
    page_key = st.session_state.get('nav_page') or st.session_state.get('page') or 'dashboard'
    page_key = {'landing':'dashboard', 'bot':'workobot', 'interview':'workobot', 'jobs':'job_assist', 'improve_cv':'cv_documents'}.get(page_key, page_key)
    if page_key == 'interview_practice':
        page_key = 'workobot'
    if page_key not in {'dashboard', 'cv_documents', 'job_assist', 'workobot', 'founder_dashboard'}:
        page_key = 'dashboard'
    st.session_state['page'] = page_key
    st.session_state['nav_page'] = page_key
    try:
        _wz28_top(True)
    except Exception:
        pass
    _wz50_sidebar(page_key)

    if page_key == 'dashboard':
        _wz50_dashboard_home()
    elif page_key == 'cv_documents':
        _wz35_css()
        show_document_tools()
    elif page_key == 'job_assist':
        _wz35_css()
        try:
            _wz28_job_assist_page()
        except Exception:
            st.subheader(txt('job_assist'))
            tab1, tab2, tab3 = st.tabs([txt('find_jobs'), txt('understand_job'), txt('prepare_this_job')])
            with tab1: st.info('Job search module could not be loaded.')
            with tab2: st.info('Understand Job module could not be loaded.')
            with tab3: st.info('Prepare module could not be loaded.')
    elif page_key == 'workobot':
        _wz35_css()
        show_workobot()
    elif page_key == 'founder_dashboard':
        _wz35_css()
        if st.session_state.get('founder_unlocked') and callable(globals().get('render_founder_dashboard')):
            render_founder_dashboard()
        else:
            st.warning('Founder mode is locked. Enter the Founder PIN in the sidebar.')

    _wz35_remember_scores()
    _wz50_save_state()


# =========================================================
# WorkZo v51 - Enable classic Job Assist and disable AI Job Application Assistant
# This final override intentionally runs last.
# - Restores Job Assist: Find Jobs | Understand Job | Prepare this Job
# - Removes the AI Job Application Assistant wrapper from the active route
# - Keeps existing dashboard, sidebar, memory, progress, Work-O-Bot, and CV tools
# =========================================================
def _wz51_safe_label(text_value, fallback=None):
    try:
        if callable(globals().get("txt")):
            translated = txt(str(text_value))
            if translated and translated != str(text_value):
                return translated
    except Exception:
        pass
    try:
        if callable(globals().get("ui_label")):
            return ui_label(str(fallback or text_value))
    except Exception:
        pass
    return str(fallback or text_value)


def _wz51_go(page_key, extra=None):
    try:
        if extra:
            for k, v in extra.items():
                st.session_state[k] = v
        st.session_state["page"] = page_key
        st.session_state["nav_page"] = page_key
        if callable(globals().get("request_scroll_to_top")):
            request_scroll_to_top()
        st.rerun()
    except Exception:
        st.session_state["page"] = page_key
        st.session_state["nav_page"] = page_key


def _wz51_extract_roles_from_cv(cv_text):
    cv_text = str(cv_text or "")
    roles = []
    for key in ["target_role", "detected_target_role", "current_role_detected"]:
        val = st.session_state.get(key)
        if isinstance(val, str) and val.strip():
            roles.append(val.strip())
    first_lines = [x.strip() for x in cv_text.splitlines() if x.strip()][:8]
    for line in first_lines:
        low = line.lower()
        if any(word in low for word in ["engineer", "developer", "analyst", "scientist", "support", "manager", "consultant", "specialist", "designer"]):
            clean = re.sub(r"[|•].*$", "", line).strip(" -–—")
            if 3 <= len(clean) <= 70:
                roles.append(clean)
    # sensible fallback
    if not roles:
        roles = ["Data Analyst", "IT Support Specialist", "Customer Support Specialist"]
    deduped = []
    seen = set()
    for r in roles:
        k = r.casefold()
        if k not in seen:
            seen.add(k)
            deduped.append(r)
    return deduped[:6]


def _wz51_simple_job_card(job, idx=0):
    title = html.escape(str(job.get("title") or job.get("job_title") or "Job opening"))
    company = html.escape(str(job.get("company") or job.get("employer_name") or "Company not listed"))
    location = html.escape(str(job.get("location") or job.get("job_location") or "Location not listed"))
    source = html.escape(str(job.get("source") or job.get("publisher") or "Live source"))
    url = str(job.get("url") or job.get("redirect_url") or job.get("job_apply_link") or "")
    st.markdown(f"""
    <div class='next-action-card' style='margin:10px 0;'>
      <div class='next-action-label'>{source}</div>
      <div class='next-action-title'>{title}</div>
      <div class='next-action-copy'>{company} · {location}</div>
    </div>
    """, unsafe_allow_html=True)
    if url:
        st.link_button(_wz51_safe_label("View job", "View job"), url, use_container_width=False)


def _wz51_render_find_jobs():
    """Smarter Job Assist > Find Jobs page. Only Job Assist is changed in this v54 patch."""
    st.markdown("### " + _wz51_safe_label("find_jobs", "Find Jobs"))

    cv_text = str(st.session_state.get("cv_text") or st.session_state.get("clean_structured_cv_text") or "")
    user_country = str(st.session_state.get("country") or st.session_state.get("migration_country") or "").strip() or "Global"
    suggested_roles = _wz51_extract_roles_from_cv(cv_text)
    default_titles = ", ".join(suggested_roles[:3]) or str(st.session_state.get("target_role") or "")

    def _wz54_country_options():
        countries = []
        try:
            countries.extend([str(x) for x in (globals().get("country_options") or []) if str(x).strip()])
        except Exception:
            pass
        try:
            pc = globals().get("pycountry")
            if pc is not None:
                countries.extend([c.name for c in pc.countries if getattr(c, "name", "")])
        except Exception:
            pass
        fallback = ["Global", "Germany", "India", "United States", "United Kingdom", "Canada", "Australia", "Netherlands", "France", "Austria", "Switzerland", "Singapore", "United Arab Emirates", "Ireland", "Spain", "Italy", "Sweden", "Denmark", "Norway", "Finland", "Belgium", "Poland", "Portugal", "New Zealand", "South Africa"]
        countries.extend(fallback)
        clean = []
        seen = set()
        for c in countries:
            c = str(c).strip()
            if not c:
                continue
            key = c.casefold()
            if key not in seen:
                seen.add(key)
                clean.append(c)
        return ["Global"] + sorted([c for c in clean if c.casefold() != "global"], key=lambda x: x.lower())

    def _wz54_city_options(country_name: str):
        try:
            fn = globals().get("fetch_country_cities")
            if callable(fn):
                cities = fn(country_name) or []
                return [str(c).strip() for c in cities if str(c).strip()]
        except Exception:
            pass
        return []

    def _wz54_country_aliases(country_name: str):
        low = (country_name or "").strip().lower()
        aliases = {low}
        mapping = {
            "germany": ["germany", "deutschland", "de"],
            "india": ["india", "in"],
            "united states": ["united states", "usa", "u.s.", "u.s.a.", "us"],
            "united kingdom": ["united kingdom", "uk", "great britain", "england"],
            "canada": ["canada", "ca"],
            "australia": ["australia", "au"],
            "netherlands": ["netherlands", "holland", "nl"],
            "france": ["france", "fr"],
            "austria": ["austria", "at"],
            "switzerland": ["switzerland", "ch", "schweiz", "suisse"],
            "singapore": ["singapore", "sg"],
        }
        aliases.update(mapping.get(low, []))
        return {a for a in aliases if a}

    def _wz54_filter_jobs(jobs, country_name, city_name=""):
        if not jobs or not country_name or country_name == "Global":
            return jobs or []
        selected_aliases = _wz54_country_aliases(country_name)
        city = (city_name or "").strip().lower()
        common_wrong = {
            "germany", "deutschland", "india", "united states", "usa", "u.s.", "u.s.a.", "canada", "united kingdom", "uk", "australia", "netherlands", "france", "austria", "switzerland", "singapore"
        } - selected_aliases
        filtered = []
        for job in jobs:
            try:
                loc = str(job.get("location") or job.get("job_location") or job.get("candidate_required_location") or "")
                title = str(job.get("title") or job.get("job_title") or "")
                company = str(job.get("company") or job.get("employer_name") or "")
                summary = str(job.get("summary") or job.get("description") or "")
                hay = " ".join([loc, title, company, summary]).lower()
                loc_low = loc.lower()
                if any(w and w in loc_low for w in common_wrong):
                    continue
                if city and city in hay:
                    filtered.append(job); continue
                if any(a and a in hay for a in selected_aliases):
                    filtered.append(job); continue
                if "remote" in loc_low and not any(w and w in loc_low for w in common_wrong):
                    filtered.append(job); continue
            except Exception:
                continue
        return filtered

    # Safe defaults BEFORE widgets render. Do not overwrite widget keys later.
    if "job_assist_target_titles" not in st.session_state:
        st.session_state["job_assist_target_titles"] = default_titles
    if "job_assist_preferred_country_v54" not in st.session_state:
        st.session_state["job_assist_preferred_country_v54"] = user_country if user_country else "Global"
    if "job_assist_region_city_text_v54" not in st.session_state:
        st.session_state["job_assist_region_city_text_v54"] = ""

    st.markdown(f"""
    <div class='next-action-card' style='margin-top:4px;'>
      <div class='next-action-label'>{html.escape(_wz51_safe_label('Smart job search', 'Smart job search'))}</div>
      <div class='next-action-title'>{html.escape(_wz51_safe_label('Search by role + country + city, then analyze the best job', 'Search by role + country + city, then analyze the best job'))}</div>
      <div class='next-action-copy'>{html.escape(_wz51_safe_label('WorkZo uses your CV signals and location context to find tighter matches. Choose the country, then add a city/region only if needed.', 'WorkZo uses your CV signals and location context to find tighter matches. Choose the country, then add a city/region only if needed.'))}</div>
    </div>
    """, unsafe_allow_html=True)

    countries = _wz54_country_options()
    current_country = st.session_state.get("job_assist_preferred_country_v54") or user_country or "Global"
    if current_country not in countries:
        countries.insert(1, current_country)

    row1a, row1b = st.columns([1.05, 0.95])
    with row1a:
        target_titles = st.text_input(
            _wz51_safe_label("Target job titles", "Target job titles"),
            placeholder="Data Analyst, IT Support, Customer Success",
            key="job_assist_target_titles",
            help=_wz51_safe_label("Use 1-3 role titles. WorkZo will search around these titles instead of using your full CV text.", "Use 1-3 role titles. WorkZo will search around these titles instead of using your full CV text."),
        )
    with row1b:
        preferred_country = st.selectbox(
            _wz51_safe_label("Preferred country", "Preferred country"),
            countries,
            index=countries.index(current_country) if current_country in countries else 0,
            key="job_assist_preferred_country_v54",
            help=_wz51_safe_label("Choose the country where you want to search jobs.", "Choose the country where you want to search jobs."),
        )

    cities = _wz54_city_options(preferred_country) if preferred_country != "Global" else []
    city_text = st.text_input(
        _wz51_safe_label("Region / city", "Region / city"),
        placeholder="Berlin, Chennai, Frankfurt, Remote...",
        key="job_assist_region_city_text_v54",
        help=_wz51_safe_label("Start typing a city/region. Suggestions appear when available.", "Start typing a city/region. Suggestions appear when available."),
    )
    city_query = (city_text or "").strip().lower()
    final_city = ""
    city_verified = False
    if city_query and cities:
        matches = [c for c in cities if c.lower().startswith(city_query)][:12]
        if matches:
            city_choice = st.selectbox(
                _wz51_safe_label("City suggestions", "City suggestions"),
                [""] + matches,
                index=0,
                key="job_assist_city_suggestion_v54",
                help=_wz51_safe_label("Select a suggestion, or leave empty to search the whole country.", "Select a suggestion, or leave empty to search the whole country."),
            )
            final_city = city_choice.strip()
            city_verified = bool(final_city)
        else:
            st.caption(_wz51_safe_label("City not recognized. WorkZo will search the selected country instead.", "City not recognized. WorkZo will search the selected country instead."))
    elif city_query:
        st.caption(_wz51_safe_label("City suggestions are unavailable for this country. WorkZo will search the selected country instead.", "City suggestions are unavailable for this country. WorkZo will search the selected country instead."))

    roles_preview = [x.strip() for x in re.split(r"[,;\n/]", target_titles or "") if x.strip()]
    if not roles_preview and suggested_roles:
        roles_preview = suggested_roles[:3]
    role_chips = "".join(f"<span class='workzo-dashboard-chip'>{html.escape(r)}</span>" for r in roles_preview[:4]) or f"<span class='workzo-dashboard-chip'>{html.escape(_wz51_safe_label('Add a target title', 'Add a target title'))}</span>"
    location_label = ", ".join([x for x in [final_city, preferred_country if preferred_country != "Global" else ""] if x]) or (preferred_country if preferred_country != "Global" else "Global")
    st.markdown(f"""
    <div class='workzo-mini-note' style='margin: 8px 0 14px 0;'>
        {_wz51_safe_label('Search context', 'Search context')}: {role_chips}
        <span class='workzo-dashboard-chip'>📍 {html.escape(location_label)}</span>
    </div>
    """, unsafe_allow_html=True)

    with st.expander(_wz51_safe_label("Review CV signals used for matching", "Review CV signals used for matching"), expanded=False):
        try:
            cv_profile = build_job_matching_profile(cv_text) if callable(globals().get("build_job_matching_profile")) else cv_text
        except Exception:
            cv_profile = cv_text
        st.text_area(_wz51_safe_label("CV matching profile", "CV matching profile"), value=cv_profile, height=220, key="job_assist_cv_review_v54")

    find_col, tip_col = st.columns([0.45, 1])
    with find_col:
        find_clicked = st.button(_wz51_safe_label("Find smart matches", "Find smart matches"), key="btn_find_jobs_v54", use_container_width=True)
    with tip_col:
        st.caption(_wz51_safe_label("Tip: after finding jobs, open one job and use Understand Job before improving your CV.", "Tip: after finding jobs, open one job and use Understand Job before improving your CV."))

    if find_clicked:
        roles = [x.strip() for x in re.split(r"[,;\n/]", target_titles or "") if x.strip()] or suggested_roles
        if not roles:
            st.warning(_wz51_safe_label("Please add at least one target job title.", "Please add at least one target job title."))
        else:
            search_location = ", ".join([x for x in [final_city, preferred_country if preferred_country != "Global" else ""] if x]).strip() or preferred_country
            # If the typed city is not selected from suggestions, search the whole selected country.
            # This prevents valid country-level jobs from being hidden by an unrecognized city string.
            if not final_city and preferred_country != "Global":
                search_location = preferred_country
            # Store search memory in non-widget keys only.
            st.session_state["last_job_search_target_titles"] = ", ".join(roles[:6])
            st.session_state["last_job_search_location_text"] = search_location
            st.session_state["last_job_search_country"] = preferred_country
            try:
                if callable(globals().get("track_button_click")):
                    track_button_click("Find Jobs", "Job Assist", {"country": preferred_country, "location": search_location, "roles": roles[:3]})
            except Exception:
                pass

            with st.status(_wz51_safe_label("Searching and ranking jobs...", "Searching and ranking jobs..."), expanded=True) as status:
                st.write(_wz51_safe_label("Building focused search terms from your CV and target titles...", "Building focused search terms from your CV and target titles..."))
                jobs = []
                try:
                    if callable(globals().get("fetch_live_jobs_global")):
                        jobs = fetch_live_jobs_global(preferred_country, roles, search_location or preferred_country, st.session_state.get("user_status", "")) or []
                except Exception as exc:
                    st.warning(f"Live job source error: {exc}")
                jobs = _wz54_filter_jobs(jobs, preferred_country, final_city if city_verified else "")
                st.write(_wz51_safe_label("Ranking results for your CV and location...", "Ranking results for your CV and location..."))
                try:
                    if jobs and callable(globals().get("curate_job_matches")):
                        jobs = curate_job_matches(jobs, cv_text, {"job_titles": roles, "search_queries": roles, "location": search_location}, preferred_country, st.session_state.get("user_status", ""), limit=25)
                        jobs = _wz54_filter_jobs(jobs, preferred_country, final_city if city_verified else "")
                except Exception:
                    pass
                st.session_state["latest_curated_jobs"] = jobs
                st.session_state["workzo_progress_job_matched"] = bool(jobs)
                status.update(label=_wz51_safe_label("Job search complete", "Job search complete"), state="complete", expanded=False)

    jobs = st.session_state.get("latest_curated_jobs") or []
    last_titles = st.session_state.get("last_job_search_target_titles") or target_titles or default_titles or "jobs"
    last_location = st.session_state.get("last_job_search_location_text") or location_label

    if jobs:
        st.markdown("#### " + _wz51_safe_label("Best matches found", "Best matches found"))
        st.caption(_wz51_safe_label("Open the most relevant job, then paste its description in Understand Job to get a real fit score.", "Open the most relevant job, then paste its description in Understand Job to get a real fit score."))
        try:
            if callable(globals().get("render_curated_job_matches")):
                render_curated_job_matches(jobs, preferred_country)
            else:
                for i, job in enumerate(jobs[:12]):
                    _wz51_simple_job_card(job, i)
        except Exception:
            for i, job in enumerate(jobs[:12]):
                _wz51_simple_job_card(job, i)
    else:
        st.info(_wz51_safe_label("No saved job results yet. Search with a specific role title and preferred country/city.", "No saved job results yet. Search with a specific role title and preferred country/city."))
        role_for_link = (last_titles or "jobs").split(",")[0].strip()
        q = urllib.parse.quote_plus(f"{role_for_link} {last_location}")
        st.markdown("#### " + _wz51_safe_label("Quick search links", "Quick search links"))
        st.caption(_wz51_safe_label("Use these if live APIs return too few jobs during testing.", "Use these if live APIs return too few jobs during testing."))
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.link_button("LinkedIn", f"https://www.linkedin.com/jobs/search/?keywords={q}")
        with c2: st.link_button("Indeed", f"https://www.indeed.com/jobs?q={q}")
        with c3: st.link_button("Google Jobs", f"https://www.google.com/search?q={q}+jobs")
        with c4: st.link_button("RemoteOK", f"https://remoteok.com/remote-{urllib.parse.quote_plus(role_for_link)}-jobs")

def _wz51_render_understand_job():
    st.markdown("### " + _wz51_safe_label("understand_job", "Understand Job"))
    st.caption(_wz51_safe_label("Paste a job description. WorkZo checks fit, risks, missing keywords, and next actions.", "Paste a job description. WorkZo checks fit, risks, missing keywords, and next actions."))
    default_jd = st.session_state.get("last_understand_job_description") or st.session_state.get("current_job_description") or st.session_state.get("improve_cv_for_job_desc") or ""
    jd = st.text_area(_wz51_safe_label("Paste the job description", "Paste the job description"), value=default_jd, height=260, key="job_desc_v51_understand")
    if st.button(_wz51_safe_label("Analyze Job Fit", "Analyze Job Fit"), key="btn_understand_job_v51", use_container_width=True):
        if not jd.strip():
            st.warning(_wz51_safe_label("Please paste a job description first.", "Please paste a job description first."))
        else:
            cv_text = str(st.session_state.get("cv_text") or st.session_state.get("clean_structured_cv_text") or "")
            score, matched, missing = _wz51_keyword_match(cv_text, jd)
            st.session_state["current_job_description"] = jd
            st.session_state["last_understand_job_description"] = jd
            st.session_state["improve_cv_for_job_desc"] = jd
            st.session_state["latest_job_analysis"] = {"score": score, "matched": matched, "missing": missing, "source": "job_assist_v51"}
            st.session_state["job_fit_score_value"] = score
            st.session_state["workzo_progress_job_matched"] = True
            try:
                if callable(globals().get("track_event")):
                    track_event("job_analyzed", "Job Assist", {"fit_score": score})
            except Exception:
                pass
            st.success(_wz51_safe_label("Job analyzed. You can now tailor the CV or prepare the application.", "Job analyzed. You can now tailor the CV or prepare the application."))

    analysis = st.session_state.get("latest_job_analysis") or {}
    if jd.strip() or analysis:
        score = int(analysis.get("score") or st.session_state.get("job_fit_score_value") or 0)
        matched = analysis.get("matched") or []
        missing = analysis.get("missing") or []
        st.markdown("#### " + _wz51_safe_label("Job Fit", "Job Fit"))
        c1, c2, c3 = st.columns(3)
        c1.metric(_wz51_safe_label("Fit score", "Fit score"), f"{score}%" if score else "—")
        c2.metric(_wz51_safe_label("Matched keywords", "Matched keywords"), len(matched))
        c3.metric(_wz51_safe_label("Missing keywords", "Missing keywords"), len(missing))
        if missing:
            st.warning(_wz51_safe_label("Missing or weak keywords. Add them only if they are truthful.", "Missing or weak keywords. Add them only if they are truthful."))
            st.write(", ".join([html.escape(str(x)) for x in missing[:15]]))
        if matched:
            st.success(_wz51_safe_label("Your CV already shows some relevant signals.", "Your CV already shows some relevant signals."))
        a, b = st.columns(2)
        with a:
            if st.button(_wz51_safe_label("Improve CV for this job", "Improve CV for this job"), key="wz51_understand_improve", use_container_width=True):
                _wz51_go("cv_documents", {"document_tools_mode": "Improve CV for a Job", "improve_cv_for_job_desc": jd})
        with b:
            if st.button(_wz51_safe_label("Prepare for this job", "Prepare for this job"), key="wz51_understand_prepare", use_container_width=True):
                st.session_state["job_assist_mode_key"] = "prepare"
                st.rerun()


def _wz51_render_prepare_job():
    st.markdown("### " + _wz51_safe_label("prepare_this_job", "Prepare for this Job"))
    st.caption(_wz51_safe_label("Create a focused application and interview preparation plan from your CV and job context.", "Create a focused application and interview preparation plan from your CV and job context."))
    c1, c2 = st.columns(2)
    with c1:
        company = st.text_input(_wz51_safe_label("Target company", "Target company"), value="", key="wz51_target_company_clean", placeholder=_wz51_safe_label("Example: Siemens, SAP, Google", "Example: Siemens, SAP, Google"))
    with c2:
        role = st.text_input(_wz51_safe_label("Target role", "Target role"), value="", key="wz51_target_role_clean", placeholder=_wz51_safe_label("Example: Data Analyst, IT Support", "Example: Data Analyst, IT Support"))
    website = st.text_input(_wz51_safe_label("Company website / careers page", "Company website / careers page"), value="", key="wz51_company_website_clean", placeholder="https://company.com")
    jd = st.text_area(_wz51_safe_label("Job description", "Job description"), value=st.session_state.get("last_understand_job_description", ""), height=220, key="wz51_prepare_jd")
    if st.button(_wz51_safe_label("Prepare application", "Prepare application"), key="wz51_prepare_application", use_container_width=True):
        st.session_state["target_company"] = company.strip()
        st.session_state["target_job_title"] = role.strip()
        st.session_state["company_website"] = website.strip()
        st.session_state["current_job_description"] = jd.strip()
        st.session_state["last_prepare_job_description"] = jd.strip()
        cv_text = str(st.session_state.get("cv_text") or st.session_state.get("clean_structured_cv_text") or "")
        prompt = f"""
You are WorkZo AI. Create a practical, honest job application preparation plan.
Do not invent company facts, skills, salary, language level, or experience.
Preferred language: {st.session_state.get('preferred_language','English')}
Country: {st.session_state.get('country','')}
Company: {company}
Role: {role}
Website: {website}
CV summary/text:
{cv_text[:4000]}
Job description:
{jd[:4000]}
Return concise sections: application focus, CV tailoring points, cover letter angle, interview stories, risks/missing proof, next actions.
"""
        result = ""
        try:
            if callable(globals().get("run_ai_prompt")):
                result = run_ai_prompt(prompt)
        except Exception as exc:
            result = f"Preparation could not use AI right now. Review CV-job alignment manually. Error: {exc}"
        if not result:
            result = "Application focus: tailor your CV to the job description, prepare 3 examples using STAR, and write a cover letter using only truthful company/context details."
        st.session_state["latest_application_prep"] = result
        st.session_state["workzo_progress_prepared"] = True
        try:
            if callable(globals().get("track_event")):
                track_event("application_prepared", "Job Assist", {"company": company, "role": role})
        except Exception:
            pass
        st.success(_wz51_safe_label("Preparation created.", "Preparation created."))
    if st.session_state.get("latest_application_prep"):
        st.markdown("#### " + _wz51_safe_label("Preparation plan", "Preparation plan"))
        st.markdown(str(st.session_state.get("latest_application_prep")))


def _wz51_render_job_assist_page():
    try:
        _wz35_css()
    except Exception:
        pass
    st.subheader(_wz51_safe_label("job_assist", "Job Assist"))
    mode_labels = {
        "find": _wz51_safe_label("find_jobs", "Find Jobs"),
        "understand": _wz51_safe_label("understand_job", "Understand Job"),
        "prepare": _wz51_safe_label("prepare_this_job", "Prepare for this Job"),
    }
    if st.session_state.get("job_assist_mode_key") not in mode_labels:
        st.session_state["job_assist_mode_key"] = "find"
    mode = st.radio(
        "Job Assist mode",
        ["find", "understand", "prepare"],
        horizontal=True,
        format_func=lambda x: mode_labels.get(x, x),
        key="job_assist_mode_key",
        label_visibility="collapsed",
    )
    st.divider()
    if mode == "find":
        _wz51_render_find_jobs()
    elif mode == "understand":
        _wz51_render_understand_job()
    else:
        _wz51_render_prepare_job()


# Final v51 router override: keeps Dashboard/CV/Work-O-Bot but uses classic Job Assist.
def show_dashboard():
    try:
        _wz35_load_state()
    except Exception:
        pass
    try:
        _wz35_sync_language()
    except Exception:
        pass
    try:
        _wz35_force_scroll_top()
    except Exception:
        pass

    page_key = st.session_state.get("nav_page") or st.session_state.get("page") or "dashboard"
    page_key = {"landing":"dashboard", "bot":"workobot", "interview":"workobot", "jobs":"job_assist", "improve_cv":"cv_documents"}.get(page_key, page_key)
    if page_key == "interview_practice":
        page_key = "workobot"
    if page_key not in {"dashboard", "cv_documents", "job_assist", "workobot", "founder_dashboard"}:
        page_key = "dashboard"
    st.session_state["page"] = page_key
    st.session_state["nav_page"] = page_key

    try:
        _wz28_top(True)
    except Exception:
        pass
    try:
        _wz35_sidebar(page_key)
    except Exception:
        pass

    if page_key == "dashboard":
        _wz35_dashboard_home()
    elif page_key == "cv_documents":
        try:
            _wz35_css()
        except Exception:
            pass
        show_document_tools()
    elif page_key == "job_assist":
        _wz51_render_job_assist_page()
    elif page_key == "workobot":
        try:
            _wz35_css()
        except Exception:
            pass
        show_workobot()
    elif page_key == "founder_dashboard":
        if st.session_state.get("founder_unlocked") and callable(globals().get("render_founder_dashboard")):
            render_founder_dashboard()
        else:
            st.warning("Founder dashboard is locked.")

    try:
        _wz35_remember_scores()
        _wz35_save_state()
    except Exception:
        pass

# =========================================================
# WorkZo v55 - smarter Understand Job only
# Scope: replaces only the Understand Job renderer used inside Job Assist.
# Keeps all other dashboard/pages unchanged.
# =========================================================
def _wz55_country_iso(country_name: str) -> str:
    try:
        name = str(country_name or '').strip()
        if not name or name.lower() == 'global':
            return ''
        aliases = {
            'usa': 'US', 'united states': 'US', 'united states of america': 'US',
            'uk': 'GB', 'united kingdom': 'GB', 'england': 'GB',
            'germany': 'DE', 'deutschland': 'DE', 'india': 'IN', 'canada': 'CA',
            'netherlands': 'NL', 'austria': 'AT', 'switzerland': 'CH', 'france': 'FR',
            'australia': 'AU', 'singapore': 'SG', 'ireland': 'IE', 'spain': 'ES',
            'italy': 'IT', 'sweden': 'SE', 'denmark': 'DK', 'norway': 'NO', 'finland': 'FI'
        }
        low = name.lower()
        if low in aliases:
            return aliases[low]
        try:
            import pycountry as _pycountry
            c = _pycountry.countries.lookup(name)
            return getattr(c, 'alpha_2', '') or ''
        except Exception:
            return ''
    except Exception:
        return ''


def _wz55_city_bbox(city: str, country_iso: str = '') -> dict:
    """Return a small bounding box for the city when available.
    Uses geonamescache if installed; otherwise falls back gracefully.
    """
    try:
        city_clean = str(city or '').strip()
        if not city_clean:
            return {}
        try:
            import geonamescache as _geonamescache
            gc = _geonamescache.GeonamesCache()
            cities = gc.get_cities()
            city_low = city_clean.lower()
            iso = str(country_iso or '').upper()
            best = None
            for item in cities.values():
                if str(item.get('name', '')).lower() == city_low and (not iso or item.get('countrycode') == iso):
                    best = item
                    break
            if not best:
                for item in cities.values():
                    if str(item.get('name', '')).lower().startswith(city_low) and (not iso or item.get('countrycode') == iso):
                        best = item
                        break
            if best:
                lat = float(best.get('latitude'))
                lon = float(best.get('longitude'))
                pad = 0.45
                return {'city': best.get('name', city_clean), 'country_iso': best.get('countrycode', iso), 'lat': lat, 'lon': lon, 'bbox': [round(lon-pad, 4), round(lat-pad, 4), round(lon+pad, 4), round(lat+pad, 4)]}
        except Exception:
            pass
        fallback = {
            ('munich','DE'):(48.1351,11.5820), ('berlin','DE'):(52.5200,13.4050), ('frankfurt','DE'):(50.1109,8.6821),
            ('nuremberg','DE'):(49.4521,11.0767), ('wurzburg','DE'):(49.7913,9.9534), ('würzburg','DE'):(49.7913,9.9534),
            ('chennai','IN'):(13.0827,80.2707), ('bangalore','IN'):(12.9716,77.5946), ('bengaluru','IN'):(12.9716,77.5946),
            ('london','GB'):(51.5072,-0.1276), ('toronto','CA'):(43.6532,-79.3832), ('amsterdam','NL'):(52.3676,4.9041)
        }
        point = fallback.get((city_clean.lower(), str(country_iso or '').upper())) or fallback.get((city_clean.lower(), ''))
        if point:
            lat, lon = point
            pad = 0.45
            return {'city': city_clean, 'country_iso': country_iso, 'lat': lat, 'lon': lon, 'bbox': [round(lon-pad, 4), round(lat-pad, 4), round(lon+pad, 4), round(lat+pad, 4)]}
    except Exception:
        pass
    return {}


def _wz55_clean_list(value, limit=6):
    if isinstance(value, list):
        items = value
    elif isinstance(value, str):
        items = re.split(r'[,;\n•-]+', value)
    else:
        items = []
    out = []
    for item in items:
        text = re.sub(r'\s+', ' ', str(item or '')).strip(' -•')
        if text and text.lower() not in [x.lower() for x in out]:
            out.append(text)
        if len(out) >= limit:
            break
    return out


def _wz55_fallback_job_analysis(cv_text: str, jd: str, country: str, city: str) -> dict:
    score, matched, missing = _wz51_keyword_match(cv_text, jd) if callable(globals().get('_wz51_keyword_match')) else (0, [], [])
    score = max(0, min(100, int(score or 0)))
    verdict = 'Strong apply' if score >= 80 else ('Apply, but tailor first' if score >= 60 else ('Possible, but improve first' if score >= 40 else 'Risky match — review before applying'))
    return {
        'score': score,
        'skill_match': min(100, score + 8) if score else 0,
        'experience_match': score,
        'keyword_match': score,
        'language_match': 0,
        'verdict': verdict,
        'main_reason': 'This is a fast rule-based review based on the CV text and the pasted job description.',
        'matched': matched[:12],
        'missing': missing[:12],
        'strong_signals': matched[:5],
        'main_gaps': missing[:5],
        'requirement_checklist': [{'requirement': x, 'status': 'Matched' if x in matched else 'Weak/Missing', 'evidence': 'Detected in CV' if x in matched else 'Not clearly visible in CV'} for x in (matched[:3] + missing[:5])[:8]],
        'honest_cv_actions': [f'Add proof for {x} only if it is true.' for x in missing[:3]] or ['Mirror the job language using only truthful experience.'],
        'interview_focus': ['Explain your most relevant experience', 'Prepare examples for weak/missing requirements', 'Be honest about tools you are still learning'],
        'apply_decision': verdict,
        'country_market_note': f'Target market: {country or "Not specified"}. City/region: {city or "Not specified"}.',
        'source': 'workzo_v55_fallback'
    }


def _wz55_render_job_analysis_cards(analysis: dict, jd: str, country_iso: str, bbox_data: dict):
    score = int(analysis.get('score') or analysis.get('fit_score') or analysis.get('job_fit_score') or st.session_state.get('job_fit_score_value') or 0)
    verdict = str(analysis.get('verdict') or analysis.get('apply_decision') or ('Run analysis' if not score else 'Review result'))
    main_reason = str(analysis.get('main_reason') or analysis.get('summary') or '')
    skill_match = int(analysis.get('skill_match') or score or 0)
    experience_match = int(analysis.get('experience_match') or score or 0)
    keyword_match = int(analysis.get('keyword_match') or score or 0)
    language_match = analysis.get('language_match')

    st.markdown("#### " + _wz51_safe_label('AI Job Fit Summary', 'AI Job Fit Summary'))
    m1, m2, m3, m4 = st.columns(4)
    m1.metric(_wz51_safe_label('Fit score', 'Fit score'), f'{score}%' if score else '—')
    m2.metric(_wz51_safe_label('Skill match', 'Skill match'), f'{skill_match}%' if skill_match else '—')
    m3.metric(_wz51_safe_label('Experience fit', 'Experience fit'), f'{experience_match}%' if experience_match else '—')
    m4.metric(_wz51_safe_label('Keyword fit', 'Keyword fit'), f'{keyword_match}%' if keyword_match else '—')

    status_style = 'border-color:rgba(20,184,166,.45);background:rgba(20,184,166,.12);' if score >= 70 else ('border-color:rgba(250,204,21,.45);background:rgba(250,204,21,.10);' if score >= 45 else 'border-color:rgba(248,113,113,.45);background:rgba(248,113,113,.10);')
    st.markdown(f"""
    <div class='wz-smart-card active' style='{status_style} margin-top:10px;'>
      <div class='wz-smart-label'>{html.escape(_wz51_safe_label('Decision', 'Decision'))}</div>
      <div class='wz-smart-title'>{html.escape(verdict)}</div>
      <div class='wz-smart-copy'>{html.escape(main_reason)}</div>
    </div>
    """, unsafe_allow_html=True)

    matched = _wz55_clean_list(analysis.get('matched') or analysis.get('strong_signals') or [], 8)
    missing = _wz55_clean_list(analysis.get('missing') or analysis.get('main_gaps') or analysis.get('gaps_and_risks') or [], 8)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('##### ✅ ' + _wz51_safe_label('What already matches', 'What already matches'))
        if matched:
            for item in matched:
                st.markdown(f'- {html.escape(item)}')
        else:
            st.caption(_wz51_safe_label('No strong match detected yet. Check if the CV was uploaded correctly.', 'No strong match detected yet. Check if the CV was uploaded correctly.'))
    with c2:
        st.markdown('##### ⚠️ ' + _wz51_safe_label('Gaps to handle honestly', 'Gaps to handle honestly'))
        if missing:
            for item in missing:
                st.markdown(f'- {html.escape(item)}')
        else:
            st.caption(_wz51_safe_label('No major missing keywords detected from the rule check.', 'No major missing keywords detected from the rule check.'))

    checklist = analysis.get('requirement_checklist') or []
    if checklist:
        st.markdown('##### ' + _wz51_safe_label('Requirement checklist', 'Requirement checklist'))
        for item in checklist[:8]:
            if isinstance(item, dict):
                req = html.escape(str(item.get('requirement') or item.get('name') or 'Requirement'))
                status = html.escape(str(item.get('status') or 'Review'))
                evidence = html.escape(str(item.get('evidence') or item.get('note') or ''))
                st.markdown(f"- **{req}** — {status}. {evidence}")
            else:
                st.markdown(f"- {html.escape(str(item))}")

    actions = _wz55_clean_list(analysis.get('honest_cv_actions') or analysis.get('tailored_cv_bullets') or analysis.get('next_actions') or [], 5)
    interview = _wz55_clean_list(analysis.get('interview_focus') or analysis.get('interview_questions') or [], 5)
    t1, t2 = st.tabs([_wz51_safe_label('How to tailor safely', 'How to tailor safely'), _wz51_safe_label('Interview focus', 'Interview focus')])
    with t1:
        st.info(_wz51_safe_label('Use these only if they are true. WorkZo should not invent skills, company facts, language level, salary, or experience.', 'Use these only if they are true. WorkZo should not invent skills, company facts, language level, salary, or experience.'))
        for item in actions or ['Rewrite 2-3 CV bullets so they clearly connect your real experience to the job requirements.']:
            st.markdown(f'- {html.escape(str(item))}')
    with t2:
        for item in interview or ['Prepare one STAR example for the strongest match and one honest explanation for the biggest gap.']:
            st.markdown(f'- {html.escape(str(item))}')

    with st.expander(_wz51_safe_label('Smart location context used', 'Smart location context used'), expanded=False):
        st.write({'country_iso': country_iso or 'Not available', 'city_bbox': bbox_data.get('bbox') if bbox_data else 'Not available'})

    a, b = st.columns(2)
    with a:
        if st.button(_wz51_safe_label('Improve CV for this job', 'Improve CV for this job'), key='wz55_understand_improve', use_container_width=True):
            _wz51_go('cv_documents', {'document_tools_mode': 'Improve CV for a Job', 'improve_cv_for_job_desc': jd})
    with b:
        if st.button(_wz51_safe_label('Prepare for this job', 'Prepare for this job'), key='wz55_understand_prepare', use_container_width=True):
            st.session_state['job_assist_mode_key'] = 'prepare'
            st.rerun()


def _wz51_render_understand_job():
    st.markdown('### ' + _wz51_safe_label('understand_job', 'Understand Job'))
    st.caption(_wz51_safe_label('Paste one real job description. WorkZo gives a practical apply/tailor decision, honest gaps, CV actions, and interview focus.', 'Paste one real job description. WorkZo gives a practical apply/tailor decision, honest gaps, CV actions, and interview focus.'))

    default_jd = st.session_state.get('last_understand_job_description') or st.session_state.get('current_job_description') or st.session_state.get('improve_cv_for_job_desc') or ''
    ctx1, ctx2, ctx3 = st.columns([1, 1, 1])
    with ctx1:
        country = st.text_input(_wz51_safe_label('Target country / market', 'Target country / market'), value=st.session_state.get('job_understand_country_v55') or st.session_state.get('country', ''), key='job_understand_country_v55')
    with ctx2:
        city = st.text_input(_wz51_safe_label('City / region', 'City / region'), value=st.session_state.get('job_understand_city_v55', ''), placeholder='Munich, Berlin, Chennai...', key='job_understand_city_v55')
    with ctx3:
        company = st.text_input(_wz51_safe_label('Company / employer', 'Company / employer'), value=st.session_state.get('target_company', ''), placeholder='Optional', key='job_understand_company_v55')

    country_iso = _wz55_country_iso(country)
    bbox_data = _wz55_city_bbox(city, country_iso)
    context_bits = []
    if country_iso:
        context_bits.append(f'ISO: {country_iso}')
    if bbox_data.get('bbox'):
        context_bits.append('city bbox ready')
    if context_bits:
        st.caption(' · '.join(context_bits))

    jd = st.text_area(_wz51_safe_label('Paste the job description', 'Paste the job description'), value=default_jd, height=260, key='job_desc_v55_understand')
    analyze_clicked = st.button(_wz51_safe_label('Analyze with WorkZo AI', 'Analyze with WorkZo AI'), key='btn_understand_job_v55', use_container_width=True)

    if analyze_clicked:
        if not jd.strip():
            st.warning(_wz51_safe_label('Please paste a job description first.', 'Please paste a job description first.'))
        else:
            cv_text = str(st.session_state.get('cv_text') or st.session_state.get('clean_structured_cv_text') or '')
            st.session_state['target_company'] = company.strip()
            st.session_state['current_job_description'] = jd.strip()
            st.session_state['last_understand_job_description'] = jd.strip()
            st.session_state['improve_cv_for_job_desc'] = jd.strip()
            prompt = f"""
You are WorkZo AI, an honest job-fit decision assistant.
Do not invent skills, company facts, language level, salary, location eligibility, or experience.
Preferred language: {st.session_state.get('preferred_language', 'English')}
Candidate country: {st.session_state.get('country', '')}
Target country: {country}
Target country ISO code: {country_iso or 'Unknown'}
Target city/region: {city or 'Not specified'}
City geolocation bounding box [west, south, east, north]: {bbox_data.get('bbox') if bbox_data else 'Unknown'}
Company: {company or 'Not specified'}
Career status: {st.session_state.get('user_status', 'Not specified')}

Candidate CV:
{cv_text[:5500]}

Job description:
{jd[:5500]}

Return ONLY valid JSON with these keys:
score, skill_match, experience_match, keyword_match, language_match, verdict, main_reason,
matched, missing, requirement_checklist, honest_cv_actions, interview_focus, country_market_note.
Rules:
- score 0-100, strict and realistic.
- verdict must be one of: Strong apply, Apply but tailor first, Possible but improve first, Risky match - consider skipping.
- matched: max 8 real strengths already visible in the CV.
- missing: max 8 important gaps or weak signals.
- requirement_checklist: max 8 objects with requirement, status, evidence.
- honest_cv_actions: max 5 actions; separate what to add only if true.
- interview_focus: max 5 likely interview topics/questions based on gaps and strengths.
"""
            analysis = {}
            with st.spinner(_wz51_safe_label('Reading CV + job description like a recruiter...', 'Reading CV + job description like a recruiter...')):
                try:
                    if callable(globals().get('run_ai_prompt')):
                        raw = run_ai_prompt(prompt, json_mode=True)
                        try:
                            analysis = safe_json_loads(raw) if callable(globals().get('safe_json_loads')) else json.loads(raw)
                        except Exception:
                            analysis = {}
                except Exception:
                    analysis = {}
                if not isinstance(analysis, dict) or not analysis:
                    analysis = _wz55_fallback_job_analysis(cv_text, jd, country, city)

            score = int(analysis.get('score') or analysis.get('fit_score') or 0)
            analysis['score'] = max(0, min(100, score))
            analysis['country_iso'] = country_iso
            analysis['city_bbox'] = bbox_data.get('bbox') if bbox_data else []
            analysis['source'] = analysis.get('source') or 'workzo_v55_understand_job'
            st.session_state['latest_job_analysis'] = analysis
            st.session_state['job_fit_score_value'] = analysis['score']
            st.session_state['workzo_progress_job_matched'] = True
            try:
                if callable(globals().get('track_event')):
                    track_event('job_analyzed', 'Job Assist', {'fit_score': analysis['score'], 'country_iso': country_iso, 'city_bbox_ready': bool(bbox_data.get('bbox'))})
            except Exception:
                pass
            st.success(_wz51_safe_label('Job analyzed. Review the decision, gaps, and safe next actions below.', 'Job analyzed. Review the decision, gaps, and safe next actions below.'))

    analysis = st.session_state.get('latest_job_analysis') or {}
    if isinstance(analysis, str):
        try:
            analysis = safe_json_loads(analysis) if callable(globals().get('safe_json_loads')) else json.loads(analysis)
        except Exception:
            analysis = {}
    if jd.strip() or analysis:
        _wz55_render_job_analysis_cards(analysis if isinstance(analysis, dict) else {}, jd, country_iso, bbox_data)

# =========================================================
# WorkZo v56 - requested small fixes only
# Scope:
# 1) Find Jobs: merge city suggestions + city/region into one field.
# 2) Find Jobs live list: make "Use in Understand Job" actually prefill and open Understand Job.
# 3) Application Progress is handled above as 4 visual cards with no buttons.
# =========================================================
def _wz56_unique(values):
    seen, out = set(), []
    for value in values or []:
        value = str(value or '').strip()
        if value and value.casefold() not in seen:
            seen.add(value.casefold())
            out.append(value)
    return out


def _wz56_country_options():
    countries = []
    try:
        countries.extend([str(x) for x in (globals().get('country_options') or []) if str(x).strip()])
    except Exception:
        pass
    countries.extend(['Global', 'Germany', 'India', 'United States', 'United Kingdom', 'Canada', 'Australia', 'Netherlands', 'France', 'Austria', 'Switzerland', 'Singapore', 'Ireland', 'Spain', 'Italy', 'Sweden', 'Denmark', 'Norway', 'Finland'])
    clean = _wz56_unique(countries)
    return ['Global'] + sorted([c for c in clean if c.casefold() != 'global'], key=lambda x: x.lower())


def _wz56_city_options(country_name):
    if not country_name or country_name == 'Global':
        return []
    try:
        fn = globals().get('fetch_country_cities')
        if callable(fn):
            return _wz56_unique(fn(country_name) or [])[:500]
    except Exception:
        pass
    fallback = {
        'Germany': ['Berlin', 'Munich', 'Frankfurt', 'Nuremberg', 'Würzburg', 'Hamburg', 'Cologne', 'Stuttgart', 'Düsseldorf'],
        'India': ['Chennai', 'Bengaluru', 'Hyderabad', 'Pune', 'Mumbai', 'Delhi', 'Coimbatore'],
        'United Kingdom': ['London', 'Manchester', 'Birmingham', 'Edinburgh'],
        'Canada': ['Toronto', 'Vancouver', 'Montreal', 'Calgary'],
        'Netherlands': ['Amsterdam', 'Rotterdam', 'Utrecht', 'Eindhoven'],
    }
    return fallback.get(str(country_name), [])


def _wz56_location_value(selected_location, country_name):
    selected_location = str(selected_location or '').strip()
    country_name = str(country_name or '').strip()
    if not selected_location or selected_location.startswith('Anywhere in '):
        return country_name if country_name and country_name != 'Global' else 'Global'
    if selected_location == 'Remote / hybrid':
        return f'Remote {country_name}'.strip() if country_name and country_name != 'Global' else 'Remote'
    return f'{selected_location}, {country_name}' if country_name and country_name != 'Global' else selected_location


def _wz56_job_description_from_result(job):
    title = str(job.get('title') or job.get('job_title') or 'Job opening').strip()
    company = str(job.get('company') or job.get('employer_name') or job.get('company_name') or '').strip()
    location = str(job.get('location') or job.get('job_location') or job.get('candidate_required_location') or '').strip()
    source = str(job.get('source') or job.get('publisher') or '').strip()
    description = str(job.get('description') or job.get('summary') or job.get('snippet') or job.get('assistant_note') or '').strip()
    url = str(job.get('url') or job.get('redirect_url') or job.get('job_apply_link') or job.get('apply_url') or '').strip()
    parts = [
        f'Job title: {title}',
        f'Company: {company}' if company else '',
        f'Location: {location}' if location else '',
        f'Source: {source}' if source else '',
        '',
        description or 'Full job description was not available from the live search result. Open the job link, copy the full description, and paste it here for a more accurate analysis.',
        '',
        f'Job link: {url}' if url else '',
    ]
    return '\n'.join([p for p in parts if p is not None]).strip()


def _wz56_render_live_job_results(jobs, country):
    st.markdown('#### ' + _wz51_safe_label('Curated job matches', 'Curated job matches'))
    st.caption(_wz51_safe_label('Open a job, then use it in Understand Job for a real CV-to-job fit check.', 'Open a job, then use it in Understand Job for a real CV-to-job fit check.'))
    for idx, job in enumerate((jobs or [])[:12], start=1):
        title = str(job.get('title') or job.get('job_title') or 'Job opening').strip()
        company = str(job.get('company') or job.get('employer_name') or job.get('company_name') or 'Company not listed').strip()
        location = str(job.get('location') or job.get('job_location') or job.get('candidate_required_location') or country or 'Location not listed').strip()
        source = str(job.get('source') or job.get('publisher') or 'Live source').strip()
        score = job.get('fit_score') or job.get('score') or job.get('match_score') or ''
        url = str(job.get('url') or job.get('redirect_url') or job.get('job_apply_link') or job.get('apply_url') or '').strip()
        label_score = f' — {score}%' if str(score).strip() else ''
        with st.expander(f'{idx}. {title} at {company}{label_score}', expanded=(idx == 1)):
            c1, c2 = st.columns([2.2, 1])
            with c1:
                st.markdown(f'**Location / market:** {html.escape(location)}')
                st.markdown(f'**Source:** {html.escape(source)}')
                note = str(job.get('assistant_note') or job.get('note') or '').strip()
                if note:
                    st.info(note)
                tags = job.get('tags') or job.get('keywords') or []
                if isinstance(tags, (list, tuple)) and tags:
                    st.caption(', '.join([str(t) for t in tags[:8]]))
            with c2:
                if url:
                    st.link_button(_wz51_safe_label('Open job', 'Open job'), url, use_container_width=True)
                if st.button(_wz51_safe_label('Use in Understand Job', 'Use in Understand Job'), key=f'wz56_use_understand_{idx}', use_container_width=True):
                    jd_text = _wz56_job_description_from_result(job)
                    st.session_state['current_job_description'] = jd_text
                    st.session_state['last_understand_job_description'] = jd_text
                    st.session_state['improve_cv_for_job_desc'] = jd_text
                    st.session_state['job_desc_v55_understand'] = jd_text
                    st.session_state['job_desc_v51_understand'] = jd_text
                    st.session_state['target_company'] = '' if company == 'Company not listed' else company
                    st.session_state['job_assist_mode_key'] = 'understand'
                    st.rerun()


def _wz51_render_find_jobs():
    st.markdown('### ' + _wz51_safe_label('find_jobs', 'Find Jobs'))
    cv_text = str(st.session_state.get('cv_text') or st.session_state.get('clean_structured_cv_text') or '')
    user_country = str(st.session_state.get('country') or st.session_state.get('migration_country') or '').strip() or 'Global'
    suggested_roles = _wz51_extract_roles_from_cv(cv_text)
    default_titles = ', '.join(suggested_roles[:3])

    if 'job_assist_target_titles' not in st.session_state:
        st.session_state['job_assist_target_titles'] = default_titles
    if 'job_assist_preferred_country_v56' not in st.session_state:
        st.session_state['job_assist_preferred_country_v56'] = user_country

    st.markdown(f"""
    <div class='next-action-card' style='margin-top:4px;'>
      <div class='next-action-label'>{html.escape(_wz51_safe_label('Smart job search', 'Smart job search'))}</div>
      <div class='next-action-title'>{html.escape(_wz51_safe_label('Search by role, country, and city in one clean flow', 'Search by role, country, and city in one clean flow'))}</div>
      <div class='next-action-copy'>{html.escape(_wz51_safe_label('Choose a country, then choose a city/region from the same location field. Open a job and send it directly to Understand Job.', 'Choose a country, then choose a city/region from the same location field. Open a job and send it directly to Understand Job.'))}</div>
    </div>
    """, unsafe_allow_html=True)

    countries = _wz56_country_options()
    current_country = st.session_state.get('job_assist_preferred_country_v56') or user_country or 'Global'
    if current_country not in countries:
        countries.insert(1, current_country)

    c1, c2, c3 = st.columns([1.15, 0.9, 1.05])
    with c1:
        target_titles = st.text_input(
            _wz51_safe_label('Target job titles', 'Target job titles'),
            placeholder='Data Analyst, IT Support, Customer Success',
            key='job_assist_target_titles',
        )
    with c2:
        preferred_country = st.selectbox(
            _wz51_safe_label('Preferred country', 'Preferred country'),
            countries,
            index=countries.index(current_country) if current_country in countries else 0,
            key='job_assist_preferred_country_v56',
        )
    with c3:
        cities = _wz56_city_options(preferred_country)
        location_options = []
        if preferred_country and preferred_country != 'Global':
            location_options.append(f'Anywhere in {preferred_country}')
        else:
            location_options.append('Global')
        location_options.append('Remote / hybrid')
        location_options.extend(cities)
        selected_location = st.selectbox(
            _wz51_safe_label('City / region', 'City / region'),
            _wz56_unique(location_options),
            index=0,
            key='job_assist_city_region_v56',
            help=_wz51_safe_label('This single searchable field replaces the separate city suggestions box.', 'This single searchable field replaces the separate city suggestions box.'),
        )

    search_location = _wz56_location_value(selected_location, preferred_country)
    roles_preview = [x.strip() for x in re.split(r'[,;\n/]', target_titles or '') if x.strip()] or suggested_roles[:3]
    role_chips = ''.join(f"<span class='workzo-dashboard-chip'>{html.escape(r)}</span>" for r in roles_preview[:4])
    st.markdown(f"""
    <div class='workzo-mini-note' style='margin: 8px 0 14px 0;'>
        {_wz51_safe_label('Search context', 'Search context')}: {role_chips}
        <span class='workzo-dashboard-chip'>📍 {html.escape(search_location)}</span>
    </div>
    """, unsafe_allow_html=True)

    find_clicked = st.button(_wz51_safe_label('Find smart matches', 'Find smart matches'), key='btn_find_jobs_v56', use_container_width=True)
    if find_clicked:
        roles = [x.strip() for x in re.split(r'[,;\n/]', target_titles or '') if x.strip()] or suggested_roles
        if not roles:
            st.warning(_wz51_safe_label('Please add at least one target job title.', 'Please add at least one target job title.'))
        else:
            st.session_state['last_job_search_target_titles'] = ', '.join(roles[:6])
            st.session_state['last_job_search_location_text'] = search_location
            st.session_state['last_job_search_country'] = preferred_country
            jobs = []
            with st.status(_wz51_safe_label('Searching and ranking jobs...', 'Searching and ranking jobs...'), expanded=True) as status:
                try:
                    st.write(_wz51_safe_label('Searching live job sources...', 'Searching live job sources...'))
                    if callable(globals().get('fetch_live_jobs_global')):
                        jobs = fetch_live_jobs_global(preferred_country, roles, search_location, st.session_state.get('user_status', '')) or []
                except Exception as exc:
                    st.warning(f'Live job source error: {exc}')
                try:
                    st.write(_wz51_safe_label('Ranking matches against your CV...', 'Ranking matches against your CV...'))
                    if jobs and callable(globals().get('curate_job_matches')):
                        jobs = curate_job_matches(jobs, cv_text, {'job_titles': roles, 'search_queries': roles, 'location': search_location}, preferred_country, st.session_state.get('user_status', ''), limit=25)
                except Exception:
                    pass
                st.session_state['latest_curated_jobs'] = jobs
                st.session_state['workzo_progress_job_matched'] = bool(jobs)
                status.update(label=_wz51_safe_label('Job search complete', 'Job search complete'), state='complete', expanded=False)

    jobs = st.session_state.get('latest_curated_jobs') or []
    if jobs:
        _wz56_render_live_job_results(jobs, preferred_country)
    else:
        st.info(_wz51_safe_label('No saved job results yet. Search with a specific role title, country, and city/region.', 'No saved job results yet. Search with a specific role title, country, and city/region.'))
        role_for_link = (st.session_state.get('last_job_search_target_titles') or target_titles or default_titles or 'jobs').split(',')[0].strip()
        q = urllib.parse.quote_plus(f'{role_for_link} {search_location}')
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.link_button('LinkedIn', f'https://www.linkedin.com/jobs/search/?keywords={q}')
        with c2: st.link_button('Indeed', f'https://www.indeed.com/jobs?q={q}')
        with c3: st.link_button('Google Jobs', f'https://www.google.com/search?q={q}+jobs')
        with c4: st.link_button('RemoteOK', f'https://remoteok.com/remote-{urllib.parse.quote_plus(role_for_link)}-jobs')

# =========================================================
# WorkZo v57 - Understand Job UX + speed patch only
# Scope: replaces only Understand Job rendering/AI prompt/output layout.
# No changes to dashboard, CV tools, Find Jobs, or Work-O-Bot.
# =========================================================
def _wz57_num(value, default=0):
    try:
        return max(0, min(100, int(float(value or default))))
    except Exception:
        return default


def _wz57_items(value, limit=5):
    try:
        return _wz55_clean_list(value, limit) if callable(globals().get('_wz55_clean_list')) else []
    except Exception:
        return []


def _wz57_badge(text, tone='neutral'):
    colors = {
        'good': ('rgba(20,184,166,.16)', 'rgba(20,184,166,.45)', '#86efac'),
        'warn': ('rgba(250,204,21,.13)', 'rgba(250,204,21,.42)', '#fde68a'),
        'bad': ('rgba(248,113,113,.13)', 'rgba(248,113,113,.42)', '#fecaca'),
        'neutral': ('rgba(59,130,246,.13)', 'rgba(59,130,246,.38)', '#bfdbfe'),
    }.get(tone, ('rgba(59,130,246,.13)', 'rgba(59,130,246,.38)', '#bfdbfe'))
    return f"<span style='display:inline-flex;align-items:center;gap:6px;border:1px solid {colors[1]};background:{colors[0]};color:{colors[2]};border-radius:999px;padding:6px 10px;font-size:.82rem;font-weight:800;margin:2px 6px 2px 0;'>{html.escape(str(text))}</span>"


def _wz57_render_list_card(title, items, empty_text, icon='•'):
    st.markdown(f"<div style='font-size:1rem;font-weight:900;color:#f8fafc;margin:8px 0 8px 0;'>{html.escape(str(title))}</div>", unsafe_allow_html=True)
    items = _wz57_items(items, 6)
    if not items:
        st.caption(empty_text)
        return
    html_items = ''.join(f"<li>{html.escape(str(x))}</li>" for x in items)
    st.markdown(f"""
    <div style='border:1px solid rgba(148,163,184,.18);background:rgba(15,23,42,.46);border-radius:18px;padding:14px 16px;margin-bottom:12px;'>
      <ul style='margin:0;padding-left:20px;line-height:1.75;color:#e5e7eb;'>{html_items}</ul>
    </div>
    """, unsafe_allow_html=True)


def _wz57_render_job_analysis_cards(analysis: dict, jd: str, country_iso: str, bbox_data: dict):
    if not isinstance(analysis, dict) or not analysis:
        return

    score = _wz57_num(analysis.get('score') or analysis.get('fit_score') or analysis.get('job_fit_score') or st.session_state.get('job_fit_score_value'))
    skill_match = _wz57_num(analysis.get('skill_match'), score)
    experience_match = _wz57_num(analysis.get('experience_match'), score)
    keyword_match = _wz57_num(analysis.get('keyword_match'), score)
    verdict = str(analysis.get('verdict') or analysis.get('apply_decision') or 'Review before applying')
    main_reason = str(analysis.get('main_reason') or analysis.get('summary') or 'WorkZo compared the pasted job with your available CV details.')

    tone = 'good' if score >= 70 else ('warn' if score >= 45 else 'bad')
    st.markdown(f"""
    <style>
    .wz57-hero {{border:1px solid rgba(59,130,246,.28);background:linear-gradient(135deg,rgba(37,99,235,.16),rgba(15,23,42,.72));border-radius:22px;padding:18px 20px;margin:14px 0 16px 0;}}
    .wz57-kicker {{color:#93c5fd;font-size:.75rem;text-transform:uppercase;letter-spacing:.08em;font-weight:900;margin-bottom:6px;}}
    .wz57-title {{color:#f8fafc;font-size:1.35rem;font-weight:950;line-height:1.25;margin-bottom:8px;}}
    .wz57-copy {{color:#cbd5e1;font-size:.95rem;line-height:1.5;}}
    .wz57-score-grid {{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:12px 0 16px 0;}}
    .wz57-score-card {{border:1px solid rgba(148,163,184,.18);background:rgba(15,23,42,.52);border-radius:18px;padding:14px;}}
    .wz57-score-label {{color:#94a3b8;font-size:.76rem;font-weight:850;margin-bottom:6px;}}
    .wz57-score-value {{color:#f8fafc;font-size:1.65rem;font-weight:950;}}
    @media(max-width:900px){{.wz57-score-grid{{grid-template-columns:repeat(2,minmax(0,1fr));}}}}
    </style>
    <div class='wz57-hero'>
      <div class='wz57-kicker'>AI job-fit summary</div>
      <div class='wz57-title'>{html.escape(verdict)}</div>
      <div class='wz57-copy'>{html.escape(main_reason)}</div>
      <div style='margin-top:10px;'>
        {_wz57_badge('Strict score: ' + str(score) + '%', tone)}
        {_wz57_badge('ISO: ' + str(country_iso), 'neutral') if country_iso else ''}
        {_wz57_badge('Location ready', 'good') if bbox_data and bbox_data.get('bbox') else ''}
      </div>
    </div>
    <div class='wz57-score-grid'>
      <div class='wz57-score-card'><div class='wz57-score-label'>Fit score</div><div class='wz57-score-value'>{score}%</div></div>
      <div class='wz57-score-card'><div class='wz57-score-label'>Skill match</div><div class='wz57-score-value'>{skill_match}%</div></div>
      <div class='wz57-score-card'><div class='wz57-score-label'>Experience fit</div><div class='wz57-score-value'>{experience_match}%</div></div>
      <div class='wz57-score-card'><div class='wz57-score-label'>Keyword fit</div><div class='wz57-score-value'>{keyword_match}%</div></div>
    </div>
    """, unsafe_allow_html=True)

    matched = analysis.get('matched') or analysis.get('strong_signals') or []
    missing = analysis.get('missing') or analysis.get('main_gaps') or analysis.get('gaps_and_risks') or []
    c1, c2 = st.columns(2)
    with c1:
        _wz57_render_list_card('✅ What already matches', matched, 'No strong match detected yet. Check whether the CV was uploaded correctly.')
    with c2:
        _wz57_render_list_card('⚠️ Gaps to handle honestly', missing, 'No major missing requirement detected.')

    checklist = analysis.get('requirement_checklist') or []
    if checklist:
        st.markdown('#### Requirement check')
        rows = []
        for item in checklist[:7]:
            if isinstance(item, dict):
                rows.append((str(item.get('requirement') or item.get('name') or 'Requirement'), str(item.get('status') or 'Review'), str(item.get('evidence') or item.get('note') or '')))
            else:
                rows.append((str(item), 'Review', ''))
        for req, status, evidence in rows:
            status_low = status.lower()
            pill_tone = 'good' if 'match' in status_low and 'missing' not in status_low and 'weak' not in status_low else ('bad' if 'missing' in status_low else 'warn')
            st.markdown(f"""
            <div style='border:1px solid rgba(148,163,184,.16);border-radius:15px;padding:12px 14px;margin:8px 0;background:rgba(15,23,42,.45);'>
              <div style='font-weight:850;color:#f8fafc;'>{html.escape(req)} {_wz57_badge(status, pill_tone)}</div>
              <div style='color:#cbd5e1;font-size:.9rem;margin-top:4px;'>{html.escape(evidence)}</div>
            </div>
            """, unsafe_allow_html=True)

    actions = analysis.get('honest_cv_actions') or analysis.get('tailored_cv_bullets') or analysis.get('next_actions') or []
    interview = analysis.get('interview_focus') or analysis.get('interview_questions') or []
    t1, t2 = st.tabs(['How to tailor safely', 'Interview focus'])
    with t1:
        st.info('Use these only if they are true. Do not invent skills, company facts, language level, salary, or experience.')
        _wz57_render_list_card('Safe CV actions', actions, 'Rewrite 2-3 CV bullets so they clearly connect your real experience to this job.')
    with t2:
        _wz57_render_list_card('Likely discussion areas', interview, 'Prepare one STAR example for the strongest match and one honest explanation for the biggest gap.')

    a, b = st.columns(2)
    with a:
        if st.button('Improve CV for this job', key='wz57_understand_improve', use_container_width=True):
            _wz51_go('cv_documents', {'document_tools_mode': 'Improve CV for a Job', 'improve_cv_for_job_desc': jd})
    with b:
        if st.button('Prepare for this job', key='wz57_understand_prepare', use_container_width=True):
            st.session_state['job_assist_mode_key'] = 'prepare'
            st.rerun()


def _wz51_render_understand_job():
    st.markdown('### Understand Job')
    st.caption('Paste one real job description. WorkZo gives a clear apply/tailor decision, honest gaps, safe CV actions, and interview focus.')

    default_jd = st.session_state.get('last_understand_job_description') or st.session_state.get('current_job_description') or st.session_state.get('improve_cv_for_job_desc') or ''
    with st.expander('Job context', expanded=True):
        ctx1, ctx2, ctx3 = st.columns([1, 1, 1])
        with ctx1:
            country = st.text_input('Target country / market', value=st.session_state.get('job_understand_country_v55') or st.session_state.get('country', ''), key='job_understand_country_v55')
        with ctx2:
            city = st.text_input('City / region', value=st.session_state.get('job_understand_city_v55', ''), placeholder='Munich, Berlin, Chennai...', key='job_understand_city_v55')
        with ctx3:
            company = st.text_input('Company / employer', value=st.session_state.get('target_company', ''), placeholder='Optional', key='job_understand_company_v55')

    country_iso = _wz55_country_iso(country) if callable(globals().get('_wz55_country_iso')) else ''
    bbox_data = _wz55_city_bbox(city, country_iso) if callable(globals().get('_wz55_city_bbox')) else {}
    context_line = []
    if country_iso:
        context_line.append('Country code: ' + country_iso)
    if bbox_data.get('bbox'):
        context_line.append('City location understood')
    if context_line:
        st.caption(' · '.join(context_line))

    jd = st.text_area('Paste the job description', value=default_jd, height=230, key='job_desc_v55_understand')
    col_btn, col_hint = st.columns([0.9, 2])
    with col_btn:
        analyze_clicked = st.button('Analyze Job Fit', key='btn_understand_job_v57', use_container_width=True)
    with col_hint:
        st.caption('Faster mode: concise prompt + compact recruiter-style JSON. Full CV/JD is trimmed to reduce loading time.')

    if analyze_clicked:
        if not jd.strip():
            st.warning('Please paste a job description first.')
        else:
            cv_text = str(st.session_state.get('cv_text') or st.session_state.get('clean_structured_cv_text') or '')
            st.session_state['target_company'] = company.strip()
            st.session_state['current_job_description'] = jd.strip()
            st.session_state['last_understand_job_description'] = jd.strip()
            st.session_state['improve_cv_for_job_desc'] = jd.strip()
            cache_key = 'wz57_analysis_' + str(abs(hash((cv_text[:1800], jd[:1800], country, city, company))))
            analysis = st.session_state.get(cache_key)
            if not isinstance(analysis, dict):
                prompt = f"""
You are WorkZo AI. Act like a strict recruiter + career coach.
Return ONLY compact valid JSON. Be honest. Do not invent experience.

Context: target_country={country}; country_iso={country_iso or 'Unknown'}; city={city or 'Not specified'}; bbox={bbox_data.get('bbox') if bbox_data else 'Unknown'}; company={company or 'Not specified'}; preferred_language={st.session_state.get('preferred_language', 'English')}; career_status={st.session_state.get('user_status', 'Not specified')}.

CV (trimmed):
{cv_text[:3800]}

Job description (trimmed):
{jd[:4200]}

JSON keys exactly:
score, skill_match, experience_match, keyword_match, language_match, verdict, main_reason, matched, missing, requirement_checklist, honest_cv_actions, interview_focus.

Rules:
- score/matches are 0-100 and strict.
- verdict: Strong apply / Apply but tailor first / Possible but improve first / Risky match - consider skipping.
- matched: max 5 CV-backed strengths.
- missing: max 5 important gaps.
- requirement_checklist: max 7 objects: requirement, status, evidence.
- honest_cv_actions: max 5 practical CV improvements, only if true.
- interview_focus: max 5 interview topics/questions.
"""
                with st.spinner('Analyzing like a recruiter...'):
                    try:
                        if callable(globals().get('run_ai_prompt')):
                            raw = run_ai_prompt(prompt, json_mode=True)
                            try:
                                analysis = safe_json_loads(raw) if callable(globals().get('safe_json_loads')) else json.loads(raw)
                            except Exception:
                                analysis = {}
                    except Exception:
                        analysis = {}
                    if not isinstance(analysis, dict) or not analysis:
                        analysis = _wz55_fallback_job_analysis(cv_text, jd, country, city) if callable(globals().get('_wz55_fallback_job_analysis')) else {}
                st.session_state[cache_key] = analysis

            score = _wz57_num(analysis.get('score') or analysis.get('fit_score'))
            analysis['score'] = score
            analysis['country_iso'] = country_iso
            analysis['city_bbox'] = bbox_data.get('bbox') if bbox_data else []
            st.session_state['latest_job_analysis'] = analysis
            st.session_state['job_fit_score_value'] = score
            st.session_state['workzo_progress_job_matched'] = True
            st.success('Job analyzed. Review the clean summary below.')

    analysis = st.session_state.get('latest_job_analysis') or {}
    if isinstance(analysis, str):
        try:
            analysis = safe_json_loads(analysis) if callable(globals().get('safe_json_loads')) else json.loads(analysis)
        except Exception:
            analysis = {}
    if isinstance(analysis, dict) and analysis:
        _wz57_render_job_analysis_cards(analysis, jd, country_iso, bbox_data)
