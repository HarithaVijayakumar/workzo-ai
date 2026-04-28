

# =========================================================
# WorkZo split-module shared UI helpers
# Added by fix_workzo_split_modules.py
# =========================================================
import os
import base64
import streamlit as st
import streamlit.components.v1 as components

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
    """Scroll Streamlit page to the top when navigation changes."""
    try:
        should_scroll = st.session_state.pop("_workzo_scroll_to_top", True)
    except Exception:
        should_scroll = True
    if not should_scroll:
        return
    try:
        components.html(
            """
            <script>
            const forceTop = () => {
                try {
                    window.parent.scrollTo({top: 0, left: 0, behavior: 'auto'});
                    const doc = window.parent.document;
                    const targets = [
                        doc.documentElement,
                        doc.body,
                        doc.querySelector('[data-testid="stAppViewContainer"]'),
                        doc.querySelector('[data-testid="stMain"]'),
                        doc.querySelector('[data-testid="stMainBlockContainer"]')
                    ].filter(Boolean);
                    for (const t of targets) { try { t.scrollTop = 0; } catch(e) {} }
                } catch(e) {}
            };
            forceTop();
            setTimeout(forceTop, 80);
            setTimeout(forceTop, 250);
            </script>
            """,
            height=0,
            width=0,
        )
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
import streamlit.components.v1 as components


def maybe_scroll_to_top():
    """
    Scroll the page to the top when navigation changes.
    Prevents Streamlit from showing the middle of the page.
    """
    components.html(
        """
        <script>
        window.scrollTo({top: 0, behavior: 'instant'});
        </script>
        """,
        height=0,
    )

ICON_PATH = "assets/workzo_icon.png"
LOGO_PATH = "assets/workzo_logo.png"

def image_to_data_uri(image_path: str):
    ...

def render_workzo_header():
    ...
def render_workzo_header() -> None:
    """Premium SaaS-style product header for WorkZo.

    The logo/brand acts like a Home button by linking to the dashboard URL state.
    """
    logo_src = image_to_data_uri(ICON_PATH) or image_to_data_uri(LOGO_PATH)
    logo_html = f'<img src="{logo_src}" class="workzo-logo" alt="WorkZo AI logo">' if logo_src else '<div class="workzo-logo-fallback"></div>'
    subtitle = html.escape(txt("title"))
    home_href = "?page=dashboard&home=1"
    st.markdown(f"""
    <div class="workzo-header">
        <a class="workzo-brand workzo-home-link" href="{home_href}" target="_self" title="Go to dashboard">
            {logo_html}
            <div>
                <div class="workzo-title">WorkZo <span>AI</span></div>
                <div class="workzo-subtitle">{subtitle}</div>
            </div>
        </a>
        <div class="workzo-beta">BETA</div>
    </div>
    """, unsafe_allow_html=True)


# =========================================================
# SAMPLE DATA DEMO FLOW
# =========================================================
SAMPLE_CV_TEXT = """
ALEX MORGAN
Junior Data Analyst | IT Support Analyst
Berlin, Germany | alex.morgan@example.com | +49 151 00000000 | linkedin.com/in/alexmorgan-demo

PROFESSIONAL SUMMARY
Junior Data Analyst with hands-on experience in Python, SQL, Tableau, Excel, and technical support operations. Experienced in analyzing support data, creating dashboards, documenting processes, and translating technical issues into clear business insights. Interested in roles that combine data analysis, reporting, process improvement, and customer-facing problem solving.

CORE SKILLS
Python, SQL, Excel, Tableau, Power BI, pandas, Data Cleaning, Data Visualization, Dashboard Development, Technical Support, Ticket Analysis, Incident Management, Root Cause Analysis, Process Documentation, Stakeholder Communication

PROFESSIONAL EXPERIENCE
IT Support Specialist | BrightDesk Solutions | 2021 - 2023
- Resolved software and account-related support requests for business users through ticketing and remote troubleshooting.
- Analyzed recurring support tickets to identify common issues and recommend process improvements.
- Created internal documentation that helped reduce repeated questions and improved handover quality.
- Collaborated with product and operations teams to report bugs, clarify user needs, and improve support workflows.

Customer Support Analyst | Northstar Digital Services | 2019 - 2021
- Supported customers with onboarding, product usage questions, and technical troubleshooting.
- Used Excel and basic SQL reports to track issue trends, customer requests, and service performance.
- Prepared weekly summaries for the team to highlight common customer pain points and improvement ideas.

PROJECTS
Support Ticket Dashboard
- Built a Tableau dashboard to analyze ticket volume, resolution time, issue categories, and customer impact.
- Used SQL and Excel to clean support data and identify repeated issues across teams.

Sales Trend Analysis
- Used Python, pandas, and visualization libraries to analyze monthly sales data and highlight growth opportunities.
- Presented findings in a simple report with charts and business recommendations.

API Data Automation
- Created Python scripts to collect public API data, clean the results, and prepare a reusable reporting dataset.

EDUCATION
Data Analytics Bootcamp | Digital Skills Academy | 2024
Bachelor of Science in Business Information Systems | Sample State University | 2016 - 2019

LANGUAGES
English: Fluent
German: Intermediate
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
    st.session_state.preferred_language = "English"
    st.session_state.ui_language = "English"
    st.session_state.response_language = "English"
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
    st.markdown("#### Just exploring?")
    st.caption("Load a generic sample CV and job description to see the full WorkZo workflow instantly. No private data needed.")
    c1, c2 = st.columns([1.6, 1])
    with c1:
        st.markdown("<div class=\"workzo-demo-note\"><b>Sample mode uses fictional data.</b><br>Good for first-time testers, Reddit, Product Hunt, and quick demos.</div>", unsafe_allow_html=True)
    with c2:
        if st.button("Try with Sample Resume", type="primary", use_container_width=True, key=f"sample_resume_{location}"):
            with st.status("Loading sample career workspace...", expanded=True) as status:
                st.write("Adding sample CV...")
                st.write("Adding sample job description...")
                st.write("Preparing dashboard, ATS audit, job fit, and interview context...")
                load_workzo_sample_data()
                status.update(label="Sample workspace ready", state="complete")
            st.rerun()


maybe_scroll_to_top()
render_workzo_header()

def show_landing_page():
    """Premium introduction page: one clear start action only."""
    maybe_scroll_to_top()
    st.markdown("""
    <div class="workzo-landing-hero">
      <div class="workzo-kicker">HONEST AI CAREER ASSISTANT</div>
      <div class="workzo-landing-title">Land more interviews with honest ATS insights, CV optimization, and AI-powered job preparation.</div>
      <div class="workzo-landing-copy">WorkZo helps you understand your CV, improve it honestly, match jobs smarter, and prepare for interviews with one connected career workspace.</div>
      <div class="workzo-landing-steps">
        <div class="workzo-landing-step"><span>1</span>Upload CV</div>
        <div class="workzo-landing-step"><span>2</span>Review profile</div>
        <div class="workzo-landing-step"><span>3</span>Improve CV</div>
        <div class="workzo-landing-step"><span>4</span>Prepare + apply</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown('<div class="workzo-start-button-wrapper">', unsafe_allow_html=True)
        if st.button("Start Now", type="primary", use_container_width=True, key="landing_start_now_simple"):
            st.session_state.page = "onboarding"
            st.session_state.nav_page = "dashboard"
            request_scroll_to_top()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.caption("You can upload a CV, create one with AI, or try sample data on the next page.")

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

def render_resume_choice_card(icon: str, title: str, desc: str, active: bool = False):
    active_class = " active" if active else ""
    st.markdown(f"""
    <div class="workzo-action-card{active_class}">
        <div class="workzo-action-title">{html.escape(icon)} {html.escape(title)}</div>
        <div class="workzo-action-copy">{html.escape(desc)}</div>
    </div>
    """, unsafe_allow_html=True)

def show_onboarding():
    maybe_scroll_to_top()
    st.subheader(txt("onboarding_title"), help=txt("app_info_help"))
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
    set_single_preferred_language(preferred_language)

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

    c_upload, c_create, c_linkedin = st.columns(3)
    with c_upload:
        active = st.session_state.get("cv_mode") == "Upload CV"
        st.markdown(f"""
        <div class='workzo-resume-mode-card {'active' if active else ''}'>
            <div class='workzo-resume-mode-title'>Upload CV{' - selected' if active else ''}</div>
            <div class='workzo-resume-mode-copy'>Upload an existing PDF or TXT resume.</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Choose Upload CV", key="choose_upload_cv", use_container_width=True):
            st.session_state.cv_mode = "Upload CV"
            st.rerun()
    with c_create:
        active = st.session_state.get("cv_mode") == "Create CV"
        st.markdown(f"""
        <div class='workzo-resume-mode-card {'active' if active else ''}'>
            <div class='workzo-resume-mode-title'>Create CV{' - selected' if active else ''}</div>
            <div class='workzo-resume-mode-copy'>Enter rough notes and WorkZo builds a professional CV.</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Choose Create CV", key="choose_create_cv", use_container_width=True):
            st.session_state.cv_mode = "Create CV"
            st.rerun()
    with c_linkedin:
        active = st.session_state.get("cv_mode") == "LinkedIn"
        st.markdown(f"""
        <div class='workzo-resume-mode-card {'active' if active else ''}'>
            <div class='workzo-resume-mode-title'>Import LinkedIn{' - selected' if active else ''}</div>
            <div class='workzo-resume-mode-copy'>Paste your LinkedIn link and add extra notes.</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Choose LinkedIn Import", key="choose_linkedin_cv", use_container_width=True):
            st.session_state.cv_mode = "LinkedIn"
            st.rerun()

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
            st.success(ui_label("CV uploaded successfully. You can continue to the dashboard."))

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
                st.caption(ui_label("Choose a PDF or TXT file above to continue."))

        elif cv_mode == "LinkedIn":
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
                target_role = st.text_input(txt("target_role_optional"), placeholder="Example: Data Analyst / IT Support Specialist")
                education_level = st.selectbox(txt("education_level"), EDUCATION_LEVELS, index=0, key="onboarding_education_level")
                selected_skills = st.multiselect(txt("suggested_skills"), POPULAR_SKILLS, key="onboarding_suggested_skills")
                languages = st.text_area(txt("languages_label"), placeholder="Example: English fluent, French intermediate, Portuguese native")

            summary = st.text_area(txt("summary"), placeholder="Example: Customer support professional with SaaS experience, interested in data and technology roles.")
            skills = st.text_area(txt("skills"), placeholder="Example: SQL, Excel, Python, customer support, problem solving, CRM tools")
            if selected_skills:
                skills = ", ".join(dict.fromkeys([x.strip() for x in (skills.split(",") if skills else [])] + selected_skills))
            experience = st.text_area(txt("experience"), placeholder="Example: Technical Support Associate, ABC Software, 2020-2024 — handled customer tickets and troubleshooting.")
            projects = st.text_area(txt("projects_label"), placeholder="Example: Built a dashboard to track monthly sales and customer trends.")
            certifications = st.text_area(txt("cert_courses"), placeholder="Example: Google Data Analytics Certificate, Excel Advanced, AWS basics")
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
                    st.warning("Please enter at least a few details so WorkZo can build your CV.")
                    return

                with st.spinner("Creating your CV draft with AI..."):
                    ai_cv = generate_cv_from_user_details(cv_text_input, migration_country if migration_country else country, user_status)
                    if ai_cv and not ai_cv.startswith("ERROR:"):
                        st.session_state.created_cv_ai_output = ai_cv
                        cv_text_input = ai_cv

            st.session_state.country = country
            st.session_state.user_status = user_status
            st.session_state.migration_country = migration_country if migration_country else country
            st.session_state.cv_mode = cv_mode
            if cv_mode == "Upload CV":
                st.session_state.raw_cv_extraction = cv_text_input
                with st.spinner("Extracting resume facts into clean sections..."):
                    structured_data = extract_structured_resume_json(cv_text_input, st.session_state.migration_country, user_status)
                clean_from_sections = _format_structured_resume_profile(structured_data)
                st.session_state.structured_cv_json = structured_data if isinstance(structured_data, dict) else {}
                st.session_state.pending_structured_cv_json = {}
                st.session_state.cv_review_required = False
                if clean_from_sections and len(clean_from_sections.strip()) > 120:
                    st.session_state.structured_cv_profile = clean_from_sections
                    st.session_state.clean_structured_cv_text = clean_from_sections
                    cv_text_input = clean_from_sections
                track_event("cv_structured_profile_created", "Onboarding", {"cv_mode": cv_mode, "target_country": st.session_state.get("migration_country", country)})

            st.session_state.cv_text = clean_cv_text(cv_text_input)
            track_event("cv_ready", "Onboarding", {"cv_mode": cv_mode, "user_status": user_status, "target_country": st.session_state.get("migration_country", country)})
            st.session_state.onboarding_complete = True
            sync_navigation_state("dashboard")

            with st.spinner("Reading your resume and preparing dashboard..."):
                analyze_resume_dashboard_stable(st.session_state.cv_text, force_refresh=True)

            request_scroll_to_top()
            st.session_state.nav_page = "dashboard"
            st.rerun()

# =========================================================
# =========================================================
# WORK-O-BOT
# =========================================================
def workobot_intro_message() -> str:
    return """Hi, I'm Work-O-Bot Bot

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
    if not can_make_request():
        return "I'm sorry, the hourly AI usage limit has been reached. Please try again later."

    register_request()
    answer_lang = normalize_answer_language(st.session_state.get("preferred_language", "English"))
    intent = infer_workobot_intent(user_message)
    model_name = os.getenv("WORKZO_AI_MODEL") or get_streamlit_secret("WORKZO_AI_MODEL", "gpt-4o-mini")

    system_prompt = f"""
You are Work-O-Bot, the AI career coach inside WorkZo AI.

Your role: {intent}

You help users with:
- job search strategy
- CV and ATS improvement
- interview preparation and mock interview feedback
- career change planning
- language practice for work
- skill gap analysis
- HR, recruiter, LinkedIn, and professional communication

User context:
{workobot_context_snapshot()}

Rules:
1. Be honest, practical, and supportive.
2. Use the user's CV/profile context when relevant.
3. Never invent experience, employers, dates, degrees, certifications, achievements, or language level.
4. If the user asks something vague, answer with a best first step and ask only one useful follow-up question.
5. Give structured answers with short headings and bullets.
6. When relevant, include exact examples the user can copy.
7. If the user practices an interview or language answer, give: corrected version, stronger version, and one practice task.
8. If the user asks about jobs, mention realistic role level, target-country fit, and risks.
9. If the user asks about CV, give safe-to-use wording and mark anything that should be used only if true.
10. End with one clear next best action.
11. Answer fully in {answer_lang}. Do not mix languages unless the user asks for translation or language practice.
""".strip()

    history = []
    for msg in st.session_state.get("workobot_messages", [])[-10:]:
        role = msg.get("role", "assistant")
        content = msg.get("content", "")
        if role in ["user", "assistant"] and content:
            history.append({"role": role, "content": content})

    messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": user_message}]

    try:
        res = client.chat.completions.create(
            model=model_name,
            temperature=0.25,
            messages=messages,
        )
        return (res.choices[0].message.content or "").strip()
    except Exception as e:
        return f"I couldn't answer right now because the AI service is unavailable. ({type(e).__name__})"


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
            ("B1/B2 mock questions", "Give me a German B1/B2 mock test practice set with example questions and answers."),
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
            "Brazil Professional CV": "Brazilian-market currÃ­culo with objective/profile, experience, education, skills and courses.",
            "Brazil ATS CV": "Simple keyword-rich CV for online applications and recruiters.",
            "Brazil Entry-Level CV": "Education, projects, internships, tools and courses first.",
        },
        "spain": {
            "Spain CV - Profesional": "Spanish-market CV with perfil, experiencia, formaciÃ³n, competencias and idiomas.",
            "Spain ATS CV": "Clean no-photo CV for portals and international employers.",
            "Spain Internship CV": "CV for practicas, becario, trainee and junior roles.",
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
    st.components.v1.html(build_visual_cv_html(sample_cv, template_name, target_country), height=620, scrolling=True)

    with st.expander("What this template includes", expanded=False):
        st.markdown(get_template_instructions(template_name, target_country))

def generate_country_cv_template(cv_text: str, target_country: str, user_status: str, template_name: str = "ATS Classic") -> str:
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

{rules_text}

Template instructions:
{template_instructions}

Output rules:
- Use these exact section headings: 1. Country Fit Notes, 2. Full Resume Draft, 3. WorkZo Changes, 4. Missing Details to Confirm.
- Do not use markdown symbols like ###, **, or bullet characters outside the resume bullets.
- Section 1 must be 3 short bullets only: country fit, removed/kept details, ideal length.
- Section 2 must be the full copy-ready resume/CV only.
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
    country = st.session_state.get("country") or "selected country"
    target = st.session_state.get("migration_country") or country
    if is_applying_abroad_status(st.session_state.get("user_status", "")):
        return target
    return target or country

def onboarding_country_for_cv() -> str:
    """Country selected on the onboarding page. Builder-only country choices must not affect this."""
    return st.session_state.get("country") or st.session_state.get("onboarding_country") or "International"

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

    st.components.v1.html(
        build_visual_cv_html(live_text, template_name, target_country),
        height=850,
        scrolling=True
    )

    try:
        with st.expander("What this template includes", expanded=False):
            st.markdown(get_template_instructions(template_name, target_country))
    except Exception:
        pass
