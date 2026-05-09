# =========================================================
# 🌍 WorkZo Global Career Rules Engine
# Country + language rules used by CV, Jobs, Interview, and Cover Letter.
# Safe to exec-load in WorkZo's modular loader.
# =========================================================
from __future__ import annotations
from typing import Dict, Any, List


def _wz_rules_norm_country(country: str) -> str:
    c = (country or "").strip()
    aliases = {
        "united states": "USA", "us": "USA", "u.s.": "USA", "u.s.a.": "USA", "america": "USA",
        "united kingdom": "UK", "great britain": "UK", "england": "UK",
        "deutschland": "Germany", "uae": "UAE", "united arab emirates": "UAE",
        "the netherlands": "Netherlands", "holland": "Netherlands",
    }
    return aliases.get(c.lower(), c)


COUNTRY_CAREER_RULES: Dict[str, Dict[str, Any]] = {
    "Germany": {
        "cv_style": "structured, formal CV with clear sections, precise dates, role-relevant proof, and clear language levels",
        "avoid": ["overly casual tone", "unstructured resume format", "invented language levels", "unsupported claims"],
        "interview_style": "precise, structured, evidence-based answers with clear examples and practical proof",
        "job_keywords": ["Junior", "Trainee", "Werkstudent", "Praktikum", "Quereinsteiger"],
        "cover_letter_tone": "formal, structured, role-specific, and concise",
        "job_search_note": "include German-market keywords such as Werkstudent/Trainee when relevant",
        "preferred_cv_template": "German ATS Resume",
        "job_platforms": ["LinkedIn", "StepStone", "Indeed", "Xing", "Arbeitsagentur"],
    },
    "Austria": {
        "cv_style": "DACH-style structured CV with formal tone, clear sections, and language-level clarity",
        "avoid": ["casual tone", "unsupported claims", "unclear dates"],
        "interview_style": "structured, precise, and evidence-based",
        "job_keywords": ["Junior", "Trainee", "Praktikum", "Berufseinsteiger"],
        "cover_letter_tone": "formal and concise",
        "job_search_note": "use DACH-market terminology when relevant",
        "preferred_cv_template": "German-Style Lebenslauf",
        "job_platforms": ["LinkedIn", "StepStone", "Indeed"],
    },
    "Switzerland": {
        "cv_style": "structured Swiss/DACH-style CV with precision, clear qualifications, and language-level clarity",
        "avoid": ["casual tone", "vague language ability", "unsupported claims"],
        "interview_style": "precise, professional, and evidence-based",
        "job_keywords": ["Junior", "Trainee", "Praktikum", "Berufseinsteiger"],
        "cover_letter_tone": "formal and precise",
        "job_search_note": "include language and location expectations clearly",
        "preferred_cv_template": "German-Style Lebenslauf",
        "job_platforms": ["LinkedIn", "Jobs.ch", "Indeed"],
    },
    "USA": {
        "cv_style": "achievement-focused resume with measurable impact, strong action verbs, and no personal demographic details",
        "avoid": ["photo", "age", "date of birth", "marital status", "overly long paragraphs"],
        "interview_style": "confident storytelling with measurable impact and STAR-style examples",
        "job_keywords": ["Entry Level", "Associate", "Junior", "New Grad"],
        "cover_letter_tone": "concise, confident, and impact-focused",
        "job_search_note": "use entry-level/associate/new-grad keywords where relevant",
        "preferred_cv_template": "ATS Resume",
        "job_platforms": ["LinkedIn", "Indeed", "Glassdoor", "Wellfound"],
    },
    "Canada": {
        "cv_style": "achievement-focused Canadian resume, concise and ATS-friendly, without personal demographic details",
        "avoid": ["photo", "age", "date of birth", "marital status", "unsupported claims"],
        "interview_style": "clear STAR examples, measurable impact, and collaborative communication",
        "job_keywords": ["Entry Level", "Associate", "Junior", "New Grad"],
        "cover_letter_tone": "professional, concise, and role-focused",
        "job_search_note": "use Canadian-style ATS keywords and location/remote clarity",
        "preferred_cv_template": "ATS Resume",
        "job_platforms": ["LinkedIn", "Indeed", "Job Bank"],
    },
    "UK": {
        "cv_style": "concise CV with strong skills, achievements, and role-specific evidence",
        "avoid": ["too long CV", "generic profile", "unsupported claims"],
        "interview_style": "clear, competency-based answers with practical examples",
        "job_keywords": ["Graduate", "Junior", "Entry Level", "Trainee"],
        "cover_letter_tone": "professional, concise, and direct",
        "job_search_note": "include graduate/junior/trainee keywords when relevant",
        "preferred_cv_template": "Modern Professional",
        "job_platforms": ["LinkedIn", "Indeed", "Reed", "Totaljobs"],
    },
    "Ireland": {
        "cv_style": "concise CV with practical achievements, skills, and clear role fit",
        "avoid": ["too long CV", "generic claims", "unsupported metrics"],
        "interview_style": "competency-based and practical",
        "job_keywords": ["Graduate", "Junior", "Entry Level"],
        "cover_letter_tone": "professional and concise",
        "job_search_note": "use graduate/junior language where relevant",
        "preferred_cv_template": "Modern Professional",
        "job_platforms": ["LinkedIn", "Indeed", "IrishJobs"],
    },
    "Netherlands": {
        "cv_style": "direct, practical, role-fit focused CV with clear skills and outcomes",
        "avoid": ["overly formal language", "vague motivation", "long paragraphs"],
        "interview_style": "direct, practical, and honest answers with clear role fit",
        "job_keywords": ["Junior", "Starter", "Traineeship", "Internship"],
        "cover_letter_tone": "direct, practical, and role-focused",
        "job_search_note": "use starter/traineeship keywords for early-career roles",
        "preferred_cv_template": "Dutch / EU Modern",
        "job_platforms": ["LinkedIn", "Indeed", "Nationale Vacaturebank", "Werk.nl"],
    },
    "India": {
        "cv_style": "ATS-friendly CV emphasizing skills, projects, certifications, tools, and relevant achievements",
        "avoid": ["missing technical skills", "generic project descriptions", "unsupported claims"],
        "interview_style": "technical + HR mixed style with project depth, fundamentals, and communication clarity",
        "job_keywords": ["Fresher", "Entry Level", "Graduate", "Junior"],
        "cover_letter_tone": "skills-focused, role-specific, and practical",
        "job_search_note": "include fresher/entry-level and project/skills keywords when relevant",
        "preferred_cv_template": "ATS Resume",
        "job_platforms": ["LinkedIn", "Naukri", "Indeed", "Internshala"],
    },
    "UAE": {
        "cv_style": "international CV with clear experience, skills, location flexibility, and work authorization/visa clarity when relevant",
        "avoid": ["unclear visa/work status", "vague relocation availability", "unsupported claims"],
        "interview_style": "professional, business-oriented, and internationally framed",
        "job_keywords": ["Junior", "Associate", "Entry Level"],
        "cover_letter_tone": "formal, professional, and business-focused",
        "job_search_note": "make location and work authorization context clear where appropriate",
        "preferred_cv_template": "Modern Professional",
        "job_platforms": ["LinkedIn", "GulfTalent", "Bayt", "Indeed"],
    },
    "Singapore": {
        "cv_style": "clean international resume with clear skills, impact, and business relevance",
        "avoid": ["too verbose content", "vague achievements", "unsupported claims"],
        "interview_style": "structured, practical, and business-focused",
        "job_keywords": ["Junior", "Associate", "Graduate", "Entry Level"],
        "cover_letter_tone": "professional, concise, and role-focused",
        "job_search_note": "use graduate/associate keywords when relevant",
        "preferred_cv_template": "Modern Professional",
        "job_platforms": ["LinkedIn", "JobStreet", "Indeed", "MyCareersFuture"],
    },
    "Australia": {
        "cv_style": "concise, achievement-based resume with clear skills and practical outcomes",
        "avoid": ["overly long profile", "generic claims", "unsupported metrics"],
        "interview_style": "clear behavioral examples with practical results",
        "job_keywords": ["Graduate", "Junior", "Entry Level"],
        "cover_letter_tone": "professional and concise",
        "job_search_note": "use graduate/junior/entry-level terms where relevant",
        "preferred_cv_template": "Modern Professional",
        "job_platforms": ["LinkedIn", "Seek", "Indeed"],
    },
}


def get_country_rules(country: str = "") -> Dict[str, Any]:
    country_key = _wz_rules_norm_country(country)
    default = {
        "cv_style": "standard professional CV tailored to the selected country and role",
        "avoid": ["unsupported claims", "invented experience", "unclear dates", "long generic paragraphs"],
        "interview_style": "clear, structured, role-specific answers with evidence",
        "job_keywords": ["Junior", "Entry Level", "Graduate"],
        "cover_letter_tone": "professional, concise, and role-specific",
        "job_search_note": "adapt seniority keywords to the selected country and user status",
        "preferred_cv_template": "ATS Resume",
        "job_platforms": ["LinkedIn", "Indeed"],
    }
    found = COUNTRY_CAREER_RULES.get(country_key, {})
    merged = {**default, **found}
    merged["country"] = country_key or "International"
    return merged


def format_country_rules_for_prompt(country: str = "") -> str:
    rules = get_country_rules(country)
    avoid = ", ".join(rules.get("avoid") or [])
    keywords = ", ".join(rules.get("job_keywords") or [])
    return f"""
Selected market: {rules.get('country')}
CV style: {rules.get('cv_style')}
Interview style: {rules.get('interview_style')}
Cover-letter tone: {rules.get('cover_letter_tone')}
Job-search keywords: {keywords}
Avoid: {avoid}
Job-search note: {rules.get('job_search_note')}
""".strip()


def apply_cv_rules_prompt(cv_text: str, country: str = "", job_desc: str = "", language: str = "English") -> str:
    rules = get_country_rules(country)
    avoid = ", ".join(rules.get("avoid") or [])
    return f"""
Improve this CV for the selected job market.

Target country / market: {rules.get('country')}
Preferred output language: {language or 'English'}
Country CV style: {rules.get('cv_style')}
Avoid: {avoid}

Rules:
- Keep it truthful and ATS-friendly.
- Do not invent employers, dates, certificates, metrics, language levels, visa status, or achievements.
- Adapt tone and structure to the target country.
- If the job description requires something missing, mention it as a gap or suggestion, not as a claim.

CV:
{cv_text or ''}

Job description:
{job_desc or 'Not provided'}
""".strip()


def apply_interview_rules_prompt(country: str = "", language: str = "English", career_status: str = "", job_desc: str = "") -> str:
    rules = get_country_rules(country)
    return f"""
You are a realistic interviewer for the selected market.

Target country / market: {rules.get('country')}
Interview language: {language or 'English'}
Career situation: {career_status or 'Not specified'}
Interview style for this market: {rules.get('interview_style')}

Rules:
- Ask questions in the selected interview language.
- Adapt expectations to the country, role, career situation, CV, and job description.
- If the job description has a language requirement, evaluate whether the answer demonstrates that level.
- Be honest but helpful. Do not invent facts.

Job description context:
{job_desc or 'Not provided'}
""".strip()


def apply_cover_letter_prompt(country: str = "", language: str = "English", company: str = "") -> str:
    rules = get_country_rules(country)
    return f"""
Write a cover letter for the selected market.

Target country / market: {rules.get('country')}
Output language: {language or 'English'}
Company: {company or 'Not specified'}
Tone for this market: {rules.get('cover_letter_tone')}
CV/application style: {rules.get('cv_style')}

Rules:
- Keep it realistic, concise, and role-specific.
- Do not invent experience, dates, certificates, language levels, work authorization, or company facts.
- Use the selected country's communication style.
""".strip()


def get_job_search_keywords(country: str = "") -> List[str]:
    return list(get_country_rules(country).get("job_keywords") or ["Junior", "Entry Level"])


# =========================================================
# WorkZo v95 - Global auto-switch helpers
# =========================================================
def get_recommended_cv_template(country: str = "", career_status: str = "") -> str:
    """Return the best default CV template for the user's selected country/status.

    This is intentionally conservative: it only chooses a default. Users can
    still manually switch templates in the CV Editor.
    """
    rules = get_country_rules(country)
    status = (career_status or "").lower()
    base = rules.get("preferred_cv_template") or "ATS Resume"
    if any(x in status for x in ["student", "thesis", "intern", "graduate", "fresher", "entry"]):
        if (country or "").strip().lower() in ["germany", "austria", "switzerland"]:
            return "German ATS Resume"
        return "Graduate Portfolio"
    if any(x in status for x in ["career changer", "quereinsteiger", "returning", "career break"]):
        return "Career Pivot"
    return base


def get_country_job_platforms(country: str = "") -> List[str]:
    return list(get_country_rules(country).get("job_platforms") or ["LinkedIn", "Indeed"])


def build_global_feature_context(country: str = "", language: str = "English", career_status: str = "") -> Dict[str, Any]:
    """Shared context object for CV, Jobs, Interview, and Cover Letter."""
    rules = get_country_rules(country)
    return {
        "country": rules.get("country"),
        "language": language or "English",
        "career_status": career_status or "Not specified",
        "cv_style": rules.get("cv_style"),
        "avoid": rules.get("avoid") or [],
        "interview_style": rules.get("interview_style"),
        "job_keywords": rules.get("job_keywords") or [],
        "job_platforms": rules.get("job_platforms") or [],
        "cover_letter_tone": rules.get("cover_letter_tone"),
        "preferred_cv_template": get_recommended_cv_template(country, career_status),
        "job_search_note": rules.get("job_search_note"),
    }


# =========================================================
# WorkZo v96 - Shared memory, analytics, and CV-based job ranking
# Safe helpers used by Dashboard, Jobs, CV, Interview, and Cover Letter.
# These helpers avoid storing raw CV text by default.
# =========================================================
from datetime import datetime, timezone
import csv
import json
import os
import re
import hashlib
from pathlib import Path
from typing import Any, Dict, List

_WORKZO_MEMORY_FILE = Path("workzo_user_memory.json")
_WORKZO_ANALYTICS_FILE = Path("workzo_product_analytics.csv")


def _wz96_hash(value: str) -> str:
    return hashlib.sha256(str(value or "").encode("utf-8", errors="ignore")).hexdigest()[:16]


def _wz96_safe_memory_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    """Persist only non-sensitive product state. Do not store raw CV text or personal documents."""
    data = data or {}
    allowed = {
        "country", "migration_country", "preferred_language", "language", "user_status",
        "target_role", "selected_cv_template", "wz92_cv_template", "journey_stage",
        "application_readiness_value", "cv_score_value", "ats_score_value",
        "last_selected_job_title", "last_selected_job_company", "last_selected_job_location",
    }
    out = {k: v for k, v in data.items() if k in allowed and isinstance(v, (str, int, float, bool, type(None)))}
    if data.get("cv_text"):
        out["cv_hash"] = _wz96_hash(str(data.get("cv_text")))
    return out


def save_user_memory(data: Dict[str, Any], user_key: str = "default") -> bool:
    """Best-effort local memory for non-sensitive fields only."""
    try:
        user_key = _wz96_hash(user_key or "default")
        existing = {}
        if _WORKZO_MEMORY_FILE.exists():
            existing = json.loads(_WORKZO_MEMORY_FILE.read_text(encoding="utf-8") or "{}")
        existing[user_key] = _wz96_safe_memory_payload(data)
        _WORKZO_MEMORY_FILE.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
        return True
    except Exception:
        return False


def load_user_memory(user_key: str = "default") -> Dict[str, Any]:
    try:
        user_key = _wz96_hash(user_key or "default")
        if not _WORKZO_MEMORY_FILE.exists():
            return {}
        existing = json.loads(_WORKZO_MEMORY_FILE.read_text(encoding="utf-8") or "{}")
        value = existing.get(user_key, {})
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def log_event(event_name: str, page: str = "", metadata: Dict[str, Any] | None = None) -> bool:
    """Strong-but-simple analytics: timestamp, event, page, non-sensitive metadata."""
    try:
        metadata = metadata or {}
        safe_meta = {}
        for k, v in metadata.items():
            if k.lower() in {"cv", "cv_text", "resume", "email", "phone", "address", "document"}:
                continue
            if isinstance(v, (str, int, float, bool, type(None))):
                safe_meta[k] = v
        row = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": str(event_name or ""),
            "page": str(page or ""),
            "metadata": json.dumps(safe_meta, ensure_ascii=False),
        }
        exists = _WORKZO_ANALYTICS_FILE.exists()
        with _WORKZO_ANALYTICS_FILE.open("a", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["timestamp", "event", "page", "metadata"])
            if not exists:
                writer.writeheader()
            writer.writerow(row)
        return True
    except Exception:
        return False


def _wz96_extract_cv_skills(cv_text: str) -> List[str]:
    text = str(cv_text or "").lower()
    known = [
        "python", "sql", "excel", "tableau", "power bi", "pandas", "numpy", "machine learning",
        "data analysis", "dashboard", "reporting", "customer support", "technical support", "crm",
        "javascript", "react", "java", "aws", "azure", "gcp", "docker", "linux", "figma",
        "project management", "agile", "scrum", "sales", "marketing", "seo", "nlp", "api", "rest api",
    ]
    found = []
    for skill in known:
        if skill in text and skill not in found:
            found.append(skill)
    return found


def score_job_against_cv(job: Any, cv_text: str = "", country: str = "") -> int:
    """Score a job dict/string against CV skills + country keywords."""
    if isinstance(job, dict):
        hay = " ".join(str(job.get(k, "")) for k in ["title", "company", "location", "summary", "description", "tags"])
    else:
        hay = str(job or "")
    hay_l = hay.lower()
    skills = _wz96_extract_cv_skills(cv_text)
    score = 0
    for skill in skills:
        if skill.lower() in hay_l:
            score += 4
    for kw in get_job_search_keywords(country or ""):
        if str(kw).lower() in hay_l:
            score += 1
    return int(score)


def filter_jobs_by_cv(jobs: List[Any], cv_text: str = "", country: str = "", limit: int | None = None) -> List[Any]:
    """Deep CV-based ranking. Keeps all jobs but puts strongest matches first."""
    try:
        scored = []
        for job in jobs or []:
            scored.append((score_job_against_cv(job, cv_text, country), job))
        scored.sort(key=lambda x: x[0], reverse=True)
        ranked = []
        for score, job in scored:
            if isinstance(job, dict):
                job = dict(job)
                job["workzo_match_score"] = score
            ranked.append(job)
        return ranked[:limit] if limit else ranked
    except Exception:
        return jobs or []


def auto_select_template(country: str = "", career_stage: str = "") -> str:
    """Compatibility alias requested by UI modules."""
    return get_recommended_cv_template(country, career_stage)


# =========================================================
# WorkZo vNext Global Recruiter Rules Engine
# Structured behavior rules for global recruiter simulation.
# =========================================================
WORKZO_INTERVIEW_LANGUAGES = ["Auto","English","German","French","Spanish","Dutch","Italian","Portuguese","Hindi","Tamil","Malayalam","Telugu","Kannada","Arabic","Turkish","Polish","Swedish","Danish","Norwegian","Finnish","Chinese","Japanese","Korean","Indonesian","Thai","Vietnamese","Mixed / bilingual"]
_GLOBAL_RECRUITER_RULES = {
 "Global": dict(tone="balanced, realistic, evidence-seeking", expects=["clear role fit","truthful examples","measurable proof"], risks=["generic answers","unsupported claims"], languages=["English","Mixed / bilingual"], interruption_style="Ask for clarity when answers become vague.", resume_norms=["ATS-friendly","role-specific","no invented metrics"]),
 "Germany": dict(tone="structured, precise, evidence-heavy", expects=["clear structure","specific examples","truthful language levels","practical proof"], risks=["overclaiming","vague impact","unstructured storytelling"], languages=["German","English","Mixed / bilingual"], interruption_style="Polite but direct; asks for structure and evidence.", resume_norms=["structured Lebenslauf","clear dates","language levels","no exaggerated claims"]),
 "USA": dict(tone="confident, impact-focused, direct", expects=["ownership","measurable business impact","concise STAR stories"], risks=["weak ownership","low energy","missing numbers"], languages=["English","Spanish"], interruption_style="Fast clarification; pushes for business outcome and ownership.", resume_norms=["ATS resume","no photo/age","impact bullets","action verbs"]),
 "UK": dict(tone="professional, competency-based, balanced", expects=["competency examples","collaboration","clear judgement"], risks=["over-selling","unclear contribution","too much background"], languages=["English"], interruption_style="Calm, asks for a sharper competency example.", resume_norms=["concise CV","role evidence","no unnecessary personal details"]),
 "Canada": dict(tone="collaborative, practical, evidence-based", expects=["team fit","clear impact","communication clarity"], risks=["generic examples","no measurable result"], languages=["English","French"], interruption_style="Supportive but asks for concrete proof.", resume_norms=["ATS resume","no photo","impact-focused","clear location/remote fit"]),
 "India": dict(tone="technical-depth seeking, structured, detail-friendly", expects=["technical depth","clear ownership","communication fluency","project explanation"], risks=["too much theory","weak practical impact","unclear personal contribution"], languages=["English","Hindi","Tamil","Telugu","Malayalam","Kannada","Mixed / bilingual"], interruption_style="Pushes for exact contribution and technical clarity.", resume_norms=["skills clarity","project proof","education clarity","ATS keywords"]),
 "UAE": dict(tone="professional, multicultural, adaptability-focused", expects=["professional presence","adaptability","cross-cultural communication","business value"], risks=["unclear relocation/availability","weak professionalism","generic motivation"], languages=["English","Arabic","Hindi","Mixed / bilingual"], interruption_style="Asks for concise business relevance and adaptability.", resume_norms=["professional CV","availability clarity","international experience","role relevance"]),
 "Netherlands": dict(tone="direct, practical, low-fluff", expects=["clear contribution","practical problem-solving","honest self-assessment"], risks=["over-polished answers","vague ownership"], languages=["Dutch","English"], interruption_style="Directly asks for shorter, clearer answers.", resume_norms=["concise CV","skills evidence","straightforward wording"]),
 "Australia": dict(tone="practical, friendly, evidence-led", expects=["clear examples","team fit","practical outcomes"], risks=["generic claims","poor role alignment"], languages=["English"], interruption_style="Friendly but probes for exact result.", resume_norms=["ATS-friendly resume","clear achievements","no unnecessary personal data"]),
 "France": dict(tone="formal, analytical, structured", expects=["structured explanation","education/qualification clarity","professional tone"], risks=["too casual","unsupported claims"], languages=["French","English"], interruption_style="Formal probe for structure and reasoning.", resume_norms=["structured CV","education clarity","French/English language fit"]),
 "Spain": dict(tone="warm but role-focused", expects=["motivation","teamwork","practical examples"], risks=["weak specificity","unclear motivation"], languages=["Spanish","English"], interruption_style="Asks for a concrete example.", resume_norms=["clear CV","skills and experience","language levels"]),
 "Switzerland": dict(tone="precise, formal, quality-focused", expects=["precision","reliability","language clarity","proof"], risks=["casual tone","unclear language level","unsupported claims"], languages=["German","French","Italian","English"], interruption_style="Precise, asks for evidence and fit.", resume_norms=["structured CV","language levels","clear dates"]),
 "Austria": dict(tone="formal, structured, evidence-based", expects=["clear examples","formal communication","reliable proof"], risks=["vagueness","overclaiming"], languages=["German","English"], interruption_style="Structured follow-up for details.", resume_norms=["DACH-style CV","clear dates","language levels"]),
 "Singapore": dict(tone="efficient, high-standard, business-focused", expects=["clarity","business impact","adaptability","professionalism"], risks=["generic answers","weak impact"], languages=["English","Chinese","Malay","Tamil"], interruption_style="Efficient probe for outcome and fit.", resume_norms=["ATS resume","achievement bullets","language clarity"]),
 "Japan": dict(tone="formal, precise, reliability-focused", expects=["respectful communication","process discipline","team orientation"], risks=["too casual","unclear reliability","overclaiming"], languages=["Japanese","English"], interruption_style="Formal clarification; asks for process and team fit.", resume_norms=["structured resume","education/work history clarity","formal tone"]),
 "Brazil": dict(tone="warm, practical, communication-aware", expects=["collaboration","motivation","practical results"], risks=["vague results","unclear ownership"], languages=["Portuguese","English"], interruption_style="Warm but asks for a clear result.", resume_norms=["clear CV","achievements","skills"]),
}
for _country in ["Ireland","New Zealand","Italy","Portugal","Sweden","Denmark","Norway","Finland","Poland","Malaysia","South Korea","Mexico","South Africa","Belgium","Luxembourg","Czech Republic","Hungary","Romania","Greece","Turkey","Saudi Arabia","Qatar","Kuwait","Oman","Bahrain","Israel","China","Hong Kong","Taiwan","Thailand","Vietnam","Indonesia","Philippines","Argentina","Chile","Colombia","Nigeria","Kenya","Egypt"]:
    _GLOBAL_RECRUITER_RULES.setdefault(_country, dict(tone="professional, market-aware, evidence-seeking", expects=["role fit","clear examples","truthful proof"], risks=["generic answers","unsupported claims","missing impact"], languages=["English","Local language","Mixed / bilingual"], interruption_style="Ask for concrete evidence and local market fit.", resume_norms=["ATS-friendly","role-specific","clear language levels"]))
WORKZO_SUPPORTED_COUNTRIES = sorted(_GLOBAL_RECRUITER_RULES.keys())
def get_workzo_supported_countries(): return WORKZO_SUPPORTED_COUNTRIES[:]
def get_workzo_interview_languages(country="Global"):
    rules=get_workzo_global_recruiter_rules(country); langs=["Auto"]+[x for x in rules.get("languages",[]) if x!="Auto"]+[x for x in WORKZO_INTERVIEW_LANGUAGES if x not in rules.get("languages",[]) and x!="Auto"]
    return list(dict.fromkeys(langs))
def get_workzo_global_recruiter_rules(country="Global"):
    country=_wz_rules_norm_country(country or "Global"); rules=dict(_GLOBAL_RECRUITER_RULES.get(country) or _GLOBAL_RECRUITER_RULES.get("Global")); rules["country"]=country if country in _GLOBAL_RECRUITER_RULES else "Global"
    rules.setdefault("honesty_rules", ["Do not invent metrics, job titles, certifications, company names, or achievements.","If proof is missing, say clearly that proof is missing.","Reward truthful, specific examples more than confident but unsupported claims.","Adapt tone, questions, and rejection reasoning to the selected market and language."])
    rules.setdefault("scoring_weights", {"relevance":18,"clarity":14,"star":16,"metrics":18,"ownership":16,"confidence":8,"country_fit":10})
    rules.setdefault("rejection_reasons", ["insufficient proof","unclear ownership","weak role alignment","missing measurable impact"])
    return rules
def build_workzo_recruiter_system_prompt(country="Global", language="English"):
    r=get_workzo_global_recruiter_rules(country)
    return ("You are WorkZo's AI recruiter simulation engine.\n"
            f"Market/country: {r.get('country')}\nInterview language: {language}\nRecruiter tone: {r.get('tone')}\n"
            f"Expected behavior: {', '.join(r.get('expects', []))}\nRisk flags: {', '.join(r.get('risks', []))}\n"
            f"Interruption style: {r.get('interruption_style')}\nResume norms: {', '.join(r.get('resume_norms', []))}\n"
            f"Honesty rules: {', '.join(r.get('honesty_rules', []))}\n"
            "Evaluate every answer for relevance, clarity, STAR structure, measurable proof, ownership, confidence, and country fit. Never fake praise.")
