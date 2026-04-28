"""
WorkZo split-module repair script
Run this from your project root, for example:
    cd C:\\Users\\User\\Desktop\\ai-germany-assistant
    python fix_workzo_split_modules.py

What it fixes safely:
- Adds missing UI helpers used after splitting modules: image_to_data_uri, maybe_scroll_to_top, request_scroll_to_top,
  update_url_page, read_url_page, sync_navigation_state, queue_navigation, consume_pending_navigation, go_home.
- Adds missing imports to 06_header_onboarding_workobot.py.
- Adds missing imports to 05_pdf_docx_generators.py.
- Does not delete or replace your existing feature logic.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path.cwd()
MODULES_DIR = ROOT / "workzo_modules"

HEADER_FILE = MODULES_DIR / "06_header_onboarding_workobot.py"
PDF_FILE = MODULES_DIR / "05_pdf_docx_generators.py"

UI_HELPER_BLOCK = r'''
# =========================================================
# WorkZo split-module shared UI helpers
# Added by fix_workzo_split_modules.py
# =========================================================
import os
import base64
import streamlit as st
import streamlit.components.v1 as components

try:
    BASE_DIR
except NameError:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

try:
    ICON_PATH
except NameError:
    ICON_PATH = os.path.join(BASE_DIR, "workzo_icon.png")

try:
    LOGO_PATH
except NameError:
    LOGO_PATH = os.path.join(BASE_DIR, "logo.png")


def image_to_data_uri(image_path: str):
    """Convert a local image into a base64 data URI for HTML rendering."""
    if not image_path:
        return None
    try:
        path = str(image_path)
        if not os.path.exists(path):
            return None
        ext = os.path.splitext(path)[1].lower().replace(".", "") or "png"
        mime = "jpeg" if ext in {"jpg", "jpeg"} else ext
        with open(path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
        return f"data:image/{mime};base64,{encoded}"
    except Exception:
        return None


def request_scroll_to_top() -> None:
    """Mark the next run to scroll to top."""
    try:
        st.session_state["_workzo_scroll_to_top"] = True
    except Exception:
        pass


def maybe_scroll_to_top() -> None:
    """Scroll Streamlit page to the top when navigation changes."""
    try:
        should_scroll = st.session_state.pop("_workzo_scroll_to_top", True)
    except Exception:
        should_scroll = True
    if not should_scroll:
        return
    try:
        components.html(
            """
            <script>
            const forceTop = () => {
                try {
                    window.parent.scrollTo({top: 0, left: 0, behavior: 'auto'});
                    const doc = window.parent.document;
                    const targets = [
                        doc.documentElement,
                        doc.body,
                        doc.querySelector('[data-testid="stAppViewContainer"]'),
                        doc.querySelector('[data-testid="stMain"]'),
                        doc.querySelector('[data-testid="stMainBlockContainer"]')
                    ].filter(Boolean);
                    for (const t of targets) { try { t.scrollTop = 0; } catch(e) {} }
                } catch(e) {}
            };
            forceTop();
            setTimeout(forceTop, 80);
            setTimeout(forceTop, 250);
            </script>
            """,
            height=0,
            width=0,
        )
    except Exception:
        pass


def update_url_page(page_key: str) -> None:
    try:
        st.query_params["page"] = page_key
    except Exception:
        pass


def read_url_page(default: str = "dashboard") -> str:
    try:
        value = st.query_params.get("page", default)
        if isinstance(value, list):
            value = value[0] if value else default
        return value or default
    except Exception:
        return default


def sync_navigation_state(page_key: str) -> None:
    try:
        st.session_state.page = page_key
        st.session_state.nav_page = page_key
        st.session_state.nav_change_nonce = st.session_state.get("nav_change_nonce", 0) + 1
        update_url_page(page_key)
        request_scroll_to_top()
    except Exception:
        pass


def queue_navigation(page_key: str) -> None:
    try:
        st.session_state._workzo_pending_nav = page_key
        request_scroll_to_top()
    except Exception:
        pass


def consume_pending_navigation() -> None:
    try:
        page_key = st.session_state.pop("_workzo_pending_nav", None)
        if page_key:
            sync_navigation_state(page_key)
    except Exception:
        pass


def go_home() -> None:
    """Home should return to dashboard/workspace, not restart onboarding."""
    try:
        st.session_state.onboarding_complete = True
        queue_navigation("dashboard")
    except Exception:
        pass
# =========================================================
'''

PDF_IMPORT_BLOCK = '''
# =========================================================
# WorkZo split-module missing imports
# Added by fix_workzo_split_modules.py
# =========================================================
import os
import re
import html
import json
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
'''


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def backup(path: Path) -> Path:
    bak = path.with_suffix(path.suffix + ".bak")
    if not bak.exists():
        bak.write_text(read_text(path), encoding="utf-8")
    return bak


def ensure_top_block(path: Path, marker: str, block: str) -> bool:
    if not path.exists():
        print(f"[SKIP] Missing file: {path}")
        return False
    text = read_text(path)
    if marker in text:
        print(f"[OK] Already patched: {path.name}")
        return False
    backup(path)
    # Keep shebang/encoding comments at top if present.
    lines = text.splitlines(True)
    insert_at = 0
    while insert_at < len(lines) and (lines[insert_at].startswith("#!") or "coding" in lines[insert_at][:80]):
        insert_at += 1
    new_text = "".join(lines[:insert_at]) + block + "\n" + "".join(lines[insert_at:])
    write_text(path, new_text)
    print(f"[PATCHED] {path.name}")
    return True


def fix_header_module() -> None:
    ensure_top_block(HEADER_FILE, "WorkZo split-module shared UI helpers", UI_HELPER_BLOCK)


def fix_pdf_module() -> None:
    ensure_top_block(PDF_FILE, "WorkZo split-module missing imports", PDF_IMPORT_BLOCK)


def quick_compile_check(path: Path) -> None:
    if not path.exists():
        return
    try:
        compile(read_text(path), str(path), "exec")
        print(f"[COMPILE OK] {path.name}")
    except Exception as e:
        print(f"[COMPILE WARNING] {path.name}: {type(e).__name__}: {e}")


def main() -> None:
    print("WorkZo split-module repair")
    print(f"Project root: {ROOT}")
    if not MODULES_DIR.exists():
        print(f"[ERROR] Could not find workzo_modules folder at: {MODULES_DIR}")
        print("Move this script into your ai-germany-assistant project folder and run it again.")
        return
    fix_header_module()
    fix_pdf_module()
    quick_compile_check(HEADER_FILE)
    quick_compile_check(PDF_FILE)
    print("\nDone. Now run:")
    print("    streamlit run app.py")
    print("\nBackups were created as .bak files before patching.")


if __name__ == "__main__":
    main()
