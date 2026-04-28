# WorkZo AI modular split v138

Run with:

```bash
streamlit run app.py
```

Keep `app.py` and the `workzo_modules/` folder together.

This is a safe transitional split: the modules are executed in order into one shared namespace, so your current features keep working while the code is physically separated.

Module map:

- `00_bootstrap_config.py` — imports, config, secrets, country rules, analytics, CSS, translations
- `01_ui_language_geo.py` — language helpers, countries/cities, local guidance
- `02_job_sources.py` — job APIs, search links, job relevance, curated job cards
- `03_resume_extraction_schema.py` — CV extraction, structured JSON, anti-drift schema
- `04_ai_core_analysis.py` — OpenAI wrapper, job analysis, scoring, honesty audit
- `05_pdf_docx_generators.py` — PDF/DOCX/export helpers
- `06_header_onboarding_workobot.py` — header, sample data, landing, onboarding, Work-O-Bot helpers
- `07_document_tools.py` — Improve CV, resume builder, cover letter tools
- `08_dashboard.py` — dashboard and navigation
- `09_interview_assistant.py` — JD-specific interview assistant
- `10_stability_patches_router.py` — latest patches and final router

Next real refactor: move one area at a time into normal importable modules, starting with resume schema/PDF generator.
