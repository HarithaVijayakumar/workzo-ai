"""WorkZo AI - core AI helpers and stable resume dashboard analysis.

Replace your existing workzo_modules/04_ai_core_analysis.py with this file.
It provides:
- run_ai_prompt(...)
- safe_json_loads(...)
- analyze_resume_dashboard_stable(...)

Designed for your modular loader where other modules call these functions globally.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional

import streamlit as st
from openai import OpenAI


# -----------------------------------------------------------------------------
# OpenAI client
# -----------------------------------------------------------------------------

def _get_openai_api_key() -> Optional[str]:
    """Read API key safely from Streamlit secrets first, then environment."""
    try:
        if hasattr(st, "secrets") and "OPENAI_API_KEY" in st.secrets:
            return st.secrets.get("OPENAI_API_KEY")
    except Exception:
        pass

    return os.getenv("OPENAI_API_KEY")


OPENAI_API_KEY = _get_openai_api_key()
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


# -----------------------------------------------------------------------------
# Safe JSON helpers
# -----------------------------------------------------------------------------

def safe_json_loads(raw: Any) -> Dict[str, Any]:
    """Safely parse JSON returned by AI responses.

    Handles markdown code fences and tries to extract the first JSON object if
    the model adds extra text.
    """
    if not raw:
        return {}

    if isinstance(raw, dict):
        return raw

    raw_text = str(raw).strip()

    if raw_text.startswith("```"):
        raw_text = re.sub(r"^```(?:json)?", "", raw_text, flags=re.IGNORECASE).strip()
        raw_text = re.sub(r"```$", "", raw_text).strip()

    try:
        parsed = json.loads(raw_text)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        pass

    # Fallback: extract first {...} block.
    match = re.search(r"\{.*\}", raw_text, flags=re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group(0))
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}

    return {}


def _as_list(value: Any) -> List[str]:
    """Normalize model output to a clean list of strings."""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        lines = [line.strip(" -•\t") for line in value.splitlines()]
        return [line for line in lines if line]
    return [str(value).strip()] if str(value).strip() else []


def _safe_int(value: Any, default: int = 0, min_value: int = 0, max_value: int = 100) -> int:
    """Convert scores safely and clamp to 0-100."""
    try:
        if isinstance(value, str):
            found = re.search(r"\d+", value)
            value = found.group(0) if found else default
        number = int(round(float(value)))
    except Exception:
        number = default
    return max(min_value, min(max_value, number))


# -----------------------------------------------------------------------------
# AI prompt wrapper
# -----------------------------------------------------------------------------

def run_ai_prompt(
    prompt: str,
    system_addition: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: int = 2000,
    model: str = "gpt-4o-mini",
    force_json: bool = False,
    **kwargs: Any,
) -> str:
    """Central AI function used across WorkZo.

    Accepts extra keyword arguments with **kwargs so older/newer modules do not
    crash when they pass options such as system_addition, force_json, etc.
    """
    if client is None:
        return "AI Error: OPENAI_API_KEY not found. Add it to .env locally or Streamlit secrets in cloud."

    try:
        messages = []

        base_system = (
            "You are WorkZo AI, a careful career assistant. "
            "Be accurate, practical, and do not invent candidate details."
        )

        if system_addition:
            base_system += "\n\n" + str(system_addition)

        messages.append({"role": "system", "content": base_system})
        messages.append({"role": "user", "content": str(prompt)})

        request: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if force_json:
            request["response_format"] = {"type": "json_object"}

        response = client.chat.completions.create(**request)
        return response.choices[0].message.content or ""

    except Exception as e:
        return f"AI Error: {e}"


# -----------------------------------------------------------------------------
# Stable dashboard resume analyzer
# -----------------------------------------------------------------------------

def _basic_resume_fallback(cv_text: str) -> Dict[str, Any]:
    """Rule-based fallback when AI is unavailable or JSON parsing fails."""
    text = cv_text or ""
    lower = text.lower()
    word_count = len(text.split())

    has_email = bool(re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text))
    has_phone = bool(re.search(r"(?:\+?\d[\d\s().-]{7,}\d)", text))
    has_tools = any(tool in lower for tool in ["python", "sql", "tableau", "excel", "power bi", "pandas", "cloud", "api"])
    has_experience = any(word in lower for word in ["experience", "work experience", "technical support", "customer", "project"])
    has_education = any(word in lower for word in ["education", "bootcamp", "degree", "university", "school"])
    has_numbers = bool(re.search(r"\d+\s*(%|years?|months?|clients?|tickets?|users?|projects?)", lower))

    resume_score = 45
    resume_score += 10 if has_email else 0
    resume_score += 8 if has_phone else 0
    resume_score += 12 if has_tools else 0
    resume_score += 12 if has_experience else 0
    resume_score += 8 if has_education else 0
    resume_score += 10 if has_numbers else 0
    resume_score += 8 if word_count >= 250 else 0
    resume_score = _safe_int(resume_score, default=60)

    ats_score = resume_score - 5
    if not has_numbers:
        ats_score -= 8
    if word_count < 180:
        ats_score -= 8
    ats_score = _safe_int(ats_score, default=55)

    return {
        "resume_score": resume_score,
        "ats_score": ats_score,
        "summary": "Basic resume analysis loaded. AI analysis was unavailable, so WorkZo used a safe rule-based review.",
        "strengths": [
            item for item, ok in [
                ("Contact details are present.", has_email or has_phone),
                ("Relevant tools or technical keywords are visible.", has_tools),
                ("Experience or project background is included.", has_experience),
                ("Education or training information is included.", has_education),
            ] if ok
        ] or ["CV text was uploaded successfully."],
        "improvements": [
            item for item, missing in [
                ("Add measurable achievements with numbers, outcomes, or impact.", not has_numbers),
                ("Add more role-specific tools and keywords from the target job description.", not has_tools),
                ("Make the experience section clearer with job title, company, dates, and bullet points.", not has_experience),
                ("Add or improve the education/training section.", not has_education),
            ] if missing
        ] or ["Tailor the CV to each job description before applying."],
        "target_roles": [
            "Data Analyst",
            "Technical Support Specialist",
            "Customer Success Associate",
        ],
        "keyword_gaps": [
            "Job-specific tools",
            "Measurable impact",
            "Role keywords from JD",
        ],
        "next_steps": [
            "Paste the target job description before tailoring the CV.",
            "Rewrite 3-5 bullets with numbers and outcomes.",
            "Keep one master CV and create small tailored versions per job.",
        ],
    }


def analyze_resume_dashboard_stable(cv_text: str, force_refresh: bool = False) -> Dict[str, Any]:
    """Create stable resume/dashboard analysis and save it to st.session_state.

    This function is called from onboarding. It must never crash the app.
    """
    try:
        cv_text = cv_text or ""
        if not cv_text.strip() or len(cv_text.strip()) < 50:
            result = {
                "resume_score": 0,
                "ats_score": 0,
                "summary": "Please upload a complete CV to analyse your resume.",
                "strengths": [],
                "improvements": ["Upload a readable CV with contact, experience, skills, and education details."],
                "target_roles": [],
                "keyword_gaps": [],
                "next_steps": ["Upload or paste your CV text."],
            }
            st.session_state.resume_analysis = result
            st.session_state.dashboard_resume_analysis = result
            return result

        if not force_refresh and st.session_state.get("resume_analysis"):
            existing = st.session_state.resume_analysis
            if isinstance(existing, dict) and existing.get("summary"):
                return existing

        country = st.session_state.get("country") or st.session_state.get("migration_country") or "the selected country"
        preferred_language = st.session_state.get("preferred_language") or st.session_state.get("language") or "English"

        prompt = f"""
Analyze this CV for a career dashboard.

Target country: {country}
Preferred response language: {preferred_language}

Return ONLY valid JSON with this exact structure:
{{
  "resume_score": 0,
  "ats_score": 0,
  "summary": "short honest summary",
  "strengths": ["..."],
  "improvements": ["..."],
  "target_roles": ["..."],
  "keyword_gaps": ["..."],
  "next_steps": ["..."]
}}

Scoring rules:
- Be realistic. Do not give 90+ unless the CV is truly strong.
- Resume score = clarity, structure, achievements, relevance.
- ATS score = keyword match potential, standard formatting, measurable bullets.
- Do not invent experience, employers, dates, degrees, or certifications.
- Keep suggestions practical for job seekers.

CV text:
{cv_text[:12000]}
"""

        raw = run_ai_prompt(
            prompt,
            system_addition="Return strict JSON only. No markdown. No extra explanation.",
            temperature=0.2,
            max_tokens=1600,
            force_json=True,
        )

        parsed = safe_json_loads(raw)
        if not parsed or str(raw).startswith("AI Error:"):
            parsed = _basic_resume_fallback(cv_text)

        result = {
            "resume_score": _safe_int(parsed.get("resume_score"), default=60),
            "ats_score": _safe_int(parsed.get("ats_score"), default=55),
            "summary": str(parsed.get("summary") or "Resume analysis completed.").strip(),
            "strengths": _as_list(parsed.get("strengths"))[:6],
            "improvements": _as_list(parsed.get("improvements"))[:6],
            "target_roles": _as_list(parsed.get("target_roles"))[:5],
            "keyword_gaps": _as_list(parsed.get("keyword_gaps"))[:8],
            "next_steps": _as_list(parsed.get("next_steps"))[:5],
        }

        # Backward-compatible aliases for different dashboard versions.
        st.session_state.resume_analysis = result
        st.session_state.dashboard_resume_analysis = result
        st.session_state.resume_score = result["resume_score"]
        st.session_state.ats_score = result["ats_score"]
        st.session_state.best_match_roles = result["target_roles"]

        return result

    except Exception as e:
        result = _basic_resume_fallback(cv_text or "")
        result["summary"] = f"Resume analysis fallback loaded because of an internal error: {e}"
        st.session_state.resume_analysis = result
        st.session_state.dashboard_resume_analysis = result
        return result
