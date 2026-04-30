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
                st.session_state["target_company_website"] = _sidebar_company_url.strip()
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
        st.session_state["target_company_website"] = company_website
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
                st.session_state["target_company_website"] = company_website
                st.session_state["company_context"] = _wz26_fetch_company_context(target_company, company_website)
                _wz19_go("cv_documents")
        with c:
            if st.button("Practice interview", key="wz20_go_interview", use_container_width=True):
                st.session_state["workobot_mode"] = "real_interview_simulation"
                st.session_state["real_interview_jd"] = jd
                st.session_state["real_interview_company"] = target_company
                st.session_state["target_company_website"] = company_website
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
    st.session_state['target_company_website'] = st.session_state.get('wz27_company_website','')
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
    st.session_state['target_company_website'] = website
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
    st.session_state['target_company_website'] = str(website or '').strip()
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

    st.markdown('### Application progress')
    st.caption('Move step by step, or jump to the part you want to work on.')
    current_step = _wz32_pick_current_step(cv_exists, resume_score, ats_score, job_exists, improved_ready, cover_ready)
    score_checked = bool(cv_exists and resume_score > 0 and ats_score > 0)
    prepared_ready = bool(cover_ready or str(st.session_state.get('latest_application_prep','')).strip())
    progress_items = [
        ('1. CV added', cv_exists, current_step == 0, 'Upload or create CV' if not cv_exists else 'Completed', 'Edit CV', 'cv_documents', {'document_tools_mode':'Improve / Update CV'}),
        ('2. Job analyzed', job_exists, current_step == 2, 'Paste or analyze one job' if not job_exists else 'Completed', 'Analyze job', 'job_assist', {'job_assist_mode_key':'understand'}),
        ('3. CV improved', improved_ready, current_step == 3 or (score_checked and not improved_ready), 'Tailor CV to selected job' if not improved_ready else 'Completed', 'Improve CV', 'cv_documents', {'document_tools_mode':'Improve CV for a Job' if job_exists else 'Improve / Update CV'}),
        ('4. Prepared to apply', prepared_ready, current_step == 4 or (improved_ready and not prepared_ready), 'Cover letter / prep pending' if not prepared_ready else 'Completed', 'Prepare', 'job_assist', {'job_assist_mode_key':'prepare'}),
    ]
    cols = st.columns(4)
    for idx, (label, done, current, note, button_label, target, extra_state) in enumerate(progress_items):
        with cols[idx]:
            st.markdown(_wz32_flow_step(label, done, current, note), unsafe_allow_html=True)
            if st.button(button_label, key=f'wz32_progress_{idx}_{target}', use_container_width=True):
                if isinstance(extra_state, dict):
                    for k, v in extra_state.items():
                        st.session_state[k] = v
                _wz28_go(target)
    st.caption('Scores are guidance only. WorkZo should not invent skills, company facts, language level, salary, or experience.')
    _wz32_remember_best_scores()

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
    company = st.session_state.get("prepare_target_company") or st.session_state.get("target_company") or st.session_state.get("target_company_website") or "Company not added"
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
            if st.button(button, key=f"wz35_flow_btn_{i}", use_container_width=True):
                _wz35_go(target, extra)
    st.caption("Scores are guidance only. WorkZo should not invent skills, company facts, language level, salary, or experience.")
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
