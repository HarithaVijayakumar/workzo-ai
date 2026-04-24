
import os
import re
import time
import json
import hashlib
from io import BytesIO
import urllib.parse
import urllib.request
from typing import Dict, Optional, List, Tuple

import pdfplumber
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

try:
    import pycountry
except ImportError:
    pycountry = None

try:
    import geonamescache
except ImportError:
    geonamescache = None

try:
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.pagesizes import A4
except ImportError:
    SimpleDocTemplate = None
    Paragraph = None
    Spacer = None
    getSampleStyleSheet = None
    A4 = None


def get_streamlit_secret(key: str, default=None):
    try:
        return st.secrets[key]
    except Exception:
        return default

# =========================================================
# PAGE CONFIG + LOGO PATH
# =========================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(BASE_DIR, "logo.png")

st.set_page_config(
    page_title="WorkZo AI",
    page_icon=LOGO_PATH if os.path.exists(LOGO_PATH) else "🚀",
    layout="wide"
)

# =========================================================
# LOAD ENV
# =========================================================
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY") or get_streamlit_secret("OPENAI_API_KEY")
if not api_key:
    st.error("OPENAI_API_KEY not found. Please check your .env file or Streamlit secrets.")
    st.stop()

client = OpenAI(api_key=api_key)

# =========================================================
# RATE LIMITING
# =========================================================
MAX_REQUESTS_PER_HOUR = 25
SCORING_VERSION = "v5.0"

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
    .stApp {
        background: linear-gradient(180deg, #0b1020 0%, #111827 22%, #0f172a 100%);
    }
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    .beta-badge {
        background: linear-gradient(135deg, #14b8a6, #2563eb);
        color: white;
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 12px;
        display: inline-block;
        font-weight: 600;
    }
    .hero-card {
        background: linear-gradient(135deg, rgba(37,99,235,0.22), rgba(20,184,166,0.16));
        border: 1px solid rgba(148,163,184,0.18);
        border-radius: 24px;
        padding: 20px 22px;
        box-shadow: 0 12px 35px rgba(2,6,23,0.25);
        margin-bottom: 14px;
    }
    .glass-card {
        border: 1px solid rgba(148,163,184,0.16);
        border-radius: 20px;
        padding: 16px;
        background: rgba(15,23,42,0.55);
        backdrop-filter: blur(8px);
        box-shadow: 0 8px 24px rgba(2,6,23,0.18);
        margin-bottom: 12px;
    }
    .metric-card {
        border: 1px solid rgba(148,163,184,0.16);
        border-radius: 20px;
        padding: 16px;
        background: linear-gradient(180deg, rgba(30,41,59,0.86), rgba(15,23,42,0.74));
        min-height: 116px;
        box-shadow: 0 8px 24px rgba(2,6,23,0.18);
    }
    .metric-label {
        color: #94a3b8;
        font-size: 0.92rem;
        margin-bottom: 8px;
    }
    .metric-value {
        color: white;
        font-size: 1.8rem;
        font-weight: 700;
        line-height: 1.1;
        margin-bottom: 6px;
    }
    .metric-foot {
        color: #cbd5e1;
        font-size: 0.9rem;
    }
    .card {
        border: 1px solid rgba(148,163,184,0.16);
        border-radius: 18px;
        padding: 16px;
        background: rgba(15,23,42,0.58);
        margin-bottom: 12px;
    }
    .section-title {
        font-size: 1.05rem;
        font-weight: 700;
        margin-bottom: 8px;
        color: #f8fafc;
    }
    .small-muted {
        color: #94a3b8;
        font-size: 0.95rem;
    }
    .pill {
        display: inline-block;
        padding: 6px 10px;
        border-radius: 999px;
        background: rgba(37,99,235,0.12);
        border: 1px solid rgba(96,165,250,0.18);
        color: #dbeafe;
        margin-right: 6px;
        margin-bottom: 6px;
        font-size: 0.9rem;
    }
    .feature-tile {
        border: 1px solid rgba(148,163,184,0.16);
        border-radius: 18px;
        padding: 16px;
        min-height: 140px;
        background: rgba(15,23,42,0.58);
        margin-bottom: 10px;
    }
    .feature-title {
        font-size: 1rem;
        font-weight: 700;
        color: #f8fafc;
        margin-bottom: 6px;
    }
    .feature-copy {
        color: #cbd5e1;
        font-size: 0.92rem;
        line-height: 1.45;
    }
    .workflow-step {
        border: 1px solid rgba(148,163,184,0.16);
        border-radius: 16px;
        padding: 12px 14px;
        background: rgba(30,41,59,0.5);
        margin-bottom: 8px;
    }
    div[data-testid="stButton"] > button {
        border-radius: 14px;
        border: 1px solid rgba(96,165,250,0.18);
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
        "dashboard": "Dashboard",
        "actions": "Explore tools",
        "understand_job": "Understand Job",
        "improve_cv": "Improve CV",
        "career_communication": "Career Communication",
        "find_jobs": "Find Jobs",
        "mock_interview": "Mock Interview",
        "skill_gap": "Skill Gap",
        "career_roadmap": "Career Roadmap",
        "job_assist": "Job Assist",
        "document_tools": "Document Tools",
        "cv_translator": "CV Translator",
        "cover_letter_generator": "Cover Letter Generator",
        "cover_letter_translator": "Cover Letter Translator",
        "workobot": "Work-O-Bot",
        "workobot_sub": "AI career and language coach",
        "start_here_intro": "Your dashboard shows a stable resume analysis, ATS readiness, and extracted profile. Use the menu on the left for deeper tools.",
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
        "ats_score": "ATS Score",
        "strengths": "Top Strengths",
        "improvements": "Top Improvements",
        "job_fit_score": "Job Fit",
        "skill_gap_score": "Skill Gap",
        "interview_score": "Interview",
        "resume_insights": "Resume Insights",
        "update_resume": "Update My Resume",
        "top_countries_fit": "Top Countries for This Resume",
        "country_fit_note": "Likely strongest markets based on CV language, profile, and transferability.",
        "detected_country": "Detected Country",
        "refresh_resume": "Re-analyze Resume",
        "save_resume": "Save as My New Resume",
        "document_hub_caption": "Keep all writing and translation tools in one place.",
        "quick_prompts": "Quick prompts",
        "chat_mode": "Mode",
        "chat_placeholder": "Ask Work-O-Bot anything...",
        "clear_chat": "Clear Chat",
        "preferred_language": "Preferred Language",
        "user_status": "Current Career Situation",
        "fresh_graduate": "Fresh graduate / student",
        "career_changer": "Career changer",
        "migrant": "Planning to migrate / applying abroad",
        "local_jobseeker": "Looking for jobs locally",
        "experienced": "Experienced professional",
        "returning": "Returning after a career break",
        "guided_cv_builder": "Guided CV Builder",
        "generate_cv": "Generate CV with AI",
        "extra_cv_info": "Would you like to add more information?",
        "country_readiness": "Country Readiness",
        "next_steps": "What should you do next?",
        "cv_template_builder": "Country CV Template Builder",
        "migration_country": "Which country do you want to move/apply to?",
        "chosen_country_resume_score": "Resume readiness for chosen country",
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
        "dashboard": "Dashboard",
        "actions": "Tools erkunden",
        "understand_job": "Stelle verstehen",
        "improve_cv": "Lebenslauf verbessern",
        "career_communication": "Karrierekommunikation",
        "find_jobs": "Jobs finden",
        "mock_interview": "Vorstellungsgespräch",
        "skill_gap": "Kompetenzlücke",
        "career_roadmap": "Karriereplan",
        "job_assist": "Job-Assistent",
        "document_tools": "Dokument-Tools",
        "cv_translator": "Lebenslauf übersetzen",
        "cover_letter_generator": "Anschreiben erstellen",
        "cover_letter_translator": "Anschreiben übersetzen",
        "workobot": "Work-O-Bot",
        "workobot_sub": "KI-Karriere- und Sprachcoach",
        "start_here_intro": "Dein Dashboard zeigt eine stabile Lebenslaufanalyse, ATS-Bereitschaft und extrahierte Profildaten. Nutze das linke Menü für weitere Tools.",
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
        "ats_score": "ATS-Score",
        "strengths": "Top-Stärken",
        "improvements": "Top-Verbesserungen",
        "job_fit_score": "Job-Fit",
        "skill_gap_score": "Kompetenzlücke",
        "interview_score": "Interview",
        "resume_insights": "Lebenslauf-Einblicke",
        "update_resume": "Lebenslauf aktualisieren",
        "top_countries_fit": "Top-Länder für diesen Lebenslauf",
        "country_fit_note": "Wahrscheinlich die stärksten Märkte basierend auf Sprache, Profil und Übertragbarkeit.",
        "detected_country": "Erkanntes Land",
        "refresh_resume": "Lebenslauf neu analysieren",
        "save_resume": "Als neuen Lebenslauf speichern",
        "document_hub_caption": "Alle Schreib- und Übersetzungstools an einem Ort.",
        "quick_prompts": "Schnellstarts",
        "chat_mode": "Modus",
        "chat_placeholder": "Frag Work-O-Bot etwas...",
        "clear_chat": "Chat löschen",
        "preferred_language": "Bevorzugte Sprache",
        "user_status": "Aktuelle Karrieresituation",
        "fresh_graduate": "Absolvent/in / Student/in",
        "career_changer": "Quereinsteiger/in",
        "migrant": "Migration / Bewerbung im Ausland geplant",
        "local_jobseeker": "Jobsuche im aktuellen Land",
        "experienced": "Erfahrene Fachkraft",
        "returning": "Rückkehr nach Karrierepause",
        "guided_cv_builder": "Geführter Lebenslauf-Builder",
        "generate_cv": "Lebenslauf mit KI erstellen",
        "extra_cv_info": "Möchtest du weitere Informationen hinzufügen?",
        "country_readiness": "Länder-Eignung",
        "next_steps": "Was solltest du als Nächstes tun?",
        "cv_template_builder": "Lebenslauf-Vorlage nach Land",
        "migration_country": "In welches Land möchtest du ziehen/dich bewerben?",
        "chosen_country_resume_score": "Lebenslauf-Eignung für das gewählte Land",
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
        "dashboard": "Dashboard",
        "actions": "Tools verkennen",
        "understand_job": "Vacature begrijpen",
        "improve_cv": "CV verbeteren",
        "career_communication": "Carrièrecommunicatie",
        "find_jobs": "Banen vinden",
        "mock_interview": "Proefinterview",
        "skill_gap": "Vaardigheidskloof",
        "career_roadmap": "Carrièreplan",
        "job_assist": "Jobhulp",
        "document_tools": "Documenttools",
        "cv_translator": "CV vertalen",
        "cover_letter_generator": "Motivatiebrief maken",
        "cover_letter_translator": "Motivatiebrief vertalen",
        "workobot": "Work-O-Bot",
        "workobot_sub": "AI carrière- en taalcoach",
        "start_here_intro": "Je dashboard toont een stabiele cv-analyse, ATS-gereedheid en geëxtraheerde profielgegevens. Gebruik daarna het linkermenu voor meer tools.",
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
        "ats_score": "ATS-score",
        "strengths": "Topsterktes",
        "improvements": "Topverbeteringen",
        "job_fit_score": "Vacaturematch",
        "skill_gap_score": "Vaardigheidskloof",
        "interview_score": "Interview",
        "resume_insights": "CV-inzichten",
        "update_resume": "CV bijwerken",
        "top_countries_fit": "Toplanden voor dit CV",
        "country_fit_note": "Waarschijnlijk de sterkste markten op basis van taal, profiel en overdraagbaarheid.",
        "detected_country": "Gedetecteerd land",
        "refresh_resume": "CV opnieuw analyseren",
        "save_resume": "Opslaan als nieuw CV",
        "document_hub_caption": "Houd al je schrijf- en vertaaltools op één plek.",
        "quick_prompts": "Snelle prompts",
        "chat_mode": "Modus",
        "chat_placeholder": "Vraag Work-O-Bot iets...",
        "clear_chat": "Chat wissen",
    }
}

def ui_lang() -> str:
    current = st.session_state.get("preferred_language", st.session_state.get("ui_language", "English"))
    return current if current in UI_TEXT else "English"

def txt(key: str) -> str:
    return UI_TEXT[ui_lang()].get(key, key)

# =========================================================
# DYNAMIC COUNTRY + LANGUAGE DATA
# =========================================================
def get_country_options() -> List[str]:
    if pycountry:
        countries = sorted({c.name for c in pycountry.countries if getattr(c, "name", None)})
    else:
        countries = [
            "Austria", "Canada", "France", "Germany", "India", "Netherlands",
            "United Kingdom", "United States"
        ]
    return countries

def get_language_options() -> List[str]:
    if pycountry:
        languages = sorted({
            getattr(lang, "name", "").strip()
            for lang in pycountry.languages
            if getattr(lang, "name", None)
            and len(getattr(lang, "name", "")) > 1
            and "sign language" not in getattr(lang, "name", "").lower()
        })
    else:
        languages = ["Dutch", "English", "French", "German", "Hindi"]
    return languages

def get_geo_defaults() -> Tuple[str, str]:
    """
    Best-effort IP-based suggestion. Gracefully falls back.
    """
    if "geo_country_suggestion" in st.session_state and "geo_language_suggestion" in st.session_state:
        return st.session_state.geo_country_suggestion, st.session_state.geo_language_suggestion

    fallback_country = "Germany"
    fallback_language = "English"

    try:
        req = urllib.request.Request(
            "https://ipapi.co/json/",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=3) as response:
            payload = json.loads(response.read().decode("utf-8"))
            country_name = payload.get("country_name") or fallback_country

            languages_raw = payload.get("languages", "")
            first_lang_code = languages_raw.split(",")[0].split("-")[0].strip() if languages_raw else ""

            language_name = fallback_language
            if pycountry and first_lang_code:
                lang_obj = pycountry.languages.get(alpha_2=first_lang_code)
                if lang_obj and getattr(lang_obj, "name", None):
                    language_name = lang_obj.name

            st.session_state.geo_country_suggestion = country_name
            st.session_state.geo_language_suggestion = language_name
            return country_name, language_name
    except Exception:
        st.session_state.geo_country_suggestion = fallback_country
        st.session_state.geo_language_suggestion = fallback_language
        return fallback_country, fallback_language



def get_country_code(country_name: str) -> str:
    if not country_name or not pycountry:
        return ""
    try:
        obj = pycountry.countries.get(name=country_name)
        if obj and getattr(obj, "alpha_2", None):
            return obj.alpha_2
    except Exception:
        pass

    try:
        matches = pycountry.countries.search_fuzzy(country_name)
        if matches and getattr(matches[0], "alpha_2", None):
            return matches[0].alpha_2
    except Exception:
        pass
    return ""

@st.cache_data(show_spinner=False)
def get_local_city_index() -> Dict[str, List[str]]:
    """
    Local city index for fast suggestions. Uses geonamescache when available.
    """
    index: Dict[str, List[Tuple[str, int]]] = {}
    if not geonamescache:
        return {}

    try:
        gc = geonamescache.GeonamesCache(min_city_population=5000)
    except TypeError:
        gc = geonamescache.GeonamesCache()

    cities = gc.get_cities()

    for city in cities.values():
        name = (city.get("name") or "").strip()
        country_code = (city.get("countrycode") or "").strip().upper()
        population = int(city.get("population") or 0)

        if not name or not country_code:
            continue
        if population < 5000:
            continue

        index.setdefault(country_code, []).append((name, population))

    final_index: Dict[str, List[str]] = {}
    for code, rows in index.items():
        rows = sorted(rows, key=lambda x: (-x[1], x[0].lower()))
        seen = set()
        names = []
        for name, _ in rows:
            k = name.casefold()
            if k not in seen:
                seen.add(k)
                names.append(name)
        final_index[code] = names
    return final_index

@st.cache_data(show_spinner=False, ttl=86400)
def fetch_country_cities(country_name: str) -> List[str]:
    """
    Country-level city list with two layers:
    1) local geonamescache data when installed
    2) CountriesNow public API fallback for global coverage
    """
    country_code = get_country_code(country_name)
    merged: List[str] = []

    local_index = get_local_city_index()
    if country_code and country_code in local_index:
        merged.extend(local_index[country_code])

    urls = [
        "https://countriesnow.space/api/v0.1/countries/cities/q?country=" + urllib.parse.quote(country_name),
        "https://countriesnow.space/api/v0.1/countries/cities?country=" + urllib.parse.quote(country_name),
    ]

    for url in urls:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as response:
                payload = json.loads(response.read().decode("utf-8"))
                data = payload.get("data", [])
                if isinstance(data, list):
                    merged.extend([str(x).strip() for x in data if str(x).strip()])
                if merged:
                    break
        except Exception:
            continue

    deduped = []
    seen = set()
    for city in merged:
        k = city.casefold()
        if k not in seen:
            seen.add(k)
            deduped.append(city)

    return deduped

def fetch_city_suggestions(query: str, country_name: str = "", limit: int = 20) -> List[str]:
    query = (query or "").strip()
    cities = fetch_country_cities(country_name) if country_name else []

    if not cities:
        return []

    if not query:
        return cities[:limit]

    q = query.casefold()
    starts = [c for c in cities if c.casefold().startswith(q)]
    contains = [c for c in cities if q in c.casefold() and c not in starts]
    return (starts + contains)[:limit]

def http_get_json(url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 12) -> Dict:
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))

@st.cache_data(show_spinner=False, ttl=900)
def fetch_arbeitnow_jobs(query: str, location: str = "", limit: int = 15) -> List[Dict]:
    url = "https://www.arbeitnow.com/api/job-board-api"
    try:
        payload = http_get_json(url)
    except Exception:
        return []

    items = payload.get("data", []) if isinstance(payload, dict) else []
    q = (query or "").casefold()
    loc = (location or "").casefold()
    if loc.startswith("anywhere in "):
        loc = ""
    results = []

    for item in items:
        title = str(item.get("title", "")).strip()
        company = str(item.get("company_name", "")).strip()
        job_location = str(item.get("location", "")).strip()
        description = str(item.get("description", "")).strip()
        tags = ", ".join(item.get("tags", [])[:5]) if isinstance(item.get("tags"), list) else ""
        remote = bool(item.get("remote", False))
        url_apply = item.get("url") or item.get("job_url") or ""

        haystack = " ".join([title, company, job_location, description, tags]).casefold()
        if q and q not in haystack:
            continue
        if loc and loc not in haystack and not remote:
            continue

        results.append({
            "source": "Arbeitnow",
            "title": title,
            "company": company,
            "location": job_location or ("Remote" if remote else "Germany"),
            "remote": remote,
            "url": url_apply,
            "summary": tags or (description[:220] + "..." if description else "")
        })
        if len(results) >= limit:
            break

    return results

@st.cache_data(show_spinner=False, ttl=900)
def fetch_arbeitsagentur_jobs(query: str, location: str = "", limit: int = 15) -> List[Dict]:
    client_id = (os.getenv("BA_JOBS_API_KEY") or get_streamlit_secret("BA_JOBS_API_KEY") or "c003a37f-024f-462a-b36d-b001be4cd24a")
    normalized_location = "" if str(location or "").lower().startswith("anywhere in ") else (location or "")
    params = {
        "was": query or "",
        "wo": normalized_location,
        "size": str(limit),
    }
    url = "https://jobsuche.api.bund.dev/pc/v4/app/jobs?" + urllib.parse.urlencode(params)

    try:
        payload = http_get_json(url, headers={"X-API-Key": client_id, "User-Agent": "Mozilla/5.0"}, timeout=12)
    except Exception:
        return []

    raw_items = []
    if isinstance(payload, dict):
        for key in ["stellenangebote", "jobOffers", "jobs", "data"]:
            value = payload.get(key)
            if isinstance(value, list):
                raw_items = value
                break

    results = []
    for item in raw_items:
        title = str(item.get("beruf") or item.get("titel") or item.get("title") or "").strip()
        employer = item.get("arbeitgeber") or item.get("company") or {}
        if isinstance(employer, dict):
            company = str(employer.get("name") or employer.get("firma") or "").strip()
        else:
            company = str(employer or "").strip()

        location_value = item.get("arbeitsort") or item.get("arbeitsorte") or item.get("location") or {}
        if isinstance(location_value, list) and location_value:
            first_loc = location_value[0]
            if isinstance(first_loc, dict):
                place = ", ".join([str(first_loc.get("ort") or "").strip(), str(first_loc.get("region") or "").strip()]).strip(", ")
            else:
                place = str(first_loc)
        elif isinstance(location_value, dict):
            place = ", ".join([str(location_value.get("ort") or "").strip(), str(location_value.get("region") or "").strip()]).strip(", ")
        else:
            place = str(location_value or "").strip()

        refnr = str(item.get("refnr") or item.get("referenznummer") or "").strip()
        detail_url = f"https://www.arbeitsagentur.de/jobsuche/jobdetail/{urllib.parse.quote(refnr)}" if refnr else "https://www.arbeitsagentur.de/jobsuche/"
        summary = str(item.get("eintrittsdatum") or item.get("aktuelleVeroeffentlichungsdatum") or item.get("modifikationsTimestamp") or "").strip()

        if title:
            results.append({
                "source": "Bundesagentur für Arbeit",
                "title": title,
                "company": company or "Employer not shown",
                "location": place or (location or "Germany"),
                "remote": False,
                "url": detail_url,
                "summary": summary
            })
        if len(results) >= limit:
            break

    return results

def fetch_live_jobs_for_germany(roles: List[str], location: str = "") -> List[Dict]:
    results: List[Dict] = []
    normalized_roles = [r.strip() for r in roles if r and r.strip()]
    search_roles = normalized_roles[:6] if normalized_roles else ["Data Analyst", "Business Analyst", "IT Support Specialist"]

    for role in search_roles:
        results.extend(fetch_arbeitsagentur_jobs(role, location, limit=15))
        results.extend(fetch_arbeitnow_jobs(role, location, limit=15))

    deduped = []
    seen = set()
    for item in results:
        key = (item.get("source", "") + "|" + item.get("title", "") + "|" + item.get("company", "") + "|" + item.get("location", "")).casefold()
        if key not in seen:
            seen.add(key)
            deduped.append(item)
    return deduped[:40]


def render_live_jobs(jobs: List[Dict], country_name: str = ""):
    country_lower = (country_name or "").strip().lower()
    adzuna_ready = bool(os.getenv("ADZUNA_APP_ID") or get_streamlit_secret("ADZUNA_APP_ID")) and bool(os.getenv("ADZUNA_APP_KEY") or get_streamlit_secret("ADZUNA_APP_KEY"))
    if not jobs:
        if country_lower == "germany":
            st.info("No live jobs matched this Germany search right now. Try a broader city, another role title, or 'Anywhere in Germany'.")
        elif not adzuna_ready:
            st.info("No live jobs could be loaded for this country right now because Adzuna is not configured in this app run. The page will still show job-board links and a search strategy below.")
        else:
            st.info("No live jobs matched this exact search right now. Try a broader location, a simpler job title, or the whole country.")
        return

    title = f"Actual live job openings in {country_name}" if country_name else "Actual live job openings"
    st.markdown(f"### {title}")
    for job in jobs:
        st.markdown(f"""
<div class="card">
  <div class="section-title">{job.get('title','')}</div>
  <div><strong>{job.get('company','')}</strong></div>
  <div class="small-muted">{job.get('location','')} • {job.get('source','')}</div>
  <div style="margin-top:8px;">{job.get('summary','') or '—'}</div>
</div>
""", unsafe_allow_html=True)
        if job.get("url"):
            st.markdown(f"[Open job posting]({job['url']})")

def get_job_board_links(country_name: str, location: str, role: str = "") -> List[Tuple[str, str]]:

    q = urllib.parse.quote(f"{role} jobs in {location}".strip())
    country = (country_name or "").strip().lower()

    boards = []
    if country == "germany":
        boards.extend([
            ("LinkedIn Jobs", f"https://www.linkedin.com/jobs/search/?keywords={q}"),
            ("Indeed Germany", f"https://de.indeed.com/jobs?q={q}"),
            ("StepStone Germany", f"https://www.stepstone.de/jobs/{q}"),
            ("XING Jobs", f"https://www.xing.com/jobs/search?keywords={q}"),
            ("Bundesagentur für Arbeit", f"https://www.arbeitsagentur.de/jobsuche/suche?was={q}"),
        ])
    elif country in {"netherlands", "the netherlands"}:
        boards.extend([
            ("LinkedIn Jobs", f"https://www.linkedin.com/jobs/search/?keywords={q}"),
            ("Indeed Netherlands", f"https://nl.indeed.com/jobs?q={q}"),
            ("National Vacaturebank", f"https://www.nationalevacaturebank.nl/vacatures/zoekterm/{q}"),
            ("Werk.nl", f"https://www.werk.nl/werkzoekenden/vacatures/?q={q}"),
        ])
    elif country in {"united kingdom", "uk"}:
        boards.extend([
            ("LinkedIn Jobs", f"https://www.linkedin.com/jobs/search/?keywords={q}"),
            ("Indeed UK", f"https://uk.indeed.com/jobs?q={q}"),
            ("Reed", f"https://www.reed.co.uk/jobs/{q}"),
            ("Totaljobs", f"https://www.totaljobs.com/jobs/{q}"),
        ])
    else:
        boards.extend([
            ("LinkedIn Jobs", f"https://www.linkedin.com/jobs/search/?keywords={q}"),
            ("Indeed", f"https://www.indeed.com/jobs?q={q}"),
            ("Google Jobs Search", f"https://www.google.com/search?q={q}"),
        ])

    return boards


def build_role_suggestions(user_titles: List[str], detected_roles_text: str, current_role: str) -> List[str]:
    roles: List[str] = []
    for role in user_titles:
        role = role.strip()
        if role and role not in roles:
            roles.append(role)

    if detected_roles_text:
        for line in detected_roles_text.splitlines():
            candidate = line.replace("-", "").strip()
            if candidate and candidate not in roles:
                roles.append(candidate)

    if current_role and current_role.strip() and current_role.strip() not in roles:
        roles.append(current_role.strip())

    fallback = [
        "Data Analyst",
        "Business Analyst",
        "Reporting Analyst",
        "Operations Analyst",
        "IT Support Specialist",
    ]
    for role in fallback:
        if len(roles) >= 5:
            break
        if role not in roles:
            roles.append(role)

    return roles[:5]

def get_country_market_hint(country_name: str) -> str:
    country = (country_name or "").strip().lower()
    if country == "germany":
        return "German language helps strongly for many local roles, but English-speaking jobs exist in tech, startups, analytics, product, and international companies."
    if country in {"netherlands", "the netherlands"}:
        return "English-speaking roles are more common than in many EU markets, especially in tech, operations, and international business functions."
    if country in {"austria", "switzerland"}:
        return "Local language is often important, especially for customer-facing and traditional companies."
    if country in {"canada", "united states", "united kingdom", "ireland", "australia", "new zealand"}:
        return "English-first roles are common, but local resume style and market positioning still matter."
    return "Target roles with transferable skills first, then adapt your CV and search keywords to local market expectations."


ADZUNA_COUNTRY_CODES = {
    "australia": "au",
    "austria": "at",
    "belgium": "be",
    "brazil": "br",
    "canada": "ca",
    "france": "fr",
    "germany": "de",
    "india": "in",
    "italy": "it",
    "mexico": "mx",
    "netherlands": "nl",
    "the netherlands": "nl",
    "new zealand": "nz",
    "poland": "pl",
    "singapore": "sg",
    "south africa": "za",
    "spain": "es",
    "switzerland": "ch",
    "united kingdom": "gb",
    "uk": "gb",
    "united states": "us",
    "usa": "us",
}

@st.cache_data(show_spinner=False, ttl=900)
def fetch_adzuna_jobs(query: str, country_name: str, location: str = "", limit: int = 24) -> List[Dict]:
    country_code = ADZUNA_COUNTRY_CODES.get((country_name or "").strip().lower())
    app_id = os.getenv("ADZUNA_APP_ID") or get_streamlit_secret("ADZUNA_APP_ID")
    app_key = os.getenv("ADZUNA_APP_KEY") or get_streamlit_secret("ADZUNA_APP_KEY")

    if not country_code or not app_id or not app_key:
        return []

    results: List[Dict] = []
    seen = set()

    for page_no in range(1, 6):
        params = {
            "app_id": app_id,
            "app_key": app_key,
            "results_per_page": "12",
            "what_phrase": query or "",
            "where": location or "",
            "sort_by": "date",
            "content-type": "application/json",
            "max_days_old": "30",
        }

        url = f"https://api.adzuna.com/v1/api/jobs/{country_code}/search/{page_no}?" + urllib.parse.urlencode(params)

        try:
            payload = http_get_json(url, timeout=12)
        except Exception:
            continue

        items = payload.get("results", []) if isinstance(payload, dict) else []
        if not items:
            continue

        for item in items:
            title = str(item.get("title", "")).strip()
            company_obj = item.get("company") or {}
            company = str(company_obj.get("display_name") if isinstance(company_obj, dict) else company_obj or "").strip()

            location_obj = item.get("location") or {}
            if isinstance(location_obj, dict):
                display_loc = str(location_obj.get("display_name") or "").strip()
            else:
                display_loc = str(location_obj or "").strip()

            redirect_url = str(item.get("redirect_url", "")).strip()
            description = str(item.get("description", "")).strip()
            contract = str(item.get("contract_type", "")).strip()
            salary_min = item.get("salary_min")
            salary_max = item.get("salary_max")
            salary_text = ""
            if salary_min or salary_max:
                salary_text = f"Salary: {salary_min or '—'} to {salary_max or '—'}"

            summary_parts = [x for x in [contract, salary_text, (description[:200] + "...") if description else ""] if x]
            summary = " • ".join(summary_parts)

            key = (title + "|" + company + "|" + display_loc).casefold()
            if title and key not in seen:
                seen.add(key)
                results.append({
                    "source": "Adzuna",
                    "title": title,
                    "company": company or "Employer not shown",
                    "location": display_loc or (location or country_name),
                    "remote": False,
                    "url": redirect_url,
                    "summary": summary
                })
            if len(results) >= limit:
                return results[:limit]

    return results[:limit]

def fetch_live_jobs_global(country_name: str, roles: List[str], location: str = "") -> List[Dict]:
    results: List[Dict] = []
    country_lower = (country_name or "").strip().lower()

    if country_lower == "germany":
        results.extend(fetch_live_jobs_for_germany(roles, location))

    for role in roles[:6]:
        query = role.strip()
        if not query:
            continue
        results.extend(fetch_adzuna_jobs(query, country_name, location, limit=12))

    deduped: List[Dict] = []
    seen = set()
    for item in results:
        key = (item.get("source", "") + "|" + item.get("title", "") + "|" + item.get("company", "") + "|" + item.get("location", "")).casefold()
        if key not in seen:
            seen.add(key)
            deduped.append(item)

    return deduped[:50]


def fallback_job_search_plan(country_name: str, location: str, roles: List[str], cv_text: str) -> Dict:
    best_titles = []
    for role in roles[:5]:
        best_titles.append({
            "title": role,
            "fit_reason": "This matches the transferable skills and positioning suggested by your resume.",
            "seniority": "Junior to Mid-level",
            "english_realistic": "Depends on country and company type"
        })

    search_terms = []
    for role in roles[:4]:
        search_terms.extend([
            f"{role} jobs in {location}",
            f"{role} {country_name} English speaking",
            f"{role} remote {country_name}",
        ])

    return {
        "best_match_titles": best_titles,
        "search_terms": search_terms[:12],
        "market_strategy": [
            get_country_market_hint(country_name),
            f"Start with roles closest to your current profile and apply broadly in {location or country_name}.",
            "Prioritize companies with international teams, clear English-language postings, and realistic entry requirements."
        ],
        "best_live_matches": [],
        "priority_plan": [
            "Apply first to the 10 closest-fit roles.",
            "Use 2 to 3 tailored CV versions for your top role clusters.",
            "Track applications and improve search keywords every 3 to 4 days."
        ],
        "resume_positioning": [
            "Keep your headline aligned to the target role.",
            "Highlight measurable achievements and relevant tools.",
            "Move the most market-relevant skills higher in the CV."
        ],
        "fastest_route": [
            "Apply to 10 to 15 realistic roles this week.",
            "Tailor your CV headline and summary for each role cluster.",
            "Use LinkedIn, Indeed, and the strongest local job board for your country.",
            "Message 3 recruiters or hiring managers where possible.",
            "Practice short interview answers through Work-O-Bot."
        ]
    }

def generate_job_search_plan(country_name: str, location: str, roles: List[str], cv_text: str, live_jobs: List[Dict]) -> Dict:
    prompt = f"""
Return ONLY valid JSON. Do not use markdown.

JSON format:
{{
  "best_match_titles": [
    {{
      "title": "string",
      "fit_reason": "string",
      "seniority": "string",
      "english_realistic": "string"
    }}
  ],
  "search_terms": ["string"],
  "market_strategy": ["string"],
  "best_live_matches": ["string"],
  "priority_plan": ["string"],
  "resume_positioning": ["string"],
  "fastest_route": ["string"]
}}

Country: {country_name}
Preferred location: {location}
Target roles: {roles}

Candidate CV:
{cv_text}

Live jobs:
{live_jobs[:8]}

Rules:
- Be realistic about seniority. Do not suggest mid-senior if the CV does not support it.
- Prefer entry-level or junior recommendations when direct experience is limited.
- Fill every array with useful content.
- best_match_titles must contain 4 to 5 items.
- search_terms must contain 6 to 10 items and avoid repetitive variations.
- market_strategy must contain 3 to 5 bullets.
- priority_plan must contain 3 to 5 bullets.
- resume_positioning must contain 3 to 5 bullets.
- fastest_route must contain 4 to 6 bullets.
"""
    result = run_ai_prompt(prompt, force_english=True)
    if result.startswith("ERROR:"):
        return fallback_job_search_plan(country_name, location, roles, cv_text)

    try:
        parsed = safe_json_loads(result)
        if not isinstance(parsed, dict) or not parsed.get("best_match_titles"):
            return fallback_job_search_plan(country_name, location, roles, cv_text)
        return parsed
    except Exception:
        return fallback_job_search_plan(country_name, location, roles, cv_text)

def render_job_plan(plan: Dict):
    st.markdown("### Top 5 Best-Match Job Titles")
    titles = plan.get("best_match_titles", [])
    if isinstance(titles, list) and titles:
        for item in titles:
            if isinstance(item, dict):
                title = item.get("title", "Role")
                fit_reason = item.get("fit_reason", "—")
                seniority = item.get("seniority", "—")
                english_realistic = item.get("english_realistic", "—")
                st.markdown(f"""
<div class="card">
  <div class="section-title">{title}</div>
  <div><strong>Fit reason:</strong> {fit_reason}</div>
  <div><strong>Likely seniority:</strong> {seniority}</div>
  <div><strong>Can I apply in English?</strong> {english_realistic}</div>
</div>
""", unsafe_allow_html=True)
            else:
                st.markdown(f"- {item}")
    else:
        st.info("No role recommendations were generated.")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Best Immediate Search Terms")
        for item in plan.get("search_terms", [])[:12]:
            st.markdown(f"- {item}")

        st.markdown("### Market Strategy")
        for item in plan.get("market_strategy", [])[:6]:
            st.markdown(f"- {item}")

        st.markdown("### Job Search Priority Plan")
        for item in plan.get("priority_plan", [])[:6]:
            st.markdown(f"- {item}")

    with col2:
        st.markdown("### Resume Positioning Advice")
        for item in plan.get("resume_positioning", [])[:6]:
            st.markdown(f"- {item}")

        st.markdown("### Fastest Route to Interviews")
        for item in plan.get("fastest_route", [])[:6]:
            st.markdown(f"- {item}")

        best_live = plan.get("best_live_matches", [])
        if best_live:
            st.markdown("### Best Live Matches Right Now")
            for item in best_live[:6]:
                st.markdown(f"- {item}")


def analyze_cv_text_features(cv_text: str) -> Dict:
    text = cv_text or ""
    lower = text.lower()
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    words = re.findall(r"\S+", text)
    word_count = len(words)

    heading_patterns = {
        "professional_summary_present": r"(professional summary|summary|profile|about me|objective)",
        "work_experience_present": r"(work experience|experience|employment history|professional experience)",
        "skills_present": r"(^|\n)(skills|technical skills|core skills|competencies)\b",
        "education_present": r"(education|academic background|qualifications)",
    }

    email_present = bool(re.search(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", text, re.I))
    phone_present = bool(re.search(r"(\+?\d[\d\s\-()]{7,}\d)", text))
    linkedin_present = "linkedin.com" in lower
    contact_info_present = email_present or phone_present

    bullet_lines = [l for l in lines if l.startswith(("•", "-", "*"))]
    bullet_points_count = len(bullet_lines)
    bullet_points_present = bullet_points_count >= 2

    date_ranges_present = bool(re.search(r"(19\d{2}|20\d{2}).{0,10}(19\d{2}|20\d{2}|present|current|heute|till date)", lower, re.I))
    years_mentions = re.findall(r"(\d{1,2})\+?\s+(years|year|yrs)", lower)
    years_count = len(years_mentions)

    quantified_patterns = [
        r"\d+%",
        r"€\s?\d+",
        r"\$\s?\d+",
        r"\b\d+[+,]?\s+(users|clients|projects|tickets|years|months|team members|stakeholders)\b",
        r"\b(increased|reduced|improved|managed|supported|led)\b.{0,20}\d+",
    ]
    quantified_hits = 0
    for p in quantified_patterns:
        quantified_hits += len(re.findall(p, lower, re.I))
    quantified_achievements_present = quantified_hits > 0

    short_lines = sum(1 for l in lines if len(l) < 80)
    long_lines = sum(1 for l in lines if len(l) > 140)
    section_heading_hits = sum(1 for pattern in heading_patterns.values() if re.search(pattern, lower, re.I | re.M))
    clear_formatting = len(lines) >= 8 and short_lines >= 5 and long_lines <= max(2, len(lines) // 8)
    plain_text_readable = len(lines) >= 5 and word_count > 60 and long_lines <= max(3, len(lines) // 6)
    standard_headings_present = section_heading_hits >= 2

    action_verbs = [
        "developed", "analyzed", "managed", "led", "created", "built", "improved",
        "supported", "optimized", "designed", "implemented", "coordinated",
        "resolved", "delivered", "maintained", "automated"
    ]
    action_verb_hits = sum(1 for verb in action_verbs if verb in lower)

    skills_line_count = 0
    for l in lines:
        if "," in l and len(l.split(",")) >= 3:
            skills_line_count += 1

    contact_score = 1.0 if contact_info_present else 0.0
    summary_score = 1.0 if re.search(heading_patterns["professional_summary_present"], lower, re.I) else 0.0
    experience_score = 1.0 if re.search(heading_patterns["work_experience_present"], lower, re.I) else 0.0
    skills_score = min(1.0, 0.35 + 0.2 * skills_line_count) if re.search(heading_patterns["skills_present"], lower, re.I | re.M) else 0.0
    education_score = 1.0 if re.search(heading_patterns["education_present"], lower, re.I) else 0.0
    quantified_score = min(1.0, quantified_hits / 4) if quantified_hits else 0.0
    bullet_score = min(1.0, bullet_points_count / 8) if bullet_points_count else 0.0
    date_score = min(1.0, max(1, years_count) / 4) if date_ranges_present or years_count else 0.0
    formatting_score = 1.0 if clear_formatting else (0.55 if plain_text_readable else 0.2)

    if word_count < 120:
        grammar_quality = "weak"
    elif word_count < 220:
        grammar_quality = "average"
    else:
        grammar_quality = "good"

    features = {
        "contact_info_present": contact_info_present,
        "professional_summary_present": bool(re.search(heading_patterns["professional_summary_present"], lower, re.I)),
        "work_experience_present": bool(re.search(heading_patterns["work_experience_present"], lower, re.I)),
        "skills_present": bool(re.search(heading_patterns["skills_present"], lower, re.I | re.M)),
        "education_present": bool(re.search(heading_patterns["education_present"], lower, re.I)),
        "quantified_achievements_present": quantified_achievements_present,
        "clear_formatting": clear_formatting,
        "grammar_quality": grammar_quality,
        "standard_headings_present": standard_headings_present,
        "plain_text_readable": plain_text_readable,
        "bullet_points_present": bullet_points_present,
        "date_ranges_present": date_ranges_present,
        "word_count": word_count,
        "long_lines": long_lines,
        "bullet_points_count": bullet_points_count,
        "quantified_hits": quantified_hits,
        "action_verb_hits": action_verb_hits,
        "linkedin_present": linkedin_present,
        "section_heading_hits": section_heading_hits,
        "contact_score": contact_score,
        "summary_score": summary_score,
        "experience_score": experience_score,
        "skills_score": skills_score,
        "education_score": education_score,
        "quantified_score": quantified_score,
        "bullet_score": bullet_score,
        "date_score": date_score,
        "formatting_score": formatting_score,
    }
    return features


# =========================================================
# CV CLEANING + STRUCTURING
# =========================================================
def join_spaced_caps(match):
    return match.group(0).replace(" ", "")

def clean_cv_text(raw_text: str) -> str:
    """
    Fix common PDF extraction problems before WorkZo sends CV text to AI.
    """
    if not raw_text:
        return ""

    text = raw_text.replace("\x00", " ")
    text = re.sub(r"\r", "\n", text)
    text = re.sub(r"\b(?:[A-Z]\s){2,}[A-Z]\b", join_spaced_caps, text)

    replacements = {
        "VIZUALIZATION": "VISUALIZATION",
        "Scrapping": "Scraping",
        "Analisys": "Analysis",
        "suppoprt": "support",
        "Engince": "Engine",
        "knowlegde": "knowledge",
    }
    for wrong, right in replacements.items():
        text = re.sub(wrong, right, text, flags=re.I)

    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    return text.strip()

def build_created_cv_text(full_name, email, phone, location, summary, skills, experience, education, projects="", certifications="", languages="", extra_info="") -> str:
    return f"""
Name: {full_name}
Email: {email}
Phone: {phone}
Location: {location}

Professional Summary:
{summary}

Skills:
{skills}

Work Experience:
{experience}

Projects:
{projects}

Certifications:
{certifications}

Education:
{education}

Languages:
{languages}

Additional Information:
{extra_info}
""".strip()

def generate_cv_from_user_details(cv_details: str, target_country: str, user_status: str) -> str:
    prompt = build_quality_prompt(
        task="Create a complete professional CV from the user's raw details.",
        user_input=cv_details,
        expected_structure="""
Return:
1. Full CV
2. Missing Information to Improve It
3. Resume Score Estimate
4. ATS Improvement Suggestions
5. Questions to Ask the User Next
"""
    )
    prompt += f"""

Target country: {target_country}
User status: {user_status}

Rules:
- Build a clean, ATS-friendly CV.
- Use only information the user provided.
- Do not invent employers, dates, degrees, tools, or achievements.
- If details are missing, add a clear section called "Missing Information to Improve It".
- Make the CV suitable for the target country where possible.
"""
    return run_ai_prompt(prompt)

def organize_cv_for_display(cv_text: str) -> str:
    return clean_cv_text(cv_text)

# =========================================================
# SESSION STATE
# =========================================================
country_options = get_country_options()
language_options = get_language_options()
geo_country_default, geo_language_default = get_geo_defaults()

defaults = {
    "page": "onboarding",
    "onboarding_complete": False,
    "country": geo_country_default if geo_country_default in country_options else "Germany",
    "ui_language": "English",
    "response_language": geo_language_default if geo_language_default in language_options else "English",
    "user_status": "Career changer",
    "migration_country": geo_country_default if geo_country_default in country_options else "Germany",
    "career_goal": "",
    "cv_mode": "Upload CV",
    "cv_text": "",
    "dashboard_action": "Dashboard",

    # extracted dashboard profile
    "profile_summary": "",
    "current_role_detected": "",
    "key_skills_detected": "",
    "suggested_roles_detected": "",
    "best_fit_countries_detected": "",
    "next_actions_detected": "",
    "country_cv_readiness": "",
    "status_guidance": "",
    "cv_profile_raw": "",

    # dashboard analysis
    "cv_score_value": None,
    "ats_score_value": None,
    "country_readiness_score_value": None,
    "resume_strengths": "",
    "resume_improvements": "",
    "latest_resume_dashboard_analysis": "",
    "dashboard_cv_hash": "",

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
    "latest_cv_translation": "",
    "latest_cover_letter_translation": "",

    # work-o-bot
    "workobot_mode": "General Help",
    "workobot_messages": [
        {
            "role": "assistant",
            "content": "Hi, I’m Work-O-Bot. I can help with German practice, mock tests, interview prep, career communication, and skill gap guidance."
        }
    ],

    # cache
    "dashboard_cache": {},
    "next_best_step_result": "",
    "ai_quality_style": "coach",
    "target_role_context": "",
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

def safe_json_loads(raw: str) -> Dict:
    cleaned = raw.strip()

    # remove ```json fences if present
    cleaned = re.sub(r"^```json\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"^```\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise


# =========================================================
# AI QUALITY LAYER
# =========================================================
def get_user_status_context() -> str:
    return st.session_state.get("user_status", "Not specified")

def get_target_country_context() -> str:
    return st.session_state.get("country", "Not specified")

def get_target_role_context() -> str:
    return st.session_state.get("target_role_context", "") or st.session_state.get("current_role_detected", "") or "Not specified"

def compact_cv_context(max_chars: int = 3500) -> str:
    cv = st.session_state.get("cv_text", "") or ""
    cv = re.sub(r"\s+", " ", cv).strip()
    return cv[:max_chars] + ("..." if len(cv) > max_chars else "")

def workzo_expert_context() -> str:
    return f"""
User status: {get_user_status_context()}
Target country: {get_target_country_context()}
Target role/context: {get_target_role_context()}
AI response language: {st.session_state.get("response_language", "English")}
Known CV/Profile:
{compact_cv_context()}
""".strip()

def quality_system_prompt(answer_lang: str, system_addition: str = "") -> str:
    return f"""
You are WorkZo AI, a senior international career strategist, resume consultant, ATS specialist, interview coach, and job-search advisor.

Your job is NOT to give generic AI advice. Your job is to give precise, personalized, practical guidance based on:
- the user's CV/profile
- the user's status: fresh graduate, migrant, career changer, experienced professional, etc.
- the target country and local hiring expectations
- the user's target role and current experience level

Always respond ONLY in {answer_lang}.

Quality rules:
1. Be specific. Avoid generic sentences like "improve your skills" unless you say exactly which skill, why, and what to do next.
2. Use the user's actual CV/profile details whenever available.
3. Be honest about weak fit, missing experience, language gaps, unrealistic seniority, or template mismatch.
4. Give prioritized actions: what to do first, second, third.
5. For migration/country-specific topics, mention local CV expectations, language expectations, and role-market fit.
6. For fresh graduates, focus on portfolio projects, internships, entry-level roles, keywords, and proof of skill.
7. For career changers, focus on transferable skills, bridge roles, portfolio proof, and realistic role titles.
8. For experienced users, focus on positioning, measurable achievements, leadership/impact, and market fit.
9. Keep output structured with useful headings and concise bullets.
10. Never invent employers, degrees, certifications, dates, or achievements.
11. If information is missing, say what is missing and give a best-effort recommendation.
12. End with a clear "Next best action" when appropriate.

Use this context where relevant:
{workzo_expert_context()}

{system_addition}
""".strip()

def build_quality_prompt(task: str, user_input: str, expected_structure: str = "") -> str:
    return f"""
Task: {task}

Context:
{workzo_expert_context()}

User input:
{user_input}

Expected output structure:
{expected_structure}

Remember:
- Make it tailored, not generic.
- Give country-aware and status-aware advice.
- Be practical and decision-oriented.
""".strip()


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
        answer_lang = st.session_state.response_language or "English"

    system_prompt = quality_system_prompt(answer_lang, system_addition)

    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        return (res.choices[0].message.content or "").strip()
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

def make_pdf_from_text(title: str, body: str) -> bytes:
    """
    Create a simple PDF from generated CV text.
    Falls back to encoded text if reportlab is unavailable, but Streamlit label will show dependency need.
    """
    if SimpleDocTemplate is None:
        return body.encode("utf-8")

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=42, leftMargin=42, topMargin=42, bottomMargin=42)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(title, styles["Title"]))
    story.append(Spacer(1, 12))

    for raw_line in body.splitlines():
        line = raw_line.strip()
        if not line:
            story.append(Spacer(1, 8))
            continue
        safe_line = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if line.endswith(":") or line.isupper():
            story.append(Paragraph(f"<b>{safe_line}</b>", styles["Heading3"]))
        else:
            story.append(Paragraph(safe_line, styles["BodyText"]))
            story.append(Spacer(1, 4))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

def get_section_text(result: str, names: List[str]) -> str:
    sections = numbered_sections_to_markdown(result)
    for name in names:
        value = sections.get(name, "").strip()
        if value:
            return value
    # fallback: return whole result if exact numbered title parsing fails
    return result.strip()


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
    fig.update_layout(height=260, margin=dict(l=20, r=20, t=50, b=20))
    st.plotly_chart(fig, use_container_width=True)

def make_cv_hash(cv_text: str, country: str) -> str:
    raw = f"{SCORING_VERSION}||{country.strip()}||{st.session_state.get('migration_country', '').strip()}||{st.session_state.get('user_status', '').strip()}||{cv_text.strip()}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()

def bool_score(flag: bool, points: int) -> int:
    return points if flag else 0

def calculate_resume_score(features: Dict) -> int:
    score = 18
    score += round(features.get("contact_score", 0) * 8)
    score += round(features.get("summary_score", 0) * 8)
    score += round(features.get("experience_score", 0) * 16)
    score += round(features.get("skills_score", 0) * 10)
    score += round(features.get("education_score", 0) * 8)
    score += round(features.get("quantified_score", 0) * 14)
    score += round(features.get("bullet_score", 0) * 8)
    score += round(features.get("date_score", 0) * 6)
    score += round(features.get("formatting_score", 0) * 10)

    action_verb_hits = int(features.get("action_verb_hits", 0))
    if action_verb_hits >= 8:
        score += 5
    elif action_verb_hits >= 4:
        score += 3

    if features.get("linkedin_present", False):
        score += 2

    word_count = int(features.get("word_count", 0))
    if word_count < 120:
        score -= 12
    elif word_count < 180:
        score -= 6
    elif word_count > 900:
        score -= 8
    elif word_count > 700:
        score -= 4

    if int(features.get("long_lines", 0)) > 6:
        score -= 6
    elif int(features.get("long_lines", 0)) > 3:
        score -= 3

    if not features.get("contact_info_present", False):
        score -= 8
    if not features.get("work_experience_present", False):
        score -= 12
    if not features.get("skills_present", False):
        score -= 8

    return max(35, min(score, 92))


def calculate_ats_score(features: Dict) -> int:
    score = 20
    score += 14 if features.get("standard_headings_present", False) else 4
    score += round(features.get("contact_score", 0) * 8)
    score += 12 if features.get("plain_text_readable", False) else 4
    score += round(features.get("skills_score", 0) * 8)
    score += round(features.get("experience_score", 0) * 10)
    score += round(features.get("education_score", 0) * 6)
    score += round(features.get("bullet_score", 0) * 8)
    score += round(features.get("date_score", 0) * 8)

    word_count = int(features.get("word_count", 0))
    if word_count < 120:
        score -= 10
    elif word_count > 950:
        score -= 8

    if int(features.get("long_lines", 0)) > 6:
        score -= 8
    elif int(features.get("long_lines", 0)) > 3:
        score -= 4

    if not features.get("contact_info_present", False):
        score -= 10
    if not features.get("standard_headings_present", False):
        score -= 8
    if not features.get("date_ranges_present", False):
        score -= 6

    return max(30, min(score, 90))


def calculate_country_readiness_score(features: Dict, target_country: str, user_status: str) -> int:
    """
    Resume readiness for selected migration/target country.
    This is intentionally stricter than the general resume score.
    """
    base = calculate_resume_score(features)

    score = int(base * 0.72)

    # Country-template/readability signals
    if features.get("contact_info_present", False):
        score += 6
    if features.get("standard_headings_present", False):
        score += 8
    if features.get("plain_text_readable", False):
        score += 8
    if features.get("date_ranges_present", False):
        score += 5
    if features.get("skills_present", False):
        score += 5
    if features.get("quantified_achievements_present", False):
        score += 6

    country = (target_country or "").lower()
    status = (user_status or "").lower()

    # Migrating users need stronger country adaptation.
    if "migrate" in status or "abroad" in status:
        score -= 5

    # Local language/country expectations: not exact, but useful early signal.
    cv_raw = (st.session_state.get("cv_text", "") or "").lower()
    if country in {"germany", "austria", "switzerland"}:
        if "german" in cv_raw or "deutsch" in cv_raw:
            score += 5
        else:
            score -= 6
    if country in {"united kingdom", "united states", "canada", "australia", "ireland"}:
        if "english" in cv_raw:
            score += 4

    if not features.get("work_experience_present", False):
        score -= 8
    if int(features.get("word_count", 0)) < 180:
        score -= 6

    return max(25, min(score, 92))

def analyze_resume_dashboard_stable(cv_text: str, force_refresh: bool = False):
    cv_key = make_cv_hash(cv_text, st.session_state.country)

    if not force_refresh and cv_key in st.session_state.dashboard_cache:
        cached = st.session_state.dashboard_cache[cv_key]
        apply_dashboard_cache(cached)
        return

    prompt = f"""
Analyze this CV like a senior international career advisor and return ONLY valid JSON.
Do not add markdown, explanations, or code fences.

The analysis must be personalized to the user status and target country.
Do not give generic strengths like "good communication" unless the CV actually shows it.

JSON format:
{{
  "professional_summary": "short paragraph",
  "current_or_likely_role": "role name",
  "key_skills": ["skill1", "skill2", "skill3", "skill4", "skill5"],
  "suggested_roles": ["role1", "role2", "role3"],
  "best_fit_countries": ["Country 1 - short reason", "Country 2 - short reason", "Country 3 - short reason", "Country 4 - short reason", "Country 5 - short reason"],
  "country_cv_readiness": "short country-specific verdict on whether this CV fits the target country",
  "status_guidance": "short advice based on the user's career status",
  "next_actions": ["action1", "action2", "action3", "action4"],
  "strengths": ["specific strength from CV", "specific strength from CV", "specific strength from CV", "specific strength from CV"],
  "improvements": ["specific improvement", "specific improvement", "specific improvement", "specific improvement"],
  "next_best_actions": ["action1", "action2", "action3"],
  "country_readiness_notes": ["note1", "note2", "note3"]
}}

Rules:
- Be concise, practical, and specific.
- Consider the user's status from onboarding.
- Include next_best_actions that tell the user exactly what to do next.
- Include country_readiness_notes for the chosen country.
- For best_fit_countries, suggest 5 countries where this CV/profile is likely to be competitive.
- Avoid repeating the same default countries unless they are clearly justified by the CV.
- Make the reasons specific to the candidate profile and country market.
- Keep each country reason short.
- Do not generate any numeric score.
- Do not add keys outside this JSON structure.
- Return valid JSON only.

Country context: {st.session_state.country}
User status: {st.session_state.get('user_status', 'Not specified')}
Career goal: {st.session_state.get('career_goal', 'Not specified')}

CV:
{cv_text}
"""
    result = run_ai_prompt(prompt, force_english=True)

    if result.startswith("ERROR:"):
        return

    try:
        parsed = safe_json_loads(result)
    except Exception:
        st.warning("The resume analysis response could not be parsed. Please try refresh once.")
        return

    features = analyze_cv_text_features(cv_text)

    cached = {
        "profile_summary": parsed.get("professional_summary", "").strip(),
        "current_role_detected": parsed.get("current_or_likely_role", "").strip(),
        "key_skills_detected": parsed.get("key_skills", []),
        "suggested_roles_detected": parsed.get("suggested_roles", []),
        "best_fit_countries_detected": parsed.get("best_fit_countries", []),
        "country_cv_readiness": parsed.get("country_cv_readiness", ""),
        "status_guidance": parsed.get("status_guidance", ""),
        "next_actions_detected": parsed.get("next_actions", []),
        "resume_strengths": parsed.get("strengths", []),
        "resume_improvements": parsed.get("improvements", []),
        "next_best_actions_detected": parsed.get("next_best_actions", []),
        "country_readiness_notes_detected": parsed.get("country_readiness_notes", []),
        "country_readiness_score_value": calculate_country_readiness_score(features, st.session_state.get("migration_country") or st.session_state.country, st.session_state.get("user_status", "")),
        "cv_profile_raw": json.dumps({"ai_extract": parsed, "text_features": features}, indent=2),
        "cv_score_value": calculate_resume_score(features),
        "ats_score_value": calculate_ats_score(features),
    }

    st.session_state.dashboard_cache[cv_key] = cached
    apply_dashboard_cache(cached)
    st.session_state.dashboard_cv_hash = cv_key

def apply_dashboard_cache(cached: Dict):
    st.session_state.profile_summary = cached.get("profile_summary", "")
    st.session_state.current_role_detected = cached.get("current_role_detected", "")

    skills = cached.get("key_skills_detected", [])
    roles = cached.get("suggested_roles_detected", [])
    strengths = cached.get("resume_strengths", [])
    improvements = cached.get("resume_improvements", [])
    best_fit_countries = cached.get("best_fit_countries_detected", [])
    next_best_actions = cached.get("next_best_actions_detected", [])
    country_readiness_notes = cached.get("country_readiness_notes_detected", [])
    next_actions = cached.get("next_actions_detected", [])

    st.session_state.key_skills_detected = "\n".join([f"- {x}" for x in skills]) if isinstance(skills, list) else str(skills)
    st.session_state.suggested_roles_detected = "\n".join([f"- {x}" for x in roles]) if isinstance(roles, list) else str(roles)
    st.session_state.resume_strengths = "\n".join([f"- {x}" for x in strengths]) if isinstance(strengths, list) else str(strengths)
    st.session_state.resume_improvements = "\n".join([f"- {x}" for x in improvements]) if isinstance(improvements, list) else str(improvements)
    st.session_state.best_fit_countries_detected = "\n".join([f"- {x}" for x in best_fit_countries]) if isinstance(best_fit_countries, list) else str(best_fit_countries)
    st.session_state.next_best_step_result = "\n".join([f"- {x}" for x in next_best_actions]) if isinstance(next_best_actions, list) else str(next_best_actions)
    st.session_state.country_readiness_notes = "\n".join([f"- {x}" for x in country_readiness_notes]) if isinstance(country_readiness_notes, list) else str(country_readiness_notes)

    st.session_state.cv_profile_raw = cached.get("cv_profile_raw", "")
    st.session_state.cv_score_value = cached.get("cv_score_value")
    st.session_state.ats_score_value = cached.get("ats_score_value")
    st.session_state.country_readiness_score_value = cached.get("country_readiness_score_value")

def reset_onboarding():
    preserve = {
        "request_count": st.session_state.request_count,
        "first_request_time": st.session_state.first_request_time,
        "ui_language": st.session_state.ui_language,
        "response_language": st.session_state.response_language,
        "dashboard_cache": st.session_state.dashboard_cache,
        "geo_country_suggestion": st.session_state.get("geo_country_suggestion", "Germany"),
        "geo_language_suggestion": st.session_state.get("geo_language_suggestion", "English"),
    }
    for key in list(st.session_state.keys()):
        del st.session_state[key]

    for key, value in defaults.items():
        st.session_state[key] = value

    for key, value in preserve.items():
        st.session_state[key] = value

    st.session_state.page = "onboarding"
    st.session_state.onboarding_complete = False

def set_new_resume_and_refresh(new_resume_text: str):
    st.session_state.cv_text = new_resume_text.strip()

    st.session_state.profile_summary = ""
    st.session_state.current_role_detected = ""
    st.session_state.key_skills_detected = ""
    st.session_state.suggested_roles_detected = ""
    st.session_state.best_fit_countries_detected = ""
    st.session_state.next_actions_detected = ""
    st.session_state.country_cv_readiness = ""
    st.session_state.status_guidance = ""
    st.session_state.cv_profile_raw = ""
    st.session_state.cv_score_value = None
    st.session_state.ats_score_value = None
    st.session_state.resume_strengths = ""
    st.session_state.resume_improvements = ""

    analyze_resume_dashboard_stable(st.session_state.cv_text, force_refresh=True)



def render_metric_card(label: str, value: str, foot: str = ""):
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-foot">{foot}</div>
    </div>
    """, unsafe_allow_html=True)


def render_feature_tile(icon: str, title: str, copy: str):
    st.markdown(f"""
    <div class="feature-tile">
        <div style="font-size:1.45rem; margin-bottom:8px;">{icon}</div>
        <div class="feature-title">{title}</div>
        <div class="feature-copy">{copy}</div>
    </div>
    """, unsafe_allow_html=True)


def generate_next_best_steps(cv_text: str, country_name: str, current_role: str, suggested_roles: str, user_status: str = "", career_goal: str = "") -> str:
    prompt = f"""
Country: {country_name}
User status: {user_status or 'Not specified'}
Career goal: {career_goal or 'Not specified'}
Current role: {current_role or 'Not clear'}
Suggested roles:
{suggested_roles}
Candidate CV:
{cv_text}

Create a personalized action center. Adapt the advice based on the user status:
- Fresh graduate: portfolio projects, internships, entry-level search, skills proof.
- Career changer: transferable skills, bridge role, portfolio, realistic job titles.
- Migrating to another country: country CV format, language expectations, local job titles, application documents.
- Returning after career break: confidence positioning, gap explanation, restart strategy.
- Experienced professional: positioning, seniority, specialization, leadership proof.

Return in this exact structure:
1. Resume Readiness Verdict
2. Best Immediate Goal
3. This Week's 3 Priority Actions
4. Best Role Cluster to Target
5. One Resume Fix That Will Help Most
6. One Skill or Proof to Build Next
7. Country-Specific Advice
8. One Message to Send Today

Keep it practical, specific, and motivating.
"""
    result = run_ai_prompt(prompt)
    return result

# =========================================================
# HEADER
# =========================================================
# HEADER
# =========================================================
header_col1, header_col2 = st.columns([1, 7])

with header_col1:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=72)
    else:
        st.markdown("<div style='font-size:46px; line-height:1.2;'>🚀</div>", unsafe_allow_html=True)

with header_col2:
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap;">
        <h1 style="margin:0;">WORKZO AI</h1>
        <span class="beta-badge">BETA V5.0</span>
    </div>
    <div style="margin-top:6px;">
        <h4 style="margin:0;">{txt("title")}</h4>
        <p style="color: gray; margin:6px 0 0 0;">{txt("subtitle")}</p>
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# TOP BAR - LANGUAGE SETTINGS
# =========================================================
lang_col1, lang_col2, lang_col3 = st.columns([4, 2, 2])
with lang_col2:
    current_ui = st.session_state.get("ui_language", "English")
    st.session_state.ui_language = st.selectbox(
        "App Language",
        ["English", "German", "Dutch"],
        index=["English", "German", "Dutch"].index(current_ui) if current_ui in ["English", "German", "Dutch"] else 0,
        key="top_ui_language_select"
    )
with lang_col3:
    current_response = st.session_state.get("response_language", "English")
    response_index = language_options.index(current_response) if current_response in language_options else (language_options.index("English") if "English" in language_options else 0)
    st.session_state.response_language = st.selectbox(
        "AI Response Language",
        language_options,
        index=response_index,
        key="top_response_language_select"
    )

# =========================================================
# ONBOARDING
# =========================================================
def show_onboarding():
    st.subheader(txt("onboarding_title"))
    st.caption(txt("onboarding_subtitle"))

    language_list = ["English", "German", "Dutch"]
    lang_default = st.session_state.get("preferred_language", "English")
    if lang_default not in language_list:
        lang_default = "English"

    preferred_language = st.selectbox(
        txt("preferred_language"),
        language_list,
        index=language_list.index(lang_default),
        help="This language is used for both app labels and AI responses."
    )
    st.session_state.preferred_language = preferred_language
    st.session_state.ui_language = preferred_language
    st.session_state.response_language = preferred_language

    country_index = country_options.index(st.session_state.country) if st.session_state.country in country_options else 0
    country = st.selectbox(txt("country"), country_options, index=country_index)

    status_options = [
        txt("local_jobseeker"),
        txt("fresh_graduate"),
        txt("career_changer"),
        txt("migrant"),
        txt("experienced"),
        txt("returning"),
    ]
    status_display = st.selectbox(txt("user_status"), status_options)
    status_map = {
        txt("local_jobseeker"): "Looking for jobs locally",
        txt("fresh_graduate"): "Fresh graduate / student",
        txt("career_changer"): "Career changer",
        txt("migrant"): "Planning to migrate / applying abroad",
        txt("experienced"): "Experienced professional",
        txt("returning"): "Returning after a career break",
    }
    user_status = status_map.get(status_display, status_display)

    migration_country = ""
    if "migrate" in user_status.lower() or "abroad" in user_status.lower():
        migration_default = st.session_state.get("migration_country") or st.session_state.get("country") or "Germany"
        migration_index = country_options.index(migration_default) if migration_default in country_options else 0
        migration_country = st.selectbox(
            txt("migration_country"),
            country_options,
            index=migration_index
        )

    cv_mode_display = st.radio(
        txt("resume_input"),
        [txt("upload_cv"), txt("create_cv")],
        horizontal=True
    )
    cv_mode = "Upload CV" if cv_mode_display == txt("upload_cv") else "Create CV"

    with st.form("onboarding_form_v47"):
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

        if cv_mode == "Upload CV":
            uploaded_file = st.file_uploader(
                txt("upload_resume"),
                type=["txt", "pdf"]
            )

            if uploaded_file is not None:
                if uploaded_file.size > 5 * 1024 * 1024:
                    st.error("File too large. Please upload a CV under 5 MB.")
                elif uploaded_file.type == "text/plain":
                    cv_text_input = organize_cv_for_display(uploaded_file.read().decode("utf-8", errors="ignore"))
                elif uploaded_file.type == "application/pdf":
                    try:
                        cv_text_input = organize_cv_for_display(extract_pdf_text(uploaded_file))
                    except Exception as e:
                        st.error(f"PDF read error: {e}")
                else:
                    st.error(txt("unsupported_file"))

            if cv_text_input:
                with st.expander("Preview cleaned CV text", expanded=False):
                    st.text_area("Cleaned extracted CV", value=cv_text_input, height=260)

        else:
            st.markdown(f"#### {txt('guided_cv_builder')}")
            st.caption("Add what you know. WorkZo will generate a cleaner CV and ask what is missing.")

            c1, c2 = st.columns(2)
            with c1:
                full_name = st.text_input(txt("full_name"))
                email = st.text_input(txt("email"))
                phone = st.text_input(txt("phone"))
                location = st.text_input("Location")
            with c2:
                languages = st.text_area("Languages", placeholder="Example: English C1, German A2, Tamil native")
                certifications = st.text_area("Certifications / Courses", placeholder="Example: Data Science Bootcamp, AWS basics")

            summary = st.text_area(txt("summary"), placeholder="Write a short background. Example: Technical support engineer transitioning into data analytics.")
            skills = st.text_area(txt("skills"), placeholder="Example: Python, SQL, Tableau, customer support, troubleshooting")
            experience = st.text_area(txt("experience"), placeholder="Mention roles, companies, years, responsibilities, achievements.")
            projects = st.text_area("Projects", placeholder="Example: E-scooter data pipeline, sentiment analysis, Tableau dashboard")
            education = st.text_area(txt("education"))
            extra_info = st.text_area(txt("extra_cv_info"), placeholder="Achievements, tools, target countries, job preferences, gaps, anything else.")

            if any([full_name.strip(), email.strip(), phone.strip(), location.strip(), summary.strip(), skills.strip(), experience.strip(), projects.strip(), certifications.strip(), education.strip(), languages.strip(), extra_info.strip()]):
                cv_text_input = build_created_cv_text(
                    full_name, email, phone, location, summary, skills, experience, education, projects, certifications, languages, extra_info
                )

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
                if not summary.strip() and not experience.strip() and not skills.strip():
                    st.warning("Please enter at least a summary, experience, or skills so WorkZo can build your CV.")
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
            st.session_state.cv_text = clean_cv_text(cv_text_input)
            st.session_state.onboarding_complete = True
            st.session_state.page = "dashboard"

            with st.spinner("Reading your resume and preparing dashboard..."):
                analyze_resume_dashboard_stable(st.session_state.cv_text, force_refresh=True)

            st.rerun()

# =========================================================
# WORK-O-BOT
# =========================================================
# WORK-O-BOT
# =========================================================
def run_workobot(user_message: str, mode: str):
    task_map = {
        "General Help": "Act as a career strategist and answer the user's question with personalized, practical guidance.",
        "German Practice": "Act as a workplace German coach. Correct the user's German, explain briefly, and give practice sentences for career situations.",
        "Mock Test Prep": "Act as a language/mock-test coach. Create exam-style tasks, model answers, corrections, and scoring guidance.",
        "Interview Prep": "Act as a realistic interviewer and interview coach. Give questions, evaluate answers, and improve responses using STAR/CAR structure.",
        "Career Communication": "Act as a professional communication coach. Improve emails, LinkedIn messages, HR replies, and interview answers.",
        "Skill Gap Help": "Act as a skill-gap strategist. Identify realistic gaps, priority learning path, portfolio proof, and role-targeting advice.",
    }

    expected = """
1. Direct Answer
2. Personalized Analysis
3. Suggested Response / Example
4. Mistakes or Risks to Avoid
5. Practice / Next Best Action
"""

    prompt = build_quality_prompt(
        task=task_map.get(mode, task_map["General Help"]),
        user_input=user_message,
        expected_structure=expected
    )

    result = run_ai_prompt(
        prompt,
        system_addition="""
For Work-O-Bot:
- Sound like a real coach, not a generic chatbot.
- Ask at most one follow-up question only if it is truly needed.
- If the user is practicing language/interview, include a corrected version, a natural version, and one practice task.
- If the user asks about jobs/career, include realistic role levels and target-country fit.
"""
    )
    if result.startswith("ERROR:"):
        return "I couldn’t answer right now because the AI service is unavailable."
    return result

def show_workobot():
    st.subheader(txt("workobot"))
    st.caption(txt("workobot_sub"))

    mode = st.selectbox(
        txt("chat_mode"),
        [
            "General Help",
            "German Practice",
            "Mock Test Prep",
            "Interview Prep",
            "Career Communication",
            "Skill Gap Help",
        ],
        index=[
            "General Help",
            "German Practice",
            "Mock Test Prep",
            "Interview Prep",
            "Career Communication",
            "Skill Gap Help",
        ].index(st.session_state.get("workobot_mode", "General Help"))
    )
    st.session_state.workobot_mode = mode

    st.markdown(f"### {txt('quick_prompts')}")
    qp1, qp2, qp3, qp4 = st.columns(4)
    quick_prompt = None
    country_quick_prompts = get_country_specific_quick_prompts(st.session_state.country)

    with qp1:
        if st.button(country_quick_prompts[0][0], use_container_width=True):
            quick_prompt = country_quick_prompts[0][1]
    with qp2:
        if st.button(country_quick_prompts[1][0], use_container_width=True):
            quick_prompt = country_quick_prompts[1][1]
    with qp3:
        if st.button(country_quick_prompts[2][0], use_container_width=True):
            quick_prompt = country_quick_prompts[2][1]
    with qp4:
        if st.button(country_quick_prompts[3][0], use_container_width=True):
            quick_prompt = country_quick_prompts[3][1]

    right1, right2 = st.columns([1, 5])
    with right1:
        if st.button(txt("clear_chat")):
            st.session_state.workobot_messages = [
                {
                    "role": "assistant",
                    "content": "Hi, I’m Work-O-Bot. I can help with German practice, mock tests, interview prep, career communication, and skill gap guidance."
                }
            ]
            st.rerun()

    for msg in st.session_state.workobot_messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    user_input = st.chat_input(txt("chat_placeholder"))
    final_input = quick_prompt or user_input

    if final_input:
        st.session_state.workobot_messages.append({"role": "user", "content": final_input})
        with st.chat_message("user"):
            st.write(final_input)

        with st.chat_message("assistant"):
            with st.spinner("Work-O-Bot is thinking..."):
                reply = run_workobot(final_input, mode)
                st.write(reply)

        st.session_state.workobot_messages.append({"role": "assistant", "content": reply})

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



def get_cv_template_options(target_country: str, user_status: str) -> Dict[str, str]:
    country = (target_country or "").lower()
    status = (user_status or "").lower()

    options = {
        "ATS Classic": "Clean one-column ATS-friendly CV. Best for most online applications and job portals.",
        "Modern Professional": "Modern but still ATS-safe CV. Best for business, tech, customer success, and support roles.",
        "Career Changer": "Highlights transferable skills, bridge experience, and target-role relevance.",
        "Fresh Graduate / Entry-Level": "Highlights education, projects, tools, internships, and learning proof.",
        "Migration-Friendly": "Country-aware CV for applying abroad, with local expectations and readable structure.",
    }

    if country in {"germany", "austria", "switzerland"}:
        options = {
            "German-Style Lebenslauf": "Structured German-style CV with clear sections, reverse chronology, language levels, and practical details.",
            **options,
        }

    if "graduate" in status or "student" in status:
        options = {
            "Fresh Graduate / Entry-Level": "Highlights education, projects, tools, internships, and learning proof.",
            **{k: v for k, v in options.items() if k != "Fresh Graduate / Entry-Level"}
        }

    if "career changer" in status:
        options = {
            "Career Changer": "Highlights transferable skills, bridge experience, and target-role relevance.",
            **{k: v for k, v in options.items() if k != "Career Changer"}
        }

    if "migrate" in status or "abroad" in status:
        options = {
            "Migration-Friendly": "Country-aware CV for applying abroad, with local expectations and readable structure.",
            **{k: v for k, v in options.items() if k != "Migration-Friendly"}
        }

    return options

def get_template_instructions(template_name: str, target_country: str) -> str:
    country = target_country or "the selected country"

    instructions = {
        "ATS Classic": f"""
Use a clean one-column ATS-friendly format for {country}.
Sections:
- Name and contact details
- Professional Summary
- Core Skills
- Work Experience
- Projects if relevant
- Education
- Certifications
- Languages

Avoid tables, columns, icons, photos, and complex formatting.
""",
        "Modern Professional": f"""
Use a modern but ATS-safe professional format for {country}.
Sections:
- Header
- Professional Profile
- Key Skills / Tools
- Selected Achievements
- Professional Experience
- Projects
- Education
- Languages

Keep it elegant but still readable as plain text.
""",
        "Career Changer": f"""
Use a career-change focused CV format for {country}.
Sections:
- Target Role Headline
- Career Change Summary
- Transferable Skills
- Relevant Projects / Training
- Professional Experience with transferable achievements
- Technical Skills
- Education
- Languages

Position old experience as useful for the new target role.
""",
        "Fresh Graduate / Entry-Level": f"""
Use an entry-level CV format for {country}.
Sections:
- Career Objective / Profile
- Education
- Projects
- Technical Skills
- Internship / Work Experience if any
- Certifications / Courses
- Languages
- Activities or Achievements if relevant

Do not overstate experience. Emphasize proof of skill.
""",
        "Migration-Friendly": f"""
Use a migration-friendly CV format for {country}.
Sections:
- Contact Details
- Professional Summary adapted to {country}
- Target Role / Open Roles
- Key Skills
- Work Experience
- Projects
- Education
- Certifications
- Languages with CEFR level if possible
- Work authorization / relocation note only if provided by the user

Follow country expectations. If personal details/photo/date of birth are not recommended, avoid them.
""",
        "German-Style Lebenslauf": """
Use a German-style Lebenslauf structure.
Sections:
- Persönliche Daten / Contact Details
- Profil
- Berufserfahrung
- Weiterbildung / Certifications
- Ausbildung
- Kenntnisse / Skills
- Sprachen
- Projekte if relevant

Use reverse chronological order.
Mention German language level if provided.
Avoid inventing date of birth, nationality, marital status, photo, or signature.
""",
    }
    return instructions.get(template_name, instructions["ATS Classic"])

def render_cv_template_preview(template_name: str, target_country: str, user_status: str):
    st.markdown("### Template Preview")
    st.markdown(f"""
<div class="glass-card">
  <div class="section-title">{template_name}</div>
  <div class="small-muted">Target country: {target_country} • User status: {user_status}</div>
  <br>
  <div>{get_cv_template_options(target_country, user_status).get(template_name, "")}</div>
</div>
""", unsafe_allow_html=True)

    instructions = get_template_instructions(template_name, target_country)
    with st.expander("What this template includes", expanded=False):
        st.markdown(instructions)


def generate_country_cv_template(cv_text: str, target_country: str, user_status: str, template_name: str = "ATS Classic") -> str:
    template_instructions = get_template_instructions(template_name, target_country)

    prompt = build_quality_prompt(
        task="Rebuild the user's CV into a country-appropriate CV format using the selected template.",
        user_input=cv_text,
        expected_structure="""
1. Template and Country Fit Notes
2. Full Country-Specific CV Draft
3. What Was Changed
4. Missing Details to Confirm
"""
    )
    prompt += f"""

Target country: {target_country}
User status: {user_status}
Selected template: {template_name}

Template instructions:
{template_instructions}

Rules:
- The most important output is section 2: Full Country-Specific CV Draft.
- Do not split the CV into many empty fields.
- Use only the user's real information.
- Do not invent employers, dates, degrees, certifications, tools, achievements, nationality, visa status, or language level.
- Follow common professional expectations for the target country.
- If the selected country usually avoids photo/date of birth/personal details, mention this in section 1.
- Make the CV ATS-friendly and readable.
- If something is missing, put it only in section 4.
"""
    return run_ai_prompt(prompt)

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


# =========================================================
# DOCUMENT TOOLS
# =========================================================
def show_document_tools():
    st.subheader(txt("document_tools"))
    st.caption(txt("document_hub_caption"))

    tabs = st.tabs([
        "Improve CV for a Job",
        "Update Resume Details",
        txt("cv_template_builder"),
        txt("cover_letter_generator"),
        txt("cv_translator"),
        txt("cover_letter_translator"),
    ])

    # -----------------------------------------------------
    # 1. Improve CV for a Job
    # -----------------------------------------------------
    with tabs[0]:
        st.markdown("### Improve CV for a Job")
        st.caption("Use this when you have a specific job description. WorkZo will tailor your CV for that role.")
        current_cv = st.text_area(txt("your_cv"), value=organize_cv_for_display(st.session_state.cv_text), height=260, key="improve_cv_for_job_cv")
        job_desc_cv = st.text_area(txt("target_job"), height=220, key="improve_cv_for_job_desc")

        if st.button(txt("improve"), key="btn_improve_cv_for_job_v49"):
            if not current_cv.strip() or not job_desc_cv.strip():
                st.warning("Please provide both CV and job description.")
            else:
                with st.spinner("Improving CV for this job..."):
                    prompt = build_quality_prompt(
                        task="Tailor the user's CV to a specific job description.",
                        user_input=f"CV:\n{current_cv}\n\nJob description:\n{job_desc_cv}",
                        expected_structure="""
1. Fit Verdict
2. Better Professional Summary
3. Rewritten Experience Bullet Points
4. Missing Keywords from the Job
5. Skills to Move Higher
6. ATS-Friendly Suggestions
7. What Not to Change
8. Copy-Ready Tailored CV Sections
"""
                    )
                    prompt += """
Rules:
- Do not invent experience.
- Make it job-description specific.
- Focus on keywords, proof, and positioning.
"""
                    result = run_ai_prompt(prompt)
                    if render_error_or_success(result):
                        st.session_state.latest_cv_analysis = result
                        render_section_cards(result, default_expand=True)

    # -----------------------------------------------------
    # 2. Update Resume Details
    # -----------------------------------------------------
    with tabs[1]:
        st.markdown("### Update Resume Details")
        st.caption("Use this when your CV information changed: new experience, language level, tools, projects, certificates, or career break.")
        current_resume = st.text_area("Current Resume", value=organize_cv_for_display(st.session_state.cv_text), height=260, key="update_resume_current_v49")
        update_notes = st.text_area(
            "What changed?",
            height=160,
            key="update_resume_notes_v49",
            placeholder="Example: Add German A2, add my latest project, change experience from 3 years to 4 years, add Tableau certificate..."
        )
        optional_job_desc = st.text_area(
            "Optional job description",
            height=160,
            key="update_resume_optional_job_v49",
            placeholder="Paste a job description only if you also want this update tailored to a role."
        )

        if st.button("Update My Resume", key="btn_update_resume_v49"):
            if not current_resume.strip() or not update_notes.strip():
                st.warning("Please provide your current resume and what changed.")
            else:
                with st.spinner("Updating resume..."):
                    result = update_cv_with_ai(current_resume, update_notes, optional_job_desc)
                    if render_error_or_success(result):
                        st.session_state.latest_cv_analysis = result
                        render_section_cards(result, default_expand=True)

                        updated_cv = get_section_text(result, ["Updated CV", "Full Updated Resume", "Full CV"])
                        if updated_cv:
                            st.markdown("### Copy-ready updated CV")
                            st.text_area("Updated CV", value=updated_cv, height=340, key="updated_cv_text_area_v49")
                            if st.button("Save as Dashboard Resume", key="save_updated_cv_dashboard_v49"):
                                set_new_resume_and_refresh(updated_cv)
                                st.success("Saved as your dashboard resume.")
                                st.rerun()

    # -----------------------------------------------------
    # 3. Country CV Template Builder
    # -----------------------------------------------------
    with tabs[2]:
        st.markdown(f"### {txt('cv_template_builder')}")
        st.caption("Choose a country and template. WorkZo previews the template style, rebuilds your CV accordingly, and lets you download it as PDF.")

        target_country = st.selectbox(
            "Target CV country",
            country_options,
            index=country_options.index(st.session_state.get("migration_country") or st.session_state.country)
            if (st.session_state.get("migration_country") or st.session_state.country) in country_options else 0,
            key="country_template_target_v50"
        )

        user_status_for_template = st.session_state.get("user_status", "Not specified")
        template_options = get_cv_template_options(target_country, user_status_for_template)
        template_names = list(template_options.keys())

        selected_template = st.selectbox(
            "Choose CV template",
            template_names,
            index=0,
            key="country_cv_template_choice_v50",
            help="Choose the structure that best matches the user's situation and target country."
        )

        render_cv_template_preview(selected_template, target_country, user_status_for_template)

        cv_template_input = st.text_area(
            txt("your_cv"),
            value=organize_cv_for_display(st.session_state.cv_text),
            height=300,
            key="country_template_cv_v50"
        )

        col_a, col_b = st.columns([1, 1])
        with col_a:
            generate_clicked = st.button("Generate CV Preview", key="btn_country_cv_template_preview_v50")
        with col_b:
            st.caption("After preview is generated, download it as PDF below.")

        if generate_clicked:
            if not cv_template_input.strip():
                st.warning("Please provide your CV.")
            else:
                with st.spinner("Building country-specific CV preview..."):
                    result = generate_country_cv_template(
                        cv_template_input,
                        target_country,
                        user_status_for_template,
                        selected_template
                    )
                    if render_error_or_success(result):
                        st.session_state.latest_cv_analysis = result
                        st.session_state.generated_country_cv_result = result
                        st.session_state.generated_country_cv_template = selected_template
                        st.session_state.generated_country_cv_country = target_country

        if st.session_state.get("generated_country_cv_result"):
            result = st.session_state.generated_country_cv_result
            full_cv = get_section_text(result, ["Full Country-Specific CV Draft", "Rebuilt CV in Target Country Style", "Full CV"])

            st.markdown("### CV Preview")
            st.text_area(
                f"{st.session_state.get('generated_country_cv_template', selected_template)} preview for {st.session_state.get('generated_country_cv_country', target_country)}",
                value=full_cv,
                height=420,
                key="country_cv_preview_text_v50"
            )

            with st.expander("Template / Country Fit Notes", expanded=False):
                notes = get_section_text(result, ["Template and Country Fit Notes", "Country CV Format Notes"])
                st.write(notes)

            with st.expander("What WorkZo changed", expanded=False):
                changes = get_section_text(result, ["What Was Changed"])
                st.write(changes)

            with st.expander("Missing details to confirm", expanded=False):
                missing = get_section_text(result, ["Missing Details to Confirm"])
                st.write(missing)

            pdf_data = make_pdf_from_text(
                f"WorkZo CV - {st.session_state.get('generated_country_cv_country', target_country)} - {st.session_state.get('generated_country_cv_template', selected_template)}",
                full_cv
            )
            mime_type = "application/pdf" if SimpleDocTemplate is not None else "text/plain"
            file_ext = "pdf" if SimpleDocTemplate is not None else "txt"
            st.download_button(
                label=f"Download CV Preview as {file_ext.upper()}",
                data=pdf_data,
                file_name=f"workzo_{st.session_state.get('generated_country_cv_country', target_country).lower().replace(' ', '_')}_{st.session_state.get('generated_country_cv_template', selected_template).lower().replace(' ', '_')}_cv.{file_ext}",
                mime=mime_type,
                key="download_country_cv_pdf_v50"
            )

            if SimpleDocTemplate is None:
                st.warning("For real PDF downloads, add reportlab to requirements.txt.")

    # -----------------------------------------------------
    # 4. Cover Letter Generator
    # -----------------------------------------------------
    with tabs[3]:
        company_name = st.text_input("Company Name", key="doc_tools_company_name")
        role_name = st.text_input(txt("target_role"), key="doc_tools_role_name")
        job_desc_letter = st.text_area(txt("job_desc"), height=220, key="doc_tools_job_desc")

        if st.button(txt("generate"), key="btn_cover_letter_v49"):
            if not role_name.strip() or not job_desc_letter.strip():
                st.warning("Please enter a target role and job description.")
            elif not st.session_state.cv_text.strip():
                st.warning("Please upload or create a CV first.")
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

Write a strong, personalized professional cover letter.

Quality requirements:
- Use the candidate's actual CV details.
- Connect 3 to 5 specific candidate strengths to the job description.
- Avoid generic sentences.
- Sound natural, confident, and human.
- Keep it suitable for the selected country and role level.

Return in this exact structure:

1. Full Cover Letter
2. Short Email Version
3. 3 Customization Tips

Important:
- Do not leave any section empty.
- Write complete content for each section.
"""
                    result = run_ai_prompt(prompt)
                    if render_error_or_success(result):
                        if not result.strip():
                            st.error("Cover letter generation returned an empty response. Please try again.")
                        else:
                            st.session_state.latest_cover_letter = result
                            render_section_cards(result, default_expand=True)

                            sections = numbered_sections_to_markdown(result)
                            full_letter = sections.get("Full Cover Letter", "").strip()
                            short_email = sections.get("Short Email Version", "").strip()

                            if full_letter:
                                st.markdown("### Full Cover Letter")
                                st.text_area("Generated Cover Letter", value=full_letter, height=320)
                                st.download_button(
                                    "Download Cover Letter as TXT",
                                    data=full_letter,
                                    file_name="cover_letter.txt",
                                    mime="text/plain",
                                    key="download_cover_letter_txt_v49"
                                )
                            if short_email:
                                st.markdown("### Short Email Version")
                                st.text_area("Generated Short Email", value=short_email, height=180)

    # -----------------------------------------------------
    # 5. CV Translator
    # -----------------------------------------------------
    with tabs[4]:
        col1, col2 = st.columns(2)
        with col1:
            default_src = language_options.index("English") if "English" in language_options else 0
            source_lang = st.selectbox(txt("translator_source"), language_options, index=default_src, key="cv_src_lang")
        with col2:
            target_default = language_options.index("German") if "German" in language_options else 0
            target_lang = st.selectbox(txt("translator_target"), language_options, index=target_default, key="cv_tgt_lang")

        cv_input = st.text_area(txt("cv_input"), value=organize_cv_for_display(st.session_state.cv_text), height=280)

        if st.button(txt("translate"), key="btn_cv_translate_v49"):
            if not cv_input.strip():
                st.warning("Please provide your CV.")
            else:
                with st.spinner("Translating CV..."):
                    prompt = f"""
Translate and localize this CV from {source_lang} to {target_lang} for professional job applications.

Quality requirements:
- Translate naturally, not word-for-word.
- Keep the CV accurate. Do not invent experience, tools, dates, employers, or achievements.
- Adapt section headings to the target language and target-country CV style.
- Preserve achievements, metrics, tools, and responsibilities.
- Improve awkward phrasing while keeping the original meaning.
- Keep bullet points readable and ATS-friendly.
- Do not merge the CV into one paragraph.

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

    # -----------------------------------------------------
    # 6. Cover Letter Translator
    # -----------------------------------------------------
    with tabs[5]:
        col1, col2 = st.columns(2)
        with col1:
            source_default = language_options.index("English") if "English" in language_options else 0
            source_lang = st.selectbox(txt("translator_source"), language_options, index=source_default, key="cl_source_v49")
        with col2:
            target_default = language_options.index("German") if "German" in language_options else 0
            target_lang = st.selectbox(txt("translator_target"), language_options, index=target_default, key="cl_target_v49")

        cover_letter_input = st.text_area(
            txt("cover_letter_input"),
            value=st.session_state.latest_cover_letter if st.session_state.latest_cover_letter else "",
            height=280
        )

        if st.button(txt("translate"), key="btn_cover_letter_translate_v49"):
            if not cover_letter_input.strip():
                st.warning("Please paste your cover letter.")
            else:
                with st.spinner("Translating cover letter..."):
                    prompt = f"""
Translate and localize this cover letter from {source_lang} to {target_lang}.

Quality requirements:
- Make it sound like a natural professional cover letter in the target language.
- Preserve meaning, tone, paragraph structure, and application intent.
- Do not invent qualifications, employers, or achievements.
- Improve awkward direct translations.
- Keep it polite, confident, and country-appropriate.
- Return only the translated cover letter.

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

# =========================================================
# DASHBOARD
# =========================================================
# DASHBOARD
# =========================================================
def get_workflow_progress() -> int:
    steps = [
        bool(st.session_state.cv_text.strip()),
        bool(st.session_state.latest_job_analysis.strip()),
        bool(st.session_state.latest_cv_analysis.strip() or st.session_state.latest_cover_letter.strip() or st.session_state.latest_cv_translation.strip()),
        bool(st.session_state.next_best_step_result.strip() or st.session_state.latest_cover_letter.strip() or st.session_state.latest_job_analysis.strip()),
    ]
    return int(sum(steps) / len(steps) * 100)


def show_dashboard():
    with st.sidebar:
        st.title("WORKZO AI")
        st.caption("⚡ Beta V4.7")
        st.caption(f"🌍 {st.session_state.country}")
        st.caption(f"👤 {st.session_state.get('user_status', 'Not specified')}")
        if st.session_state.get("migration_country") and st.session_state.get("migration_country") != st.session_state.country:
            st.caption(f"🎯 Target: {st.session_state.migration_country}")

        language_list = ["English", "German", "Dutch"]
        current_language = st.session_state.get("preferred_language", "English")
        if current_language not in language_list:
            current_language = "English"
        preferred = st.selectbox(
            txt("preferred_language"),
            language_list,
            index=language_list.index(current_language),
            key="sidebar_preferred_language",
            help="This language controls both the app text and AI responses."
        )
        st.session_state.preferred_language = preferred
        st.session_state.ui_language = preferred
        st.session_state.response_language = preferred
        st.caption(f"Status: {st.session_state.get('user_status', 'Not specified')}")

        st.markdown("### Language")
        current_ui = st.session_state.get("ui_language", "English")
        st.session_state.ui_language = st.selectbox("App", ["English", "German", "Dutch"], index=["English", "German", "Dutch"].index(current_ui) if current_ui in ["English", "German", "Dutch"] else 0, key="sidebar_ui_lang")
        current_response = st.session_state.get("response_language", "English")
        resp_idx = language_options.index(current_response) if current_response in language_options else (language_options.index("English") if "English" in language_options else 0)
        st.session_state.response_language = st.selectbox("AI", language_options, index=resp_idx, key="sidebar_ai_lang")

        st.markdown(f"### {txt('actions')}")
        action_labels = [
            txt("dashboard"),
            txt("job_assist"),
            txt("document_tools"),
            txt("workobot"),
        ]
        page = st.radio("Navigation", action_labels, label_visibility="collapsed")

        progress_pct = get_workflow_progress()
        st.progress(progress_pct / 100)
        st.caption(f"Workflow progress: {progress_pct}%")

        st.markdown("---")
        st.caption("Suggested workflow")
        st.markdown("<div class='workflow-step'>1. Upload CV</div>", unsafe_allow_html=True)
        st.markdown("<div class='workflow-step'>2. Understand a job</div>", unsafe_allow_html=True)
        st.markdown("<div class='workflow-step'>3. Improve CV</div>", unsafe_allow_html=True)
        st.markdown("<div class='workflow-step'>4. Apply smarter</div>", unsafe_allow_html=True)

        st.markdown("---")
        if st.button(txt("edit_setup"), use_container_width=True):
            reset_onboarding()
            st.rerun()

    if page == txt("dashboard"):
        st.markdown(f"""
        <div class="hero-card">
            <div style="display:flex; justify-content:space-between; gap:14px; flex-wrap:wrap; align-items:center;">
                <div>
                    <div style="font-size:0.95rem; color:#cbd5e1; margin-bottom:6px;">Career command center</div>
                    <div style="font-size:1.65rem; font-weight:700; color:white; margin-bottom:6px;">Your next career move, organized</div>
                    <div style="color:#dbeafe; max-width:760px;">{txt('start_here_intro')}</div>
                </div>
                <div>
                    <div class="pill">Country: {st.session_state.country}</div>
                    <div class="pill">Status: {st.session_state.get('user_status', 'Not specified')}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            render_metric_card(txt("resume_score"), str(st.session_state.cv_score_value or "—"), "Overall quality and clarity")
        with m2:
            render_metric_card(txt("ats_score"), str(st.session_state.ats_score_value or "—"), "How scanner-friendly your resume looks")
        with m3:
            render_metric_card(txt("detected_role"), st.session_state.current_role_detected or "Not analyzed", "Detected from your current resume")
        with m4:
            roles_count = len([x for x in str(st.session_state.suggested_roles_detected).splitlines() if x.strip()]) if st.session_state.suggested_roles_detected else 0
            render_metric_card("Target roles", str(roles_count or "—"), "Suggested role cluster options")


        st.markdown("### What you should do next")
        n1, n2 = st.columns([1.1, 0.9])
        with n1:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            if st.session_state.next_actions_detected:
                st.markdown(st.session_state.next_actions_detected)
            else:
                status = st.session_state.get("user_status", "")
            target_country = st.session_state.get("migration_country") or st.session_state.get("country")
            if "migrate" in status.lower() or "abroad" in status.lower():
                st.markdown(f"- Adapt your CV to the {target_country} format.\n- Add local role keywords and remove country-inappropriate details.\n- Use Document Tools → Country CV Template before applying.")
            elif "graduate" in status.lower():
                st.markdown("- Add 1–2 portfolio projects.\n- Highlight tools, coursework, internships, and projects.\n- Target entry-level, trainee, or junior roles.")
            elif "career changer" in status.lower():
                st.markdown("- Connect your previous experience to the target role.\n- Add proof projects and bridge skills.\n- Avoid applying directly to senior roles in the new field.")
            else:
                st.markdown("- Improve the weakest CV sections first.\n- Use Job Assist after your CV is ready.\n- Tailor the CV for each job description.")
            st.markdown("</div>", unsafe_allow_html=True)
        with n2:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            if st.session_state.country_cv_readiness:
                st.markdown(f"**Country CV readiness:** {st.session_state.country_cv_readiness}")
            if st.session_state.status_guidance:
                st.markdown(f"**Status guidance:** {st.session_state.status_guidance}")
            if not st.session_state.country_cv_readiness and not st.session_state.status_guidance:
                target_country = st.session_state.get("migration_country") or st.session_state.get("country")
            st.markdown(f"- Target country: **{target_country}**\n- WorkZo will judge your CV against this market.\n- Use the Country CV Template tool if the format does not match the target country.")
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("### Explore tools")
        f1, f2, f3 = st.columns(3)
        with f1:
            render_feature_tile("🧭", "Job Assist", "Understand a role, find live jobs, and see where you realistically fit before applying.")
        with f2:
            render_feature_tile("📝", "Document Tools", "Improve your CV, generate a cover letter, translate documents, and update your resume faster.")
        with f3:
            render_feature_tile("🤖", "Work-O-Bot", "Country-aware coaching for interviews, communication, mock questions, and next steps.")

        top_left, top_right = st.columns([1.1, 0.9])
        with top_left:
            st.markdown("### Resume insights")
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.markdown(f"**{txt('detected_summary')}**")
            st.write(st.session_state.profile_summary or txt("not_analyzed"))
            st.markdown(f"**{txt('detected_skills')}**")
            if st.session_state.key_skills_detected:
                st.markdown(st.session_state.key_skills_detected)
            else:
                st.info(txt("not_analyzed"))
            st.markdown("</div>", unsafe_allow_html=True)

            left_a, left_b = st.columns(2)
            with left_a:
                st.markdown("### Strengths")
                st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                if st.session_state.resume_strengths:
                    st.markdown(st.session_state.resume_strengths)
                else:
                    st.info(txt("not_analyzed"))
                st.markdown("</div>", unsafe_allow_html=True)
            with left_b:
                st.markdown("### Improvements")
                st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                if st.session_state.resume_improvements:
                    st.markdown(st.session_state.resume_improvements)
                else:
                    st.info(txt("not_analyzed"))
                st.markdown("</div>", unsafe_allow_html=True)

        with top_right:
            st.markdown(f"### {txt('top_countries_fit')}")
            st.caption(txt("country_fit_note"))
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            if st.session_state.best_fit_countries_detected:
                st.markdown(st.session_state.best_fit_countries_detected)
            else:
                st.info(txt("not_analyzed"))
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown(f"### {txt('suggested_roles')}")
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            if st.session_state.suggested_roles_detected:
                st.markdown(st.session_state.suggested_roles_detected)
            else:
                st.info(txt("not_analyzed"))
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("### Standout feature: Next Best Step")
        st.caption("A personalized action center based on your resume, country, and role direction.")
        action_col1, action_col2 = st.columns([1, 1.2])
        with action_col1:
            if st.button("Generate My Next Best Step", use_container_width=True, key="btn_next_best_step"):
                with st.spinner("Building your action center..."):
                    st.session_state["next_best_step_result"] = generate_next_best_steps(
                        st.session_state.cv_text,
                        st.session_state.country,
                        st.session_state.current_role_detected,
                        st.session_state.suggested_roles_detected,
                        st.session_state.get("user_status", ""),
                        st.session_state.get("career_goal", ""),
                    )
            if st.button(txt("refresh_resume"), use_container_width=True):
                with st.spinner("Refreshing..."):
                    analyze_resume_dashboard_stable(st.session_state.cv_text, force_refresh=True)
                st.success("Dashboard updated.")
                st.rerun()
        with action_col2:
            next_best = st.session_state.get("next_best_step_result", "")
            if next_best:
                render_section_cards(next_best, default_expand=True)
            else:
                st.info("Generate a personalized action center to see your best immediate goal, weekly priorities, role cluster, and the message you should send today.")

    elif page == txt("document_tools"):
        show_document_tools()

    elif page == txt("job_assist"):
        st.subheader(txt("job_assist"))
        assist_tab1, assist_tab2 = st.tabs([txt("find_jobs"), txt("understand_job")])

        with assist_tab1:
            st.markdown(f"### {txt('find_jobs')}")
            st.caption("Real job openings first. If live jobs are unavailable for the exact search, WorkZo still shows role-specific job-board links and a fallback plan.")

            target_country_options = country_options
            country_index = target_country_options.index(st.session_state.country) if st.session_state.country in target_country_options else 0
            search_country = st.selectbox("Country for job search", target_country_options, index=country_index, key="job_assist_search_country")

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

            cv_for_jobs = st.text_area(txt("your_cv"), value=organize_cv_for_display(st.session_state.cv_text), height=240, key="job_assist_cv")
            target_titles = st.text_input(
                "Optional target job titles",
                placeholder="Example: Data Analyst, Reporting Analyst, IT Support",
                key="job_assist_target_titles"
            )

            if st.button(txt("generate"), key="btn_find_jobs_v42"):
                if not cv_for_jobs.strip():
                    st.warning("Please provide your CV.")
                else:
                    with st.spinner("Searching live jobs..."):
                        roles_from_input = [x.strip() for x in target_titles.split(",") if x.strip()]
                        roles_from_input = build_role_suggestions(
                            roles_from_input,
                            st.session_state.suggested_roles_detected,
                            st.session_state.current_role_detected
                        )

                        live_jobs = fetch_live_jobs_global(search_country, roles_from_input, final_location)
                        render_live_jobs(live_jobs, search_country)

                        st.markdown("### Apply through job boards")
                        for role in roles_from_input[:3]:
                            st.markdown(f"**{role}**")
                            for label, url in get_job_board_links(search_country, final_location, role):
                                st.markdown(f"- [{label}]({url})")

                        plan = generate_job_search_plan(
                            search_country,
                            final_location,
                            roles_from_input,
                            cv_for_jobs,
                            live_jobs
                        )
                        render_job_plan(plan)

        with assist_tab2:
            st.markdown(f"### {txt('understand_job')}")
            st.caption("Paste a job description to see fit, hidden expectations, salary estimate, likely interview focus, and how to tailor your application.")

            job_desc = st.text_area(txt("job_desc"), key="job_desc_v42", height=240)

            if st.button(txt("analyze"), key="btn_understand_job_v42"):
                if not job_desc.strip():
                    st.warning("Please enter a job description.")
                else:
                    with st.spinner("Analyzing the job..."):
                        prompt = f"""
Country: {st.session_state.country}
Candidate CV:
{st.session_state.cv_text}

Analyze this job description for the candidate.

Return in this exact structure:

1. Role Snapshot
2. Main Responsibilities
3. Must-Have Requirements
4. Nice-to-Have Requirements
5. Hidden Expectations
6. Salary Range Estimate for {st.session_state.country}
7. Fit Verdict
Give a realistic fit score from 0 to 100 and explain.
8. Match Breakdown
- Strong matches
- Partial matches
- Clear gaps
9. Risks / Concerns
10. How to Tailor the CV
11. Likely Interview Focus
12. Should You Apply?
Give a short recommendation: Yes / Yes, but tailor / Maybe later

Job description:
{job_desc}
"""
                        result = run_ai_prompt(prompt)
                        if render_error_or_success(result):
                            st.session_state.latest_job_analysis = result
                            st.session_state.job_fit_score_value = parse_score(result)
                            if st.session_state.job_fit_score_value is not None:
                                show_gauge(st.session_state.job_fit_score_value, txt("job_fit_score"))
                            st.markdown(f"### {txt('job_fit_analysis')}")
                            render_section_cards(result, default_expand=True)

    elif page == txt("workobot"):
        show_workobot()

    st.divider()
    st.caption("WORKZO AI V5.0 • Status-aware onboarding • Stronger AI outputs • Improved document tools")

# =========================================================
# ROUTER
# =========================================================
if not st.session_state.onboarding_complete or st.session_state.page == "onboarding":
    show_onboarding()
else:
    show_dashboard()

