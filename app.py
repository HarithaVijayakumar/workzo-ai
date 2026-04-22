import os
import re
import time
import urllib.parse
from typing import Dict, Optional

import pdfplumber
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="WORKZO AI",
    page_icon="🚀",
    layout="wide"
)

# =========================================================
# LOAD ENV
# =========================================================
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")
if not api_key:
    st.error("OPENAI_API_KEY not found. Please check your .env file or Streamlit secrets.")
    st.stop()

client = OpenAI(api_key=api_key)

# =========================================================
# RATE LIMITING
# =========================================================
MAX_REQUESTS_PER_HOUR = 20

if "request_count" not in st.session_state:
    st.session_state.request_count = 0

if "first_request_time" not in st.session_state:
    st.session_state.first_request_time = time.time()

if time.time() - st.session_state.first_request_time > 3600:
    st.session_state.request_count = 0
    st.session_state.first_request_time = time.time()

def can_make_request() -> bool:
    return st.session_state.request_count < MAX_REQUESTS_PER_HOUR

def register_request() -> None:
    st.session_state.request_count += 1

# =========================================================
# STYLES
# =========================================================
st.markdown("""
<style>
    .beta-badge {
        background-color: #ff4b4b;
        color: white;
        padding: 4px 10px;
        border-radius: 8px;
        font-size: 12px;
        margin-left: 10px;
        display: inline-block;
    }
    .card {
        border: 1px solid rgba(128,128,128,0.25);
        border-radius: 16px;
        padding: 16px;
        background: rgba(255,255,255,0.02);
        margin-bottom: 12px;
    }
    .section-title {
        font-size: 1.05rem;
        font-weight: 700;
        margin-bottom: 8px;
    }
    .small-muted {
        color: #888;
        font-size: 0.95rem;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# UI LANGUAGE TEXT
# =========================================================
UI_TEXT = {
    "English": {
        "title": "Your 360° AI Career Assistant",
        "subtitle": "AI-powered career support based on your country and CV.",
        "onboarding_title": "Welcome to WorkZo",
        "onboarding_subtitle": "Start with your country and CV. WorkZo will build the rest from there.",
        "country": "Target Country",
        "ui_language": "App Language",
        "response_language": "AI Response Language",
        "resume_input": "Resume Input",
        "upload_cv": "Upload CV",
        "create_cv": "Create CV",
        "upload_resume": "Upload your CV",
        "create_resume": "Create your CV",
        "full_name": "Full Name",
        "email": "Email",
        "phone": "Phone Number",
        "summary": "Professional Summary",
        "skills": "Skills",
        "experience": "Work Experience",
        "education": "Education",
        "continue": "Continue to Dashboard",
        "edit_setup": "Edit Onboarding",
        "onboarding_complete": "Onboarding complete",
        "dashboard": "Dashboard",
        "actions": "What do you want to do?",
        "understand_job": "Understand Job",
        "improve_cv": "Improve CV",
        "career_communication": "Career Communication",
        "find_jobs": "Find Jobs",
        "mock_interview": "Mock Interview",
        "skill_gap": "Skill Gap",
        "career_roadmap": "Career Roadmap",
        "cv_translator": "CV Translator",
        "cover_letter_generator": "Cover Letter Generator",
        "cover_letter_translator": "Cover Letter Translator",
        "language_support": "Language Support",
        "start_here": "Start here",
        "start_here_intro": "Your dashboard gives a quick view of your resume strength and extracted profile. Then use the menu on the left for deeper tools.",
        "detected_profile": "Extracted from your resume",
        "detected_role": "Likely Current Role",
        "detected_summary": "Professional Summary",
        "detected_skills": "Key Skills",
        "suggested_roles": "Suggested Roles",
        "resume_loaded": "Resume Loaded",
        "yes": "Yes",
        "no": "No",
        "not_analyzed": "Not analyzed yet",
        "warn_country": "Please select a country.",
        "warn_upload_cv": "Please upload your CV before continuing.",
        "warn_full_name": "Please enter your full name.",
        "warn_summary": "Please enter your professional summary.",
        "warn_skills": "Please enter your skills.",
        "warn_experience": "Please enter your work experience.",
        "warn_education": "Please enter your education.",
        "unsupported_file": "Unsupported file type.",
        "done": "Done",
        "ai_unavailable": "AI service unavailable",
        "job_desc": "Paste the job description",
        "your_cv": "Your CV",
        "target_job": "Paste target job description",
        "job_title": "Job title",
        "background": "Short background about yourself",
        "preferred_location": "Preferred city or region",
        "target_role": "Target role",
        "current_role": "Your current role",
        "current_profile": "Your current profile / CV",
        "interview_language": "Interview language",
        "language_support_task": "Support task",
        "enter_text": "Enter your text",
        "improve": "Improve",
        "analyze": "Analyze",
        "generate": "Generate",
        "translate": "Translate",
        "job_fit_analysis": "Job Fit Analysis",
        "career_comm_result": "Career Communication Feedback",
        "search_queries": "Suggested search links",
        "platform_hint": "These links open search pages. Later, you can replace them with local job portals.",
        "translator_source": "Source Language",
        "translator_target": "Target Language",
        "cover_letter_input": "Paste your cover letter",
        "cv_input": "Paste your CV",
        "copy_ready": "Copy-ready output",
        "resume_score": "Resume Score",
        "ats_score": "ATS Readiness",
        "strengths": "Top Strengths",
        "improvements": "Top Improvements",
        "raw_resume_extract": "Raw Resume Extraction",
        "job_fit_score": "Job Fit",
        "skill_gap_score": "Skill Gap",
        "interview_score": "Interview",
        "resume_insights": "Resume Insights",
        "update_resume": "Update My Resume",
    },
    "German": {
        "title": "Dein 360° KI-Karriereassistent",
        "subtitle": "KI-gestützte Karrierehilfe basierend auf deinem Land und deinem Lebenslauf.",
        "onboarding_title": "Willkommen bei WorkZo",
        "onboarding_subtitle": "Starte mit deinem Land und deinem Lebenslauf. WorkZo erstellt den Rest daraus.",
        "country": "Zielland",
        "ui_language": "App-Sprache",
        "response_language": "Antwortsprache der KI",
        "resume_input": "Lebenslauf-Eingabe",
        "upload_cv": "Lebenslauf hochladen",
        "create_cv": "Lebenslauf erstellen",
        "upload_resume": "Lebenslauf hochladen",
        "create_resume": "Lebenslauf erstellen",
        "full_name": "Vollständiger Name",
        "email": "E-Mail",
        "phone": "Telefonnummer",
        "summary": "Berufliche Zusammenfassung",
        "skills": "Kenntnisse",
        "experience": "Berufserfahrung",
        "education": "Ausbildung",
        "continue": "Zum Dashboard",
        "edit_setup": "Onboarding bearbeiten",
        "onboarding_complete": "Onboarding abgeschlossen",
        "dashboard": "Dashboard",
        "actions": "Was möchtest du tun?",
        "understand_job": "Stelle verstehen",
        "improve_cv": "Lebenslauf verbessern",
        "career_communication": "Karrierekommunikation",
        "find_jobs": "Jobs finden",
        "mock_interview": "Vorstellungsgespräch",
        "skill_gap": "Kompetenzlücke",
        "career_roadmap": "Karriereplan",
        "cv_translator": "Lebenslauf übersetzen",
        "cover_letter_generator": "Anschreiben erstellen",
        "cover_letter_translator": "Anschreiben übersetzen",
        "language_support": "Sprachhilfe",
        "start_here": "Starte hier",
        "start_here_intro": "Dein Dashboard zeigt zuerst die Stärke deines Lebenslaufs und die erkannten Informationen. Nutze danach das linke Menü für weitere Tools.",
        "detected_profile": "Aus deinem Lebenslauf erkannt",
        "detected_role": "Wahrscheinliche aktuelle Rolle",
        "detected_summary": "Berufliche Zusammenfassung",
        "detected_skills": "Wichtige Kenntnisse",
        "suggested_roles": "Vorgeschlagene Rollen",
        "resume_loaded": "Lebenslauf geladen",
        "yes": "Ja",
        "no": "Nein",
        "not_analyzed": "Noch nicht analysiert",
        "warn_country": "Bitte wähle ein Land.",
        "warn_upload_cv": "Bitte lade deinen Lebenslauf hoch.",
        "warn_full_name": "Bitte gib deinen vollständigen Namen ein.",
        "warn_summary": "Bitte gib deine berufliche Zusammenfassung ein.",
        "warn_skills": "Bitte gib deine Kenntnisse ein.",
        "warn_experience": "Bitte gib deine Berufserfahrung ein.",
        "warn_education": "Bitte gib deine Ausbildung ein.",
        "unsupported_file": "Nicht unterstützter Dateityp.",
        "done": "Fertig",
        "ai_unavailable": "KI-Dienst nicht verfügbar",
        "job_desc": "Stellenbeschreibung einfügen",
        "your_cv": "Dein Lebenslauf",
        "target_job": "Ziel-Stellenbeschreibung einfügen",
        "job_title": "Berufsbezeichnung",
        "background": "Kurzer Hintergrund über dich",
        "preferred_location": "Bevorzugte Stadt oder Region",
        "target_role": "Zielrolle",
        "current_role": "Deine aktuelle Rolle",
        "current_profile": "Dein aktuelles Profil / Lebenslauf",
        "interview_language": "Sprache des Interviews",
        "language_support_task": "Aufgabe",
        "enter_text": "Text eingeben",
        "improve": "Verbessern",
        "analyze": "Analysieren",
        "generate": "Erstellen",
        "translate": "Übersetzen",
        "job_fit_analysis": "Job-Fit-Analyse",
        "career_comm_result": "Feedback zur Karrierekommunikation",
        "search_queries": "Vorgeschlagene Suchlinks",
        "platform_hint": "Diese Links öffnen Suchseiten. Später kannst du lokale Jobportale nutzen.",
        "translator_source": "Ausgangssprache",
        "translator_target": "Zielsprache",
        "cover_letter_input": "Anschreiben einfügen",
        "cv_input": "Lebenslauf einfügen",
        "copy_ready": "Kopierfertige Ausgabe",
        "resume_score": "Lebenslauf-Score",
        "ats_score": "ATS-Bereitschaft",
        "strengths": "Top-Stärken",
        "improvements": "Top-Verbesserungen",
        "raw_resume_extract": "Rohe Lebenslauf-Extraktion",
        "job_fit_score": "Job-Fit",
        "skill_gap_score": "Kompetenzlücke",
        "interview_score": "Interview",
        "resume_insights": "Lebenslauf-Einblicke",
        "update_resume": "Lebenslauf aktualisieren",
    },
    "Dutch": {
        "title": "Jouw 360° AI-carrièreassistent",
        "subtitle": "AI-ondersteuning gebaseerd op jouw land en cv.",
        "onboarding_title": "Welkom bij WorkZo",
        "onboarding_subtitle": "Begin met je land en cv. WorkZo bouwt de rest daarop.",
        "country": "Doelland",
        "ui_language": "App-taal",
        "response_language": "AI-antwoordtaal",
        "resume_input": "CV-invoer",
        "upload_cv": "CV uploaden",
        "create_cv": "CV maken",
        "upload_resume": "Upload je CV",
        "create_resume": "Maak je CV",
        "full_name": "Volledige naam",
        "email": "E-mail",
        "phone": "Telefoonnummer",
        "summary": "Professionele samenvatting",
        "skills": "Vaardigheden",
        "experience": "Werkervaring",
        "education": "Opleiding",
        "continue": "Ga naar dashboard",
        "edit_setup": "Onboarding bewerken",
        "onboarding_complete": "Onboarding voltooid",
        "dashboard": "Dashboard",
        "actions": "Wat wil je doen?",
        "understand_job": "Vacature begrijpen",
        "improve_cv": "CV verbeteren",
        "career_communication": "Carrièrecommunicatie",
        "find_jobs": "Banen vinden",
        "mock_interview": "Proefinterview",
        "skill_gap": "Vaardigheidskloof",
        "career_roadmap": "Carrièreplan",
        "cv_translator": "CV vertalen",
        "cover_letter_generator": "Motivatiebrief maken",
        "cover_letter_translator": "Motivatiebrief vertalen",
        "language_support": "Taalhulp",
        "start_here": "Begin hier",
        "start_here_intro": "Je dashboard toont eerst de kracht van je cv en de gedetecteerde gegevens. Gebruik daarna het linkermenu voor meer tools.",
        "detected_profile": "Gedetecteerd uit je cv",
        "detected_role": "Waarschijnlijke huidige rol",
        "detected_summary": "Professionele samenvatting",
        "detected_skills": "Belangrijkste vaardigheden",
        "suggested_roles": "Voorgestelde rollen",
        "resume_loaded": "CV geladen",
        "yes": "Ja",
        "no": "Nee",
        "not_analyzed": "Nog niet geanalyseerd",
        "warn_country": "Selecteer een land.",
        "warn_upload_cv": "Upload je cv voordat je doorgaat.",
        "warn_full_name": "Voer je volledige naam in.",
        "warn_summary": "Voer je professionele samenvatting in.",
        "warn_skills": "Voer je vaardigheden in.",
        "warn_experience": "Voer je werkervaring in.",
        "warn_education": "Voer je opleiding in.",
        "unsupported_file": "Niet-ondersteund bestandstype.",
        "done": "Klaar",
        "ai_unavailable": "AI-service niet beschikbaar",
        "job_desc": "Plak de vacaturetekst",
        "your_cv": "Jouw CV",
        "target_job": "Plak de doelvacature",
        "job_title": "Functietitel",
        "background": "Korte achtergrond over jezelf",
        "preferred_location": "Voorkeursstad of regio",
        "target_role": "Doelrol",
        "current_role": "Je huidige rol",
        "current_profile": "Je huidige profiel / CV",
        "interview_language": "Taal van het interview",
        "language_support_task": "Taak",
        "enter_text": "Voer je tekst in",
        "improve": "Verbeter",
        "analyze": "Analyseer",
        "generate": "Genereer",
        "translate": "Vertaal",
        "job_fit_analysis": "Vacaturematch-analyse",
        "career_comm_result": "Feedback op carrièrecommunicatie",
        "search_queries": "Voorgestelde zoeklinks",
        "platform_hint": "Deze links openen zoekpagina’s. Later kun je lokale vacatureplatforms gebruiken.",
        "translator_source": "Brontaal",
        "translator_target": "Doeltaal",
        "cover_letter_input": "Plak je motivatiebrief",
        "cv_input": "Plak je cv",
        "copy_ready": "Kopieerklare output",
        "resume_score": "CV-score",
        "ats_score": "ATS-gereedheid",
        "strengths": "Topsterktes",
        "improvements": "Topverbeteringen",
        "raw_resume_extract": "Ruwe cv-extractie",
        "job_fit_score": "Vacaturematch",
        "skill_gap_score": "Vaardigheidskloof",
        "interview_score": "Interview",
        "resume_insights": "CV-inzichten",
        "update_resume": "CV bijwerken",
    }
}

def ui_lang() -> str:
    current = st.session_state.get("ui_language", "English")
    return current if current in UI_TEXT else "English"

def txt(key: str) -> str:
    return UI_TEXT[ui_lang()].get(key, key)

# =========================================================
# SESSION STATE
# =========================================================
defaults = {
    "page": "onboarding",
    "onboarding_complete": False,
    "country": "",
    "ui_language": "English",
    "response_language": "English",
    "cv_mode": "Upload CV",
    "cv_text": "",
    "dashboard_action": "Dashboard",

    # extracted
    "profile_summary": "",
    "current_role_detected": "",
    "key_skills_detected": "",
    "suggested_roles_detected": "",
    "cv_profile_raw": "",

    # dashboard analysis
    "cv_score_value": None,
    "ats_score_value": None,
    "resume_strengths": "",
    "resume_improvements": "",
    "latest_resume_dashboard_analysis": "",

    # other scores
    "job_fit_score_value": None,
    "skill_gap_score_value": None,
    "interview_score_value": None,

    # outputs
    "latest_job_analysis": "",
    "latest_cv_analysis": "",
    "latest_interview": "",
    "latest_skill_gap": "",
    "latest_cover_letter": "",
    "latest_language_support": "",
    "latest_cv_translation": "",
    "latest_cover_letter_translation": "",
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# =========================================================
# HELPERS
# =========================================================
def google_search_url(query: str) -> str:
    return "https://www.google.com/search?q=" + urllib.parse.quote(query)

def extract_pdf_text(uploaded_file) -> str:
    text = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()

def run_ai_prompt(
    prompt: str,
    system_addition: str = "",
    force_language: str = None,
    force_english: bool = False
) -> str:
    if not can_make_request():
        return "ERROR: Usage limit reached. Please try again later."

    register_request()

    if force_english:
        answer_lang = "English"
    elif force_language:
        answer_lang = force_language
    else:
        answer_lang = st.session_state.ui_language

    system_prompt = f"""
You are WorkZo AI, a professional career assistant.

Always respond ONLY in {answer_lang}.
Be clear, structured, practical, and helpful for job seekers.
{system_addition}
""".strip()

    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        return res.choices[0].message.content.strip()
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {str(e)}"

def render_error_or_success(result: str):
    if result.startswith("ERROR:"):
        st.error(txt("ai_unavailable"))
        st.caption(result)
        return False
    return True

def parse_score(text: str) -> Optional[int]:
    if not text:
        return None

    match = re.search(r'(\d{1,3})\s*/\s*100', text)
    if match:
        value = int(match.group(1))
        if 0 <= value <= 100:
            return value

    match = re.search(r'(?<!\d)(\d{1,3})(?!\d)', text)
    if match:
        value = int(match.group(1))
        if 0 <= value <= 100:
            return value

    return None

def numbered_sections_to_markdown(text: str) -> Dict[str, str]:
    sections = {}
    pattern = r'(?m)^\s*(\d+)\.\s*(.+?)\s*$'
    matches = list(re.finditer(pattern, text))
    if not matches:
        return {"Result": text}

    for i, match in enumerate(matches):
        title = match.group(2).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        sections[title] = body
    return sections

def render_section_cards(result: str, default_expand: bool = False):
    if not render_error_or_success(result):
        return
    sections = numbered_sections_to_markdown(result)
    for title, body in sections.items():
        with st.expander(title, expanded=default_expand):
            st.write(body if body else "—")

def score_display(value: Optional[int]) -> str:
    return f"{value}/100" if value is not None else "—"

def show_gauge(score: Optional[int], title: str):
    if score is None:
        st.info(txt("not_analyzed"))
        return

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={"text": title},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"thickness": 0.35},
            "steps": [
                {"range": [0, 40], "color": "#f8d7da"},
                {"range": [40, 70], "color": "#fff3cd"},
                {"range": [70, 100], "color": "#d1e7dd"},
            ],
        }
    ))
    fig.update_layout(
        height=260,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    st.plotly_chart(fig, use_container_width=True)

def extract_cv_profile(cv_text: str):
    prompt = f"""
Read this CV and extract a short profile for the dashboard.

IMPORTANT:
- Keep the section headings EXACTLY in English.
- You may write the content in English.
- Do not translate the headings.

Return in this exact structure:

1. Professional Summary
2. Current / Likely Role
3. Key Skills
4. Suggested Roles

CV:
{cv_text}
"""

    result = run_ai_prompt(
    prompt,
    system_addition="""
For this task, keep the section titles EXACTLY as:
1. Professional Summary
2. Current / Likely Role
3. Key Skills
4. Suggested Roles

Do not translate these headings.
""",
    force_english=True
)

    if result.startswith("ERROR:"):
        return

    st.session_state.cv_profile_raw = result

    sections = numbered_sections_to_markdown(result)

    st.session_state.profile_summary = sections.get("Professional Summary", "").strip()
    st.session_state.current_role_detected = sections.get("Current / Likely Role", "").strip()
    st.session_state.key_skills_detected = sections.get("Key Skills", "").strip()
    st.session_state.suggested_roles_detected = sections.get("Suggested Roles", "").strip()

def analyze_resume_dashboard(cv_text: str):
    prompt = f"""
Country: {st.session_state.country}

Analyze this CV for the dashboard.

IMPORTANT:
- Keep the section headings EXACTLY in English.
- Do not translate the headings.

Return in this exact structure:

1. CV Score
Give only the score from 0 to 100.

2. ATS Score
Give only the score from 0 to 100.

3. Top Strengths
List 3 to 5 strengths.

4. Top Improvements
List 3 to 5 practical improvements.

CV:
{cv_text}
"""

    result = run_ai_prompt(
    prompt,
    system_addition="""
For this task, keep the section titles EXACTLY as:
1. CV Score
2. ATS Score
3. Top Strengths
4. Top Improvements

Do not translate these headings.
""",
    force_english=True
)

    if result.startswith("ERROR:"):
        return

    st.session_state.latest_resume_dashboard_analysis = result

    sections = numbered_sections_to_markdown(result)

    cv_score_text = sections.get("CV Score", "").strip()
    ats_score_text = sections.get("ATS Score", "").strip()

    st.session_state.cv_score_value = parse_score(cv_score_text)
    st.session_state.ats_score_value = parse_score(ats_score_text)
    st.session_state.resume_strengths = sections.get("Top Strengths", "").strip()
    st.session_state.resume_improvements = sections.get("Top Improvements", "").strip()

def reset_onboarding():
    preserve = {
        "request_count": st.session_state.request_count,
        "first_request_time": st.session_state.first_request_time,
        "ui_language": st.session_state.ui_language,
        "response_language": st.session_state.response_language,
    }
    for key in list(st.session_state.keys()):
        del st.session_state[key]

    for key, value in defaults.items():
        st.session_state[key] = value

    for key, value in preserve.items():
        st.session_state[key] = value

    st.session_state.page = "onboarding"
    st.session_state.onboarding_complete = False

# =========================================================
# HEADER
# =========================================================
st.markdown(f"""
<h1>
🚀 WORKZO AI
<span class="beta-badge">BETA V2.1</span>
</h1>
<h4>{txt("title")}</h4>
<p style="color: gray;">{txt("subtitle")}</p>
""", unsafe_allow_html=True)

# =========================================================
# TOP BAR
# =========================================================
top1, top2, top3 = st.columns([5, 2, 2])
with top2:
    st.session_state.ui_language = st.selectbox(
        txt("ui_language"),
        ["English", "German", "Dutch"],
        index=["English", "German", "Dutch"].index(st.session_state.ui_language)
        if st.session_state.ui_language in ["English", "German", "Dutch"] else 0
    )


# =========================================================
# ONBOARDING
# =========================================================
def show_onboarding():
    st.subheader(txt("onboarding_title"))
    st.caption(txt("onboarding_subtitle"))

    countries = ["", "Germany", "Austria", "Netherlands", "India", "France", "Canada", "United Kingdom", "United States", "Other"]

    country = st.selectbox(
        txt("country"),
        countries,
        format_func=lambda x: "Select" if x == "" else x
    )

    cv_mode_display = st.radio(
        txt("resume_input"),
        [txt("upload_cv"), txt("create_cv")],
        horizontal=True
    )
    cv_mode = "Upload CV" if cv_mode_display == txt("upload_cv") else "Create CV"

    with st.form("onboarding_form_v21"):
        cv_text_input = ""
        full_name = ""
        email = ""
        phone = ""
        summary = ""
        skills = ""
        experience = ""
        education = ""

        if cv_mode == "Upload CV":
            uploaded_file = st.file_uploader(
                txt("upload_resume"),
                type=["txt", "pdf"]
            )

            if uploaded_file is not None:
                if uploaded_file.type == "text/plain":
                    cv_text_input = uploaded_file.read().decode("utf-8")
                elif uploaded_file.type == "application/pdf":
                    try:
                        cv_text_input = extract_pdf_text(uploaded_file)
                    except Exception as e:
                        st.error(f"PDF read error: {e}")
                else:
                    st.error(txt("unsupported_file"))

        else:
            st.markdown(f"#### {txt('create_resume')}")
            full_name = st.text_input(txt("full_name"))
            email = st.text_input(txt("email"))
            phone = st.text_input(txt("phone"))
            summary = st.text_area(txt("summary"))
            skills = st.text_area(txt("skills"))
            experience = st.text_area(txt("experience"))
            education = st.text_area(txt("education"))

            if any([
                full_name.strip(),
                email.strip(),
                phone.strip(),
                summary.strip(),
                skills.strip(),
                experience.strip(),
                education.strip(),
            ]):
                cv_text_input = f"""
Name: {full_name}
Email: {email}
Phone: {phone}

Professional Summary:
{summary}

Skills:
{skills}

Work Experience:
{experience}

Education:
{education}
                """.strip()

        submitted = st.form_submit_button(txt("continue"))

        if submitted:
            if not country:
                st.warning(txt("warn_country"))
                return

            if cv_mode == "Upload CV":
                if not cv_text_input.strip():
                    st.warning(txt("warn_upload_cv"))
                    return
            else:
                if not full_name.strip():
                    st.warning(txt("warn_full_name"))
                    return
                if not summary.strip():
                    st.warning(txt("warn_summary"))
                    return
                if not skills.strip():
                    st.warning(txt("warn_skills"))
                    return
                if not experience.strip():
                    st.warning(txt("warn_experience"))
                    return
                if not education.strip():
                    st.warning(txt("warn_education"))
                    return

            st.session_state.country = country
            st.session_state.cv_mode = cv_mode
            st.session_state.cv_text = cv_text_input
            st.session_state.onboarding_complete = True
            st.session_state.page = "dashboard"

            with st.spinner("Reading your resume and preparing dashboard..."):
                extract_cv_profile(st.session_state.cv_text)
                analyze_resume_dashboard(st.session_state.cv_text)

            st.rerun()

# =========================================================
# DASHBOARD
# =========================================================
def show_dashboard():
    with st.sidebar:
        st.title("WORKZO AI")
        st.caption("⚡ Beta V2.1")
        st.caption(f"🌍 {st.session_state.country}")

        st.markdown(f"### {txt('actions')}")
        action_labels = [
            txt("dashboard"),
            txt("update_resume"),
            txt("understand_job"),
            txt("improve_cv"),
            txt("career_communication"),
            txt("find_jobs"),
            txt("mock_interview"),
            txt("skill_gap"),
            txt("career_roadmap"),
            txt("cv_translator"),
            txt("cover_letter_generator"),
            txt("cover_letter_translator"),
            txt("language_support"),
        ]
        page = st.radio("Navigation", action_labels, label_visibility="collapsed")

        

        st.markdown("---")
        if st.button(txt("edit_setup"), use_container_width=True):
            reset_onboarding()
            st.rerun()


    # =====================================================
    # DASHBOARD
    # =====================================================
    if page == txt("dashboard"):
        st.subheader(txt("dashboard"))
        st.caption(txt("start_here_intro"))

        col1, col2 = st.columns([1, 1.2])

        with col1:
            st.markdown(f"### {txt('resume_score')}")
            show_gauge(st.session_state.cv_score_value, txt("resume_score"))

            score_col1, score_col2 = st.columns(2)
            with score_col1:
                st.metric(txt("resume_score"), score_display(st.session_state.cv_score_value))
            with score_col2:
                st.metric(txt("ats_score"), score_display(st.session_state.ats_score_value))

        with col2:
            st.markdown(f"### {txt('resume_insights')}")
            st.markdown(f"**{txt('detected_role')}:**")
            st.write(st.session_state.current_role_detected or txt("not_analyzed"))

            st.markdown(f"**{txt('detected_summary')}:**")
            st.write(st.session_state.profile_summary or txt("not_analyzed"))

        a, b = st.columns(2)
        with a:
            st.markdown(f"### {txt('detected_skills')}")
            if st.session_state.key_skills_detected:
                st.markdown(st.session_state.key_skills_detected)
            else:
                st.info(txt("not_analyzed"))

            st.markdown(f"### {txt('strengths')}")
            if st.session_state.resume_strengths:
                st.markdown(st.session_state.resume_strengths)
            else:
                st.info(txt("not_analyzed"))

        with b:
            st.markdown(f"### {txt('suggested_roles')}")
            if st.session_state.suggested_roles_detected:
                st.markdown(st.session_state.suggested_roles_detected)
            else:
                st.info(txt("not_analyzed"))
        
            st.markdown(f"### {txt('improvements')}")
            if st.session_state.resume_improvements:
                st.markdown(st.session_state.resume_improvements)
            else:
                st.info(txt("not_analyzed"))

        refresh1, refresh2 = st.columns([1, 3])
        with refresh1:
             if st.button("Refresh Resume Analysis"):
                with st.spinner("Refreshing..."):
                    extract_cv_profile(st.session_state.cv_text)
                    analyze_resume_dashboard(st.session_state.cv_text)
                st.success("Dashboard updated.")
                st.rerun()

    # =====================================================
    # UPDATE RESUME
    # =====================================================
    elif page == txt("update_resume"):
        st.subheader(txt("update_resume"))
        st.caption(
            "Upload or use your current resume, then describe what has changed. "
            "WorkZo will update and rewrite the resume for you."
        )

        current_resume = st.text_area(
            "Current Resume",
            value=st.session_state.cv_text,
            height=260,
            key="resume_update_current_resume"
        )

        update_instructions = st.text_area(
            "What should be updated?",
            height=180,
            key="resume_update_instructions",
            placeholder=(
                "Example: I now have 8 years of experience instead of 4. "
                "My current title is Senior Manager. Add leadership, stakeholder "
                "management, budgeting, and my latest responsibilities."
            )
        )

        if st.button("Generate Updated Resume", key="btn_generate_updated_resume"):
            if not current_resume.strip():
                st.warning("Please provide your current resume.")
            elif not update_instructions.strip():
                st.warning("Please describe what needs to be updated.")
            else:
                with st.spinner("Updating your resume..."):
                    prompt = f"""
    Country: {st.session_state.country}

    You are a professional resume editor.

    The user has an older resume and has provided update instructions.
    Your task is to update the resume based on the user's instructions.

    Rules:
    - Keep the resume professional and realistic.
    - Preserve useful information unless the user wants it changed.
    - Update titles, years of experience, skills, and role details where relevant.
    - Do not invent employers, dates, or achievements unless clearly implied by the user.
    - Keep the formatting clean and readable.
    - If something is unclear, mention it in the notes section.

    Return in this exact structure:

    1. Updated Professional Summary
    2. Updated Experience Changes
    3. Updated Skills
    4. Full Updated Resume
    5. Notes / Missing Details to Confirm

    Current Resume:
    {current_resume}

    User Update Instructions:
    {update_instructions}
    """
                    result = run_ai_prompt(prompt)

                    if render_error_or_success(result):
                        st.session_state.latest_cv_analysis = result
                        render_section_cards(result, default_expand=True)

        st.markdown("### Use the updated resume for your dashboard")

        use_updated_resume_text = st.text_area(
            "Paste the full updated resume here if you want to save it as your new dashboard resume",
            height=220,
            key="use_updated_resume_text",
            placeholder="After generating the updated resume, copy section 4 'Full Updated Resume' and paste it here."
        )

        if st.button("Save as My New Resume", key="btn_save_updated_resume"):
            if not use_updated_resume_text.strip():
                st.warning("Please paste the full updated resume first.")
            else:
                with st.spinner("Saving updated resume to dashboard..."):
                    st.session_state.cv_text = use_updated_resume_text

                    st.session_state.profile_summary = ""
                    st.session_state.current_role_detected = ""
                    st.session_state.key_skills_detected = ""
                    st.session_state.suggested_roles_detected = ""
                    st.session_state.cv_profile_raw = ""

                    st.session_state.cv_score_value = None
                    st.session_state.ats_score_value = None
                    st.session_state.resume_strengths = ""
                    st.session_state.resume_improvements = ""
                    st.session_state.latest_resume_dashboard_analysis = ""

                    extract_cv_profile(st.session_state.cv_text)
                    analyze_resume_dashboard(st.session_state.cv_text)

                st.success("Your dashboard resume has been updated.")
                st.rerun()

        
    # =====================================================
    # UNDERSTAND JOB
    # =====================================================
    elif page == txt("understand_job"):
        st.subheader(txt("understand_job"))
        job_desc = st.text_area(txt("job_desc"), key="job_desc_v21", height=220)

        if st.button(txt("analyze"), key="btn_understand_job_v21"):
            if not job_desc.strip():
                st.warning("Please enter a job description.")
            else:
                with st.spinner("Analyzing..."):
                    prompt = f"""
Country: {st.session_state.country}
Candidate CV:
{st.session_state.cv_text}

Analyze this job description for the candidate.

Return in this exact order:

1. Overview
2. Main Responsibilities
3. Required Skills
4. Compatibility Score
Give a score from 0 to 100 and explain briefly.
5. Quick Skill Gap
- Skills the candidate already has
- Skills missing or weak
- What to improve first

Job description:
{job_desc}
"""
                    result = run_ai_prompt(prompt)
                    if render_error_or_success(result):
                        st.session_state.latest_job_analysis = result
                        st.session_state.job_fit_score_value = parse_score(result)
                        st.markdown(f"### {txt('job_fit_analysis')}")
                        render_section_cards(result, default_expand=True)

    # =====================================================
    # IMPROVE CV
    # =====================================================
    elif page == txt("improve_cv"):
        st.subheader(txt("improve_cv"))
        current_cv = st.text_area(txt("your_cv"), value=st.session_state.cv_text, height=260)
        job_desc_cv = st.text_area(txt("target_job"), height=220)

        if st.button(txt("improve"), key="btn_improve_cv_v21"):
            if not current_cv.strip() or not job_desc_cv.strip():
                st.warning("Please provide both CV and job description.")
            else:
                with st.spinner("Improving CV..."):
                    prompt = f"""
Country: {st.session_state.country}

Improve this CV for the target job.

Return:
1. Better Summary
2. Improved Bullet Points
3. Skills to Highlight
4. ATS-Friendly Suggestions

CV:
{current_cv}

Job description:
{job_desc_cv}
"""
                    result = run_ai_prompt(prompt)
                    if render_error_or_success(result):
                        st.session_state.latest_cv_analysis = result
                        render_section_cards(result, default_expand=True)

    # =====================================================
    # CAREER COMMUNICATION
    # =====================================================
    elif page == txt("career_communication"):
        st.subheader(txt("career_communication"))

        practice_mode = st.selectbox(
            "Practice mode",
            [
                "Self Introduction",
                "Interview Answer Practice",
                "HR Call Practice",
                "Workplace Conversation",
                "Email / Message Improvement"
            ]
        )
        practice_job = st.text_input("Target job (optional)")
        user_input = st.text_area("Type your answer or message", height=220)

        if st.button("Practice Communication", key="btn_career_comm_v21"):
            if not user_input.strip():
                st.warning("Please enter a message or answer to practice.")
            else:
                with st.spinner("Checking..."):
                    prompt = f"""
Country: {st.session_state.country}
Practice language: {st.session_state.response_language}
Practice mode: {practice_mode}
Target job: {practice_job if practice_job.strip() else "Not specified"}

User answer:
{user_input}

Act as a career communication coach.

Return in this exact structure:

1. Corrected Version
2. Natural Professional Version
3. Explanation
4. Interview / Career Tip
5. Next Question
"""
                    result = run_ai_prompt(prompt)
                    if render_error_or_success(result):
                        st.markdown(f"### {txt('career_comm_result')}")
                        render_section_cards(result, default_expand=True)

    # =====================================================
    # FIND JOBS
    # =====================================================
    elif page == txt("find_jobs"):
        st.subheader(txt("find_jobs"))
        location = st.text_input(txt("preferred_location"))
        cv_for_jobs = st.text_area(txt("your_cv"), value=st.session_state.cv_text, height=260)

        if st.button(txt("generate"), key="btn_find_jobs_v21"):
            if not cv_for_jobs.strip():
                st.warning("Please provide your CV.")
            else:
                with st.spinner("Finding jobs..."):
                    city = location.strip() if location.strip() else st.session_state.country

                    prompt = f"""
You are an AI career assistant helping users find real job opportunities.

Country: {st.session_state.country}
Preferred location: {city}

Candidate CV:
{cv_for_jobs}

Return in this exact structure:

1. Best-Match Roles
2. Match Reason
3. Recommended Seniority
4. Location-Based Job Searches
5. Direct Job Search Links
6. Work Mode Suggestions
7. Application Priority
"""
                    result = run_ai_prompt(prompt)
                    if render_error_or_success(result):
                        render_section_cards(result, default_expand=True)

                        sample_queries = [
                            f"Data Analyst jobs in {city}",
                            f"IT Support jobs in {city}",
                            f"English speaking jobs in {city}",
                            f"Remote jobs in {city}",
                        ]
                        st.markdown(f"### {txt('search_queries')}")
                        for q in sample_queries:
                            st.markdown(f"- [{q}]({google_search_url(q)})")
                        st.caption(txt("platform_hint"))

    # =====================================================
    # MOCK INTERVIEW
    # =====================================================
    elif page == txt("mock_interview"):
        st.subheader(txt("mock_interview"))
        interview_role = st.text_input(txt("job_title"))
        interview_language = st.selectbox(
            txt("interview_language"),
            ["English", "German", "Dutch"]
        )
        interview_background = st.text_area(txt("background"), value=st.session_state.cv_text, height=240)

        if st.button(txt("generate"), key="btn_mock_interview_v21"):
            if not interview_role.strip():
                st.warning("Please enter a job title.")
            else:
                with st.spinner("Preparing interview practice..."):
                    prompt = f"""
Country: {st.session_state.country}
Interview language: {interview_language}
Job title: {interview_role}

Candidate background:
{interview_background}

Return:
1. Interview Readiness Score
2. 5 Likely Interview Questions
3. Sample Answers
4. Improvement Tips
5. Common Mistakes to Avoid
"""
                    result = run_ai_prompt(prompt)
                    if render_error_or_success(result):
                        st.session_state.latest_interview = result
                        st.session_state.interview_score_value = parse_score(result)
                        render_section_cards(result, default_expand=True)

    # =====================================================
    # SKILL GAP
    # =====================================================
    elif page == txt("skill_gap"):
        st.subheader(txt("skill_gap"))

        target_role_gap = st.text_input(txt("target_role"))
        current_cv_gap = st.text_area(txt("your_cv"), value=st.session_state.cv_text, height=260)

        if st.button(txt("analyze"), key="btn_skill_gap_v21"):
            if not target_role_gap.strip() or not current_cv_gap.strip():
                st.warning("Please enter your target role and your CV/profile.")
            else:
                with st.spinner("Analyzing skill gap..."):
                    prompt = f"""
Country: {st.session_state.country}
Target role: {target_role_gap}

Analyze the user's profile and identify the gap.

Return in this exact structure:

1. Skill Gap Score
2. Current Strengths
3. Missing Skills
4. Missing Tools / Certifications
5. Communication / Language Gaps
6. Priority Gap to Fix First
7. Ask 2 Follow-up Questions

User CV / Profile:
{current_cv_gap}
"""
                    result = run_ai_prompt(prompt)
                    if render_error_or_success(result):
                        st.session_state.latest_skill_gap = result
                        st.session_state.skill_gap_score_value = parse_score(result)
                        render_section_cards(result, default_expand=True)

        st.markdown("### Follow-up")
        follow_up_gap = st.text_input("Ask a follow-up question about your skill gap")
        if st.button("Discuss My Gaps", key="btn_gap_followup_v21"):
            if not follow_up_gap.strip():
                st.warning("Please enter a question.")
            else:
                with st.spinner("Thinking..."):
                    prompt = f"""
Country: {st.session_state.country}

User profile:
{current_cv_gap}

Target role:
{target_role_gap}

User follow-up question:
{follow_up_gap}

Answer like an AI career coach. Be practical, specific, and action-oriented.
"""
                    result = run_ai_prompt(prompt)
                    render_section_cards(result, default_expand=True)

    # =====================================================
    # CAREER ROADMAP
    # =====================================================
    elif page == txt("career_roadmap"):
        st.subheader(txt("career_roadmap"))
        current_role = st.text_input(txt("current_role"), value=st.session_state.current_role_detected)
        target_role_roadmap = st.text_input(txt("target_role"))
        current_profile = st.text_area(txt("current_profile"), value=st.session_state.cv_text, height=250)

        if st.button(txt("generate"), key="btn_roadmap_v21"):
            if not current_role.strip() or not target_role_roadmap.strip() or not current_profile.strip():
                st.warning("Please fill in your current role, target role, and profile.")
            else:
                with st.spinner("Generating roadmap..."):
                    prompt = f"""
Country: {st.session_state.country}
Current role: {current_role}
Target role: {target_role_roadmap}

Create a practical action plan.

Return in this exact structure:

1. Goal
2. 30-Day Plan
3. 90-Day Plan
4. 6-Month Plan
5. Projects to Build
6. Certifications / Learning
7. Job Application Strategy
8. One Motivating Next Step for Today

User profile:
{current_profile}
"""
                    result = run_ai_prompt(prompt)
                    render_section_cards(result, default_expand=True)

    # =====================================================
    # CV TRANSLATOR
    # =====================================================
    elif page == txt("cv_translator"):
        st.subheader(txt("cv_translator"))

        col1, col2 = st.columns(2)
        with col1:
            source_lang = st.selectbox(txt("translator_source"), ["English", "German", "Dutch"])
        with col2:
            target_lang = st.selectbox(txt("translator_target"), ["English", "German", "Dutch"], index=1)

        cv_input = st.text_area(txt("cv_input"), value=st.session_state.cv_text, height=280)

        if st.button(txt("translate"), key="btn_cv_translate_v21"):
            if not cv_input.strip():
                st.warning("Please provide your CV.")
            else:
                with st.spinner("Translating CV..."):
                    prompt = f"""
    Translate this CV from {source_lang} to {target_lang}.

    Requirements:
    - Keep the structure professional.
    - Preserve meaning and achievements.
    - Make it sound natural for job applications.
    - Do not add new experience that is not in the original.
    - Keep section headings clear.
    - Keep bullet points readable.
    - Do not merge everything into one paragraph.

    CV:
    {cv_input}
    """
                    result = run_ai_prompt(
                        prompt,
                        system_addition=f"Translate the content fully into {target_lang}. Return only the translated CV in {target_lang}.",
                        force_language=target_lang
                    )

                    if render_error_or_success(result):
                        st.session_state.latest_cv_translation = result
                        st.markdown(f"### {txt('copy_ready')}")
                        st.text_area("Translated CV", value=result, height=350)

    # =====================================================
    # COVER LETTER GENERATOR
    # =====================================================
    elif page == txt("cover_letter_generator"):
        st.subheader(txt("cover_letter_generator"))

        company_name = st.text_input("Company Name")
        role_name = st.text_input(txt("target_role"))
        job_desc_letter = st.text_area(txt("job_desc"), height=220)

        if st.button(txt("generate"), key="btn_cover_letter_v21"):
            if not role_name.strip() or not job_desc_letter.strip():
                st.warning("Please enter a target role and job description.")
            else:
                with st.spinner("Generating cover letter..."):
                    prompt = f"""
Country: {st.session_state.country}
Target role: {role_name}
Company: {company_name if company_name.strip() else "Not specified"}

Candidate CV:
{st.session_state.cv_text}

Job description:
{job_desc_letter}

Write a strong professional cover letter.

Return in this exact structure:

1. Full Cover Letter
2. Short Email Version
3. 3 Customization Tips
"""
                    result = run_ai_prompt(prompt)
                    if render_error_or_success(result):
                        st.session_state.latest_cover_letter = result
                        render_section_cards(result, default_expand=True)

    # =====================================================
    # COVER LETTER TRANSLATOR
    # =====================================================
    elif page == txt("cover_letter_translator"):
        st.subheader(txt("cover_letter_translator"))

        col1, col2 = st.columns(2)
        with col1:
            source_lang = st.selectbox(txt("translator_source"), ["English", "German", "Dutch"], key="cl_source_v21")
        with col2:
            target_lang = st.selectbox(txt("translator_target"), ["English", "German", "Dutch"], index=1, key="cl_target_v21")

        cover_letter_input = st.text_area(
            txt("cover_letter_input"),
            value=st.session_state.latest_cover_letter if st.session_state.latest_cover_letter else "",
            height=280
        )

        if st.button(txt("translate"), key="btn_cover_letter_translate_v21"):
            if not cover_letter_input.strip():
                st.warning("Please paste your cover letter.")
            else:
                with st.spinner("Translating cover letter..."):
                    prompt = f"""
    Translate this cover letter from {source_lang} to {target_lang}.

    Requirements:
    - Preserve the professional tone.
    - Keep the meaning and structure.
    - Make it sound natural for job applications in the target language.
    - Do not invent qualifications.
    - Keep paragraph breaks.

    Cover letter:
    {cover_letter_input}
    """
                    result = run_ai_prompt(
                        prompt,
                        system_addition=f"Translate the content fully into {target_lang}. Return only the translated cover letter in {target_lang}.",
                        force_language=target_lang
                    )

                    if render_error_or_success(result):
                        st.session_state.latest_cover_letter_translation = result
                        st.markdown(f"### {txt('copy_ready')}")
                        st.text_area("Translated Cover Letter", value=result, height=320)

    # =====================================================
    # LANGUAGE SUPPORT
    # =====================================================
    elif page == txt("language_support"):
        st.subheader(txt("language_support"))

        support_task = st.selectbox(
            txt("language_support_task"),
            [
                "Rewrite email professionally",
                "Simplify my answer",
                "Explain job description in simple language",
                "Improve interview answer",
                "Create formal application phrases",
            ]
        )
        support_text = st.text_area(txt("enter_text"), height=220)

        if st.button(txt("generate"), key="btn_language_support_v21"):
            if not support_text.strip():
                st.warning("Please enter some text.")
            else:
                with st.spinner("Generating support..."):
                    prompt = f"""
Country: {st.session_state.country}
Task: {support_task}
Response language: {st.session_state.response_language}

Input text:
{support_text}

Return in this exact structure:

1. Improved Version
2. Simpler Version
3. Useful Vocabulary / Phrases
4. Short Explanation in English
"""
                    result = run_ai_prompt(prompt)
                    if render_error_or_success(result):
                        st.session_state.latest_language_support = result
                        sections = numbered_sections_to_markdown(result)

                        col_left, col_right = st.columns([1.2, 1])

                        with col_left:
                            st.markdown("### Improved Version")
                            st.markdown(sections.get("Improved Version", "—"))

                            st.markdown("### Simpler Version")
                            st.markdown(sections.get("Simpler Version", "—"))

                        with col_right:
                            with st.expander("Useful Vocabulary / Phrases", expanded=True):
                                st.write(sections.get("Useful Vocabulary / Phrases", "—"))
                            with st.expander("Short Explanation in English", expanded=False):
                                st.write(sections.get("Short Explanation in English", "—"))

    st.divider()
    st.caption("MVP • WORKZO AI V2.1 • Dashboard-first resume experience")

# =========================================================
# ROUTER
# =========================================================
if not st.session_state.onboarding_complete or st.session_state.page == "onboarding":
    show_onboarding()
else:
    show_dashboard()