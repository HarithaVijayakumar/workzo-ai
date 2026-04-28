# WorkZo modular split v138
# Source: app_workzo_v137_stable_no_feature_change.py, lines 2112-2622

def ui_lang() -> str:
    # Keep the user's selected language even when we do not have a manual UI_TEXT dictionary for it.
    # This allows French, Portuguese, Spanish, etc. to use the automatic translation fallback.
    return st.session_state.get("preferred_language", st.session_state.get("ui_language", "English")) or "English"

def ui_label(text: str) -> str:
    """Translate a visible UI phrase automatically when the selected language is not English."""
    lang = ui_lang()
    return ai_translate_ui(text, lang) if lang != "English" else text

def txt(key: str) -> str:
    lang = ui_lang()

    # 1) Use a manually curated translation if available.
    val = UI_TEXT.get(lang, {}).get(key)
    if val:
        return val

    # 2) If the selected language is not manually supported, translate from the English label.
    english_val = UI_TEXT.get("English", {}).get(key)
    if english_val:
        return ai_translate_ui(english_val, lang)

    # 3) Last fallback: translate a cleaned version of the key.
    readable_key = str(key).replace("_", " ").strip()
    return ai_translate_ui(readable_key, lang)



# =========================================================
# STUDENT / THESIS / INTERNSHIP CAREER PATH
# =========================================================
STUDENT_STATUS_INTERNAL = "Student / Thesis / Internship seeker"

STUDENT_JOB_KEYWORDS_BY_COUNTRY = {
    "germany": ["Praktikum", "Werkstudent", "Abschlussarbeit", "Bachelorarbeit", "Masterarbeit", "Thesis", "Trainee"],
    "austria": ["Praktikum", "Werkstudent", "Abschlussarbeit", "Bachelorarbeit", "Masterarbeit", "Trainee"],
    "switzerland": ["Praktikum", "Werkstudent", "Internship", "Thesis", "Trainee"],
    "netherlands": ["Stage", "Afstudeerstage", "Werkstudent", "Internship", "Traineeship"],
    "the netherlands": ["Stage", "Afstudeerstage", "Werkstudent", "Internship", "Traineeship"],
    "belgium": ["Stage", "Internship", "Student job", "Thesis", "Traineeship"],
    "france": ["Stage", "Alternance", "Apprentissage", "Internship", "Trainee"],
    "spain": ["Practicas", "Becario", "Internship", "Trainee"],
    "italy": ["Tirocinio", "Stage", "Internship", "Trainee"],
    "portugal": ["Estagio", "Internship", "Trainee"],
    "united kingdom": ["Placement Year", "Internship", "Graduate Intern", "Industrial Placement", "Sandwich Placement"],
    "uk": ["Placement Year", "Internship", "Graduate Intern", "Industrial Placement", "Sandwich Placement"],
    "ireland": ["Internship", "Graduate Intern", "Placement", "Trainee"],
    "united states": ["Internship", "Co-op", "Student Intern", "New Grad", "Campus"],
    "usa": ["Internship", "Co-op", "Student Intern", "New Grad", "Campus"],
    "canada": ["Internship", "Co-op", "Student Intern", "New Grad", "Campus"],
    "india": ["Internship", "Trainee", "Fresher Internship", "Graduate Trainee", "Campus"],
    "australia": ["Internship", "Vacation Program", "Graduate Program", "Student Intern"],
    "new zealand": ["Internship", "Graduate Program", "Student Intern"],
    "singapore": ["Internship", "Traineeship", "Graduate Intern", "Student Intern"],
    "default": ["Internship", "Student Intern", "Thesis", "Placement", "Working Student", "Trainee", "Graduate Intern"],
}

def is_student_thesis_status(user_status: str) -> bool:
    status = (user_status or "").lower()
    return any(x in status for x in ["student / thesis", "thesis", "internship seeker", "praktikum", "placement", "afstudeer", "abschlussarbeit", "werkstudent", "stagezoeker"])

def get_student_job_keywords(country_name: str) -> List[str]:
    country = (country_name or st.session_state.get("migration_country") or st.session_state.get("country") or "").strip().lower()
    return STUDENT_JOB_KEYWORDS_BY_COUNTRY.get(country, STUDENT_JOB_KEYWORDS_BY_COUNTRY["default"])

def render_student_opportunity_guidance(country_name: str):
    keywords = get_student_job_keywords(country_name)
    st.markdown(f"### {txt('student_opportunities')}")
    st.caption(txt("student_guidance_caption"))
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**{txt('student_search_keywords')}**")
        st.markdown(" ".join([f"<span class='pill'>{html.escape(k)}</span>" for k in keywords[:8]]), unsafe_allow_html=True)
    with c2:
        st.markdown(f"**{txt('student_cv_tips')}**")
        st.markdown("- Put education, thesis topic, and projects near the top.\n- Add tools, coursework, and university/research projects.\n- Use student-friendly role titles instead of only full-time junior roles.\n- Keep the CV focused on learning potential and practical proof.")

LANG_EXTRA = {
    "English": {
        "navigation": "Navigation", "workflow_progress": "Workflow progress", "suggested_workflow": "Suggested workflow",
        "workflow_upload_cv": "1. Upload CV", "workflow_understand_job": "2. Understand a job", "workflow_improve_cv": "3. Improve CV", "workflow_apply_smarter": "4. Apply smarter",
        "career_command_center": "Your Career Dashboard", "career_move_organized": "Everything you need to plan your next career step",
        "country_label": "Country", "status_label": "Status", "not_specified": "Not specified",
        "metric_resume_quality": "Overall quality and clarity", "metric_ats_friendly": "How scanner-friendly your resume looks", "metric_detected_resume": "Detected from your current resume",
        "target_roles": "Target roles", "metric_role_cluster": "Suggested role cluster options", "what_next": "What you should do next",
        "next_default_1": "Improve the weakest CV sections first.", "next_default_2": "Use Job Assist after your CV is ready.", "next_default_3": "Tailor the CV for each job description.",
        "next_migrate_1": "Adapt your CV to the target-country format.", "next_migrate_2": "Add local role keywords and remove country-inappropriate details.", "next_migrate_3": "Use Document Tools → Country CV Template before applying.",
        "next_graduate_1": "Add 1-2 portfolio projects.", "next_graduate_2": "Highlight tools, coursework, internships, and projects.", "next_graduate_3": "Target entry-level, trainee, or junior roles.",
        "next_changer_1": "Connect your previous experience to the target role.", "next_changer_2": "Add proof projects and bridge skills.", "next_changer_3": "Avoid applying directly to senior roles in the new field.",
        "country_cv_readiness": "Country CV readiness", "status_guidance": "Status guidance", "target_country_label": "Target country", "judge_market": "WorkZo will judge your CV against this market.", "use_country_template": "Use the Country CV Template tool if the format does not match the target country.",
        "job_assist_desc": "Understand a role, find live jobs, and see where you realistically fit before applying.", "document_tools_desc": "Improve your CV, generate a cover letter, translate documents, and update your resume faster.", "workobot_desc": "Country-aware coaching for interviews, communication, mock questions, and next steps.",
        "standout_next_best_step": "Standout feature: Next Best Step", "next_best_caption": "A personalized action center based on your resume, country, and role direction.", "generate_next_best_step": "Generate My Next Best Step", "building_action_center": "Building your action center...", "refreshing": "Refreshing...", "dashboard_updated": "Dashboard updated.",
        "next_best_empty": "Generate a personalized action center to see your best immediate goal, weekly priorities, role cluster, and the message you should send today.",
        "founder_dashboard": "Founder Dashboard", "founder_access": "Founder access", "founder_pin": "Founder PIN", "open_job": "Open job", "job_summary_first": "Top matches first. Click any job card to open the posting.", "details_later": "Show details", "country_fit_summary": "Country fit summary", "country_fit_details": "Country-fit details", "view_details": "View details", "no_founder_pin": "Add FOUNDER_PIN in secrets to unlock founder analytics.", "recommended_next_step": "Recommended Next Step", "next_action_upload_title": "Upload your CV first", "next_action_upload_desc": "WorkZo needs your CV to calculate scores and guide your next career step.", "next_action_upload_button": "Upload CV", "next_action_improve_title": "Improve your CV for ATS", "next_action_improve_desc": "Your ATS score can improve. Start by strengthening keywords, structure, and country-specific formatting.", "next_action_improve_button": "Improve My CV", "next_action_job_title": "Analyze a job before applying", "next_action_job_desc": "Your CV is ready. Paste a job description or find matching jobs to understand your fit.", "next_action_job_button": "Go to Job Assist", "next_action_interview_title": "Practice for your next interview", "next_action_interview_desc": "You have started job preparation. Now practice answers based on your profile and target role.", "next_action_interview_button": "Practice Interview"
    },
    "German": {
        "navigation": "Navigation", "workflow_progress": "Workflow-Fortschritt", "suggested_workflow": "Empfohlener Ablauf",
        "workflow_upload_cv": "1. Lebenslauf hochladen", "workflow_understand_job": "2. Stelle verstehen", "workflow_improve_cv": "3. Lebenslauf verbessern", "workflow_apply_smarter": "4. Gezielter bewerben",
        "career_command_center": "Karriere-Kommandozentrale", "career_move_organized": "Dein nachster Karriereschritt, klar organisiert",
        "country_label": "Land", "status_label": "Status", "not_specified": "Nicht angegeben",
        "metric_resume_quality": "Gesamtqualitat und Klarheit", "metric_ats_friendly": "Wie ATS-freundlich dein Lebenslauf wirkt", "metric_detected_resume": "Aus deinem aktuellen Lebenslauf erkannt",
        "target_roles": "Zielrollen", "metric_role_cluster": "Vorgeschlagene Rollen-Cluster", "what_next": "Was du als Nachstes tun solltest",
        "next_default_1": "Verbessere zuerst die schwachsten Lebenslaufbereiche.", "next_default_2": "Nutze den Job-Assistenten, sobald dein Lebenslauf bereit ist.", "next_default_3": "Passe den Lebenslauf an jede Stellenbeschreibung an.",
        "next_migrate_1": "Passe deinen Lebenslauf an das Format des Ziellandes an.", "next_migrate_2": "Erganze lokale Rollen-Keywords und entferne unpassende Angaben.", "next_migrate_3": "Nutze vor der Bewerbung Dokument-Tools → Lebenslauf-Vorlage nach Land.",
        "next_graduate_1": "Fuge 1-2 Portfolio-Projekte hinzu.", "next_graduate_2": "Betone Tools, Kurse, Praktika und Projekte.", "next_graduate_3": "Bewirb dich gezielt auf Einstiegs-, Trainee- oder Junior-Rollen.",
        "next_changer_1": "Verbinde deine bisherige Erfahrung klar mit der Zielrolle.", "next_changer_2": "Fuge Nachweisprojekte und Bruckenkompetenzen hinzu.", "next_changer_3": "Bewirb dich im neuen Bereich nicht direkt auf Senior-Rollen.",
        "country_cv_readiness": "Lebenslauf-Eignung fur das Zielland", "status_guidance": "Hinweise zu deiner Situation", "target_country_label": "Zielland", "judge_market": "WorkZo bewertet deinen Lebenslauf fur diesen Arbeitsmarkt.", "use_country_template": "Nutze die Lebenslauf-Vorlage nach Land, wenn das Format nicht zum Zielland passt.",
        "job_assist_desc": "Verstehe eine Rolle, finde Live-Jobs und erkenne realistisch, wo du vor der Bewerbung passt.", "document_tools_desc": "Verbessere deinen Lebenslauf, erstelle ein Anschreiben, ubersetze Dokumente und aktualisiere deine Bewerbung schneller.", "workobot_desc": "Landerspezifisches Coaching fur Interviews, Kommunikation, Ubungsfragen und nachste Schritte.",
        "standout_next_best_step": "Besondere Funktion: Nachster bester Schritt", "next_best_caption": "Ein personalisiertes Aktionszentrum basierend auf deinem Lebenslauf, Land und deiner Rollenrichtung.", "generate_next_best_step": "Meinen nachsten besten Schritt erstellen", "building_action_center": "Aktionszentrum wird erstellt...", "refreshing": "Aktualisiere...", "dashboard_updated": "Dashboard aktualisiert.",
        "next_best_empty": "Erstelle ein personalisiertes Aktionszentrum, um dein wichtigstes Sofortziel, Wochenprioritaten, Rollen-Cluster und die heutige Nachricht zu sehen.",
        "founder_dashboard": "Founder-Dashboard", "founder_access": "Founder-Zugang", "founder_pin": "Founder-PIN", "open_job": "Job offnen", "job_summary_first": "Beste Treffer zuerst. Klicke auf eine Jobkarte, um die Anzeige zu offnen.", "details_later": "Details anzeigen", "country_fit_summary": "Beste Lander fur diesen Lebenslauf", "country_fit_details": "Details zur Lander-Eignung", "view_details": "Details anzeigen", "no_founder_pin": "Fuge FOUNDER_PIN in Secrets hinzu, um Founder Analytics zu offnen.", "recommended_next_step": "Empfohlener nachster Schritt", "next_action_upload_title": "Lade zuerst deinen Lebenslauf hoch", "next_action_upload_desc": "WorkZo braucht deinen Lebenslauf, um Scores zu berechnen und deinen nachsten Karriereschritt zu empfehlen.", "next_action_upload_button": "Lebenslauf hochladen", "next_action_improve_title": "Verbessere deinen Lebenslauf fur ATS", "next_action_improve_desc": "Dein ATS-Score kann besser werden. Starke zuerst Keywords, Struktur und landerspezifisches Format.", "next_action_improve_button": "Lebenslauf verbessern", "next_action_job_title": "Analysiere eine Stelle vor der Bewerbung", "next_action_job_desc": "Dein Lebenslauf ist bereit. Fuge eine Stellenbeschreibung ein oder finde passende Jobs.", "next_action_job_button": "Zum Job-Assistenten", "next_action_interview_title": "Ube fur dein nachstes Interview", "next_action_interview_desc": "Du hast mit der Bewerbungsvorbereitung begonnen. Ube jetzt Antworten passend zu Profil und Zielrolle.", "next_action_interview_button": "Interview uben"
    },
    "Dutch": {
        "navigation": "Navigatie", "workflow_progress": "Workflowvoortgang", "suggested_workflow": "Aanbevolen workflow",
        "workflow_upload_cv": "1. CV uploaden", "workflow_understand_job": "2. Vacature begrijpen", "workflow_improve_cv": "3. CV verbeteren", "workflow_apply_smarter": "4. Slimmer solliciteren",
        "career_command_center": "Carriere-commandocentrum", "career_move_organized": "Je volgende carrieremove, helder georganiseerd",
        "country_label": "Land", "status_label": "Status", "not_specified": "Niet opgegeven",
        "metric_resume_quality": "Algemene kwaliteit en duidelijkheid", "metric_ats_friendly": "Hoe ATS-vriendelijk je cv is", "metric_detected_resume": "Gedetecteerd uit je huidige cv",
        "target_roles": "Doelrollen", "metric_role_cluster": "Voorgestelde rolclusters", "what_next": "Wat je nu moet doen",
        "next_default_1": "Verbeter eerst de zwakste cv-onderdelen.", "next_default_2": "Gebruik Jobhulp zodra je cv klaar is.", "next_default_3": "Pas je cv aan voor elke vacaturetekst.",
        "next_migrate_1": "Pas je cv aan aan het format van het doelland.", "next_migrate_2": "Voeg lokale rolkeywords toe en verwijder ongepaste gegevens.", "next_migrate_3": "Gebruik Documenttools → Country CV Template voordat je solliciteert.",
        "next_graduate_1": "Voeg 1-2 portfolio-projecten toe.", "next_graduate_2": "Benadruk tools, cursussen, stages en projecten.", "next_graduate_3": "Richt je op starters-, trainee- of juniorrollen.",
        "next_changer_1": "Koppel je eerdere ervaring aan de doelrol.", "next_changer_2": "Voeg bewijsprojecten en brugvaardigheden toe.", "next_changer_3": "Solliciteer niet direct op seniorrollen in het nieuwe vakgebied.",
        "country_cv_readiness": "CV-gereedheid voor doelland", "status_guidance": "Advies voor je situatie", "target_country_label": "Doelland", "judge_market": "WorkZo beoordeelt je cv voor deze arbeidsmarkt.", "use_country_template": "Gebruik de Country CV Template-tool als het format niet past bij het doelland.",
        "job_assist_desc": "Begrijp een rol, vind live vacatures en zie realistisch waar je past voordat je solliciteert.", "document_tools_desc": "Verbeter je cv, maak een motivatiebrief, vertaal documenten en werk je sollicitatie sneller bij.", "workobot_desc": "Landbewuste coaching voor interviews, communicatie, oefenvragen en vervolgstappen.",
        "standout_next_best_step": "Sterke functie: Volgende beste stap", "next_best_caption": "Een persoonlijk actiecentrum gebaseerd op je cv, land en rolrichting.", "generate_next_best_step": "Maak mijn volgende beste stap", "building_action_center": "Actiecentrum wordt gemaakt...", "refreshing": "Vernieuwen...", "dashboard_updated": "Dashboard bijgewerkt.",
        "next_best_empty": "Maak een persoonlijk actiecentrum om je beste directe doel, weekprioriteiten, rolcluster en het bericht dat je vandaag moet sturen te zien.",
        "founder_dashboard": "Founder dashboard",
        "founder_access": "Founder access",
        "founder_pin": "Founder PIN",
        "open_job": "Open job",
        "job_summary_first": "Best matches first. Click a job card to open it.",
        "details_later": "Show details",
        "country_fit_summary": "Country fit",
        "country_fit_details": "Country fit details",
        "view_details": "View details",
        "no_founder_pin": "Add FOUNDER_PIN in secrets to unlock founder analytics.",
        "recommended_next_step": "Recommended next step",
        "next_action_upload_title": "Upload your CV first",
        "next_action_upload_desc": "WorkZo needs your CV to calculate scores and guide your next career step.",
        "next_action_upload_button": "Upload CV",
        "next_action_improve_title": "Improve your CV for ATS",
        "next_action_improve_desc": "Your ATS score can improve. Start with keywords, structure and country-specific formatting.",
        "next_action_improve_button": "Improve my CV",
        "next_action_job_title": "Analyze a job before applying",
        "next_action_job_desc": "Your CV is ready. Paste a job description or find matching jobs.",
        "next_action_job_button": "Go to Job Help",
        "next_action_interview_title": "Practice for your next interview",
        "next_action_interview_desc": "Practice answers based on your profile and target role.",
        "next_action_interview_button": "Practice interview"
    }
}
for _lang, _items in LANG_EXTRA.items():
    UI_TEXT.setdefault(_lang, {}).update(_items)

# =========================================================
# UI LOCALIZATION CLEANUP PATCH (WorkZo v8.1)
# Fixes mixed English/German/Dutch labels in onboarding and CV builder.
# =========================================================
UI_LOCALIZATION_PATCH = {
    "English": {
        "select_optional": "Select one option",
        "beta_privacy_note": "⚠️ WorkZo AI is currently in Beta. Some results may not be perfect yet. Your feedback helps improve the tool. Privacy note: WorkZo collects anonymous usage data such as features used, selected country/status, and session duration. It does not store your CV text, email, phone number, address, or personal documents.",
        "language_help": "This language is used for the app, AI replies, and generated documents.",
        "status_help": "Optional. Select this only if it matches your current situation.",
        "resume_choice_caption": "Choose one option to add your resume. You can upload an existing CV or create one with the guided builder.",
        "upload_cv_title": "Upload CV",
        "upload_cv_desc": "Best if you already have a PDF or text CV.",
        "create_cv_title": "Create CV",
        "create_cv_desc": "Best if you want WorkZo to build a CV from your details.",
        "choose_resume_continue": "Please choose Upload CV or Create CV to continue.",
        "file_too_large": "File too large. Please upload a CV under 5 MB.",
        "upload_cv_instruction": "Please upload a PDF or TXT CV using the Upload CV option above.",
        "guided_cv_caption": "Add what you know. WorkZo will generate a cleaner CV and ask what is missing.",
        "location": "Location",
        "languages_label": "Languages",
        "cert_courses": "Certifications / Courses",
        "projects_label": "Projects",
        "pdf_read_error": "PDF read error",
    },
    "German": {
        "select_optional": "Option auswahlen",
        "beta_privacy_note": "⚠️ WorkZo AI ist aktuell in der Beta-Version. Manche Ergebnisse sind möglicherweise noch nicht perfekt. Dein Feedback hilft, das Tool zu verbessern. Datenschutzhinweis: WorkZo erfasst anonyme Nutzungsdaten wie verwendete Funktionen, ausgewähltes Land/Status und Sitzungsdauer. Dein Lebenslauftext, deine E-Mail, Telefonnummer, Adresse oder persönliche Dokumente werden nicht gespeichert.",
        "language_help": "Diese Sprache wird fur die App, KI-Antworten und erstellte Dokumente verwendet.",
        "status_help": "Optional. Wahle dies nur aus, wenn es zu deiner aktuellen Situation passt.",
        "resume_choice_caption": "Wahle eine Option aus, um deinen Lebenslauf hinzuzufugen. Du kannst einen vorhandenen Lebenslauf hochladen oder mit dem gefuhrten Builder einen neuen erstellen.",
        "upload_cv_title": "Lebenslauf hochladen",
        "upload_cv_desc": "Ideal, wenn du bereits einen PDF- oder Text-Lebenslauf hast.",
        "create_cv_title": "Lebenslauf erstellen",
        "create_cv_desc": "Ideal, wenn WorkZo aus deinen Angaben einen Lebenslauf erstellen soll.",
        "choose_resume_continue": "Bitte wahle Lebenslauf hochladen oder Lebenslauf erstellen, um fortzufahren.",
        "file_too_large": "Die Datei ist zu groÃ. Bitte lade einen Lebenslauf unter 5 MB hoch.",
        "upload_cv_instruction": "Bitte lade oben uber die Option Lebenslauf hochladen eine PDF- oder TXT-Datei hoch.",
        "guided_cv_caption": "Fuge hinzu, was du weiÃt. WorkZo erstellt daraus einen klareren Lebenslauf und erganzt fehlende Punkte.",
        "location": "Standort",
        "languages_label": "Sprachen",
        "cert_courses": "Zertifikate / Kurse",
        "projects_label": "Projekte",
        "pdf_read_error": "PDF-Lesefehler",
        "career_command_center": "Dein Karriere-Dashboard",
        "career_move_organized": "Alles, was du fur deinen nachsten Karriereschritt brauchst",
    },
    "Dutch": {
        "preferred_language": "Taal selecteren",
        "user_status": "Huidige carrieresituatie",
        "fresh_graduate": "Afgestudeerd / starter",
        "student_thesis_internship": "Student / scriptie / stagezoeker",
        "career_changer": "Carriereswitcher",
        "migrant": "Verhuizen / solliciteren in het buitenland",
        "local_jobseeker": "Lokaal werk zoeken",
        "experienced": "Ervaren professional",
        "returning": "Terugkeer na loopbaanpauze",
        "guided_cv_builder": "Begeleide CV-builder",
        "generate_cv": "CV genereren met AI",
        "extra_cv_info": "Wil je extra informatie toevoegen?",
        "country_readiness": "Landgeschiktheid",
        "next_steps": "Wat moet je nu doen?",
        "cv_template_builder": "Landspecifieke CV-builder",
        "migration_country": "Naar welk land wil je verhuizen/solliciteren?",
        "chosen_country_resume_score": "CV-gereedheid voor gekozen land",
        "select_optional": "Selecteer een optie",
        "beta_privacy_note": "⚠️ WorkZo AI is momenteel in beta. Sommige resultaten zijn mogelijk nog niet perfect. Jouw feedback helpt om de tool te verbeteren. Privacyverklaring: WorkZo verzamelt anonieme gebruiksgegevens zoals gebruikte functies, gekozen land/status en sessieduur. Je CV-tekst, e-mail, telefoonnummer, adres of persoonlijke documenten worden niet opgeslagen.",
        "language_help": "Deze taal wordt gebruikt voor de app, AI-antwoorden en gegenereerde documenten.",
        "status_help": "Optioneel. Selecteer dit alleen als het past bij je huidige situatie.",
        "resume_choice_caption": "Kies een optie om je CV toe te voegen. Je kunt een bestaand CV uploaden of er een maken met de begeleide builder.",
        "upload_cv_title": "CV uploaden",
        "upload_cv_desc": "Beste keuze als je al een PDF- of tekst-CV hebt.",
        "create_cv_title": "CV maken",
        "create_cv_desc": "Beste keuze als je wilt dat WorkZo een CV maakt op basis van jouw gegevens.",
        "choose_resume_continue": "Kies CV uploaden of CV maken om door te gaan.",
        "file_too_large": "Bestand is te groot. Upload een CV kleiner dan 5 MB.",
        "upload_cv_instruction": "Upload hierboven een PDF- of TXT-CV via de optie CV uploaden.",
        "guided_cv_caption": "Voeg toe wat je weet. WorkZo maakt er een duidelijker CV van en vult ontbrekende punten aan.",
        "location": "Locatie",
        "languages_label": "Talen",
        "cert_courses": "Certificaten / Cursussen",
        "projects_label": "Projecten",
        "pdf_read_error": "PDF-leesfout",
    },
}
for _lang, _items in UI_LOCALIZATION_PATCH.items():
    UI_TEXT.setdefault(_lang, {}).update(_items)

# =========================================================
# ONBOARDING GLOBAL UX PATCH (WorkZo v9.7)
# =========================================================
ONBOARDING_GLOBAL_TEXT = {
    "English": {
        "app_info_help": "WorkZo analyzes your resume, adapts it to your selected country, suggests jobs, identifies skill gaps, and helps you prepare for interviews.",
        "privacy_short": "⚠️ WorkZo AI is currently in Beta. Some results may not be perfect yet. Your feedback helps improve the tool. Privacy note: WorkZo collects anonymous usage data such as features used, selected country/status, and session duration. It does not store your CV text, email, phone number, address, or personal documents.",
        "detected_country_hint": "Suggested country based on your location",
        "resume_choice_caption": "Choose how you want to start. You can upload a CV, create one with AI, or paste a LinkedIn profile link.",
        "upload_cv_desc": "Upload an existing PDF or TXT CV.",
        "create_cv_desc": "Enter rough notes or broken English. WorkZo will turn them into a professional CV.",
        "linkedin_cv_title": "Import LinkedIn",
        "linkedin_cv_desc": "Paste your LinkedIn profile link and add any extra notes.",
        "linkedin_profile_link": "LinkedIn Profile Link",
        "linkedin_extra_details": "Optional: paste LinkedIn About / Experience text or extra notes",
        "linkedin_instruction": "Public LinkedIn pages are often restricted. For best results, paste your LinkedIn link plus your About, Experience, Skills, or key notes.",
        "choose_resume_continue": "Choose one resume option to continue.",
        "upload_cv_instruction": "Upload your CV",
        "guided_cv_caption": "Write in keywords or broken English if needed. WorkZo will clean, expand, and translate it based on your selected language.",
        "suggested_skills": "Suggested skills",
        "education_level": "Education level",
        "target_role_optional": "Target role / job title",
        "generated_language_note": "Generated CV language",
        "select_upload": "Upload CV",
        "select_create": "Create CV",
        "select_linkedin": "Import LinkedIn"
    },
    "German": {
        "app_info_help": "WorkZo analysiert deinen Lebenslauf, passt ihn an das gewahlte Land an, schlagt Jobs vor, erkennt Kompetenzlucken und hilft bei der Interviewvorbereitung.",
        "privacy_short": "Beta-Datenschutz: Anonyme Nutzung wird erfasst, aber Lebenslauftext und persönliche Dokumente werden nicht gespeichert.",
        "detected_country_hint": "Vorgeschlagenes Land basierend auf deinem Standort",
        "resume_choice_caption": "Wahle, wie du starten mochtest: CV hochladen, mit KI erstellen oder LinkedIn-Profil einfugen.",
        "upload_cv_desc": "Lade einen vorhandenen PDF- oder TXT-Lebenslauf hoch.",
        "create_cv_desc": "Gib grobe Notizen oder fehlerhaftes Englisch ein. WorkZo erstellt daraus einen professionellen Lebenslauf.",
        "linkedin_cv_title": "LinkedIn importieren",
        "linkedin_cv_desc": "Fuge deinen LinkedIn-Profillink ein und erganze Notizen.",
        "linkedin_profile_link": "LinkedIn-Profillink",
        "linkedin_extra_details": "Optional: LinkedIn-Info / Erfahrung oder zusatzliche Notizen einfugen",
        "linkedin_instruction": "Ãffentliche LinkedIn-Seiten sind oft eingeschrankt. Fur beste Ergebnisse: Link plus Info, Erfahrung, Skills oder Stichpunkte einfugen.",
        "guided_cv_caption": "Schreibe bei Bedarf Stichworter oder fehlerhaftes Englisch. WorkZo bereinigt, erweitert und ubersetzt es passend zur gewahlten Sprache.",
        "suggested_skills": "Vorgeschlagene Fahigkeiten",
        "education_level": "Bildungsniveau",
        "target_role_optional": "Zielrolle / Berufsbezeichnung",
        "generated_language_note": "Sprache des generierten Lebenslaufs",
        "select_upload": "Upload auswahlen",
        "select_create": "Erstellen auswahlen",
        "select_linkedin": "LinkedIn auswahlen"
    },
    "Dutch": {
        "app_info_help": "WorkZo analyseert je CV, past het aan je geselecteerde land aan, suggereert banen, vindt vaardigheidskloven en helpt met interviewvoorbereiding.",
        "privacy_short": "Beta-privacy: anoniem gebruik wordt bijgehouden, maar CV-tekst en persoonlijke documenten worden niet opgeslagen.",
        "detected_country_hint": "Voorgesteld land op basis van je locatie",
        "resume_choice_caption": "Kies hoe je wilt starten: CV uploaden, met AI maken of LinkedIn-profiel plakken.",
        "upload_cv_desc": "Upload een bestaand PDF- of TXT-CV.",
        "create_cv_desc": "Voer ruwe notities of gebroken Engels in. WorkZo maakt er een professioneel CV van.",
        "linkedin_cv_title": "LinkedIn importeren",
        "linkedin_cv_desc": "Plak je LinkedIn-profiel en voeg extra notities toe.",
        "linkedin_profile_link": "LinkedIn-profiel link",
        "linkedin_extra_details": "Optioneel: plak LinkedIn Over / Ervaring of extra notities",
        "linkedin_instruction": "Openbare LinkedIn-pagina's zijn vaak beperkt. Plak voor het beste resultaat de link plus Over, Ervaring, Skills of kernpunten.",
        "guided_cv_caption": "Schrijf desnoods trefwoorden of gebroken Engels. WorkZo maakt het netter, breidt het uit en vertaalt het naar je gekozen taal.",
        "suggested_skills": "Voorgestelde vaardigheden",
        "education_level": "Opleidingsniveau",
        "target_role_optional": "Doelrol / functietitel",
        "generated_language_note": "Taal van gegenereerd CV",
        "select_upload": "Upload selecteren",
        "select_create": "Maken selecteren",
        "select_linkedin": "LinkedIn selecteren"
    },
}
for _lang, _items in ONBOARDING_GLOBAL_TEXT.items():
    UI_TEXT.setdefault(_lang, {}).update(_items)

# =========================================================
# DYNAMIC COUNTRY + LANGUAGE DATA
# =========================================================
def get_country_options() -> List[str]:
    if pycountry:
        countries = sorted({c.name for c in pycountry.countries if getattr(c, "name", None)})
    else:
        countries = [
            "Afghanistan", "Albania", "Algeria", "Argentina", "Australia", "Austria", "Bangladesh",
            "Belgium", "Brazil", "Bulgaria", "Canada", "Chile", "China", "Colombia", "Croatia",
            "Czechia", "Denmark", "Egypt", "Estonia", "Finland", "France", "Germany", "Greece",
            "Hungary", "India", "Indonesia", "Ireland", "Italy", "Japan", "Kenya", "Malaysia",
            "Mexico", "Netherlands", "New Zealand", "Nigeria", "Norway", "Pakistan", "Philippines",
            "Poland", "Portugal", "Romania", "Saudi Arabia", "Singapore", "South Africa", "South Korea",
            "Spain", "Sri Lanka", "Sweden", "Switzerland", "Thailand", "Turkey", "United Arab Emirates",
            "United Kingdom", "United States", "Vietnam"
        ]
    return countries

def get_language_options() -> List[str]:
    priority_languages = [
        "English", "German", "French", "Portuguese", "Spanish", "Dutch", "Italian",
        "Arabic", "Hindi", "Bengali", "Chinese", "Japanese", "Korean", "Tamil",
        "Telugu", "Malayalam", "Kannada", "Marathi", "Urdu", "Turkish", "Polish",
        "Romanian", "Swedish", "Norwegian", "Danish", "Finnish", "Greek", "Russian",
        "Ukrainian", "Indonesian", "Malay", "Thai", "Vietnamese"
    ]
    if pycountry:
        all_languages = sorted({
            getattr(lang, "name", "").strip()
            for lang in pycountry.languages
            if getattr(lang, "name", None)
            and len(getattr(lang, "name", "")) > 1
            and "sign language" not in getattr(lang, "name", "").lower()
        })
        languages = list(dict.fromkeys(priority_languages + all_languages))
    else:
        languages = priority_languages
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

