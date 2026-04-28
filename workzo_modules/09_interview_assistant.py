# WorkZo modular split v138
# Source: app_workzo_v137_stable_no_feature_change.py, lines 10803-11206

def _workzo_latest_cv_text() -> str:
    """Use the cleanest approved CV source available for interview coaching."""
    for key in ["clean_structured_cv_text", "approved_structured_cv_text", "improved_cv_text_v92", "cv_text", "created_cv_text"]:
        value = st.session_state.get(key, "")
        if isinstance(value, str) and value.strip():
            return value.strip()
    profile = st.session_state.get("structured_cv_profile")
    if isinstance(profile, dict):
        try:
            return json.dumps(profile, ensure_ascii=False, indent=2)
        except Exception:
            return str(profile)
    return ""


def _workzo_latest_job_description() -> str:
    """Find the most recent JD from Understand Job / Prepare Job / Improve CV."""
    for key in ["last_understand_job_description", "last_prepare_job_description", "job_desc_prepare_v928", "job_desc_v42", "improve_cv_for_job_desc", "doc_tools_job_desc"]:
        value = st.session_state.get(key, "")
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _workzo_score_label(score: int) -> str:
    try:
        score = int(score)
    except Exception:
        score = 0
    if score >= 85:
        return "Strong"
    if score >= 70:
        return "Good"
    if score >= 55:
        return "Needs practice"
    return "Weak"


def _workzo_interview_mode_instruction(mode: str) -> str:
    mode = (mode or "").lower()
    if "technical" in mode:
        return "Focus on technical requirements, tools, problem solving, tradeoffs, and practical examples."
    if "behavior" in mode or "starr" in mode:
        return "Focus on STARR: Situation, Task, Action, Result, Reflection."
    if "pressure" in mode:
        return "Ask realistic follow-up and pressure questions about gaps, missing tools, salary, relocation, language, or career break. Be professional, not rude."
    if "language" in mode or "german" in mode:
        return "Focus on interview communication, simple clear wording, and language confidence."
    return "Focus on HR fit, motivation, experience relevance, and role alignment."


def _workzo_generate_interview_questions(cv_text: str, jd_text: str, mode: str, country: str, language: str):
    fallback = [
        {"question": "Walk me through your background and explain why this role fits your next career step.", "type": "HR", "pressure_point": "Role motivation and career transition", "expected_keywords": ["relevant experience", "motivation", "tools", "impact"], "honesty_check": "Use only experience that is present in your CV."},
        {"question": "Which project or work achievement best proves you can handle the responsibilities in this job description?", "type": "Behavioral/STARR", "pressure_point": "Evidence quality", "expected_keywords": ["situation", "action", "result", "metric"], "honesty_check": "Do not add metrics unless they are true or already in your CV."},
        {"question": "I see some requirements in the job description that may not be strongly visible in your CV. How would you close that gap?", "type": "Pressure point", "pressure_point": "Skill gap honesty", "expected_keywords": ["learning plan", "transferable skills", "practical example"], "honesty_check": "Admit gaps honestly and explain how you would handle them."},
    ]
    if not cv_text.strip() and not jd_text.strip():
        return fallback
    prompt = f"""
You are a JD-specific mock interviewer for WorkZo AI.
Generate 6 interview questions based on the CV and the job description.

Interview mode: {mode}
Target country: {country or 'Not specified'}
Answer language: {language or 'English'}
Mode instruction: {_workzo_interview_mode_instruction(mode)}

STRICT HONESTY RULES:
- Do not invent companies, tools, years, certifications, or achievements.
- If a JD requirement is missing from the CV, ask a pressure-point question about how the candidate would handle the gap.
- Include at least 2 STARR behavioral questions.
- Include at least 1 gap/pressure question.
- Include expected_keywords only when they are required by the JD or clearly present in the CV.

Return ONLY valid JSON in this exact structure:
{{"questions": [{{"question": "", "type": "HR | Technical | Behavioral/STARR | Pressure point | Language practice", "pressure_point": "", "expected_keywords": [], "honesty_check": ""}}]}}

CV:
{cv_text[:8000]}

JOB DESCRIPTION:
{jd_text[:8000]}
"""
    result = run_ai_prompt(prompt, system_addition="Return only valid JSON. No markdown. No commentary.", force_language="English", json_mode=True)
    data = safe_json_loads(result)
    questions = data.get("questions") if isinstance(data, dict) else None
    return questions if isinstance(questions, list) and questions else fallback


def _workzo_evaluate_interview_answer(question_obj: dict, answer: str, cv_text: str, jd_text: str, country: str, language: str):
    fallback = {"overall_score": 60, "confidence_score": 60, "role_alignment_score": 60, "technical_accuracy_score": 60, "communication_score": 60, "honesty_score": 80, "starr": {"situation": False, "task": False, "action": True, "result": False, "reflection": False}, "missing_parts": ["Add a measurable result", "Connect the answer more clearly to the job description"], "honesty_flags": [], "good_points": [], "stronger_answer": "Use a specific example from your CV, explain the action you took, and end with a result or lesson learned.", "next_question_focus": "Practice a result-focused example."}
    if not answer.strip():
        return fallback
    prompt = f"""
You are an honest interview coach.
Evaluate the user's answer against the question, CV, and job description.

Return ONLY valid JSON with this structure:
{{"overall_score": 0, "confidence_score": 0, "role_alignment_score": 0, "technical_accuracy_score": 0, "communication_score": 0, "honesty_score": 0, "starr": {{"situation": false, "task": false, "action": false, "result": false, "reflection": false}}, "missing_parts": [], "honesty_flags": [], "good_points": [], "stronger_answer": "", "next_question_focus": ""}}

STRICT HONESTY RULES:
- If the answer claims a company, tool, number, leadership size, certification, or timeline not found or supported by the CV, add an honesty flag.
- Do not encourage lying. Suggest honest pivots.
- Do not invent metrics. If metric is missing, ask the user to add one only if true.
- Keep the stronger answer realistic and based on the CV.

Target country: {country or 'Not specified'}
Language: {language or 'English'}
QUESTION:
{json.dumps(question_obj, ensure_ascii=False)}
USER ANSWER:
{answer}
CV:
{cv_text[:8000]}
JOB DESCRIPTION:
{jd_text[:8000]}
"""
    result = run_ai_prompt(prompt, system_addition="Return only valid JSON. No markdown. No extra text.", force_language="English", json_mode=True)
    data = safe_json_loads(result)
    if isinstance(data, dict):
        for key in ["overall_score", "confidence_score", "role_alignment_score", "technical_accuracy_score", "communication_score", "honesty_score"]:
            data[key] = clamp_score_value(data.get(key, 0), 0)
        return data
    return fallback


def _workzo_build_interview_cheat_sheet(cv_text: str, jd_text: str, country: str, language: str) -> str:
    prompt = f"""
Create a one-page interview cheat sheet for the user using the CV and job description only.
Include: 3 strongest stories from the CV mapped to the job; a 2-sentence answer to Why this role; 5 pressure-point questions; 3 reverse questions; honesty reminders; and a country-specific interview note for {country or 'the target country'}.
Do not invent facts. If something is missing, say "confirm before using".
CV:
{cv_text[:8000]}
JOB DESCRIPTION:
{jd_text[:8000]}
"""
    return run_ai_prompt(prompt, force_language=language or st.session_state.get("preferred_language", "English"))


def _workzo_generate_flashcards(cv_text: str, jd_text: str, country: str):
    fallback = [
        {"requirement": "Explain your strongest relevant experience", "prompt": "Give a 30-second answer using one CV example.", "hint": "Use Action + Result."},
        {"requirement": "Handle a missing skill honestly", "prompt": "Explain how you would close the gap without pretending you already have it.", "hint": "Show learning plan + transferable skill."},
        {"requirement": "Ask smart questions", "prompt": "Ask one thoughtful question about the team, product, or success metrics.", "hint": "Avoid questions already answered in the JD."},
    ]
    if not cv_text.strip() and not jd_text.strip():
        return fallback
    prompt = f"""
Create 8 interview flashcards from this CV and job description. Each flashcard must help the user practice a job requirement in 30 seconds.
Return ONLY valid JSON: {{"flashcards": [{{"requirement":"", "prompt":"", "hint":""}}]}}
Country: {country or 'Not specified'}
CV:
{cv_text[:6000]}
JOB DESCRIPTION:
{jd_text[:6000]}
"""
    result = run_ai_prompt(prompt, system_addition="Return only valid JSON. No markdown.", force_language="English", json_mode=True)
    data = safe_json_loads(result)
    cards = data.get("flashcards") if isinstance(data, dict) else None
    return cards if isinstance(cards, list) and cards else fallback


def render_interview_scorecard(evaluations: list):
    if not evaluations:
        st.info("Complete at least one answer to see your interview scorecard.")
        return
    def avg(key):
        vals = [clamp_score_value(e.get(key, 0), 0) for e in evaluations if isinstance(e, dict)]
        return int(sum(vals) / len(vals)) if vals else 0
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Overall", f"{avg('overall_score')}/100")
    c2.metric("Confidence", f"{avg('confidence_score')}/100")
    c3.metric("Role fit", f"{avg('role_alignment_score')}/100")
    c4.metric("Communication", f"{avg('communication_score')}/100")
    c5.metric("Honesty", f"{avg('honesty_score')}/100")
    flags, missing = [], []
    for e in evaluations:
        flags.extend(e.get("honesty_flags", []) if isinstance(e.get("honesty_flags"), list) else [])
        missing.extend(e.get("missing_parts", []) if isinstance(e.get("missing_parts"), list) else [])
    if flags:
        st.warning("Honesty flags to review:")
        render_list_items(flags[:8])
    if missing:
        st.markdown("**Most common improvement areas**")
        render_list_items(missing[:8])


def render_jd_specific_mock_interview():
    st.markdown("### JD-Specific Mock Interview")
    st.caption("Practice one question at a time using your CV, the job description, and strict honesty checks.")
    cv_text = _workzo_latest_cv_text()
    default_jd = _workzo_latest_job_description()
    country = st.session_state.get("country", "") or st.session_state.get("migration_country", "")
    language = st.session_state.get("preferred_language", "English")
    with st.expander("Interview setup", expanded=not bool(default_jd)):
        mode = st.selectbox("Interview mode", ["HR interview", "Technical interview", "Behavioral/STARR interview", "Pressure round", "Language practice / German-English"], key="interview_mode_v117")
        jd_text = st.text_area("Job description used for interview practice", value=default_jd, height=180, key="interview_jd_text_v117", help="WorkZo uses the saved JD from Understand Job/Prepare Job when available. You can edit it here.")
        strict_honesty = st.toggle("Strict Honesty Mode — do not invent skills, dates, companies, or metrics", value=True, key="interview_strict_honesty_v117")
        if strict_honesty:
            st.caption("Claims not supported by the CV will be flagged instead of encouraged.")
    gen_col, reset_col = st.columns([3, 1])
    with gen_col:
        if st.button("Generate JD-specific interview questions", key="generate_interview_questions_v117", use_container_width=True):
            with st.status("Building a JD-aware interview simulation...", expanded=True) as status:
                st.write("Reading your CV and job description...")
                st.write("Finding pressure points and skill gaps...")
                questions = _workzo_generate_interview_questions(cv_text, st.session_state.get("interview_jd_text_v117", jd_text), mode, country, language)
                st.session_state["mock_interview_questions_v117"] = questions
                st.session_state["mock_interview_index_v117"] = 0
                st.session_state["mock_interview_answers_v117"] = []
                st.session_state["mock_interview_evals_v117"] = []
                status.update(label="Interview simulation ready", state="complete")
            st.rerun()
    with reset_col:
        if st.button("Reset", key="reset_interview_v117", use_container_width=True):
            for key in ["mock_interview_questions_v117", "mock_interview_index_v117", "mock_interview_answers_v117", "mock_interview_evals_v117"]:
                st.session_state.pop(key, None)
            st.rerun()
    questions = st.session_state.get("mock_interview_questions_v117", [])
    if not questions:
        st.info("Generate questions to start. For best results, paste a job description first.")
        return
    idx = int(st.session_state.get("mock_interview_index_v117", 0))
    idx = max(0, min(idx, len(questions) - 1))
    q = questions[idx] if isinstance(questions[idx], dict) else {"question": str(questions[idx])}
    st.markdown(f"#### Question {idx + 1} of {len(questions)}")
    st.markdown(f"**{q.get('question', '')}**")
    meta_cols = st.columns(3)
    meta_cols[0].caption(f"Type: {q.get('type', 'Interview')}")
    meta_cols[1].caption(f"Pressure point: {q.get('pressure_point', '—')}")
    meta_cols[2].caption(f"Honesty check: {q.get('honesty_check', 'Use CV facts only')}")
    expected = q.get("expected_keywords", [])
    if expected:
        with st.expander("Expected keywords / themes", expanded=False):
            render_list_items(expected)
    answer = st.text_area("Your answer", height=170, key=f"mock_answer_v117_{idx}")
    submit_col, nav_col = st.columns([2, 1])
    with submit_col:
        if st.button("Evaluate my answer", key=f"eval_answer_v117_{idx}", use_container_width=True):
            with st.spinner("Checking STARR, confidence, role alignment, and honesty..."):
                evaluation = _workzo_evaluate_interview_answer(q, answer, cv_text, st.session_state.get("interview_jd_text_v117", jd_text), country, language)
                evals = st.session_state.get("mock_interview_evals_v117", [])
                answers = st.session_state.get("mock_interview_answers_v117", [])
                while len(evals) <= idx:
                    evals.append({})
                while len(answers) <= idx:
                    answers.append("")
                evals[idx] = evaluation
                answers[idx] = answer
                st.session_state["mock_interview_evals_v117"] = evals
                st.session_state["mock_interview_answers_v117"] = answers
            st.rerun()
    with nav_col:
        if st.button("Next question ->", key=f"next_question_v117_{idx}", use_container_width=True):
            st.session_state["mock_interview_index_v117"] = min(idx + 1, len(questions) - 1)
            st.rerun()
    evals = st.session_state.get("mock_interview_evals_v117", [])
    current_eval = evals[idx] if idx < len(evals) and isinstance(evals[idx], dict) else None
    if current_eval:
        st.markdown("### Feedback")
        score = clamp_score_value(current_eval.get("overall_score", 0), 0)
        confidence = clamp_score_value(current_eval.get("confidence_score", 0), 0)
        f1, f2, f3 = st.columns(3)
        f1.metric("Answer score", f"{score}/100", _workzo_score_label(score))
        f2.metric("Confidence", f"{confidence}/100", _workzo_score_label(confidence))
        f3.metric("Honesty", f"{clamp_score_value(current_eval.get('honesty_score', 0), 0)}/100")
        starr = current_eval.get("starr", {}) if isinstance(current_eval.get("starr"), dict) else {}
        st.markdown("**STARR check**")
        st.markdown(" ".join([f"{'OK' if starr.get(k) else 'Missing'} {k.title()}" for k in ["situation", "task", "action", "result", "reflection"]]))
        col_good, col_fix = st.columns(2)
        with col_good:
            st.markdown("**What worked**")
            render_list_items(current_eval.get("good_points", []), "Add more concrete evidence.")
        with col_fix:
            st.markdown("**What to improve**")
            render_list_items(current_eval.get("missing_parts", []), "No major missing parts found.")
        flags = current_eval.get("honesty_flags", [])
        if flags:
            st.warning("Honesty flags")
            render_list_items(flags)
        with st.expander("Stronger answer suggestion", expanded=True):
            st.write(current_eval.get("stronger_answer", ""))
    with st.expander("Session scorecard", expanded=False):
        render_interview_scorecard(st.session_state.get("mock_interview_evals_v117", []))


def render_interview_flashcards():
    st.markdown("### 30-Second Flashcards")
    st.caption("Practice explaining each JD requirement quickly and honestly.")
    cv_text = _workzo_latest_cv_text()
    jd_text = st.session_state.get("interview_jd_text_v117", "") or _workzo_latest_job_description()
    country = st.session_state.get("country", "") or st.session_state.get("migration_country", "")
    if st.button("Generate flashcards from CV + JD", key="generate_flashcards_v117", use_container_width=True):
        with st.spinner("Creating role-specific flashcards..."):
            st.session_state["interview_flashcards_v117"] = _workzo_generate_flashcards(cv_text, jd_text, country)
            st.session_state["interview_flashcard_index_v117"] = 0
        st.rerun()
    cards = st.session_state.get("interview_flashcards_v117", [])
    if not cards:
        st.info("Generate flashcards after adding a job description.")
        return
    idx = int(st.session_state.get("interview_flashcard_index_v117", 0))
    idx = max(0, min(idx, len(cards) - 1))
    card = cards[idx]
    st.markdown(f"#### Card {idx + 1} of {len(cards)}")
    st.markdown(f"<div class='next-action-card'><div class='next-action-label'>Requirement</div><div class='next-action-title'>{html.escape(str(card.get('requirement','Practice prompt')))}</div><div class='next-action-copy'>{html.escape(str(card.get('prompt','Explain this in 30 seconds.')))}</div></div>", unsafe_allow_html=True)
    with st.expander("Hint", expanded=False):
        st.write(card.get("hint", "Use a specific CV example and end with a result."))
    c1, c2 = st.columns(2)
    if c1.button("Previous", key="flash_prev_v117", use_container_width=True):
        st.session_state["interview_flashcard_index_v117"] = max(0, idx - 1)
        st.rerun()
    if c2.button("Next", key="flash_next_v117", use_container_width=True):
        st.session_state["interview_flashcard_index_v117"] = min(len(cards) - 1, idx + 1)
        st.rerun()


def render_interview_cheat_sheet():
    st.markdown("### Interview Cheat Sheet")
    st.caption("A one-page guide for remote interview preparation: stories, fit, reverse questions, and honesty reminders.")
    cv_text = _workzo_latest_cv_text()
    jd_text = st.session_state.get("interview_jd_text_v117", "") or _workzo_latest_job_description()
    country = st.session_state.get("country", "") or st.session_state.get("migration_country", "")
    language = st.session_state.get("preferred_language", "English")
    if st.button("Generate 1-page cheat sheet", key="generate_cheat_sheet_v117", use_container_width=True):
        with st.spinner("Creating your interview cheat sheet..."):
            st.session_state["interview_cheat_sheet_v117"] = _workzo_build_interview_cheat_sheet(cv_text, jd_text, country, language)
        st.rerun()
    sheet = st.session_state.get("interview_cheat_sheet_v117", "")
    if sheet:
        st.markdown(sheet)
        pdf_bytes = make_minimal_pdf_from_text("WorkZo Interview Cheat Sheet", sheet)
        st.download_button("Download cheat sheet PDF", data=pdf_bytes, file_name="workzo_interview_cheat_sheet.pdf", mime="application/pdf", key="download_interview_cheat_sheet_v117", use_container_width=True)
    else:
        st.info("Generate a cheat sheet after adding your CV and job description.")


def render_voice_webcam_future_panel():
    st.markdown("### Voice & Live Simulation")
    st.info("Voice and webcam practice are planned as an advanced stage. The current MVP keeps interview practice typed so it remains stable on Streamlit Cloud.")
    st.markdown("""
**Future upgrade path**
- Voice question playback and recorded user answers.
- Transcript with filler-word detection.
- Webcam preview with `streamlit-webrtc` for body-language self-check.
- Live mock interviewer persona.
""")


def show_workobot():
    """Unified career assistant page with chat + advanced interview simulator."""
    st.subheader(txt("workobot"))
    st.caption("Your AI career assistant for doubts, JD-specific mock interviews, STARR practice, and interview cheat sheets.")
    chat_tab, mock_tab, flash_tab, cheat_tab, live_tab = st.tabs(["Career Chat", "Mock Interview", "Flashcards", "Cheat Sheet", "Voice / Live"])
    with chat_tab:
        st.caption("Ask any career question. Work-O-Bot uses your CV, country, target market, and latest job analysis when available.")
        if "workobot_messages" not in st.session_state or not st.session_state.workobot_messages:
            st.session_state.workobot_messages = [{"role": "assistant", "content": workobot_intro_message()}]
        top_left, top_right = st.columns([5, 1])
        with top_left:
            st.markdown("### Try asking:")
        with top_right:
            if st.button("Clear Chat", key="workobot_clear_chat_v117", use_container_width=True):
                st.session_state.workobot_messages = [{"role": "assistant", "content": workobot_intro_message()}]
                st.rerun()
        quick_prompts = get_country_specific_quick_prompts(st.session_state.get("country", ""))
        qp_cols = st.columns(4)
        quick_prompt = None
        for i, col in enumerate(qp_cols):
            label, prompt = quick_prompts[i]
            with col:
                if st.button(label, use_container_width=True, key=f"workobot_quick_v117_{i}_{st.session_state.get('country','global')}"):
                    quick_prompt = prompt
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
    with mock_tab:
        render_jd_specific_mock_interview()
    with flash_tab:
        render_interview_flashcards()
    with cheat_tab:
        render_interview_cheat_sheet()
    with live_tab:
        render_voice_webcam_future_panel()
    st.markdown("---")
    st.caption("Interview coaching follows Strict Honesty Mode: WorkZo helps you frame the truth better, not invent experience.")



# =========================================================
# WorkZo v135: anti-drift PDF grid + strict job-location bouncer
# =========================================================
