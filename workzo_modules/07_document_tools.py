

def _wz26_company_context_for_docs(company_name: str = "", company_website: str = "") -> str:
    """Fast optional company context for cover letters/CV tailoring."""
    company_name = str(company_name or "").strip()
    company_website = str(company_website or "").strip()
    cache_key = f"_wz26_doc_company_context::{company_name}::{company_website}"
    if st is not None and cache_key in st.session_state:
        return st.session_state.get(cache_key, "")
    context = ""
    if company_website:
        url = company_website if company_website.startswith(("http://", "https://")) else "https://" + company_website
        try:
            import requests, re as _re
            r = requests.get(url, timeout=3, headers={"User-Agent": "WorkZoAI/1.0"})
            if r.ok:
                txt0 = _re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", " ", r.text, flags=_re.I)
                txt0 = _re.sub(r"<[^>]+>", " ", txt0)
                txt0 = _re.sub(r"\s+", " ", txt0).strip()
                context = txt0[:1800]
        except Exception:
            context = ""
    if not context and st is not None:
        context = st.session_state.get("company_context", "")
    if not context and company_name:
        context = f"Company name provided by user: {company_name}. Do not invent company facts; use only the job description and CV unless the user provides more company details."
    if st is not None:
        st.session_state[cache_key] = context
        if context:
            st.session_state["company_context"] = context
    return context

# WorkZo modular split v138
# Source: app_workzo_v137_stable_no_feature_change.py, lines 9297-9819
def get_clean_cv_source_for_tools() -> str:
    """Return the exact live edited CV text first, then fall back to AI/CV sources."""
    import streamlit as st
    priority_keys = [
        "cv_editor_widget",
        "workzo_live_cv_text",
        "improved_cv_edit_buffer_v92",
        "improved_cv_text_v92",
        "generated_country_cv_text",
        "clean_structured_cv_text",
        "approved_cv_text",
        "structured_cv_text",
        "final_cv_text",
        "improved_cv_text",
        "cv_text",
        "uploaded_cv_text",
    ]
    for key in priority_keys:
        value = st.session_state.get(key, "")
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""



def workzo_translate_structured_resume_live(structured_data: dict, target_country: str, output_language: str) -> dict:
    """Translate/improve editable CV sections while keeping protected facts stable."""
    try:
        if not output_language or str(output_language).strip().lower() == "english":
            return structured_data or {}
        translated = transform_structured_resume_for_job_json(
            structured_data or {},
            "",
            f"Translate the editable CV wording and section content into {output_language}. Keep names, companies, dates, education, email, phone, locations, links and language levels unchanged unless already written differently by the user.",
            target_country or st.session_state.get("country", "International"),
            output_language,
        )
        return translated if isinstance(translated, dict) and translated else (structured_data or {})
    except Exception:
        return structured_data or {}


def show_document_tools():
    # Snapshot global country context so the Country-Specific Resume Builder can never leak changes across the app.
    _main_country_snapshot = st.session_state.get("country")
    _main_migration_snapshot = st.session_state.get("migration_country")

    st.subheader(txt("document_tools"))
    st.caption(txt("document_hub_caption"))

    show_country_builder = is_applying_abroad_status(st.session_state.get("user_status", ""))
    tab_labels = [ui_label("Improve / Update CV")]
    if show_country_builder:
        tab_labels.append(ui_label("Country resume explorer"))
    tab_labels.append(ui_label("Cover Letter Generator + Language"))
    tabs = st.tabs(tab_labels)
    cover_tab = tabs[2] if show_country_builder else tabs[1]

    # -----------------------------------------------------
    # 1. Improve / Update CV
    # -----------------------------------------------------
    with tabs[0]:
        st.markdown(f"### {ui_label('Improve / Update CV')}")
        st.caption(ui_label("Tailor your existing CV to a job description, update details, preview it in a country-aware template, then download it."))

        # Improve / Update CV uses the country chosen during onboarding, not the temporary country selected in the Country-Specific Resume Builder.
        selected_country_for_cv = onboarding_country_for_cv()
        user_status_for_template = st.session_state.get("user_status", "Not specified")
        template_options = get_cv_template_options(selected_country_for_cv, user_status_for_template)
        template_names = list(template_options.keys()) if template_options else ["ATS Classic"]

        col_a, col_b = st.columns(2)
        with col_a:
            selected_template = st.selectbox(
                ui_label("CV template style"),
                template_names,
                index=0,
                key="improve_cv_template_style_v92",
                help=ui_label("This uses the country selected during onboarding. Country-Specific Resume Builder choices do not affect this tab.")
            )
        with col_b:
            output_language = st.selectbox(
                ui_label("CV language"),
                language_options,
                index=language_options.index(st.session_state.get("preferred_language", "English")) if st.session_state.get("preferred_language", "English") in language_options else 0,
                key="improve_cv_output_language_v92"
            )

        st.caption(ui_label("WorkZo uses the approved structured CV profile here, not the messy raw PDF extraction."))

        # Structured resume review editor removed from this page to reduce confusion.
        # Improve/Update CV now uses the approved structured CV source silently.
        current_cv = get_clean_cv_source_for_tools()

        job_desc_cv = st.text_area(
            ui_label("Paste the job description"),
            height=210,
            key="improve_cv_for_job_desc",
            placeholder=ui_label("Paste the job description here. If you came from Understand Job, it should already be filled."),
        )

        # If the user clicked an ATS suggestion button on the previous run, prefill notes before the widget is created.
        pending_ats_notes = st.session_state.pop("workzo_pending_ats_notes_v92", "") if st.session_state.get("workzo_pending_ats_notes_v92") else ""
        if pending_ats_notes and not str(st.session_state.get("improve_update_cv_notes_v92", "")).strip():
            st.session_state["improve_update_cv_notes_v92"] = pending_ats_notes

        update_notes = st.text_area(
            ui_label("Optional updates to include"),
            height=120,
            key="improve_update_cv_notes_v92",
            placeholder=ui_label("Example: Add B1 German, new certificate, new project, updated phone number, or career break note."),
        )

        st.markdown("#### " + ui_label("Step 1 — Generate or regenerate your improved CV"))
        st.caption(ui_label("Use this button after changing the job description or optional notes."))
        if st.button(ui_label("Generate Improved CV"), key="btn_generate_improved_cv_v92", type="primary", use_container_width=True):
            job_desc_combined = (job_desc_cv or "").strip()
            notes_combined = (update_notes or "").strip()
            if not current_cv.strip():
                st.warning(ui_label("Please provide your CV."))
            elif not job_desc_combined.strip() and not notes_combined.strip():
                st.warning(ui_label("Please paste a job description or add update notes."))
            else:
                with st.spinner(ui_label("Building a clean, truthful, downloadable CV...")):
                    # Anti-drift pipeline: Extract -> Transform -> Generate.
                    # The model works with JSON data, not visual resume text.
                    source_structured = st.session_state.get("structured_cv_json")
                    if not isinstance(source_structured, dict) or not source_structured:
                        source_structured = extract_structured_resume_json(current_cv, selected_country_for_cv, user_status_for_template)
                    source_structured = validate_resume_dates_and_sections(source_structured or {})
                    tailored_structured = transform_structured_resume_for_job_json(
                        source_structured,
                        job_desc_combined,
                        notes_combined,
                        selected_country_for_cv,
                        output_language,
                    )
                    clean_cv = _format_structured_resume_profile(tailored_structured)
                    audit = tailored_structured.get("honesty_audit", {}) if isinstance(tailored_structured, dict) else {}
                    result = """1. Tailoring Summary
- Fit level: Generated from structured CV data.
- Main improvement: Tailored summary and bullet wording without changing protected facts.
- Changes made: Protected names, companies, dates, education, and contact fields were re-injected after AI transformation.

3. Changes Made
- Reordered and improved truthful keywords where supported.
- Missing job requirements were kept in suggested additions, not added as claims.

4. Details to Confirm
""" + "\n".join([f"- {x}" for x in _as_list(tailored_structured.get("details_to_confirm"))[:12]])
                    st.session_state.structured_cv_json = tailored_structured
                    st.session_state.structured_cv_profile = clean_cv
                    st.session_state.clean_structured_cv_text = clean_cv
                    st.session_state.cv_text = clean_cv
                    st.session_state.improved_cv_result_v92 = result
                    st.session_state.improved_cv_text_v92 = clean_cv
                    st.session_state.improved_cv_structured_v92 = tailored_structured
                    st.session_state.improved_cv_edit_buffer_v92 = clean_cv
                    st.session_state.improved_cv_template_v92 = selected_template
                    st.session_state.improved_cv_country_v92 = selected_country_for_cv
                    st.session_state.improved_cv_language_v92 = output_language
                    st.session_state["prepare_cv_tailored"] = True
                    st.success(ui_label("Improved CV generated. Review and edit it below."))

        if st.session_state.get("improved_cv_text_v92"):
            st.markdown("### " + ui_label("Step 2 — Result summary"))
            st.caption(ui_label("Review the score and only use suggestions that are true for your experience."))
            result = st.session_state.get("improved_cv_result_v92", "")
            with st.expander(ui_label("Tailoring summary"), expanded=False):
                summary = get_section_text(result, ["Tailoring Summary", "Changes Made", "Details to Confirm"], fallback_to_full=False)
                st.write(summary if summary else ui_label("Review the improved CV below."))

            structured_audit_data = st.session_state.get("structured_cv_json", {}) if isinstance(st.session_state.get("structured_cv_json", {}), dict) else {}
            if structured_audit_data.get("honesty_audit") or structured_audit_data.get("suggested_additions"):
                with st.expander(ui_label("Anti-drift validation report"), expanded=False):
                    if structured_audit_data.get("suggested_additions"):
                        st.markdown("**" + ui_label("Missing JD items kept out of the CV unless you confirm them:") + "**")
                        for item in _as_list(structured_audit_data.get("suggested_additions"))[:10]:
                            st.markdown(f"- {html.escape(str(item))}")
                    audit_obj = structured_audit_data.get("honesty_audit") or {}
                    if audit_obj.get("needs_user_confirmation"):
                        st.markdown("**" + ui_label("Protected-field / truth checks:") + "**")
                        for item in _as_list(audit_obj.get("needs_user_confirmation"))[:10]:
                            st.markdown(f"- {html.escape(str(item))}")
                    if audit_obj.get("rephrased_terms"):
                        st.markdown("**Rephrased for ATS, based on source facts:**")
                        for item in _as_list(audit_obj.get("rephrased_terms"))[:8]:
                            st.markdown(f"- {html.escape(str(item))}")

            audit = build_honesty_impact_audit(current_cv, st.session_state.get("improved_cv_text_v92", ""), job_desc_cv)
            with st.expander(ui_label("ATS score details"), expanded=False):
                ats_match = audit.get("ats_match", {}) or {}
                if ats_match:
                    st.metric(ui_label("Deterministic ATS match for this job"), f"{ats_match.get('ats_match_score', 0)}%")
                    st.caption(ui_label("This score is calculated from keyword coverage and structure. AI does not guess this number."))
                    if ats_match.get("matched_keywords"):
                        st.markdown("**Matched keywords:** " + ", ".join(ats_match.get("matched_keywords", [])[:10]))
                    if ats_match.get("missing_keywords"):
                        st.markdown("**Missing keywords to consider only if true:** " + ", ".join(ats_match.get("missing_keywords", [])[:10]))
                if audit.get("added_keywords"):
                    st.markdown("**Added / strengthened keywords:** " + ", ".join(audit.get("added_keywords", [])[:10]))
                if audit.get("needs_confirmation"):
                    st.warning(ui_label("Please confirm these are truthful before downloading:"))
                    for item in audit.get("needs_confirmation", [])[:8]:
                        st.markdown(f"- {html.escape(str(item))}")
                else:
                    st.success(ui_label("No obvious unsupported metrics or risky added claims were detected."))

            # Friendly guidance: what the user can do when the ATS score is still low.
            ats_match_for_help = audit.get("ats_match", {}) or {}
            missing_for_help = _as_list(ats_match_for_help.get("missing_keywords"))[:8]
            if ats_match_for_help:
                st.markdown("### " + ui_label("How to improve this ATS score"))
                score_value = int(ats_match_for_help.get("ats_match_score", 0) or 0)
                if score_value < 70:
                    st.info(ui_label("Your CV can improve for this job. Add only truthful keywords and examples you can explain in an interview."))
                else:
                    st.success(ui_label("Good match. You can still improve it by adding truthful role-specific wording."))
                if missing_for_help:
                    st.markdown("**" + ui_label("Missing keywords to consider only if true:") + "** " + ", ".join([html.escape(str(x)) for x in missing_for_help]))
                    st.markdown("**" + ui_label("Suggested honest next step:") + "** " + ui_label("Add short examples under Optional updates, then generate the CV again."))
                    if st.button(ui_label("Use these keywords as honest update notes"), key="btn_use_ats_keywords_v92", use_container_width=True):
                        st.session_state["workzo_pending_ats_notes_v92"] = "Consider these job keywords only if truthful: " + ", ".join([str(x) for x in missing_for_help])
                        st.success(ui_label("I added these as optional notes. Review them, remove anything untrue, then regenerate."))
                        st.rerun()

            render_country_specific_honesty_audit(
                st.session_state.get("improved_cv_text_v92", ""),
                st.session_state.get("improved_cv_country_v92", selected_country_for_cv),
                st.session_state.get("structured_cv_json", {}),
                expanded=False
            )

            st.markdown(f"### {ui_label('Step 3 — Edit, preview, and download')}")
            preview_template = st.session_state.get("improved_cv_template_v92", selected_template)
            preview_country = st.session_state.get("improved_cv_country_v92", selected_country_for_cv)

            editable_structured = workzo_editable_cv_editor(
                "improved_cv_preview_v141",
                st.session_state.get("improved_cv_text_v92", ""),
                st.session_state.get("improved_cv_structured_v92") or st.session_state.get("structured_cv_json", {})
            )

            # IMPORTANT:
            # The visual preview and download must use the current editable widgets directly.
            # Do NOT prefer st.session_state["improved_cv_structured_v92"] here, because that can
            # contain an older/stale version and is the reason Experience/Education appeared as "—".
            preview_structured = editable_structured
            preview_cv = workzo_build_cv_text_from_editable(preview_structured)

            # Keep one live source of truth for preview, download, translation, dashboard save, and later reruns.
            st.session_state["workzo_live_cv_structured"] = preview_structured
            st.session_state["workzo_live_cv_text"] = preview_cv
            st.session_state["cv_editor_widget"] = preview_cv
            st.session_state["clean_structured_cv_text"] = preview_cv
            st.session_state["cv_text"] = preview_cv
            st.session_state.improved_cv_structured_v92 = preview_structured
            st.session_state.structured_cv_json = preview_structured
            st.session_state.improved_cv_text_v92 = preview_cv
            st.session_state.improved_cv_edit_buffer_v92 = preview_cv
            st.session_state["prepare_cv_tailored"] = True

            st.markdown("#### " + ui_label("After editing"))
            if st.button(ui_label("Update Preview & Use These Edits"), key="btn_update_improved_cv_preview_v92", type="primary", use_container_width=True):
                # Force-sync current editor widgets to every source older code might read.
                st.session_state["workzo_live_cv_structured"] = preview_structured
                st.session_state["workzo_live_cv_text"] = preview_cv
                st.session_state["cv_editor_widget"] = preview_cv
                st.session_state["clean_structured_cv_text"] = preview_cv
                st.session_state["cv_text"] = preview_cv
                st.session_state.improved_cv_structured_v92 = preview_structured
                st.session_state.structured_cv_json = preview_structured
                st.session_state.improved_cv_text_v92 = preview_cv
                st.session_state.improved_cv_edit_buffer_v92 = preview_cv
                st.success(ui_label("Preview updated with your edits."))
                st.rerun()

            tr_col1, tr_col2 = st.columns([2, 1])
            with tr_col1:
                translate_language = st.selectbox(
                    ui_label("Translate this improved CV to"),
                    language_options,
                    index=language_options.index(st.session_state.get("improved_cv_language_v92", output_language)) if st.session_state.get("improved_cv_language_v92", output_language) in language_options else 0,
                    key="translate_improved_cv_language_v92",
                )
            with tr_col2:
                st.write("")
                if st.button(ui_label("Translate CV"), key="btn_translate_improved_cv_v92"):
                    with st.spinner(ui_label("Translating CV while keeping facts unchanged...")):
                        translated_structured = workzo_translate_structured_resume_live(preview_structured, preview_country, translate_language)
                        translated_cv = workzo_build_cv_text_from_editable(translated_structured)
                        st.session_state["workzo_live_cv_structured"] = translated_structured
                        st.session_state["workzo_live_cv_text"] = translated_cv
                        st.session_state["cv_editor_widget"] = translated_cv
                        st.session_state["clean_structured_cv_text"] = translated_cv
                        st.session_state["cv_text"] = translated_cv
                        st.session_state.improved_cv_structured_v92 = translated_structured
                        st.session_state.structured_cv_json = translated_structured
                        st.session_state.improved_cv_text_v92 = translated_cv
                        st.session_state.improved_cv_edit_buffer_v92 = translated_cv
                        st.session_state.improved_cv_language_v92 = translate_language
                        st.success(ui_label("CV translated. Review the preview below."))
                        st.rerun()

            st.html(workzo_visual_cv_html_from_structured(preview_structured, preview_template, preview_country))

            safe_country = re.sub(r"[^a-z0-9]+", "_", str(preview_country).lower()).strip("_") or "country"
            safe_template = re.sub(r"[^a-z0-9]+", "_", str(preview_template).lower()).strip("_") or "template"
            safe_file_base = f"workzo_improved_{safe_country}_{safe_template}_cv"
            clean_download_cv = strip_markdown_for_resume(preview_cv)

            pdf_data = make_styled_pdf_from_structured_preview(
                f"WorkZo Improved CV - {preview_country}",
                preview_structured,
                preview_template,
                preview_country
            )
            rendercv_yaml = rendercv_yaml_from_cv_text(clean_download_cv, preview_template, preview_country)
            rendercv_pdf = try_rendercv_pdf_from_yaml(rendercv_yaml)

            dl_col1, dl_col2, dl_col3, dl_col4 = st.columns(4)
            with dl_col1:
                st.download_button(
                    label=ui_label("Download PDF"),
                    data=pdf_data,
                    file_name=f"{safe_file_base}.pdf",
                    mime="application/pdf",
                    key="download_improved_cv_pdf_v92",
                    use_container_width=True,
                    on_click=track_event,
                    args=("cv_downloaded", "CV & Documents", {"format": "pdf"})
                )
            with dl_col2:
                st.download_button(
                    label=ui_label("Download TXT"),
                    data=clean_download_cv.encode("utf-8"),
                    file_name=f"{safe_file_base}.txt",
                    mime="text/plain",
                    key="download_improved_cv_txt_v92",
                    use_container_width=True,
                    on_click=track_event,
                    args=("cv_downloaded", "CV & Documents", {"format": "txt"})
                )
            with dl_col3:
                if st.button(ui_label("Save Resume"), key="save_improved_cv_dashboard_v92", use_container_width=True):
                    set_new_resume_and_refresh(clean_download_cv)
                    st.success(ui_label("Saved as your dashboard resume."))
                    st.rerun()
            with dl_col4:
                if rendercv_pdf:
                    st.download_button(label=ui_label("Download RenderCV PDF"), data=rendercv_pdf, file_name=f"{safe_file_base}_rendercv.pdf", mime="application/pdf", key="download_improved_cv_rendercv_pdf_v1")

    # -----------------------------------------------------
    # 2. Country CV Template Builder
    # -----------------------------------------------------
    if show_country_builder:
      with tabs[1]:
        st.markdown(f"### {ui_label('Country resume explorer')}")
        st.caption(ui_label("Visible only for applying abroad / migration users. Main CV tools already use your target country automatically."))
        st.markdown(f"""
        <div class='next-action-card'>
            <div class='next-action-label'>{html.escape(ui_label('Country-specific builder'))}</div>
            <div class='next-action-title'>{html.escape(ui_label('Build a resume for one selected job market'))}</div>
            <div class='next-action-copy'>{html.escape(ui_label('Experiment with another target market without changing your main onboarding profile.'))}</div>
        </div>
        """, unsafe_allow_html=True)

        # This country selector is local to this tab only. It must not update onboarding country, target market, dashboard, or Job Assist.
        _builder_default_country = onboarding_country_for_cv()
        target_country = st.selectbox(
            ui_label("Target CV country"),
            country_options,
            index=country_options.index(_builder_default_country) if _builder_default_country in country_options else 0,
            key="country_specific_builder_only_country_v25"
        )
        st.session_state["country_specific_builder_country"] = target_country
        country_cv_language = st.selectbox(
            ui_label("Resume language"),
            language_options,
            index=language_options.index(st.session_state.get("preferred_language", "English")) if st.session_state.get("preferred_language", "English") in language_options else 0,
            key="country_cv_output_language_v51",
        )
        if _main_country_snapshot is not None:
            st.session_state["country"] = _main_country_snapshot
        if _main_migration_snapshot is not None:
            st.session_state["migration_country"] = _main_migration_snapshot
        # Country-specific builder selection is local to this tab only. Do not overwrite onboarding/target-market state.

        user_status_for_template = st.session_state.get("user_status", "Not specified")
        template_options = get_cv_template_options(target_country, user_status_for_template)
        template_names = list(template_options.keys())

        selected_template = st.selectbox(
            ui_label("Choose resume template style"),
            template_names,
            index=0,
            key="country_cv_template_choice_v51",
            help=ui_label("Templates are suggested based on the target country and your career situation.")
        )

        # IMPORTANT:
        # Do NOT render the old static template preview here.
        # That preview uses sample/old cached CV text and was the reason Experience/Education
        # appeared as "—" even though the editable fields were correct.
        # The real preview is rendered below AFTER the resume is generated/edited,
        # using workzo_visual_cv_html_from_structured(preview_structured, ...).
        st.info(ui_label("Choose a template, generate the resume, then review the live editable preview below."))

        cv_template_input = st.text_area(
            ui_label("Source CV / profile text (auto-cleaned from uploaded CV)"),
            value=organize_cv_for_display(get_clean_cv_source_for_tools()),
            height=260,
            key="country_template_cv_v51"
        )

        if st.button(ui_label("Generate Template Resume"), key="btn_country_cv_template_preview_v51"):
            track_button_click("Generate Country CV Template", "Document Tools", {"template": selected_template, "target_country": target_country})
            if not cv_template_input.strip():
                st.warning(ui_label("Please provide your CV."))
            else:
                with st.spinner(ui_label("Building country-specific CV in selected template...")):
                    result = generate_country_cv_template(
                        cv_template_input,
                        target_country,
                        user_status_for_template,
                        selected_template,
                        country_cv_language
                    )
                    if render_error_or_success(result):
                        full_cv = get_section_text(result, ["Full Resume Draft", "Full Country-Specific CV Draft", "Rebuilt CV in Target Country Style", "Full CV"], fallback_to_full=True)
                        st.session_state.generated_country_cv_result = result
                        st.session_state.generated_country_cv_text = strip_markdown_for_resume(full_cv)
                        st.session_state.generated_country_cv_structured = workzo_cv_text_to_editable_sections(st.session_state.generated_country_cv_text, {})
                        st.session_state.generated_country_cv_template = selected_template
                        st.session_state.generated_country_cv_country = target_country

        if st.session_state.get("generated_country_cv_text"):
            st.markdown(f"### {ui_label('Edit Resume Preview Details')}")
            country_preview_template = st.session_state.get("generated_country_cv_template", selected_template)
            country_preview_country = st.session_state.get("generated_country_cv_country", target_country)
            country_structured = st.session_state.get("generated_country_cv_structured")
            if not isinstance(country_structured, dict) or not country_structured:
                country_structured = workzo_cv_text_to_editable_sections(st.session_state.generated_country_cv_text, {})

            editable_country_structured = workzo_editable_cv_editor(
                "country_cv_preview_v141",
                st.session_state.generated_country_cv_text,
                country_structured
            )
            if st.button("Update Preview", key="btn_update_country_cv_preview_v77"):
                st.session_state.generated_country_cv_structured = editable_country_structured
                st.session_state.generated_country_cv_text = workzo_build_cv_text_from_editable(editable_country_structured)
                st.session_state.country_cv_edit_buffer = st.session_state.generated_country_cv_text
                st.success(ui_label("Preview updated with your edits."))
                st.rerun()

            tr_country_col1, tr_country_col2 = st.columns([2, 1])
            with tr_country_col1:
                translate_country_language = st.selectbox(
                    ui_label("Translate this resume to"),
                    language_options,
                    index=language_options.index(st.session_state.get("country_cv_output_language_v51", st.session_state.get("preferred_language", "English"))) if st.session_state.get("country_cv_output_language_v51", st.session_state.get("preferred_language", "English")) in language_options else 0,
                    key="translate_country_cv_language_v77",
                )
            with tr_country_col2:
                st.write("")
                if st.button(ui_label("Translate Resume"), key="btn_translate_country_cv_v77"):
                    with st.spinner(ui_label("Translating resume while keeping facts unchanged...")):
                        translated_country_structured = workzo_translate_structured_resume_live(editable_country_structured, country_preview_country, translate_country_language)
                        translated_country_cv = workzo_build_cv_text_from_editable(translated_country_structured)
                        st.session_state.generated_country_cv_structured = translated_country_structured
                        st.session_state.generated_country_cv_text = translated_country_cv
                        st.session_state.country_cv_edit_buffer = translated_country_cv
                        st.session_state["workzo_live_cv_structured"] = translated_country_structured
                        st.session_state["workzo_live_cv_text"] = translated_country_cv
                        st.session_state["cv_editor_widget"] = translated_country_cv
                        st.success(ui_label("Resume translated. Review the preview below."))
                        st.rerun()

            preview_structured = editable_country_structured
            preview_cv = workzo_build_cv_text_from_editable(preview_structured)
            st.session_state["workzo_live_cv_structured"] = preview_structured
            st.session_state["workzo_live_cv_text"] = preview_cv
            st.session_state["cv_editor_widget"] = preview_cv
            st.session_state["clean_structured_cv_text"] = preview_cv
            st.session_state["cv_text"] = preview_cv
            st.session_state.generated_country_cv_structured = preview_structured
            st.session_state.generated_country_cv_text = preview_cv
            st.markdown(f"### {ui_label('Live Visual Resume Preview — uses the editable fields above')}")
            st.html(workzo_visual_cv_html_from_structured(
                preview_structured,
                country_preview_template,
                country_preview_country
            ))

            result = st.session_state.get("generated_country_cv_result", "")
            with st.expander(ui_label("Template / Country Fit Notes"), expanded=False):
                notes = get_section_text(result, ["Country Fit Notes", "Template and Country Fit Notes", "Country CV Format Notes"])
                st.write(notes)

            with st.expander(ui_label("What WorkZo changed"), expanded=False):
                changes = get_section_text(result, ["WorkZo Changes", "What Was Changed"])
                st.write(changes)

            with st.expander(ui_label("Missing details to confirm"), expanded=False):
                missing = get_section_text(result, ["Missing Details to Confirm"])
                st.write(missing)

            render_country_specific_honesty_audit(
                st.session_state.get('generated_country_cv_text', ''),
                st.session_state.get('generated_country_cv_country', target_country),
                st.session_state.get('structured_cv_json', {}),
                expanded=False
            )

            download_country = st.session_state.get('generated_country_cv_country', target_country)
            download_template = st.session_state.get('generated_country_cv_template', selected_template)
            download_structured = st.session_state.get("generated_country_cv_structured") or preview_structured
            clean_download_cv = strip_markdown_for_resume(workzo_build_cv_text_from_editable(download_structured))
            safe_file_base = f"workzo_{download_country.lower().replace(' ', '_')}_{download_template.lower().replace(' ', '_')}_cv"

            pdf_data = make_styled_pdf_from_structured_preview(
                f"WorkZo CV - {download_country} - {download_template}",
                download_structured,
                download_template,
                download_country
            )
            docx_data = make_docx_from_cv_text(
                f"WorkZo CV - {download_country} - {download_template}",
                clean_download_cv,
                download_template,
                download_country
            )
            rendercv_yaml = rendercv_yaml_from_cv_text(clean_download_cv, download_template, download_country)
            rendercv_pdf = try_rendercv_pdf_from_yaml(rendercv_yaml)

            dl_col1, dl_col2, dl_col3, dl_col4 = st.columns(4)
            with dl_col1:
                st.download_button(
                    label=ui_label("Download PDF"),
                    data=pdf_data,
                    file_name=f"{safe_file_base}.pdf",
                    mime="application/pdf",
                    key="download_country_cv_pdf_v77"
                )
            with dl_col2:
                st.download_button(
                    label=ui_label("Download TXT"),
                    data=clean_download_cv.encode("utf-8"),
                    file_name=f"{safe_file_base}.txt",
                    mime="text/plain",
                    key="download_country_cv_txt_v77"
                )
            with dl_col3:
                if Document is not None:
                    st.download_button(
                        label=ui_label("Download DOCX"),
                        data=docx_data,
                        file_name=f"{safe_file_base}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key="download_country_cv_docx_v77"
                    )
            with dl_col4:
                if rendercv_pdf:
                    st.download_button(label=ui_label("Download RenderCV PDF"), data=rendercv_pdf, file_name=f"{safe_file_base}_rendercv.pdf", mime="application/pdf", key="download_country_cv_rendercv_pdf_v1")

    # -----------------------------------------------------
    # 3. Cover Letter Generator
    # -----------------------------------------------------
    with cover_tab:
        company_name = st.text_input(ui_label("Company Name"), value=st.session_state.get("target_company", ""), key="doc_tools_company_name")
        company_website = st.text_input(ui_label("Company website / careers page (optional)"), value=st.session_state.get("target_company_website", ""), key="doc_tools_company_website", help=ui_label("Optional. Helps WorkZo make the letter more company-specific without guessing."))
        role_name = st.text_input(txt("target_role"), value=st.session_state.get("target_job_title", ""), key="doc_tools_role_name")
        cover_letter_language = st.selectbox(
            ui_label("Cover letter language"),
            language_options,
            index=language_options.index(st.session_state.get("preferred_language", "English")) if st.session_state.get("preferred_language", "English") in language_options else 0,
            key="cover_letter_language_v60"
        )
        job_desc_letter = st.text_area(ui_label("Paste the job description"), height=220, key="doc_tools_job_desc")

        if st.button(txt("generate"), key="btn_cover_letter_v49"):
            track_button_click("Generate Cover Letter", "Document Tools")
            job_desc_letter_combined = (job_desc_letter or "").strip()
            if not role_name.strip() or not job_desc_letter_combined.strip():
                st.warning(ui_label("Please enter a target role and paste the job description."))
            elif not st.session_state.cv_text.strip():
                st.warning(ui_label("Please upload or create a CV first."))
            else:
                with st.spinner(ui_label("Generating cover letter...")):
                    company_context = _wz26_company_context_for_docs(company_name, company_website)
                    st.session_state["target_company"] = company_name
                    st.session_state["target_company_website"] = company_website
                    prompt = f"""
{txt('country_label')}: {st.session_state.country}
Target role: {role_name}
Company: {company_name if company_name.strip() else "Not specified"}
Company website: {company_website if company_website.strip() else "Not specified"}
Company context from website/user input:
{company_context or "Not available. Do not invent company facts."}

Candidate CV:
{st.session_state.cv_text}

Job description:
{job_desc_letter_combined}

Write a strong, personalized professional cover letter in {cover_letter_language}.

Quality requirements:
- Use the candidate's actual CV details.
- Connect 3 to 5 specific candidate strengths to the job description.
- Avoid generic sentences and repeated buzzwords.
- Use company context only when available; if not available, stay based on the JD and CV.
- Be honest: do not invent tools, achievements, metrics, language levels, or company knowledge.
- Sound natural, confident, concise, and human.
- Keep it suitable for the selected country and role level.
- Write the final cover letter and email version fully in {cover_letter_language}.

Return in this exact structure:

1. Full Cover Letter
2. Short Email Version
3. 3 Customization Tips

Important:
- Do not leave any section empty.
- Write complete content for each section.
"""
                    result = run_ai_prompt(prompt, force_language=cover_letter_language)
                    if render_error_or_success(result):
                        if not result.strip():
                            st.error(ui_label("Cover letter generation returned an empty response. Please try again."))
                        else:
                            st.session_state.latest_cover_letter = result
                            render_section_cards(result, default_expand=True)

                            sections = numbered_sections_to_markdown(result)
                            full_letter = sections.get("Full Cover Letter", "").strip()
                            short_email = sections.get("Short Email Version", "").strip()

                            if full_letter:
                                st.markdown(f"### {ui_label('Full Cover Letter')}")
                                st.text_area(ui_label("Generated Cover Letter"), value=full_letter, height=320)
                                st.download_button(
                                    ui_label("Download Cover Letter as TXT"),
                                    data=full_letter,
                                    file_name="cover_letter.txt",
                                    mime="text/plain",
                                    key="download_cover_letter_txt_v49"
                                )
                            if short_email:
                                st.markdown(f"### {ui_label('Short Email Version')}")
                                st.text_area(ui_label("Generated Short Email"), value=short_email, height=180)



def render_country_fit_cards(country_text: str):
    rows = []
    for raw in str(country_text or "").splitlines():
        item = raw.strip().lstrip("-• ").strip()
        if item:
            rows.append(item)
    if not rows:
        st.info(txt("not_analyzed"))
        return

    st.caption(txt("country_fit_note"))
    for item in rows[:3]:
        if " - " in item:
            country, reason = item.split(" - ", 1)
        elif ":" in item:
            country, reason = item.split(":", 1)
        else:
            country, reason = item, ""
        reason = reason.strip()
        if len(reason) > 120:
            reason = reason[:120].rsplit(" ", 1)[0] + "..."
        card_html = f"""
<div class="card">
  <div class="section-title">{html.escape(country.strip())}</div>
  <div class="small-muted">{html.escape(reason or txt('view_details'))}</div>
</div>
"""
        st.markdown(card_html, unsafe_allow_html=True)

    if len(rows) > 3:
        with st.expander(txt("country_fit_details"), expanded=False):
            for item in rows[3:]:
                st.markdown(f"- {item}")

# =========================================================
# DASHBOARD
# =========================================================
# DASHBOARD
# =========================================================

# WorkZo v30 note:
# Cover Letter, CV, Job Match and Interview pages share these session keys:
# target_company, target_role / target_job_title, target_company_website,
# current_job_description / last_understand_job_description.
# The existing widgets in this file already read these values. Job Match and
# Interview Practice now keep them updated so users do not re-enter details.
