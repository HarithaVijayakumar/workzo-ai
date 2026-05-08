

# =========================================================
# WorkZo split-module shared UI helpers
# Added by fix_workzo_split_modules.py
# =========================================================
import os
import base64
import html
import streamlit as st
# components removed: no deprecated st.components.v1.html


# =========================================================
# WorkZo v37 - Work-O-Bot request limiter fallbacks
# Keeps Work-O-Bot working even if bootstrap rate-limit helpers are not loaded.
# =========================================================
if "can_make_request" not in globals():
    def can_make_request() -> bool:
        try:
            import time as _time
            max_requests = int(globals().get("MAX_REQUESTS_PER_HOUR", 25) or 25)
            if "request_count" not in st.session_state:
                st.session_state.request_count = 0
            if "first_request_time" not in st.session_state:
                st.session_state.first_request_time = _time.time()
            if _time.time() - float(st.session_state.first_request_time or _time.time()) > 3600:
                st.session_state.request_count = 0
                st.session_state.first_request_time = _time.time()
            return int(st.session_state.request_count or 0) < max_requests
        except Exception:
            return True

if "register_request" not in globals():
    def register_request() -> None:
        try:
            import time as _time
            if "request_count" not in st.session_state:
                st.session_state.request_count = 0
            if "first_request_time" not in st.session_state:
                st.session_state.first_request_time = _time.time()
            st.session_state.request_count = int(st.session_state.request_count or 0) + 1
        except Exception:
            pass


def strip_markdown_for_resume(text):
    """
    Removes markdown symbols from generated CV text
    so the resume preview/download looks clean.
    """
    import re

    text = str(text or "")
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    text = text.replace("**", "")
    text = text.replace("__", "")
    text = text.replace("###", "")
    text = text.replace("##", "")
    text = text.replace("#", "")
    text = text.replace("`", "")

    text = re.sub(r"^\s*[-*]\s+", "• ", text, flags=re.MULTILINE)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()
def clean_generated_cv_text_for_template(cv_text):
    """
    Normalizes CV text before rendering templates.
    Prevents formatting issues in preview and PDF.
    """
    import re

    text_value = strip_markdown_for_resume(cv_text or "")

    # Normalize line breaks
    text_value = text_value.replace("\r\n", "\n").replace("\r", "\n")

    # Remove repeated blank lines
    text_value = re.sub(r"\n{3,}", "\n\n", text_value)

    # Remove trailing spaces
    text_value = "\n".join(line.rstrip() for line in text_value.splitlines())

    return text_value.strip()




try:
    BASE_DIR
except NameError:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

try:
    ICON_PATH
except NameError:
    ICON_PATH = os.path.join(BASE_DIR, "workzo_icon.png")

try:
    LOGO_PATH
except NameError:
    LOGO_PATH = os.path.join(BASE_DIR, "logo.png")


def image_to_data_uri(image_path: str):
    """Convert a local image into a base64 data URI for HTML rendering."""
    if not image_path:
        return None
    try:
        path = str(image_path)
        if not os.path.exists(path):
            return None
        ext = os.path.splitext(path)[1].lower().replace(".", "") or "png"
        mime = "jpeg" if ext in {"jpg", "jpeg"} else ext
        with open(path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
        return f"data:image/{mime};base64,{encoded}"
    except Exception:
        return None


def request_scroll_to_top() -> None:
    """Mark the next run to scroll to top."""
    try:
        st.session_state["_workzo_scroll_to_top"] = True
    except Exception:
        pass


def maybe_scroll_to_top() -> None:
    """Native warning-free top marker. No iframe/components/script."""
    st.markdown('<span id="workzo-page-top"></span>', unsafe_allow_html=True)
    try:
        if st.session_state.pop("_workzo_scroll_to_top", False):
            st.query_params["wz_view"] = str(st.session_state.get("_workzo_page_nonce", "top"))
    except Exception:
        pass

def update_url_page(page_key: str) -> None:
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
    try:
        st.session_state.page = page_key
        st.session_state.nav_page = page_key
        st.session_state.nav_change_nonce = st.session_state.get("nav_change_nonce", 0) + 1
        update_url_page(page_key)
        request_scroll_to_top()
    except Exception:
        pass


def queue_navigation(page_key: str) -> None:
    try:
        st.session_state._workzo_pending_nav = page_key
        request_scroll_to_top()
    except Exception:
        pass


def consume_pending_navigation() -> None:
    try:
        page_key = st.session_state.pop("_workzo_pending_nav", None)
        if page_key:
            sync_navigation_state(page_key)
    except Exception:
        pass


def go_home() -> None:
    """Home should return to dashboard/workspace, not restart onboarding."""
    try:
        st.session_state.onboarding_complete = True
        queue_navigation("dashboard")
    except Exception:
        pass
# =========================================================

# WorkZo modular split v138
# Source: app_workzo_v137_stable_no_feature_change.py, lines 7680-9296
import streamlit as st
import base64
import os
# components removed: no deprecated st.components.v1.html


def maybe_scroll_to_top():
    """Scroll the active Streamlit page to the top after navigation.

    Uses st.iframe (the Streamlit-recommended replacement for deprecated
    st.components.v1.html). If the Streamlit version does not support iframe,
    it falls back to a harmless top anchor.
    """
    try:
        if st.session_state.pop("_workzo_scroll_to_top", False):
            script = """
            <script>
            const scrollTop = () => {
              try { window.parent.scrollTo({top: 0, left: 0, behavior: 'instant'}); } catch(e) {}
              try { window.parent.document.querySelector('section.main').scrollTo(0,0); } catch(e) {}
              try { window.parent.document.querySelector('[data-testid="stAppViewContainer"]').scrollTo(0,0); } catch(e) {}
            };
            scrollTop(); setTimeout(scrollTop, 60); setTimeout(scrollTop, 220);
            </script>
            """
            if hasattr(st, "iframe"):
                st.iframe(srcdoc=script, height=0, width=0)
            else:
                st.markdown('<span id="workzo-page-top"></span>', unsafe_allow_html=True)
    except Exception:
        pass
ICON_PATH = os.path.join(BASE_DIR, "workzo_icon.png")
LOGO_PATH = os.path.join(BASE_DIR, "logo.png")

# =========================================================
# WorkZo v39 GLOBAL RATE LIMIT FALLBACKS
# Must exist before Work-O-Bot or any AI helper is called.
# =========================================================
def workzo_safe_can_make_request() -> bool:
    try:
        fn = globals().get("_original_can_make_request")
        if callable(fn):
            return bool(fn())
    except Exception:
        pass
    try:
        import time as _time
        max_requests = int(globals().get("MAX_REQUESTS_PER_HOUR", 25) or 25)
        if "request_count" not in st.session_state:
            st.session_state.request_count = 0
        if "first_request_time" not in st.session_state:
            st.session_state.first_request_time = _time.time()
        if _time.time() - float(st.session_state.first_request_time or _time.time()) > 3600:
            st.session_state.request_count = 0
            st.session_state.first_request_time = _time.time()
        return int(st.session_state.request_count or 0) < max_requests
    except Exception:
        return True

def workzo_safe_register_request() -> None:
    try:
        fn = globals().get("_original_register_request")
        if callable(fn):
            fn()
            return
    except Exception:
        pass
    try:
        import time as _time
        if "request_count" not in st.session_state:
            st.session_state.request_count = 0
        if "first_request_time" not in st.session_state:
            st.session_state.first_request_time = _time.time()
        st.session_state.request_count = int(st.session_state.request_count or 0) + 1
    except Exception:
        pass

try:
    if callable(globals().get("register_request")):
        _original_register_request = globals().get("register_request")
except Exception:
    pass
try:
    if callable(globals().get("can_make_request")):
        _original_can_make_request = globals().get("can_make_request")
except Exception:
    pass
register_request = workzo_safe_register_request
can_make_request = workzo_safe_can_make_request



# =========================================================
# WorkZo v75 - compact top spacing + clean landing + safe Work-O-Bot routing
# =========================================================
def apply_workzo_v75_global_css() -> None:
    """Keep the brand/header close to the top on every page and simplify landing spacing."""
    try:
        st.markdown("""
        <style id="workzo-v75-global-spacing">
        html, body { margin-top: 0 !important; padding-top: 0 !important; }
        [data-testid="stAppViewContainer"] { padding-top: 0 !important; }
        [data-testid="stAppViewContainer"] > .main { padding-top: 0 !important; }
        [data-testid="stMain"] { padding-top: 0 !important; }
        [data-testid="stMainBlockContainer"], .block-container {
            padding-top: 0.35rem !important;
            margin-top: 0 !important;
        }
        .workzo-header, .wz72-brand { margin-top: 0 !important; }
        .workzo-landing-hero-simple {
            margin: 0.7rem 0 1.1rem 0;
            padding: 2.2rem 2rem;
            border-radius: 28px;
            border: 1px solid rgba(34,211,238,.28);
            background: radial-gradient(circle at 18% 10%, rgba(20,214,201,.22), transparent 26%), linear-gradient(135deg, rgba(3,16,42,.98), rgba(8,30,68,.96));
            box-shadow: 0 24px 70px rgba(2,6,23,.42);
        }
        .workzo-landing-hero-simple h1 { color: #fff; font-size: clamp(2.1rem, 5vw, 4.2rem); line-height: 1.02; letter-spacing: -.045em; margin: 0 0 .85rem 0; font-weight: 950; max-width: 900px; }
        .workzo-landing-hero-simple p { color: #cbd5e1; font-size: clamp(1rem, 2vw, 1.2rem); line-height: 1.55; margin: 0; max-width: 780px; }
        .st-key-landing_start_with_cv button { min-height: 58px !important; border-radius: 18px !important; font-size: 1.1rem !important; font-weight: 900 !important; }
        @media (max-width: 700px) {
            [data-testid="stMainBlockContainer"], .block-container { padding-top: 0.2rem !important; padding-left: 1rem !important; padding-right: 1rem !important; }
            .workzo-landing-hero-simple { padding: 1.35rem 1.05rem; border-radius: 22px; margin-top: .35rem; }
        }
        </style>
        """, unsafe_allow_html=True)
    except Exception:
        pass


def _workzo_header_progress_state():
    """Small header progress tracker: CV → Jobs → Interview."""
    try:
        cv_done = bool(str(st.session_state.get("cv_text", "") or st.session_state.get("clean_structured_cv_text", "")).strip())
        job_done = bool(str(
            st.session_state.get("selected_job_description", "")
            or st.session_state.get("last_understand_job_description", "")
            or st.session_state.get("improve_cv_for_job_desc", "")
            or st.session_state.get("interview_jd_text_v117", "")
        ).strip())
        interview_done = bool(
            st.session_state.get("interview_completed")
            or st.session_state.get("real_interview_completed")
            or st.session_state.get("latest_interview_feedback")
        )
        done = sum([cv_done, job_done, interview_done])
        progress_pct = int(round(done / 3 * 100))
        stage = "CV"
        if cv_done and not job_done:
            stage = "Jobs"
        elif cv_done and job_done and not interview_done:
            stage = "Interview"
        elif interview_done:
            stage = "Ready"
        return progress_pct, stage, cv_done, job_done, interview_done
    except Exception:
        return 0, "CV", False, False, False


def render_workzo_header() -> None:
    """Sticky responsive SaaS header with progress and back navigation.

    Kept self-contained so it does not depend on global_header.py and does not affect
    dashboard/interview/CV/job logic.
    """
    try:
        apply_workzo_v75_global_css()
    except Exception:
        pass

    try:
        logo_src = image_to_data_uri(ICON_PATH) or image_to_data_uri(LOGO_PATH)
    except Exception:
        logo_src = None

    logo_html = (
        f'<img src="{logo_src}" class="workzo-logo" alt="WorkZo AI logo">'
        if logo_src
        else '<div class="workzo-logo workzo-logo-fallback">WZ</div>'
    )

    progress_pct, stage, cv_done, job_done, interview_done = _workzo_header_progress_state()
    cv_mark = "✓" if cv_done else "1"
    job_mark = "✓" if job_done else "2"
    interview_mark = "✓" if interview_done else "3"
    # Use deterministic Streamlit query navigation instead of javascript:history.back().
    # JavaScript links are unreliable inside Streamlit markdown on some deployments.
    current_page = str(st.session_state.get("nav_page") or st.session_state.get("page", "landing") or "landing")
    show_back = current_page not in {"landing", "dashboard"}
    if current_page == "onboarding":
        back_href = "?page=landing"
    else:
        back_href = "?page=dashboard&home=1"
    back_html = f'<a class="workzo-back" href="{back_href}" target="_self">← Back</a>' if show_back else '<span></span>'

    st.markdown(f"""
    <style id="workzo-sticky-saas-header-css">
    .workzo-header {{
        width: min(1180px, calc(100vw - 2rem)) !important;
        margin: 0 auto 1.05rem auto !important;
        position: sticky !important;
        top: .55rem !important;
        z-index: 99999 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: space-between !important;
        gap: 1rem !important;
        padding: .82rem 1rem !important;
        border-radius: 22px !important;
        border: 1px solid rgba(34,211,238,.30) !important;
        background: linear-gradient(135deg, rgba(8,47,73,.96), rgba(15,23,42,.98)) !important;
        box-shadow: 0 18px 45px rgba(2,6,23,.35) !important;
        backdrop-filter: blur(14px) !important;
    }}
    .workzo-brand {{ display:flex !important; align-items:center !important; gap:.85rem !important; min-width:0 !important; text-decoration:none !important; }}
    .workzo-logo {{ width:54px !important; height:54px !important; min-width:54px !important; border-radius:15px !important; object-fit:cover !important; display:flex !important; align-items:center !important; justify-content:center !important; background:linear-gradient(135deg,#06b6d4,#2563eb) !important; color:#fff !important; font-weight:950 !important; box-shadow:0 10px 24px rgba(14,165,233,.25) !important; }}
    .workzo-title {{ color:#fff !important; font-size:1.45rem !important; font-weight:950 !important; letter-spacing:-.04em !important; line-height:1 !important; white-space:nowrap !important; }}
    .workzo-title span {{ color:#22d3ee !important; }}
    .workzo-subtitle {{ color:#cbd5e1 !important; font-size:.82rem !important; font-weight:650 !important; margin-top:.25rem !important; white-space:nowrap !important; overflow:hidden !important; text-overflow:ellipsis !important; max-width:380px !important; }}
    .workzo-header-right {{ display:flex !important; align-items:center !important; gap:.75rem !important; }}
    .workzo-back {{ color:#cbd5e1 !important; text-decoration:none !important; border:1px solid rgba(148,163,184,.28) !important; border-radius:999px !important; padding:.42rem .68rem !important; font-weight:850 !important; font-size:.78rem !important; background:rgba(15,23,42,.42) !important; white-space:nowrap !important; }}
    .workzo-progress-wrap {{ min-width:220px !important; }}
    .workzo-progress-top {{ display:flex !important; justify-content:space-between !important; color:#cbd5e1 !important; font-size:.72rem !important; font-weight:850 !important; margin-bottom:.28rem !important; }}
    .workzo-progress-bar {{ height:7px !important; border-radius:999px !important; background:rgba(148,163,184,.18) !important; overflow:hidden !important; }}
    .workzo-progress-fill {{ height:100% !important; width:{progress_pct}% !important; border-radius:999px !important; background:linear-gradient(90deg,#22d3ee,#22c55e) !important; }}
    .workzo-progress-steps {{ display:flex !important; gap:.35rem !important; margin-top:.34rem !important; }}
    .workzo-step {{ color:#cbd5e1 !important; border:1px solid rgba(148,163,184,.22) !important; background:rgba(15,23,42,.42) !important; border-radius:999px !important; padding:.16rem .42rem !important; font-size:.63rem !important; font-weight:850 !important; white-space:nowrap !important; }}
    .workzo-step.done {{ color:#67e8f9 !important; border-color:rgba(34,211,238,.45) !important; background:rgba(8,145,178,.18) !important; }}
    .workzo-beta {{ color:#67e8f9 !important; border:1px solid rgba(103,232,249,.42) !important; background:rgba(8,145,178,.16) !important; border-radius:999px !important; padding:.38rem .72rem !important; font-size:.7rem !important; font-weight:950 !important; letter-spacing:.04em !important; white-space:nowrap !important; }}
    @media (max-width:760px) {{
        .workzo-header {{ width:calc(100vw - 1rem) !important; top:.45rem !important; border-radius:18px !important; padding:.65rem .75rem !important; }}
        .workzo-logo {{ width:44px !important; height:44px !important; min-width:44px !important; }}
        .workzo-title {{ font-size:1.16rem !important; }}
        .workzo-subtitle {{ font-size:.70rem !important; max-width:150px !important; }}
        .workzo-progress-wrap, .workzo-back {{ display:none !important; }}
        .workzo-beta {{ font-size:.62rem !important; padding:.32rem .52rem !important; }}
    }}
    </style>
    <div class="workzo-header">
        <a class="workzo-brand workzo-home-link" href="?page=dashboard&home=1" target="_self" title="Go to dashboard">
            {logo_html}
            <div>
                <div class="workzo-title">WorkZo <span>AI</span></div>
                <div class="workzo-subtitle">Your guided AI career system</div>
            </div>
        </a>
        <div class="workzo-header-right">
            {back_html}
            <div class="workzo-progress-wrap">
                <div class="workzo-progress-top"><span>{'Interview setup complete' if stage == 'Interview' else stage}</span><span>{'AI recruiter ready' if stage == 'Interview' else ('Step 1/3' if int(progress_pct or 0) == 0 else 'In progress')}</span></div>
                <div class="workzo-progress-bar"><div class="workzo-progress-fill"></div></div>
                <div class="workzo-progress-steps">
                    <span class="workzo-step {'done' if cv_done else ''}">{cv_mark} CV</span>
                    <span class="workzo-step {'done' if job_done else ''}">{job_mark} Jobs</span>
                    <span class="workzo-step {'done' if interview_done else ''}">{interview_mark} Interview</span>
                </div>
            </div>
            <div class="workzo-beta">BETA</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# =========================================================
# SAMPLE DATA DEMO FLOW
# =========================================================
SAMPLE_CV_TEXT = """
ALEX MORGAN
Junior Data Analyst | IT Support Specialist
Berlin, Germany | alex.morgan@example.com | +49 151 00000000 | linkedin.com/in/alexmorgan-demo

PROFESSIONAL SUMMARY
Junior Data Analyst with a technical support background and hands-on experience in SQL, Python, Excel, Tableau, Power BI, and customer-facing problem solving. Strong at turning support tickets, user issues, and operational data into clear dashboards, insights, and process improvements. Looking for junior data analyst, reporting analyst, or data-focused customer operations roles.

CORE SKILLS
SQL, Python, pandas, Excel, Tableau, Power BI, Data Cleaning, Data Visualization, Dashboard Development, Ticket Analysis, KPI Reporting, Technical Support, SaaS Support, Incident Management, Root Cause Analysis, Process Documentation, Stakeholder Communication

PROFESSIONAL EXPERIENCE
IT Support Specialist | BrightDesk Solutions | Berlin, Germany | 2021 - 2023
- Resolved software, login, access, and workflow issues for business users through ticketing and remote troubleshooting.
- Analyzed recurring support tickets to identify issue patterns, common root causes, and process improvement opportunities.
- Created Excel reports and simple dashboards to track ticket volume, response time, resolution time, and repeated customer pain points.
- Collaborated with product and operations teams to document bugs, clarify user needs, and improve support workflows.

Customer Support Analyst | Northstar Digital Services | 2019 - 2021
- Supported customers with onboarding, product usage questions, and technical troubleshooting.
- Used Excel reports and basic SQL queries to summarize issue trends, customer requests, and service performance.
- Prepared weekly summaries for team leads highlighting common questions, unresolved blockers, and improvement ideas.

PROJECTS
Support Ticket Analytics Dashboard
- Built a Tableau dashboard using sample support data to analyze ticket categories, resolution time, volume trends, and customer impact.
- Used Python and pandas to clean raw ticket exports and prepare analysis-ready datasets.

E-Scooter Data Pipeline
- Collected public data using APIs and Python, cleaned the data, and prepared basic visual insights for operational planning.

EDUCATION
Data Science Bootcamp | WBS Coding School | 2024
Bachelor's Degree | Demo University | 2018

LANGUAGES
English - Professional | German - A2/B1 learning
""".strip()

SAMPLE_JOB_DESCRIPTION = """
Junior Data Analyst / IT Support Analyst
Location: Germany, hybrid or remote

We are looking for a motivated Junior Data Analyst with strong technical support experience to help analyze support data, build dashboards, and improve internal processes. The ideal candidate can work with SQL, Python, Excel, and Tableau or Power BI, and can communicate clearly with business and technical stakeholders.

Responsibilities:
- Analyze customer support and operational data to identify trends and improvement opportunities.
- Build dashboards and reports using Tableau, Power BI, or similar tools.
- Use SQL and Python to clean, transform, and analyze datasets.
- Support incident management, root cause analysis, and process documentation.
- Collaborate with product, support, and operations teams.

Requirements:
- Experience with SQL, Python, Excel, and data visualization.
- Understanding of IT support, ticketing systems, or ITSM processes.
- Strong communication skills and ability to explain technical topics clearly.
- Experience with dashboards, reporting, APIs, or cloud tools is a plus.
- English fluency; German communication skills are a plus.
""".strip()


def load_workzo_sample_data() -> None:
    """Load a complete demo profile so testers can understand the product before uploading private data."""
    st.session_state.country = "Germany"
    st.session_state.migration_country = "Germany"
    _sample_lang = st.session_state.get("preferred_language") or st.session_state.get("language") or "English"
    st.session_state.preferred_language = _sample_lang
    st.session_state.language = _sample_lang
    st.session_state.ui_language = _sample_lang
    st.session_state.response_language = _sample_lang
    st.session_state.user_status = "Career changer"
    st.session_state.career_goal = "Move from IT Support into Data Analyst / IT Support Analyst roles in Germany."

    st.session_state.cv_mode = "Sample Resume"
    st.session_state.cv_text = SAMPLE_CV_TEXT
    st.session_state.clean_structured_cv_text = SAMPLE_CV_TEXT
    st.session_state.generated_country_cv_text = SAMPLE_CV_TEXT
    st.session_state.improved_cv_text_v92 = ""

    st.session_state.last_understand_job_description = SAMPLE_JOB_DESCRIPTION
    st.session_state.improve_cv_for_job_desc = SAMPLE_JOB_DESCRIPTION
    st.session_state.last_prepare_job_description = SAMPLE_JOB_DESCRIPTION
    st.session_state.job_desc_v42 = SAMPLE_JOB_DESCRIPTION
    st.session_state.doc_tools_job_desc = SAMPLE_JOB_DESCRIPTION
    st.session_state.interview_jd_text_v117 = SAMPLE_JOB_DESCRIPTION

    st.session_state.structured_cv_json = {
        "personal_info": {
            "name": "Alex Morgan",
            "title": "Junior Data Analyst | IT Support Analyst",
            "email": "alex.morgan@example.com",
            "phone": "+49 151 00000000",
            "city": "Berlin, Germany",
            "linkedin": "linkedin.com/in/alexmorgan-demo",
        },
        "summary": "Junior Data Analyst with hands-on experience in Python, SQL, Tableau, Excel, technical support operations, dashboard development, and process improvement.",
        "skills": ["Python", "SQL", "Tableau", "Excel", "pandas", "ITIL/ITSM", "Technical Support", "Incident Management", "Root Cause Analysis", "GCP"],
        "experience": [
            {"role": "IT Support Specialist", "company": "BrightDesk Solutions", "start_date": "2021", "end_date": "2023", "bullets": ["Resolved software and account-related support requests through ticketing and remote troubleshooting.", "Analyzed recurring support tickets to identify common issues and recommend process improvements.", "Created internal documentation that improved handover quality."]},
            {"role": "Customer Support Analyst", "company": "Northstar Digital Services", "start_date": "2019", "end_date": "2021", "bullets": ["Supported customers with onboarding, product usage questions, and technical troubleshooting.", "Used Excel and basic SQL reports to track issue trends, customer requests, and service performance."]},
        ],
        "projects": [
            {"name": "Support Ticket Dashboard", "bullets": ["Built a Tableau dashboard to analyze ticket volume, resolution time, issue categories, and customer impact."]},
            {"name": "API Data Automation", "bullets": ["Created Python scripts to collect public API data, clean the results, and prepare a reusable reporting dataset."]},
        ],
        "education": [
            {"degree": "Data Analytics Bootcamp", "school": "Digital Skills Academy", "date": "2024"},
            {"degree": "Bachelor of Science in Business Information Systems", "school": "Sample State University", "date": "2016 - 2019"},
        ],
        "languages": ["English: Fluent", "German: Intermediate"],
    }
    st.session_state.structured_cv_profile = st.session_state.structured_cv_json

    sample_job_analysis = """
**Job Fit: Strong but needs targeting**

**Matches**
- Python, SQL, Tableau, Excel, and data visualization are already present.
- Technical support, ticket analysis, troubleshooting, and customer communication match the hybrid Data Analyst / IT Support Analyst profile.
- Data pipeline and API projects support the transition into analytics.

**Gaps to fix before applying**
- Add keywords such as incident management, root cause analysis, reporting, dashboard development, and stakeholder communication.
- Make the CV headline more focused for this role.
- Add one or two bullets showing how support experience connects to data/process improvement.

**Next step**
Improve the CV for this job, then prepare interview stories around SQL troubleshooting, dashboard projects, and customer-facing problem solving.
""".strip()
    st.session_state.latest_job_analysis = sample_job_analysis
    st.session_state.latest_cv_analysis = "Sample profile loaded. Try Improve CV, Find Jobs, Prepare for Job, or Work-O-Bot."
    st.session_state.job_fit_score_value = 74
    st.session_state.skill_gap_score_value = 26
    st.session_state.interview_score_value = 68

    # Build stable, deterministic dashboard scores immediately without waiting for an AI call.
    try:
        cached = build_rule_based_dashboard_cache(SAMPLE_CV_TEXT)
        cached.update({
            "profile_summary": "Sample profile: Junior Data Analyst / IT Support Analyst, with Python, SQL, Tableau, support-data analysis, dashboards, and customer-facing troubleshooting experience.",
            "current_role_detected": "Junior Data Analyst / IT Support Analyst",
            "key_skills_detected": ["Python", "SQL", "Tableau", "Technical Support", "ITIL/ITSM", "Data Visualization"],
            "suggested_roles_detected": ["Junior Data Analyst", "IT Support Analyst", "Service Desk Analyst", "Technical Support Engineer"],
            "resume_strengths": ["Clear technical support background", "Relevant analytics tools are present", "Projects support the career transition", "Good country/language context for Germany"],
            "resume_improvements": ["Add more job-specific keywords", "Tighten the headline for one target role", "Connect support achievements to data/process impact", "Add dashboard/reporting examples"],
        })
        apply_dashboard_cache(cached)
        st.session_state.dashboard_cache[make_cv_hash(SAMPLE_CV_TEXT, "Germany")] = cached
    except Exception:
        pass

    st.session_state.onboarding_complete = True
    sync_navigation_state("dashboard")
    track_event("sample_data_loaded", "Sample Demo", {"source": "landing_or_onboarding"})


def render_sample_data_button(location: str = "top") -> None:
    """Clean demo CTA for testers who do not want to upload a CV first."""
    st.markdown("#### " + txt("just_exploring"))
    st.caption(txt("sample_mode_intro") if "sample_mode_intro" in globals().get("UI_TEXT", {}).get(ui_lang(), {}) else ui_label("Load a generic sample CV and job description to see the full WorkZo workflow instantly. No private data needed."))
    c1, c2 = st.columns([1.6, 1])
    with c1:
        st.markdown(f"<div class=\"workzo-demo-note\"><b>{html.escape(txt('sample_mode_title'))}</b><br>{html.escape(txt('sample_mode_copy'))}</div>", unsafe_allow_html=True)
    with c2:
        if st.button(txt("try_sample_resume"), type="primary", use_container_width=True, key=f"sample_resume_{location}"):
            with st.status(txt("loading_sample"), expanded=True) as status:
                st.write(txt("adding_sample_cv"))
                st.write(txt("adding_sample_job"))
                st.write(txt("preparing_dashboard"))
                load_workzo_sample_data()
                status.update(label=txt("sample_ready"), state="complete")
            st.rerun()


def show_landing_page():
    """Modern SaaS-style landing page: one hero, one CTA, one product preview."""
    apply_workzo_v75_global_css()
    maybe_scroll_to_top()
    try:
        render_workzo_header()
    except Exception:
        pass

    st.markdown("""
    <style id="workzo-landing-product-hero-css">
    .workzo-landing-shell {
        max-width: 1180px;
        margin: 0 auto;
        padding: 0.4rem 0 0.6rem 0;
    }
    .workzo-landing-hero-v2 {
        position: relative;
        overflow: hidden;
        display: grid;
        grid-template-columns: minmax(0, 1.08fr) minmax(320px, .92fr);
        gap: 2rem;
        align-items: center;
        min-height: 430px;
        padding: 3rem 3.2rem;
        border-radius: 30px;
        border: 1px solid rgba(34, 211, 238, .28);
        background:
            radial-gradient(circle at 80% 20%, rgba(37, 99, 235, .34), transparent 28%),
            radial-gradient(circle at 15% 15%, rgba(20, 184, 166, .28), transparent 25%),
            linear-gradient(135deg, rgba(3, 16, 42, .98), rgba(8, 30, 68, .96));
        box-shadow: 0 26px 80px rgba(2, 6, 23, .42);
    }
    .workzo-landing-hero-v2:before {
        content: "";
        position: absolute;
        inset: 0;
        background-image: linear-gradient(120deg, rgba(255,255,255,.05) 0 1px, transparent 1px 90px);
        opacity: .28;
        pointer-events: none;
    }
    .workzo-landing-copy, .workzo-preview-card {
        position: relative;
        z-index: 1;
    }
    .workzo-kicker {
        color: #67e8f9;
        font-size: .78rem;
        font-weight: 900;
        letter-spacing: .22em;
        text-transform: uppercase;
        margin-bottom: 1rem;
    }
    .workzo-landing-title-v2 {
        color: #fff;
        font-size: clamp(2.25rem, 5vw, 4.35rem);
        line-height: 1.03;
        letter-spacing: -.055em;
        font-weight: 950;
        margin: 0 0 1.1rem 0;
        max-width: 780px;
    }
    .workzo-landing-subtitle-v2 {
        color: #cbd5e1;
        font-size: clamp(1rem, 1.6vw, 1.18rem);
        line-height: 1.55;
        max-width: 700px;
        margin-bottom: 1.35rem;
    }
    .workzo-trust-row {
        display: flex;
        gap: .55rem;
        flex-wrap: wrap;
        margin-top: .7rem;
    }
    .workzo-trust-chip {
        color: #dbeafe;
        border: 1px solid rgba(148, 163, 184, .22);
        background: rgba(15, 23, 42, .36);
        border-radius: 999px;
        padding: .48rem .72rem;
        font-size: .82rem;
        font-weight: 750;
    }
    .workzo-preview-card {
        border-radius: 26px;
        padding: 1.35rem;
        border: 1px solid rgba(34, 211, 238, .26);
        background: rgba(2, 6, 23, .46);
        box-shadow: 0 18px 50px rgba(2, 6, 23, .32);
        backdrop-filter: blur(8px);
    }
    .workzo-preview-title {
        color: #fff;
        font-size: 1.05rem;
        font-weight: 900;
        margin-bottom: .25rem;
    }
    .workzo-preview-subtitle {
        color: #94a3b8;
        font-size: .88rem;
        margin-bottom: 1rem;
    }
    .workzo-preview-metric {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        padding: .9rem 1rem;
        margin-bottom: .75rem;
        border-radius: 18px;
        background: rgba(15, 23, 42, .72);
        border: 1px solid rgba(148, 163, 184, .18);
    }
    .workzo-preview-label {
        color: #e2e8f0;
        font-weight: 800;
        font-size: .92rem;
    }
    .workzo-preview-value {
        color: #67e8f9;
        font-weight: 950;
        font-size: 1.25rem;
    }
    .workzo-next-card {
        margin-top: .95rem;
        border-radius: 20px;
        padding: 1rem;
        background: linear-gradient(135deg, rgba(8, 47, 73, .86), rgba(30, 41, 59, .72));
        border: 1px solid rgba(34, 211, 238, .24);
        color: #e0f2fe;
    }
    .workzo-next-card strong { color: #fff; }
    .st-key-landing_start_with_cv button {
        min-height: 56px !important;
        max-width: 280px !important;
        border-radius: 16px !important;
        font-size: 1rem !important;
        font-weight: 900 !important;
        box-shadow: 0 16px 38px rgba(239, 68, 68, .26) !important;
    }
    @media (max-width: 900px) {
        .workzo-landing-hero-v2 {
            grid-template-columns: 1fr;
            padding: 1.35rem 1.1rem;
            min-height: auto;
            border-radius: 24px;
            gap: 1.1rem;
        }
        .workzo-landing-title-v2 { font-size: clamp(2rem, 10vw, 2.75rem); }
        .workzo-preview-card { padding: 1rem; }
        .st-key-landing_start_with_cv button { max-width: 100% !important; }
    }
    </style>
    <div class="workzo-landing-shell">
      <div class="workzo-landing-hero-v2">
        <div class="workzo-landing-copy">
          <div class="workzo-kicker">Real Interview Practice</div>
          <h1 class="workzo-landing-title-v2">Practice real interviews using your CV and job description.</h1>
          <div class="workzo-landing-subtitle-v2">
            Upload or create your CV, add a job description later, and prepare for realistic interview practice based on your profile.
          </div>
          <div class="workzo-trust-row">
            <span class="workzo-trust-chip">CV optimization</span>
            <span class="workzo-trust-chip">Job matching</span>
            <span class="workzo-trust-chip">Real Interview AI</span>
          </div>
        </div>
        <div class="workzo-preview-card">
          <div class="workzo-preview-title">Your career snapshot</div>
          <div class="workzo-preview-subtitle">A quick preview of what WorkZo helps you improve.</div>
          <div class="workzo-preview-metric"><span class="workzo-preview-label">CV Match</span><span class="workzo-preview-value">72%</span></div>
          <div class="workzo-preview-metric"><span class="workzo-preview-label">Interview Readiness</span><span class="workzo-preview-value">58%</span></div>
          <div class="workzo-preview-metric"><span class="workzo-preview-label">Next Step</span><span class="workzo-preview-value">Interview</span></div>
          <div class="workzo-next-card"><strong>Next:</strong> Upload your CV and get a guided plan.</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 1.15, 1])
    with c2:
        if st.button("🚀 Start with your CV", type="primary", use_container_width=True, key="landing_start_with_cv"):
            st.session_state["page"] = "onboarding"
            st.session_state["nav_page"] = "onboarding"
            st.session_state["onboarding_complete"] = False
            try:
                st.query_params["page"] = "onboarding"
            except Exception:
                pass
            request_scroll_to_top()
            st.rerun()


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


SMART_CREATE_ROLE_OPTIONS = [
    "Data Analyst", "Junior Data Analyst", "Business Analyst", "IT Support Specialist", "Help Desk Analyst",
    "Technical Support Engineer", "Customer Success Manager", "Customer Support Specialist", "Service Desk Analyst",
    "Python Developer", "QA Tester", "Project Coordinator", "Product Support Specialist", "Other",
]
SMART_CREATE_SKILL_OPTIONS = sorted(set(POPULAR_SKILLS + [
    "Power Query", "Power Pivot", "Looker Studio", "NumPy", "Statistics", "Dashboard Development",
    "Reporting", "ETL", "REST APIs", "Web Scraping", "Ticketing Systems", "ITSM", "Jira",
    "ServiceDesk Plus", "Incident Management", "Root Cause Analysis", "Documentation", "Stakeholder Communication",
]))
SMART_CREATE_LANGUAGE_OPTIONS = [
    "English - Fluent", "English - Professional", "English - Intermediate", "German - A1", "German - A2",
    "German - B1", "German - B2", "German - C1", "Tamil - Native", "Hindi - Fluent",
    "Malayalam - Native", "French - Basic", "Spanish - Basic", "Dutch - Basic",
]
SMART_CREATE_CERT_OPTIONS = [
    "Data Science Bootcamp", "Data Analytics Bootcamp", "Google Data Analytics Certificate", "Microsoft Excel Advanced",
    "Power BI Certificate", "Tableau Certificate", "AWS Cloud Practitioner", "Google Cloud Fundamentals",
    "ITIL Foundation", "Scrum Fundamentals", "Python Certificate", "SQL Certificate",
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
    # WorkZo user insights: show once, inside render flow only. Never call at module import time.
    try:
        if callable(globals().get("show_user_identity_prompt")):
            show_user_identity_prompt()
    except Exception:
        pass
    maybe_scroll_to_top()
    try:
        render_workzo_header()
    except Exception:
        pass
    # WorkZo v36: sync language BEFORE rendering labels, so onboarding never shows mixed languages.
    try:
        _chosen_lang = st.session_state.get("onboarding_preferred_language") or st.session_state.get("preferred_language") or "English"
        if callable(globals().get("workzo_set_language_everywhere")):
            workzo_set_language_everywhere(_chosen_lang)
        elif callable(globals().get("set_single_preferred_language")):
            set_single_preferred_language(_chosen_lang)
    except Exception:
        pass
    st.subheader(txt("welcome_workzo"), help=txt("app_info_help"))
    st.caption(txt("onboarding_subtitle"))
    render_sample_data_button("onboarding")

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
    _old_lang = st.session_state.get("preferred_language") or st.session_state.get("language") or "English"
    if callable(globals().get("workzo_set_language_everywhere")):
        workzo_set_language_everywhere(preferred_language)
    else:
        set_single_preferred_language(preferred_language)
    if preferred_language != _old_lang:
        try:
            st.query_params["wz_lang"] = preferred_language
        except Exception:
            pass
        st.rerun()

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

    if "career changer" in user_status.lower():
        career_change_goal = st.text_input(
            "What role would you like to move into?",
            value=st.session_state.get("target_role", ""),
            placeholder="Example: Data Analyst, Customer Success Manager, IT Support"
        )
        if career_change_goal.strip():
            st.session_state.target_role = career_change_goal.strip()

    migration_country = ""
    if "migrate" in user_status.lower() or "abroad" in user_status.lower():
        migration_default = st.session_state.get("migration_country") or st.session_state.get("country") or "Germany"
        migration_index = country_options.index(migration_default) if migration_default in country_options else 0
        migration_country = st.selectbox(
            txt("migration_country"),
            country_options,
            index=migration_index
        )

    # CV review is no longer shown during onboarding. Users review/edit the structured CV inside Improve / Update CV.
    if st.session_state.get("cv_review_required"):
        st.session_state.cv_review_required = False

    st.markdown(f"### {txt('resume_input')}")
    st.caption(txt("resume_choice_caption"))

    if "cv_mode" not in st.session_state:
        st.session_state.cv_mode = ""

    st.markdown(
        f"<div class='workzo-mini-note'>{html.escape(txt('privacy_short'))}</div>",
        unsafe_allow_html=True
    )

    c_upload, c_create, c_linkedin = st.columns(3, gap="large")

    def _cv_mode_card(col, mode_value: str, display_label: str, copy: str, key: str):
        with col:
            active = st.session_state.get("cv_mode") == mode_value
            label = ("✓ " if active else "") + display_label
            with st.container(border=True):
                st.markdown(f"**{label}**")
                st.caption(copy)
                if st.button(display_label, key=key, use_container_width=True):
                    st.session_state.cv_mode = mode_value
                    request_scroll_to_top()
                    st.rerun()

    _cv_mode_card(c_upload, "Upload CV", txt("upload_cv"), txt("upload_cv_copy"), "choose_upload_cv")
    _cv_mode_card(c_create, "Create CV", txt("create_cv"), txt("create_cv_copy"), "choose_create_cv")
    _cv_mode_card(c_linkedin, "Import LinkedIn", txt("import_linkedin"), txt("import_linkedin_copy"), "choose_linkedin_cv")

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
            st.success(txt("cv_uploaded_success"))

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
                st.caption(txt("choose_pdf_txt"))

        elif cv_mode == "Import LinkedIn":
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
                target_role_choice = st.selectbox("Target role", [""] + SMART_CREATE_ROLE_OPTIONS, key="onboarding_target_role_smart")
                if target_role_choice == "Other":
                    target_role = st.text_input(txt("target_role_optional"), placeholder="Example: Data Analyst / IT Support Specialist")
                else:
                    target_role = target_role_choice
                education_level = st.selectbox(txt("education_level"), EDUCATION_LEVELS, index=0, key="onboarding_education_level")
                selected_skills = st.multiselect(txt("suggested_skills"), SMART_CREATE_SKILL_OPTIONS, key="onboarding_suggested_skills", placeholder="Start typing skills")
                selected_languages = st.multiselect(txt("languages_label"), SMART_CREATE_LANGUAGE_OPTIONS, key="onboarding_languages_smart", placeholder="Start typing languages")
                languages = ", ".join(selected_languages)

            summary = st.text_area(txt("summary"), placeholder="Example: Customer support professional with SaaS experience, interested in data and technology roles.")
            skills = st.text_area(txt("skills"), placeholder="Example: SQL, Excel, Python, customer support, problem solving, CRM tools")
            if selected_skills:
                skills = ", ".join(dict.fromkeys([x.strip() for x in (skills.split(",") if skills else [])] + selected_skills))
            experience = st.text_area(txt("experience"), placeholder="Example: Technical Support Associate, ABC Software, 2020-2024 — handled customer tickets and troubleshooting.")
            projects = st.text_area(txt("projects_label"), placeholder="Example: Built a dashboard to track monthly sales and customer trends.")
            selected_certifications = st.multiselect("Certificates / Courses", SMART_CREATE_CERT_OPTIONS, key="onboarding_certifications_smart", placeholder="Start typing certificates")
            certifications = st.text_area(txt("cert_courses"), placeholder="Example: Google Data Analytics Certificate, Excel Advanced, AWS basics")
            if selected_certifications:
                certifications = ", ".join(dict.fromkeys([x.strip() for x in (certifications.split(",") if certifications else [])] + selected_certifications))
            education = st.text_area(txt("education"), placeholder="Example: Bachelor of Computer Science, University of Toronto, 2020-2024")
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
                    st.warning(txt("warn_enter_details"))
                    return

                with st.spinner(txt("creating_cv_draft")):
                    ai_cv = generate_cv_from_user_details(cv_text_input, migration_country if migration_country else country, user_status)
                    if ai_cv and not ai_cv.startswith("ERROR:"):
                        st.session_state.created_cv_ai_output = ai_cv
                        cv_text_input = ai_cv

            st.session_state.country = country
            st.session_state.user_status = user_status
            st.session_state.migration_country = migration_country if migration_country else country
            st.session_state.cv_mode = cv_mode
            if target_role:
                st.session_state.target_role = target_role
                st.session_state.detected_target_role = target_role

            # Build a clean structured CV for EVERY input method: upload, create CV, and LinkedIn import.
            # This makes later editing, template rendering, translation, and PDF download reliable.
            st.session_state.raw_cv_extraction = cv_text_input
            with st.spinner("Extracting resume facts into clean editable sections..."):
                structured_data = extract_structured_resume_json(cv_text_input, active_application_country(), user_status)
            clean_from_sections = _format_structured_resume_profile(structured_data)
            st.session_state.structured_cv_json = structured_data if isinstance(structured_data, dict) else {}
            st.session_state.pending_structured_cv_json = {}
            st.session_state.cv_review_required = False
            if clean_from_sections and len(clean_from_sections.strip()) > 120:
                st.session_state.structured_cv_profile = clean_from_sections
                st.session_state.clean_structured_cv_text = clean_from_sections
                cv_text_input = clean_from_sections
            track_event("cv_structured_profile_created", "Onboarding", {"cv_mode": cv_mode, "target_country": active_application_country()})

            st.session_state.cv_text = clean_cv_text(cv_text_input)
            workzo_sync_user_profile()
            track_event("cv_ready", "Onboarding", {"cv_mode": cv_mode, "user_status": user_status, "target_country": st.session_state.get("migration_country", country)})
            st.session_state.onboarding_complete = True
            sync_navigation_state("dashboard")

            with st.spinner(txt("reading_resume_dashboard")):
                analyze_resume_dashboard_stable(st.session_state.cv_text, force_refresh=True)

            request_scroll_to_top()
            st.session_state.nav_page = "dashboard"
            st.rerun()

# =========================================================
# =========================================================
# WORK-O-BOT
# =========================================================
def workobot_intro_message() -> str:
    return """Hi, I'm Work-O-Bot

If you have uploaded or created a CV, I can use it for personalized answers.

I can help you with:
• CV improvement
• Interview preparation
• Job search strategy
• Skill gap analysis
• Career change guidance
• Work-related language practice

Ask me anything about your career."""



def get_workzo_cv_context_for_bot(max_chars: int = 7000) -> str:
    """Return the best available CV/profile text for Work-O-Bot.

    This centralizes all CV keys used across onboarding, CV tools, translation,
    structured parsing, and dashboard cache so the bot never says it cannot read
    a CV when one was already uploaded or created.
    """
    keys = [
        "cv_text",
        "clean_structured_cv_text",
        "structured_cv_profile",
        "generated_country_cv_text",
        "created_cv_ai_output",
        "raw_cv_extraction",
        "cv_profile_raw",
        "improved_cv_text_v92",
        "translated_cv_text",
        "latest_translated_cv_text",
    ]
    parts = []
    seen = set()
    for key in keys:
        try:
            value = st.session_state.get(key, "")
        except Exception:
            value = ""
        if isinstance(value, dict):
            try:
                if callable(globals().get("_format_structured_resume_profile")):
                    value = _format_structured_resume_profile(value)
                else:
                    value = str(value)
            except Exception:
                value = str(value)
        value = str(value or "").strip()
        if len(value) < 40:
            continue
        marker = value[:300].lower()
        if marker in seen:
            continue
        seen.add(marker)
        parts.append(value)

    # Structured JSON fallback
    try:
        structured = st.session_state.get("structured_cv_json") or st.session_state.get("approved_structured_cv_json") or {}
        if isinstance(structured, dict) and structured:
            if callable(globals().get("_format_structured_resume_profile")):
                structured_text = _format_structured_resume_profile(structured)
            else:
                structured_text = str(structured)
            if structured_text and len(structured_text) > 40:
                parts.append(str(structured_text))
    except Exception:
        pass

    combined = "\n\n--- CV/Profile source ---\n\n".join(parts).strip()
    return combined[:max_chars] if combined else ""


def workzo_bot_has_cv_context() -> bool:
    try:
        return bool(get_workzo_cv_context_for_bot(500).strip())
    except Exception:
        return False

def workobot_context_snapshot() -> str:
    """Small private context packet so Work-O-Bot can answer like a personalized career coach."""
    cv_text = get_workzo_cv_context_for_bot(max_chars=7000)
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
    if any(x in text for x in ["interview", "mock", "question", "answer", "vorstellung", "gesprach"]):
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
    """Run Work-O-Bot with local rate-limit fallbacks so it never crashes if helpers are missing."""
    def _local_can_make_request() -> bool:
        fn = globals().get("can_make_request")
        if callable(fn):
            try:
                return bool(fn())
            except Exception:
                pass
        try:
            import time as _time
            max_requests = int(globals().get("MAX_REQUESTS_PER_HOUR", 25) or 25)
            if "request_count" not in st.session_state:
                st.session_state.request_count = 0
            if "first_request_time" not in st.session_state:
                st.session_state.first_request_time = _time.time()
            if _time.time() - float(st.session_state.first_request_time or _time.time()) > 3600:
                st.session_state.request_count = 0
                st.session_state.first_request_time = _time.time()
            return int(st.session_state.request_count or 0) < max_requests
        except Exception:
            return True

    def _local_register_request() -> None:
        fn = globals().get("register_request")
        if callable(fn):
            try:
                fn()
                return
            except Exception:
                pass
        try:
            import time as _time
            if "request_count" not in st.session_state:
                st.session_state.request_count = 0
            if "first_request_time" not in st.session_state:
                st.session_state.first_request_time = _time.time()
            st.session_state.request_count = int(st.session_state.request_count or 0) + 1
        except Exception:
            pass

    if not _local_can_make_request():
        return ui_label("I'm sorry, the hourly AI usage limit has been reached. Please try again later.") if callable(globals().get("ui_label")) else "I'm sorry, the hourly AI usage limit has been reached. Please try again later."

    _local_register_request()
    answer_lang = normalize_answer_language(st.session_state.get("preferred_language", "English"))
    intent = infer_workobot_intent(user_message)
    model_name = os.getenv("WORKZO_AI_MODEL") or get_streamlit_secret("WORKZO_AI_MODEL", "gpt-4o-mini")
    cv_context = get_workzo_cv_context_for_bot(max_chars=7000)
    jd_context = (
        st.session_state.get("selected_job_description")
        or st.session_state.get("last_understand_job_description")
        or st.session_state.get("improve_cv_for_job_desc")
        or st.session_state.get("interview_jd_text_v117")
        or st.session_state.get("current_job_description")
        or ""
    )
    cv_status_note = "CV is available and must be used for personalized answers." if cv_context else "No CV is currently available in session. Ask the user to upload or create a CV."

    system_prompt = f"""
You are Work-O-Bot, the AI career coach inside WorkZo AI.

Your role: {intent}

You help users with:
- CV improvement
- ATS and resume strategy
- job search decisions
- cover letter and recruiter messages
- interview preparation
- language practice for work
- skill gap planning
- career roadmap decisions

User context:
- Country: {st.session_state.get('country', 'Not specified')}
- Target market: {st.session_state.get('migration_country') or st.session_state.get('country', 'Not specified')}
- Career status: {st.session_state.get('user_status', 'Not specified')}
- Preferred language: {answer_lang}
- Resume score: {st.session_state.get('cv_score_value', st.session_state.get('resume_score', 'Not scored'))}
- ATS score: {st.session_state.get('ats_score_value', st.session_state.get('ats_score', 'Not scored'))}
- Company website/context: {st.session_state.get('target_company_website', 'Not provided')}
- CV status: {cv_status_note}

Uploaded CV/profile context available to Work-O-Bot:
{cv_context if cv_context else "No CV context available."}

Current/selected job description context:
{str(jd_context or "No job description selected yet.")[:3500]}

Rules:
1. Answer in {answer_lang}.
2. Be practical and specific.
3. Be honest. Do not invent experience, employers, dates, degrees, certifications, achievements, salary, company facts, or language level.
4. If company-specific information is missing, say what to verify instead of pretending.
5. If CV context is available, never say you cannot read the resume. Use the CV details directly and cite specific roles, skills, projects, gaps, and strengths from it.
6. If job description is missing, explain that job-specific advice will be stronger after the user adds one.
7. Give concise steps and copy-ready examples when useful.
"""
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": str(user_message or "")},
            ],
            temperature=0.45,
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        return f"Work-O-Bot error: {exc}"


def show_workobot():
    st.subheader(txt("workobot"))
    st.caption("Personal AI career coach based on your CV, country, target market, and selected language.")
    try:
        _bot_cv_context = get_workzo_cv_context_for_bot(max_chars=1200)
        if _bot_cv_context:
            st.markdown('<div id="workzo-bot-cv-context-status" style="border:1px solid rgba(34,211,238,.25);background:rgba(8,145,178,.12);border-radius:14px;padding:.65rem .8rem;margin:.5rem 0 1rem;color:#cbd5e1;"><b style="color:#67e8f9;">✅ Using your uploaded CV/profile</b> for personalized answers.</div>', unsafe_allow_html=True)
        else:
            st.info("📄 Upload or create your CV to get personalized Work-O-Bot answers.")
    except Exception:
        pass

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
            ("Mock test", "Create a role-specific mock interview test based on my CV, target role, and selected language. Ask only realistic employer interview questions and keep questions and answers in the same selected language."),
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


def clean_generated_cv_text_for_template(cv_text: str) -> str:
    """Post-process AI-generated CV text before preview/download.
    This fixes common issues from messy PDF extraction where contact details or section words
    leak into the wrong part of the resume.
    """
    text_value = strip_markdown_for_resume(normalize_resume_dates(cv_text or ""))
    text_value = text_value.replace("\r\n", "\n").replace("\r", "\n")

    # Repair frequent PDF/OCR spacing problems from two-column resumes.
    repairs = {
        r"Detail-orientedIT": "Detail-oriented IT",
        r"Specialistandaspiring": "Specialist and aspiring",
        r"\bLinked in\b": "LinkedIn",
        r"\blinked in\b": "LinkedIn",
        r"\bYou Tube\b": "YouTube",
        r"\bText Blob\b": "TextBlob",
        r"\bIn dian\b": "Indian",
        r"\bfor ms\b": "forms",
        r"\bin ternal\b": "internal",
        r"\bin tegration\b": "integration",
        r"\bin itiatives\b": "initiatives",
        r"\bin for m\b": "inform",
        r"Enginner": "Engineer",
        r"Manage Engine": "ManageEngine",
    }
    for pat, repl in repairs.items():
        text_value = re.sub(pat, repl, text_value, flags=re.IGNORECASE)

    # Remove chat/report headings that should never appear inside a CV.
    text_value = re.sub(r"(?im)^\s*(tailoring summary|fit level|main improvement|changes made|resume review|roast notes|why this is better|problem|replace with)\s*:?.*$", "", text_value)
    text_value = re.sub(r"(?im)^\s*\d+[A-Z]?\.\s*(Full Tailored CV|Full Resume Draft|Rebuilt CV|Country-Specific CV Draft)\s*$", "", text_value)

    # Remove lonely duplicated heading fragments produced by weak extraction.
    text_value = re.sub(r"(?im)^\s*(PROFESSIONAL|CORE|CONTACT|PROFILE|ADDITIONAL)\s*$", "", text_value)
    text_value = re.sub(r"\n{3,}", "\n\n", text_value)
    return sanitize_pdf_text(text_value.strip())

def parse_cv_sections_for_template(cv_text: str) -> Dict[str, str]:
    """
    More defensive parser for WorkZo-generated CVs.
    It does not try to preserve the uploaded CV layout. It extracts/moves contact lines,
    removes leaked headings, and rebuilds logical sections for preview/download.
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

    text = clean_generated_cv_text_for_template(cv_text)
    raw_lines = [line.strip(" \t|•") for line in text.splitlines() if line.strip()]
    if not raw_lines:
        return sections

    def is_email(s):
        return bool(re.search(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", s, flags=re.I))
    def is_phone(s):
        return bool(re.search(r"(?:\+\d{1,3}\s*)?(?:\(?\d{2,5}\)?[\s.-]*){2,}\d{2,}", s))
    def is_linkedin(s):
        return "linkedin" in s.lower() or "linked in" in s.lower()
    def is_location(s):
        lower = s.lower()
        return any(x in lower for x in ["wurzburg", "wuerzburg", "berlin", "munich", "germany", "chennai", "india", "straÃe", "strasse", "weg "]) or bool(re.search(r"\b\d{5}\b", s))
    def looks_like_name(s):
        cleaned = re.sub(r"[^A-Za-zÃÃUaouÃ ]", "", s).strip()
        if not cleaned:
            return False
        words = cleaned.split()
        return 1 <= len(words) <= 4 and not any(w.lower() in ["summary", "profile", "skills", "experience", "education", "projects"] for w in words)
    def looks_like_title(s):
        lower = s.lower()
        return any(x in lower for x in ["analyst", "engineer", "specialist", "developer", "manager", "consultant", "support", "scientist"])

    heading_map = {
        "summary": ["summary", "profile summary", "profile", "professional summary", "professional profile", "personal profile", "career profile", "about me", "career objective", "objective"],
        "skills": ["skills", "core skills", "technical skills", "expertise", "tools", "tools and technologies", "technical expertise", "kenntnisse"],
        "experience": ["experience", "work experience", "professional experience", "employment", "career history", "employment history", "berufserfahrung"],
        "projects": ["projects", "project", "academic projects", "projekte"],
        "education": ["education", "ausbildung", "academic", "studies", "academic background", "formation", "bildung"],
        "certifications": ["certification", "certifications", "courses", "training", "weiterbildung"],
        "languages": ["languages", "sprachen"],
    }
    all_heading_labels = {label for labels in heading_map.values() for label in labels}

    def clean_heading_key(line):
        normalized = re.sub(r"[^a-zA-Z ]", "", line).strip().lower()
        normalized = re.sub(r"\s+", " ", normalized)
        # Spaced-out all-caps headings: P R O F I L E  S U M M A R Y -> profile summary
        letters_only = normalized.replace(" ", "")
        spaced_map = {
            "profilesummary": "profile summary",
            "professionalsummary": "professional summary",
            "workexperience": "work experience",
            "professionalexperience": "professional experience",
            "coreskills": "core skills",
        }
        if letters_only in spaced_map:
            normalized = spaced_map[letters_only]
        return normalized

    name = ""
    role = ""
    contact_bits = []
    current = None
    bucket_lines = {k: [] for k in sections if k != "header"}

    for original in raw_lines:
        line = original.strip()
        if not line:
            continue
        normalized = clean_heading_key(line)
        if normalized in ["professional", "core", "contact", "profile", "additional"]:
            continue

        matched_key = None
        for key, labels in heading_map.items():
            if normalized in labels or any(normalized == label for label in labels):
                matched_key = key
                break
        if matched_key:
            current = matched_key
            continue

        # Contact details can appear anywhere in messy PDFs; move them to the header.
        if is_email(line) or is_phone(line) or is_linkedin(line) or is_location(line):
            cleaned_contact = re.sub(r"\s*\|\s*$", "", line).strip()
            if cleaned_contact and cleaned_contact not in contact_bits:
                contact_bits.append(cleaned_contact)
            continue

        # Detect name/title before first real section.
        if current is None:
            if not name and looks_like_name(line):
                name = " ".join(part.capitalize() if part.isupper() else part for part in line.split())
                continue
            if not role and looks_like_title(line):
                role = line.replace(" / ", " | ").replace("/", " | ")
                continue
            # If it is not clearly header, treat as summary.
            current = "summary"

        # Do not add fake placeholder certification text.
        if "list any relevant" in line.lower() or "details to confirm" in line.lower():
            continue

        # Guard against two-column extraction: route education-like lines to Education
        # instead of letting them leak under the name/profile section.
        edu_markers = ["university", "school", "college", "bootcamp", "bachelor", "master", "degree", "coding school", "science college"]
        if (current in [None, "summary"] and any(m in line.lower() for m in edu_markers)):
            bucket_lines.setdefault("education", []).append(line)
            continue

        bucket_lines.setdefault(current or "summary", []).append(line)

    # If generated CV started with name/title but parser missed them, recover from first two lines.
    if not name:
        for line in raw_lines[:6]:
            if looks_like_name(line) and not (is_email(line) or is_phone(line) or is_location(line) or is_linkedin(line)):
                name = " ".join(part.capitalize() if part.isupper() else part for part in line.split())
                break
    if not role:
        for line in raw_lines[:8]:
            if looks_like_title(line) and line != name:
                role = line.replace(" / ", " | ").replace("/", " | ")
                break

    # Remove accidental duplicated name/title/contact from buckets.
    for key, vals in list(bucket_lines.items()):
        cleaned_vals = []
        for line in vals:
            if name and line.strip().lower() == name.strip().lower():
                continue
            if role and line.strip().lower() == role.strip().lower():
                continue
            if is_email(line) or is_phone(line) or is_linkedin(line) or is_location(line):
                continue
            if clean_heading_key(line) in all_heading_labels:
                continue
            cleaned_vals.append(line)
        bucket_lines[key] = cleaned_vals

    # If summary is too fragmented, keep only the first meaningful paragraph/sentence-like lines.
    summary_vals = bucket_lines.get("summary", [])
    if summary_vals:
        # Remove single generic fragments like "in technical support" from summary when experience exists.
        summary_vals = [s for s in summary_vals if len(s.split()) >= 4 or any(x in s.lower() for x in ["analyst", "engineer", "specialist"])]
        bucket_lines["summary"] = summary_vals[:3]

    if not name:
        name = "Your Name"
    if not role:
        role = f"CV for {target_country}" if 'target_country' in globals() else "Professional CV"

    sections["header"] = "\n".join([name, role] + contact_bits[:4]).strip()
    for key, vals in bucket_lines.items():
        # Remove duplicate adjacent lines while preserving order.
        seen = set()
        unique = []
        for v in vals:
            marker = re.sub(r"\s+", " ", v.lower()).strip()
            if marker and marker not in seen:
                seen.add(marker)
                unique.append(v)
        sections[key] = "\n".join(unique).strip()

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

    # Specific template names first so the three German options do not look identical.
    if "german ats" in name or "no photo" in name or "ats" in name:
        return "Minimal ATS"
    if "student" in name or "werkstudent" in name or "graduate" in name or "intern" in name or "thesis" in name or "fresher" in name or "stage" in name or "entry-level" in name:
        return "Graduate Portfolio"
    if "lebenslauf" in name or "german" in name or "austria" in name or "swiss" in name or "dach" in name:
        return "German-Style Lebenslauf"
    if any(x in name for x in ["career change", "pivot", "returning", "newcomer"]):
        return "Career Pivot"
    if any(x in name for x in ["modern", "portfolio", "netherlands", "dutch", "singapore"]):
        return "Creative Modern"
    if any(x in name for x in ["france", "french", "classique"]):
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
            "Canadian Professional Resume": "Balanced Canadian resume: no photo, no date of birth, achievement-focused, recruiter-friendly, usually 1-2 pages.",
            "Canadian ATS Keyword Resume": "Strict ATS Canadian resume with simple formatting, strong keywords, skills and measurable impact bullets.",
            "Canadian Newcomer / Career Pivot Resume": "Useful for immigrants, newcomers, and career changers: highlights transferable experience and Canadian-style wording.",
        },
        "india": {
            "India Professional Resume": "Indian market resume with profile, skills, projects, experience and education; suitable for job portals.",
            "India ATS Resume": "Clean Naukri/LinkedIn-style resume with keywords, tools, achievements and project proof.",
            "India Fresher Resume": "Fresher-focused resume emphasizing education, projects, internships, tools and certifications.",
        },
        "france": {
            "France CV - Classique": "French-style CV with Profil, Experience, Formation, Competences and Langues; concise and structured.",
            "France ATS - International": "No-photo international French-market CV for online applications and multinational companies.",
            "France Stage / Alternance CV": "Student CV for stage, alternance, apprentissage and junior roles.",
        },
        "netherlands": {
            "Netherlands CV - Direct": "Dutch-style CV: direct, skills-focused, concise, no unnecessary personal details.",
            "Netherlands ATS CV": "Clean ATS CV for Dutch job portals and international companies.",
            "Netherlands Internship / Stage CV": "Stage/afstudeerstage focused CV for students and graduates.",
        },
        "australia": {
            "Australia Resume": "Australian resume style: 2-3 pages if needed, no photo, achievement-focused and recruiter-friendly.",
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
            "Portugal Internship CV": "Education/project-first CV for estagio, trainee and junior applications.",
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
Use a concise French-market structure: Profil, Experience professionnelle, Formation, Competences, Langues.
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
    st.html(build_visual_cv_html(sample_cv, template_name, target_country))

    with st.expander("What this template includes", expanded=False):
        st.markdown(get_template_instructions(template_name, target_country))

def generate_country_cv_template(cv_text: str, target_country: str, user_status: str, template_name: str = "ATS Classic", output_language: str = "English") -> str:
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
Output language for the resume/CV: {output_language}

{rules_text}

Template instructions:
{template_instructions}

Output rules:
- Use these exact section headings: 1. Country Fit Notes, 2. Full Resume Draft, 3. WorkZo Changes, 4. Missing Details to Confirm.
- Do not use markdown symbols like ###, **, or bullet characters outside the resume bullets.
- Section 1 must be 3 short bullets only: country fit, removed/kept details, ideal length.
- Section 2 must be the full copy-ready resume/CV only.
- Write the resume/CV fully in {output_language}. Do not mix languages.
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
    """Return the country every career feature should use.

Local/career-change users stay tied to their current country. Only users who
selected applying abroad / migration use the separate target market.
"""
    country = st.session_state.get("country") or st.session_state.get("onboarding_country") or "International"
    target = st.session_state.get("migration_country") or country
    if is_applying_abroad_status(st.session_state.get("user_status", "")):
        return target or country
    return country

def onboarding_country_for_cv() -> str:
    """Country context for CV/job/interview features."""
    return active_application_country()

def workzo_sync_user_profile() -> dict:
    """Single source of truth for profile-driven WorkZo features."""
    profile = {
        "career_status": st.session_state.get("user_status", ""),
        "current_country": st.session_state.get("country", ""),
        "target_country": active_application_country(),
        "preferred_language": st.session_state.get("preferred_language", "English"),
        "cv_mode": st.session_state.get("cv_mode", ""),
        "target_role": st.session_state.get("target_role", st.session_state.get("detected_target_role", "")),
        "cv_text": st.session_state.get("cv_text", ""),
    }
    st.session_state["user_profile"] = profile
    return profile

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




# =========================================================
# WorkZo FINAL live-preview override
# Purpose:
# - Stop using the old parser-based preview when the user is editing CV fields.
# - Experience/Education must come directly from the visible editable widgets.
# - This intentionally replaces the broken old build_visual_cv_html path.
# =========================================================

try:
    _workzo_legacy_build_visual_cv_html
except NameError:
    try:
        _workzo_legacy_build_visual_cv_html = build_visual_cv_html
    except Exception:
        _workzo_legacy_build_visual_cv_html = None

try:
    _workzo_legacy_render_cv_template_preview
except NameError:
    try:
        _workzo_legacy_render_cv_template_preview = render_cv_template_preview
    except Exception:
        _workzo_legacy_render_cv_template_preview = None


def _workzo_live_parse_simple_lines(text):
    import re
    return [
        re.sub(r"^[-•*]\s*", "", str(x or "").strip()).strip()
        for x in str(text or "").splitlines()
        if str(x or "").strip()
    ]


def _workzo_live_parse_experience_blocks(text):
    import re
    items = []
    raw = str(text or "").strip()
    if not raw:
        return items

    for block in re.split(r"\n\s*\n", raw):
        lines = [x.strip() for x in block.splitlines() if x.strip()]
        if not lines:
            continue

        header = lines[0].strip()
        parts = [p.strip() for p in header.split("|")]
        title = parts[0] if len(parts) >= 1 else ""
        company = parts[1] if len(parts) >= 2 else ""
        dates = parts[2] if len(parts) >= 3 else ""

        bullets = []
        for line in lines[1:]:
            clean = re.sub(r"^[-•*]\s*", "", line).strip()
            if clean:
                bullets.append(clean)

        # If a user pasted bullets without a header, still show them.
        if not title and not company and not dates and bullets:
            title = "Experience"

        if title or company or dates or bullets:
            items.append({
                "title": title,
                "company": company,
                "dates": dates,
                "bullets": bullets,
            })

    return items


def _workzo_live_parse_education_lines(text):
    items = []
    for line in str(text or "").splitlines():
        line = line.strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split("|")]
        items.append({
            "degree": parts[0] if len(parts) >= 1 else "",
            "institution": parts[1] if len(parts) >= 2 else "",
            "dates": parts[2] if len(parts) >= 3 else "",
        })
    return items


def _workzo_live_editor_prefixes():
    """Known prefixes plus any prefix discovered from *_experience widget keys."""
    prefixes = [
        "improved_cv_preview_v141",
        "improved_cv_preview_v92",
        "country_cv_preview_v141",
        "country_cv_preview_v92",
        "cv_preview",
    ]
    try:
        for key in list(st.session_state.keys()):
            if key.endswith("_experience"):
                prefixes.insert(0, key[:-len("_experience")])
    except Exception:
        pass

    seen = set()
    out = []
    for p in prefixes:
        if p and p not in seen:
            seen.add(p)
            out.append(p)
    return out


def _workzo_live_data_from_editor_prefix(prefix):
    """Build structured CV directly from current Streamlit widget values."""
    try:
        ss = st.session_state
    except Exception:
        return {}

    def get(field):
        return str(ss.get(f"{prefix}_{field}", "") or "").strip()

    has_any = any(get(field) for field in [
        "name", "role", "phone", "email", "location", "linkedin",
        "summary", "skills", "experience", "education", "projects",
        "languages", "certifications"
    ])
    if not has_any:
        return {}

    return {
        "full_name": get("name"),
        "target_role": get("role"),
        "contact": {
            "phone": get("phone"),
            "email": get("email"),
            "location": get("location"),
            "linkedin": get("linkedin"),
        },
        "professional_summary": get("summary"),
        "core_skills": _workzo_live_parse_simple_lines(get("skills")),
        "tools_technologies": [],
        "work_experience": _workzo_live_parse_experience_blocks(get("experience")),
        "education": _workzo_live_parse_education_lines(get("education")),
        "projects": [{"name": x, "bullets": []} for x in _workzo_live_parse_simple_lines(get("projects"))],
        "languages": _workzo_live_parse_simple_lines(get("languages")),
        "certifications": _workzo_live_parse_simple_lines(get("certifications")),
    }


def _workzo_live_has_real_sections(data):
    if not isinstance(data, dict):
        return False
    return bool(
        data.get("work_experience")
        or data.get("education")
        or data.get("professional_summary")
        or data.get("core_skills")
        or data.get("languages")
        or data.get("certifications")
    )


def _workzo_live_current_structured(cv_text=""):
    """
    Final source priority:
    1. Current visible editor widgets
    2. workzo_live_cv_structured
    3. improved_cv_structured_v92 / structured_cv_json
    4. text-to-structured fallback
    """
    try:
        for prefix in _workzo_live_editor_prefixes():
            data = _workzo_live_data_from_editor_prefix(prefix)
            if _workzo_live_has_real_sections(data):
                return data
    except Exception:
        pass

    try:
        for key in ["workzo_live_cv_structured", "improved_cv_structured_v92", "structured_cv_json"]:
            data = st.session_state.get(key)
            if isinstance(data, dict) and _workzo_live_has_real_sections(data):
                return data
    except Exception:
        pass

    try:
        if "workzo_cv_text_to_editable_sections" in globals():
            data = workzo_cv_text_to_editable_sections(cv_text or "")
            if _workzo_live_has_real_sections(data):
                return data
    except Exception:
        pass

    return {}


def build_visual_cv_html(cv_text: str, template_name: str, target_country: str) -> str:
    """
    Replacement for the old parser-based preview.
    This version checks the live editable widgets first, so Experience/Education
    appear in preview immediately after editing.
    """
    data = _workzo_live_current_structured(cv_text)

    try:
        if _workzo_live_has_real_sections(data) and "workzo_visual_cv_html_from_structured" in globals():
            # Force-save the same data so download/PDF paths see the same version.
            try:
                st.session_state["workzo_live_cv_structured"] = data
                if "workzo_build_cv_text_from_editable" in globals():
                    live_text = workzo_build_cv_text_from_editable(data)
                    st.session_state["workzo_live_cv_text"] = live_text
                    st.session_state["clean_structured_cv_text"] = live_text
                    st.session_state["cv_text"] = live_text
            except Exception:
                pass
            return workzo_visual_cv_html_from_structured(data, template_name, target_country)
    except Exception:
        pass

    # Last fallback only: old behavior for sample templates or if no live CV exists.
    if _workzo_legacy_build_visual_cv_html is not None:
        return _workzo_legacy_build_visual_cv_html(cv_text, template_name, target_country)

    return "<div style='padding:24px;background:white;color:#111827;'>No CV preview available.</div>"


def render_cv_template_preview(template_name: str, target_country: str, user_status: str):
    """
    Replacement preview renderer.
    Uses the user's current edited CV when available; otherwise shows the old sample.
    """
    st.markdown("### Template Preview")
    try:
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
    except Exception:
        pass

    try:
        live_text = (
            st.session_state.get("workzo_live_cv_text")
            or st.session_state.get("cv_editor_widget")
            or st.session_state.get("clean_structured_cv_text")
            or st.session_state.get("cv_text")
            or ""
        )
    except Exception:
        live_text = ""

    if not str(live_text or "").strip():
        try:
            live_text = build_template_sample_cv(template_name, target_country)
        except Exception:
            live_text = ""

    st.html(build_visual_cv_html(live_text, template_name, target_country))

    try:
        with st.expander("What this template includes", expanded=False):
            st.markdown(get_template_instructions(template_name, target_country))
    except Exception:
        pass

# =========================================================
# WorkZo v20 - Work-O-Bot safety patch
# =========================================================
if "register_request" not in globals():
    def register_request():
        return None


# =========================================================
# WorkZo v38 onboarding translation support
# =========================================================
try:
    if "UI_TEXT" in globals():
        UI_TEXT.setdefault("German", {}).update({
            "sample_mode_intro": "Lade einen generischen Beispiel-Lebenslauf und eine Stellenbeschreibung, um den kompletten WorkZo-Workflow sofort zu testen. Keine privaten Daten nötig.",
        })
        UI_TEXT.setdefault("French", {}).update({"sample_mode_intro": "Chargez un CV et une offre d’emploi exemples pour voir tout le workflow WorkZo instantanément. Aucune donnée privée nécessaire."})
        UI_TEXT.setdefault("Spanish", {}).update({"sample_mode_intro": "Carga un CV y una descripción de empleo de ejemplo para ver todo el flujo de WorkZo al instante. No se necesitan datos privados."})
        UI_TEXT.setdefault("Portuguese", {}).update({"sample_mode_intro": "Carregue um currículo e uma descrição de vaga de exemplo para ver todo o fluxo do WorkZo instantaneamente. Nenhum dado privado necessário."})
        UI_TEXT.setdefault("Dutch", {}).update({"sample_mode_intro": "Laad een voorbeeld-cv en vacaturetekst om direct de volledige WorkZo-workflow te zien. Geen privégegevens nodig."})
except Exception:
    pass


# =========================================================
# WorkZo v39 onboarding literal translation patch
# =========================================================
try:
    if "UI_TEXT" in globals():
        UI_TEXT.setdefault("English", {}).update({
            "warn_enter_details": "Please enter at least a few details so WorkZo can build your CV.",
            "creating_cv_draft": "Creating your CV draft with AI...",
            "reading_resume_dashboard": "Reading your resume and preparing dashboard...",
        })
        UI_TEXT.setdefault("German", {}).update({
            "warn_enter_details": "Bitte gib mindestens ein paar Details ein, damit WorkZo deinen Lebenslauf erstellen kann.",
            "creating_cv_draft": "Dein CV-Entwurf wird mit KI erstellt...",
            "reading_resume_dashboard": "Dein Lebenslauf wird gelesen und das Dashboard vorbereitet...",
        })
        UI_TEXT.setdefault("Dutch", {}).update({
            "warn_enter_details": "Voer minstens enkele details in zodat WorkZo je cv kan maken.",
            "creating_cv_draft": "Je cv-concept wordt met AI gemaakt...",
            "reading_resume_dashboard": "Je cv wordt gelezen en het dashboard wordt voorbereid...",
        })
except Exception:
    pass

# =========================================================
# WorkZo v90 - Clean onboarding with smarter Create CV
# Safe override: Upload CV OR Create CV only. LinkedIn option removed.
# =========================================================
import re as _wz_re

_WZ90_SKILL_OPTIONS = [
    "Python", "SQL", "Excel", "Power BI", "Tableau", "Data Analysis", "Pandas", "NumPy", "Matplotlib",
    "Machine Learning", "Scikit-learn", "Statistics", "Dashboard Development", "Reporting", "ETL",
    "REST APIs", "Web Scraping", "Google Cloud", "AWS", "Azure", "Git", "Linux", "Docker",
    "Technical Support", "IT Support", "Help Desk", "Troubleshooting", "Ticketing Systems", "ITSM",
    "Customer Support", "Customer Success", "CRM", "SaaS", "Product Support", "Incident Management",
    "Root Cause Analysis", "Documentation", "Stakeholder Communication", "Agile", "Scrum", "Jira",
]

_WZ90_EDUCATION_OPTIONS = [
    "High School", "Diploma", "Vocational Training", "Bachelor's Degree", "B.Sc Computer Science",
    "B.Tech", "Bachelor of Engineering", "Bachelor of Commerce", "Master's Degree", "M.Sc Data Science",
    "MBA", "M.Tech", "PhD", "Data Science Bootcamp", "Data Analytics Bootcamp", "Certificate Course",
    "Self-taught", "Other",
]

_WZ90_LANGUAGE_OPTIONS = [
    "English", "German A1", "German A2", "German B1", "German B2", "German C1",
    "Dutch A1", "Dutch A2", "Dutch B1", "Dutch B2", "Dutch C1",
    "French", "Spanish", "Italian", "Portuguese", "Hindi", "Tamil", "Malayalam", "Telugu", "Kannada",
]

_WZ90_CERT_OPTIONS = [
    "Google Data Analytics", "IBM Data Analyst", "Microsoft Power BI", "Tableau", "AWS Cloud Practitioner",
    "Azure Fundamentals", "Google Cloud Digital Leader", "ITIL Foundation", "Scrum Master", "Python Certificate",
    "SQL Certificate", "Excel Advanced", "Data Science Bootcamp", "WBS Coding School Bootcamp",
]

_WZ90_ROLE_OPTIONS = [
    "Data Analyst", "Junior Data Analyst", "Business Analyst", "Reporting Analyst", "BI Analyst",
    "Technical Support Engineer", "IT Support Specialist", "Help Desk Analyst", "Customer Support Specialist",
    "Customer Success Manager", "Product Support Specialist", "Software Tester", "Junior Python Developer",
]


def _wz90_label(text: str) -> str:
    try:
        return ui_label(text)
    except Exception:
        return text


def _wz90_top_header_once() -> None:
    try:
        render_workzo_header()
    except Exception:
        pass


def _wz90_set_lang_country(language: str, country: str) -> None:
    try:
        if callable(globals().get("workzo_set_language_everywhere")):
            workzo_set_language_everywhere(language)
        elif callable(globals().get("set_single_preferred_language")):
            set_single_preferred_language(language)
    except Exception:
        pass
    try:
        st.session_state.preferred_language = language
        st.session_state.language = language
        st.session_state.ui_language = language
        st.session_state.response_language = language
        st.session_state.country = country
        st.session_state.migration_country = country
    except Exception:
        pass


def _wz90_extract_uploaded_cv(uploaded_file) -> str:
    if uploaded_file is None:
        return ""
    try:
        name = (getattr(uploaded_file, "name", "") or "").lower()
        mime = getattr(uploaded_file, "type", "") or ""
        if mime == "text/plain" or name.endswith(".txt"):
            return uploaded_file.read().decode("utf-8", errors="ignore")
        if mime == "application/pdf" or name.endswith(".pdf"):
            try:
                return extract_pdf_text(uploaded_file)
            except Exception:
                return ""
        if name.endswith(".docx"):
            try:
                from docx import Document
                doc = Document(uploaded_file)
                return "\n".join(p.text for p in doc.paragraphs if p.text and p.text.strip())
            except Exception:
                return ""
    except Exception:
        return ""
    return ""


def _wz90_clean_sentence(text: str) -> str:
    """Small local fallback that makes broken notes more readable if AI is unavailable."""
    text = str(text or "").strip()
    if not text:
        return ""
    text = _wz_re.sub(r"\s+", " ", text)
    text = text.replace(" i ", " I ")
    if text and text[0].islower():
        text = text[0].upper() + text[1:]
    if text and text[-1] not in ".!?":
        text += "."
    return text


def _wz90_build_create_cv_notes(data: dict) -> str:
    skills = ", ".join(data.get("skills", []) or [])
    languages = ", ".join(data.get("languages", []) or [])
    certs = ", ".join(data.get("certificates", []) or [])
    return f"""
Full name: {data.get('full_name','')}
Target role: {data.get('target_role','')}
Target country: {data.get('country','')}
Career status: {data.get('status','')}

Experience / background notes:
{data.get('experience','')}

Education:
{data.get('education','')}

Skills:
{skills}

Projects:
{data.get('projects','')}

Certificates:
{certs}

Languages:
{languages}

Extra details:
{data.get('extra','')}
""".strip()


def _wz90_generate_smart_cv(data: dict) -> str:
    """Generate a better CV from rough user notes. Uses existing AI helper if available, with safe fallback."""
    raw_notes = _wz90_build_create_cv_notes(data)
    country = data.get("country") or st.session_state.get("country", "") or "Germany"
    status = data.get("status") or st.session_state.get("user_status", "") or "Job seeker"

    # Use existing WorkZo AI CV generator when available. This preserves your current AI behavior.
    try:
        if callable(globals().get("generate_cv_from_user_details")):
            generated = generate_cv_from_user_details(raw_notes, country, status)
            if generated and not str(generated).startswith("ERROR:") and len(str(generated).strip()) > 120:
                return str(generated).strip()
    except Exception:
        pass

    # Clean local fallback so onboarding never crashes if AI/API is unavailable.
    full_name = data.get("full_name") or "Your Name"
    target_role = data.get("target_role") or "Target Role"
    summary_parts = []
    if data.get("experience"):
        summary_parts.append(_wz90_clean_sentence(data.get("experience")))
    if data.get("skills"):
        summary_parts.append("Skilled in " + ", ".join(data.get("skills")[:8]) + ".")
    summary = " ".join(summary_parts) or f"Motivated candidate targeting {target_role} roles."

    projects = _wz90_clean_sentence(data.get("projects"))
    extra = _wz90_clean_sentence(data.get("extra"))
    certs = ", ".join(data.get("certificates", []) or [])
    langs = ", ".join(data.get("languages", []) or [])
    skills = ", ".join(data.get("skills", []) or [])

    return f"""
{full_name}
{target_role}

PROFESSIONAL SUMMARY
{summary}

CORE SKILLS
{skills or 'Add your main skills here'}

EXPERIENCE
{_wz90_clean_sentence(data.get('experience')) or 'Add your work, internship, project, or volunteer experience here.'}

PROJECTS
{projects or 'Add relevant projects here.'}

EDUCATION
{data.get('education') or 'Add your education here.'}

CERTIFICATIONS
{certs or 'Add relevant certifications here.'}

LANGUAGES
{langs or 'Add languages here.'}

ADDITIONAL DETAILS
{extra}
""".strip()


def _wz90_finalize_cv_to_dashboard(cv_text: str, cv_mode: str, country: str, language: str, user_status: str = "") -> None:
    """Shared finalization for uploaded or created CV. Keeps existing WorkZo downstream state intact."""
    _wz90_set_lang_country(language, country)
    st.session_state.cv_mode = cv_mode
    st.session_state.user_status = user_status or st.session_state.get("user_status", "") or "Job seeker"
    st.session_state.raw_cv_extraction = cv_text

    clean_text = cv_text
    try:
        clean_text = organize_cv_for_display(cv_text)
    except Exception:
        pass

    # Keep structured extraction so Improve CV / Downloads / Dashboard continue to work.
    try:
        with st.spinner(_wz90_label("Creating a clean profile from your CV...")):
            structured_data = extract_structured_resume_json(clean_text, country, st.session_state.user_status)
            clean_from_sections = _format_structured_resume_profile(structured_data)
            st.session_state.structured_cv_json = structured_data if isinstance(structured_data, dict) else {}
            st.session_state.pending_structured_cv_json = {}
            st.session_state.cv_review_required = False
            if clean_from_sections and len(clean_from_sections.strip()) > 120:
                st.session_state.structured_cv_profile = clean_from_sections
                st.session_state.clean_structured_cv_text = clean_from_sections
                clean_text = clean_from_sections
    except Exception:
        st.session_state.clean_structured_cv_text = clean_text

    try:
        st.session_state.cv_text = clean_cv_text(clean_text)
    except Exception:
        st.session_state.cv_text = str(clean_text or "").strip()

    try:
        workzo_sync_user_profile()
    except Exception:
        pass
    try:
        track_event("cv_ready", "Onboarding", {"cv_mode": cv_mode, "target_country": country, "user_status": st.session_state.user_status})
    except Exception:
        pass

    st.session_state.onboarding_complete = True
    try:
        with st.spinner(_wz90_label("Preparing your dashboard...")):
            analyze_resume_dashboard_stable(st.session_state.cv_text, force_refresh=True)
    except Exception:
        pass
    try:
        sync_navigation_state("dashboard")
    except Exception:
        st.session_state.page = "dashboard"
    try:
        request_scroll_to_top()
    except Exception:
        pass


def _wz90_render_create_cv_form(language: str, country: str, user_status: str) -> None:
    st.markdown("### ✍️ Create your CV")
    st.caption(_wz90_label("Write simple notes. WorkZo will turn them into a cleaner CV."))

    full_name = st.text_input(_wz90_label("Full name"), key="wz90_create_full_name", placeholder="Example: Haritha Vijayakumar")

    target_role = st.selectbox(
        _wz90_label("Target role"),
        [""] + _WZ90_ROLE_OPTIONS + ["Other"],
        key="wz90_create_target_role_select",
    )
    if target_role == "Other":
        target_role = st.text_input(_wz90_label("Type your target role"), key="wz90_create_target_role_custom")

    experience = st.text_area(
        _wz90_label("Experience or background"),
        key="wz90_create_experience",
        height=120,
        placeholder="Example: I worked in technical support for 4 years. I helped customers, handled tickets, solved product issues, and worked with support teams.",
    )

    education = st.selectbox(
        _wz90_label("Education"),
        [""] + _WZ90_EDUCATION_OPTIONS,
        key="wz90_create_education_select",
    )
    if education == "Other":
        education = st.text_input(_wz90_label("Type your education"), key="wz90_create_education_custom")

    skills = st.multiselect(
        _wz90_label("Skills"),
        _WZ90_SKILL_OPTIONS,
        key="wz90_create_skills",
        placeholder=_wz90_label("Start typing skills"),
    )

    with st.expander(_wz90_label("Add more details (optional)"), expanded=False):
        projects = st.text_area(
            _wz90_label("Projects"),
            key="wz90_create_projects",
            height=90,
            placeholder="Example: Built a Tableau dashboard / Python data project / customer support analysis project.",
        )
        certificates = st.multiselect(
            _wz90_label("Certificates"),
            _WZ90_CERT_OPTIONS,
            key="wz90_create_certificates",
            placeholder=_wz90_label("Start typing certificates"),
        )
        languages_known = st.multiselect(
            _wz90_label("Languages"),
            _WZ90_LANGUAGE_OPTIONS,
            key="wz90_create_languages",
            placeholder=_wz90_label("Start typing languages"),
        )
        extra = st.text_area(
            _wz90_label("Anything else WorkZo should know?"),
            key="wz90_create_extra",
            height=80,
            placeholder="Example: career break, relocation, preferred remote roles, willing to migrate, German level, etc.",
        )

    if st.button(_wz90_label("Create My CV"), type="primary", use_container_width=True, key="wz90_create_cv_btn"):
        if not full_name.strip() or not target_role.strip():
            st.warning(_wz90_label("Please add your name and target role."))
            return
        if not experience.strip() and not skills:
            st.warning(_wz90_label("Please add at least your experience/background or key skills."))
            return

        data = {
            "full_name": full_name.strip(),
            "target_role": target_role.strip(),
            "experience": experience.strip(),
            "education": education.strip(),
            "skills": skills,
            "projects": projects.strip(),
            "certificates": certificates,
            "languages": languages_known,
            "extra": extra.strip(),
            "country": country,
            "status": user_status,
        }
        with st.spinner(_wz90_label("Creating and improving your CV...")):
            generated_cv = _wz90_generate_smart_cv(data)
        st.session_state.wz90_created_cv_preview = generated_cv
        st.session_state.wz90_created_cv_data = data
        st.rerun()

    if st.session_state.get("wz90_created_cv_preview"):
        st.success(_wz90_label("Your CV draft is ready."))
        edited_cv = st.text_area(
            _wz90_label("Review your CV before continuing"),
            value=st.session_state.get("wz90_created_cv_preview", ""),
            height=260,
            key="wz90_created_cv_review",
        )
        if st.button(_wz90_label("Go to Dashboard"), type="primary", use_container_width=True, key="wz90_created_cv_continue"):
            _wz90_finalize_cv_to_dashboard(edited_cv, "Create CV", country, language, user_status)
            st.rerun()


def show_onboarding():
    """Clean onboarding override: Upload CV or smart Create CV. LinkedIn option removed."""
    _wz90_top_header_once()
    try:
        maybe_scroll_to_top()
    except Exception:
        pass

    if "wz90_onboarding_step" not in st.session_state:
        st.session_state.wz90_onboarding_step = 1

    # Keep steps short. One action per screen.
    st.markdown("### " + _wz90_label("Start your WorkZo journey"))
    step = int(st.session_state.get("wz90_onboarding_step", 1) or 1)
    st.caption(_wz90_label(f"Step {step} of 3"))

    language_list = globals().get("language_options", None) or ["English", "German", "Dutch", "French", "Spanish", "Portuguese"]
    country_list = globals().get("country_options", None) or ["Germany", "Netherlands", "India", "United States", "United Kingdom", "Canada", "Australia"]

    if step == 1:
        st.markdown("#### " + _wz90_label("Choose your language and job market"))
        current_lang = st.session_state.get("preferred_language", "English")
        if current_lang not in language_list:
            current_lang = "English" if "English" in language_list else language_list[0]
        language = st.selectbox(_wz90_label("Preferred language"), language_list, index=language_list.index(current_lang), key="wz90_pref_language")

        current_country = st.session_state.get("country", "Germany")
        if current_country not in country_list:
            current_country = "Germany" if "Germany" in country_list else country_list[0]
        country = st.selectbox(_wz90_label("Target country"), country_list, index=country_list.index(current_country), key="wz90_target_country")

        user_status_options = [
            "Job seeker", "Fresh graduate", "Student / thesis / internship", "Career changer",
            "Experienced professional", "Returning after a career break", "Willing to migrate / international applicant",
        ]
        current_status = st.session_state.get("user_status", "Job seeker")
        if current_status not in user_status_options:
            current_status = "Job seeker"
        user_status = st.selectbox(_wz90_label("Career situation"), user_status_options, index=user_status_options.index(current_status), key="wz90_user_status")

        if st.button(_wz90_label("Continue"), type="primary", use_container_width=True, key="wz90_step1_continue"):
            _wz90_set_lang_country(language, country)
            st.session_state.user_status = user_status
            st.session_state.wz90_onboarding_step = 2
            st.rerun()
        return

    language = st.session_state.get("preferred_language", "English")
    country = st.session_state.get("country", "Germany")
    user_status = st.session_state.get("user_status", "Job seeker")

    if step == 2:
        st.markdown("#### " + _wz90_label("How do you want to start?"))
        method = st.radio(
            _wz90_label("Choose one"),
            ["📄 Upload CV", "✍️ Create CV"],
            horizontal=True,
            key="wz90_cv_start_method",
            label_visibility="collapsed",
        )
        st.caption(_wz90_label("Upload an existing CV, or create one from simple notes."))
        col_back, col_continue = st.columns([1, 2])
        with col_back:
            if st.button(_wz90_label("Back"), use_container_width=True, key="wz90_step2_back"):
                st.session_state.wz90_onboarding_step = 1
                st.rerun()
        with col_continue:
            if st.button(_wz90_label("Continue"), type="primary", use_container_width=True, key="wz90_step2_continue"):
                st.session_state.wz90_cv_method = method
                st.session_state.wz90_onboarding_step = 3
                st.rerun()
        return

    if step == 3:
        method = st.session_state.get("wz90_cv_method", "📄 Upload CV")
        if method.startswith("📄"):
            st.markdown("#### " + _wz90_label("Upload your CV"))
            st.caption(_wz90_label("Upload your CV and WorkZo will prepare your dashboard."))
            uploaded_file = st.file_uploader(_wz90_label("Upload PDF, TXT, or DOCX"), type=["pdf", "txt", "docx"], key="wz90_upload_cv_file")
            col_back, col_continue = st.columns([1, 2])
            with col_back:
                if st.button(_wz90_label("Back"), use_container_width=True, key="wz90_upload_back"):
                    st.session_state.wz90_onboarding_step = 2
                    st.rerun()
            with col_continue:
                if st.button(_wz90_label("Go to Dashboard"), type="primary", use_container_width=True, key="wz90_upload_continue"):
                    if uploaded_file is None:
                        st.warning(_wz90_label("Please upload your CV first."))
                        return
                    if getattr(uploaded_file, "size", 0) and uploaded_file.size > 5 * 1024 * 1024:
                        st.error(_wz90_label("File is too large. Please upload a smaller CV."))
                        return
                    cv_text = _wz90_extract_uploaded_cv(uploaded_file)
                    if not cv_text or len(cv_text.strip()) < 40:
                        st.error(_wz90_label("I could not read enough text from this file. Please try a clearer PDF/TXT/DOCX."))
                        return
                    _wz90_finalize_cv_to_dashboard(cv_text, "Upload CV", country, language, user_status)
                    st.rerun()
        else:
            _wz90_render_create_cv_form(language, country, user_status)

# =========================================================
# WorkZo v91 - Onboarding: Upload CV | Create CV | Sample Demo
# Scope: onboarding only. LinkedIn remains removed. Existing helpers/features preserved.
# =========================================================
def _wz91_onboarding_css() -> None:
    try:
        st.markdown("""
        <style id="workzo-v91-onboarding-css">
        .wz91-onboard-hero { margin:.55rem 0 1rem 0; padding:1.1rem 1.2rem; border-radius:22px; border:1px solid rgba(34,211,238,.28); background:linear-gradient(135deg, rgba(8,47,73,.86), rgba(15,23,42,.95)); box-shadow:0 16px 38px rgba(2,6,23,.20); }
        .wz91-kicker { color:#67e8f9; font-size:.72rem; font-weight:900; letter-spacing:.13em; text-transform:uppercase; margin-bottom:.3rem; }
        .wz91-title { color:#fff; font-size:clamp(1.35rem,4vw,2rem); line-height:1.12; font-weight:950; letter-spacing:-.035em; margin:0; }
        .wz91-sub { color:#cbd5e1; font-size:.94rem; line-height:1.45; margin:.42rem 0 0 0; max-width:760px; }
        .wz91-card { border-radius:18px; border:1px solid rgba(148,163,184,.25); background:rgba(15,23,42,.055); padding:.95rem 1rem; margin:.55rem 0; min-height:130px; }
        .wz91-card strong { font-size:1rem; }
        .wz91-muted { color:#64748b; font-size:.9rem; line-height:1.35; }
        .wz91-step { display:inline-block; padding:.32rem .62rem; border-radius:999px; background:rgba(34,211,238,.12); border:1px solid rgba(34,211,238,.25); font-size:.82rem; font-weight:850; margin:.15rem .25rem .45rem 0; }
        div[data-testid="stButton"] button { min-height:46px; border-radius:14px !important; font-weight:850 !important; }
        @media(max-width:760px){ .wz91-onboard-hero{padding:1rem .9rem;border-radius:18px}.wz91-card{min-height:auto;padding:.85rem} }
        </style>
        """, unsafe_allow_html=True)
    except Exception:
        pass


def _wz91_go_onboarding_step(step: int) -> None:
    try:
        st.session_state.wz91_onboarding_step = int(step)
        request_scroll_to_top()
    except Exception:
        pass
    st.rerun()


def _wz91_render_method_cards() -> None:
    st.markdown("#### " + _wz90_label("How do you want to start?"))
    st.caption(_wz90_label("Choose how you want to start. You can upload an existing CV, create one, or try a sample demo."))
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("<div class='wz91-card'><strong>📄 Upload CV</strong><div class='wz91-muted'>Already have a resume? Upload it and get started instantly.</div></div>", unsafe_allow_html=True)
        if st.button(_wz90_label("Upload CV"), type="primary", use_container_width=True, key="wz91_choose_upload"):
            st.session_state.wz91_cv_method = "upload"
            _wz91_go_onboarding_step(3)
    with c2:
        st.markdown("<div class='wz91-card'><strong>✍️ Create CV</strong><div class='wz91-muted'>No CV? Answer a few questions and WorkZo will create one.</div></div>", unsafe_allow_html=True)
        if st.button(_wz90_label("Create CV"), use_container_width=True, key="wz91_choose_create"):
            st.session_state.wz91_cv_method = "create"
            _wz91_go_onboarding_step(3)
    with c3:
        st.markdown("<div class='wz91-card'><strong>⚡ Sample Demo</strong><div class='wz91-muted'>Just exploring? Load a demo CV and job to see the full flow.</div></div>", unsafe_allow_html=True)
        if st.button(_wz90_label("Try Sample Demo"), use_container_width=True, key="wz91_choose_sample"):
            try:
                load_workzo_sample_data()
            except Exception:
                st.session_state.cv_mode = "Sample Demo"
                st.session_state.cv_text = globals().get("SAMPLE_CV_TEXT", "Sample Demo CV")
                st.session_state.clean_structured_cv_text = st.session_state.cv_text
                st.session_state.onboarding_complete = True
                try: sync_navigation_state("dashboard")
                except Exception: st.session_state.page = "dashboard"
            st.rerun()


def show_onboarding():
    """v91 clean onboarding: Upload CV | Create CV | Sample Demo. LinkedIn option removed."""
    _wz90_top_header_once()
    _wz91_onboarding_css()
    try:
        maybe_scroll_to_top()
    except Exception:
        pass

    if "wz91_onboarding_step" not in st.session_state:
        st.session_state.wz91_onboarding_step = 1

    step = int(st.session_state.get("wz91_onboarding_step", 1) or 1)
    st.markdown(f"<span class='wz91-step'>Step {step} of 3</span>", unsafe_allow_html=True)

    language_list = globals().get("language_options", None) or ["English", "German", "Dutch", "French", "Spanish", "Portuguese"]
    country_list = globals().get("country_options", None) or ["Germany", "Netherlands", "India", "United States", "United Kingdom", "Canada", "Australia"]

    if step == 1:
        st.markdown("""
        <div class="wz91-onboard-hero">
          <div class="wz91-kicker">SETUP</div>
          <div class="wz91-title">Choose your country, language, and career status</div>
          <p class="wz91-sub">WorkZo will use this to personalize your dashboard, CV guidance, job search, and interview practice.</p>
        </div>
        """, unsafe_allow_html=True)
        current_country = st.session_state.get("country", "Germany")
        if current_country not in country_list:
            current_country = "Germany" if "Germany" in country_list else country_list[0]

        current_lang = st.session_state.get("preferred_language", "English")
        if current_lang not in language_list:
            current_lang = "English" if "English" in language_list else language_list[0]

        user_status_options = [
            "Job seeker", "Fresh graduate", "Student / thesis / internship", "Career changer",
            "Experienced professional", "Returning after a career break", "Willing to migrate / international applicant",
        ]
        current_status = st.session_state.get("user_status", "Job seeker")
        if current_status not in user_status_options:
            current_status = "Job seeker"

        c_country, c_language, c_status = st.columns(3)
        with c_country:
            country = st.selectbox(_wz90_label("Choose country"), country_list, index=country_list.index(current_country), key="wz91_target_country")
        with c_language:
            language = st.selectbox(_wz90_label("Choose language"), language_list, index=language_list.index(current_lang), key="wz91_pref_language")
        with c_status:
            user_status = st.selectbox(_wz90_label("Career status"), user_status_options, index=user_status_options.index(current_status), key="wz91_user_status")

        if st.button(_wz90_label("Continue"), type="primary", use_container_width=True, key="wz91_step1_continue"):
            _wz90_set_lang_country(language, country)
            st.session_state.user_status = user_status
            _wz91_go_onboarding_step(2)
        return

    language = st.session_state.get("preferred_language", "English")
    country = st.session_state.get("country", "Germany")
    user_status = st.session_state.get("user_status", "Job seeker")

    if step == 2:
        st.markdown("""
        <div class="wz91-onboard-hero">
          <div class="wz91-kicker">ADD CV</div>
          <div class="wz91-title">Upload CV, create CV, or try sample demo</div>
          <p class="wz91-sub">Choose how you want to enter WorkZo. After this, you can go to your dashboard.</p>
        </div>
        """, unsafe_allow_html=True)
        _wz91_render_method_cards()
        if st.button(_wz90_label("Back"), use_container_width=True, key="wz91_step2_back"):
            _wz91_go_onboarding_step(1)
        return

    if step == 3:
        method = st.session_state.get("wz91_cv_method", "upload")
        if method == "upload":
            st.markdown("#### " + _wz90_label("Upload your CV"))
            st.caption(_wz90_label("Upload your CV and WorkZo will prepare your dashboard."))
            uploaded_file = st.file_uploader(_wz90_label("Upload PDF, TXT, or DOCX"), type=["pdf", "txt", "docx"], key="wz91_upload_cv_file")
            col_back, col_continue = st.columns([1, 2])
            with col_back:
                if st.button(_wz90_label("Back"), use_container_width=True, key="wz91_upload_back"):
                    _wz91_go_onboarding_step(2)
            with col_continue:
                if st.button(_wz90_label("Go to Dashboard"), type="primary", use_container_width=True, key="wz91_upload_continue"):
                    if uploaded_file is None:
                        st.warning(_wz90_label("Please upload your CV first."))
                        return
                    if getattr(uploaded_file, "size", 0) and uploaded_file.size > 5 * 1024 * 1024:
                        st.error(_wz90_label("File is too large. Please upload a smaller CV."))
                        return
                    cv_text = _wz90_extract_uploaded_cv(uploaded_file)
                    if not cv_text or len(cv_text.strip()) < 40:
                        st.error(_wz90_label("I could not read enough text from this file. Please try a clearer PDF/TXT/DOCX."))
                        return
                    _wz90_finalize_cv_to_dashboard(cv_text, "Upload CV", country, language, user_status)
                    st.rerun()
            return

        # Create CV path: searchable multiselects are kept, and rough notes are improved by AI/fallback.
        _wz90_render_create_cv_form(language, country, user_status)
        if st.button(_wz90_label("Back"), use_container_width=True, key="wz91_create_back"):
            st.session_state.pop("wz90_created_cv_preview", None)
            _wz91_go_onboarding_step(2)
        return

# =========================================================
# WorkZo PERMANENT landing/onboarding guard
# This block is intentionally at the END of this module so it wins over any
# earlier show_landing_page/show_onboarding definitions in this file.
# Do not create another onboarding function after this block.
# =========================================================
try:
    WORKZO_ACTIVE_ONBOARDING_VERSION = "permanent_v92_guided_3_step"
except Exception:
    pass


# =========================================================
# WorkZo FINAL UX FIX - one header + real back navigation
# Scope: header/back behavior only. No product feature logic changed.
# =========================================================
_WORKZO_HEADER_RENDERED_THIS_RUN = False
try:
    _workzo_original_sync_navigation_state = sync_navigation_state
except Exception:
    _workzo_original_sync_navigation_state = None
try:
    _workzo_original_queue_navigation = queue_navigation
except Exception:
    _workzo_original_queue_navigation = None
try:
    _workzo_original_render_workzo_header = render_workzo_header
except Exception:
    _workzo_original_render_workzo_header = None


def _workzo_push_history(next_page: str) -> None:
    """Keep a small Streamlit-side navigation stack so the app back button returns to the previous WorkZo page."""
    try:
        current = str(st.session_state.get("nav_page") or st.session_state.get("page") or "landing")
        next_page = str(next_page or "dashboard")
        if current and current != next_page:
            stack = list(st.session_state.get("workzo_nav_stack", []) or [])
            if not stack or stack[-1] != current:
                stack.append(current)
            st.session_state["workzo_nav_stack"] = stack[-12:]
            st.session_state["workzo_previous_page"] = current
    except Exception:
        pass


def sync_navigation_state(page_key: str) -> None:
    """Canonical navigation: session state + URL + history stack."""
    try:
        _workzo_push_history(page_key)
    except Exception:
        pass
    try:
        st.session_state.page = page_key
        st.session_state.nav_page = page_key
        st.session_state.nav_change_nonce = st.session_state.get("nav_change_nonce", 0) + 1
        try:
            st.query_params["page"] = page_key
        except Exception:
            pass
        if callable(globals().get("request_scroll_to_top")):
            request_scroll_to_top()
    except Exception:
        if callable(_workzo_original_sync_navigation_state):
            try:
                _workzo_original_sync_navigation_state(page_key)
            except Exception:
                pass


def queue_navigation(page_key: str) -> None:
    """Queue page navigation and preserve previous page for the header back button."""
    try:
        _workzo_push_history(page_key)
        st.session_state._workzo_pending_nav = page_key
        try:
            st.query_params["page"] = page_key
        except Exception:
            pass
        if callable(globals().get("request_scroll_to_top")):
            request_scroll_to_top()
    except Exception:
        if callable(_workzo_original_queue_navigation):
            try:
                _workzo_original_queue_navigation(page_key)
            except Exception:
                pass


def _workzo_header_back_href() -> str:
    try:
        stack = list(st.session_state.get("workzo_nav_stack", []) or [])
        current = str(st.session_state.get("nav_page") or st.session_state.get("page") or "landing")
        while stack and stack[-1] == current:
            stack.pop()
        target = stack[-1] if stack else ("dashboard" if current not in {"landing", "onboarding", "dashboard"} else "landing")
        if target == "landing":
            return "?page=landing"
        if target == "onboarding":
            return "?page=onboarding"
        return f"?page={target}"
    except Exception:
        return "?page=dashboard"


def render_workzo_header() -> None:
    """Render the WorkZo header once per Streamlit run, with previous-page back navigation."""
    global _WORKZO_HEADER_RENDERED_THIS_RUN
    if _WORKZO_HEADER_RENDERED_THIS_RUN:
        return
    _WORKZO_HEADER_RENDERED_THIS_RUN = True

    try:
        apply_workzo_v75_global_css()
    except Exception:
        pass

    try:
        logo_src = image_to_data_uri(ICON_PATH) or image_to_data_uri(LOGO_PATH)
    except Exception:
        logo_src = None

    logo_html = (
        f'<img src="{logo_src}" class="workzo-logo" alt="WorkZo AI logo">'
        if logo_src
        else '<div class="workzo-logo workzo-logo-fallback">WZ</div>'
    )

    try:
        progress_pct, stage, cv_done, job_done, interview_done = _workzo_header_progress_state()
    except Exception:
        progress_pct, stage, cv_done, job_done, interview_done = 0, "CV", False, False, False
    cv_mark = "✓" if cv_done else "1"
    job_mark = "✓" if job_done else "2"
    interview_mark = "✓" if interview_done else "3"
    current_page = str(st.session_state.get("nav_page") or st.session_state.get("page", "landing") or "landing")
    show_back = current_page not in {"landing"}
    back_href = _workzo_header_back_href()
    back_html = f'<a class="workzo-back" href="{back_href}" target="_self">← Back</a>' if show_back else '<span></span>'

    st.markdown(f"""
    <style id="workzo-final-single-header-css">
    .workzo-header {{
        width: min(1180px, calc(100vw - 2rem)) !important;
        margin: 0 auto 1.05rem auto !important;
        position: sticky !important;
        top: .55rem !important;
        z-index: 99999 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: space-between !important;
        gap: 1rem !important;
        padding: .82rem 1rem !important;
        border-radius: 22px !important;
        border: 1px solid rgba(34,211,238,.30) !important;
        background: linear-gradient(135deg, rgba(8,47,73,.96), rgba(15,23,42,.98)) !important;
        box-shadow: 0 18px 45px rgba(2,6,23,.35) !important;
        backdrop-filter: blur(14px) !important;
    }}
    .workzo-brand {{ display:flex !important; align-items:center !important; gap:.85rem !important; min-width:0 !important; text-decoration:none !important; }}
    .workzo-logo {{ width:54px !important; height:54px !important; min-width:54px !important; border-radius:15px !important; object-fit:cover !important; display:flex !important; align-items:center !important; justify-content:center !important; background:linear-gradient(135deg,#06b6d4,#2563eb) !important; color:#fff !important; font-weight:950 !important; box-shadow:0 10px 24px rgba(14,165,233,.25) !important; }}
    .workzo-title {{ color:#fff !important; font-size:1.45rem !important; font-weight:950 !important; letter-spacing:-.04em !important; line-height:1 !important; white-space:nowrap !important; }}
    .workzo-title span {{ color:#22d3ee !important; }}
    .workzo-subtitle {{ color:#cbd5e1 !important; font-size:.82rem !important; font-weight:650 !important; margin-top:.25rem !important; white-space:nowrap !important; overflow:hidden !important; text-overflow:ellipsis !important; max-width:380px !important; }}
    .workzo-header-right {{ display:flex !important; align-items:center !important; gap:.75rem !important; }}
    .workzo-back {{ color:#cbd5e1 !important; text-decoration:none !important; border:1px solid rgba(148,163,184,.28) !important; border-radius:999px !important; padding:.42rem .68rem !important; font-weight:850 !important; font-size:.78rem !important; background:rgba(15,23,42,.42) !important; white-space:nowrap !important; }}
    .workzo-progress-wrap {{ min-width:220px !important; }}
    .workzo-progress-top {{ display:flex !important; justify-content:space-between !important; color:#cbd5e1 !important; font-size:.72rem !important; font-weight:850 !important; margin-bottom:.28rem !important; }}
    .workzo-progress-bar {{ height:7px !important; border-radius:999px !important; background:rgba(148,163,184,.18) !important; overflow:hidden !important; }}
    .workzo-progress-fill {{ height:100% !important; width:{progress_pct}% !important; border-radius:999px !important; background:linear-gradient(90deg,#22d3ee,#22c55e) !important; }}
    .workzo-progress-steps {{ display:flex !important; gap:.35rem !important; margin-top:.34rem !important; }}
    .workzo-step {{ color:#cbd5e1 !important; border:1px solid rgba(148,163,184,.22) !important; background:rgba(15,23,42,.42) !important; border-radius:999px !important; padding:.16rem .42rem !important; font-size:.63rem !important; font-weight:850 !important; white-space:nowrap !important; }}
    .workzo-step.done {{ color:#67e8f9 !important; border-color:rgba(34,211,238,.45) !important; background:rgba(8,145,178,.18) !important; }}
    .workzo-beta {{ color:#67e8f9 !important; border:1px solid rgba(103,232,249,.42) !important; background:rgba(8,145,178,.16) !important; border-radius:999px !important; padding:.38rem .72rem !important; font-size:.7rem !important; font-weight:950 !important; letter-spacing:.04em !important; white-space:nowrap !important; }}
    @media (max-width:760px) {{
        .workzo-header {{ width:calc(100vw - 1rem) !important; top:.45rem !important; border-radius:18px !important; padding:.65rem .75rem !important; }}
        .workzo-logo {{ width:44px !important; height:44px !important; min-width:44px !important; }}
        .workzo-title {{ font-size:1.16rem !important; }}
        .workzo-subtitle {{ font-size:.70rem !important; max-width:150px !important; }}
        .workzo-progress-wrap, .workzo-back {{ display:none !important; }}
        .workzo-beta {{ font-size:.62rem !important; padding:.32rem .52rem !important; }}
    }}
    </style>
    <div class="workzo-header">
        <a class="workzo-brand workzo-home-link" href="?page=dashboard&home=1" target="_self" title="Go to dashboard">
            {logo_html}
            <div>
                <div class="workzo-title">WorkZo <span>AI</span></div>
                <div class="workzo-subtitle">Your guided AI career system</div>
            </div>
        </a>
        <div class="workzo-header-right">
            {back_html}
            <div class="workzo-progress-wrap">
                <div class="workzo-progress-top"><span>{'Interview setup complete' if stage == 'Interview' else stage}</span><span>{'AI recruiter ready' if stage == 'Interview' else ('Step 1/3' if int(progress_pct or 0) == 0 else 'In progress')}</span></div>
                <div class="workzo-progress-bar"><div class="workzo-progress-fill"></div></div>
                <div class="workzo-progress-steps">
                    <span class="workzo-step {'done' if cv_done else ''}">{cv_mark} CV</span>
                    <span class="workzo-step {'done' if job_done else ''}">{job_mark} Jobs</span>
                    <span class="workzo-step {'done' if interview_done else ''}">{interview_mark} Interview</span>
                </div>
            </div>
            <div class="workzo-beta">BETA</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# =========================================================
# WorkZo FINAL SaaS Flow Override: Landing + 3-step onboarding
# Appended as final definitions so older duplicate functions cannot override it.
# =========================================================

def _wzflow_go(page: str) -> None:
    try:
        if "nav_stack" not in st.session_state:
            st.session_state.nav_stack = []
        current = st.session_state.get("nav_page") or st.session_state.get("page")
        if current and current != page and current not in ["landing", "identity"]:
            st.session_state.nav_stack.append(current)
        st.session_state.page = page
        st.session_state.nav_page = page
        try:
            st.query_params["page"] = page
        except Exception:
            pass
        request_scroll_to_top()
        st.rerun()
    except Exception:
        st.session_state.page = page
        st.session_state.nav_page = page
        st.rerun()


def _wzflow_logo_uri() -> str:
    try:
        return image_to_data_uri(ICON_PATH) or image_to_data_uri(LOGO_PATH) or ""
    except Exception:
        return ""


def _wzflow_render_minimal_brand() -> None:
    logo = _wzflow_logo_uri()
    logo_html = f'<img src="{logo}" class="wzflow-logo" alt="WorkZo AI logo">' if logo else '<div class="wzflow-logo wzflow-logo-fallback">WZ</div>'
    st.markdown(f"""
    <style id="wzflow-landing-css">
    .block-container {{ max-width: 1180px !important; padding-top: 1.2rem !important; }}
    .wzflow-brand {{ display:flex; align-items:center; gap:.85rem; margin:.4rem 0 1.4rem 0; }}
    .wzflow-logo {{ width:54px; height:54px; border-radius:15px; object-fit:cover; box-shadow:0 12px 28px rgba(14,165,233,.25); }}
    .wzflow-logo-fallback {{ display:flex; align-items:center; justify-content:center; background:linear-gradient(135deg,#06b6d4,#2563eb); color:white; font-weight:950; }}
    .wzflow-brand-title {{ color:#fff; font-weight:950; font-size:1.55rem; letter-spacing:-.04em; }}
    .wzflow-brand-title span {{ color:#22d3ee; }}
    .wzflow-hero {{ border:1px solid rgba(34,211,238,.28); border-radius:32px; padding:clamp(2rem,5vw,4.2rem); background:radial-gradient(circle at 12% 12%, rgba(34,211,238,.18), transparent 32%), linear-gradient(135deg, rgba(8,47,73,.90), rgba(15,23,42,.96)); box-shadow:0 30px 90px rgba(2,6,23,.42); }}
    .wzflow-hero h1 {{ color:#fff; font-size:clamp(2.4rem,6vw,5rem); line-height:1.02; letter-spacing:-.06em; margin:0 0 1rem 0; max-width:950px; }}
    .wzflow-hero p {{ color:#cbd5e1; font-size:clamp(1rem,2vw,1.3rem); max-width:720px; line-height:1.5; margin:0; }}
    .wzflow-how {{ display:grid; grid-template-columns:repeat(3,1fr); gap:1rem; margin-top:1.2rem; }}
    .wzflow-step {{ border:1px solid rgba(148,163,184,.22); border-radius:20px; padding:1rem; background:rgba(15,23,42,.50); color:#e2e8f0; }}
    .wzflow-step b {{ color:#67e8f9; }}
    @media (max-width:760px) {{ .wzflow-how {{ grid-template-columns:1fr; }} .wzflow-hero {{ padding:1.4rem; border-radius:24px; }} }}
    </style>
    <div class="wzflow-brand">{logo_html}<div class="wzflow-brand-title">WorkZo <span>AI</span></div></div>
    """, unsafe_allow_html=True)


def show_landing_page():
    """Final landing: one strong promise, two actions, three-step explanation."""
    maybe_scroll_to_top()
    _wzflow_render_minimal_brand()
    st.markdown("""
    <section class="wzflow-hero">
      <h1>Face a real interview before the real one</h1>
      <p>Practice an interview based on your CV and the job you want.</p>
    </section>
    """, unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,1,2])
    with c1:
        if st.button("📄 Upload CV", type="primary", use_container_width=True, key="wzflow_upload_cv_landing"):
            st.session_state["wz_onboarding_step"] = 1
            _wzflow_go("onboarding")
    with c2:
        if st.button("✨ Try Demo", use_container_width=True, key="wzflow_try_demo_landing"):
            st.session_state["wz_demo_requested"] = True
            st.session_state["wz_onboarding_step"] = 3
            # lightweight demo profile without forcing old dashboard routing
            if not str(st.session_state.get("cv_text", "")).strip():
                st.session_state["cv_text"] = SAMPLE_CV_TEXT if "SAMPLE_CV_TEXT" in globals() else "Demo CV: Junior Data Analyst with Python, SQL, support experience and customer-facing background."
                st.session_state["clean_structured_cv_text"] = st.session_state["cv_text"]
            if not str(st.session_state.get("selected_job_description", "")).strip():
                jd = SAMPLE_JOB_DESCRIPTION if "SAMPLE_JOB_DESCRIPTION" in globals() else "Demo job description: Junior Data Analyst role requiring SQL, Python, dashboards, communication and problem solving."
                st.session_state["selected_job_description"] = jd
                st.session_state["current_job_description"] = jd
                st.session_state["job_description"] = jd
                st.session_state["selected_job"] = {"title":"Junior Data Analyst", "company":"Demo Company", "description": jd, "match_score": 74}
            _wzflow_go("onboarding")
    st.markdown("""
    <div class="wzflow-how">
      <div class="wzflow-step"><b>1. Upload your CV</b><br>WorkZo reads your real profile.</div>
      <div class="wzflow-step"><b>2. Paste the job description</b><br>Use the role you want to prepare for.</div>
      <div class="wzflow-step"><b>3. Start your real interview</b><br>Practice with CV + job context.</div>
    </div>
    """, unsafe_allow_html=True)


def _wzflow_store_cv_text(cv_text: str, mode: str = "Upload CV") -> None:
    cv_text = str(cv_text or "").strip()
    if not cv_text:
        return
    st.session_state["cv_text"] = cv_text
    st.session_state["clean_structured_cv_text"] = cv_text
    st.session_state["raw_cv_extraction"] = cv_text
    st.session_state["uploaded_cv_text"] = cv_text
    st.session_state["cv_mode"] = mode
    st.session_state["onboarding_complete"] = True
    try:
        structured = extract_structured_resume_json(cv_text, st.session_state.get("country", "Germany"), st.session_state.get("user_status", ""))
        if isinstance(structured, dict) and structured:
            st.session_state["structured_cv_json"] = structured
            try:
                clean = _format_structured_resume_profile(structured)
                if clean and len(clean) > 100:
                    st.session_state["cv_text"] = clean
                    st.session_state["clean_structured_cv_text"] = clean
            except Exception:
                pass
    except Exception:
        pass


def _wzflow_store_job(title: str, desc: str, company: str = "") -> None:
    title = str(title or "Target job").strip() or "Target job"
    desc = str(desc or "").strip()
    company = str(company or "").strip()
    job = {"title": title, "company": company or "Company not set", "description": desc, "match_score": 70}
    st.session_state["selected_job"] = job
    st.session_state["selected_job_description"] = desc
    st.session_state["current_job_description"] = desc
    st.session_state["job_description"] = desc
    st.session_state["last_understand_job_description"] = desc
    st.session_state["improve_cv_for_job_desc"] = desc
    st.session_state["interview_jd_text_v117"] = desc
    sessions = st.session_state.get("workzo_job_sessions") or []
    marker = (title + company).casefold()
    if not any(((s.get("title","") + s.get("company","")).casefold() == marker) for s in sessions if isinstance(s, dict)):
        sessions.insert(0, {"title": title, "company": company or "Company not set", "description": desc, "progress": 35, "last_activity": "Job added"})
        st.session_state["workzo_job_sessions"] = sessions[:10]


def show_onboarding():
    """Final frictionless onboarding: Upload CV -> Paste job -> Start interview."""
    maybe_scroll_to_top()
    _wzflow_render_minimal_brand()
    step = int(st.session_state.get("wz_onboarding_step", 1) or 1)
    if step < 1 or step > 3:
        step = 1
    st.caption(f"Step {step} of 3")

    st.markdown("""
    <style id="wzflow-onboarding-css">
    .wzflow-card { border:1px solid rgba(34,211,238,.26); border-radius:28px; padding:1.6rem; background:linear-gradient(135deg, rgba(8,47,73,.62), rgba(15,23,42,.94)); box-shadow:0 20px 60px rgba(2,6,23,.28); margin:.8rem 0 1.2rem; }
    .wzflow-card h2 { color:#fff; font-size:clamp(1.8rem,4vw,3rem); line-height:1.08; letter-spacing:-.05em; margin:.2rem 0 .6rem; }
    .wzflow-card p { color:#cbd5e1; font-size:1.05rem; line-height:1.5; margin:0; }
    </style>
    """, unsafe_allow_html=True)

    if step == 1:
        st.markdown('<div class="wzflow-card"><h2>Upload your CV</h2><p>This lets WorkZo create interview questions based on your real experience.</p></div>', unsafe_allow_html=True)
        uploaded = st.file_uploader("Upload PDF or TXT", type=["pdf", "txt"], key="wzflow_cv_upload")
        if uploaded is not None:
            try:
                if uploaded.type == "text/plain":
                    text = uploaded.read().decode("utf-8", errors="ignore")
                else:
                    text = extract_pdf_text(uploaded)
                text = organize_cv_for_display(text) if callable(globals().get("organize_cv_for_display")) else str(text or "")
                if len(str(text).strip()) < 80:
                    st.error("CV upload worked, but text extraction looks too short. Try TXT or paste your CV details.")
                else:
                    _wzflow_store_cv_text(text, "Upload CV")
                    st.success(f"CV loaded. {len(str(text).split())} words extracted.")
            except Exception as exc:
                st.error(f"Could not read CV safely: {exc}")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Continue", type="primary", use_container_width=True, key="wzflow_continue_after_cv"):
                if not str(st.session_state.get("cv_text", "")).strip():
                    st.warning("Please upload your CV or use the demo CV.")
                else:
                    st.session_state["wz_onboarding_step"] = 2
                    st.rerun()
        with c2:
            if st.button("Skip with Demo CV", use_container_width=True, key="wzflow_demo_cv"):
                demo_cv = SAMPLE_CV_TEXT if "SAMPLE_CV_TEXT" in globals() else "Demo CV: Junior Data Analyst with Python, SQL, support experience and customer-facing troubleshooting background."
                _wzflow_store_cv_text(demo_cv, "Sample Resume")
                st.session_state["wz_onboarding_step"] = 2
                st.rerun()
        return

    if step == 2:
        st.markdown('<div class="wzflow-card"><h2>Paste the job you want</h2><p>Add the role you want to prepare for. WorkZo will connect this job to CV improvement and interview practice.</p></div>', unsafe_allow_html=True)
        title = st.text_input("Job title", value=st.session_state.get("target_role", ""), placeholder="Example: Data Analyst")
        company = st.text_input("Company / employer", value=(st.session_state.get("selected_job") or {}).get("company", ""), placeholder="Example: Amazon")
        jd_default = st.session_state.get("selected_job_description") or st.session_state.get("current_job_description") or ""
        desc = st.text_area("Job description", value=jd_default, height=240, placeholder="Paste the job description here...")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Continue", type="primary", use_container_width=True, key="wzflow_continue_after_job"):
                if not str(desc).strip():
                    st.warning("Paste a job description or use the demo job.")
                else:
                    if title.strip():
                        st.session_state["target_role"] = title.strip()
                    _wzflow_store_job(title or st.session_state.get("target_role") or "Target job", desc, company)
                    st.session_state["wz_onboarding_step"] = 3
                    st.rerun()
        with c2:
            if st.button("Use Demo Job", use_container_width=True, key="wzflow_demo_job"):
                jd = SAMPLE_JOB_DESCRIPTION if "SAMPLE_JOB_DESCRIPTION" in globals() else "Demo job description: Junior Data Analyst role requiring SQL, Python, dashboards, communication and stakeholder collaboration."
                _wzflow_store_job("Junior Data Analyst", jd, "Demo Company")
                st.session_state["wz_onboarding_step"] = 3
                st.rerun()
        return

    st.markdown('<div class="wzflow-card"><h2>You\'re ready.</h2><p>Start your real interview now. WorkZo will use your CV, the selected job, country, and language.</p></div>', unsafe_allow_html=True)
    if st.button("🎤 Start Real Interview", type="primary", use_container_width=True, key="wzflow_start_interview_now"):
        st.session_state["onboarding_complete"] = True
        _wzflow_go("real_interview")
    st.caption("Dashboard is available after the interview setup.")


# =========================================================
# WorkZo FINAL SaaS Landing + 3-step onboarding override
# Added: focused landing -> upload/demo -> job -> interview
# =========================================================

def _wz_final_safe_go(page_key: str) -> None:
    try:
        st.session_state["page"] = page_key
        st.session_state["nav_page"] = page_key
        try:
            st.query_params["page"] = page_key
        except Exception:
            pass
        request_scroll_to_top()
        st.rerun()
    except Exception:
        pass


def _wz_final_logo_html() -> str:
    try:
        src = image_to_data_uri(ICON_PATH) or image_to_data_uri(LOGO_PATH) or ""
    except Exception:
        src = ""
    if src:
        return f'<img src="{src}" class="wzfinal-logo" alt="WorkZo AI logo">'
    return '<div class="wzfinal-logo wzfinal-logo-fallback">WZ</div>'


def _wz_final_landing_css() -> None:
    st.markdown("""
    <style id="wz-final-landing-css">
    [data-testid="stMainBlockContainer"], .block-container {max-width:1180px !important; padding-top:1.2rem !important;}
    .wzfinal-top {display:flex; align-items:center; justify-content:space-between; gap:1rem; margin:.6rem 0 3rem;}
    .wzfinal-brand {display:flex; align-items:center; gap:.8rem;}
    .wzfinal-logo {width:54px;height:54px;border-radius:15px;object-fit:cover;box-shadow:0 10px 24px rgba(14,165,233,.25);}
    .wzfinal-logo-fallback {display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,#06b6d4,#2563eb);color:white;font-weight:950;}
    .wzfinal-title {font-size:1.45rem;font-weight:950;color:white;letter-spacing:-.04em}.wzfinal-title span{color:#22d3ee}
    .wzfinal-sub {font-size:.86rem;color:#a8c2d8;font-weight:700;margin-top:.1rem}
    .wzfinal-hero {border:1px solid rgba(34,211,238,.30);border-radius:34px;padding:clamp(2rem,6vw,5rem);background:radial-gradient(circle at 10% 8%,rgba(34,211,238,.19),transparent 31%),linear-gradient(135deg,rgba(8,47,73,.92),rgba(15,23,42,.98));box-shadow:0 28px 80px rgba(2,6,23,.44);text-align:center;}
    .wzfinal-kicker {color:#67e8f9;text-transform:uppercase;letter-spacing:.22em;font-size:.78rem;font-weight:950;margin-bottom:1rem;}
    .wzfinal-hero h1 {color:white;font-size:clamp(2.4rem,6vw,5rem);line-height:1.03;letter-spacing:-.06em;font-weight:950;max-width:920px;margin:0 auto 1rem;}
    .wzfinal-hero p {color:#dbeafe;font-size:clamp(1rem,2vw,1.28rem);line-height:1.55;max-width:720px;margin:0 auto;}
    .wzfinal-actions {display:flex;gap:1rem;justify-content:center;margin-top:2rem;flex-wrap:wrap;}
    .wzfinal-how {display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;margin-top:1.2rem;}
    .wzfinal-step {border:1px solid rgba(148,163,184,.22);background:rgba(15,23,42,.55);border-radius:20px;padding:1.1rem;color:white;font-weight:850;}
    .wzfinal-num {display:inline-flex;width:28px;height:28px;border-radius:999px;align-items:center;justify-content:center;background:rgba(34,211,238,.18);border:1px solid rgba(34,211,238,.4);color:#67e8f9;margin-right:.45rem;}
    @media(max-width:760px){.wzfinal-how{grid-template-columns:1fr}.wzfinal-actions{display:block}.wzfinal-actions>*{margin-bottom:.6rem}.wzfinal-top{margin-bottom:1.4rem}.wzfinal-hero{text-align:left}}
    </style>
    """, unsafe_allow_html=True)


def show_landing_page():
    """Final SaaS landing page: one hook, two actions, 3-step explanation."""
    try:
        maybe_scroll_to_top()
    except Exception:
        pass
    _wz_final_landing_css()
    st.markdown(f"""
    <div class="wzfinal-top">
      <div class="wzfinal-brand">{_wz_final_logo_html()}<div><div class="wzfinal-title">WorkZo <span>AI</span></div><div class="wzfinal-sub">Real interview practice for job seekers</div></div></div>
      <div style="color:#67e8f9;border:1px solid rgba(103,232,249,.35);border-radius:999px;padding:.45rem .8rem;font-weight:950;font-size:.75rem;">BETA</div>
    </div>
    <section class="wzfinal-hero">
      <div class="wzfinal-kicker">Real Interview AI</div>
      <h1>Face a real interview before the real one</h1>
      <p>Practice an interview based on your CV and the job you want.</p>
    </section>
    """, unsafe_allow_html=True)
    c1,c2,c3,c4 = st.columns([1,1.25,1.25,1])
    with c2:
        if st.button("📄 Upload CV", type="primary", use_container_width=True, key="wz_final_upload_cv_landing"):
            st.session_state["onboarding_step_final"] = 1
            st.session_state["onboarding_complete"] = False
            _wz_final_safe_go("onboarding")
    with c3:
        if st.button("✨ Try Demo", use_container_width=True, key="wz_final_demo_landing"):
            try:
                load_workzo_sample_data()
            except Exception:
                st.session_state["cv_text"] = SAMPLE_CV_TEXT if "SAMPLE_CV_TEXT" in globals() else "Demo CV for a junior data analyst with Python, SQL and support experience."
                st.session_state["current_job_description"] = SAMPLE_JOB_DESCRIPTION if "SAMPLE_JOB_DESCRIPTION" in globals() else "Demo job description for Data Analyst."
                st.session_state["selected_job_description"] = st.session_state["current_job_description"]
                st.session_state["selected_job"] = {"title":"Data Analyst","company":"Demo Company","description":st.session_state["current_job_description"]}
                st.session_state["onboarding_complete"] = True
            _wz_final_safe_go("dashboard")
    st.markdown("""
    <div class="wzfinal-how">
      <div class="wzfinal-step"><span class="wzfinal-num">1</span>Upload your CV</div>
      <div class="wzfinal-step"><span class="wzfinal-num">2</span>Paste the job description</div>
      <div class="wzfinal-step"><span class="wzfinal-num">3</span>Start your real interview</div>
    </div>
    """, unsafe_allow_html=True)


def _wz_final_save_cv_text(cv_text: str) -> None:
    cv_text = str(cv_text or "").strip()
    if not cv_text:
        return
    for k in ["cv_text","clean_structured_cv_text","raw_cv_extraction","workzo_live_cv_text","cv_editor_widget"]:
        st.session_state[k] = cv_text
    try:
        if not isinstance(st.session_state.get("structured_cv_json"), dict) or not st.session_state.get("structured_cv_json"):
            st.session_state["structured_cv_json"] = extract_structured_resume_json(cv_text, st.session_state.get("country","Germany"), st.session_state.get("user_status",""))
    except Exception:
        pass


def show_onboarding():
    """Final frictionless onboarding: CV -> job -> start interview."""
    try:
        maybe_scroll_to_top()
    except Exception:
        pass
    _wz_final_landing_css()
    step = int(st.session_state.get("onboarding_step_final", 1) or 1)
    st.markdown(f"""
    <div class="wzfinal-top">
      <div class="wzfinal-brand">{_wz_final_logo_html()}<div><div class="wzfinal-title">WorkZo <span>AI</span></div><div class="wzfinal-sub">Setup takes less than 2 minutes</div></div></div>
      <div style="color:#cbd5e1;font-weight:900;">Step {step} of 3</div>
    </div>
    """, unsafe_allow_html=True)

    if step == 1:
        st.markdown("### Upload your CV")
        st.caption("This makes every answer, job match, and interview question specific to your profile.")
        up = st.file_uploader("Upload PDF or TXT", type=["pdf","txt"], key="wz_final_cv_upload")
        if up is not None:
            text = ""
            try:
                if up.type == "text/plain":
                    text = up.read().decode("utf-8", errors="ignore")
                else:
                    text = extract_pdf_text(up)
                text = organize_cv_for_display(text) if callable(globals().get("organize_cv_for_display")) else str(text or "")
            except Exception as exc:
                st.error(f"Could not read this CV: {exc}")
            if text and len(text.strip()) > 80:
                _wz_final_save_cv_text(text)
                st.success(f"CV loaded successfully — {len(text.split())} words extracted.")
                if st.button("Continue", type="primary", use_container_width=True, key="wz_final_step1_continue"):
                    st.session_state["onboarding_step_final"] = 2
                    _wz_final_safe_go("onboarding")
            elif up is not None:
                st.warning("The CV uploaded, but little or no text was extracted. Try a TXT file or paste your CV content later.")
        if st.button("Skip with Demo CV", use_container_width=True, key="wz_final_demo_cv"):
            try:
                _wz_final_save_cv_text(SAMPLE_CV_TEXT)
            except Exception:
                _wz_final_save_cv_text("Demo CV: Junior Data Analyst with Python, SQL, Tableau, Excel, and technical support experience.")
            st.session_state["onboarding_step_final"] = 2
            _wz_final_safe_go("onboarding")
        return

    if step == 2:
        st.markdown("### Paste the job you want")
        st.caption("WorkZo will use this job to tailor your interview and CV guidance.")
        job_title = st.text_input("Job title", value=st.session_state.get("target_role", ""), placeholder="Example: Data Analyst")
        job_desc = st.text_area("Job description", value=st.session_state.get("selected_job_description", ""), height=240, placeholder="Paste the full job description here")
        if st.button("Continue", type="primary", use_container_width=True, key="wz_final_job_continue"):
            st.session_state["target_role"] = job_title.strip() or st.session_state.get("target_role", "Target role")
            st.session_state["selected_job_description"] = job_desc.strip()
            st.session_state["current_job_description"] = job_desc.strip()
            st.session_state["improve_cv_for_job_desc"] = job_desc.strip()
            st.session_state["interview_jd_text_v117"] = job_desc.strip()
            st.session_state["selected_job"] = {"title": st.session_state["target_role"], "company": "Target company", "description": job_desc.strip()}
            st.session_state["onboarding_step_final"] = 3
            _wz_final_safe_go("onboarding")
        return

    st.markdown("### You're ready.")
    st.caption("Start your interview now. WorkZo will use your CV, selected job, country, and language.")
    if st.button("🎤 Start Real Interview", type="primary", use_container_width=True, key="wz_final_start_interview_ready"):
        st.session_state["onboarding_complete"] = True
        _wz_final_safe_go("real_interview")
    st.caption("Dashboard is available later from the header after you start or finish the interview.")


# =========================================================
# WorkZo FINAL PATCH - clean CV-first onboarding
# Fixes: upload/create mixed UI, missing continue after upload, clearer CV ready state.
# This final definition intentionally overrides older duplicate show_onboarding/show_landing_page definitions.
# =========================================================
def _wz_final_safe_rerun():
    try:
        st.rerun()
    except Exception:
        try:
            st.experimental_rerun()
        except Exception:
            pass


def _wz_final_go(page: str):
    try:
        current = st.session_state.get("nav_page") or st.session_state.get("page")
        if current and current != page:
            st.session_state.setdefault("nav_stack", []).append(current)
        st.session_state["page"] = page
        st.session_state["nav_page"] = page
        try:
            st.query_params["page"] = page
        except Exception:
            pass
        request_scroll_to_top()
    except Exception:
        pass
    _wz_final_safe_rerun()


def _wz_final_set_cv_text(cv_text: str, mode: str = "Upload CV") -> bool:
    cv_text = str(cv_text or "").strip()
    if not cv_text:
        return False
    try:
        cv_text = organize_cv_for_display(cv_text) if callable(globals().get("organize_cv_for_display")) else cv_text
    except Exception:
        pass
    # Single source of truth used across dashboard, jobs, interview, documents, Work-O-Bot.
    for key in [
        "cv_text", "clean_structured_cv_text", "structured_cv_profile", "raw_cv_extraction",
        "uploaded_cv_text", "workzo_live_cv_text", "cv_editor_widget"
    ]:
        try:
            st.session_state[key] = cv_text
        except Exception:
            pass
    st.session_state["cv_mode"] = mode
    st.session_state["cv_ready"] = True
    st.session_state["prepare_cv_uploaded"] = True
    # Best-effort structured extraction; never block onboarding.
    try:
        if callable(globals().get("extract_structured_resume_json")):
            country = st.session_state.get("country") or st.session_state.get("migration_country") or "International"
            status = st.session_state.get("user_status") or "Not specified"
            structured = extract_structured_resume_json(cv_text, country, status)
            if isinstance(structured, dict) and structured:
                st.session_state["structured_cv_json"] = structured
                st.session_state["approved_structured_cv_json"] = structured
                if callable(globals().get("_format_structured_resume_profile")):
                    clean = _format_structured_resume_profile(structured)
                    if str(clean or "").strip():
                        for key in ["cv_text", "clean_structured_cv_text", "structured_cv_profile", "workzo_live_cv_text", "cv_editor_widget"]:
                            st.session_state[key] = clean
    except Exception:
        pass
    try:
        if callable(globals().get("track_event")):
            track_event("cv_uploaded", "Onboarding", {"mode": mode})
    except Exception:
        pass
    return True


def show_landing_page():
    """Ultra-simple SaaS landing: one message, two actions, one how-it-works row."""
    try: maybe_scroll_to_top()
    except Exception: pass
    apply_workzo_v75_global_css()
    try: render_workzo_header()
    except Exception: pass
    st.markdown("""
    <style id="wz-final-landing-clean-css">

    /* WorkZo v125: stronger landing CTA buttons */
    .st-key-wz_final_landing_upload button,
    .st-key-wz_final_landing_demo button,
    .st-key-wzflow_upload_cv_landing button,
    .st-key-wz_final_upload_cv_landing button,
    .st-key-landing_start_with_cv button,
    .st-key-wz_final_continue_to_job button,
    .st-key-wz_final_start_interview button {
        min-height: 66px !important;
        border-radius: 20px !important;
        font-size: 1.16rem !important;
        font-weight: 950 !important;
        padding: 1rem 1.5rem !important;
        box-shadow: 0 16px 42px rgba(37,99,235,.30) !important;
    }
    .st-key-wz_final_landing_upload button:hover,
    .st-key-wz_final_landing_demo button:hover,
    .st-key-wzflow_upload_cv_landing button:hover,
    .st-key-wz_final_upload_cv_landing button:hover,
    .st-key-landing_start_with_cv button:hover,
    .st-key-wz_final_continue_to_job button:hover,
    .st-key-wz_final_start_interview button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 20px 52px rgba(37,99,235,.40) !important;
    }

    .wz-landing-clean{max-width:1120px;margin:2rem auto 1rem;padding:clamp(1.6rem,4vw,3.4rem);border:1px solid rgba(34,211,238,.26);border-radius:30px;background:radial-gradient(circle at 12% 15%,rgba(20,184,166,.22),transparent 28%),linear-gradient(135deg,rgba(8,47,73,.96),rgba(15,23,42,.98));box-shadow:0 24px 70px rgba(2,6,23,.40)}
    .wz-landing-k{color:#67e8f9;letter-spacing:.18em;text-transform:uppercase;font-size:.78rem;font-weight:950;margin-bottom:.8rem}.wz-landing-clean h1{color:#fff;font-size:clamp(2.25rem,5vw,4.6rem);line-height:1.02;letter-spacing:-.055em;margin:0 0 .85rem;font-weight:950;max-width:920px}.wz-landing-clean p{color:#cbd5e1;font-size:1.12rem;line-height:1.55;max-width:720px}.wz-how{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:.8rem;max-width:1120px;margin:1rem auto}.wz-how div{border:1px solid rgba(148,163,184,.22);border-radius:18px;background:rgba(15,23,42,.55);padding:1rem;color:#dbeafe;font-weight:800}.wz-how span{display:block;color:#94a3b8;font-weight:500;margin-top:.3rem;font-size:.92rem}@media(max-width:800px){.wz-how{grid-template-columns:1fr}.wz-landing-clean{margin-top:1rem}}
    </style>
    <section class="wz-landing-clean"><div class="wz-landing-k">Real Interview AI</div><h1>Face a real interview before the real one</h1><p>Practice an interview based on your CV and the job you want.</p></section>
    """, unsafe_allow_html=True)
    c1,c2,c3 = st.columns([1,1,2])
    with c1:
        if st.button("📄 Upload CV", type="primary", use_container_width=True, key="wz_final_landing_upload"):
            st.session_state["onboarding_step_final"] = 1
            _wz_final_go("onboarding")
    with c2:
        if st.button("⚡ Try Demo", use_container_width=True, key="wz_final_landing_demo"):
            try:
                load_workzo_sample_data()
            except Exception:
                _wz_final_set_cv_text(SAMPLE_CV_TEXT if "SAMPLE_CV_TEXT" in globals() else "Sample CV", "Sample Demo")
                st.session_state["selected_job_description"] = SAMPLE_JOB_DESCRIPTION if "SAMPLE_JOB_DESCRIPTION" in globals() else "Sample job description"
                st.session_state["current_job_description"] = st.session_state["selected_job_description"]
                st.session_state["onboarding_complete"] = True
                _wz_final_go("dashboard")
            _wz_final_safe_rerun()
    st.markdown("""
    <div class="wz-how"><div>1. Upload your CV<span>WorkZo reads your real profile.</span></div><div>2. Paste the job description<span>Prepare for one target role.</span></div><div>3. Start your real interview<span>Practice with CV + job context.</span></div></div>
    """, unsafe_allow_html=True)


def show_onboarding():
    """Frictionless onboarding: CV -> Job -> Start interview."""
    try: maybe_scroll_to_top()
    except Exception: pass
    apply_workzo_v75_global_css()
    step = int(st.session_state.get("onboarding_step_final", 1) or 1)
    if step < 1 or step > 3:
        step = 1
    st.markdown("""
    <style id="wz-onboarding-final-clean-css">
    .wz-onb{max-width:1120px;margin:1.4rem auto}.wz-onb-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:1.8rem}.wz-onb-brand{display:flex;align-items:center;gap:.8rem}.wz-onb-logo{width:58px;height:58px;border-radius:16px}.wz-onb-title{font-size:1.4rem;color:#fff;font-weight:950}.wz-onb-sub{color:#cbd5e1;font-weight:700;font-size:.9rem}.wz-onb-step{color:#dbeafe;font-weight:900}.wz-onb-card{border:1px solid rgba(34,211,238,.24);background:linear-gradient(135deg,rgba(8,47,73,.72),rgba(15,23,42,.96));border-radius:28px;padding:clamp(1.2rem,3vw,2rem);box-shadow:0 20px 55px rgba(2,6,23,.28);margin-bottom:1rem}.wz-onb-card h2{color:#fff;font-size:clamp(2rem,4vw,3rem);letter-spacing:-.04em;margin:.2rem 0 .6rem}.wz-onb-card p{color:#cbd5e1;font-size:1rem;line-height:1.5}.wz-ready{border:1px solid rgba(34,197,94,.28);background:rgba(20,83,45,.22);border-radius:16px;padding:.9rem 1rem;color:#bbf7d0;font-weight:850;margin:.8rem 0}.wz-note{border:1px solid rgba(148,163,184,.22);border-radius:16px;padding:.8rem 1rem;color:#cbd5e1;background:rgba(15,23,42,.55)}
    </style>
    """, unsafe_allow_html=True)
    logo_src = None
    try: logo_src = image_to_data_uri(ICON_PATH) or image_to_data_uri(LOGO_PATH)
    except Exception: logo_src = None
    logo = f'<img src="{logo_src}" class="wz-onb-logo">' if logo_src else '<div class="wz-onb-logo">WZ</div>'
    st.markdown(f'<div class="wz-onb"><div class="wz-onb-head"><div class="wz-onb-brand">{logo}<div><div class="wz-onb-title">WorkZo <span style="color:#22d3ee">AI</span></div><div class="wz-onb-sub">Setup takes less than 2 minutes</div></div></div><div class="wz-onb-step">Step {step} of 3</div></div>', unsafe_allow_html=True)

    if step == 1:
        st.markdown('<section class="wz-onb-card"><h2>Upload your CV</h2><p>This makes every answer, job match, and interview question specific to your profile.</p></section>', unsafe_allow_html=True)
        c1,c2 = st.columns([2,1])
        with c1:
            st.markdown("### 📄 Use your own CV")
            uploaded = st.file_uploader("Upload PDF or TXT", type=["pdf","txt"], key="wz_final_cv_upload")
            if uploaded is not None:
                extracted = ""
                try:
                    if str(getattr(uploaded, 'type', '') or '').lower() == "text/plain" or str(getattr(uploaded, 'name', '')).lower().endswith('.txt'):
                        extracted = uploaded.read().decode('utf-8', errors='ignore')
                    else:
                        extracted = extract_pdf_text(uploaded) if callable(globals().get("extract_pdf_text")) else ""
                except Exception as exc:
                    st.warning(f"Could not read the uploaded CV: {exc}")
                if str(extracted or "").strip():
                    _wz_final_set_cv_text(extracted, "Upload CV")
                    st.success("CV is ready")
                else:
                    st.warning("The file uploaded, but text could not be extracted. Use the paste option below.")
            with st.expander("Paste CV text instead", expanded=not bool(st.session_state.get("cv_text"))):
                pasted = st.text_area("Paste your CV text", height=180, key="wz_final_paste_cv_text")
                if st.button("Use pasted CV", key="wz_final_use_pasted_cv"):
                    if _wz_final_set_cv_text(pasted, "Paste CV"):
                        st.success("CV is ready")
                    else:
                        st.warning("Please paste your CV text first.")
        with c2:
            st.markdown("### ⚡ Try demo")
            st.caption("No CV ready? Explore WorkZo with sample data.")
            if st.button("Skip with Demo CV", use_container_width=True, key="wz_final_skip_demo_cv"):
                if "SAMPLE_CV_TEXT" in globals():
                    _wz_final_set_cv_text(SAMPLE_CV_TEXT, "Sample Demo")
                if "SAMPLE_JOB_DESCRIPTION" in globals():
                    st.session_state["selected_job_description"] = SAMPLE_JOB_DESCRIPTION
                    st.session_state["current_job_description"] = SAMPLE_JOB_DESCRIPTION
                    st.session_state["improve_cv_for_job_desc"] = SAMPLE_JOB_DESCRIPTION
                    st.session_state["interview_jd_text_v117"] = SAMPLE_JOB_DESCRIPTION
                    st.session_state["selected_job"] = {"title":"Junior Data Analyst / IT Support Analyst", "company":"Demo Company", "description":SAMPLE_JOB_DESCRIPTION}
                st.session_state["onboarding_step_final"] = 3
                _wz_final_safe_rerun()
        st.markdown('<div class="wz-note">Privacy: WorkZo uses your CV to personalize guidance. Avoid sharing sensitive details you do not want analyzed.</div>', unsafe_allow_html=True)
        if st.session_state.get("cv_text"):
            if st.button("Continue to job", type="primary", use_container_width=True, key="wz_final_continue_to_job"):
                st.session_state["onboarding_step_final"] = 2
                _wz_final_safe_rerun()

    elif step == 2:
        st.markdown('<section class="wz-onb-card"><h2>Paste the job you want</h2><p>Add one job description so WorkZo can tailor the CV, questions, and feedback to that exact role.</p></section>', unsafe_allow_html=True)
        title = st.text_input("Job title", value=st.session_state.get("target_role") or "", placeholder="Example: Data Analyst", key="wz_final_job_title")
        company = st.text_input("Company / employer (optional)", value=st.session_state.get("selected_company") or "", placeholder="Example: Amazon", key="wz_final_company")
        jd = st.text_area("Job description", height=260, value=st.session_state.get("selected_job_description") or st.session_state.get("current_job_description") or "", key="wz_final_jd_text")
        c1,c2 = st.columns([1,1])
        with c1:
            if st.button("Back", use_container_width=True, key="wz_final_back_to_cv"):
                st.session_state["onboarding_step_final"] = 1
                _wz_final_safe_rerun()
        with c2:
            if st.button("Continue", type="primary", use_container_width=True, key="wz_final_save_job"):
                if not str(jd or "").strip():
                    st.warning("Please paste the job description, or use demo mode.")
                else:
                    st.session_state["target_role"] = title.strip() or st.session_state.get("target_role") or "Target role"
                    st.session_state["selected_company"] = company.strip()
                    job = {"title": st.session_state["target_role"], "company": company.strip() or "Target company", "description": jd, "location": st.session_state.get("country", "")}
                    st.session_state["selected_job"] = job
                    for key in ["selected_job_description", "current_job_description", "last_understand_job_description", "last_prepare_job_description", "improve_cv_for_job_desc", "job_description", "interview_jd_text_v117"]:
                        st.session_state[key] = jd
                    st.session_state["prepare_job_selected"] = True
                    st.session_state["onboarding_step_final"] = 3
                    _wz_final_safe_rerun()

    else:
        st.markdown('<section class="wz-onb-card"><h2>You’re ready.</h2><p>Your interview will use your CV and target job context.</p></section>', unsafe_allow_html=True)
        st.success("CV is ready")
        if st.session_state.get("selected_job_description"):
            st.success("Job is ready")
        if st.button("🎤 Start Real Interview", type="primary", use_container_width=True, key="wz_final_start_interview"):
            st.session_state["onboarding_complete"] = True
            _wz_final_go("real_interview")
        st.caption("Dashboard is available later from the header after you start or finish the interview.")
    st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# WorkZo v125 - landing CTA final size patch
# Keeps the existing landing page, only makes the main CTA buttons bigger.
# =========================================================
try:
    _wz125_previous_show_landing_page = show_landing_page
    def show_landing_page():
        st.markdown("""
        <style id="workzo-v125-landing-cta-size-final">
        .st-key-wz_final_landing_upload button,
        .st-key-wz_final_landing_demo button,
        .st-key-wzflow_upload_cv_landing button,
        .st-key-wz_final_upload_cv_landing button,
        .st-key-landing_start_with_cv button,
        .st-key-wz_final_continue_to_job button,
        .st-key-wz_final_start_interview button {
            min-height: 66px !important;
            border-radius: 20px !important;
            font-size: 1.16rem !important;
            font-weight: 950 !important;
            padding: 1rem 1.5rem !important;
            box-shadow: 0 16px 42px rgba(37,99,235,.30) !important;
        }
        .st-key-wz_final_landing_upload button:hover,
        .st-key-wz_final_landing_demo button:hover,
        .st-key-wzflow_upload_cv_landing button:hover,
        .st-key-wz_final_upload_cv_landing button:hover,
        .st-key-landing_start_with_cv button:hover,
        .st-key-wz_final_continue_to_job button:hover,
        .st-key-wz_final_start_interview button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 20px 52px rgba(37,99,235,.40) !important;
        }
        </style>
        """, unsafe_allow_html=True)
        return _wz125_previous_show_landing_page()
except Exception:
    pass


# =========================================================
# WorkZo v126 - Final landing polish requested May 6
# - Remove progress from logo/name card
# - Remove Try Demo button from landing
# - Rename Upload CV to Let's start now
# - Make main CTA larger
# =========================================================

def _wz126_landing_polish_css():
    try:
        st.markdown("""
        <style id="workzo-v126-landing-polish-css">
        /* Hide progress in landing/header card */
        .workzo-progress-wrap,
        .workzo-progress-top,
        .workzo-progress-bar,
        .workzo-progress-fill,
        .workzo-progress-steps {
            display: none !important;
        }
        .workzo-header,
        .workzo-topbar,
        .workzo-brand-shell,
        .workzo-brand-card {
            border-radius: 26px !important;
            border: 1px solid rgba(34,211,238,.26) !important;
            background: linear-gradient(135deg, rgba(8,47,73,.72), rgba(15,23,42,.96)) !important;
            box-shadow: 0 20px 58px rgba(2,6,23,.34) !important;
        }
        .workzo-title { font-size: 1.35rem !important; letter-spacing: -.04em !important; }
        .workzo-subtitle { color: #cbd5e1 !important; font-size: .9rem !important; font-weight: 800 !important; }
        .st-key-wz126_landing_start button,
        .st-key-wz_final_landing_upload button,
        .st-key-wzflow_upload_cv_landing button,
        .st-key-wz_final_upload_cv_landing button,
        .st-key-landing_start_with_cv button {
            min-height: 72px !important;
            border-radius: 22px !important;
            font-size: 1.22rem !important;
            font-weight: 950 !important;
            padding: 1.05rem 1.65rem !important;
            background: linear-gradient(135deg, #ff4b4b, #ef4444) !important;
            box-shadow: 0 18px 48px rgba(239,68,68,.30) !important;
        }
        .st-key-wz126_landing_start button:hover,
        .st-key-wz_final_landing_upload button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 22px 58px rgba(239,68,68,.42) !important;
        }
        .wz-landing-clean{
            margin-top: 2.2rem !important;
            border-radius: 32px !important;
            border-color: rgba(34,211,238,.28) !important;
            box-shadow: 0 26px 75px rgba(2,6,23,.42) !important;
        }
        </style>
        """, unsafe_allow_html=True)
    except Exception:
        pass


def show_landing_page():
    """v126: clean landing with one bigger CTA and no demo button."""
    try: maybe_scroll_to_top()
    except Exception: pass
    try: apply_workzo_v75_global_css()
    except Exception: pass
    try: _wz126_landing_polish_css()
    except Exception: pass
    try: render_workzo_header()
    except Exception: pass
    try: _wz126_landing_polish_css()
    except Exception: pass

    st.markdown("""
    <style id="wz126-landing-clean-css">
    .wz-landing-clean{max-width:1120px;margin:2rem auto 1rem;padding:clamp(1.6rem,4vw,3.4rem);border:1px solid rgba(34,211,238,.26);border-radius:30px;background:radial-gradient(circle at 12% 15%,rgba(20,184,166,.22),transparent 28%),linear-gradient(135deg,rgba(8,47,73,.96),rgba(15,23,42,.98));box-shadow:0 24px 70px rgba(2,6,23,.40)}
    .wz-landing-k{color:#67e8f9;letter-spacing:.18em;text-transform:uppercase;font-size:.78rem;font-weight:950;margin-bottom:.8rem}
    .wz-landing-clean h1{color:#fff;font-size:clamp(2.25rem,5vw,4.6rem);line-height:1.02;letter-spacing:-.055em;margin:0 0 .85rem;font-weight:950;max-width:920px}
    .wz-landing-clean p{color:#cbd5e1;font-size:1.12rem;line-height:1.55;max-width:720px}
    .wz-how{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:.8rem;max-width:1120px;margin:1rem auto}
    .wz-how div{border:1px solid rgba(148,163,184,.22);border-radius:18px;background:rgba(15,23,42,.55);padding:1rem;color:#dbeafe;font-weight:800}
    .wz-how span{display:block;color:#94a3b8;font-weight:500;margin-top:.3rem;font-size:.92rem}
    @media(max-width:800px){.wz-how{grid-template-columns:1fr}.wz-landing-clean{margin-top:1rem}}
    </style>
    <section class="wz-landing-clean">
      <div class="wz-landing-k">Real Interview AI</div>
      <h1>Face a real interview before the real one</h1>
      <p>Practice an interview based on your CV and the job you want.</p>
    </section>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns([1.25, 2.75])
    with c1:
        if st.button("Let’s start now", type="primary", use_container_width=True, key="wz126_landing_start"):
            st.session_state["onboarding_step_final"] = 1
            _wz_final_go("onboarding")
    st.markdown("""
    <div class="wz-how">
      <div>1. Upload your CV<span>WorkZo reads your real profile.</span></div>
      <div>2. Paste the job description<span>Prepare for one target role.</span></div>
      <div>3. Start your real interview<span>Practice with CV + job context.</span></div>
    </div>
    """, unsafe_allow_html=True)


# =========================================================
# WorkZo v127 - Landing CTA final polish
# - Pastel rainbow CTA matching dark background
# - Remove progress + demo button from landing/header
# - Rename primary CTA to Let's start now
# =========================================================
def _wz127_landing_pastel_css():
    try:
        st.markdown("""
        <style id="workzo-v127-landing-pastel-css">
        .workzo-progress-wrap,.workzo-progress-top,.workzo-progress-bar,.workzo-progress-fill,.workzo-progress-steps{display:none!important;}
        .st-key-wz_final_landing_demo,.st-key-wzflow_try_demo_landing,.st-key-wz_final_demo_landing,.st-key-wz_final_landing_demo{display:none!important;}
        .workzo-header,.workzo-topbar,.workzo-brand-shell,.workzo-brand-card{
            max-width:1120px!important;margin-left:auto!important;margin-right:auto!important;
            border-radius:28px!important;border:1px solid rgba(125,211,252,.28)!important;
            background:linear-gradient(135deg,rgba(8,47,73,.78),rgba(15,23,42,.96))!important;
            box-shadow:0 22px 60px rgba(2,6,23,.38)!important;
        }
        .workzo-title{font-size:1.45rem!important;letter-spacing:-.04em!important;font-weight:950!important;}
        .workzo-subtitle{color:#dbeafe!important;font-size:.95rem!important;font-weight:800!important;}
        .st-key-wz127_landing_start button,
        .st-key-wz126_landing_start button,
        .st-key-wz_final_landing_upload button,
        .st-key-wzflow_upload_cv_landing button,
        .st-key-wz_final_upload_cv_landing button,
        .st-key-landing_start_with_cv button{
            min-height:78px!important;border-radius:24px!important;padding:1.12rem 1.8rem!important;
            font-size:1.22rem!important;font-weight:950!important;color:#07111f!important;
            border:1px solid rgba(255,255,255,.42)!important;
            background:linear-gradient(135deg,#fde68a 0%,#fbcfe8 34%,#bae6fd 67%,#bbf7d0 100%)!important;
            box-shadow:0 20px 55px rgba(125,211,252,.22),0 12px 38px rgba(251,207,232,.16)!important;
        }
        .st-key-wz127_landing_start button p,
        .st-key-wz126_landing_start button p,
        .st-key-wz_final_landing_upload button p,
        .st-key-wzflow_upload_cv_landing button p,
        .st-key-wz_final_upload_cv_landing button p,
        .st-key-landing_start_with_cv button p{font-size:1.22rem!important;font-weight:950!important;color:#07111f!important;}
        .st-key-wz127_landing_start button:hover,
        .st-key-wz126_landing_start button:hover,
        .st-key-wz_final_landing_upload button:hover,
        .st-key-wzflow_upload_cv_landing button:hover,
        .st-key-wz_final_upload_cv_landing button:hover,
        .st-key-landing_start_with_cv button:hover{
            transform:translateY(-2px)!important;
            box-shadow:0 24px 68px rgba(125,211,252,.32),0 16px 46px rgba(251,207,232,.22)!important;
            filter:saturate(1.04)!important;
        }
        .wz-landing-clean{
            margin-top:2.25rem!important;border-radius:32px!important;
            border-color:rgba(125,211,252,.30)!important;
            background:radial-gradient(circle at 10% 12%,rgba(34,211,238,.20),transparent 30%),linear-gradient(135deg,rgba(8,47,73,.92),rgba(15,23,42,.98))!important;
            box-shadow:0 28px 78px rgba(2,6,23,.42)!important;
        }
        </style>
        """, unsafe_allow_html=True)
    except Exception:
        pass


def show_landing_page():
    """v127: final landing page with one pastel CTA only."""
    try: maybe_scroll_to_top()
    except Exception: pass
    try: apply_workzo_v75_global_css()
    except Exception: pass
    try: _wz127_landing_pastel_css()
    except Exception: pass
    try: render_workzo_header()
    except Exception: pass
    try: _wz127_landing_pastel_css()
    except Exception: pass

    st.markdown("""
    <style id="wz127-landing-clean-css">
    .wz-landing-clean{max-width:1120px;margin:2rem auto 1rem;padding:clamp(1.65rem,4vw,3.5rem);border:1px solid rgba(34,211,238,.26);border-radius:30px;background:radial-gradient(circle at 12% 15%,rgba(20,184,166,.22),transparent 28%),linear-gradient(135deg,rgba(8,47,73,.96),rgba(15,23,42,.98));box-shadow:0 24px 70px rgba(2,6,23,.40)}
    .wz-landing-k{color:#67e8f9;letter-spacing:.18em;text-transform:uppercase;font-size:.78rem;font-weight:950;margin-bottom:.8rem}
    .wz-landing-clean h1{color:#fff;font-size:clamp(2.2rem,5vw,4.6rem);line-height:1.02;letter-spacing:-.055em;margin:0 0 .85rem;font-weight:950;max-width:980px}
    .wz-landing-clean p{color:#dbeafe;font-size:1.12rem;line-height:1.55;max-width:760px}
    .wz-how{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:.8rem;max-width:1120px;margin:1.1rem auto}
    .wz-how div{border:1px solid rgba(148,163,184,.22);border-radius:18px;background:rgba(15,23,42,.55);padding:1rem;color:#dbeafe;font-weight:850}
    .wz-how span{display:block;color:#94a3b8;font-weight:600;margin-top:.3rem;font-size:.92rem}
    @media(max-width:800px){.wz-how{grid-template-columns:1fr}.wz-landing-clean{margin-top:1rem}}
    </style>
    <section class="wz-landing-clean">
      <div class="wz-landing-k">Real Interview AI</div>
      <h1>Practice a real interview using your CV and job description.</h1>
      <p>Upload your CV, improve it for the role, and prepare with WorkZo AI.</p>
    </section>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 1.35, 1])
    with c2:
        if st.button("🚀 Let’s start now", type="primary", use_container_width=True, key="wz127_landing_start"):
            st.session_state["onboarding_step_final"] = 1
            try:
                _wz_final_go("onboarding")
            except Exception:
                st.session_state["page"] = "onboarding"
                st.session_state["nav_page"] = "onboarding"
                st.rerun()

    st.markdown("""
    <div class="wz-how">
      <div>1. Upload your CV<span>WorkZo reads your real profile.</span></div>
      <div>2. Paste the job description<span>Prepare for one target role.</span></div>
      <div>3. Start your real interview<span>Practice with CV + job context.</span></div>
    </div>
    """, unsafe_allow_html=True)



# =========================================================
# WorkZo v128 - Landing page conversion upgrade
# Purpose:
# - Make hero feel alive with animated interview preview
# - Place primary CTA visually inside hero area
# - Make CTA large pastel/rainbow and premium
# - Remove demo/progress clutter
# - Reduce top brand card height
# - Add credibility signal and connected 3-step flow
# =========================================================

def _wz128_landing_live_preview_css():
    try:
        st.markdown("""
        <style id="workzo-v128-landing-live-preview-css">
        /* Compact brand card / navbar */
        .workzo-progress-wrap,
        .workzo-progress-top,
        .workzo-progress-bar,
        .workzo-progress-fill,
        .workzo-progress-steps,
        .st-key-wz_final_landing_demo,
        .st-key-wzflow_try_demo_landing,
        .st-key-wz_final_demo_landing {
            display:none!important;
        }

        .workzo-header,
        .workzo-topbar,
        .workzo-brand-shell,
        .workzo-brand-card{
            max-width:1120px!important;
            min-height:76px!important;
            padding:14px 18px!important;
            margin-left:auto!important;
            margin-right:auto!important;
            border-radius:24px!important;
            border:1px solid rgba(34,211,238,.26)!important;
            background:linear-gradient(135deg,rgba(8,47,73,.72),rgba(15,23,42,.96))!important;
            box-shadow:0 18px 52px rgba(2,6,23,.34)!important;
        }
        .workzo-title{
            font-size:1.32rem!important;
            letter-spacing:-.045em!important;
            font-weight:950!important;
        }
        .workzo-subtitle{
            color:#dbeafe!important;
            font-size:.88rem!important;
            font-weight:800!important;
        }

        /* Hero */
        .wz128-hero{
            max-width:1120px;
            margin:clamp(1.1rem,3vw,2.1rem) auto 1.1rem;
            padding:clamp(1.35rem,3vw,2.6rem);
            border-radius:34px;
            border:1px solid rgba(125,211,252,.30);
            background:
                radial-gradient(circle at 8% 10%,rgba(45,212,191,.24),transparent 28%),
                radial-gradient(circle at 90% 18%,rgba(168,85,247,.16),transparent 26%),
                linear-gradient(135deg,rgba(8,47,73,.94),rgba(15,23,42,.98));
            box-shadow:0 30px 85px rgba(2,6,23,.46);
            position:relative;
            overflow:hidden;
        }
        .wz128-hero:before{
            content:"";
            position:absolute;
            inset:-45%;
            background:conic-gradient(from 180deg,transparent,rgba(34,211,238,.10),rgba(251,207,232,.10),rgba(187,247,208,.08),transparent);
            animation:wz128GlowSpin 9s linear infinite;
            opacity:.55;
        }
        @keyframes wz128GlowSpin{to{transform:rotate(360deg)}}
        .wz128-hero-inner{
            position:relative;
            display:grid;
            grid-template-columns:minmax(0,1.05fr) minmax(330px,.72fr);
            gap:clamp(1.2rem,3vw,2.2rem);
            align-items:center;
        }
        .wz128-kicker{
            color:#67e8f9;
            letter-spacing:.18em;
            text-transform:uppercase;
            font-size:.78rem;
            font-weight:950;
            margin-bottom:.9rem;
        }
        .wz128-title{
            color:#fff;
            font-size:clamp(2.35rem,5.5vw,4.85rem);
            line-height:1.01;
            letter-spacing:-.062em;
            margin:0 0 1rem;
            font-weight:950;
            max-width:850px;
        }
        .wz128-subtitle{
            color:#dbeafe;
            font-size:clamp(1.02rem,1.4vw,1.18rem);
            line-height:1.58;
            max-width:710px;
            margin:0 0 1rem;
        }
        .wz128-proof-row{
            display:flex;
            flex-wrap:wrap;
            gap:.55rem;
            margin:.95rem 0 1.15rem;
        }
        .wz128-proof-pill{
            border:1px solid rgba(186,230,253,.24);
            background:rgba(15,23,42,.46);
            color:#bfdbfe;
            border-radius:999px;
            padding:.48rem .72rem;
            font-size:.84rem;
            font-weight:850;
        }

        /* Live interview preview */
        .wz128-preview{
            border:1px solid rgba(148,163,184,.22);
            border-radius:28px;
            background:linear-gradient(180deg,rgba(15,23,42,.84),rgba(2,6,23,.78));
            box-shadow:0 22px 60px rgba(2,6,23,.38);
            padding:1rem;
            position:relative;
        }
        .wz128-preview-top{
            display:flex;
            align-items:center;
            justify-content:space-between;
            gap:.7rem;
            margin-bottom:.85rem;
        }
        .wz128-recruiter{
            display:flex;
            align-items:center;
            gap:.7rem;
        }
        .wz128-avatar{
            width:44px;height:44px;
            border-radius:16px;
            display:grid;place-items:center;
            background:linear-gradient(135deg,#67e8f9,#818cf8);
            box-shadow:0 14px 34px rgba(96,165,250,.22);
            animation:wz128Pulse 2.2s ease-in-out infinite;
        }
        @keyframes wz128Pulse{0%,100%{transform:scale(1);box-shadow:0 14px 34px rgba(96,165,250,.22)}50%{transform:scale(1.04);box-shadow:0 16px 42px rgba(45,212,191,.34)}}
        .wz128-rec-name{color:#f8fafc;font-weight:950;font-size:.98rem;line-height:1.1}
        .wz128-rec-status{color:#94a3b8;font-size:.78rem;font-weight:700;margin-top:.18rem}
        .wz128-timer{
            color:#fecaca;
            background:rgba(127,29,29,.22);
            border:1px solid rgba(248,113,113,.24);
            border-radius:999px;
            padding:.36rem .58rem;
            font-weight:950;
            font-size:.82rem;
            min-width:58px;
            text-align:center;
        }
        .wz128-chat-bubble{
            border-radius:20px;
            padding:.85rem .95rem;
            margin:.6rem 0;
            font-size:.92rem;
            line-height:1.45;
        }
        .wz128-chat-bubble.ai{
            color:#e0f2fe;
            background:rgba(30,41,59,.74);
            border:1px solid rgba(125,211,252,.16);
        }
        .wz128-chat-bubble.user{
            color:#f8fafc;
            background:rgba(37,99,235,.20);
            border:1px solid rgba(96,165,250,.22);
            margin-left:2.2rem;
        }
        .wz128-listening{
            display:flex;
            align-items:center;
            justify-content:space-between;
            gap:.8rem;
            margin-top:.8rem;
            border:1px solid rgba(45,212,191,.20);
            background:rgba(20,184,166,.10);
            border-radius:18px;
            padding:.72rem .8rem;
            color:#ccfbf1;
            font-size:.82rem;
            font-weight:850;
        }
        .wz128-dots{display:flex;gap:.24rem;align-items:center}
        .wz128-dots span{
            width:7px;height:7px;border-radius:99px;background:#67e8f9;
            animation:wz128Dot 1.2s infinite ease-in-out;
        }
        .wz128-dots span:nth-child(2){animation-delay:.16s}
        .wz128-dots span:nth-child(3){animation-delay:.32s}
        @keyframes wz128Dot{0%,80%,100%{opacity:.28;transform:translateY(0)}40%{opacity:1;transform:translateY(-4px)}}
        .wz128-feedback-mini{
            margin-top:.75rem;
            border-radius:18px;
            padding:.72rem .85rem;
            background:linear-gradient(135deg,rgba(250,204,21,.12),rgba(251,207,232,.10));
            border:1px solid rgba(253,224,71,.18);
            color:#fde68a;
            font-size:.82rem;
            font-weight:850;
        }

        /* CTA: deliberately oversized and pastel/rainbow */
        .st-key-wz128_landing_start{
            max-width:1120px!important;
            margin:-105px auto 1.45rem!important;
            padding-left:clamp(1.35rem,3vw,2.6rem)!important;
            position:relative!important;
            z-index:9!important;
        }
        .st-key-wz128_landing_start button{
            width:min(430px,100%)!important;
            min-height:82px!important;
            border-radius:26px!important;
            padding:1.15rem 2rem!important;
            font-size:1.22rem!important;
            font-weight:950!important;
            color:#07111f!important;
            border:1px solid rgba(255,255,255,.50)!important;
            background:linear-gradient(135deg,#fde68a 0%,#fbcfe8 32%,#bae6fd 66%,#bbf7d0 100%)!important;
            box-shadow:0 26px 70px rgba(125,211,252,.28),0 18px 52px rgba(251,207,232,.20)!important;
            transition:all .18s ease!important;
        }
        .st-key-wz128_landing_start button p{
            color:#07111f!important;
            font-size:1.22rem!important;
            font-weight:950!important;
        }
        .st-key-wz128_landing_start button:hover{
            transform:translateY(-3px) scale(1.012)!important;
            filter:saturate(1.05)!important;
            box-shadow:0 30px 82px rgba(125,211,252,.38),0 22px 62px rgba(251,207,232,.26)!important;
        }

        /* Hide old landing CTA variants if they appear from previous overrides */
        .st-key-wz127_landing_start,
        .st-key-wz126_landing_start,
        .st-key-wz_final_landing_upload,
        .st-key-wzflow_upload_cv_landing,
        .st-key-wz_final_upload_cv_landing,
        .st-key-landing_start_with_cv{
            display:none!important;
        }

        /* Three-step flow */
        .wz128-flow{
            max-width:1120px;
            margin:1rem auto 0;
            display:grid;
            grid-template-columns:repeat(3,minmax(0,1fr));
            gap:.9rem;
            position:relative;
        }
        .wz128-step{
            border:1px solid rgba(148,163,184,.20);
            border-radius:22px;
            background:rgba(15,23,42,.56);
            padding:1.05rem;
            color:#dbeafe;
            font-weight:900;
            min-height:118px;
            position:relative;
            overflow:hidden;
        }
        .wz128-step:before{
            content:"";
            position:absolute;inset:auto 14px 14px auto;
            width:54px;height:54px;border-radius:18px;
            background:rgba(34,211,238,.10);
        }
        .wz128-step-icon{
            font-size:1.55rem;
            margin-bottom:.45rem;
        }
        .wz128-step span{
            display:block;
            color:#94a3b8;
            font-weight:650;
            margin-top:.35rem;
            font-size:.92rem;
            line-height:1.38;
        }
        .wz128-step-arrow{
            position:absolute;
            top:48%;right:-18px;
            color:#67e8f9;
            font-weight:950;
            z-index:3;
            opacity:.65;
        }

        @media(max-width:920px){
            .wz128-hero-inner{grid-template-columns:1fr;}
            .wz128-preview{margin-top:.5rem;}
            .st-key-wz128_landing_start{margin:-18px auto 1.25rem!important;padding:0 1rem!important;}
            .st-key-wz128_landing_start button{width:100%!important;min-height:74px!important;}
            .wz128-flow{grid-template-columns:1fr;margin-left:1rem;margin-right:1rem;}
            .wz128-step-arrow{display:none;}
        }
        </style>
        """, unsafe_allow_html=True)
    except Exception:
        pass


def show_landing_page():
    """v128: animated interview landing page with stronger conversion-focused hero."""
    try:
        maybe_scroll_to_top()
    except Exception:
        pass
    try:
        apply_workzo_v75_global_css()
    except Exception:
        pass
    try:
        _wz128_landing_live_preview_css()
    except Exception:
        pass
    try:
        render_workzo_header()
    except Exception:
        pass
    try:
        _wz128_landing_live_preview_css()
    except Exception:
        pass

    st.markdown("""
    <section class="wz128-hero">
      <div class="wz128-hero-inner">
        <div>
          <div class="wz128-kicker">Real Interview AI</div>
          <h1 class="wz128-title">Face a real interview before the real one</h1>
          <p class="wz128-subtitle">Practice realistic interviews with pressure, recruiter-style follow-ups, and feedback based on your CV and target job.</p>
          <div class="wz128-proof-row">
            <span class="wz128-proof-pill">No generic mock questions</span>
            <span class="wz128-proof-pill">Personalized from CV + JD</span>
            <span class="wz128-proof-pill">Recruiter-style follow-ups</span>
          </div>
        </div>

        <div class="wz128-preview" aria-label="Live interview preview">
          <div class="wz128-preview-top">
            <div class="wz128-recruiter">
              <div class="wz128-avatar">🤖</div>
              <div>
                <div class="wz128-rec-name">AI Recruiter</div>
                <div class="wz128-rec-status">Listening for proof and impact</div>
              </div>
            </div>
            <div class="wz128-timer">00:45</div>
          </div>
          <div class="wz128-chat-bubble ai">Tell me about yourself — but keep it relevant to this role.</div>
          <div class="wz128-chat-bubble user">I worked in technical support and handled customer issues...</div>
          <div class="wz128-listening">
            <span>Recruiter is typing a follow-up</span>
            <div class="wz128-dots"><span></span><span></span><span></span></div>
          </div>
          <div class="wz128-feedback-mini">⚠️ You’re losing me — give me one measurable result.</div>
        </div>
      </div>
    </section>
    """, unsafe_allow_html=True)

    if st.button("✨ Let’s start now", type="primary", use_container_width=False, key="wz128_landing_start"):
        st.session_state["onboarding_step_final"] = 1
        try:
            _wz_final_go("onboarding")
        except Exception:
            st.session_state["page"] = "onboarding"
            st.session_state["nav_page"] = "onboarding"
            st.rerun()

    st.markdown("""
    <div class="wz128-flow">
      <div class="wz128-step"><div class="wz128-step-icon">📄</div>1. Upload your CV<span>WorkZo reads your real profile and interview context.</span><div class="wz128-step-arrow">→</div></div>
      <div class="wz128-step"><div class="wz128-step-icon">🎯</div>2. Paste the job description<span>The interview becomes specific to the role you want.</span><div class="wz128-step-arrow">→</div></div>
      <div class="wz128-step"><div class="wz128-step-icon">🎤</div>3. Start your real interview<span>Answer under pressure and get recruiter-style feedback.</span></div>
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# WorkZo v129 - Landing live preview render fix
# Purpose: override previous landing hero so the interview preview
# renders as HTML instead of showing raw <div> text.
# =========================================================
def show_landing_page():
    """v129: fixed animated landing page. Preview HTML is minified to avoid Markdown code rendering."""
    try:
        maybe_scroll_to_top()
    except Exception:
        pass
    try:
        apply_workzo_v75_global_css()
    except Exception:
        pass
    try:
        _wz128_landing_live_preview_css()
    except Exception:
        pass
    try:
        render_workzo_header()
    except Exception:
        pass
    try:
        _wz128_landing_live_preview_css()
    except Exception:
        pass

    hero_html = (
        '<section class="wz128-hero">'
        '<div class="wz128-hero-inner">'
        '<div>'
        '<div class="wz128-kicker">Real Interview AI</div>'
        '<h1 class="wz128-title">Face a real interview before the real one</h1>'
        '<p class="wz128-subtitle">Practice realistic interviews with pressure, recruiter-style follow-ups, and feedback based on your CV and target job.</p>'
        '<div class="wz128-proof-row">'
        '<span class="wz128-proof-pill">No generic mock questions</span>'
        '<span class="wz128-proof-pill">Personalized from CV + JD</span>'
        '<span class="wz128-proof-pill">Recruiter-style follow-ups</span>'
        '</div>'
        '</div>'
        '<div class="wz128-preview" aria-label="Live interview preview">'
        '<div class="wz128-preview-top">'
        '<div class="wz128-recruiter">'
        '<div class="wz128-avatar">🤖</div>'
        '<div><div class="wz128-rec-name">AI Recruiter</div><div class="wz128-rec-status">Listening for proof and impact</div></div>'
        '</div>'
        '<div class="wz128-timer">00:45</div>'
        '</div>'
        '<div class="wz128-chat-bubble ai">Tell me about yourself — but keep it relevant to this role.</div>'
        '<div class="wz128-chat-bubble user">I worked in technical support and handled customer issues...</div>'
        '<div class="wz128-listening"><span>Recruiter is typing a follow-up</span><div class="wz128-dots"><span></span><span></span><span></span></div></div>'
        '<div class="wz128-feedback-mini">⚠️ You’re losing me — give me one measurable result.</div>'
        '</div>'
        '</div>'
        '</section>'
    )
    st.markdown(hero_html, unsafe_allow_html=True)

    if st.button("✨ Let’s start now", type="primary", use_container_width=False, key="wz128_landing_start"):
        st.session_state["onboarding_step_final"] = 1
        try:
            _wz_final_go("onboarding")
        except Exception:
            st.session_state["page"] = "onboarding"
            st.session_state["nav_page"] = "onboarding"
            st.rerun()

    flow_html = (
        '<div class="wz128-flow">'
        '<div class="wz128-step"><div class="wz128-step-icon">📄</div>1. Upload your CV<span>WorkZo reads your real profile and interview context.</span><div class="wz128-step-arrow">→</div></div>'
        '<div class="wz128-step"><div class="wz128-step-icon">🎯</div>2. Paste the job description<span>The interview becomes specific to the role you want.</span><div class="wz128-step-arrow">→</div></div>'
        '<div class="wz128-step"><div class="wz128-step-icon">🎤</div>3. Start your real interview<span>Answer under pressure and get recruiter-style feedback.</span></div>'
        '</div>'
    )
    st.markdown(flow_html, unsafe_allow_html=True)


# =========================================================
# WorkZo v130 - Serious interview landing polish
# Purpose:
# - Replace pastel CTA with serious neon/electric interview-tech CTA
# - Keep CTA visually inside hero without breaking Streamlit navigation
# - Add believable live-interview details: waveform, confidence meter, live tag
# - Add one emotional trust/proof line
# - Reduce navbar/brand vertical height for better above-the-fold view
# =========================================================

def _wz130_landing_serious_cta_css():
    try:
        st.markdown("""
        <style id="workzo-v130-landing-serious-cta-css">
        /* Make top brand/header less tall */
        .workzo-header,
        .workzo-topbar,
        .workzo-brand-shell,
        .workzo-brand-card{
            max-width:1120px!important;
            min-height:66px!important;
            padding:10px 16px!important;
            border-radius:22px!important;
            margin-top:.5rem!important;
            margin-bottom:.8rem!important;
            background:linear-gradient(135deg,rgba(8,47,73,.72),rgba(15,23,42,.94))!important;
            border:1px solid rgba(34,211,238,.24)!important;
            box-shadow:0 16px 46px rgba(2,6,23,.30)!important;
        }
        .workzo-logo,
        .workzo-sidebar-logo,
        .wzfinal-logo,
        .wzflow-logo{
            width:52px!important;
            height:52px!important;
        }
        .workzo-title{font-size:1.24rem!important;line-height:1.05!important;}
        .workzo-subtitle{font-size:.82rem!important;line-height:1.2!important;}

        /* Hide older landing CTA variants */
        .st-key-wz128_landing_start,
        .st-key-wz127_landing_start,
        .st-key-wz126_landing_start,
        .st-key-wz_final_landing_upload,
        .st-key-wzflow_upload_cv_landing,
        .st-key-wz_final_upload_cv_landing,
        .st-key-landing_start_with_cv{
            display:none!important;
        }

        .wz130-hero{
            max-width:1120px;
            margin:clamp(.85rem,2vw,1.45rem) auto 1.1rem;
            padding:clamp(1.3rem,2.8vw,2.45rem) clamp(1.35rem,3vw,2.7rem) clamp(6.4rem,7.5vw,7.4rem);
            border-radius:34px;
            border:1px solid rgba(34,211,238,.32);
            background:
                radial-gradient(circle at 5% 8%,rgba(45,212,191,.25),transparent 28%),
                radial-gradient(circle at 82% 12%,rgba(37,99,235,.28),transparent 30%),
                linear-gradient(135deg,rgba(8,47,73,.96),rgba(15,23,42,.98));
            box-shadow:0 30px 88px rgba(2,6,23,.52), inset 0 1px 0 rgba(255,255,255,.04);
            position:relative;
            overflow:hidden;
        }
        .wz130-hero:before{
            content:"";
            position:absolute;
            inset:-30%;
            background:conic-gradient(from 180deg,transparent,rgba(34,211,238,.11),rgba(59,130,246,.13),transparent 58%);
            animation:wz130GlowSpin 10s linear infinite;
            opacity:.64;
        }
        @keyframes wz130GlowSpin{to{transform:rotate(360deg)}}
        .wz130-hero-inner{
            position:relative;
            display:grid;
            grid-template-columns:minmax(0,1.02fr) minmax(340px,.72fr);
            gap:clamp(1.25rem,3vw,2.35rem);
            align-items:center;
        }
        .wz130-kicker{
            color:#67e8f9;
            letter-spacing:.18em;
            text-transform:uppercase;
            font-size:.76rem;
            font-weight:950;
            margin-bottom:.85rem;
        }
        .wz130-title{
            color:#fff;
            font-size:clamp(2.25rem,5.3vw,4.6rem);
            line-height:1.015;
            letter-spacing:-.061em;
            margin:0 0 .95rem;
            font-weight:950;
            max-width:820px;
        }
        .wz130-subtitle{
            color:#dbeafe;
            font-size:clamp(1.02rem,1.35vw,1.16rem);
            line-height:1.55;
            max-width:700px;
            margin:0 0 .95rem;
        }
        .wz130-proof-line{
            display:inline-flex;
            align-items:center;
            gap:.45rem;
            color:#a7f3d0;
            background:rgba(20,184,166,.09);
            border:1px solid rgba(45,212,191,.18);
            border-radius:999px;
            padding:.5rem .75rem;
            font-size:.84rem;
            font-weight:850;
            margin:.1rem 0 .85rem;
        }
        .wz130-proof-row{display:flex;flex-wrap:wrap;gap:.55rem;margin:.25rem 0 0;}
        .wz130-proof-pill{
            border:1px solid rgba(186,230,253,.22);
            background:rgba(15,23,42,.50);
            color:#bfdbfe;
            border-radius:999px;
            padding:.46rem .70rem;
            font-size:.82rem;
            font-weight:850;
        }

        /* Serious neon CTA - visually placed inside hero */
        .st-key-wz130_landing_start{
            max-width:1120px!important;
            margin:clamp(-6.95rem,-7vw,-5.7rem) auto 2.15rem!important;
            padding-left:clamp(1.35rem,3vw,2.7rem)!important;
            padding-right:clamp(1.35rem,3vw,2.7rem)!important;
            position:relative!important;
            z-index:20!important;
        }
        .st-key-wz130_landing_start button{
            width:min(340px,100%)!important;
            min-height:66px!important;
            border-radius:20px!important;
            padding:1rem 1.35rem!important;
            font-size:1.08rem!important;
            font-weight:950!important;
            letter-spacing:-.02em!important;
            color:#eff6ff!important;
            border:1px solid rgba(125,211,252,.62)!important;
            background:
                radial-gradient(circle at 15% 10%,rgba(103,232,249,.42),transparent 34%),
                linear-gradient(135deg,#0f172a 0%,#075985 48%,#1d4ed8 100%)!important;
            box-shadow:0 0 0 1px rgba(34,211,238,.16),0 18px 52px rgba(14,165,233,.32),0 12px 34px rgba(37,99,235,.25)!important;
            transition:all .18s ease!important;
        }
        .st-key-wz130_landing_start button p{
            color:#eff6ff!important;
            font-size:1.08rem!important;
            font-weight:950!important;
        }
        .st-key-wz130_landing_start button:hover{
            transform:translateY(-2px) scale(1.01)!important;
            border-color:rgba(165,243,252,.86)!important;
            box-shadow:0 0 0 1px rgba(34,211,238,.25),0 24px 70px rgba(14,165,233,.42),0 15px 42px rgba(37,99,235,.32)!important;
            filter:saturate(1.08)!important;
        }

        /* Live interview card */
        .wz130-preview{
            border:1px solid rgba(148,163,184,.22);
            border-radius:28px;
            background:linear-gradient(180deg,rgba(15,23,42,.88),rgba(2,6,23,.82));
            box-shadow:0 22px 60px rgba(2,6,23,.42);
            padding:1rem;
            position:relative;
        }
        .wz130-preview:after{
            content:"LIVE";
            position:absolute;
            top:12px;
            right:12px;
            font-size:.62rem;
            letter-spacing:.12em;
            font-weight:950;
            color:#fecaca;
            background:rgba(127,29,29,.24);
            border:1px solid rgba(248,113,113,.26);
            border-radius:999px;
            padding:.24rem .42rem;
        }
        .wz130-preview-top{display:flex;align-items:center;justify-content:space-between;gap:.8rem;margin-bottom:.85rem;padding-right:2.4rem;}
        .wz130-recruiter{display:flex;align-items:center;gap:.7rem;}
        .wz130-avatar{
            width:44px;height:44px;border-radius:16px;display:grid;place-items:center;
            background:linear-gradient(135deg,#67e8f9,#2563eb);
            box-shadow:0 14px 34px rgba(96,165,250,.25);
            animation:wz130AvatarPulse 2.2s ease-in-out infinite;
        }
        @keyframes wz130AvatarPulse{0%,100%{transform:scale(1);box-shadow:0 14px 34px rgba(96,165,250,.25)}50%{transform:scale(1.045);box-shadow:0 16px 44px rgba(45,212,191,.40)}}
        .wz130-rec-name{color:#f8fafc;font-weight:950;font-size:.98rem;line-height:1.1;}
        .wz130-rec-status{color:#94a3b8;font-size:.78rem;font-weight:700;margin-top:.18rem;}
        .wz130-timer{color:#fecaca;background:rgba(127,29,29,.22);border:1px solid rgba(248,113,113,.24);border-radius:999px;padding:.36rem .58rem;font-weight:950;font-size:.82rem;min-width:58px;text-align:center;}
        .wz130-chat-bubble{border-radius:20px;padding:.82rem .92rem;margin:.58rem 0;font-size:.9rem;line-height:1.43;}
        .wz130-chat-bubble.ai{color:#e0f2fe;background:rgba(30,41,59,.78);border:1px solid rgba(125,211,252,.16);}
        .wz130-chat-bubble.user{color:#f8fafc;background:rgba(37,99,235,.21);border:1px solid rgba(96,165,250,.22);margin-left:2.1rem;}
        .wz130-wave{
            height:34px;
            display:flex;
            gap:.24rem;
            align-items:center;
            padding:.2rem .25rem;
            margin:.55rem 0 .35rem;
        }
        .wz130-wave span{
            width:5px;
            border-radius:999px;
            background:linear-gradient(180deg,#67e8f9,#2563eb);
            opacity:.85;
            animation:wz130Wave 1.15s ease-in-out infinite;
        }
        .wz130-wave span:nth-child(1){height:12px;animation-delay:.05s}.wz130-wave span:nth-child(2){height:22px;animation-delay:.14s}.wz130-wave span:nth-child(3){height:30px;animation-delay:.22s}.wz130-wave span:nth-child(4){height:18px;animation-delay:.30s}.wz130-wave span:nth-child(5){height:26px;animation-delay:.38s}.wz130-wave span:nth-child(6){height:14px;animation-delay:.46s}.wz130-wave span:nth-child(7){height:24px;animation-delay:.54s}
        @keyframes wz130Wave{0%,100%{transform:scaleY(.55);opacity:.45}50%{transform:scaleY(1.05);opacity:1}}
        .wz130-listening{display:flex;align-items:center;justify-content:space-between;gap:.8rem;margin-top:.75rem;border:1px solid rgba(45,212,191,.20);background:rgba(20,184,166,.10);border-radius:18px;padding:.7rem .78rem;color:#ccfbf1;font-size:.81rem;font-weight:850;}
        .wz130-dots{display:flex;gap:.24rem;align-items:center}.wz130-dots span{width:7px;height:7px;border-radius:99px;background:#67e8f9;animation:wz130Dot 1.2s infinite ease-in-out}.wz130-dots span:nth-child(2){animation-delay:.16s}.wz130-dots span:nth-child(3){animation-delay:.32s}@keyframes wz130Dot{0%,80%,100%{opacity:.28;transform:translateY(0)}40%{opacity:1;transform:translateY(-4px)}}
        .wz130-meter{margin:.72rem 0 .55rem;}
        .wz130-meter-row{display:flex;justify-content:space-between;color:#94a3b8;font-size:.72rem;font-weight:850;margin-bottom:.32rem;}
        .wz130-meter-track{height:8px;border-radius:999px;background:rgba(148,163,184,.18);overflow:hidden;}
        .wz130-meter-fill{width:42%;height:100%;border-radius:999px;background:linear-gradient(90deg,#f59e0b,#22d3ee);animation:wz130Meter 3.2s ease-in-out infinite;}
        @keyframes wz130Meter{0%,100%{width:38%}50%{width:58%}}
        .wz130-feedback-mini{margin-top:.68rem;border-radius:18px;padding:.70rem .82rem;background:linear-gradient(135deg,rgba(250,204,21,.13),rgba(15,23,42,.36));border:1px solid rgba(253,224,71,.20);color:#fde68a;font-size:.81rem;font-weight:850;}
        .wz130-tag{display:inline-flex;margin-top:.55rem;border-radius:999px;padding:.32rem .54rem;background:rgba(251,113,133,.10);border:1px solid rgba(251,113,133,.18);color:#fecdd3;font-size:.72rem;font-weight:900;}

        .wz130-flow{max-width:1120px;margin:1.15rem auto 0;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:.9rem;position:relative;}
        .wz130-step{border:1px solid rgba(148,163,184,.20);border-radius:22px;background:rgba(15,23,42,.56);padding:1.05rem;color:#dbeafe;font-weight:900;min-height:118px;position:relative;overflow:hidden;}
        .wz130-step:before{content:"";position:absolute;inset:auto 14px 14px auto;width:54px;height:54px;border-radius:18px;background:rgba(34,211,238,.10);}
        .wz130-step-icon{font-size:1.55rem;margin-bottom:.45rem;}.wz130-step span{display:block;color:#94a3b8;font-weight:650;margin-top:.35rem;font-size:.92rem;line-height:1.38;}.wz130-step-arrow{position:absolute;top:48%;right:-18px;color:#67e8f9;font-weight:950;z-index:3;opacity:.65;}

        @media(max-width:920px){
            .wz130-hero{padding-bottom:1.35rem;margin-left:1rem;margin-right:1rem;}
            .wz130-hero-inner{grid-template-columns:1fr;}
            .wz130-preview{margin-top:.5rem;}
            .st-key-wz130_landing_start{margin:.2rem 1rem 1.2rem!important;padding:0!important;}
            .st-key-wz130_landing_start button{width:100%!important;min-height:66px!important;}
            .wz130-flow{grid-template-columns:1fr;margin-left:1rem;margin-right:1rem;}
            .wz130-step-arrow{display:none;}
        }
        </style>
        """, unsafe_allow_html=True)
    except Exception:
        pass


def show_landing_page():
    """v130: serious animated interview landing page with recruiter-tech CTA."""
    try:
        maybe_scroll_to_top()
    except Exception:
        pass
    try:
        apply_workzo_v75_global_css()
    except Exception:
        pass
    try:
        _wz128_landing_live_preview_css()
    except Exception:
        pass
    try:
        _wz130_landing_serious_cta_css()
    except Exception:
        pass
    try:
        render_workzo_header()
    except Exception:
        pass
    try:
        _wz128_landing_live_preview_css()
        _wz130_landing_serious_cta_css()
    except Exception:
        pass

    hero_html = (
        '<section class="wz130-hero">'
        '<div class="wz130-hero-inner">'
        '<div>'
        '<div class="wz130-kicker">Real Interview AI</div>'
        '<h1 class="wz130-title">Face a real interview before the real one</h1>'
        '<p class="wz130-subtitle">Train with recruiter-style pressure, follow-ups, and CV-based feedback.</p>'
        '<div class="wz130-proof-line">⚡ Built to simulate real interview pressure</div>'
        '<div class="wz130-proof-row">'
        '<span class="wz130-proof-pill">No generic mock questions</span>'
        '<span class="wz130-proof-pill">Personalized from CV + JD</span>'
        '<span class="wz130-proof-pill">Recruiter-style follow-ups</span>'
        '</div>'
        '</div>'
        '<div class="wz130-preview" aria-label="Live interview preview">'
        '<div class="wz130-preview-top">'
        '<div class="wz130-recruiter">'
        '<div class="wz130-avatar">🤖</div>'
        '<div><div class="wz130-rec-name">AI Recruiter</div><div class="wz130-rec-status">Listening for proof and impact</div></div>'
        '</div>'
        '<div class="wz130-timer">00:45</div>'
        '</div>'
        '<div class="wz130-chat-bubble ai">Tell me about yourself — but keep it relevant to this role.</div>'
        '<div class="wz130-chat-bubble user">I worked in technical support and handled customer issues...</div>'
        '<div class="wz130-wave"><span></span><span></span><span></span><span></span><span></span><span></span><span></span></div>'
        '<div class="wz130-listening"><span>Recruiter is typing a follow-up</span><div class="wz130-dots"><span></span><span></span><span></span></div></div>'
        '<div class="wz130-meter"><div class="wz130-meter-row"><span>Answer confidence</span><span>42%</span></div><div class="wz130-meter-track"><div class="wz130-meter-fill"></div></div></div>'
        '<div class="wz130-feedback-mini">⚠️ You’re losing me — give me one measurable result.</div>'
        '<div class="wz130-tag">Live tag: Answer too generic</div>'
        '</div>'
        '</div>'
        '</section>'
    )
    st.markdown(hero_html, unsafe_allow_html=True)

    if st.button("🎤 Let’s start now", type="primary", use_container_width=False, key="wz130_landing_start"):
        st.session_state["onboarding_step_final"] = 1
        try:
            _wz_final_go("onboarding")
        except Exception:
            st.session_state["page"] = "onboarding"
            st.session_state["nav_page"] = "onboarding"
            st.rerun()

    flow_html = (
        '<div class="wz130-flow">'
        '<div class="wz130-step"><div class="wz130-step-icon">📄</div>1. Upload your CV<span>WorkZo reads your real profile and interview context.</span><div class="wz130-step-arrow">→</div></div>'
        '<div class="wz130-step"><div class="wz130-step-icon">🎯</div>2. Paste the job description<span>The interview becomes specific to the role you want.</span><div class="wz130-step-arrow">→</div></div>'
        '<div class="wz130-step"><div class="wz130-step-icon">🎤</div>3. Start your real interview<span>Answer under pressure and get recruiter-style feedback.</span></div>'
        '</div>'
    )
    st.markdown(flow_html, unsafe_allow_html=True)


# =========================================================
# WorkZo v131 - Premium onboarding override
# Added: shorter hero, premium upload zone, stronger demo card,
# trust microcopy, guided progress, and post-upload AI-understood moment.
# This is additive and does not remove existing landing/dashboard logic.
# =========================================================

def _wz131_go(page_key: str) -> None:
    try:
        st.session_state["page"] = page_key
        st.session_state["nav_page"] = page_key
        try:
            st.query_params["page"] = page_key
        except Exception:
            pass
        try:
            request_scroll_to_top()
        except Exception:
            pass
        st.rerun()
    except Exception:
        try:
            st.rerun()
        except Exception:
            pass


def _wz131_css() -> None:
    st.markdown("""
    <style id="workzo-v131-premium-onboarding-css">
    [data-testid="stMainBlockContainer"], .block-container{
        max-width:1120px!important;
        padding-top:.75rem!important;
    }

    /* slightly smaller top/header footprint on onboarding */
    .workzo-header,.workzo-topbar,.workzo-brand-shell,.workzo-brand-card,
    .wzfinal-top,.wzflow-brand{
        margin-top:.25rem!important;
        margin-bottom:.85rem!important;
        padding-top:.75rem!important;
        padding-bottom:.75rem!important;
    }

    .wz131-shell{max-width:1120px;margin:0 auto 2rem;}
    .wz131-topline{display:flex;align-items:center;justify-content:space-between;gap:1rem;margin:.35rem 0 .8rem;}
    .wz131-step-text{color:#cbd5e1;font-weight:900;font-size:.9rem;}
    .wz131-trust-pill{display:inline-flex;align-items:center;gap:.45rem;border:1px solid rgba(45,212,191,.22);background:rgba(20,184,166,.10);color:#ccfbf1;border-radius:999px;padding:.42rem .68rem;font-size:.82rem;font-weight:850;}

    .wz131-progress{display:grid;grid-template-columns:repeat(3,1fr);gap:.65rem;margin:.55rem 0 1rem;position:relative;}
    .wz131-progress:before{content:"";position:absolute;left:8%;right:8%;top:24px;height:2px;background:rgba(148,163,184,.18);z-index:0;}
    .wz131-progress-step{position:relative;z-index:1;border:1px solid rgba(148,163,184,.18);background:rgba(15,23,42,.70);border-radius:18px;padding:.72rem .78rem;color:#94a3b8;font-weight:850;font-size:.86rem;display:flex;align-items:center;gap:.55rem;}
    .wz131-progress-step.active{border-color:rgba(34,211,238,.45);background:linear-gradient(135deg,rgba(14,165,233,.18),rgba(15,23,42,.82));color:#f8fafc;box-shadow:0 14px 36px rgba(14,165,233,.10);}
    .wz131-progress-step.done{border-color:rgba(45,212,191,.36);background:rgba(20,184,166,.10);color:#ccfbf1;}
    .wz131-progress-num{width:30px;height:30px;border-radius:999px;display:grid;place-items:center;background:rgba(34,211,238,.14);border:1px solid rgba(34,211,238,.30);color:#67e8f9;font-weight:950;flex:0 0 auto;}

    .wz131-hero{border:1px solid rgba(34,211,238,.26);border-radius:26px;padding:1.35rem 1.45rem;background:radial-gradient(circle at 8% 0%,rgba(34,211,238,.18),transparent 32%),linear-gradient(135deg,rgba(8,47,73,.76),rgba(15,23,42,.94));box-shadow:0 18px 52px rgba(2,6,23,.30);margin:.75rem 0 1rem;min-height:unset!important;}
    .wz131-kicker{color:#67e8f9;text-transform:uppercase;letter-spacing:.16em;font-size:.74rem;font-weight:950;margin-bottom:.45rem;}
    .wz131-hero h1{color:#fff;font-size:clamp(1.85rem,4vw,3.15rem);line-height:1.06;letter-spacing:-.055em;margin:0 0 .55rem;font-weight:950;}
    .wz131-hero p{color:#cbd5e1;font-size:1.02rem;line-height:1.45;max-width:760px;margin:0;}

    .wz131-grid{display:grid;grid-template-columns:1.35fr .85fr;gap:1rem;align-items:stretch;margin-top:.75rem;}
    .wz131-panel{border:1px solid rgba(148,163,184,.18);background:linear-gradient(180deg,rgba(15,23,42,.70),rgba(2,6,23,.55));border-radius:26px;padding:1.15rem;box-shadow:0 18px 48px rgba(2,6,23,.22);position:relative;overflow:hidden;}
    .wz131-panel:before{content:"";position:absolute;inset:-35% auto auto -20%;width:240px;height:240px;background:radial-gradient(circle,rgba(34,211,238,.15),transparent 64%);pointer-events:none;}
    .wz131-panel h2{color:#fff;font-size:clamp(1.35rem,3vw,2.05rem);letter-spacing:-.04em;line-height:1.08;margin:.1rem 0 .45rem;font-weight:950;}
    .wz131-panel p{color:#cbd5e1;margin:0 0 .8rem;line-height:1.45;}

    .wz131-upload-wrap{border:1.5px dashed rgba(103,232,249,.42);border-radius:24px;background:rgba(8,47,73,.22);padding:1rem;margin:.75rem 0 .85rem;box-shadow:inset 0 0 0 1px rgba(34,211,238,.06),0 16px 48px rgba(14,165,233,.08);animation:wz131UploadPulse 2.6s ease-in-out infinite;}
    @keyframes wz131UploadPulse{0%,100%{box-shadow:inset 0 0 0 1px rgba(34,211,238,.06),0 16px 48px rgba(14,165,233,.08)}50%{box-shadow:inset 0 0 0 1px rgba(34,211,238,.14),0 18px 62px rgba(14,165,233,.16)}}
    .wz131-upload-head{display:flex;align-items:center;gap:.75rem;margin-bottom:.65rem;}
    .wz131-upload-icon{width:46px;height:46px;border-radius:16px;display:grid;place-items:center;background:linear-gradient(135deg,#22d3ee,#2563eb);box-shadow:0 14px 36px rgba(37,99,235,.22);font-size:1.2rem;animation:wz131Float 2.6s ease-in-out infinite;}
    @keyframes wz131Float{0%,100%{transform:translateY(0)}50%{transform:translateY(-4px)}}
    .wz131-upload-title{color:#f8fafc;font-weight:950;font-size:1.02rem;}
    .wz131-upload-sub{color:#94a3b8;font-size:.86rem;font-weight:700;margin-top:.12rem;}
    div[data-testid="stFileUploader"]{border:1px solid rgba(125,211,252,.22)!important;background:rgba(15,23,42,.58)!important;border-radius:18px!important;padding:.7rem!important;transition:all .18s ease!important;}
    div[data-testid="stFileUploader"]:hover{border-color:rgba(103,232,249,.52)!important;box-shadow:0 0 0 1px rgba(34,211,238,.12),0 18px 42px rgba(14,165,233,.12)!important;}
    div[data-testid="stFileUploader"] small{color:#94a3b8!important;}

    .wz131-note{border:1px solid rgba(45,212,191,.18);background:rgba(20,184,166,.08);border-radius:18px;padding:.8rem .9rem;color:#ccfbf1;font-size:.88rem;font-weight:750;line-height:1.42;margin:.65rem 0 .9rem;}
    .wz131-ai-read{border:1px solid rgba(34,211,238,.28);background:linear-gradient(135deg,rgba(14,165,233,.13),rgba(15,23,42,.58));border-radius:22px;padding:1rem;margin:.8rem 0;}
    .wz131-ai-read-title{color:#fff;font-weight:950;margin-bottom:.45rem;}
    .wz131-scan-row{display:flex;flex-wrap:wrap;gap:.5rem;margin-top:.5rem;}
    .wz131-scan-pill{border:1px solid rgba(148,163,184,.20);background:rgba(15,23,42,.70);border-radius:999px;padding:.36rem .58rem;color:#bfdbfe;font-size:.82rem;font-weight:850;}
    .wz131-dots{display:inline-flex;gap:.22rem;margin-left:.35rem;vertical-align:middle}.wz131-dots span{width:6px;height:6px;border-radius:99px;background:#67e8f9;animation:wz131Dots 1.2s infinite ease-in-out}.wz131-dots span:nth-child(2){animation-delay:.15s}.wz131-dots span:nth-child(3){animation-delay:.3s}@keyframes wz131Dots{0%,80%,100%{opacity:.28;transform:translateY(0)}40%{opacity:1;transform:translateY(-3px)}}

    .wz131-demo-card{border:1px solid rgba(129,140,248,.30);background:radial-gradient(circle at 10% 0%,rgba(129,140,248,.22),transparent 38%),linear-gradient(180deg,rgba(30,41,59,.76),rgba(15,23,42,.72));border-radius:26px;padding:1.15rem;min-height:100%;box-shadow:0 18px 48px rgba(2,6,23,.20);}
    .wz131-demo-title{color:#fff;font-weight:950;font-size:1.3rem;letter-spacing:-.035em;margin-bottom:.3rem;}
    .wz131-demo-copy{color:#cbd5e1;font-size:.95rem;line-height:1.42;margin-bottom:.75rem;}
    .wz131-mini-chat{border:1px solid rgba(148,163,184,.18);background:rgba(2,6,23,.32);border-radius:20px;padding:.8rem;margin:.75rem 0;}
    .wz131-mini-bubble{border-radius:16px;padding:.62rem .7rem;margin:.45rem 0;font-size:.84rem;line-height:1.35;}
    .wz131-mini-bubble.ai{background:rgba(30,41,59,.78);color:#e0f2fe;border:1px solid rgba(125,211,252,.14);}
    .wz131-mini-bubble.warn{background:rgba(250,204,21,.10);color:#fde68a;border:1px solid rgba(253,224,71,.16);}
    .wz131-actions{display:grid;grid-template-columns:1fr 1fr;gap:.75rem;margin-top:.75rem;}
    .wz131-actions.single{grid-template-columns:1fr;}
    .st-key-wz131_continue_cv button,.st-key-wz131_demo_cv button,.st-key-wz131_use_pasted_cv button,.st-key-wz131_continue_job button,.st-key-wz131_demo_job button,.st-key-wz131_start_interview button,.st-key-wz131_open_dashboard button{
        min-height:56px!important;border-radius:17px!important;font-weight:950!important;font-size:1rem!important;transition:all .18s ease!important;
    }
    .st-key-wz131_continue_cv button,.st-key-wz131_continue_job button,.st-key-wz131_start_interview button{
        color:#eff6ff!important;border:1px solid rgba(125,211,252,.56)!important;background:radial-gradient(circle at 18% 12%,rgba(103,232,249,.36),transparent 35%),linear-gradient(135deg,#0f172a,#075985,#1d4ed8)!important;box-shadow:0 18px 50px rgba(14,165,233,.24)!important;
    }
    .st-key-wz131_continue_cv button:hover,.st-key-wz131_continue_job button:hover,.st-key-wz131_start_interview button:hover{transform:translateY(-2px)!important;box-shadow:0 24px 64px rgba(14,165,233,.34)!important;}

    @media(max-width:860px){
        .wz131-grid{grid-template-columns:1fr;}
        .wz131-progress{grid-template-columns:1fr;}.wz131-progress:before{display:none;}
        .wz131-topline{align-items:flex-start;flex-direction:column;}
        .wz131-actions{grid-template-columns:1fr;}
        .wz131-hero{padding:1.05rem;border-radius:22px;}
    }
    </style>
    """, unsafe_allow_html=True)


def _wz131_progress(step: int) -> None:
    labels = [(1, "Upload CV"), (2, "Add Job Description"), (3, "Start Interview")]
    html_parts = ['<div class="wz131-progress">']
    for n, label in labels:
        cls = "done" if n < step else ("active" if n == step else "")
        icon = "✓" if n < step else str(n)
        html_parts.append(f'<div class="wz131-progress-step {cls}"><span class="wz131-progress-num">{icon}</span><span>{html.escape(label)}</span></div>')
    html_parts.append('</div>')
    st.markdown("".join(html_parts), unsafe_allow_html=True)


def _wz131_detect_cv_insights(cv_text: str) -> dict:
    text = str(cv_text or "")
    lower = text.lower()
    role = st.session_state.get("target_role") or st.session_state.get("current_role_detected") or "Target role not set yet"
    for candidate in ["data analyst", "technical support", "customer success", "it support", "support engineer", "business analyst", "product analyst"]:
        if candidate in lower:
            role = candidate.title()
            break
    skill_pool = ["Python", "SQL", "Excel", "Tableau", "Power BI", "API", "Cloud", "Customer Support", "Troubleshooting", "Dashboard", "Communication", "Stakeholder"]
    skills = []
    for skill in skill_pool:
        if skill.lower() in lower and skill not in skills:
            skills.append(skill)
    years = "Experience detected"
    m = re.search(r"\b(\d{1,2})\+?\s*(?:years|yrs)\b", lower)
    if m:
        years = f"{m.group(1)}+ years mentioned"
    return {"role": role, "skills": skills[:5] or ["Profile skills detected"], "experience": years, "words": len(text.split())}


def _wz131_store_cv_text(cv_text: str, mode: str = "Upload CV") -> bool:
    cv_text = str(cv_text or "").strip()
    if len(cv_text) < 60:
        return False
    for key in ["cv_text", "clean_structured_cv_text", "raw_cv_extraction", "uploaded_cv_text", "workzo_live_cv_text", "cv_editor_widget"]:
        st.session_state[key] = cv_text
    st.session_state["cv_mode"] = mode
    st.session_state["wz131_cv_insights"] = _wz131_detect_cv_insights(cv_text)
    try:
        if callable(globals().get("extract_structured_resume_json")):
            structured = extract_structured_resume_json(cv_text, st.session_state.get("country", "Germany"), st.session_state.get("user_status", ""))
            if isinstance(structured, dict) and structured:
                st.session_state["structured_cv_json"] = structured
    except Exception:
        pass
    return True


def _wz131_store_job(title: str, desc: str, company: str = "") -> bool:
    desc = str(desc or "").strip()
    if len(desc) < 30:
        return False
    title = str(title or st.session_state.get("target_role") or "Target role").strip() or "Target role"
    company = str(company or "Target company").strip() or "Target company"
    st.session_state["target_role"] = title
    st.session_state["selected_company"] = company
    job = {"title": title, "company": company, "description": desc, "location": st.session_state.get("country", "")}
    st.session_state["selected_job"] = job
    for key in ["selected_job_description", "current_job_description", "last_understand_job_description", "last_prepare_job_description", "improve_cv_for_job_desc", "job_description", "interview_jd_text_v117", "real_interview_jd_saved"]:
        st.session_state[key] = desc
    return True


def _wz131_render_cv_understood() -> None:
    insights = st.session_state.get("wz131_cv_insights") or _wz131_detect_cv_insights(st.session_state.get("cv_text", ""))
    skills = insights.get("skills", []) if isinstance(insights, dict) else []
    st.markdown(
        '<div class="wz131-ai-read">'
        '<div class="wz131-ai-read-title">✅ CV parsed — AI is preparing your interview<span class="wz131-dots"><span></span><span></span><span></span></span></div>'
        f'<div class="wz131-scan-row"><span class="wz131-scan-pill">Role: {html.escape(str(insights.get("role", "Detected")))}</span>'
        f'<span class="wz131-scan-pill">{html.escape(str(insights.get("experience", "Experience detected")))}</span>'
        f'<span class="wz131-scan-pill">{int(insights.get("words", 0) or 0)} words read</span>'
        + ''.join([f'<span class="wz131-scan-pill">{html.escape(str(s))}</span>' for s in skills[:4]])
        + '</div></div>',
        unsafe_allow_html=True,
    )


def show_onboarding():
    """v131 premium onboarding: faster, emotional CV-first journey."""
    try:
        maybe_scroll_to_top()
    except Exception:
        pass
    try:
        apply_workzo_v75_global_css()
    except Exception:
        pass
    _wz131_css()
    try:
        render_workzo_header()
    except Exception:
        try:
            _wzflow_render_minimal_brand()
        except Exception:
            pass

    step = int(st.session_state.get("onboarding_step_final", st.session_state.get("wz_onboarding_step", 1)) or 1)
    if step < 1 or step > 3:
        step = 1
    st.session_state["onboarding_step_final"] = step

    st.markdown('<div class="wz131-shell">', unsafe_allow_html=True)
    st.markdown(
        f'<div class="wz131-topline"><div class="wz131-step-text">Step {step} of 3</div><div class="wz131-trust-pill">🔒 Your CV is used only to personalize your interview. Takes less than 30 seconds.</div></div>',
        unsafe_allow_html=True,
    )
    _wz131_progress(step)

    if step == 1:
        st.markdown(
            '<section class="wz131-hero"><div class="wz131-kicker">Start with your CV</div>'
            '<h1>Your interview starts with your CV</h1>'
            '<p>Upload your CV so WorkZo can understand your experience, detect your skills, and prepare realistic recruiter-style interview questions.</p></section>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="wz131-grid">', unsafe_allow_html=True)
        left, right = st.columns([1.35, .85])
        with left:
            st.markdown(
                '<div class="wz131-panel"><h2>Let AI understand your experience</h2><p>This is the core step. WorkZo reads your profile so the interview does not feel generic.</p>'
                '<div class="wz131-upload-wrap"><div class="wz131-upload-head"><div class="wz131-upload-icon">📄</div><div><div class="wz131-upload-title">Drop your CV here</div><div class="wz131-upload-sub">PDF or TXT works best. You can also paste text below.</div></div></div>',
                unsafe_allow_html=True,
            )
            uploaded = st.file_uploader("Upload PDF or TXT", type=["pdf", "txt"], key="wz131_cv_upload")
            st.markdown('</div>', unsafe_allow_html=True)
            if uploaded is not None:
                extracted = ""
                try:
                    file_name = str(getattr(uploaded, "name", "") or "").lower()
                    file_type = str(getattr(uploaded, "type", "") or "").lower()
                    if file_type == "text/plain" or file_name.endswith(".txt"):
                        extracted = uploaded.read().decode("utf-8", errors="ignore")
                    else:
                        extracted = extract_pdf_text(uploaded) if callable(globals().get("extract_pdf_text")) else ""
                    if callable(globals().get("organize_cv_for_display")):
                        extracted = organize_cv_for_display(extracted)
                except Exception as exc:
                    st.warning(f"Could not read the uploaded CV: {exc}")
                if _wz131_store_cv_text(extracted, "Upload CV"):
                    _wz131_render_cv_understood()
                else:
                    st.warning("The file uploaded, but the text looked too short. Try TXT or paste your CV below.")
            with st.expander("Paste CV text instead", expanded=not bool(st.session_state.get("cv_text"))):
                pasted = st.text_area("Paste your CV text", height=170, key="wz131_paste_cv_text", placeholder="Paste your resume text here...")
                if st.button("Use pasted CV", key="wz131_use_pasted_cv", use_container_width=True):
                    if _wz131_store_cv_text(pasted, "Paste CV"):
                        st.success("CV is ready.")
                        _wz131_render_cv_understood()
                    else:
                        st.warning("Please paste more CV details first.")
            st.markdown('<div class="wz131-note">No account required for testing. Avoid uploading sensitive details you do not want analyzed.</div>', unsafe_allow_html=True)
            if st.session_state.get("cv_text"):
                if st.button("Continue to job description", type="primary", use_container_width=True, key="wz131_continue_cv"):
                    st.session_state["onboarding_step_final"] = 2
                    _wz131_go("onboarding")
            st.markdown('</div>', unsafe_allow_html=True)
        with right:
            st.markdown(
                '<div class="wz131-demo-card"><div class="wz131-demo-title">Try demo instantly</div>'
                '<div class="wz131-demo-copy">Experience the interview flow without uploading your own CV.</div>'
                '<div class="wz131-mini-chat"><div class="wz131-mini-bubble ai">AI Recruiter: Tell me about yourself, but keep it relevant.</div>'
                '<div class="wz131-mini-bubble warn">⚠️ Follow-up: Give me one measurable result.</div></div>'
                '<div class="wz131-note">Best for first-time testers who want to feel the product before sharing a CV.</div></div>',
                unsafe_allow_html=True,
            )
            if st.button("Experience demo interview", use_container_width=True, key="wz131_demo_cv"):
                demo_cv = SAMPLE_CV_TEXT if "SAMPLE_CV_TEXT" in globals() else "Demo CV: Technical Support Engineer with customer-facing experience, SQL, Python, dashboards, troubleshooting, and communication skills."
                _wz131_store_cv_text(demo_cv, "Sample Demo")
                demo_jd = SAMPLE_JOB_DESCRIPTION if "SAMPLE_JOB_DESCRIPTION" in globals() else "Demo job description: Junior Data Analyst role requiring SQL, Python, dashboards, communication, problem solving, and stakeholder support."
                _wz131_store_job("Junior Data Analyst", demo_jd, "Demo Company")
                st.session_state["onboarding_step_final"] = 3
                _wz131_go("onboarding")
        st.markdown('</div></div>', unsafe_allow_html=True)
        return

    if step == 2:
        st.markdown(
            '<section class="wz131-hero"><div class="wz131-kicker">Add your target role</div>'
            '<h1>Make the interview specific to the job</h1>'
            '<p>Paste one real job description so WorkZo can challenge you on the exact skills, gaps, and recruiter expectations.</p></section>',
            unsafe_allow_html=True,
        )
        with st.container(border=True):
            title = st.text_input("Job title", value=st.session_state.get("target_role", ""), placeholder="Example: Data Analyst", key="wz131_job_title")
            company = st.text_input("Company / employer (optional)", value=st.session_state.get("selected_company", ""), placeholder="Example: Siemens", key="wz131_company")
            jd = st.text_area("Job description", height=230, value=st.session_state.get("selected_job_description") or st.session_state.get("current_job_description") or "", placeholder="Paste the job description here...", key="wz131_jd")
        c1, c2, c3 = st.columns([1,1,1])
        with c1:
            if st.button("Back", use_container_width=True, key="wz131_back_to_cv"):
                st.session_state["onboarding_step_final"] = 1
                _wz131_go("onboarding")
        with c2:
            if st.button("Use demo job", use_container_width=True, key="wz131_demo_job"):
                demo_jd = SAMPLE_JOB_DESCRIPTION if "SAMPLE_JOB_DESCRIPTION" in globals() else "Demo job description: Junior Data Analyst role requiring SQL, Python, dashboards, communication and stakeholder collaboration."
                _wz131_store_job("Junior Data Analyst", demo_jd, "Demo Company")
                st.session_state["onboarding_step_final"] = 3
                _wz131_go("onboarding")
        with c3:
            if st.button("Continue", type="primary", use_container_width=True, key="wz131_continue_job"):
                if _wz131_store_job(title, jd, company):
                    st.session_state["onboarding_step_final"] = 3
                    _wz131_go("onboarding")
                else:
                    st.warning("Please paste the job description, or use the demo job.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    st.markdown(
        '<section class="wz131-hero"><div class="wz131-kicker">Interview room ready</div>'
        '<h1>AI has your CV and target job</h1>'
        '<p>Start the interview now. WorkZo will ask recruiter-style questions, challenge weak answers, and give a hiring-style decision.</p></section>',
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns(2)
    with c1:
        _wz131_render_cv_understood()
    with c2:
        job = st.session_state.get("selected_job") or {}
        st.markdown(
            '<div class="wz131-ai-read"><div class="wz131-ai-read-title">🎯 Job context ready</div>'
            f'<div class="wz131-scan-row"><span class="wz131-scan-pill">Role: {html.escape(str(job.get("title") or st.session_state.get("target_role") or "Target role"))}</span>'
            f'<span class="wz131-scan-pill">Company: {html.escape(str(job.get("company") or "Target company"))}</span>'
            '<span class="wz131-scan-pill">Recruiter follow-ups enabled</span></div></div>',
            unsafe_allow_html=True,
        )
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🎤 Start Real Interview", type="primary", use_container_width=True, key="wz131_start_interview"):
            st.session_state["onboarding_complete"] = True
            _wz131_go("real_interview")
    with c2:
        st.caption("Dashboard is available later from the header.")
    st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# WorkZo v132 - ACTIVE onboarding override
# Purpose: make the actual routed onboarding page visibly shorter,
# premium, CV-first, trust-building, and demo-friendly.
# This block is intentionally appended at the END so it becomes the
# active show_onboarding() used by the router.
# =========================================================

def _wz132_onboarding_css() -> None:
    st.markdown("""
    <style id="workzo-v132-active-onboarding-css">
    [data-testid="stMainBlockContainer"], .block-container{
        max-width:1080px!important;
        padding-top:.45rem!important;
    }

    /* reduce top/navbar footprint on onboarding */
    .workzo-header,.workzo-topbar,.workzo-brand-shell,.workzo-brand-card,
    .wzfinal-top,.wzflow-brand,.wz128-topbar,.wz130-topbar{
        margin-top:.12rem!important;
        margin-bottom:.55rem!important;
        padding-top:.55rem!important;
        padding-bottom:.55rem!important;
        min-height:unset!important;
    }

    .wz132-shell{max-width:1080px;margin:0 auto 1.8rem;}
    .wz132-topline{display:flex;align-items:center;justify-content:space-between;gap:.8rem;margin:.15rem 0 .62rem;}
    .wz132-step-text{color:#dbeafe;font-weight:950;font-size:.88rem;}
    .wz132-trust{display:inline-flex;align-items:center;gap:.45rem;border:1px solid rgba(45,212,191,.22);background:rgba(20,184,166,.10);color:#ccfbf1;border-radius:999px;padding:.38rem .62rem;font-size:.8rem;font-weight:850;}

    .wz132-progress{display:grid;grid-template-columns:repeat(3,1fr);gap:.58rem;margin:.45rem 0 .78rem;position:relative;}
    .wz132-progress:before{content:"";position:absolute;left:8%;right:8%;top:20px;height:2px;background:linear-gradient(90deg,rgba(34,211,238,.55),rgba(148,163,184,.14));z-index:0;}
    .wz132-step{position:relative;z-index:1;border:1px solid rgba(148,163,184,.16);background:rgba(15,23,42,.72);border-radius:16px;padding:.58rem .68rem;color:#94a3b8;font-weight:850;font-size:.83rem;display:flex;align-items:center;gap:.48rem;}
    .wz132-step.active{border-color:rgba(34,211,238,.48);background:linear-gradient(135deg,rgba(14,165,233,.20),rgba(15,23,42,.86));color:#f8fafc;box-shadow:0 14px 34px rgba(14,165,233,.12);}
    .wz132-step.done{border-color:rgba(45,212,191,.36);background:rgba(20,184,166,.11);color:#ccfbf1;}
    .wz132-num{width:26px;height:26px;border-radius:999px;display:grid;place-items:center;background:rgba(34,211,238,.14);border:1px solid rgba(34,211,238,.32);color:#67e8f9;font-weight:950;flex:0 0 auto;}

    /* 35% shorter hero: action appears faster */
    .wz132-hero{border:1px solid rgba(34,211,238,.24);border-radius:22px;padding:1rem 1.12rem;background:radial-gradient(circle at 8% 0%,rgba(34,211,238,.16),transparent 30%),linear-gradient(135deg,rgba(8,47,73,.70),rgba(15,23,42,.94));box-shadow:0 14px 42px rgba(2,6,23,.28);margin:.55rem 0 .78rem;min-height:0!important;}
    .wz132-kicker{color:#67e8f9;text-transform:uppercase;letter-spacing:.15em;font-size:.70rem;font-weight:950;margin-bottom:.32rem;}
    .wz132-hero h1{color:#fff;font-size:clamp(1.55rem,3.3vw,2.45rem);line-height:1.04;letter-spacing:-.05em;margin:0 0 .38rem;font-weight:950;}
    .wz132-hero p{color:#cbd5e1;font-size:.96rem;line-height:1.38;max-width:760px;margin:0;}

    .wz132-grid{display:grid;grid-template-columns:1.32fr .86fr;gap:.9rem;align-items:stretch;margin-top:.55rem;}
    .wz132-panel{border:1px solid rgba(148,163,184,.18);background:linear-gradient(180deg,rgba(15,23,42,.73),rgba(2,6,23,.58));border-radius:24px;padding:1rem;box-shadow:0 16px 42px rgba(2,6,23,.22);position:relative;overflow:hidden;}
    .wz132-panel:before{content:"";position:absolute;left:-80px;top:-90px;width:210px;height:210px;background:radial-gradient(circle,rgba(34,211,238,.18),transparent 64%);pointer-events:none;}
    .wz132-panel h2{color:#fff;font-size:clamp(1.25rem,2.6vw,1.82rem);letter-spacing:-.04em;line-height:1.08;margin:.05rem 0 .32rem;font-weight:950;position:relative;}
    .wz132-panel p{color:#cbd5e1;margin:0 0 .68rem;line-height:1.38;position:relative;}

    .wz132-upload-wrap{border:1.6px dashed rgba(103,232,249,.50);border-radius:22px;background:rgba(8,47,73,.24);padding:.92rem;margin:.58rem 0 .72rem;box-shadow:inset 0 0 0 1px rgba(34,211,238,.08),0 16px 46px rgba(14,165,233,.09);animation:wz132UploadPulse 2.4s ease-in-out infinite;position:relative;}
    @keyframes wz132UploadPulse{0%,100%{box-shadow:inset 0 0 0 1px rgba(34,211,238,.06),0 12px 36px rgba(14,165,233,.08)}50%{box-shadow:inset 0 0 0 1px rgba(34,211,238,.18),0 18px 58px rgba(14,165,233,.18)}}
    .wz132-upload-head{display:flex;align-items:center;gap:.72rem;margin-bottom:.58rem;}
    .wz132-upload-icon{width:44px;height:44px;border-radius:16px;display:grid;place-items:center;background:linear-gradient(135deg,#22d3ee,#2563eb);box-shadow:0 14px 34px rgba(37,99,235,.24);font-size:1.18rem;animation:wz132Float 2.5s ease-in-out infinite;}
    @keyframes wz132Float{0%,100%{transform:translateY(0)}50%{transform:translateY(-4px)}}
    .wz132-upload-title{color:#f8fafc;font-weight:950;font-size:1rem;}
    .wz132-upload-sub{color:#94a3b8;font-size:.84rem;font-weight:750;margin-top:.1rem;}
    div[data-testid="stFileUploader"]{border:1px solid rgba(125,211,252,.22)!important;background:rgba(15,23,42,.56)!important;border-radius:17px!important;padding:.65rem!important;transition:all .18s ease!important;}
    div[data-testid="stFileUploader"]:hover{border-color:rgba(103,232,249,.55)!important;box-shadow:0 0 0 1px rgba(34,211,238,.12),0 16px 38px rgba(14,165,233,.14)!important;}

    .wz132-note{border:1px solid rgba(45,212,191,.18);background:rgba(20,184,166,.08);border-radius:16px;padding:.68rem .78rem;color:#ccfbf1;font-size:.84rem;font-weight:750;line-height:1.38;margin:.52rem 0 .72rem;}
    .wz132-ai-read{border:1px solid rgba(34,211,238,.30);background:linear-gradient(135deg,rgba(14,165,233,.14),rgba(15,23,42,.62));border-radius:20px;padding:.9rem;margin:.72rem 0;}
    .wz132-ai-title{color:#fff;font-weight:950;margin-bottom:.42rem;}
    .wz132-scan-row{display:flex;flex-wrap:wrap;gap:.46rem;margin-top:.45rem;}
    .wz132-pill{border:1px solid rgba(148,163,184,.20);background:rgba(15,23,42,.72);border-radius:999px;padding:.32rem .54rem;color:#bfdbfe;font-size:.8rem;font-weight:850;}
    .wz132-dots{display:inline-flex;gap:.22rem;margin-left:.35rem;vertical-align:middle}.wz132-dots span{width:6px;height:6px;border-radius:99px;background:#67e8f9;animation:wz132Dots 1.15s infinite ease-in-out}.wz132-dots span:nth-child(2){animation-delay:.15s}.wz132-dots span:nth-child(3){animation-delay:.3s}@keyframes wz132Dots{0%,80%,100%{opacity:.28;transform:translateY(0)}40%{opacity:1;transform:translateY(-3px)}}

    .wz132-demo{border:1px solid rgba(129,140,248,.35);background:radial-gradient(circle at 10% 0%,rgba(129,140,248,.25),transparent 38%),linear-gradient(180deg,rgba(30,41,59,.82),rgba(15,23,42,.76));border-radius:24px;padding:1rem;min-height:100%;box-shadow:0 18px 46px rgba(2,6,23,.22);}
    .wz132-demo-title{color:#fff;font-weight:950;font-size:1.22rem;letter-spacing:-.035em;margin-bottom:.24rem;}
    .wz132-demo-copy{color:#cbd5e1;font-size:.92rem;line-height:1.38;margin-bottom:.65rem;}
    .wz132-mini-chat{border:1px solid rgba(148,163,184,.18);background:rgba(2,6,23,.34);border-radius:18px;padding:.72rem;margin:.62rem 0;}
    .wz132-bubble{border-radius:15px;padding:.56rem .64rem;margin:.4rem 0;font-size:.82rem;line-height:1.34;}
    .wz132-bubble.ai{background:rgba(30,41,59,.78);color:#e0f2fe;border:1px solid rgba(125,211,252,.14);}
    .wz132-bubble.warn{background:rgba(250,204,21,.10);color:#fde68a;border:1px solid rgba(253,224,71,.16);}
    .wz132-demo-badge{display:inline-flex;border:1px solid rgba(103,232,249,.24);background:rgba(14,165,233,.12);color:#bae6fd;border-radius:999px;padding:.34rem .58rem;font-size:.78rem;font-weight:900;margin:.38rem 0 .55rem;}

    .st-key-wz132_continue_cv button,.st-key-wz132_demo_cv button,.st-key-wz132_use_pasted_cv button,.st-key-wz132_continue_job button,.st-key-wz132_demo_job button,.st-key-wz132_start_interview button,.st-key-wz132_open_dashboard button{
        min-height:54px!important;border-radius:16px!important;font-weight:950!important;font-size:.98rem!important;transition:all .18s ease!important;
    }
    .st-key-wz132_continue_cv button,.st-key-wz132_continue_job button,.st-key-wz132_start_interview button{
        color:#eff6ff!important;border:1px solid rgba(125,211,252,.56)!important;background:radial-gradient(circle at 18% 12%,rgba(103,232,249,.36),transparent 35%),linear-gradient(135deg,#0f172a,#075985,#1d4ed8)!important;box-shadow:0 18px 50px rgba(14,165,233,.24)!important;
    }
    .st-key-wz132_continue_cv button:hover,.st-key-wz132_continue_job button:hover,.st-key-wz132_start_interview button:hover{transform:translateY(-2px)!important;box-shadow:0 24px 64px rgba(14,165,233,.34)!important;}
    .st-key-wz132_demo_cv button{border-color:rgba(129,140,248,.45)!important;background:rgba(99,102,241,.14)!important;color:#e0e7ff!important;}

    @media(max-width:860px){
        .wz132-grid{grid-template-columns:1fr;}
        .wz132-progress{grid-template-columns:1fr;}.wz132-progress:before{display:none;}
        .wz132-topline{align-items:flex-start;flex-direction:column;}
        .wz132-hero{padding:.9rem;border-radius:20px;}
    }
    </style>
    """, unsafe_allow_html=True)


def _wz132_progress(step: int) -> None:
    labels = [(1, "Upload CV"), (2, "Add Job Description"), (3, "Start Interview")]
    parts = ['<div class="wz132-progress">']
    for n, label in labels:
        cls = "done" if n < step else ("active" if n == step else "")
        icon = "✓" if n < step else str(n)
        parts.append(f'<div class="wz132-step {cls}"><span class="wz132-num">{icon}</span><span>{html.escape(label)}</span></div>')
    parts.append('</div>')
    st.markdown(''.join(parts), unsafe_allow_html=True)


def _wz132_detect_cv_insights(cv_text: str) -> dict:
    try:
        return _wz131_detect_cv_insights(cv_text)
    except Exception:
        text = str(cv_text or '')
        return {"role":"Profile detected", "skills":["Skills detected"], "experience":"Experience detected", "words":len(text.split())}


def _wz132_store_cv_text(cv_text: str, mode: str = "Upload CV") -> bool:
    try:
        return _wz131_store_cv_text(cv_text, mode)
    except Exception:
        cv_text = str(cv_text or '').strip()
        if len(cv_text) < 60:
            return False
        for key in ["cv_text", "clean_structured_cv_text", "raw_cv_extraction", "uploaded_cv_text", "workzo_live_cv_text", "cv_editor_widget"]:
            st.session_state[key] = cv_text
        st.session_state["cv_mode"] = mode
        st.session_state["wz132_cv_insights"] = _wz132_detect_cv_insights(cv_text)
        return True


def _wz132_store_job(title: str, desc: str, company: str = "") -> bool:
    try:
        return _wz131_store_job(title, desc, company)
    except Exception:
        desc = str(desc or '').strip()
        if len(desc) < 30:
            return False
        title = str(title or st.session_state.get("target_role") or "Target role").strip() or "Target role"
        company = str(company or "Target company").strip() or "Target company"
        st.session_state["target_role"] = title
        st.session_state["selected_company"] = company
        job = {"title": title, "company": company, "description": desc, "location": st.session_state.get("country", "")}
        st.session_state["selected_job"] = job
        for key in ["selected_job_description", "current_job_description", "last_understand_job_description", "last_prepare_job_description", "improve_cv_for_job_desc", "job_description", "interview_jd_text_v117", "real_interview_jd_saved"]:
            st.session_state[key] = desc
        return True


def _wz132_render_cv_understood() -> None:
    insights = st.session_state.get("wz132_cv_insights") or st.session_state.get("wz131_cv_insights") or _wz132_detect_cv_insights(st.session_state.get("cv_text", ""))
    skills = insights.get("skills", []) if isinstance(insights, dict) else []
    st.markdown(
        '<div class="wz132-ai-read">'
        '<div class="wz132-ai-title">✅ CV parsed — Preparing your interview<span class="wz132-dots"><span></span><span></span><span></span></span></div>'
        f'<div class="wz132-scan-row"><span class="wz132-pill">Role: {html.escape(str(insights.get("role", "Detected")))}</span>'
        f'<span class="wz132-pill">{html.escape(str(insights.get("experience", "Experience detected")))}</span>'
        f'<span class="wz132-pill">{int(insights.get("words", 0) or 0)} words read</span>'
        + ''.join([f'<span class="wz132-pill">{html.escape(str(s))}</span>' for s in skills[:4]])
        + '</div></div>',
        unsafe_allow_html=True,
    )


def show_onboarding():
    """v132 ACTIVE onboarding: compact hero + premium CV upload + stronger demo path."""
    try:
        maybe_scroll_to_top()
    except Exception:
        pass
    try:
        apply_workzo_v75_global_css()
    except Exception:
        pass
    _wz132_onboarding_css()
    try:
        render_workzo_header()
    except Exception:
        try:
            _wzflow_render_minimal_brand()
        except Exception:
            pass

    step = int(st.session_state.get("onboarding_step_final", st.session_state.get("wz_onboarding_step", 1)) or 1)
    if step < 1 or step > 3:
        step = 1
    st.session_state["onboarding_step_final"] = step

    st.markdown('<div class="wz132-shell">', unsafe_allow_html=True)
    st.markdown(
        f'<div class="wz132-topline"><div class="wz132-step-text">Step {step} of 3</div><div class="wz132-trust">🔒 Your CV is only used to personalize your interview · No account required · We don’t store sensitive resume data · Takes less than 30 seconds</div></div>',
        unsafe_allow_html=True,
    )
    _wz132_progress(step)

    if step == 1:
        st.markdown(
            '<section class="wz132-hero"><div class="wz132-kicker">Start with your CV</div>'
            '<h1>Your interview starts with your CV</h1>'
            '<p>Upload your CV to personalize recruiter-style questions, pressure follow-ups, and hiring feedback. WorkZo first understands your experience — then builds the interview around it.</p></section>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="wz132-grid">', unsafe_allow_html=True)
        left, right = st.columns([1.32, .86])
        with left:
            st.markdown(
                '<div class="wz132-panel"><h2>Let AI understand your experience</h2><p>This is the core step. Your interview becomes specific to your real background, not a generic mock test.</p>'
                '<div class="wz132-upload-wrap"><div class="wz132-upload-head"><div class="wz132-upload-icon">📄</div><div><div class="wz132-upload-title">Upload your CV to personalize your interview</div><div class="wz132-upload-sub">PDF or TXT works best. Drag, drop, or browse.</div></div></div>',
                unsafe_allow_html=True,
            )
            uploaded = st.file_uploader("Upload PDF or TXT", type=["pdf", "txt"], key="wz132_cv_upload")
            st.markdown('</div>', unsafe_allow_html=True)
            if uploaded is not None:
                extracted = ""
                try:
                    file_name = str(getattr(uploaded, "name", "") or "").lower()
                    file_type = str(getattr(uploaded, "type", "") or "").lower()
                    if file_type == "text/plain" or file_name.endswith(".txt"):
                        extracted = uploaded.read().decode("utf-8", errors="ignore")
                    else:
                        extracted = extract_pdf_text(uploaded) if callable(globals().get("extract_pdf_text")) else ""
                    if callable(globals().get("organize_cv_for_display")):
                        extracted = organize_cv_for_display(extracted)
                except Exception as exc:
                    st.warning(f"Could not read the uploaded CV: {exc}")
                if _wz132_store_cv_text(extracted, "Upload CV"):
                    _wz132_render_cv_understood()
                    st.markdown(
                        '<div class="wz134-scan-motion"><div class="wz134-scan-title">AI is building your interview<span class="wz132-dots"><span></span><span></span><span></span></span></div>'
                        '<div class="wz134-scan-line">Analyzing communication style...</div>'
                        '<div class="wz134-scan-line">Understanding experience level...</div>'
                        '<div class="wz134-scan-line">Generating recruiter pressure prompts...</div>'
                        '<div class="wz134-scan-line">Preparing follow-up questions...</div></div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.warning("The file uploaded, but the extracted text looked too short. Try TXT or paste your CV below.")

            with st.expander("Paste CV text instead", expanded=not bool(st.session_state.get("cv_text"))):
                pasted = st.text_area("Paste your CV text", height=155, key="wz132_paste_cv_text", placeholder="Paste your resume text here...")
                if st.button("Use pasted CV", key="wz132_use_pasted_cv", use_container_width=True):
                    if _wz132_store_cv_text(pasted, "Paste CV"):
                        st.session_state["wz132_cv_insights"] = _wz132_detect_cv_insights(pasted)
                        st.success("CV is ready.")
                        _wz132_render_cv_understood()
                        st.markdown(
                            '<div class="wz134-scan-motion"><div class="wz134-scan-title">AI is building your interview<span class="wz132-dots"><span></span><span></span><span></span></span></div>'
                            '<div class="wz134-scan-line">Analyzing communication style...</div>'
                            '<div class="wz134-scan-line">Understanding experience level...</div>'
                            '<div class="wz134-scan-line">Generating recruiter pressure prompts...</div>'
                            '<div class="wz134-scan-line">Preparing follow-up questions...</div></div>',
                            unsafe_allow_html=True,
                        )
                    else:
                        st.warning("Please paste more CV details first.")
            st.markdown('<div class="wz132-note">Your CV is only used to personalize your interview. We don’t store sensitive resume data in analytics. Takes less than 30 seconds.</div>', unsafe_allow_html=True)
            if st.session_state.get("cv_text"):
                if st.button("Continue to interview setup →", type="primary", use_container_width=True, key="wz132_continue_cv"):
                    st.session_state["onboarding_step_final"] = 2
                    try:
                        request_scroll_to_top()
                    except Exception:
                        pass
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with right:
            st.markdown(
                '<div class="wz132-demo wz134-demo-live"><div class="wz134-demo-top"><div><div class="wz132-demo-title">Experience the interview instantly</div>'
                '<div class="wz132-demo-copy">Not ready to upload? Try a sample CV and feel how WorkZo challenges answers.</div></div><div class="wz134-demo-timer">00:45</div></div>'
                '<div class="wz132-demo-badge">Demo path for first-time testers</div>'
                '<div class="wz132-mini-chat"><div class="wz134-rec-row"><span class="wz134-rec-dot"></span><span>AI Recruiter is listening</span><div class="wz134-wave"><span></span><span></span><span></span><span></span></div></div>'
                '<div class="wz132-bubble ai">AI Recruiter: Tell me about yourself, but keep it relevant.</div>'
                '<div class="wz132-bubble warn">⚠️ Follow-up: You’re losing me — give me one measurable result.</div>'
                '<div class="wz134-confidence"><span>Answer confidence</span><b>Needs proof</b><div><i></i></div></div></div>'
                '<div class="wz132-note">Best for testers who want to feel the product before sharing a CV.</div></div>',
                unsafe_allow_html=True,
            )
            if st.button("Experience demo interview", use_container_width=True, key="wz132_demo_cv"):
                demo_cv = SAMPLE_CV_TEXT if "SAMPLE_CV_TEXT" in globals() else "Demo CV: Technical Support Engineer with customer-facing experience, SQL, Python, dashboards, troubleshooting, communication skills, and experience handling customer issues."
                _wz132_store_cv_text(demo_cv, "Sample Demo")
                demo_jd = SAMPLE_JOB_DESCRIPTION if "SAMPLE_JOB_DESCRIPTION" in globals() else "Demo job description: Junior Data Analyst role requiring SQL, Python, dashboards, communication, problem solving, stakeholder support, and clear reporting."
                _wz132_store_job("Junior Data Analyst", demo_jd, "Demo Company")
                st.session_state["onboarding_step_final"] = 3
                try:
                    request_scroll_to_top()
                except Exception:
                    pass
                st.rerun()
        st.markdown('</div></div>', unsafe_allow_html=True)
        return

    if step == 2:
        st.markdown(
            '<section class="wz132-hero"><div class="wz132-kicker">Add your target role</div>'
            '<h1>Make the interview specific to the job</h1>'
            '<p>Paste one real job description so WorkZo can challenge you on the exact skills, gaps, language expectations, and recruiter pressure points.</p></section>',
            unsafe_allow_html=True,
        )
        with st.container(border=True):
            title = st.text_input("Job title", value=st.session_state.get("target_role", ""), placeholder="Example: Data Analyst", key="wz132_job_title")
            company = st.text_input("Company / employer (optional)", value=st.session_state.get("selected_company", ""), placeholder="Example: Siemens", key="wz132_company")
            jd = st.text_area("Job description", height=220, value=st.session_state.get("selected_job_description") or st.session_state.get("current_job_description") or "", placeholder="Paste the job description here...", key="wz132_jd")
        c1, c2, c3 = st.columns([1,1,1])
        with c1:
            if st.button("Back", use_container_width=True, key="wz132_back_to_cv"):
                st.session_state["onboarding_step_final"] = 1
                st.rerun()
        with c2:
            if st.button("Use demo job", use_container_width=True, key="wz132_demo_job"):
                demo_jd = SAMPLE_JOB_DESCRIPTION if "SAMPLE_JOB_DESCRIPTION" in globals() else "Demo job description: Junior Data Analyst role requiring SQL, Python, dashboards, communication and stakeholder collaboration."
                _wz132_store_job("Junior Data Analyst", demo_jd, "Demo Company")
                st.session_state["onboarding_step_final"] = 3
                st.rerun()
        with c3:
            if st.button("Continue", type="primary", use_container_width=True, key="wz132_continue_job"):
                if _wz132_store_job(title, jd, company):
                    st.session_state["onboarding_step_final"] = 3
                    st.rerun()
                else:
                    st.warning("Please paste the job description, or use the demo job.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    job = st.session_state.get("selected_job") or {}
    job_title_ready = html.escape(str(job.get("title") or st.session_state.get("target_role") or "Target role"))
    company_ready = html.escape(str(job.get("company") or "Target company"))
    st.markdown(
        '<section class="wz135-ready-hero">'
        '<div class="wz135-ready-copy"><div class="wz132-kicker">Interview room ready</div>'
        '<h1>AI recruiter is ready for you</h1>'
        '<p>Your CV and target job are loaded. WorkZo is preparing recruiter-style follow-ups, pressure prompts, and a hiring-style decision.</p>'
        '<div class="wz135-ready-tags"><span>CV understood</span><span>Job context loaded</span><span>Follow-ups enabled</span></div></div>'
        '<div class="wz135-recruiter-prep"><div class="wz135-prep-top"><div class="wz135-avatar">🎙️</div><div><b>AI Recruiter</b><span>Preparing your interview</span></div><strong>LIVE</strong></div>'
        '<div class="wz135-prep-line"><span></span>Preparing follow-up questions<div class="wz132-dots"><span></span><span></span><span></span></div></div>'
        '<div class="wz135-prep-line"><span></span>Analyzing measurable-impact gaps</div>'
        '<div class="wz135-prep-line"><span></span>Setting pressure level: realistic</div>'
        '<div class="wz135-wave"><i></i><i></i><i></i><i></i><i></i></div></div>'
        '</section>',
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns([1, 1])
    with c1:
        _wz132_render_cv_understood()
    with c2:
        st.markdown(
            '<div class="wz132-ai-read wz135-job-card"><div class="wz132-ai-title">🎯 Job context ready</div>'
            f'<div class="wz132-scan-row"><span class="wz132-pill">Role: {job_title_ready}</span>'
            f'<span class="wz132-pill">Company: {company_ready}</span>'
            '<span class="wz132-pill">Recruiter follow-ups enabled</span><span class="wz132-pill">Hiring-decision feedback enabled</span></div></div>',
            unsafe_allow_html=True,
        )
    if st.button("🎤 Start Real Interview", type="primary", use_container_width=True, key="wz132_start_interview"):
        st.session_state["onboarding_complete"] = True
        try:
            queue_navigation("workobot")
        except Exception:
            st.session_state["nav_page"] = "workobot"
            st.session_state["page"] = "workobot"
        st.rerun()
    st.caption("Need to change something? Use the Back button in the header or edit your setup from the dashboard later.")
    st.markdown('</div>', unsafe_allow_html=True)



# =========================================================
# WorkZo v134 - onboarding tightening + motion polish
# Scope: active onboarding/header only. Preserves previous logic.
# =========================================================
try:
    _wz134_previous_onboarding_css = _wz132_onboarding_css
except Exception:
    _wz134_previous_onboarding_css = None


def _wz132_onboarding_css() -> None:
    try:
        if callable(_wz134_previous_onboarding_css):
            _wz134_previous_onboarding_css()
    except Exception:
        pass
    try:
        st.markdown("""
        <style id="workzo-v134-onboarding-polish-css">
        /* Tighten vertical spacing by roughly 15-20% */
        .workzo-header{padding:.68rem .88rem!important;margin:0 auto .72rem auto!important;border-radius:18px!important;}
        .workzo-logo{width:46px!important;height:46px!important;min-width:46px!important;border-radius:13px!important;}
        .workzo-title{font-size:1.28rem!important;}
        .workzo-subtitle{font-size:.75rem!important;margin-top:.18rem!important;}
        .workzo-progress-wrap{min-width:190px!important;}
        .workzo-progress-bar{height:5px!important;}
        .workzo-progress-steps{margin-top:.24rem!important;}
        .wz132-shell{max-width:1080px!important;margin:0 auto 1.1rem!important;}
        .wz132-topline{margin:0 0 .42rem!important;gap:.55rem!important;}
        .wz132-progress{margin:.28rem 0 .52rem!important;gap:.42rem!important;}
        .wz132-step{padding:.46rem .56rem!important;border-radius:14px!important;font-size:.78rem!important;}
        .wz132-num{width:23px!important;height:23px!important;}
        .wz132-hero{padding:.72rem .92rem!important;margin:.32rem 0 .48rem!important;border-radius:19px!important;box-shadow:0 10px 30px rgba(2,6,23,.22)!important;}
        .wz132-kicker{font-size:.66rem!important;margin-bottom:.24rem!important;}
        .wz132-hero h1{font-size:clamp(1.36rem,3vw,2.1rem)!important;margin-bottom:.25rem!important;}
        .wz132-hero p{font-size:.89rem!important;line-height:1.32!important;}
        .wz132-grid{gap:.68rem!important;margin-top:.36rem!important;}
        .wz132-panel,.wz132-demo{border-radius:20px!important;padding:.82rem!important;box-shadow:0 12px 34px rgba(2,6,23,.20)!important;}
        .wz132-panel h2{font-size:clamp(1.12rem,2.2vw,1.55rem)!important;margin-bottom:.22rem!important;}
        .wz132-panel p,.wz132-demo-copy{font-size:.86rem!important;line-height:1.3!important;margin-bottom:.45rem!important;}
        .wz132-upload-wrap{padding:.76rem!important;margin:.42rem 0 .52rem!important;border-color:rgba(103,232,249,.58)!important;animation:wz134UploadGlow 2.1s ease-in-out infinite!important;}
        .wz132-upload-icon{width:40px!important;height:40px!important;animation:wz134IconFloat 2.4s ease-in-out infinite!important;}
        div[data-testid="stFileUploader"]{padding:.52rem!important;}
        .wz132-note{padding:.56rem .66rem!important;margin:.42rem 0 .52rem!important;font-size:.8rem!important;}
        .wz132-ai-read{padding:.72rem!important;margin:.48rem 0!important;border-radius:17px!important;}
        .wz132-mini-chat{padding:.58rem!important;margin:.46rem 0!important;}
        .wz132-bubble{padding:.48rem .54rem!important;margin:.32rem 0!important;font-size:.78rem!important;}
        .st-key-wz132_continue_cv button,.st-key-wz132_continue_job button,.st-key-wz132_start_interview button{min-height:58px!important;border-radius:18px!important;background:radial-gradient(circle at 18% 12%,rgba(103,232,249,.42),transparent 35%),linear-gradient(135deg,#020617,#075985,#2563eb)!important;box-shadow:0 0 0 1px rgba(125,211,252,.34),0 18px 56px rgba(14,165,233,.30)!important;}
        .st-key-wz132_continue_cv button:after,.st-key-wz132_continue_job button:after{content:' →';}
        @keyframes wz134UploadGlow{0%,100%{box-shadow:inset 0 0 0 1px rgba(34,211,238,.07),0 10px 28px rgba(14,165,233,.08)}50%{box-shadow:inset 0 0 0 1px rgba(34,211,238,.24),0 20px 60px rgba(14,165,233,.22)}}
        @keyframes wz134IconFloat{0%,100%{transform:translateY(0) rotate(0deg)}50%{transform:translateY(-4px) rotate(-2deg)}}
        .wz134-scan-motion{border:1px solid rgba(34,211,238,.28);background:linear-gradient(135deg,rgba(8,47,73,.44),rgba(15,23,42,.72));border-radius:18px;padding:.72rem;margin:.52rem 0;animation:wz134ScanIn .28s ease-out both;}
        .wz134-scan-title{color:#e0f2fe;font-weight:950;margin-bottom:.36rem;}
        .wz134-scan-line{color:#bae6fd;font-size:.82rem;padding:.18rem 0;opacity:.92;}
        .wz134-scan-line:before{content:'✓';color:#22d3ee;font-weight:950;margin-right:.4rem;}
        @keyframes wz134ScanIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
        .wz134-demo-live{border-color:rgba(103,232,249,.35)!important;background:radial-gradient(circle at 20% 0%,rgba(103,232,249,.16),transparent 35%),radial-gradient(circle at 85% 20%,rgba(129,140,248,.20),transparent 38%),linear-gradient(180deg,rgba(30,41,59,.88),rgba(15,23,42,.80))!important;}
        .wz134-demo-top{display:flex;justify-content:space-between;gap:.65rem;align-items:flex-start;}
        .wz134-demo-timer{border:1px solid rgba(248,113,113,.35);background:rgba(127,29,29,.18);color:#fecaca;border-radius:999px;padding:.32rem .52rem;font-size:.78rem;font-weight:950;box-shadow:0 0 22px rgba(248,113,113,.12);}
        .wz134-rec-row{display:flex;align-items:center;gap:.42rem;color:#bae6fd;font-size:.76rem;font-weight:900;margin-bottom:.42rem;}
        .wz134-rec-dot{width:8px;height:8px;border-radius:999px;background:#22d3ee;box-shadow:0 0 0 0 rgba(34,211,238,.7);animation:wz134Pulse 1.4s infinite;}
        @keyframes wz134Pulse{70%{box-shadow:0 0 0 9px rgba(34,211,238,0)}}
        .wz134-wave{display:flex;gap:3px;margin-left:auto;align-items:end;height:18px;}
        .wz134-wave span{width:4px;border-radius:999px;background:#67e8f9;animation:wz134Wave 1s infinite ease-in-out;}
        .wz134-wave span:nth-child(1){height:7px}.wz134-wave span:nth-child(2){height:15px;animation-delay:.1s}.wz134-wave span:nth-child(3){height:10px;animation-delay:.2s}.wz134-wave span:nth-child(4){height:17px;animation-delay:.3s}
        @keyframes wz134Wave{0%,100%{transform:scaleY(.55);opacity:.55}50%{transform:scaleY(1);opacity:1}}
        .wz134-confidence{border:1px solid rgba(250,204,21,.16);background:rgba(250,204,21,.07);border-radius:14px;padding:.5rem;margin-top:.45rem;color:#fde68a;font-size:.76rem;font-weight:850;}
        .wz134-confidence{display:grid;grid-template-columns:1fr auto;gap:.35rem;align-items:center;}
        .wz134-confidence div{grid-column:1/3;height:5px;border-radius:99px;background:rgba(250,204,21,.16);overflow:hidden;}
        .wz134-confidence i{display:block;height:100%;width:42%;border-radius:99px;background:linear-gradient(90deg,#facc15,#fb923c);animation:wz134Confidence 2s ease-in-out infinite;}
        @keyframes wz134Confidence{50%{width:52%}}
        @media(max-width:760px){.workzo-header{padding:.56rem .64rem!important;margin-bottom:.52rem!important}.wz132-hero{padding:.68rem!important}.wz132-grid{gap:.55rem!important}.wz132-topline{align-items:flex-start!important}.wz132-trust{border-radius:14px!important;line-height:1.25!important}.wz134-demo-top{flex-direction:column}.wz134-demo-timer{align-self:flex-start}}
        </style>
        """, unsafe_allow_html=True)
    except Exception:
        pass


# =========================================================
# WorkZo v135 - final interview-ready immersion polish
# Scope: step 3 onboarding, CTA momentum, progress wording.
# =========================================================
try:
    _wz135_previous_onboarding_css = _wz132_onboarding_css
except Exception:
    _wz135_previous_onboarding_css = None


def _wz132_onboarding_css() -> None:
    try:
        if callable(_wz135_previous_onboarding_css):
            _wz135_previous_onboarding_css()
    except Exception:
        pass
    try:
        st.markdown("""
        <style id="workzo-v135-ready-immersion-css">
        .workzo-header{padding:.56rem .78rem!important;margin-bottom:.58rem!important;border-radius:18px!important;}
        .workzo-logo{width:42px!important;height:42px!important;min-width:42px!important;}
        .workzo-progress-top span:last-child{color:#67e8f9!important;font-weight:950!important;}
        .wz132-trust{padding:.30rem .54rem!important;font-size:.75rem!important;opacity:.88!important;}
        .wz135-ready-hero{display:grid;grid-template-columns:1.08fr .78fr;gap:1rem;align-items:center;border:1px solid rgba(34,211,238,.26);border-radius:22px;padding:1rem 1.05rem;background:radial-gradient(circle at 8% 0%,rgba(34,211,238,.16),transparent 32%),linear-gradient(135deg,rgba(8,47,73,.72),rgba(15,23,42,.94));box-shadow:0 14px 42px rgba(2,6,23,.26);margin:.35rem 0 .70rem;}
        .wz135-ready-copy h1{color:#fff;font-size:clamp(1.55rem,3vw,2.35rem);line-height:1.02;letter-spacing:-.055em;margin:0 0 .36rem;font-weight:950;}
        .wz135-ready-copy p{color:#cbd5e1;font-size:.92rem;line-height:1.34;margin:0;max-width:620px;}
        .wz135-ready-tags{display:flex;flex-wrap:wrap;gap:.42rem;margin-top:.65rem;}
        .wz135-ready-tags span{border:1px solid rgba(103,232,249,.20);background:rgba(14,165,233,.10);color:#bae6fd;border-radius:999px;padding:.30rem .52rem;font-size:.76rem;font-weight:900;}
        .wz135-recruiter-prep{border:1px solid rgba(103,232,249,.24);background:rgba(2,6,23,.38);border-radius:20px;padding:.86rem;box-shadow:inset 0 0 0 1px rgba(34,211,238,.06),0 18px 48px rgba(14,165,233,.11);position:relative;overflow:hidden;}
        .wz135-recruiter-prep:before{content:"";position:absolute;inset:-80px auto auto -80px;width:190px;height:190px;background:radial-gradient(circle,rgba(34,211,238,.18),transparent 66%);animation:wz135PrepGlow 3s ease-in-out infinite;}
        @keyframes wz135PrepGlow{50%{transform:translate(14px,8px);opacity:.8}}
        .wz135-prep-top{display:flex;align-items:center;gap:.62rem;margin-bottom:.68rem;position:relative;}
        .wz135-avatar{width:42px;height:42px;border-radius:15px;display:grid;place-items:center;background:linear-gradient(135deg,#22d3ee,#2563eb);box-shadow:0 0 0 0 rgba(34,211,238,.58);animation:wz135MicPulse 1.8s infinite;}
        @keyframes wz135MicPulse{70%{box-shadow:0 0 0 12px rgba(34,211,238,0)}}
        .wz135-prep-top b{display:block;color:#fff;font-weight:950;}
        .wz135-prep-top span{display:block;color:#94a3b8;font-size:.78rem;font-weight:800;}
        .wz135-prep-top strong{margin-left:auto;border:1px solid rgba(34,211,238,.26);background:rgba(14,165,233,.12);color:#67e8f9;border-radius:999px;padding:.24rem .48rem;font-size:.68rem;letter-spacing:.08em;}
        .wz135-prep-line{display:flex;align-items:center;gap:.42rem;color:#dbeafe;font-size:.80rem;font-weight:850;padding:.34rem 0;position:relative;}
        .wz135-prep-line>span{width:7px;height:7px;border-radius:99px;background:#22d3ee;box-shadow:0 0 16px rgba(34,211,238,.55);}
        .wz135-wave{height:30px;display:flex;gap:5px;align-items:end;margin-top:.58rem;border-top:1px solid rgba(148,163,184,.12);padding-top:.54rem;}
        .wz135-wave i{display:block;width:6px;border-radius:999px;background:linear-gradient(180deg,#67e8f9,#2563eb);animation:wz135Wave 1.1s infinite ease-in-out;}
        .wz135-wave i:nth-child(1){height:12px}.wz135-wave i:nth-child(2){height:22px;animation-delay:.08s}.wz135-wave i:nth-child(3){height:16px;animation-delay:.16s}.wz135-wave i:nth-child(4){height:28px;animation-delay:.24s}.wz135-wave i:nth-child(5){height:14px;animation-delay:.32s}
        @keyframes wz135Wave{0%,100%{transform:scaleY(.55);opacity:.55}50%{transform:scaleY(1);opacity:1}}
        .wz135-job-card{margin-top:0!important;}
        .st-key-wz132_start_interview button{min-height:64px!important;border-radius:20px!important;font-size:1.05rem!important;font-weight:950!important;background:radial-gradient(circle at 18% 10%,rgba(103,232,249,.42),transparent 36%),linear-gradient(135deg,#020617,#0369a1,#2563eb)!important;border:1px solid rgba(125,211,252,.62)!important;color:#eff6ff!important;box-shadow:0 0 0 1px rgba(125,211,252,.22),0 0 28px rgba(34,211,238,.22),0 22px 70px rgba(37,99,235,.34)!important;animation:wz135StartBreath 2.3s ease-in-out infinite!important;}
        .st-key-wz132_start_interview button:hover{transform:translateY(-3px) scale(1.01)!important;box-shadow:0 0 0 1px rgba(125,211,252,.34),0 0 38px rgba(34,211,238,.34),0 28px 84px rgba(37,99,235,.42)!important;}
        @keyframes wz135StartBreath{0%,100%{filter:brightness(1)}50%{filter:brightness(1.13)}}
        .st-key-wz132_open_dashboard{display:none!important;}
        @media(max-width:860px){.wz135-ready-hero{grid-template-columns:1fr;padding:.86rem}.wz135-recruiter-prep{margin-top:.2rem}.wz135-ready-tags span{font-size:.72rem}.st-key-wz132_start_interview button{min-height:58px!important}}
        </style>
        """, unsafe_allow_html=True)
    except Exception:
        pass


# =========================================================
# WorkZo v136 - enforce single CTA on onboarding ready step
# Purpose: remove secondary dashboard CTA, tighten ready hero, and make
# the start interview moment feel like the only next action.
# =========================================================
try:
    _wz136_previous_onboarding_css = _wz132_onboarding_css
except Exception:
    _wz136_previous_onboarding_css = None

def _wz132_onboarding_css() -> None:
    try:
        if callable(_wz136_previous_onboarding_css):
            _wz136_previous_onboarding_css()
    except Exception:
        pass
    try:
        st.markdown("""
        <style id="workzo-v136-single-cta-ready-css">
        /* Hide every old secondary dashboard CTA from previous onboarding variants */
        .st-key-wzflow_open_dashboard,
        .st-key-wz131_open_dashboard,
        .st-key-wz132_open_dashboard,
        .st-key-wz_final_dashboard_ready,
        .st-key-wz_final_go_dashboard,
        .st-key-wz_final_dashboard_ready button,
        .st-key-wz_final_go_dashboard button{
            display:none!important;
            visibility:hidden!important;
            height:0!important;
            margin:0!important;
            padding:0!important;
            overflow:hidden!important;
        }
        /* Make the final ready card shorter and better utilized */
        .wz135-ready-hero{
            padding:.78rem .88rem!important;
            margin:.24rem 0 .54rem!important;
            gap:.72rem!important;
            border-radius:20px!important;
        }
        .wz135-ready-copy h1{
            font-size:clamp(1.36rem,2.55vw,2.02rem)!important;
            margin-bottom:.24rem!important;
            line-height:1!important;
        }
        .wz135-ready-copy p{
            font-size:.86rem!important;
            line-height:1.28!important;
        }
        .wz135-ready-tags{margin-top:.48rem!important;gap:.32rem!important;}
        .wz135-ready-tags span{padding:.24rem .44rem!important;font-size:.70rem!important;}
        .wz135-recruiter-prep{padding:.68rem!important;border-radius:17px!important;}
        .wz135-prep-top{margin-bottom:.46rem!important;}
        .wz135-avatar{width:36px!important;height:36px!important;border-radius:13px!important;}
        .wz135-prep-line{font-size:.74rem!important;padding:.23rem 0!important;}
        .wz135-wave{height:24px!important;margin-top:.36rem!important;padding-top:.38rem!important;}
        /* One powerful CTA only */
        .st-key-wz132_start_interview button,
        .st-key-wz131_start_interview button,
        .st-key-wzflow_start_interview_now button{
            min-height:68px!important;
            border-radius:22px!important;
            font-size:1.08rem!important;
            font-weight:950!important;
            letter-spacing:-.01em!important;
            background:radial-gradient(circle at 18% 10%,rgba(103,232,249,.52),transparent 34%),linear-gradient(135deg,#020617,#0369a1,#1d4ed8)!important;
            border:1px solid rgba(125,211,252,.70)!important;
            color:#f8fafc!important;
            box-shadow:0 0 0 1px rgba(125,211,252,.28),0 0 36px rgba(34,211,238,.30),0 26px 84px rgba(37,99,235,.42)!important;
            animation:wz136StartCallPulse 2.15s ease-in-out infinite!important;
        }
        .st-key-wz132_start_interview button:before,
        .st-key-wz131_start_interview button:before,
        .st-key-wzflow_start_interview_now button:before{
            content:'🎙 ';
            display:inline-block;
            animation:wz136MicNudge 1.6s ease-in-out infinite;
        }
        .st-key-wz132_start_interview button:hover,
        .st-key-wz131_start_interview button:hover,
        .st-key-wzflow_start_interview_now button:hover{
            transform:translateY(-3px) scale(1.012)!important;
            box-shadow:0 0 0 1px rgba(125,211,252,.38),0 0 46px rgba(34,211,238,.38),0 32px 92px rgba(37,99,235,.50)!important;
        }
        @keyframes wz136StartCallPulse{0%,100%{filter:brightness(1);box-shadow:0 0 0 1px rgba(125,211,252,.28),0 0 30px rgba(34,211,238,.25),0 22px 72px rgba(37,99,235,.34)}50%{filter:brightness(1.14);box-shadow:0 0 0 1px rgba(125,211,252,.42),0 0 46px rgba(34,211,238,.40),0 28px 88px rgba(37,99,235,.46)}}
        @keyframes wz136MicNudge{0%,100%{transform:translateY(0) rotate(0deg)}50%{transform:translateY(-1px) rotate(-6deg)}}
        /* More meaningful progress language area */
        .workzo-progress-top span:first-child{font-size:.74rem!important;color:#c7d2fe!important;}
        .workzo-progress-top span:last-child{font-size:.78rem!important;color:#67e8f9!important;}
        .wz132-trust{padding:.24rem .46rem!important;font-size:.70rem!important;opacity:.82!important;}
        @media(max-width:860px){
            .wz135-ready-hero{grid-template-columns:1fr!important;padding:.72rem!important;}
            .st-key-wz132_start_interview button,.st-key-wz131_start_interview button,.st-key-wzflow_start_interview_now button{min-height:60px!important;}
        }
        </style>
        """, unsafe_allow_html=True)
    except Exception:
        pass


# =========================================================
# WorkZo v137 - hard remove dashboard secondary CTA on onboarding ready step
# This is additive. It keeps the original onboarding logic but hides/removes all
# dashboard CTA variants so the only visible next action is Start Real Interview.
# =========================================================
def _wz137_hide_dashboard_secondary_cta() -> None:
    try:
        st.markdown("""
        <style id="workzo-v137-hide-dashboard-secondary-cta">
        .st-key-wzflow_open_dashboard,
        .st-key-wz131_open_dashboard,
        .st-key-wz132_open_dashboard,
        .st-key-wz_final_dashboard_ready,
        .st-key-wz_final_go_dashboard,
        div[data-testid="stButton"]:has(button[aria-label="Open Dashboard"]),
        div[data-testid="stButton"]:has(button[aria-label="Go to dashboard"]) {
            display:none!important;
            visibility:hidden!important;
            height:0!important;
            min-height:0!important;
            margin:0!important;
            padding:0!important;
            overflow:hidden!important;
        }
        </style>
        """, unsafe_allow_html=True)
    except Exception:
        pass

try:
    _wz137_previous_show_onboarding = show_onboarding
    def show_onboarding():
        _wz137_hide_dashboard_secondary_cta()
        return _wz137_previous_show_onboarding()
except Exception:
    pass

# =========================================================
# WorkZo v138 - definitive active onboarding override
# Fixes: no Open Dashboard CTA, shorter ready hero, live recruiter prep,
# single pulsing Start Real Interview CTA, and clearer header progress.
# This block is intentionally LAST so it overrides earlier onboarding variants.
# =========================================================

def _wz138_render_header(step: int = 1) -> None:
    """Compact onboarding header with meaningful progress text instead of raw % confusion."""
    try:
        logo_src = None
        try:
            logo_src = image_to_data_uri(ICON_PATH) or image_to_data_uri(LOGO_PATH)
        except Exception:
            logo_src = None
        progress_label = "Ready to begin" if int(step or 1) >= 3 else f"Step {int(step or 1)}/3"
        status_label = "Interview setup complete" if int(step or 1) >= 3 else "Interview setup"
        logo_html = f"<img src='{logo_src}' class='wz138-logo' alt='WorkZo AI'>" if logo_src else "<div class='wz138-logo wz138-logo-fallback'>WZ</div>"
        st.markdown(f"""
        <div class="wz138-header">
            <div class="wz138-brand">
                {logo_html}
                <div>
                    <div class="wz138-title">WorkZo <span>AI</span></div>
                    <div class="wz138-subtitle">Your guided AI career system</div>
                </div>
            </div>
            <div class="wz138-header-right">
                <button class="wz138-back" onclick="history.back()">← Back</button>
                <div class="wz138-status">
                    <div class="wz138-status-top"><span>{html.escape(status_label)}</span><b>{html.escape(progress_label)}</b></div>
                    <div class="wz138-status-line"><i style="width:{'100%' if int(step or 1) >= 3 else '66%'}"></i></div>
                    <div class="wz138-mini-steps"><span class="done">✓ CV</span><span class="done">✓ Jobs</span><span class="{'done' if int(step or 1) >= 3 else ''}">3 Interview</span></div>
                </div>
                <div class="wz138-beta">BETA</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    except Exception:
        try:
            render_workzo_header()
        except Exception:
            pass


def _wz138_css() -> None:
    st.markdown("""
    <style id="workzo-v138-definitive-onboarding-css">
    [data-testid="stMainBlockContainer"], .block-container{max-width:1080px!important;padding-top:.35rem!important;}
    .wz138-header{max-width:1080px;margin:.15rem auto .58rem;padding:.58rem .76rem;border:1px solid rgba(34,211,238,.30);border-radius:18px;background:linear-gradient(135deg,rgba(8,47,73,.78),rgba(15,23,42,.92));box-shadow:0 14px 42px rgba(2,6,23,.28);display:flex;align-items:center;justify-content:space-between;gap:.9rem;}
    .wz138-brand{display:flex;align-items:center;gap:.72rem;min-width:0;}
    .wz138-logo{width:44px;height:44px;border-radius:13px;object-fit:cover;box-shadow:0 10px 28px rgba(14,165,233,.20);}
    .wz138-logo-fallback{display:grid;place-items:center;background:linear-gradient(135deg,#22d3ee,#2563eb);color:white;font-weight:950;}
    .wz138-title{color:#fff;font-size:1.25rem;font-weight:950;letter-spacing:-.04em;line-height:1;}.wz138-title span{color:#22d3ee;}.wz138-subtitle{color:#cbd5e1;font-size:.74rem;font-weight:800;margin-top:.18rem;}
    .wz138-header-right{display:flex;align-items:center;gap:.7rem;}
    .wz138-back{border:1px solid rgba(148,163,184,.20);background:rgba(15,23,42,.58);color:#e0f2fe;border-radius:999px;padding:.42rem .72rem;font-weight:900;cursor:pointer;}
    .wz138-status{min-width:230px;}.wz138-status-top{display:flex;align-items:center;justify-content:space-between;color:#cbd5e1;font-size:.74rem;font-weight:900;margin-bottom:.28rem;}.wz138-status-top b{color:#67e8f9;}
    .wz138-status-line{height:5px;background:rgba(148,163,184,.18);border-radius:99px;overflow:hidden;}.wz138-status-line i{display:block;height:100%;border-radius:99px;background:linear-gradient(90deg,#22d3ee,#22c55e);box-shadow:0 0 18px rgba(34,211,238,.35);}
    .wz138-mini-steps{display:flex;gap:.34rem;margin-top:.28rem;}.wz138-mini-steps span{border:1px solid rgba(148,163,184,.18);background:rgba(15,23,42,.52);color:#cbd5e1;border-radius:999px;padding:.18rem .38rem;font-size:.64rem;font-weight:950;}.wz138-mini-steps span.done{border-color:rgba(34,211,238,.34);background:rgba(14,165,233,.14);color:#67e8f9;}
    .wz138-beta{border:1px solid rgba(34,211,238,.42);background:rgba(14,165,233,.13);color:#67e8f9;border-radius:999px;padding:.34rem .56rem;font-size:.68rem;font-weight:950;letter-spacing:.04em;}
    .wz132-shell{max-width:1080px!important;margin:0 auto .9rem!important;}
    .wz132-topline{margin:0 0 .36rem!important;}.wz132-trust{padding:.22rem .44rem!important;font-size:.69rem!important;opacity:.78!important;line-height:1.2!important;}.wz132-step-text{font-size:.80rem!important;}
    .wz132-progress{margin:.22rem 0 .48rem!important;gap:.40rem!important;}.wz132-step{padding:.42rem .52rem!important;border-radius:14px!important;font-size:.76rem!important;}.wz132-num{width:22px!important;height:22px!important;}
    .wz138-ready-hero{display:grid;grid-template-columns:1.04fr .88fr;gap:.72rem;align-items:center;border:1px solid rgba(34,211,238,.26);border-radius:20px;padding:.72rem .84rem;background:radial-gradient(circle at 8% 0%,rgba(34,211,238,.17),transparent 32%),linear-gradient(135deg,rgba(8,47,73,.72),rgba(15,23,42,.94));box-shadow:0 12px 36px rgba(2,6,23,.25);margin:.22rem 0 .50rem;}
    .wz138-ready-copy h1{color:#fff;font-size:clamp(1.38rem,2.55vw,2.05rem);line-height:1.02;letter-spacing:-.055em;margin:0 0 .24rem;font-weight:950;}.wz138-ready-copy p{color:#cbd5e1;font-size:.86rem;line-height:1.28;margin:0;max-width:600px;}
    .wz138-kicker{color:#67e8f9;text-transform:uppercase;letter-spacing:.16em;font-size:.66rem;font-weight:950;margin-bottom:.22rem;}
    .wz138-tags{display:flex;flex-wrap:wrap;gap:.32rem;margin-top:.46rem;}.wz138-tags span{border:1px solid rgba(103,232,249,.20);background:rgba(14,165,233,.10);color:#bae6fd;border-radius:999px;padding:.23rem .42rem;font-size:.70rem;font-weight:900;}
    .wz138-recruiter-prep{border:1px solid rgba(103,232,249,.25);background:rgba(2,6,23,.40);border-radius:17px;padding:.68rem;box-shadow:inset 0 0 0 1px rgba(34,211,238,.06),0 16px 42px rgba(14,165,233,.12);position:relative;overflow:hidden;}.wz138-recruiter-prep:before{content:"";position:absolute;left:-70px;top:-80px;width:170px;height:170px;background:radial-gradient(circle,rgba(34,211,238,.18),transparent 66%);animation:wz138PrepGlow 3s ease-in-out infinite;}@keyframes wz138PrepGlow{50%{transform:translate(14px,8px);opacity:.8}}
    .wz138-prep-top{display:flex;align-items:center;gap:.54rem;margin-bottom:.44rem;position:relative;}.wz138-avatar{width:36px;height:36px;border-radius:13px;display:grid;place-items:center;background:linear-gradient(135deg,#22d3ee,#2563eb);box-shadow:0 0 0 0 rgba(34,211,238,.58);animation:wz138MicPulse 1.7s infinite;}@keyframes wz138MicPulse{70%{box-shadow:0 0 0 12px rgba(34,211,238,0)}}.wz138-prep-top b{display:block;color:#fff;font-weight:950;line-height:1;}.wz138-prep-top span{display:block;color:#94a3b8;font-size:.72rem;font-weight:800;margin-top:.12rem;}.wz138-prep-top strong{margin-left:auto;border:1px solid rgba(34,211,238,.26);background:rgba(14,165,233,.12);color:#67e8f9;border-radius:999px;padding:.20rem .42rem;font-size:.64rem;letter-spacing:.08em;}
    .wz138-prep-line{display:flex;align-items:center;gap:.38rem;color:#dbeafe;font-size:.74rem;font-weight:850;padding:.22rem 0;position:relative;}.wz138-prep-line>span{width:7px;height:7px;border-radius:99px;background:#22d3ee;box-shadow:0 0 16px rgba(34,211,238,.55);}.wz138-dots{display:inline-flex;gap:.20rem;margin-left:.28rem}.wz138-dots i{width:5px;height:5px;border-radius:99px;background:#67e8f9;animation:wz138Dots 1.2s infinite ease-in-out}.wz138-dots i:nth-child(2){animation-delay:.15s}.wz138-dots i:nth-child(3){animation-delay:.3s}@keyframes wz138Dots{0%,80%,100%{opacity:.28;transform:translateY(0)}40%{opacity:1;transform:translateY(-3px)}}
    .wz138-wave{height:23px;display:flex;gap:5px;align-items:end;margin-top:.34rem;border-top:1px solid rgba(148,163,184,.12);padding-top:.36rem;}.wz138-wave i{display:block;width:6px;border-radius:999px;background:linear-gradient(180deg,#67e8f9,#2563eb);animation:wz138Wave 1.1s infinite ease-in-out}.wz138-wave i:nth-child(1){height:10px}.wz138-wave i:nth-child(2){height:20px;animation-delay:.08s}.wz138-wave i:nth-child(3){height:14px;animation-delay:.16s}.wz138-wave i:nth-child(4){height:24px;animation-delay:.24s}.wz138-wave i:nth-child(5){height:12px;animation-delay:.32s}@keyframes wz138Wave{0%,100%{transform:scaleY(.55);opacity:.55}50%{transform:scaleY(1);opacity:1}}
    .wz132-ai-read{padding:.68rem!important;margin:.36rem 0!important;border-radius:17px!important;}.wz132-ai-title{font-size:.95rem!important;}.wz132-pill{font-size:.72rem!important;padding:.25rem .42rem!important;}.wz132-scan-row{gap:.32rem!important;}
    .st-key-wz138_start_interview button{min-height:68px!important;border-radius:22px!important;font-size:1.08rem!important;font-weight:950!important;letter-spacing:-.01em!important;background:radial-gradient(circle at 18% 10%,rgba(103,232,249,.52),transparent 34%),linear-gradient(135deg,#020617,#0369a1,#1d4ed8)!important;border:1px solid rgba(125,211,252,.70)!important;color:#f8fafc!important;box-shadow:0 0 0 1px rgba(125,211,252,.28),0 0 36px rgba(34,211,238,.30),0 26px 84px rgba(37,99,235,.42)!important;animation:wz138StartCallPulse 2.15s ease-in-out infinite!important;}.st-key-wz138_start_interview button:before{content:'🎙 ';display:inline-block;animation:wz138MicNudge 1.6s ease-in-out infinite}.st-key-wz138_start_interview button:hover{transform:translateY(-3px) scale(1.012)!important;box-shadow:0 0 0 1px rgba(125,211,252,.38),0 0 46px rgba(34,211,238,.38),0 32px 92px rgba(37,99,235,.50)!important}@keyframes wz138StartCallPulse{0%,100%{filter:brightness(1)}50%{filter:brightness(1.14)}}@keyframes wz138MicNudge{0%,100%{transform:translateY(0) rotate(0deg)}50%{transform:translateY(-1px) rotate(-6deg)}}
    /* emergency hide all older dashboard buttons/captions from previous variants */
    .st-key-wz132_open_dashboard,.st-key-wz131_open_dashboard,.st-key-wzflow_open_dashboard,.st-key-wz_final_go_dashboard,.st-key-wz_final_dashboard_ready{display:none!important;visibility:hidden!important;height:0!important;margin:0!important;padding:0!important;overflow:hidden!important;}
    @media(max-width:860px){.wz138-header{align-items:flex-start;flex-direction:column}.wz138-header-right{width:100%;justify-content:space-between}.wz138-status{min-width:0;flex:1}.wz138-ready-hero{grid-template-columns:1fr;padding:.72rem}.st-key-wz138_start_interview button{min-height:60px!important}}
    </style>
    """, unsafe_allow_html=True)


def show_onboarding():
    """v138 definitive active onboarding. This override removes competing dashboard CTA."""
    try:
        maybe_scroll_to_top()
    except Exception:
        pass
    try:
        apply_workzo_v75_global_css()
    except Exception:
        pass
    _wz138_css()

    step = int(st.session_state.get("onboarding_step_final", st.session_state.get("wz_onboarding_step", 1)) or 1)
    if step < 1 or step > 3:
        step = 1
    st.session_state["onboarding_step_final"] = step

    _wz138_render_header(step)

    st.markdown('<div class="wz132-shell">', unsafe_allow_html=True)
    st.markdown(
        f'<div class="wz132-topline"><div class="wz132-step-text">Step {step} of 3</div><div class="wz132-trust">🔒 Your CV is only used to personalize your interview · No account required · We don’t store sensitive resume data · Takes less than 30 seconds</div></div>',
        unsafe_allow_html=True,
    )
    try:
        _wz132_progress(step)
    except Exception:
        pass

    if step == 1:
        st.markdown(
            '<section class="wz132-hero"><div class="wz132-kicker">Start with your CV</div>'
            '<h1>Your interview starts with your CV</h1>'
            '<p>Upload your CV to personalize recruiter-style questions, pressure follow-ups, and hiring feedback. WorkZo first understands your experience — then builds the interview around it.</p></section>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="wz132-grid">', unsafe_allow_html=True)
        left, right = st.columns([1.32, .86])
        with left:
            st.markdown(
                '<div class="wz132-panel"><h2>Let AI understand your experience</h2><p>This is the core step. Your interview becomes specific to your real background, not a generic mock test.</p>'
                '<div class="wz132-upload-wrap"><div class="wz132-upload-head"><div class="wz132-upload-icon">📄</div><div><div class="wz132-upload-title">Upload your CV to personalize your interview</div><div class="wz132-upload-sub">PDF or TXT works best. Drag, drop, or browse.</div></div></div>',
                unsafe_allow_html=True,
            )
            uploaded = st.file_uploader("Upload PDF or TXT", type=["pdf", "txt"], key="wz132_cv_upload")
            st.markdown('</div>', unsafe_allow_html=True)
            if uploaded is not None:
                extracted = ""
                try:
                    file_name = str(getattr(uploaded, "name", "") or "").lower()
                    file_type = str(getattr(uploaded, "type", "") or "").lower()
                    if file_type == "text/plain" or file_name.endswith(".txt"):
                        extracted = uploaded.read().decode("utf-8", errors="ignore")
                    else:
                        extracted = extract_pdf_text(uploaded) if callable(globals().get("extract_pdf_text")) else ""
                    if callable(globals().get("organize_cv_for_display")):
                        extracted = organize_cv_for_display(extracted)
                except Exception as exc:
                    st.warning(f"Could not read the uploaded CV: {exc}")
                if _wz132_store_cv_text(extracted, "Upload CV"):
                    _wz132_render_cv_understood()
                    st.markdown('<div class="wz134-scan-motion"><div class="wz134-scan-title">AI is building your interview<span class="wz132-dots"><span></span><span></span><span></span></span></div><div class="wz134-scan-line">Analyzing communication style...</div><div class="wz134-scan-line">Understanding experience level...</div><div class="wz134-scan-line">Generating recruiter pressure prompts...</div><div class="wz134-scan-line">Preparing follow-up questions...</div></div>', unsafe_allow_html=True)
                else:
                    st.warning("The file uploaded, but the extracted text looked too short. Try TXT or paste your CV below.")
            with st.expander("Paste CV text instead", expanded=not bool(st.session_state.get("cv_text"))):
                pasted = st.text_area("Paste your CV text", height=155, key="wz132_paste_cv_text", placeholder="Paste your resume text here...")
                if st.button("Use pasted CV", key="wz132_use_pasted_cv", use_container_width=True):
                    if _wz132_store_cv_text(pasted, "Paste CV"):
                        st.session_state["wz132_cv_insights"] = _wz132_detect_cv_insights(pasted)
                        st.success("CV is ready.")
                        _wz132_render_cv_understood()
                        st.markdown('<div class="wz134-scan-motion"><div class="wz134-scan-title">AI is building your interview<span class="wz132-dots"><span></span><span></span><span></span></span></div><div class="wz134-scan-line">Analyzing communication style...</div><div class="wz134-scan-line">Understanding experience level...</div><div class="wz134-scan-line">Generating recruiter pressure prompts...</div><div class="wz134-scan-line">Preparing follow-up questions...</div></div>', unsafe_allow_html=True)
                    else:
                        st.warning("Please paste more CV details first.")
            st.markdown('<div class="wz132-note">Your CV is only used to personalize your interview. We don’t store sensitive resume data in analytics. Takes less than 30 seconds.</div>', unsafe_allow_html=True)
            if st.session_state.get("cv_text"):
                if st.button("Continue to interview setup", type="primary", use_container_width=True, key="wz132_continue_cv"):
                    st.session_state["onboarding_step_final"] = 2
                    try: request_scroll_to_top()
                    except Exception: pass
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with right:
            st.markdown(
                '<div class="wz132-demo wz134-demo-live"><div class="wz134-demo-top"><div><div class="wz132-demo-title">Experience the interview instantly</div>'
                '<div class="wz132-demo-copy">Not ready to upload? Try a sample CV and feel how WorkZo challenges answers.</div></div><div class="wz134-demo-timer">00:45</div></div>'
                '<div class="wz132-demo-badge">Demo path for first-time testers</div><div class="wz132-mini-chat"><div class="wz134-rec-row"><span class="wz134-rec-dot"></span><span>AI Recruiter is listening</span><div class="wz134-wave"><span></span><span></span><span></span><span></span></div></div>'
                '<div class="wz132-bubble ai">AI Recruiter: Tell me about yourself, but keep it relevant.</div><div class="wz132-bubble warn">⚠️ Follow-up: You’re losing me — give me one measurable result.</div><div class="wz134-confidence"><span>Answer confidence</span><b>Needs proof</b><div><i></i></div></div></div><div class="wz132-note">Best for testers who want to feel the product before sharing a CV.</div></div>',
                unsafe_allow_html=True,
            )
            if st.button("Experience demo interview", use_container_width=True, key="wz132_demo_cv"):
                demo_cv = SAMPLE_CV_TEXT if "SAMPLE_CV_TEXT" in globals() else "Demo CV: Technical Support Engineer with customer-facing experience, SQL, Python, dashboards, troubleshooting, communication skills, and experience handling customer issues."
                _wz132_store_cv_text(demo_cv, "Sample Demo")
                demo_jd = SAMPLE_JOB_DESCRIPTION if "SAMPLE_JOB_DESCRIPTION" in globals() else "Demo job description: Junior Data Analyst role requiring SQL, Python, dashboards, communication, problem solving, stakeholder support, and clear reporting."
                _wz132_store_job("Junior Data Analyst", demo_jd, "Demo Company")
                st.session_state["onboarding_step_final"] = 3
                try: request_scroll_to_top()
                except Exception: pass
                st.rerun()
        st.markdown('</div></div>', unsafe_allow_html=True)
        return

    if step == 2:
        st.markdown('<section class="wz132-hero"><div class="wz132-kicker">Add your target role</div><h1>Make the interview specific to the job</h1><p>Paste one real job description so WorkZo can challenge you on the exact skills, gaps, language expectations, and recruiter pressure points.</p></section>', unsafe_allow_html=True)
        with st.container(border=True):
            title = st.text_input("Job title", value=st.session_state.get("target_role", ""), placeholder="Example: Data Analyst", key="wz132_job_title")
            company = st.text_input("Company / employer (optional)", value=st.session_state.get("selected_company", ""), placeholder="Example: Siemens", key="wz132_company")
            jd = st.text_area("Job description", height=220, value=st.session_state.get("selected_job_description") or st.session_state.get("current_job_description") or "", placeholder="Paste the job description here...", key="wz132_jd")
        c1, c2, c3 = st.columns([1,1,1])
        with c1:
            if st.button("Back", use_container_width=True, key="wz132_back_to_cv"):
                st.session_state["onboarding_step_final"] = 1
                st.rerun()
        with c2:
            if st.button("Use demo job", use_container_width=True, key="wz132_demo_job"):
                demo_jd = SAMPLE_JOB_DESCRIPTION if "SAMPLE_JOB_DESCRIPTION" in globals() else "Demo job description: Junior Data Analyst role requiring SQL, Python, dashboards, communication and stakeholder collaboration."
                _wz132_store_job("Junior Data Analyst", demo_jd, "Demo Company")
                st.session_state["onboarding_step_final"] = 3
                st.rerun()
        with c3:
            if st.button("Continue to interview room", type="primary", use_container_width=True, key="wz132_continue_job"):
                if _wz132_store_job(title, jd, company):
                    st.session_state["onboarding_step_final"] = 3
                    st.rerun()
                else:
                    st.warning("Please paste the job description, or use the demo job.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    job = st.session_state.get("selected_job") or {}
    job_title_ready = html.escape(str(job.get("title") or st.session_state.get("target_role") or "Target role"))
    company_ready = html.escape(str(job.get("company") or "Target company"))
    st.markdown(
        '<section class="wz138-ready-hero"><div class="wz138-ready-copy"><div class="wz138-kicker">Interview room ready</div><h1>AI recruiter is ready for you</h1><p>Your CV and target job are loaded. WorkZo is preparing recruiter-style follow-ups, pressure prompts, and a hiring-style decision.</p><div class="wz138-tags"><span>CV understood</span><span>Job context loaded</span><span>Follow-ups enabled</span></div></div><div class="wz138-recruiter-prep"><div class="wz138-prep-top"><div class="wz138-avatar">🎙️</div><div><b>AI Recruiter</b><span>Preparing your interview</span></div><strong>LIVE</strong></div><div class="wz138-prep-line"><span></span>Preparing follow-up questions<div class="wz138-dots"><i></i><i></i><i></i></div></div><div class="wz138-prep-line"><span></span>Analyzing measurable-impact gaps</div><div class="wz138-prep-line"><span></span>Setting pressure level: realistic</div><div class="wz138-wave"><i></i><i></i><i></i><i></i><i></i></div></div></section>',
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns([1, 1])
    with c1:
        _wz132_render_cv_understood()
    with c2:
        st.markdown('<div class="wz132-ai-read"><div class="wz132-ai-title">🎯 Job context ready</div>' + f'<div class="wz132-scan-row"><span class="wz132-pill">Role: {job_title_ready}</span><span class="wz132-pill">Company: {company_ready}</span><span class="wz132-pill">Recruiter follow-ups enabled</span><span class="wz132-pill">Hiring-decision feedback enabled</span></div></div>', unsafe_allow_html=True)
    if st.button("Start Real Interview", type="primary", use_container_width=True, key="wz138_start_interview"):
        st.session_state["onboarding_complete"] = True
        try:
            queue_navigation("workobot")
        except Exception:
            st.session_state["nav_page"] = "workobot"
            st.session_state["page"] = "workobot"
        st.rerun()
    st.caption("Need to change something? Use the Back button in the header or edit setup later.")
    st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# WorkZo v139 - FORCE active onboarding single-CTA immersive flow
# This final override is deliberately placed at the very end of the file.
# It does not render any Open Dashboard button. The only Step 3 CTA is
# Start Real Interview.
# =========================================================

def _wz139_go_to_interview():
    try:
        st.session_state["onboarding_complete"] = True
        st.session_state["nav_page"] = "workobot"
        st.session_state["page"] = "workobot"
        st.session_state["workobot_mode"] = "real_interview"
        st.session_state["start_real_interview_now"] = True
        if callable(globals().get("queue_navigation")):
            queue_navigation("workobot")
        st.rerun()
    except Exception:
        st.session_state["onboarding_complete"] = True
        st.session_state["nav_page"] = "workobot"
        st.session_state["page"] = "workobot"
        st.rerun()


def _wz139_css():
    st.markdown("""
    <style id="workzo-v139-force-single-cta-css">
    [data-testid="stMainBlockContainer"], .block-container{
        max-width:1080px!important;
        padding-top:.25rem!important;
        padding-bottom:1.2rem!important;
    }
    .wz139-header{
        max-width:1080px;margin:.05rem auto .42rem!important;
        padding:.48rem .72rem!important;border:1px solid rgba(34,211,238,.30);
        border-radius:17px;background:linear-gradient(135deg,rgba(8,47,73,.78),rgba(15,23,42,.92));
        box-shadow:0 14px 42px rgba(2,6,23,.25);display:flex;align-items:center;justify-content:space-between;gap:.8rem;
    }
    .wz139-brand{display:flex;align-items:center;gap:.68rem}.wz139-logo{width:42px;height:42px;border-radius:13px;object-fit:cover;box-shadow:0 10px 28px rgba(14,165,233,.20)}
    .wz139-logo-fallback{display:grid;place-items:center;background:linear-gradient(135deg,#22d3ee,#2563eb);color:#fff;font-weight:950}
    .wz139-title{font-size:1.2rem;font-weight:950;color:#fff;letter-spacing:-.04em;line-height:1}.wz139-title span{color:#22d3ee}.wz139-sub{font-size:.72rem;color:#cbd5e1;font-weight:800;margin-top:.16rem}
    .wz139-right{display:flex;align-items:center;gap:.62rem}.wz139-back{border:1px solid rgba(148,163,184,.22);background:rgba(15,23,42,.55);color:#e0f2fe;border-radius:999px;padding:.36rem .62rem;font-weight:900;font-size:.78rem;cursor:pointer}
    .wz139-status{min-width:226px}.wz139-status-top{display:flex;justify-content:space-between;gap:.8rem;font-size:.72rem;font-weight:900;margin-bottom:.24rem}.wz139-status-top span{color:#cbd5e1}.wz139-status-top b{color:#67e8f9}
    .wz139-line{height:5px;border-radius:99px;background:rgba(148,163,184,.18);overflow:hidden}.wz139-line i{display:block;height:100%;background:linear-gradient(90deg,#22d3ee,#22c55e);border-radius:99px;box-shadow:0 0 18px rgba(34,211,238,.35)}
    .wz139-mini{display:flex;gap:.3rem;margin-top:.25rem}.wz139-mini span{border:1px solid rgba(148,163,184,.18);background:rgba(15,23,42,.52);color:#cbd5e1;border-radius:999px;padding:.15rem .34rem;font-size:.61rem;font-weight:950}.wz139-mini span.done{border-color:rgba(34,211,238,.35);background:rgba(14,165,233,.14);color:#67e8f9}
    .wz139-beta{border:1px solid rgba(34,211,238,.42);background:rgba(14,165,233,.13);color:#67e8f9;border-radius:999px;padding:.30rem .52rem;font-size:.64rem;font-weight:950;letter-spacing:.04em}
    .wz139-shell{max-width:1080px;margin:0 auto!important}.wz139-topline{display:flex;align-items:center;gap:.5rem;margin:.18rem 0 .38rem!important}.wz139-step{font-size:.80rem;font-weight:950;color:#f8fafc;white-space:nowrap}.wz139-trust{display:inline-flex;align-items:center;border:1px solid rgba(34,211,238,.22);background:rgba(20,184,166,.09);color:#dffeff;border-radius:999px;padding:.19rem .46rem!important;font-size:.68rem!important;font-weight:850;line-height:1.15!important;opacity:.84;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100%}
    .wz139-progress{display:grid;grid-template-columns:repeat(3,1fr);gap:.5rem;margin:.20rem 0 .52rem}.wz139-progress-card{position:relative;border:1px solid rgba(34,211,238,.26);background:rgba(15,23,42,.40);border-radius:15px;padding:.55rem .72rem;display:flex;align-items:center;gap:.46rem;color:#e0f2fe;font-weight:950;font-size:.82rem;min-height:48px}.wz139-progress-card.done{background:rgba(20,184,166,.10);border-color:rgba(45,212,191,.38)}.wz139-progress-card.active{background:rgba(14,165,233,.11);border-color:rgba(14,165,233,.55)}.wz139-num{width:25px;height:25px;border-radius:999px;display:grid;place-items:center;background:rgba(14,165,233,.18);border:1px solid rgba(34,211,238,.30);color:#67e8f9;font-size:.72rem}.wz139-progress-card.done .wz139-num{background:rgba(20,184,166,.22);color:#ccfbf1}.wz139-progress-card:not(:last-child):after{content:'';position:absolute;right:-.50rem;top:50%;width:.5rem;height:1px;background:rgba(34,211,238,.20)}
    .wz139-hero{border:1px solid rgba(34,211,238,.28);background:radial-gradient(circle at 0 0,rgba(34,211,238,.22),transparent 30%),linear-gradient(135deg,rgba(8,47,73,.70),rgba(15,23,42,.92));border-radius:21px;padding:.92rem 1.02rem!important;min-height:0!important;margin:.22rem 0 .70rem!important;box-shadow:0 16px 50px rgba(2,6,23,.28)}
    .wz139-kicker{font-size:.66rem;text-transform:uppercase;letter-spacing:.18em;color:#67e8f9;font-weight:950;margin-bottom:.36rem}.wz139-hero h1{font-size:clamp(1.55rem,3vw,2.32rem)!important;line-height:1.02!important;margin:.08rem 0 .42rem!important;color:#fff;letter-spacing:-.055em}.wz139-hero p{color:#dbeafe;font-size:.92rem;line-height:1.42;max-width:760px;margin:0}
    .wz139-ready-hero{display:grid;grid-template-columns:minmax(0,1.12fr) minmax(320px,.88fr);gap:.9rem;align-items:center;border:1px solid rgba(34,211,238,.28);background:radial-gradient(circle at 0 0,rgba(34,211,238,.22),transparent 30%),linear-gradient(135deg,rgba(8,47,73,.72),rgba(15,23,42,.92));border-radius:21px;padding:1.02rem!important;margin:.20rem 0 .72rem!important;box-shadow:0 18px 54px rgba(2,6,23,.30)}
    .wz139-ready-copy h1{font-size:clamp(1.62rem,3.2vw,2.42rem)!important;line-height:1.02!important;margin:.1rem 0 .44rem!important;color:#fff;letter-spacing:-.06em}.wz139-ready-copy p{font-size:.92rem;line-height:1.42;color:#dbeafe;margin:0;max-width:650px}.wz139-tags{display:flex;flex-wrap:wrap;gap:.36rem;margin-top:.62rem}.wz139-tags span{border:1px solid rgba(148,163,184,.18);background:rgba(15,23,42,.50);border-radius:999px;padding:.27rem .48rem;color:#cbd5e1;font-weight:850;font-size:.70rem}
    .wz139-prep{border:1px solid rgba(34,211,238,.26);background:rgba(2,6,23,.48);border-radius:18px;padding:.78rem;box-shadow:inset 0 0 28px rgba(34,211,238,.045)}.wz139-prep-top{display:flex;align-items:center;gap:.55rem;margin-bottom:.55rem}.wz139-avatar{width:38px;height:38px;border-radius:14px;display:grid;place-items:center;background:linear-gradient(135deg,#0891b2,#2563eb);box-shadow:0 0 24px rgba(34,211,238,.24);animation:wz139Pulse 1.9s ease-in-out infinite}.wz139-prep-top b{display:block;color:#fff;font-size:.86rem}.wz139-prep-top span{display:block;color:#94a3b8;font-size:.70rem}.wz139-prep-top strong{margin-left:auto;color:#22c55e;border:1px solid rgba(34,197,94,.30);background:rgba(34,197,94,.10);border-radius:999px;padding:.18rem .38rem;font-size:.58rem}.wz139-prep-line{display:flex;align-items:center;gap:.42rem;color:#dbeafe;font-size:.75rem;font-weight:850;padding:.25rem 0;border-top:1px solid rgba(148,163,184,.08)}.wz139-prep-line>span{width:7px;height:7px;border-radius:99px;background:#22d3ee;box-shadow:0 0 12px rgba(34,211,238,.75)}.wz139-dots{display:inline-flex;gap:.18rem;margin-left:.15rem}.wz139-dots i{width:4px;height:4px;border-radius:99px;background:#67e8f9;animation:wz139Dot 1s infinite}.wz139-dots i:nth-child(2){animation-delay:.16s}.wz139-dots i:nth-child(3){animation-delay:.32s}.wz139-wave{height:25px;display:flex;align-items:end;gap:4px;margin-top:.42rem;border-top:1px solid rgba(148,163,184,.08);padding-top:.44rem}.wz139-wave i{width:5px;border-radius:99px;background:linear-gradient(180deg,#67e8f9,#2563eb);height:10px;animation:wz139Wave 1.05s ease-in-out infinite}.wz139-wave i:nth-child(2){height:17px;animation-delay:.12s}.wz139-wave i:nth-child(3){height:23px;animation-delay:.24s}.wz139-wave i:nth-child(4){height:14px;animation-delay:.36s}.wz139-wave i:nth-child(5){height:20px;animation-delay:.48s}
    .wz139-grid{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(300px,.85fr);gap:.8rem}.wz139-card{border:1px solid rgba(34,211,238,.28);background:rgba(15,23,42,.44);border-radius:18px;padding:.9rem;box-shadow:0 14px 42px rgba(2,6,23,.20)}.wz139-card-title{font-size:1rem;color:#fff;font-weight:950;margin-bottom:.42rem}.wz139-pillrow{display:flex;gap:.35rem;flex-wrap:wrap}.wz139-pill{border:1px solid rgba(148,163,184,.18);background:rgba(15,23,42,.54);color:#dbeafe;border-radius:999px;padding:.25rem .45rem;font-size:.72rem;font-weight:850}.wz139-ai-title{font-size:1rem;font-weight:950;color:#fff;margin-bottom:.48rem}.wz139-scan{border:1px dashed rgba(34,211,238,.35);background:rgba(34,211,238,.055);border-radius:16px;padding:.68rem;margin:.55rem 0;animation:wz139DashPulse 2.2s ease-in-out infinite}.wz139-scan-title{font-weight:950;color:#fff;margin-bottom:.28rem}.wz139-scan-line{color:#bfdbfe;font-size:.76rem;padding:.12rem 0}.wz139-demo{background:radial-gradient(circle at top right,rgba(34,211,238,.12),transparent 38%),rgba(15,23,42,.46)}.wz139-demo-bubble{border:1px solid rgba(148,163,184,.14);background:rgba(2,6,23,.36);border-radius:13px;padding:.48rem .58rem;color:#dbeafe;font-size:.78rem;margin-top:.46rem}.wz139-demo-bubble.warn{border-color:rgba(251,191,36,.26);background:rgba(251,191,36,.07);color:#fde68a}.wz139-note{font-size:.72rem;color:#94a3b8;margin-top:.52rem;line-height:1.35}
    .st-key-wz139_start_interview button{min-height:66px!important;border-radius:22px!important;font-size:1.08rem!important;font-weight:950!important;letter-spacing:-.01em!important;background:radial-gradient(circle at 18% 10%,rgba(103,232,249,.52),transparent 34%),linear-gradient(135deg,#020617,#0369a1,#1d4ed8)!important;border:1px solid rgba(125,211,252,.70)!important;color:#f8fafc!important;box-shadow:0 0 0 1px rgba(125,211,252,.28),0 0 36px rgba(34,211,238,.30),0 26px 84px rgba(37,99,235,.42)!important;animation:wz139StartPulse 2.1s ease-in-out infinite!important}.st-key-wz139_start_interview button:before{content:'🎙 ';display:inline-block;animation:wz139Mic 1.55s ease-in-out infinite}.st-key-wz139_start_interview button:hover{transform:translateY(-3px) scale(1.012)!important;box-shadow:0 0 0 1px rgba(125,211,252,.38),0 0 46px rgba(34,211,238,.40),0 32px 92px rgba(37,99,235,.50)!important}
    @keyframes wz139Pulse{0%,100%{transform:scale(1);filter:brightness(1)}50%{transform:scale(1.05);filter:brightness(1.16)}}@keyframes wz139Dot{0%,80%,100%{opacity:.28;transform:translateY(0)}40%{opacity:1;transform:translateY(-2px)}}@keyframes wz139Wave{0%,100%{transform:scaleY(.72);opacity:.65}50%{transform:scaleY(1.22);opacity:1}}@keyframes wz139DashPulse{0%,100%{border-color:rgba(34,211,238,.25);box-shadow:0 0 0 rgba(34,211,238,0)}50%{border-color:rgba(34,211,238,.55);box-shadow:0 0 22px rgba(34,211,238,.10)}}@keyframes wz139StartPulse{0%,100%{filter:brightness(1)}50%{filter:brightness(1.14)}}@keyframes wz139Mic{0%,100%{transform:translateY(0) rotate(0)}50%{transform:translateY(-1px) rotate(-7deg)}}
    @media(max-width:900px){.wz139-header,.wz139-ready-hero,.wz139-grid{grid-template-columns:1fr!important;display:grid}.wz139-header{display:block}.wz139-header-right{margin-top:.7rem;justify-content:space-between}.wz139-status{min-width:0;flex:1}.wz139-trust{white-space:normal}.wz139-ready-hero{padding:.82rem!important}.wz139-progress{grid-template-columns:1fr}.wz139-progress-card:after{display:none}}
    </style>
    """, unsafe_allow_html=True)


def _wz139_header(step=1):
    logo_src = None
    try:
        logo_src = image_to_data_uri(ICON_PATH) or image_to_data_uri(LOGO_PATH)
    except Exception:
        logo_src = None
    logo_html = f"<img src='{logo_src}' class='wz139-logo' alt='WorkZo AI'>" if logo_src else "<div class='wz139-logo wz139-logo-fallback'>WZ</div>"
    status = "Interview Setup Complete" if int(step) >= 3 else "Interview setup"
    progress = "Ready to begin" if int(step) >= 3 else f"Step {int(step)}/3"
    width = "100%" if int(step) >= 3 else ("66%" if int(step) == 2 else "33%")
    st.markdown(f"""
    <div class="wz139-header">
      <div class="wz139-brand">{logo_html}<div><div class="wz139-title">WorkZo <span>AI</span></div><div class="wz139-sub">Your guided AI career system</div></div></div>
      <div class="wz139-right"><button class="wz139-back" onclick="history.back()">← Back</button><div class="wz139-status"><div class="wz139-status-top"><span>{html.escape(status)}</span><b>{html.escape(progress)}</b></div><div class="wz139-line"><i style="width:{width}"></i></div><div class="wz139-mini"><span class="done">✓ CV</span><span class="{'done' if int(step)>=2 else ''}">✓ Jobs</span><span class="{'done' if int(step)>=3 else ''}">3 Interview</span></div></div><div class="wz139-beta">BETA</div></div>
    </div>
    """, unsafe_allow_html=True)


def _wz139_progress(step=1):
    labels = [(1,"Upload CV"),(2,"Add Job Description"),(3,"Start Interview")]
    html_parts=[]
    for n,label in labels:
        cls = "done" if n < step else ("active" if n == step else "")
        num = "✓" if n < step else str(n)
        html_parts.append(f'<div class="wz139-progress-card {cls}"><span class="wz139-num">{num}</span>{html.escape(label)}</div>')
    st.markdown('<div class="wz139-progress">' + ''.join(html_parts) + '</div>', unsafe_allow_html=True)


def _wz139_get_step():
    try:
        step = int(st.session_state.get("onboarding_step_final", st.session_state.get("wz_onboarding_step", 1)) or 1)
    except Exception:
        step = 1
    if step < 1 or step > 3:
        step = 1
    st.session_state["onboarding_step_final"] = step
    return step


def _wz139_store_cv_text(text, source="CV"):
    text = str(text or "").strip()
    if len(text) < 40:
        return False
    for key in ["cv_text","workzo_live_cv_text","clean_structured_cv_text","approved_structured_cv_text"]:
        st.session_state[key] = text
    try:
        st.session_state["wz139_cv_insights"] = _wz132_detect_cv_insights(text) if callable(globals().get("_wz132_detect_cv_insights")) else {}
    except Exception:
        st.session_state["wz139_cv_insights"] = {}
    return True


def _wz139_store_job(title, jd, company=""):
    jd = str(jd or "").strip()
    if len(jd) < 30:
        return False
    title = str(title or st.session_state.get("target_role") or "Target role").strip() or "Target role"
    company = str(company or "Target company").strip() or "Target company"
    st.session_state["target_role"] = title
    st.session_state["selected_company"] = company
    job = {"title": title, "company": company, "description": jd, "location": st.session_state.get("country", "")}
    st.session_state["selected_job"] = job
    for key in ["selected_job_description","current_job_description","last_understand_job_description","last_prepare_job_description","improve_cv_for_job_desc","job_description","interview_jd_text_v117","real_interview_jd_saved"]:
        st.session_state[key] = jd
    return True


def _wz139_render_cv_understood():
    text = str(st.session_state.get("cv_text", "") or "")
    try:
        insights = st.session_state.get("wz139_cv_insights") or (_wz132_detect_cv_insights(text) if callable(globals().get("_wz132_detect_cv_insights")) else {})
    except Exception:
        insights = {}
    if not isinstance(insights, dict):
        insights = {}
    role = html.escape(str(insights.get("role") or st.session_state.get("target_role") or "Experience detected"))
    exp = html.escape(str(insights.get("experience") or "Experience detected"))
    words = int(insights.get("words") or len(text.split()) or 0)
    skills = insights.get("skills") if isinstance(insights.get("skills"), list) else []
    skill_html = ''.join(f'<span class="wz139-pill">{html.escape(str(s))}</span>' for s in skills[:4])
    st.markdown(f'<div class="wz139-card"><div class="wz139-ai-title">✅ CV parsed — Preparing your interview <span class="wz139-dots"><i></i><i></i><i></i></span></div><div class="wz139-pillrow"><span class="wz139-pill">Role: {role}</span><span class="wz139-pill">{exp}</span><span class="wz139-pill">{words} words read</span>{skill_html}</div></div>', unsafe_allow_html=True)


def show_onboarding():
    """Forced final onboarding renderer. No Open Dashboard secondary CTA."""
    try:
        maybe_scroll_to_top()
    except Exception:
        pass
    try:
        apply_workzo_v75_global_css()
    except Exception:
        pass
    _wz139_css()
    step = _wz139_get_step()
    _wz139_header(step)
    st.markdown('<div class="wz139-shell">', unsafe_allow_html=True)
    st.markdown(f'<div class="wz139-topline"><div class="wz139-step">Step {step} of 3</div><div class="wz139-trust">🔒 Your CV is only used to personalize your interview · No account required · We don’t store sensitive resume data · Takes less than 30 seconds</div></div>', unsafe_allow_html=True)
    _wz139_progress(step)

    if step == 1:
        st.markdown('<section class="wz139-hero"><div class="wz139-kicker">Start with your CV</div><h1>Your interview starts with your CV</h1><p>Upload your CV so WorkZo can understand your experience, detect your skills, and prepare realistic recruiter-style interview questions.</p></section>', unsafe_allow_html=True)
        st.markdown('<div class="wz139-grid">', unsafe_allow_html=True)
        left, right = st.columns([1.15, .85])
        with left:
            st.markdown('<div class="wz139-card"><div class="wz139-card-title">Let AI understand your experience</div><p style="color:#cbd5e1;margin-top:0;font-size:.86rem">This is the core step. WorkZo reads your profile so the interview does not feel generic.</p><div class="wz139-scan"><div class="wz139-scan-title">📄 Drop your CV here</div><div class="wz139-scan-line">PDF or TXT works best. You can also paste text below.</div><div class="wz139-scan-line">AI will detect role, skills, experience and interview pressure points.</div></div>', unsafe_allow_html=True)
            uploaded = st.file_uploader("Upload PDF or TXT", type=["pdf", "txt"], key="wz139_cv_upload")
            if uploaded is not None:
                extracted = ""
                try:
                    file_name = str(getattr(uploaded, "name", "") or "").lower()
                    file_type = str(getattr(uploaded, "type", "") or "").lower()
                    if file_type == "text/plain" or file_name.endswith(".txt"):
                        extracted = uploaded.read().decode("utf-8", errors="ignore")
                    else:
                        extracted = extract_pdf_text(uploaded) if callable(globals().get("extract_pdf_text")) else ""
                    if callable(globals().get("organize_cv_for_display")):
                        extracted = organize_cv_for_display(extracted)
                except Exception as exc:
                    st.warning(f"Could not read the uploaded CV: {exc}")
                if _wz139_store_cv_text(extracted, "Upload CV"):
                    _wz139_render_cv_understood()
                    st.markdown('<div class="wz139-scan"><div class="wz139-scan-title">AI is building your interview <span class="wz139-dots"><i></i><i></i><i></i></span></div><div class="wz139-scan-line">Analyzing communication style...</div><div class="wz139-scan-line">Understanding experience level...</div><div class="wz139-scan-line">Generating recruiter pressure prompts...</div><div class="wz139-scan-line">Preparing follow-up questions...</div></div>', unsafe_allow_html=True)
                else:
                    st.warning("The file uploaded, but the extracted text looked too short. Try TXT or paste your CV below.")
            with st.expander("Paste CV text instead", expanded=not bool(st.session_state.get("cv_text"))):
                pasted = st.text_area("Paste your CV text", height=145, key="wz139_paste_cv_text", placeholder="Paste your resume text here...")
                if st.button("Use pasted CV", key="wz139_use_pasted_cv", use_container_width=True):
                    if _wz139_store_cv_text(pasted, "Paste CV"):
                        _wz139_render_cv_understood()
                        st.markdown('<div class="wz139-scan"><div class="wz139-scan-title">AI is building your interview <span class="wz139-dots"><i></i><i></i><i></i></span></div><div class="wz139-scan-line">Analyzing communication style...</div><div class="wz139-scan-line">Understanding experience level...</div><div class="wz139-scan-line">Generating recruiter pressure prompts...</div><div class="wz139-scan-line">Preparing follow-up questions...</div></div>', unsafe_allow_html=True)
                    else:
                        st.warning("Please paste more CV details first.")
            st.markdown('<div class="wz139-note">Your CV is only used to personalize your interview. We don’t store sensitive resume data in analytics.</div>', unsafe_allow_html=True)
            if st.session_state.get("cv_text"):
                if st.button("Continue to interview setup →", type="primary", use_container_width=True, key="wz139_continue_cv"):
                    st.session_state["onboarding_step_final"] = 2
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with right:
            st.markdown('<div class="wz139-card wz139-demo"><div class="wz139-card-title">Experience the interview instantly</div><p style="color:#cbd5e1;font-size:.84rem;margin-top:0">Not ready to upload? Try a sample CV and feel how WorkZo challenges answers.</p><div class="wz139-prep" style="margin-top:.55rem"><div class="wz139-prep-top"><div class="wz139-avatar">🤖</div><div><b>AI Recruiter</b><span>Demo pressure round</span></div><strong>00:45</strong></div><div class="wz139-demo-bubble">Tell me about yourself — but keep it relevant.</div><div class="wz139-demo-bubble warn">⚠️ You’re losing me — give me one measurable result.</div><div class="wz139-wave"><i></i><i></i><i></i><i></i><i></i></div></div><div class="wz139-note">Best for testers who want to feel the product before sharing a CV.</div></div>', unsafe_allow_html=True)
            if st.button("Experience demo interview", use_container_width=True, key="wz139_demo_cv"):
                demo_cv = SAMPLE_CV_TEXT if "SAMPLE_CV_TEXT" in globals() else "Demo CV: Technical Support Engineer with customer-facing experience, SQL, Python, dashboards, troubleshooting, communication skills, and experience handling customer issues."
                _wz139_store_cv_text(demo_cv, "Sample Demo")
                demo_jd = SAMPLE_JOB_DESCRIPTION if "SAMPLE_JOB_DESCRIPTION" in globals() else "Demo job description: Junior Data Analyst role requiring SQL, Python, dashboards, communication, problem solving, stakeholder support, and clear reporting."
                _wz139_store_job("Junior Data Analyst", demo_jd, "Demo Company")
                st.session_state["onboarding_step_final"] = 3
                st.rerun()
        st.markdown('</div></div>', unsafe_allow_html=True)
        return

    if step == 2:
        st.markdown('<section class="wz139-hero"><div class="wz139-kicker">Add your target role</div><h1>Make the interview specific to the job</h1><p>Paste one real job description so WorkZo can challenge you on exact skills, gaps, language expectations, and recruiter pressure points.</p></section>', unsafe_allow_html=True)
        with st.container(border=True):
            title = st.text_input("Job title", value=st.session_state.get("target_role", ""), placeholder="Example: Data Analyst", key="wz139_job_title")
            company = st.text_input("Company / employer (optional)", value=st.session_state.get("selected_company", ""), placeholder="Example: Siemens", key="wz139_company")
            jd = st.text_area("Job description", height=190, value=st.session_state.get("selected_job_description") or st.session_state.get("current_job_description") or "", placeholder="Paste the job description here...", key="wz139_jd")
        b1,b2,b3 = st.columns([1,1,1])
        with b1:
            if st.button("Back", use_container_width=True, key="wz139_back_to_cv"):
                st.session_state["onboarding_step_final"] = 1
                st.rerun()
        with b2:
            if st.button("Use demo job", use_container_width=True, key="wz139_demo_job"):
                demo_jd = SAMPLE_JOB_DESCRIPTION if "SAMPLE_JOB_DESCRIPTION" in globals() else "Demo job description: Junior Data Analyst role requiring SQL, Python, dashboards, communication and stakeholder collaboration."
                _wz139_store_job("Junior Data Analyst", demo_jd, "Demo Company")
                st.session_state["onboarding_step_final"] = 3
                st.rerun()
        with b3:
            if st.button("Continue to interview room →", type="primary", use_container_width=True, key="wz139_continue_job"):
                if _wz139_store_job(title, jd, company):
                    st.session_state["onboarding_step_final"] = 3
                    st.rerun()
                else:
                    st.warning("Please paste the job description, or use the demo job.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    job = st.session_state.get("selected_job") or {}
    job_title = html.escape(str(job.get("title") or st.session_state.get("target_role") or "Target role"))
    company = html.escape(str(job.get("company") or st.session_state.get("selected_company") or "Target company"))
    st.markdown('<section class="wz139-ready-hero"><div class="wz139-ready-copy"><div class="wz139-kicker">Interview room ready</div><h1>AI recruiter is ready for you</h1><p>Your CV and target job are loaded. WorkZo is preparing recruiter-style follow-ups, pressure prompts, and a hiring-style decision.</p><div class="wz139-tags"><span>CV understood</span><span>Job context loaded</span><span>Follow-ups enabled</span></div></div><div class="wz139-prep"><div class="wz139-prep-top"><div class="wz139-avatar">🎙️</div><div><b>AI Recruiter</b><span>Preparing your interview</span></div><strong>LIVE</strong></div><div class="wz139-prep-line"><span></span>Preparing follow-up questions <div class="wz139-dots"><i></i><i></i><i></i></div></div><div class="wz139-prep-line"><span></span>Analyzing measurable-impact gaps</div><div class="wz139-prep-line"><span></span>Pressure level: realistic</div><div class="wz139-prep-line"><span></span>Voice room: ready</div><div class="wz139-wave"><i></i><i></i><i></i><i></i><i></i></div></div></section>', unsafe_allow_html=True)
    st.markdown('<div class="wz139-grid">', unsafe_allow_html=True)
    left, right = st.columns(2)
    with left:
        _wz139_render_cv_understood()
    with right:
        st.markdown(f'<div class="wz139-card"><div class="wz139-ai-title">🎯 Job context ready</div><div class="wz139-pillrow"><span class="wz139-pill">Role: {job_title}</span><span class="wz139-pill">Company: {company}</span><span class="wz139-pill">Recruiter follow-ups enabled</span><span class="wz139-pill">Hiring-decision feedback enabled</span></div></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    if st.button("Start Real Interview", type="primary", use_container_width=True, key="wz139_start_interview"):
        _wz139_go_to_interview()
    st.caption("Need to change something? Use the Back button in the header or edit setup later.")
    st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# WorkZo v152 - Mobile landing polish
# - smaller header footprint
# - compact hero typography and proof pills
# - less intrusive floating widgets on mobile
# - tighter cards and sticky mobile CTA
# =========================================================

def _wz152_mobile_landing_css():
    try:
        st.markdown(r"""
        <style id="workzo-v152-mobile-landing-polish-css">
        @media (max-width: 760px){
            [data-testid="stMainBlockContainer"], .block-container{
                padding-top:.25rem!important;
                padding-left:.78rem!important;
                padding-right:.78rem!important;
                padding-bottom:5.2rem!important;
            }
            .workzo-header,.workzo-topbar,.workzo-brand-shell,.workzo-brand-card,
            .wzfinal-top,.wzflow-brand,.wz128-topbar,.wz130-topbar{
                margin:.15rem 0 .42rem 0!important;
                padding:.42rem .55rem!important;
                min-height:0!important;
                border-radius:16px!important;
                gap:.46rem!important;
            }
            .workzo-header img,.workzo-topbar img,.workzo-brand-card img,
            .wzfinal-top img,.wzflow-brand img,.wz128-topbar img,.wz130-topbar img,
            .workzo-logo,img[alt*="WorkZo"],img[alt*="logo"]{
                max-width:42px!important;
                max-height:42px!important;
                width:42px!important;
                height:42px!important;
                border-radius:12px!important;
            }
            .workzo-header h1,.workzo-topbar h1,.workzo-brand-card h1,
            .wzfinal-top h1,.wzflow-brand h1{
                font-size:1.05rem!important;
                line-height:1.05!important;
                margin:0!important;
            }
            .workzo-header p,.workzo-topbar p,.workzo-brand-card p,
            .wzfinal-top p,.wzflow-brand p{
                font-size:.72rem!important;
                line-height:1.05!important;
                margin:.08rem 0 0!important;
                max-width:160px!important;
                white-space:nowrap!important;
                overflow:hidden!important;
                text-overflow:ellipsis!important;
            }
            .wz130-hero{
                margin:.38rem .15rem .72rem!important;
                padding:.92rem .78rem 1rem!important;
                border-radius:22px!important;
            }
            .wz130-hero-inner{gap:.72rem!important;}
            .wz130-kicker{
                font-size:.68rem!important;
                letter-spacing:.12em!important;
                margin-bottom:.28rem!important;
            }
            .wz130-title{
                font-size:clamp(2.05rem, 10.4vw, 2.75rem)!important;
                line-height:1.02!important;
                letter-spacing:-.055em!important;
                margin:.08rem 0 .56rem!important;
            }
            .wz130-subtitle{
                font-size:.94rem!important;
                line-height:1.42!important;
                margin:.22rem 0 .64rem!important;
                max-width:100%!important;
            }
            .wz130-proof-line{
                padding:.46rem .58rem!important;
                font-size:.78rem!important;
                line-height:1.22!important;
                margin:.52rem 0 .58rem!important;
                border-radius:14px!important;
            }
            .wz130-proof-row{
                display:grid!important;
                grid-template-columns:1fr 1fr!important;
                gap:.42rem!important;
                margin:.55rem 0 .15rem!important;
            }
            .wz130-proof-pill{
                width:100%!important;
                justify-content:center!important;
                padding:.46rem .46rem!important;
                font-size:.72rem!important;
                line-height:1.12!important;
                border-radius:999px!important;
                min-height:34px!important;
                white-space:normal!important;
                text-align:center!important;
            }
            .wz130-proof-pill:nth-child(3){grid-column:1 / -1!important;}
            .wz130-preview{
                padding:.72rem!important;
                border-radius:20px!important;
                margin-top:.38rem!important;
            }
            .wz130-preview-top{
                margin-bottom:.54rem!important;
                gap:.5rem!important;
                padding-right:2rem!important;
            }
            .wz130-avatar{width:36px!important;height:36px!important;border-radius:13px!important;font-size:1rem!important;}
            .wz130-rec-name{font-size:.88rem!important;}
            .wz130-rec-status{font-size:.68rem!important;max-width:150px!important;white-space:nowrap!important;overflow:hidden!important;text-overflow:ellipsis!important;}
            .wz130-timer{font-size:.72rem!important;min-width:50px!important;padding:.28rem .44rem!important;}
            .wz130-chat-bubble{
                padding:.58rem .66rem!important;
                margin:.38rem 0!important;
                font-size:.78rem!important;
                line-height:1.32!important;
                border-radius:15px!important;
            }
            .wz130-chat-bubble.user{margin-left:1rem!important;}
            .wz130-wave{height:24px!important;margin:.34rem 0 .22rem!important;}
            .wz130-listening{padding:.48rem .56rem!important;font-size:.72rem!important;border-radius:14px!important;margin-top:.4rem!important;}
            .wz130-meter{margin:.42rem 0 .24rem!important;}
            .wz130-feedback-mini,.wz130-tag{display:none!important;}
            .st-key-wz130_landing_start{
                position:fixed!important;
                left:12px!important;
                right:12px!important;
                bottom:12px!important;
                z-index:999990!important;
                margin:0!important;
                padding:0!important;
            }
            .st-key-wz130_landing_start button{
                width:100%!important;
                min-height:54px!important;
                border-radius:18px!important;
                padding:.72rem .95rem!important;
                font-size:.98rem!important;
                box-shadow:0 14px 40px rgba(14,165,233,.36),0 0 28px rgba(34,211,238,.22)!important;
                transform:none!important;
            }
            .st-key-wz130_landing_start button p{font-size:.98rem!important;}
            .st-key-wz130_landing_start button:active{transform:scale(.985)!important;}
            .wz130-flow{
                margin:.65rem .15rem 0!important;
                gap:.48rem!important;
            }
            .wz130-step{
                min-height:auto!important;
                padding:.72rem .78rem!important;
                border-radius:16px!important;
                display:grid!important;
                grid-template-columns:34px 1fr!important;
                column-gap:.55rem!important;
                align-items:start!important;
            }
            .wz130-step:before{display:none!important;}
            .wz130-step-icon{font-size:1.14rem!important;margin:0!important;line-height:1.2!important;}
            .wz130-step span{font-size:.78rem!important;line-height:1.26!important;margin-top:.12rem!important;}
            .st-key-wz141_float_workobot,
            .wz-floating-chat,
            .wz-floating-feedback,
            .wz-feedback-float,
            .wz-beta-float,
            [class*="floating"][class*="bot"],
            [class*="floating"][class*="feedback"]{
                display:none!important;
                pointer-events:none!important;
            }
        }
        </style>
        """, unsafe_allow_html=True)
    except Exception:
        pass

try:
    _wz152_previous_show_landing_page = show_landing_page
    def show_landing_page():
        try:
            _wz152_mobile_landing_css()
        except Exception:
            pass
        return _wz152_previous_show_landing_page()
except Exception:
    pass

try:
    _wz152_mobile_landing_css()
except Exception:
    pass


# =========================================================
# WorkZo v154 - Onboarding must open the main recruiter dashboard
# Fixes: Start Real Interview after onboarding must NOT route to Work-O-Bot.
# =========================================================

def _wz139_go_to_interview():
    """Final onboarding CTA route: open the main Real Interview dashboard."""
    try:
        st.session_state["onboarding_complete"] = True
        st.session_state["nav_page"] = "real_interview"
        st.session_state["page"] = "real_interview"
        st.session_state["_wz_force_page"] = "real_interview"
        st.session_state["_wz154_after_onboarding_main"] = True
        # Clear stale Work-O-Bot flags left from earlier versions.
        for _k in ["workobot_mode", "start_real_interview_now", "_wz_force_workobot", "_wz_allow_workobot_route"]:
            try:
                st.session_state.pop(_k, None)
            except Exception:
                pass
        try:
            st.query_params["page"] = "real_interview"
        except Exception:
            pass
        if callable(globals().get("queue_navigation")):
            queue_navigation("real_interview")
        st.rerun()
    except Exception:
        st.session_state["onboarding_complete"] = True
        st.session_state["nav_page"] = "real_interview"
        st.session_state["page"] = "real_interview"
        st.session_state["_wz_force_page"] = "real_interview"
        st.session_state["_wz154_after_onboarding_main"] = True
        try:
            st.query_params["page"] = "real_interview"
        except Exception:
            pass
        st.rerun()

# Some older onboarding CTA blocks call queue_navigation('workobot') directly.
# This safety wrapper converts that specific onboarding/start-interview intent to real_interview.
try:
    _wz154_previous_queue_navigation = queue_navigation
    def queue_navigation(page_key: str) -> None:
        target = str(page_key or "").strip().lower()
        if target in {"workobot", "work-o-bot", "work_o_bot", "bot"} and bool(st.session_state.get("onboarding_step_final") == 3):
            page_key = "real_interview"
            st.session_state["_wz154_after_onboarding_main"] = True
            st.session_state["_wz_force_page"] = "real_interview"
            st.session_state["nav_page"] = "real_interview"
            st.session_state["page"] = "real_interview"
            try:
                st.query_params["page"] = "real_interview"
            except Exception:
                pass
        return _wz154_previous_queue_navigation(page_key)
except Exception:
    pass
