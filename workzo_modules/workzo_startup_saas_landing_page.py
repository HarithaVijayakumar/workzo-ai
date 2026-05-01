
# WorkZo AI - Startup SaaS Landing Page
# Drop-in Streamlit landing page function.
# Use this to replace your current landing page / hero section.
#
# Main headline:
# From CV to Real Interview — in one AI workspace.

import html
import streamlit as st


def _wz_landing_go(target: str):
    """Safe navigation helper for WorkZo modular app."""
    try:
        fn = globals().get("queue_navigation")
        if callable(fn):
            fn(target)
        else:
            st.session_state["nav_page"] = target
            st.session_state["page"] = target
        st.rerun()
    except Exception:
        st.session_state["nav_page"] = target
        st.session_state["page"] = target


def _wz_landing_logo_html():
    """Uses existing WorkZo logo helpers if available; otherwise uses a clean fallback."""
    logo_src = None
    try:
        image_to_data_uri = globals().get("image_to_data_uri")
        icon_path = globals().get("ICON_PATH")
        logo_path = globals().get("LOGO_PATH")
        if callable(image_to_data_uri):
            logo_src = image_to_data_uri(icon_path) or image_to_data_uri(logo_path)
    except Exception:
        logo_src = None

    if logo_src:
        return f"<img src='{logo_src}' class='wz-lp-logo-img' alt='WorkZo AI logo'>"

    return "<div class='wz-lp-logo-fallback'>WZ</div>"


def show_landing_page():
    """Premium startup-style landing page for WorkZo AI."""
    logo_html = _wz_landing_logo_html()

    st.markdown(
        f"""
        <style>
        .wz-lp-wrap {{
            max-width: 1180px;
            margin: 0 auto;
            padding: 14px 10px 48px;
        }}

        .wz-lp-topbar {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 18px;
            padding: 18px 20px;
            margin-bottom: 28px;
            border: 1px solid rgba(20,184,166,.24);
            border-radius: 24px;
            background: linear-gradient(135deg, rgba(8,47,73,.82), rgba(15,23,42,.92));
            box-shadow: 0 18px 50px rgba(2,6,23,.32);
        }}

        .wz-lp-brand {{
            display: flex;
            align-items: center;
            gap: 14px;
        }}

        .wz-lp-logo-img {{
            width: 58px;
            height: 58px;
            border-radius: 16px;
            object-fit: contain;
            box-shadow: 0 10px 25px rgba(14,165,233,.22);
        }}

        .wz-lp-logo-fallback {{
            width: 58px;
            height: 58px;
            border-radius: 16px;
            display:flex;
            align-items:center;
            justify-content:center;
            font-weight:900;
            color:#f8fafc;
            background: linear-gradient(135deg, #06b6d4, #2563eb);
            box-shadow: 0 10px 25px rgba(14,165,233,.22);
        }}

        .wz-lp-brand-title {{
            font-size: 1.55rem;
            font-weight: 950;
            color: #f8fafc;
            line-height: 1.05;
        }}

        .wz-lp-brand-title span {{
            color: #22d3ee;
        }}

        .wz-lp-brand-sub {{
            color:#bfdbfe;
            font-size:.9rem;
            margin-top:4px;
            font-weight:650;
        }}

        .wz-lp-beta {{
            border: 1px solid rgba(34,211,238,.38);
            background: rgba(8,145,178,.28);
            color:#67e8f9;
            padding: 9px 16px;
            border-radius: 999px;
            font-size: .78rem;
            font-weight: 900;
            letter-spacing: .08em;
        }}

        .wz-lp-hero {{
            position: relative;
            overflow: hidden;
            border-radius: 34px;
            padding: 54px 54px 42px;
            background:
                radial-gradient(circle at 18% 15%, rgba(20,184,166,.24), transparent 34%),
                radial-gradient(circle at 86% 18%, rgba(37,99,235,.28), transparent 36%),
                linear-gradient(135deg, rgba(8,47,73,.84), rgba(15,23,42,.96));
            border: 1px solid rgba(20,184,166,.26);
            box-shadow: 0 28px 70px rgba(2,6,23,.38);
        }}

        .wz-lp-kicker {{
            color:#5eead4;
            font-weight: 950;
            letter-spacing:.16em;
            text-transform: uppercase;
            font-size:.78rem;
            margin-bottom: 16px;
        }}

        .wz-lp-title {{
            max-width: 900px;
            color:#f8fafc;
            font-size: clamp(2.35rem, 5vw, 4.6rem);
            line-height: .98;
            font-weight: 950;
            letter-spacing: -.055em;
            margin-bottom: 22px;
        }}

        .wz-lp-sub {{
            max-width: 760px;
            color:#dbeafe;
            font-size: clamp(1rem, 2vw, 1.23rem);
            line-height: 1.65;
            font-weight: 560;
            margin-bottom: 14px;
        }}

        .wz-lp-micro {{
            color:#94a3b8;
            font-size: .98rem;
            line-height:1.5;
            margin-bottom: 30px;
        }}

        .wz-lp-cta-row {{
            display:flex;
            flex-wrap:wrap;
            align-items:center;
            gap: 14px;
            margin-bottom: 34px;
        }}

        .wz-lp-trust {{
            color:#93c5fd;
            font-size: .9rem;
            font-weight: 700;
        }}

        .wz-lp-flow {{
            display:grid;
            grid-template-columns: repeat(4, minmax(0,1fr));
            gap: 14px;
            margin-top: 28px;
        }}

        .wz-lp-flow-card {{
            border:1px solid rgba(148,163,184,.17);
            background: rgba(15,23,42,.48);
            border-radius: 20px;
            padding: 18px;
            min-height: 104px;
        }}

        .wz-lp-flow-num {{
            color:#5eead4;
            font-weight:950;
            font-size:.86rem;
            margin-bottom: 12px;
        }}

        .wz-lp-flow-title {{
            color:#f8fafc;
            font-size:1.02rem;
            font-weight: 900;
        }}

        .wz-lp-section {{
            margin-top: 26px;
            display:grid;
            grid-template-columns: 1.05fr .95fr;
            gap: 18px;
            align-items: stretch;
        }}

        .wz-lp-panel {{
            border:1px solid rgba(148,163,184,.16);
            background: rgba(15,23,42,.50);
            border-radius: 26px;
            padding: 24px;
        }}

        .wz-lp-panel-label {{
            color:#38bdf8;
            font-weight: 950;
            letter-spacing:.12em;
            text-transform: uppercase;
            font-size:.76rem;
            margin-bottom: 10px;
        }}

        .wz-lp-panel-title {{
            color:#f8fafc;
            font-size: 1.55rem;
            font-weight: 950;
            line-height: 1.18;
            margin-bottom: 10px;
        }}

        .wz-lp-panel-copy {{
            color:#cbd5e1;
            font-size: 1rem;
            line-height: 1.6;
        }}

        .wz-lp-mini-grid {{
            display:grid;
            grid-template-columns: repeat(3, minmax(0,1fr));
            gap: 14px;
            margin-top: 18px;
        }}

        .wz-lp-mini {{
            border:1px solid rgba(148,163,184,.14);
            background: rgba(2,6,23,.26);
            border-radius: 18px;
            padding: 16px;
        }}

        .wz-lp-mini-title {{
            color:#f8fafc;
            font-weight: 900;
            margin-bottom: 6px;
        }}

        .wz-lp-mini-copy {{
            color:#94a3b8;
            font-size:.92rem;
            line-height:1.45;
        }}

        .wz-lp-proof {{
            display:flex;
            align-items:center;
            gap:12px;
            border:1px solid rgba(20,184,166,.18);
            background: rgba(20,184,166,.08);
            border-radius: 22px;
            padding: 18px;
            color:#ccfbf1;
            line-height:1.5;
            font-weight: 650;
        }}

        .wz-lp-proof-dot {{
            width: 10px;
            height: 10px;
            min-width:10px;
            border-radius: 999px;
            background:#34d399;
            box-shadow: 0 0 0 6px rgba(52,211,153,.12);
        }}

        @media (max-width: 900px) {{
            .wz-lp-hero {{
                padding: 36px 24px 28px;
                border-radius: 28px;
            }}
            .wz-lp-flow {{
                grid-template-columns: repeat(2, minmax(0,1fr));
            }}
            .wz-lp-section {{
                grid-template-columns: 1fr;
            }}
            .wz-lp-mini-grid {{
                grid-template-columns: 1fr;
            }}
        }}

        @media (max-width: 540px) {{
            .wz-lp-topbar {{
                padding: 14px;
                border-radius: 20px;
            }}
            .wz-lp-beta {{
                display:none;
            }}
            .wz-lp-flow {{
                grid-template-columns: 1fr;
            }}
        }}
        </style>

        <div class="wz-lp-wrap">
            <div class="wz-lp-topbar">
                <div class="wz-lp-brand">
                    {logo_html}
                    <div>
                        <div class="wz-lp-brand-title">WorkZo <span>AI</span></div>
                        <div class="wz-lp-brand-sub">Your 360-degree AI Career Assistant</div>
                    </div>
                </div>
                <div class="wz-lp-beta">BETA</div>
            </div>

            <div class="wz-lp-hero">
                <div class="wz-lp-kicker">AI career workspace</div>
                <div class="wz-lp-title">From CV to Real Interview — in one AI workspace.</div>
                <div class="wz-lp-sub">
                    Understand your CV, fix what’s holding you back, match the right jobs,
                    and practice real interviews — all in one place.
                </div>
                <div class="wz-lp-micro">
                    No guesswork. No fake experience. Just honest, job-ready preparation.
                </div>

                <div class="wz-lp-cta-row">
                    <div class="wz-lp-trust">Built for job seekers who want clarity before applying.</div>
                </div>

                <div class="wz-lp-flow">
                    <div class="wz-lp-flow-card">
                        <div class="wz-lp-flow-num">1</div>
                        <div class="wz-lp-flow-title">Upload CV</div>
                    </div>
                    <div class="wz-lp-flow-card">
                        <div class="wz-lp-flow-num">2</div>
                        <div class="wz-lp-flow-title">Understand gaps</div>
                    </div>
                    <div class="wz-lp-flow-card">
                        <div class="wz-lp-flow-num">3</div>
                        <div class="wz-lp-flow-title">Improve + match jobs</div>
                    </div>
                    <div class="wz-lp-flow-card">
                        <div class="wz-lp-flow-num">4</div>
                        <div class="wz-lp-flow-title">Practice interview</div>
                    </div>
                </div>
            </div>

            <div class="wz-lp-section">
                <div class="wz-lp-panel">
                    <div class="wz-lp-panel-label">Why WorkZo</div>
                    <div class="wz-lp-panel-title">One connected flow instead of scattered career tools.</div>
                    <div class="wz-lp-panel-copy">
                        WorkZo connects your CV, job descriptions, application documents, and interview preparation
                        so every step uses the same context.
                    </div>

                    <div class="wz-lp-mini-grid">
                        <div class="wz-lp-mini">
                            <div class="wz-lp-mini-title">Honest CV review</div>
                            <div class="wz-lp-mini-copy">Find what is missing without inventing experience.</div>
                        </div>
                        <div class="wz-lp-mini">
                            <div class="wz-lp-mini-title">Smarter matching</div>
                            <div class="wz-lp-mini-copy">Compare your CV with real job expectations.</div>
                        </div>
                        <div class="wz-lp-mini">
                            <div class="wz-lp-mini-title">Real interview prep</div>
                            <div class="wz-lp-mini-copy">Practice with pressure, follow-ups, and feedback.</div>
                        </div>
                    </div>
                </div>

                <div class="wz-lp-panel">
                    <div class="wz-lp-panel-label">Beta signal</div>
                    <div class="wz-lp-panel-title">Built around real job-search friction.</div>
                    <div class="wz-lp-panel-copy">
                        WorkZo is designed for people who keep applying but do not know what is blocking them:
                        CV gaps, weak job fit, unclear answers, or poor interview readiness.
                    </div>
                    <div style="height:16px"></div>
                    <div class="wz-lp-proof">
                        <div class="wz-lp-proof-dot"></div>
                        <div>Early testers are using WorkZo to improve CVs, prepare applications, and practice interviews before applying.</div>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Real Streamlit CTA buttons, so navigation works reliably.
    cta1, cta2, _ = st.columns([1.3, 1.25, 3])
    with cta1:
        if st.button("🚀 Start Your Interview Prep", key="wz_landing_start_interview_prep", use_container_width=True):
            _wz_landing_go("onboarding")
    with cta2:
        if st.button("🎤 Try Real Interview Simulation", key="wz_landing_try_real_interview", use_container_width=True):
            _wz_landing_go("real_interview")


# Compatibility aliases depending on your router name.
def render_landing_page():
    show_landing_page()


def show_landing():
    show_landing_page()
