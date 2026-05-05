
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


# =========================================================
# WorkZo v150 - 10x Real Interview Upgrade
# Adds: bilingual mode, interviewer personality, interruptions,
# pressure simulation, typed/voice answers, hiring decision logic,
# and stronger end-of-interview report.
# This block intentionally overrides selected functions above.
# =========================================================


def _wz150_get_selected_job_context() -> dict:
    try:
        job = st.session_state.get("selected_job") or st.session_state.get("active_job_session") or {}
        if not isinstance(job, dict):
            job = {}
        return job
    except Exception:
        return {}


def _wz150_detect_job_language_requirement(jd: str) -> str:
    text = str(jd or "").lower()
    if any(x in text for x in ["deutsch", "german", "b2", "c1", "c2", "gute deutsch", "sehr gute deutsch"]):
        return "German"
    if any(x in text for x in ["french", "français", "francais"]):
        return "French"
    if any(x in text for x in ["spanish", "español", "espanol"]):
        return "Spanish"
    if any(x in text for x in ["dutch", "nederlands"]):
        return "Dutch"
    return ""


def _wz150_interview_language(preferred_language: str, jd: str, override: str = "Auto") -> str:
    override = str(override or "Auto").strip()
    if override and override != "Auto":
        return override
    required = _wz150_detect_job_language_requirement(jd)
    if required:
        return required
    return preferred_language or "English"


def _wz150_cv_snapshot(cv_text: str, jd: str, role: str) -> str:
    cv = str(cv_text or "")
    jd_text = str(jd or "")
    role_text = str(role or st.session_state.get("target_role", "") or "the role")
    return f"CV words: {len(cv.split())} · JD words: {len(jd_text.split())} · Target: {role_text or 'Not set'}"


def _wz150_star_flags(answer: str) -> dict:
    text = str(answer or "").lower()
    return {
        "situation": any(x in text for x in ["situation", "when", "while", "in my role", "during", "project"]),
        "task": any(x in text for x in ["task", "responsible", "needed", "goal", "objective"]),
        "action": any(x in text for x in ["i did", "i used", "i built", "i created", "i analyzed", "i handled", "i worked", "i solved"]),
        "result": any(x in text for x in ["result", "impact", "improved", "reduced", "increased", "%", "saved", "measured", "outcome", "faster", "better"]),
    }


def _wz_ri_build_questions(cv_text: str, jd: str, company: str, role: str, website: str, company_context: str, language: str, personality: str):
    intro_question = "Let’s begin. Tell me about yourself, but keep it relevant to this job."
    prompt = f"""
You are a realistic senior interviewer in a live hiring interview.

Interview personality: {personality}
Interview language: {language}

Candidate CV:
{cv_text[:7500]}

Job Description:
{jd[:7500]}

Company: {company or "Not specified"}
Target role: {role or "Not specified"}
Company website: {website or "Not specified"}
Company context: {company_context or "No reliable company context available."}

Create exactly 5 interview questions after the cold-open introduction.
The interview must feel real, slightly pressured, and job-specific.

Question design:
1. Role fit / motivation linked to CV and JD.
2. Technical or skill-based screening based on the JD.
3. Behavioral STAR question based on the CV.
4. Pressure follow-up about a gap/missing skill/risk in the CV.
5. Curveball/hiring decision question.

Rules:
- Reference the CV and job description directly.
- Do not ask generic textbook questions.
- Keep questions natural and recruiter-like.
- Use firm but fair language.
- If job requires a local language, ask at least one question in that language.
- Return only valid JSON.

Return JSON:
{{"questions": ["question 2", "question 3", "question 4", "question 5", "question 6"]}}
"""
    raw = _wz_ri_ai(prompt, json_mode=True, language=language)
    data = _wz_ri_json(raw, {})
    extra = data.get("questions") if isinstance(data, dict) else None
    if not isinstance(extra, list) or len(extra) < 5:
        extra = [
            "Why are you a strong fit for this job based on your CV?",
            "Which skill from the job description can you prove with a real example?",
            "Tell me about a project or support case from your CV using STAR: situation, task, action, result.",
            "I see some possible gaps compared with this job. What would you need to improve quickly?",
            "If I had to decide today, why should I move you to the next round?",
        ]
    return [intro_question] + [str(q).strip() for q in extra[:5] if str(q).strip()]


def _wz_ri_react_to_answer(question: str, answer: str, cv_text: str, jd: str, qa_pairs: list, language: str, personality: str):
    flags = _wz_ri_answer_quality_flags(answer, jd)
    star = _wz150_star_flags(answer)
    words = int(flags.get("words", 0) or 0)
    personality_l = str(personality or "Strict").lower()

    # deterministic pressure/interruption layer first
    if words < 25:
        return {
            "reaction": "That was too short for a real interview answer.",
            "needs_followup": True,
            "followup_question": "Give me one specific example with what you did and what changed because of it.",
            "interruption_reason": "too short",
            "coach_note": "Use STAR and add a result.",
        }
    if flags.get("too_long"):
        return {
            "reaction": "I’ll stop you there — this is getting too long.",
            "needs_followup": True,
            "followup_question": "Give me the same answer again in 45 seconds, with one clear result.",
            "interruption_reason": "too long",
            "coach_note": "Be concise and lead with the result.",
        }
    if not star.get("result"):
        return {
            "reaction": "Good context, but I’m missing the result.",
            "needs_followup": True,
            "followup_question": "What was the measurable outcome or business impact?",
            "interruption_reason": "missing impact",
            "coach_note": "Add a metric, speed, quality, volume, customer outcome, or learning result.",
        }

    prompt = f"""
You are a realistic {personality_l} interviewer.

React to the user's answer as a human interviewer would, then decide if a follow-up is required.

Question:
{question}

User answer:
{answer}

Previous answers:
{json.dumps(qa_pairs, ensure_ascii=False)}

Detected flags:
{json.dumps(flags, ensure_ascii=False)}

STAR flags:
{json.dumps(star, ensure_ascii=False)}

CV:
{cv_text[:5000]}

Job Description:
{jd[:5000]}

Return ONLY valid JSON:
{{
  "reaction": "short human interviewer reaction",
  "needs_followup": true,
  "followup_question": "specific follow-up question if needed",
  "interruption_reason": "too vague|too long|missing impact|missing tools|off-topic|weak STAR|none",
  "coach_note": "one short private coaching note for candidate"
}}

Rules:
- Be realistic, not overly friendly.
- If answer is vague, challenge it.
- If answer lacks STAR, ask for structure.
- If answer misses job keywords, ask for job-specific evidence.
- If answer is strong, acknowledge briefly and move on.
- Keep the response in {language}.
"""
    raw = _wz_ri_ai(prompt, json_mode=True, language=language)
    data = _wz_ri_json(raw, {})
    if not isinstance(data, dict) or not data:
        return {
            "reaction": "Good, but I want one sharper example.",
            "needs_followup": True,
            "followup_question": "Can you answer that again using STAR and include the result?",
            "interruption_reason": "weak STAR",
            "coach_note": "Use situation, task, action, result.",
        }
    data.setdefault("reaction", "Hmm, okay.")
    data.setdefault("needs_followup", False)
    data.setdefault("followup_question", "")
    data.setdefault("interruption_reason", "none")
    data.setdefault("coach_note", "")
    return data


def _wz_ri_score_full_interview(cv_text: str, jd: str, company: str, role: str, qa_pairs: list, reactions: list, language: str) -> dict:
    prompt = f"""
You are a senior hiring manager making a realistic hiring decision after an interview.

Candidate CV:
{cv_text[:7000]}

Job Description:
{jd[:7000]}

Company: {company or "Not specified"}
Role: {role or "Not specified"}

Interview answers:
{json.dumps(qa_pairs, ensure_ascii=False)}

Interviewer reactions during interview:
{json.dumps(reactions, ensure_ascii=False)}

Return ONLY valid JSON:
{{
  "overall_score": 0,
  "target_score": 80,
  "hiring_decision": "Pass to next round|Borderline|Not ready",
  "hiring_reason": "short realistic reason",
  "scores": {{
    "relevance": 0,
    "depth": 0,
    "structure_star": 0,
    "clarity": 0,
    "confidence": 0,
    "job_keyword_match": 0,
    "honesty": 0
  }},
  "strengths": [],
  "top_3_mistakes": [],
  "what_hurt_you_most": [],
  "missed_opportunities": [],
  "interviewer_impression": "",
  "missing_keywords": [],
  "weakest_answer_question_number": 1,
  "improved_version_of_weakest_answer": "",
  "better_answer_formula": "",
  "next_action": "",
  "final_readiness_message": ""
}}

Scoring rules:
- overall_score is 0-100.
- all category scores are 0-10.
- Be strict like a real interviewer.
- If answers lack measurable impact, penalize depth and structure.
- If answers do not connect CV to JD, penalize relevance and keyword match.
- Do not invent achievements.
- Improved answer must be truthful and based only on CV/user answers.
- Keep feedback in {language}.
"""
    raw = _wz_ri_ai(prompt, json_mode=True, language=language)
    data = _wz_ri_json(raw, {})
    if not isinstance(data, dict) or not data:
        data = {
            "overall_score": 58,
            "target_score": 80,
            "hiring_decision": "Borderline",
            "hiring_reason": "You showed relevant background, but answers need stronger examples and measurable impact.",
            "scores": {
                "relevance": 6,
                "depth": 4,
                "structure_star": 5,
                "clarity": 6,
                "confidence": 6,
                "job_keyword_match": 5,
                "honesty": 8,
            },
            "strengths": ["Clear basic communication", "Relevant background present in CV"],
            "top_3_mistakes": ["Answers were too general", "Missing measurable impact", "Weak connection to the job description"],
            "what_hurt_you_most": ["You did not prove your claims with specific examples."],
            "missed_opportunities": ["You could have connected your CV skills directly to the job requirements."],
            "interviewer_impression": "You came across as promising but not fully interview-ready yet.",
            "missing_keywords": [],
            "weakest_answer_question_number": 1,
            "improved_version_of_weakest_answer": "Use STAR. Start with the situation, explain your task, describe your action, and finish with a truthful result.",
            "better_answer_formula": "Situation → Task → Action → Result → Why it matters for this job.",
            "next_action": "Practice your weakest answer again with a measurable result.",
            "final_readiness_message": "Not fully ready yet. Aim for 80+ before the real interview.",
        }

    scores = data.get("scores", {}) if isinstance(data.get("scores"), dict) else {}
    clean_scores = {}
    for key in ["relevance", "depth", "structure_star", "clarity", "confidence", "job_keyword_match", "honesty"]:
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
        data["overall_score"] = int(sum(clean_scores.values()) / max(1, len(clean_scores)) * 10)
    if data["overall_score"] >= 80:
        data.setdefault("hiring_decision", "Pass to next round")
    elif data["overall_score"] >= 60:
        data.setdefault("hiring_decision", "Borderline")
    else:
        data.setdefault("hiring_decision", "Not ready")
    for key in ["strengths", "top_3_mistakes", "what_hurt_you_most", "missed_opportunities", "missing_keywords"]:
        if not isinstance(data.get(key), list):
            data[key] = _as_list(data.get(key)) if "_as_list" in globals() else []
    data.setdefault("hiring_reason", "Based on your answers and job fit.")
    data.setdefault("next_action", "Practice again with stronger examples.")
    data.setdefault("better_answer_formula", "Situation → Task → Action → Result.")
    data.setdefault("interviewer_impression", "You came across as generally prepared, but could be more specific.")
    data.setdefault("final_readiness_message", "Practice again before the real interview.")
    try:
        data["weakest_answer_question_number"] = max(1, min(6, int(data.get("weakest_answer_question_number", 1))))
    except Exception:
        data["weakest_answer_question_number"] = 1
    return data


def _wz150_render_pressure_bar(start_time: float, limit_seconds: int):
    try:
        elapsed = max(0, int(time.time() - float(start_time or time.time())))
    except Exception:
        elapsed = 0
    ratio = min(1.0, elapsed / max(1, int(limit_seconds or 60)))
    remain = max(0, int(limit_seconds or 60) - elapsed)
    st.progress(ratio)
    if remain > 0:
        st.caption(f"⏱ Pressure timer: {remain}s left. Keep it concise and structured.")
    else:
        st.warning("⏱ Time is up. In a real interview, the interviewer may interrupt now.")


def render_real_interview_simulation():
    st.subheader("🎤 Real Interview AI")
    st.caption("A realistic interview based on your CV, selected job, country, and language. Answer by voice or typing.")

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
        "wz_ri_question_started_at": time.time(),
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    cv_text = _wz_ri_get_cv_text()
    default_jd = _wz_ri_get_jd_text()
    selected_job = _wz150_get_selected_job_context()

    language_options = ["Auto", "English", "German", "Dutch", "French", "Spanish", "Hindi", "Tamil"]
    answer_language_options = ["Same as interview", "English", "German", "Dutch", "French", "Spanish", "Hindi", "Tamil", "Any language"]
    preferred = st.session_state.get("preferred_language", "English")
    required = _wz150_detect_job_language_requirement(default_jd)
    suggested_language = required or preferred or "English"

    with st.container(border=True):
        st.markdown("### Interview setup")
        st.caption("WorkZo will use your uploaded CV and selected job. You can answer in another language; feedback will include a stronger answer in the interview/job language.")

        c1, c2, c3 = st.columns(3)
        with c1:
            language_choice = st.selectbox(
                "Interview language",
                language_options,
                index=0,
                key="wz_ri_language_choice_v150",
                disabled=bool(st.session_state.get("wz_ri_started")),
            )
        with c2:
            answer_language = st.selectbox(
                "You may answer in",
                answer_language_options,
                index=0,
                key="wz_ri_answer_language_v150",
                disabled=bool(st.session_state.get("wz_ri_started")),
            )
        with c3:
            pressure_level = st.selectbox(
                "Pressure level",
                ["Normal", "Realistic", "High pressure"],
                index=1,
                key="wz_ri_pressure_level_v150",
                disabled=bool(st.session_state.get("wz_ri_started")),
            )

        interview_language = _wz150_interview_language(suggested_language, default_jd, language_choice)
        st.session_state["wz_ri_interview_language"] = interview_language

        personality = st.selectbox(
            "Interviewer personality",
            ["Strict", "Fast-paced", "Friendly", "Skeptical hiring manager", "Technical recruiter"],
            index=0,
            key="wz_ri_personality",
            disabled=bool(st.session_state.get("wz_ri_started")),
        )
        round_type = st.selectbox(
            "Interview round",
            ["Hiring Manager Round", "Technical Screening", "Behavioral Round", "Final Round"],
            index=0,
            key="wz_ri_round_type",
            disabled=bool(st.session_state.get("wz_ri_started")),
        )

        c1, c2 = st.columns(2)
        with c1:
            company_default = selected_job.get("company", "") if isinstance(selected_job, dict) else ""
            company = st.text_input("Target company", value=company_default, key="wz_ri_company", disabled=bool(st.session_state.get("wz_ri_started")))
        with c2:
            role_default = selected_job.get("title", "") or st.session_state.get("target_role", "")
            role = st.text_input("Target role", value=role_default, key="wz_ri_role", disabled=bool(st.session_state.get("wz_ri_started")))

        website = st.text_input("Company website / careers page (optional)", value="", key="wz_ri_company_website", disabled=bool(st.session_state.get("wz_ri_started")))
        jd = st.text_area("Job description", value=default_jd or selected_job.get("description", ""), height=160, key="wz_ri_jd", disabled=bool(st.session_state.get("wz_ri_started")))

        st.session_state["target_company"] = company
        st.session_state["target_role"] = role
        st.session_state["target_job_title"] = role
        st.session_state["target_company_website"] = website
        st.session_state["selected_job_description"] = jd
        st.session_state["last_understand_job_description"] = jd
        st.session_state["last_prepare_job_description"] = jd
        st.session_state["improve_cv_for_job_desc"] = jd
        st.session_state["doc_tools_job_desc"] = jd
        st.session_state["real_interview_jd_saved"] = jd

        st.info(f"Interview language: {interview_language} · Answer mode: {answer_language} · {_wz150_cv_snapshot(cv_text, jd, role)}")
        if required:
            st.warning(f"This job appears to require {required}. Interview language is adjusted unless you override it.")
        if not cv_text:
            st.error("No CV found. Upload or create your CV first so the interview is not generic.")

        if cv_text and not st.session_state.get("wz_ri_started"):
            if st.button("Prepare Real Interview", key="wz_ri_prepare_brief_v150", use_container_width=True):
                with st.spinner("Building a realistic interview brief from your CV and job..."):
                    st.session_state["wz_ri_focus_areas"] = _wz_ri_extract_focus_areas(cv_text, jd, role, interview_language)
                st.rerun()
            focus = st.session_state.get("wz_ri_focus_areas", [])
            if focus:
                st.success("Interview brief ready.")
                st.markdown("**This interview will test:** " + " · ".join([str(x) for x in focus[:5]]))

    if not cv_text:
        return

    if not st.session_state.get("wz_ri_started"):
        if st.button("🎤 Start Real Interview", key="wz_ri_start_interview_v150", type="primary", use_container_width=True):
            company_context = _wz_ri_company_context(company, website)
            with st.spinner("Interviewer is reading your CV and job description..."):
                questions = _wz_ri_build_questions(cv_text, jd, company, role, website, company_context, interview_language, personality)
            st.session_state["wz_ri_questions"] = questions[:6]
            st.session_state["wz_ri_current_index"] = 0
            st.session_state["wz_ri_answers"] = []
            st.session_state["wz_ri_live_reactions"] = []
            st.session_state["wz_ri_final_score"] = {}
            st.session_state["wz_ri_started"] = True
            st.session_state["wz_ri_closing_reached"] = False
            st.session_state["wz_ri_question_started_at"] = time.time()
            try:
                track_event("interview_started", "Interview", {"language": interview_language, "role": role})
            except Exception:
                pass
            _wz_ri_reset_answer_box()
            st.rerun()
        return

    end_col, reset_col = st.columns([3, 1])
    with end_col:
        if st.button("End Interview & Get Hiring Decision", key="wz_ri_end_now_v150", use_container_width=True):
            st.session_state["wz_ri_closing_reached"] = True
            st.rerun()
    with reset_col:
        if st.button("Reset", key="wz_ri_reset_v150", use_container_width=True):
            for key in ["wz_ri_questions", "wz_ri_current_index", "wz_ri_answers", "wz_ri_transcript", "wz_ri_answer_saved", "wz_ri_audio_nonce", "wz_ri_final_score", "wz_ri_started", "wz_ri_focus_areas", "wz_ri_live_reactions", "wz_ri_closing_reached", "wz_ri_last_processed_audio_key", "wz_ri_question_started_at"]:
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
    # Keep Work-O-Bot context-aware while the interview is in progress.
    st.session_state["current_interview_question"] = str(question)
    st.session_state["wz_current_interview_question"] = str(question)
    st.session_state["wz_ri_current_question"] = str(question)
    st.session_state["wz_ri_current_question_index"] = idx

    limit_seconds = {"Normal": 120, "Realistic": 75, "High pressure": 45}.get(st.session_state.get("wz_ri_pressure_level_v150", "Realistic"), 75)

    st.markdown("### Interview in progress")
    st.caption(f"{personality} · {round_type} · Question {idx + 1}/{len(questions)}")
    _wz150_render_pressure_bar(st.session_state.get("wz_ri_question_started_at", time.time()), limit_seconds)

    st.markdown("### Interviewer")
    st.markdown(
        f"""
        <div class="wz-interview-card">
            <div class="wz-interview-label">{html.escape(personality)} · {html.escape(interview_language)}</div>
            <div class="wz-interview-title">{html.escape(str(question))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    _wz_ri_auto_speak(question, f"q_{idx}_{st.session_state.get('wz_ri_audio_nonce', 0)}")

    st.markdown("### Your answer")
    st.caption("Answer naturally. You can speak or type. WorkZo evaluates structure, relevance, impact, and job fit.")

    typed_answer = st.text_area("⌨ Type your answer", key=f"wz_ri_typed_answer_{idx}_{st.session_state.get('wz_ri_audio_nonce', 0)}", height=150, placeholder="Answer in any supported language. WorkZo will give feedback and improve it in the interview/job language.")

    audio_file = st.audio_input("🎙 Or record your answer", key=f"wz_ri_audio_{idx}_{st.session_state.get('wz_ri_audio_nonce', 0)}") if hasattr(st, "audio_input") else None

    submitted_answer = ""
    if st.button("Submit Answer", key=f"wz_ri_submit_answer_{idx}_{st.session_state.get('wz_ri_audio_nonce', 0)}", type="primary", use_container_width=True):
        if str(typed_answer or "").strip():
            submitted_answer = str(typed_answer).strip()
        elif audio_file is not None:
            with st.spinner("Transcribing your answer..."):
                submitted_answer = _wz_ri_transcribe(audio_file)
        else:
            st.warning("Type or record your answer first.")
            return

        answers = list(st.session_state.get("wz_ri_answers", []))
        while len(answers) <= idx:
            answers.append({})
        answers[idx] = {"question": question, "answer": submitted_answer}
        st.session_state["wz_ri_answers"] = answers

        with st.spinner("Interviewer is reacting..."):
            reaction = _wz_ri_react_to_answer(question, submitted_answer, cv_text, jd, answers, interview_language, personality)

        reactions = list(st.session_state.get("wz_ri_live_reactions", []))
        while len(reactions) <= idx:
            reactions.append({})
        reactions[idx] = reaction
        st.session_state["wz_ri_live_reactions"] = reactions

        st.info(str(reaction.get("reaction", "Hmm...")))
        if reaction.get("coach_note"):
            st.caption("Coach note: " + str(reaction.get("coach_note")))
        if reaction.get("needs_followup") and reaction.get("followup_question") and idx < len(questions) - 1:
            st.session_state["wz_ri_questions"][idx + 1] = reaction.get("followup_question")

        if idx < len(questions) - 1:
            st.session_state["wz_ri_current_index"] = idx + 1
            st.session_state["wz_ri_question_started_at"] = time.time()
            _wz_ri_reset_answer_box()
            st.rerun()
        else:
            st.session_state["wz_ri_closing_reached"] = True
            _wz_ri_reset_answer_box()
            st.rerun()


def _wz_ri_render_final_score(result: dict, company: str, role: str, website: str, language: str):
    st.markdown("## Interview Result")
    previous = st.session_state.get("wz_ri_previous_score")
    current = int(result.get("overall_score", 0) or 0)
    target = int(result.get("target_score", 80) or 80)
    decision = result.get("hiring_decision", "Borderline")

    if current >= target:
        st.success(f"✅ {decision}")
    elif current >= 60:
        st.warning(f"⚠️ {decision}")
    else:
        st.error(f"❌ {decision}")

    st.metric("Interview Readiness Score", f"{current}/100", None if previous is None else current - int(previous))
    st.caption(str(result.get("hiring_reason", "Based on your answers and job fit.")))

    scores = result.get("scores", {}) if isinstance(result.get("scores"), dict) else {}
    c1, c2, c3 = st.columns(3)
    for idx, key in enumerate(["relevance", "depth", "structure_star", "clarity", "confidence", "job_keyword_match", "honesty"]):
        value = scores.get(key, 0)
        [c1, c2, c3][idx % 3].metric(key.replace("_", " ").title(), f"{value}/10")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("### Strengths")
        for item in _as_list(result.get("strengths"))[:3]:
            st.markdown(f"- {item}")
    with col_b:
        st.markdown("### Top 3 mistakes")
        for item in _as_list(result.get("top_3_mistakes"))[:3]:
            st.markdown(f"- {item}")

    st.markdown("### Interviewer impression")
    st.info(str(result.get("interviewer_impression", "You came across as generally prepared, but could be more specific.")))

    st.markdown("### Better answer formula")
    st.caption(str(result.get("better_answer_formula", "Situation → Task → Action → Result.")))

    with st.expander("Improved version of weakest answer", expanded=True):
        st.write(result.get("improved_version_of_weakest_answer", "Use STAR structure and include a truthful measurable result."))

    st.markdown("### Next action")
    st.success(str(result.get("next_action", "Practice your weakest answer again.")))

    retry_col, full_retry_col = st.columns(2)
    with retry_col:
        if st.button("Practice Weakest Answer", key="wz_ri_retry_weakest_v150", use_container_width=True):
            st.session_state["wz_ri_previous_score"] = current
            q_num = int(result.get("weakest_answer_question_number", 1) or 1)
            st.session_state["wz_ri_current_index"] = max(0, min(5, q_num - 1))
            st.session_state["wz_ri_final_score"] = {}
            st.session_state["wz_ri_closing_reached"] = False
            st.session_state["wz_ri_question_started_at"] = time.time()
            _wz_ri_reset_answer_box()
            st.rerun()
    with full_retry_col:
        if st.button("Restart Full Interview", key="wz_ri_restart_full_v150", use_container_width=True):
            st.session_state["wz_ri_previous_score"] = current
            for key in ["wz_ri_questions", "wz_ri_current_index", "wz_ri_answers", "wz_ri_transcript", "wz_ri_answer_saved", "wz_ri_final_score", "wz_ri_started", "wz_ri_live_reactions", "wz_ri_closing_reached", "wz_ri_last_processed_audio_key", "wz_ri_question_started_at"]:
                st.session_state.pop(key, None)
            st.rerun()

    report_text = f"""WorkZo AI - Real Interview Report

Company: {company or "Not specified"}
Role: {role or "Not specified"}
Website: {website or "Not specified"}
Language: {language}
Decision: {decision}
Score: {current}/100

Answers:
{json.dumps(st.session_state.get("wz_ri_answers", []), indent=2, ensure_ascii=False)}

Reactions:
{json.dumps(st.session_state.get("wz_ri_live_reactions", []), indent=2, ensure_ascii=False)}

Final Evaluation:
{json.dumps(result, indent=2, ensure_ascii=False)}
"""
    dl1, dl2 = st.columns(2)
    with dl1:
        st.download_button("Download Report TXT", data=report_text.encode("utf-8"), file_name="workzo_real_interview_report.txt", mime="text/plain", key="wz_ri_download_txt_v150", use_container_width=True)
    with dl2:
        pdf = _wz_ri_make_pdf_report(report_text)
        if pdf:
            st.download_button("Download Report PDF", data=pdf, file_name="workzo_real_interview_report.pdf", mime="application/pdf", key="wz_ri_download_pdf_v150", use_container_width=True)
        else:
            st.caption("PDF report unavailable because ReportLab is not installed.")



# =========================================================
# WorkZo v151 - Real Human Interviewer + Language Lock Fix
# Purpose:
# - Remove passive "time is up" warning and replace it with an actual interviewer interruption.
# - Make first question, fallbacks, reactions and timer text respect the selected interview language.
# - Make fallback questions CV/job-specific instead of generic.
# - Add human interviewer fillers: "hmm", "okay", "interesting", "let me stop you there".
# =========================================================

def _wz151_lang_code(language: str) -> str:
    return str(language or "English").strip().lower()


def _wz151_phrase(key: str, language: str = "English", **kwargs) -> str:
    """Small deterministic UI/interviewer phrase translator for supported languages."""
    lang = _wz151_lang_code(language)
    phrases = {
        "timer_left": {
            "english": "⏱ {seconds}s left. Keep it concise and structured.",
            "german": "⏱ Noch {seconds}s. Antworten Sie kurz und strukturiert.",
            "dutch": "⏱ Nog {seconds}s. Houd het kort en gestructureerd.",
            "french": "⏱ Encore {seconds}s. Répondez de façon concise et structurée.",
            "spanish": "⏱ Quedan {seconds}s. Responde de forma breve y estructurada.",
            "hindi": "⏱ {seconds}s बाकी हैं। जवाब छोटा और structured रखें।",
            "tamil": "⏱ இன்னும் {seconds}s. சுருக்கமாகவும் கட்டமைப்புடனும் பதிலளிக்கவும்.",
        },
        "interrupt_time": {
            "english": "Hmm, let me stop you there. In a real interview I need a sharper answer. Give me the direct point, one example, and the result.",
            "german": "Hm, ich unterbreche Sie kurz. In einem echten Interview brauche ich eine klarere Antwort: Punkt, Beispiel und Ergebnis.",
            "dutch": "Hmm, ik onderbreek je even. In een echt interview heb ik een scherper antwoord nodig: punt, voorbeeld en resultaat.",
            "french": "Hmm, je vous interromps ici. Dans un vrai entretien, il faut une réponse plus claire : l'idée, un exemple et le résultat.",
            "spanish": "Hmm, te interrumpo aquí. En una entrevista real necesito una respuesta más clara: punto principal, ejemplo y resultado.",
            "hindi": "Hmm, मैं आपको यहीं रोकूंगा। Real interview में मुझे साफ जवाब चाहिए: main point, example और result.",
            "tamil": "Hmm, இங்கே நான் நிறுத்துகிறேன். உண்மையான interview-ல் தெளிவான பதில் வேண்டும்: முக்கிய point, example, result.",
        },
        "intro": {
            "english": "Let’s begin. Give me a brief introduction based on your CV, and connect it to this job.",
            "german": "Lassen Sie uns beginnen. Stellen Sie sich kurz anhand Ihres Lebenslaufs vor und verbinden Sie es mit dieser Stelle.",
            "dutch": "Laten we beginnen. Geef een korte introductie op basis van je cv en koppel die aan deze functie.",
            "french": "Commençons. Présentez-vous brièvement à partir de votre CV et reliez votre profil à ce poste.",
            "spanish": "Empecemos. Preséntate brevemente usando tu CV y conecta tu experiencia con este puesto.",
            "hindi": "चलिए शुरू करते हैं। अपने CV के आधार पर अपना छोटा introduction दीजिए और इसे इस job से जोड़िए।",
            "tamil": "தொடங்கலாம். உங்கள் CV அடிப்படையில் சிறிய அறிமுகம் சொல்லி, அதை இந்த job-க்கு இணைக்கவும்.",
        },
        "too_short": {
            "english": "Hmm, that’s too short. Give me a real example — what happened, what you did, and what changed?",
            "german": "Hm, das ist zu kurz. Geben Sie mir ein konkretes Beispiel: Was ist passiert, was haben Sie getan, und was hat sich verändert?",
            "dutch": "Hmm, dat is te kort. Geef een concreet voorbeeld: wat gebeurde er, wat deed jij, en wat veranderde er?",
            "french": "Hmm, c’est trop court. Donnez-moi un exemple concret : que s’est-il passé, qu’avez-vous fait, et quel a été le résultat ?",
            "spanish": "Hmm, eso es demasiado corto. Dame un ejemplo real: qué pasó, qué hiciste y qué cambió.",
            "hindi": "Hmm, यह बहुत छोटा है। एक real example दीजिए: क्या हुआ, आपने क्या किया, और क्या बदला?",
            "tamil": "Hmm, இது மிகவும் short. ஒரு real example சொல்லுங்கள்: என்ன நடந்தது, நீங்கள் என்ன செய்தீர்கள், என்ன result?",
        },
        "too_long": {
            "english": "I’ll stop you there — you’re losing the main point. Give me the same answer in 45 seconds with one clear result.",
            "german": "Ich stoppe Sie kurz — der Hauptpunkt geht verloren. Sagen Sie es in 45 Sekunden mit einem klaren Ergebnis.",
            "dutch": "Ik stop je even — je verliest de kern. Geef hetzelfde antwoord in 45 seconden met één duidelijk resultaat.",
            "french": "Je vous arrête ici — le point principal se perd. Répondez en 45 secondes avec un résultat clair.",
            "spanish": "Te interrumpo — se está perdiendo el punto principal. Respóndelo en 45 segundos con un resultado claro.",
            "hindi": "मैं आपको रोकता हूँ — main point खो रहा है। यही answer 45 seconds में एक clear result के साथ दीजिए।",
            "tamil": "நான் இங்கே நிறுத்துகிறேன் — முக்கிய point தெளிவாக இல்லை. இதே பதிலை 45 seconds-ல் ஒரு தெளிவான result உடன் சொல்லுங்கள்.",
        },
        "missing_impact": {
            "english": "Okay, interesting — but I’m missing the impact. What was the measurable outcome?",
            "german": "Okay, interessant — aber mir fehlt die Wirkung. Was war das messbare Ergebnis?",
            "dutch": "Oké, interessant — maar ik mis de impact. Wat was het meetbare resultaat?",
            "french": "D’accord, intéressant — mais il manque l’impact. Quel était le résultat mesurable ?",
            "spanish": "Bien, interesante — pero falta el impacto. ¿Cuál fue el resultado medible?",
            "hindi": "Okay, interesting — लेकिन impact missing है। measurable outcome क्या था?",
            "tamil": "சரி, interesting — ஆனால் impact missing. measurable outcome என்ன?",
        },
    }
    lang_map = phrases.get(key, {})
    template = lang_map.get(lang) or lang_map.get("english") or ""
    try:
        return template.format(**kwargs)
    except Exception:
        return template


def _wz151_extract_cv_keywords(cv_text: str, jd: str = "") -> list:
    text = (str(cv_text or "") + "\n" + str(jd or "")).lower()
    candidates = [
        "python", "sql", "tableau", "power bi", "excel", "customer support", "technical support",
        "data analysis", "dashboard", "reporting", "crm", "saas", "api", "cloud", "gcp", "aws",
        "stakeholder", "communication", "troubleshooting", "incident", "service desk", "it support",
        "project", "leadership", "sales", "marketing", "analytics", "machine learning"
    ]
    found = []
    for word in candidates:
        if word in text and word not in found:
            found.append(word)
    return found[:6]


def _wz151_question_fallbacks(cv_text: str, jd: str, role: str, language: str) -> list:
    role_text = str(role or st.session_state.get("target_role", "this role") or "this role")
    skills = _wz151_extract_cv_keywords(cv_text, jd)
    skill_text = ", ".join(skills[:3]) if skills else "your most relevant skills"
    lang = _wz151_lang_code(language)
    if lang == "german":
        return [
            f"Warum passen Ihre Erfahrungen aus dem Lebenslauf zu dieser Stelle als {role_text}?",
            f"Ich sehe {skill_text} in Ihrem Profil. Beschreiben Sie ein konkretes Beispiel, wo Sie das angewendet haben.",
            "Erzählen Sie mir von einer schwierigen Situation aus Ihrer bisherigen Arbeit. Nutzen Sie STAR: Situation, Aufgabe, Aktion, Ergebnis.",
            "Welche Anforderung aus der Stellenbeschreibung ist für Sie aktuell die größte Lücke, und wie würden Sie sie schnell schließen?",
            "Wenn ich heute entscheiden müsste: Warum sollte ich Sie in die nächste Runde einladen?",
        ]
    if lang == "tamil":
        return [
            f"உங்கள் CV அடிப்படையில், {role_text} role-க்கு நீங்கள் ஏன் பொருத்தமானவர்?",
            f"உங்கள் profile-ல் {skill_text} தெரிகிறது. அதைப் பயன்படுத்திய ஒரு real example சொல்லுங்கள்.",
            "உங்கள் வேலை அனுபவத்தில் ஒரு சவாலான situation பற்றி STAR format-ல் சொல்லுங்கள்: Situation, Task, Action, Result.",
            "இந்த job description-ல் உங்களுக்கு இருக்கும் பெரிய gap என்ன? அதை விரைவாக எப்படி improve செய்வீர்கள்?",
            "நான் இன்று முடிவு செய்ய வேண்டுமென்றால், next round-க்கு உங்களை ஏன் move செய்ய வேண்டும்?",
        ]
    if lang == "hindi":
        return [
            f"अपने CV के आधार पर बताइए कि आप {role_text} role के लिए क्यों fit हैं?",
            f"आपके profile में {skill_text} दिख रहा है। इसका एक real example बताइए।",
            "अपने पिछले काम से एक challenging situation बताइए using STAR: Situation, Task, Action, Result.",
            "इस job description के हिसाब से आपका biggest gap क्या है और आप उसे जल्दी कैसे improve करेंगे?",
            "अगर मुझे आज decision लेना हो, तो मैं आपको next round में क्यों भेजूं?",
        ]
    return [
        f"Why are you a strong fit for {role_text} based on your CV?",
        f"I see {skill_text} in your profile. Give me one specific example where you used it.",
        "Tell me about a challenging situation from your CV using STAR: situation, task, action, result.",
        "Compared with this job description, what is your biggest gap and how would you close it quickly?",
        "If I had to decide today, why should I move you to the next round?",
    ]


# Override previous timer renderer: show a real interviewer interruption instead of passive warning.
def _wz150_render_pressure_bar(start_time: float, limit_seconds: int):
    try:
        elapsed = max(0, int(time.time() - float(start_time or time.time())))
    except Exception:
        elapsed = 0
    ratio = min(1.0, elapsed / max(1, int(limit_seconds or 60)))
    remain = max(0, int(limit_seconds or 60) - elapsed)
    language = st.session_state.get("wz_ri_interview_language", st.session_state.get("preferred_language", "English"))
    st.progress(ratio)
    if remain > 0:
        st.caption(_wz151_phrase("timer_left", language, seconds=remain))
    else:
        st.session_state["wz_ri_time_interrupted"] = True
        st.markdown(
            f"""
            <div style="border:1px solid rgba(248,113,113,.35);background:rgba(127,29,29,.24);border-radius:18px;padding:1rem 1.1rem;margin:.75rem 0;">
              <div style="font-weight:900;color:#fecaca;margin-bottom:.35rem;">Interviewer interrupts</div>
              <div style="color:#fff;font-size:1.02rem;line-height:1.45;">{html.escape(_wz151_phrase('interrupt_time', language))}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# Override question builder: language-locked, CV/JD-specific, no English hardcoded first question.
def _wz_ri_build_questions(cv_text: str, jd: str, company: str, role: str, website: str, company_context: str, language: str, personality: str):
    intro_question = _wz151_phrase("intro", language)
    cv_keywords = ", ".join(_wz151_extract_cv_keywords(cv_text, jd)) or "not detected"
    prompt = f"""
You are a realistic senior interviewer in a live hiring interview.

CRITICAL LANGUAGE RULE:
- Ask every question in this exact interview language: {language}.
- Do not switch to English unless the interview language is English.
- If the candidate may answer bilingually, you still ask in {language}.

Interview personality: {personality}
Candidate CV keywords detected: {cv_keywords}

Candidate CV:
{cv_text[:7500]}

Job Description:
{jd[:7500]}

Company: {company or "Not specified"}
Target role: {role or "Not specified"}
Company website: {website or "Not specified"}
Company context: {company_context or "No reliable company context available."}

Create exactly 5 interview questions after the cold-open introduction.
The interview must feel real, human, slightly pressured, and job-specific.

Rules:
- Reference the CV directly.
- Reference the job description directly.
- Ask why their CV evidence proves role fit.
- Challenge at least one gap or weak area.
- Avoid generic textbook questions.
- Keep questions natural and recruiter-like.
- Use small human wording like "hmm", "okay", "interesting" only when natural.
- Return only valid JSON.

Return JSON:
{{"questions": ["question 2", "question 3", "question 4", "question 5", "question 6"]}}
"""
    raw = _wz_ri_ai(prompt, json_mode=True, language=language)
    data = _wz_ri_json(raw, {})
    extra = data.get("questions") if isinstance(data, dict) else None
    if not isinstance(extra, list) or len(extra) < 5:
        extra = _wz151_question_fallbacks(cv_text, jd, role, language)
    extra = [str(q).strip() for q in extra[:5] if str(q).strip()]
    return [intro_question] + extra


# Override answer reaction: human-like interviewer reactions + language lock + real interruptions.
def _wz_ri_react_to_answer(question: str, answer: str, cv_text: str, jd: str, qa_pairs: list, language: str, personality: str):
    flags = _wz_ri_answer_quality_flags(answer, jd)
    star = _wz150_star_flags(answer)
    words = int(flags.get("words", 0) or 0)
    personality_l = str(personality or "Strict").lower()

    if st.session_state.get("wz_ri_time_interrupted"):
        st.session_state["wz_ri_time_interrupted"] = False
        return {
            "reaction": _wz151_phrase("interrupt_time", language),
            "needs_followup": True,
            "followup_question": _wz151_phrase("missing_impact", language),
            "interruption_reason": "time pressure",
            "coach_note": "Keep answers under the time limit: point → example → result.",
        }
    if words < 25:
        return {
            "reaction": _wz151_phrase("too_short", language),
            "needs_followup": True,
            "followup_question": _wz151_phrase("too_short", language),
            "interruption_reason": "too short",
            "coach_note": "Use STAR and add a result.",
        }
    if flags.get("too_long"):
        return {
            "reaction": _wz151_phrase("too_long", language),
            "needs_followup": True,
            "followup_question": _wz151_phrase("too_long", language),
            "interruption_reason": "too long",
            "coach_note": "Be concise and lead with the result.",
        }
    if not star.get("result"):
        return {
            "reaction": _wz151_phrase("missing_impact", language),
            "needs_followup": True,
            "followup_question": _wz151_phrase("missing_impact", language),
            "interruption_reason": "missing impact",
            "coach_note": "Add a metric, speed, quality, volume, customer outcome, or learning result.",
        }

    prompt = f"""
You are a realistic {personality_l} interviewer.

CRITICAL LANGUAGE RULE:
- Keep your interviewer reaction and follow-up in this exact language: {language}.
- Do not answer in English unless {language} is English.

React to the user's answer as a human interviewer would.
Use natural short reactions such as "hmm", "okay", "interesting", "good", or "let me stop you there" when appropriate.
Then decide if a follow-up is required.

Question:
{question}

User answer:
{answer}

Previous answers:
{json.dumps(qa_pairs, ensure_ascii=False)}

Detected flags:
{json.dumps(flags, ensure_ascii=False)}

STAR flags:
{json.dumps(star, ensure_ascii=False)}

CV:
{cv_text[:5000]}

Job Description:
{jd[:5000]}

Return ONLY valid JSON:
{{
  "reaction": "short human interviewer reaction in {language}",
  "needs_followup": true,
  "followup_question": "specific follow-up question in {language} if needed",
  "interruption_reason": "too vague|too long|missing impact|missing tools|off-topic|weak STAR|none",
  "coach_note": "one short private coaching note for candidate"
}}

Rules:
- Be realistic, not overly friendly.
- Interrupt when vague, long, or missing impact.
- If answer is strong, acknowledge briefly and move on.
- Make follow-up questions based on CV and JD.
"""
    raw = _wz_ri_ai(prompt, json_mode=True, language=language)
    data = _wz_ri_json(raw, {})
    if not isinstance(data, dict) or not data:
        return {
            "reaction": _wz151_phrase("missing_impact", language),
            "needs_followup": True,
            "followup_question": _wz151_phrase("missing_impact", language),
            "interruption_reason": "weak STAR",
            "coach_note": "Use situation, task, action, result.",
        }
    data.setdefault("reaction", _wz151_phrase("missing_impact", language))
    data.setdefault("needs_followup", False)
    data.setdefault("followup_question", "")
    data.setdefault("interruption_reason", "none")
    data.setdefault("coach_note", "")
    return data

# =========================================================
# WorkZo vFINAL - Recruiter Call Interview UI
# Purpose:
# - Replace mixed/old interview page with one focused recruiter-call experience.
# - Enforce selected interview language.
# - Make questions CV + selected-job based.
# - Replace passive timer with real interviewer interruptions.
# =========================================================

def _wz_final_cv_context():
    keys = [
        "workzo_live_cv_text", "cv_editor_widget", "clean_structured_cv_text", "structured_cv_profile",
        "approved_cv_text", "final_cv_text", "improved_cv_text_v92", "cv_text", "uploaded_cv_text"
    ]
    for k in keys:
        try:
            v = st.session_state.get(k, "")
            if isinstance(v, str) and v.strip():
                return v.strip()
        except Exception:
            pass
    try:
        data = st.session_state.get("structured_cv_json") or {}
        if isinstance(data, dict) and callable(globals().get("build_clean_cv_text_from_structured")):
            txt = build_clean_cv_text_from_structured(data)
            if txt:
                return txt
    except Exception:
        pass
    return ""


def _wz_final_job_context():
    job = st.session_state.get("selected_job") or {}
    if isinstance(job, dict):
        title = job.get("title") or job.get("role") or st.session_state.get("target_role") or "target role"
        company = job.get("company") or job.get("employer") or "selected company"
        desc = job.get("description") or job.get("summary") or ""
    else:
        title = st.session_state.get("target_role") or "target role"
        company = st.session_state.get("selected_company") or "selected company"
        desc = ""
    desc = st.session_state.get("selected_job_description") or st.session_state.get("current_job_description") or st.session_state.get("job_description") or desc
    return str(title or "target role"), str(company or "selected company"), str(desc or "")


def _wz_final_lang_name(value):
    v = str(value or "English").strip()
    if not v or v.lower() == "auto":
        v = str(st.session_state.get("preferred_language") or "English")
    return v


def _wz_final_lang_code(value):
    v = str(value or "english").lower()
    if "german" in v or "deutsch" in v:
        return "german"
    if "hindi" in v:
        return "hindi"
    if "tamil" in v:
        return "tamil"
    if "french" in v:
        return "french"
    if "spanish" in v:
        return "spanish"
    if "dutch" in v:
        return "dutch"
    return "english"


def _wz_final_phrase(key, language, **kwargs):
    lang = _wz_final_lang_code(language)
    bank = {
        "intro": {
            "english": "Hi, let’s begin. Walk me through your background and why this role fits your experience.",
            "german": "Hallo, dann beginnen wir. Führen Sie mich kurz durch Ihren Hintergrund und warum diese Rolle zu Ihrer Erfahrung passt.",
            "hindi": "चलिए शुरू करते हैं। अपने background और इस role के लिए आप क्यों fit हैं, briefly बताइए.",
            "tamil": "சரி, ஆரம்பிப்போம். உங்கள் background மற்றும் இந்த role உங்களுக்கு ஏன் பொருத்தம் என்பதைச் சொல்லுங்கள்.",
            "french": "Commençons. Présentez votre parcours et expliquez pourquoi ce poste correspond à votre expérience.",
            "spanish": "Empecemos. Cuéntame tu trayectoria y por qué este puesto encaja con tu experiencia.",
            "dutch": "Laten we beginnen. Vertel kort over je achtergrond en waarom deze rol bij je ervaring past.",
        },
        "timer_interrupt": {
            "english": "Hmm, I’ll stop you there. In a real interview, I need a sharper answer. Give me the result first, then one example.",
            "german": "Hm, ich stoppe Sie hier kurz. In einem echten Interview brauche ich eine klarere Antwort. Nennen Sie zuerst das Ergebnis, dann ein Beispiel.",
            "hindi": "Hmm, मैं आपको यहीं रोकता हूँ। Real interview में answer sharper चाहिए. पहले result बताइए, फिर एक example.",
            "tamil": "Hmm, இங்கே நிறுத்துகிறேன். Real interview-ல் answer இன்னும் sharp ஆக வேண்டும். முதலில் result, பிறகு example சொல்லுங்கள்.",
            "french": "Hmm, je vous arrête ici. Dans un vrai entretien, il faut une réponse plus directe. Donnez d’abord le résultat, puis un exemple.",
            "spanish": "Hmm, te interrumpo aquí. En una entrevista real necesito una respuesta más clara. Primero el resultado, luego un ejemplo.",
            "dutch": "Hmm, ik stop je hier even. In een echt interview heb ik een scherper antwoord nodig. Eerst het resultaat, dan een voorbeeld.",
        },
        "too_short": {
            "english": "Okay, that’s too short. Give me one concrete example from your CV.",
            "german": "Okay, das ist zu kurz. Geben Sie mir ein konkretes Beispiel aus Ihrem Lebenslauf.",
            "hindi": "Okay, यह बहुत short है. अपने CV से एक concrete example बताइए.",
            "tamil": "Okay, இது மிகவும் short. உங்கள் CV-லிருந்து ஒரு concrete example சொல்லுங்கள்.",
        },
        "missing_impact": {
            "english": "Interesting, but I’m missing the impact. What changed because of your work?",
            "german": "Interessant, aber mir fehlt die Wirkung. Was hat sich durch Ihre Arbeit verändert?",
            "hindi": "Interesting, लेकिन impact missing है. आपके काम से क्या change हुआ?",
            "tamil": "Interesting, ஆனால் impact missing. உங்கள் workனால் என்ன change ஆனது?",
        },
    }
    val = (bank.get(key, {}).get(lang) or bank.get(key, {}).get("english") or "")
    try:
        return val.format(**kwargs)
    except Exception:
        return val


def _wz_final_keywords(text):
    text_l = str(text or "").lower()
    words = ["python", "sql", "tableau", "power bi", "excel", "customer support", "technical support", "data analysis", "dashboard", "reporting", "crm", "api", "cloud", "aws", "gcp", "communication", "troubleshooting", "stakeholder", "service desk", "project"]
    out = []
    for w in words:
        if w in text_l and w not in out:
            out.append(w)
    return out[:6]


def _wz_final_questions(cv_text, jd, role, language):
    skills = _wz_final_keywords(cv_text + "\n" + jd)
    skill_text = ", ".join(skills[:3]) if skills else "your strongest experience"
    lang = _wz_final_lang_code(language)
    if lang == "german":
        return [
            _wz_final_phrase("intro", language),
            f"Ich sehe in Ihrem Profil {skill_text}. Erzählen Sie mir ein konkretes Beispiel, das zu {role} passt.",
            "Welche Leistung aus Ihrem Lebenslauf zeigt am besten, dass Sie in dieser Rolle erfolgreich sein können?",
            "Ich sehe eine mögliche Lücke zur Stellenbeschreibung. Wie würden Sie diese schnell schließen?",
            "Beschreiben Sie eine schwierige Arbeitssituation mit STAR: Situation, Aufgabe, Aktion, Ergebnis.",
            "Warum sollte ich Sie in die nächste Runde einladen? Antworten Sie bitte konkret und kurz.",
        ]
    if lang == "hindi":
        return [
            _wz_final_phrase("intro", language),
            f"आपके profile में {skill_text} दिख रहा है. {role} के लिए इसका एक concrete example बताइए.",
            "आपके CV की कौनसी achievement सबसे ज्यादा proof देती है कि आप इस role में perform करेंगे?",
            "Job description के comparison में आपका biggest gap क्या है और आप उसे कैसे close करेंगे?",
            "अपने काम से एक difficult situation बताइए using STAR: Situation, Task, Action, Result.",
            "मैं आपको next round में क्यों भेजूं? Short और specific answer दीजिए.",
        ]
    if lang == "tamil":
        return [
            _wz_final_phrase("intro", language),
            f"உங்கள் profile-ல் {skill_text} தெரிகிறது. {role} role-க்கு பொருந்தும் ஒரு concrete example சொல்லுங்கள்.",
            "உங்கள் CV-ல் எந்த achievement இந்த role-ல் நீங்கள் perform செய்வீர்கள் என்பதை prove செய்கிறது?",
            "Job description-ஐ compare செய்தால் உங்கள் biggest gap என்ன? அதை எப்படி close செய்வீர்கள்?",
            "உங்கள் வேலை அனுபவத்தில் ஒரு difficult situation-ஐ STAR format-ல் சொல்லுங்கள்.",
            "நான் உங்களை next round-க்கு ஏன் move செய்ய வேண்டும்? Short and specific answer சொல்லுங்கள்.",
        ]
    return [
        _wz_final_phrase("intro", language),
        f"I see {skill_text} in your CV. Give me one specific example that proves you can do this {role} role.",
        "Which achievement from your CV is the strongest proof that you can succeed in this job?",
        "Compared with this job description, what is your biggest gap and how will you close it quickly?",
        "Tell me about a difficult work situation using STAR: situation, task, action, result.",
        "If I had to decide today, why should I move you to the next round? Keep it specific.",
    ]


def _wz_final_answer_scores(answer, question, cv_text, jd):
    answer_l = str(answer or "").lower()
    words = len(str(answer or "").split())
    cv_keys = _wz_final_keywords(cv_text)
    jd_keys = _wz_final_keywords(jd)
    relevance = 35 + min(35, sum(8 for k in jd_keys if k in answer_l))
    clarity = 30 + min(40, words) if words < 70 else 75
    impact_terms = ["improved", "reduced", "increased", "resolved", "%", "users", "customers", "tickets", "hours", "days", "faster", "saved"]
    impact = 30 + min(50, sum(10 for t in impact_terms if t in answer_l))
    confidence = 45 if words >= 25 else 25
    overall = int((min(100, clarity) + min(100, relevance) + min(100, impact) + min(100, confidence)) / 4)
    return {"clarity": min(100, clarity), "relevance": min(100, relevance), "impact": min(100, impact), "confidence": min(100, confidence), "overall": overall, "words": words}


def _wz_final_reaction(answer, language, scores):
    if scores["words"] < 22:
        return _wz_final_phrase("too_short", language), True
    if scores["impact"] < 45:
        return _wz_final_phrase("missing_impact", language), True
    if scores["overall"] >= 75:
        lang = _wz_final_lang_code(language)
        if lang == "german": return "Gut, das ist konkret. Ich frage trotzdem nach dem messbaren Ergebnis.", False
        if lang == "hindi": return "Good, यह answer clear है. अब मैं measurable result पर थोड़ा और पूछूंगा.", False
        if lang == "tamil": return "Good, answer clear. இப்போது measurable result பற்றி கொஞ்சம் கேட்கிறேன்.", False
        return "Good, that’s clear. I’m going to push a bit more on measurable impact.", False
    return _wz_final_phrase("missing_impact", language), True


def _wz_final_improved_answer(answer, role, language):
    lang = _wz_final_lang_code(language)
    if lang == "german":
        return f"Eine stärkere Antwort wäre: In meiner bisherigen Erfahrung habe ich relevante Aufgaben für {role} übernommen, indem ich ein konkretes Problem analysiert, die passende Aktion umgesetzt und das Ergebnis messbar gemacht habe. Zum Beispiel würde ich den Kontext, meine Aufgabe, die konkrete Handlung und das Ergebnis klar in 45 Sekunden erklären."
    if lang == "hindi":
        return f"बेहतर answer: मेरी previous experience में मैंने {role} से related काम किया, जहाँ मैंने problem समझी, action लिया और result measure किया. मैं इसे STAR format में बोलूंगा: situation, task, action, result."
    if lang == "tamil":
        return f"Better answer: என் previous experience-ல் {role} role-க்கு relevant work செய்தேன். Problem-ஐ analyze செய்து, action எடுத்தேன், result-ஐ measurable ஆக explain செய்வேன். STAR format: situation, task, action, result."
    return f"A stronger answer would be: In my previous experience, I handled responsibilities relevant to {role} by identifying the problem, taking a specific action, and measuring the result. For example, I would explain the situation, my task, the action I took, and the outcome in a concise STAR structure."


def render_real_interview_simulation():
    try:
        st.markdown("""
        <style>
        .wz-call-wrap {max-width:1180px;margin:0 auto;padding:.25rem 0 2rem;}
        .wz-call-hero {border:1px solid rgba(34,211,238,.28);background:linear-gradient(135deg,rgba(8,47,73,.86),rgba(15,23,42,.96));border-radius:28px;padding:1.3rem 1.5rem;margin:.5rem 0 1rem;}
        .wz-call-title {font-size:clamp(2rem,4vw,3.4rem);font-weight:950;color:#fff;letter-spacing:-.05em;margin:0;}
        .wz-call-sub {color:#bae6fd;font-size:1.04rem;margin-top:.45rem;}
        .wz-interviewer {border:1px solid rgba(148,163,184,.24);background:rgba(2,6,23,.35);border-radius:26px;padding:1.2rem;margin:1rem 0;}
        .wz-interviewer small {color:#67e8f9;text-transform:uppercase;letter-spacing:.12em;font-weight:900;}
        .wz-question {font-size:1.45rem;line-height:1.35;font-weight:850;color:#fff;margin-top:.5rem;}
        .wz-reaction {border-left:4px solid #22d3ee;background:rgba(8,145,178,.12);padding:.85rem 1rem;border-radius:14px;color:#e0f2fe;margin:.8rem 0;}
        .wz-pressure {border:1px solid rgba(248,113,113,.3);background:rgba(127,29,29,.18);padding:.8rem 1rem;border-radius:16px;color:#fee2e2;margin:.75rem 0;}
        </style>
        <div class="wz-call-wrap">
        """, unsafe_allow_html=True)

        cv_text = _wz_final_cv_context()
        role, company, jd = _wz_final_job_context()
        preferred = st.session_state.get("preferred_language", "English")
        jd_l = str(jd or "").lower()
        requires_german = any(x in jd_l for x in ["german", "deutsch", " b2", " c1", "b2 ", "c1 "])
        auto_lang = "German" if requires_german else preferred

        st.markdown(f"""
        <section class="wz-call-hero">
          <div style="display:flex;justify-content:space-between;gap:1rem;align-items:flex-start;flex-wrap:wrap;">
            <div>
              <div style="color:#67e8f9;text-transform:uppercase;letter-spacing:.14em;font-weight:900;font-size:.8rem;">Real Interview AI</div>
              <h1 class="wz-call-title">Recruiter call mode</h1>
              <div class="wz-call-sub">Based on your CV and {html.escape(role)}{(' @ ' + html.escape(company)) if company and company != 'selected company' else ''}.</div>
            </div>
            <div style="display:flex;gap:.55rem;flex-wrap:wrap;">
              <span style="border:1px solid rgba(148,163,184,.3);border-radius:999px;padding:.5rem .75rem;color:#dbeafe;font-weight:800;">CV: {'Ready' if cv_text else 'Missing'}</span>
              <span style="border:1px solid rgba(148,163,184,.3);border-radius:999px;padding:.5rem .75rem;color:#dbeafe;font-weight:800;">Pressure: On</span>
            </div>
          </div>
        </section>
        """, unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        with c1:
            lang_choice = st.selectbox("Interview language", ["Auto", "English", "German", "Hindi", "Tamil", "French", "Spanish", "Dutch"], index=0, key="wz_final_interview_language_choice")
        with c2:
            answer_lang = st.selectbox("You may answer in", ["Same as interview", "English", "German", "Hindi", "Tamil", "Mixed / bilingual"], index=0, key="wz_final_answer_language_choice")
        with c3:
            pressure = st.selectbox("Pressure level", ["Realistic", "Friendly", "Strict"], index=0, key="wz_final_pressure_choice")

        interview_language = auto_lang if lang_choice == "Auto" else lang_choice
        st.session_state["wz_ri_interview_language"] = interview_language
        st.session_state["interview_language"] = interview_language
        st.caption(f"Interviewer will speak in: {interview_language}. You can answer in: {answer_lang}.")

        if not cv_text:
            st.warning("Upload or create your CV first. The interview must be based on your CV, not generic questions.")
            return

        if "wz_final_questions" not in st.session_state or st.session_state.get("wz_final_questions_lang") != interview_language:
            st.session_state["wz_final_questions"] = _wz_final_questions(cv_text, jd, role, interview_language)
            st.session_state["wz_final_questions_lang"] = interview_language
            st.session_state["wz_final_q_index"] = 0
            st.session_state["wz_final_answers"] = []
            st.session_state["wz_final_answer_start"] = time.time()

        q_index = int(st.session_state.get("wz_final_q_index", 0))
        questions = st.session_state.get("wz_final_questions", []) or _wz_final_questions(cv_text, jd, role, interview_language)

        if q_index >= len(questions):
            answers = st.session_state.get("wz_final_answers", []) or []
            avg = int(sum(a.get("scores", {}).get("overall", 0) for a in answers) / max(1, len(answers)))
            decision = "Pass" if avg >= 78 else "Borderline" if avg >= 58 else "Not ready"
            st.markdown("### Interview result")
            st.metric("Hiring decision", decision)
            st.metric("Score", f"{avg}/100")
            st.markdown("**Top 3 mistakes to fix:**")
            st.markdown("- Add measurable impact\n- Use STAR structure\n- Connect each answer back to the target job")
            if answers:
                weakest = sorted(answers, key=lambda x: x.get("scores", {}).get("overall", 0))[0]
                st.markdown("**Improved version for weakest answer:**")
                st.info(_wz_final_improved_answer(weakest.get("answer", ""), role, interview_language))
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Practice Again", type="primary", use_container_width=True, key="wz_final_practice_again"):
                    st.session_state["wz_final_q_index"] = 0
                    st.session_state["wz_final_answers"] = []
                    st.session_state["wz_final_answer_start"] = time.time()
                    st.rerun()
            with c2:
                if st.button("Improve My Answers", use_container_width=True, key="wz_final_improve_answers"):
                    st.session_state["nav_page"] = "document_tools"
                    st.session_state["page"] = "document_tools"
                    st.rerun()
            return

        question = questions[q_index]
        st.markdown(f"""
        <div class="wz-interviewer">
          <small>Interviewer · Question {q_index + 1} of {len(questions)}</small>
          <div class="wz-question">{html.escape(question)}</div>
        </div>
        """, unsafe_allow_html=True)

        limit = 60 if pressure == "Realistic" else 45 if pressure == "Strict" else 90
        start = float(st.session_state.get("wz_final_answer_start", time.time()))
        elapsed = int(time.time() - start)
        remain = max(0, limit - elapsed)
        st.progress(min(1.0, elapsed / max(1, limit)))
        if remain > 0:
            st.caption(f"⏱ {remain}s left — answer like this is a live recruiter screen.")
        else:
            st.markdown(f"<div class='wz-pressure'><b>Interviewer:</b> {html.escape(_wz_final_phrase('timer_interrupt', interview_language))}</div>", unsafe_allow_html=True)

        answer = st.text_area("Your answer", key=f"wz_final_answer_{q_index}", height=150, placeholder="Speak or type your answer here...")
        if answer:
            scores_live = _wz_final_answer_scores(answer, question, cv_text, jd)
            st.markdown("**Live feedback meter**")
            m1,m2,m3,m4 = st.columns(4)
            m1.metric("Clarity", f"{scores_live['clarity']}%")
            m2.metric("Relevance", f"{scores_live['relevance']}%")
            m3.metric("Impact", f"{scores_live['impact']}%")
            m4.metric("Confidence", f"{scores_live['confidence']}%")

        c1, c2, c3 = st.columns([1,1,1])
        with c1:
            submit = st.button("Answer", type="primary", use_container_width=True, key=f"wz_final_submit_{q_index}")
        with c2:
            again = st.button("Answer again", use_container_width=True, key=f"wz_final_again_{q_index}")
        with c3:
            skip = st.button("Skip question", use_container_width=True, key=f"wz_final_skip_{q_index}")

        if again:
            st.session_state["wz_final_answer_start"] = time.time()
            st.rerun()
        if skip:
            st.session_state["wz_final_q_index"] = q_index + 1
            st.session_state["wz_final_answer_start"] = time.time()
            st.rerun()
        if submit:
            if not str(answer or "").strip():
                st.warning("Please answer first.")
            else:
                scores = _wz_final_answer_scores(answer, question, cv_text, jd)
                reaction, needs_followup = _wz_final_reaction(answer, interview_language, scores)
                st.session_state.setdefault("wz_final_answers", []).append({"question": question, "answer": answer, "scores": scores, "reaction": reaction})
                st.markdown(f"<div class='wz-reaction'><b>Interviewer:</b> {html.escape(reaction)}</div>", unsafe_allow_html=True)
                if needs_followup:
                    st.session_state["wz_final_questions"].insert(q_index + 1, reaction)
                st.session_state["wz_final_q_index"] = q_index + 1
                st.session_state["wz_final_answer_start"] = time.time()
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
    except Exception as exc:
        st.error(f"Interview could not load safely: {exc}")

# =========================================================
# WorkZo v160 - One-click realistic recruiter interview
# Purpose:
# - Default interview language is English; it changes only when user selects another language.
# - Start with one button, then run a natural interviewer conversation loop.
# - Opening uses the candidate name extracted from CV/profile.
# - Questions are CV + JD + optional company-link/context based.
# - Reactions/interruptions feel human: hmm, okay, interesting, let me stop you there.
# - No generic hardcoded English after user changes language.
# =========================================================

def _wz160_clean_text(value: str, limit: int = 4000) -> str:
    import re as _re
    text = _re.sub(r"\s+", " ", str(value or "")).strip()
    return text[:limit]


def _wz160_candidate_name(cv_text: str = "") -> str:
    """Best-effort candidate name from structured CV first, then first lines of CV."""
    try:
        data = st.session_state.get("structured_cv_json") or st.session_state.get("workzo_live_cv_structured") or {}
        if isinstance(data, dict):
            for key in ["full_name", "name"]:
                val = str(data.get(key) or "").strip()
                if val and len(val.split()) <= 5:
                    return val
            personal = data.get("personal_info") or data.get("contact") or {}
            if isinstance(personal, dict):
                val = str(personal.get("name") or personal.get("full_name") or "").strip()
                if val and len(val.split()) <= 5:
                    return val
    except Exception:
        pass
    text = str(cv_text or _wz_final_cv_context() or "")
    for raw in text.splitlines()[:8]:
        line = raw.strip(" |\t-")
        if not line or "@" in line or "linkedin" in line.lower() or any(ch.isdigit() for ch in line):
            continue
        words = [w for w in line.split() if w.strip()]
        if 2 <= len(words) <= 5 and all(len(w) > 1 for w in words):
            return " ".join(words)
    return "there"


def _wz160_fetch_company_context(url: str = "", company: str = "") -> str:
    """Fast optional public-page context. Fails safely and never blocks the interview."""
    url = str(url or "").strip()
    company = str(company or "").strip()
    cache_key = "wz160_company_context::" + url + "::" + company
    try:
        if cache_key in st.session_state:
            return st.session_state.get(cache_key, "")
    except Exception:
        pass
    context = ""
    if url:
        try:
            import requests, re as _re
            final_url = url if url.startswith(("http://", "https://")) else "https://" + url
            r = requests.get(final_url, timeout=4, headers={"User-Agent": "WorkZoAI/1.0"})
            if getattr(r, "ok", False):
                text = _re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", " ", r.text, flags=_re.I)
                text = _re.sub(r"<[^>]+>", " ", text)
                text = _re.sub(r"\s+", " ", text).strip()
                context = text[:2200]
        except Exception:
            context = ""
    if not context and company:
        context = f"Company name provided by user: {company}. Do not invent facts. Ask company-aware questions only from the job description, CV, and any provided link context."
    try:
        st.session_state[cache_key] = context
        if context:
            st.session_state["company_context"] = context
    except Exception:
        pass
    return context


def _wz160_phrase(key: str, language: str = "English", **kwargs) -> str:
    lang = _wz_final_lang_code(language)
    bank = {
        "opening": {
            "english": "Hi {name}, good to meet you. How are you today? Great — let's begin. Tell me about yourself and keep it relevant to this role.",
            "german": "Hallo {name}, schön Sie kennenzulernen. Wie geht es Ihnen heute? Gut — dann beginnen wir. Erzählen Sie mir kurz etwas über sich und beziehen Sie es auf diese Rolle.",
            "hindi": "Hi {name}, आपसे मिलकर अच्छा लगा. आप कैसे हैं? Great — चलिए शुरू करते हैं. अपने बारे में बताइए और इसे इस role से connect कीजिए.",
            "tamil": "Hi {name}, உங்களை சந்திப்பதில் மகிழ்ச்சி. எப்படி இருக்கிறீர்கள்? சரி — ஆரம்பிப்போம். உங்களைப் பற்றி சொல்லுங்கள், அதை இந்த role-க்கு connect செய்யுங்கள்.",
            "french": "Bonjour {name}, ravi de vous rencontrer. Comment allez-vous aujourd’hui ? Très bien — commençons. Présentez-vous brièvement en lien avec ce poste.",
            "spanish": "Hola {name}, encantado/a de conocerte. ¿Cómo estás hoy? Bien — empecemos. Háblame de ti y conecta tu experiencia con este puesto.",
            "dutch": "Hallo {name}, fijn je te ontmoeten. Hoe gaat het vandaag? Goed — laten we beginnen. Vertel kort over jezelf en koppel het aan deze functie.",
        },
        "short": {
            "english": "Hmm, that’s a bit too short. Give me one concrete example from your CV — what happened, what you did, and what changed?",
            "german": "Hm, das ist etwas zu kurz. Geben Sie mir ein konkretes Beispiel aus Ihrem Lebenslauf: Was ist passiert, was haben Sie getan, und was hat sich verändert?",
            "hindi": "Hmm, यह थोड़ा short है. अपने CV से एक concrete example दीजिए — क्या हुआ, आपने क्या किया, और क्या बदला?",
            "tamil": "Hmm, இது கொஞ்சம் short. உங்கள் CV-லிருந்து ஒரு concrete example சொல்லுங்கள் — என்ன நடந்தது, நீங்கள் என்ன செய்தீர்கள், என்ன மாறியது?",
        },
        "long": {
            "english": "Let me stop you there — you’re losing the main point. Give me the same answer again in 45 seconds: result first, then one example.",
            "german": "Ich stoppe Sie kurz — der Hauptpunkt geht verloren. Antworten Sie bitte noch einmal in 45 Sekunden: zuerst das Ergebnis, dann ein Beispiel.",
            "hindi": "मैं आपको यहीं रोकता हूँ — main point खो रहा है. यही answer 45 seconds में दीजिए: पहले result, फिर एक example.",
            "tamil": "நான் இங்கே நிறுத்துகிறேன் — main point தெளிவாக இல்லை. 45 seconds-ல் மீண்டும் சொல்லுங்கள்: முதலில் result, பிறகு example.",
        },
        "impact": {
            "english": "Okay, interesting — but I’m missing the impact. What was the measurable result or business outcome?",
            "german": "Okay, interessant — aber mir fehlt die Wirkung. Was war das messbare Ergebnis oder der geschäftliche Nutzen?",
            "hindi": "Okay, interesting — लेकिन impact missing है. measurable result या business outcome क्या था?",
            "tamil": "Okay, interesting — ஆனால் impact missing. measurable result அல்லது business outcome என்ன?",
        },
        "good": {
            "english": "Good, that’s clearer. I’m going to push a little deeper now.",
            "german": "Gut, das ist klarer. Ich werde jetzt etwas tiefer nachfragen.",
            "hindi": "Good, यह clearer है. अब मैं थोड़ा deeper पूछूंगा.",
            "tamil": "Good, இது clear. இப்போது கொஞ்சம் deeper கேட்கிறேன்.",
        },
        "timer": {
            "english": "Hmm, I’ll stop you there. In a real interview I would need a sharper answer now — give me the direct point and one result.",
            "german": "Hm, ich unterbreche Sie kurz. In einem echten Interview brauche ich jetzt eine klarere Antwort — nennen Sie den direkten Punkt und ein Ergebnis.",
            "hindi": "Hmm, मैं आपको रोकता हूँ. Real interview में मुझे अब sharper answer चाहिए — direct point और एक result बताइए.",
            "tamil": "Hmm, நான் இங்கே நிறுத்துகிறேன். Real interview-ல் இப்போது sharper answer வேண்டும் — direct point மற்றும் ஒரு result சொல்லுங்கள்.",
        },
        "finished": {
            "english": "Okay, thanks. I have enough to make a hiring-style decision now.",
            "german": "Okay, danke. Ich habe genug Informationen, um eine realistische Entscheidung zu treffen.",
            "hindi": "Okay, thanks. अब मेरे पास hiring-style decision के लिए enough information है.",
            "tamil": "Okay, thanks. இப்போது hiring-style decision எடுக்க போதுமான information உள்ளது.",
        },
    }
    val = bank.get(key, {}).get(lang) or bank.get(key, {}).get("english") or ""
    try:
        return val.format(**kwargs)
    except Exception:
        return val


def _wz160_company_from_jd(jd: str, company: str = "") -> str:
    if company and company not in ["selected company", "Demo Company"]:
        return company
    import re as _re
    jd = str(jd or "")
    m = _re.search(r"(?:at|company|employer)[:\s]+([A-Z][A-Za-z0-9& .-]{2,50})", jd)
    return (m.group(1).strip() if m else company or "the company")


def _wz160_build_questions(cv_text: str, jd: str, role: str, company: str, company_context: str, language: str) -> list:
    name = _wz160_candidate_name(cv_text)
    opening = _wz160_phrase("opening", language, name=name)
    skills = _wz_final_keywords(cv_text + "\n" + jd + "\n" + company_context)
    skill_text = ", ".join(skills[:3]) if skills else "your most relevant CV experience"
    prompt = f"""
You are a realistic human interviewer. Create a natural interview sequence, not generic questions.

Language for interviewer: {language}
Candidate name: {name}
Role: {role}
Company: {company}
CV:
{cv_text[:7000]}
Job description:
{jd[:7000]}
Company/link context:
{company_context[:2200]}

Create exactly 5 questions AFTER the opening greeting.
Rules:
- Every question must be based on the CV, JD, or company context.
- Ask like a real recruiter/hiring manager, not a textbook.
- Include at least one role-fit question, one CV evidence question, one STAR behavioral question, one gap/risk question, and one hiring-decision question.
- If company context exists, ask one question that connects the candidate to the company/role.
- Keep all interviewer questions in {language}.
- Return only JSON: {{"questions": ["q2", "q3", "q4", "q5", "q6"]}}
"""
    try:
        raw = _wz_ri_ai(prompt, json_mode=True, language=language)
        data = _wz_ri_json(raw, {})
        qs = data.get("questions") if isinstance(data, dict) else None
        if isinstance(qs, list) and len(qs) >= 5:
            return [opening] + [str(q).strip() for q in qs[:5] if str(q).strip()]
    except Exception:
        pass
    lang = _wz_final_lang_code(language)
    if lang == "german":
        fallback = [
            f"Ich sehe {skill_text} in Ihrem Profil. Geben Sie mir ein konkretes Beispiel, das zu {role} passt.",
            f"Was interessiert Sie an {company}, und wie passt Ihre Erfahrung zu dieser Rolle?",
            "Beschreiben Sie eine schwierige Situation aus Ihrer Arbeit im STAR-Format: Situation, Aufgabe, Aktion, Ergebnis.",
            "Welche Anforderung aus dieser Stelle ist aktuell Ihre größte Lücke, und wie würden Sie sie schnell schließen?",
            "Wenn ich heute entscheiden müsste: Warum sollte ich Sie in die nächste Runde einladen?",
        ]
    elif lang == "hindi":
        fallback = [
            f"आपके profile में {skill_text} दिख रहा है. {role} के लिए एक concrete example दीजिए.",
            f"{company} में यह role आपको क्यों interest करता है, और आपकी experience इससे कैसे match होती है?",
            "अपने काम की एक difficult situation STAR format में बताइए: Situation, Task, Action, Result.",
            "इस job description के comparison में आपका biggest gap क्या है, और आप उसे जल्दी कैसे close करेंगे?",
            "अगर मुझे आज decision लेना हो, तो मैं आपको next round में क्यों भेजूं?",
        ]
    elif lang == "tamil":
        fallback = [
            f"உங்கள் profile-ல் {skill_text} தெரிகிறது. {role} role-க்கு ஒரு concrete example சொல்லுங்கள்.",
            f"{company}-இல் இந்த role உங்களுக்கு ஏன் interest? உங்கள் experience எப்படி match ஆகிறது?",
            "உங்கள் work experience-ல் ஒரு difficult situation-ஐ STAR format-ல் சொல்லுங்கள்: Situation, Task, Action, Result.",
            "இந்த job description-ஐ compare செய்தால் உங்கள் biggest gap என்ன? அதை எப்படி விரைவாக close செய்வீர்கள்?",
            "இன்று decision எடுக்க வேண்டுமெனில், உங்களை next round-க்கு ஏன் அனுப்ப வேண்டும்?",
        ]
    else:
        fallback = [
            f"I see {skill_text} in your CV. Give me one specific example that proves you can do this {role} role.",
            f"What interests you about {company}, and how does your experience connect to this role?",
            "Tell me about a difficult work situation using STAR: situation, task, action, result.",
            "Compared with this job description, what is your biggest gap and how would you close it quickly?",
            "If I had to decide today, why should I move you to the next round? Keep it specific.",
        ]
    return [opening] + fallback


def _wz160_reaction(answer: str, question: str, cv_text: str, jd: str, language: str, q_index: int) -> tuple:
    scores = _wz_final_answer_scores(answer, question, cv_text, jd)
    words = int(scores.get("words", 0) or 0)
    answer_l = str(answer or "").lower()
    has_metric = any(x in answer_l for x in ["%", "improved", "reduced", "increased", "resolved", "saved", "customers", "tickets", "users", "revenue", "time"])
    if words < 24:
        return _wz160_phrase("short", language), True, scores
    if words > 180:
        return _wz160_phrase("long", language), True, scores
    if not has_metric and q_index > 0:
        return _wz160_phrase("impact", language), True, scores
    # occasional human filler to keep it alive
    fillers = {
        "english": ["Hmm, okay.", "Good, interesting.", "Right, I see."],
        "german": ["Hm, okay.", "Gut, interessant.", "Verstehe."],
        "hindi": ["Hmm, okay.", "Good, interesting.", "ठीक है, समझा."],
        "tamil": ["Hmm, okay.", "Good, interesting.", "சரி, புரிகிறது."],
    }
    lang = _wz_final_lang_code(language)
    prefix = fillers.get(lang, fillers["english"])[q_index % 3]
    return f"{prefix} {_wz160_phrase('good', language)}", False, scores


def _wz160_finish_report(cv_text: str, jd: str, role: str, company: str, answers: list, language: str) -> dict:
    if not answers:
        return {"overall_score": 0, "hiring_decision": "Not ready", "hiring_reason": "No answers were submitted.", "top_3_mistakes": ["No interview answers submitted"], "strengths": [], "next_action": "Start the interview and answer at least 3 questions."}
    avg = int(sum((a.get("scores") or {}).get("overall", 0) for a in answers) / max(1, len(answers)))
    decision = "Pass to next round" if avg >= 80 else "Borderline" if avg >= 60 else "Not ready"
    prompt = f"""
Act as a strict hiring manager. Create final interview feedback in {language}.
CV:
{cv_text[:5000]}
JD:
{jd[:5000]}
Role: {role}
Company: {company}
Answers and scores:
{json.dumps(answers, ensure_ascii=False)}
Return JSON with: overall_score, hiring_decision, hiring_reason, strengths(list), top_3_mistakes(list), improved_answer, next_action.
Do not invent achievements.
"""
    try:
        raw = _wz_ri_ai(prompt, json_mode=True, language=language)
        data = _wz_ri_json(raw, {})
        if isinstance(data, dict) and data:
            data.setdefault("overall_score", avg)
            data.setdefault("hiring_decision", decision)
            return data
    except Exception:
        pass
    return {
        "overall_score": avg,
        "hiring_decision": decision,
        "hiring_reason": "Your answers were evaluated for relevance, clarity, impact, confidence, and job fit.",
        "strengths": ["You gave relevant career context", "You completed the interview flow"],
        "top_3_mistakes": ["Add measurable impact", "Use STAR structure", "Connect each answer to the target job"],
        "improved_answer": _wz_final_improved_answer(answers[0].get("answer", ""), role, language),
        "next_action": "Practice again and improve the weakest answer with a concrete result.",
    }


def render_real_interview_simulation():
    """One-click realistic text interview with human-like interruptions and CV/job/company context."""
    try:
        st.markdown("""
        <style>
        .wz160-wrap{max-width:1120px;margin:0 auto;padding:.4rem 0 2rem;}
        .wz160-hero{border:1px solid rgba(34,211,238,.28);background:linear-gradient(135deg,rgba(8,47,73,.9),rgba(15,23,42,.96));border-radius:28px;padding:1.25rem 1.45rem;margin:.4rem 0 1rem;}
        .wz160-title{font-size:clamp(2rem,4vw,3.25rem);font-weight:950;color:white;letter-spacing:-.05em;margin:.2rem 0 .4rem;}
        .wz160-sub{color:#bae6fd;font-size:1.05rem;line-height:1.45;}
        .wz160-card{border:1px solid rgba(148,163,184,.22);background:rgba(2,6,23,.36);border-radius:24px;padding:1.05rem;margin:.8rem 0;}
        .wz160-label{color:#67e8f9;text-transform:uppercase;letter-spacing:.14em;font-weight:900;font-size:.78rem;margin-bottom:.45rem;}
        .wz160-question{font-size:1.42rem;line-height:1.36;font-weight:850;color:#fff;}
        .wz160-reaction{border-left:4px solid #22d3ee;background:rgba(8,145,178,.13);padding:.85rem 1rem;border-radius:14px;color:#e0f2fe;margin:.8rem 0;}
        .wz160-interrupt{border:1px solid rgba(248,113,113,.35);background:rgba(127,29,29,.18);padding:.85rem 1rem;border-radius:16px;color:#fee2e2;margin:.75rem 0;}
        .wz160-chip{display:inline-flex;border:1px solid rgba(148,163,184,.3);border-radius:999px;padding:.45rem .72rem;color:#dbeafe;font-weight:800;margin-right:.4rem;margin-top:.35rem;}
        </style>
        <div class="wz160-wrap">
        """, unsafe_allow_html=True)

        cv_text = _wz_final_cv_context()
        role, company, jd = _wz_final_job_context()
        name = _wz160_candidate_name(cv_text)
        company = _wz160_company_from_jd(jd, company)

        if not cv_text:
            st.warning("Upload or create your CV first. The interview must be based on your CV, not generic questions.")
            return

        # Defaults: English unless user explicitly changes it.
        lang_options = ["English", "German", "Hindi", "Tamil", "French", "Spanish", "Dutch"]
        if "wz160_language" not in st.session_state:
            st.session_state["wz160_language"] = "English"
        if "wz160_answer_language" not in st.session_state:
            st.session_state["wz160_answer_language"] = "Same as interview"
        if "wz160_pressure" not in st.session_state:
            st.session_state["wz160_pressure"] = "Realistic"

        st.markdown(f"""
        <section class="wz160-hero">
          <div class="wz160-label">Real Interview AI</div>
          <div class="wz160-title">Recruiter call mode</div>
          <div class="wz160-sub">Based on your CV and {html.escape(str(role or 'target role'))}{(' @ ' + html.escape(str(company))) if company else ''}. One click starts a realistic interview loop.</div>
          <div style="margin-top:.65rem;"><span class="wz160-chip">CV: Ready</span><span class="wz160-chip">Candidate: {html.escape(name)}</span><span class="wz160-chip">Pressure: On</span></div>
        </section>
        """, unsafe_allow_html=True)

        started = bool(st.session_state.get("wz160_started"))
        if not started:
            with st.expander("Optional setup", expanded=False):
                c1, c2, c3 = st.columns(3)
                with c1:
                    language = st.selectbox("Interview language", lang_options, index=lang_options.index(st.session_state.get("wz160_language", "English")) if st.session_state.get("wz160_language", "English") in lang_options else 0, key="wz160_language")
                with c2:
                    st.selectbox("You may answer in", ["Same as interview", "English", "German", "Hindi", "Tamil", "Mixed / bilingual"], key="wz160_answer_language")
                with c3:
                    st.selectbox("Pressure level", ["Friendly", "Realistic", "Strict"], index=1, key="wz160_pressure")
                company_link = st.text_input("Company / opening link (optional)", key="wz160_company_link", placeholder="Paste company careers page or job opening link")
                if company_link:
                    st.caption("WorkZo will use whatever reliable text it can read from the link. If the link cannot be read, paste the JD/company notes in Job Match.")

            if st.button("🎤 Start Interview", type="primary", use_container_width=True, key="wz160_start"):
                language = st.session_state.get("wz160_language", "English") or "English"
                link = st.session_state.get("wz160_company_link", "")
                company_context = _wz160_fetch_company_context(link, company)
                with st.spinner("Interviewer is reading your CV, job, and company context..."):
                    questions = _wz160_build_questions(cv_text, jd, role, company, company_context, language)
                st.session_state["wz160_questions"] = questions
                st.session_state["wz160_q_index"] = 0
                st.session_state["wz160_answers"] = []
                st.session_state["wz160_started"] = True
                st.session_state["wz160_finished"] = False
                st.session_state["wz160_company_context"] = company_context
                st.session_state["wz160_answer_started_at"] = time.time()
                try:
                    track_event("interview_started", "Interview", {"language": language, "role": role, "company": company})
                except Exception:
                    pass
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
            return

        language = st.session_state.get("wz160_language", "English") or "English"
        pressure = st.session_state.get("wz160_pressure", "Realistic") or "Realistic"
        questions = st.session_state.get("wz160_questions", []) or _wz160_build_questions(cv_text, jd, role, company, st.session_state.get("wz160_company_context", ""), language)
        idx = int(st.session_state.get("wz160_q_index", 0) or 0)
        answers = st.session_state.get("wz160_answers", []) or []

        if st.session_state.get("wz160_finished") or idx >= len(questions):
            result = _wz160_finish_report(cv_text, jd, role, company, answers, language)
            score = int(result.get("overall_score", 0) or 0)
            decision = str(result.get("hiring_decision", "Borderline"))
            st.markdown("## Interview Result")
            if score >= 80:
                st.success(f"✅ {decision}")
            elif score >= 60:
                st.warning(f"⚠️ {decision}")
            else:
                st.error(f"❌ {decision}")
            st.metric("Score", f"{score}/100")
            st.caption(str(result.get("hiring_reason", "Based on your CV, job fit, and answers.")))
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### Strengths")
                for item in _as_list(result.get("strengths"))[:3]:
                    st.markdown(f"- {item}")
            with col2:
                st.markdown("### Top mistakes")
                for item in _as_list(result.get("top_3_mistakes"))[:3]:
                    st.markdown(f"- {item}")
            with st.expander("Improved answer", expanded=True):
                st.write(result.get("improved_answer") or _wz_final_improved_answer(answers[0].get("answer", "") if answers else "", role, language))
            st.success(str(result.get("next_action", "Practice again with stronger examples.")))
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Practice Again", type="primary", use_container_width=True, key="wz160_again"):
                    st.session_state["wz160_q_index"] = 0
                    st.session_state["wz160_answers"] = []
                    st.session_state["wz160_finished"] = False
                    st.session_state["wz160_answer_started_at"] = time.time()
                    st.rerun()
            with c2:
                if st.button("Reset Interview", use_container_width=True, key="wz160_reset"):
                    for k in ["wz160_started", "wz160_finished", "wz160_questions", "wz160_q_index", "wz160_answers", "wz160_answer_started_at"]:
                        st.session_state.pop(k, None)
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
            return

        question = questions[idx]
        st.markdown(f"""
        <div class="wz160-card">
          <div class="wz160-label">Interviewer · Question {idx + 1} of {len(questions)}</div>
          <div class="wz160-question">{html.escape(str(question))}</div>
        </div>
        """, unsafe_allow_html=True)
        try:
            _wz_ri_auto_speak(question, f"wz160_q_{idx}_{language}")
        except Exception:
            pass

        limit = {"Friendly": 100, "Realistic": 70, "Strict": 45}.get(pressure, 70)
        start = float(st.session_state.get("wz160_answer_started_at", time.time()))
        elapsed = int(time.time() - start)
        remain = max(0, limit - elapsed)
        st.progress(min(1.0, elapsed / max(1, limit)))
        if remain > 0:
            st.caption(f"⏱ {remain}s left — answer naturally, like a real recruiter screen.")
        else:
            st.markdown(f"<div class='wz160-interrupt'><b>Interviewer:</b> {html.escape(_wz160_phrase('timer', language))}</div>", unsafe_allow_html=True)

        key = f"wz160_answer_box_{idx}"
        answer = st.text_area("Your answer", key=key, height=150, placeholder="Type your answer here. You may answer in your selected answer language.")
        if answer:
            live = _wz_final_answer_scores(answer, question, cv_text, jd)
            st.markdown("**Live feedback meter**")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Clarity", f"{live['clarity']}%")
            m2.metric("Relevance", f"{live['relevance']}%")
            m3.metric("Impact", f"{live['impact']}%")
            m4.metric("Confidence", f"{live['confidence']}%")

        c1, c2, c3 = st.columns([1.2, 1, 1])
        with c1:
            submit = st.button("Submit answer", type="primary", use_container_width=True, key=f"wz160_submit_{idx}")
        with c2:
            repeat = st.button("Answer again", use_container_width=True, key=f"wz160_repeat_{idx}")
        with c3:
            end_now = st.button("End interview", use_container_width=True, key=f"wz160_end_{idx}")

        if repeat:
            st.session_state["wz160_answer_started_at"] = time.time()
            st.rerun()
        if end_now:
            st.session_state["wz160_finished"] = True
            st.rerun()
        if submit:
            if not str(answer or "").strip():
                st.warning("Please answer first.")
            else:
                reaction, followup, scores = _wz160_reaction(answer, question, cv_text, jd, language, idx)
                answers.append({"question": question, "answer": answer, "reaction": reaction, "scores": scores})
                st.session_state["wz160_answers"] = answers
                st.markdown(f"<div class='wz160-reaction'><b>Interviewer:</b> {html.escape(str(reaction))}</div>", unsafe_allow_html=True)
                if followup and idx < len(questions) - 1:
                    # Realistic interruption: replace the next question with an immediate follow-up.
                    questions[idx + 1] = str(reaction)
                    st.session_state["wz160_questions"] = questions
                st.session_state["wz160_q_index"] = idx + 1
                st.session_state["wz160_answer_started_at"] = time.time()
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    except Exception as exc:
        st.error(f"Interview could not load safely: {exc}")


# =========================================================
# WorkZo Voice-first recruiter interview override
# Added to make the interview feel like a real recruiter call.
# This overrides earlier render_real_interview_simulation and final-score UI only.
# =========================================================

def _wz_voice_first_safe_name() -> str:
    try:
        name = _wz_ri_get_candidate_name()
    except Exception:
        name = ""
    name = str(name or "").strip()
    if not name or name.lower() in {"candidate", "your name", "unknown"}:
        return "there"
    # Avoid shouting all-caps names extracted from PDFs.
    return " ".join([p.capitalize() if p.isupper() else p for p in name.split()[:3]])


def _wz_voice_first_normalize_decision(decision: str, score: int) -> str:
    decision_l = str(decision or "").strip().lower()
    if decision_l in {"no", "reject", "rejected", "fail", "not selected"} or score < 60:
        return "Not ready yet — but close"
    if decision_l in {"yes", "pass", "hire", "selected"} or score >= 80:
        return "Ready to pass this round"
    return "Borderline — needs one more practice round"


def _wz_voice_first_reaction_phrase(answer: str, idx: int) -> str:
    words = len(str(answer or "").split())
    if words < 25:
        return "Hmm… let me stop you there. That was too short for a real interview. Give me one concrete example next."
    if words > 180:
        return "Okay, I’ll pause you there. You’re giving too much detail — keep it tighter and focus on the result."
    phrases = [
        "Hmm, interesting. I like the direction, but I need a clearer result.",
        "Okay, good. Now connect that more directly to this job.",
        "That’s useful context. I’m going to push you for a more specific example.",
        "Good start. What I’m missing is the measurable impact.",
    ]
    return phrases[idx % len(phrases)]


def _wz_voice_first_company_bits(company: str = "", website: str = "") -> str:
    try:
        ctx = _wz_ri_company_context(company, website)
    except Exception:
        ctx = ""
    return str(ctx or "")[:1200]


def _wz_voice_first_build_opening_question(cv_text: str, jd: str, role: str, company: str, language: str) -> str:
    name = _wz_voice_first_safe_name()
    role_txt = role or "this role"
    company_txt = f" at {company}" if company else ""
    # Default English. Only change if user explicitly selected a different interview language.
    if str(language).lower().startswith("german"):
        return f"Hallo {name}, schön Sie kennenzulernen. Wie geht es Ihnen heute? Gut, dann beginnen wir. Erzählen Sie mir bitte kurz von sich und warum Sie zu {role_txt}{company_txt} passen."
    if str(language).lower().startswith("hindi"):
        return f"Hi {name}, aapse milkar achha laga. Kaise hain aap? Chaliye shuru karte hain. Apne baare mein batayein aur batayein ki aap {role_txt}{company_txt} ke liye kyon fit hain."
    if str(language).lower().startswith("tamil"):
        return f"Hi {name}, ungaḷai sandhiththathil magizhchi. Eppadi irukkeenga? Seri, interview start pannalaam. Ungala patri sollunga, {role_txt}{company_txt} role-ku neenga epdi fit nu explain pannunga."
    return f"Hi {name}, good to meet you. How are you today? Great — let’s begin. Tell me about yourself and keep it relevant to {role_txt}{company_txt}."


def _wz_voice_first_next_question(cv_text: str, jd: str, role: str, company: str, language: str, answers: list, idx: int) -> str:
    # Use existing AI question builder when available, but make the first question human.
    if idx == 0:
        return _wz_voice_first_build_opening_question(cv_text, jd, role, company, language)
    try:
        company_context = _wz_voice_first_company_bits(company, st.session_state.get("wz_ri_company_website", ""))
        qs = _wz_ri_build_questions(cv_text, jd, company, role, st.session_state.get("wz_ri_company_website", ""), company_context, language, "Human recruiter")
        if isinstance(qs, list) and len(qs) > idx:
            return str(qs[idx])
    except Exception:
        pass
    fallback = [
        f"Walk me through one specific example from your CV that proves you can succeed in {role or 'this role'}.",
        "Tell me about a difficult situation with a customer or stakeholder. What did you do, and what changed because of your action?",
        "What is one skill gap you may have for this job, and how would you handle it honestly?",
        f"Why should {company or 'this company'} choose you over another candidate? Give me evidence from your experience.",
        "Before we finish, what is one achievement from your background that you want me to remember?",
    ]
    return fallback[min(idx - 1, len(fallback) - 1)]


def _wz_voice_first_score_answers(cv_text: str, jd: str, role: str, company: str, answers: list, language: str) -> dict:
    try:
        return _wz_ri_score_interview(cv_text, jd, company, role, st.session_state.get("wz_ri_company_website", ""), answers, language)
    except Exception:
        # deterministic fallback, less harsh and more useful than “No”.
        total_words = sum(len(str(a.get("answer", "")).split()) for a in answers if isinstance(a, dict))
        avg = total_words / max(1, len(answers))
        score = 50
        if avg >= 50:
            score += 15
        if avg >= 90:
            score += 10
        if any(any(ch.isdigit() for ch in str(a.get("answer", ""))) for a in answers if isinstance(a, dict)):
            score += 10
        score = max(35, min(88, score))
        return {
            "overall_score": score,
            "target_score": 80,
            "hiring_decision": _wz_voice_first_normalize_decision("", score),
            "hiring_reason": "Based on your spoken answers, CV relevance, structure, and evidence for the target role.",
            "strengths": ["You completed the interview flow", "Your answers showed relevant background", "You communicated your experience clearly in parts"],
            "what_hurt_you_most": ["Some answers need stronger measurable impact", "Examples should connect more directly to the job", "Use STAR structure more consistently"],
            "top_mistakes": ["Not enough measurable results", "Some answers were too general", "Job-specific connection could be stronger"],
            "weakest_answer_question_number": 1,
            "improved_version_of_weakest_answer": "Use STAR: briefly state the situation, explain your task, describe your action, and finish with a truthful result that connects to the job.",
            "next_action": "Practice again and add one measurable result to each answer.",
        }


def _wz_ri_render_final_score(result: dict, company: str = "", role: str = "", website: str = "", language: str = "English"):
    st.markdown("## Interview result")
    current = int(result.get("overall_score", 0) or 0)
    decision = _wz_voice_first_normalize_decision(result.get("hiring_decision", ""), current)

    if current >= 80:
        st.success(f"✅ {decision}")
    elif current >= 60:
        st.warning(f"⚠️ {decision}")
    else:
        st.error(f"🟠 {decision}")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Readiness score", f"{current}/100")
    with c2:
        st.metric("Target", "80+")
    with c3:
        st.metric("Next focus", str(result.get("next_action", "Practice again"))[:28])

    st.caption(str(result.get("hiring_reason", "Based on your answers and job fit.")))

    left, right = st.columns(2)
    with left:
        st.markdown("### What went well")
        for item in (result.get("strengths") or [])[:3]:
            st.markdown(f"- {item}")
    with right:
        st.markdown("### What to fix next")
        mistakes = result.get("top_mistakes") or result.get("what_hurt_you_most") or []
        for item in mistakes[:3]:
            st.markdown(f"- {item}")

    with st.expander("Improved answer example", expanded=True):
        st.write(result.get("improved_version_of_weakest_answer", "Use STAR structure and add a truthful measurable result."))

    b1, b2, b3 = st.columns(3)
    with b1:
        if st.button("🎤 Practice again", type="primary", use_container_width=True):
            for key in ["wz_ri_questions", "wz_ri_current_index", "wz_ri_answers", "wz_ri_final_score", "wz_ri_started", "wz_ri_live_reactions", "wz_ri_last_audio_id", "wz_ri_question_started_at"]:
                st.session_state.pop(key, None)
            st.rerun()
    with b2:
        if st.button("Improve CV", use_container_width=True):
            st.session_state["page"] = "improve_cv"
            st.rerun()
    with b3:
        if st.button("Find better-fit jobs", use_container_width=True):
            st.session_state["page"] = "jobs"
            st.rerun()


def render_real_interview_simulation():
    # Voice-first, one-button interview flow.
    cv_text = _wz_ri_get_cv_text()
    default_jd = _wz_ri_get_jd_text()
    selected_job = _wz150_get_selected_job_context() if callable(globals().get("_wz150_get_selected_job_context")) else {}

    role_default = (selected_job.get("title", "") if isinstance(selected_job, dict) else "") or st.session_state.get("target_role", "") or st.session_state.get("target_job_title", "") or "the role"
    company_default = (selected_job.get("company", "") if isinstance(selected_job, dict) else "") or st.session_state.get("target_company", "")
    jd_default = default_jd or (selected_job.get("description", "") if isinstance(selected_job, dict) else "") or st.session_state.get("real_interview_jd_saved", "")

    for key, value in {
        "wz_ri_started": False,
        "wz_ri_current_index": 0,
        "wz_ri_answers": [],
        "wz_ri_questions": [],
        "wz_ri_live_reactions": [],
        "wz_ri_final_score": {},
        "wz_ri_last_audio_id": "",
        "wz_ri_question_started_at": time.time(),
    }.items():
        if key not in st.session_state:
            st.session_state[key] = value

    st.markdown("""
    <style>
      .wz-call-card{border:1px solid rgba(0,210,255,.28);border-radius:24px;padding:28px;background:linear-gradient(135deg,rgba(0,80,110,.35),rgba(10,20,45,.75));margin-bottom:18px;}
      .wz-call-label{letter-spacing:.22em;text-transform:uppercase;color:#5eefff;font-weight:800;font-size:.78rem;margin-bottom:12px;}
      .wz-call-title{font-size:2.4rem;font-weight:900;line-height:1.05;margin-bottom:12px;color:#fff;}
      .wz-question{border:1px solid rgba(255,255,255,.14);border-radius:22px;padding:24px;background:rgba(8,16,35,.74);margin:18px 0;}
      .wz-question small{color:#5eefff;font-weight:800;letter-spacing:.18em;text-transform:uppercase;}
      .wz-question h2{font-size:1.55rem;line-height:1.25;margin-top:12px;color:#fff;}
      .wz-reaction{border-left:4px solid #5eefff;border-radius:16px;padding:16px 18px;background:rgba(94,239,255,.08);margin:12px 0;}
    </style>
    """, unsafe_allow_html=True)

    candidate = _wz_voice_first_safe_name()

    if not cv_text:
        st.error("Upload or create your CV first. This interview must be based on your CV, not generic questions.")
        return

    # Show minimal setup only before starting. Default language is ALWAYS English.
    if not st.session_state.get("wz_ri_started"):
        c1, c2 = st.columns(2)
        with c1:
            interview_language = st.selectbox(
                "Interview language",
                ["English", "German", "Hindi", "Tamil", "Dutch", "French", "Spanish"],
                index=0,
                key="wz_voice_first_language",
            )
        with c2:
            answer_mode = st.selectbox(
                "You may answer in",
                ["Same as interview", "English", "German", "Hindi", "Tamil", "Any language"],
                index=0,
                key="wz_voice_first_answer_mode",
            )

        c1, c2 = st.columns(2)
        with c1:
            role = st.text_input("Target role", value=role_default, key="wz_ri_role")
        with c2:
            company = st.text_input("Target company", value=company_default, key="wz_ri_company")
        website = st.text_input("Company opening / careers link (optional)", value=st.session_state.get("wz_ri_company_website", ""), key="wz_ri_company_website")
        jd = st.text_area("Job description or opening details", value=jd_default, height=130, key="wz_ri_jd")

        st.session_state["target_role"] = role
        st.session_state["target_company"] = company
        st.session_state["selected_job_description"] = jd
        st.session_state["real_interview_jd_saved"] = jd

        if st.button("🎤 Start recruiter call", type="primary", use_container_width=True):
            st.session_state["wz_ri_interview_language"] = interview_language
            st.session_state["wz_ri_answer_language"] = answer_mode
            questions = [_wz_voice_first_build_opening_question(cv_text, jd, role, company, interview_language)]
            for i in range(1, 6):
                questions.append(_wz_voice_first_next_question(cv_text, jd, role, company, interview_language, [], i))
            st.session_state["wz_ri_questions"] = questions
            st.session_state["wz_ri_current_index"] = 0
            st.session_state["wz_ri_answers"] = []
            st.session_state["wz_ri_live_reactions"] = []
            st.session_state["wz_ri_final_score"] = {}
            st.session_state["wz_ri_started"] = True
            st.session_state["wz_ri_question_started_at"] = time.time()
            try:
                track_event("interview_started", "Interview", {"language": interview_language, "role": role, "company": company})
            except Exception:
                pass
            st.rerun()
        return

    final = st.session_state.get("wz_ri_final_score", {})
    if isinstance(final, dict) and final:
        _wz_ri_render_final_score(final, st.session_state.get("wz_ri_company", ""), st.session_state.get("wz_ri_role", ""), st.session_state.get("wz_ri_company_website", ""), st.session_state.get("wz_ri_interview_language", "English"))
        return

    questions = st.session_state.get("wz_ri_questions", []) or []
    idx = int(st.session_state.get("wz_ri_current_index", 0) or 0)
    if idx >= len(questions):
        result = _wz_voice_first_score_answers(cv_text, st.session_state.get("wz_ri_jd", ""), st.session_state.get("wz_ri_role", ""), st.session_state.get("wz_ri_company", ""), st.session_state.get("wz_ri_answers", []), st.session_state.get("wz_ri_interview_language", "English"))
        st.session_state["wz_ri_final_score"] = result
        try:
            track_event("interview_completed", "Interview", {"score": result.get("overall_score")})
        except Exception:
            pass
        st.rerun()
        return

    language = st.session_state.get("wz_ri_interview_language", "English") or "English"
    role = st.session_state.get("wz_ri_role", role_default)
    company = st.session_state.get("wz_ri_company", company_default)
    question = questions[idx]

    # WorkZo v120: defensive cleanup so HTML from older broken renders never appears as text.
    # Handles escaped HTML (&lt;div&gt;), JSON-style escaped quotes (\"), and whole Zoom-room blocks.
    def _wz120_plain_question(value):
        """
        Convert any accidentally stored Zoom/HTML UI block back into a plain
        recruiter question. This is intentionally aggressive because older
        versions could save rendered HTML into wz_ri_questions/session state.
        """
        try:
            import re as _re
            import html as _html

            raw = str(value or "")
            # Unescape multiple times because Streamlit/session state may contain
            # &lt;div&gt;, escaped JSON quotes, or already escaped HTML.
            for _ in range(3):
                raw = _html.unescape(raw)
            raw = raw.replace('\\"', '"').replace("\\'", "'")
            raw = raw.replace("\\n", "\n").replace("\\t", " ")

            # Most important case: the whole Zoom UI was saved as the question.
            # Extract only the actual question from the wz118-question div.
            extract_patterns = [
                r'<div[^>]*class\s*=\s*["\'][^"\']*wz118-question[^"\']*["\'][^>]*>(.*?)</div>',
                r'class\s*=\s*["\'][^"\']*wz118-question[^"\']*["\'][^>]*>\s*(.*?)\s*</div>',
                r'wz118-question[^>]*>\s*(.*?)\s*</div>',
            ]
            for pat in extract_patterns:
                m = _re.search(pat, raw, flags=_re.I | _re.S)
                if m and m.group(1).strip():
                    raw = m.group(1)
                    break

            # If the string starts in the middle of the broken HTML block, still recover it.
            if "wz118-question" in raw.lower():
                parts = _re.split(r'wz118-question[^>]*>', raw, flags=_re.I | _re.S)
                if len(parts) > 1:
                    raw = parts[1].split("</div>")[0]

            # Drop all remaining Zoom UI / helper fragments.
            raw = _re.sub(r'<style.*?</style>', ' ', raw, flags=_re.I | _re.S)
            raw = _re.sub(r'<script.*?</script>', ' ', raw, flags=_re.I | _re.S)
            raw = _re.sub(r'<div[^>]*class\s*=\s*["\'][^"\']*wz118-(?:listening|bars|pane|timer|pressure|cue|thinking|typing)[^"\']*["\'][^>]*>.*', ' ', raw, flags=_re.I | _re.S)
            raw = _re.sub(r'<[^>]+>', ' ', raw)
            raw = _html.unescape(raw)

            # Remove visible labels from the right-side Zoom pane if they leaked.
            cleanup_phrases = [
                r'Recruiter is listening for JD relevance.*',
                r'Recruiter is listening\..*',
                r'You\s*·\s*(?:Speaking\s*/\s*typing|Answering).*',
                r'(?:Answer time left|Time left).*',
                r'Tip:\s*answer in 45.*',
                r'Looking for:\s*clear role fit.*',
                r'Recording practice session.*',
                r'WorkZo Interview Room.*',
            ]
            for pat in cleanup_phrases:
                raw = _re.sub(pat, ' ', raw, flags=_re.I | _re.S)

            raw = _re.sub(r'\{(?:previous_reaction_html|thinking_indicator_html)\}', ' ', raw)
            raw = _re.sub(r'\s+', ' ', raw).strip(' -|•\n\t')

            # Final hard stop: never show UI markup as an interview question.
            bad_markers = ["<div", "</div", "wz118-", "class=", "span>", "timer-card", "pressure", "listening"]
            if any(marker in raw.lower() for marker in bad_markers):
                return "Tell me about yourself and connect your experience to this job."

            return raw or "Tell me about yourself and connect your experience to this job."
        except Exception:
            cleaned = str(value or "").strip()
            if any(marker in cleaned.lower() for marker in ["<div", "wz118-", "class=", "</div"]):
                return "Tell me about yourself and connect your experience to this job."
            return cleaned or "Tell me about yourself and connect your experience to this job."


    # WorkZo v121: scrub broken HTML from all live interview session keys.
    try:
        for _key in [
            "wz_ri_current_question",
            "current_interview_question",
            "workobot_current_question",
            "wz_current_question",
            "latest_interview_question",
        ]:
            if _key in st.session_state:
                st.session_state[_key] = _wz120_plain_question(st.session_state.get(_key))
    except Exception:
        pass

    # Clean the whole question list once, so next/previous questions are also fixed.
    try:
        cleaned_questions = [_wz120_plain_question(q) for q in (questions or [])]
        st.session_state["wz_ri_questions"] = cleaned_questions
        questions = cleaned_questions
        question = questions[idx]
    except Exception:
        pass

    question_display = _wz120_plain_question(question)
    # Keep downstream scoring clean too, but preserve the original list structure.
    question = question_display

    # WorkZo v118/v119: Zoom-style live interview room UI.
    # This changes only the live interview presentation; the interview engine, scoring, routing, and state keys stay intact.
    elapsed = int(time.time() - float(st.session_state.get("wz_ri_question_started_at", time.time())))
    question_limit = 75
    left = max(0, question_limit - elapsed)
    progress_value = max(0.02, min(1.0, elapsed / question_limit))
    minutes = left // 60
    seconds = left % 60
    timer_text = f"{minutes:02d}:{seconds:02d}"
    mode_label = str(st.session_state.get("wz_ri_personality", "Human recruiter") or "Human recruiter")

    st.markdown("""
    <style>
    .wz118-room {
        border: 1px solid rgba(37, 196, 218, .34);
        border-radius: 28px;
        background: radial-gradient(circle at 18% 10%, rgba(11, 184, 216, .20), rgba(15, 23, 42, .94) 42%, rgba(8, 13, 28, .98));
        padding: 22px;
        box-shadow: 0 22px 60px rgba(0,0,0,.22);
        margin: 12px 0 18px 0;
    }
    .wz118-room-top {
        display:flex; align-items:center; justify-content:space-between; gap:16px;
        padding: 8px 6px 20px 6px;
    }
    .wz118-title { font-size: 1.05rem; font-weight: 900; color:#f8fafc; letter-spacing:.02em; }
    .wz118-sub { color:#9fb3d9; font-size:.88rem; margin-top:4px; }
    .wz118-rec { display:inline-flex; align-items:center; gap:8px; border:1px solid rgba(248,113,113,.34); color:#fecaca; background:rgba(127,29,29,.20); padding:8px 12px; border-radius:999px; font-weight:850; font-size:.82rem; }
    .wz118-dot { width:9px; height:9px; background:#ef4444; border-radius:999px; box-shadow:0 0 16px rgba(239,68,68,.75); display:inline-block; animation:wz118-blink 1.05s infinite ease-in-out; }
    @keyframes wz118-blink { 0%,100%{opacity:.35; transform:scale(.82)} 45%{opacity:1; transform:scale(1.18)} }
    .wz118-grid { display:grid; grid-template-columns:minmax(0,1.2fr) minmax(280px,.8fr); gap:18px; }
    .wz118-pane {
        min-height: 310px; border-radius:24px; border:1px solid rgba(148,163,184,.18);
        background:rgba(2,6,23,.42); padding:22px; position:relative; overflow:hidden;
    }
    .wz118-pane.you { background:rgba(15,23,42,.58); }
    .wz118-pane-label { color:#93c5fd; font-size:.76rem; font-weight:900; letter-spacing:.13em; text-transform:uppercase; margin-bottom:14px; }
    .wz118-question { color:#ffffff; font-size:1.65rem; line-height:1.24; font-weight:950; max-width:920px; }
    .wz118-listening { margin-top:18px; color:#cbd5e1; font-size:.94rem; }
    .wz118-bars { display:flex; align-items:flex-end; gap:7px; height:48px; margin-top:20px; }
    .wz118-bars span { width:9px; border-radius:999px; background:linear-gradient(180deg,#67e8f9,#2563eb); display:block; opacity:.95; }
    .wz118-bars span { animation:wz118-bars 1.15s infinite ease-in-out; }
    .wz118-bars span:nth-child(1){height:18px;animation-delay:.05s}.wz118-bars span:nth-child(2){height:30px;animation-delay:.16s}.wz118-bars span:nth-child(3){height:42px;animation-delay:.28s}.wz118-bars span:nth-child(4){height:25px;animation-delay:.39s}.wz118-bars span:nth-child(5){height:36px;animation-delay:.51s}
    @keyframes wz118-bars { 0%,100%{transform:scaleY(.55);opacity:.55} 50%{transform:scaleY(1.15);opacity:1} }
    .wz118-timer-card { border:1px solid rgba(148,163,184,.18); background:rgba(2,6,23,.38); padding:18px; border-radius:20px; margin-bottom:14px; }
    .wz118-timer-label { color:#9fb3d9; text-transform:uppercase; font-size:.72rem; font-weight:900; letter-spacing:.12em; }
    .wz118-timer { color:#fff; font-size:2.7rem; font-weight:950; margin-top:8px; }
    .wz118-pressure { height:10px; border-radius:999px; background:#1f2937; overflow:hidden; margin-top:10px; }
    .wz118-pressure > div { height:10px; border-radius:999px; background:linear-gradient(90deg,#22d3ee,#fb923c,#ef4444); }
    .wz118-cue { color:#cbd5e1; font-size:.9rem; line-height:1.45; border-top:1px solid rgba(148,163,184,.12); padding-top:14px; margin-top:14px; }
    .wz118-bottom { border:1px solid rgba(148,163,184,.18); background:rgba(2,6,23,.58); padding:14px; border-radius:22px; margin-top:16px; }
    .wz118-help-title { color:#e2e8f0; font-weight:900; margin-bottom:8px; }
    .wz118-previous { border-left:3px solid rgba(34,211,238,.65); background:rgba(14,165,233,.08); padding:12px 14px; border-radius:12px; margin:0 0 14px 0; color:#dbeafe; }
    .wz118-thinking { display:flex; align-items:center; gap:8px; color:#bae6fd; font-size:.88rem; margin-top:14px; }
    .wz118-typing-dots { display:inline-flex; gap:4px; align-items:center; }
    .wz118-typing-dots span { width:6px; height:6px; border-radius:999px; background:#38bdf8; display:block; animation:wz118-typing 1.15s infinite ease-in-out; }
    .wz118-typing-dots span:nth-child(2){animation-delay:.16s}.wz118-typing-dots span:nth-child(3){animation-delay:.32s}
    @keyframes wz118-typing { 0%,100%{transform:translateY(0);opacity:.35} 50%{transform:translateY(-5px);opacity:1} }
    @media (max-width: 900px) { .wz118-grid { grid-template-columns:1fr; } .wz118-question { font-size:1.28rem; } }
    </style>
    """, unsafe_allow_html=True)

    reactions = st.session_state.get("wz_ri_live_reactions", []) or []
    previous_reaction_html = ""
    if reactions and idx > 0:
        last = reactions[min(idx - 1, len(reactions) - 1)] or {}
        if last.get("reaction"):
            previous_reaction_html = f"<div class='wz118-previous'><b>Interviewer:</b> {html.escape(str(last.get('reaction')))}</div>"

    if left == 0:
        pressure_message = "Interviewer may interrupt: give the strongest short version now."
    elif left <= 20:
        pressure_message = "High pressure: finish with one clear result."
    else:
        pressure_message = "Recruiter is listening. Keep it specific, truthful, and tied to the job."

    # First few seconds show a fake-but-useful live call cue.
    thinking_indicator_html = ""
    try:
        if elapsed <= 4:
            thinking_indicator_html = "<div class='wz118-thinking'><span>Recruiter is thinking</span><span class='wz118-typing-dots'><span></span><span></span><span></span></span></div>"
    except Exception:
        thinking_indicator_html = ""

    # WorkZo v123: render the Zoom room through an HTML component instead of Markdown.
    # This prevents Streamlit from ever showing <div class="wz118..."> as plain text.
    try:
        import streamlit.components.v1 as _wz_components
    except Exception:
        _wz_components = None

    zoom_room_html = f"""
    <style>
    html, body {{ margin:0; padding:0; background:transparent; font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }}
    .wz118-room {{
        border: 1px solid rgba(37, 196, 218, .34);
        border-radius: 28px;
        background: radial-gradient(circle at 18% 10%, rgba(11, 184, 216, .20), rgba(15, 23, 42, .94) 42%, rgba(8, 13, 28, .98));
        padding: 22px;
        box-shadow: 0 22px 60px rgba(0,0,0,.22);
        margin: 0;
        box-sizing:border-box;
    }}
    .wz118-room-top {{ display:flex; align-items:center; justify-content:space-between; gap:16px; padding: 8px 6px 20px 6px; }}
    .wz118-title {{ font-size: 1.05rem; font-weight: 900; color:#f8fafc; letter-spacing:.02em; }}
    .wz118-sub {{ color:#9fb3d9; font-size:.88rem; margin-top:4px; }}
    .wz118-rec {{ display:inline-flex; align-items:center; gap:8px; border:1px solid rgba(248,113,113,.34); color:#fecaca; background:rgba(127,29,29,.20); padding:8px 12px; border-radius:999px; font-weight:850; font-size:.82rem; white-space:nowrap; }}
    .wz118-dot {{ width:9px; height:9px; background:#ef4444; border-radius:999px; box-shadow:0 0 16px rgba(239,68,68,.75); display:inline-block; animation:wz118-blink 1.05s infinite ease-in-out; }}
    @keyframes wz118-blink {{ 0%,100%{{opacity:.35; transform:scale(.82)}} 45%{{opacity:1; transform:scale(1.18)}} }}
    .wz118-grid {{ display:grid; grid-template-columns:minmax(0,1.2fr) minmax(280px,.8fr); gap:18px; }}
    .wz118-pane {{ min-height: 285px; border-radius:24px; border:1px solid rgba(148,163,184,.18); background:rgba(2,6,23,.42); padding:22px; position:relative; overflow:hidden; box-sizing:border-box; }}
    .wz118-pane.you {{ background:rgba(15,23,42,.58); }}
    .wz118-pane-label {{ color:#93c5fd; font-size:.76rem; font-weight:900; letter-spacing:.13em; text-transform:uppercase; margin-bottom:14px; }}
    .wz118-question {{ color:#ffffff; font-size:1.55rem; line-height:1.25; font-weight:950; max-width:920px; }}
    .wz118-listening {{ margin-top:18px; color:#cbd5e1; font-size:.94rem; }}
    .wz118-bars {{ display:flex; align-items:flex-end; gap:7px; height:48px; margin-top:20px; }}
    .wz118-bars span {{ width:9px; border-radius:999px; background:linear-gradient(180deg,#67e8f9,#2563eb); display:block; opacity:.95; animation:wz118-bars 1.15s infinite ease-in-out; }}
    .wz118-bars span:nth-child(1){{height:18px;animation-delay:.05s}}.wz118-bars span:nth-child(2){{height:30px;animation-delay:.16s}}.wz118-bars span:nth-child(3){{height:42px;animation-delay:.28s}}.wz118-bars span:nth-child(4){{height:25px;animation-delay:.39s}}.wz118-bars span:nth-child(5){{height:36px;animation-delay:.51s}}
    @keyframes wz118-bars {{ 0%,100%{{transform:scaleY(.55);opacity:.55}} 50%{{transform:scaleY(1.15);opacity:1}} }}
    .wz118-timer-card {{ border:1px solid rgba(148,163,184,.18); background:rgba(2,6,23,.38); padding:18px; border-radius:20px; margin-bottom:14px; }}
    .wz118-timer-label {{ color:#9fb3d9; text-transform:uppercase; font-size:.72rem; font-weight:900; letter-spacing:.12em; }}
    .wz118-timer {{ color:#fff; font-size:2.7rem; font-weight:950; margin-top:8px; }}
    .wz118-pressure {{ height:10px; border-radius:999px; background:#1f2937; overflow:hidden; margin-top:10px; }}
    .wz118-pressure > div {{ height:10px; border-radius:999px; background:linear-gradient(90deg,#22d3ee,#fb923c,#ef4444); }}
    .wz118-cue {{ color:#cbd5e1; font-size:.9rem; line-height:1.45; border-top:1px solid rgba(148,163,184,.12); padding-top:14px; margin-top:14px; }}
    .wz118-previous {{ border-left:3px solid rgba(34,211,238,.65); background:rgba(14,165,233,.08); padding:12px 14px; border-radius:12px; margin:0 0 14px 0; color:#dbeafe; }}
    .wz118-thinking {{ display:flex; align-items:center; gap:8px; color:#bae6fd; font-size:.88rem; margin-top:14px; }}
    .wz118-typing-dots {{ display:inline-flex; gap:4px; align-items:center; }}
    .wz118-typing-dots span {{ width:6px; height:6px; border-radius:999px; background:#38bdf8; display:block; animation:wz118-typing 1.15s infinite ease-in-out; }}
    .wz118-typing-dots span:nth-child(2){{animation-delay:.16s}}.wz118-typing-dots span:nth-child(3){{animation-delay:.32s}}
    @keyframes wz118-typing {{ 0%,100%{{transform:translateY(0);opacity:.35}} 50%{{transform:translateY(-5px);opacity:1}} }}
    @media (max-width: 900px) {{ .wz118-grid {{ grid-template-columns:1fr; }} .wz118-question {{ font-size:1.24rem; }} .wz118-room-top {{ align-items:flex-start; flex-direction:column; }} }}
    </style>
    <div class="wz118-room">
      <div class="wz118-room-top">
        <div>
          <div class="wz118-title">WorkZo Interview Room</div>
          <div class="wz118-sub">Candidate: {html.escape(candidate)} · Role: {html.escape(role or 'target role')} {('@ ' + html.escape(company)) if company else ''}</div>
        </div>
        <div class="wz118-rec"><span class="wz118-dot"></span> Recording practice session · {html.escape(mode_label)}</div>
      </div>
      <div class="wz118-grid">
        <div class="wz118-pane">
          <div class="wz118-pane-label">AI Recruiter · Question {idx + 1} of {len(questions)}</div>
          {previous_reaction_html}
          <div class="wz118-question">{html.escape(str(question_display))}</div>
          <div class="wz118-listening">Looking for: clear role fit, measurable impact, and relevance to the job.</div>
          {thinking_indicator_html}
          <div class="wz118-bars"><span></span><span></span><span></span><span></span><span></span></div>
        </div>
        <div class="wz118-pane you">
          <div class="wz118-pane-label">You · Answering</div>
          <div class="wz118-timer-card">
            <div class="wz118-timer-label">Time left</div>
            <div class="wz118-timer">{timer_text}</div>
            <div class="wz118-pressure"><div style="width:{int(progress_value * 100)}%"></div></div>
          </div>
          <div class="wz118-cue">{html.escape(pressure_message)}<br>Keep it concise. Focus on results and relevance. (45–75 sec)</div>
        </div>
      </div>
    </div>
    """
    if _wz_components is not None:
        _wz_components.html(zoom_room_html, height=430, scrolling=False)
    else:
        st.markdown(zoom_room_html, unsafe_allow_html=True)

    try:
        _wz_ri_auto_speak(question, f"voice_first_q_{idx}")
    except Exception:
        pass

    st.markdown("### Your answer")
    st.caption("Speak naturally like a real call. You can type only if speaking is not possible.")
    audio_key = f"wz_voice_first_audio_{idx}_{len(st.session_state.get('wz_ri_answers', []))}"
    audio_file = st.audio_input("🎙 Record answer", key=audio_key) if hasattr(st, "audio_input") else None

    fallback_text = ""
    with st.expander("Can’t speak right now? Type as fallback", expanded=False):
        fallback_text = st.text_area("Typed fallback", key=f"wz_voice_first_text_{idx}", height=100)

    # WorkZo v125: keep the live room clean. Put Copilot in a closed helper box
    # directly above Submit, and remove the old "Interview controls" header/line.
    with st.expander("💡 Interview Copilot — help with this question", expanded=False):
        try:
            if callable(globals().get("_wz113_render_interview_helper_bar")):
                _wz113_render_interview_helper_bar(compact=True, key_prefix=f"wz113_live_{idx}")
        except Exception as exc:
            try:
                st.warning(f"Interview Copilot could not load safely: {exc}")
            except Exception:
                pass

    c1, c2, c3, c4 = st.columns([2.2, 1, 1, 1])
    with c1:
        submit = st.button("🎙 Submit answer", type="primary", use_container_width=True, key=f"wz_voice_first_submit_{idx}")
    with c2:
        again = st.button("↻ Record again", use_container_width=True, key=f"wz_voice_first_again_{idx}")
    with c3:
        interrupt_now = st.button("⚡ Interrupt me", use_container_width=True, key=f"wz_voice_first_interrupt_{idx}")
    with c4:
        end_now = st.button("⏹ End call", use_container_width=True, key=f"wz_voice_first_end_{idx}")

    if interrupt_now:
        st.warning("Interviewer: Let me stop you there — can you make that more specific and add the result?")

    if again:
        st.rerun()
    if end_now:
        result = _wz_voice_first_score_answers(cv_text, st.session_state.get("wz_ri_jd", ""), role, company, st.session_state.get("wz_ri_answers", []), language)
        st.session_state["wz_ri_final_score"] = result
        st.rerun()

    if submit:
        answer = ""
        if audio_file is not None:
            with st.spinner("Transcribing your spoken answer..."):
                answer = _wz_ri_transcribe(audio_file)
        elif str(fallback_text or "").strip():
            answer = str(fallback_text).strip()
        else:
            st.warning("Please record your answer first. Use typed fallback only if you cannot speak.")
            return

        if not str(answer or "").strip():
            st.error("I could not hear/transcribe the answer clearly. Please record again.")
            return

        answers = list(st.session_state.get("wz_ri_answers", []))
        answers.append({"question": question, "answer": answer})
        st.session_state["wz_ri_answers"] = answers

        with st.spinner("Recruiter is thinking about your answer..."):
            try:
                # Small deliberate pause makes the simulator feel like a real interviewer,
                # while keeping the flow fast.
                time.sleep(0.8)
            except Exception:
                pass
            try:
                reaction = _wz_ri_react_to_answer(question, answer, cv_text, st.session_state.get("wz_ri_jd", ""), answers, language, "Human recruiter")
            except Exception:
                reaction = {"reaction": _wz_voice_first_reaction_phrase(answer, idx), "needs_followup": False, "followup_question": ""}

        # Make the reaction feel more human and less robotic.
        if not reaction.get("reaction"):
            reaction["reaction"] = _wz_voice_first_reaction_phrase(answer, idx)
        elif str(reaction.get("reaction", "")).strip().lower() in {"good", "ok", "okay"}:
            reaction["reaction"] = _wz_voice_first_reaction_phrase(answer, idx)

        reactions = list(st.session_state.get("wz_ri_live_reactions", []))
        reactions.append(reaction)
        st.session_state["wz_ri_live_reactions"] = reactions

        # Natural follow-up behavior: if weak, insert follow-up as next question.
        next_idx = idx + 1
        if reaction.get("needs_followup") and reaction.get("followup_question") and next_idx < len(questions):
            questions[next_idx] = str(reaction.get("followup_question"))
            st.session_state["wz_ri_questions"] = questions

        st.session_state["wz_ri_current_index"] = idx + 1
        st.session_state["wz_ri_question_started_at"] = time.time()
        st.rerun()


# =========================================================
# WorkZo v115 - JD-first, company-aware, conservative interview engine override
# Purpose:
# - Prevents the interview from relying mostly on the candidate intro.
# - Generates questions with JD-first weighting: JD 50%, CV 30%, previous answers 20%.
# - Scores conservatively; 70% = usable/safe preparation, not guaranteed pass.
# - Checks whether answers are useful for the company when company context exists.
# =========================================================


def _wz115_safe(text, limit=4000):
    try:
        import re as _re
        return _re.sub(r"\s+", " ", str(text or "")).strip()[:limit]
    except Exception:
        return str(text or "")[:limit]


def _wz115_context_rules(company_context: str = "") -> str:
    return f"""
Context weighting rules:
- Job description = 50% priority. Questions and scoring must test real job requirements first.
- Candidate CV = 30% priority. Use it to ask for evidence, proof, projects, tools, and experience.
- User introduction/previous answers = 20% priority. Use it only for follow-ups, not as the main interview source.
- Company context = optional extra. Use it only if provided; never invent company facts.
- Do not base the interview mostly on the user's introduction.
- Be conservative and honest. A 70% readiness score means usable/safe preparation, but a real interview result may differ.
Company context available: {'yes' if company_context else 'no'}
""".strip()


def _wz_ri_build_questions(cv_text: str, jd: str, company: str, role: str, website: str, company_context: str, language: str, personality: str):
    """v115 override: create JD-first interview questions after the intro."""
    intro_question = _wz_voice_first_build_opening_question(cv_text, jd, role, company, language) if callable(globals().get('_wz_voice_first_build_opening_question')) else "Tell me about yourself and connect it to this job."
    cv_text = _wz115_safe(cv_text, 7000)
    jd = _wz115_safe(jd, 7000)
    company_context = _wz115_safe(company_context, 2200)
    role = _wz115_safe(role or "the role", 200)
    company = _wz115_safe(company or "the company", 200)

    prompt = f"""
You are a realistic interviewer for {role} at {company}.

{_wz115_context_rules(company_context)}

Language for interviewer questions: {language}
Interviewer personality: {personality or 'Human recruiter'}

CV evidence:
{cv_text or 'No CV text available'}

Job description — highest priority:
{jd or 'No job description available'}

Company website/context:
{company_context or 'No company context available'}

Create exactly 5 questions AFTER the opening introduction.
Question mix:
1. JD requirement question: test the most important requirement in the job description.
2. CV proof question: ask for evidence from the CV that matches a JD requirement.
3. Company usefulness question: if company context exists, ask how the candidate would be useful for this company; otherwise ask role/business-impact fit.
4. Gap/risk question: ask about the biggest gap compared with the JD.
5. Hiring-decision follow-up: ask for one specific reason/evidence to choose the candidate.

Rules:
- Do not ask mostly from the user's introduction.
- Do not create generic textbook questions.
- Mention JD/company context naturally when possible.
- Keep questions realistic, short, and spoken.
- Keep all questions in {language}.
- Return ONLY valid JSON: {{"questions": ["q2", "q3", "q4", "q5", "q6"]}}
""".strip()
    try:
        raw = _wz_ri_ai(prompt, json_mode=True, language=language)
        data = _wz_ri_json(raw, {})
        qs = data.get('questions') if isinstance(data, dict) else None
        if isinstance(qs, list) and len(qs) >= 5:
            return [intro_question] + [str(q).strip() for q in qs[:5] if str(q).strip()]
    except Exception:
        pass

    fallback = [
        f"Which requirement from this job description is your strongest match, and what evidence from your CV proves it?",
        f"Walk me through one CV example that shows you can succeed as {role}.",
        f"How would your experience be useful for {company} specifically?" if company and company != 'the company' else "How would your experience create value in this role, not just match the title?",
        "Compared with this job description, what is your biggest gap and how would you close it quickly?",
        "Give me one specific reason, with evidence, why we should move you to the next round.",
    ]
    return [intro_question] + fallback


def _wz_ri_react_to_answer(question: str, answer: str, cv_text: str, jd: str, qa_pairs: list, language: str, personality: str):
    """v115 override: realistic JD/company-aware reaction and follow-up."""
    try:
        flags = _wz_ri_answer_quality_flags(answer, jd) if callable(globals().get('_wz_ri_answer_quality_flags')) else {}
    except Exception:
        flags = {}
    try:
        star = _wz150_star_flags(answer) if callable(globals().get('_wz150_star_flags')) else {}
    except Exception:
        star = {}
    words = len(str(answer or '').split())
    company = st.session_state.get('wz_ri_company') or st.session_state.get('target_company') or ''
    website = st.session_state.get('wz_ri_company_website') or ''
    try:
        company_context = _wz_ri_company_context(company, website) if callable(globals().get('_wz_ri_company_context')) else ''
    except Exception:
        company_context = ''

    if words < 25:
        return {
            "reaction": "Hmm… let me stop you there. That was too short for a real interview. Give me one concrete example connected to the job description.",
            "needs_followup": True,
            "followup_question": "Which exact requirement from the job description does your example prove?",
            "interruption_reason": "too short",
            "coach_note": "Use JD requirement → CV example → result.",
        }
    if words > 180:
        return {
            "reaction": "Okay, I’ll pause you there. You’re giving too much detail — give me the direct point, one example, and the result.",
            "needs_followup": True,
            "followup_question": "Can you repeat that in 45 seconds and connect it to this job requirement?",
            "interruption_reason": "too long",
            "coach_note": "Keep it tighter and lead with impact.",
        }
    if not any(ch.isdigit() for ch in str(answer or '')) and not str(answer or '').lower().count('result'):
        return {
            "reaction": "Okay, interesting — but I’m missing the impact. What was the measurable result or business outcome?",
            "needs_followup": True,
            "followup_question": "What changed because of your action — time saved, quality improved, customers helped, or another real result?",
            "interruption_reason": "missing impact",
            "coach_note": "Add a truthful metric or outcome if available.",
        }

    prompt = f"""
You are a realistic {personality or 'human recruiter'}.

{_wz115_context_rules(company_context)}

Language rule: respond only in {language}.

Question:
{question}

Candidate answer:
{answer}

Previous answers / intro:
{json.dumps(qa_pairs, ensure_ascii=False)[:3500]}

Job description — highest priority:
{_wz115_safe(jd, 5000)}

CV evidence:
{_wz115_safe(cv_text, 5000)}

Company context:
{_wz115_safe(company_context, 1600) or 'No company context available'}

Detected answer flags:
{json.dumps(flags, ensure_ascii=False)}
STAR flags:
{json.dumps(star, ensure_ascii=False)}

Return ONLY valid JSON:
{{
  "reaction": "short human interviewer reaction in {language}",
  "needs_followup": true,
  "followup_question": "specific follow-up question in {language} if needed",
  "interruption_reason": "too vague|too long|missing impact|missing JD connection|generic for company|weak STAR|none",
  "coach_note": "one short private coaching note"
}}

Rules:
- Push for JD relevance first.
- If company context exists and the answer is generic, ask how it helps this company specifically.
- If the answer is based only on introduction, ask for CV/JD proof.
- If strong, acknowledge briefly and ask a deeper follow-up only if useful.
""".strip()
    try:
        raw = _wz_ri_ai(prompt, json_mode=True, language=language)
        data = _wz_ri_json(raw, {})
        if isinstance(data, dict) and data.get('reaction'):
            return data
    except Exception:
        pass
    return {
        "reaction": "Good start. Now connect it more directly to one job requirement and one result.",
        "needs_followup": True,
        "followup_question": "Which job requirement does this answer prove, and what result did you create?",
        "interruption_reason": "missing JD connection",
        "coach_note": "Tie every answer to JD + evidence + impact.",
    }


def _wz_voice_first_score_answers(cv_text: str, jd: str, role: str, company: str, answers: list, language: str) -> dict:
    """v115 override: conservative JD/company-aware final scoring."""
    website = st.session_state.get('wz_ri_company_website', '')
    try:
        company_context = _wz_ri_company_context(company, website) if callable(globals().get('_wz_ri_company_context')) else ''
    except Exception:
        company_context = ''
    prompt = f"""
You are WorkZo's honest interview evaluator. Score conservatively.

{_wz115_context_rules(company_context)}

Language for report: {language}
Role: {role or 'target role'}
Company: {company or 'target company'}

Job description — highest priority:
{_wz115_safe(jd, 7000)}

CV evidence:
{_wz115_safe(cv_text, 7000)}

Company context:
{_wz115_safe(company_context, 2200) or 'No company context available'}

Interview answers:
{json.dumps(answers, ensure_ascii=False)[:9000]}

Scoring rules:
- 90+ only for very specific, JD-aligned, company-relevant, evidence-based answers with impact.
- 80-89 strong but not guaranteed.
- 70-79 safe/usable preparation; real outcome may differ.
- 60-69 possible but weak evidence or gaps remain.
- Below 60 not ready.
- Penalize answers that rely mostly on introduction and not JD/CV evidence.
- Penalize invented or unproven claims.

Return ONLY valid JSON:
{{
  "overall_score": 0,
  "target_score": 80,
  "hiring_decision": "Ready to pass this round|Borderline — needs one more practice round|Not ready yet — but close",
  "hiring_reason": "honest reason including that the result is not guaranteed",
  "score_meaning": "what this score means in reality",
  "strengths": ["..."],
  "what_hurt_you_most": ["..."],
  "top_mistakes": ["..."],
  "jd_alignment": ["matched requirement", "weak/missing requirement"],
  "company_usefulness": ["helpful for company", "still generic"],
  "truth_check": ["safe to say", "use only if true", "do not say unless proven"],
  "weakest_answer_question_number": 1,
  "improved_version_of_weakest_answer": "truthful improved answer with placeholders only when needed",
  "next_action": "specific next step"
}}
""".strip()
    try:
        raw = _wz_ri_ai(prompt, json_mode=True, language=language)
        data = _wz_ri_json(raw, {})
        if isinstance(data, dict) and data.get('overall_score') is not None:
            try:
                score = int(float(data.get('overall_score') or 0))
            except Exception:
                score = 0
            data['overall_score'] = max(35, min(92, score))
            if 70 <= data['overall_score'] < 80 and 'not guaranteed' not in str(data.get('hiring_reason', '')).lower():
                data['hiring_reason'] = str(data.get('hiring_reason', '') or 'Your answers are usable, but real interview results may differ based on interviewer, competition, and company expectations.')
            return data
    except Exception:
        pass

    total_words = sum(len(str(a.get('answer', '')).split()) for a in answers if isinstance(a, dict))
    avg = total_words / max(1, len(answers or []))
    has_metric = any(any(ch.isdigit() for ch in str(a.get('answer', ''))) for a in answers if isinstance(a, dict))
    mentions_jd = any(any(k.lower() in str(a.get('answer', '')).lower() for k in _wz115_safe(jd, 600).split()[:20]) for a in answers if isinstance(a, dict)) if jd else False
    score = 52 + (12 if avg >= 50 else 0) + (8 if avg >= 90 else 0) + (8 if has_metric else 0) + (7 if mentions_jd else 0)
    score = max(35, min(78, score))
    return {
        "overall_score": score,
        "target_score": 80,
        "hiring_decision": "Borderline — needs one more practice round" if score >= 60 else "Not ready yet — but close",
        "hiring_reason": "This is a conservative estimate based on answer length, JD relevance, evidence, and impact. It is not a guarantee of real interview outcome.",
        "score_meaning": "70% means usable preparation, but real outcome may differ.",
        "strengths": ["You completed the interview flow", "Some answers showed relevant background"],
        "what_hurt_you_most": ["Answers need stronger JD connection", "Measurable impact should be clearer", "Company relevance may still be generic"],
        "top_mistakes": ["Too generic", "Missing measurable result", "Weak link to the job description"],
        "jd_alignment": ["Some transferable experience", "Needs clearer proof for top JD requirements"],
        "company_usefulness": ["Potentially useful if connected to company needs", "Still needs company-specific motivation"],
        "truth_check": ["Safe to say: your real CV evidence", "Use only if true: metrics and business impact", "Do not say unless proven: invented tools/results"],
        "weakest_answer_question_number": 1,
        "improved_version_of_weakest_answer": "Use STAR: state the situation, your task, your specific action, and a truthful result that connects to the JD.",
        "next_action": "Practice again with JD-specific examples and add one truthful result to each answer.",
    }


# =========================================================
# WorkZo v122 - FINAL Zoom HTML session scrub + safer live-call UI wrapper
# Purpose:
# Some earlier v118/v119 sessions saved the Zoom HTML block itself as the
# current interview question. This wrapper cleans every relevant session key
# before rendering, so <div class="wz118-..."> can never appear as question text.
# It is additive and does not change CV tools, Job Assist, Work-O-Bot routing,
# scoring, or existing interview logic.
# =========================================================

try:
    _wz122_previous_render_real_interview_simulation = render_real_interview_simulation
except Exception:
    _wz122_previous_render_real_interview_simulation = None


def _wz122_extract_plain_interview_question(value, fallback="Tell me about yourself and connect your experience to this job."):
    """Return a safe plain interview question from text that may contain old HTML UI."""
    try:
        import re as _re
        import html as _html

        raw = str(value or "")
        for _ in range(5):
            new_raw = _html.unescape(raw)
            if new_raw == raw:
                break
            raw = new_raw

        raw = raw.replace('\\"', '"').replace("\\'", "'")
        raw = raw.replace("\\n", "\n").replace("\\t", " ")

        # If a whole Zoom UI block leaked, keep only the actual recruiter question.
        question_patterns = [
            r'<div[^>]*class\s*=\s*["\'][^"\']*wz118-question[^"\']*["\'][^>]*>(.*?)</div>',
            r'<[^>]+class\s*=\s*["\'][^"\']*wz118-question[^"\']*["\'][^>]*>(.*?)</[^>]+>',
            r'wz118-question[^>]*>\s*(.*?)\s*</div>',
        ]
        for pat in question_patterns:
            match = _re.search(pat, raw, flags=_re.I | _re.S)
            if match and match.group(1).strip():
                raw = match.group(1).strip()
                break

        # Remove leftover UI fragments if extraction did not catch everything.
        raw = _re.sub(r'<style.*?</style>', ' ', raw, flags=_re.I | _re.S)
        raw = _re.sub(r'<script.*?</script>', ' ', raw, flags=_re.I | _re.S)
        raw = _re.sub(r'<br\s*/?>', ' ', raw, flags=_re.I)
        raw = _re.sub(r'<[^>]+>', ' ', raw)
        raw = _html.unescape(raw)

        # Remove leaked UI copy from the right-side Zoom panel.
        leaked_phrases = [
            r'Recruiter is listening for JD relevance.*',
            r'Recruiter is listening\..*',
            r'You\s*·\s*(?:Speaking\s*/\s*typing|Answering).*',
            r'(?:Answer time left|Time left).*',
            r'Tip:\s*answer in 45.*',
                r'Looking for:\s*clear role fit.*',
            r'Recording practice session.*',
            r'WorkZo Interview Room.*',
            r'AI Recruiter\s*·\s*Question.*',
        ]
        for pat in leaked_phrases:
            raw = _re.sub(pat, ' ', raw, flags=_re.I | _re.S)

        raw = _re.sub(r'\s+', ' ', raw).strip(' -|•\n\t')
        # If any markup indicators survive, do not show them. Use fallback.
        lower = raw.lower()
        broken_markers = [
            '<div', '</div', '<span', '</span', 'wz118-', 'class=', 'timer-card',
            'wz118-question', 'wz118-pane', 'wz118-pressure', 'wz118-bars',
        ]
        if any(marker in lower for marker in broken_markers):
            return fallback

        return raw or fallback
    except Exception:
        text = str(value or "").strip()
        if any(marker in text.lower() for marker in ['<div', '</div', 'wz118-', 'class=']):
            return fallback
        return text or fallback


def _wz122_scrub_interview_html_state():
    """Clean broken HTML from all known interview/Work-O-Bot context keys."""
    try:
        # Clean direct question/context keys.
        direct_keys = [
            'wz_ri_current_question',
            'current_interview_question',
            'workobot_current_question',
            'wz_current_question',
            'latest_interview_question',
            'current_question',
            'interview_current_question',
            'workobot_context_question',
        ]
        for key in direct_keys:
            if key in st.session_state:
                st.session_state[key] = _wz122_extract_plain_interview_question(st.session_state.get(key))

        # Clean the active interview question list.
        if isinstance(st.session_state.get('wz_ri_questions'), list):
            st.session_state['wz_ri_questions'] = [
                _wz122_extract_plain_interview_question(q) for q in st.session_state.get('wz_ri_questions', [])
            ]

        # Clean saved answers in case a question field stored HTML.
        if isinstance(st.session_state.get('wz_ri_answers'), list):
            cleaned_answers = []
            for item in st.session_state.get('wz_ri_answers', []):
                if isinstance(item, dict):
                    new_item = dict(item)
                    new_item['question'] = _wz122_extract_plain_interview_question(new_item.get('question'))
                    cleaned_answers.append(new_item)
                else:
                    cleaned_answers.append(item)
            st.session_state['wz_ri_answers'] = cleaned_answers
    except Exception:
        pass


def render_real_interview_simulation():
    _wz122_scrub_interview_html_state()
    if callable(_wz122_previous_render_real_interview_simulation):
        result = _wz122_previous_render_real_interview_simulation()
    else:
        result = None
    _wz122_scrub_interview_html_state()
    return result


def show_workobot():
    # Preserve the existing behavior, but make sure the interview context is scrubbed first.
    _wz122_scrub_interview_html_state()
    return render_real_interview_simulation()


# =========================================================
# WorkZo v123 - final Zoom HTML render/scrub patch
# Purpose: prevent any wz118 HTML block from appearing as raw text.
# =========================================================
try:
    _wz123_prev_extract_plain_interview_question = _wz122_extract_plain_interview_question
except Exception:
    _wz123_prev_extract_plain_interview_question = None


def _wz122_extract_plain_interview_question(value, fallback="Tell me about yourself — and keep it relevant to this role."):
    try:
        import re as _re
        import html as _html
        raw = str(value or "")
        for _ in range(4):
            raw = _html.unescape(raw)
        raw = raw.replace('\\"', '"').replace("\\'", "'").replace('\\n', '\n')

        # Prefer exact content inside the question div if a previous UI block leaked into state.
        m = _re.search(r'<div[^>]*class\s*=\s*["\'][^"\']*wz118-question[^"\']*["\'][^>]*>(.*?)</div>', raw, flags=_re.I | _re.S)
        if m and m.group(1).strip():
            raw = m.group(1)
        elif 'wz118-question' in raw.lower():
            raw = _re.split(r'wz118-question[^>]*>', raw, flags=_re.I | _re.S)[-1].split('</div>')[0]

        raw = _re.sub(r'<style.*?</style>|<script.*?</script>', ' ', raw, flags=_re.I | _re.S)
        raw = _re.sub(r'<br\s*/?>', ' ', raw, flags=_re.I)
        raw = _re.sub(r'<[^>]+>', ' ', raw)
        raw = _html.unescape(raw)

        # Remove common leaked UI phrases that are not interview questions.
        leaked = [
            r'Looking for:\s*clear role fit.*',
            r'Recruiter is listening.*',
            r'You\s*·\s*(?:Answering|Speaking\s*/\s*typing).*',
            r'(?:Answer time left|Time left).*',
            r'Keep it concise\. Focus on results.*',
            r'Tip:\s*answer in 45.*',
            r'Recording practice session.*',
            r'WorkZo Interview Room.*',
            r'AI Recruiter\s*·\s*Question.*',
        ]
        for pat in leaked:
            raw = _re.sub(pat, ' ', raw, flags=_re.I | _re.S)
        raw = _re.sub(r'\s+', ' ', raw).strip(' -|•\n\t')
        if any(x in raw.lower() for x in ['<div', '</div', '<span', '</span', 'wz118-', 'class=', 'timer-card']):
            return fallback
        return raw or fallback
    except Exception:
        try:
            if callable(_wz123_prev_extract_plain_interview_question):
                return _wz123_prev_extract_plain_interview_question(value, fallback)
        except Exception:
            pass
        return fallback


# =========================================================
# WorkZo v124 - Human interviewer realism + no repeated follow-ups
# Purpose:
# - Start with candidate name extracted from CV/session.
# - Generate varied JD/CV/company-aware questions instead of repeating impact prompts.
# - Add human micro-reactions: "Hmm", "okay", "interesting", etc.
# - Interrupt/coach when answers are too long, too vague, or too generic.
# - Make browser voice less robotic by selecting natural voices and using softer pacing.
# This patch is additive and only overrides interview helper functions used by the
# existing render_real_interview_simulation() flow.
# =========================================================

import random as _wz124_random
import re as _wz124_re
import json as _wz124_json
import html as _wz124_html
import time as _wz124_time


def _wz124_clean_text(value, limit=1200):
    try:
        text = str(value or "")
        text = _wz124_html.unescape(text)
        text = _wz124_re.sub(r"<[^>]+>", " ", text)
        text = _wz124_re.sub(r"\s+", " ", text).strip()
        return text[:limit]
    except Exception:
        return str(value or "")[:limit]


def _wz124_candidate_name_from_cv(cv_text=""):
    """Return a friendly first name from session state or the first plausible CV header line."""
    try:
        for key in [
            "candidate_first_name", "first_name", "user_first_name", "candidate_name", "full_name", "user_name"
        ]:
            value = _wz124_clean_text(st.session_state.get(key, ""), 80)
            if value and value.lower() not in {"there", "unknown", "not specified", "none"}:
                return value.split()[0].strip(" ,|•-")

        cv = cv_text or st.session_state.get("cv_text") or st.session_state.get("clean_structured_cv_text") or ""
        lines = [ln.strip() for ln in str(cv or "").splitlines() if ln.strip()]
        bad_words = {
            "cv", "resume", "curriculum", "vitae", "professional", "summary", "experience",
            "skills", "education", "projects", "languages", "contact", "email", "phone"
        }
        for ln in lines[:12]:
            clean = _wz124_re.sub(r"[^A-Za-zÀ-ÿ .'-]", " ", ln)
            clean = _wz124_re.sub(r"\s+", " ", clean).strip()
            if not clean:
                continue
            words = clean.split()
            low = clean.lower()
            if any(b in low for b in bad_words):
                continue
            if 1 <= len(words) <= 4 and len(clean) <= 60:
                first = words[0].strip(" ,|•-")
                if len(first) >= 2:
                    st.session_state["candidate_first_name"] = first
                    return first
    except Exception:
        pass
    return "there"


def _wz_voice_first_safe_name():
    return _wz124_candidate_name_from_cv()


def _wz124_role_company_phrase(role="", company=""):
    role = _wz124_clean_text(role or st.session_state.get("wz_ri_role") or st.session_state.get("target_role") or "this role", 120)
    company = _wz124_clean_text(company or st.session_state.get("wz_ri_company") or st.session_state.get("target_company") or "", 120)
    if company:
        return f"for {role} at {company}"
    return f"for {role}"


def _wz_voice_first_build_opening_question(cv_text: str, jd: str, role: str, company: str, language: str) -> str:
    """Human opening that uses candidate name and sets a natural interview tone."""
    name = _wz124_candidate_name_from_cv(cv_text)
    target = _wz124_role_company_phrase(role, company)
    openers = [
        f"Hi {name}, good to meet you. Let’s start simple — tell me about yourself and keep it relevant to {target}.",
        f"Hi {name}, welcome. To begin, give me a short introduction and connect your background to {target}.",
        f"Hi {name}, nice to meet you. Could you walk me through your background in about a minute, focusing on what matters for {target}?",
    ]
    return openers[int(_wz124_time.time()) % len(openers)]


def _wz124_extract_jd_topics(jd: str, role: str = ""):
    jd_low = str(jd or "").lower()
    topics = []
    checks = [
        ("SQL / data querying", ["sql", "query", "database"]),
        ("Python / automation", ["python", "pandas", "automation", "script"]),
        ("dashboard or reporting", ["dashboard", "tableau", "power bi", "report", "visualization", "visualisation"]),
        ("customer communication", ["customer", "client", "stakeholder", "communication", "support"]),
        ("troubleshooting", ["troubleshoot", "debug", "incident", "root cause", "problem"]),
        ("team collaboration", ["collaborat", "team", "cross-functional", "partner"]),
        ("business impact", ["kpi", "metric", "impact", "improve", "performance"]),
        ("language or market fit", ["german", "english", "language", "local", "market"]),
    ]
    for label, keys in checks:
        if any(k in jd_low for k in keys):
            topics.append(label)
    if not topics:
        role = _wz124_clean_text(role or "target role", 80)
        topics = [f"core requirement for {role}", "problem-solving", "communication", "business impact", "role motivation"]
    return topics[:6]


def _wz124_question_bank(cv_text: str, jd: str, role: str, company: str, idx: int):
    role_txt = _wz124_clean_text(role or "this role", 100)
    company_txt = _wz124_clean_text(company or "the company", 100)
    topics = _wz124_extract_jd_topics(jd, role_txt)
    topic = topics[idx % len(topics)] if topics else "the job requirement"
    company_specific = bool(company and company.lower() not in {"the company", "company", "not specified"})
    questions_by_dimension = [
        f"Looking at this job description, which requirement do you feel is your strongest match, and what proof from your CV supports that?",
        f"Can you walk me through one real example where you used {topic} in a practical situation?",
        f"Tell me about a time you solved a problem that is similar to what this {role_txt} role might face.",
        f"What part of this job description looks most challenging for you, and how would you close that gap quickly?",
        f"Give me one reason I should move you to the next round for {role_txt}, but make it specific and evidence-based.",
        f"How would your background be useful for {company_txt} specifically?" if company_specific else f"How would your background create value in this {role_txt} role, beyond just matching the title?",
        f"Describe a situation where you had to explain something technical or complex to another person. How did you make it clear?",
        f"Tell me about a project or task from your CV that best proves you can do this job.",
    ]
    return questions_by_dimension


def _wz124_human_prefix(idx=0, strict=False):
    friendly = ["Okay.", "Great.", "Alright.", "Thanks.", "Got it."]
    strict_phrases = ["Hmm, let me check something.", "Okay, I want to push a little deeper.", "Interesting — let’s make that more concrete.", "Right, now be specific."]
    phrases = strict_phrases if strict else friendly
    return phrases[idx % len(phrases)]


def _wz_voice_first_next_question(cv_text: str, jd: str, role: str, company: str, language: str, answers: list, idx: int) -> str:
    """Varied next question generator used when the interview starts."""
    asked = [
        _wz124_clean_text(q.get("question") if isinstance(q, dict) else q, 400).lower()
        for q in (answers or [])
    ]
    bank = _wz124_question_bank(cv_text, jd, role, company, idx)
    # Use deterministic variation so six generated questions are not clones.
    for offset in range(len(bank)):
        q = bank[(idx - 1 + offset) % len(bank)]
        q_key = _wz124_re.sub(r"[^a-z0-9]+", " ", q.lower()).strip()
        if not any(q_key[:45] in prev for prev in asked):
            prefix = _wz124_human_prefix(idx, strict=idx >= 3)
            return f"{prefix} {q}"
    return f"{_wz124_human_prefix(idx, strict=True)} Let’s take a different angle. What evidence from your CV best proves you can handle the most important requirement in this job description?"


def _wz124_seen_followup_key(text: str) -> str:
    text = _wz124_clean_text(text, 300).lower()
    text = _wz124_re.sub(r"[^a-z0-9]+", " ", text).strip()
    return text[:90]


def _wz124_next_followup(reason: str, question: str, answer: str, jd: str, role: str, company: str) -> str:
    if "wz124_asked_followups" not in st.session_state:
        st.session_state["wz124_asked_followups"] = []
    asked = set(st.session_state.get("wz124_asked_followups", []))
    role_txt = _wz124_clean_text(role or st.session_state.get("wz_ri_role") or "this role", 100)
    company_txt = _wz124_clean_text(company or st.session_state.get("wz_ri_company") or "the company", 100)
    jd_topics = _wz124_extract_jd_topics(jd, role_txt)
    topic = jd_topics[0] if jd_topics else "the key requirement"

    pools = {
        "too long": [
            "Can you summarize that in 30 seconds with only the situation, your action, and the result?",
            "Let me pause you there — what is the one main point you want me to remember?",
            "Can you give me the short version and connect it directly to this job?",
        ],
        "missing impact": [
            "What was the concrete outcome — time saved, fewer tickets, better quality, faster response, or happier users?",
            "How did your action help the team, customer, or business in a visible way?",
            "What changed after you did that, and how do you know it worked?",
        ],
        "missing JD connection": [
            f"Which exact requirement in this job description does that answer prove?",
            f"Connect that example to {topic}. Why does it matter for this role?",
            "If I compare your answer to the JD, what should I mark as the strongest match?",
        ],
        "generic for company": [
            f"Make that specific to {company_txt}. What would they care about in your answer?",
            f"How would that experience help {company_txt} in this role specifically?",
            "What company problem or team need does your answer solve?",
        ],
        "weak STAR": [
            "Can you restructure that as Situation, Action, and Result?",
            "What exactly did you do personally, not just the team?",
            "Give me the situation first, then your action, then the result.",
        ],
        "too short": [
            "Can you give me one real example from your CV?",
            "Add a specific situation. What happened, and what did you do?",
            "That is too brief. Give me one concrete example connected to the JD.",
        ],
    }
    default_pool = [
        "Can you make that more specific with one real example?",
        "What was your personal contribution in that example?",
        "What would your manager or customer say improved because of your work?",
    ]
    candidates = pools.get(reason, default_pool) + default_pool
    for candidate in candidates:
        key = _wz124_seen_followup_key(candidate)
        if key not in asked:
            st.session_state["wz124_asked_followups"] = list(asked | {key})
            return candidate
    # Last resort still varied by time.
    candidate = default_pool[int(_wz124_time.time()) % len(default_pool)]
    st.session_state["wz124_asked_followups"] = list(asked | {_wz124_seen_followup_key(candidate)})
    return candidate


def _wz124_answer_has_company_specificity(answer: str, company: str) -> bool:
    answer_low = str(answer or "").lower()
    company_low = str(company or "").lower().strip()
    if company_low and company_low in answer_low:
        return True
    return any(w in answer_low for w in ["product", "customer", "market", "users", "business", "team", "company", "industry"])


def _wz124_answer_has_jd_connection(answer: str, jd: str) -> bool:
    answer_low = str(answer or "").lower()
    jd_low = str(jd or "").lower()
    if not jd_low.strip():
        return True
    keywords = []
    for token in _wz124_re.findall(r"[a-zA-Z][a-zA-Z+#.]{2,}", jd_low):
        if token not in {"the", "and", "for", "with", "you", "our", "are", "will", "this", "that", "job", "role", "work", "team"}:
            keywords.append(token)
    keywords = list(dict.fromkeys(keywords))[:35]
    hits = sum(1 for k in keywords if k in answer_low)
    return hits >= 2


def _wz_ri_react_to_answer(question: str, answer: str, cv_text: str, jd: str, qa_pairs: list, language: str, personality: str):
    """Human, honest, non-repetitive interviewer reaction."""
    answer_text = _wz124_clean_text(answer, 8000)
    words = len(answer_text.split())
    elapsed = 0
    try:
        elapsed = _wz124_time.time() - float(st.session_state.get("wz_ri_question_started_at", _wz124_time.time()))
    except Exception:
        elapsed = 0
    role = st.session_state.get("wz_ri_role") or st.session_state.get("target_role") or "this role"
    company = st.session_state.get("wz_ri_company") or st.session_state.get("target_company") or ""

    # Detect quality signals.
    has_number = bool(_wz124_re.search(r"\b\d+\b|%|percent|reduced|increased|improved|saved|faster|fewer|more", answer_text, flags=_wz124_re.I))
    has_jd = _wz124_answer_has_jd_connection(answer_text, jd)
    has_company = _wz124_answer_has_company_specificity(answer_text, company) if company else True
    has_action = bool(_wz124_re.search(r"\b(I|my)\b|\bI\s+(built|created|handled|resolved|analyzed|analysed|improved|worked|led|documented|supported|used|designed|fixed)", answer_text, flags=_wz124_re.I))

    # Time/length interruption: this catches cases where the candidate talks for 2+ minutes.
    if elapsed > 115 or words > 210:
        reason = "too long"
        follow = _wz124_next_followup(reason, question, answer_text, jd, role, company)
        return {
            "reaction": "Okay, I’ll stop you there for a moment. You’re giving a lot of detail, but in a real interview I need the clearer version.",
            "needs_followup": True,
            "followup_question": follow,
            "interruption_reason": reason,
            "coach_note": "Keep answers under 75 seconds: situation → your action → result.",
        }
    if words < 25:
        reason = "too short"
        return {
            "reaction": "Hmm, that’s a little too short. I need one real example, not just a statement.",
            "needs_followup": True,
            "followup_question": _wz124_next_followup(reason, question, answer_text, jd, role, company),
            "interruption_reason": reason,
            "coach_note": "Add one specific example from your CV and connect it to the JD.",
        }
    if not has_action:
        reason = "weak STAR"
        return {
            "reaction": "Okay, interesting — but I’m not fully hearing what you personally did.",
            "needs_followup": True,
            "followup_question": _wz124_next_followup(reason, question, answer_text, jd, role, company),
            "interruption_reason": reason,
            "coach_note": "Use 'I did...' and describe your exact contribution.",
        }
    if not has_jd:
        reason = "missing JD connection"
        return {
            "reaction": "Got it. Now I want you to connect that more directly to the job description.",
            "needs_followup": True,
            "followup_question": _wz124_next_followup(reason, question, answer_text, jd, role, company),
            "interruption_reason": reason,
            "coach_note": "Tie your example to one exact requirement in the JD.",
        }
    if company and not has_company:
        reason = "generic for company"
        return {
            "reaction": "That’s a fair answer, but it still sounds a bit generic for this company.",
            "needs_followup": True,
            "followup_question": _wz124_next_followup(reason, question, answer_text, jd, role, company),
            "interruption_reason": reason,
            "coach_note": "Mention why your example matters for this company/team/product.",
        }
    if not has_number:
        reason = "missing impact"
        return {
            "reaction": "Okay, interesting. The example is relevant, but I’m still missing the result.",
            "needs_followup": True,
            "followup_question": _wz124_next_followup(reason, question, answer_text, jd, role, company),
            "interruption_reason": reason,
            "coach_note": "Add a truthful result. If you don’t know a number, describe the visible improvement.",
        }

    # Strong answer: react naturally and go deeper without repeating the same impact prompt.
    reactions = [
        "Okay, that’s a stronger answer — it has context and a result.",
        "Good, that feels more concrete.",
        "Interesting. That gives me better evidence.",
        "Alright, that’s clearer and more relevant.",
    ]
    follow = _wz124_next_followup("default", question, answer_text, jd, role, company)
    return {
        "reaction": reactions[len(st.session_state.get("wz_ri_answers", [])) % len(reactions)],
        "needs_followup": False,
        "followup_question": follow,
        "interruption_reason": "none",
        "coach_note": "Good structure. Keep this level of specificity.",
    }


def _wz_ri_auto_speak(text: str, key_suffix: str = "question"):
    """More natural browser speech: slower, warmer, picks a better available voice."""
    safe_text = _wz124_json.dumps(_wz124_clean_text(text, 1600))
    safe_key = _wz124_re.sub(r"[^a-zA-Z0-9_]+", "_", str(key_suffix))
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
      function pickVoice() {{
          const voices = window.speechSynthesis.getVoices() || [];
          const preferred = [
            'Google UK English Female', 'Google US English', 'Microsoft Sonia', 'Microsoft Jenny',
            'Microsoft Aria', 'Samantha', 'Karen', 'Daniel', 'Moira', 'Tessa'
          ];
          for (const name of preferred) {{
            const v = voices.find(x => (x.name || '').toLowerCase().includes(name.toLowerCase()));
            if (v) return v;
          }}
          return voices.find(v => (v.lang || '').toLowerCase().startsWith('en')) || voices[0] || null;
      }}
      function humanizeText(t) {{
          return String(t || '')
            .replace(/—/g, ', ')
            .replace(/\s+/g, ' ')
            .replace(/([.!?])\s+/g, '$1 ');
      }}
      function speak_{safe_key}() {{
          const msg = new SpeechSynthesisUtterance(humanizeText({safe_text}));
          const voice = pickVoice();
          if (voice) msg.voice = voice;
          msg.rate = 0.86;
          msg.pitch = 0.98;
          msg.volume = 1.0;
          window.speechSynthesis.cancel();
          setTimeout(() => window.speechSynthesis.speak(msg), 120);
      }}
      const btn = document.getElementById("wz_ri_speak_{safe_key}");
      btn.onclick = speak_{safe_key};
      if (speechSynthesis.onvoiceschanged !== undefined) {{
          speechSynthesis.onvoiceschanged = function() {{}};
      }}
      setTimeout(function() {{
          try {{ speak_{safe_key}(); }} catch(e) {{}}
      }}, 700);
      </script>
    </body>
    </html>
    """
    try:
        import streamlit.components.v1 as components
        components.html(html_code, height=48)
    except Exception:
        try:
            st.caption("Voice playback is unavailable in this browser. You can still read the question.")
        except Exception:
            pass


def _wz124_live_interruption_notice():
    """Optional UI warning during long answers. Called from render if available; safe no-op otherwise."""
    try:
        elapsed = _wz124_time.time() - float(st.session_state.get("wz_ri_question_started_at", _wz124_time.time()))
        if elapsed > 115:
            st.warning("Interviewer: I’ll pause you there soon — please wrap this into one clear result sentence.")
        elif elapsed > 80:
            st.info("Interviewer cue: keep it tight now — result and relevance only.")
    except Exception:
        pass

