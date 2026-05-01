
# WorkZo AI - Real Interview Simulation
# v65 Streamlit-safe pseudo-live interview
#
# What this version does:
# - One main button: Start Interview
# - AI interviewer speaks the question automatically where browser allows it, with replay fallback
# - User records answer with st.audio_input
# - Whisper transcription starts automatically after recording
# - Transcript is displayed in a dialogue box and cannot be edited
# - Interviewer waits briefly, reacts, then moves to the next question
# - User can end interview anytime
# - Final review, suggestions, scores, coaching loop, TXT/PDF report
#
# Note: True continuous hands-free voice streaming needs a frontend/WebRTC layer.
# This is the safest Product Hunt-ready Streamlit pseudo-live version.

import os
import re
import json
import time
import html
import tempfile
from io import BytesIO

try:
    import streamlit as st
except Exception:
    st = None


# -----------------------------
# Basic helpers
# -----------------------------
def _wz_ri_get_cv_text() -> str:
    for key in [
        "workzo_live_cv_text",
        "clean_structured_cv_text",
        "approved_structured_cv_text",
        "improved_cv_text_v92",
        "cv_text",
        "created_cv_text",
    ]:
        value = st.session_state.get(key, "")
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _wz_ri_get_jd_text() -> str:
    for key in [
        "real_interview_jd_saved",
        "last_understand_job_description",
        "last_prepare_job_description",
        "job_desc_prepare_v928",
        "job_desc_v42",
        "improve_cv_for_job_desc",
        "doc_tools_job_desc",
    ]:
        value = st.session_state.get(key, "")
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _wz_ri_get_openai_client():
    try:
        existing = globals().get("client")
        if existing is not None:
            return existing
    except Exception:
        pass

    try:
        from openai import OpenAI
        api_key = ""
        try:
            api_key = st.secrets.get("OPENAI_API_KEY", "")
        except Exception:
            api_key = ""
        api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            return None
        return OpenAI(api_key=api_key)
    except Exception:
        return None


def _wz_ri_ai(prompt: str, json_mode: bool = False, language: str = "English") -> str:
    """Uses WorkZo's existing run_ai_prompt when available, otherwise OpenAI Responses API."""
    try:
        fn = globals().get("run_ai_prompt")
        if callable(fn):
            try:
                return str(fn(
                    prompt,
                    system_addition="Return only valid JSON. No markdown." if json_mode else "",
                    force_language=language or st.session_state.get("preferred_language", "English"),
                    json_mode=json_mode,
                ) or "").strip()
            except TypeError:
                return str(fn(prompt) or "").strip()
    except Exception:
        pass

    wz_client = _wz_ri_get_openai_client()
    if wz_client is None:
        return ""

    try:
        kwargs = {
            "model": "gpt-4o-mini",
            "input": prompt,
        }
        if json_mode:
            kwargs["text"] = {"format": {"type": "json_object"}}
        resp = wz_client.responses.create(**kwargs)
        return str(getattr(resp, "output_text", "") or "").strip()
    except Exception as exc:
        try:
            st.error(f"AI request failed: {exc}")
        except Exception:
            pass
        return ""


def _wz_ri_json(raw, fallback=None):
    fallback = fallback if fallback is not None else {}
    try:
        if isinstance(raw, dict):
            return raw
        text = str(raw or "").strip()
        if text.startswith("```"):
            text = text.strip("`")
            text = text.replace("json\n", "", 1).strip()
        return json.loads(text)
    except Exception:
        return fallback


def _wz_ri_audio_bytes(audio_file):
    if audio_file is None:
        return b""
    try:
        return audio_file.getvalue() if hasattr(audio_file, "getvalue") else audio_file.read()
    except Exception:
        return b""


def _wz_ri_transcribe(audio_file) -> str:
    """Transcribe recorded audio using OpenAI Whisper."""
    if audio_file is None:
        return ""

    raw = _wz_ri_audio_bytes(audio_file)
    if not raw:
        st.warning("No audio data was captured. Please record again.")
        return ""

    wz_client = _wz_ri_get_openai_client()
    if wz_client is None:
        st.warning("OPENAI_API_KEY is not available. Please check Streamlit Secrets or environment variables.")
        return ""

    tmp_path = None
    try:
        name = getattr(audio_file, "name", "") or "answer.wav"
        suffix = ".wav"
        if "." in name:
            suffix = "." + name.rsplit(".", 1)[-1].lower()
        if suffix not in [".wav", ".mp3", ".m4a", ".webm", ".mp4", ".mpeg", ".mpga", ".oga", ".ogg"]:
            suffix = ".wav"

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(raw)
            tmp_path = tmp.name

        with open(tmp_path, "rb") as f:
            transcript = wz_client.audio.transcriptions.create(model="whisper-1", file=f)

        return str(getattr(transcript, "text", "") or "").strip()
    except Exception as exc:
        st.error(f"Transcription failed: {exc}")
        return ""
    finally:
        if tmp_path:
            try:
                os.remove(tmp_path)
            except Exception:
                pass


def _wz_ri_company_context(company: str, website: str) -> str:
    company = str(company or "").strip()
    website = str(website or "").strip()
    if not company and not website:
        return ""

    cache_key = f"wz_ri_company_context::{company}::{website}"
    if cache_key in st.session_state:
        return st.session_state.get(cache_key, "")

    context = ""
    if website:
        try:
            import requests
            url = website if website.startswith(("http://", "https://")) else "https://" + website
            r = requests.get(url, timeout=3, headers={"User-Agent": "WorkZoAI/1.0"})
            if r.ok:
                txt = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", " ", r.text, flags=re.I)
                txt = re.sub(r"<[^>]+>", " ", txt)
                txt = re.sub(r"\s+", " ", txt).strip()
                context = txt[:1800]
        except Exception:
            context = ""

    if not context and company:
        context = f"Company name provided by user: {company}. Do not invent company facts; use JD and CV unless context is available."

    st.session_state[cache_key] = context
    if context:
        st.session_state["company_context"] = context
    return context


def _wz_ri_extract_focus_areas(cv_text: str, jd: str, role: str, language: str):
    prompt = f"""
Extract 3 to 5 interview focus areas from this CV and job description.

Role:
{role or "Not specified"}

CV:
{cv_text[:5000]}

Job Description:
{jd[:5000]}

Return ONLY valid JSON:
{{"focus_areas": ["area 1", "area 2", "area 3"]}}

Rules:
- Use job requirements and CV overlap.
- Keep each area short.
- Language: {language}
"""
    raw = _wz_ri_ai(prompt, json_mode=True, language=language)
    data = _wz_ri_json(raw, {})
    areas = data.get("focus_areas") if isinstance(data, dict) else None
    if isinstance(areas, list) and areas:
        return [str(x).strip() for x in areas if str(x).strip()][:5]

    text = f"{cv_text} {jd}".lower()
    fallback = []
    for kw in ["sql", "python", "excel", "tableau", "power bi", "communication", "stakeholder communication", "problem solving", "customer support", "data analysis", "reporting", "apis"]:
        if kw in text and kw.title() not in fallback:
            fallback.append(kw.title())
    return fallback[:5] or ["Role fit", "Problem solving", "Communication"]


def _wz_ri_build_questions(cv_text: str, jd: str, company: str, role: str, website: str, company_context: str, language: str, personality: str):
    intro_question = "Let’s begin. Tell me about yourself."

    prompt = f"""
You are a realistic {personality.lower()} senior hiring manager.

Create exactly 3 additional questions after the cold-open introduction.

Candidate CV:
{cv_text[:7000]}

Job Description:
{jd[:7000]}

Company:
{company or "Not specified"}

Target role:
{role or "Not specified"}

Company website:
{website or "Not specified"}

Company context:
{company_context or "No reliable company context available."}

Rules:
- Question 2: role-specific or technical screening based on CV + JD.
- Question 3: memory/pressure question that can reference CV gaps or missing details.
- Question 4: curveball question.
- Use company context only if reliable.
- Keep tone slightly challenging but not rude.
- Match interviewer personality: {personality}
- Language: {language}

Return ONLY valid JSON:
{{"questions": ["question 2", "question 3", "curveball question"]}}
"""
    raw = _wz_ri_ai(prompt, json_mode=True, language=language)
    data = _wz_ri_json(raw, {})
    extra = data.get("questions") if isinstance(data, dict) else None

    if not isinstance(extra, list) or len(extra) < 3:
        extra = [
            "Which experience from your CV best proves you can handle the key responsibilities in this role?",
            "Earlier in your CV, you mention technical or support work. How does that translate into this role?",
            "Why should we choose you over other candidates?",
        ]

    return [intro_question] + [str(q).strip() for q in extra[:3] if str(q).strip()]


def _wz_ri_answer_quality_flags(answer: str, jd: str) -> dict:
    words = len(str(answer or "").split())
    lower = str(answer or "").lower()
    jd_lower = str(jd or "").lower()

    has_impact = any(x in lower for x in ["result", "impact", "improved", "reduced", "increased", "%", "saved", "measured", "outcome"])
    jd_tools = [tool for tool in ["sql", "python", "excel", "tableau", "power bi", "api", "dashboard"] if tool in jd_lower]
    missed_tools = [tool for tool in jd_tools if tool not in lower]
    vague = words < 35 or not any(x in lower for x in ["example", "project", "worked", "built", "created", "handled", "solved", "analyzed"])
    too_long = words > 130
    off_topic = words > 25 and len(set(lower.split()).intersection(set(jd_lower.split()))) < 4 if jd_lower else False

    return {
        "words": words,
        "has_impact": has_impact,
        "missed_tools": missed_tools,
        "vague": vague,
        "too_long": too_long,
        "off_topic": off_topic,
    }


def _wz_ri_react_to_answer(question: str, answer: str, cv_text: str, jd: str, qa_pairs: list, language: str, personality: str):
    flags = _wz_ri_answer_quality_flags(answer, jd)

    if flags["too_long"]:
        return {
            "reaction": "I'll stop you there.",
            "needs_followup": True,
            "followup_question": "Let's move on. Give me the same answer again, but in one specific example with the result.",
            "interruption_reason": "too long",
        }

    prompt = f"""
You are a realistic {personality.lower()} interviewer.

React briefly to the user's latest answer and decide whether the next question should become a follow-up.

Current question:
{question}

User answer:
{answer}

Previous answers:
{json.dumps(qa_pairs, ensure_ascii=False)}

Detected quality flags:
{json.dumps(flags, ensure_ascii=False)}

CV:
{cv_text[:5000]}

Job Description:
{jd[:5000]}

Return ONLY valid JSON:
{{
  "reaction": "brief human reaction, e.g. Hmm... / That's quite general / Good, that's clearer",
  "needs_followup": true,
  "followup_question": "specific follow-up question if needed",
  "interruption_reason": "too vague|too long|missing impact|missing tools|off-topic|none"
}}

Rules:
- If vague: "That's quite general—can you give a specific example?"
- If no impact: "What was the result of that?"
- If off-topic: "Let's stay focused on the question."
- If missing tools: ask what tools/methods were used.
- Use layered follow-up style: ask how, then tools, then measurable impact.
- Use memory if previous answers mention a relevant skill.
- Match interviewer personality: {personality}
- Keep it firm, not rude.
- Language: {language}
"""
    raw = _wz_ri_ai(prompt, json_mode=True, language=language)
    data = _wz_ri_json(raw, {})
    if not isinstance(data, dict) or not data:
        if flags["vague"]:
            return {
                "reaction": "That's quite general.",
                "needs_followup": True,
                "followup_question": "Can you give a specific example?",
                "interruption_reason": "too vague",
            }
        if not flags["has_impact"]:
            return {
                "reaction": "Hmm...",
                "needs_followup": True,
                "followup_question": "What was the result of that, and how did you measure success?",
                "interruption_reason": "missing impact",
            }
        if flags["missed_tools"]:
            return {
                "reaction": "Okay.",
                "needs_followup": True,
                "followup_question": f"Which tools did you use? I expected to hear about {', '.join(flags['missed_tools'][:3])}.",
                "interruption_reason": "missing tools",
            }
        return {
            "reaction": "Good, that gives me some context.",
            "needs_followup": False,
            "followup_question": "",
            "interruption_reason": "none",
        }
    data.setdefault("reaction", "Hmm...")
    data.setdefault("needs_followup", False)
    data.setdefault("followup_question", "")
    data.setdefault("interruption_reason", "none")
    return data


def _wz_ri_score_full_interview(cv_text: str, jd: str, company: str, role: str, qa_pairs: list, reactions: list, language: str) -> dict:
    prompt = f"""
You are a senior hiring manager and interview coach.

Reconstruct the interview experience and score it.

Candidate CV:
{cv_text[:6500]}

Job Description:
{jd[:6500]}

Company: {company or "Not specified"}
Role: {role or "Not specified"}

Interview answers:
{json.dumps(qa_pairs, ensure_ascii=False)}

Live interviewer reactions:
{json.dumps(reactions, ensure_ascii=False)}

Return ONLY valid JSON:
{{
  "overall_score": 0,
  "target_score": 80,
  "scores": {{
    "relevance": 0,
    "depth": 0,
    "structure": 0,
    "confidence": 0,
    "keyword_match": 0,
    "honesty": 0
  }},
  "what_hurt_you_most": [],
  "missed_opportunities": [],
  "interviewer_impression": "",
  "what_was_good": [],
  "missing_keywords": [],
  "weakest_answer_question_number": 1,
  "improved_version_of_weakest_answer": "",
  "retry_instruction": "",
  "final_readiness_message": ""
}}

Rules:
- Reconstruct the experience, don't just evaluate.
- what_hurt_you_most: explain the biggest interview problem.
- missed_opportunities: mention missed skills/keywords if relevant.
- interviewer_impression: say how the user came across.
- Scores are 0-10 except overall_score 0-100.
- If answers lack STAR structure, say that.
- If answers lack measurable impact, say that.
- Do not invent achievements.
- weakest_answer_question_number must be 1, 2, 3, or 4.
- Keep feedback in {language}.
"""
    raw = _wz_ri_ai(prompt, json_mode=True, language=language)
    data = _wz_ri_json(raw, {})

    if not isinstance(data, dict) or not data:
        data = {
            "overall_score": 58,
            "target_score": 80,
            "scores": {
                "relevance": 6,
                "depth": 4,
                "structure": 5,
                "confidence": 6,
                "keyword_match": 5,
                "honesty": 8,
            },
            "what_hurt_you_most": ["You gave high-level answers without enough specific examples."],
            "missed_opportunities": ["You did not clearly connect your experience to the most important job requirements."],
            "interviewer_impression": "You came across as knowledgeable, but not yet specific or impactful enough.",
            "what_was_good": ["You communicated your background in a clear way."],
            "missing_keywords": [],
            "weakest_answer_question_number": 1,
            "improved_version_of_weakest_answer": "Use STAR: situation, task, action, result. Add one truthful result or measurable impact.",
            "retry_instruction": "Retry your weakest answer with one specific example and a clear result.",
            "final_readiness_message": "Needs improvement. Try to reach 80+ before the real interview.",
        }

    scores = data.get("scores", {})
    if not isinstance(scores, dict):
        scores = {}

    clean_scores = {}
    for key in ["relevance", "depth", "structure", "confidence", "keyword_match", "honesty"]:
        try:
            val = int(float(scores.get(key, 0)))
            if val > 10:
                val = round(val / 10)
            clean_scores[key] = max(0, min(10, val))
        except Exception:
            clean_scores[key] = 0

    data["scores"] = clean_scores
    try:
        data["overall_score"] = max(0, min(100, int(float(data.get("overall_score", 0)))))
    except Exception:
        vals = list(clean_scores.values())
        data["overall_score"] = int(sum(vals) / len(vals) * 10) if vals else 58

    for key in ["what_hurt_you_most", "missed_opportunities", "what_was_good", "missing_keywords"]:
        if not isinstance(data.get(key), list):
            data[key] = []

    try:
        data["weakest_answer_question_number"] = max(1, min(4, int(data.get("weakest_answer_question_number", 1))))
    except Exception:
        data["weakest_answer_question_number"] = 1

    data.setdefault("target_score", 80)
    data.setdefault("interviewer_impression", "You came across as generally prepared, but could be more specific.")
    data.setdefault("improved_version_of_weakest_answer", "Use STAR structure and add a truthful result.")
    data.setdefault("retry_instruction", "Retry the weakest answer with more structure.")
    data.setdefault("final_readiness_message", "Interview completed.")
    return data


def _wz_ri_make_pdf_report(report_text: str):
    try:
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20 * mm, leftMargin=20 * mm, topMargin=18 * mm, bottomMargin=18 * mm)
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle("WorkZoTitle", parent=styles["Heading1"], fontSize=16, leading=20, spaceAfter=12)
        body_style = ParagraphStyle("WorkZoBody", parent=styles["BodyText"], fontSize=9.5, leading=13, spaceAfter=7)
        story = [Paragraph("WorkZo Pseudo-Live Interview Simulation Report", title_style), Spacer(1, 6)]
        for para in str(report_text or "").split("\n"):
            if para.strip():
                story.append(Paragraph(html.escape(para), body_style))
            else:
                story.append(Spacer(1, 5))
        doc.build(story)
        return buffer.getvalue()
    except Exception:
        return None


def _wz_ri_reset_answer_box():
    st.session_state["wz_ri_transcript"] = ""
    st.session_state["wz_ri_answer_saved"] = ""
    st.session_state["wz_ri_audio_nonce"] = int(st.session_state.get("wz_ri_audio_nonce", 0) or 0) + 1


def _wz_ri_apply_css():
    # Important: no global red button styling here. This keeps toolbox buttons as before.
    st.markdown(
        """
        <style>
        .wz-interview-card {
            border: 1px solid rgba(148,163,184,.28);
            border-radius: 18px;
            padding: 18px;
            background: rgba(15,23,42,.42);
            margin: 12px 0;
        }
        .wz-interview-label {
            color: #93c5fd;
            font-size: .82rem;
            font-weight: 850;
            text-transform: uppercase;
            letter-spacing: .08em;
            margin-bottom: 8px;
        }
        .wz-interview-title {
            color: #f8fafc;
            font-size: 1.15rem;
            font-weight: 900;
            line-height: 1.35;
        }
        .wz-dialogue {
            border-left: 3px solid rgba(59,130,246,.75);
            background: rgba(15,23,42,.36);
            padding: 12px 14px;
            border-radius: 12px;
            margin: 10px 0;
        }
        .wz-pressure-note {
            color:#fca5a5;
            font-weight:700;
            font-size:.92rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _wz_ri_auto_speak(text: str, key_suffix: str = "question"):
    """Try to speak automatically after Start Interview. Browser may block autoplay, so a replay button is provided."""
    safe_text = json.dumps(str(text or ""))
    safe_key = re.sub(r"[^a-zA-Z0-9_]+", "_", str(key_suffix))
    html_code = f"""
    <!doctype html>
    <html>
    <body style="margin:0; background:transparent;">
      <button id="wz_ri_speak_{safe_key}" style="
          border:1px solid rgba(148,163,184,.45);
          border-radius:12px;
          padding:9px 14px;
          background:#0f172a;
          color:white;
          cursor:pointer;
          font-weight:800;
          font-family:system-ui,-apple-system,Segoe UI,sans-serif;
          font-size:14px;
      ">🔊 Replay interviewer voice</button>
      <script>
      function speak_{safe_key}() {{
          const msg = new SpeechSynthesisUtterance({safe_text});
          msg.rate = 0.93;
          msg.pitch = 1.0;
          window.speechSynthesis.cancel();
          window.speechSynthesis.speak(msg);
      }}
      const btn = document.getElementById("wz_ri_speak_{safe_key}");
      btn.onclick = speak_{safe_key};
      setTimeout(function() {{
          try {{ speak_{safe_key}(); }} catch(e) {{}}
      }}, 650);
      </script>
    </body>
    </html>
    """
    try:
        import streamlit.components.v1 as components
        components.html(html_code, height=48)
    except Exception:
        st.caption("Voice playback is unavailable in this browser. You can still read the question.")


def _wz_ri_render_dialogue():
    answers = st.session_state.get("wz_ri_answers", [])
    reactions = st.session_state.get("wz_ri_live_reactions", [])
    if not answers:
        return
    with st.expander("Interview dialogue transcript", expanded=True):
        for i, item in enumerate(answers):
            q = item.get("question", "")
            a = item.get("answer", "")
            st.markdown(
                f"""
                <div class="wz-dialogue">
                    <strong>Interviewer:</strong> {html.escape(str(q))}<br><br>
                    <strong>You:</strong> {html.escape(str(a))}
                </div>
                """,
                unsafe_allow_html=True,
            )
            if i < len(reactions) and isinstance(reactions[i], dict) and reactions[i].get("reaction"):
                st.caption("Interviewer reaction: " + str(reactions[i].get("reaction")))


# -----------------------------
# Main feature
# -----------------------------
def render_real_interview_simulation():
    _wz_ri_apply_css()

    st.markdown("## 🎤 Pseudo-Live Real Interview Simulation")
    st.caption("Click Start Interview once. The interviewer asks, you answer by voice, WorkZo transcribes and continues.")

    st.warning(
        "Testing phase disclaimer: this interview practice is still a beta version. "
        "It may not behave perfectly yet. A more advanced real-time interview experience is coming soon."
    )

    defaults = {
        "wz_ri_questions": [],
        "wz_ri_current_index": 0,
        "wz_ri_answers": [],
        "wz_ri_transcript": "",
        "wz_ri_answer_saved": "",
        "wz_ri_audio_nonce": 0,
        "wz_ri_final_score": {},
        "wz_ri_started": False,
        "wz_ri_focus_areas": [],
        "wz_ri_live_reactions": [],
        "wz_ri_closing_reached": False,
        "wz_ri_last_processed_audio_key": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    cv_text = _wz_ri_get_cv_text()
    default_jd = _wz_ri_get_jd_text()

    language_options = ["English", "German", "Dutch", "French", "Spanish", "Hindi", "Tamil"]
    current_lang = st.session_state.get("preferred_language", "English")
    if current_lang not in language_options:
        current_lang = "English"

    with st.container(border=True):
        st.markdown("### 🧾 Interview Brief")

        interview_language = st.selectbox(
            "Interview language",
            language_options,
            index=language_options.index(current_lang),
            key="wz_ri_interview_language",
            disabled=bool(st.session_state.get("wz_ri_started")),
        )

        personality = st.selectbox(
            "Interviewer mode",
            ["Strict", "Fast-paced", "Friendly"],
            index=0,
            key="wz_ri_personality",
            disabled=bool(st.session_state.get("wz_ri_started")),
        )

        round_type = st.selectbox(
            "Interview round",
            ["Technical Screening", "Hiring Manager Round", "Behavioral Round", "Final Round"],
            index=0,
            key="wz_ri_round_type",
            disabled=bool(st.session_state.get("wz_ri_started")),
        )

        c1, c2 = st.columns(2)
        with c1:
            company = st.text_input(
                "Target company",
                value="",
                placeholder="Example: Siemens, HubSpot, Hubdrive",
                key="wz_ri_company",
                disabled=bool(st.session_state.get("wz_ri_started")),
            )
        with c2:
            role = st.text_input(
                "Target role",
                value="",
                placeholder="Example: Data Analyst, IT Support Analyst",
                key="wz_ri_role",
                disabled=bool(st.session_state.get("wz_ri_started")),
            )

        website = st.text_input(
            "Company website / careers page (optional)",
            value="",
            placeholder="https://company.com/careers",
            key="wz_ri_company_website",
            disabled=bool(st.session_state.get("wz_ri_started")),
        )

        jd = st.text_area(
            "Paste job description",
            value=default_jd,
            height=180,
            key="wz_ri_jd",
            disabled=bool(st.session_state.get("wz_ri_started")),
        )

        # Sync details to the rest of WorkZo
        st.session_state["target_company"] = company
        st.session_state["target_role"] = role
        st.session_state["target_job_title"] = role
        st.session_state["target_company_website"] = website
        st.session_state["last_understand_job_description"] = jd
        st.session_state["last_prepare_job_description"] = jd
        st.session_state["improve_cv_for_job_desc"] = jd
        st.session_state["doc_tools_job_desc"] = jd
        st.session_state["real_interview_jd_saved"] = jd

        if not cv_text:
            st.warning("Please upload or create your CV first. The simulation needs your CV to feel realistic.")
        elif not st.session_state.get("wz_ri_started"):
            if st.button("Prepare Interview Brief", key="wz_ri_prepare_brief", use_container_width=True):
                with st.spinner("Preparing interview brief..."):
                    st.session_state["wz_ri_focus_areas"] = _wz_ri_extract_focus_areas(cv_text, jd, role, interview_language)
                st.rerun()

            focus_areas = st.session_state.get("wz_ri_focus_areas", [])
            if focus_areas:
                st.markdown(f"**Role:** {role or 'Not specified'}")
                st.markdown(f"**Company:** {company or 'Optional / not specified'}")
                st.markdown(f"**Round:** {round_type}")
                st.markdown("**Interviewer:** Senior Hiring Manager")
                st.markdown("**Duration:** ~10 mins")
                st.markdown("**Focus areas:** " + " · ".join([str(x) for x in focus_areas]))
                st.markdown("<div class='wz-pressure-note'>This interview will assess your role fit and communication clarity.</div>", unsafe_allow_html=True)

    if not cv_text:
        return

    if not st.session_state.get("wz_ri_started"):
        if st.button("Start Interview", key="wz_ri_start_interview", use_container_width=True):
            with st.spinner("Preparing interview room..."):
                time.sleep(2.0)
            company_context = _wz_ri_company_context(company, website)
            with st.spinner("Senior Hiring Manager has joined..."):
                time.sleep(1.2)
                questions = _wz_ri_build_questions(
                    cv_text=cv_text,
                    jd=jd,
                    company=company,
                    role=role,
                    website=website,
                    company_context=company_context,
                    language=interview_language,
                    personality=personality,
                )
            st.session_state["wz_ri_questions"] = questions[:4]
            st.session_state["wz_ri_current_index"] = 0
            st.session_state["wz_ri_answers"] = []
            st.session_state["wz_ri_live_reactions"] = []
            st.session_state["wz_ri_final_score"] = {}
            st.session_state["wz_ri_started"] = True
            st.session_state["wz_ri_closing_reached"] = False
            _wz_ri_reset_answer_box()
            st.rerun()
        return

    end_col, reset_col = st.columns([3, 1])
    with end_col:
        if st.button("End Interview Now", key="wz_ri_end_now", use_container_width=True):
            st.session_state["wz_ri_closing_reached"] = True
            st.rerun()
    with reset_col:
        if st.button("Reset", key="wz_ri_reset", use_container_width=True):
            for key in [
                "wz_ri_questions",
                "wz_ri_current_index",
                "wz_ri_answers",
                "wz_ri_transcript",
                "wz_ri_answer_saved",
                "wz_ri_audio_nonce",
                "wz_ri_final_score",
                "wz_ri_started",
                "wz_ri_focus_areas",
                "wz_ri_live_reactions",
                "wz_ri_closing_reached",
                "wz_ri_last_processed_audio_key",
            ]:
                st.session_state.pop(key, None)
            st.rerun()

    _wz_ri_render_dialogue()

    questions = st.session_state.get("wz_ri_questions", [])
    if not questions:
        st.info("Start the interview to begin.")
        return

    final_score = st.session_state.get("wz_ri_final_score", {})
    if isinstance(final_score, dict) and final_score:
        _wz_ri_render_final_score(final_score, company, role, website, interview_language)
        return

    if st.session_state.get("wz_ri_closing_reached"):
        _wz_ri_finish_and_score(cv_text, jd, company, role, website, interview_language)
        return

    idx = int(st.session_state.get("wz_ri_current_index", 0) or 0)
    idx = max(0, min(idx, len(questions) - 1))
    question = questions[idx]

    st.markdown("### 👤 Interviewer")
    if idx == 0:
        st.info("Let’s begin.")

    st.markdown(f"### Question {idx + 1}")
    st.progress((idx + 1) / len(questions))
    st.markdown(
        f"""
        <div class="wz-interview-card">
            <div class="wz-interview-label">{html.escape(personality)} · {html.escape(round_type)}</div>
            <div class="wz-interview-title">{html.escape(str(question))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    _wz_ri_auto_speak(question, f"q_{idx}_{st.session_state.get('wz_ri_audio_nonce', 0)}")

    st.markdown("### Your answer")
    st.caption("Speak your answer. WorkZo will transcribe it automatically and move the interview forward.")
    st.progress(0.72)
    st.caption("⏱ Pseudo-live pressure: aim for 60–90 seconds. Keep it concise and structured.")

    audio_key = f"wz_ri_audio_{idx}_{st.session_state.get('wz_ri_audio_nonce', 0)}"
    audio_file = st.audio_input("🎙 Record your answer", key=audio_key) if hasattr(st, "audio_input") else None

    if audio_file is not None:
        raw_audio = _wz_ri_audio_bytes(audio_file)
        st.markdown("#### Playback")
        st.audio(raw_audio)

        unique_audio_key = f"{audio_key}_{len(raw_audio)}"
        if st.session_state.get("wz_ri_last_processed_audio_key") != unique_audio_key:
            st.session_state["wz_ri_last_processed_audio_key"] = unique_audio_key

            with st.spinner("Transcribing your answer..."):
                transcript = _wz_ri_transcribe(audio_file)

            if transcript:
                st.session_state["wz_ri_transcript"] = transcript
                st.session_state["wz_ri_answer_saved"] = transcript

                st.markdown("#### Transcript")
                st.markdown(
                    f"""
                    <div class="wz-dialogue">
                        <strong>You:</strong> {html.escape(transcript)}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                answers = list(st.session_state.get("wz_ri_answers", []))
                while len(answers) <= idx:
                    answers.append({})
                answers[idx] = {"question": question, "answer": transcript}
                st.session_state["wz_ri_answers"] = answers

                with st.spinner("Silence..."):
                    time.sleep(1.2)
                with st.spinner("Interviewer is thinking..."):
                    time.sleep(5.0)
                    reaction = _wz_ri_react_to_answer(
                        question=question,
                        answer=transcript,
                        cv_text=cv_text,
                        jd=jd,
                        qa_pairs=answers,
                        language=interview_language,
                        personality=personality,
                    )

                reactions = list(st.session_state.get("wz_ri_live_reactions", []))
                while len(reactions) <= idx:
                    reactions.append({})
                reactions[idx] = reaction
                st.session_state["wz_ri_live_reactions"] = reactions

                st.info(str(reaction.get("reaction", "Hmm...")))

                if reaction.get("needs_followup") and reaction.get("followup_question") and idx < len(questions) - 1:
                    st.session_state["wz_ri_questions"][idx + 1] = reaction.get("followup_question")

                if idx < len(questions) - 1:
                    st.session_state["wz_ri_current_index"] = idx + 1
                    _wz_ri_reset_answer_box()
                    st.rerun()
                else:
                    st.session_state["wz_ri_closing_reached"] = True
                    _wz_ri_reset_answer_box()
                    st.rerun()
            else:
                st.warning("Transcript was not created. Please record again.")


def _wz_ri_finish_and_score(cv_text: str, jd: str, company: str, role: str, website: str, language: str):
    st.markdown("### Closing")
    st.info("That’s all from my side. We’ll wrap up here.")

    if st.button("Show Final Feedback", key="wz_ri_show_final_feedback", use_container_width=True):
        answers = list(st.session_state.get("wz_ri_answers", []))
        with st.spinner("Reconstructing interviewer impression..."):
            time.sleep(1.5)
            result = _wz_ri_score_full_interview(
                cv_text=cv_text,
                jd=jd,
                company=company,
                role=role,
                qa_pairs=answers,
                reactions=st.session_state.get("wz_ri_live_reactions", []),
                language=language,
            )
        st.session_state["wz_ri_final_score"] = result
        st.session_state["interview_score"] = result.get("overall_score", 0)
        st.session_state["wz_ri_closing_reached"] = False
        st.rerun()


def _wz_ri_render_final_score(result: dict, company: str, role: str, website: str, language: str):
    st.markdown("## Final Interview Feedback")
    previous = st.session_state.get("wz_ri_previous_score")
    current = int(result.get("overall_score", 0) or 0)
    target = int(result.get("target_score", 80) or 80)

    st.metric("Interview Readiness Score", f"{current}/100", None if previous is None else current - int(previous))
    st.caption(f"Target: {target}+ for stronger interview readiness.")

    scores = result.get("scores", {}) if isinstance(result.get("scores"), dict) else {}
    c1, c2, c3 = st.columns(3)
    for idx, key in enumerate(["relevance", "depth", "structure", "confidence", "keyword_match", "honesty"]):
        value = scores.get(key, 0)
        [c1, c2, c3][idx % 3].metric(key.replace("_", " ").title(), f"{value}/10")

    st.markdown("### 🔍 What hurt you most")
    wrong = result.get("what_hurt_you_most", [])
    if wrong:
        for item in wrong:
            st.markdown(f"- {item}")

    st.markdown("### ⚠️ Missed opportunities")
    missed = result.get("missed_opportunities", [])
    if missed:
        for item in missed:
            st.markdown(f"- {item}")

    st.markdown("### 🎯 Interviewer impression")
    st.info(str(result.get("interviewer_impression", "You came across as generally prepared, but could be more specific.")))

    st.markdown("### ✅ What was good")
    good = result.get("what_was_good", [])
    if good:
        for item in good:
            st.markdown(f"- {item}")

    if result.get("missing_keywords"):
        st.markdown("### Missing keywords to add only if true")
        for item in result.get("missing_keywords", []):
            st.markdown(f"- {item}")

    st.markdown("### 🔁 Immediate coaching loop")
    st.info(str(result.get("retry_instruction", "Let’s improve your weakest answer.")))

    with st.expander("Improved version of weakest answer", expanded=True):
        st.write(result.get("improved_version_of_weakest_answer", "Use STAR structure and include a truthful measurable result."))

    retry_col, full_retry_col = st.columns(2)
    with retry_col:
        if st.button("Retry Weakest Answer", key="wz_ri_retry_weakest", use_container_width=True):
            st.session_state["wz_ri_previous_score"] = current
            q_num = int(result.get("weakest_answer_question_number", 1) or 1)
            st.session_state["wz_ri_current_index"] = max(0, min(3, q_num - 1))
            st.session_state["wz_ri_final_score"] = {}
            st.session_state["wz_ri_closing_reached"] = False
            _wz_ri_reset_answer_box()
            st.rerun()

    with full_retry_col:
        if st.button("Restart Full Interview", key="wz_ri_restart_full", use_container_width=True):
            st.session_state["wz_ri_previous_score"] = current
            for key in [
                "wz_ri_questions",
                "wz_ri_current_index",
                "wz_ri_answers",
                "wz_ri_transcript",
                "wz_ri_answer_saved",
                "wz_ri_final_score",
                "wz_ri_started",
                "wz_ri_live_reactions",
                "wz_ri_closing_reached",
                "wz_ri_last_processed_audio_key",
            ]:
                st.session_state.pop(key, None)
            st.rerun()

    report_text = f"""WorkZo AI - Pseudo-Live Interview Simulation Report

Company: {company or "Not specified"}
Role: {role or "Not specified"}
Website: {website or "Not specified"}
Language: {language}

Interview Answers:
{json.dumps(st.session_state.get("wz_ri_answers", []), indent=2, ensure_ascii=False)}

Live Reactions:
{json.dumps(st.session_state.get("wz_ri_live_reactions", []), indent=2, ensure_ascii=False)}

Final Evaluation:
{json.dumps(result, indent=2, ensure_ascii=False)}
"""
    dl1, dl2 = st.columns(2)
    with dl1:
        st.download_button(
            "Download Report TXT",
            data=report_text.encode("utf-8"),
            file_name="workzo_pseudo_live_interview_report.txt",
            mime="text/plain",
            key="wz_ri_download_txt",
            use_container_width=True,
        )
    with dl2:
        pdf = _wz_ri_make_pdf_report(report_text)
        if pdf:
            st.download_button(
                "Download Report PDF",
                data=pdf,
                file_name="workzo_pseudo_live_interview_report.pdf",
                mime="application/pdf",
                key="wz_ri_download_pdf",
                use_container_width=True,
            )
        else:
            st.caption("PDF report unavailable because ReportLab is not installed.")


def show_workobot():
    render_real_interview_simulation()
