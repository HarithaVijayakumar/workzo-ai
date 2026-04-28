# WorkZo modular split v138
# Source: app_workzo_v137_stable_no_feature_change.py, lines 4160-5657

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
        r"â¬\s?\d+",
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
    Fix common PDF extraction problems before WorkZo shows or sends CV text to AI.
    Keeps contact details, headings, and profile text from being merged into one line.
    """
    if not raw_text:
        return ""

    text = raw_text.replace("\x00", " ").replace("\r", "\n")
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

    text = re.sub(r"([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})", r"\n\1\n", text, flags=re.I)
    text = re.sub(r"(\+?\d[\d\s\-()]{7,}\d)", r"\n\1\n", text)
    text = re.sub(r"(linkedin\.com/\S+)", r"\n\1\n", text, flags=re.I)

    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
    text = re.sub(r"\b(and|with|in|using|after|before|through|for)([a-zA-Z])", r"\1 \2", text, flags=re.I)
    text = re.sub(r"([a-zA-Z])(and|with|in|using|after|before|through|for)\b", r"\1 \2", text, flags=re.I)
    text = re.sub(r"(Wurzburg|Wuerzburg|Germany|Deutschland)\s+(SQL|Python|Tableau|Power BI|Over|Ex-|Experienced|Skilled)", r"\1\n\2", text, flags=re.I)
    text = re.sub(r"(Bootcamp|School|University|College)\s+(Resolved|Provided|Improved|Automated|Built|Managed|Handled)", r"\1\n\2", text, flags=re.I)

    headings = [
        "PROFILE", "PROFESSIONAL SUMMARY", "SUMMARY", "OBJECTIVE", "WORK EXPERIENCE", "EXPERIENCE",
        "EMPLOYMENT HISTORY", "PROJECTS", "SKILLS", "TECHNICAL SKILLS", "EDUCATION", "CERTIFICATIONS",
        "LANGUAGES", "TOOLS", "CONTACT", "ACHIEVEMENTS"
    ]
    for h in headings:
        text = re.sub(rf"\s+({re.escape(h)})\s+", rf"\n\1\n", text, flags=re.I)

    text = re.sub(r"(\b\d{5}\b\s+[^\n,]+(?:,\s*[^\n]+)?)(\s+(?:Over|Ex-|Experienced|Skilled|Motivated|Passionate)\b)", r"\1\n\2", text)

    text = re.sub(r"[ \t]+", " ", text)
    lines = [line.strip() for line in text.splitlines()]
    cleaned = []
    for line in lines:
        if not line:
            if cleaned and cleaned[-1] != "":
                cleaned.append("")
            continue
        cleaned.append(line)
    text = "\n".join(cleaned)
    text = re.sub(r"\n{3,}", "\n\n", text)
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
Selected output language: {st.session_state.get("preferred_language", "English")}

Rules:
- Build a clean, ATS-friendly CV.
- The user may write broken English, short notes, or keywords. Convert them into polished professional resume wording.
- Translate the CV headings and content fully into the selected output language. Do not mix languages.
- Use only information the user provided.
- Do not invent employers, dates, degrees, tools, or achievements.
- If details are missing, add a clear section called "Missing Information to Improve It" in the selected output language.
- Make the CV suitable for the target country where possible.
"""
    return run_ai_prompt(prompt)

def organize_cv_for_display(cv_text: str) -> str:
    return clean_cv_text(cv_text)


def _json_extract_object(raw: str) -> dict:
    """Best-effort JSON extraction without depending on later helper definitions."""
    if not raw:
        return {}
    try:
        return json.loads(raw.strip())
    except Exception:
        pass
    m = re.search(r"\{.*\}", raw, flags=re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            return {}
    return {}


def _as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    text = str(value).strip()
    if not text:
        return []
    return [x.strip(" -•\t") for x in re.split(r"\n|;|\|", text) if x.strip(" -•\t")]



def _normalize_date_text(value: str) -> str:
    """Normalize resume date text without guessing missing dates."""
    text = str(value or "").strip()
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text)
    text = text.replace("-", "-").replace("—", "-")
    text = re.sub(r"\b(present|current|till date|today|heute)\b", "Present", text, flags=re.I)
    text = re.sub(r"\s*-\s*", " - ", text)
    return text.strip(" |,-")


def _date_sort_value(date_text: str) -> int:
    """Return sortable year value; Present/current ranks highest. Unknown dates rank low."""
    text = str(date_text or "")
    if re.search(r"present|current|heute|today|till date", text, re.I):
        return 9999
    years = [int(y) for y in re.findall(r"(?:19|20)\d{2}", text)]
    return max(years) if years else 0


def _looks_like_date_piece(text: str) -> bool:
    return bool(re.search(r"(?:19|20)\d{2}|present|current|heute|till date", str(text or ""), re.I))


def _split_structured_header(line: str):
    """Parse a header like 'Role | Company | 2018 - 2020' into fields."""
    raw = str(line or "").strip(" -•\t")
    if not raw:
        return "", "", ""
    parts = [x.strip() for x in re.split(r"\s+\|\s+|\t+", raw) if x.strip()]
    date = ""
    non_date = []
    for part in parts:
        if _looks_like_date_piece(part) and not date:
            date = _normalize_date_text(part)
        else:
            non_date.append(part)
    if not date:
        m = re.search(r"((?:19|20)\d{2}\s*(?:-|to|-|—)\s*(?:(?:19|20)\d{2}|Present|present|Current|current|Heute|heute)|(?:19|20)\d{2})", raw)
        if m:
            date = _normalize_date_text(m.group(1))
            raw_without_date = (raw[:m.start()] + raw[m.end():]).strip(" |,-")
            non_date = [x.strip() for x in re.split(r"\s+\|\s+|\t+", raw_without_date) if x.strip()]
    first = non_date[0] if len(non_date) > 0 else ""
    second = non_date[1] if len(non_date) > 1 else ""
    return first, second, date


def sort_resume_items_by_date(items: list) -> list:
    if not isinstance(items, list):
        return []
    return sorted(items, key=lambda item: _date_sort_value(str((item or {}).get("dates") or (item or {}).get("year") or "")), reverse=True)


def parse_experience_text_to_items(text: str) -> list:
    """Convert editable experience text into stable objects with title/company/dates/bullets."""
    items = []
    current = None
    for raw in str(text or "").splitlines():
        line = raw.strip()
        if not line:
            if current and (current.get("title") or current.get("company") or current.get("bullets")):
                items.append(current)
                current = None
            continue
        if line.startswith(("-", "•")):
            if current is None:
                current = {"title": "", "company": "", "dates": "", "bullets": []}
            bullet = line.strip("-• ")
            if bullet:
                current.setdefault("bullets", []).append(bullet)
            continue
        if current and (current.get("title") or current.get("company") or current.get("bullets")):
            items.append(current)
        first, second, date = _split_structured_header(line)
        current = {"title": first, "company": second, "dates": date, "bullets": []}
    if current and (current.get("title") or current.get("company") or current.get("bullets")):
        items.append(current)

    cleaned = []
    edu_words = ("school", "college", "university", "bachelor", "master", "degree", "bootcamp")
    for item in items:
        joined = " ".join([str(item.get("title", "")), str(item.get("company", ""))]).lower()
        if any(w in joined for w in edu_words) and not item.get("bullets"):
            continue
        cleaned.append(item)
    return sort_resume_items_by_date(cleaned)


def parse_education_text_to_items(text: str) -> list:
    items = []
    for raw in str(text or "").splitlines():
        line = raw.strip(" -•\t")
        if not line:
            continue
        first, second, date = _split_structured_header(line)
        degree = first
        institution = second
        if re.search(r"school|college|university|coding", degree, re.I) and re.search(r"bachelor|master|bootcamp|degree|science|arts", institution, re.I):
            degree, institution = institution, degree
        items.append({"degree": degree, "institution": institution, "dates": date, "year": ""})
    return sort_resume_items_by_date(items)


def parse_projects_text_to_items(text: str) -> list:
    items = []
    current = None
    for raw in str(text or "").splitlines():
        line = raw.strip()
        if not line:
            if current:
                items.append(current)
                current = None
            continue
        if line.startswith(("-", "•")):
            if current is None:
                current = {"name": "Project", "bullets": []}
            b = line.strip("-• ")
            if b:
                current.setdefault("bullets", []).append(b)
        else:
            if current:
                items.append(current)
            current = {"name": line.strip("-• "), "bullets": []}
    if current:
        items.append(current)
    return items


def _safe_string(value) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, dict)):
        return ""
    return clean_cv_text(str(value)).strip()


def _dedupe_case_insensitive(items: List[str]) -> List[str]:
    seen = set()
    out = []
    for item in items or []:
        value = _safe_string(item)
        key = value.lower()
        if value and key not in seen:
            seen.add(key)
            out.append(value)
    return out


def _normalize_contact_dict(value) -> Dict:
    value = value if isinstance(value, dict) else {}
    return {
        "phone": _safe_string(value.get("phone")),
        "email": _safe_string(value.get("email")),
        "location": _safe_string(value.get("location")),
        "linkedin": _safe_string(value.get("linkedin")),
    }


def _coerce_structured_resume_schema(data: dict) -> dict:
    """Force AI JSON into WorkZo's data contract before any template rendering."""
    if not isinstance(data, dict):
        return {}

    clean = {
        "full_name": _safe_string(data.get("full_name") or data.get("name")),
        "target_role": _safe_string(data.get("target_role") or data.get("current_role") or data.get("headline")),
        "contact": _normalize_contact_dict(data.get("contact") or data.get("personal_info") or {}),
        "professional_summary": _safe_string(data.get("professional_summary") or data.get("summary")),
        "core_skills": _dedupe_case_insensitive(_as_list(data.get("core_skills") or data.get("skills") or data.get("sidebar_skills"))),
        "tools_technologies": _dedupe_case_insensitive(_as_list(data.get("tools_technologies") or data.get("tools") or data.get("expertise"))),
        "work_experience": [],
        "projects": [],
        "education": [],
        "certifications": _dedupe_case_insensitive(_as_list(data.get("certifications"))),
        "languages": _dedupe_case_insensitive(_as_list(data.get("languages"))),
        "suggested_additions": _dedupe_case_insensitive(_as_list(data.get("suggested_additions"))),
        "details_to_confirm": _dedupe_case_insensitive(_as_list(data.get("details_to_confirm"))),
        "honesty_audit": data.get("honesty_audit") if isinstance(data.get("honesty_audit"), dict) else {
            "omitted_missing_jd_requirements": [],
            "rephrased_terms": [],
            "needs_user_confirmation": [],
        },
    }

    exp = data.get("work_experience") or data.get("experience") or data.get("main_experience") or []
    if isinstance(exp, str):
        exp = parse_experience_text_to_items(exp)
    elif isinstance(exp, dict):
        exp = [exp]
    for job in exp if isinstance(exp, list) else []:
        if not isinstance(job, dict):
            continue
        date_parts = [_safe_string(job.get("startDate") or job.get("start_date")), _safe_string(job.get("endDate") or job.get("end_date"))]
        clean["work_experience"].append({
            "title": _safe_string(job.get("title") or job.get("role") or job.get("position")),
            "company": _safe_string(job.get("company") or job.get("employer")),
            "dates": _normalize_date_text(job.get("dates") or " - ".join([x for x in date_parts if x])),
            "bullets": _dedupe_case_insensitive(_as_list(job.get("bullets") or job.get("achievements") or job.get("responsibilities") or job.get("description"))),
        })

    projects = data.get("projects") or []
    if isinstance(projects, str):
        projects = parse_projects_text_to_items(projects)
    elif isinstance(projects, dict):
        projects = [projects]
    for pr in projects if isinstance(projects, list) else []:
        if isinstance(pr, dict):
            clean["projects"].append({
                "name": _safe_string(pr.get("name") or pr.get("title")),
                "bullets": _dedupe_case_insensitive(_as_list(pr.get("bullets") or pr.get("description") or pr.get("details"))),
            })

    edu = data.get("education") or data.get("main_education") or []
    if isinstance(edu, str):
        edu = parse_education_text_to_items(edu)
    elif isinstance(edu, dict):
        edu = [edu]
    for ed in edu if isinstance(edu, list) else []:
        if isinstance(ed, dict):
            clean["education"].append({
                "degree": _safe_string(ed.get("degree") or ed.get("qualification") or ed.get("area")),
                "institution": _safe_string(ed.get("institution") or ed.get("school") or ed.get("college") or ed.get("university")),
                "year": _safe_string(ed.get("year")),
                "dates": _normalize_date_text(ed.get("dates") or ed.get("date") or ed.get("year")),
            })

    audit = clean.get("honesty_audit") or {}
    clean["honesty_audit"] = {
        "omitted_missing_jd_requirements": _dedupe_case_insensitive(_as_list(audit.get("omitted_missing_jd_requirements") or audit.get("omitted"))),
        "rephrased_terms": _as_list(audit.get("rephrased_terms") or audit.get("rephrased")),
        "needs_user_confirmation": _dedupe_case_insensitive(_as_list(audit.get("needs_user_confirmation") or audit.get("needs_confirmation"))),
    }
    return clean


def _original_company_names(cv_text: str) -> set:
    companies = set()
    for name in re.findall(r"\b(?:Zoho Corp|CSS Corp|WBS Coding School|SRM Arts & Science College|[A-Z][A-Za-z&. ]{2,40}(?:Corp|Ltd|GmbH|Inc|LLC|School|College|University))\b", cv_text or ""):
        companies.add(name.strip().lower())
    return companies


def validate_structured_resume_against_source(data: dict, raw_cv_text: str) -> dict:
    """Add honesty flags if extraction appears to introduce unsupported entities."""
    data = _coerce_structured_resume_schema(data)
    source = (raw_cv_text or "").lower()
    source_companies = _original_company_names(raw_cv_text or "")
    flags = list(data.get("details_to_confirm") or [])
    unsupported = []

    for job in data.get("work_experience", []):
        company = str(job.get("company") or "").strip()
        if company and company.lower() not in source and source_companies and company.lower() not in source_companies:
            unsupported.append(f"Confirm company name: {company}")
        for metric in re.findall(r"\b\d+%|\b\d+\+?\s+(?:users|clients|tickets|projects|teams|months|years)\b", " ".join(job.get("bullets") or []), flags=re.I):
            if metric.lower() not in source:
                unsupported.append(f"Confirm metric: {metric}")

    for skill in (data.get("core_skills") or []) + (data.get("tools_technologies") or []):
        sk = str(skill).lower().strip()
        if sk and len(sk) > 2 and sk not in source:
            unsupported.append(f"Confirm skill/tool: {skill}")

    data["details_to_confirm"] = _dedupe_case_insensitive(flags + unsupported)[:18]
    audit = data.get("honesty_audit") or {}
    audit["needs_user_confirmation"] = _dedupe_case_insensitive(_as_list(audit.get("needs_user_confirmation")) + unsupported)[:18]
    data["honesty_audit"] = audit
    return data


def validate_resume_dates_and_sections(data: dict) -> dict:
    """Keep dates attached to their own objects and prevent education/project dates from drifting."""
    if not isinstance(data, dict):
        return {}
    data = _coerce_structured_resume_schema(data)

    exp = data.get("work_experience") or data.get("experience") or []
    if isinstance(exp, str):
        exp = parse_experience_text_to_items(exp)
    elif isinstance(exp, dict):
        exp = [exp]
    elif isinstance(exp, list):
        exp = [x for x in exp if isinstance(x, dict)]

    normalized_exp = []
    moved_education = []
    for job in exp:
        title = str(job.get("title") or job.get("role") or "").strip()
        company = str(job.get("company") or job.get("employer") or "").strip()
        dates = _normalize_date_text(job.get("dates") or job.get("date") or "")
        bullets = _as_list(job.get("bullets") or job.get("achievements") or job.get("responsibilities"))
        joined = f"{title} {company}".lower()
        if any(w in joined for w in ["school", "college", "university", "bachelor", "master", "bootcamp"]) and not bullets:
            moved_education.append({"degree": title, "institution": company, "dates": dates, "year": ""})
            continue
        normalized_exp.append({"title": title, "company": company, "dates": dates, "bullets": bullets})
    data["work_experience"] = sort_resume_items_by_date(normalized_exp)

    edu = data.get("education") or []
    if isinstance(edu, str):
        edu = parse_education_text_to_items(edu)
    elif isinstance(edu, dict):
        edu = [edu]
    elif isinstance(edu, list):
        normalized = []
        for ed in edu:
            if isinstance(ed, dict):
                ed = dict(ed)
                ed["dates"] = _normalize_date_text(ed.get("dates") or ed.get("year") or "")
                normalized.append(ed)
            elif str(ed).strip():
                normalized.extend(parse_education_text_to_items(str(ed)))
        edu = normalized
    data["education"] = sort_resume_items_by_date((edu or []) + moved_education)

    projects = data.get("projects") or []
    if isinstance(projects, str):
        projects = parse_projects_text_to_items(projects)
    elif isinstance(projects, dict):
        projects = [projects]
    data["projects"] = projects if isinstance(projects, list) else []
    return data

def _format_structured_resume_profile(data: dict) -> str:
    """Convert AI-extracted JSON facts into the exact plain structure WorkZo templates expect."""
    data = validate_resume_dates_and_sections(data)
    if not isinstance(data, dict) or not data:
        return ""

    def val(*keys, default=""):
        for k in keys:
            v = data.get(k)
            if isinstance(v, str) and v.strip():
                return v.strip()
        return default

    name = val("full_name", "name", default="Your Name")
    role = val("target_role", "current_role", "headline", default="Target Role")
    contact = data.get("contact", {}) if isinstance(data.get("contact"), dict) else {}
    contact_parts = []
    for k in ["phone", "email", "location", "linkedin"]:
        v = contact.get(k) or data.get(k)
        if v and str(v).strip():
            contact_parts.append(str(v).strip())

    lines = [name, role]
    if contact_parts:
        lines.append(" | ".join(contact_parts))

    summary = val("professional_summary", "summary")
    if summary:
        lines += ["", "PROFESSIONAL SUMMARY", summary]

    skills = _as_list(data.get("core_skills") or data.get("skills"))
    tools = _as_list(data.get("tools_technologies") or data.get("tools"))
    merged_skills = []
    for item in skills + tools:
        if item and item.lower() not in [x.lower() for x in merged_skills]:
            merged_skills.append(item)
    if merged_skills:
        lines += ["", "CORE SKILLS"] + [f"- {x}" for x in merged_skills]

    experience = data.get("work_experience") or data.get("experience") or []
    if isinstance(experience, dict):
        experience = [experience]
    if experience:
        lines += ["", "PROFESSIONAL EXPERIENCE"]
        for job in experience if isinstance(experience, list) else [experience]:
            if isinstance(job, dict):
                title = str(job.get("title") or job.get("role") or "").strip()
                company = str(job.get("company") or job.get("employer") or "").strip()
                dates = str(job.get("dates") or job.get("date") or "").strip()
                header = " | ".join([x for x in [title, company, dates] if x])
                if header:
                    lines.append(header)
                for b in _as_list(job.get("bullets") or job.get("achievements") or job.get("responsibilities")):
                    lines.append(f"- {b}")
            else:
                for b in _as_list(job):
                    lines.append(f"- {b}")

    projects = data.get("projects") or []
    if projects:
        lines += ["", "PROJECTS"]
        for pr in projects if isinstance(projects, list) else [projects]:
            if isinstance(pr, dict):
                title = str(pr.get("name") or pr.get("title") or "Project").strip()
                lines.append(title)
                for b in _as_list(pr.get("bullets") or pr.get("description") or pr.get("details")):
                    lines.append(f"- {b}")
            else:
                lines.append(str(pr).strip())

    education = data.get("education") or []
    if education:
        lines += ["", "EDUCATION"]
        for ed in education if isinstance(education, list) else [education]:
            if isinstance(ed, dict):
                parts = [str(ed.get(k) or "").strip() for k in ["degree", "institution", "dates", "year"]]
                line = " | ".join([x for x in parts if x])
                if line:
                    lines.append(line)
            else:
                lines.append(str(ed).strip())

    certs = _as_list(data.get("certifications"))
    if certs:
        lines += ["", "CERTIFICATIONS"] + [f"- {x}" for x in certs]

    langs = _as_list(data.get("languages"))
    if langs:
        lines += ["", "LANGUAGES"] + [f"- {x}" for x in langs]

    confirm = _as_list(data.get("details_to_confirm"))
    if confirm:
        lines += ["", "DETAILS TO CONFIRM"] + [f"- {x}" for x in confirm]

    return clean_cv_text("\n".join(lines))




def extract_structured_resume_json(raw_cv_text: str, target_country: str, user_status: str) -> dict:
    """Extract resume facts into structured JSON while deliberately ignoring PDF reading order."""
    cleaned_raw = clean_cv_text(raw_cv_text)
    if not cleaned_raw.strip():
        return {}

    prompt = f"""
The following CV text may come from a two-column, Canva-style, table-style, or badly parsed PDF.
The reading order may be wrong. Your task is to extract resume FACTS into a strict JSON data contract. Do not design or format a CV.

Target country: {target_country}
Career status: {user_status}
Preferred language: {st.session_state.get('preferred_language', 'English')}

STRICT HONESTY RULES:
- Use only facts present in the raw CV text. Do not use outside knowledge.
- Do not invent employers, job titles, dates, degrees, certifications, languages, tools, percentages, achievements, or seniority.
- If a target job would need a skill that is missing from the CV, place it in suggested_additions only. Do NOT add it to core_skills/tools/work bullets.
- If information is missing, return an empty string/list. Do not guess.
- Every work_experience object MUST contain title, company, dates, and bullets. If a date is missing, use an empty string.
- Every education object MUST contain degree, institution, year, and dates. If a date is missing, use an empty string.
- Do not borrow dates from a nearby line. Attach dates only when clearly connected to the same company/degree/project.
- Classify every useful line by meaning, NOT by raw PDF order. Education must stay in education even if it appears under the name in the extracted text.
- Fix broken PDF words such as "in ternal" -> "internal", "You Tube" -> "YouTube", "for m" -> "form", "In dian" -> "Indian", "Support Specialistandaspiring" -> "Support Specialist and aspiring".
- Remove generic soft skills unless clearly relevant to the target role.

FEW-SHOT FORMAT EXAMPLE FOR DATES:
Input-like fact: "Zoho Corp 2018 - 2020 Technical Support Engineer Resolved 90%..."
Correct JSON object: {{"title":"Technical Support Engineer","company":"Zoho Corp","dates":"2018 - 2020","bullets":["Resolved 90%..."]}}
If the date is not clearly connected: {{"title":"Technical Support Engineer","company":"Zoho Corp","dates":"","bullets":["..."]}}

Return ONLY valid JSON with exactly these top-level keys:
{{
  "full_name": "",
  "target_role": "",
  "contact": {{"phone":"", "email":"", "location":"", "linkedin":""}},
  "professional_summary": "",
  "core_skills": [],
  "tools_technologies": [],
  "work_experience": [
    {{"title":"", "company":"", "dates":"", "bullets": []}}
  ],
  "projects": [
    {{"name":"", "bullets": []}}
  ],
  "education": [
    {{"degree":"", "institution":"", "year":"", "dates":""}}
  ],
  "certifications": [],
  "languages": [],
  "suggested_additions": [],
  "details_to_confirm": [],
  "honesty_audit": {{
    "omitted_missing_jd_requirements": [],
    "rephrased_terms": [],
    "needs_user_confirmation": []
  }}
}}

Raw extracted CV text:
{cleaned_raw[:16000]}
"""
    raw_json = run_ai_prompt(
        prompt,
        system_addition="You are a strict resume information extraction engine. Return valid JSON only.",
        force_language="English",
        json_mode=True,
    )
    data = _json_extract_object(raw_json)
    if not isinstance(data, dict):
        return {}
    data = validate_structured_resume_against_source(data, cleaned_raw)
    return validate_resume_dates_and_sections(data)


def _protected_resume_facts(data: dict) -> dict:
    """Facts that AI must never rewrite during tailoring."""
    data = validate_resume_dates_and_sections(data or {})
    contact = data.get("contact", {}) if isinstance(data.get("contact"), dict) else {}
    return {
        "full_name": data.get("full_name", ""),
        "target_role": data.get("target_role", ""),
        "contact": {
            "phone": contact.get("phone", ""),
            "email": contact.get("email", ""),
            "location": contact.get("location", ""),
            "linkedin": contact.get("linkedin", ""),
        },
        "companies": [j.get("company", "") for j in data.get("work_experience", []) if isinstance(j, dict)],
        "roles": [j.get("title", "") for j in data.get("work_experience", []) if isinstance(j, dict)],
        "work_dates": [j.get("dates", "") for j in data.get("work_experience", []) if isinstance(j, dict)],
        "education_institutions": [e.get("institution", "") for e in data.get("education", []) if isinstance(e, dict)],
        "education_dates": [e.get("dates", "") or e.get("year", "") for e in data.get("education", []) if isinstance(e, dict)],
    }


def _reinject_protected_resume_facts(candidate: dict, protected: dict) -> dict:
    """Put protected facts back after AI transformation so dates/companies cannot drift."""
    candidate = _coerce_structured_resume_schema(candidate or {})
    if not protected:
        return validate_resume_dates_and_sections(candidate)
    candidate["full_name"] = protected.get("full_name") or candidate.get("full_name", "")
    if protected.get("target_role") and not candidate.get("target_role"):
        candidate["target_role"] = protected.get("target_role")
    candidate["contact"] = protected.get("contact") or candidate.get("contact", {})

    # Experience count/order is anchored to the source. AI may rewrite only bullets/summary.
    anchored = []
    source_companies = protected.get("companies") or []
    source_roles = protected.get("roles") or []
    source_dates = protected.get("work_dates") or []
    ai_exp = candidate.get("work_experience") or []
    for idx, company in enumerate(source_companies):
        ai_job = ai_exp[idx] if idx < len(ai_exp) and isinstance(ai_exp[idx], dict) else {}
        anchored.append({
            "company": company,
            "title": source_roles[idx] if idx < len(source_roles) else ai_job.get("title", ""),
            "dates": source_dates[idx] if idx < len(source_dates) else ai_job.get("dates", ""),
            "bullets": _dedupe_case_insensitive(_as_list(ai_job.get("bullets") or [])),
        })
    if anchored:
        candidate["work_experience"] = anchored

    anchored_edu = []
    source_schools = protected.get("education_institutions") or []
    source_edu_dates = protected.get("education_dates") or []
    ai_edu = candidate.get("education") or []
    for idx, school in enumerate(source_schools):
        ai_ed = ai_edu[idx] if idx < len(ai_edu) and isinstance(ai_edu[idx], dict) else {}
        anchored_edu.append({
            "institution": school,
            "degree": ai_ed.get("degree", ""),
            "dates": source_edu_dates[idx] if idx < len(source_edu_dates) else ai_ed.get("dates", ""),
            "year": source_edu_dates[idx] if idx < len(source_edu_dates) else ai_ed.get("year", ""),
        })
    if anchored_edu:
        candidate["education"] = anchored_edu
    return validate_resume_dates_and_sections(candidate)


def validate_generated_resume_against_source(original: dict, candidate: dict) -> dict:
    """QA layer: flag any drift between source facts and the generated CV JSON."""
    original = validate_resume_dates_and_sections(original or {})
    candidate = validate_resume_dates_and_sections(candidate or {})
    flags = []
    protected = _protected_resume_facts(original)

    def norm_list(values):
        return [str(x or "").strip().lower() for x in values if str(x or "").strip()]

    for label, src, out in [
        ("company", protected.get("companies", []), [j.get("company") for j in candidate.get("work_experience", []) if isinstance(j, dict)]),
        ("role", protected.get("roles", []), [j.get("title") for j in candidate.get("work_experience", []) if isinstance(j, dict)]),
        ("work date", protected.get("work_dates", []), [j.get("dates") for j in candidate.get("work_experience", []) if isinstance(j, dict)]),
        ("education institution", protected.get("education_institutions", []), [e.get("institution") for e in candidate.get("education", []) if isinstance(e, dict)]),
    ]:
        src_norm = norm_list(src)
        out_norm = norm_list(out)
        if src_norm and out_norm and src_norm != out_norm[:len(src_norm)]:
            flags.append(f"Check {label} order/details. WorkZo restored the original factual fields where possible.")

    audit = candidate.get("honesty_audit") or {}
    audit["needs_user_confirmation"] = _dedupe_case_insensitive(_as_list(audit.get("needs_user_confirmation")) + flags)
    candidate["honesty_audit"] = audit
    candidate["details_to_confirm"] = _dedupe_case_insensitive(_as_list(candidate.get("details_to_confirm")) + flags)
    return candidate


def transform_structured_resume_for_job_json(source_data: dict, job_description: str, update_notes: str, target_country: str, output_language: str) -> dict:
    """Step 2 of the anti-drift pipeline: transform only editable fields, keep facts protected."""
    source_data = validate_resume_dates_and_sections(source_data or {})
    protected = _protected_resume_facts(source_data)
    prompt = f"""
You are WorkZo's anti-drift CV transformation engine.

INPUT STRUCTURED CV JSON:
{json.dumps(source_data, ensure_ascii=False, indent=2)}

PROTECTED FACTS - do not change these values:
{json.dumps(protected, ensure_ascii=False, indent=2)}

TARGET COUNTRY: {target_country}
OUTPUT LANGUAGE: {output_language}
JOB DESCRIPTION:
{(job_description or 'No job description provided.')[:9000]}

USER UPDATE NOTES:
{(update_notes or 'No extra update notes provided.')[:3000]}

TASK:
Update only the professional_summary, bullets, core_skills ordering, tools_technologies ordering, and suggested_additions.

HARD CONSTRAINTS:
- Do NOT change full_name, phone, email, location, LinkedIn, company names, role titles, work dates, education institutions, education dates, degrees, or languages unless the user update notes explicitly provide the correction.
- Do NOT add a missing JD skill to the final CV unless it is clearly supported by the source CV or update notes.
- Put missing JD requirements into suggested_additions only.
- Keep each date attached to its original job/education item.
- Do not output markdown, tables, commentary, or visual columns.
- Return ONLY valid JSON in the same WorkZo schema.
- Include honesty_audit with rephrased_terms, omitted_missing_jd_requirements, and needs_user_confirmation.
"""
    raw = run_ai_prompt(
        prompt,
        system_addition="Return only valid JSON. You may improve wording, but factual fields are locked by the protected facts object.",
        force_language="English",
        json_mode=True,
    )
    obj = _json_extract_object(raw)
    if not isinstance(obj, dict) or not obj:
        return source_data
    obj = _reinject_protected_resume_facts(obj, protected)
    obj = validate_generated_resume_against_source(source_data, obj)
    return obj


def render_structured_cv_review(target_country: str, user_status: str) -> None:
    """Review screen shown after upload before WorkZo saves cv_text."""
    data = st.session_state.get("pending_structured_cv_json") or st.session_state.get("structured_cv_json") or {}
    if not isinstance(data, dict):
        data = {}
    contact = data.get("contact", {}) if isinstance(data.get("contact"), dict) else {}

    st.markdown("### Review what WorkZo understood from your CV")
    st.caption("Your PDF layout may be two-column/table-style. WorkZo now extracts facts, lets you correct them, and then rebuilds a clean ATS-friendly CV from the approved sections.")

    def join_list(value):
        if isinstance(value, list):
            out=[]
            for item in value:
                if isinstance(item, dict):
                    out.append(json.dumps(item, ensure_ascii=False))
                else:
                    out.append(str(item))
            return "\n".join(out)
        return str(value or "")

    def experience_to_text(items):
        lines=[]
        if isinstance(items, dict):
            items=[items]
        for job in items or []:
            if isinstance(job, dict):
                header=" | ".join([str(job.get(k) or "").strip() for k in ["title","company","dates"] if str(job.get(k) or "").strip()])
                if header: lines.append(header)
                for b in _as_list(job.get("bullets") or job.get("achievements") or job.get("responsibilities")):
                    lines.append(f"- {b}")
                lines.append("")
            else:
                lines.append(str(job))
        return "\n".join(lines).strip()

    def projects_to_text(items):
        lines=[]
        if isinstance(items, dict):
            items=[items]
        for pr in items or []:
            if isinstance(pr, dict):
                name=str(pr.get("name") or pr.get("title") or "Project").strip()
                if name: lines.append(name)
                for b in _as_list(pr.get("bullets") or pr.get("description") or pr.get("details")):
                    lines.append(f"- {b}")
                lines.append("")
            else:
                lines.append(str(pr))
        return "\n".join(lines).strip()

    def education_to_text(items):
        lines=[]
        if isinstance(items, dict):
            items=[items]
        for ed in items or []:
            if isinstance(ed, dict):
                line=" | ".join([str(ed.get(k) or "").strip() for k in ["degree","institution","dates","year"] if str(ed.get(k) or "").strip()])
                if line: lines.append(line)
            else:
                lines.append(str(ed))
        return "\n".join(lines).strip()

    with st.form("structured_cv_review_form"):
        c1, c2 = st.columns(2)
        with c1:
            full_name = st.text_input("Full name", value=str(data.get("full_name") or data.get("name") or ""))
            target_role = st.text_input("Target/current role", value=str(data.get("target_role") or data.get("current_role") or data.get("headline") or ""))
            phone = st.text_input("Phone", value=str(contact.get("phone") or data.get("phone") or ""))
            email = st.text_input("Email", value=str(contact.get("email") or data.get("email") or ""))
        with c2:
            location = st.text_input("Location", value=str(contact.get("location") or data.get("location") or ""))
            linkedin = st.text_input("LinkedIn", value=str(contact.get("linkedin") or data.get("linkedin") or ""))
            languages = st.text_area("Languages", value=join_list(data.get("languages")), height=80)
            certifications = st.text_area("Certifications", value=join_list(data.get("certifications")), height=80)

        summary = st.text_area("Professional summary", value=str(data.get("professional_summary") or data.get("summary") or ""), height=120)
        skills = st.text_area("Core skills", value=join_list(data.get("core_skills") or data.get("skills")), height=120)
        tools = st.text_area("Tools / technologies", value=join_list(data.get("tools_technologies") or data.get("tools")), height=100)
        experience = st.text_area("Work experience", value=experience_to_text(data.get("work_experience") or data.get("experience")), height=220)
        projects = st.text_area("Projects", value=projects_to_text(data.get("projects")), height=180)
        education = st.text_area("Education", value=education_to_text(data.get("education")), height=120)
        details_to_confirm = st.text_area("Details to confirm", value=join_list(data.get("details_to_confirm")), height=80)

        c_approve, c_back = st.columns(2)
        approve = c_approve.form_submit_button("✓ Approve and build my clean CV", use_container_width=True)
        back = c_back.form_submit_button("Back Re-upload / edit setup", use_container_width=True)

    if back:
        st.session_state.cv_review_required = False
        st.session_state.pending_structured_cv_json = {}
        st.rerun()

    if approve:
        approved = {
            "full_name": full_name,
            "target_role": target_role,
            "contact": {"phone": phone, "email": email, "location": location, "linkedin": linkedin},
            "professional_summary": summary,
            "core_skills": [x.strip(" -•") for x in skills.splitlines() if x.strip(" -•")],
            "tools_technologies": [x.strip(" -•") for x in tools.splitlines() if x.strip(" -•")],
            "work_experience": parse_experience_text_to_items(experience),
            "projects": parse_projects_text_to_items(projects),
            "education": parse_education_text_to_items(education),
            "certifications": [x.strip(" -•") for x in certifications.splitlines() if x.strip(" -•")],
            "languages": [x.strip(" -•") for x in languages.splitlines() if x.strip(" -•")],
            "details_to_confirm": [x.strip(" -•") for x in details_to_confirm.splitlines() if x.strip(" -•")],
        }
        clean_cv = _format_structured_resume_profile(approved)
        if not clean_cv.strip():
            st.warning("Please keep at least your name, summary, skills, or experience before continuing.")
            return
        st.session_state.structured_cv_json = approved
        st.session_state.structured_cv_profile = clean_cv
        st.session_state.clean_structured_cv_text = clean_cv
        st.session_state.cv_text = clean_cv
        st.session_state.cv_review_required = False
        st.session_state.pending_structured_cv_json = {}
        st.session_state.onboarding_complete = True
        st.session_state.country = target_country or st.session_state.get("country", "")
        st.session_state.migration_country = target_country or st.session_state.get("migration_country", "") or st.session_state.get("country", "")
        track_event("cv_structured_review_approved", "Onboarding", {"target_country": st.session_state.get("migration_country", "")})
        with st.spinner("Preparing dashboard from approved CV profile..."):
            analyze_resume_dashboard_stable(st.session_state.cv_text, force_refresh=True)
        sync_navigation_state("dashboard")
        st.rerun()


def render_inline_structured_cv_editor(target_country: str, user_status: str) -> None:
    """Editable master resume source used by CV templates, scoring, and Improve/Update CV."""
    data = st.session_state.get("structured_cv_json") or st.session_state.get("pending_structured_cv_json") or {}
    if not isinstance(data, dict) or not data:
        raw_source = st.session_state.get("raw_cv_extraction") or st.session_state.get("cv_text") or ""
        if raw_source and len(str(raw_source).strip()) > 80:
            with st.spinner("Building editable resume sections from your CV..."):
                data = extract_structured_resume_json(str(raw_source), target_country, user_status)
            st.session_state.structured_cv_json = data if isinstance(data, dict) else {}
        else:
            data = {}
    contact = data.get("contact", {}) if isinstance(data.get("contact"), dict) else {}

    def join_list(value):
        if isinstance(value, list):
            return "\n".join([str(x).strip() for x in value if str(x).strip()])
        return str(value or "")

    def experience_to_text(items):
        lines=[]
        if isinstance(items, dict):
            items=[items]
        for job in items or []:
            if isinstance(job, dict):
                header=" | ".join([str(job.get(k) or "").strip() for k in ["title","company","dates"] if str(job.get(k) or "").strip()])
                if header:
                    lines.append(header)
                for b in _as_list(job.get("bullets") or job.get("achievements") or job.get("responsibilities")):
                    lines.append(f"- {b}")
                lines.append("")
            else:
                lines.append(str(job))
        return "\n".join(lines).strip()

    def projects_to_text(items):
        lines=[]
        if isinstance(items, dict):
            items=[items]
        for pr in items or []:
            if isinstance(pr, dict):
                name=str(pr.get("name") or pr.get("title") or "Project").strip()
                if name:
                    lines.append(name)
                for b in _as_list(pr.get("bullets") or pr.get("description") or pr.get("details")):
                    lines.append(f"- {b}")
                lines.append("")
            else:
                lines.append(str(pr))
        return "\n".join(lines).strip()

    def education_to_text(items):
        lines=[]
        if isinstance(items, dict):
            items=[items]
        for ed in items or []:
            if isinstance(ed, dict):
                line=" | ".join([str(ed.get(k) or "").strip() for k in ["degree","institution","dates","year"] if str(ed.get(k) or "").strip()])
                if line:
                    lines.append(line)
            else:
                lines.append(str(ed))
        return "\n".join(lines).strip()

    with st.expander(ui_label("Review / edit resume sections used by the template"), expanded=True):
        st.caption(ui_label("This is the master resume source. When you change and save it here, the CV template, dashboard score, ATS score, and job tools use the updated version."))
        with st.form("inline_structured_cv_editor_form_v112"):
            c1, c2 = st.columns(2)
            with c1:
                full_name = st.text_input(ui_label("Full name"), value=str(data.get("full_name") or data.get("name") or ""), key="inline_cv_full_name_v112")
                target_role = st.text_input(ui_label("Target/current role"), value=str(data.get("target_role") or data.get("current_role") or data.get("headline") or ""), key="inline_cv_target_role_v112")
                phone = st.text_input(ui_label("Phone"), value=str(contact.get("phone") or data.get("phone") or ""), key="inline_cv_phone_v112")
                email = st.text_input(ui_label("Email"), value=str(contact.get("email") or data.get("email") or ""), key="inline_cv_email_v112")
            with c2:
                location = st.text_input(ui_label("Location"), value=str(contact.get("location") or data.get("location") or ""), key="inline_cv_location_v112")
                linkedin = st.text_input(ui_label("LinkedIn"), value=str(contact.get("linkedin") or data.get("linkedin") or ""), key="inline_cv_linkedin_v112")
                languages = st.text_area(ui_label("Languages"), value=join_list(data.get("languages")), height=80, key="inline_cv_languages_v112")
                certifications = st.text_area(ui_label("Certifications"), value=join_list(data.get("certifications")), height=80, key="inline_cv_certs_v112")
            summary = st.text_area(ui_label("Professional summary"), value=str(data.get("professional_summary") or data.get("summary") or ""), height=110, key="inline_cv_summary_v112")
            skills = st.text_area(ui_label("Core skills"), value=join_list(data.get("core_skills") or data.get("skills")), height=100, key="inline_cv_skills_v112")
            tools = st.text_area(ui_label("Tools / technologies"), value=join_list(data.get("tools_technologies") or data.get("tools")), height=90, key="inline_cv_tools_v112")
            experience = st.text_area(ui_label("Work experience fallback text"), value=experience_to_text(data.get("work_experience") or data.get("experience")), height=120, key="inline_cv_experience_v112")
            st.caption(ui_label("Recommended: edit each job in this table so dates stay attached to the correct company."))
            experience_rows = st.data_editor(
                _as_editor_rows(data.get("work_experience") or data.get("experience"), "experience"),
                num_rows="dynamic",
                use_container_width=True,
                key="inline_cv_experience_table_v113",
            )
            projects = st.text_area(ui_label("Projects fallback text"), value=projects_to_text(data.get("projects")), height=100, key="inline_cv_projects_v112")
            project_rows = st.data_editor(
                _as_editor_rows(data.get("projects"), "project"),
                num_rows="dynamic",
                use_container_width=True,
                key="inline_cv_projects_table_v113",
            )
            education = st.text_area(ui_label("Education fallback text"), value=education_to_text(data.get("education")), height=80, key="inline_cv_education_v112")
            education_rows = st.data_editor(
                _as_editor_rows(data.get("education"), "education"),
                num_rows="dynamic",
                use_container_width=True,
                key="inline_cv_education_table_v113",
            )
            save_master = st.form_submit_button(ui_label("Save and update CV template"), use_container_width=True)

        if save_master:
            approved = {
                "full_name": full_name,
                "target_role": target_role,
                "contact": {"phone": phone, "email": email, "location": location, "linkedin": linkedin},
                "professional_summary": summary,
                "core_skills": [x.strip(" -•") for x in skills.splitlines() if x.strip(" -•")],
                "tools_technologies": [x.strip(" -•") for x in tools.splitlines() if x.strip(" -•")],
                "work_experience": _rows_to_experience_items(experience_rows) or parse_experience_text_to_items(experience),
                "projects": _rows_to_project_items(project_rows) or parse_projects_text_to_items(projects),
                "education": _rows_to_education_items(education_rows) or parse_education_text_to_items(education),
                "certifications": [x.strip(" -•") for x in certifications.splitlines() if x.strip(" -•")],
                "languages": [x.strip(" -•") for x in languages.splitlines() if x.strip(" -•")],
                "details_to_confirm": [],
            }
            clean_cv = _format_structured_resume_profile(approved)
            if not clean_cv.strip():
                st.warning(ui_label("Please keep at least your name, summary, skills, or experience before saving."))
            else:
                st.session_state.structured_cv_json = approved
                st.session_state.structured_cv_profile = clean_cv
                st.session_state.clean_structured_cv_text = clean_cv
                st.session_state.cv_text = clean_cv
                st.session_state.improved_cv_text_v92 = clean_cv
                st.session_state.improved_cv_edit_buffer_v92 = clean_cv
                st.session_state.pop("dashboard_cv_hash", None)
                analyze_resume_dashboard_stable(clean_cv, force_refresh=True)
                st.success(ui_label("Saved. The preview/template now uses this updated resume."))
                st.rerun()

def build_clean_cv_from_messy_extraction(raw_cv_text: str, target_country: str, user_status: str) -> str:
    """Turn messy PDF extraction into a clean structured CV.

    Extraction is now only fact capture. WorkZo ignores the PDF order, asks AI to classify facts
    into sections, and rebuilds a clean resume from those sections.
    """
    cleaned_raw = clean_cv_text(raw_cv_text)
    if not cleaned_raw.strip():
        return ""
    if len(cleaned_raw) < 250:
        return cleaned_raw

    data = extract_structured_resume_json(cleaned_raw, target_country, user_status)
    standardized = _format_structured_resume_profile(data)
    if standardized and len(standardized) > 350:
        try:
            st.session_state["structured_cv_json"] = data
            st.session_state["structured_cv_profile"] = standardized
            st.session_state["clean_structured_cv_text"] = standardized
        except Exception:
            pass
        return standardized
    return cleaned_raw

def infer_relevant_roles_from_cv(cv_text: str) -> List[str]:
    text = (cv_text or "").lower()
    roles: List[str] = []
    def add(role: str):
        if role not in roles:
            roles.append(role)
    if any(x in text for x in ["technical support", "it support", "service desk", "helpdesk", "troubleshoot", "tickets"]):
        add("IT Support Specialist")
        add("Technical Support Engineer")
        add("Service Desk Analyst")
        add("Customer Support Specialist")
    if any(x in text for x in ["sql", "python", "tableau", "power bi", "data analysis", "data visualization", "bootcamp"]):
        add("Junior Data Analyst")
        add("Business Intelligence Analyst")
        add("Reporting Analyst")
    if any(x in text for x in ["customer success", "onboarding", "saas", "client"]):
        add("Customer Success Associate")
    return roles[:6]

def build_job_matching_profile(cv_text: str) -> str:
    cleaned = clean_cv_text(cv_text)
    roles = infer_relevant_roles_from_cv(cleaned)
    skill_bank = ["Python", "SQL", "Tableau", "Power BI", "Excel", "Data Visualization", "Machine Learning", "Technical Support", "IT Support", "Service Desk", "Customer Support", "ITSM", "Zoho", "ManageEngine", "GCP", "Matplotlib", "Seaborn"]
    found_skills = [sk for sk in skill_bank if sk.lower() in cleaned.lower()]
    summary_bits = []
    if "technical support" in cleaned.lower() or "it support" in cleaned.lower():
        summary_bits.append("Experience in technical support, customer-facing troubleshooting, ticket handling, and user support.")
    if any(x in cleaned.lower() for x in ["data science", "data analyst", "sql", "python", "tableau"]):
        summary_bits.append("Data/analytics transition profile with Python, SQL, visualization, and bootcamp/project experience.")
    if not summary_bits:
        summary_bits.append(cleaned[:500])
    lines = ["MATCH-READY CV SUMMARY", ""]
    if roles:
        lines += ["Target roles that fit this profile:", *[f"- {r}" for r in roles[:5]], ""]
    lines += ["Professional profile:", *[f"- {b}" for b in summary_bits], ""]
    if found_skills:
        lines += ["Key skills/tools:", "- " + ", ".join(found_skills[:12]), ""]
    lines += ["Note:", "- This clean summary is used only for matching jobs. It avoids messy PDF line extraction."]
    return "\n".join(lines).strip()

# =========================================================
# SESSION STATE
# =========================================================
country_options = get_country_options()
language_options = get_language_options()
geo_country_default, geo_language_default = get_geo_defaults()

defaults = {
    "page": "landing",
    "onboarding_complete": False,
    "country": geo_country_default if geo_country_default in country_options else "Germany",
    "preferred_language": geo_language_default if geo_language_default in language_options else "English",
    "ui_language": geo_language_default if geo_language_default in language_options else "English",
    "response_language": geo_language_default if geo_language_default in language_options else "English",
    "user_status": "Career changer",
    "migration_country": geo_country_default if geo_country_default in country_options else "Germany",
    "career_goal": "",
    "cv_mode": "Upload CV",
    "cv_text": "",
    "dashboard_action": "Dashboard",
    "nav_page": "dashboard",

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
            "content": txt("workobot_intro") if "workobot_intro" in UI_TEXT.get(ui_lang(), {}) else "Hi, I'm Work-O-Bot. I can help with interview prep, career communication, and skill gap guidance."
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

init_beta_analytics()
track_event("app_open", "App")

# =========================================================
# HELPERS
# =========================================================
def google_search_url(query: str) -> str:
    return "https://www.google.com/search?q=" + urllib.parse.quote(query)

def _clean_pdf_extraction_noise(text: str) -> str:
    """Clean common PDF extraction artifacts before AI profile building.

    Keep this light: aggressive cleanup can add spaces or break dates.
    The AI structured-profile step rebuilds the CV after this.
    """
    if not text:
        return ""
    text = text.replace("\x00", " ")
    replacements = {
        "in ternal": "internal", "in tegration": "integration", "in tegrations": "integrations",
        "in to": "into", "in dian": "Indian", "for m": "form", "for ms": "forms",
        "You Tube": "YouTube", "Text Blob": "TextBlob", "My SQL": "MySQL",
        "Lang Cha in": "LangChain", "Manage Engine": "ManageEngine", "Service Desk Plus": "ServiceDesk Plus",
        "Bachelors": "Bachelor's", "Enginner": "Engineer", "Linked in": "LinkedIn", "linked in": "LinkedIn",
        "Specialistandaspiring": "Specialist and aspiring", "Detail-orientedIT": "Detail-oriented IT",
    }
    for a, b in replacements.items():
        text = re.sub(re.escape(a), b, text, flags=re.IGNORECASE)

    # Fix spaced-out ALL CAPS headings/names only. Do not split normal CamelCase words.
    def _join_spaced_caps(match):
        return match.group(0).replace(" ", "")
    text = re.sub(r"(?:\b[A-Z]\s+){3,}[A-Z]\b", _join_spaced_caps, text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return clean_cv_text(text)


def _pdfminer_extract_candidate(uploaded_file) -> str:
    """Use pdfminer.six as the primary extraction engine for PDFs.

    It is often better than PyMuPDF for designed CVs where words get split or
    sidebar dates get mixed into the main content.
    """
    if pdfminer_extract_text is None or LAParams is None:
        return ""
    try:
        data = uploaded_file.getvalue()
    except Exception:
        try:
            uploaded_file.seek(0)
            data = uploaded_file.read()
        except Exception:
            return ""
    candidates = []
    for params in [
        LAParams(line_margin=0.35, word_margin=0.10, char_margin=2.0, boxes_flow=None),
        LAParams(line_margin=0.25, word_margin=0.05, char_margin=1.5, boxes_flow=0.0),
        LAParams(line_margin=0.50, word_margin=0.15, char_margin=2.5, boxes_flow=0.5),
    ]:
        try:
            t = pdfminer_extract_text(BytesIO(data), laparams=params) or ""
            t = _clean_pdf_extraction_noise(t)
            if t.strip():
                candidates.append(t)
        except Exception:
            pass
    return max(candidates, key=_score_extracted_cv_text) if candidates else ""

def _score_extracted_cv_text(text: str) -> int:
    """Heuristic score for choosing the richest PDF extraction candidate."""
    if not text:
        return 0
    lower = text.lower()
    score = len(re.findall(r"[a-zA-Z0-9@.+#/-]", text))
    for kw in ["summary", "profile", "experience", "education", "skills", "projects", "languages", "python", "sql", "engineer", "analyst", "linkedin", "@"]:
        if kw in lower:
            score += 350
    score -= len(re.findall(r"\b[a-zA-Z]\s+[a-zA-Z]\b", text)) * 8
    return score


def _pymupdf_block_extract(uploaded_file) -> str:
    """Use PyMuPDF blocks to better handle two-column/table resumes."""
    if fitz is None:
        return ""
    try:
        data = uploaded_file.getvalue()
    except Exception:
        try:
            uploaded_file.seek(0)
            data = uploaded_file.read()
        except Exception:
            return ""
    try:
        doc = fitz.open(stream=data, filetype="pdf")
    except Exception:
        return ""
    pages_text = []
    try:
        for page in doc:
            blocks = page.get_text("blocks") or []
            clean_blocks = []
            width = float(page.rect.width or 1)
            for b in blocks:
                if len(b) < 5:
                    continue
                x0, y0, x1, y1, txt = b[:5]
                txt = _clean_pdf_extraction_noise(str(txt or "").strip())
                if txt:
                    clean_blocks.append((float(x0), float(y0), float(x1), float(y1), txt))
            if not clean_blocks:
                continue
            # Row reading candidate.
            by_rows = sorted(clean_blocks, key=lambda z: (round(z[1] / 8) * 8, z[0]))
            row_text = "\n".join(z[4] for z in by_rows)
            # Column-aware candidate. Designed CVs usually have sidebars; main column should come first.
            left = [z for z in clean_blocks if (z[0] + z[2]) / 2 < width * 0.43]
            right = [z for z in clean_blocks if (z[0] + z[2]) / 2 >= width * 0.43]
            left_text = "\n".join(z[4] for z in sorted(left, key=lambda z: (z[1], z[0])))
            right_text = "\n".join(z[4] for z in sorted(right, key=lambda z: (z[1], z[0])))
            column_text = "\n".join([x for x in [right_text, left_text] if x.strip()])
            raw_text = page.get_text("text") or ""
            pages_text.append(max([row_text, column_text, raw_text], key=_score_extracted_cv_text))
    finally:
        try:
            doc.close()
        except Exception:
            pass
    return _clean_pdf_extraction_noise("\n\n".join(pages_text))


def _pdfplumber_extract_candidates(uploaded_file) -> list:
    candidates_all = []
    try:
        uploaded_file.seek(0)
    except Exception:
        pass
    try:
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                page_candidates = []
                for kwargs in [
                    {"x_tolerance": 1, "y_tolerance": 3, "layout": True},
                    {"x_tolerance": 2, "y_tolerance": 4},
                    {"x_tolerance": 3, "y_tolerance": 5},
                ]:
                    try:
                        t = page.extract_text(**kwargs) or ""
                        if t.strip():
                            page_candidates.append(t)
                    except Exception:
                        pass
                try:
                    tables = page.extract_tables() or []
                    table_text = []
                    for table in tables:
                        for row in table or []:
                            cells = [str(c).strip() for c in (row or []) if c and str(c).strip()]
                            if cells:
                                table_text.append(" | ".join(cells))
                    if table_text:
                        page_candidates.append("\n".join(table_text))
                except Exception:
                    pass
                if page_candidates:
                    candidates_all.append(max(page_candidates, key=_score_extracted_cv_text))
    except Exception:
        pass
    return [_clean_pdf_extraction_noise("\n\n".join(candidates_all))] if candidates_all else []


def extract_pdf_text(uploaded_file) -> str:
    """Extract PDF resume text using pdfminer.six first, then pdfplumber/PyMuPDF fallback.

    WorkZo only uses extraction to capture facts; the AI profile builder then
    rebuilds a clean, structured CV instead of preserving messy PDF layout.
    """
    candidates = []
    miner_text = _pdfminer_extract_candidate(uploaded_file)
    if miner_text.strip():
        candidates.append(miner_text)
    candidates.extend(_pdfplumber_extract_candidates(uploaded_file))
    pm_text = _pymupdf_block_extract(uploaded_file)
    if pm_text.strip():
        candidates.append(pm_text)
    candidates = [c for c in candidates if c and c.strip()]
    if not candidates:
        return ""
    best = max(candidates, key=_score_extracted_cv_text)
    return _clean_pdf_extraction_noise(best)



# =========================================================
# WorkZo v9 schema hardening: no raw dict strings in Projects
# =========================================================
def workzo_v9_project_item(item):
    import ast, json, re
    if isinstance(item, str):
        raw = item.strip()
        if raw.startswith('{') and raw.endswith('}'):
            try:
                item = ast.literal_eval(raw)
            except Exception:
                try:
                    item = json.loads(raw)
                except Exception:
                    return {"name": re.sub(r"[{}'\"]", "", raw)[:90], "bullets": []}
        else:
            return {"name": raw.strip(' -•'), "bullets": []}
    if isinstance(item, dict):
        name = item.get('name') or item.get('title') or item.get('project') or ''
        bullets = item.get('bullets') or item.get('description') or []
        if isinstance(name, str) and name.strip().startswith('{') and name.strip().endswith('}'):
            try:
                inner = ast.literal_eval(name.strip())
                if isinstance(inner, dict):
                    name = inner.get('name') or inner.get('title') or name
                    bullets = inner.get('bullets') or bullets
            except Exception:
                pass
        if isinstance(bullets, str):
            bullets = [x.strip(' -•') for x in bullets.replace(';','\n').splitlines() if x.strip()]
        elif not isinstance(bullets, list):
            bullets = [str(bullets)] if bullets else []
        return {"name": str(name).strip(), "bullets": [str(x).strip(' -•') for x in bullets if str(x).strip()]}
    return {"name": str(item), "bullets": []}

try:
    _old_parse_projects_text_to_items = parse_projects_text_to_items
    def parse_projects_text_to_items(text: str) -> list:
        items = _old_parse_projects_text_to_items(text)
        return [workzo_v9_project_item(x) for x in (items or [])]
except Exception:
    pass

try:
    _old_validate_resume_dates_and_sections = validate_resume_dates_and_sections
    def validate_resume_dates_and_sections(data: dict) -> dict:
        data = _old_validate_resume_dates_and_sections(data or {})
        data['projects'] = [workzo_v9_project_item(x) for x in (data.get('projects') or [])]
        return data
except Exception:
    pass
