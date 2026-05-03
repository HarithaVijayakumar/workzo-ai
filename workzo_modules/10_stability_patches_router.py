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

    try:
        style_key = resolve_template_style(template_name)
    except Exception:
        style_key = "Minimal ATS"

    base_css = """
<style>
.cv-page { width: 794px; min-height: 1123px; margin: 0 auto 24px auto; background: white; color: #111827; box-shadow: 0 18px 50px rgba(0,0,0,.30); overflow: hidden; font-family: Arial, Helvetica, sans-serif; }
.cv-page p { margin: 0 0 7px 0; line-height: 1.38; font-size: 13px; }
.cv-page ul { margin: 0 0 10px 18px; padding: 0; }
.cv-page li { font-size: 13px; margin-bottom: 5px; line-height: 1.35; }
.cv-section-title { font-size: 12px; letter-spacing: 1.5px; text-transform: uppercase; font-weight: 800; margin: 17px 0 8px; }
.cv-empty { color:#64748b; }
.cv-job-head { margin-top: 4px !important; margin-bottom: 5px !important; }
@media (max-width: 850px) { .cv-page { width: 100%; min-height: auto; } }
</style>
"""

    if style_key == "Minimal ATS":
        return base_css + f"""
<div class="cv-page" style="padding:46px 56px;">
  <div style="border-bottom:2px solid #e5e7eb; padding-bottom:14px;">
    <div style="font-size:31px;font-weight:850;">{name}</div>
    <div style="font-size:15px;margin-top:5px;color:#334155;">{role}</div>
    <div style="font-size:12px;color:#64748b;margin-top:8px;">{contact_line}</div>
  </div>
  <div class="cv-section-title">Professional Summary</div>{summary}
  <div class="cv-section-title">Core Skills</div>{skills}
  <div class="cv-section-title">Professional Experience</div>{experience}
  <div class="cv-section-title">Projects</div>{projects}
  <div class="cv-section-title">Education</div>{education}
  <div class="cv-section-title">Certifications</div>{certifications}
  <div class="cv-section-title">Languages</div>{languages}
</div>
"""

    if style_key in ["German-Style Lebenslauf", "Executive Slate"]:
        return base_css + f"""
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

    if style_key == "Graduate Portfolio":
        return base_css + f"""
<div class="cv-page">
  <div style="padding:38px 46px; border-bottom:1px solid #e5e7eb;">
    <div style="font-size:33px;font-weight:900;">{name}</div>
    <div style="font-size:15px;color:#0369a1;margin-top:6px;">{role}</div>
    <div style="font-size:12px;color:#64748b;margin-top:8px;">{contact_line}</div>
  </div>
  <div style="padding:28px 42px;">
    <div class="cv-section-title" style="color:#0369a1;">Career Objective</div>{summary}
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:24px;">
      <div><div class="cv-section-title" style="color:#0369a1;">Education</div>{education}</div>
      <div><div class="cv-section-title" style="color:#0369a1;">Skills & Tools</div>{skills}</div>
    </div>
    <div class="cv-section-title" style="color:#0369a1;">Projects</div>{projects}
    <div class="cv-section-title" style="color:#0369a1;">Experience / Internships</div>{experience}
    <div class="cv-section-title" style="color:#0369a1;">Languages & Certifications</div>{languages}{certifications}
  </div>
</div>
"""

    if style_key == "Career Pivot":
        return base_css + f"""
<div class="cv-page" style="padding:42px 50px;">
  <div style="background:#f8fafc;border-left:6px solid #7c3aed;padding:20px 24px;margin-bottom:22px;">
    <div style="font-size:32px;font-weight:900;">{name}</div>
    <div style="font-size:15px;color:#4c1d95;margin-top:6px;">{role}</div>
    <div style="font-size:12px;color:#64748b;margin-top:8px;">{contact_line}</div>
  </div>
  <div class="cv-section-title" style="color:#7c3aed;">Career Change Profile</div>{summary}
  <div class="cv-section-title" style="color:#7c3aed;">Transferable + Target Skills</div>{skills}
  <div class="cv-section-title" style="color:#7c3aed;">Relevant Projects / Training</div>{projects}
  <div class="cv-section-title" style="color:#7c3aed;">Previous Experience Reframed</div>{experience}
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:24px;">
    <div><div class="cv-section-title" style="color:#7c3aed;">Education</div>{education}</div>
    <div><div class="cv-section-title" style="color:#7c3aed;">Languages</div>{languages}</div>
  </div>
</div>
"""

    return base_css + f"""
<div class="cv-page">
  <div style="background:linear-gradient(135deg,#2563eb,#14b8a6);color:white;padding:42px 46px;">
    <div style="font-size:35px;font-weight:900;">{name}</div>
    <div style="font-size:16px;margin-top:6px;opacity:.95;">{role}</div>
    <div style="font-size:12px;margin-top:10px;opacity:.9;">{contact_line}</div>
  </div>
  <div style="padding:30px 42px;display:grid;grid-template-columns:1.2fr .8fr;gap:30px;">
    <main>
      <div class="cv-section-title" style="color:#2563eb;">Profile</div>{summary}
      <div class="cv-section-title" style="color:#2563eb;">Experience</div>{experience}
      <div class="cv-section-title" style="color:#2563eb;">Projects</div>{projects}
    </main>
    <aside style="border-left:1px solid #e5e7eb;padding-left:24px;">
      <div class="cv-section-title" style="color:#0f766e;">Skills</div>{skills}
      <div class="cv-section-title" style="color:#0f766e;">Education</div>{education}
      <div class="cv-section-title" style="color:#0f766e;">Certifications</div>{certifications}
      <div class="cv-section-title" style="color:#0f766e;">Languages</div>{languages}
    </aside>
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
    st.html(_wz_force_visual_html({}, template_name, target_country))
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
        # Native Streamlit-only scroll reset: change query params on navigation.
        # This avoids deprecated components/iframe scripts.
        try:
            import time
            st.session_state["_workzo_scroll_to_top"] = True
            st.session_state["_workzo_page_nonce"] = str(int(time.time() * 1000))
            st.query_params["wz_top"] = st.session_state["_workzo_page_nonce"]
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
        if callable(globals().get("workzo_preserve_best_scores")):
            workzo_preserve_best_scores()
        elif callable(globals().get("workzo_preserve_best_scores_v12")):
            workzo_preserve_best_scores_v12()
    except Exception:
        pass

    try:
        # Fresh browser/session rule:
        # After stopping/restarting Streamlit, do not reopen the last query-param page
        # (for example ?page=job_assist). Start clean from landing unless user data
        # already exists in the current Streamlit session.
        if not st.session_state.get("_workzo_runtime_session_started", False):
            st.session_state["_workzo_runtime_session_started"] = True
            has_active_profile = bool(
                str(st.session_state.get("cv_text", "") or st.session_state.get("clean_structured_cv_text", "")).strip()
                or st.session_state.get("structured_cv_json")
            )
            if not has_active_profile and not st.session_state.get("onboarding_complete", False):
                st.session_state.page = "landing"
                st.session_state.nav_page = "landing"
                st.session_state.onboarding_complete = False
                try:
                    st.query_params["page"] = "landing"
                except Exception:
                    pass

        url_page = read_url_page(st.session_state.get("page", "landing"))
        aliases = {"improve_cv": "cv_documents", "jobs": "job_assist", "interview": "real_interview", "interview_practice": "real_interview", "prepare_job": "job_assist", "edit_cv": "cv_editor", "preview_cv": "cv_editor"}
        url_page = aliases.get(url_page, url_page)
        valid_pages = {"landing", "dashboard", "job_assist", "cv_documents", "workobot", "interview_practice", "real_interview", "cv_editor", "founder_dashboard", "onboarding"}

        try:
            _home_param = st.query_params.get("home", "")
        except Exception:
            _home_param = ""

        # Permanent routing rule:
        # landing and onboarding must always be honored, even before onboarding_complete.
        # This prevents old/dashboard paths from hijacking the updated onboarding page.
        if url_page == "dashboard" and _home_param:
            st.session_state.onboarding_complete = True
            st.session_state.page = "dashboard"
            st.session_state.nav_page = "dashboard"
        elif url_page == "landing":
            st.session_state.page = "landing"
            st.session_state.nav_page = "landing"
        elif url_page == "onboarding":
            st.session_state.page = "onboarding"
            st.session_state.nav_page = "onboarding"
            st.session_state.onboarding_complete = False
        elif url_page in valid_pages and st.session_state.get("onboarding_complete"):
            st.session_state.page = url_page
            st.session_state.nav_page = url_page

        if "page" not in st.session_state:
            st.session_state.page = "landing"
        if "onboarding_complete" not in st.session_state:
            st.session_state.onboarding_complete = False

        # Consume queued navigation after defaults so button clicks cannot be overwritten.
        try:
            pending = st.session_state.pop("_workzo_pending_nav", None)
            if pending in valid_pages:
                st.session_state.page = pending
                st.session_state.nav_page = pending
                if pending == "onboarding":
                    st.session_state.onboarding_complete = False
        except Exception:
            pass

        if st.session_state.page == "landing":
            show_landing_page()
            return
        if st.session_state.page == "onboarding" or not st.session_state.get("onboarding_complete", False):
            show_onboarding()
            return

        try:
            if callable(globals().get("render_workzo_header")):
                render_workzo_header()
        except Exception:
            pass
        show_dashboard()
        return
    except Exception as exc:
        try:
            st.error(f"WorkZo router error: {exc}")
            st.exception(exc)
        except Exception:
            raise



# =========================================================
# WorkZo v7 consolidated fixes (applied BEFORE router render)
# =========================================================
def _workzo_apply_v7_fixes() -> None:
    """Final pre-router monkey patches for CV structure, PDF, navigation, UI, and profile context."""
    import re, ast, html, json
    try:
        import streamlit as st
    except Exception:
        return

    # ---------- text cleanup ----------
    def wz7_clean_text(value):
        text = str(value or "")
        replacements = {
            "ðŸš€":"🚀", "ðŸ¤–":"🤖", "ðŸ§­":"🧭", "ðŸ“„":"📄", "ðŸŽ¯":"🎯", "ðŸ“Œ":"📌",
            "âœ“":"✓", "âœ…":"✅", "â€¢":"•", "â€“":"–", "â€”":"—", "â€˜":"'", "â€™":"'", "â€œ":"\"", "â€\x9d":"\"", "â€":"\"",
            "Ã¢â‚¬â€œ":"–", "Ã¢â‚¬â€":"—", "Ã¢â‚¬Â¢":"•", "Â":"", "�":"",
            "Linked In":"LinkedIn", "Manage Engine":"ManageEngine", "Service Desk":"ServiceDesk", "My SQL":"MySQL", "You Tube":"YouTube", "Text Blob":"TextBlob",
            " in for m ":" inform ", " for m ":" form ", " in itiatives":" initiatives", "In dian":"Indian",
            "CV CV missing":"CV missing", "Bot Work-O-Bot":"Work-O-Bot", "Bot Work O Bot":"Work-O-Bot",
        }
        for a,b in replacements.items(): text=text.replace(a,b)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()
    globals()['wz7_clean_text'] = wz7_clean_text

    # ---------- robust list/dict coercion ----------
    def wz7_maybe_literal(value):
        if isinstance(value, str):
            v=value.strip()
            if (v.startswith('{') and v.endswith('}')) or (v.startswith('[') and v.endswith(']')):
                try: return ast.literal_eval(v)
                except Exception:
                    try: return json.loads(v)
                    except Exception: return value
        return value

    def wz7_as_list(value):
        value=wz7_maybe_literal(value)
        if value is None or value=="": return []
        if isinstance(value, list): return value
        if isinstance(value, tuple): return list(value)
        if isinstance(value, dict): return [value]
        if isinstance(value, str):
            parts=[]
            for line in re.split(r"\n|;|\s+•\s+", value):
                line=wz7_clean_text(line).strip(' -•*')
                if line: parts.append(line)
            return parts or [wz7_clean_text(value)]
        return [value]

    def wz7_clean_bullets(value):
        out=[]
        for item in wz7_as_list(value):
            item=wz7_maybe_literal(item)
            if isinstance(item, dict):
                # If a dict accidentally sits as a bullet, unfold its useful text.
                for k in ('bullet','text','description','details','summary'):
                    if item.get(k): out.extend(wz7_clean_bullets(item.get(k)))
                if item.get('bullets'): out.extend(wz7_clean_bullets(item.get('bullets')))
                continue
            txt=wz7_clean_text(item).strip(' -•*')
            if txt and txt not in out: out.append(txt)
        return out

    def wz7_clean_projects(value):
        value=wz7_maybe_literal(value)
        projects=[]
        if isinstance(value, str):
            maybe=wz7_maybe_literal(value)
            if maybe is not value:
                value=maybe
            else:
                # Fallback: split project blocks.
                current=None
                for line in [x.strip() for x in value.splitlines() if x.strip()]:
                    if not line.startswith(('-', '•')) and len(line) < 90:
                        if current: projects.append(current)
                        current={'name': wz7_clean_text(line), 'bullets': []}
                    else:
                        if current is None: current={'name':'Project', 'bullets': []}
                        current['bullets'].append(wz7_clean_text(line).strip(' -•*'))
                if current: projects.append(current)
                return projects
        if isinstance(value, dict): value=[value]
        for pr in value if isinstance(value, list) else []:
            pr=wz7_maybe_literal(pr)
            if isinstance(pr, str):
                pr=wz7_maybe_literal(pr)
            if isinstance(pr, dict):
                raw_name=pr.get('name') or pr.get('title') or pr.get('project') or ''
                raw_name=wz7_maybe_literal(raw_name)
                if isinstance(raw_name, dict):
                    # Handles {'name': "{'name':'Magist','bullets':[...]}"}
                    nested=raw_name
                    name=wz7_clean_text(nested.get('name') or nested.get('title') or '')
                    bullets=wz7_clean_bullets(nested.get('bullets') or nested.get('description') or pr.get('bullets'))
                else:
                    name=wz7_clean_text(raw_name)
                    bullets=wz7_clean_bullets(pr.get('bullets') or pr.get('description') or pr.get('details'))
                if not name and bullets:
                    name='Project'
                if name or bullets:
                    projects.append({'name': name, 'bullets': bullets})
            elif isinstance(pr, str) and pr.strip():
                projects.append({'name': wz7_clean_text(pr), 'bullets': []})
        # de-dupe
        seen=set(); final=[]
        for pr in projects:
            key=(pr.get('name','').lower(), tuple(pr.get('bullets',[])[:2]))
            if key not in seen:
                seen.add(key); final.append(pr)
        return final

    def wz7_clean_experience(value):
        value=wz7_maybe_literal(value)
        if isinstance(value, dict): value=[value]
        if isinstance(value, str):
            # keep old parser if available
            parser=globals().get('parse_experience_text_to_items')
            try: value=parser(value) if callable(parser) else []
            except Exception: value=[]
        out=[]
        for job in value if isinstance(value, list) else []:
            job=wz7_maybe_literal(job)
            if not isinstance(job, dict): continue
            out.append({
                'title': wz7_clean_text(job.get('title') or job.get('role') or job.get('position')),
                'company': wz7_clean_text(job.get('company') or job.get('employer')),
                'dates': wz7_clean_text(job.get('dates') or ' - '.join([str(job.get('start_date') or job.get('startDate') or '').strip(), str(job.get('end_date') or job.get('endDate') or '').strip()]).strip(' -')),
                'bullets': wz7_clean_bullets(job.get('bullets') or job.get('achievements') or job.get('responsibilities') or job.get('description')),
            })
        return out

    def wz7_normalize_cv_data(data):
        if not isinstance(data, dict): data={}
        contact=data.get('contact') if isinstance(data.get('contact'), dict) else data.get('personal_info') if isinstance(data.get('personal_info'), dict) else {}
        normalized={
            'full_name': wz7_clean_text(data.get('full_name') or data.get('name')),
            'target_role': wz7_clean_text(data.get('target_role') or data.get('current_role') or data.get('headline') or data.get('title')),
            'contact': {
                'phone': wz7_clean_text(contact.get('phone') or data.get('phone')),
                'email': wz7_clean_text(contact.get('email') or data.get('email')),
                'location': wz7_clean_text(contact.get('location') or data.get('location')),
                'linkedin': wz7_clean_text(contact.get('linkedin') or data.get('linkedin')),
            },
            'professional_summary': wz7_clean_text(data.get('professional_summary') or data.get('summary') or data.get('profile')),
            'core_skills': wz7_clean_bullets(data.get('core_skills') or data.get('skills') or data.get('sidebar_skills')),
            'tools_technologies': wz7_clean_bullets(data.get('tools_technologies') or data.get('tools') or data.get('technologies')),
            'work_experience': wz7_clean_experience(data.get('work_experience') or data.get('experience') or data.get('main_experience')),
            'projects': wz7_clean_projects(data.get('projects')),
            'education': [],
            'certifications': wz7_clean_bullets(data.get('certifications')),
            'languages': wz7_clean_bullets(data.get('languages')),
            'suggested_additions': wz7_clean_bullets(data.get('suggested_additions')),
            'details_to_confirm': wz7_clean_bullets(data.get('details_to_confirm')),
            'honesty_audit': data.get('honesty_audit') if isinstance(data.get('honesty_audit'), dict) else {'omitted_missing_jd_requirements': [], 'rephrased_terms': [], 'needs_user_confirmation': []},
        }
        edu=data.get('education') or data.get('main_education') or []
        edu=wz7_maybe_literal(edu)
        if isinstance(edu, dict): edu=[edu]
        if isinstance(edu, str):
            parser=globals().get('parse_education_text_to_items')
            try: edu=parser(edu) if callable(parser) else []
            except Exception: edu=[]
        for ed in edu if isinstance(edu, list) else []:
            ed=wz7_maybe_literal(ed)
            if isinstance(ed, dict):
                normalized['education'].append({'degree':wz7_clean_text(ed.get('degree') or ed.get('qualification') or ed.get('area')), 'institution':wz7_clean_text(ed.get('institution') or ed.get('school') or ed.get('university') or ed.get('college')), 'dates':wz7_clean_text(ed.get('dates') or ed.get('year') or ed.get('date'))})
        return normalized

    globals()['_coerce_structured_resume_schema'] = wz7_normalize_cv_data
    globals()['_workzo_final_preview_data'] = wz7_normalize_cv_data

    def wz7_build_cv_text(data):
        d=wz7_normalize_cv_data(data or {})
        lines=[]
        for x in [d.get('full_name'), d.get('target_role')]:
            if x: lines.append(x)
        contact=d.get('contact') or {}
        c=' | '.join([contact.get(k,'') for k in ['phone','email','location','linkedin'] if contact.get(k)])
        if c: lines.append(c)
        def section(name): lines.extend(['', name])
        if d.get('professional_summary'):
            section('Professional Summary'); lines.append(d['professional_summary'])
        skills=list(dict.fromkeys((d.get('core_skills') or [])+(d.get('tools_technologies') or [])))
        if skills:
            section('Skills'); lines.extend(['- '+x for x in skills])
        if d.get('work_experience'):
            section('Experience')
            for job in d['work_experience']:
                hdr=' | '.join([job.get(k,'') for k in ['title','company','dates'] if job.get(k)])
                if hdr: lines.append(hdr)
                lines.extend(['- '+b for b in job.get('bullets',[])])
        if d.get('projects'):
            section('Projects')
            for pr in d['projects']:
                if pr.get('name'): lines.append(pr['name'])
                lines.extend(['- '+b for b in pr.get('bullets',[])])
        if d.get('education'):
            section('Education')
            for ed in d['education']:
                line=' | '.join([ed.get(k,'') for k in ['degree','institution','dates'] if ed.get(k)])
                if line: lines.append(line)
        if d.get('languages'):
            section('Languages'); lines.extend(['- '+x for x in d['languages']])
        if d.get('certifications'):
            section('Certifications'); lines.extend(['- '+x for x in d['certifications']])
        return '\n'.join([wz7_clean_text(x) for x in lines if x is not None]).strip()
    globals()['workzo_build_cv_text_from_editable']=wz7_build_cv_text

    # ---------- PDF: 3 genuinely different templates, all using structured data ----------
    def wz7_pdf_from_structured(title, structured_data, template_name='ATS Resume', target_country=''):
        """Safe WorkZo PDF renderer with 3 visibly different downloadable layouts.

        - No giant two-column ReportLab tables, so long CVs can flow across pages.
        - Always returns real PDF bytes beginning with %PDF.
        - Template styles differ in alignment, accent colour, section styling and spacing.
        """
        from io import BytesIO
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib import colors
        except Exception as exc:
            raise RuntimeError('ReportLab is required to generate a valid PDF. Please install reportlab.') from exc

        d = wz7_normalize_cv_data(structured_data or {})
        template = (template_name or 'ATS Resume').lower()
        is_minimal = 'minimal' in template
        is_pivot = 'pivot' in template or 'career' in template
        is_creative = 'creative' in template or 'modern' in template or 'portfolio' in template
        is_eu = 'eu' in template or 'europe' in template or 'germany' in template or 'professional' in template

        # Template-specific visual identity.
        accent = '#1d4ed8'
        section_bg = None
        name_align = 0
        margins = dict(rightMargin=38, leftMargin=38, topMargin=34, bottomMargin=34)
        if is_minimal:
            accent = '#111827'; name_align = 1; margins = dict(rightMargin=54, leftMargin=54, topMargin=42, bottomMargin=42)
        elif is_pivot:
            accent = '#7c3aed'; section_bg = '#f3e8ff'
        elif is_creative:
            accent = '#0891b2'; section_bg = '#ecfeff'
        elif is_eu:
            accent = '#0f766e'; section_bg = '#f0fdfa'

        buf = BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, **margins)
        base = getSampleStyleSheet()

        styles = {
            'name': ParagraphStyle('wzv17_name', parent=base['Title'], fontName='Helvetica-Bold', fontSize=22 if not is_minimal else 20, leading=26, alignment=name_align, textColor=colors.HexColor('#0f172a'), spaceAfter=2),
            'role': ParagraphStyle('wzv17_role', parent=base['BodyText'], fontSize=10.5, leading=13, alignment=name_align, textColor=colors.HexColor(accent), spaceAfter=4),
            'contact': ParagraphStyle('wzv17_contact', parent=base['BodyText'], fontSize=8.5, leading=10.5, alignment=name_align, textColor=colors.HexColor('#475569'), spaceAfter=8),
            'section': ParagraphStyle('wzv17_section', parent=base['Heading3'], fontName='Helvetica-Bold', fontSize=10.5, leading=13, textColor=colors.HexColor(accent), spaceBefore=10, spaceAfter=6),
            'body': ParagraphStyle('wzv17_body', parent=base['BodyText'], fontSize=9, leading=12.4, textColor=colors.HexColor('#111827'), spaceAfter=4),
            'bullet': ParagraphStyle('wzv17_bullet', parent=base['BodyText'], fontSize=8.8, leading=11.8, leftIndent=14, firstLineIndent=0, textColor=colors.HexColor('#111827'), spaceAfter=2),
            'mini': ParagraphStyle('wzv17_mini', parent=base['BodyText'], fontName='Helvetica-Bold', fontSize=9.2, leading=11.8, textColor=colors.HexColor('#111827'), spaceBefore=3, spaceAfter=2),
            'muted': ParagraphStyle('wzv17_muted', parent=base['BodyText'], fontSize=8.1, leading=10.2, textColor=colors.HexColor('#64748b'), spaceAfter=2),
        }

        def clean(x):
            return wz7_clean_text(x).strip()
        def P(x, style='body'):
            return Paragraph(html.escape(clean(x)), styles[style])
        def add_section(story, label):
            label = clean(label).upper() if not is_minimal else clean(label)
            if section_bg:
                tbl = Table([[Paragraph(html.escape(label), styles['section'])]], colWidths=[doc.width])
                tbl.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,-1), colors.HexColor(section_bg)),
                    ('LEFTPADDING', (0,0), (-1,-1), 7), ('RIGHTPADDING', (0,0), (-1,-1), 7),
                    ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                    ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor(accent)),
                ]))
                story.append(tbl); story.append(Spacer(1, 4))
            else:
                story.append(P(label, 'section'))
                if not is_minimal:
                    story.append(HRFlowable(width='100%', thickness=0.6, color=colors.HexColor(accent), spaceBefore=0, spaceAfter=4))
        def add_bullets(story, vals, limit=20):
            count = 0
            for v in vals or []:
                val = clean(v).strip(' -•*\t')
                if val:
                    story.append(Paragraph(html.escape(val), styles['bullet'], bulletText='-'))
                    count += 1
                    if count >= limit:
                        break

        story = []
        story.append(P(d.get('full_name') or 'Your Name', 'name'))
        story.append(P(d.get('target_role') or title or 'Professional CV', 'role'))
        contact = d.get('contact') or {}
        contact_line = ' | '.join([clean(contact.get(k, '')) for k in ['phone', 'email', 'location', 'linkedin'] if clean(contact.get(k, ''))])
        if contact_line:
            story.append(P(contact_line, 'contact'))
        story.append(HRFlowable(width='100%', thickness=1.1 if is_creative else 0.8, color=colors.HexColor(accent), spaceBefore=4, spaceAfter=9))

        if d.get('professional_summary'):
            add_section(story, 'Professional Summary' if not is_eu else 'Profile')
            story.append(P(d.get('professional_summary'), 'body'))

        skills = list(dict.fromkeys((d.get('core_skills') or []) + (d.get('tools_technologies') or [])))
        if skills:
            add_section(story, 'Skills')
            if is_minimal:
                story.append(P(' · '.join(skills[:28]), 'body'))
            else:
                add_bullets(story, skills, 32)

        if d.get('work_experience'):
            add_section(story, 'Experience' if not is_eu else 'Professional Experience')
            for job in d.get('work_experience') or []:
                if not isinstance(job, dict):
                    continue
                hdr = ' | '.join([clean(job.get(k, '')) for k in ['title', 'company', 'dates'] if clean(job.get(k, ''))])
                if hdr:
                    story.append(P(hdr, 'mini'))
                add_bullets(story, job.get('bullets', []), 7)
                story.append(Spacer(1, 4))

        if d.get('projects'):
            add_section(story, 'Projects')
            for pr in (d.get('projects') or [])[:6]:
                if not isinstance(pr, dict):
                    continue
                name = clean(pr.get('name') or pr.get('title') or '')
                if name:
                    story.append(P(name, 'mini'))
                add_bullets(story, pr.get('bullets', []), 4)
                story.append(Spacer(1, 3))

        if d.get('education'):
            add_section(story, 'Education')
            for ed in d.get('education') or []:
                if not isinstance(ed, dict):
                    continue
                line = ' | '.join([clean(ed.get(k, '')) for k in ['degree', 'institution', 'dates'] if clean(ed.get(k, ''))])
                if line:
                    story.append(P(line, 'body'))

        if d.get('languages'):
            add_section(story, 'Languages')
            if is_minimal:
                story.append(P(' · '.join([clean(x) for x in d.get('languages') if clean(x)]), 'body'))
            else:
                add_bullets(story, d.get('languages'), 12)

        if d.get('certifications'):
            add_section(story, 'Certifications')
            add_bullets(story, d.get('certifications'), 12)

        if not story:
            story = [P('WorkZo CV', 'name')]
        doc.build(story)
        buf.seek(0)
        data = buf.getvalue()
        if not data.startswith(b'%PDF'):
            raise ValueError('Invalid PDF generated')
        return data

    def wz7_pdf_from_text(title, cv_text, template_name='ATS Resume', target_country=''):
        data={'full_name':'','target_role':title,'professional_summary':wz7_clean_text(cv_text)}
        return wz7_pdf_from_structured(title, data, template_name, target_country)

    globals()['make_styled_pdf_from_structured_preview']=wz7_pdf_from_structured
    globals()['make_styled_pdf_from_cv_text']=wz7_pdf_from_text

    # ---------- user profile and migration logic ----------
    def wz7_sync_profile():
        status=str(st.session_state.get('user_status') or st.session_state.get('career_status') or '')
        migrates=any(x in status.lower() for x in ['migrate','abroad','relocat','move'])
        target_country=st.session_state.get('migration_country') if migrates else st.session_state.get('country')
        if not target_country: target_country=st.session_state.get('country','')
        profile={'career_status':status,'target_country':target_country,'country_features_enabled':bool(migrates),'language':st.session_state.get('preferred_language','English'),'target_role':st.session_state.get('target_role') or st.session_state.get('detected_target_role',''),'cv_text':st.session_state.get('cv_text','')}
        st.session_state['user_profile']=profile
        return profile
    globals()['workzo_sync_user_profile']=wz7_sync_profile

    # ---------- score preservation before every render ----------
    def wz7_preserve_scores():
        for key in ['cv_score_value','ats_score_value','application_readiness_value']:
            try:
                cur=int(st.session_state.get(key) or 0); best=int(st.session_state.get('_best_'+key) or 0)
                if cur < best: st.session_state[key]=best
                elif cur > best: st.session_state['_best_'+key]=cur
            except Exception: pass
    globals()['workzo_preserve_best_scores']=wz7_preserve_scores
    wz7_preserve_scores(); wz7_sync_profile()
    # ---------- reliable page-top navigation ----------
    def wz7_request_scroll_to_top():
        try:
            st.session_state['_workzo_scroll_to_top'] = True
            st.session_state['_workzo_page_nonce'] = str(int(st.session_state.get('_workzo_page_nonce', 0)) + 1)
        except Exception:
            pass

    def wz7_scroll_top():
        try:
            st.markdown('<span id="workzo-page-top"></span>', unsafe_allow_html=True)
            if st.session_state.pop('_workzo_scroll_to_top', False):
                # Streamlit currently has no native scroll-to-top API. st.iframe is the
                # supported replacement for the older deprecated components.html call.
                js = """<script>
                const doc = window.parent.document;
                const containers = [doc.querySelector('section.main'), doc.querySelector('[data-testid=\"stAppViewContainer\"]'), doc.scrollingElement, doc.documentElement, doc.body];
                containers.forEach(el => { if (el) { try { el.scrollTo({top:0,left:0,behavior:'instant'}); el.scrollTop = 0; } catch(e) {} } });
                </script>"""
                if hasattr(st, 'iframe'):
                    st.iframe(srcdoc=js, height=0)
                st.query_params['wz_top'] = st.session_state.get('_workzo_page_nonce', '1')
        except Exception:
            pass
    globals()['maybe_scroll_to_top']=wz7_scroll_top
    globals()['request_scroll_to_top']=wz7_request_scroll_to_top

    # ---------- UI CSS ----------
    st.markdown("""
    <style>
    .block-container{padding-top:0.75rem!important;}
    div[data-testid="stButton"] > button,
    div[data-testid="stDownloadButton"] > button,
    div[data-testid="stLinkButton"] > a{
      min-height:42px!important; padding:.55rem 1rem!important; border-radius:12px!important; font-size:1rem!important; width:auto!important; max-width:100%!important; white-space:normal!important;
    }
    .workzo-start-button-wrapper div[data-testid="stButton"] > button{
      min-height:58px!important; width:260px!important; min-width:260px!important; font-size:1.08rem!important; padding:.9rem 1.3rem!important; display:block!important; margin:0 auto!important;
    }
    .workzo-action-grid div[data-testid="stButton"] > button,
    .workzo-progress-action div[data-testid="stButton"] > button,
    div[data-testid="column"] div[data-testid="stButton"] > button{width:100%!important;}
    </style>
    """, unsafe_allow_html=True)

    # ---------- safer job match rendering (no mojibake, remote warning) ----------
    old_render_jobs=globals().get('render_curated_job_matches')
    def wz7_render_curated_job_matches(jobs, country_name=''):
        st.markdown('### Curated job matches')
        if not jobs:
            st.info('Live sources did not return strong matches. Use the search links below, then paste one job description into Understand Job for a precise fit check.'); return
        st.caption('Scores are guidance only. For remote roles, always confirm whether remote means worldwide or only within that country/time zone.')
        for idx, job in enumerate(jobs, start=1):
            title=wz7_clean_text(job.get('title') or 'Job'); company=wz7_clean_text(job.get('company') or 'Company not shown')
            loc=wz7_clean_text(job.get('location') or country_name or ''); score=int(job.get('match_score') or 0); badge=wz7_clean_text(job.get('badge') or 'Review')
            url=str(job.get('url') or ''); source=wz7_clean_text(job.get('source') or 'Source')
            with st.expander(f"{idx}. {title} at {company} — {score}% • {badge}", expanded=(idx<=3)):
                c1,c2=st.columns([2,1])
                with c1:
                    st.markdown(f"**Location / market:** {html.escape(loc)}")
                    st.markdown(f"**Source:** {html.escape(source)}")
                    if 'remote' in (loc+' '+source+' '+title).lower() or source.lower() in ['remotive','remoteok','we work remotely']:
                        st.warning('Remote role: confirm whether it is worldwide remote or restricted to a specific country/time zone before applying.')
                    st.markdown(f"**Assistant note:** {html.escape(wz7_clean_text(job.get('assistant_note') or 'Review this JD before tailoring.'))}")
                    if job.get('matched_skills'): st.markdown('**Matched from your CV:** '+', '.join(html.escape(wz7_clean_text(x)) for x in job.get('matched_skills',[])[:6]))
                    if job.get('missing_or_stretch'): st.markdown('**Reality check / confirm before adding:** '+', '.join(html.escape(wz7_clean_text(x)) for x in job.get('missing_or_stretch',[])[:6]))
                    if job.get('summary'): st.caption(wz7_clean_text(job.get('summary'))[:500])
                with c2:
                    if url: st.link_button('Open job', url, use_container_width=True)
                    if st.button('Use in Understand Job', key=f'wz7_use_job_{idx}_{abs(hash(title+company))%99999}', use_container_width=True):
                        seed=f"{title}\nCompany: {company}\nLocation: {loc}\nSource: {source}\n\n{wz7_clean_text(job.get('summary',''))}\n\nApply URL: {url}"
                        st.session_state['last_understand_job_description']=seed; st.session_state['job_desc_v42']=seed; st.session_state['job_assist_mode_key']='understand'; st.session_state['page']='job_assist'; st.session_state['nav_page']='job_assist'; st.rerun()
                    st.caption('Practice interview after you receive an interview response. First use Understand Job, Improve CV, and Cover Letter.')
        
    globals()['render_curated_job_matches']=wz7_render_curated_job_matches

    # ---------- Work-O-Bot prompt improvements ----------
    def wz7_workobot_suggestions(country_name='Germany'):
        role=st.session_state.get('target_role') or st.session_state.get('detected_target_role') or 'my target role'
        lang=st.session_state.get('preferred_language','English')
        return [
          ('Mock test', f'Create realistic interview/mock test questions for {role} based on my CV. Use {lang} for both questions and answers.'),
          ('Career communication', f'Help me write recruiter/HR messages for {role} in {country_name}, using {lang}.'),
          ('Skill gap help', f'Based on my CV and target role {role}, what skill gap should I fix first?'),
          ('Job search plan', f'Create a practical job search plan for {role} in {country_name}.')]
    globals()['get_workobot_suggestions']=wz7_workobot_suggestions

try:
    _workzo_apply_v7_fixes()
except Exception as _wz7_exc:
    try:
        st.warning(f"WorkZo v7 patch warning: {_wz7_exc}")
    except Exception:
        pass



# --- WorkZo v12 verified UI + navigation + score patches ---
def workzo_preserve_best_scores_v12() -> None:
    try:
        for key in ["cv_score_value", "ats_score_value", "application_readiness_value"]:
            best_key = "_best_" + key
            current = int(st.session_state.get(key) or 0)
            best = int(st.session_state.get(best_key) or 0)
            if current < best:
                st.session_state[key] = best
            elif current > best:
                st.session_state[best_key] = current
    except Exception:
        pass

def request_scroll_to_top() -> None:
    try:
        import time
        st.session_state["_workzo_scroll_to_top"] = True
        st.session_state["_workzo_page_nonce"] = str(int(time.time() * 1000))
        st.query_params["wz_top"] = st.session_state["_workzo_page_nonce"]
    except Exception:
        pass

def maybe_scroll_to_top() -> None:
    try:
        if st.session_state.pop("_workzo_scroll_to_top", False):
            script = """
            <script>
            const scrollTop = () => {
              try { window.parent.scrollTo({top:0,left:0,behavior:'instant'}); } catch(e) {}
              try { window.parent.document.querySelector('section.main').scrollTo(0,0); } catch(e) {}
              try { window.parent.document.querySelector('[data-testid="stAppViewContainer"]').scrollTo(0,0); } catch(e) {}
            };
            scrollTop(); setTimeout(scrollTop, 60); setTimeout(scrollTop, 220);
            </script>
            """
            if hasattr(st, "iframe"):
                st.iframe(srcdoc=script, height=0, width=0)
            else:
                st.markdown('<span id="workzo-page-top"></span>', unsafe_allow_html=True)
    except Exception:
        pass

try:
    workzo_preserve_best_scores_v12()
    st.markdown("""
    <style>
    /* v12 button system */
    div[data-testid="stButton"] > button,
    div.stButton > button,
    div[data-testid="stDownloadButton"] > button,
    div[data-testid="stLinkButton"] > a {
        min-height: 46px !important;
        padding: 0.70rem 1.10rem !important;
        border-radius: 13px !important;
        font-size: 1.02rem !important;
        font-weight: 650 !important;
        white-space: normal !important;
        text-align: center !important;
        max-width: 100% !important;
    }
    /* Primary buttons are the main CTAs; this fixes the visible Start Now button. */
    button[kind="primary"],
    div[data-testid="stButton"] button[kind="primary"],
    div[data-testid="stButton"] > button[data-testid="baseButton-primary"] {
        min-height: 66px !important;
        min-width: 280px !important;
        padding: 1rem 2rem !important;
        border-radius: 16px !important;
        font-size: 1.18rem !important;
        font-weight: 850 !important;
    }
    .workzo-start-button-wrapper,
    .workzo-start-button-wrapper + div,
    .workzo-start-button-wrapper ~ div {
        text-align:center !important;
    }
    .workzo-resume-button-row div[data-testid="stButton"] > button,
    .workzo-action-grid div[data-testid="stButton"] > button,
    .workzo-progress-action div[data-testid="stButton"] > button,
    div[data-testid="column"] div[data-testid="stButton"] > button {
        width: 100% !important;
    }
    .workzo-progress-done { color:#22c55e!important; font-weight:900!important; margin-left:8px!important; }
    </style>
    """, unsafe_allow_html=True)
except Exception:
    pass

_workzo_run_router_if_available()


# --- WorkZo v6 final stability overrides ---
def workzo_preserve_best_scores() -> None:
    try:
        for key in ["cv_score_value", "ats_score_value", "application_readiness_value"]:
            best_key = "_best_" + key
            current = int(st.session_state.get(key) or 0)
            best = int(st.session_state.get(best_key) or 0)
            if current < best:
                st.session_state[key] = best
            elif current > best:
                st.session_state[best_key] = current
    except Exception:
        pass

try:
    workzo_preserve_best_scores()
    maybe_scroll_to_top()
except Exception:
    pass

# =========================================================
# WorkZo FINAL: HTML preview -> PDF via Playwright, fallback to ReportLab.
# No toolbox/sidebar monkey patches here. Sidebar belongs to 08_dashboard.py.
# =========================================================
def _workzo_html_preview_pdf_export(title, structured_data, template_name='ATS Resume', target_country=''):
    fallback = globals().get('_workzo_reportlab_pdf_fallback')
    try:
        from playwright.sync_api import sync_playwright
        html_doc = workzo_visual_cv_html_from_structured(structured_data or {}, template_name, target_country)
        html_doc = f"""<!doctype html><html><head><meta charset='utf-8'>
        <style>@page {{ size: A4; margin: 0; }} body {{ margin: 0; background: white; }}</style>
        </head><body>{html_doc}</body></html>"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={'width': 794, 'height': 1123}, device_scale_factor=1)
            page.set_content(html_doc, wait_until='networkidle')
            pdf_bytes = page.pdf(format='A4', print_background=True, margin={'top':'0mm','right':'0mm','bottom':'0mm','left':'0mm'})
            browser.close()
        return pdf_bytes
    except Exception as exc:
        try:
            st.warning(f'HTML-to-PDF export is not active, using fallback PDF. Details: {exc}')
        except Exception:
            pass
        if callable(fallback):
            return fallback(title, structured_data, template_name, target_country)
        return wz7_pdf_from_structured(title, structured_data, template_name, target_country)

try:
    if '_workzo_reportlab_pdf_fallback' not in globals():
        globals()['_workzo_reportlab_pdf_fallback'] = globals().get('make_styled_pdf_from_structured_preview')
    globals()['make_styled_pdf_from_structured_preview'] = _workzo_html_preview_pdf_export
except Exception:
    pass
