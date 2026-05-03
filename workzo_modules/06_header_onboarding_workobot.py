

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
                <div class="workzo-progress-top"><span>{stage}</span><span>{progress_pct}%</span></div>
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

Rules:
1. Answer in {answer_lang}.
2. Be practical and specific.
3. Be honest. Do not invent experience, employers, dates, degrees, certifications, achievements, salary, company facts, or language level.
4. If company-specific information is missing, say what to verify instead of pretending.
5. If the user's CV or job description is missing, ask for it or explain the limitation.
6. Give concise steps and copy-ready examples when useful.
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
