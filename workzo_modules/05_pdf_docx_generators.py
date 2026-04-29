
# =========================================================
# WorkZo split-module missing imports
# Added by fix_workzo_split_modules.py
# =========================================================
from __future__ import annotations
import os
import re
import html
import json
import ast
import shutil
import tempfile
import subprocess
from pathlib import Path
from io import BytesIO
from typing import Dict, List, Optional, Tuple, Any

try:
    import streamlit as st
except Exception:
    st = None

try:
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
except Exception:
    SimpleDocTemplate = Paragraph = Spacer = Table = TableStyle = KeepTogether = None
    A4 = None
    getSampleStyleSheet = ParagraphStyle = None
    colors = None
# =========================================================

# WorkZo modular split v139/v140 - CLEANED
# Stability/router + CV template mixer fix extracted from app_workzo_v139_cv_template_mixer_fix.py
# WorkZo v135/v139: anti-drift PDF grid + strict job-location bouncer
# This file is safe to import in a modular project.
# =========================================================


import re
import html
from io import BytesIO
from typing import Any, Dict, List, Optional

try:
    import streamlit as st
except Exception:
    st = None

try:
    from reportlab.platypus import (
        SimpleDocTemplate,
        Table,
        TableStyle,
        Paragraph,
        Spacer,
        KeepTogether,
    )
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
except Exception:
    SimpleDocTemplate = None
    Table = None
    TableStyle = None
    Paragraph = None
    Spacer = None
    KeepTogether = None
    A4 = None
    getSampleStyleSheet = None
    ParagraphStyle = None
    colors = None

# -----------------------------------------------------------------------------
# Safe fallbacks. In the full WorkZo app these names may already exist; we do not
# override them. These fallbacks prevent NameError crashes in the modular version.
# -----------------------------------------------------------------------------
if "_as_list" not in globals():
    def _as_list(value: Any) -> List[Any]:
        if value is None:
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, tuple):
            return list(value)
        if isinstance(value, str):
            return [x.strip() for x in re.split(r"[\n;]+", value) if x.strip()]
        return [value]

if "_dedupe_case_insensitive" not in globals():
    def _dedupe_case_insensitive(items: List[Any]) -> List[str]:
        seen = set()
        out = []
        for item in _as_list(items):
            text = str(item or "").strip()
            key = text.casefold()
            if text and key not in seen:
                seen.add(key)
                out.append(text)
        return out

if "_normalize_date_text" not in globals():
    def _normalize_date_text(value: Any) -> str:
        text = str(value or "").strip()
        text = re.sub(r"\s+", " ", text)
        text = text.replace("–", "-").replace("—", "-")
        return text

if "resolve_template_style" not in globals():
    def resolve_template_style(template_name: str = "ATS Resume") -> str:
        return template_name or "ATS Resume"

if "sanitize_pdf_text" not in globals():
    def sanitize_pdf_text(text: str) -> str:
        return str(text or "")

if "clean_generated_cv_text_for_template" not in globals():
    def clean_generated_cv_text_for_template(text: str) -> str:
        return str(text or "")

if "build_clean_cv_text_from_structured" not in globals():
    def build_clean_cv_text_from_structured(data: Dict[str, Any]) -> str:
        if not isinstance(data, dict):
            return ""
        parts = []
        for key in ["full_name", "target_role", "professional_summary"]:
            if data.get(key):
                parts.append(str(data[key]))
        for job in _as_list(data.get("work_experience")):
            if isinstance(job, dict):
                parts.append(" ".join(str(job.get(k, "")) for k in ["title", "company", "dates"]))
                parts.extend(str(b) for b in _as_list(job.get("bullets")))
        return "\n".join(x for x in parts if str(x).strip())

if "_coerce_structured_resume_schema" not in globals():
    def _coerce_structured_resume_schema(data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(data, dict):
            return {}
        if any(k in data for k in ["full_name", "work_experience", "core_skills", "professional_summary"]):
            return data
        personal = data.get("personal_info") or data.get("contact") or {}
        exp = []
        for item in _as_list(data.get("experience") or data.get("work_experience")):
            if isinstance(item, dict):
                exp.append({
                    "title": item.get("title") or item.get("role") or "",
                    "company": item.get("company") or "",
                    "dates": item.get("dates") or " - ".join([str(x) for x in [item.get("start_date"), item.get("end_date")] if x]),
                    "bullets": item.get("bullets") or item.get("achievements") or item.get("responsibilities") or [],
                })
        edu = []
        for item in _as_list(data.get("education")):
            if isinstance(item, dict):
                edu.append({
                    "degree": item.get("degree") or item.get("qualification") or "",
                    "institution": item.get("institution") or item.get("school") or item.get("university") or item.get("college") or "",
                    "dates": item.get("dates") or " - ".join([str(x) for x in [item.get("start_year"), item.get("end_year")] if x]),
                })
        return {
            "full_name": personal.get("name") or data.get("name") or data.get("full_name") or "",
            "target_role": personal.get("title") or data.get("title") or data.get("target_role") or "Professional CV",
            "contact": {
                "phone": personal.get("phone") or data.get("phone") or "",
                "email": personal.get("email") or data.get("email") or "",
                "location": personal.get("location") or data.get("location") or "",
                "linkedin": personal.get("linkedin") or data.get("linkedin") or "",
            },
            "professional_summary": data.get("summary") or data.get("professional_summary") or "",
            "core_skills": data.get("skills") or data.get("core_skills") or [],
            "tools_technologies": data.get("tools_technologies") or [],
            "work_experience": exp,
            "education": edu,
            "projects": data.get("projects") or [],
            "languages": data.get("languages") or [],
            "certifications": data.get("certifications") or [],
        }

if "validate_resume_dates_and_sections" not in globals():
    def validate_resume_dates_and_sections(data: Dict[str, Any]) -> Dict[str, Any]:
        data = _coerce_structured_resume_schema(data or {})
        if not data:
            return {}
        data.setdefault("contact", {})
        data.setdefault("work_experience", [])
        data.setdefault("education", [])
        data.setdefault("core_skills", [])
        data.setdefault("tools_technologies", [])
        data.setdefault("projects", [])
        data.setdefault("languages", [])
        data.setdefault("certifications", [])
        for job in data.get("work_experience", []):
            if isinstance(job, dict):
                job["dates"] = _normalize_date_text(job.get("dates") or "")
                job["bullets"] = _as_list(job.get("bullets"))
        for ed in data.get("education", []):
            if isinstance(ed, dict):
                ed["dates"] = _normalize_date_text(ed.get("dates") or ed.get("year") or "")
        return data

if "_best_cv_sections_for_template" not in globals():
    def _best_cv_sections_for_template(cv_text: str) -> Dict[str, str]:
        return {"header": str(cv_text or "").split("\n", 4)[0] if cv_text else "", "summary": str(cv_text or ""), "skills": "", "experience": "", "education": "", "projects": "", "languages": "", "certifications": ""}

if "parse_experience_text_to_items" not in globals():
    def parse_experience_text_to_items(text: str) -> List[Dict[str, Any]]:
        return [{"company": "", "title": "", "dates": "", "bullets": [x.strip() for x in str(text or "").splitlines() if x.strip()]}] if str(text or "").strip() else []

if "parse_education_text_to_items" not in globals():
    def parse_education_text_to_items(text: str) -> List[Dict[str, Any]]:
        return [{"degree": str(text or "").strip(), "institution": "", "dates": ""}] if str(text or "").strip() else []

if "parse_projects_text_to_items" not in globals():
    def parse_projects_text_to_items(text: str) -> List[Dict[str, Any]]:
        return []

if "build_live_job_queries" not in globals():
    def build_live_job_queries(roles, user_status="", max_queries=10, country_name=""):
        return [str(r) for r in _as_list(roles) if str(r).strip()][:max_queries]
if "fetch_live_jobs_for_germany" not in globals():
    def fetch_live_jobs_for_germany(roles, location="", user_status=""):
        return []
if "fetch_adzuna_jobs" not in globals():
    def fetch_adzuna_jobs(query, country_name="", location="", limit=30):
        return []
if "fetch_remotive_jobs" not in globals():
    def fetch_remotive_jobs(query, location="", limit=20):
        return []
if "sort_jobs_for_user" not in globals():
    def sort_jobs_for_user(jobs, user_status="", roles=None, country_name=""):
        return jobs

# WorkZo modular split v139
# Stability/router + CV template mixer fix extracted from app_workzo_v139_cv_template_mixer_fix.py
# WorkZo v135: anti-drift PDF grid + strict job-location bouncer
# =========================================================
def wz135_pdf_safe_text(text_value: str) -> str:
    """Clean AI/PDF text for ReportLab without destroying normal accented letters."""
    value = str(text_value or "")
    replacements = {
        "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
        "\u2013": "-", "\u2014": "-", "\u2022": "-", "\u00a0": " ",
        "\ufeff": "", "\u200b": "", "\t": " ",
        "Ã¢â‚¬â€œ": "-", "Ã¢â‚¬â€": "-", "Ã¢â‚¬Â¢": "-",
        "â€“": "-", "â€”": "-", "â€¢": "-", "â€˜": "'", "â€™": "'", "â€œ": '"', "â€": '"',
        "Â": "", "�": "",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    # Preserve paragraph boundaries for CV PDFs; collapse spaces within each line only.
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()

# Keep older helper name working, but make it stronger.
def clean_for_pdf_grid(text_value: str) -> str:
    return wz135_pdf_safe_text(text_value)


def _wz135_contact_line(data: dict) -> str:
    contact = data.get("contact") or {}
    return " | ".join([
        wz135_pdf_safe_text(x)
        for x in [contact.get("phone"), contact.get("email"), contact.get("location"), contact.get("linkedin")]
        if str(x or "").strip()
    ])


def _strict_structured_pdf(title: str, structured_data: dict, template_name: str = "ATS Resume", target_country: str = "") -> bytes:
    """WorkZo v135 structural CV renderer.

    Uses strict JSON buckets and nested ReportLab tables:
    - header table accepts only name/title/contact
    - job cards keep company/date/title attached to bullets
    - master grid isolates sidebar from main content
    This prevents education/header leakage, date drift and company-as-bullet issues.
    """
    data = validate_resume_dates_and_sections(_coerce_structured_resume_schema(structured_data or {}))
    if not data:
        raise ValueError("No structured CV data available")

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=28, leftMargin=28, topMargin=24, bottomMargin=24)
    base = getSampleStyleSheet()

    styles = {
        "name": ParagraphStyle("WZ135Name", parent=base["Title"], fontName="Helvetica-Bold", fontSize=23, leading=27, textColor=colors.HexColor("#0f172a"), spaceAfter=2),
        "role": ParagraphStyle("WZ135Role", parent=base["BodyText"], fontName="Helvetica", fontSize=10.5, leading=13, textColor=colors.HexColor("#334155"), spaceAfter=4),
        "contact": ParagraphStyle("WZ135Contact", parent=base["BodyText"], fontName="Helvetica", fontSize=8.4, leading=10.2, textColor=colors.HexColor("#475569"), spaceAfter=4),
        "section": ParagraphStyle("WZ135Section", parent=base["Heading4"], fontName="Helvetica-Bold", fontSize=9.2, leading=11.2, textColor=colors.HexColor("#0f172a"), spaceBefore=7, spaceAfter=5),
        "mini": ParagraphStyle("WZ135Mini", parent=base["BodyText"], fontName="Helvetica-Bold", fontSize=8.9, leading=11.2, textColor=colors.HexColor("#111827"), spaceBefore=3, spaceAfter=2),
        "body": ParagraphStyle("WZ135Body", parent=base["BodyText"], fontName="Helvetica", fontSize=8.75, leading=11.2, textColor=colors.HexColor("#111827"), spaceAfter=3),
        "side": ParagraphStyle("WZ135Side", parent=base["BodyText"], fontName="Helvetica", fontSize=8.3, leading=10.4, textColor=colors.HexColor("#111827"), spaceAfter=2),
        "side_bullet": ParagraphStyle("WZ135SideBullet", parent=base["BodyText"], fontName="Helvetica", fontSize=8.25, leading=10.3, textColor=colors.HexColor("#111827"), leftIndent=8, firstLineIndent=0, spaceAfter=2),
        "bullet": ParagraphStyle("WZ135Bullet", parent=base["BodyText"], fontName="Helvetica", fontSize=8.55, leading=10.9, textColor=colors.HexColor("#111827"), leftIndent=11, firstLineIndent=0, spaceAfter=2),
        "company": ParagraphStyle("WZ135Company", parent=base["Heading4"], fontName="Helvetica-Bold", fontSize=9.4, leading=11.5, textColor=colors.HexColor("#1d4ed8"), spaceAfter=1),
        "dates": ParagraphStyle("WZ135Dates", parent=base["BodyText"], fontName="Helvetica", alignment=2, fontSize=8.15, leading=10.2, textColor=colors.HexColor("#475569"), spaceAfter=1),
        "jobtitle": ParagraphStyle("WZ135JobTitle", parent=base["BodyText"], fontName="Helvetica-Oblique", fontSize=8.7, leading=10.8, textColor=colors.HexColor("#334155"), spaceAfter=3),
        "muted": ParagraphStyle("WZ135Muted", parent=base["BodyText"], fontName="Helvetica", fontSize=8, leading=10, textColor=colors.HexColor("#64748b")),
    }

    def safe_html(value):
        return html.escape(wz135_pdf_safe_text(value))
    def P(value, style):
        return Paragraph(safe_html(value), style)
    def section(label):
        return Paragraph(safe_html(label).upper(), styles["section"])
    def bullets(items, style, limit=18):
        out = []
        for item in _as_list(items)[:limit]:
            val = wz135_pdf_safe_text(str(item or "").strip(" -•\t"))
            if val:
                out.append(Paragraph(html.escape(val), style, bulletText="-"))
        return out or [Paragraph("-", styles["muted"])]

    contact_line = _wz135_contact_line(data)
    role_line = data.get("target_role") or title or "Professional CV"

    header_table = Table([
        [P(data.get("full_name") or "Your Name", styles["name"])],
        [P(role_line, styles["role"])],
        [P(contact_line, styles["contact"]) if contact_line else Paragraph("", styles["contact"])],
    ], colWidths=[doc.width])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 0),
        ("RIGHTPADDING", (0,0), (-1,-1), 0),
        ("TOPPADDING", (0,0), (-1,-1), 0),
        ("BOTTOMPADDING", (0,0), (-1,-1), 2),
    ]))

    sidebar = []
    skills = (data.get("core_skills") or []) + (data.get("tools_technologies") or [])
    sidebar.append(section("Skills"))
    sidebar.extend(bullets(skills, styles["side_bullet"], 22))

    if data.get("languages"):
        sidebar.append(section("Languages"))
        sidebar.extend(bullets(data.get("languages"), styles["side_bullet"], 8))

    sidebar.append(section("Education"))
    for ed in data.get("education") or []:
        if not isinstance(ed, dict):
            continue
        degree = wz135_pdf_safe_text(ed.get("degree") or "")
        institution = wz135_pdf_safe_text(ed.get("institution") or ed.get("school") or "")
        dates = wz135_pdf_safe_text(_normalize_date_text(ed.get("dates") or ed.get("year") or ""))
        if degree:
            sidebar.append(P(degree, styles["mini"]))
        bits = " | ".join([x for x in [institution, dates] if x])
        if bits:
            sidebar.append(P(bits, styles["side"]))
        sidebar.append(Spacer(1, 4))

    if data.get("certifications"):
        sidebar.append(section("Certifications"))
        sidebar.extend(bullets(data.get("certifications"), styles["side_bullet"], 8))

    main = []
    if data.get("professional_summary"):
        main.append(section("Professional Summary"))
        main.append(P(data.get("professional_summary"), styles["body"]))
        main.append(Spacer(1, 6))

    main.append(section("Professional Experience"))
    main_w = doc.width * 0.66 - 24
    for job in data.get("work_experience") or []:
        if not isinstance(job, dict):
            continue
        company = wz135_pdf_safe_text(job.get("company") or "Company")
        dates = wz135_pdf_safe_text(_normalize_date_text(job.get("dates") or ""))
        role = wz135_pdf_safe_text(job.get("title") or job.get("role") or "")
        job_header = Table([
            [Paragraph(html.escape(company), styles["company"]), Paragraph(html.escape(dates), styles["dates"])],
            [Paragraph(html.escape(role), styles["jobtitle"]), ""],
        ], colWidths=[main_w * .68, main_w * .32])
        job_header.setStyle(TableStyle([
            ("VALIGN", (0,0), (-1,-1), "TOP"),
            ("LEFTPADDING", (0,0), (-1,-1), 0),
            ("RIGHTPADDING", (0,0), (-1,-1), 0),
            ("TOPPADDING", (0,0), (-1,-1), 0),
            ("BOTTOMPADDING", (0,0), (-1,-1), 1),
            ("SPAN", (0,1), (1,1)),
        ]))
        job_block = [job_header]
        for b in _as_list(job.get("bullets"))[:7]:
            clean_b = wz135_pdf_safe_text(str(b or "").strip(" -•\t"))
            if clean_b:
                job_block.append(Paragraph(html.escape(clean_b), styles["bullet"], bulletText="-"))
        main.append(KeepTogether(job_block) if KeepTogether is not None else job_block)
        main.append(Spacer(1, 8))

    if data.get("projects"):
        main.append(section("Projects"))
        for pr in data.get("projects")[:4]:
            if not isinstance(pr, dict):
                continue
            block = []
            if pr.get("name"):
                block.append(P(pr.get("name"), styles["mini"]))
            for b in _as_list(pr.get("bullets"))[:4]:
                clean_b = wz135_pdf_safe_text(str(b or "").strip(" -•\t"))
                if clean_b:
                    block.append(Paragraph(html.escape(clean_b), styles["bullet"], bulletText="-"))
            if block:
                main.append(KeepTogether(block) if KeepTogether is not None else block)
                main.append(Spacer(1, 6))

    style_key = resolve_template_style(template_name)
    left_bg = colors.HexColor("#eef2f7")
    if style_key == "Career Pivot":
        left_bg = colors.HexColor("#f3e8ff")
    elif style_key == "Graduate Portfolio":
        left_bg = colors.HexColor("#e0f2fe")
    elif style_key == "Creative Modern":
        left_bg = colors.HexColor("#ecfeff")

    master_grid = Table([[sidebar, main]], colWidths=[doc.width * .34, doc.width * .66])
    master_grid.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (0,0), left_bg),
        ("BACKGROUND", (1,0), (1,0), colors.white),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (0,0), 12),
        ("RIGHTPADDING", (0,0), (0,0), 12),
        ("LEFTPADDING", (1,0), (1,0), 18),
        ("RIGHTPADDING", (1,0), (1,0), 6),
        ("TOPPADDING", (0,0), (-1,-1), 14),
        ("BOTTOMPADDING", (0,0), (-1,-1), 14),
        ("BOX", (0,0), (-1,-1), 0.5, colors.HexColor("#e5e7eb")),
    ]))

    story = [header_table, Table([[""]], colWidths=[doc.width], rowHeights=[1.5], style=TableStyle([("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#1f2937"))])), Spacer(1, 10), master_grid]
    doc.build(story)
    buffer.seek(0)
    out = buffer.getvalue()
    if not out.startswith(b"%PDF"):
        raise ValueError("Invalid PDF")
    return out


def _wz135_is_specific_location(location: str, country_name: str = "") -> bool:
    loc = (location or "").strip().lower()
    country = (country_name or "").strip().lower()
    if not loc:
        return False
    generic = {"remote", "worldwide", "anywhere", "all", "global", "europe", "eu", country, f"anywhere in {country}".strip()}
    return loc not in generic and not loc.startswith("anywhere in ")


def _wz135_location_matches(job: Dict, requested_location: str, country_name: str = "") -> bool:
    """Strict city bouncer for location-specific searches.
    Keeps exact-city matches and remote/worldwide roles only when the user asked remote/anywhere.
    """
    if not _wz135_is_specific_location(requested_location, country_name):
        return True
    requested = (requested_location or "").strip().lower()
    loc_text = str(job.get("location") or "").lower()
    title_text = str(job.get("title") or "").lower()
    summary_text = str(job.get("summary") or "").lower()
    hay = " ".join([loc_text, title_text, summary_text])
    # exact phrase first
    if requested in hay:
        return True
    # allow common comma formats and city tokens for multi-word cities
    tokens = [t for t in re.split(r"[^a-z0-9äöüßáéíóúñ]+", requested) if len(t) >= 3]
    if tokens and all(t in hay for t in tokens):
        return True
    return False


def fetch_live_jobs_global(country_name: str, roles: List[str], location: str = "", user_status: str = "") -> List[Dict]:
    """v135: Live jobs with strict location bouncer and no broad fallback for city-specific searches."""
    results: List[Dict] = []
    country_lower = (country_name or "").strip().lower()
    search_queries = build_live_job_queries(roles, user_status, max_queries=10, country_name=country_name)

    if country_lower == "germany":
        results.extend(fetch_live_jobs_for_germany(roles, location, user_status))

    for query in search_queries:
        results.extend(fetch_adzuna_jobs(query, country_name, location, limit=30))

    # Remotive is remote/global. Only include for broad or remote searches.
    if not _wz135_is_specific_location(location, country_name) or str(location or "").strip().lower() in {"remote", "worldwide", "anywhere"}:
        for query in search_queries[:10]:
            results.extend(fetch_remotive_jobs(query, location, limit=20))

    # Do not silently broaden location for a city query; that is what caused irrelevant locations.
    if not _wz135_is_specific_location(location, country_name) and len(results) < 15 and location and location.strip().lower() != (country_name or "").strip().lower():
        for query in search_queries[:12]:
            results.extend(fetch_adzuna_jobs(query, country_name, "", limit=30))
            results.extend(fetch_remotive_jobs(query, "", limit=20))

    deduped: List[Dict] = []
    seen = set()
    for item in results:
        if not _wz135_location_matches(item, location, country_name):
            continue
        key = (item.get("source", "") + "|" + item.get("title", "") + "|" + item.get("company", "") + "|" + item.get("location", "") + "|" + item.get("url", "")).casefold()
        if key not in seen:
            seen.add(key)
            deduped.append(item)

    return sort_jobs_for_user(deduped, user_status, roles, country_name)[:40]




# =========================================================
# WorkZo v137 STABILITY PATCH - no feature changes
# Purpose: keep one session-state source of truth while preserving the full app.
# This avoids repeated issues caused by old keys and new keys drifting apart.
# =========================================================
def workzo_v137_stabilize_state() -> None:
    """Synchronize CV/JD state without removing any existing feature."""
    try:
        # Prefer the approved structured CV, but do not overwrite with empty values.
        structured = (
            st.session_state.get("structured_cv_json")
            or st.session_state.get("approved_structured_cv_json")
            or st.session_state.get("pending_structured_cv_json")
            or {}
        )
        if isinstance(structured, dict) and structured:
            st.session_state["structured_cv_json"] = structured
            st.session_state["approved_structured_cv_json"] = structured
            # Keep cv_text as a clean display/matching fallback only when current text is empty/raw.
            current_text = str(st.session_state.get("cv_text", "") or "").strip()
            if not current_text or st.session_state.get("cv_text_is_raw", False):
                try:
                    st.session_state["cv_text"] = build_clean_cv_text_from_structured(structured)
                    st.session_state["cv_text_is_raw"] = False
                except Exception:
                    pass

        # Keep the job description available across Understand Job, Improve CV, Prepare, and Job cards.
        jd = (
            st.session_state.get("current_job_description")
            or st.session_state.get("last_understand_job_description")
            or st.session_state.get("last_prepare_job_description")
            or st.session_state.get("improve_cv_for_job_desc")
            or st.session_state.get("job_description")
            or ""
        )
        if str(jd).strip():
            st.session_state["current_job_description"] = jd
            st.session_state["last_understand_job_description"] = jd
            st.session_state["last_prepare_job_description"] = jd
            st.session_state["improve_cv_for_job_desc"] = jd
            st.session_state["job_description"] = jd

        # If user already has data, do not send logo/home back to first intro page.
        if st.session_state.get("cv_text") or st.session_state.get("structured_cv_json") or str(jd).strip():
            st.session_state["onboarding_complete"] = True
    except Exception:
        # Stability patch must never break the app.
        pass


# =========================================================
# WorkZo v139: CV Template Mixer Fix (JSON -> locked ReportLab grid)
# =========================================================
WZ_CV_STRICT_SCHEMA = {
    "personal_info": {"name": "", "title": "", "phone": "", "email": "", "location": "", "linkedin": ""},
    "summary": "",
    "experience": [{"title": "", "company": "", "start_date": "", "end_date": "", "dates": "", "bullets": []}],
    "skills": [], "languages": [],
    "education": [{"degree": "", "school": "", "institution": "", "start_year": "", "end_year": "", "dates": ""}],
    "projects": [], "certifications": [],
}

def wz139_pdf_text(value) -> str:
    """ReportLab-safe text cleaner that removes mojibake and AI smart punctuation."""
    value = str(value or "")
    replacements = {
        "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
        "\u2013": "-", "\u2014": "-", "\u2212": "-", "\u2022": "-",
        "\u00a0": " ", "\ufeff": "", "\u200b": "", "\t": " ",
        "Ã¢â‚¬â€œ": "-", "Ã¢â‚¬Â¢": "-", "â€“": "-", "â€”": "-", "â€¢": "-", "ð\x9f\x8e¤": "", "ð\x9f\x93\x8b": "", "ð\x9f\x94´": "", "ð\x9f\x9f¢": "",
        "â€˜": "'", "â€™": "'", "â€œ": '"', "Â": "", "�": "",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    return re.sub(r"\s+", " ", value).strip()

def wz139_safe_paragraph(value, style):
    return Paragraph(html.escape(wz139_pdf_text(value)), style)

def wz139_date_range(item: dict) -> str:
    if not isinstance(item, dict):
        return ""
    explicit = item.get("dates") or item.get("date") or item.get("year")
    if explicit:
        return wz139_pdf_text(_normalize_date_text(explicit))
    start = item.get("start_date") or item.get("startDate") or item.get("start_year") or ""
    end = item.get("end_date") or item.get("endDate") or item.get("end_year") or ""
    return wz139_pdf_text(_normalize_date_text(" - ".join([str(x) for x in [start, end] if str(x or '').strip()])))

def wz139_structured_data_from_state_or_text(cv_text: str = "") -> dict:
    """Return one clean structured CV object. Text is only fallback, not the main source."""
    candidates = [
        st.session_state.get("structured_cv_json") if hasattr(st, "session_state") else {},
        st.session_state.get("pending_structured_cv_json") if hasattr(st, "session_state") else {},
        st.session_state.get("reviewed_structured_cv_json") if hasattr(st, "session_state") else {},
    ]
    for c in candidates:
        if isinstance(c, dict) and c:
            data = validate_resume_dates_and_sections(_coerce_structured_resume_schema(c))
            if data.get("work_experience") or data.get("education") or data.get("core_skills"):
                return data
    if cv_text:
        sec = _best_cv_sections_for_template(cv_text)
        header = [x.strip() for x in str(sec.get("header", "")).splitlines() if x.strip()]
        fallback = {
            "full_name": header[0] if header else "Your Name",
            "target_role": header[1] if len(header) > 1 else "Professional CV",
            "contact": {"phone": "", "email": "", "location": "", "linkedin": ""},
            "professional_summary": sec.get("summary", ""),
            "core_skills": [re.sub(r"^[-•*]\s*", "", x).strip() for x in str(sec.get("skills", "")).splitlines() if x.strip()],
            "tools_technologies": [],
            "work_experience": parse_experience_text_to_items(sec.get("experience", "")),
            "education": parse_education_text_to_items(sec.get("education", "")),
            "projects": parse_projects_text_to_items(sec.get("projects", "")),
            "languages": [re.sub(r"^[-•*]\s*", "", x).strip() for x in str(sec.get("languages", "")).splitlines() if x.strip()],
            "certifications": [re.sub(r"^[-•*]\s*", "", x).strip() for x in str(sec.get("certifications", "")).splitlines() if x.strip()],
        }
        contact_text = " | ".join(header[2:]) if len(header) > 2 else ""
        email_match = re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", contact_text)
        phone_match = re.search(r"(?:\+\d{1,3}[\s-]?)?(?:\(?\d+\)?[\s-]?){6,}", contact_text)
        linkedin_match = re.search(r"(?:linkedin\.com/[^\s|]+)", contact_text, flags=re.I)
        fallback["contact"]["email"] = email_match.group(0) if email_match else ""
        fallback["contact"]["phone"] = phone_match.group(0) if phone_match else ""
        fallback["contact"]["linkedin"] = linkedin_match.group(0) if linkedin_match else ""
        fallback["contact"]["location"] = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|(?:\+\d{1,3}[\s-]?)?(?:\(?\d+\)?[\s-]?){6,}|(?:linkedin\.com/[^\s|]+)", "", contact_text, flags=re.I).strip(" |,-")
        return validate_resume_dates_and_sections(_coerce_structured_resume_schema(fallback))
    return {}

def _strict_structured_pdf(title: str, structured_data: dict, template_name: str = "ATS Resume", target_country: str = "") -> bytes:
    """v139 locked-grid CV renderer: strict header + sidebar + job cards."""
    if SimpleDocTemplate is None or Table is None or TableStyle is None or colors is None:
        raise ValueError("ReportLab is not available")
    data = validate_resume_dates_and_sections(_coerce_structured_resume_schema(structured_data or {}))
    if not isinstance(data, dict) or not data:
        raise ValueError("No structured CV data available")
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=28, leftMargin=28, topMargin=24, bottomMargin=24)
    base = getSampleStyleSheet()
    styles = {
        "name": ParagraphStyle("WZ139Name", parent=base["Title"], fontName="Helvetica-Bold", fontSize=23, leading=27, textColor=colors.HexColor("#0f172a"), spaceAfter=2),
        "role": ParagraphStyle("WZ139Role", parent=base["BodyText"], fontName="Helvetica", fontSize=10.5, leading=13, textColor=colors.HexColor("#334155"), spaceAfter=4),
        "contact": ParagraphStyle("WZ139Contact", parent=base["BodyText"], fontName="Helvetica", fontSize=8.4, leading=10.2, textColor=colors.HexColor("#475569"), spaceAfter=4),
        "section": ParagraphStyle("WZ139Section", parent=base["Heading4"], fontName="Helvetica-Bold", fontSize=9.2, leading=11.2, textColor=colors.HexColor("#0f172a"), spaceBefore=7, spaceAfter=5),
        "mini": ParagraphStyle("WZ139Mini", parent=base["BodyText"], fontName="Helvetica-Bold", fontSize=8.9, leading=11.2, textColor=colors.HexColor("#111827"), spaceBefore=3, spaceAfter=2),
        "body": ParagraphStyle("WZ139Body", parent=base["BodyText"], fontName="Helvetica", fontSize=8.75, leading=11.2, textColor=colors.HexColor("#111827"), spaceAfter=3),
        "side": ParagraphStyle("WZ139Side", parent=base["BodyText"], fontName="Helvetica", fontSize=8.3, leading=10.4, textColor=colors.HexColor("#111827"), spaceAfter=2),
        "side_bullet": ParagraphStyle("WZ139SideBullet", parent=base["BodyText"], fontName="Helvetica", fontSize=8.25, leading=10.3, textColor=colors.HexColor("#111827"), leftIndent=8, firstLineIndent=0, spaceAfter=2),
        "bullet": ParagraphStyle("WZ139Bullet", parent=base["BodyText"], fontName="Helvetica", fontSize=8.55, leading=10.9, textColor=colors.HexColor("#111827"), leftIndent=11, firstLineIndent=0, spaceAfter=2),
        "company": ParagraphStyle("WZ139Company", parent=base["Heading4"], fontName="Helvetica-Bold", fontSize=9.4, leading=11.5, textColor=colors.HexColor("#1d4ed8"), spaceAfter=1),
        "dates": ParagraphStyle("WZ139Dates", parent=base["BodyText"], fontName="Helvetica", alignment=2, fontSize=8.15, leading=10.2, textColor=colors.HexColor("#475569"), spaceAfter=1),
        "jobtitle": ParagraphStyle("WZ139JobTitle", parent=base["BodyText"], fontName="Helvetica-Oblique", fontSize=8.7, leading=10.8, textColor=colors.HexColor("#334155"), spaceAfter=3),
        "muted": ParagraphStyle("WZ139Muted", parent=base["BodyText"], fontName="Helvetica", fontSize=8, leading=10, textColor=colors.HexColor("#64748b")),
    }
    def P(value, style_name="body"):
        return wz139_safe_paragraph(value, styles[style_name])
    def SEC(label):
        return Paragraph(html.escape(wz139_pdf_text(label).upper()), styles["section"])
    def BL(items, style_name="bullet", limit=18):
        out=[]
        for item in _as_list(items)[:limit]:
            val=wz139_pdf_text(str(item or "").strip(" -•*\t"))
            if val:
                out.append(Paragraph(html.escape(val), styles[style_name], bulletText="-"))
        return out
    contact = data.get("contact") if isinstance(data.get("contact"), dict) else {}
    contact_line = " | ".join([wz139_pdf_text(x) for x in [contact.get("phone"), contact.get("email"), contact.get("location"), contact.get("linkedin")] if str(x or "").strip()])
    header_table = Table([[P(data.get("full_name") or "Your Name", "name")], [P(data.get("target_role") or title or "Professional CV", "role")], [P(contact_line, "contact") if contact_line else Paragraph("", styles["contact"])]], colWidths=[doc.width])
    header_table.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),0),("TOPPADDING",(0,0),(-1,-1),0),("BOTTOMPADDING",(0,0),(-1,-1),2)]))
    sidebar=[]
    skills=_dedupe_case_insensitive(_as_list(data.get("core_skills"))+_as_list(data.get("tools_technologies")))
    if skills:
        sidebar.append(SEC("Skills")); sidebar.extend(BL(skills,"side_bullet",24))
    if data.get("languages"):
        sidebar.append(SEC("Languages")); sidebar.extend(BL(data.get("languages"),"side_bullet",8))
    if data.get("education"):
        sidebar.append(SEC("Education"))
        for ed in data.get("education") or []:
            if not isinstance(ed, dict): continue
            degree=ed.get("degree") or ed.get("qualification") or ""
            school=ed.get("institution") or ed.get("school") or ed.get("university") or ed.get("college") or ""
            dates=wz139_date_range(ed)
            if degree: sidebar.append(P(degree,"mini"))
            details=" | ".join([wz139_pdf_text(x) for x in [school,dates] if str(x or "").strip()])
            if details: sidebar.append(P(details,"side"))
            sidebar.append(Spacer(1,4))
    if data.get("certifications"):
        sidebar.append(SEC("Certifications")); sidebar.extend(BL(data.get("certifications"),"side_bullet",10))
    if not sidebar: sidebar.append(P("No sidebar details provided.","muted"))
    main=[]
    if data.get("professional_summary"):
        main.append(SEC("Profile")); main.append(P(data.get("professional_summary"),"body")); main.append(Spacer(1,6))
    if data.get("work_experience"):
        main.append(SEC("Experience")); main_w=doc.width*0.66-24
        for job in data.get("work_experience") or []:
            if not isinstance(job, dict): continue
            company=wz139_pdf_text(job.get("company") or "Company")
            role=wz139_pdf_text(job.get("title") or job.get("role") or "")
            dates=wz139_date_range(job)
            job_header=Table([[Paragraph(html.escape(company),styles["company"]),Paragraph(html.escape(dates),styles["dates"])],[Paragraph(html.escape(role),styles["jobtitle"]),""]], colWidths=[main_w*.68, main_w*.32])
            job_header.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),0),("TOPPADDING",(0,0),(-1,-1),0),("BOTTOMPADDING",(0,0),(-1,-1),1),("SPAN",(0,1),(1,1))]))
            job_block=[job_header]
            for b in _as_list(job.get("bullets"))[:7]:
                val=wz139_pdf_text(str(b or "").strip(" -•*\t"))
                if val: job_block.append(Paragraph(html.escape(val),styles["bullet"],bulletText="-"))
            main.append(KeepTogether(job_block) if KeepTogether is not None else job_block); main.append(Spacer(1,8))
    if data.get("projects"):
        main.append(SEC("Projects"))
        for pr in data.get("projects")[:4]:
            if not isinstance(pr, dict): continue
            block=[]
            if pr.get("name"): block.append(P(pr.get("name"),"mini"))
            for b in _as_list(pr.get("bullets"))[:4]:
                val=wz139_pdf_text(str(b or "").strip(" -•*\t"))
                if val: block.append(Paragraph(html.escape(val),styles["bullet"],bulletText="-"))
            if block: main.append(KeepTogether(block) if KeepTogether is not None else block); main.append(Spacer(1,6))
    if not main: main.append(P("No main CV details provided.","muted"))
    style_key=resolve_template_style(template_name)
    left_bg=colors.HexColor("#eef2f7")
    if style_key=="Career Pivot": left_bg=colors.HexColor("#f3e8ff")
    elif style_key=="Graduate Portfolio": left_bg=colors.HexColor("#e0f2fe")
    elif style_key=="Creative Modern": left_bg=colors.HexColor("#ecfeff")
    master_grid=Table([[sidebar, main]], colWidths=[doc.width*.34, doc.width*.66])
    master_grid.setStyle(TableStyle([("BACKGROUND",(0,0),(0,0),left_bg),("BACKGROUND",(1,0),(1,0),colors.white),("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(0,0),12),("RIGHTPADDING",(0,0),(0,0),12),("LEFTPADDING",(1,0),(1,0),18),("RIGHTPADDING",(1,0),(1,0),6),("TOPPADDING",(0,0),(-1,-1),14),("BOTTOMPADDING",(0,0),(-1,-1),14),("BOX",(0,0),(-1,-1),0.5,colors.HexColor("#e5e7eb"))]))
    divider=Table([[""]], colWidths=[doc.width], rowHeights=[1.5]); divider.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#1f2937"))]))
    doc.build([header_table, divider, Spacer(1,10), master_grid])
    buffer.seek(0); pdf=buffer.getvalue()
    if not pdf.startswith(b"%PDF"): raise ValueError("Invalid PDF")
    return pdf

try:
    _wz139_legacy_make_styled_pdf_from_cv_text = make_styled_pdf_from_cv_text
except NameError:
    _wz139_legacy_make_styled_pdf_from_cv_text = None

def _workzo_plain_text_pdf(title: str, body: str) -> bytes:
    """Safe fallback PDF generator for the modular version.

    If structured CV JSON is missing, generate a normal PDF from the available
    CV text instead of crashing.
    """
    body = sanitize_pdf_text(str(body or "").strip())
    title = sanitize_pdf_text(str(title or "CV").strip() or "CV")

    if SimpleDocTemplate is not None and Paragraph is not None and Spacer is not None and getSampleStyleSheet is not None:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=42, leftMargin=42, topMargin=42, bottomMargin=42)
        styles = getSampleStyleSheet()
        story = [Paragraph(html.escape(title), styles["Title"]), Spacer(1, 12)]

        for raw_line in body.splitlines():
            line = str(raw_line or "").strip()
            if not line:
                story.append(Spacer(1, 7))
                continue
            safe_line = html.escape(line)
            is_heading = (len(line) <= 45 and (line.endswith(":") or line.isupper()))
            if is_heading:
                story.append(Paragraph(f"<b>{safe_line.rstrip(':')}</b>", styles["Heading3"]))
            elif line.startswith(("- ", "• ", "* ")):
                story.append(Paragraph(html.escape(line.lstrip("-•* ")), styles["BodyText"], bulletText="-"))
            else:
                story.append(Paragraph(safe_line, styles["BodyText"]))
                story.append(Spacer(1, 3))

        try:
            doc.build(story)
            buffer.seek(0)
            data = buffer.getvalue()
            if data.startswith(b"%PDF"):
                return data
        except Exception:
            pass

    safe = (title + "\n\n" + body).replace("\r", "").replace("\n", "\\n")[:900]
    safe = safe.replace("(", "[").replace(")", "]")
    content = f"BT /F1 10 Tf 40 780 Td ({safe}) Tj ET"
    pdf = f"%PDF-1.4\n1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n5 0 obj << /Length {len(content)} >> stream\n{content}\nendstream endobj\ntrailer << /Root 1 0 R >>\n%%EOF"
    return pdf.encode("latin-1", errors="ignore")


def make_styled_pdf_from_cv_text(title: str, cv_text: str, template_name: str = "ATS Resume", target_country: str = "") -> bytes:
    cleaned = sanitize_pdf_text(clean_generated_cv_text_for_template(cv_text or ""))

    try:
        data = wz139_structured_data_from_state_or_text(cleaned)
        if isinstance(data, dict) and (data.get("work_experience") or data.get("education") or data.get("core_skills") or data.get("professional_summary")):
            pdf = _strict_structured_pdf(title, data, template_name, target_country)
            if isinstance(pdf, (bytes, bytearray)) and bytes(pdf).startswith(b"%PDF"):
                return bytes(pdf)
    except Exception:
        pass

    if _wz139_legacy_make_styled_pdf_from_cv_text is not None:
        try:
            pdf = _wz139_legacy_make_styled_pdf_from_cv_text(title, cleaned, template_name, target_country)
            if isinstance(pdf, (bytes, bytearray)) and bytes(pdf).startswith(b"%PDF"):
                return bytes(pdf)
        except Exception:
            pass

    return _workzo_plain_text_pdf(title, cleaned or cv_text or "")


# ROUTER
# =========================================================
# This module is now safe to import. The router only runs when this file is executed
# inside the original WorkZo app where all page functions exist.
def _workzo_run_router_if_available() -> None:
    required = ["read_url_page", "show_landing_page", "show_onboarding", "show_dashboard"]
    if not all(name in globals() for name in required):
        return
    if st is None:
        return
    try:
        workzo_v137_stabilize_state()
        url_page = read_url_page(st.session_state.get("page", "landing"))
        valid_pages = {"landing", "dashboard", "job_assist", "cv_documents", "workobot", "founder_dashboard", "onboarding"}
        try:
            _home_param = st.query_params.get("home", "")
        except Exception:
            _home_param = ""
        if url_page == "dashboard" and _home_param:
            st.session_state.onboarding_complete = True
            st.session_state.page = "dashboard"
            st.session_state.nav_page = "dashboard"
        elif url_page in valid_pages and st.session_state.get("onboarding_complete"):
            st.session_state.page = url_page
            st.session_state.nav_page = "dashboard" if url_page in ["onboarding", "landing"] else url_page

        if st.session_state.page == "landing":
            show_landing_page()
        elif not st.session_state.onboarding_complete or st.session_state.page == "onboarding":
            show_onboarding()
        else:
            show_dashboard()
    except Exception as exc:
        try:
            st.error(f"WorkZo router error: {exc}")
        except Exception:
            raise

_workzo_run_router_if_available()


# =========================================================
# WorkZo v141 - editable visual CV preview helpers
# Purpose: let users edit the visual preview section-by-section and
# download a PDF generated from the same structured fields.
# =========================================================
def workzo_cv_text_to_editable_sections(cv_text: str = "", structured_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Build a simple editable CV object from structured JSON or CV text."""
    data = {}
    if isinstance(structured_data, dict) and structured_data:
        data = validate_resume_dates_and_sections(_coerce_structured_resume_schema(structured_data))
    if not data:
        sec = _best_cv_sections_for_template(cv_text or "")
        header_lines = [x.strip() for x in str(sec.get("header", "")).splitlines() if x.strip()]
        data = {
            "full_name": header_lines[0] if header_lines else "",
            "target_role": header_lines[1] if len(header_lines) > 1 else "",
            "contact": {"phone": "", "email": "", "location": "", "linkedin": ""},
            "professional_summary": sec.get("summary", ""),
            "core_skills": [re.sub(r"^[-•*]\s*", "", x).strip() for x in str(sec.get("skills", "")).splitlines() if x.strip()],
            "tools_technologies": [],
            "work_experience": parse_experience_text_to_items(sec.get("experience", "")),
            "education": parse_education_text_to_items(sec.get("education", "")),
            "projects": parse_projects_text_to_items(sec.get("projects", "")),
            "languages": [re.sub(r"^[-•*]\s*", "", x).strip() for x in str(sec.get("languages", "")).splitlines() if x.strip()],
            "certifications": [re.sub(r"^[-•*]\s*", "", x).strip() for x in str(sec.get("certifications", "")).splitlines() if x.strip()],
        }
        contact_text = " | ".join(header_lines[2:]) if len(header_lines) > 2 else ""
        email_match = re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", contact_text)
        phone_match = re.search(r"(?:\+\d{1,3}[\s-]?)?(?:\(?\d+\)?[\s-]?){6,}", contact_text)
        linkedin_match = re.search(r"(?:linkedin\.com/[^\s|]+)", contact_text, flags=re.I)
        data["contact"]["email"] = email_match.group(0) if email_match else ""
        data["contact"]["phone"] = phone_match.group(0) if phone_match else ""
        data["contact"]["linkedin"] = linkedin_match.group(0) if linkedin_match else ""
        data["contact"]["location"] = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|(?:\+\d{1,3}[\s-]?)?(?:\(?\d+\)?[\s-]?){6,}|(?:linkedin\.com/[^\s|]+)", "", contact_text, flags=re.I).strip(" |,-")
        data = validate_resume_dates_and_sections(_coerce_structured_resume_schema(data))
    try:
        data = _workzo_normalize_editable_data(data)
    except Exception:
        pass
    return data or {}




def _workzo_clean_text_token(value: Any) -> str:
    """Clean visible CV text and remove common PDF extraction splits."""
    txt = str(value or "")
    replacements = {
        "for m": "form", "in for m": "inform", "in itiative": "initiative",
        "In dian": "Indian", "You Tube": "YouTube", "Text Blob": "TextBlob",
        "Manage Engine": "ManageEngine", "Service Desk": "ServiceDesk", "My SQL": "MySQL",
        "Linked In": "LinkedIn",
    }
    for a,b in replacements.items():
        txt = txt.replace(a,b)
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt

def _workzo_project_to_text(item: Any) -> str:
    item = _workzo_literal_if_possible(item)
    if isinstance(item, dict):
        # Sometimes a previous run saved the whole dict inside the name field.
        name_obj = _workzo_literal_if_possible(item.get("name") or item.get("title") or "")
        if isinstance(name_obj, dict):
            item = name_obj
        name = _workzo_clean_text_token(item.get("name") or item.get("title") or "")
        bullets = [_workzo_clean_text_token(b).strip(" -•*") for b in _as_list(item.get("bullets") or item.get("details") or item.get("description")) if str(b or "").strip()]
        lines = []
        if name: lines.append(name)
        lines += ["- " + b for b in bullets if b]
        return "\n".join(lines).strip()
    return _workzo_clean_text_token(item)

def _workzo_parse_project_blocks(text: str) -> List[Dict[str, Any]]:
    projects=[]
    for block in re.split(r"\n\s*\n", str(text or "").strip()):
        lines=[x.strip() for x in block.splitlines() if x.strip()]
        if not lines: continue
        first=_workzo_literal_if_possible(lines[0])
        if isinstance(first, dict):
            block_text=_workzo_project_to_text(first)
            lines=[x.strip() for x in block_text.splitlines() if x.strip()]
            if not lines: continue
        name=re.sub(r"^[-•*]\s*", "", lines[0]).strip()
        bullets=[re.sub(r"^[-•*]\s*", "", x).strip() for x in lines[1:] if x.strip()]
        projects.append({"name": _workzo_clean_text_token(name), "bullets": [_workzo_clean_text_token(b) for b in bullets if b]})
    return projects

def _workzo_join_list_for_edit(items: Any) -> str:
    out = []
    for item in _as_list(_workzo_literal_if_possible(items)):
        text = _workzo_project_to_text(item)
        if text.strip():
            out.append(text.strip())
    return "\n\n".join(out)


def _workzo_literal_if_possible(value: Any) -> Any:
    """Convert stringified list/dict sections back into real data safely."""
    if not isinstance(value, str):
        return value
    text = value.strip()
    if not text:
        return value
    if (text.startswith("[") and text.endswith("]")) or (text.startswith("{") and text.endswith("}")):
        try:
            return ast.literal_eval(text)
        except Exception:
            try:
                return json.loads(text)
            except Exception:
                return value
    return value


def _workzo_normalize_editable_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize editable CV fields so preview/PDF never see raw dict strings."""
    if not isinstance(data, dict):
        return {}
    data = dict(data)
    for key in ["work_experience", "experience", "education", "projects", "core_skills", "skills", "tools_technologies", "languages", "certifications"]:
        if key in data:
            data[key] = _workzo_literal_if_possible(data.get(key))

    raw_exp = _workzo_literal_if_possible(data.get("work_experience") or data.get("experience") or [])
    normalized_exp = []
    for item in _as_list(raw_exp):
        item = _workzo_literal_if_possible(item)
        if isinstance(item, dict):
            dates = item.get("dates") or item.get("date") or " - ".join(str(x) for x in [item.get("start_date") or item.get("start"), item.get("end_date") or item.get("end")] if str(x or '').strip())
            normalized_exp.append({
                "title": str(item.get("title") or item.get("role") or item.get("position") or "").strip(),
                "company": str(item.get("company") or item.get("employer") or item.get("organization") or "").strip(),
                "dates": str(dates or "").strip(),
                "bullets": [str(b).strip(" -•*") for b in _as_list(item.get("bullets") or item.get("achievements") or item.get("responsibilities")) if str(b or "").strip()],
            })
        elif str(item or "").strip():
            normalized_exp.extend(_workzo_parse_experience_blocks(str(item)))
    data["work_experience"] = normalized_exp

    raw_edu = _workzo_literal_if_possible(data.get("education") or [])
    normalized_edu = []
    for item in _as_list(raw_edu):
        item = _workzo_literal_if_possible(item)
        if isinstance(item, dict):
            dates = item.get("dates") or item.get("year") or " - ".join(str(x) for x in [item.get("start_year") or item.get("start_date"), item.get("end_year") or item.get("end_date")] if str(x or '').strip())
            normalized_edu.append({
                "degree": str(item.get("degree") or item.get("qualification") or "").strip(),
                "institution": str(item.get("institution") or item.get("school") or item.get("university") or item.get("college") or "").strip(),
                "dates": str(dates or "").strip(),
            })
        elif str(item or "").strip():
            normalized_edu.extend(_workzo_parse_education_lines(str(item)))
    data["education"] = normalized_edu

    data["core_skills"] = [str(x).strip(" -•*") for x in _as_list(data.get("core_skills") or data.get("skills")) if str(x or "").strip()]
    data["tools_technologies"] = [str(x).strip(" -•*") for x in _as_list(data.get("tools_technologies")) if str(x or "").strip()]
    data["languages"] = [str(x).strip(" -•*") for x in _as_list(data.get("languages")) if str(x or "").strip()]
    data["certifications"] = [str(x).strip(" -•*") for x in _as_list(data.get("certifications")) if str(x or "").strip()]

    raw_projects = _workzo_literal_if_possible(data.get("projects") or [])
    normalized_projects = []
    for item in _as_list(raw_projects):
        item = _workzo_literal_if_possible(item)
        if isinstance(item, dict):
            name_obj = _workzo_literal_if_possible(item.get("name") or item.get("title") or "")
            if isinstance(name_obj, dict):
                item = name_obj
            normalized_projects.append({
                "name": _workzo_clean_text_token(item.get("name") or item.get("title") or ""),
                "bullets": [_workzo_clean_text_token(b).strip(" -•*") for b in _as_list(item.get("bullets") or item.get("details") or item.get("description")) if str(b or "").strip()],
            })
        elif str(item or "").strip():
            normalized_projects.append({"name": str(item).strip(), "bullets": []})
    data["projects"] = normalized_projects
    return data


def _workzo_experience_to_edit_text(items: Any) -> str:
    """Readable editor text for experience. Handles real dicts and stringified dict/list values."""
    items = _workzo_literal_if_possible(items)
    blocks = []
    for item in _as_list(items):
        item = _workzo_literal_if_possible(item)
        if isinstance(item, dict):
            header = " | ".join(str(x).strip() for x in [item.get("title") or item.get("role"), item.get("company"), item.get("dates")] if str(x or "").strip())
            bullets = "\n".join("- " + str(b).strip(" -•*") for b in _as_list(item.get("bullets")) if str(b or "").strip())
            block = "\n".join(x for x in [header, bullets] if x.strip())
            if block.strip():
                blocks.append(block.strip())
        elif str(item or "").strip():
            blocks.append(str(item).strip())
    return "\n\n".join(blocks)


def _workzo_education_to_edit_text(items: Any) -> str:
    """Readable editor text for education. Handles real dicts and stringified dict/list values."""
    items = _workzo_literal_if_possible(items)
    lines = []
    for item in _as_list(items):
        item = _workzo_literal_if_possible(item)
        if isinstance(item, dict):
            line = " | ".join(str(x).strip() for x in [item.get("degree"), item.get("institution") or item.get("school") or item.get("university"), item.get("dates") or item.get("year")] if str(x or "").strip())
            if line.strip():
                lines.append(line)
        elif str(item or "").strip():
            lines.append(str(item).strip())
    return "\n".join(lines)


def _workzo_parse_experience_blocks(text: str) -> List[Dict[str, Any]]:
    items = []
    for block in re.split(r"\n\s*\n", str(text or "").strip()):
        lines = [x.strip() for x in block.splitlines() if x.strip()]
        if not lines:
            continue
        header = lines[0]
        parts = [p.strip() for p in header.split("|")]
        title = parts[0] if parts else ""
        company = parts[1] if len(parts) > 1 else ""
        dates = parts[2] if len(parts) > 2 else ""
        bullets = [re.sub(r"^[-•*]\s*", "", x).strip() for x in lines[1:] if x.strip()]
        items.append({"title": title, "company": company, "dates": dates, "bullets": bullets})
    return items


def _workzo_parse_education_lines(text: str) -> List[Dict[str, Any]]:
    items = []
    for line in str(text or "").splitlines():
        line = line.strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split("|")]
        items.append({"degree": parts[0] if parts else "", "institution": parts[1] if len(parts) > 1 else "", "dates": parts[2] if len(parts) > 2 else ""})
    return items


def _workzo_parse_simple_lines(text: str) -> List[str]:
    return [re.sub(r"^[-•*]\s*", "", x).strip() for x in str(text or "").splitlines() if x.strip()]


def workzo_editable_cv_editor(prefix: str, cv_text: str = "", structured_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Bulletproof section editor.

    IMPORTANT STREAMLIT RULE:
    The widgets below intentionally do NOT use value= together with key=.
    Each widget is initialized once in st.session_state and every preview/PDF
    call reads directly from the widget keys. This prevents old AI text or old
    structured JSON from overwriting manual edits during reruns.
    """
    if st is None:
        return workzo_cv_text_to_editable_sections(cv_text, structured_data)

    data = _workzo_final_preview_data(workzo_cv_text_to_editable_sections(cv_text, structured_data))
    contact = data.get("contact") if isinstance(data.get("contact"), dict) else {}

    def _set_once(key: str, initial: Any) -> None:
        initial = "" if initial is None else str(initial)
        # Initialize once. Also repair old empty widget state when the parsed data has content.
        if key not in st.session_state or (not str(st.session_state.get(key, "")).strip() and initial.strip()):
            st.session_state[key] = initial

    keys = {
        "name": f"{prefix}_name",
        "role": f"{prefix}_role",
        "phone": f"{prefix}_phone",
        "email": f"{prefix}_email",
        "location": f"{prefix}_location",
        "linkedin": f"{prefix}_linkedin",
        "summary": f"{prefix}_summary",
        "skills": f"{prefix}_skills",
        "experience": f"{prefix}_experience",
        "education": f"{prefix}_education",
        "projects": f"{prefix}_projects",
        "languages": f"{prefix}_languages",
        "certifications": f"{prefix}_certifications",
    }

    _set_once(keys["name"], data.get("full_name") or "")
    _set_once(keys["role"], data.get("target_role") or "")
    _set_once(keys["phone"], contact.get("phone") or "")
    _set_once(keys["email"], contact.get("email") or "")
    _set_once(keys["location"], contact.get("location") or "")
    _set_once(keys["linkedin"], contact.get("linkedin") or "")
    _set_once(keys["summary"], data.get("professional_summary") or "")
    _set_once(keys["skills"], "\n".join(_as_list(data.get("core_skills")) + _as_list(data.get("tools_technologies"))))
    _set_once(keys["experience"], _workzo_experience_to_edit_text(data.get("work_experience")))
    _set_once(keys["education"], _workzo_education_to_edit_text(data.get("education")))
    _set_once(keys["projects"], _workzo_join_list_for_edit(data.get("projects")))
    _set_once(keys["languages"], "\n".join(_as_list(data.get("languages"))))
    _set_once(keys["certifications"], "\n".join(_as_list(data.get("certifications"))))

    st.markdown("### Editable Resume Preview Details")
    st.caption("Edit these fields. The preview and PDF download use these exact widget values.")

    c1, c2 = st.columns(2)
    with c1:
        st.text_input("Name", key=keys["name"])
        st.text_input("Phone", key=keys["phone"])
        st.text_input("Location", key=keys["location"])
    with c2:
        st.text_input("Role / headline", key=keys["role"])
        st.text_input("Email", key=keys["email"])
        st.text_input("LinkedIn / portfolio", key=keys["linkedin"])

    st.text_area("Professional Summary", height=120, key=keys["summary"])
    st.text_area("Skills", height=130, key=keys["skills"])
    st.text_area("Experience", height=260, key=keys["experience"], help="Use blocks like: Role | Company | Dates, then bullets below.")
    st.text_area("Education", height=130, key=keys["education"], help="Use one line per item: Degree | Institution | Dates")
    st.text_area("Projects", height=120, key=keys["projects"])
    st.text_area("Languages", height=90, key=keys["languages"])
    st.text_area("Certifications", height=90, key=keys["certifications"])

    updated = {
        "full_name": str(st.session_state.get(keys["name"], "")).strip(),
        "target_role": str(st.session_state.get(keys["role"], "")).strip(),
        "contact": {
            "phone": str(st.session_state.get(keys["phone"], "")).strip(),
            "email": str(st.session_state.get(keys["email"], "")).strip(),
            "location": str(st.session_state.get(keys["location"], "")).strip(),
            "linkedin": str(st.session_state.get(keys["linkedin"], "")).strip(),
        },
        "professional_summary": str(st.session_state.get(keys["summary"], "")).strip(),
        "core_skills": _workzo_parse_simple_lines(st.session_state.get(keys["skills"], "")),
        "tools_technologies": [],
        "work_experience": _workzo_parse_experience_blocks(st.session_state.get(keys["experience"], "")),
        "education": _workzo_parse_education_lines(st.session_state.get(keys["education"], "")),
        "projects": _workzo_parse_project_blocks(st.session_state.get(keys["projects"], "")),
        "languages": _workzo_parse_simple_lines(st.session_state.get(keys["languages"], "")),
        "certifications": _workzo_parse_simple_lines(st.session_state.get(keys["certifications"], "")),
    }

    final_data = _workzo_final_preview_data(updated)
    # Store both structured and plain text live, so hardcoded older calls still see the edits.
    st.session_state["workzo_live_cv_structured"] = final_data
    st.session_state["workzo_live_cv_text"] = workzo_build_cv_text_from_editable(final_data)
    st.session_state["cv_editor_widget"] = st.session_state["workzo_live_cv_text"]
    st.session_state["clean_structured_cv_text"] = st.session_state["workzo_live_cv_text"]
    st.session_state["cv_text"] = st.session_state["workzo_live_cv_text"]
    return final_data

def workzo_build_cv_text_from_editable(data: Dict[str, Any]) -> str:
    """Create clean text from editable structured fields for TXT/save operations."""
    data = _workzo_final_preview_data(data or {})
    contact = data.get("contact") if isinstance(data.get("contact"), dict) else {}
    lines = []
    lines.append(str(data.get("full_name") or "").strip())
    lines.append(str(data.get("target_role") or "").strip())
    contact_line = " | ".join(str(contact.get(k) or "").strip() for k in ["phone", "email", "location", "linkedin"] if str(contact.get(k) or "").strip())
    if contact_line:
        lines.append(contact_line)
    if data.get("professional_summary"):
        lines += ["", "Professional Summary", str(data.get("professional_summary")).strip()]
    if data.get("core_skills"):
        lines += ["", "Skills"] + ["- " + str(x) for x in _as_list(data.get("core_skills")) if str(x).strip()]
    if data.get("work_experience"):
        lines += ["", "Experience"]
        for job in _as_list(data.get("work_experience")):
            if isinstance(job, dict):
                lines.append(" | ".join(str(job.get(k) or "").strip() for k in ["title", "company", "dates"] if str(job.get(k) or "").strip()))
                lines += ["- " + str(b).strip(" -•*") for b in _as_list(job.get("bullets")) if str(b).strip()]
    if data.get("projects"):
        lines += ["", "Projects"]
        for pr in _as_list(data.get("projects")):
            if isinstance(pr, dict):
                if pr.get("name"):
                    lines.append(str(pr.get("name")))
                lines += ["- " + str(b).strip(" -•*") for b in _as_list(pr.get("bullets")) if str(b).strip()]
            elif str(pr).strip():
                lines.append("- " + str(pr).strip())
    if data.get("education"):
        lines += ["", "Education"]
        for ed in _as_list(data.get("education")):
            if isinstance(ed, dict):
                lines.append(" | ".join(str(ed.get(k) or "").strip() for k in ["degree", "institution", "dates"] if str(ed.get(k) or "").strip()))
    if data.get("languages"):
        lines += ["", "Languages"] + ["- " + str(x) for x in _as_list(data.get("languages")) if str(x).strip()]
    if data.get("certifications"):
        lines += ["", "Certifications"] + ["- " + str(x) for x in _as_list(data.get("certifications")) if str(x).strip()]
    return "\n".join(x for x in lines if x is not None).strip()



def _workzo_final_preview_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Single source of truth for editable CV preview and PDF.

    IMPORTANT: This intentionally does NOT call the old text-template parser or
    validate_resume_dates_and_sections(), because those were the reason edited
    Experience/Education disappeared in preview. It only normalizes the current
    editable fields returned by workzo_editable_cv_editor().
    """
    data = _workzo_normalize_editable_data(data or {})
    contact = data.get("contact") if isinstance(data.get("contact"), dict) else {}
    fixed = {
        "full_name": str(data.get("full_name") or "").strip(),
        "target_role": str(data.get("target_role") or "").strip(),
        "contact": {
            "phone": str(contact.get("phone") or "").strip(),
            "email": str(contact.get("email") or "").strip(),
            "location": str(contact.get("location") or "").strip(),
            "linkedin": str(contact.get("linkedin") or "").strip(),
        },
        "professional_summary": str(data.get("professional_summary") or "").strip(),
        "core_skills": [str(x).strip(" -•*") for x in _as_list(data.get("core_skills")) if str(x or "").strip()],
        "tools_technologies": [str(x).strip(" -•*") for x in _as_list(data.get("tools_technologies")) if str(x or "").strip()],
        "languages": [str(x).strip(" -•*") for x in _as_list(data.get("languages")) if str(x or "").strip()],
        "certifications": [str(x).strip(" -•*") for x in _as_list(data.get("certifications")) if str(x or "").strip()],
        "projects": [],
        "work_experience": [],
        "education": [],
    }

    for job in _as_list(data.get("work_experience") or data.get("experience")):
        job = _workzo_literal_if_possible(job)
        if isinstance(job, dict):
            fixed["work_experience"].append({
                "title": str(job.get("title") or job.get("role") or job.get("position") or "").strip(),
                "company": str(job.get("company") or job.get("employer") or job.get("organization") or "").strip(),
                "dates": str(job.get("dates") or job.get("date") or "").strip(),
                "bullets": [str(b).strip(" -•*") for b in _as_list(job.get("bullets") or job.get("achievements") or job.get("responsibilities")) if str(b or "").strip()],
            })
        elif str(job or "").strip():
            fixed["work_experience"].extend(_workzo_parse_experience_blocks(str(job)))

    for ed in _as_list(data.get("education")):
        ed = _workzo_literal_if_possible(ed)
        if isinstance(ed, dict):
            fixed["education"].append({
                "degree": str(ed.get("degree") or ed.get("qualification") or "").strip(),
                "institution": str(ed.get("institution") or ed.get("school") or ed.get("university") or ed.get("college") or "").strip(),
                "dates": str(ed.get("dates") or ed.get("year") or "").strip(),
            })
        elif str(ed or "").strip():
            fixed["education"].extend(_workzo_parse_education_lines(str(ed)))

    for pr in _as_list(data.get("projects")):
        pr = _workzo_literal_if_possible(pr)
        if isinstance(pr, dict):
            name_obj = _workzo_literal_if_possible(pr.get("name") or pr.get("title") or "")
            if isinstance(name_obj, dict):
                pr = name_obj
            fixed["projects"].append({
                "name": _workzo_clean_text_token(pr.get("name") or pr.get("title") or ""),
                "bullets": [_workzo_clean_text_token(b).strip(" -•*") for b in _as_list(pr.get("bullets") or pr.get("details") or pr.get("description")) if str(b or "").strip()],
            })
        elif str(pr or "").strip():
            fixed["projects"].append({"name": str(pr).strip(), "bullets": []})

    return fixed


def workzo_visual_cv_html_from_structured(data: Dict[str, Any], template_name: str, target_country: str) -> str:
    """Build the visual CV preview directly from the live editable fields.

    This replaces the old parser-based preview. The preview now uses the same
    fields that the user edits, so Experience and Education will not disappear
    or turn into raw dictionaries.
    """
    data = _workzo_final_preview_data(data or {})
    contact = data.get("contact") if isinstance(data.get("contact"), dict) else {}

    def esc(v):
        return html.escape(wz139_pdf_text(v))

    def list_html(items):
        vals = [esc(str(x).strip(" -•*")) for x in _as_list(items) if str(x or "").strip()]
        return "<ul>" + "".join(f"<li>{v}</li>" for v in vals) + "</ul>" if vals else "<p class='cv-empty'>—</p>"

    def exp_html(items):
        blocks = []
        for job in _as_list(items):
            if not isinstance(job, dict):
                continue
            title = esc(job.get("title"))
            company = esc(job.get("company"))
            dates = esc(job.get("dates"))
            head_parts = [x for x in [title, company, dates] if x]
            bullets = [esc(str(b).strip(" -•*")) for b in _as_list(job.get("bullets")) if str(b or "").strip()]
            if not head_parts and not bullets:
                continue
            block = ""
            if head_parts:
                block += f"<p class='cv-job-head'><b>{' | '.join(head_parts)}</b></p>"
            if bullets:
                block += "<ul>" + "".join(f"<li>{b}</li>" for b in bullets) + "</ul>"
            blocks.append(block)
        return "".join(blocks) if blocks else "<p class='cv-empty'>—</p>"

    def edu_html(items):
        lines = []
        for ed in _as_list(items):
            if not isinstance(ed, dict):
                continue
            parts = [esc(ed.get("degree")), esc(ed.get("institution")), esc(ed.get("dates"))]
            parts = [x for x in parts if x]
            if parts:
                lines.append(f"<p>{' | '.join(parts)}</p>")
        return "".join(lines) if lines else "<p class='cv-empty'>—</p>"

    def projects_html(items):
        blocks = []
        for pr in _as_list(items):
            if isinstance(pr, dict):
                part = ""
                if pr.get("name"):
                    part += f"<p><b>{esc(pr.get('name'))}</b></p>"
                bullets = [esc(str(b).strip(" -•*")) for b in _as_list(pr.get("bullets")) if str(b or "").strip()]
                if bullets:
                    part += "<ul>" + "".join(f"<li>{b}</li>" for b in bullets) + "</ul>"
                if part:
                    blocks.append(part)
            elif str(pr or "").strip():
                blocks.append(f"<p>{esc(pr)}</p>")
        return "".join(blocks) if blocks else "<p class='cv-empty'>—</p>"

    style_key = resolve_template_style(template_name)
    name = esc(data.get("full_name") or "Your Name")
    title = esc(data.get("target_role") or f"CV for {target_country}")
    contact_line = esc(" · ".join(str(contact.get(k) or "").strip() for k in ["phone", "email", "location", "linkedin"] if str(contact.get(k) or "").strip()))
    summary = f"<p>{esc(data.get('professional_summary'))}</p>" if data.get("professional_summary") else "<p class='cv-empty'>—</p>"
    skills = list_html(_as_list(data.get("core_skills")) + _as_list(data.get("tools_technologies")))
    experience = exp_html(data.get("work_experience"))
    projects = projects_html(data.get("projects"))
    education = edu_html(data.get("education"))
    languages = list_html(data.get("languages"))
    certifications = list_html(data.get("certifications"))

    base_css = """
    <style>
      .cv-page { width: 794px; min-height: 1123px; margin: 0 auto 24px auto; background: white; color: #111827; box-shadow: 0 18px 50px rgba(0,0,0,0.35); border-radius: 8px; overflow: hidden; font-family: Arial, Helvetica, sans-serif; }
      .cv-page p { margin: 0 0 7px 0; line-height: 1.38; font-size: 13px; }
      .cv-page ul { margin: 0 0 10px 18px; padding: 0; }
      .cv-page li { font-size: 13px; margin-bottom: 5px; line-height: 1.35; }
      .cv-section-title { font-size: 12px; letter-spacing: 1.4px; text-transform: uppercase; font-weight: 800; margin: 16px 0 8px; }
      .cv-small { color:#64748b; font-size:12px; }
      .cv-empty { color:#64748b; }
      .cv-job-head { margin-top: 4px !important; margin-bottom: 5px !important; }
      @media (max-width: 850px) { .cv-page { width: 100%; min-height: auto; border-radius: 0; } }
    </style>
    """

    two_column = style_key in ["Executive Slate", "German-Style Lebenslauf", "Creative Modern", "Career Pivot", "Graduate Portfolio"]
    if two_column:
        return base_css + f"""
        <div class="cv-page">
          <div style="padding:42px 46px 20px; border-bottom:4px solid #1f2937;">
            <div style="font-size:34px; font-weight:800; letter-spacing:1px;">{name}</div>
            <div style="font-size:15px; color:#334155; margin-top:6px;">{title}</div>
            <div class="cv-small" style="margin-top:10px;">{contact_line}</div>
          </div>
          <div style="display:grid; grid-template-columns: 36% 64%;">
            <aside style="background:#f1f5f9; padding:26px 28px; min-height:900px;">
              <div class="cv-section-title">Skills</div>{skills}
              <div class="cv-section-title">Languages</div>{languages}
              <div class="cv-section-title">Education</div>{education}
              <div class="cv-section-title">Certifications</div>{certifications}
            </aside>
            <main style="padding:26px 32px;">
              <div class="cv-section-title">Profile</div>{summary}
              <div class="cv-section-title">Experience</div>{experience}
              <div class="cv-section-title">Projects</div>{projects}
            </main>
          </div>
        </div>
        """

    return base_css + f"""
    <div class="cv-page" style="padding:46px 56px;">
      <div style="border-bottom:2px solid #e5e7eb; padding-bottom:14px;">
        <div style="font-size:31px; font-weight:800;">{name}</div>
        <div style="font-size:15px; margin-top:5px;">{title}</div>
        <div class="cv-small" style="margin-top:8px;">{contact_line}</div>
      </div>
      <div class="cv-section-title">Professional Summary</div>{summary}
      <div class="cv-section-title">Skills</div>{skills}
      <div class="cv-section-title">Experience</div>{experience}
      <div class="cv-section-title">Projects</div>{projects}
      <div class="cv-section-title">Education</div>{education}
      <div class="cv-section-title">Languages</div>{languages}
      <div class="cv-section-title">Certifications</div>{certifications}
    </div>
    """


def make_styled_pdf_from_structured_preview(title: str, structured_data: Dict[str, Any], template_name: str = "ATS Resume", target_country: str = "") -> bytes:
    """Generate PDF from the same live editable structured data used in preview."""
    data = _workzo_final_preview_data(structured_data or {})

    if SimpleDocTemplate is None or Table is None or TableStyle is None or Paragraph is None or Spacer is None or colors is None:
        return make_styled_pdf_from_cv_text(title, workzo_build_cv_text_from_editable(data), template_name, target_country)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=28, leftMargin=28, topMargin=24, bottomMargin=24)
    base = getSampleStyleSheet()

    styles = {
        "name": ParagraphStyle("WZLiveName", parent=base["Title"], fontName="Helvetica-Bold", fontSize=23, leading=27, textColor=colors.HexColor("#0f172a"), spaceAfter=2),
        "role": ParagraphStyle("WZLiveRole", parent=base["BodyText"], fontName="Helvetica", fontSize=10.5, leading=13, textColor=colors.HexColor("#334155"), spaceAfter=4),
        "contact": ParagraphStyle("WZLiveContact", parent=base["BodyText"], fontName="Helvetica", fontSize=8.4, leading=10.2, textColor=colors.HexColor("#475569"), spaceAfter=4),
        "section": ParagraphStyle("WZLiveSection", parent=base["Heading4"], fontName="Helvetica-Bold", fontSize=9.2, leading=11.2, textColor=colors.HexColor("#0f172a"), spaceBefore=7, spaceAfter=5),
        "mini": ParagraphStyle("WZLiveMini", parent=base["BodyText"], fontName="Helvetica-Bold", fontSize=8.9, leading=11.2, textColor=colors.HexColor("#111827"), spaceBefore=3, spaceAfter=2),
        "body": ParagraphStyle("WZLiveBody", parent=base["BodyText"], fontName="Helvetica", fontSize=8.75, leading=11.2, textColor=colors.HexColor("#111827"), spaceAfter=3),
        "side": ParagraphStyle("WZLiveSide", parent=base["BodyText"], fontName="Helvetica", fontSize=8.3, leading=10.4, textColor=colors.HexColor("#111827"), spaceAfter=2),
        "side_bullet": ParagraphStyle("WZLiveSideBullet", parent=base["BodyText"], fontName="Helvetica", fontSize=8.25, leading=10.3, textColor=colors.HexColor("#111827"), leftIndent=8, firstLineIndent=0, spaceAfter=2),
        "bullet": ParagraphStyle("WZLiveBullet", parent=base["BodyText"], fontName="Helvetica", fontSize=8.55, leading=10.9, textColor=colors.HexColor("#111827"), leftIndent=11, firstLineIndent=0, spaceAfter=2),
        "company": ParagraphStyle("WZLiveCompany", parent=base["Heading4"], fontName="Helvetica-Bold", fontSize=9.4, leading=11.5, textColor=colors.HexColor("#1d4ed8"), spaceAfter=1),
        "dates": ParagraphStyle("WZLiveDates", parent=base["BodyText"], fontName="Helvetica", alignment=2, fontSize=8.15, leading=10.2, textColor=colors.HexColor("#475569"), spaceAfter=1),
        "jobtitle": ParagraphStyle("WZLiveJobTitle", parent=base["BodyText"], fontName="Helvetica-Oblique", fontSize=8.7, leading=10.8, textColor=colors.HexColor("#334155"), spaceAfter=3),
        "muted": ParagraphStyle("WZLiveMuted", parent=base["BodyText"], fontName="Helvetica", fontSize=8, leading=10, textColor=colors.HexColor("#64748b")),
    }

    def safe(v):
        return html.escape(wz139_pdf_text(v))

    def P(v, style="body"):
        return Paragraph(safe(v), styles[style])

    def SEC(label):
        return Paragraph(safe(label).upper(), styles["section"])

    def bullets(items, style="bullet", limit=18):
        out = []
        for item in _as_list(items)[:limit]:
            val = wz139_pdf_text(str(item or "").strip(" -•*\t"))
            if val:
                out.append(Paragraph(html.escape(val), styles[style], bulletText="-"))
        return out or [Paragraph("—", styles["muted"])]

    contact = data.get("contact") if isinstance(data.get("contact"), dict) else {}
    contact_line = " | ".join(wz139_pdf_text(contact.get(k)) for k in ["phone", "email", "location", "linkedin"] if str(contact.get(k) or "").strip())

    header_table = Table([
        [P(data.get("full_name") or "Your Name", "name")],
        [P(data.get("target_role") or title or "Professional CV", "role")],
        [P(contact_line, "contact") if contact_line else Paragraph("", styles["contact"])],
    ], colWidths=[doc.width])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 0),
        ("RIGHTPADDING", (0,0), (-1,-1), 0),
        ("TOPPADDING", (0,0), (-1,-1), 0),
        ("BOTTOMPADDING", (0,0), (-1,-1), 2),
    ]))

    sidebar = []
    sidebar.append(SEC("Skills")); sidebar.extend(bullets(_as_list(data.get("core_skills")) + _as_list(data.get("tools_technologies")), "side_bullet", 28))
    sidebar.append(SEC("Languages")); sidebar.extend(bullets(data.get("languages"), "side_bullet", 10))
    sidebar.append(SEC("Education"))
    if data.get("education"):
        for ed in data.get("education"):
            if not isinstance(ed, dict):
                continue
            line1 = ed.get("degree") or ""
            line2 = " | ".join(wz139_pdf_text(x) for x in [ed.get("institution"), ed.get("dates")] if str(x or "").strip())
            if line1: sidebar.append(P(line1, "mini"))
            if line2: sidebar.append(P(line2, "side"))
            sidebar.append(Spacer(1, 4))
    else:
        sidebar.append(P("—", "muted"))
    sidebar.append(SEC("Certifications")); sidebar.extend(bullets(data.get("certifications"), "side_bullet", 10))

    main = []
    main.append(SEC("Profile"))
    main.append(P(data.get("professional_summary") or "—", "body"))
    main.append(Spacer(1, 6))
    main.append(SEC("Experience"))
    if data.get("work_experience"):
        main_w = doc.width * 0.66 - 24
        for job in data.get("work_experience"):
            if not isinstance(job, dict):
                continue
            company = wz139_pdf_text(job.get("company") or "")
            role = wz139_pdf_text(job.get("title") or "")
            dates = wz139_pdf_text(job.get("dates") or "")
            header = Table([
                [Paragraph(html.escape(company or role or "Experience"), styles["company"]), Paragraph(html.escape(dates), styles["dates"])],
                [Paragraph(html.escape(role), styles["jobtitle"]), ""],
            ], colWidths=[main_w * .68, main_w * .32])
            header.setStyle(TableStyle([
                ("VALIGN", (0,0), (-1,-1), "TOP"),
                ("LEFTPADDING", (0,0), (-1,-1), 0),
                ("RIGHTPADDING", (0,0), (-1,-1), 0),
                ("TOPPADDING", (0,0), (-1,-1), 0),
                ("BOTTOMPADDING", (0,0), (-1,-1), 1),
                ("SPAN", (0,1), (1,1)),
            ]))
            block = [header]
            for b in _as_list(job.get("bullets"))[:7]:
                val = wz139_pdf_text(str(b or "").strip(" -•*\t"))
                if val:
                    block.append(Paragraph(html.escape(val), styles["bullet"], bulletText="-"))
            main.append(KeepTogether(block) if KeepTogether is not None else block)
            main.append(Spacer(1, 8))
    else:
        main.append(P("—", "muted"))
    main.append(SEC("Projects"))
    if data.get("projects"):
        for pr in data.get("projects")[:4]:
            if not isinstance(pr, dict):
                continue
            if pr.get("name"): main.append(P(pr.get("name"), "mini"))
            main.extend(bullets(pr.get("bullets"), "bullet", 4))
            main.append(Spacer(1, 5))
    else:
        main.append(P("—", "muted"))

    style_key = resolve_template_style(template_name)
    left_bg = colors.HexColor("#eef2f7")
    if style_key == "Career Pivot": left_bg = colors.HexColor("#f3e8ff")
    elif style_key == "Graduate Portfolio": left_bg = colors.HexColor("#e0f2fe")
    elif style_key == "Creative Modern": left_bg = colors.HexColor("#ecfeff")

    grid = Table([[sidebar, main]], colWidths=[doc.width * .34, doc.width * .66])
    grid.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (0,0), left_bg),
        ("BACKGROUND", (1,0), (1,0), colors.white),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (0,0), 12),
        ("RIGHTPADDING", (0,0), (0,0), 12),
        ("LEFTPADDING", (1,0), (1,0), 18),
        ("RIGHTPADDING", (1,0), (1,0), 6),
        ("TOPPADDING", (0,0), (-1,-1), 14),
        ("BOTTOMPADDING", (0,0), (-1,-1), 14),
        ("BOX", (0,0), (-1,-1), 0.5, colors.HexColor("#e5e7eb")),
    ]))

    divider = Table([[""]], colWidths=[doc.width], rowHeights=[1.5])
    divider.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#1f2937"))]))
    doc.build([header_table, divider, Spacer(1, 10), grid])
    buffer.seek(0)
    pdf = buffer.getvalue()
    if isinstance(pdf, (bytes, bytearray)) and bytes(pdf).startswith(b"%PDF"):
        return bytes(pdf)
    return make_styled_pdf_from_cv_text(title, workzo_build_cv_text_from_editable(data), template_name, target_country)


# =========================================================
# WorkZo final PDF safety patch: preserve resume line breaks
# =========================================================
def _workzo_resume_text_pdf_safe(title: str, cv_text: str) -> bytes:
    """Generate a readable PDF from resume text. Prevents one-line/train output."""
    from io import BytesIO
    import re, html
    if SimpleDocTemplate is None or Paragraph is None or Spacer is None or getSampleStyleSheet is None:
        return (cv_text or "").encode("utf-8")
    raw = str(cv_text or "").replace("\r\n", "\n").replace("\r", "\n")
    # Add line breaks before common section headings if AI returned one long paragraph.
    headings = ["Professional Summary", "Profile", "Summary", "Core Skills", "Skills", "Professional Experience", "Experience", "Projects", "Education", "Languages", "Certifications", "Contact"]
    for h in headings:
        raw = re.sub(r"(?<!\n)(\s*)(" + re.escape(h) + r")\b", r"\n\n\2", raw, flags=re.I)
    raw = re.sub(r"\s*[-•]\s+", "\n• ", raw)
    raw = re.sub(r"[ \t]+", " ", raw)
    raw = re.sub(r"\n{3,}", "\n\n", raw).strip()
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=32, bottomMargin=32)
    base = getSampleStyleSheet()
    styles = {
        "name": ParagraphStyle("WZPDFNameSafe", parent=base["Title"], fontName="Helvetica-Bold", fontSize=18, leading=22, spaceAfter=8, textColor=colors.HexColor("#0f172a")),
        "heading": ParagraphStyle("WZPDFHeadingSafe", parent=base["Heading3"], fontName="Helvetica-Bold", fontSize=10.5, leading=13, spaceBefore=9, spaceAfter=5, textColor=colors.HexColor("#0f172a")),
        "body": ParagraphStyle("WZPDFBodySafe", parent=base["BodyText"], fontName="Helvetica", fontSize=9.2, leading=12.6, spaceAfter=4, textColor=colors.HexColor("#111827")),
        "bullet": ParagraphStyle("WZPDFBulletSafe", parent=base["BodyText"], fontName="Helvetica", fontSize=9.0, leading=12.2, leftIndent=12, spaceAfter=3, textColor=colors.HexColor("#111827")),
    }
    story=[]
    lines=[ln.strip() for ln in raw.split("\n")]
    first=True
    heading_set={h.lower() for h in headings}
    for ln in lines:
        if not ln:
            story.append(Spacer(1,5)); continue
        clean=html.escape(ln.strip())
        key=ln.strip().rstrip(':').lower()
        if first:
            story.append(Paragraph(clean, styles["name"])); first=False; continue
        if key in heading_set or (len(ln)<32 and not ln.startswith(('•','-')) and ln.isupper()):
            story.append(Paragraph(clean.upper(), styles["heading"])); continue
        if ln.startswith(('•','-')):
            story.append(Paragraph(html.escape(ln.lstrip('•- ').strip()), styles["bullet"], bulletText="•")); continue
        story.append(Paragraph(clean, styles["body"]))
    doc.build(story or [Paragraph(html.escape(title or "WorkZo CV"), styles["name"])])
    buffer.seek(0)
    return buffer.getvalue()

# Keep references to the previous implementations, then replace with a safer final version.
try:
    _workzo_prev_make_styled_pdf_from_cv_text = make_styled_pdf_from_cv_text
except Exception:
    _workzo_prev_make_styled_pdf_from_cv_text = None
try:
    _workzo_prev_make_styled_pdf_from_structured_preview = make_styled_pdf_from_structured_preview
except Exception:
    _workzo_prev_make_styled_pdf_from_structured_preview = None

def make_styled_pdf_from_cv_text(title: str, cv_text: str, template_name: str = "ATS Resume", target_country: str = "") -> bytes:
    # Prefer the robust text PDF because it preserves readable resume structure.
    return _workzo_resume_text_pdf_safe(title, clean_generated_cv_text_for_template(cv_text or ""))

def make_styled_pdf_from_structured_preview(title: str, structured_data: Dict[str, Any], template_name: str = "ATS Resume", target_country: str = "") -> bytes:
    data = _workzo_final_preview_data(structured_data or {})
    text = workzo_build_cv_text_from_editable(data)
    return _workzo_resume_text_pdf_safe(title, text)


# =========================================================
# WorkZo v9: robust structured CV cleanup before rendering/PDF
# =========================================================
def wz9_normalize_project_item(item):
    import ast, json, re
    if isinstance(item, str):
        raw = item.strip()
        # Handle strings like "{'name': 'Magist', 'bullets': [...]}"
        if raw.startswith('{') and raw.endswith('}'):
            try:
                item = ast.literal_eval(raw)
            except Exception:
                try:
                    item = json.loads(raw)
                except Exception:
                    return {"name": re.sub(r"[{}'\"]", "", raw)[:80], "bullets": []}
        else:
            return {"name": raw.strip("- •"), "bullets": []}
    if isinstance(item, dict):
        name = item.get('name') or item.get('project') or item.get('title') or ''
        # Some broken builds put the full dict inside name.
        if isinstance(name, str) and name.strip().startswith('{') and name.strip().endswith('}'):
            try:
                inner = ast.literal_eval(name.strip())
                if isinstance(inner, dict):
                    name = inner.get('name') or inner.get('title') or name
                    bullets = inner.get('bullets') or item.get('bullets') or []
                else:
                    bullets = item.get('bullets') or []
            except Exception:
                bullets = item.get('bullets') or []
        else:
            bullets = item.get('bullets') or item.get('description') or []
        if isinstance(bullets, str):
            bullets = [x.strip(' -•') for x in bullets.replace(';','\n').splitlines() if x.strip()]
        if not isinstance(bullets, list):
            bullets = [str(bullets)] if bullets else []
        return {"name": wz135_pdf_safe_text(name), "bullets": [wz135_pdf_safe_text(x) for x in bullets if str(x).strip()]}
    return {"name": wz135_pdf_safe_text(item), "bullets": []}

def wz9_clean_structured_resume_data(data):
    data = validate_resume_dates_and_sections(_coerce_structured_resume_schema(data or {}))
    data['projects'] = [wz9_normalize_project_item(x) for x in (data.get('projects') or [])]
    for key in ['core_skills','tools_technologies','languages','certifications']:
        data[key] = [wz135_pdf_safe_text(x) for x in _as_list(data.get(key)) if str(x).strip()]
    for job in data.get('work_experience') or []:
        if isinstance(job, dict):
            job['bullets'] = [wz135_pdf_safe_text(x) for x in _as_list(job.get('bullets')) if str(x).strip()]
    return data

# Wrap the strict PDF renderer so every PDF gets cleaned data first.
try:
    _workzo_old_strict_structured_pdf = _strict_structured_pdf
    def _strict_structured_pdf(title: str, structured_data: dict, template_name: str = "ATS Resume", target_country: str = "") -> bytes:
        return _workzo_old_strict_structured_pdf(title, wz9_clean_structured_resume_data(structured_data or {}), template_name, target_country)
except Exception:
    pass


# =========================================================
# WorkZo v12: final robust CV cleanup + PDF safety layer
# Prevents raw dict/list strings such as {'name': 'Magist', 'bullets': [...]} from appearing.
# =========================================================
def _wz12_literal(value):
    try:
        import ast, json
        if isinstance(value, str):
            t=value.strip()
            if (t.startswith('{') and t.endswith('}')) or (t.startswith('[') and t.endswith(']')):
                try: return ast.literal_eval(t)
                except Exception:
                    try: return json.loads(t)
                    except Exception: return value
        return value
    except Exception:
        return value

def _wz12_list(value):
    value=_wz12_literal(value)
    if value is None or value=='': return []
    if isinstance(value, list): return value
    if isinstance(value, tuple): return list(value)
    return [value]

def _wz12_text(value):
    import re
    value=_wz12_literal(value)
    if isinstance(value, dict):
        if 'name' in value and ('bullets' in value or 'description' in value):
            return _wz12_project_text(value)
        return ' '.join(_wz12_text(v) for v in value.values() if str(v or '').strip())
    if isinstance(value, list):
        return ', '.join(_wz12_text(v) for v in value if str(v or '').strip())
    txt=str(value or '')
    reps={
        'for m':'form','in for m':'inform','in itiative':'initiative','In dian':'Indian','You Tube':'YouTube',
        'Text Blob':'TextBlob','Manage Engine':'ManageEngine','Service Desk':'ServiceDesk','My SQL':'MySQL',
        'Linked In':'LinkedIn','ð□□':'','ð□':'','â€™':"'",'â€“':'–','â€”':'—','â€¢':'•','Â':'',
    }
    for a,b in reps.items(): txt=txt.replace(a,b)
    txt=re.sub(r'[\ufffd]+','',txt)
    txt=re.sub(r'\s+',' ',txt).strip()
    return txt

def _wz12_project_text(item):
    item=_wz12_literal(item)
    if isinstance(item, str):
        lit=_wz12_literal(item)
        if lit is not item: return _wz12_project_text(lit)
        return _wz12_text(item)
    if isinstance(item, dict):
        name=_wz12_literal(item.get('name') or item.get('title') or item.get('project') or '')
        if isinstance(name, dict):
            # previous broken builds nested the full project dict in name
            item=name
            name=item.get('name') or item.get('title') or item.get('project') or ''
        bullets=item.get('bullets') or item.get('details') or item.get('description') or []
        if isinstance(bullets, str):
            lit=_wz12_literal(bullets)
            if isinstance(lit, list): bullets=lit
            else: bullets=[x.strip(' -•*') for x in bullets.replace(';','\n').splitlines() if x.strip()]
        lines=[]
        nm=_wz12_text(name)
        if nm: lines.append(nm)
        for b in _wz12_list(bullets):
            bt=_wz12_text(b).strip(' -•*')
            if bt: lines.append('- '+bt)
        return '\n'.join(lines).strip()
    return _wz12_text(item)

def _wz12_normalize_structured(data):
    try:
        data=_wz12_literal(data)
        if not isinstance(data, dict): return {}
        data=dict(data)
        # Normalize projects deeply
        projects=[]
        for p in _wz12_list(data.get('projects')):
            p=_wz12_literal(p)
            if isinstance(p, dict):
                name=_wz12_literal(p.get('name') or p.get('title') or p.get('project') or '')
                if isinstance(name, dict): p=name; name=p.get('name') or p.get('title') or p.get('project') or ''
                bullets=p.get('bullets') or p.get('details') or p.get('description') or []
                projects.append({'name':_wz12_text(name), 'bullets':[_wz12_text(x).strip(' -•*') for x in _wz12_list(bullets) if _wz12_text(x).strip()]})
            elif str(p or '').strip():
                txt=_wz12_project_text(p)
                lines=[x.strip() for x in txt.splitlines() if x.strip()]
                if lines:
                    projects.append({'name':lines[0].strip(' -•*'), 'bullets':[x.strip(' -•*') for x in lines[1:]]})
        data['projects']=projects
        for key in ['core_skills','skills','tools_technologies','languages','certifications']:
            if key in data:
                data[key]=[_wz12_text(x).strip(' -•*') for x in _wz12_list(data.get(key)) if _wz12_text(x).strip()]
        for key in ['work_experience','experience']:
            if key in data:
                out=[]
                for j in _wz12_list(data.get(key)):
                    j=_wz12_literal(j)
                    if isinstance(j, dict):
                        out.append({
                            'title':_wz12_text(j.get('title') or j.get('role') or j.get('position')),
                            'company':_wz12_text(j.get('company') or j.get('employer') or j.get('organization')),
                            'dates':_wz12_text(j.get('dates') or j.get('date') or ''),
                            'bullets':[_wz12_text(x).strip(' -•*') for x in _wz12_list(j.get('bullets') or j.get('responsibilities') or j.get('achievements')) if _wz12_text(x).strip()]
                        })
                    elif str(j or '').strip():
                        out.append({'title':_wz12_text(j),'company':'','dates':'','bullets':[]})
                data['work_experience']=out
        return data
    except Exception:
        return data if isinstance(data, dict) else {}

def _wz12_clean_cv_text(text):
    import re
    out=[]
    for line in str(text or '').splitlines():
        raw=line.strip()
        candidate=raw.lstrip('-•* ').strip()
        lit=_wz12_literal(candidate)
        if isinstance(lit, dict) and ('name' in lit or 'title' in lit or 'bullets' in lit):
            proj=_wz12_project_text(lit)
            if proj:
                out.extend(proj.splitlines())
            continue
        cleaned=_wz12_text(raw)
        if cleaned:
            out.append(cleaned)
    text='\n'.join(out)
    text=re.sub(r'\n{3,}','\n\n',text).strip()
    return text

try:
    _wz12_prev_pdf_text = make_styled_pdf_from_cv_text
except Exception:
    _wz12_prev_pdf_text = None
try:
    _wz12_prev_pdf_struct = make_styled_pdf_from_structured_preview
except Exception:
    _wz12_prev_pdf_struct = None

def make_styled_pdf_from_cv_text(title: str, cv_text: str, template_name: str = "ATS Resume", target_country: str = "") -> bytes:
    return _workzo_resume_text_pdf_safe(_wz12_text(title or 'WorkZo CV'), _wz12_clean_cv_text(cv_text or ''))

def make_styled_pdf_from_structured_preview(title: str, structured_data: dict, template_name: str = "ATS Resume", target_country: str = "") -> bytes:
    data=_wz12_normalize_structured(structured_data or {})
    try:
        text=workzo_build_cv_text_from_editable(data)
    except Exception:
        text=''
    return _workzo_resume_text_pdf_safe(_wz12_text(title or 'WorkZo CV'), _wz12_clean_cv_text(text))
