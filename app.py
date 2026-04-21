import os
import urllib.parse
import streamlit as st
import pdfplumber
from openai import OpenAI
from dotenv import load_dotenv

# -----------------------------
# LOAD ENV + API
# -----------------------------
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    st.error("OPENAI_API_KEY not found. Please check your .env file.")
    st.stop()

client = OpenAI(api_key=api_key)

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="WORKZO AI",
    page_icon="🚀",
    layout="wide"
)

# -----------------------------
# TRANSLATIONS
# -----------------------------
translations = {
    "English": {
        "title": "Your 360° AI Career Assistant",
        "subtitle": "Personalized career support based on your country, language, and profile.",
        "start": "Let’s get started",
        "start_info": "Choose your country, preferred language, and add your CV to continue.",
        "select_country": "Select your target country",
        "select_language": "Select your preferred language",
        "select_option": "Select",
        "continue_mode": "How would you like to continue?",
        "upload_cv": "Upload CV",
        "create_cv": "Create CV",
        "upload_your_cv": "Upload your CV",
        "create_your_cv": "Create your CV",
        "full_name": "Full Name",
        "email": "Email",
        "phone": "Phone Number",
        "summary": "Professional Summary",
        "skills": "Skills",
        "experience": "Work Experience",
        "education": "Education",
        "continue": "Continue",
        "setup_complete": "Setup complete. Your personalized dashboard is ready.",
        "edit_setup": "Edit Setup",
        "response_language": "Response language",
        "country_label": "Country",
        "language_label": "Language",
        "cv_mode_label": "CV Mode",
        "tab1": "📘 Understand Job",
        "tab2": "📄 Improve CV",
        "tab3": "🗣️ Career Communication",
        "tab4": "🔍 Find Jobs",
        "tab5": "🎤 Mock Interview",
        "tab6": "📊 Skill Gap",
        "tab7": "🛣️ Career Roadmap",
        "interview_language": "Interview language",
        "job_title": "Job title",
        "background": "Short background about yourself",
        "paste_job": "Paste the job description",
        "your_cv": "Your CV",
        "paste_target_job": "Paste the target job description",
        "preferred_location": "Preferred city or region",
        "target_role": "Target role",
        "target_job_optional": "Target job description (optional)",
        "current_role": "Your current role",
        "target_role_roadmap": "Your target role",
        "current_profile": "Your current profile / CV",
        "explain_job": "Explain Job",
        "improve_cv": "Improve CV",
        "score_cv": "Score CV",
        "find_jobs": "Find Jobs",
        "generate_mock": "Generate Interview Practice",
        "analyze_gap": "Analyze Skill Gap",
        "generate_roadmap": "Generate Career Roadmap",
        "done": "Done",
        "analyzing": "Analyzing...",
        "improving_cv": "Improving CV...",
        "finding_jobs": "Finding jobs...",
        "preparing_interview": "Preparing interview practice...",
        "analyzing_gap": "Analyzing skill gap...",
        "generating_roadmap": "Generating roadmap...",
        "scoring_cv": "Scoring CV...",
        "warn_country": "Please select a country.",
        "warn_language": "Please select a language.",
        "warn_upload_cv": "Please upload your CV before continuing.",
        "warn_full_name": "Please enter your full name.",
        "warn_summary": "Please enter your professional summary.",
        "warn_skills": "Please enter your skills.",
        "warn_experience": "Please enter your work experience.",
        "warn_education": "Please enter your education.",
        "warn_job_desc": "Please enter a job description.",
        "warn_cv_and_job": "Please provide both CV and job description.",
        "warn_cv_only": "Please provide your CV.",
        "warn_job_title": "Please enter a job title.",
        "warn_target_role_profile": "Please enter your target role and your CV/profile.",
        "warn_all_fields": "Please fill in your current role, target role, and profile.",
        "unsupported_file": "Unsupported file type.",
        "ai_unavailable": "⚠️ AI service unavailable",
        "job_fit_analysis": "Job Fit Analysis",
        "cv_score_result": "CV Score Result",
        "career_comm_mode": "Practice mode",
        "career_comm_input": "Type your answer or message",
        "career_comm_button": "Practice Communication",
        "career_comm_job": "Target job (optional)",
        "career_comm_mode_1": "Self Introduction",
        "career_comm_mode_2": "Interview Answer Practice",
        "career_comm_mode_3": "HR Call Practice",
        "career_comm_mode_4": "Workplace Conversation",
        "career_comm_mode_5": "Email / Message Improvement",
        "career_comm_result": "Career Communication Feedback",
        "career_comm_warn": "Please enter a message or answer to practice.",
        "search_queries": "Suggested search links",
        "platform_hint": "These links open Google searches. Later, you can replace them with LinkedIn, Indeed, StepStone, or local job portals."
    },
    "German": {
        "title": "Dein 360° KI-Karriereassistent",
        "subtitle": "Personalisierte Karriereunterstützung basierend auf deinem Land, deiner Sprache und deinem Profil.",
        "start": "Lass uns loslegen",
        "start_info": "Wähle dein Zielland, deine bevorzugte Sprache und füge deinen Lebenslauf hinzu, um fortzufahren.",
        "select_country": "Wähle dein Zielland",
        "select_language": "Wähle deine bevorzugte Sprache",
        "select_option": "Bitte wählen",
        "continue_mode": "Wie möchtest du fortfahren?",
        "upload_cv": "Lebenslauf hochladen",
        "create_cv": "Lebenslauf erstellen",
        "upload_your_cv": "Lade deinen Lebenslauf hoch",
        "create_your_cv": "Erstelle deinen Lebenslauf",
        "full_name": "Vollständiger Name",
        "email": "E-Mail",
        "phone": "Telefonnummer",
        "summary": "Berufliche Zusammenfassung",
        "skills": "Kenntnisse",
        "experience": "Berufserfahrung",
        "education": "Ausbildung",
        "continue": "Weiter",
        "setup_complete": "Einrichtung abgeschlossen. Dein personalisiertes Dashboard ist bereit.",
        "edit_setup": "Einstellungen bearbeiten",
        "response_language": "Antwortsprache",
        "country_label": "Land",
        "language_label": "Sprache",
        "cv_mode_label": "Lebenslauf-Modus",
        "tab1": "📘 Stelle verstehen",
        "tab2": "📄 Lebenslauf verbessern",
        "tab3": "🗣️ Karrierekommunikation",
        "tab4": "🔍 Jobs finden",
        "tab5": "🎤 Vorstellungsgespräch",
        "tab6": "📊 Kompetenzlücke",
        "tab7": "🛣️ Karriereplan",
        "interview_language": "Sprache des Vorstellungsgesprächs",
        "job_title": "Berufsbezeichnung",
        "background": "Kurzer Hintergrund über dich",
        "paste_job": "Stellenbeschreibung einfügen",
        "your_cv": "Dein Lebenslauf",
        "paste_target_job": "Ziel-Stellenbeschreibung einfügen",
        "preferred_location": "Bevorzugte Stadt oder Region",
        "target_role": "Zielrolle",
        "target_job_optional": "Ziel-Stellenbeschreibung (optional)",
        "current_role": "Deine aktuelle Rolle",
        "target_role_roadmap": "Deine Zielrolle",
        "current_profile": "Dein aktuelles Profil / Lebenslauf",
        "explain_job": "Stelle erklären",
        "improve_cv": "Lebenslauf verbessern",
        "score_cv": "Lebenslauf bewerten",
        "find_jobs": "Jobs finden",
        "generate_mock": "Interviewtraining erstellen",
        "analyze_gap": "Kompetenzlücke analysieren",
        "generate_roadmap": "Karriereplan erstellen",
        "done": "Fertig",
        "analyzing": "Analysiere...",
        "improving_cv": "Verbessere Lebenslauf...",
        "finding_jobs": "Suche Jobs...",
        "preparing_interview": "Erstelle Interviewtraining...",
        "analyzing_gap": "Analysiere Kompetenzlücke...",
        "generating_roadmap": "Erstelle Karriereplan...",
        "scoring_cv": "Bewerte Lebenslauf...",
        "warn_country": "Bitte wähle ein Land.",
        "warn_language": "Bitte wähle eine Sprache.",
        "warn_upload_cv": "Bitte lade deinen Lebenslauf hoch.",
        "warn_full_name": "Bitte gib deinen vollständigen Namen ein.",
        "warn_summary": "Bitte gib deine berufliche Zusammenfassung ein.",
        "warn_skills": "Bitte gib deine Kenntnisse ein.",
        "warn_experience": "Bitte gib deine Berufserfahrung ein.",
        "warn_education": "Bitte gib deine Ausbildung ein.",
        "warn_job_desc": "Bitte gib eine Stellenbeschreibung ein.",
        "warn_cv_and_job": "Bitte gib Lebenslauf und Stellenbeschreibung ein.",
        "warn_cv_only": "Bitte gib deinen Lebenslauf ein.",
        "warn_job_title": "Bitte gib eine Berufsbezeichnung ein.",
        "warn_target_role_profile": "Bitte gib Zielrolle und Profil ein.",
        "warn_all_fields": "Bitte fülle alle Felder aus.",
        "unsupported_file": "Nicht unterstützter Dateityp.",
        "ai_unavailable": "⚠️ KI-Dienst derzeit nicht verfügbar",
        "job_fit_analysis": "Job-Fit-Analyse",
        "cv_score_result": "Ergebnis der Lebenslaufbewertung",
        "career_comm_mode": "Übungsmodus",
        "career_comm_input": "Schreibe deine Antwort oder Nachricht",
        "career_comm_button": "Kommunikation üben",
        "career_comm_job": "Zielberuf (optional)",
        "career_comm_mode_1": "Selbstvorstellung",
        "career_comm_mode_2": "Interviewantwort üben",
        "career_comm_mode_3": "HR-Anruf üben",
        "career_comm_mode_4": "Gespräch am Arbeitsplatz",
        "career_comm_mode_5": "E-Mail / Nachricht verbessern",
        "career_comm_result": "Feedback zur Karrierekommunikation",
        "career_comm_warn": "Bitte gib eine Nachricht oder Antwort ein.",
        "search_queries": "Vorgeschlagene Suchlinks",
        "platform_hint": "Diese Links öffnen Google-Suchen. Später kannst du sie durch LinkedIn, Indeed, StepStone oder lokale Jobportale ersetzen."
    }
}

# -----------------------------
# SESSION STATE
# -----------------------------
defaults = {
    "onboarding_complete": False,
    "country": "",
    "language": "",
    "cv_text": "",
    "cv_mode": "Upload CV",
    "onboarding_country": "",
    "onboarding_language": ""
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# -----------------------------
# HELPERS
# -----------------------------
def active_lang() -> str:
    return st.session_state.language if st.session_state.language in translations else "English"

def t(key: str) -> str:
    return translations[active_lang()].get(key, key)

def ui_lang_for_selection(selected_language: str) -> str:
    return selected_language if selected_language in translations else "English"

def run_ai_prompt(prompt: str) -> str:
    lang = st.session_state.language if st.session_state.language else "English"
    system_prompt = f"""
You are WorkZo AI, a professional career assistant.

Always respond ONLY in {lang}.
Be clear, structured, practical, and helpful for job seekers.
"""
    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        return res.choices[0].message.content
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {str(e)}"

def show_ai_result(result: str):
    if result.startswith("ERROR:"):
        st.error(t("ai_unavailable"))
        st.caption(result)
    else:
        st.success(t("done"))
        st.write(result)

def google_search_url(query: str) -> str:
    return "https://www.google.com/search?q=" + urllib.parse.quote(query)

# -----------------------------
# HEADER
# -----------------------------
st.markdown(f"""
# 🚀 WORKZO AI
### {t("title")}

{t("subtitle")}
""")

st.divider()

# -----------------------------
# ONBOARDING
# -----------------------------
if not st.session_state.onboarding_complete:
    onboarding_lang = ui_lang_for_selection(st.session_state.onboarding_language)
    labels = translations[onboarding_lang]

    st.subheader(labels["start"])
    st.info(labels["start_info"])

    country = st.selectbox(
    labels["select_country"],
    ["", "Germany", "Austria", "Netherlands", "India", "France", "Canada", "Other"],
    format_func=lambda x: labels["select_option"] if x == "" else x,
    key="onboarding_country"
)
    language = st.selectbox(
    labels["select_language"],
    ["", "German", "English", "Dutch"],
    format_func=lambda x: labels["select_option"] if x == "" else x,
    key="onboarding_language"
)
    current_ui_lang = ui_lang_for_selection(language)
    current_labels = translations[current_ui_lang]

    if language in translations and st.session_state.language != language:
        st.session_state.language = language
        st.rerun()

    with st.form("onboarding_form"):
        cv_mode_display = st.radio(
            current_labels["continue_mode"],
            [current_labels["upload_cv"], current_labels["create_cv"]]
        )
        cv_mode = "Upload CV" if cv_mode_display == current_labels["upload_cv"] else "Create CV"

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
                current_labels["upload_your_cv"],
                type=["txt", "pdf"]
            )

            if uploaded_file is not None:
                if uploaded_file.type == "text/plain":
                    cv_text_input = uploaded_file.read().decode("utf-8")

                elif uploaded_file.type == "application/pdf":
                    text = ""
                    with pdfplumber.open(uploaded_file) as pdf:
                        for page in pdf.pages:
                            page_text = page.extract_text()
                            if page_text:
                                text += page_text + "\n"
                    cv_text_input = text.strip()
                else:
                    st.error(current_labels["unsupported_file"])

        else:
            st.markdown(f"#### {current_labels['create_your_cv']}")
            full_name = st.text_input(current_labels["full_name"])
            email = st.text_input(current_labels["email"])
            phone = st.text_input(current_labels["phone"])
            summary = st.text_area(current_labels["summary"])
            skills = st.text_area(current_labels["skills"])
            experience = st.text_area(current_labels["experience"])
            education = st.text_area(current_labels["education"])

            if any([
                full_name.strip(),
                email.strip(),
                phone.strip(),
                summary.strip(),
                skills.strip(),
                experience.strip(),
                education.strip()
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

        submitted = st.form_submit_button(current_labels["continue"])

        if submitted:
            if not country:
                st.warning(current_labels["warn_country"])
            elif not language:
                st.warning(current_labels["warn_language"])
            elif cv_mode == "Upload CV":
                if not cv_text_input.strip():
                    st.warning(current_labels["warn_upload_cv"])
                else:
                    st.session_state.country = country
                    st.session_state.language = language
                    st.session_state.cv_mode = cv_mode
                    st.session_state.cv_text = cv_text_input
                    st.session_state.onboarding_complete = True
                    st.rerun()
            else:
                if not full_name.strip():
                    st.warning(current_labels["warn_full_name"])
                elif not summary.strip():
                    st.warning(current_labels["warn_summary"])
                elif not skills.strip():
                    st.warning(current_labels["warn_skills"])
                elif not experience.strip():
                    st.warning(current_labels["warn_experience"])
                elif not education.strip():
                    st.warning(current_labels["warn_education"])
                else:
                    st.session_state.country = country
                    st.session_state.language = language
                    st.session_state.cv_mode = cv_mode
                    st.session_state.cv_text = cv_text_input
                    st.session_state.onboarding_complete = True
                    st.rerun()

# -----------------------------
# MAIN DASHBOARD
# -----------------------------
else:
    with st.sidebar:
        st.title("WORKZO AI")
        st.write(t("title"))
        st.success(f"{t('response_language')}: {st.session_state.language}")
        st.info(f"{t('country_label')}: {st.session_state.country}")
        st.info(f"{t('language_label')}: {st.session_state.language}")
        st.write(f"{t('cv_mode_label')}: {st.session_state.cv_mode}")

        if st.button(t("edit_setup"), key="btn_edit_setup"):
            st.session_state.onboarding_complete = False
            st.rerun()

    st.success(t("setup_complete"))

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        t("tab1"),
        t("tab2"),
        t("tab3"),
        t("tab4"),
        t("tab5"),
        t("tab6"),
        t("tab7")
    ])

    # -----------------------------
    # TAB 1 — UNDERSTAND JOB
    # -----------------------------
    with tab1:
        st.subheader(t("tab1"))
        job_desc = st.text_area(t("paste_job"), key="job_desc")

        if st.button(t("explain_job"), key="btn_explain_job"):
            if not job_desc.strip():
                st.warning(t("warn_job_desc"))
            else:
                with st.spinner(t("analyzing")):
                    prompt = f"""
Country: {st.session_state.country}
Candidate CV:
{st.session_state.cv_text}

Analyze this job description for the candidate.

Return in this exact order:

1. Overview
Write one short and very easy-to-understand paragraph explaining the job.

2. Main Responsibilities
- ...

3. Required Skills
- ...

4. Compatibility Score
Give a percentage from 0 to 100 showing how well the candidate's CV matches this job.
Also explain briefly why.

5. Quick Skill Gap
- Skills the candidate already has
- Skills missing or weak
- What to improve first

Job description:
{job_desc}
"""
                    result = run_ai_prompt(prompt)
                    if not result.startswith("ERROR:"):
                        st.markdown(f"### {t('job_fit_analysis')}")
                    show_ai_result(result)

    # -----------------------------
    # TAB 2 — IMPROVE CV
    # -----------------------------
    with tab2:
        st.subheader(t("tab2"))
        current_cv = st.text_area(
            t("your_cv"),
            value=st.session_state.cv_text,
            key="cv_text_main"
        )
        job_desc_cv = st.text_area(
            t("paste_target_job"),
            key="job_desc_cv"
        )

        if st.button(t("improve_cv"), key="btn_improve_cv"):
            if not current_cv.strip() or not job_desc_cv.strip():
                st.warning(t("warn_cv_and_job"))
            else:
                with st.spinner(t("improving_cv")):
                    prompt = f"""
Country: {st.session_state.country}

Improve this CV for the target job.

Return:
1. Better summary
2. Improved bullet points
3. Skills to highlight
4. ATS-friendly suggestions

CV:
{current_cv}

Job description:
{job_desc_cv}
"""
                    result = run_ai_prompt(prompt)
                    show_ai_result(result)

        if st.button(t("score_cv"), key="btn_score_cv"):
            if not current_cv.strip():
                st.warning(t("warn_cv_only"))
            else:
                with st.spinner(t("scoring_cv")):
                    prompt = f"""
Country: {st.session_state.country}

Analyze this CV and give a score from 0 to 100.

Return:
1. CV Score
2. Strengths
3. Weaknesses
4. ATS issues
5. Suggestions to improve

CV:
{current_cv}
"""
                    result = run_ai_prompt(prompt)
                    if not result.startswith("ERROR:"):
                        st.markdown(f"### {t('cv_score_result')}")
                    show_ai_result(result)

    # -----------------------------
    # TAB 3 — CAREER COMMUNICATION
    # -----------------------------
    with tab3:
        st.subheader(t("tab3"))

        practice_mode = st.selectbox(
            t("career_comm_mode"),
            [
                t("career_comm_mode_1"),
                t("career_comm_mode_2"),
                t("career_comm_mode_3"),
                t("career_comm_mode_4"),
                t("career_comm_mode_5")
            ],
            key="career_comm_mode"
        )

        practice_job = st.text_input(
            t("career_comm_job"),
            key="career_comm_job"
        )

        user_input = st.text_area(
            t("career_comm_input"),
            key="career_comm_input"
        )

        if st.button(t("career_comm_button"), key="btn_career_comm"):
            if not user_input.strip():
                st.warning(t("career_comm_warn"))
            else:
                with st.spinner(t("checking") if "checking" in translations[active_lang()] else t("analyzing")):
                    prompt = f"""
Country: {st.session_state.country}
Practice language: {st.session_state.language}
Practice mode: {practice_mode}
Target job: {practice_job if practice_job.strip() else "Not specified"}

User answer:
{user_input}

Act as a career communication coach.

Return in this exact structure:

1. Corrected Version
Correct the user's response.

2. Natural Professional Version
Rewrite it to sound more natural and professional.

3. Explanation
Briefly explain the main mistakes.

4. Interview / Career Tip
Give 1 useful tip to sound more confident.

5. Next Question
Ask one realistic follow-up question to continue the practice.
"""
                    result = run_ai_prompt(prompt)
                    if not result.startswith("ERROR:"):
                        st.markdown(f"### {t('career_comm_result')}")
                    show_ai_result(result)

    # -----------------------------
    # TAB 4 — FIND JOBS
    # -----------------------------
    with tab4:
        st.subheader(t("tab4"))
        location = st.text_input(t("preferred_location"), key="location")
        cv_for_jobs = st.text_area(
            t("your_cv"),
            value=st.session_state.cv_text,
            key="cv_for_jobs"
        )

        if st.button(t("find_jobs"), key="btn_find_jobs"):
            if not cv_for_jobs.strip():
                st.warning(t("warn_cv_only"))
            else:
                with st.spinner(t("finding_jobs")):
                    prompt = f"""
Country: {st.session_state.country}
Preferred location: {location if location.strip() else st.session_state.country}

Candidate CV:
{cv_for_jobs}

Act as a smart career matching assistant.

Return in this exact structure:

1. Best-Match Roles
List the 5 most suitable roles for this CV.

2. Match Reason
For each role, explain in 1 short line why it matches the candidate's profile.

3. Recommended Seniority
Say whether the candidate is best suited for entry-level, junior, mid-level, or specialist roles.

4. Location-Based Search Queries
Give highly specific search queries using the preferred location.
Examples:
- Data Analyst jobs in Munich
- Junior Business Analyst Berlin English
- IT Support hybrid Hamburg

5. Work Mode Suggestions
Suggest suitable Onsite / Hybrid / Remote options based on the role.

6. Best Job Platforms to Search
Suggest the most relevant platforms or channels to search on for this country and role type.

7. Application Priority
Rank which roles the candidate should apply to first and why.
"""
                    result = run_ai_prompt(prompt)
                    show_ai_result(result)

                    # Clickable search links
                    if not result.startswith("ERROR:"):
                        city = location.strip() if location.strip() else st.session_state.country
                        sample_queries = [
                            f"Jobs {city} {st.session_state.country}",
                            f"{city} English jobs {st.session_state.country}",
                            f"{city} hybrid jobs {st.session_state.country}"
                        ]

                        st.markdown(f"### {t('search_queries')}")
                        for q in sample_queries:
                            st.markdown(f"- [{q}]({google_search_url(q)})")

                        st.caption(t("platform_hint"))

    # -----------------------------
    # TAB 5 — MOCK INTERVIEW
    # -----------------------------
    with tab5:
        st.subheader(t("tab5"))
        interview_role = st.text_input(t("job_title"), key="interview_role")

        language_options = ["German", "English"]
        if st.session_state.language in language_options:
            language_options = [st.session_state.language] + [
                lang for lang in language_options if lang != st.session_state.language
            ]

        interview_language = st.selectbox(
            t("interview_language"),
            language_options,
            key="interview_language"
        )

        interview_background = st.text_area(
            t("background"),
            value=st.session_state.cv_text,
            key="interview_background"
        )

        if st.button(t("generate_mock"), key="btn_mock_interview"):
            if not interview_role.strip():
                st.warning(t("warn_job_title"))
            else:
                with st.spinner(t("preparing_interview")):
                    prompt = f"""
Country: {st.session_state.country}
Interview language: {interview_language}
Job title: {interview_role}

Candidate background:
{interview_background}

Return:
1. 5 likely interview questions
2. Sample answers
3. Improvement tips
4. Common mistakes to avoid
"""
                    result = run_ai_prompt(prompt)
                    show_ai_result(result)

    # -----------------------------
    # TAB 6 — SKILL GAP
    # -----------------------------
    with tab6:
        st.subheader(t("tab6"))
        target_role_gap = st.text_input(t("target_role"), key="target_role_gap")
        current_cv_gap = st.text_area(
            t("your_cv"),
            value=st.session_state.cv_text,
            key="current_cv_gap"
        )
        target_job_desc_gap = st.text_area(
            t("target_job_optional"),
            key="target_job_desc_gap"
        )

        if st.button(t("analyze_gap"), key="btn_skill_gap"):
            if not target_role_gap.strip() or not current_cv_gap.strip():
                st.warning(t("warn_target_role_profile"))
            else:
                with st.spinner(t("analyzing_gap")):
                    prompt = f"""
Country: {st.session_state.country}
Target role: {target_role_gap}

Analyze the user's current profile and identify the skill gap.

Return in this format:

Current Strengths:
- ...

Missing Skills:
- ...

Important Tools / Technologies to Learn:
- ...

Language / Communication Gaps:
- ...

Recommended Next Steps:
- ...

User CV / Profile:
{current_cv_gap}

Target job description:
{target_job_desc_gap if target_job_desc_gap.strip() else "Not provided"}
"""
                    result = run_ai_prompt(prompt)
                    show_ai_result(result)

    # -----------------------------
    # TAB 7 — CAREER ROADMAP
    # -----------------------------
    with tab7:
        st.subheader(t("tab7"))
        current_role = st.text_input(t("current_role"), key="current_role")
        target_role_roadmap = st.text_input(
            t("target_role_roadmap"),
            key="target_role_roadmap"
        )
        current_profile = st.text_area(
            t("current_profile"),
            value=st.session_state.cv_text,
            key="current_profile"
        )

        if st.button(t("generate_roadmap"), key="btn_career_roadmap"):
            if not current_role.strip() or not target_role_roadmap.strip() or not current_profile.strip():
                st.warning(t("warn_all_fields"))
            else:
                with st.spinner(t("generating_roadmap")):
                    prompt = f"""
Country: {st.session_state.country}

Current role: {current_role}
Target role: {target_role_roadmap}

Create a practical career roadmap for this user.

Return in this format:

Goal:
- ...

Step-by-Step Roadmap:
1. ...
2. ...
3. ...

Skills to Build First:
- ...

Projects to Add to Portfolio:
- ...

Certifications or Learning Suggestions:
- ...

Job Application Strategy:
- ...

Estimated Timeline:
- Short term
- Medium term
- Long term

User profile:
{current_profile}
"""
                    result = run_ai_prompt(prompt)
                    show_ai_result(result)

    st.divider()
    st.caption("MVP • WORKZO AI • Your 360° AI Career Assistant")