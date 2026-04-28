"""WorkZo AI - modular loader v138 fixed."""
from pathlib import Path

MODULE_ORDER = [
    "00_bootstrap_config.py",
    "01_ui_language_geo.py",
    "02_job_sources.py",
    "04_ai_core_analysis.py",
    "03_resume_extraction_schema.py",
    "05_pdf_docx_generators.py",
    "07_document_tools.py",
    "08_dashboard.py",
    "09_interview_assistant.py",
    "06_header_onboarding_workobot.py",
    "11_recovered_helpers_patch.py",
    "10_stability_patches_router.py",
]

BASE_PATH = Path(__file__).parent
MODULE_DIR = BASE_PATH / "workzo_modules"

for module_name in MODULE_ORDER:
    module_path = MODULE_DIR / module_name
    code = module_path.read_text(encoding="utf-8")
    exec(compile(code, str(module_path), "exec"), globals(), globals())
