# =========================================================
# WorkZo Global Header - Premium SaaS Header
# Stable standalone component. Keep independent from onboarding.
# =========================================================
import os
import base64
from pathlib import Path

try:
    import streamlit as st
except Exception:  # Allows syntax check outside Streamlit runtime
    st = None


def _wz_header_logo_data_uri() -> str:
    """Load WorkZo logo from common app locations without depending on other modules."""
    candidates = []
    base = Path.cwd()
    here = Path(__file__).resolve().parent if "__file__" in globals() else base
    candidates.extend([
        base / "workzo_icon.png",
        base / "logo.png",
        base / "assets" / "workzo_icon.png",
        here / "workzo_icon.png",
        here / "logo.png",
        here.parent / "workzo_icon.png",
        here.parent / "logo.png",
    ])
    for path in candidates:
        try:
            if path.exists() and path.is_file():
                ext = path.suffix.lower().replace(".", "") or "png"
                mime = "jpeg" if ext in {"jpg", "jpeg"} else ext
                return f"data:image/{mime};base64," + base64.b64encode(path.read_bytes()).decode("utf-8")
        except Exception:
            continue
    return ""


def _wz_header_progress_state() -> tuple[int, str, bool, bool, bool]:
    if st is None:
        return 0, "CV", False, False, False
    try:
        cv_done = bool(str(st.session_state.get("cv_text", "") or st.session_state.get("clean_structured_cv_text", "")).strip())
        job_done = bool(str(
            st.session_state.get("selected_job_description", "")
            or st.session_state.get("last_understand_job_description", "")
            or st.session_state.get("improve_cv_for_job_desc", "")
            or st.session_state.get("interview_jd_text_v117", "")
        ).strip())
        interview_done = bool(st.session_state.get("interview_completed") or st.session_state.get("real_interview_completed") or st.session_state.get("latest_interview_feedback"))
        done = sum([cv_done, job_done, interview_done])
        pct = int(round(done / 3 * 100))
        stage = "CV"
        if cv_done and not job_done:
            stage = "Jobs"
        elif cv_done and job_done and not interview_done:
            stage = "Interview"
        elif interview_done:
            stage = "Ready"
        return pct, stage, cv_done, job_done, interview_done
    except Exception:
        return 0, "CV", False, False, False


def render_global_header() -> None:
    if st is None:
        return
    logo_src = _wz_header_logo_data_uri()
    logo_html = f'<img src="{logo_src}" class="wz-global-logo" alt="WorkZo AI logo">' if logo_src else '<div class="wz-global-logo wz-global-logo-fallback">WZ</div>'
    progress_pct, stage, cv_done, job_done, interview_done = _wz_header_progress_state()
    cv_mark = "✓" if cv_done else "1"
    job_mark = "✓" if job_done else "2"
    int_mark = "✓" if interview_done else "3"

    st.markdown(f"""
    <style id="workzo-global-premium-header-css">
    html, body {{ margin-top:0 !important; padding-top:0 !important; overflow-x:hidden !important; }}
    [data-testid="stAppViewContainer"] {{ padding-top:0 !important; }}
    [data-testid="stMain"], [data-testid="stMainBlockContainer"], .block-container {{ padding-top:5.8rem !important; margin-top:0 !important; }}
    .wz-global-header {{ position:fixed; top:.65rem; left:50%; transform:translateX(-50%); width:min(1280px, calc(100vw - 2rem)); z-index:999999; display:flex; align-items:center; justify-content:space-between; gap:1rem; padding:.82rem 1rem; border-radius:22px; border:1px solid rgba(34,211,238,.30); background:linear-gradient(135deg, rgba(8,47,73,.96), rgba(15,23,42,.97)); box-shadow:0 18px 45px rgba(2,6,23,.38); backdrop-filter:blur(14px); }}
    .wz-global-left {{ display:flex; align-items:center; gap:.85rem; min-width:0; }}
    .wz-global-logo {{ width:56px; height:56px; min-width:56px; border-radius:15px; object-fit:cover; display:block; box-shadow:0 10px 24px rgba(14,165,233,.25); }}
    .wz-global-logo-fallback {{ display:flex; align-items:center; justify-content:center; background:linear-gradient(135deg,#06b6d4,#2563eb); color:white; font-weight:950; }}
    .wz-global-title {{ color:white; font-size:1.55rem; font-weight:950; letter-spacing:-.04em; line-height:1; white-space:nowrap; }}
    .wz-global-title span {{ color:#22d3ee; }}
    .wz-global-subtitle {{ color:#cbd5e1; font-size:.85rem; font-weight:650; margin-top:.25rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:420px; }}
    .wz-global-right {{ display:flex; align-items:center; gap:.75rem; }}
    .wz-global-back {{ color:#cbd5e1 !important; text-decoration:none !important; border:1px solid rgba(148,163,184,.28); border-radius:999px; padding:.48rem .7rem; font-weight:800; font-size:.82rem; background:rgba(15,23,42,.45); }}
    .wz-global-progress-wrap {{ min-width:230px; }}
    .wz-global-progress-top {{ display:flex; justify-content:space-between; align-items:center; color:#cbd5e1; font-size:.74rem; font-weight:800; margin-bottom:.32rem; }}
    .wz-global-progress-bar {{ height:7px; border-radius:999px; background:rgba(148,163,184,.18); overflow:hidden; }}
    .wz-global-progress-fill {{ height:100%; width:{progress_pct}%; border-radius:999px; background:linear-gradient(90deg,#22d3ee,#22c55e); }}
    .wz-global-steps {{ display:flex; gap:.35rem; margin-top:.35rem; }}
    .wz-step {{ color:#cbd5e1; border:1px solid rgba(148,163,184,.22); background:rgba(15,23,42,.42); border-radius:999px; padding:.18rem .45rem; font-size:.66rem; font-weight:850; white-space:nowrap; }}
    .wz-step.done {{ color:#67e8f9; border-color:rgba(34,211,238,.45); background:rgba(8,145,178,.18); }}
    .wz-global-beta {{ color:#67e8f9; border:1px solid rgba(103,232,249,.42); background:rgba(8,145,178,.16); border-radius:999px; padding:.43rem .8rem; font-size:.72rem; font-weight:950; letter-spacing:.04em; white-space:nowrap; }}
    @media (max-width:760px) {{
        [data-testid="stMain"], [data-testid="stMainBlockContainer"], .block-container {{ padding-top:5.1rem !important; padding-left:.85rem !important; padding-right:.85rem !important; }}
        .wz-global-header {{ top:.45rem; width:calc(100vw - 1rem); padding:.65rem .75rem; border-radius:18px; }}
        .wz-global-logo {{ width:44px; height:44px; min-width:44px; border-radius:13px; }}
        .wz-global-title {{ font-size:1.15rem; }}
        .wz-global-subtitle {{ font-size:.72rem; max-width:160px; }}
        .wz-global-progress-wrap {{ display:none; }}
        .wz-global-back {{ display:none; }}
        .wz-global-beta {{ padding:.34rem .58rem; font-size:.64rem; }}
        div[data-testid="column"] {{ width:100% !important; flex:1 1 100% !important; }}
        button {{ min-height:44px !important; }}
    }}
    </style>
    <div class="wz-global-header">
        <div class="wz-global-left">{logo_html}<div><div class="wz-global-title">WorkZo <span>AI</span></div><div class="wz-global-subtitle">Your 360-degree AI Career Assistant</div></div></div>
        <div class="wz-global-right">
            <a class="wz-global-back" href="javascript:history.back()">← Back</a>
            <div class="wz-global-progress-wrap"><div class="wz-global-progress-top"><span>{stage}</span><span>{progress_pct}%</span></div><div class="wz-global-progress-bar"><div class="wz-global-progress-fill"></div></div><div class="wz-global-steps"><span class="wz-step {'done' if cv_done else ''}">{cv_mark} CV</span><span class="wz-step {'done' if job_done else ''}">{job_mark} Jobs</span><span class="wz-step {'done' if interview_done else ''}">{int_mark} Interview</span></div></div>
            <div class="wz-global-beta">BETA</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
