"""
WorkZo AI - recovered helpers patch.
Auto-generated from app_old.py to restore helpers lost during modular split.
No feature changes: functions are copied from the old working app.py when they were missing from split modules.
"""
# The modular loader executes all files in the same global namespace.
# These imports mirror app_old.py and are intentionally broad because copied helpers
# depend on shared globals from other modules.
import os
import re
import time
import json
import csv
import hashlib
import html
import uuid
import base64
from pathlib import Path
from io import BytesIO
import urllib.parse
import urllib.request
import subprocess
import tempfile
import shutil
from typing import Dict, Optional, List, Tuple, Any

try:
    import streamlit as st
    import streamlit.components.v1 as components
except Exception:
    st = None
    components = None

try:
    import plotly.graph_objects as go
except Exception:
    go = None

try:
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
except Exception:
    SimpleDocTemplate = Paragraph = ParagraphStyle = Spacer = getSampleStyleSheet = A4 = mm = Table = TableStyle = KeepTogether = colors = None

try:
    from docx import Document
    from docx.shared import Pt, Inches
    from docx.enum.text import WD_ALIGN_PARAGRAPH
except Exception:
    Document = Pt = Inches = WD_ALIGN_PARAGRAPH = None

def clean_ui_text(value: str) -> str:
    """Fix common mojibake characters before showing UI text."""
    text = str(value or "")
    replacements = {
        "Ã": "ß", "Ã¤": "ä", "Ã¶": "ö", "Ã¼": "ü", "Ã": "Ä", "Ã": "Ö", "Ã": "Ü",
        "Ã©": "é", "Ã¨": "è", "Ã¡": "á", "Ã³": "ó", "Ã­": "í", "Ã±": "ñ",
        "€": "€", "â": "–", "â": "—", "â": "'", "â": "\"",
        "â": "\"", "â¦": "…", "Â ": " ", "Â": "", "ï¸": "", "�": "",
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    return text


def get_user_status_context() -> str:
    return st.session_state.get("user_status", "Not specified")


def get_target_country_context() -> str:
    """Return the real application market. If applying abroad, target market overrides current country."""
    return st.session_state.get("migration_country") or st.session_state.get("country", "Not specified")


def get_target_role_context() -> str:
    return st.session_state.get("target_role_context", "") or st.session_state.get("current_role_detected", "") or "Not specified"


def compact_cv_context(max_chars: int = 3500) -> str:
    cv = st.session_state.get("cv_text", "") or ""
    cv = re.sub(r"\s+", " ", cv).strip()
    return cv[:max_chars] + ("..." if len(cv) > max_chars else "")


def clean_context_value(value, fallback: str = "Not available") -> str:
    value = str(value or "").strip()
    return value if value else fallback


def build_career_intelligence_layer(max_cv_chars: int = 4500) -> str:
    """
    Central context layer used before every AI call.
    This makes WorkZo's answers specific, country-aware, and less generic.
    """
    country = clean_context_value(st.session_state.get("country"), "Not selected")
    target_country = clean_context_value(st.session_state.get("migration_country") or st.session_state.get("country"), country)
    language = clean_context_value(st.session_state.get("preferred_language"), "English")
    user_status = clean_context_value(st.session_state.get("user_status"), "Not selected")
    target_role = clean_context_value(get_target_role_context(), "Not specified")

    return f"""
CAREER INTELLIGENCE LAYER
User selected country: {country}
Target / application country: {target_country}
Preferred output language: {language}
Current career situation: {user_status}
Target role or role direction: {target_role}
Career goal: {clean_context_value(st.session_state.get("career_goal"))}

AI-extracted profile summary:
{clean_context_value(st.session_state.get("profile_summary"))}

AI-extracted current role:
{clean_context_value(st.session_state.get("current_role_detected"))}

AI-extracted key skills:
{clean_context_value(st.session_state.get("key_skills_detected"))}

Detected resume strengths:
{clean_context_value(st.session_state.get("resume_strengths"))}

Detected resume improvements:
{clean_context_value(st.session_state.get("resume_improvements"))}

Current scores:
- Resume score: {clean_context_value(st.session_state.get("cv_score_value"), "Not calculated")}
- ATS score: {clean_context_value(st.session_state.get("ats_score_value"), "Not calculated")}
- Country readiness score: {clean_context_value(st.session_state.get("country_readiness_score_value"), "Not calculated")}

CV / profile text excerpt:
{compact_cv_context(max_cv_chars) or "No CV text available"}
""".strip()


def workzo_expert_context() -> str:
    return build_career_intelligence_layer()


def normalize_answer_language(language: str) -> str:
    language = (language or "English").strip()
    return language if language else "English"


def language_guard_rules(answer_lang: str) -> str:
    answer_lang = normalize_answer_language(answer_lang)
    if answer_lang == "German":
        return """
STRICT LANGUAGE MODE: German.
- Write the final answer completely in natural German.
- Do not mix English sentence starters, headings, explanations, or filler words.
- Allowed English only: company names, software/tool names, job titles when commonly used, URLs, email addresses, code, and exact keywords from a job ad/CV.
- Use German career terms where natural: Lebenslauf, Anschreiben, Berufserfahrung, Kenntnisse, Fahigkeiten, Ausbildung, Bewerbungsunterlagen.
- If you accidentally produce English headings or mixed English/German, rewrite the whole answer in German before returning it.
""".strip()
    if answer_lang == "Dutch":
        return """
STRICT LANGUAGE MODE: Dutch.
- Write the final answer completely in natural Dutch.
- Do not mix English sentence starters, headings, explanations, or filler words.
- Allowed English only: company names, software/tool names, job titles when commonly used, URLs, email addresses, code, and exact keywords from a job ad/CV.
- Use Dutch career terms where natural: cv, motivatiebrief, werkervaring, vaardigheden, opleiding, sollicitatie.
- If you accidentally produce English headings or mixed English/Dutch, rewrite the whole answer in Dutch before returning it.
""".strip()
    if answer_lang == "English":
        return """
STRICT LANGUAGE MODE: English.
- Write the final answer completely in English.
- Do not switch into German, Dutch, or another language unless the user specifically asks for a translation example.
""".strip()
    return f"""
STRICT LANGUAGE MODE: {answer_lang}.
- Write the final answer completely in natural {answer_lang}.
- Do not mix English sentence starters, headings, explanations, or filler words unless they are exact job titles, software/tool names, company names, URLs, email addresses, code, or keywords copied from the user's CV/job ad.
- Translate all guidance, headings, labels, and conclusions into {answer_lang}.
- If you accidentally produce mixed-language output, rewrite the whole answer in {answer_lang} before returning it.
""".strip()


def quality_system_prompt(answer_lang: str, system_addition: str = "") -> str:
    return f"""
You are WorkZo AI, a senior international career strategist, resume consultant, ATS specialist, interview coach, and job-search advisor.

Your job is NOT to give generic AI advice. Your job is to give precise, personalized, practical guidance based on:
- the user's CV/profile
- the user's status: fresh graduate, migrant, career changer, experienced professional, etc.
- the target country and local hiring expectations
- the user's target role and current experience level

{language_guard_rules(answer_lang)}

Quality rules:
1. Be specific. Avoid generic sentences like "improve your skills" unless you say exactly which skill, why it matters, and what to do next.
2. Use the user's actual CV/profile details whenever available. Reference concrete roles, tools, skills, industries, projects, and gaps from the provided context.
3. Be honest about weak fit, missing experience, language gaps, unrealistic seniority, or template mismatch.
4. Give prioritized actions: what to do first, second, third.
5. For migration/country-specific topics, mention local CV expectations, language expectations, and role-market fit.
6. For fresh graduates, focus on portfolio projects, internships, entry-level roles, keywords, and proof of skill.
7. For career changers, focus on transferable skills, bridge roles, portfolio proof, and realistic role titles.
8. For experienced users, focus on positioning, measurable achievements, leadership/impact, and market fit.
9. Keep output structured with useful headings and concise bullets. Prefer 3-5 strong points over long generic lists.
10. Never invent employers, degrees, certifications, dates, or achievements.
11. If information is missing, clearly say what is missing and give a best-effort recommendation.
12. End with a clear "Next best action" when appropriate.
13. Every answer must feel like it was written for this user, this country, and this career situation.
14. Do not give generic advice such as "network more", "improve your resume", or "learn more skills" without converting it into a concrete action.

Use this context where relevant:
{workzo_expert_context()}

{system_addition}
""".strip()


def build_quality_prompt(task: str, user_input: str, expected_structure: str = "") -> str:
    return f"""
Task: {task}

{build_career_intelligence_layer()}

User input:
{user_input}

Expected output structure:
{expected_structure}

Advanced output rules:
- Start with the most useful answer first, not a long introduction.
- Give practical, tailored, country-aware, and status-aware advice.
- Avoid generic advice. Mention concrete skills, role titles, keywords, CV sections, or actions wherever possible.
- Keep the answer easy to scan with short sections and bullets.
- When useful, include a short "Why this matters" and a "Next best action".
- Follow the selected preferred language strictly. Do not mix languages.
""".strip()


def render_error_or_success(result: str):
    if result.startswith("ERROR:"):
        st.error(txt("ai_unavailable"))
        st.caption(result)
        return False
    return True


def parse_score(text: str) -> Optional[int]:
    if not text:
        return None

    match = re.search(r'(\d{1,3})\s*/\s*100', text)
    if match:
        value = int(match.group(1))
        if 0 <= value <= 100:
            return value

    match = re.search(r'(?<!\d)(\d{1,3})(?!\d)', text)
    if match:
        value = int(match.group(1))
        if 0 <= value <= 100:
            return value

    return None


def numbered_sections_to_markdown(text: str) -> Dict[str, str]:
    """Parse AI sections like `1. Title`, `### 1. Title`, or `**1. Title**`.
    This prevents the same full response appearing in every expander.
    """
    text = text or ""
    sections = {}
    pattern = r'(?m)^\s*(?:#{1,6}\s*)?(?:\*\*)?(\d+)\.\s*(.+?)(?:\*\*)?\s*$'
    matches = list(re.finditer(pattern, text))
    if not matches:
        return {"Result": text.strip()}

    for i, match in enumerate(matches):
        title = match.group(2).strip()
        title = title.replace("**", "").replace("__", "").strip().rstrip(":")
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        body = re.sub(r"^[--—\s]+", "", body).strip()
        sections[title] = body
    return sections


def render_section_cards(result: str, default_expand: bool = False):
    if not render_error_or_success(result):
        return
    sections = numbered_sections_to_markdown(result)
    for title, body in sections.items():
        with st.expander(title, expanded=default_expand):
            st.write(body if body else "—")


def clamp_score_value(value, default: int = 0) -> int:
    try:
        score = int(float(value))
    except Exception:
        score = default
    return max(0, min(100, score))


def verdict_from_score(score: int) -> str:
    if score >= 80:
        return "Strong apply"
    if score >= 60:
        return "Apply, but tailor first"
    if score >= 40:
        return "Possible, but risky"
    return "Skip or improve first"


def render_list_items(items, empty_text: str = "—"):
    if isinstance(items, str):
        items = [items]
    if not items:
        st.write(empty_text)
        return
    for item in items:
        if str(item).strip():
            st.markdown(f"- {str(item).strip()}")


def render_requirement_checklist(requirements):
    if not isinstance(requirements, list) or not requirements:
        st.info("No requirement checklist was generated.")
        return
    st.markdown("#### Requirement checklist")
    for req in requirements:
        if not isinstance(req, dict):
            continue
        requirement = str(req.get("requirement", "Requirement")).strip()
        status = str(req.get("status", "Partial")).strip()
        evidence = str(req.get("evidence", "")).strip()
        status_lower = status.lower()
        icon = "✓" if "strong" in status_lower or "match" in status_lower else "No" if "missing" in status_lower or "gap" in status_lower else "Maybe"
        st.markdown(f"**{icon} {requirement}**  ")
        if evidence:
            st.caption(evidence)


def render_understand_job_analysis(data: dict):
    """Render Understand Job as a compact decision assistant instead of a long report."""
    if not isinstance(data, dict):
        st.warning("The job analysis could not be structured. Please try again.")
        return

    fit_score = clamp_score_value(data.get("fit_score", 0))
    skill_score = clamp_score_value(data.get("skill_match", 0))
    exp_score = clamp_score_value(data.get("experience_match", 0))
    lang_score = clamp_score_value(data.get("language_match", 0))
    keyword_score = clamp_score_value(data.get("keyword_match", 0))
    verdict = str(data.get("verdict") or verdict_from_score(fit_score)).strip()
    main_reason = str(data.get("main_reason") or "Review the match breakdown before applying.").strip()

    st.markdown("### Job Fit Summary")
    st.markdown(f"""
<div class='next-action-card'>
  <div class='next-action-label'>Decision assistant</div>
  <div class='next-action-title'>Job Fit: {fit_score}/100 — {html.escape(verdict)}</div>
  <div class='next-action-copy'>{html.escape(main_reason)}</div>
</div>
""", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Skill match", f"{skill_score}/100")
    c2.metric("Experience match", f"{exp_score}/100")
    c3.metric("Language match", f"{lang_score}/100")
    c4.metric("Keyword match", f"{keyword_score}/100")

    comparison = data.get("cv_job_comparison", {}) if isinstance(data.get("cv_job_comparison"), dict) else {}
    if comparison:
        st.markdown("### CV vs Job")
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.markdown("**Job asks for**")
            render_list_items(comparison.get("job_asks_for", []))
        with col_b:
            st.markdown("**Your CV shows**")
            render_list_items(comparison.get("cv_shows", []))
        with col_c:
            st.markdown("**Main gaps**")
            render_list_items(comparison.get("main_gaps", []))

    render_requirement_checklist(data.get("requirement_checklist", []))

    col_gap, col_tailor = st.columns(2)
    with col_gap:
        with st.expander("Gaps & Risks", expanded=True):
            render_list_items(data.get("gaps_and_risks", []))
    with col_tailor:
        with st.expander("How to Tailor Your CV", expanded=True):
            st.markdown("**Suggested CV bullets**")
            render_list_items(data.get("tailored_cv_bullets", []))

    with st.expander("Interview Preparation", expanded=False):
        st.markdown("**Likely interview focus**")
        render_list_items(data.get("interview_focus", []))
        questions = data.get("interview_questions", [])
        if questions:
            st.markdown("**Sample interview questions**")
            for idx, q in enumerate(questions, 1):
                st.markdown(f"{idx}. {q}")

    salary_note = str(data.get("salary_estimate_note", "")).strip()
    if salary_note:
        with st.expander("Salary estimate — optional", expanded=False):
            st.write(salary_note)
            st.caption("Approximate only. Verify with local salary sources and the employer.")

    st.markdown("### Next Best Action")
    st.info(str(data.get("next_best_action") or "Tailor your CV before applying.").strip())


def normalize_resume_dates(text_value: str) -> str:
    """Repair PDF/AI date splits and protect resume date ranges from ugly line breaks."""
    text_value = text_value or ""
    text_value = text_value.replace("\r\n", "\n").replace("\r", "\n")

    # Collapse dates split across lines, including blank lines:
    # 10/
    # 2018 - 01
    # /2020  -> 10/2018 - 01/2020
    for _ in range(4):
        text_value = re.sub(r"(\b\d{1,2})\s*/\s*\n+\s*(\d{4}\b)", r"\1/\2", text_value)
        text_value = re.sub(r"(\b\d{1,2})\s*\n+\s*/\s*(\d{4}\b)", r"\1/\2", text_value)
        text_value = re.sub(r"(\b\d{1,2}/\d{4})\s*\n+\s*[--—]\s*\n+\s*(\d{1,2}/\d{4}\b)", r"\1 - \2", text_value)
        text_value = re.sub(r"(\b\d{1,2}/\d{4})\s*[--—]\s*\n+\s*(\d{1,2}/\d{4}\b)", r"\1 - \2", text_value)
        text_value = re.sub(r"(\b\d{4})\s*\n+\s*[--—]\s*\n+\s*(\d{4}|Present|Current|Heute|Now)\b", r"\1 - \2", text_value, flags=re.I)
        text_value = re.sub(r"(\b\d{4})\s*[--—]\s*\n+\s*(\d{4}|Present|Current|Heute|Now)\b", r"\1 - \2", text_value, flags=re.I)

    # Fix slash spacing and range spacing inside a single line.
    text_value = re.sub(r"\b(\d{1,2})\s*/\s*(\d{4})\b", r"\1/\2", text_value)
    text_value = re.sub(r"\b(\d{1,2}/\d{4})\s*[--—]\s*(\d{1,2}/\d{4}|Present|Current|Heute|Now)\b", r"\1 - \2", text_value, flags=re.I)
    text_value = re.sub(r"\b(\d{4})\s*[--—]\s*(\d{4}|Present|Current|Heute|Now)\b", r"\1 - \2", text_value, flags=re.I)

    text_value = re.sub(r"\bBer\s+l\s+in\b", "Berlin", text_value, flags=re.IGNORECASE)
    return text_value


def sanitize_pdf_text(text_value: str) -> str:
    """Make text safer for ReportLab standard fonts and ATS parsing."""
    text_value = str(text_value or "")
    replacements = {
        "\u00a0": " ", "\ufeff": "",
        "\u2013": "-", "\u2014": "-", "\u2212": "-",
        "\u2022": "-", "\u25cf": "-", "\u25aa": "-", "\u25e6": "-",
        "\u2018": "'", "\u2019": "'", "\u201a": "'",
        "\u201c": '"', "\u201d": '"', "\u201e": '"',
        "\u2026": "...", "\u20ac": "EUR", "\u00a3": "GBP", "\u00a5": "JPY",
        "\u2122": "TM", "\u00ae": "(R)", "\u00a9": "(C)",
        "\u2713": "Yes", "\u2714": "Yes", "\u2717": "No", "\u274c": "No",
        "\u2192": "->", "\u2190": "<-", "\u00b7": "-", "\u2605": "*",
        "-": "-", "—": "-", "•": "-", "✓": "Yes", "Done": "Yes", "No": "No",
    }
    for old, new in replacements.items():
        text_value = text_value.replace(old, new)
    text_value = text_value.replace("ß", "ss")
    text_value = re.sub(r"[ \t]+", " ", text_value)
    text_value = re.sub(r"\n{3,}", "\n\n", text_value)
    return text_value.strip()


def make_minimal_pdf_from_text(title: str, body: str) -> bytes:
    """Create a valid simple PDF without external libraries, used as a safe fallback."""
    def esc_pdf(txt: str) -> str:
        txt = sanitize_pdf_text(txt or "").encode("latin-1", "replace").decode("latin-1")
        return txt.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    cleaned = sanitize_pdf_text(strip_markdown_for_resume(body))
    lines = []
    for raw in cleaned.splitlines():
        line = raw.strip()
        if line:
            while len(line) > 95:
                cut = line.rfind(" ", 0, 95)
                if cut < 35:
                    cut = 95
                lines.append(line[:cut].strip())
                line = line[cut:].strip()
            lines.append(line)
        else:
            lines.append("")
    pages = []
    current = []
    for line in lines:
        current.append(line)
        if len(current) >= 48:
            pages.append(current)
            current = []
    if current or not pages:
        pages.append(current)
    page_ids = []
    content_objects = []
    page_objects = []
    next_obj_id = 4
    for page_lines in pages:
        content_id = next_obj_id
        page_id = next_obj_id + 1
        next_obj_id += 2
        page_ids.append(page_id)
        stream_lines = ["BT", "/F1 10 Tf", "50 800 Td", "14 TL"]
        first = True
        for line in page_lines:
            if not first:
                stream_lines.append("T*")
            first = False
            if line:
                stream_lines.append(f"({esc_pdf(line)}) Tj")
            else:
                stream_lines.append("T*")
        stream_lines.append("ET")
        stream = "\n".join(stream_lines).encode("latin-1", "replace")
        content_objects.append((content_id, f"<< /Length {len(stream)} >>\nstream\n".encode("latin-1") + stream + b"\nendstream"))
        page_objects.append((page_id, f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 3 0 R >> >> /Contents {content_id} 0 R >>".encode("latin-1")))
    all_objects = [
        (1, b"<< /Type /Catalog /Pages 2 0 R >>"),
        (2, f"<< /Type /Pages /Kids [{' '.join(f'{pid} 0 R' for pid in page_ids)}] /Count {len(page_ids)} >>".encode("latin-1")),
        (3, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"),
    ] + content_objects + page_objects
    all_objects.sort(key=lambda x: x[0])
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = {0: 0}
    for obj_id, content in all_objects:
        offsets[obj_id] = len(pdf)
        pdf.extend(f"{obj_id} 0 obj\n".encode("latin-1"))
        pdf.extend(content)
        pdf.extend(b"\nendobj\n")
    xref_pos = len(pdf)
    max_id = max(offsets)
    pdf.extend(f"xref\n0 {max_id+1}\n".encode("latin-1"))
    pdf.extend(b"0000000000 65535 f \n")
    for i in range(1, max_id+1):
        pdf.extend(f"{offsets.get(i, 0):010d} 00000 n \n".encode("latin-1"))
    pdf.extend(f"trailer\n<< /Size {max_id+1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF".encode("latin-1"))
    return bytes(pdf)


def country_resume_rules_text(country: str) -> str:
    rules = get_country_cv_rules(country)
    return f"""
Country style rules for {country}:
- Recommended length: about {rules.get('pages', 2)} page(s), depending on experience.
- Recommended sections: {', '.join(rules.get('sections', []))}.
- Photo: {'allowed/optional' if rules.get('photo') else 'do not include'}.
- Date of birth / sensitive personal details: {'allowed only if user already provided and it is appropriate' if rules.get('dob') else 'do not include'}.
- Important exclusions: {rules.get('avoid', 'Avoid sensitive personal details and do not invent information.')}.
""".strip()


def make_docx_from_cv_text(title: str, cv_text: str, template_name: str = "ATS Resume", target_country: str = "") -> bytes:
    """Create a real editable DOCX resume. Falls back to TXT bytes if python-docx is unavailable."""
    cleaned = strip_markdown_for_resume(cv_text)
    if Document is None:
        return cleaned.encode("utf-8")

    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(0.55)
    section.bottom_margin = Inches(0.55)
    section.left_margin = Inches(0.65)
    section.right_margin = Inches(0.65)

    style = doc.styles["Normal"]
    style.font.name = "Arial"
    style.font.size = Pt(10.5)

    lines = [line.rstrip() for line in cleaned.splitlines()]
    first_written = False
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        heading_candidate = line.upper() == line and len(line) <= 45 and not line.startswith("-")
        if not first_written:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(line)
            run.bold = True
            run.font.size = Pt(18)
            first_written = True
        elif line.startswith("- "):
            p = doc.add_paragraph(style=None)
            p.style = doc.styles["List Bullet"]
            p.add_run(line[2:].strip())
        elif heading_candidate or line.endswith(":"):
            p = doc.add_paragraph()
            run = p.add_run(line.rstrip(":"))
            run.bold = True
            run.font.size = Pt(12)
        else:
            doc.add_paragraph(line)

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()


def _cv_flowables_for_pdf(text_value: str, styles, title: str = ""):
    """Convert a CV section into ReportLab flowables with neat bullets."""
    flow = []
    if title:
        flow.append(Paragraph(title.upper(), styles["section"]))
    text_value = sanitize_pdf_text(normalize_resume_dates(text_value or ""))
    for raw in text_value.splitlines():
        line = raw.strip()
        if not line:
            flow.append(Spacer(1, 3))
            continue
        safe = html.escape(line)
        if line.startswith(("- ", "• ", "* ", "• ")):
            flow.append(Paragraph(safe.lstrip("-••* ").strip(), styles["bullet"], bulletText="-"))
        elif line.upper() == line and len(line) <= 48 and not re.search(r"\d", line):
            flow.append(Paragraph(safe.title() if len(line) < 8 else safe, styles["mini_heading"]))
        else:
            flow.append(Paragraph(safe, styles["body"]))
    if not text_value.strip():
        flow.append(Paragraph("-", styles["muted"]))
    return flow


def _escape_pdf(text_value: str) -> str:
    return html.escape(sanitize_pdf_text(str(text_value or "")))


def _as_editor_rows(value, kind: str = "experience") -> list:
    rows = []
    if isinstance(value, dict):
        value = [value]
    for item in value or []:
        if not isinstance(item, dict):
            continue
        if kind == "education":
            rows.append({
                "degree": str(item.get("degree") or item.get("qualification") or ""),
                "institution": str(item.get("institution") or item.get("school") or item.get("university") or ""),
                "dates": str(item.get("dates") or item.get("year") or "")
            })
        elif kind == "project":
            rows.append({
                "name": str(item.get("name") or item.get("title") or ""),
                "bullets": "\n".join(_as_list(item.get("bullets") or item.get("description") or item.get("details")))
            })
        else:
            rows.append({
                "title": str(item.get("title") or item.get("role") or ""),
                "company": str(item.get("company") or item.get("employer") or ""),
                "dates": str(item.get("dates") or ""),
                "bullets": "\n".join(_as_list(item.get("bullets") or item.get("achievements") or item.get("responsibilities")))
            })
    if not rows:
        rows = [{"degree": "", "institution": "", "dates": ""}] if kind == "education" else ([{"name": "", "bullets": ""}] if kind == "project" else [{"title": "", "company": "", "dates": "", "bullets": ""}])
    return rows


def _rows_to_experience_items(rows) -> list:
    items = []
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        title = str(row.get("title") or "").strip()
        company = str(row.get("company") or "").strip()
        dates = _normalize_date_text(str(row.get("dates") or "").strip())
        bullets = [b.strip(" -••\t") for b in str(row.get("bullets") or "").splitlines() if b.strip(" -••\t")]
        if title or company or dates or bullets:
            items.append({"title": title, "company": company, "dates": dates, "bullets": bullets})
    return sort_resume_items_by_date(items)


def _rows_to_education_items(rows) -> list:
    items = []
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        degree = str(row.get("degree") or "").strip()
        institution = str(row.get("institution") or "").strip()
        dates = _normalize_date_text(str(row.get("dates") or "").strip())
        if degree or institution or dates:
            items.append({"degree": degree, "institution": institution, "dates": dates, "year": ""})
    return sort_resume_items_by_date(items)


def _rows_to_project_items(rows) -> list:
    items = []
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        name = str(row.get("name") or "").strip()
        bullets = [b.strip(" -••\t") for b in str(row.get("bullets") or "").splitlines() if b.strip(" -••\t")]
        if name or bullets:
            items.append({"name": name, "bullets": bullets})
    return items


def _structured_experience_flowables(items, styles, title: str = "Experience"):
    flow = []
    if title:
        flow.append(Paragraph(title.upper(), styles["section"]))
    items = sort_resume_items_by_date(items or [])
    if not items:
        flow.append(Paragraph("-", styles["muted"]))
        return flow
    for job in items:
        if not isinstance(job, dict):
            continue
        heading = " | ".join([x for x in [job.get("title"), job.get("company"), _normalize_date_text(job.get("dates") or "")] if str(x or "").strip()])
        block = []
        if heading:
            block.append(Paragraph(_escape_pdf(heading), styles["mini_heading"]))
        for bullet in _as_list(job.get("bullets") or job.get("achievements") or job.get("responsibilities")):
            b = str(bullet or "").strip(" -••\t")
            if b:
                block.append(Paragraph(_escape_pdf(b), styles["bullet"], bulletText="-"))
        block.append(Spacer(1, 4))
        flow.append(KeepTogether(block) if KeepTogether is not None else block)
    return flow


def _structured_education_flowables(items, styles, title: str = "Education"):
    flow = []
    if title:
        flow.append(Paragraph(title.upper(), styles["section"]))
    items = sort_resume_items_by_date(items or [])
    if not items:
        flow.append(Paragraph("-", styles["muted"]))
        return flow
    for ed in items:
        if not isinstance(ed, dict):
            continue
        line = " | ".join([x for x in [ed.get("degree"), ed.get("institution"), _normalize_date_text(ed.get("dates") or ed.get("year") or "")] if str(x or "").strip()])
        if line:
            block = [Paragraph(_escape_pdf(line), styles["body"]), Spacer(1, 3)]
            flow.append(KeepTogether(block) if KeepTogether is not None else block)
    return flow


def _structured_projects_flowables(items, styles, title: str = "Projects"):
    flow = []
    if title:
        flow.append(Paragraph(title.upper(), styles["section"]))
    if not items:
        flow.append(Paragraph("-", styles["muted"]))
        return flow
    for pr in items or []:
        if not isinstance(pr, dict):
            continue
        block = []
        name = str(pr.get("name") or pr.get("title") or "").strip()
        if name:
            block.append(Paragraph(_escape_pdf(name), styles["mini_heading"]))
        for bullet in _as_list(pr.get("bullets") or pr.get("description") or pr.get("details")):
            b = str(bullet or "").strip(" -••\t")
            if b:
                block.append(Paragraph(_escape_pdf(b), styles["bullet"], bulletText="-"))
        block.append(Spacer(1, 4))
        flow.append(KeepTogether(block) if KeepTogether is not None else block)
    return flow


def _structured_resume_to_template_sections(data: dict) -> Dict[str, str]:
    """Convert WorkZo structured CV JSON into fixed template buckets.

    This is the key anti-drift layer: ReportLab receives section buckets, not an
    AI-generated visual text block. Dates remain inside each object.
    """
    data = validate_resume_dates_and_sections(_coerce_structured_resume_schema(data or {})) if isinstance(data, dict) else {}
    if not data:
        return {}

    contact = data.get("contact") or {}
    header_bits = [
        data.get("full_name") or "Your Name",
        data.get("target_role") or "Professional CV",
    ]
    contact_line = " | ".join([x for x in [contact.get("phone"), contact.get("email"), contact.get("location"), contact.get("linkedin")] if x])
    if contact_line:
        header_bits.append(contact_line)

    def bullets(items):
        return "\n".join([f"- {x}" for x in _as_list(items) if str(x).strip()])

    exp_lines = []
    for job in data.get("work_experience") or []:
        title = job.get("title") or ""
        company = job.get("company") or ""
        dates = _normalize_date_text(job.get("dates") or "")
        heading = " — ".join([x for x in [title, company, dates] if x])
        if heading:
            exp_lines.append(heading)
        for b in _as_list(job.get("bullets")):
            exp_lines.append(f"- {b}")
        exp_lines.append("")

    edu_lines = []
    for ed in data.get("education") or []:
        degree = ed.get("degree") or ""
        institution = ed.get("institution") or ""
        dates = _normalize_date_text(ed.get("dates") or ed.get("year") or "")
        line = " — ".join([x for x in [degree, institution, dates] if x])
        if line:
            edu_lines.append(line)

    project_lines = []
    for pr in data.get("projects") or []:
        if pr.get("name"):
            project_lines.append(pr.get("name"))
        for b in _as_list(pr.get("bullets")):
            project_lines.append(f"- {b}")
        project_lines.append("")

    return {
        "header": "\n".join([x for x in header_bits if x]).strip(),
        "summary": data.get("professional_summary") or "",
        "skills": bullets((data.get("core_skills") or []) + (data.get("tools_technologies") or [])),
        "experience": "\n".join(exp_lines).strip(),
        "projects": "\n".join(project_lines).strip(),
        "education": "\n".join(edu_lines).strip(),
        "certifications": bullets(data.get("certifications") or []),
        "languages": bullets(data.get("languages") or []),
        "other": "",
    }


def _best_cv_sections_for_template(cv_text: str) -> Dict[str, str]:
    """Prefer approved structured JSON; fall back to text parsing only when needed."""
    try:
        structured = st.session_state.get("structured_cv_json") or st.session_state.get("pending_structured_cv_json") or {}
        if isinstance(structured, dict) and structured:
            sections = _structured_resume_to_template_sections(structured)
            if sections and (sections.get("summary") or sections.get("experience") or sections.get("education")):
                return sections
    except Exception:
        pass
    return parse_cv_sections_for_template(cv_text)


def make_pdf_from_text(title: str, body: str) -> bytes:
    """
    Create a simple PDF from generated CV text.
    Falls back to encoded text if reportlab is unavailable, but Streamlit label will show dependency need.
    """
    if SimpleDocTemplate is None:
        return make_minimal_pdf_from_text(title, body)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=42, leftMargin=42, topMargin=42, bottomMargin=42)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(title, styles["Title"]))
    story.append(Spacer(1, 12))

    for raw_line in body.splitlines():
        line = raw_line.strip()
        if not line:
            story.append(Spacer(1, 8))
            continue
        safe_line = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if line.endswith(":") or line.isupper():
            story.append(Paragraph(f"<b>{safe_line}</b>", styles["Heading3"]))
        else:
            story.append(Paragraph(safe_line, styles["BodyText"]))
            story.append(Spacer(1, 4))

    try:
        doc.build(story)
        buffer.seek(0)
        data = buffer.getvalue()
        if not data.startswith(b"%PDF"):
            return make_minimal_pdf_from_text(title, body)
        return data
    except Exception:
        return make_minimal_pdf_from_text(title, body)


def get_section_text(result: str, names: List[str], fallback_to_full: bool = False) -> str:
    sections = numbered_sections_to_markdown(result)
    lower_map = {k.lower().strip(): v for k, v in sections.items()}
    for name in names:
        value = sections.get(name, "").strip()
        if value:
            return value
        value = lower_map.get(name.lower().strip(), "").strip()
        if value:
            return value
    return result.strip() if fallback_to_full else ""


def show_gauge(score: Optional[int], title: str):
    if score is None:
        st.info(txt("not_analyzed"))
        return

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={"text": title},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"thickness": 0.35},
            "steps": [
                {"range": [0, 40], "color": "#f8d7da"},
                {"range": [40, 70], "color": "#fff3cd"},
                {"range": [70, 100], "color": "#d1e7dd"},
            ],
        }
    ))
    fig.update_layout(height=260, margin=dict(l=20, r=20, t=50, b=20))
    st.plotly_chart(fig, use_container_width=True)


def make_cv_hash(cv_text: str, country: str) -> str:
    raw = f"{SCORING_VERSION}||{country.strip()}||{st.session_state.get('migration_country', '').strip()}||{st.session_state.get('user_status', '').strip()}||{cv_text.strip()}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def bool_score(flag: bool, points: int) -> int:
    return points if flag else 0


def calculate_resume_score(features: Dict) -> int:
    """
    Honest resume quality score.
    A basic or messy CV should land around 35-60, not 85-95.
    Scores above 85 require strong structure, measurable achievements, clear sections, and enough detail.
    """
    word_count = int(features.get("word_count", 0) or 0)
    score = 0
    score += round(features.get("contact_score", 0) * 8)
    score += round(features.get("summary_score", 0) * 10)
    score += round(features.get("experience_score", 0) * 18)
    score += round(features.get("skills_score", 0) * 12)
    score += round(features.get("education_score", 0) * 8)
    score += round(features.get("quantified_score", 0) * 18)
    score += round(features.get("bullet_score", 0) * 10)
    score += round(features.get("date_score", 0) * 8)
    score += round(features.get("formatting_score", 0) * 8)

    action_verb_hits = int(features.get("action_verb_hits", 0) or 0)
    score += min(6, action_verb_hits)

    # Strong penalties for CVs that look complete but lack proof or structure.
    if word_count < 80:
        score = min(score, 35)
    elif word_count < 120:
        score = min(score, 45)
    elif word_count < 180:
        score = min(score, 58)

    if not features.get("work_experience_present", False):
        score = min(score, 55)
    if not features.get("skills_present", False):
        score = min(score, 62)
    if not features.get("professional_summary_present", False):
        score = min(score, 72)
    if not features.get("contact_info_present", False):
        score = min(score, 70)
    if not features.get("bullet_points_present", False):
        score = min(score, 74)
    if not features.get("quantified_achievements_present", False):
        score = min(score, 76)
    if int(features.get("section_heading_hits", 0) or 0) < 3:
        score = min(score, 78)

    long_lines = int(features.get("long_lines", 0) or 0)
    if long_lines > 6:
        score -= 10
    elif long_lines > 3:
        score -= 5

    # Reserve very high scores for genuinely strong CVs.
    if not (features.get("quantified_achievements_present") and features.get("bullet_points_present") and int(features.get("section_heading_hits", 0) or 0) >= 4 and word_count >= 280):
        score = min(score, 84)

    return max(10, min(int(score), 90))


def calculate_ats_score(features: Dict) -> int:
    """
    Honest ATS-readiness score.
    ATS score is about readable structure, standard headings, keywords, dates, and simple formatting.
    High scores require clear headings, skills, experience, dates, bullets, and readable text.
    """
    word_count = int(features.get("word_count", 0) or 0)
    score = 0
    score += 18 if features.get("standard_headings_present", False) else 4
    score += round(features.get("contact_score", 0) * 8)
    score += 14 if features.get("plain_text_readable", False) else 2
    score += round(features.get("skills_score", 0) * 14)
    score += round(features.get("experience_score", 0) * 16)
    score += round(features.get("education_score", 0) * 7)
    score += round(features.get("bullet_score", 0) * 9)
    score += round(features.get("date_score", 0) * 9)
    score += min(5, int(features.get("action_verb_hits", 0) or 0))

    if word_count < 80:
        score = min(score, 32)
    elif word_count < 120:
        score = min(score, 42)
    elif word_count < 180:
        score = min(score, 55)

    if not features.get("standard_headings_present", False):
        score = min(score, 62)
    if not features.get("work_experience_present", False):
        score = min(score, 55)
    if not features.get("skills_present", False):
        score = min(score, 60)
    if not features.get("date_ranges_present", False):
        score = min(score, 70)
    if not features.get("plain_text_readable", False):
        score = min(score, 64)
    if not features.get("bullet_points_present", False):
        score = min(score, 72)

    long_lines = int(features.get("long_lines", 0) or 0)
    if long_lines > 6:
        score -= 12
    elif long_lines > 3:
        score -= 6

    if not (features.get("standard_headings_present") and features.get("skills_present") and features.get("date_ranges_present") and features.get("plain_text_readable") and word_count >= 260):
        score = min(score, 82)

    return max(10, min(int(score), 90))


def calculate_robust_ats_score(cv_text: str, jd_text: str = "") -> Dict:
    """Deterministic ATS score with transparent keyword evidence. AI never guesses this score."""
    cv_text = sanitize_pdf_text(cv_text or "")
    jd_text = sanitize_pdf_text(jd_text or "")
    features = analyze_cv_text_features(cv_text)
    base_score = calculate_ats_score(features)
    if not jd_text.strip():
        return {"score": base_score, "matched_keywords": [], "missing_keywords": [], "method": "structure_only"}
    cv_words = set(re.findall(r"\b[a-zA-Z][a-zA-Z0-9+#.-]{2,}\b", cv_text.lower()))
    jd_words_raw = re.findall(r"\b[a-zA-Z][a-zA-Z0-9+#.-]{2,}\b", jd_text.lower())
    stop_words = {"the", "and", "for", "with", "from", "this", "that", "your", "you", "our", "are", "will", "have", "has", "job", "role", "team", "work", "working", "candidate", "responsibilities", "requirements", "must", "should", "about", "company", "using", "good", "strong"}
    counts = {}
    for w in jd_words_raw:
        if len(w) > 3 and w not in stop_words:
            counts[w] = counts.get(w, 0) + 1
    meaningful = [w for w, _ in sorted(counts.items(), key=lambda x: x[1], reverse=True)[:30]]
    matched = [w for w in meaningful if w in cv_words]
    missing = [w for w in meaningful if w not in cv_words]
    coverage = len(matched) / max(1, len(meaningful))
    structure_bonus = 0
    if features.get("standard_headings_present"): structure_bonus += 8
    if features.get("skills_present"): structure_bonus += 7
    if features.get("work_experience_present"): structure_bonus += 7
    if features.get("date_ranges_present"): structure_bonus += 4
    if features.get("bullet_points_present"): structure_bonus += 4
    if features.get("plain_text_readable"): structure_bonus += 5
    score = int(round(30 + coverage * 52 + structure_bonus))
    if not (features.get("standard_headings_present") and features.get("work_experience_present") and features.get("skills_present") and features.get("date_ranges_present")):
        score = min(score, 82)
    return {"score": max(10, min(score, 92)), "matched_keywords": matched, "missing_keywords": missing, "method": "keyword_structure"}


def normalize_cv_for_scoring(cv_text: str) -> str:
    """Normalize CV text so identical content always gives identical scores."""
    text = strip_markdown_for_resume(cv_text or "")
    text = re.sub(r"\s+", " ", text).strip().lower()
    return text


def stable_score_hash(cv_text: str) -> str:
    """Score hash depends only on resume content and scoring version."""
    raw = f"{SCORING_VERSION}||{normalize_cv_for_scoring(cv_text)}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def get_stable_resume_scores(cv_text: str, features: Optional[Dict] = None) -> Tuple[int, int, Dict]:
    """Return deterministic Resume + ATS scores. AI never calculates these numbers."""
    if "stable_score_cache" not in st.session_state:
        st.session_state.stable_score_cache = {}
    score_key = stable_score_hash(cv_text)
    if score_key in st.session_state.stable_score_cache:
        cached = st.session_state.stable_score_cache[score_key]
        return int(cached.get("resume_score", 0)), int(cached.get("ats_score", 0)), cached.get("features", {})
    features = features or analyze_cv_text_features(cv_text or "")
    resume_score = calculate_resume_score(features)
    ats_score = calculate_ats_score(features)
    st.session_state.stable_score_cache[score_key] = {"resume_score": resume_score, "ats_score": ats_score, "features": features}
    return resume_score, ats_score, features


def extract_resume_keywords(text: str, max_terms: int = 18) -> List[str]:
    """Lightweight ATS keyword extractor without extra dependencies."""
    text = (text or "").lower()
    protected = {
        "python", "sql", "tableau", "power bi", "excel", "jira", "salesforce", "servicenow",
        "itil", "itsm", "incident management", "root cause analysis", "troubleshooting",
        "data analysis", "data visualization", "dashboard", "reporting", "stakeholder",
        "customer support", "technical support", "api", "gcp", "aws", "azure", "machine learning",
        "nlp", "rag", "langchain", "pandas", "numpy", "mysql", "postgresql", "etl"
    }
    found = []
    for kw in sorted(protected, key=len, reverse=True):
        if re.search(r"\b" + re.escape(kw) + r"\b", text):
            found.append(kw)
    words = re.findall(r"\b[a-z][a-z0-9+#.-]{2,}\b", text)
    stop = {"and", "the", "with", "for", "from", "that", "this", "your", "you", "are", "will", "job", "role", "work", "team", "using", "have", "has", "our", "their", "skills", "experience", "candidate", "responsibilities", "requirements"}
    counts = {}
    for w in words:
        if w not in stop and len(w) > 2:
            counts[w] = counts.get(w, 0) + 1
    for w, _ in sorted(counts.items(), key=lambda x: x[1], reverse=True):
        if w not in found:
            found.append(w)
        if len(found) >= max_terms:
            break
    return found[:max_terms]


def calculate_ats_match_against_jd(cv_text: str, job_description: str) -> Dict:
    """Deterministic ATS match: keyword evidence, not AI opinion."""
    jd_keywords = extract_resume_keywords(job_description, 20)
    cv_lower = (cv_text or "").lower()
    matched = [kw for kw in jd_keywords if re.search(r"\b" + re.escape(kw.lower()) + r"\b", cv_lower)]
    missing = [kw for kw in jd_keywords if kw not in matched]
    coverage = (len(matched) / max(1, len(jd_keywords)))
    features = analyze_cv_text_features(cv_text or "")
    structure_bonus = 0
    if features.get("standard_headings_present"): structure_bonus += 8
    if features.get("skills_present"): structure_bonus += 7
    if features.get("work_experience_present"): structure_bonus += 7
    if features.get("date_ranges_present"): structure_bonus += 5
    if features.get("bullet_points_present"): structure_bonus += 5
    if features.get("quantified_achievements_present"): structure_bonus += 5
    score = int(35 + coverage * 45 + structure_bonus)
    if coverage < 0.55:
        score = min(score, 74)
    if coverage < 0.35:
        score = min(score, 62)
    if not features.get("quantified_achievements_present"):
        score = min(score, 82)
    return {
        "ats_match_score": max(10, min(score, 94)),
        "jd_keywords": jd_keywords,
        "matched_keywords": matched,
        "missing_keywords": missing[:10],
        "keyword_coverage": round(coverage * 100, 1),
    }


def build_honesty_impact_audit(original_cv: str, improved_cv: str, job_description: str = "") -> Dict:
    """Show what changed and what needs user confirmation before download."""
    orig = original_cv or ""
    improved = improved_cv or ""
    orig_lower = orig.lower()
    improved_keywords = extract_resume_keywords(improved, 24)
    original_keywords = set(extract_resume_keywords(orig, 40))
    added_keywords = [kw for kw in improved_keywords if kw not in original_keywords][:10]
    metrics_added = re.findall(r"\b\d+%|\b\d+\+?\s+(?:users|clients|tickets|projects|teams|months|years)\b", improved, flags=re.I)
    unsupported_metrics = [m for m in metrics_added if m.lower() not in orig_lower][:8]
    jd_match = calculate_ats_match_against_jd(improved, job_description) if job_description else {}
    needs_confirmation = []
    for kw in added_keywords:
        if kw not in orig_lower:
            needs_confirmation.append(f"Confirm this keyword is truthful: {kw}")
    for metric in unsupported_metrics:
        needs_confirmation.append(f"Confirm this metric is accurate: {metric}")
    return {
        "added_keywords": added_keywords,
        "unsupported_metrics": unsupported_metrics,
        "needs_confirmation": needs_confirmation[:10],
        "ats_match": jd_match,
    }


def calculate_country_readiness_score(features: Dict, target_country: str, user_status: str) -> int:
    """
    Resume readiness for selected migration/target country.
    This is intentionally stricter than the general resume score.
    """
    base = calculate_resume_score(features)

    score = int(base * 0.72)

    # Country-template/readability signals
    if features.get("contact_info_present", False):
        score += 6
    if features.get("standard_headings_present", False):
        score += 8
    if features.get("plain_text_readable", False):
        score += 8
    if features.get("date_ranges_present", False):
        score += 5
    if features.get("skills_present", False):
        score += 5
    if features.get("quantified_achievements_present", False):
        score += 6

    country = (target_country or "").lower()
    status = (user_status or "").lower()

    # Migrating users need stronger country adaptation.
    if "migrate" in status or "abroad" in status:
        score -= 5

    # Local language/country expectations: not exact, but useful early signal.
    cv_raw = (st.session_state.get("cv_text", "") or "").lower()
    if country in {"germany", "austria", "switzerland"}:
        if "german" in cv_raw or "deutsch" in cv_raw:
            score += 5
        else:
            score -= 6
    if country in {"united kingdom", "united states", "canada", "australia", "ireland"}:
        if "english" in cv_raw:
            score += 4

    if not features.get("work_experience_present", False):
        score -= 8
    if int(features.get("word_count", 0)) < 180:
        score -= 6

    return max(25, min(score, 92))


def apply_dashboard_cache(cached: Dict):
    st.session_state.profile_summary = cached.get("profile_summary", "")
    st.session_state.current_role_detected = cached.get("current_role_detected", "")

    skills = cached.get("key_skills_detected", [])
    roles = cached.get("suggested_roles_detected", [])
    strengths = cached.get("resume_strengths", [])
    improvements = cached.get("resume_improvements", [])
    best_fit_countries = cached.get("best_fit_countries_detected", [])
    next_best_actions = cached.get("next_best_actions_detected", [])
    country_readiness_notes = cached.get("country_readiness_notes_detected", [])
    next_actions = cached.get("next_actions_detected", [])

    st.session_state.key_skills_detected = "\n".join([f"- {x}" for x in skills]) if isinstance(skills, list) else str(skills)
    st.session_state.suggested_roles_detected = "\n".join([f"- {x}" for x in roles]) if isinstance(roles, list) else str(roles)
    st.session_state.resume_strengths = "\n".join([f"- {x}" for x in strengths]) if isinstance(strengths, list) else str(strengths)
    st.session_state.resume_improvements = country_aware_resume_improvements("\n".join([f"- {x}" for x in improvements]) if isinstance(improvements, list) else str(improvements))
    st.session_state.best_fit_countries_detected = "\n".join([f"- {x}" for x in best_fit_countries]) if isinstance(best_fit_countries, list) else str(best_fit_countries)
    st.session_state.next_best_step_result = "\n".join([f"- {x}" for x in next_best_actions]) if isinstance(next_best_actions, list) else str(next_best_actions)
    st.session_state.country_readiness_notes = "\n".join([f"- {x}" for x in country_readiness_notes]) if isinstance(country_readiness_notes, list) else str(country_readiness_notes)

    st.session_state.cv_profile_raw = cached.get("cv_profile_raw", "")
    st.session_state.cv_score_value = cached.get("cv_score_value")
    st.session_state.ats_score_value = cached.get("ats_score_value")
    st.session_state.country_readiness_score_value = cached.get("country_readiness_score_value")


def reset_onboarding():
    preserve = {
        "request_count": st.session_state.request_count,
        "first_request_time": st.session_state.first_request_time,
        "ui_language": st.session_state.ui_language,
        "response_language": st.session_state.response_language,
        "dashboard_cache": st.session_state.dashboard_cache,
        "geo_country_suggestion": st.session_state.get("geo_country_suggestion", "Germany"),
        "geo_language_suggestion": st.session_state.get("geo_language_suggestion", "English"),
    }
    for key in list(st.session_state.keys()):
        del st.session_state[key]

    for key, value in defaults.items():
        st.session_state[key] = value

    for key, value in preserve.items():
        st.session_state[key] = value

    st.session_state.page = "onboarding"
    st.session_state.onboarding_complete = False


def set_new_resume_and_refresh(new_resume_text: str):
    clean_new_resume = strip_markdown_for_resume(new_resume_text or "").strip()
    st.session_state.cv_text = clean_new_resume
    st.session_state.clean_structured_cv_text = clean_new_resume
    st.session_state.structured_cv_profile = clean_new_resume

    st.session_state.profile_summary = ""
    st.session_state.current_role_detected = ""
    st.session_state.key_skills_detected = ""
    st.session_state.suggested_roles_detected = ""
    st.session_state.best_fit_countries_detected = ""
    st.session_state.next_actions_detected = ""
    st.session_state.country_cv_readiness = ""
    st.session_state.status_guidance = ""
    st.session_state.cv_profile_raw = ""
    st.session_state.cv_score_value = None
    st.session_state.ats_score_value = None
    st.session_state.resume_strengths = ""
    st.session_state.resume_improvements = ""

    analyze_resume_dashboard_stable(st.session_state.cv_text, force_refresh=True)


def escape_yaml_value(value: str) -> str:
    value = str(value or "").replace("\\", "\\\\").replace('"', '\\"').strip()
    return f'"{value}"'


def yaml_list(items: List[str], indent: int = 6) -> str:
    pad = " " * indent
    cleaned = [str(x).strip().lstrip("-•* ").strip() for x in (items or []) if str(x).strip()]
    if not cleaned:
        return f"{pad}[]"
    return "\n".join(f"{pad}- {escape_yaml_value(x)}" for x in cleaned[:12])


def rendercv_yaml_from_cv_text(cv_text: str, template_name: str = "ATS Classic", target_country: str = "") -> bytes:
    """Create an experimental RenderCV-style YAML from WorkZo's structured CV text."""
    cleaned = clean_generated_cv_text_for_template(cv_text)
    data = parse_cv_sections_for_template(cleaned)
    header = [x.strip() for x in data.get("header", "").splitlines() if x.strip()]
    name = header[0] if header else "Candidate Name"
    role = header[1] if len(header) > 1 else "Target Role"
    contact_line = " | ".join(header[2:]) if len(header) > 2 else ""
    def lines(section):
        return [x.strip().lstrip("-•* ").strip() for x in (data.get(section, "") or "").splitlines() if x.strip()]
    email = phone = website = ""
    location = target_country or ""
    for part in re.split(r"\s*\|\s*", contact_line):
        if re.search(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", part, flags=re.I):
            email = part.strip()
        elif re.search(r"\+?\d[\d\s().-]{6,}", part):
            phone = part.strip()
        elif "linkedin" in part.lower():
            website = part.strip()
        elif part.strip():
            location = part.strip()
    yaml = ["cv:", f"  name: {escape_yaml_value(name)}", f"  label: {escape_yaml_value(role)}"]
    if location: yaml.append(f"  location: {escape_yaml_value(location)}")
    if email: yaml.append(f"  email: {escape_yaml_value(email)}")
    if phone: yaml.append(f"  phone: {escape_yaml_value(phone)}")
    if website: yaml.append(f"  website: {escape_yaml_value(website)}")
    yaml.append("  sections:")
    yaml.append("    professional_summary:")
    summary_lines = lines("summary")
    yaml.extend([f"      - {escape_yaml_value(x)}" for x in summary_lines[:2]] or ["      []"])
    yaml.append("    skills:")
    yaml.append(yaml_list(lines("skills"), 6))
    yaml.append("    experience:")
    exp_lines = lines("experience")
    if exp_lines:
        yaml += ['      - company: "Experience"', '        position: "Relevant Experience"', "        highlights:", yaml_list(exp_lines, 10)]
    else:
        yaml.append("      []")
    yaml.append("    projects:")
    project_lines = lines("projects")
    if project_lines:
        yaml += ['      - name: "Projects"', "        highlights:", yaml_list(project_lines, 10)]
    else:
        yaml.append("      []")
    yaml.append("    education:")
    edu_lines = lines("education")
    if edu_lines:
        for ed in edu_lines[:5]:
            yaml.append("      - institution: " + escape_yaml_value(ed))
            yaml.append('        area: ""')
            yaml.append('        degree: ""')
    else:
        yaml.append("      []")
    if lines("certifications"):
        yaml.append("    certifications:")
        yaml.append(yaml_list(lines("certifications"), 6))
    if lines("languages"):
        yaml.append("    languages:")
        yaml.append(yaml_list(lines("languages"), 6))
    yaml += ["design:", '  theme: "classic"', "  page:", "    size: a4", "    top_margin: 1.2cm", "    bottom_margin: 1.2cm", "    left_margin: 1.4cm", "    right_margin: 1.4cm"]
    return ("\n".join(yaml) + "\n").encode("utf-8")


def try_rendercv_pdf_from_yaml(yaml_bytes: bytes) -> Optional[bytes]:
    if not shutil.which("rendercv"):
        return None
    try:
        with tempfile.TemporaryDirectory() as tmp:
            yaml_path = os.path.join(tmp, "workzo_rendercv.yaml")
            with open(yaml_path, "wb") as f:
                f.write(yaml_bytes)
            subprocess.run(["rendercv", "render", yaml_path], cwd=tmp, check=True, timeout=25, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            for root, _, files in os.walk(tmp):
                for name in files:
                    if name.lower().endswith(".pdf"):
                        return Path(os.path.join(root, name)).read_bytes()
    except Exception:
        return None
    return None


def build_rule_based_dashboard_cache(cv_text: str) -> Dict:
    """Create honest dashboard scores and basic insights without waiting for AI.
    This prevents empty dashboard cards when the AI analysis fails or JSON parsing breaks.
    """
    features = analyze_cv_text_features(cv_text or "")
    resume_score, ats_score, features = get_stable_resume_scores(cv_text or "", features)
    country_score = calculate_country_readiness_score(
        features,
        st.session_state.get("migration_country") or st.session_state.get("country", ""),
        st.session_state.get("user_status", ""),
    )

    strengths = []
    improvements = []
    if features.get("contact_info_present"):
        strengths.append("Contact information is present")
    else:
        improvements.append("Add clear contact information")
    if features.get("skills_present"):
        strengths.append("Skills section is visible")
    else:
        improvements.append("Add a dedicated skills section")
    if features.get("work_experience_present"):
        strengths.append("Work experience section is included")
    else:
        improvements.append("Add a clear work experience section")
    if features.get("bullet_points_present"):
        strengths.append("Uses bullet points for readability")
    else:
        improvements.append("Use bullet points under each role or project")
    if features.get("quantified_achievements_present"):
        strengths.append("Includes measurable achievements")
    else:
        improvements.append("Add numbers such as tickets handled, projects, users, revenue, or percentage improvements")
    if features.get("standard_headings_present"):
        strengths.append("Uses standard resume headings")
    else:
        improvements.append("Use standard headings like Summary, Experience, Skills, Education")
    if features.get("date_ranges_present"):
        strengths.append("Includes dates or experience duration")
    else:
        improvements.append("Add dates for education and work experience")

    while len(strengths) < 3:
        strengths.append("Resume text was successfully read")
    while len(improvements) < 3:
        improvements.append("Add more specific role keywords for your target job")

    word_count = int(features.get("word_count", 0) or 0)
    profile_summary = (
        f"WorkZo read about {word_count} words from your resume. "
        f"The current resume looks {score_band(resume_score).lower()} and needs clearer proof, structure, or role targeting."
    )

    cached = {
        "profile_summary": profile_summary,
        "current_role_detected": "Not detected yet",
        "key_skills_detected": [],
        "suggested_roles_detected": [],
        "best_fit_countries_detected": [],
        "country_cv_readiness": f"{score_band(country_score)} for {st.session_state.get('migration_country') or st.session_state.get('country', 'selected country')}",
        "status_guidance": "Improve the weakest resume sections first, then analyze one target job description.",
        "next_actions_detected": [
            "Fix missing resume sections first",
            "Add measurable achievements",
            "Paste a target job description in Job Assist",
        ],
        "resume_strengths": strengths[:4],
        "resume_improvements": improvements[:4],
        "next_best_actions_detected": [],
        "country_readiness_notes_detected": [],
        "country_readiness_score_value": country_score,
        "cv_profile_raw": json.dumps({"rule_based_features": features}, indent=2),
        "cv_score_value": resume_score,
        "ats_score_value": ats_score,
    }
    return cached


def render_feature_tile(icon: str, title: str, copy: str):
    st.markdown(f"""
    <div class="feature-tile">
        <div style="font-size:1.45rem; margin-bottom:8px;">{icon}</div>
        <div class="feature-title">{title}</div>
        <div class="feature-copy">{copy}</div>
    </div>
    """, unsafe_allow_html=True)


def generate_next_best_steps(cv_text: str, country_name: str, current_role: str, suggested_roles: str, user_status: str = "", career_goal: str = "") -> str:
    prompt = f"""
Country: {country_name}
User status: {user_status or 'Not specified'}
Career goal: {career_goal or 'Not specified'}
Current role: {current_role or 'Not clear'}
Suggested roles:
{suggested_roles}
Candidate CV:
{cv_text}

Create a personalized action center. Adapt the advice based on the user status:
st.info("⚠️ WorkZo AI is currently in Beta. Some results may not be perfect yet. Your feedback helps improve the tool.")

- Fresh graduate: portfolio projects, internships, entry-level search, skills proof.
- Career changer: transferable skills, bridge role, portfolio, realistic job titles.
- Migrating to another country: country CV format, language expectations, local job titles, application documents.
- Returning after career break: confidence positioning, gap explanation, restart strategy.
- Experienced professional: positioning, seniority, specialization, leadership proof.

Return in this exact structure:
1. Resume Readiness Verdict
2. Best Immediate Goal
3. This Week's 3 Priority Actions
4. Best Role Cluster to Target
5. One Resume Fix That Will Help Most
6. One Skill or Proof to Build Next
7. Country-Specific Advice
8. One Message to Send Today

Keep it practical, specific, and motivating.
"""
    result = run_ai_prompt(prompt)
    return result
