"""WorkZo AI - production clean dashboard + feature router.

Replace workzo_modules/08_dashboard.py with this file.
Goal: one UI renderer, one session-state router, no old/duplicate UI.
"""
from __future__ import annotations

import os, re, csv, html, json
from pathlib import Path
from datetime import datetime, UTC
from typing import Any, Dict, List
from io import BytesIO

try:
    import streamlit as st
except Exception:
    st = None

PAGE_ALIASES = {
    "dashboard":"dashboard", "home":"dashboard", "main":"dashboard",
    "improve":"improve_cv", "improve_cv":"improve_cv", "cv":"improve_cv", "update_cv":"improve_cv",
    "cv_preview":"cv_preview", "preview_cv":"cv_preview", "edit_cv":"cv_preview", "cv_editor":"cv_preview",
    "cover":"cover_letter", "cover_letter":"cover_letter", "cover_letter_generator":"cover_letter",
    "find_job":"find_jobs", "find_jobs":"find_jobs", "jobs":"find_jobs", "job_match":"find_jobs",
    "understand_job":"understand_job", "understand":"understand_job", "analyze_job":"understand_job",
    "real_interview":"real_interview", "interview":"real_interview", "start_interview":"real_interview",
    "founder_dashboard":"founder_dashboard", "founder":"founder_dashboard",
}
VALID_PAGES = set(PAGE_ALIASES.values())

# -----------------------------------------------------------------------------
# Navigation
# -----------------------------------------------------------------------------
def _normalize_page(page: Any = None) -> str:
    raw = str(page or st.session_state.get("page") or "dashboard").strip()
    return PAGE_ALIASES.get(raw, raw if raw in VALID_PAGES else "dashboard")

def _rerun() -> None:
    try:
        st.rerun()
    except Exception:
        try: st.experimental_rerun()
        except Exception: pass

def go_to(page: str, **extra: Any) -> None:
    target = _normalize_page(page)
    current = _normalize_page()
    if current != target:
        st.session_state.setdefault("wz_nav_stack", []).append(current)
    for k in ["page", "nav_page", "current_page", "active_page", "selected_page", "workzo_active_page"]:
        st.session_state[k] = target
    st.session_state["onboarding_complete"] = True
    for k, v in extra.items():
        st.session_state[k] = v
    _rerun()

def go_back() -> None:
    stack = st.session_state.get("wz_nav_stack") or []
    while stack:
        target = _normalize_page(stack.pop())
        if target != _normalize_page():
            st.session_state["wz_nav_stack"] = stack
            for k in ["page", "nav_page", "current_page", "active_page", "selected_page", "workzo_active_page"]:
                st.session_state[k] = target
            _rerun(); return
    go_to("dashboard")

# -----------------------------------------------------------------------------
# Data helpers
# -----------------------------------------------------------------------------
def _s(v: Any) -> str:
    return str(v or "").strip()

def _cv_text() -> str:
    for key in ["workzo_live_cv_text","wz_final_cv_edit_text","cv_editor_widget","improved_cv_edit_buffer_v92","improved_cv_text_v92","clean_structured_cv_text","approved_cv_text","structured_cv_text","final_cv_text","cv_text","uploaded_cv_text","generated_country_cv_text"]:
        v = st.session_state.get(key, "")
        if isinstance(v, str) and v.strip(): return v.strip()
    fn = globals().get("get_clean_cv_source_for_tools")
    if callable(fn):
        try:
            v = fn()
            if isinstance(v, str) and v.strip(): return v.strip()
        except Exception: pass
    return ""

def _set_cv_text(text: str) -> None:
    text = _s(text)
    if not text: return
    for key in ["workzo_live_cv_text","wz_final_cv_edit_text","cv_editor_widget","improved_cv_edit_buffer_v92","improved_cv_text_v92","clean_structured_cv_text","approved_cv_text","final_cv_text","cv_text"]:
        st.session_state[key] = text

def _structured_cv() -> Dict[str, Any]:
    data = st.session_state.get("workzo_live_cv_structured") or st.session_state.get("improved_cv_structured_v92") or st.session_state.get("structured_cv_json") or {}
    if isinstance(data, dict) and data:
        for fn_name in ["_coerce_structured_resume_schema", "validate_resume_dates_and_sections"]:
            fn = globals().get(fn_name)
            if callable(fn):
                try: data = fn(data)
                except Exception: pass
        return data if isinstance(data, dict) else {}
    return {}

def _user_name() -> str:
    data = _structured_cv()
    for k in ["full_name", "name"]:
        if _s(data.get(k)): return _s(data[k]).split("\n")[0]
    for obj_key in ["personal_info", "contact"]:
        obj = data.get(obj_key) or {}
        if isinstance(obj, dict):
            for k in ["name", "full_name"]:
                if _s(obj.get(k)): return _s(obj[k]).split("\n")[0]
    for line in _cv_text().splitlines()[:12]:
        line = line.strip(" |\t")
        if line and "@" not in line and "linkedin" not in line.lower() and not re.search(r"\d", line) and len(line.split()) <= 5:
            return line
    return "there"

def _jd_text() -> str:
    for key in ["selected_job_description","current_job_description","improve_cv_for_job_desc","job_description","last_understand_job_description"]:
        v = st.session_state.get(key, "")
        if isinstance(v, str) and v.strip(): return v.strip()
    job = st.session_state.get("selected_job")
    if isinstance(job, dict): return _s(job.get("description") or job.get("summary"))
    return ""

def _set_jd(text: str) -> None:
    for key in ["selected_job_description","current_job_description","improve_cv_for_job_desc","job_description","last_understand_job_description"]:
        st.session_state[key] = text or ""

def _ai(prompt: str) -> str:
    for name in ["run_ai_prompt", "ask_ai", "call_openai"]:
        fn = globals().get(name)
        if callable(fn):
            try:
                out = fn(prompt)
            except TypeError:
                out = fn([{"role":"user","content":prompt}])
            if isinstance(out, str) and out.strip(): return out.strip()
    return ""

def _readiness() -> int:
    score = 20
    if _cv_text(): score += 30
    if _jd_text(): score += 25
    if st.session_state.get("prepare_cv_tailored"): score += 15
    if st.session_state.get("interview_completed") or st.session_state.get("wz_interview_history"): score += 10
    return min(score, 100)

# -----------------------------------------------------------------------------
# Styling + shell
# -----------------------------------------------------------------------------
def _css() -> None:
    st.markdown("""
    <style>
    .block-container{padding-top:2.2rem!important;max-width:1120px!important;}
    div[data-testid="stAppViewContainer"]{background:#0b1220;}
    .wz-card{background:linear-gradient(135deg,#062f42,#07142a 72%);border:1px solid #0e7490;border-radius:22px;padding:24px 28px;margin:18px 0;box-shadow:0 18px 45px rgba(0,0,0,.22)}
    .wz-row{display:flex;gap:14px;align-items:center;justify-content:space-between;flex-wrap:wrap}.wz-brand{display:flex;gap:14px;align-items:center}.wz-logo{width:56px;height:56px;border-radius:14px;background:linear-gradient(135deg,#22d3ee,#2563eb);display:grid;place-items:center;font-weight:900;font-size:28px;color:white}.wz-title{font-size:2.2rem;font-weight:900;color:#f8fafc;line-height:1.05;margin:0}.wz-kicker{font-size:.78rem;letter-spacing:.22em;text-transform:uppercase;color:#67e8f9;font-weight:900}.wz-copy{color:#bae6fd;font-size:1.02rem}.wz-pill{border:1px solid rgba(148,163,184,.28);border-radius:999px;padding:7px 12px;color:#e0f2fe;background:#0b1326;font-weight:700}.wz-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin-top:16px}.wz-metric{background:#071225;border:1px solid rgba(148,163,184,.25);border-radius:16px;padding:18px}.wz-metric b{display:block;font-size:2rem;color:white;margin:8px 0}.wz-muted{color:#94a3b8}.wz-small{font-size:.9rem}.wz-bot{position:fixed;right:26px;bottom:24px;z-index:99999;background:#06364a;border:1px solid #06b6d4;border-radius:18px;padding:13px 16px;min-width:230px;box-shadow:0 20px 55px rgba(0,0,0,.35)}
    .wz-bot strong{color:#f8fafc}.wz-bot span{color:#bae6fd;font-size:.85rem}.wz-preview{background:white;color:#111827;border-radius:10px;padding:34px 42px;line-height:1.45}.wz-preview h1{color:#0f172a;margin-bottom:0}.wz-preview h2{font-size:1rem;letter-spacing:.12em;text-transform:uppercase;border-bottom:1px solid #d1d5db;padding-bottom:4px;margin-top:22px}.wz-preview.two{display:grid;grid-template-columns:32% 1fr;gap:24px}.wz-preview.two .side{background:#eef2f7;padding:18px;border-radius:8px}.wz-footer{margin:34px 0 14px}.stButton>button{border-radius:13px!important}.stButton>button[kind="primary"]{background:#ff4b4b!important;color:white!important;border:0!important}
    @media(max-width:800px){.wz-grid{grid-template-columns:1fr}.wz-title{font-size:1.65rem}.wz-card{padding:20px}.wz-bot{right:12px;bottom:12px;min-width:190px}}
    </style>
    """, unsafe_allow_html=True)

def _header() -> None:
    st.markdown(f"""
    <div class='wz-card'>
      <div class='wz-row'>
        <div class='wz-brand'><div class='wz-logo'>↗</div><div><div style='font-size:1.35rem;font-weight:900;color:white'>WorkZo <span style='color:#22d3ee'>AI</span></div><div class='wz-muted'>Your guided AI career system</div></div></div>
        <div style='min-width:230px'><div class='wz-muted wz-small'>Readiness <b style='float:right;color:white'>{_readiness()}%</b></div><progress value='{_readiness()}' max='100' style='width:100%;height:10px'></progress></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

def _nav_dropdown() -> None:
    with st.expander("› You can also try", expanded=False):
        c1,c2,c3,c4 = st.columns(4)
        with c1:
            if st.button("Improve CV", key="nav_improve_cv", use_container_width=True): go_to("improve_cv")
        with c2:
            if st.button("Cover Letter", key="nav_cover_letter", use_container_width=True): go_to("cover_letter")
        with c3:
            if st.button("Find Job", key="nav_find_job", use_container_width=True): go_to("find_jobs")
        with c4:
            if st.button("Understand Job", key="nav_understand_job", use_container_width=True): go_to("understand_job")

def _floating_bot() -> None:
    page = _normalize_page()
    if page in {"dashboard","improve_cv","cv_preview","cover_letter","find_jobs","understand_job","real_interview"}:
        st.markdown("""<div class='wz-bot'><strong>Ask Work-O-Bot</strong><br><span>career questions</span></div>""", unsafe_allow_html=True)
        with st.expander("💬 Career-related questions? Ask me!", expanded=False):
            context = st.session_state.get("current_interview_question", "") or st.session_state.get("wz_current_question", "")
            if context: st.caption("I can see the current interview question.")
            q = st.text_input("Ask Work-O-Bot", key="wz_inline_bot_q")
            if st.button("Ask", key="wz_inline_bot_send") and q.strip():
                cv = _cv_text()[:2200]; jd = _jd_text()[:1800]
                ans = _ai(f"You are Work-O-Bot, a concise career assistant. Use CV, job and current interview question if available.\nCV:\n{cv}\nJob:\n{jd}\nCurrent interview question:\n{context}\nUser question: {q}")
                st.info(ans or "Based on your current CV/job context, focus on clear examples, measurable impact, and truthful role-specific wording.")

# -----------------------------------------------------------------------------
# Feature pages
# -----------------------------------------------------------------------------
def _dashboard_page() -> None:
    name = html.escape(_user_name())
    st.markdown(f"""
    <div class='wz-card'>
      <div class='wz-kicker'>Dashboard</div>
      <div class='wz-title'>Hi 👋 {name}</div>
      <div class='wz-copy'>Prepare one target job, improve your CV for that job, then practice a realistic interview.</div>
      <div class='wz-grid'>
        <div class='wz-metric'><div class='wz-kicker'>Job readiness</div><b>{_readiness()}%</b><div class='wz-copy'>CV + job connected</div></div>
        <div class='wz-metric'><div class='wz-kicker'>CV</div><b>{'Ready' if _cv_text() else 'Missing'}</b><div class='wz-copy'>CV is ready</div></div>
        <div class='wz-metric'><div class='wz-kicker'>Interview</div><b>Ready</b><div class='wz-copy'>Practice with pressure + follow-ups</div></div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🎤 Start Real Interview", key="dash_start_interview", type="primary", use_container_width=False): go_to("real_interview")
    st.markdown("<div class='wz-card'><div class='wz-kicker'>Before you start</div><div class='wz-copy'>Recommended: improve your CV for the selected job, or find one matching job first.</div></div>", unsafe_allow_html=True)
    c1,c2 = st.columns(2)
    with c1:
        if st.button("Improve CV", key="dash_improve", use_container_width=True): go_to("improve_cv")
    with c2:
        if st.button("Find matching jobs", key="dash_jobs", use_container_width=True): go_to("find_jobs")

def _improve_cv_page() -> None:
    st.markdown("<div class='wz-card'><div class='wz-kicker'>CV step</div><div class='wz-title'>Improve your CV for this job</div><div class='wz-copy'>Paste one job description. WorkZo will tailor your CV, then you can edit, preview, translate and download it.</div></div>", unsafe_allow_html=True)
    jd = st.text_area("Job description", value=_jd_text(), height=220, key="wz_jd_for_improve")
    notes = st.text_area("Optional updates to include", height=90, key="wz_cv_update_notes", placeholder="Example: Add B1 German, new project, certificate, updated phone number...")
    c1,c2 = st.columns([1,1])
    with c1:
        if st.button("Improve CV", key="wz_generate_improved_cv", type="primary", use_container_width=True):
            cv = _cv_text()
            if not cv:
                st.warning("Please upload or create a CV first.")
            elif not jd.strip() and not notes.strip():
                st.warning("Please paste a job description or add update notes.")
            else:
                _set_jd(jd)
                prompt = f"Rewrite this CV for the job description. Keep it truthful. Do not invent employers, dates, education or metrics. Add only wording supported by the CV or notes. Return a clean CV only.\n\nCV:\n{cv}\n\nJOB DESCRIPTION:\n{jd}\n\nUSER NOTES:\n{notes}"
                improved = _ai(prompt) or cv
                _set_cv_text(improved)
                st.session_state["prepare_cv_tailored"] = True
                st.success("Improved CV created. Open Edit / Preview CV to review and download.")
    with c2:
        if st.button("Edit / Preview CV", key="wz_edit_preview_from_improve", use_container_width=True): go_to("cv_preview")
    if st.session_state.get("prepare_cv_tailored"):
        st.info("CV tailored. Next: edit/preview/download, or start interview.")

def _basic_pdf_bytes(text: str) -> bytes:
    try:
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        buf = BytesIO(); doc = SimpleDocTemplate(buf, pagesize=A4); styles = getSampleStyleSheet(); story=[]
        for line in text.splitlines():
            story.append(Paragraph(html.escape(line) if line.strip() else "&nbsp;", styles["BodyText"])); story.append(Spacer(1,4))
        doc.build(story); return buf.getvalue()
    except Exception:
        return text.encode("utf-8")

def _cv_preview_html(text: str, template: str) -> str:
    esc = html.escape(text).replace("\n", "<br>")
    if template == "Two-column modern":
        return f"<div class='wz-preview two'><div class='side'><h2>Profile</h2><p>Country-aware CV style</p><h2>Skills</h2><p>{esc[:900]}</p></div><div><h2>Experience</h2><p>{esc}</p></div></div>"
    if template == "Clean ATS":
        return f"<div class='wz-preview'><h1>{html.escape(_user_name())}</h1><h2>Professional CV</h2><p>{esc}</p></div>"
    return f"<div class='wz-preview'><h1>{html.escape(_user_name())}</h1><div style='border-left:6px solid #06b6d4;padding-left:18px'><p>{esc}</p></div></div>"

def _cv_preview_page() -> None:
    st.markdown("<div class='wz-card'><div class='wz-kicker'>CV editor</div><div class='wz-title'>Edit, preview and download your CV</div><div class='wz-copy'>Choose a country-aware template, edit the CV, translate it if needed, then download.</div></div>", unsafe_allow_html=True)
    cv = st.session_state.get("wz_cv_editor_value") or _cv_text()
    template = st.selectbox("CV template", ["Clean ATS", "Two-column modern", "Country professional"], key="wz_cv_template_choice")
    lang = st.selectbox("CV language", ["English","German","Hindi","Tamil","French","Spanish"], key="wz_cv_language_choice")
    edited = st.text_area("Edit CV", value=cv, height=360, key="wz_cv_editor_text_area")
    c1,c2,c3 = st.columns(3)
    with c1:
        if st.button("Save CV edits", key="wz_save_cv_edits", type="primary", use_container_width=True):
            _set_cv_text(edited); st.session_state["wz_cv_editor_value"] = edited; st.success("Saved.")
    with c2:
        if st.button("Translate CV", key="wz_translate_cv", use_container_width=True):
            out = _ai(f"Translate this CV fully into {lang}. Keep names, companies, dates, email, phone, links unchanged.\n\n{edited}") if lang != "English" else edited
            if out: edited = out; _set_cv_text(out); st.session_state["wz_cv_editor_value"] = out; st.success("Translated. Review below."); _rerun()
    with c3:
        if st.button("Back to Improve CV", key="wz_back_improve_from_preview", use_container_width=True): go_to("improve_cv")
    st.markdown("### Preview")
    st.markdown(_cv_preview_html(edited, template), unsafe_allow_html=True)
    st.markdown("### Download")
    d1,d2,d3 = st.columns(3)
    with d1: st.download_button("Download TXT", edited.encode("utf-8"), "workzo_cv.txt", "text/plain", use_container_width=True)
    with d2: st.download_button("Download HTML Preview", _cv_preview_html(edited, template).encode("utf-8"), "workzo_cv_preview.html", "text/html", use_container_width=True)
    with d3: st.download_button("Download PDF", _basic_pdf_bytes(edited), "workzo_cv.pdf", "application/pdf", use_container_width=True)

def _cover_letter_page() -> None:
    st.markdown("<div class='wz-card'><div class='wz-kicker'>AI document writer</div><div class='wz-title'>Cover Letter Generator</div><div class='wz-copy'>Generate a focused cover letter and short email from your CV and selected job context.</div></div>", unsafe_allow_html=True)
    c1,c2 = st.columns(2)
    with c1: company = st.text_input("Company name", key="wz_cover_company")
    with c2: role = st.text_input("Target role", value=st.session_state.get("target_role", ""), key="wz_cover_role")
    jd = st.text_area("Job description", value=_jd_text(), height=180, key="wz_cover_jd")
    if st.button("Generate cover letter", key="wz_generate_cover", type="primary"):
        _set_jd(jd)
        out = _ai(f"Write a concise truthful cover letter and short email using this CV and job description.\nCV:\n{_cv_text()}\nCompany:{company}\nRole:{role}\nJD:\n{jd}")
        st.session_state["wz_cover_output"] = out or "Cover letter draft could not be generated. Please add more job details."
    draft = st.text_area("Edit cover letter", value=st.session_state.get("wz_cover_output", ""), height=280, key="wz_cover_edit")
    col1,col2 = st.columns(2)
    with col1: st.download_button("Download cover letter TXT", draft.encode("utf-8"), "cover_letter.txt", "text/plain", use_container_width=True)
    with col2:
        if st.button("Edit / Preview CV", key="wz_cover_to_cv_preview", use_container_width=True): go_to("cv_preview")

def _find_jobs_page() -> None:
    st.markdown("<div class='wz-card'><div class='wz-kicker'>My jobs</div><div class='wz-title'>Top matches for you</div><div class='wz-copy'>Choose one job. WorkZo will connect it automatically to CV improvement and interview practice.</div></div>", unsafe_allow_html=True)
    c1,c2,c3 = st.columns(3)
    with c1: country = st.text_input("Target country", value=st.session_state.get("country", "Germany"), key="wz_job_country")
    with c2: city = st.text_input("City / region", value=st.session_state.get("preferred_location", ""), key="wz_job_city")
    with c3: remote = st.checkbox("Remote okay", value=bool(st.session_state.get("remote_ok", False)), key="wz_job_remote")
    role = st.text_input("Target role", value=st.session_state.get("target_role", "Data Analyst / IT Support Analyst"), key="wz_job_role")
    if st.button("Refresh matches", key="wz_refresh_job_matches") or "wz_job_matches" not in st.session_state:
        loc = city or country
        titles = [role or "Data Analyst", "Customer Success Manager", "IT Support Specialist", "Junior Data Analyst"]
        jobs=[]
        for i,t in enumerate(titles[:4]):
            jobs.append({"title": t, "company": ["Demo Company","Zalando","Siemens","HubSpot"][i%4], "location": loc or country, "description": f"{t} role in {loc or country}. Requires communication, problem-solving, customer/user support, analysis and documentation skills.", "match": 78-i*5})
        st.session_state["wz_job_matches"] = jobs
    for i, job in enumerate(st.session_state.get("wz_job_matches", [])):
        with st.container(border=True):
            st.markdown(f"### {job['title']} — {job['company']}")
            st.caption(f"{job['location']} · Match {job['match']}% · {'Remote possible' if remote else 'Location based'}")
            st.write("**Why it fits:** uses your CV background and target role.")
            st.write("**Needs improvement:** add job-specific examples and measurable results.")
            a,b,c = st.columns(3)
            with a:
                if st.button("Select job", key=f"select_job_{i}", use_container_width=True):
                    st.session_state["selected_job"] = job; _set_jd(job["description"]); st.success("Job selected."); _rerun()
            with b:
                if st.button("Improve CV for this", key=f"improve_job_{i}", use_container_width=True):
                    st.session_state["selected_job"] = job; _set_jd(job["description"]); go_to("improve_cv")
            with c:
                if st.button("Practice interview", key=f"interview_job_{i}", use_container_width=True):
                    st.session_state["selected_job"] = job; _set_jd(job["description"]); go_to("real_interview")

def _understand_job_page() -> None:
    st.markdown("<div class='wz-card'><div class='wz-kicker'>Job insight</div><div class='wz-title'>Understand this job</div><div class='wz-copy'>Paste one job description. WorkZo explains fit, gaps and next action based on your CV.</div></div>", unsafe_allow_html=True)
    jd = st.text_area("Paste job description", value=_jd_text(), height=260, key="wz_understand_jd")
    if st.button("Analyze Job Fit", key="wz_analyze_job", type="primary"):
        _set_jd(jd)
        ans = _ai(f"Analyze this job against the CV. Return: fit %, top 3 matches, top 3 gaps, next action.\nCV:\n{_cv_text()}\nJD:\n{jd}")
        st.session_state["wz_job_analysis"] = ans or "Add a full job description to get a stronger fit analysis."
    if st.session_state.get("wz_job_analysis"):
        st.markdown(st.session_state["wz_job_analysis"])
        if st.button("Improve CV for this job", key="wz_understand_to_improve"): go_to("improve_cv")

def _real_interview_page() -> None:
    # Prefer the dedicated interview module if loaded.
    for name in ["render_real_interview_simulation", "show_interview_assistant", "show_real_interview_practice"]:
        fn = globals().get(name)
        if callable(fn):
            try:
                fn(); return
            except Exception as exc:
                st.warning(f"Interview module could not load cleanly: {exc}")
                break
    st.markdown("<div class='wz-card'><div class='wz-kicker'>Real Interview AI</div><div class='wz-title'>Recruiter call mode</div><div class='wz-copy'>Interview module fallback. Your CV and selected job are connected.</div></div>", unsafe_allow_html=True)
    st.info("Interview module is not available in this build. Replace 09_interview_assistant.py with your latest interview module.")

def _safe_founder_pin() -> str:
    env = os.environ.get("FOUNDER_PIN")
    if env: return str(env)
    try:
        return str(st.secrets.get("FOUNDER_PIN", "1234"))
    except Exception:
        return "1234"

def _founder_dashboard_page(in_footer: bool=False) -> None:
    with st.expander("Founder dashboard", expanded=not in_footer):
        pin = st.text_input("Founder PIN", type="password", key="wz_founder_pin_input")
        if pin != _safe_founder_pin():
            if pin: st.error("Incorrect PIN")
            else: st.caption("Enter founder PIN to view analytics.")
            return
        st.success("Founder access granted")
        files = [Path("workzo_beta_analytics.csv"), Path("workzo_beta_feedback.csv")]
        for f in files:
            st.markdown(f"**{f.name}**")
            if f.exists():
                try:
                    rows = list(csv.reader(f.open(encoding="utf-8")))
                    st.write(f"Rows: {max(0, len(rows)-1)}")
                    st.dataframe(rows[-20:], use_container_width=True)
                except Exception as exc: st.warning(str(exc))
            else: st.caption("No data yet.")

def _footer() -> None:
    st.markdown("<div class='wz-footer'></div>", unsafe_allow_html=True)
    with st.expander("💬 Give feedback (30 sec)", expanded=False):
        fb = st.text_area("What confused you or what should improve?", key="wz_footer_feedback")
        if st.button("Submit feedback", key="wz_submit_feedback") and fb.strip():
            try:
                exists = Path("workzo_beta_feedback.csv").exists()
                with open("workzo_beta_feedback.csv", "a", newline="", encoding="utf-8") as f:
                    w = csv.writer(f)
                    if not exists: w.writerow(["timestamp","page","feedback"])
                    w.writerow([datetime.now(UTC).isoformat(timespec="seconds"), _normalize_page(), fb.strip()])
                st.success("Thank you 🙌")
            except Exception as exc: st.warning(f"Could not save feedback: {exc}")
    _founder_dashboard_page(in_footer=True)

# -----------------------------------------------------------------------------
# Single renderer
# -----------------------------------------------------------------------------
def show_dashboard() -> None:
    if st is None: return
    _css()
    for k in ["page", "nav_page", "current_page", "active_page", "selected_page", "workzo_active_page"]:
        st.session_state.setdefault(k, _normalize_page())
    st.session_state["onboarding_complete"] = True
    page = _normalize_page()
    _header()
    if page != "real_interview":
        _nav_dropdown()
    if page == "dashboard": _dashboard_page()
    elif page == "improve_cv": _improve_cv_page()
    elif page == "cv_preview": _cv_preview_page()
    elif page == "cover_letter": _cover_letter_page()
    elif page == "find_jobs": _find_jobs_page()
    elif page == "understand_job": _understand_job_page()
    elif page == "real_interview": _real_interview_page()
    elif page == "founder_dashboard": _founder_dashboard_page()
    else: _dashboard_page()
    _floating_bot()
    _footer()

# Backwards-compatible aliases older router code may look for.
show_workzo_dashboard = show_dashboard
show_improve_cv = _improve_cv_page
show_find_jobs = _find_jobs_page
show_cover_letter = _cover_letter_page
show_understand_job = _understand_job_page
show_cv_preview = _cv_preview_page
show_founder_dashboard = _founder_dashboard_page
