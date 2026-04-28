import os
import re
from typing import Dict, Any, List
# WorkZo modular split v138
# Source: app_workzo_v137_stable_no_feature_change.py, lines 11207-20000

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
    value = re.sub(r"\s+", " ", value).strip()
    return value

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
# WorkZo FINAL FORCE PREVIEW OVERRIDE
# Different perspective:
# The preview was not broken by dates. It was using the wrong renderer/source.
# This override runs in the LAST module, immediately before the router calls show_dashboard().
# Therefore it replaces every older preview path:
# - render_cv_template_preview(...)
# - build_visual_cv_html(...)
# - workzo_visual_cv_html_from_structured(...)
# It reads visible editor widget keys directly from st.session_state.
# =========================================================

def _wz_force_text(value):
    try:
        return str(value or "").strip()
    except Exception:
        return ""

def _wz_force_escape(value):
    try:
        return html.escape(_wz_force_text(value))
    except Exception:
        import html as _html
        return _html.escape(_wz_force_text(value))

def _wz_force_lines(text):
    import re as _re
    out = []
    for line in _wz_force_text(text).splitlines():
        line = _re.sub(r"^[-•*]\s*", "", line.strip()).strip()
        if line:
            out.append(line)
    return out

def _wz_force_find_editor_prefix():
    """
    Find the active editable CV widget prefix. This is the only reliable source
    because the user edits these widgets directly.
    """
    try:
        keys = list(st.session_state.keys())
    except Exception:
        return ""

    preferred = [
        "improved_cv_preview_v141",
        "improved_cv_preview_v92",
        "country_cv_preview_v141",
        "country_cv_preview_v92",
        "cv_preview",
    ]
    for p in preferred:
        if f"{p}_experience" in keys or f"{p}_education" in keys or f"{p}_summary" in keys:
            return p

    for k in keys:
        if str(k).endswith("_experience"):
            return str(k)[:-len("_experience")]
    return ""

def _wz_force_parse_experience(text):
    import re as _re
    items = []
    raw = _wz_force_text(text)
    if not raw:
        return items

    # Split by blank line into jobs.
    blocks = _re.split(r"\n\s*\n", raw)
    for block in blocks:
        lines = [x.strip() for x in block.splitlines() if x.strip()]
        if not lines:
            continue

        header = lines[0]
        bullets = []
        # Header format expected: Role | Company | Dates
        parts = [p.strip() for p in header.split("|")]
        title = parts[0] if len(parts) > 0 else ""
        company = parts[1] if len(parts) > 1 else ""
        dates = parts[2] if len(parts) > 2 else ""

        for line in lines[1:]:
            clean = _re.sub(r"^[-•*]\s*", "", line).strip()
            if clean:
                bullets.append(clean)

        # If no pipe was used but multiple lines exist, still render safely.
        if len(parts) == 1 and not bullets and len(lines) > 1:
            bullets = [_re.sub(r"^[-•*]\s*", "", x).strip() for x in lines[1:] if x.strip()]

        if title or company or dates or bullets:
            items.append({"title": title, "company": company, "dates": dates, "bullets": bullets})
    return items

def _wz_force_parse_education(text):
    items = []
    for line in _wz_force_text(text).splitlines():
        line = line.strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split("|")]
        items.append({
            "degree": parts[0] if len(parts) > 0 else "",
            "institution": parts[1] if len(parts) > 1 else "",
            "dates": parts[2] if len(parts) > 2 else "",
        })
    return items

def _wz_force_plain_projects(text):
    # Never show raw {'name': ...} in preview.
    import ast as _ast, json as _json
    out = []
    for line in _wz_force_text(text).splitlines():
        clean = line.strip()
        if not clean:
            continue
        try:
            obj = _ast.literal_eval(clean)
            if isinstance(obj, dict):
                clean = obj.get("name") or obj.get("title") or obj.get("description") or ""
        except Exception:
            pass
        if clean:
            out.append(str(clean))
    return out

def _wz_force_data_from_editor_or_given(given=None):
    """
    Highest priority: visible editor widgets.
    Fallback: structured dict passed by old code.
    """
    prefix = _wz_force_find_editor_prefix()
    data = {}

    if prefix:
        def get(field):
            return _wz_force_text(st.session_state.get(f"{prefix}_{field}", ""))

        data = {
            "full_name": get("name"),
            "target_role": get("role"),
            "contact": {
                "phone": get("phone"),
                "email": get("email"),
                "location": get("location"),
                "linkedin": get("linkedin"),
            },
            "professional_summary": get("summary"),
            "core_skills": _wz_force_lines(get("skills")),
            "tools_technologies": [],
            "work_experience": _wz_force_parse_experience(get("experience")),
            "education": _wz_force_parse_education(get("education")),
            "projects": [{"name": x, "bullets": []} for x in _wz_force_plain_projects(get("projects"))],
            "languages": _wz_force_lines(get("languages")),
            "certifications": _wz_force_lines(get("certifications")),
        }

    # Fallback only if editor has no actual section data.
    if not (data.get("work_experience") or data.get("education") or data.get("professional_summary") or data.get("core_skills")):
        if isinstance(given, dict):
            try:
                data = _coerce_structured_resume_schema(given)
            except Exception:
                data = given

    try:
        st.session_state["workzo_force_preview_data"] = data
        st.session_state["workzo_live_cv_structured"] = data
    except Exception:
        pass

    return data or {}

def _wz_force_list_html(items):
    vals = [_wz_force_escape(str(x).strip(" -•*")) for x in (items or []) if _wz_force_text(x)]
    if not vals:
        return "<p class='cv-empty'>—</p>"
    return "<ul>" + "".join(f"<li>{v}</li>" for v in vals) + "</ul>"

def _wz_force_exp_html(items):
    blocks = []
    for job in items or []:
        if not isinstance(job, dict):
            continue
        title = _wz_force_escape(job.get("title"))
        company = _wz_force_escape(job.get("company"))
        dates = _wz_force_escape(job.get("dates"))
        head = " | ".join([x for x in [title, company, dates] if x])
        bullets = [_wz_force_escape(b) for b in (job.get("bullets") or []) if _wz_force_text(b)]
        piece = ""
        if head:
            piece += f"<p class='cv-job-head'><b>{head}</b></p>"
        if bullets:
            piece += "<ul>" + "".join(f"<li>{b}</li>" for b in bullets) + "</ul>"
        if piece:
            blocks.append(piece)
    return "".join(blocks) if blocks else "<p class='cv-empty'>—</p>"

def _wz_force_edu_html(items):
    lines = []
    for ed in items or []:
        if not isinstance(ed, dict):
            continue
        parts = [_wz_force_escape(ed.get("degree")), _wz_force_escape(ed.get("institution")), _wz_force_escape(ed.get("dates"))]
        parts = [p for p in parts if p]
        if parts:
            lines.append("<p>" + " | ".join(parts) + "</p>")
    return "".join(lines) if lines else "<p class='cv-empty'>—</p>"

def _wz_force_projects_html(items):
    lines = []
    for pr in items or []:
        if isinstance(pr, dict):
            name = _wz_force_escape(pr.get("name") or pr.get("title"))
            if name:
                lines.append(f"<p>{name}</p>")
        elif _wz_force_text(pr):
            lines.append(f"<p>{_wz_force_escape(pr)}</p>")
    return "".join(lines) if lines else "<p class='cv-empty'>—</p>"

def _wz_force_visual_html(data=None, template_name="ATS Resume", target_country=""):
    data = _wz_force_data_from_editor_or_given(data)
    contact = data.get("contact") if isinstance(data.get("contact"), dict) else {}

    name = _wz_force_escape(data.get("full_name") or "Your Name")
    role = _wz_force_escape(data.get("target_role") or "Professional CV")
    contact_line = _wz_force_escape(" · ".join([
        _wz_force_text(contact.get("phone")),
        _wz_force_text(contact.get("email")),
        _wz_force_text(contact.get("location")),
        _wz_force_text(contact.get("linkedin")),
    ]).strip(" ·"))

    summary = f"<p>{_wz_force_escape(data.get('professional_summary'))}</p>" if _wz_force_text(data.get("professional_summary")) else "<p class='cv-empty'>—</p>"
    skills = _wz_force_list_html((data.get("core_skills") or []) + (data.get("tools_technologies") or []))
    experience = _wz_force_exp_html(data.get("work_experience") or [])
    education = _wz_force_edu_html(data.get("education") or [])
    projects = _wz_force_projects_html(data.get("projects") or [])
    languages = _wz_force_list_html(data.get("languages") or [])
    certifications = _wz_force_list_html(data.get("certifications") or [])

    return f"""
<style>
.cv-page {{ width: 794px; min-height: 1123px; margin: 0 auto 24px auto; background: white; color: #111827; box-shadow: 0 18px 50px rgba(0,0,0,.30); overflow: hidden; font-family: Arial, Helvetica, sans-serif; }}
.cv-page p {{ margin: 0 0 7px 0; line-height: 1.38; font-size: 13px; }}
.cv-page ul {{ margin: 0 0 10px 18px; padding: 0; }}
.cv-page li {{ font-size: 13px; margin-bottom: 5px; line-height: 1.35; }}
.cv-section-title {{ font-size: 12px; letter-spacing: 1.5px; text-transform: uppercase; font-weight: 800; margin: 17px 0 8px; }}
.cv-empty {{ color:#64748b; }}
.cv-job-head {{ margin-top: 4px !important; margin-bottom: 5px !important; }}
@media (max-width: 850px) {{ .cv-page {{ width: 100%; min-height: auto; }} }}
</style>
<div class="cv-page">
  <div style="padding:36px 42px 18px; border-bottom:4px solid #1f2937;">
    <div style="font-size:32px;font-weight:800;letter-spacing:1px;">{name}</div>
    <div style="font-size:15px;color:#334155;margin-top:6px;">{role}</div>
    <div style="font-size:12px;color:#64748b;margin-top:9px;">{contact_line}</div>
  </div>
  <div style="display:grid;grid-template-columns:36% 64%;">
    <aside style="background:#f1f5f9;padding:26px 28px;min-height:900px;">
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

# Replace ALL older preview functions with this forced renderer.
def workzo_visual_cv_html_from_structured(data, template_name="ATS Resume", target_country=""):
    return _wz_force_visual_html(data, template_name, target_country)

def build_visual_cv_html(cv_text, template_name="ATS Resume", target_country=""):
    return _wz_force_visual_html(st.session_state.get("workzo_live_cv_structured") or st.session_state.get("structured_cv_json") or {}, template_name, target_country)

def render_cv_template_preview(template_name, target_country, user_status):
    st.markdown("### Live Template Preview")
    st.caption("This preview is forced to read the current editable fields directly.")
    st.components.v1.html(_wz_force_visual_html({}, template_name, target_country), height=850, scrolling=True)
# =========================================================


# =========================================================
# WorkZo router safety fallbacks
# These prevent the router module from crashing when a helper
# was not loaded yet or when this module is accidentally run directly.
# =========================================================

if "read_url_page" not in globals():
    def read_url_page(default: str = "dashboard") -> str:
        try:
            value = st.query_params.get("page", default)
            if isinstance(value, list):
                value = value[0] if value else default
            return value or default
        except Exception:
            return default

if "request_scroll_to_top" not in globals():
    def request_scroll_to_top() -> None:
        try:
            st.session_state["_workzo_scroll_to_top"] = True
        except Exception:
            pass

if "update_url_page" not in globals():
    def update_url_page(page_key: str) -> None:
        try:
            st.query_params["page"] = page_key
        except Exception:
            pass

if "sync_navigation_state" not in globals():
    def sync_navigation_state(page_key: str) -> None:
        try:
            st.session_state.page = page_key
            st.session_state.nav_page = page_key
            update_url_page(page_key)
            request_scroll_to_top()
        except Exception:
            pass

if "queue_navigation" not in globals():
    def queue_navigation(page_key: str) -> None:
        try:
            st.session_state._workzo_pending_nav = page_key
            request_scroll_to_top()
        except Exception:
            pass

if "consume_pending_navigation" not in globals():
    def consume_pending_navigation() -> None:
        try:
            page_key = st.session_state.pop("_workzo_pending_nav", None)
            if page_key:
                sync_navigation_state(page_key)
        except Exception:
            pass

if "go_home" not in globals():
    def go_home() -> None:
        queue_navigation("dashboard")

# =========================================================

# ROUTER
# =========================================================
def _workzo_run_router_if_available() -> None:
    """
    Run the app router only when all page functions are already loaded.
    This avoids NameError crashes if the file is run directly or if module order changes.
    """
    required = ["show_landing_page", "show_onboarding", "show_dashboard"]
    missing = [name for name in required if name not in globals()]
    if missing:
        try:
            st.warning("WorkZo router is not ready yet. Missing: " + ", ".join(missing))
        except Exception:
            print("WorkZo router is not ready yet. Missing:", ", ".join(missing))
        return

    try:
        workzo_v137_stabilize_state()
    except Exception:
        pass

    try:
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

        if "page" not in st.session_state:
            st.session_state.page = "landing"
        if "onboarding_complete" not in st.session_state:
            st.session_state.onboarding_complete = False

        if st.session_state.page == "landing":
            show_landing_page()
        elif not st.session_state.onboarding_complete or st.session_state.page == "onboarding":
            show_onboarding()
        else:
            show_dashboard()
    except Exception as exc:
        try:
            st.error(f"WorkZo router error: {exc}")
            st.exception(exc)
        except Exception:
            raise

_workzo_run_router_if_available()
