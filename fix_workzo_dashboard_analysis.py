from pathlib import Path

PROJECT = Path.cwd()
MODULE = PROJECT / "workzo_modules" / "08_dashboard.py"

PATCH = r'''

# =========================================================
# WorkZo split-module fallback: dashboard analysis
# Added by fix_workzo_dashboard_analysis.py
# Purpose: keep dashboard working when ensure_dashboard_analysis was
# left behind during modular split.
# =========================================================
def ensure_dashboard_analysis():
    """Ensure dashboard score/analysis exists without breaking existing features.

    Uses the stronger existing analysis function when available. Falls back to a
    deterministic lightweight score so the dashboard can render instead of
    crashing. This function does not overwrite a valid existing analysis.
    """
    import re
    import streamlit as st

    existing = st.session_state.get("dashboard_analysis") or st.session_state.get("resume_analysis")
    if isinstance(existing, dict) and existing:
        st.session_state["dashboard_analysis"] = existing
        return existing

    cv_text = str(
        st.session_state.get("cv_text")
        or st.session_state.get("clean_structured_cv_text")
        or st.session_state.get("approved_cv_text")
        or ""
    )

    # Prefer the app's real analysis functions if they exist in the shared exec namespace.
    try:
        fn = globals().get("analyze_resume_dashboard_stable")
        if callable(fn) and cv_text.strip():
            result = fn(cv_text)
            if isinstance(result, dict) and result:
                st.session_state["dashboard_analysis"] = result
                return result
    except Exception:
        pass

    try:
        fn = globals().get("build_rule_based_dashboard_cache")
        if callable(fn) and cv_text.strip():
            result = fn(cv_text)
            if isinstance(result, dict) and result:
                st.session_state["dashboard_analysis"] = result
                return result
    except Exception:
        pass

    # Deterministic fallback. Conservative scores: avoids fake 90+ numbers.
    text_lower = cv_text.lower()
    sections = ["experience", "education", "skills", "summary", "projects"]
    section_hits = sum(1 for s in sections if s in text_lower)
    has_email = bool(re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", cv_text))
    has_phone = bool(re.search(r"(?:\+\d{1,3}[\s-]?)?(?:\(?\d+\)?[\s-]?){6,}", cv_text))
    quantified = len(re.findall(r"\b\d+\s*%|\b\d+\+|\b\d+\s*(years?|yrs?|months?)\b", cv_text, flags=re.I))
    bullet_count = len(re.findall(r"(^|\n)\s*[-•*]\s+", cv_text))
    keyword_hits = sum(1 for k in ["python", "sql", "tableau", "power bi", "support", "analysis", "dashboard", "cloud", "api", "itil", "itsm"] if k in text_lower)

    resume_score = 45 + section_hits * 5 + min(quantified, 5) * 3 + min(bullet_count, 10) + min(keyword_hits, 8)
    ats_score = 50 + section_hits * 6 + (8 if has_email else 0) + (6 if has_phone else 0) + min(keyword_hits * 2, 16)
    resume_score = max(35, min(88, int(resume_score)))
    ats_score = max(35, min(88, int(ats_score)))

    result = {
        "resume_score": resume_score,
        "ats_score": ats_score,
        "detected_role": st.session_state.get("target_role", "Not analyzed yet"),
        "professional_summary": "Upload or review your structured CV to improve this analysis." if not cv_text.strip() else "Resume analysis generated from available CV text.",
        "strengths": ["Core CV sections detected"] if section_hits else [],
        "improvements": ["Review extracted CV details", "Tailor CV to a specific job description"],
        "suggested_roles": [],
    }
    st.session_state["dashboard_analysis"] = result
    st.session_state["resume_analysis"] = result
    return result
'''


def main():
    if not MODULE.exists():
        raise SystemExit(f"Could not find {MODULE}. Run this script from your project folder.")
    text = MODULE.read_text(encoding="utf-8")
    if "def ensure_dashboard_analysis(" in text:
        print("ensure_dashboard_analysis already exists. No change needed.")
        return
    # Insert near the top after imports/comments. Safe because function imports st internally.
    MODULE.write_text(PATCH + "\n" + text, encoding="utf-8")
    print(f"Patched {MODULE}")
    print("Now run: streamlit run app.py")

if __name__ == "__main__":
    main()
