
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



def _wz_ri_country_rules(country: str) -> dict:
    """Subtle country adaptation without stereotyping."""
    c = str(country or "").strip().lower()
    rules = {
        "communication_expectation": "clear, professional, structured",
        "confidence_style": "balanced",
        "interview_pacing": "moderate",
        "formality": "professional",
        "what_recruiters_value": ["specific examples", "measurable impact", "role relevance"],
    }
    if "germany" in c or "deutsch" in c:
        rules.update({
            "communication_expectation": "structured, precise, direct, realistic claims",
            "confidence_style": "moderate and evidence-backed",
            "interview_pacing": "step-by-step",
            "formality": "formal-professional",
            "what_recruiters_value": ["clear process", "truthful scope", "technical precision", "structured examples"],
        })
    elif "usa" in c or "united states" in c or "america" in c:
        rules.update({
            "communication_expectation": "impact-first, concise, confident",
            "confidence_style": "confident with metrics",
            "interview_pacing": "fast and outcome-focused",
            "what_recruiters_value": ["measurable impact", "ownership", "leadership", "business results"],
        })
    elif "uk" in c or "united kingdom" in c or "britain" in c:
        rules.update({
            "communication_expectation": "professional, balanced, collaborative",
            "confidence_style": "moderate confidence",
            "what_recruiters_value": ["teamwork", "clear reasoning", "professional communication"],
        })
    elif "india" in c:
        rules.update({
            "communication_expectation": "clear, skill-specific, ATS/recruiter-friendly",
            "confidence_style": "confident but evidence-based",
            "what_recruiters_value": ["skills proof", "project examples", "adaptability", "communication"],
        })
    return rules


def _wz_ri_role_rules(role: str, jd: str) -> dict:
    text = f"{role or ''} {jd or ''}".lower()
    rules = {
        "role_family": "general",
        "focus": ["role fit", "communication", "specific examples", "measurable impact"],
        "likely_followups": ["Give one specific example.", "What was your individual contribution?", "What was the result?"],
    }
    if any(x in text for x in ["data analyst", "business analyst", "analytics", "sql", "tableau", "power bi", "dashboard"]):
        rules.update({
            "role_family": "data_analytics",
            "focus": ["SQL depth", "dashboarding", "business impact", "metrics", "stakeholder communication", "data cleaning"],
            "likely_followups": ["Which metric improved?", "What SQL logic did you use?", "Who used the dashboard?", "How did this influence a decision?"],
        })
    elif any(x in text for x in ["customer success", "account manager", "client success"]):
        rules.update({
            "role_family": "customer_success",
            "focus": ["client communication", "retention", "escalation handling", "prioritization", "relationship building"],
            "likely_followups": ["How did you handle the difficult customer?", "What was the retention or satisfaction impact?", "How did you prioritize accounts?"],
        })
    elif any(x in text for x in ["support", "helpdesk", "service desk", "technical support", "it support"]):
        rules.update({
            "role_family": "support_it",
            "focus": ["troubleshooting", "ticket ownership", "SLA", "customer communication", "root-cause analysis"],
            "likely_followups": ["How did you diagnose the issue?", "What was the SLA impact?", "How did you communicate with the customer?"],
        })
    return rules


def _wz_ri_default_candidate_state() -> dict:
    return {
        "answers_seen": 0,
        "metrics_usage": 0,
        "generic_answers": 0,
        "missing_impact_count": 0,
        "ownership_clarity": 5,
        "confidence_level": 5,
        "technical_depth": 5,
        "communication_clarity": 5,
        "star_quality": 5,
        "repeated_weaknesses": [],
        "unproven_claims": [],
        "last_recruiter_pressure": "neutral",
    }


def _wz_ri_get_candidate_state() -> dict:
    state = st.session_state.get("wz_ri_candidate_state")
    if not isinstance(state, dict):
        state = _wz_ri_default_candidate_state()
        st.session_state["wz_ri_candidate_state"] = state
    return state


def _wz_ri_answer_quality_flags(answer: str, jd: str, cv_text: str = "", question: str = "") -> dict:
    text = str(answer or "")
    words = len(text.split())
    lower = text.lower()
    jd_lower = str(jd or "").lower()
    cv_lower = str(cv_text or "").lower()

    number_patterns = [r"\b\d+\s?%", r"\b\d+\s?(hours?|days?|weeks?|months?)\b", r"\b\d+\+?\s?(tickets?|users?|customers?|reports?|dashboards?|cases?)\b", r"\b\d+[,.]?\d*\b"]
    has_metric = any(re.search(pat, lower) for pat in number_patterns)
    has_impact_words = any(x in lower for x in ["improved", "reduced", "increased", "saved", "resolved", "optimized", "automated", "impact", "result", "outcome"])
    has_ownership = any(x in lower for x in ["i ", "i was", "i built", "i created", "i handled", "i analyzed", "my role", "my responsibility", "i worked"])
    star_signals = sum(1 for x in ["situation", "task", "action", "result", "because", "so i", "then", "finally"] if x in lower)

    jd_tools = [tool for tool in ["sql", "python", "excel", "tableau", "power bi", "api", "dashboard", "crm", "sla", "ticket", "report"] if tool in jd_lower]
    missed_tools = [tool for tool in jd_tools if tool not in lower]
    mentioned_tools = [tool for tool in jd_tools if tool in lower]

    vague_phrases = ["etc", "many things", "various", "good communication", "hard working", "team player", "helped", "worked on", "responsible for"]
    vague = words < 35 or sum(1 for p in vague_phrases if p in lower) >= 2
    too_long = words > 135
    off_topic = words > 25 and len(set(lower.split()).intersection(set(jd_lower.split()))) < 4 if jd_lower else False
    claim_words = [x for x in ["sql", "python", "tableau", "power bi", "dashboard", "stakeholder", "customer", "analytics"] if x in lower and x not in cv_lower]

    return {
        "words": words,
        "has_metric": has_metric,
        "has_impact": bool(has_impact_words or has_metric),
        "has_ownership": has_ownership,
        "star_signals": star_signals,
        "star_quality_estimate": min(10, max(1, 2 + star_signals * 2 + (2 if has_metric else 0) + (1 if has_ownership else 0))),
        "missed_tools": missed_tools[:5],
        "mentioned_tools": mentioned_tools[:5],
        "vague": vague,
        "too_long": too_long,
        "off_topic": off_topic,
        "unproven_claims": claim_words[:5],
        "missing_impact": not has_metric and not has_impact_words,
        "missing_ownership": not has_ownership,
    }


def _wz_ri_update_candidate_state(flags: dict, reaction: dict) -> dict:
    state = dict(_wz_ri_get_candidate_state())
    state["answers_seen"] = int(state.get("answers_seen", 0) or 0) + 1
    if flags.get("has_metric"):
        state["metrics_usage"] = int(state.get("metrics_usage", 0) or 0) + 1
    if flags.get("vague"):
        state["generic_answers"] = int(state.get("generic_answers", 0) or 0) + 1
    if flags.get("missing_impact"):
        state["missing_impact_count"] = int(state.get("missing_impact_count", 0) or 0) + 1

    def clamp(v):
        return max(1, min(10, int(round(v))))

    state["ownership_clarity"] = clamp(state.get("ownership_clarity", 5) + (1 if flags.get("has_ownership") else -1))
    state["technical_depth"] = clamp(state.get("technical_depth", 5) + (1 if flags.get("mentioned_tools") else -1 if flags.get("missed_tools") else 0))
    state["communication_clarity"] = clamp(state.get("communication_clarity", 5) + (-1 if flags.get("too_long") or flags.get("off_topic") else 1 if not flags.get("vague") else 0))
    state["star_quality"] = clamp(flags.get("star_quality_estimate", state.get("star_quality", 5)))
    state["confidence_level"] = clamp(state.get("confidence_level", 5) + (1 if flags.get("has_metric") and flags.get("has_ownership") else -1 if flags.get("vague") else 0))

    weaknesses = list(state.get("repeated_weaknesses", []) or [])
    for label, cond in [
        ("missing measurable result", flags.get("missing_impact")),
        ("too general", flags.get("vague")),
        ("weak ownership", flags.get("missing_ownership")),
        ("too long", flags.get("too_long")),
        ("missed role tools", bool(flags.get("missed_tools"))),
    ]:
        if cond and label not in weaknesses:
            weaknesses.append(label)
    state["repeated_weaknesses"] = weaknesses[-6:]
    state["unproven_claims"] = list(dict.fromkeys((state.get("unproven_claims", []) or []) + (flags.get("unproven_claims", []) or [])))[-8:]
    state["last_recruiter_pressure"] = str(reaction.get("interruption_reason") or "neutral")
    st.session_state["wz_ri_candidate_state"] = state
    return state


def _wz_ri_render_intelligence_panel():
    state = _wz_ri_get_candidate_state()
    if int(state.get("answers_seen", 0) or 0) <= 0:
        return
    with st.expander("🧠 Live recruiter intelligence", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("STAR quality", f"{state.get('star_quality', 5)}/10")
        c2.metric("Metrics used", str(state.get("metrics_usage", 0)))
        c3.metric("Ownership", f"{state.get('ownership_clarity', 5)}/10")
        c4.metric("Clarity", f"{state.get('communication_clarity', 5)}/10")
        weaknesses = state.get("repeated_weaknesses", []) or []
        if weaknesses:
            st.caption("Recruiter memory: " + " · ".join(weaknesses[-4:]))


def _wz_ri_react_to_answer(question: str, answer: str, cv_text: str, jd: str, qa_pairs: list, language: str, personality: str):
    flags = _wz_ri_answer_quality_flags(answer, jd, cv_text=cv_text, question=question)
    candidate_state = _wz_ri_get_candidate_state()
    country = st.session_state.get("selected_country") or st.session_state.get("user_country") or st.session_state.get("country") or "Global"
    role = st.session_state.get("wz_ri_role") or st.session_state.get("target_role") or st.session_state.get("target_job_title") or ""
    country_rules = _wz_ri_country_rules(country)
    role_rules = _wz_ri_role_rules(role, jd)

    if flags["too_long"]:
        reaction = {
            "reaction": "I'll stop you there — that was too long.",
            "needs_followup": True,
            "followup_question": "Give me the same answer again in 45 seconds: one example, your action, and one measurable result.",
            "interruption_reason": "too long",
            "live_reaction": "Too long",
            "pressure_change": "+1",
        }
        _wz_ri_update_candidate_state(flags, reaction)
        return reaction

    prompt = f"""
You are WorkZo's Recruiter Intelligence Engine, not a generic chatbot.
You behave like a realistic {personality.lower()} recruiter.

Your job: evaluate the latest answer, remember repeated weaknesses, and decide the next recruiter move.

Current question:
{question}

User answer:
{answer}

Previous Q&A memory:
{json.dumps(qa_pairs, ensure_ascii=False)}

Candidate state memory:
{json.dumps(candidate_state, ensure_ascii=False)}

Detected answer signals:
{json.dumps(flags, ensure_ascii=False)}

Role intelligence:
{json.dumps(role_rules, ensure_ascii=False)}

Country expectation layer:
{json.dumps(country_rules, ensure_ascii=False)}

CV excerpt:
{cv_text[:4500]}

Job Description excerpt:
{jd[:4500]}

Return ONLY valid JSON:
{{
  "reaction": "brief human recruiter reaction",
  "needs_followup": true,
  "followup_question": "specific pressure follow-up question",
  "interruption_reason": "too vague|too long|missing impact|weak ownership|missing tools|off-topic|strong answer|none",
  "live_reaction": "Too broad|Good metric|Weak ownership|Can you quantify that?|Strong STAR|Avoided question",
  "pressure_change": "+1|0|-1",
  "memory_note": "what the recruiter will remember for later"
}}

Recruiter behavior rules:
- If answer is generic, challenge it directly.
- If no metric/result, ask for one measurable outcome.
- If ownership is unclear, ask what the candidate personally did.
- If role tools are missing, ask about the most relevant missing tool.
- If this repeats an earlier weakness, mention that briefly: "Earlier you also..."
- If answer is strong, acknowledge briefly and go deeper.
- Adapt subtly to country expectations without stereotypes.
- Keep reaction firm, useful, and human. Do not be rude.
- Language: {language}
"""
    raw = _wz_ri_ai(prompt, json_mode=True, language=language)
    data = _wz_ri_json(raw, {})
    if not isinstance(data, dict) or not data:
        if flags["vague"]:
            data = {
                "reaction": "That's still too general.",
                "needs_followup": True,
                "followup_question": "Give me one specific example from your experience. What did you personally do and what changed because of it?",
                "interruption_reason": "too vague",
                "live_reaction": "Too broad",
                "pressure_change": "+1",
                "memory_note": "candidate gave a generic answer",
            }
        elif flags["missing_impact"]:
            data = {
                "reaction": "I’m missing the business result.",
                "needs_followup": True,
                "followup_question": "What was the measurable result — time saved, tickets reduced, users helped, or quality improved?",
                "interruption_reason": "missing impact",
                "live_reaction": "Can you quantify that?",
                "pressure_change": "+1",
                "memory_note": "candidate did not quantify impact",
            }
        elif flags["missed_tools"]:
            data = {
                "reaction": "Okay, but I expected more role-specific detail.",
                "needs_followup": True,
                "followup_question": f"This role mentions {', '.join(flags['missed_tools'][:3])}. Which of these have you actually used, and in what context?",
                "interruption_reason": "missing tools",
                "live_reaction": "Missing role tools",
                "pressure_change": "+1",
                "memory_note": "candidate missed key tools",
            }
        else:
            data = {
                "reaction": "Good, that gives me useful context.",
                "needs_followup": False,
                "followup_question": "",
                "interruption_reason": "strong answer",
                "live_reaction": "Good example",
                "pressure_change": "-1",
                "memory_note": "candidate answered clearly",
            }

    data.setdefault("reaction", "Hmm...")
    data.setdefault("needs_followup", False)
    data.setdefault("followup_question", "")
    data.setdefault("interruption_reason", "none")
    data.setdefault("live_reaction", "Recruiter thinking")
    data.setdefault("pressure_change", "0")
    data.setdefault("memory_note", "")
    _wz_ri_update_candidate_state(flags, data)
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
        "wz_ri_candidate_state": _wz_ri_default_candidate_state(),
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    cv_text = _wz_ri_get_cv_text()
    default_jd = _wz_ri_get_jd_text()

    language_options = ["English", "German", "Dutch", "French", "Spanish", "Portuguese", "Italian", "Arabic", "Hindi", "Tamil", "Polish", "Turkish", "Swedish", "Danish", "Norwegian", "Finnish", "Czech", "Greek", "Japanese", "Korean", "Chinese"]
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
            st.session_state["wz_ri_candidate_state"] = _wz_ri_default_candidate_state()
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
                "wz_ri_candidate_state",
            ]:
                st.session_state.pop(key, None)
            st.rerun()

    _wz_ri_render_dialogue()
    _wz_ri_render_intelligence_panel()

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
                "wz_ri_candidate_state",
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

Recruiter Intelligence Memory:
{json.dumps(st.session_state.get("wz_ri_candidate_state", {}), indent=2, ensure_ascii=False)}

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

    language_options = ["Auto", "English", "German", "Dutch", "French", "Spanish", "Portuguese", "Italian", "Arabic", "Hindi", "Tamil", "Polish", "Turkish", "Swedish", "Danish", "Norwegian", "Finnish", "Czech", "Greek", "Japanese", "Korean", "Chinese"]
    answer_language_options = ["Same as interview", "English", "German", "Dutch", "French", "Spanish", "Portuguese", "Italian", "Arabic", "Hindi", "Tamil", "Polish", "Turkish", "Swedish", "Danish", "Norwegian", "Finnish", "Czech", "Greek", "Japanese", "Korean", "Chinese", "Any language"]
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
            st.session_state["wz_ri_candidate_state"] = _wz_ri_default_candidate_state()
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
    _wz_ri_render_intelligence_panel()

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
            st.session_state["wz_ri_candidate_state"] = _wz_ri_default_candidate_state()
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

# =========================================================
# WorkZo v160 - Interview Memory + Weak-Area Practice Loop
# Additive patch: preserves the original interview module above.
# Adds:
# - Interview history saved in session_state and optional local JSON file
# - Weak-area memory across sessions
# - Strongest / weakest answer tracking
# - Next practice goal before the next interview starts
# - More recruiter-like follow-ups for vague, generic, metric-free answers
# =========================================================

import json as _wz160_json
import time as _wz160_time
import re as _wz160_re
from pathlib import Path as _wz160_Path

_WZ160_HISTORY_FILE = _wz160_Path("workzo_interview_history.json")


def _wz160_safe_int(value, default=0):
    try:
        return int(float(value))
    except Exception:
        return default


def _wz160_as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    if isinstance(value, str):
        parts = [_p.strip(" -•\t") for _p in value.split("\n")]
        return [p for p in parts if p]
    return [str(value)] if str(value).strip() else []


def _wz160_load_history():
    """Load interview history from session_state first, then optional local JSON."""
    try:
        existing = st.session_state.get("wz_interview_history")
        if isinstance(existing, list):
            return existing
    except Exception:
        pass

    history = []
    try:
        if _WZ160_HISTORY_FILE.exists():
            raw = _WZ160_HISTORY_FILE.read_text(encoding="utf-8")
            parsed = _wz160_json.loads(raw or "[]")
            if isinstance(parsed, list):
                history = parsed[-20:]
    except Exception:
        history = []

    try:
        st.session_state["wz_interview_history"] = history
    except Exception:
        pass
    return history


def _wz160_save_history(history):
    """Save interview history in Streamlit session and best-effort local JSON."""
    if not isinstance(history, list):
        history = []
    history = history[-20:]
    try:
        st.session_state["wz_interview_history"] = history
    except Exception:
        pass
    try:
        _WZ160_HISTORY_FILE.write_text(_wz160_json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass
    return history


def _wz160_answer_text(item):
    try:
        if isinstance(item, dict):
            return str(item.get("answer", "") or "").strip()
    except Exception:
        pass
    return str(item or "").strip()


def _wz160_question_text(item):
    try:
        if isinstance(item, dict):
            return str(item.get("question", "") or "").strip()
    except Exception:
        pass
    return ""


def _wz160_detect_weak_areas_from_answers(qa_pairs, reactions=None, result=None, jd=""):
    """Deterministic weak-area detection so history works even if AI JSON is incomplete."""
    reactions = reactions if isinstance(reactions, list) else []
    result = result if isinstance(result, dict) else {}
    weak = []

    for item in _wz160_as_list(result.get("top_3_mistakes")):
        weak.append(item)
    for item in _wz160_as_list(result.get("what_hurt_you_most")):
        weak.append(item)
    for item in _wz160_as_list(result.get("missed_opportunities")):
        weak.append(item)

    all_answers = "\n".join(_wz160_answer_text(x) for x in (qa_pairs or []))
    lower = all_answers.lower()
    words = len(all_answers.split())

    if words < 80:
        weak.append("Answers were too short and did not give enough proof.")
    if not any(x in lower for x in ["%", "result", "impact", "improved", "reduced", "increased", "saved", "measured", "outcome"]):
        weak.append("Missing measurable impact or business result.")
    if not any(x in lower for x in ["situation", "task", "action", "result", "when", "during", "i did", "i used", "i built", "i handled"]):
        weak.append("Weak STAR structure.")
    if jd:
        jd_words = {w for w in _wz160_re.findall(r"[a-zA-Z]{4,}", jd.lower()) if len(w) > 4}
        answer_words = set(_wz160_re.findall(r"[a-zA-Z]{4,}", lower))
        overlap = len(jd_words.intersection(answer_words))
        if jd_words and overlap < 5:
            weak.append("Answers did not connect strongly enough to the job description.")

    for r in reactions:
        if isinstance(r, dict):
            reason = str(r.get("interruption_reason") or "").strip().lower()
            if reason and reason != "none":
                weak.append(f"Interviewer flagged: {reason}.")

    # Deduplicate while preserving order
    seen = set()
    clean = []
    for item in weak:
        key = str(item).strip().lower()
        if key and key not in seen:
            seen.add(key)
            clean.append(str(item).strip())
    return clean[:6]


def _wz160_pick_strongest_answer(qa_pairs):
    best = {"question": "", "answer": "", "reason": ""}
    best_score = -1
    for item in qa_pairs or []:
        ans = _wz160_answer_text(item)
        if not ans:
            continue
        lower = ans.lower()
        score = 0
        score += min(30, len(ans.split()) // 3)
        score += 20 if any(x in lower for x in ["result", "impact", "improved", "reduced", "increased", "%", "outcome"]) else 0
        score += 15 if any(x in lower for x in ["example", "project", "case", "customer", "team", "stakeholder"]) else 0
        score += 15 if any(x in lower for x in ["i did", "i used", "i built", "i created", "i handled", "i solved", "i analyzed"]) else 0
        if score > best_score:
            best_score = score
            best = {
                "question": _wz160_question_text(item),
                "answer": ans[:800],
                "reason": "This answer had the clearest proof, structure, or relevance compared with the others.",
            }
    return best


def _wz160_pick_weakest_answer(qa_pairs, result=None):
    result = result if isinstance(result, dict) else {}
    try:
        wanted = int(result.get("weakest_answer_question_number", 1)) - 1
    except Exception:
        wanted = 0
    if isinstance(qa_pairs, list) and 0 <= wanted < len(qa_pairs):
        item = qa_pairs[wanted]
        return {
            "question": _wz160_question_text(item),
            "answer": _wz160_answer_text(item)[:800],
            "reason": "Marked as weakest by the final interview evaluation.",
        }

    worst = {"question": "", "answer": "", "reason": ""}
    worst_score = 10**9
    for item in qa_pairs or []:
        ans = _wz160_answer_text(item)
        if not ans:
            continue
        lower = ans.lower()
        score = len(ans.split())
        score += 25 if any(x in lower for x in ["result", "impact", "improved", "reduced", "increased", "%", "outcome"]) else 0
        score += 15 if any(x in lower for x in ["example", "project", "case", "customer", "team"]) else 0
        if score < worst_score:
            worst_score = score
            worst = {
                "question": _wz160_question_text(item),
                "answer": ans[:800],
                "reason": "This answer looked least specific or least measurable.",
            }
    return worst


def _wz160_next_practice_goal(weak_areas):
    text = " ".join(_wz160_as_list(weak_areas)).lower()
    if "measurable" in text or "impact" in text or "result" in text:
        return "Today we’ll focus on giving numbers, outcomes, or measurable impact in every answer."
    if "star" in text or "structure" in text:
        return "Today we’ll focus on STAR structure: situation, task, action, result."
    if "job description" in text or "keyword" in text or "relevance" in text:
        return "Today we’ll focus on connecting every answer directly to the target job description."
    if "too short" in text or "proof" in text or "vague" in text:
        return "Today we’ll focus on proving claims with one specific example."
    return "Today we’ll focus on making every answer specific, concise, and recruiter-ready."


def _wz160_build_history_entry(result, company="", role="", language=""):
    qa_pairs = list(st.session_state.get("wz_ri_answers", []) or [])
    reactions = list(st.session_state.get("wz_ri_live_reactions", []) or [])
    jd = str(st.session_state.get("real_interview_jd_saved") or st.session_state.get("last_understand_job_description") or "")
    result = result if isinstance(result, dict) else {}
    weak_areas = _wz160_detect_weak_areas_from_answers(qa_pairs, reactions, result, jd)
    strongest = _wz160_pick_strongest_answer(qa_pairs)
    weakest = _wz160_pick_weakest_answer(qa_pairs, result)
    next_goal = _wz160_next_practice_goal(weak_areas)
    score = _wz160_safe_int(result.get("overall_score"), 0)

    return {
        "created_at": _wz160_time.strftime("%Y-%m-%d %H:%M:%S"),
        "company": str(company or st.session_state.get("target_company", "") or ""),
        "role": str(role or st.session_state.get("target_role", "") or st.session_state.get("target_job_title", "") or ""),
        "language": str(language or st.session_state.get("wz_ri_interview_language", "English") or "English"),
        "score": score,
        "hiring_decision": str(result.get("hiring_decision") or result.get("final_readiness_message") or ""),
        "weak_areas": weak_areas,
        "strongest_answer": strongest,
        "weakest_answer": weakest,
        "next_practice_goal": next_goal,
        "answer_count": len([x for x in qa_pairs if _wz160_answer_text(x)]),
    }


def _wz160_store_interview_result(result, company="", role="", language=""):
    try:
        entry = _wz160_build_history_entry(result, company, role, language)
        history = _wz160_load_history()
        # Avoid duplicate save on rerun for the same final result
        latest_key = f"{entry.get('created_at')}::{entry.get('score')}::{entry.get('role')}::{entry.get('answer_count')}"
        if st.session_state.get("wz160_last_saved_history_key") != latest_key:
            history.append(entry)
            _wz160_save_history(history)
            st.session_state["wz160_last_saved_history_key"] = latest_key
            st.session_state["wz_last_interview_weak_areas"] = entry.get("weak_areas", [])
            st.session_state["wz_last_interview_next_goal"] = entry.get("next_practice_goal", "")
        return entry
    except Exception:
        return {}


def _wz160_render_history_preview():
    """Show before-start memory so users feel WorkZo remembers their last interview."""
    try:
        history = _wz160_load_history()
        if not history:
            return
        last = history[-1]
        weak = _wz160_as_list(last.get("weak_areas"))[:3]
        goal = str(last.get("next_practice_goal") or _wz160_next_practice_goal(weak))
        score = last.get("score", "—")
        role = last.get("role") or "your last role"
        st.markdown(
            f"""
            <div style="border:1px solid rgba(59,130,246,.28);border-radius:18px;padding:16px;background:rgba(15,23,42,.45);margin:12px 0;">
              <div style="color:#93c5fd;font-size:.78rem;font-weight:850;text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px;">Last interview memory</div>
              <div style="color:#f8fafc;font-weight:850;font-size:1.02rem;margin-bottom:6px;">Last score: {html.escape(str(score))}/100 · {html.escape(str(role))}</div>
              <div style="color:#cbd5e1;font-size:.92rem;line-height:1.45;">{html.escape(goal)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if weak:
            with st.expander("Weak areas from last interview", expanded=False):
                for item in weak:
                    st.markdown(f"- {html.escape(str(item))}")
    except Exception:
        pass


def _wz160_render_history_panel():
    try:
        history = _wz160_load_history()
        if not history:
            return
        st.markdown("### Interview history & next practice loop")
        latest = history[-1]
        st.info(str(latest.get("next_practice_goal") or "Practice again with stronger examples."))

        c1, c2, c3 = st.columns(3)
        c1.metric("Last score", f"{latest.get('score', '—')}/100")
        c2.metric("Answers saved", str(latest.get("answer_count", 0)))
        c3.metric("Sessions", str(len(history)))

        weak = _wz160_as_list(latest.get("weak_areas"))
        if weak:
            st.markdown("#### Saved weak areas")
            for item in weak[:5]:
                st.markdown(f"- {item}")

        strongest = latest.get("strongest_answer") if isinstance(latest.get("strongest_answer"), dict) else {}
        weakest = latest.get("weakest_answer") if isinstance(latest.get("weakest_answer"), dict) else {}
        a, b = st.columns(2)
        with a:
            with st.expander("Strongest answer", expanded=False):
                st.caption(str(strongest.get("question") or ""))
                st.write(strongest.get("answer") or "No strongest answer saved yet.")
                st.caption(strongest.get("reason") or "")
        with b:
            with st.expander("Weakest answer to retry", expanded=True):
                st.caption(str(weakest.get("question") or ""))
                st.write(weakest.get("answer") or "No weakest answer saved yet.")
                st.caption(str(weakest.get("reason") or ""))

        if len(history) >= 2:
            prev_score = _wz160_safe_int(history[-2].get("score"), 0)
            cur_score = _wz160_safe_int(history[-1].get("score"), 0)
            delta = cur_score - prev_score
            if delta > 0:
                st.success(f"Progress: your score improved by {delta} points from the previous session.")
            elif delta < 0:
                st.warning(f"Your score dropped by {abs(delta)} points. Repeat the weakest-answer practice before the next full interview.")
            else:
                st.caption("Score stayed the same. Focus on the saved weak area next.")
    except Exception:
        pass


# Capture existing functions and extend them safely.
try:
    _wz160_previous_react_to_answer = _wz_ri_react_to_answer
except Exception:
    _wz160_previous_react_to_answer = None


def _wz_ri_react_to_answer(question: str, answer: str, cv_text: str, jd: str, qa_pairs: list, language: str, personality: str):
    """Recruiter-style reaction override with sharper detection and memory-aware probing."""
    try:
        flags = _wz_ri_answer_quality_flags(answer, jd) if callable(globals().get("_wz_ri_answer_quality_flags")) else {}
    except Exception:
        flags = {}

    answer_text = str(answer or "").strip()
    lower = answer_text.lower()
    words = len(answer_text.split())
    history = _wz160_load_history()
    last_goal = str(history[-1].get("next_practice_goal", "")) if history else ""

    has_metric = bool(_wz160_re.search(r"\b\d+\s*(%|percent|users?|customers?|tickets?|minutes?|hours?|days?|weeks?|months?|years?|€|\$|k|m)?\b", lower))
    has_result = any(x in lower for x in ["result", "impact", "improved", "reduced", "increased", "saved", "measured", "outcome", "faster", "better"])
    has_example = any(x in lower for x in ["for example", "one example", "in my previous", "in my role", "during", "project", "case", "customer"])
    jd_words = {w for w in _wz160_re.findall(r"[a-zA-Z]{5,}", str(jd or "").lower())}
    answer_words = set(_wz160_re.findall(r"[a-zA-Z]{5,}", lower))
    jd_overlap = len(jd_words.intersection(answer_words)) if jd_words else 99

    if words < 25:
        return {
            "reaction": "That’s too short. I don’t have enough evidence to evaluate you.",
            "needs_followup": True,
            "followup_question": "Prove it with one example. What happened, what did you do, and what changed?",
            "interruption_reason": "too short",
            "coach_note": "Give one specific example, not a general statement.",
        }
    if words > 145 or flags.get("too_long"):
        return {
            "reaction": "I’m going to stop you there — you’re losing me.",
            "needs_followup": True,
            "followup_question": "Answer in 45 seconds: result first, then one example, then why it matters for this job.",
            "interruption_reason": "too long",
            "coach_note": "Lead with the result and cut background details.",
        }
    if not has_example:
        return {
            "reaction": "That sounds generic.",
            "needs_followup": True,
            "followup_question": "Give me one real example from your CV. What exactly did you do?",
            "interruption_reason": "vague claim",
            "coach_note": "Recruiters need proof, not broad claims.",
        }
    if not has_metric and not has_result:
        return {
            "reaction": "I’m missing the impact.",
            "needs_followup": True,
            "followup_question": "Give me numbers. By how much did it improve, how did you measure it, or what changed operationally?",
            "interruption_reason": "missing metric",
            "coach_note": "Add a truthful number, outcome, speed, quality, customer result, or business impact.",
        }
    if jd_words and jd_overlap < 4:
        return {
            "reaction": "I’m not hearing the connection to this job yet.",
            "needs_followup": True,
            "followup_question": "Connect that answer to the job description. Which requirement does this prove?",
            "interruption_reason": "not relevant to JD",
            "coach_note": "Use job keywords only if they are true for your experience.",
        }
    if last_goal and any(x in last_goal.lower() for x in ["numbers", "measurable", "impact"]) and not has_metric:
        return {
            "reaction": "This is the same issue as last time: no measurable outcome.",
            "needs_followup": True,
            "followup_question": "Try again with a number, comparison, customer result, or measurable improvement.",
            "interruption_reason": "repeated weak area",
            "coach_note": last_goal,
        }

    if callable(_wz160_previous_react_to_answer):
        try:
            data = _wz160_previous_react_to_answer(question, answer, cv_text, jd, qa_pairs, language, personality)
            if isinstance(data, dict):
                data.setdefault("coach_note", "Good. Keep answers specific, measurable, and tied to the job.")
                return data
        except Exception:
            pass

    return {
        "reaction": "Good. That gives me something concrete to evaluate.",
        "needs_followup": False,
        "followup_question": "",
        "interruption_reason": "none",
        "coach_note": "This answer had enough proof to move forward.",
    }


try:
    _wz160_previous_finish_and_score = _wz_ri_finish_and_score
except Exception:
    _wz160_previous_finish_and_score = None


def _wz_ri_finish_and_score(cv_text: str, jd: str, company: str, role: str, website: str, language: str):
    """Finish interview and save history immediately when final score is created."""
    st.markdown("### Closing")
    st.info("That’s all from my side. We’ll wrap up here.")

    if st.button("Show Final Feedback", key="wz_ri_show_final_feedback_v160", use_container_width=True):
        answers = list(st.session_state.get("wz_ri_answers", []))
        with st.spinner("Reconstructing interviewer impression and saving your practice memory..."):
            _wz160_time.sleep(1.0)
            result = _wz_ri_score_full_interview(
                cv_text=cv_text,
                jd=jd,
                company=company,
                role=role,
                qa_pairs=answers,
                reactions=st.session_state.get("wz_ri_live_reactions", []),
                language=language,
            )
            entry = _wz160_store_interview_result(result, company, role, language)
            if isinstance(result, dict):
                result["saved_practice_memory"] = entry
        st.session_state["wz_ri_final_score"] = result
        st.session_state["interview_score"] = result.get("overall_score", 0) if isinstance(result, dict) else 0
        st.session_state["wz_ri_closing_reached"] = False
        st.rerun()


try:
    _wz160_previous_render_final_score = _wz_ri_render_final_score
except Exception:
    _wz160_previous_render_final_score = None


def _wz_ri_render_final_score(result: dict, company: str, role: str, website: str, language: str):
    """Render original final score plus persistent weak-area loop."""
    try:
        _wz160_store_interview_result(result, company, role, language)
    except Exception:
        pass

    if callable(_wz160_previous_render_final_score):
        _wz160_previous_render_final_score(result, company, role, website, language)
    else:
        st.markdown("## Interview Result")
        st.metric("Interview Readiness Score", f"{_wz160_safe_int(result.get('overall_score'), 0)}/100")

    _wz160_render_history_panel()


try:
    _wz160_previous_render_real_interview_simulation = render_real_interview_simulation
except Exception:
    _wz160_previous_render_real_interview_simulation = None


def render_real_interview_simulation():
    """Show memory before the original interview UI, then run the full existing interview experience."""
    try:
        if not bool(st.session_state.get("wz_ri_started")) and not bool(st.session_state.get("wz_ri_final_score")):
            _wz160_render_history_preview()
    except Exception:
        pass

    if callable(_wz160_previous_render_real_interview_simulation):
        return _wz160_previous_render_real_interview_simulation()
    st.error("Interview module could not load the previous interview renderer.")


def show_workobot():
    render_real_interview_simulation()

# =========================================================
# End WorkZo v160 patch
# =========================================================

# =========================================================
# WorkZo v170 - Real Hiring Decision Feedback Layer
# Adds: HR screen pass/fail, hiring manager pass/fail,
# trust-damaging answer, strongest answer, rejection risk,
# next practice target, and stronger decision-style final feedback.
# Additive patch: keeps all previous WorkZo interview features intact.
# =========================================================

try:
    _wz170_json = json
except Exception:
    import json as _wz170_json

try:
    _wz170_html = html
except Exception:
    import html as _wz170_html


def _wz170_safe_text(value, default=""):
    try:
        text = str(value if value is not None else default)
        return text.strip() if text.strip() else default
    except Exception:
        return default


def _wz170_safe_list(value):
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _wz170_safe_score(value, default=0):
    try:
        return max(0, min(100, int(float(value))))
    except Exception:
        return default


def _wz170_answer_words(answer):
    try:
        return len(str(answer or "").split())
    except Exception:
        return 0


def _wz170_extract_answer_signal(qa_pairs):
    """Deterministic fallback signal if AI does not return full hiring details."""
    qa_pairs = qa_pairs if isinstance(qa_pairs, list) else []
    if not qa_pairs:
        return {
            "strongest_answer_number": 1,
            "weakest_answer_number": 1,
            "answer_that_helped": "No strong answer was captured yet.",
            "answer_that_damaged_trust": "No answer was captured yet.",
        }

    scored = []
    for idx, item in enumerate(qa_pairs, start=1):
        answer = str((item or {}).get("answer", "") or "")
        lower = answer.lower()
        score = 0
        words = _wz170_answer_words(answer)
        if 45 <= words <= 120:
            score += 2
        if any(x in lower for x in ["result", "impact", "improved", "reduced", "increased", "%", "measured", "outcome"]):
            score += 3
        if any(x in lower for x in ["example", "project", "customer", "client", "dashboard", "analysis", "support", "stakeholder"]):
            score += 2
        if words < 25:
            score -= 2
        if words > 150:
            score -= 1
        scored.append((score, idx, answer))

    strongest = max(scored, key=lambda x: x[0])
    weakest = min(scored, key=lambda x: x[0])
    return {
        "strongest_answer_number": strongest[1],
        "weakest_answer_number": weakest[1],
        "answer_that_helped": strongest[2][:260] or "The strongest answer had the clearest proof.",
        "answer_that_damaged_trust": weakest[2][:260] or "The weakest answer lacked proof or clarity.",
    }


def _wz170_normalize_hiring_decision(result, qa_pairs=None, reactions=None):
    """Ensure the final result always contains realistic hiring-decision fields."""
    if not isinstance(result, dict):
        result = {}
    qa_pairs = qa_pairs if isinstance(qa_pairs, list) else st.session_state.get("wz_ri_answers", [])
    reactions = reactions if isinstance(reactions, list) else st.session_state.get("wz_ri_live_reactions", [])
    score = _wz170_safe_score(result.get("overall_score"), 0)
    signals = _wz170_extract_answer_signal(qa_pairs)

    repeated_reasons = []
    for r in reactions or []:
        if isinstance(r, dict):
            reason = str(r.get("interruption_reason") or "").strip()
            if reason and reason != "none":
                repeated_reasons.append(reason)

    if score >= 80:
        hr_decision = "Likely pass HR screen"
        hm_decision = "Possible pass to hiring manager / next round"
        final_decision = "Pass to next round"
        rejection_risk = "Low to medium"
    elif score >= 65:
        hr_decision = "Could pass HR screen, but not strongly"
        hm_decision = "Borderline for hiring manager round"
        final_decision = "Borderline"
        rejection_risk = "Medium"
    else:
        hr_decision = "May fail HR screen"
        hm_decision = "Unlikely to pass hiring manager round yet"
        final_decision = "Not ready"
        rejection_risk = "High"

    weakest_number = result.get("weakest_answer_question_number") or signals.get("weakest_answer_number", 1)
    strongest_number = result.get("strongest_answer_question_number") or signals.get("strongest_answer_number", 1)

    main_reject_reason = _wz170_safe_text(
        result.get("biggest_reason_for_rejection")
        or result.get("hiring_reason")
        or ("Answers were not specific enough and did not prove measurable impact." if score < 80 else "No major rejection reason, but answers can still be sharper."),
        "Answers need stronger proof and clearer business impact."
    )

    damaged = _wz170_safe_text(
        result.get("answer_that_damaged_trust")
        or signals.get("answer_that_damaged_trust")
        or "The weakest answer felt too generic or lacked measurable proof.",
        "The weakest answer felt too generic or lacked measurable proof."
    )

    helped = _wz170_safe_text(
        result.get("answer_that_helped")
        or signals.get("answer_that_helped")
        or "The strongest answer gave the clearest evidence of role fit.",
        "The strongest answer gave the clearest evidence of role fit."
    )

    next_target = _wz170_safe_text(
        result.get("next_practice_target")
        or result.get("next_action")
        or result.get("retry_instruction")
        or "Practice one answer with: result first, one example, measurable impact, and job relevance.",
        "Practice one answer with: result first, one example, measurable impact, and job relevance."
    )

    result["hiring_decision"] = _wz170_safe_text(result.get("hiring_decision"), final_decision)
    result["hr_screen_decision"] = _wz170_safe_text(result.get("hr_screen_decision"), hr_decision)
    result["hiring_manager_decision"] = _wz170_safe_text(result.get("hiring_manager_decision"), hm_decision)
    result["biggest_reason_for_rejection"] = main_reject_reason
    result["rejection_risk"] = _wz170_safe_text(result.get("rejection_risk"), rejection_risk)
    result["answer_that_damaged_trust"] = damaged
    result["answer_that_helped"] = helped
    result["strongest_answer_question_number"] = _wz170_safe_score(strongest_number, 1)
    result["weakest_answer_question_number"] = _wz170_safe_score(weakest_number, 1)
    result["next_practice_target"] = next_target
    result["recruiter_decision_summary"] = _wz170_safe_text(
        result.get("recruiter_decision_summary"),
        f"{result['hr_screen_decision']}. {result['hiring_manager_decision']}. Main risk: {result['biggest_reason_for_rejection']}"
    )
    result["trust_risk_flags"] = _wz170_safe_list(result.get("trust_risk_flags")) or sorted(set(repeated_reasons))[:5]
    result["what_to_fix_before_real_interview"] = _wz170_safe_list(result.get("what_to_fix_before_real_interview")) or [
        "Lead with the result instead of long background.",
        "Give one specific example for every claim.",
        "Add truthful numbers, volume, speed, quality, customer outcome, or business impact.",
        "Connect each answer to the job description.",
    ]
    result["would_pass_summary"] = {
        "hr_screen": result["hr_screen_decision"],
        "hiring_manager": result["hiring_manager_decision"],
        "final_decision": result["hiring_decision"],
        "risk": result["rejection_risk"],
    }
    return result


try:
    _wz170_previous_score_full_interview = _wz_ri_score_full_interview
except Exception:
    _wz170_previous_score_full_interview = None


def _wz_ri_score_full_interview(cv_text: str, jd: str, company: str, role: str, qa_pairs: list, reactions: list, language: str) -> dict:
    """Final scoring with recruiter-style pass/fail decision fields."""
    base_result = {}
    if callable(_wz170_previous_score_full_interview):
        try:
            base_result = _wz170_previous_score_full_interview(cv_text, jd, company, role, qa_pairs, reactions, language)
        except Exception:
            base_result = {}

    prompt = f"""
You are not a friendly coach. You are a realistic recruiter and hiring manager making a hiring decision.

Candidate CV:
{str(cv_text or '')[:7000]}

Job Description:
{str(jd or '')[:7000]}

Company: {company or 'Not specified'}
Role: {role or 'Not specified'}

Interview answers:
{_wz170_json.dumps(qa_pairs or [], ensure_ascii=False)}

Live interviewer reactions:
{_wz170_json.dumps(reactions or [], ensure_ascii=False)}

Existing score object from WorkZo:
{_wz170_json.dumps(base_result if isinstance(base_result, dict) else {}, ensure_ascii=False)}

Return ONLY valid JSON with this exact structure:
{{
  "overall_score": 0,
  "target_score": 80,
  "hiring_decision": "Pass to next round|Borderline|Not ready",
  "hr_screen_decision": "Likely pass HR screen|Could pass HR screen, but not strongly|May fail HR screen",
  "hiring_manager_decision": "Possible pass to hiring manager / next round|Borderline for hiring manager round|Unlikely to pass hiring manager round yet",
  "rejection_risk": "Low|Low to medium|Medium|High",
  "biggest_reason_for_rejection": "specific reason",
  "answer_that_damaged_trust": "which answer damaged trust and why",
  "answer_that_helped": "which answer helped and why",
  "strongest_answer_question_number": 1,
  "weakest_answer_question_number": 1,
  "trust_risk_flags": ["generic claim", "missing metric"],
  "what_to_fix_before_real_interview": ["fix 1", "fix 2", "fix 3"],
  "next_practice_target": "one focused practice target for the next session",
  "recruiter_decision_summary": "short realistic recruiter summary",
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
  "improved_version_of_weakest_answer": "",
  "better_answer_formula": "Situation → Task → Action → Result → Why it matters for this job",
  "final_readiness_message": ""
}}

Rules:
- Be strict, realistic, and recruiter-like.
- Say whether the candidate would likely pass HR screen and hiring manager round.
- Identify the single biggest reason they might be rejected.
- Identify one answer that damaged trust and one answer that helped.
- Penalize vague claims, missing metrics, weak STAR, and low job relevance.
- Do not invent achievements.
- Keep feedback in {language}.
"""
    try:
        raw = _wz_ri_ai(prompt, json_mode=True, language=language)
        ai_result = _wz_ri_json(raw, {})
        if isinstance(ai_result, dict) and ai_result:
            merged = dict(base_result if isinstance(base_result, dict) else {})
            merged.update(ai_result)
            return _wz170_normalize_hiring_decision(merged, qa_pairs, reactions)
    except Exception:
        pass

    return _wz170_normalize_hiring_decision(base_result if isinstance(base_result, dict) else {}, qa_pairs, reactions)


def _wz170_render_hiring_decision_panel(result: dict):
    result = _wz170_normalize_hiring_decision(result)
    score = _wz170_safe_score(result.get("overall_score"), 0)
    decision = _wz170_safe_text(result.get("hiring_decision"), "Borderline")
    risk = _wz170_safe_text(result.get("rejection_risk"), "Medium")

    st.markdown("### 🧑‍💼 Recruiter hiring decision")
    d1, d2, d3 = st.columns(3)
    with d1:
        if score >= 80:
            st.success(decision)
        elif score >= 60:
            st.warning(decision)
        else:
            st.error(decision)
    with d2:
        st.metric("Rejection risk", risk)
    with d3:
        st.metric("Target readiness", f"{score}/100")

    st.markdown(
        f"""
        <div class="wz-interview-card">
            <div class="wz-interview-label">WOULD YOU PASS?</div>
            <div class="wz-interview-title">{_wz170_html.escape(_wz170_safe_text(result.get('recruiter_decision_summary'), 'Decision summary unavailable.'))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### HR screen")
        st.info(_wz170_safe_text(result.get("hr_screen_decision"), "Could pass HR screen, but not strongly"))
    with c2:
        st.markdown("#### Hiring manager round")
        st.info(_wz170_safe_text(result.get("hiring_manager_decision"), "Borderline for hiring manager round"))

    st.markdown("#### Biggest reason you may be rejected")
    st.error(_wz170_safe_text(result.get("biggest_reason_for_rejection"), "Answers need stronger proof and clearer business impact."))

    c3, c4 = st.columns(2)
    with c3:
        st.markdown("#### Answer that damaged trust")
        st.warning(_wz170_safe_text(result.get("answer_that_damaged_trust"), "The weakest answer felt too generic or lacked proof."))
    with c4:
        st.markdown("#### Answer that helped you")
        st.success(_wz170_safe_text(result.get("answer_that_helped"), "The strongest answer gave the clearest evidence of fit."))

    flags = _wz170_safe_list(result.get("trust_risk_flags"))
    if flags:
        st.markdown("#### Trust risk flags")
        st.caption("These are the parts that may make a recruiter doubt the answer.")
        for item in flags[:6]:
            st.markdown(f"- {item}")

    fixes = _wz170_safe_list(result.get("what_to_fix_before_real_interview"))
    if fixes:
        st.markdown("#### Fix before the real interview")
        for item in fixes[:6]:
            st.markdown(f"- {item}")

    st.markdown("#### Next practice target")
    st.info(_wz170_safe_text(result.get("next_practice_target"), "Practice one answer with result first, one example, measurable impact, and job relevance."))


try:
    _wz170_previous_render_final_score = _wz_ri_render_final_score
except Exception:
    _wz170_previous_render_final_score = None


def _wz_ri_render_final_score(result: dict, company: str, role: str, website: str, language: str):
    """Render hiring decision first, then preserve the existing full feedback/history UI."""
    result = _wz170_normalize_hiring_decision(result)
    try:
        st.session_state["wz_ri_final_score"] = result
    except Exception:
        pass

    _wz170_render_hiring_decision_panel(result)

    if callable(_wz170_previous_render_final_score):
        try:
            st.markdown("---")
            _wz170_previous_render_final_score(result, company, role, website, language)
            return
        except Exception:
            pass

    st.markdown("---")
    st.markdown("## Full Interview Feedback")
    st.metric("Interview Readiness Score", f"{_wz170_safe_score(result.get('overall_score'), 0)}/100")


# =========================================================
# End WorkZo v170 patch
# =========================================================



# =========================================================
# WorkZo v186 - Recruiter psychology output loop
# Adds patterns across sessions, retry weakest answer loop, emotional timeline,
# compact AI-native cards, and recruiter confidence framing.
# =========================================================
import html as _wz186_html
import re as _wz186_re


def _wz186_list(value):
    try:
        if isinstance(value, list):
            return [str(x).strip() for x in value if str(x).strip()]
        if isinstance(value, str) and value.strip():
            return [x.strip() for x in _wz186_re.split(r"[\n;•]+", value) if x.strip()]
    except Exception:
        pass
    return []


def _wz186_txt(value, fallback=""):
    try:
        text = str(value or "").strip()
        return text if text else fallback
    except Exception:
        return fallback


def _wz186_int(value, default=0):
    try:
        return int(float(value))
    except Exception:
        return default


def _wz186_short_answer(answer, limit=520):
    text = _wz186_txt(answer)
    if len(text) > limit:
        return text[:limit].rsplit(" ", 1)[0] + "…"
    return text


def _wz186_build_patterns(history, result):
    result = result if isinstance(result, dict) else {}
    patterns = []
    all_weak = []
    try:
        for entry in history[-5:]:
            all_weak.extend(_wz186_list(entry.get('weak_areas')))
    except Exception:
        pass
    all_weak.extend(_wz186_list(result.get('trust_risk_flags')))
    all_weak.extend(_wz186_list(result.get('what_hurt_you_most')))
    text = ' '.join(all_weak).lower()
    if any(x in text for x in ['metric', 'measurable', 'impact', 'quantifiable', 'result']):
        patterns.append('Consistently needs stronger measurable outcomes.')
    if any(x in text for x in ['vague', 'generic', 'specific', 'clarity']):
        patterns.append('Answers become too broad when follow-ups get specific.')
    if any(x in text for x in ['too long', 'rambling', 'background']):
        patterns.append('Tends to give background before the result.')
    if any(x in text for x in ['ownership', 'team-based', 'what specifically did you']):
        patterns.append('Needs clearer individual ownership.')
    if any(x in text for x in ['job description', 'jd', 'relevance']):
        patterns.append('Should connect answers more directly to the job description.')
    if not patterns:
        patterns = [
            'Strong communication baseline; improve proof with numbers.',
            'Interview confidence improves when answers use STAR structure.',
            'Next session should focus on concise, result-first examples.',
        ]
    return patterns[:5]


def _wz186_reaction_timeline(result):
    score = _wz186_int((result or {}).get('overall_score'), 0)
    flags = ' '.join(_wz186_list((result or {}).get('trust_risk_flags'))).lower()
    timeline = ['🙂 Interested']
    if score < 80:
        timeline.append('😐 Neutral after broad answer')
    if any(x in flags for x in ['metric', 'impact', 'vague', 'generic', 'too long']):
        timeline.append('⚠️ Doubt increased')
    if score < 65:
        timeline.append('🔴 Confidence dropped')
    else:
        timeline.append('🟢 Recoverable with one stronger STAR example')
    timeline.append('🎯 Next: retry weakest answer')
    return timeline[:5]


def _wz186_compact_cards(title, items, icon='⚠️'):
    items = _wz186_list(items)[:6]
    if not items:
        return
    st.markdown(f'#### {title}')
    cols = st.columns(min(3, max(1, len(items))))
    for i, item in enumerate(items):
        with cols[i % len(cols)]:
            st.markdown(
                f"""
                <div style='border:1px solid rgba(148,163,184,.20);background:rgba(15,23,42,.52);border-radius:16px;padding:14px 15px;margin:5px 0 10px 0;min-height:72px;'>
                    <div style='font-size:1.05rem;margin-bottom:6px;'>{icon}</div>
                    <div style='color:#f8fafc;font-weight:850;line-height:1.35;'>{_wz186_html.escape(str(item))}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _wz186_render_patterns_panel(result):
    try:
        history = _wz160_load_history() if callable(globals().get('_wz160_load_history')) else []
    except Exception:
        history = []
    patterns = _wz186_build_patterns(history, result)
    st.markdown('### 🧠 Patterns across sessions')
    st.caption('WorkZo tracks recurring recruiter signals so each practice round becomes smarter.')
    cols = st.columns(min(3, len(patterns)))
    for i, pattern in enumerate(patterns):
        with cols[i % len(cols)]:
            st.markdown(
                f"""
                <div style='border:1px solid rgba(56,189,248,.22);background:linear-gradient(135deg,rgba(14,165,233,.10),rgba(15,23,42,.58));border-radius:18px;padding:16px;min-height:96px;margin-bottom:12px;'>
                    <div style='color:#67e8f9;font-weight:900;font-size:.75rem;letter-spacing:.10em;text-transform:uppercase;margin-bottom:8px;'>Recurring pattern</div>
                    <div style='color:#f8fafc;font-weight:850;line-height:1.4;'>{_wz186_html.escape(pattern)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _wz186_render_retry_weakest(result):
    result = result if isinstance(result, dict) else {}
    weak_answer = _wz186_txt(result.get('answer_that_damaged_trust'))
    improved = _wz186_txt(result.get('improved_version_of_weakest_answer'))
    st.markdown('### 🎤 Retry weakest answer immediately')
    st.caption('Learning loop: retry the answer that damaged recruiter trust, then compare old vs improved.')
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('#### Old answer / trust damage')
        st.warning(_wz186_short_answer(weak_answer or 'Your weakest answer lacked specific proof, ownership, or measurable impact.'))
    with c2:
        st.markdown('#### Better direction')
        st.success(_wz186_short_answer(improved or 'Answer with result first, one concrete example, your exact action, and one truthful metric or business outcome.'))
    if st.button('🎤 Retry this answer now', key='wz186_retry_weakest_answer_now', use_container_width=True):
        try:
            st.session_state['wz_ri_retry_mode'] = True
            st.session_state['wz_ri_retry_prompt'] = weak_answer or 'Retry the weakest answer with measurable impact and clearer ownership.'
            st.session_state['wz_ri_live_reaction_override'] = 'Retry mode: compare old vs new answer.'
            st.session_state['page'] = 'real_interview'
            st.session_state['nav_page'] = 'real_interview'
            st.session_state['_wz_force_page'] = 'real_interview'
            st.rerun()
        except Exception:
            pass


def _wz186_render_confidence_and_timeline(result):
    result = result if isinstance(result, dict) else {}
    score = _wz186_int(result.get('overall_score'), 0)
    confidence = max(35, min(94, score + 6))
    risk = _wz186_txt(result.get('rejection_risk'), 'Medium')
    st.markdown('### 📈 Recruiter confidence timeline')
    c1, c2, c3 = st.columns(3)
    c1.metric('Recruiter confidence', f'{confidence}%')
    c2.metric('Rejection risk', risk)
    c3.metric('Trust recovery target', f'{min(95, confidence + 15)}%')
    timeline = _wz186_reaction_timeline(result)
    st.markdown(
        "<div style='display:flex;gap:10px;flex-wrap:wrap;margin:8px 0 18px 0;'>" +
        ''.join([f"<div style='border:1px solid rgba(148,163,184,.22);background:rgba(15,23,42,.54);border-radius:999px;padding:10px 13px;color:#e5e7eb;font-weight:850;'>{_wz186_html.escape(x)}</div>" for x in timeline]) +
        "</div>",
        unsafe_allow_html=True,
    )


def _wz186_render_referral_decision(result):
    result = result if isinstance(result, dict) else {}
    score = _wz186_int(result.get('overall_score'), 0)
    if score >= 82:
        verdict = 'YES — likely referral to hiring manager'
        detail = 'The recruiter has enough evidence to justify moving you forward.'
        kind = 'success'
    elif score >= 65:
        verdict = 'MAYBE — one stronger practice round needed'
        detail = 'You show role fit, but recruiter confidence drops where impact or metrics are unclear.'
        kind = 'warning'
    else:
        verdict = 'NO — not ready to refer yet'
        detail = 'The recruiter would need clearer proof, stronger structure, and more job-specific examples.'
        kind = 'error'
    st.markdown('### 🤝 Would this recruiter refer you internally?')
    getattr(st, kind)(f'{verdict}\n\n{detail}')


try:
    _wz186_previous_render_final_score = _wz_ri_render_final_score
except Exception:
    _wz186_previous_render_final_score = None


def _wz_ri_render_final_score(result: dict, company: str, role: str, website: str, language: str):
    """Final recruiter-psychology result page: memory, retry loop, confidence timeline, compact cards."""
    try:
        if callable(globals().get('_wz170_normalize_hiring_decision')):
            result = _wz170_normalize_hiring_decision(result)
    except Exception:
        result = result if isinstance(result, dict) else {}

    try:
        st.session_state['wz_ri_final_score'] = result
    except Exception:
        pass

    score = _wz186_int(result.get('overall_score'), 0)
    target = _wz186_int(result.get('target_score'), 80)
    decision = _wz186_txt(result.get('hiring_decision'), 'Borderline — needs one more practice round')
    next_target = _wz186_txt(result.get('next_practice_target'), 'Practice one answer with result first, one example, measurable impact, and job relevance.')

    st.markdown('## 🧑‍💼 Recruiter psychology report')
    st.caption('WorkZo shows where recruiter confidence increased, dropped, and what to retry next.')
    a, b, c = st.columns(3)
    a.metric('Readiness score', f'{score}/100')
    b.metric('Target', f'{target}+')
    c.metric('Next focus', next_target[:32] + ('…' if len(next_target) > 32 else ''))

    if score >= target:
        st.success(decision)
    elif score >= 60:
        st.warning(decision)
    else:
        st.error(decision)

    summary = _wz186_txt(result.get('recruiter_decision_summary'), _wz186_txt(result.get('biggest_reason_for_rejection'), 'Recruiter confidence depends on clearer measurable proof.'))
    st.markdown(
        f"""
        <div style='border:1px solid rgba(56,189,248,.20);background:rgba(15,23,42,.48);border-radius:18px;padding:18px;margin:14px 0;'>
            <div style='color:#93c5fd;font-weight:900;font-size:.78rem;text-transform:uppercase;letter-spacing:.10em;margin-bottom:8px;'>Would you pass?</div>
            <div style='color:#f8fafc;font-size:1.05rem;font-weight:850;line-height:1.5;'>{_wz186_html.escape(summary)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _wz186_render_confidence_and_timeline(result)
    _wz186_render_referral_decision(result)
    _wz186_render_patterns_panel(result)

    c1, c2 = st.columns(2)
    with c1:
        _wz186_compact_cards('⚠️ Trust risk flags', result.get('trust_risk_flags'), '⚠️')
    with c2:
        _wz186_compact_cards('✅ Fix before the real interview', result.get('what_to_fix_before_real_interview'), '✅')

    _wz186_render_retry_weakest(result)

    strengths = _wz186_list(result.get('strengths')) or ['Relevant experience', 'Communication potential', 'Role motivation']
    mistakes = _wz186_list(result.get('top_3_mistakes')) or _wz186_list(result.get('what_hurt_you_most'))
    c3, c4 = st.columns(2)
    with c3:
        _wz186_compact_cards('What helped recruiter trust', strengths, '🟢')
    with c4:
        _wz186_compact_cards('What to fix next', mistakes, '🔴')

    st.markdown('### 🎯 Next practice target')
    st.info(next_target)

    try:
        if callable(globals().get('_wz160_store_interview_result')):
            _wz160_store_interview_result(result, company, role, language)
    except Exception:
        pass

    # Preserve the old full result only behind an expander to avoid document-like overload.
    if callable(_wz186_previous_render_final_score):
        with st.expander('View detailed legacy feedback', expanded=False):
            try:
                _wz186_previous_render_final_score(result, company, role, website, language)
            except Exception:
                st.caption('Detailed feedback unavailable for this session.')

# ================================================================
# WorkZo v188 — Adaptive AI Recruiter Simulation Engine
# Adds: follow-up chaining, candidate memory, recruiter personalities,
# dynamic pressure state, role/country behaviour layers, structured scoring,
# and pre-interview intelligence hooks without changing the main UI flow.
# ================================================================

try:
    _wz188_previous_build_questions = _wz_ri_build_questions
except Exception:
    _wz188_previous_build_questions = None
try:
    _wz188_previous_react_to_answer = _wz_ri_react_to_answer
except Exception:
    _wz188_previous_react_to_answer = None
try:
    _wz188_previous_score_full_interview = _wz_ri_score_full_interview
except Exception:
    _wz188_previous_score_full_interview = None

import re as _wz188_re
import time as _wz188_time

_WZ188_RECRUITER_PROFILES = {
    "Sarah": {
        "label": "👩 Sarah — Friendly HR",
        "tone": "supportive, warm, communication-focused",
        "push_style": "gentle but persistent",
        "focus": ["communication", "motivation", "teamwork", "role fit"],
        "weak_followup": "Good start. Can you walk me through one specific example with a clear result?",
        "metric_followup": "That sounds useful. How did you measure the improvement?",
        "ramble_interrupt": "Let me pause you gently — what was the main result?",
    },
    "Daniel": {
        "label": "👨 Daniel — Technical Hiring Manager",
        "tone": "analytical, direct, technical, detail-oriented",
        "push_style": "evidence-first and process-heavy",
        "focus": ["technical depth", "tools", "process", "validation", "metrics"],
        "weak_followup": "What exactly did you do technically? Walk me through the process.",
        "metric_followup": "What metric changed, and how did you validate it?",
        "ramble_interrupt": "I need the technical point, not the background. What was your method?",
    },
    "Priya": {
        "label": "👩 Priya — Fast-paced Startup Recruiter",
        "tone": "fast, impact-focused, skeptical of rambling",
        "push_style": "quick interruptions and business-impact pressure",
        "focus": ["ownership", "speed", "impact", "ambiguity", "execution"],
        "weak_followup": "Too broad. What changed for the business? Give me the impact quickly.",
        "metric_followup": "How much faster, cheaper, or better did this make the process?",
        "ramble_interrupt": "I’m going to interrupt — summarize the result in one sentence.",
    },
    "Markus": {
        "label": "👨 Markus — German Corporate Interviewer",
        "tone": "structured, formal, precise, process-oriented",
        "push_style": "calm precision and step-by-step validation",
        "focus": ["structure", "precision", "process", "realistic claims", "responsibility"],
        "weak_followup": "Please structure the answer more clearly: situation, your responsibility, action, result.",
        "metric_followup": "What evidence supports that result? Please be precise.",
        "ramble_interrupt": "Let us make this more structured. What was your exact responsibility?",
    },
}

_WZ188_ROLE_LAYERS = {
    "data": {
        "probe": ["SQL depth", "dashboarding", "business impact", "data quality", "stakeholder communication"],
        "question": "You mentioned analysis/reporting. What data did you use, what logic did you apply, and what decision changed because of it?",
    },
    "analyst": {
        "probe": ["SQL depth", "dashboarding", "business impact", "data quality", "stakeholder communication"],
        "question": "You mentioned analysis/reporting. What data did you use, what logic did you apply, and what decision changed because of it?",
    },
    "support": {
        "probe": ["customer handling", "escalations", "ticket ownership", "resolution impact", "communication"],
        "question": "Tell me about a difficult support case. What did you own, how did you resolve it, and what improved for the customer?",
    },
    "customer success": {
        "probe": ["retention", "difficult clients", "expectation management", "escalation", "business relationship"],
        "question": "Tell me about a customer situation where expectations were difficult. How did you manage it and what was the outcome?",
    },
    "product": {
        "probe": ["user problem", "prioritization", "stakeholders", "trade-offs", "measurable outcome"],
        "question": "Describe a product decision you influenced. What trade-off did you make and how did you measure success?",
    },
    "engineer": {
        "probe": ["technical depth", "systems thinking", "debugging", "ownership", "trade-offs"],
        "question": "Describe a technical problem you solved. What was your approach, what trade-off did you make, and what changed after it shipped?",
    },
}

_WZ188_COUNTRY_LAYERS = {
    "germany": {
        "expectation": "structured, precise, process-oriented, realistic claims",
        "coach": "Structure the answer step-by-step and avoid exaggerated claims.",
    },
    "usa": {
        "expectation": "achievement-focused, confident, metric-heavy, fast communication",
        "coach": "Make the achievement more outcome-driven and quantify impact.",
    },
    "uk": {
        "expectation": "balanced confidence, teamwork, professional clarity",
        "coach": "Keep confidence balanced and show collaboration plus ownership.",
    },
    "india": {
        "expectation": "skills proof, ATS-fit keywords, clear project ownership, communication clarity",
        "coach": "Show concrete projects, tools, and your exact contribution.",
    },
}


def _wz188_text(value, default=""):
    try:
        return str(value or default).strip()
    except Exception:
        return default


def _wz188_words(text):
    return _wz188_re.findall(r"[a-zA-Z][a-zA-Z0-9+.#-]{2,}", _wz188_text(text).lower())


def _wz188_has_metric(text):
    t = _wz188_text(text).lower()
    return bool(_wz188_re.search(r"\b\d+[\d,.]*\s*(%|percent|users?|customers?|tickets?|cases?|minutes?|hours?|days?|weeks?|months?|years?|€|\$|k|m|x|times|seconds?|reports?|dashboards?)?\b", t))


def _wz188_has_result_language(text):
    t = _wz188_text(text).lower()
    return any(x in t for x in ["improved", "reduced", "increased", "saved", "delivered", "resolved", "automated", "built", "created", "impact", "result", "outcome", "faster", "better", "efficiency", "customer", "business"])


def _wz188_has_ownership(text):
    t = _wz188_text(text).lower()
    return any(x in t for x in ["i ", "i'm", "i’ve", "i have", "my role", "i worked", "i built", "i created", "i handled", "i analyzed", "i improved", "i led"])


def _wz188_profile_from_personality(personality):
    p = _wz188_text(personality).lower()
    for key, data in _WZ188_RECRUITER_PROFILES.items():
        if key.lower() in p or key.lower() in _wz188_text(data.get("label")).lower():
            return key, data
    if "technical" in p or "manager" in p:
        return "Daniel", _WZ188_RECRUITER_PROFILES["Daniel"]
    if "startup" in p or "fast" in p or "priya" in p:
        return "Priya", _WZ188_RECRUITER_PROFILES["Priya"]
    if "german" in p or "corporate" in p or "markus" in p:
        return "Markus", _WZ188_RECRUITER_PROFILES["Markus"]
    return "Sarah", _WZ188_RECRUITER_PROFILES["Sarah"]


def _wz188_role_layer(role, jd=""):
    combined = f"{role} {jd}".lower()
    for key, layer in _WZ188_ROLE_LAYERS.items():
        if key in combined:
            return key, layer
    return "general", {"probe": ["ownership", "measurable impact", "communication", "role fit"], "question": "Give me one specific example that proves you can do this role. What changed because of your work?"}


def _wz188_country_layer(country_or_jd=""):
    text = _wz188_text(country_or_jd).lower()
    for key, layer in _WZ188_COUNTRY_LAYERS.items():
        if key in text:
            return key, layer
    return "global", {"expectation": "clear, specific, measurable, role-relevant answers", "coach": "Be specific, truthful, concise, and connect your answer to the job."}


def _wz188_default_memory():
    return {
        "strong_points": [],
        "weak_points": [],
        "mentioned_metrics": [],
        "mentioned_claims": [],
        "contradictions": [],
        "areas_to_probe": [],
        "communication_style": "unknown",
        "confidence_level": 70,
        "pressure_level": 30,
        "answer_count": 0,
        "last_followup_chain": [],
    }


def _wz188_get_memory():
    try:
        mem = st.session_state.get("wz_recruiter_memory")
        if not isinstance(mem, dict):
            mem = _wz188_default_memory()
            st.session_state["wz_recruiter_memory"] = mem
        for k, v in _wz188_default_memory().items():
            mem.setdefault(k, v)
        return mem
    except Exception:
        return _wz188_default_memory()


def _wz188_add_unique(items, value, limit=8):
    if not isinstance(items, list):
        items = []
    value = _wz188_text(value)
    if value and value not in items:
        items.append(value)
    return items[-limit:]


def _wz188_detect_contradiction(answer, memory):
    t = _wz188_text(answer).lower()
    claims = memory.get("mentioned_claims", []) if isinstance(memory, dict) else []
    contradiction = ""
    if any("independent" in c or "ownership" in c for c in claims) and any(x in t for x in ["manager guided", "my manager", "team did", "we all", "not sure"]):
        contradiction = "Earlier you signaled independent ownership, but now the answer sounds heavily team/manager-led."
    if any("sql" in c for c in claims) and any(x in t for x in ["i don't know sql", "not much sql", "basic sql only"]):
        contradiction = "Earlier SQL appeared important, but this answer reduces confidence in SQL depth."
    return contradiction


def _wz188_update_memory(question, answer, jd, role, reaction_type=""):
    mem = _wz188_get_memory()
    ans = _wz188_text(answer)
    low = ans.lower()
    words = len(ans.split())
    mem["answer_count"] = int(mem.get("answer_count", 0) or 0) + 1

    has_metric = _wz188_has_metric(ans)
    has_result = _wz188_has_result_language(ans)
    has_ownership = _wz188_has_ownership(ans)

    if has_metric:
        found = _wz188_re.findall(r"\b\d+[\d,.]*\s*(?:%|percent|users?|customers?|tickets?|cases?|minutes?|hours?|days?|weeks?|months?|years?|€|\$|k|m|x|times|seconds?|reports?|dashboards?)?\b", ans, flags=_wz188_re.I)
        for metric in found[:3]:
            mem["mentioned_metrics"] = _wz188_add_unique(mem.get("mentioned_metrics", []), metric)
        mem["strong_points"] = _wz188_add_unique(mem.get("strong_points", []), "uses measurable evidence")
    else:
        mem["weak_points"] = _wz188_add_unique(mem.get("weak_points", []), "missing measurable impact")
        mem["areas_to_probe"] = _wz188_add_unique(mem.get("areas_to_probe", []), "quantified outcome")

    if has_result:
        mem["strong_points"] = _wz188_add_unique(mem.get("strong_points", []), "result-oriented answer")
    else:
        mem["weak_points"] = _wz188_add_unique(mem.get("weak_points", []), "unclear business outcome")

    if has_ownership:
        mem["strong_points"] = _wz188_add_unique(mem.get("strong_points", []), "clear personal ownership")
        mem["mentioned_claims"] = _wz188_add_unique(mem.get("mentioned_claims", []), "ownership")
    else:
        mem["weak_points"] = _wz188_add_unique(mem.get("weak_points", []), "weak individual ownership")
        mem["areas_to_probe"] = _wz188_add_unique(mem.get("areas_to_probe", []), "exact personal contribution")

    if words > 145:
        mem["weak_points"] = _wz188_add_unique(mem.get("weak_points", []), "rambling / too long")
        mem["communication_style"] = "detailed but too long"
    elif words < 25:
        mem["weak_points"] = _wz188_add_unique(mem.get("weak_points", []), "too short / not enough evidence")
        mem["communication_style"] = "too brief"
    else:
        mem["communication_style"] = "clear enough, needs sharper proof" if mem.get("weak_points") else "clear and specific"

    role_key, role_layer = _wz188_role_layer(role, jd)
    for probe in role_layer.get("probe", [])[:3]:
        if probe.lower() not in low:
            mem["areas_to_probe"] = _wz188_add_unique(mem.get("areas_to_probe", []), probe)

    contradiction = _wz188_detect_contradiction(ans, mem)
    if contradiction:
        mem["contradictions"] = _wz188_add_unique(mem.get("contradictions", []), contradiction)
        mem["areas_to_probe"] = _wz188_add_unique(mem.get("areas_to_probe", []), "clarify contradiction")

    pressure = int(mem.get("pressure_level", 30) or 30)
    confidence = int(mem.get("confidence_level", 70) or 70)
    if has_metric and has_result and has_ownership and words <= 130:
        pressure = max(10, pressure - 8)
        confidence = min(95, confidence + 7)
    else:
        pressure = min(95, pressure + 8)
        confidence = max(20, confidence - 6)
    if reaction_type in ["avoidance", "contradiction", "rambling"]:
        pressure = min(95, pressure + 10)
        confidence = max(15, confidence - 8)

    mem["pressure_level"] = pressure
    mem["confidence_level"] = confidence
    try:
        st.session_state["wz_recruiter_memory"] = mem
        st.session_state["wz_recruiter_confidence"] = confidence
        st.session_state["wz_recruiter_pressure"] = pressure
    except Exception:
        pass
    return mem


def _wz188_answer_scores(answer, question=""):
    ans = _wz188_text(answer)
    words = len(ans.split())
    has_metric = _wz188_has_metric(ans)
    has_result = _wz188_has_result_language(ans)
    has_ownership = _wz188_has_ownership(ans)
    specificity = 80 if has_metric else 55
    impact = 82 if has_result and has_metric else (65 if has_result else 45)
    ownership = 78 if has_ownership else 45
    clarity = 80 if 35 <= words <= 120 else (58 if words > 145 else 50)
    star_quality = int((specificity + impact + ownership + clarity) / 4)
    return {
        "star_quality": star_quality,
        "specificity": specificity,
        "measurable_impact": impact,
        "ownership": ownership,
        "clarity": clarity,
        "rambling": words > 145,
        "too_short": words < 25,
        "has_metric": has_metric,
        "has_result": has_result,
        "has_ownership": has_ownership,
    }


def _wz_ri_build_questions(cv_text: str, jd: str, company: str, role: str, website: str, company_context: str, language: str, personality: str):
    """Layered question generation: role context + candidate context + recruiter personality + memory + country expectations."""
    mem = _wz188_get_memory()
    recruiter_key, recruiter = _wz188_profile_from_personality(personality)
    role_key, role_layer = _wz188_role_layer(role, jd)
    country_key, country_layer = _wz188_country_layer(f"{jd} {company_context} {st.session_state.get('target_country','') if 'st' in globals() else ''}")

    memory_probe = ""
    if mem.get("areas_to_probe"):
        memory_probe = f"Earlier weak area to probe: {mem.get('areas_to_probe')[-1]}."
    elif mem.get("weak_points"):
        memory_probe = f"Candidate often struggles with: {mem.get('weak_points')[-1]}."

    fallback = [
        f"Your recruiter already read your CV. Tell me about yourself for the {role or 'target'} role, but keep it relevant to this job.",
        role_layer.get("question") or "Give me one specific example that proves you can do this role.",
        f"{memory_probe} Give me one measurable result from your most relevant experience.",
        f"I want to verify ownership. What specifically did YOU do, not the team?",
        f"How does your experience match the most important requirement in this job description?",
        f"Now answer under pressure: summarize your strongest fit in 45 seconds with one example and one measurable impact.",
    ]
    fallback = [q for q in fallback if _wz188_text(q)]

    # Use existing generator when available, but prepend intelligence-driven questions.
    try:
        if callable(_wz188_previous_build_questions):
            old = _wz188_previous_build_questions(cv_text, jd, company, role, website, company_context, language, personality)
            old_list = old if isinstance(old, list) else []
            combined = fallback[:3] + [x for x in old_list if _wz188_text(x)][:6]
            return combined[:8]
    except Exception:
        pass
    return fallback[:6]


def _wz_ri_react_to_answer(question: str, answer: str, cv_text: str, jd: str, qa_pairs: list, language: str, personality: str):
    """Adaptive recruiter reaction: memory-aware, personality-specific, pressure-sensitive, and role-aware."""
    role = st.session_state.get("target_role", "") if "st" in globals() else ""
    mem = _wz188_update_memory(question, answer, jd, role)
    recruiter_key, recruiter = _wz188_profile_from_personality(personality)
    role_key, role_layer = _wz188_role_layer(role, jd)
    country_key, country_layer = _wz188_country_layer(jd)
    scores = _wz188_answer_scores(answer, question)
    ans = _wz188_text(answer)
    words = len(ans.split())

    contradiction = _wz188_detect_contradiction(ans, mem)
    if contradiction:
        mem = _wz188_update_memory(question, answer, jd, role, "contradiction")
        return {
            "reaction": "I need to clarify something — this sounds inconsistent with what you said earlier.",
            "needs_followup": True,
            "followup_question": f"{contradiction} What was your exact role and responsibility?",
            "interruption_reason": "contradiction",
            "coach_note": "Recruiters lose trust when ownership or claims shift. Clarify precisely.",
            "recruiter_confidence": mem.get("confidence_level", 60),
            "pressure_level": mem.get("pressure_level", 50),
        }

    if scores["rambling"]:
        mem = _wz188_update_memory(question, answer, jd, role, "rambling")
        return {
            "reaction": recruiter.get("ramble_interrupt", "I’m going to stop you there — this is too long."),
            "needs_followup": True,
            "followup_question": "Answer again in 30–45 seconds: result first, then one example, then why it matters for this role.",
            "interruption_reason": "too long",
            "coach_note": "Lead with the result. Cut background. Recruiters reward concise evidence.",
            "recruiter_confidence": mem.get("confidence_level", 55),
            "pressure_level": mem.get("pressure_level", 65),
        }

    if scores["too_short"]:
        return {
            "reaction": "That is not enough evidence for me to evaluate you.",
            "needs_followup": True,
            "followup_question": "Give me one concrete example: situation, your action, and what changed.",
            "interruption_reason": "too short",
            "coach_note": "Short answers need proof. Add one specific example.",
            "recruiter_confidence": mem.get("confidence_level", 55),
            "pressure_level": mem.get("pressure_level", 55),
        }

    if not scores["has_ownership"]:
        return {
            "reaction": "That sounds team-based. I still don’t know what YOU personally did.",
            "needs_followup": True,
            "followup_question": "What was your exact contribution, and which part would not have happened without you?",
            "interruption_reason": "weak ownership",
            "coach_note": "Recruiters need your individual contribution, not only team activity.",
            "recruiter_confidence": mem.get("confidence_level", 58),
            "pressure_level": mem.get("pressure_level", 60),
        }

    if not scores["has_metric"]:
        return {
            "reaction": recruiter.get("metric_followup", "I’m missing the measurable impact."),
            "needs_followup": True,
            "followup_question": "How did you measure that? Give me a number, comparison, volume, speed, quality, customer result, or business impact.",
            "interruption_reason": "missing metric",
            "coach_note": "This is the highest-value fix: add truthful measurable impact.",
            "recruiter_confidence": mem.get("confidence_level", 60),
            "pressure_level": mem.get("pressure_level", 62),
        }

    # Role-specific deepener after a decent answer.
    if role_key in ["data", "analyst"] and not any(x in ans.lower() for x in ["sql", "dashboard", "tableau", "power bi", "data"]):
        return {
            "reaction": "Good example, but I want to test the data depth now.",
            "needs_followup": True,
            "followup_question": "What data, SQL logic, dashboard, or metric did you use, and how did it support a business decision?",
            "interruption_reason": "technical depth probe",
            "coach_note": "For analyst roles, recruiters expect tools + logic + business impact.",
            "recruiter_confidence": mem.get("confidence_level", 70),
            "pressure_level": mem.get("pressure_level", 45),
        }
    if role_key in ["support", "customer success"] and not any(x in ans.lower() for x in ["customer", "client", "ticket", "escalation", "retention", "resolution"]):
        return {
            "reaction": "Good, but I need to hear customer impact.",
            "needs_followup": True,
            "followup_question": "Which customer/client problem did this solve, and what changed after your action?",
            "interruption_reason": "customer impact probe",
            "coach_note": "For support/customer roles, show escalation handling and customer outcome.",
            "recruiter_confidence": mem.get("confidence_level", 70),
            "pressure_level": mem.get("pressure_level", 45),
        }

    # Memory callback if a previous weak area still exists.
    if mem.get("weak_points") and mem.get("answer_count", 0) >= 2:
        last_weak = mem.get("weak_points")[-1]
        if "missing measurable" in last_weak and not scores["has_metric"]:
            return {
                "reaction": "I’m noticing the same pattern again: not enough measurable proof.",
                "needs_followup": True,
                "followup_question": "Earlier answers also lacked numbers. Try again with one specific measurable outcome.",
                "interruption_reason": "repeated weak area",
                "coach_note": "Repeated weak areas are exactly what real recruiters remember.",
                "recruiter_confidence": mem.get("confidence_level", 56),
                "pressure_level": mem.get("pressure_level", 70),
            }

    return {
        "reaction": "Good — this gives me specific evidence to evaluate.",
        "needs_followup": False,
        "followup_question": "",
        "interruption_reason": "none",
        "coach_note": f"Strong enough to continue. {country_layer.get('coach', '')}",
        "recruiter_confidence": mem.get("confidence_level", 78),
        "pressure_level": mem.get("pressure_level", 35),
        "answer_scores": scores,
    }


def _wz_ri_score_full_interview(cv_text: str, jd: str, company: str, role: str, qa_pairs: list, reactions: list, language: str) -> dict:
    """Structured recruiter psychology scoring with memory, trust, pressure, and next practice loop."""
    mem = _wz188_get_memory()
    qa_pairs = qa_pairs if isinstance(qa_pairs, list) else []
    all_answers = []
    for item in qa_pairs:
        if isinstance(item, dict):
            all_answers.append(_wz188_text(item.get("answer") or item.get("a") or item.get("response")))
        elif isinstance(item, (list, tuple)) and len(item) > 1:
            all_answers.append(_wz188_text(item[1]))
    all_answers = [a for a in all_answers if a]

    scores = [_wz188_answer_scores(a) for a in all_answers] or [_wz188_answer_scores("")]
    avg = lambda key: int(sum(s.get(key, 0) for s in scores) / max(1, len(scores)))
    star = avg("star_quality")
    specificity = avg("specificity")
    impact = avg("measurable_impact")
    ownership = avg("ownership")
    clarity = avg("clarity")
    overall = int((star * 0.28) + (specificity * 0.18) + (impact * 0.24) + (ownership * 0.16) + (clarity * 0.14))

    weak = []
    strong = []
    if impact < 70: weak.append("measurable outcomes")
    else: strong.append("measurable business impact")
    if ownership < 65: weak.append("individual ownership")
    else: strong.append("clear ownership")
    if clarity < 65: weak.append("concise communication")
    else: strong.append("clear communication")
    if specificity < 65: weak.append("specific examples")
    else: strong.append("specific examples")
    if star < 70: weak.append("STAR structure")
    else: strong.append("STAR structure")

    mem["weak_points"] = list(dict.fromkeys((mem.get("weak_points") or []) + weak))[-8:]
    mem["strong_points"] = list(dict.fromkeys((mem.get("strong_points") or []) + strong))[-8:]
    mem["areas_to_probe"] = list(dict.fromkeys((mem.get("areas_to_probe") or []) + weak))[-8:]
    try:
        st.session_state["wz_recruiter_memory"] = mem
    except Exception:
        pass

    decision = "Strong — ready for a real recruiter round" if overall >= 82 else ("Borderline — needs one more practice round" if overall >= 60 else "High risk — practice before applying")
    reason = "The recruiter has enough evidence to trust your fit." if overall >= 82 else f"Recruiter confidence drops mainly around {', '.join(weak[:2]) or 'clear proof'}."

    result = {
        "overall_score": overall,
        "target_score": 80,
        "hiring_decision": decision,
        "recruiter_decision_summary": reason,
        "would_you_pass": "Yes" if overall >= 82 else ("Maybe" if overall >= 60 else "Not yet"),
        "referral_decision": "Yes" if overall >= 82 else ("Maybe" if overall >= 65 else "No"),
        "referral_reason": "A recruiter would refer you only if your answers show measurable impact, ownership, and role relevance.",
        "strengths": strong or mem.get("strong_points") or ["relevant background"],
        "weak_areas": weak or mem.get("weak_points") or ["needs more measurable evidence"],
        "top_3_mistakes": weak[:3] or ["missing measurable impact", "too much background", "weak job-description alignment"],
        "what_went_well": strong[:3] or ["role motivation", "communication potential"],
        "what_to_fix_next": [f"Add clearer proof of {x}" for x in (weak[:3] or ["measurable impact"])],
        "trust_risk_flags": [f"Weak signal: {x}" for x in (weak[:4] or ["specific proof"])] + (mem.get("contradictions") or [])[:1],
        "patterns_across_sessions": [
            f"Recurring pattern: {x}" for x in (mem.get("weak_points") or weak or ["answers need more measurable outcomes"])[-5:]
        ],
        "recruiter_emotional_timeline": [
            "🙂 Interested at opening" if strong else "😐 Neutral at opening",
            "⚠️ Doubt increased when evidence was vague" if weak else "🟢 Confidence improved with specific examples",
            "🔴 Confidence dropped on missing metrics" if "measurable outcomes" in weak else "🟢 Recovered after measurable answer",
            "🟢 Final confidence stabilized" if overall >= 70 else "🟡 Final confidence remains uncertain",
        ],
        "confidence_score": mem.get("confidence_level", overall),
        "pressure_level": mem.get("pressure_level", 40),
        "answer_evaluation": {
            "STAR quality": star,
            "specificity": specificity,
            "measurable impact": impact,
            "ownership": ownership,
            "clarity": clarity,
            "rambling_count": sum(1 for s in scores if s.get("rambling")),
            "filler_words": "Medium",
        },
        "next_practice_target": f"Practice {weak[0] if weak else 'one answer'} with result first, one specific example, measurable impact, and job relevance.",
        "weakest_answer_to_retry": all_answers[0] if all_answers else "Tell me about yourself and keep it relevant to the role.",
        "retry_instruction": "Retry this answer now with: result first → specific action → measurable outcome → why it matters for this job.",
        "old_vs_new_comparison_enabled": True,
    }

    # Merge selected fields from old scorer if it has better content, without losing v188 structure.
    try:
        if callable(_wz188_previous_score_full_interview):
            old = _wz188_previous_score_full_interview(cv_text, jd, company, role, qa_pairs, reactions, language)
            if isinstance(old, dict):
                for k in ["improved_answer_example", "strongest_answer", "answer_that_helped_you", "answer_that_damaged_trust"]:
                    if old.get(k) and not result.get(k):
                        result[k] = old.get(k)
    except Exception:
        pass

    return result


def wz188_pre_interview_live_status(role="", jd="", personality=""):
    """Small helper for dashboard/status widgets: pre-interview intelligence messages."""
    recruiter_key, recruiter = _wz188_profile_from_personality(personality)
    role_key, role_layer = _wz188_role_layer(role, jd)
    return [
        "Reviewing recruiter expectations...",
        f"Identified {', '.join(role_layer.get('probe', [])[:2])} as likely focus areas...",
        f"Preparing {recruiter_key}'s {recruiter.get('push_style', 'adaptive')} follow-ups...",
        "Extracting measurable achievement opportunities...",
        "Calibrating pressure based on your answers...",
    ]


# =========================================================
# WorkZo Streamlit-Ready Recruiter Intelligence Upgrade
# Manageable in Streamlit now; stronger real-time voice can replace it later.
# =========================================================
try:
    import json as _wz_sr_json, csv as _wz_sr_csv, uuid as _wz_sr_uuid, re as _wz_sr_re
    from pathlib import Path as _wz_sr_Path
    from datetime import datetime as _wz_sr_datetime
except Exception: pass

def _wz_sr_data_dir():
    try:
        p=_wz_sr_Path.cwd()/"workzo_data"; p.mkdir(parents=True, exist_ok=True); return p
    except Exception: return _wz_sr_Path(".")
def _wz_sr_user_id():
    try:
        if not st.session_state.get("wz_anonymous_user_id"): st.session_state["wz_anonymous_user_id"]="wz_"+_wz_sr_uuid.uuid4().hex[:12]
        return st.session_state["wz_anonymous_user_id"]
    except Exception: return "wz_local_user"
def _wz_sr_track(event, payload=None):
    payload=payload or {}
    try:
        if callable(globals().get("track_event")): track_event(event,"Interview",payload)
    except Exception: pass
    try:
        path=_wz_sr_data_dir()/"workzo_founder_analytics.csv"; new=not path.exists()
        with path.open("a", newline="", encoding="utf-8") as f:
            w=_wz_sr_csv.DictWriter(f, fieldnames=["ts","user_id","event","country","language","payload"])
            if new: w.writeheader()
            w.writerow({"ts":_wz_sr_datetime.utcnow().isoformat(),"user_id":_wz_sr_user_id(),"event":event,"country":str(st.session_state.get("country") or "Global"),"language":str(st.session_state.get("wz_ri_interview_language") or st.session_state.get("preferred_language") or "English"),"payload":_wz_sr_json.dumps(payload, ensure_ascii=False)})
    except Exception: pass
def _wz_sr_memory_path(): return _wz_sr_data_dir()/"workzo_interview_memory.json"
def _wz_sr_load_memory():
    try:
        p=_wz_sr_memory_path()
        return _wz_sr_json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    except Exception: return {}
def _wz_sr_save_memory(memory):
    try: _wz_sr_memory_path().write_text(_wz_sr_json.dumps(memory, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception: pass
def _wz_sr_country_rules(country=None):
    country=country or st.session_state.get("country") or st.session_state.get("selected_country") or "Global"
    try:
        if callable(globals().get("get_workzo_global_recruiter_rules")): return get_workzo_global_recruiter_rules(country)
    except Exception: pass
    return {"country":country,"tone":"balanced realistic","expects":["clear proof","role fit"],"risks":["generic answers"],"languages":["English"],"scoring_weights":{"relevance":18,"clarity":14,"star":16,"metrics":18,"ownership":16,"confidence":8,"country_fit":10}}
def _wz_sr_beta_disclaimer():
    try: st.info("🧪 Testing mode: voice, interruption timing, recruiter memory, analytics, and country behavior are Streamlit-ready beta features. A stronger real-time version is planned after moving WorkZo to a bigger platform.")
    except Exception: pass

def _wz_sr_score_answer(answer, jd="", cv_text="", question="", country=None):
    text=str(answer or "").strip(); lower=text.lower(); words=len(text.split()); jd_lower=str(jd or "").lower(); rules=_wz_sr_country_rules(country)
    weights=rules.get("scoring_weights",{}) if isinstance(rules,dict) else {}
    def w(k,d):
        try: return int(weights.get(k,d))
        except Exception: return d
    has_metric=bool(_wz_sr_re.search(r"\b\d+[\d,.]*\s?(%|percent|hours?|days?|weeks?|months?|users?|customers?|tickets?|cases?|reports?|dashboards?|€|\$|k|m)?\b", lower))
    impact=has_metric or any(x in lower for x in ["improved","reduced","increased","saved","resolved","optimized","automated","delivered","impact","result","outcome","faster","accuracy"])
    ownership=any(x in lower for x in ["i ","i was","i built","i created","i handled","i analyzed","i led","my role","my responsibility","i worked","i solved"])
    star_hits=sum(1 for x in ["situation","task","action","result","challenge","because","then","so i","finally","outcome"] if x in lower)
    jd_terms=[t for t in ["sql","python","excel","tableau","power bi","dashboard","api","customer","stakeholder","crm","support","analytics","report","sla","ticket"] if t in jd_lower]
    role_match=len([t for t in jd_terms if t in lower]); vague=sum(1 for p in ["many things","various","etc","good communication","hard working","team player","helped","worked on","responsible for"] if p in lower)
    too_short=words<35; too_long=words>145; unsupported=[x for x in ["expert","advanced","excellent","strong","proven","successfully"] if x in lower and not has_metric]
    relevance=min(10,4+role_match*2+(1 if not jd_terms else 0)); clarity=max(1,min(10,8-(2 if vague else 0)-(2 if too_long else 0)-(2 if too_short else 0)))
    star=max(1,min(10,2+star_hits*2+(2 if ownership else 0)+(2 if impact else 0))); metrics=10 if has_metric else 5 if impact else 2; ownership_score=9 if ownership else 3
    confidence=max(1,min(10,7-len(unsupported)-(2 if vague else 0)+(1 if has_metric else 0))); country_fit=7
    risks=" ".join([str(x).lower() for x in rules.get("risks",[])])
    if "overclaiming" in risks and unsupported: country_fit-=2
    if "missing numbers" in risks and not has_metric: country_fit-=2
    if "structure" in (risks+str(rules.get("tone","")).lower()) and star<6: country_fit-=1
    country_fit=max(1,min(10,country_fit)); total=w("relevance",18)+w("clarity",14)+w("star",16)+w("metrics",18)+w("ownership",16)+w("confidence",8)+w("country_fit",10)
    score=int(round((relevance*w("relevance",18)+clarity*w("clarity",14)+star*w("star",16)+metrics*w("metrics",18)+ownership_score*w("ownership",16)+confidence*w("confidence",8)+country_fit*w("country_fit",10))/max(1,total)*10))
    flags=[]; strengths=[]
    if not has_metric: flags.append("No measurable result detected")
    if not ownership: flags.append("Ownership is unclear")
    if star<6: flags.append("STAR structure is weak")
    if too_long: flags.append("Answer may be too long")
    if too_short: flags.append("Answer is too short to build trust")
    if vague: flags.append("Vague wording reduces recruiter confidence")
    if unsupported: flags.append("Sounds over-claimed without proof")
    if relevance<6: flags.append("Weak connection to job requirements")
    if has_metric: strengths.append("Measurable proof detected")
    if ownership: strengths.append("Personal contribution is visible")
    if role_match: strengths.append("Answer connects to role keywords")
    mood,signal,interrupt=("Engaged","Strengthening","") if score>=78 else (("Testing","Needs proof","Can you make the outcome more specific?") if score>=62 else (("Skeptical","Weakening","Let me stop you there — what was the actual result?") if score>=45 else ("Losing confidence","High risk","Can you answer that more directly? I’m still missing proof.")))
    return {"score":score,"scores":{"relevance":relevance,"clarity":clarity,"star":star,"metrics":metrics,"ownership":ownership_score,"confidence":confidence,"country_fit":country_fit},"flags":flags[:6],"strengths":strengths[:5],"mood":mood,"hiring_signal":signal,"interrupt":interrupt,"words":words,"country_rules":rules}

def _wz_sr_update_memory(answer, score_pack, event="answer_scored"):
    try:
        memory=_wz_sr_load_memory(); uid=_wz_sr_user_id(); profile=memory.get(uid) if isinstance(memory.get(uid),dict) else {"sessions":0,"answers":0,"patterns":{},"scores":[],"recovery_events":0}
        profile["answers"]=int(profile.get("answers",0))+1; profile.setdefault("scores",[]).append(int(score_pack.get("score",0))); profile["scores"]=profile["scores"][-30:]
        patterns=profile.get("patterns") if isinstance(profile.get("patterns"),dict) else {}
        for flag in score_pack.get("flags",[]): patterns[flag]=int(patterns.get(flag,0))+1
        profile["patterns"]=patterns
        if int(score_pack.get("score",0))<62: profile.update({"weakest_answer":str(answer or "")[:1200],"weakest_score":int(score_pack.get("score",0)),"weakest_flags":score_pack.get("flags",[])})
        if len(profile.get("scores",[]))>=2 and profile["scores"][-2]<62 and profile["scores"][-1]>=70: profile["recovery_events"]=int(profile.get("recovery_events",0))+1
        memory[uid]=profile; _wz_sr_save_memory(memory); st.session_state["wz_persistent_recruiter_memory"]=profile; return profile
    except Exception: return {}
def _wz_sr_apply_state(score_pack):
    try:
        state=st.session_state.get("wz_streamlit_recruiter_state") or {"confidence":72,"attention":82,"patience":68,"timeline":[]}; score=int(score_pack.get("score",60)); delta=(10,5,3) if score>=78 else ((2,0,0) if score>=62 else ((-12,-8,-6) if score>=45 else (-20,-14,-10)))
        clamp=lambda v:max(1,min(99,int(v))); before=int(state.get("confidence",72)); state["confidence"]=clamp(before+delta[0]); state["attention"]=clamp(int(state.get("attention",82))+delta[1]); state["patience"]=clamp(int(state.get("patience",68))+delta[2])
        state.update({"mood":score_pack.get("mood"),"hiring_signal":score_pack.get("hiring_signal"),"last_interrupt":score_pack.get("interrupt"),"last_flags":score_pack.get("flags",[]),"last_score":score})
        timeline=list(state.get("timeline",[])); timeline.append({"before":before,"after":state["confidence"],"score":score,"mood":state["mood"],"signal":state["hiring_signal"],"ts":_wz_sr_datetime.utcnow().isoformat()}); state["timeline"]=timeline[-12:]
        st.session_state["wz_streamlit_recruiter_state"]=state; st.session_state["wz195_recruiter_state"]=state; st.session_state["wz194_recruiter_state"]=state; return state
    except Exception: return {}
def _wz_sr_render_state_panel():
    try:
        state=st.session_state.get("wz_streamlit_recruiter_state") or {"confidence":72,"attention":82,"patience":68,"hiring_signal":"Needs proof"}; flags=state.get("last_flags",[]) or []
        st.markdown("### Recruiter confidence · live"); c1,c2,c3,c4=st.columns(4); c1.metric("Confidence",f"{state.get('confidence',72)}%"); c2.metric("Attention",f"{state.get('attention',82)}%"); c3.metric("Patience",f"{state.get('patience',68)}%"); c4.metric("Hiring signal",str(state.get("hiring_signal","Needs proof")))
        if flags: st.caption("Trust risks: "+" · ".join([str(x) for x in flags[:4]]))
    except Exception: pass
def _wz_sr_render_emotional_report():
    try:
        profile=st.session_state.get("wz_persistent_recruiter_memory") or _wz_sr_load_memory().get(_wz_sr_user_id(),{}); state=st.session_state.get("wz_streamlit_recruiter_state") or {}; timeline=state.get("timeline",[]) or []
        if not timeline and not profile: return
        st.markdown("## Recruiter psychology report"); st.caption("Where trust dropped, where you recovered, and what the recruiter would remember.")
        if timeline:
            labels=[]
            for item in timeline[-6:]:
                before,after=int(item.get("before",0)),int(item.get("after",0)); labels.append(("🟢 Recovered" if after>before else "🔴 Dropped" if after<before else "😐 Stable")+f" {before}% → {after}%")
            st.info("  →  ".join(labels))
        patterns=profile.get("patterns",{}) if isinstance(profile,dict) else {}
        if patterns: st.warning("Recurring patterns: "+" · ".join([f"{k} ({v}x)" for k,v in sorted(patterns.items(), key=lambda kv: kv[1], reverse=True)[:5]]))
        scores=profile.get("scores",[]) if isinstance(profile,dict) else []
        if scores:
            latest=int(scores[-1]); decision="YES" if latest>=78 else "MAYBE" if latest>=62 else "NO"; st.success(f"Would this recruiter refer you internally? {decision}. Latest answer trust score: {latest}/100.")
        weakest=profile.get("weakest_answer") if isinstance(profile,dict) else ""
        if weakest:
            with st.expander("🎤 Retry weakest answer now", expanded=True):
                st.caption("Old answer that damaged trust:"); st.write(weakest); retry=st.text_area("Rewrite it with truthful STAR structure and real proof", key="wz_sr_retry_weakest_text", height=120)
                if st.button("Compare old vs new", key="wz_sr_compare_weakest") and retry.strip():
                    old=int(profile.get("weakest_score",0)); new_pack=_wz_sr_score_answer(retry, st.session_state.get("wz_ri_jd",""), _wz_ri_get_cv_text() if callable(globals().get("_wz_ri_get_cv_text")) else ""); _wz_sr_apply_state(new_pack); _wz_sr_update_memory(retry,new_pack,"retry_weakest"); _wz_sr_track("retry_weakest_answer", {"old_score":old,"new_score":new_pack.get("score")}); st.success(f"Recovery result: {old}/100 → {new_pack.get('score')}/100")
    except Exception: pass
def _wz_sr_mobile_css():
    try:
        st.markdown(r'''
        <style id="wz-streamlit-intel-mobile-css">
        @media(max-width:760px){.block-container{padding-left:.75rem!important;padding-right:.75rem!important;padding-top:.7rem!important}[data-testid="stHorizontalBlock"]{gap:.5rem!important}.stButton button{min-height:42px!important;border-radius:13px!important}textarea{font-size:16px!important}[class*="workobot"],[class*="floating"],.workzo-floating-bot,.wz-floating-bot{right:16px!important;bottom:18px!important;transform:scale(.76)!important;transform-origin:bottom right!important;max-width:210px!important}}
        </style>''', unsafe_allow_html=True)
    except Exception: pass
try:
    _wz_sr_prev_country_rules=globals().get("_wz_ri_country_rules")
    def _wz_ri_country_rules(country: str) -> dict:
        rules=_wz_sr_country_rules(country); return {"country":rules.get("country",country),"style":rules.get("tone","realistic"),"expects":rules.get("expects",[]),"risks":rules.get("risks",[]),"languages":rules.get("languages",["English"]),"interruption_style":rules.get("interruption_style","Ask for clarity."),"resume_norms":rules.get("resume_norms",[]),"scoring_weights":rules.get("scoring_weights",{})}
except Exception: pass
try:
    _wz_sr_original_react_to_answer=globals().get("_wz_ri_react_to_answer")
    def _wz_ri_react_to_answer(question: str, answer: str, cv_text: str, jd: str, qa_pairs: list, language: str, personality: str):
        score_pack=_wz_sr_score_answer(answer,jd=jd,cv_text=cv_text,question=question,country=st.session_state.get("country") or "Global"); state=_wz_sr_apply_state(score_pack); _wz_sr_update_memory(answer,score_pack); _wz_sr_track("answer_scored", {"score":score_pack.get("score"),"mood":score_pack.get("mood"),"signal":score_pack.get("hiring_signal"),"flags":score_pack.get("flags",[])[:3]})
        reaction={}
        try:
            if callable(_wz_sr_original_react_to_answer): reaction=_wz_sr_original_react_to_answer(question,answer,cv_text,jd,qa_pairs,language,personality) or {}
        except Exception: reaction={}
        if not isinstance(reaction,dict): reaction={}
        reaction.setdefault("reaction", score_pack.get("interrupt") or ("Good, that gives me proof." if score_pack.get("score",0)>=78 else "I need stronger evidence before I trust this answer.")); reaction.setdefault("needs_followup", bool(score_pack.get("interrupt"))); reaction.setdefault("followup_question", "Give me the same answer again with your action and one truthful result." if score_pack.get("score",0)<62 else "Can you briefly connect that result to this role?"); reaction.setdefault("interruption_reason", score_pack.get("flags",["answer quality"])[0] if score_pack.get("flags") else "none"); reaction.setdefault("live_reaction", score_pack.get("mood")); reaction.setdefault("coach_note", " · ".join(score_pack.get("flags",[])[:3]) or "Keep it truthful, specific, and role-linked."); reaction["workzo_score_pack"]=score_pack; reaction["recruiter_state"]=state; return reaction
except Exception: pass
try:
    _wz_sr_original_render_interview=globals().get("render_real_interview_simulation")
    def render_real_interview_simulation():
        _wz_sr_mobile_css(); _wz_sr_beta_disclaimer(); _wz_sr_track("interview_page_opened", {"source":"streamlit_beta"}); result=None
        if callable(_wz_sr_original_render_interview): result=_wz_sr_original_render_interview()
        _wz_sr_render_state_panel(); return result
except Exception: pass
try:
    _wz_sr_original_final_score=globals().get("_wz_ri_render_final_score")
    def _wz_ri_render_final_score(result: dict, company: str, role: str, website: str, language: str):
        _wz_sr_track("interview_finished", {"company":company,"role":role,"score":(result or {}).get("overall_score") if isinstance(result,dict) else None})
        if callable(_wz_sr_original_final_score): _wz_sr_original_final_score(result,company,role,website,language)
        _wz_sr_render_emotional_report()
except Exception: pass
def workzo_streamlit_voice_interruption_hint(seconds_elapsed=0, answer_text=""):
    try:
        if int(seconds_elapsed or 0)>=90: return "Let me stop you there — give me the result first, then one example."
        if int(seconds_elapsed or 0)>=25 and not str(answer_text or "").strip():
            state=st.session_state.get("wz_streamlit_recruiter_state") or {"attention":82,"patience":68}; state["attention"]=max(1,int(state.get("attention",82))-6); state["patience"]=max(1,int(state.get("patience",68))-6); state["mood"]="Waiting"; st.session_state["wz_streamlit_recruiter_state"]=state; return "Take a breath — start with one specific example."
    except Exception: pass
    return ""

# =========================================================
# WorkZo v200 - Post-Interview-Only Recruiter Metrics
# =========================================================
# Fix: remove baseline/static recruiter confidence numbers from the live
# interview room. Confidence, attention, patience and hiring signal are still
# calculated silently after each submitted answer, but they are shown only in
# the final post-interview report after the user finishes the interview.
# This avoids showing demo-looking numbers while the recruiter is still asking
# questions.
# =========================================================

try:
    _wz200_original_render_interview = _wz_sr_original_render_interview
except Exception:
    _wz200_original_render_interview = globals().get("render_real_interview_simulation")

try:
    _wz200_original_final_score = _wz_sr_original_final_score
except Exception:
    _wz200_original_final_score = globals().get("_wz_ri_render_final_score")


def _wz_sr_render_state_panel():
    """Intentionally hidden during live interview.

    Recruiter state is still updated internally by _wz_sr_apply_state()
    after each answer. The user sees the derived confidence/timeline only
    after ending the interview, inside the post-interview report.
    """
    return None


def _wz200_has_real_answer_history():
    try:
        answers = st.session_state.get("wz_ri_answers")
        if isinstance(answers, list):
            for item in answers:
                if isinstance(item, dict):
                    ans = str(item.get("answer") or item.get("candidate_answer") or "").strip()
                else:
                    ans = str(item or "").strip()
                if len(ans.split()) >= 5:
                    return True
    except Exception:
        pass
    try:
        hist = st.session_state.get("wz197_answer_history")
        if isinstance(hist, list):
            for item in hist:
                if isinstance(item, dict) and len(str(item.get("answer") or "").split()) >= 5:
                    return True
    except Exception:
        pass
    return False


def _wz200_render_recruiter_metrics_after_interview():
    """Show confidence metrics only after real answers exist."""
    try:
        if not _wz200_has_real_answer_history():
            st.info("No recruiter confidence report yet. Finish at least one real interview answer first.")
            return
        state = st.session_state.get("wz_streamlit_recruiter_state") or {}
        timeline = state.get("timeline", []) if isinstance(state.get("timeline", []), list) else []
        confidence = int(state.get("confidence", 72) or 72)
        attention = int(state.get("attention", 82) or 82)
        patience = int(state.get("patience", 68) or 68)
        signal = str(state.get("hiring_signal") or "Still evaluating")
        mood = str(state.get("mood") or "Evaluating")
        flags = state.get("last_flags", []) if isinstance(state.get("last_flags", []), list) else []

        st.markdown("## Recruiter confidence after your answers")
        st.caption("These numbers are based on the answers you submitted in this interview, not pre-filled demo values.")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Confidence", f"{confidence}%")
        c2.metric("Attention", f"{attention}%")
        c3.metric("Patience", f"{patience}%")
        c4.metric("Hiring signal", signal)

        if timeline:
            parts = []
            for item in timeline[-6:]:
                before = int(item.get("before", 0) or 0)
                after = int(item.get("after", 0) or 0)
                label = "🟢 recovered" if after > before else "🔴 dropped" if after < before else "😐 stable"
                parts.append(f"{label} {before}% → {after}%")
            st.info("Recruiter confidence timeline: " + "  →  ".join(parts))

        if flags:
            st.warning("Recruiter trust risks detected: " + " · ".join([str(x) for x in flags[:5]]))
        else:
            st.success(f"Recruiter mood: {mood}. No major trust-risk flag detected in the latest answer.")
    except Exception:
        pass


def render_real_interview_simulation():
    """Voice/text interview room without visible baseline confidence metrics."""
    try:
        _wz_sr_mobile_css()
    except Exception:
        pass
    try:
        _wz_sr_beta_disclaimer()
    except Exception:
        pass
    try:
        _wz_sr_track("interview_page_opened", {"source": "streamlit_beta_no_live_metrics"})
    except Exception:
        pass
    result = None
    try:
        if callable(_wz200_original_render_interview):
            result = _wz200_original_render_interview()
    except Exception as exc:
        try:
            st.error(f"Interview room could not load safely: {exc}")
        except Exception:
            pass
    # Do NOT render confidence/attention/patience here.
    return result


def _wz_ri_render_final_score(result: dict, company: str, role: str, website: str, language: str):
    """Final report with recruiter state shown only after interview completion."""
    try:
        _wz_sr_track("interview_finished", {"company": company, "role": role, "score": (result or {}).get("overall_score") if isinstance(result, dict) else None})
    except Exception:
        pass
    try:
        if callable(_wz200_original_final_score):
            _wz200_original_final_score(result, company, role, website, language)
    except Exception:
        pass
    _wz200_render_recruiter_metrics_after_interview()
    try:
        _wz_sr_render_emotional_report()
    except Exception:
        pass

# =========================================================
# WorkZo v200 - Recruiter + Interview Language Sync Fix
# =========================================================
# Problem fixed:
# - Dashboard dropdowns could show Daniel/German, but the voice room still used
#   stale Sarah/English defaults.
# - This patch locks the latest dashboard selections at interview start, maps the
#   selected recruiter to the correct Streamlit voice/personality mode, and rebuilds
#   the first question in the selected language if stale questions are detected.
# =========================================================

def _wz200_clean_text(value, fallback=""):
    try:
        value = str(value or "").strip()
        return value if value else fallback
    except Exception:
        return fallback


def _wz200_latest_language():
    """Read the newest interview language from dashboard and interview state."""
    candidates = [
        st.session_state.get("interview_language"),
        st.session_state.get("wz_ri_interview_language"),
        st.session_state.get("wz_ri_language_choice_v150"),
        st.session_state.get("preferred_language"),
        st.session_state.get("language"),
        st.session_state.get("response_language"),
    ]
    for lang in candidates:
        lang = _wz200_clean_text(lang, "")
        if lang and lang.lower() not in ["auto", "auto-detect", "auto-detect / user preference", "same as interview"]:
            return lang
    return "English"


def _wz200_latest_recruiter():
    """Read the newest selected recruiter from dashboard and interview state."""
    candidates = [
        st.session_state.get("wz_ri_recruiter_personality_v181"),
        st.session_state.get("wz_ri_recruiter_personality"),
        st.session_state.get("wz_voice_recruiter_name"),
        st.session_state.get("selected_recruiter"),
        st.session_state.get("interviewer_personality"),
        st.session_state.get("wz_ri_personality"),
    ]
    for rec in candidates:
        rec = _wz200_clean_text(rec, "")
        if rec:
            return rec
    return "👩 Sarah — Friendly HR"


def _wz200_map_recruiter_to_personality(recruiter):
    """Map Sarah/Daniel/Priya/Markus into older 09_interview_assistant choices."""
    low = _wz200_clean_text(recruiter, "").lower()
    if "daniel" in low or "technical" in low:
        return "Technical recruiter"
    if "priya" in low or "startup" in low or "fast" in low:
        return "Fast-paced"
    if "markus" in low or "german" in low or "corporate" in low:
        return "Strict"
    if "skeptical" in low or "hiring manager" in low:
        return "Skeptical hiring manager"
    return "Friendly"


def _wz200_recruiter_display_name(recruiter):
    rec = _wz200_clean_text(recruiter, "Sarah — Friendly HR")
    # Keep emoji if present, but remove duplicate weird whitespace.
    return " ".join(rec.replace("—", " — ").split())


def _wz200_voice_gender(recruiter):
    low = _wz200_clean_text(recruiter, "").lower()
    if any(x in low for x in ["daniel", "markus", "male", "manager", "technical"]):
        return "male"
    return "female"


def _wz200_opening_question(language, recruiter, role, company, candidate=""):
    role = _wz200_clean_text(role, "this role")
    company = _wz200_clean_text(company, "the company")
    candidate = _wz200_clean_text(candidate, "")
    name_part_de = f" {candidate}," if candidate else ""
    name_part_en = f" {candidate}," if candidate else ""
    lang = _wz200_clean_text(language, "English").lower()
    if lang == "german":
        return f"Guten Tag{name_part_de}. Lassen Sie uns beginnen. Stellen Sie sich bitte kurz vor und verbinden Sie Ihren Hintergrund direkt mit der Position {role} bei {company}."
    if lang == "dutch":
        return f"Goedendag{name_part_en}. Laten we beginnen. Stel jezelf kort voor en verbind je achtergrond direct met de functie {role} bij {company}."
    if lang == "french":
        return f"Bonjour{name_part_en}. Commençons. Présentez-vous brièvement et reliez votre parcours directement au poste {role} chez {company}."
    if lang == "spanish":
        return f"Hola{name_part_en}. Empecemos. Preséntate brevemente y conecta tu experiencia directamente con el puesto de {role} en {company}."
    if lang == "portuguese":
        return f"Olá{name_part_en}. Vamos começar. Apresente-se brevemente e conecte sua experiência diretamente à vaga de {role} na {company}."
    if lang == "italian":
        return f"Buongiorno{name_part_en}. Iniziamo. Presentati brevemente e collega il tuo percorso direttamente al ruolo di {role} presso {company}."
    if lang == "hindi":
        return f"Namaste{name_part_en}. Chaliye shuru karte hain. Apne background ka short introduction dijiye aur use {company} mein {role} role se directly connect kijiye."
    if lang == "tamil":
        return f"Vanakkam{name_part_en}. தொடங்கலாம். உங்கள் background-ஐ சுருக்கமாக சொல்லி, அதை {company}-இல் {role} role-க்கு நேரடியாக இணைக்கவும்."
    return f"Hi{name_part_en}, welcome. To begin, give me a short introduction and connect your background directly to {role} at {company}."


def _wz200_fallback_question(language, index, role, company):
    lang = _wz200_clean_text(language, "English").lower()
    role = _wz200_clean_text(role, "this role")
    company = _wz200_clean_text(company, "the company")
    if lang == "german":
        qs = [
            f"Nennen Sie mir ein konkretes Beispiel, das zeigt, dass Sie für {role} geeignet sind.",
            "Was war Ihr messbares Ergebnis oder konkreter Beitrag?",
            "Wie würden frühere Kolleginnen oder Kollegen Ihre Arbeitsweise beschreiben?",
            f"Warum passt Ihr Profil zu {company}?",
            "Welche Schwäche könnte in diesem Interview Zweifel auslösen, und wie gehen Sie damit um?",
        ]
    elif lang == "french":
        qs = [
            f"Donnez-moi un exemple concret qui prouve votre adéquation pour le poste {role}.",
            "Quel résultat mesurable avez-vous obtenu ?",
            "Comment vos collègues décriraient-ils votre façon de travailler ?",
            f"Pourquoi votre profil correspond-il à {company} ?",
            "Quel point faible pourrait inquiéter le recruteur et comment le gérez-vous ?",
        ]
    elif lang == "spanish":
        qs = [
            f"Dame un ejemplo concreto que demuestre que encajas en el puesto de {role}.",
            "¿Cuál fue el resultado medible de tu trabajo?",
            "¿Cómo describirían tus compañeros tu forma de trabajar?",
            f"¿Por qué encaja tu perfil con {company}?",
            "¿Qué debilidad podría preocupar al reclutador y cómo la manejarías?",
        ]
    else:
        qs = [
            f"Give me one specific example that proves you can succeed in {role}.",
            "What was the measurable outcome of your work?",
            "How would previous colleagues describe your working style?",
            f"Why does your profile fit {company}?",
            "What weakness might make a recruiter doubt you, and how would you handle it?",
        ]
    return qs[(max(1, int(index)) - 1) % len(qs)]


# Let dashboard v199 use these if it initializes questions before calling 09.
def _wz_voice_first_build_opening_question(cv_text, jd, role, company, language):
    recruiter = _wz200_latest_recruiter()
    candidate = _wz200_clean_text(st.session_state.get("candidate_name") or st.session_state.get("user_name"), "")
    return _wz200_opening_question(language, recruiter, role, company, candidate)


def _wz_voice_first_next_question(cv_text, jd, role, company, language, answers, index):
    return _wz200_fallback_question(language, index, role, company)


def _wz200_apply_selection_lock(reset_stale_questions=True):
    """Force 09_interview_assistant to respect latest dashboard recruiter/language values."""
    try:
        language = _wz200_latest_language()
        recruiter = _wz200_latest_recruiter()
        personality = _wz200_map_recruiter_to_personality(recruiter)
        display = _wz200_recruiter_display_name(recruiter)

        # Lock language everywhere old/new modules read it.
        st.session_state["wz_ri_interview_language"] = language
        st.session_state["preferred_language"] = language
        st.session_state["language"] = language
        st.session_state["response_language"] = language
        st.session_state["ui_language"] = language
        st.session_state["wz_ri_answer_language"] = "Same as interview"
        st.session_state["wz_ri_answer_language_v150"] = "Same as interview"
        # Old setup selectbox uses this key. Setting before render prevents stale Auto/English.
        st.session_state["wz_ri_language_choice_v150"] = language

        # Lock recruiter everywhere old/new modules read it.
        st.session_state["wz_ri_recruiter_personality_v181"] = display
        st.session_state["wz_ri_recruiter_personality"] = display
        st.session_state["wz_voice_recruiter_name"] = display
        st.session_state["wz_voice_recruiter_gender"] = _wz200_voice_gender(display)
        st.session_state["wz_ri_personality"] = personality

        role = _wz200_clean_text(st.session_state.get("wz_ri_role") or st.session_state.get("target_role") or st.session_state.get("target_job_title"), "the role")
        company = _wz200_clean_text(st.session_state.get("wz_ri_company") or st.session_state.get("target_company"), "the company")
        st.session_state["wz_ri_role"] = role
        st.session_state["target_role"] = role
        st.session_state["target_job_title"] = role
        st.session_state["wz_ri_company"] = company
        st.session_state["target_company"] = company

        lock = {"language": language, "recruiter": display, "personality": personality, "role": role, "company": company}
        previous = st.session_state.get("wz_ri_selection_lock")
        changed = previous != lock
        st.session_state["wz_ri_selection_lock"] = lock

        if reset_stale_questions and changed:
            # User changed recruiter/language. Rebuild only if an interview has started or questions exist.
            if st.session_state.get("wz_ri_started") or isinstance(st.session_state.get("wz_ri_questions"), list):
                qs = [_wz200_opening_question(language, display, role, company)]
                for i in range(1, 6):
                    qs.append(_wz200_fallback_question(language, i, role, company))
                st.session_state["wz_ri_questions"] = qs
                st.session_state["wz_ri_current_index"] = 0
                st.session_state["wz_ri_answers"] = []
                st.session_state["wz_ri_live_reactions"] = []
                st.session_state["wz_ri_final_score"] = {}
                st.session_state["wz_ri_closing_reached"] = False
                st.session_state["wz_ri_audio_nonce"] = int(st.session_state.get("wz_ri_audio_nonce", 0) or 0) + 1
                try:
                    import time as _time
                    st.session_state["wz_ri_question_started_at"] = _time.time()
                except Exception:
                    pass
        return lock
    except Exception:
        return {}


try:
    _wz200_original_render_real_interview_simulation = render_real_interview_simulation
except Exception:
    _wz200_original_render_real_interview_simulation = None


def render_real_interview_simulation():
    """Wrapper: sync latest recruiter and language before rendering the voice interview."""
    _wz200_apply_selection_lock(reset_stale_questions=True)
    if callable(_wz200_original_render_real_interview_simulation):
        return _wz200_original_render_real_interview_simulation()
    st.error("Interview renderer is unavailable.")


# =========================================================
# WorkZo v201 - ALL supported languages sync + voice intent fix
# Purpose:
# - The recruiter/language lock must work for every supported interview language,
#   not only German.
# - If the user selects Daniel/Priya/Sarah/any recruiter and any language,
#   the first question, fallbacks, timer/interruption phrases, and browser TTS
#   intent should all follow that selection.
# - This remains Streamlit/browser-speech beta; stronger native voice can replace it later.
# =========================================================

_WZ201_SUPPORTED_LANGUAGES = [
    "English", "German", "Dutch", "French", "Spanish", "Portuguese", "Italian", "Arabic",
    "Hindi", "Tamil", "Polish", "Turkish", "Swedish", "Danish", "Norwegian", "Finnish",
    "Czech", "Greek", "Japanese", "Korean", "Chinese"
]

_WZ201_LANG_ALIASES = {
    "auto-detect / user preference": "English",
    "auto-detect": "English",
    "auto": "English",
    "same as interview": "English",
    "deutsch": "German",
    "german": "German",
    "english": "English",
    "eng": "English",
    "dutch": "Dutch",
    "nederlands": "Dutch",
    "french": "French",
    "français": "French",
    "francais": "French",
    "spanish": "Spanish",
    "español": "Spanish",
    "espanol": "Spanish",
    "portuguese": "Portuguese",
    "português": "Portuguese",
    "portugues": "Portuguese",
    "italian": "Italian",
    "italiano": "Italian",
    "arabic": "Arabic",
    "العربية": "Arabic",
    "hindi": "Hindi",
    "हिंदी": "Hindi",
    "tamil": "Tamil",
    "தமிழ்": "Tamil",
    "polish": "Polish",
    "polski": "Polish",
    "turkish": "Turkish",
    "türkçe": "Turkish",
    "turkce": "Turkish",
    "swedish": "Swedish",
    "svenska": "Swedish",
    "danish": "Danish",
    "dansk": "Danish",
    "norwegian": "Norwegian",
    "norsk": "Norwegian",
    "finnish": "Finnish",
    "suomi": "Finnish",
    "czech": "Czech",
    "čeština": "Czech",
    "cestina": "Czech",
    "greek": "Greek",
    "ελληνικά": "Greek",
    "japanese": "Japanese",
    "日本語": "Japanese",
    "korean": "Korean",
    "한국어": "Korean",
    "chinese": "Chinese",
    "中文": "Chinese",
    "mandarin": "Chinese",
}

_WZ201_SPEECH_LANG_CODES = {
    "English": "en-US",
    "German": "de-DE",
    "Dutch": "nl-NL",
    "French": "fr-FR",
    "Spanish": "es-ES",
    "Portuguese": "pt-PT",
    "Italian": "it-IT",
    "Arabic": "ar-SA",
    "Hindi": "hi-IN",
    "Tamil": "ta-IN",
    "Polish": "pl-PL",
    "Turkish": "tr-TR",
    "Swedish": "sv-SE",
    "Danish": "da-DK",
    "Norwegian": "nb-NO",
    "Finnish": "fi-FI",
    "Czech": "cs-CZ",
    "Greek": "el-GR",
    "Japanese": "ja-JP",
    "Korean": "ko-KR",
    "Chinese": "zh-CN",
}

_WZ201_TRANSLATIONS = {
    "English": {
        "intro": "Let’s begin. Give me a brief introduction based on your CV, and connect it to this job.",
        "timer_left": "⏱ {seconds}s left. Keep it concise and structured.",
        "interrupt_time": "Hmm, let me stop you there. In a real interview I need a sharper answer: direct point, one example, and the result.",
        "too_short": "Hmm, that’s too short. Give me a real example — what happened, what you did, and what changed?",
        "too_long": "I’ll stop you there — you’re losing the main point. Give me the same answer in 45 seconds with one clear result.",
        "missing_impact": "Okay, interesting — but I’m missing the impact. What was the measurable outcome?",
        "followups": [
            "Give me one specific example that proves you can succeed in {role}.",
            "What was the measurable outcome of your work?",
            "How would previous colleagues describe your working style?",
            "Why does your profile fit {company}?",
            "What weakness might make a recruiter doubt you, and how would you handle it?",
        ],
    },
    "German": {
        "intro": "Lassen Sie uns beginnen. Stellen Sie sich kurz anhand Ihres Lebenslaufs vor und verbinden Sie es mit dieser Stelle.",
        "timer_left": "⏱ Noch {seconds}s. Antworten Sie kurz und strukturiert.",
        "interrupt_time": "Hm, ich unterbreche Sie kurz. In einem echten Interview brauche ich eine klarere Antwort: Punkt, Beispiel und Ergebnis.",
        "too_short": "Hm, das ist zu kurz. Geben Sie mir ein konkretes Beispiel: Was ist passiert, was haben Sie getan, und was hat sich verändert?",
        "too_long": "Ich stoppe Sie kurz — der Hauptpunkt geht verloren. Sagen Sie es in 45 Sekunden mit einem klaren Ergebnis.",
        "missing_impact": "Okay, interessant — aber mir fehlt die Wirkung. Was war das messbare Ergebnis?",
        "followups": [
            "Nennen Sie mir ein konkretes Beispiel, das zeigt, dass Sie für {role} geeignet sind.",
            "Was war Ihr messbares Ergebnis oder konkreter Beitrag?",
            "Wie würden frühere Kolleginnen oder Kollegen Ihre Arbeitsweise beschreiben?",
            "Warum passt Ihr Profil zu {company}?",
            "Welche Schwäche könnte in diesem Interview Zweifel auslösen, und wie gehen Sie damit um?",
        ],
    },
    "Dutch": {
        "intro": "Laten we beginnen. Geef een korte introductie op basis van je cv en koppel die aan deze functie.",
        "timer_left": "⏱ Nog {seconds}s. Houd het kort en gestructureerd.",
        "interrupt_time": "Hmm, ik onderbreek je even. In een echt interview heb ik een scherper antwoord nodig: punt, voorbeeld en resultaat.",
        "too_short": "Hmm, dat is te kort. Geef een concreet voorbeeld: wat gebeurde er, wat deed jij, en wat veranderde er?",
        "too_long": "Ik stop je even — je verliest de kern. Geef hetzelfde antwoord in 45 seconden met één duidelijk resultaat.",
        "missing_impact": "Oké, interessant — maar ik mis de impact. Wat was het meetbare resultaat?",
        "followups": [
            "Geef één concreet voorbeeld dat bewijst dat je kunt slagen in {role}.",
            "Wat was het meetbare resultaat van je werk?",
            "Hoe zouden voormalige collega’s jouw werkstijl beschrijven?",
            "Waarom past jouw profiel bij {company}?",
            "Welke zwakte kan een recruiter laten twijfelen, en hoe ga je daarmee om?",
        ],
    },
    "French": {
        "intro": "Commençons. Présentez-vous brièvement à partir de votre CV et reliez votre profil à ce poste.",
        "timer_left": "⏱ Encore {seconds}s. Répondez de façon concise et structurée.",
        "interrupt_time": "Hmm, je vous interromps ici. Dans un vrai entretien, il faut une réponse plus claire : l’idée, un exemple et le résultat.",
        "too_short": "Hmm, c’est trop court. Donnez-moi un exemple concret : que s’est-il passé, qu’avez-vous fait, et quel a été le résultat ?",
        "too_long": "Je vous arrête ici — le point principal se perd. Répondez en 45 secondes avec un résultat clair.",
        "missing_impact": "D’accord, intéressant — mais il manque l’impact. Quel était le résultat mesurable ?",
        "followups": [
            "Donnez-moi un exemple concret qui prouve votre adéquation pour le poste {role}.",
            "Quel résultat mesurable avez-vous obtenu ?",
            "Comment vos collègues décriraient-ils votre façon de travailler ?",
            "Pourquoi votre profil correspond-il à {company} ?",
            "Quel point faible pourrait inquiéter le recruteur et comment le gérez-vous ?",
        ],
    },
    "Spanish": {
        "intro": "Empecemos. Preséntate brevemente usando tu CV y conecta tu experiencia con este puesto.",
        "timer_left": "⏱ Quedan {seconds}s. Responde de forma breve y estructurada.",
        "interrupt_time": "Hmm, te interrumpo aquí. En una entrevista real necesito una respuesta más clara: punto principal, ejemplo y resultado.",
        "too_short": "Hmm, eso es demasiado corto. Dame un ejemplo real: qué pasó, qué hiciste y qué cambió.",
        "too_long": "Te interrumpo — se está perdiendo el punto principal. Respóndelo en 45 segundos con un resultado claro.",
        "missing_impact": "Bien, interesante — pero falta el impacto. ¿Cuál fue el resultado medible?",
        "followups": [
            "Dame un ejemplo concreto que demuestre que encajas en el puesto de {role}.",
            "¿Cuál fue el resultado medible de tu trabajo?",
            "¿Cómo describirían tus compañeros tu forma de trabajar?",
            "¿Por qué encaja tu perfil con {company}?",
            "¿Qué debilidad podría preocupar al reclutador y cómo la manejarías?",
        ],
    },
    "Portuguese": {
        "intro": "Vamos começar. Apresente-se brevemente com base no seu CV e conecte sua experiência a esta vaga.",
        "timer_left": "⏱ Faltam {seconds}s. Seja breve e estruturado.",
        "interrupt_time": "Hmm, vou interromper aqui. Em uma entrevista real, preciso de uma resposta mais objetiva: ponto principal, exemplo e resultado.",
        "too_short": "Hmm, isso está curto demais. Dê um exemplo real: o que aconteceu, o que você fez e o que mudou?",
        "too_long": "Vou interromper — você está perdendo o ponto principal. Responda em 45 segundos com um resultado claro.",
        "missing_impact": "Certo, interessante — mas falta o impacto. Qual foi o resultado mensurável?",
        "followups": [
            "Dê um exemplo concreto que prove que você pode ter sucesso em {role}.",
            "Qual foi o resultado mensurável do seu trabalho?",
            "Como ex-colegas descreveriam seu estilo de trabalho?",
            "Por que seu perfil combina com {company}?",
            "Que ponto fraco poderia fazer um recrutador duvidar de você, e como você lidaria com isso?",
        ],
    },
    "Italian": {
        "intro": "Iniziamo. Presentati brevemente usando il tuo CV e collega la tua esperienza a questa posizione.",
        "timer_left": "⏱ Restano {seconds}s. Rispondi in modo breve e strutturato.",
        "interrupt_time": "Hmm, ti interrompo qui. In un vero colloquio ho bisogno di una risposta più chiara: punto principale, esempio e risultato.",
        "too_short": "Hmm, è troppo breve. Dammi un esempio concreto: cosa è successo, cosa hai fatto e cosa è cambiato?",
        "too_long": "Ti interrompo — stai perdendo il punto principale. Rispondi in 45 secondi con un risultato chiaro.",
        "missing_impact": "Ok, interessante — ma manca l’impatto. Qual è stato il risultato misurabile?",
        "followups": [
            "Fammi un esempio concreto che dimostri che puoi avere successo nel ruolo {role}.",
            "Qual è stato il risultato misurabile del tuo lavoro?",
            "Come descriverebbero il tuo stile di lavoro i tuoi ex colleghi?",
            "Perché il tuo profilo è adatto a {company}?",
            "Quale debolezza potrebbe far dubitare un recruiter e come la gestiresti?",
        ],
    },
    "Arabic": {
        "intro": "لنبدأ. قدّم نفسك باختصار بناءً على سيرتك الذاتية واربط خبرتك بهذه الوظيفة.",
        "timer_left": "⏱ بقي {seconds} ثانية. اجعل إجابتك مختصرة ومنظمة.",
        "interrupt_time": "دعني أوقفك هنا. في مقابلة حقيقية أحتاج إلى إجابة أوضح: النقطة الرئيسية، مثال، والنتيجة.",
        "too_short": "هذه الإجابة قصيرة جداً. أعطني مثالاً حقيقياً: ماذا حدث، ماذا فعلت، وما النتيجة؟",
        "too_long": "سأوقفك هنا — الفكرة الأساسية تضيع. أعطني الإجابة خلال 45 ثانية مع نتيجة واضحة.",
        "missing_impact": "مثير للاهتمام، لكن ينقصني الأثر. ما النتيجة القابلة للقياس؟",
        "followups": [
            "أعطني مثالاً محدداً يثبت أنك مناسب لدور {role}.",
            "ما النتيجة القابلة للقياس من عملك؟",
            "كيف سيصف زملاؤك السابقون أسلوب عملك؟",
            "لماذا يناسب ملفك شركة {company}؟",
            "ما نقطة الضعف التي قد تجعل مسؤول التوظيف يتردد، وكيف ستتعامل معها؟",
        ],
    },
    "Hindi": {
        "intro": "चलिए शुरू करते हैं। अपने CV के आधार पर अपना छोटा introduction दीजिए और इसे इस job से जोड़िए।",
        "timer_left": "⏱ {seconds}s बाकी हैं। जवाब छोटा और structured रखें।",
        "interrupt_time": "Hmm, मैं आपको यहीं रोकूंगा। Real interview में मुझे साफ जवाब चाहिए: main point, example और result.",
        "too_short": "Hmm, यह बहुत छोटा है। एक real example दीजिए: क्या हुआ, आपने क्या किया, और क्या बदला?",
        "too_long": "मैं आपको रोकता हूँ — main point खो रहा है। यही answer 45 seconds में एक clear result के साथ दीजिए।",
        "missing_impact": "Okay, interesting — लेकिन impact missing है। measurable outcome क्या था?",
        "followups": [
            "अपने CV के आधार पर बताइए कि आप {role} role के लिए क्यों fit हैं?",
            "आपके काम का measurable outcome क्या था?",
            "आपके पुराने colleagues आपकी working style को कैसे describe करेंगे?",
            "आपका profile {company} के लिए क्यों fit है?",
            "कौन सी weakness recruiter को doubt दे सकती है, और आप उसे कैसे handle करेंगे?",
        ],
    },
    "Tamil": {
        "intro": "தொடங்கலாம். உங்கள் CV அடிப்படையில் சிறிய அறிமுகம் சொல்லி, அதை இந்த job-க்கு இணைக்கவும்.",
        "timer_left": "⏱ இன்னும் {seconds}s. சுருக்கமாகவும் கட்டமைப்புடனும் பதிலளிக்கவும்.",
        "interrupt_time": "Hmm, இங்கே நான் நிறுத்துகிறேன். உண்மையான interview-ல் தெளிவான பதில் வேண்டும்: முக்கிய point, example, result.",
        "too_short": "Hmm, இது மிகவும் short. ஒரு real example சொல்லுங்கள்: என்ன நடந்தது, நீங்கள் என்ன செய்தீர்கள், என்ன result?",
        "too_long": "நான் இங்கே நிறுத்துகிறேன் — முக்கிய point தெளிவாக இல்லை. இதே பதிலை 45 seconds-ல் ஒரு தெளிவான result உடன் சொல்லுங்கள்.",
        "missing_impact": "சரி, interesting — ஆனால் impact missing. measurable outcome என்ன?",
        "followups": [
            "உங்கள் CV அடிப்படையில், {role} role-க்கு நீங்கள் ஏன் பொருத்தமானவர்?",
            "உங்கள் வேலைக்கான measurable result என்ன?",
            "முந்தைய colleagues உங்கள் working style-ஐ எப்படி describe செய்வார்கள்?",
            "உங்கள் profile {company}-க்கு ஏன் fit?",
            "எந்த weakness recruiter-க்கு doubt தரலாம், அதை எப்படி handle செய்வீர்கள்?",
        ],
    },
}

# Compact translated packs for additional languages. If a phrase is not included, WorkZo still asks the AI to generate in the selected language.
_WZ201_TRANSLATIONS.update({
    "Polish": {
        "intro": "Zacznijmy. Krótko przedstaw się na podstawie CV i połącz swoje doświadczenie z tym stanowiskiem.",
        "timer_left": "⏱ Zostało {seconds}s. Odpowiedz krótko i konkretnie.",
        "interrupt_time": "Przerwę tutaj. W prawdziwej rozmowie potrzebuję jaśniejszej odpowiedzi: punkt, przykład i wynik.",
        "too_short": "To zbyt krótko. Podaj konkretny przykład: co się stało, co zrobiłeś/zrobiłaś i jaki był wynik?",
        "too_long": "Przerwę — gubisz główny punkt. Odpowiedz w 45 sekund z jednym jasnym wynikiem.",
        "missing_impact": "Interesujące, ale brakuje wpływu. Jaki był mierzalny rezultat?",
        "followups": ["Podaj konkretny przykład, który pokazuje, że pasujesz do roli {role}.", "Jaki był mierzalny wynik Twojej pracy?", "Jak byli współpracownicy opisaliby Twój styl pracy?", "Dlaczego Twój profil pasuje do {company}?", "Jaka słabość może wzbudzić wątpliwości rekrutera i jak sobie z nią poradzisz?"],
    },
    "Turkish": {
        "intro": "Başlayalım. CV’ne dayanarak kendini kısaca tanıt ve deneyimini bu rolle ilişkilendir.",
        "timer_left": "⏱ {seconds}s kaldı. Kısa ve yapılandırılmış cevap ver.",
        "interrupt_time": "Burada durdurayım. Gerçek bir mülakatta daha net bir cevap isterim: ana nokta, örnek ve sonuç.",
        "too_short": "Bu çok kısa. Gerçek bir örnek ver: ne oldu, sen ne yaptın ve ne değişti?",
        "too_long": "Seni burada durduruyorum — ana noktayı kaybediyorsun. Aynı cevabı 45 saniyede net bir sonuçla ver.",
        "missing_impact": "İlginç, ama etkiyi göremiyorum. Ölçülebilir sonuç neydi?",
        "followups": ["{role} rolünde başarılı olabileceğini kanıtlayan somut bir örnek ver.", "Çalışmanın ölçülebilir sonucu neydi?", "Eski ekip arkadaşların çalışma tarzını nasıl tarif ederdi?", "Profilin neden {company} için uygun?", "Hangi zayıflığın işe alımcıda şüphe yaratabilir ve bunu nasıl yönetirsin?"],
    },
    "Swedish": {"intro":"Låt oss börja. Presentera dig kort utifrån ditt CV och koppla din bakgrund till den här rollen.","timer_left":"⏱ {seconds}s kvar. Håll det kort och strukturerat.","interrupt_time":"Jag avbryter dig där. I en riktig intervju behöver jag ett tydligare svar: poäng, exempel och resultat.","too_short":"Det är för kort. Ge ett konkret exempel: vad hände, vad gjorde du och vad förändrades?","too_long":"Jag stoppar dig där — huvudpoängen försvinner. Svara på 45 sekunder med ett tydligt resultat.","missing_impact":"Intressant, men jag saknar påverkan. Vad var det mätbara resultatet?","followups":["Ge ett konkret exempel som visar att du kan lyckas i rollen {role}.","Vad var det mätbara resultatet av ditt arbete?","Hur skulle tidigare kollegor beskriva din arbetsstil?","Varför passar din profil {company}?","Vilken svaghet kan få en rekryterare att tveka och hur hanterar du den?"]},
    "Danish": {"intro":"Lad os begynde. Præsentér dig kort ud fra dit CV og forbind din baggrund med denne rolle.","timer_left":"⏱ {seconds}s tilbage. Hold det kort og struktureret.","interrupt_time":"Jeg stopper dig lige her. I en rigtig samtale har jeg brug for et skarpere svar: pointe, eksempel og resultat.","too_short":"Det er for kort. Giv et konkret eksempel: hvad skete der, hvad gjorde du, og hvad ændrede sig?","too_long":"Jeg stopper dig her — hovedpointen forsvinder. Giv svaret på 45 sekunder med ét klart resultat.","missing_impact":"Interessant, men jeg mangler effekten. Hvad var det målbare resultat?","followups":["Giv et konkret eksempel, der viser, at du kan lykkes i rollen {role}.","Hvad var det målbare resultat af dit arbejde?","Hvordan ville tidligere kolleger beskrive din arbejdsstil?","Hvorfor passer din profil til {company}?","Hvilken svaghed kan få en recruiter til at tvivle, og hvordan håndterer du den?"]},
    "Norwegian": {"intro":"La oss begynne. Presenter deg kort basert på CV-en din og knytt bakgrunnen din til denne rollen.","timer_left":"⏱ {seconds}s igjen. Hold det kort og strukturert.","interrupt_time":"Jeg stopper deg der. I et ekte intervju trenger jeg et tydeligere svar: poeng, eksempel og resultat.","too_short":"Det er for kort. Gi et konkret eksempel: hva skjedde, hva gjorde du, og hva endret seg?","too_long":"Jeg stopper deg der — hovedpoenget forsvinner. Svar på 45 sekunder med ett tydelig resultat.","missing_impact":"Interessant, men jeg mangler effekten. Hva var det målbare resultatet?","followups":["Gi et konkret eksempel som viser at du kan lykkes i rollen {role}.","Hva var det målbare resultatet av arbeidet ditt?","Hvordan ville tidligere kolleger beskrevet arbeidsstilen din?","Hvorfor passer profilen din til {company}?","Hvilken svakhet kan få en rekrutterer til å tvile, og hvordan håndterer du den?"]},
    "Finnish": {"intro":"Aloitetaan. Esittele itsesi lyhyesti CV:si perusteella ja yhdistä taustasi tähän rooliin.","timer_left":"⏱ {seconds}s jäljellä. Vastaa lyhyesti ja jäsennellysti.","interrupt_time":"Keskeytän tähän. Oikeassa haastattelussa tarvitsen selkeämmän vastauksen: pääkohta, esimerkki ja tulos.","too_short":"Tämä on liian lyhyt. Anna konkreettinen esimerkki: mitä tapahtui, mitä teit ja mikä muuttui?","too_long":"Keskeytän — pääasia katoaa. Vastaa 45 sekunnissa yhdellä selkeällä tuloksella.","missing_impact":"Kiinnostavaa, mutta vaikutus puuttuu. Mikä oli mitattava tulos?","followups":["Anna konkreettinen esimerkki, joka osoittaa, että voit onnistua roolissa {role}.","Mikä oli työsi mitattava tulos?","Miten aiemmat kollegasi kuvailisivat työskentelytyyliäsi?","Miksi profiilisi sopii yritykseen {company}?","Mikä heikkous voi herättää rekrytoijan epäilyksen ja miten käsittelet sen?"]},
    "Czech": {"intro":"Začněme. Stručně se představte podle svého CV a propojte své zkušenosti s touto rolí.","timer_left":"⏱ Zbývá {seconds}s. Odpovězte stručně a strukturovaně.","interrupt_time":"Tady vás zastavím. V reálném pohovoru potřebuji jasnější odpověď: bod, příklad a výsledek.","too_short":"To je příliš krátké. Dejte konkrétní příklad: co se stalo, co jste udělal(a) a co se změnilo?","too_long":"Zastavím vás — hlavní pointa se ztrácí. Odpovězte do 45 sekund s jedním jasným výsledkem.","missing_impact":"Zajímavé, ale chybí mi dopad. Jaký byl měřitelný výsledek?","followups":["Uveďte konkrétní příklad, který dokazuje, že uspějete v roli {role}.","Jaký byl měřitelný výsledek vaší práce?","Jak by bývalí kolegové popsali váš pracovní styl?","Proč se váš profil hodí pro {company}?","Jaká slabina by mohla vyvolat pochybnosti a jak ji zvládnete?"]},
    "Greek": {"intro":"Ας ξεκινήσουμε. Παρουσιάστε σύντομα τον εαυτό σας με βάση το CV σας και συνδέστε την εμπειρία σας με αυτόν τον ρόλο.","timer_left":"⏱ Απομένουν {seconds}s. Απαντήστε σύντομα και δομημένα.","interrupt_time":"Θα σας σταματήσω εδώ. Σε μια πραγματική συνέντευξη χρειάζομαι πιο καθαρή απάντηση: σημείο, παράδειγμα και αποτέλεσμα.","too_short":"Αυτό είναι πολύ σύντομο. Δώστε ένα συγκεκριμένο παράδειγμα: τι έγινε, τι κάνατε και τι άλλαξε;","too_long":"Σας σταματώ — χάνεται το βασικό σημείο. Απαντήστε σε 45 δευτερόλεπτα με ένα σαφές αποτέλεσμα.","missing_impact":"Ενδιαφέρον, αλλά λείπει ο αντίκτυπος. Ποιο ήταν το μετρήσιμο αποτέλεσμα;","followups":["Δώστε ένα συγκεκριμένο παράδειγμα που δείχνει ότι μπορείτε να πετύχετε στον ρόλο {role}.","Ποιο ήταν το μετρήσιμο αποτέλεσμα της δουλειάς σας;","Πώς θα περιέγραφαν οι προηγούμενοι συνάδελφοι το στυλ εργασίας σας;","Γιατί το προφίλ σας ταιριάζει στην {company};","Ποια αδυναμία μπορεί να δημιουργήσει αμφιβολία και πώς θα τη διαχειριστείτε;"]},
    "Japanese": {"intro":"始めましょう。履歴書をもとに簡潔に自己紹介し、この職種との関連を説明してください。","timer_left":"⏱ 残り{seconds}秒です。簡潔で構造的に答えてください。","interrupt_time":"ここで止めます。実際の面接では、要点、具体例、結果がより明確な回答が必要です。","too_short":"少し短すぎます。何が起きたか、何をしたか、何が変わったかを具体例で教えてください。","too_long":"ここで止めます。要点が見えにくくなっています。45秒で明確な結果を含めて答えてください。","missing_impact":"興味深いですが、成果が見えません。測定可能な結果は何でしたか？","followups":["{role}で成功できることを示す具体例を一つ教えてください。","あなたの仕事の測定可能な成果は何でしたか？","以前の同僚はあなたの働き方をどう説明しますか？","あなたのプロフィールはなぜ{company}に合っていますか？","採用担当者が不安に思う弱点は何で、どう対応しますか？"]},
    "Korean": {"intro":"시작하겠습니다. 이력서를 바탕으로 짧게 자기소개하고 이 직무와 어떻게 연결되는지 설명해 주세요.","timer_left":"⏱ {seconds}초 남았습니다. 간결하고 구조적으로 답변해 주세요.","interrupt_time":"여기서 잠시 끊겠습니다. 실제 면접에서는 핵심, 예시, 결과가 더 명확한 답변이 필요합니다.","too_short":"너무 짧습니다. 실제 예시를 들어 주세요: 어떤 상황이었고, 무엇을 했고, 무엇이 달라졌나요?","too_long":"여기서 멈추겠습니다 — 핵심이 흐려지고 있습니다. 명확한 결과를 포함해 45초 안에 답변해 주세요.","missing_impact":"흥미롭지만 영향이 부족합니다. 측정 가능한 결과는 무엇이었나요?","followups":["{role} 역할에 적합하다는 것을 보여주는 구체적인 예를 하나 말해 주세요.","업무의 측정 가능한 결과는 무엇이었나요?","이전 동료들은 당신의 업무 스타일을 어떻게 설명할까요?","당신의 프로필이 왜 {company}에 적합한가요?","채용 담당자가 의심할 수 있는 약점은 무엇이며 어떻게 대응하겠습니까?"]},
    "Chinese": {"intro":"我们开始吧。请根据你的简历做一个简短自我介绍，并说明它如何匹配这个岗位。","timer_left":"⏱ 还剩 {seconds} 秒。请简洁、有结构地回答。","interrupt_time":"我先打断一下。真实面试中，我需要更清晰的回答：重点、例子和结果。","too_short":"这个回答太短了。请给一个真实例子：发生了什么，你做了什么，结果有什么变化？","too_long":"我先打断一下——你的重点有点散。请用45秒给出一个带明确结果的回答。","missing_impact":"有意思，但我还没听到影响。可衡量的结果是什么？","followups":["请给一个具体例子，证明你能胜任 {role}。","你的工作产生了什么可衡量的结果？","以前的同事会如何描述你的工作方式？","为什么你的背景适合 {company}？","哪个弱点可能让招聘者犹豫，你会如何处理？"]},
})


def _wz201_normalize_language(language):
    raw = _wz200_clean_text(language, "English") if callable(globals().get("_wz200_clean_text")) else str(language or "English").strip()
    low = raw.lower().strip()
    return _WZ201_LANG_ALIASES.get(low) or (raw if raw in _WZ201_SUPPORTED_LANGUAGES else "English")


def _wz151_lang_code(language: str) -> str:
    # Override older helper but keep same function name used by earlier code.
    return _wz201_normalize_language(language).lower()


def _wz151_phrase(key: str, language: str = "English", **kwargs) -> str:
    lang = _wz201_normalize_language(language)
    pack = _WZ201_TRANSLATIONS.get(lang) or _WZ201_TRANSLATIONS["English"]
    template = pack.get(key) or _WZ201_TRANSLATIONS["English"].get(key, "")
    try:
        return template.format(**kwargs)
    except Exception:
        return template


def _wz151_question_fallbacks(cv_text: str, jd: str, role: str, language: str) -> list:
    role_text = str(role or st.session_state.get("target_role", "this role") or "this role")
    company_text = str(st.session_state.get("wz_ri_company") or st.session_state.get("target_company") or "the company")
    lang = _wz201_normalize_language(language)
    pack = _WZ201_TRANSLATIONS.get(lang) or _WZ201_TRANSLATIONS["English"]
    qs = pack.get("followups") or _WZ201_TRANSLATIONS["English"]["followups"]
    return [q.format(role=role_text, company=company_text) for q in qs]


def _wz200_latest_language():
    """Read the newest interview language from every known dashboard/interview key, for every supported language."""
    candidates = [
        st.session_state.get("interview_language"),
        st.session_state.get("selected_interview_language"),
        st.session_state.get("wz_interview_language"),
        st.session_state.get("wz_ri_interview_language"),
        st.session_state.get("wz_ri_language_choice_v150"),
        st.session_state.get("preferred_language"),
        st.session_state.get("language"),
        st.session_state.get("response_language"),
    ]
    for lang in candidates:
        raw = _wz200_clean_text(lang, "") if callable(globals().get("_wz200_clean_text")) else str(lang or "").strip()
        if raw and raw.lower() not in ["auto", "auto-detect", "auto-detect / user preference", "same as interview", "user preference"]:
            return _wz201_normalize_language(raw)
    return "English"


def _wz200_opening_question(language, recruiter, role, company, candidate=""):
    role = _wz200_clean_text(role, "this role") if callable(globals().get("_wz200_clean_text")) else str(role or "this role")
    company = _wz200_clean_text(company, "the company") if callable(globals().get("_wz200_clean_text")) else str(company or "the company")
    candidate = _wz200_clean_text(candidate, "") if callable(globals().get("_wz200_clean_text")) else str(candidate or "")
    intro = _wz151_phrase("intro", language)
    if candidate:
        intro = intro.replace("Let’s begin.", f"Hi {candidate}, let’s begin.")
    return intro.replace("this job", f"{role} at {company}").replace("this role", f"{role} at {company}")


def _wz200_fallback_question(language, index, role, company):
    qs = _wz151_question_fallbacks("", "", role, language)
    try:
        return qs[(max(1, int(index)) - 1) % len(qs)]
    except Exception:
        return qs[0]


def _wz201_voice_js_lang(language):
    return _WZ201_SPEECH_LANG_CODES.get(_wz201_normalize_language(language), "en-US")

# Patch browser speech, if present, to prefer the selected interview language instead of always English.
try:
    _wz201_prev_browser_speak = globals().get("_wz_voice_first_browser_speak")
    def _wz_voice_first_browser_speak(text, key=None, auto=True, language=None, recruiter=None):
        language = _wz201_normalize_language(language or st.session_state.get("wz_ri_interview_language") or st.session_state.get("preferred_language") or "English")
        lang_code = _wz201_voice_js_lang(language)
        safe_text = html.escape(str(text or ""))
        safe_key = html.escape(str(key or "wz_voice"))
        auto_flag = "true" if auto else "false"
        gender = str(st.session_state.get("wz_voice_recruiter_gender") or "").lower()
        gender_hint = "male" if gender == "male" else "female"
        st.components.v1.html(f"""
        <div id="{safe_key}" style="display:none"></div>
        <script>
        (function() {{
          const text = `{safe_text}`;
          const lang = `{lang_code}`;
          const genderHint = `{gender_hint}`;
          const autoplay = {auto_flag};
          function pickVoice() {{
            const voices = window.speechSynthesis ? (window.speechSynthesis.getVoices() || []) : [];
            let sameLang = voices.filter(v => (v.lang || '').toLowerCase().startsWith(lang.toLowerCase().slice(0,2)));
            if (!sameLang.length) sameLang = voices;
            const natural = sameLang.find(v => /natural|premium|enhanced|neural|google|microsoft|samantha|daniel|mark|zira|helena|anna|paulina|amelie|thomas|luciana|carlos|lekha|veena|ting/i.test(v.name || ''));
            return natural || sameLang[0] || voices[0] || null;
          }}
          function speak() {{
            if (!window.speechSynthesis) return;
            window.speechSynthesis.cancel();
            const msg = new SpeechSynthesisUtterance(text);
            msg.lang = lang;
            msg.rate = genderHint === 'male' ? 0.90 : 0.94;
            msg.pitch = genderHint === 'male' ? 0.86 : 1.05;
            const voice = pickVoice();
            if (voice) msg.voice = voice;
            setTimeout(() => window.speechSynthesis.speak(msg), 160);
          }}
          window.workzoSpeakRecruiter = speak;
          if (autoplay) {{
             if (speechSynthesis.onvoiceschanged !== undefined) speechSynthesis.onvoiceschanged = speak;
             speak();
          }}
        }})();
        </script>
        """, height=0)
except Exception:
    pass

# Re-apply selection lock so old and new modules read the selected language consistently.
try:
    _wz201_prev_apply_selection_lock = globals().get("_wz200_apply_selection_lock")
    def _wz200_apply_selection_lock(reset_stale_questions=True):
        try:
            language = _wz200_latest_language()
            recruiter = _wz200_latest_recruiter() if callable(globals().get("_wz200_latest_recruiter")) else "👩 Sarah — Friendly HR"
            personality = _wz200_map_recruiter_to_personality(recruiter) if callable(globals().get("_wz200_map_recruiter_to_personality")) else "Friendly"
            display = _wz200_recruiter_display_name(recruiter) if callable(globals().get("_wz200_recruiter_display_name")) else str(recruiter)
            for key in ["wz_ri_interview_language", "preferred_language", "language", "response_language", "ui_language", "interview_language", "selected_interview_language"]:
                st.session_state[key] = language
            st.session_state["wz_ri_answer_language"] = "Same as interview"
            st.session_state["wz_ri_answer_language_v150"] = "Same as interview"
            st.session_state["wz_ri_language_choice_v150"] = language
            st.session_state["wz_speech_lang_code"] = _wz201_voice_js_lang(language)
            st.session_state["wz_ri_recruiter_personality_v181"] = display
            st.session_state["wz_ri_recruiter_personality"] = display
            st.session_state["wz_voice_recruiter_name"] = display
            st.session_state["wz_voice_recruiter_gender"] = _wz200_voice_gender(display) if callable(globals().get("_wz200_voice_gender")) else "female"
            st.session_state["wz_ri_personality"] = personality
            role = _wz200_clean_text(st.session_state.get("wz_ri_role") or st.session_state.get("target_role") or st.session_state.get("target_job_title"), "the role")
            company = _wz200_clean_text(st.session_state.get("wz_ri_company") or st.session_state.get("target_company"), "the company")
            st.session_state["wz_ri_role"] = role
            st.session_state["target_role"] = role
            st.session_state["target_job_title"] = role
            st.session_state["wz_ri_company"] = company
            st.session_state["target_company"] = company
            lock = {"language": language, "recruiter": display, "personality": personality, "role": role, "company": company}
            changed = st.session_state.get("wz_ri_selection_lock") != lock
            st.session_state["wz_ri_selection_lock"] = lock
            if reset_stale_questions and changed and (st.session_state.get("wz_ri_started") or isinstance(st.session_state.get("wz_ri_questions"), list)):
                candidate = st.session_state.get("candidate_name") or st.session_state.get("user_name") or ""
                qs = [_wz200_opening_question(language, display, role, company, candidate)]
                for i in range(1, 6):
                    qs.append(_wz200_fallback_question(language, i, role, company))
                st.session_state["wz_ri_questions"] = qs
                st.session_state["wz_ri_current_index"] = 0
                st.session_state["wz_ri_answers"] = []
                st.session_state["wz_ri_live_reactions"] = []
                st.session_state["wz_ri_final_score"] = {}
                st.session_state["wz_ri_closing_reached"] = False
                st.session_state["wz_ri_audio_nonce"] = int(st.session_state.get("wz_ri_audio_nonce", 0) or 0) + 1
            return lock
        except Exception:
            return {}
except Exception:
    pass

# =========================================================
# WorkZo FINAL PATCH - all-language interview + recruiter selection sync
# Reads dashboard selections from all known keys and prevents stale Sarah/English defaults.
# =========================================================
import json as _wz202_json
_WZ202_LANGUAGES = ["English","German","Dutch","French","Spanish","Portuguese","Italian","Arabic","Hindi","Tamil","Polish","Turkish","Swedish","Danish","Norwegian","Finnish","Czech","Greek","Japanese","Korean","Chinese"]
_WZ202_ALIAS = {"deutsch":"German","german":"German","english":"English","englisch":"English","dutch":"Dutch","nederlands":"Dutch","french":"French","français":"French","spanish":"Spanish","español":"Spanish","portuguese":"Portuguese","português":"Portuguese","italian":"Italian","arabic":"Arabic","hindi":"Hindi","tamil":"Tamil","polish":"Polish","turkish":"Turkish","swedish":"Swedish","danish":"Danish","norwegian":"Norwegian","finnish":"Finnish","czech":"Czech","greek":"Greek","japanese":"Japanese","korean":"Korean","chinese":"Chinese"}
_WZ202_SPEECH = {"English":"en-US","German":"de-DE","Dutch":"nl-NL","French":"fr-FR","Spanish":"es-ES","Portuguese":"pt-PT","Italian":"it-IT","Arabic":"ar-SA","Hindi":"hi-IN","Tamil":"ta-IN","Polish":"pl-PL","Turkish":"tr-TR","Swedish":"sv-SE","Danish":"da-DK","Norwegian":"nb-NO","Finnish":"fi-FI","Czech":"cs-CZ","Greek":"el-GR","Japanese":"ja-JP","Korean":"ko-KR","Chinese":"zh-CN"}

def _wz202_clean(v, fb=""):
    try:
        s=str(v or "").strip()
        return s if s else fb
    except Exception:
        return fb

def _wz202_lang(v):
    raw=_wz202_clean(v,"")
    if not raw or raw.lower() in {"auto","auto-detect","auto-detect / user preference","same as interview","user preference"}: return "English"
    if raw in _WZ202_LANGUAGES: return raw
    return _WZ202_ALIAS.get(raw.lower(), raw if raw in _WZ202_LANGUAGES else "English")

def _wz202_latest_lang():
    for k in ["interview_language","selected_interview_language","wz_interview_language","wz_ri_language_choice_v150","wz_ri_interview_language","preferred_language","response_language","language","ui_language"]:
        raw=_wz202_clean(st.session_state.get(k),"")
        if raw and raw.lower() not in {"auto","auto-detect","auto-detect / user preference","same as interview","user preference"}:
            return _wz202_lang(raw)
    return "English"

def _wz202_recruiter(v=None):
    if v is None:
        for k in ["wz_ri_recruiter_personality_v181","wz_ri_recruiter_personality","selected_recruiter_personality","wz_voice_recruiter_name","recruiter_personality","interviewer_personality"]:
            raw=_wz202_clean(st.session_state.get(k),"")
            if raw and raw.lower() not in {"strict","friendly","fast-paced","technical recruiter","senior hiring manager"}: v=raw; break
    txt=_wz202_clean(v,"Sarah — Friendly HR").replace("👩","").replace("👨","").strip()
    return txt or "Sarah — Friendly HR"

def _wz202_gender(recruiter):
    r=_wz202_recruiter(recruiter).lower()
    return "male" if any(x in r for x in ["daniel","markus","james","alex","hans","carlos","thomas","ahmed"]) else "female"

def _wz202_role_company():
    role=_wz202_clean(st.session_state.get("wz_ri_role") or st.session_state.get("wz183_target_role") or st.session_state.get("target_role") or st.session_state.get("target_job_title"), "the role")
    company=_wz202_clean(st.session_state.get("wz_ri_company") or st.session_state.get("wz183_target_company") or st.session_state.get("target_company"), "the company")
    return role, company

def _wz202_sync_selection(reset_if_changed=False):
    lang=_wz202_latest_lang(); rec=_wz202_recruiter(); role,company=_wz202_role_company()
    lock={"language":lang,"recruiter":rec,"role":role,"company":company}
    changed=st.session_state.get("wz_ri_selection_lock")!=lock
    for k in ["wz_ri_interview_language","interview_language","selected_interview_language","preferred_language","language","response_language","ui_language"]: st.session_state[k]=lang
    st.session_state["wz_ri_language_choice_v150"]=lang
    st.session_state["wz_speech_lang_code"]=_WZ202_SPEECH.get(lang,"en-US")
    for k in ["wz_ri_recruiter_personality_v181","wz_ri_recruiter_personality","selected_recruiter_personality","wz_voice_recruiter_name"]: st.session_state[k]=rec
    st.session_state["wz_voice_recruiter_gender"]=_wz202_gender(rec)
    st.session_state["wz_ri_personality"]="Technical recruiter" if "daniel" in rec.lower() else ("Fast-paced" if "priya" in rec.lower() else ("Strict" if "markus" in rec.lower() else "Friendly"))
    st.session_state["wz_ri_role"]=role; st.session_state["target_role"]=role; st.session_state["target_job_title"]=role
    st.session_state["wz_ri_company"]=company; st.session_state["target_company"]=company
    st.session_state["wz_ri_selection_lock"]=lock
    if reset_if_changed and changed:
        st.session_state["wz_ri_questions"]=[]; st.session_state["wz_ri_current_index"]=0; st.session_state["wz_ri_answers"]=[]; st.session_state["wz_ri_live_reactions"]=[]; st.session_state["wz_ri_final_score"]={}; st.session_state["wz_ri_audio_nonce"]=int(st.session_state.get("wz_ri_audio_nonce",0) or 0)+1
    return lock

def _wz202_opening(lang, role, company):
    d={
    "English":f"Tell me about yourself and keep it relevant to {role} at {company}.",
    "German":f"Erzählen Sie mir bitte kurz etwas über sich und verbinden Sie Ihren Hintergrund mit der Position {role} bei {company}.",
    "Dutch":f"Vertel kort iets over jezelf en koppel je achtergrond aan de functie {role} bij {company}.",
    "French":f"Présentez-vous brièvement et reliez votre parcours au poste de {role} chez {company}.",
    "Spanish":f"Preséntate brevemente y conecta tu experiencia con el puesto de {role} en {company}.",
    "Portuguese":f"Apresente-se brevemente e conecte sua experiência à vaga de {role} na {company}.",
    "Italian":f"Presentati brevemente e collega la tua esperienza al ruolo di {role} presso {company}.",
    "Hindi":f"कृपया अपना संक्षिप्त परिचय दीजिए और अपने अनुभव को {company} में {role} role से जोड़िए.",
    "Tamil":f"தயவு செய்து உங்களைச் சுருக்கமாக அறிமுகப்படுத்தி, உங்கள் அனுபவத்தை {company} நிறுவனத்தின் {role} பணியுடன் இணைக்கவும்.",
    "Arabic":f"قدّم نفسك باختصار واربط خبرتك بدور {role} في {company}.",
    "Japanese":f"簡潔に自己紹介し、あなたの経験を{company}の{role}職に結びつけて説明してください。",
    "Korean":f"간단히 자기소개를 하고, 본인의 경험을 {company}의 {role} 직무와 연결해서 설명해 주세요.",
    "Chinese":f"请简短介绍自己，并说明你的经历如何匹配 {company} 的 {role} 岗位。"}
    return d.get(lang,d["English"])

def _wz_voice_first_build_opening_question(cv_text, jd, role, company, language):
    _wz202_sync_selection(reset_if_changed=False)
    lang=_wz202_latest_lang(); role,company=_wz202_role_company()
    return _wz202_opening(lang, role, company)

def _wz_ri_build_questions(cv_text, jd, company, role, website="", company_context="", language="English", personality=""):
    _wz202_sync_selection(reset_if_changed=False)
    lang=_wz202_latest_lang(); role,company=_wz202_role_company()
    qs=[_wz202_opening(lang,role,company)]
    fallback=[f"Give me one specific example that proves you can succeed in {role}.","What measurable result did your work create?","Tell me about a challenge where you had to take ownership.",f"Why should {company} trust you for this role?","What weakness could make a recruiter hesitate, and how are you improving it?"]
    langmap={
        "German":[f"Nennen Sie mir ein konkretes Beispiel, das zeigt, dass Sie in der Position {role} erfolgreich sein können.","Welches messbare Ergebnis hat Ihre Arbeit erzielt?","Beschreiben Sie eine Herausforderung, bei der Sie Verantwortung übernommen haben.",f"Warum sollte {company} Ihnen diese Rolle zutrauen?","Welche Schwäche könnte einen Recruiter zweifeln lassen, und wie verbessern Sie sie?"],
        "French":[f"Donnez-moi un exemple concret prouvant votre adéquation pour le poste {role}.","Quel résultat mesurable avez-vous obtenu ?","Parlez-moi d’un défi où vous avez pris la responsabilité.",f"Pourquoi {company} devrait-elle vous faire confiance pour ce poste ?","Quel point faible pourrait inquiéter un recruteur et comment l’améliorez-vous ?"],
        "Spanish":[f"Dame un ejemplo concreto que demuestre que puedes tener éxito en {role}.","¿Qué resultado medible generó tu trabajo?","Cuéntame un desafío en el que asumiste responsabilidad.",f"¿Por qué {company} debería confiar en ti para este puesto?","¿Qué debilidad podría preocupar a un reclutador y cómo la estás mejorando?"],
        "Dutch":[f"Geef een concreet voorbeeld dat laat zien dat je succesvol kunt zijn in {role}.","Welk meetbaar resultaat heeft je werk opgeleverd?","Vertel over een uitdaging waarbij je verantwoordelijkheid nam.",f"Waarom zou {company} jou deze rol toevertrouwen?","Welke zwakte kan een recruiter laten twijfelen en hoe verbeter je die?"]}
    qs.extend(langmap.get(lang,fallback))
    return qs[:6]

def _wz_voice_first_browser_speak(text, key=None, auto=True, language=None, recruiter=None):
    lang=_wz202_lang(language or _wz202_latest_lang()); rec=_wz202_recruiter(recruiter); code=_WZ202_SPEECH.get(lang,"en-US")
    safe_text=_wz202_json.dumps(str(text or "")); safe_key=str(key or "wz_voice")
    gender=_wz202_gender(rec); auto_js="true" if auto else "false"
    st.components.v1.html(f"""
    <div id="{safe_key}" style="display:none"></div>
    <script>
    (function(){{
      const text = {safe_text}; const lang = "{code}"; const gender = "{gender}"; const auto = {auto_js};
      function pickVoice(){{
        const voices = window.speechSynthesis ? (window.speechSynthesis.getVoices() || []) : [];
        let list = voices.filter(v => (v.lang || '').toLowerCase().startsWith(lang.toLowerCase().slice(0,2)));
        if(!list.length) list = voices;
        if(gender === 'male'){{ const male = list.find(v => /daniel|mark|george|guy|david|alex|thomas|male|google uk english male/i.test(v.name||'')); if(male) return male; }}
        else {{ const female = list.find(v => /samantha|zira|susan|anna|helena|female|google uk english female|lekha|veena/i.test(v.name||'')); if(female) return female; }}
        return list[0] || voices[0] || null;
      }}
      function speak(){{
        if(!window.speechSynthesis || !text) return;
        window.speechSynthesis.cancel();
        const msg = new SpeechSynthesisUtterance(text);
        msg.lang = lang; msg.rate = gender === 'male' ? 0.90 : 0.94; msg.pitch = gender === 'male' ? 0.86 : 1.04;
        const v = pickVoice(); if(v) msg.voice = v;
        setTimeout(() => window.speechSynthesis.speak(msg), 180);
      }}
      window.workzoSpeakRecruiter = speak;
      if(auto){{ if(speechSynthesis.onvoiceschanged !== undefined) speechSynthesis.onvoiceschanged = speak; speak(); }}
    }})();
    </script>
    """, height=0)

try:
    _wz202_prev_render_real_interview_simulation = render_real_interview_simulation
    def render_real_interview_simulation():
        lock=_wz202_sync_selection(reset_if_changed=False)
        qlock=st.session_state.get("wz_ri_questions_lock")
        if st.session_state.get("wz_ri_started") and qlock and qlock != lock:
            st.session_state["wz_ri_questions"]=[]
            st.session_state["wz_ri_current_index"]=0
            st.session_state["wz_ri_answers"]=[]
            st.session_state["wz_ri_final_score"]={}
        return _wz202_prev_render_real_interview_simulation()
except Exception:
    pass
