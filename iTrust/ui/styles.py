"""
ui/styles.py
Adaptive CSS & Component Renderers for the CIA Hybrid Dashboard.
Supports Light Mode (default) and Dark Mode via a single authoritative session-state theme toggle.
Directly injects complete, unambiguous CSS rules for the active theme on every rerun.
"""
import streamlit as st
import html
from typing import Dict, Any


def get_theme() -> str:
    """Return active theme: 'light' (default) or 'dark'."""
    return st.session_state.get("theme", "light")


def get_chart_colors() -> Dict[str, Any]:
    """Return Plotly-ready color values for the active theme."""
    theme = get_theme()
    if theme == "light":
        return {
            "bg":          "rgba(0,0,0,0)",
            "plot_bg":     "#FFFFFF",
            "text":        "#1A202C",
            "grid":        "#D1D9E6",
            "axis":        "#3D4A5C",
            "bar_main":    "#0058CC",
            "bar_accent":  "#15803D",
            "colorscale":  [[0.0, "#DBEAFE"], [0.5, "#3B82F6"], [1.0, "#0058CC"]],
            "annot_color": "#1A202C",
        }
    else:
        return {
            "bg":          "rgba(0,0,0,0)",
            "plot_bg":     "#161B22",
            "text":        "#F0F6FC",
            "grid":        "#30363D",
            "axis":        "#B0BAC9",
            "bar_main":    "#58A6FF",
            "bar_accent":  "#56D364",
            "colorscale":  [[0.0, "#0C2D6B"], [0.5, "#1F6FEB"], [1.0, "#58A6FF"]],
            "annot_color": "#F0F6FC",
        }


def _build_theme_css(theme: str) -> str:
    """Generate deterministic, complete CSS rules for the active theme."""
    if theme == "dark":
        tokens = """
    --cia-bg:            #0D1117;
    --cia-surface:       #161B22;
    --cia-surface2:      #21262D;
    --cia-card-bg:       #161B22;
    --cia-border:        #30363D;
    --cia-border-subtle: #21262D;
    --cia-text:          #F0F6FC;
    --cia-text-muted:    #C9D1D9;
    --cia-text-faint:    #8B949E;
    --cia-accent:        #58A6FF;
    --cia-accent-soft:   #79C0FF;
    --cia-high:          #FF7B72;
    --cia-high-bg:       #3D1A1A;
    --cia-high-border:   #F85149;
    --cia-med:           #F0B429;
    --cia-med-bg:        #2D2208;
    --cia-med-border:    #E3B341;
    --cia-low:           #56D364;
    --cia-low-bg:        #0F2A1A;
    --cia-low-border:    #3FB950;
    --cia-info:          #58A6FF;
    --cia-info-bg:       #0C2D6B;
    --cia-shadow:        rgba(0,0,0,0.5);
    --cia-code-bg:       #0D1117;
    --cia-code-text:     #E6EDF3;
    --cia-code-lineno:   #6E7681;
    --cia-code-highlight:#3D1A1A;
    --cia-code-search:   rgba(240,180,41,0.25);
    --cia-code-method:   rgba(88,166,255,0.12);
        """
        app_bg = "#0D1117"
        app_text = "#F0F6FC"
        sidebar_bg = "#161B22"
        sidebar_border = "#30363D"
        input_bg = "#161B22"
        input_border = "#30363D"
        button_bg = "#21262D"
        button_hover = "#30363D"
        button_border = "#30363D"
        tab_list_bg = "#21262D"
        tab_active_color = "#58A6FF"
        expander_bg = "#161B22"
        toggle_btn_bg = "#58A6FF"
        toggle_btn_text = "#0D1117"
        toggle_btn_hover = "#79C0FF"
        popover_bg = "#161B22"
        popover_border = "#30363D"
        popover_text = "#F0F6FC"
        popover_hover_bg = "#21262D"
        popover_hover_text = "#58A6FF"
    else:  # light
        tokens = """
    --cia-bg:            #F4F6F9;
    --cia-surface:       #FFFFFF;
    --cia-surface2:      #E5E9F0;
    --cia-card-bg:       #FFFFFF;
    --cia-border:        #C8D1DC;
    --cia-border-subtle: #DFE5EC;
    --cia-text:          #1A202C;
    --cia-text-muted:    #334155;
    --cia-text-faint:    #475569;
    --cia-accent:        #0058CC;
    --cia-accent-soft:   #2563EB;
    --cia-high:          #B91C1C;
    --cia-high-bg:       #FEE2E2;
    --cia-high-border:   #EF4444;
    --cia-med:           #92400E;
    --cia-med-bg:        #FEF3C7;
    --cia-med-border:    #D97706;
    --cia-low:           #15803D;
    --cia-low-bg:        #DCFCE7;
    --cia-low-border:    #22C55E;
    --cia-info:          #0058CC;
    --cia-info-bg:       #DBEAFE;
    --cia-shadow:        rgba(15,23,42,0.08);
    --cia-code-bg:       #F8FAFC;
    --cia-code-text:     #0F172A;
    --cia-code-lineno:   #64748B;
    --cia-code-highlight:#FEE2E2;
    --cia-code-search:   rgba(146,64,14,0.18);
    --cia-code-method:   rgba(0,88,204,0.08);
        """
        app_bg = "#F4F6F9"
        app_text = "#1A202C"
        sidebar_bg = "#FFFFFF"
        sidebar_border = "#C8D1DC"
        input_bg = "#FFFFFF"
        input_border = "#C8D1DC"
        button_bg = "#FFFFFF"
        button_hover = "#E5E9F0"
        button_border = "#C8D1DC"
        tab_list_bg = "#E5E9F0"
        tab_active_color = "#0058CC"
        expander_bg = "#FFFFFF"
        toggle_btn_bg = "#1A202C"
        toggle_btn_text = "#FFFFFF"
        toggle_btn_hover = "#2D3748"
        popover_bg = "#FFFFFF"
        popover_border = "#C8D1DC"
        popover_text = "#1A202C"
        popover_hover_bg = "#E5E9F0"
        popover_hover_text = "#0058CC"

    return f"""
<style>
/* ── Google Fonts ─────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}}

/* ── Active Theme Variables ──────────────────────────────── */
:root {{
{tokens}
}}

/* ── App Layout & Backgrounds ────────────────────────────── */
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
.main,
.block-container {{
    background-color: {app_bg} !important;
    color: {app_text} !important;
}}

[data-testid="stHeader"] {{
    background-color: {app_bg} !important;
}}

/* ── Sidebar ─────────────────────────────────────────────── */
[data-testid="stSidebar"],
[data-testid="stSidebarContent"],
section[data-testid="stSidebar"] {{
    background-color: {sidebar_bg} !important;
    border-right: 1px solid {sidebar_border} !important;
    color: {app_text} !important;
}}

[data-testid="stSidebar"] *,
[data-testid="stSidebarContent"] * {{
    color: {app_text} !important;
}}

[data-testid="stSidebar"] hr {{
    border-color: {sidebar_border} !important;
}}

/* ── Native Inputs & Controls ────────────────────────────── */
.stTextInput input,
.stTextArea textarea,
[data-baseweb="input"] input,
[data-baseweb="textarea"] textarea {{
    background-color: {input_bg} !important;
    color: {app_text} !important;
    border-color: {input_border} !important;
}}

.stTextInput > div > div,
[data-baseweb="input"] > div,
[data-baseweb="textarea"] > div {{
    background-color: {input_bg} !important;
    border-color: {input_border} !important;
}}

.stTextInput input::placeholder,
.stTextArea textarea::placeholder {{
    color: var(--cia-text-faint) !important;
}}

/* ── Selectbox Closed & Search Container ──────────────────── */
.stSelectbox > div > div,
[data-baseweb="select"] > div {{
    background-color: {input_bg} !important;
    color: {app_text} !important;
    border-color: {input_border} !important;
}}

.stSelectbox [data-baseweb="select"] *,
[data-baseweb="select"] input,
[data-baseweb="select"] span,
[data-baseweb="select"] div {{
    color: {app_text} !important;
}}

/* ── Selectbox Open Popover & Options (High Contrast Fix) ── */
div[data-baseweb="popover"],
div[data-baseweb="popover"] > div,
div[data-baseweb="popover"] ul,
div[data-baseweb="menu"],
ul[role="listbox"],
[data-testid="stSelectboxVirtualDropdown"] {{
    background-color: {popover_bg} !important;
    color: {popover_text} !important;
    border: 1px solid {popover_border} !important;
    box-shadow: 0 4px 16px var(--cia-shadow) !important;
}}

div[data-baseweb="popover"] li,
div[data-baseweb="popover"] [role="option"],
div[data-baseweb="popover"] [data-baseweb="option"],
div[data-baseweb="menu"] li,
ul[role="listbox"] li,
[data-testid="stSelectboxVirtualDropdown"] li {{
    background-color: {popover_bg} !important;
    color: {popover_text} !important;
}}

div[data-baseweb="popover"] li *,
div[data-baseweb="popover"] [role="option"] *,
div[data-baseweb="popover"] [data-baseweb="option"] *,
div[data-baseweb="menu"] li *,
ul[role="listbox"] li *,
[data-testid="stSelectboxVirtualDropdown"] li * {{
    color: {popover_text} !important;
}}

div[data-baseweb="popover"] li:hover,
div[data-baseweb="popover"] [role="option"]:hover,
div[data-baseweb="popover"] [data-baseweb="option"]:hover,
div[data-baseweb="popover"] [aria-selected="true"],
div[data-baseweb="menu"] li:hover,
ul[role="listbox"] li:hover {{
    background-color: {popover_hover_bg} !important;
    color: {popover_hover_text} !important;
}}

div[data-baseweb="popover"] li:hover *,
div[data-baseweb="popover"] [role="option"]:hover *,
div[data-baseweb="popover"] [data-baseweb="option"]:hover *,
div[data-baseweb="popover"] [aria-selected="true"] *,
div[data-baseweb="menu"] li:hover *,
ul[role="listbox"] li:hover * {{
    color: {popover_hover_text} !important;
}}

/* Radio & Checkbox */
.stRadio label,
.stRadio > div,
.stRadio p,
.stRadio span,
.stCheckbox label,
.stCheckbox span,
.stCheckbox p {{
    color: {app_text} !important;
}}

/* Buttons */
.stButton > button {{
    background-color: {button_bg} !important;
    color: {app_text} !important;
    border: 1px solid {button_border} !important;
}}

.stButton > button:hover {{
    background-color: {button_hover} !important;
    border-color: var(--cia-accent) !important;
    color: var(--cia-accent) !important;
}}

.stLinkButton > a {{
    background-color: {button_bg} !important;
    color: var(--cia-accent) !important;
    border: 1px solid {button_border} !important;
}}

.stLinkButton > a:hover {{
    background-color: {button_hover} !important;
    border-color: var(--cia-accent) !important;
}}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {{
    background-color: {tab_list_bg} !important;
    border-bottom: 1px solid var(--cia-border) !important;
}}

.stTabs [data-baseweb="tab"] {{
    color: var(--cia-text-muted) !important;
    background-color: transparent !important;
}}

.stTabs [aria-selected="true"] {{
    color: {tab_active_color} !important;
    border-bottom: 2px solid {tab_active_color} !important;
    font-weight: 700 !important;
}}

.stTabs [data-baseweb="tab-panel"] {{
    background-color: {app_bg} !important;
}}

/* Expanders */
[data-testid="stExpander"] {{
    border: 1px solid var(--cia-border) !important;
    background-color: {expander_bg} !important;
    border-radius: 8px !important;
}}

[data-testid="stExpander"] summary,
details > summary {{
    color: {app_text} !important;
    background-color: {expander_bg} !important;
}}

[data-testid="stExpander"] > div > div {{
    background-color: {expander_bg} !important;
}}

/* Bordered containers */
[data-testid="stVerticalBlockBorderWrapper"] {{
    background-color: var(--cia-surface) !important;
    border-color: var(--cia-border) !important;
}}

/* Typography */
.stMarkdown p,
.stMarkdown li,
.stMarkdown span,
.stMarkdown div {{
    color: {app_text} !important;
}}

h1, h2, h3, h4, h5, h6 {{
    color: {app_text} !important;
}}

.stCaption, small {{
    color: var(--cia-text-faint) !important;
}}

label, [data-testid="stWidgetLabel"] p {{
    color: var(--cia-text-muted) !important;
}}

hr {{
    border-color: var(--cia-border) !important;
}}

/* DataFrames */
[data-testid="stDataFrameContainer"],
.stDataFrame {{
    background-color: var(--cia-surface) !important;
}}

/* ── Resets ───────────────────────────────────────────────── */
.stAppDeployButton {{ display: none !important; }}
footer {{ visibility: hidden !important; }}
[data-testid="stFooter"] {{ visibility: hidden !important; }}
[data-testid="stSidebarNav"] {{ display: none !important; }}

/* ── Theme Toggle Button ──────────────────────────────────── */
.cia-theme-btn-wrap {{
    display: flex;
    justify-content: flex-end;
    align-items: flex-start;
    padding-top: 6px;
}}

.cia-theme-btn-wrap .stButton > button {{
    background-color: {toggle_btn_bg} !important;
    color:            {toggle_btn_text} !important;
    border:           1px solid {toggle_btn_bg} !important;
    border-radius:    20px !important;
    font-weight:      700 !important;
    font-size:        13px !important;
    padding:          6px 18px !important;
    letter-spacing:   0.2px;
    white-space:      nowrap;
    box-shadow:       0 2px 5px var(--cia-shadow);
}}

.cia-theme-btn-wrap .stButton > button:hover {{
    background-color: {toggle_btn_hover} !important;
    border-color:     {toggle_btn_hover} !important;
    color:            {toggle_btn_text} !important;
}}

/* ── Custom Cards & Badges ────────────────────────────────── */
.cia-title {{
    font-size: 30px;
    font-weight: 700;
    background: linear-gradient(135deg, var(--cia-accent) 0%, var(--cia-accent-soft) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.5px;
    padding: 4px 0 2px;
}}

.cia-subtitle {{
    font-size: 13px;
    color: var(--cia-text-muted);
    margin-bottom: 18px;
}}

.metric-card {{
    background: var(--cia-surface);
    border: 1px solid var(--cia-border);
    border-radius: 10px;
    padding: 14px 12px;
    text-align: center;
    box-shadow: 0 2px 6px var(--cia-shadow);
    transition: border-color 0.2s, transform 0.2s;
}}

.metric-card:hover {{
    border-color: var(--cia-accent);
    transform: translateY(-2px);
}}

.metric-value {{
    font-size: 26px;
    font-weight: 700;
    color: var(--cia-accent);
    line-height: 1.1;
}}

.metric-label {{
    font-size: 11px;
    color: var(--cia-text-muted);
    margin-top: 5px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

.pill-high {{
    background: var(--cia-high-bg);
    color: var(--cia-high);
    border: 1px solid var(--cia-high-border);
    border-radius: 16px; padding: 3px 12px;
    font-weight: 700; font-size: 12px;
    display: inline-flex; align-items: center; gap: 5px;
}}

.pill-medium {{
    background: var(--cia-med-bg);
    color: var(--cia-med);
    border: 1px solid var(--cia-med-border);
    border-radius: 16px; padding: 3px 12px;
    font-weight: 700; font-size: 12px;
    display: inline-flex; align-items: center; gap: 5px;
}}

.pill-low {{
    background: var(--cia-low-bg);
    color: var(--cia-low);
    border: 1px solid var(--cia-low-border);
    border-radius: 16px; padding: 3px 12px;
    font-weight: 700; font-size: 12px;
    display: inline-flex; align-items: center; gap: 5px;
}}

.badge-verified {{
    background: var(--cia-low-bg);
    color: var(--cia-low);
    border: 1px solid var(--cia-low-border);
    border-radius: 14px;
    padding: 3px 10px;
    font-size: 12px;
    font-weight: 600;
    display: inline-flex;
    align-items: center;
    gap: 4px;
}}

.badge-unverified {{
    background: var(--cia-surface2);
    color: var(--cia-text-faint);
    border: 1px solid var(--cia-border);
    border-radius: 14px;
    padding: 3px 10px;
    font-size: 12px;
    font-weight: 500;
    display: inline-flex;
    align-items: center;
    gap: 4px;
}}

.artifact-impact-card {{
    background: var(--cia-card-bg);
    border: 1px solid var(--cia-border);
    border-radius: 10px;
    padding: 16px 18px;
    margin-bottom: 14px;
    box-shadow: 0 2px 6px var(--cia-shadow);
    transition: border-color 0.2s, box-shadow 0.2s;
}}

.artifact-impact-card:hover {{
    border-color: var(--cia-accent);
    box-shadow: 0 4px 12px var(--cia-shadow);
}}

.artifact-card-header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
    padding-bottom: 10px;
    border-bottom: 1px solid var(--cia-border);
}}

.artifact-name {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 16px;
    font-weight: 600;
    color: var(--cia-accent);
}}

.artifact-meta-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 12px;
    margin-bottom: 10px;
}}

.artifact-meta-item {{ font-size: 13px; color: var(--cia-text-muted); }}
.artifact-meta-label {{
    font-size: 11px;
    text-transform: uppercase;
    color: var(--cia-text-faint);
    font-weight: 600;
    margin-bottom: 2px;
}}
.artifact-meta-value {{ font-weight: 600; color: var(--cia-text); }}

.section-header {{
    font-size: 16px;
    font-weight: 600;
    color: var(--cia-text);
    margin: 20px 0 10px;
    display: flex;
    align-items: center;
    gap: 8px;
}}

.cia-divider {{
    border: none;
    border-top: 1px solid var(--cia-border);
    margin: 18px 0;
}}
</style>
"""


def inject_styles():
    """Inject dynamic CSS tailored directly to the active session-state theme."""
    theme = get_theme()
    css = _build_theme_css(theme)
    st.markdown(css, unsafe_allow_html=True)


def inject_theme_script():
    """No-op kept for backward compatibility."""
    pass


def render_theme_toggle():
    """
    Render the authoritative theme toggle button.
    Light mode → shows '🌙 Dark Mode'  (dark button on light bg)
    Dark  mode → shows '☀️ Light Mode' (vibrant button on dark bg)
    """
    theme = get_theme()
    label = "🌙  Dark Mode" if theme == "light" else "☀️  Light Mode"

    st.markdown('<div class="cia-theme-btn-wrap">', unsafe_allow_html=True)
    clicked = st.button(label, key="__cia_theme_toggle__")
    st.markdown('</div>', unsafe_allow_html=True)

    if clicked:
        st.session_state["theme"] = "dark" if theme == "light" else "light"
        st.rerun()


# ── Component renderers ───────────────────────────────────────────────────────

def metric_card(value, label):
    return (
        f'<div class="metric-card">'
        f'<div class="metric-value">{html.escape(str(value))}</div>'
        f'<div class="metric-label">{html.escape(label)}</div>'
        f'</div>'
    )


def severity_pill(severity):
    sev = str(severity).upper()
    cls = {"HIGH": "pill-high", "MEDIUM": "pill-medium", "LOW": "pill-low"}.get(sev, "pill-low")
    icons = {"HIGH": "🔴", "MEDIUM": "🟠", "LOW": "🟢"}
    return f'<span class="{cls}">{icons.get(sev, "")} {html.escape(sev)}</span>'


def render_artifact_card_native(
    artifact_name: str,
    overall_risk: str,
    ml_score: float,
    dependency_reach: str,
    method_count: int,
    is_verified: bool,
    viewer_url: str,
    risk_rationale: str = "",
    title_label: str = "Code File",
    btn_label: str = "Inspect Source ↗",
):
    """
    Renders a clean, high-visibility artifact impact card using native Streamlit containers.
    """
    score_pct = ml_score * 100.0
    icon = "📄" if artifact_name.endswith((".java", ".txt", ".py", ".ts", ".js", ".go")) else "📁"

    with st.container(border=True):
        c_title, c_btn = st.columns([3.8, 1.2])
        with c_title:
            st.markdown(
                f'<div style="display:flex; align-items:center; gap:8px; margin-bottom:2px;">'
                f'<span style="font-size:18px;">{icon}</span>'
                f'<span style="font-family:JetBrains Mono, monospace; font-size:16px; font-weight:700; color:var(--cia-accent);">{html.escape(artifact_name)}</span>'
                f'<span style="font-size:11px; color:var(--cia-text-faint); text-transform:uppercase; font-weight:600; margin-left:4px;">({html.escape(title_label)})</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with c_btn:
            st.link_button(btn_label, viewer_url, use_container_width=True)

        c_risk, c_ml, c_dep, c_trace = st.columns(4)
        with c_risk:
            st.caption("Overall Impact Risk")
            st.markdown(severity_pill(overall_risk), unsafe_allow_html=True)
        with c_ml:
            st.caption("ML Relationship Score")
            st.markdown(f'<b style="font-size:15px; font-family:JetBrains Mono, monospace; color:var(--cia-text);">{score_pct:.2f}%</b>', unsafe_allow_html=True)
        with c_dep:
            st.caption("Dependency Reach")
            dep_icon = {"HIGH": "🔴", "MEDIUM": "🟠", "LOW": "🟢", "NONE": "⚪"}.get(dependency_reach.upper(), "⚪")
            st.markdown(f'<span style="font-size:13px; font-weight:600;">{dep_icon} {html.escape(dependency_reach)} ({method_count} methods)</span>', unsafe_allow_html=True)
        with c_trace:
            st.caption("Traceability Status")
            if is_verified:
                st.markdown('<span class="badge-verified">✓ Verified Traceability Link</span>', unsafe_allow_html=True)
            else:
                st.markdown('<span class="badge-unverified">⚡ ML Predicted Relationship</span>', unsafe_allow_html=True)

        if risk_rationale:
            st.caption(f"**Rationale:** {risk_rationale}")


def render_artifact_card(
    title_label: str,
    artifact_name: str,
    ml_score: float,
    ml_conf: str,
    is_verified: bool,
    dependency_reach: str,
    method_count: int,
    overall_risk: str,
    risk_rationale: str,
    viewer_url: str
) -> str:
    """Renders a single-line HTML artifact card."""
    score_pct = ml_score * 100.0
    safe_name = html.escape(artifact_name)
    safe_title = html.escape(title_label)
    safe_rationale = html.escape(risk_rationale)

    trace_badge = (
        '<span class="badge-verified">✓ Verified Traceability</span>'
        if is_verified else
        '<span class="badge-unverified">⚡ ML Predicted Candidate</span>'
    )

    dep_tier = dependency_reach.upper()
    dep_icon = {"HIGH": "🔴", "MEDIUM": "🟠", "LOW": "🟢", "NONE": "⚪"}.get(dep_tier, "⚪")
    dep_badge = f'<span style="font-weight:600;">{dep_icon} {dep_tier} ({method_count} methods)</span>'
    risk_pill = severity_pill(overall_risk)

    return (
        f'<div class="artifact-impact-card">'
        f'<div class="artifact-card-header">'
        f'<div><span style="font-size:12px; color:var(--cia-text-faint); font-weight:600; text-transform:uppercase;">{safe_title}:</span> '
        f'<span class="artifact-name" style="margin-left:6px;">{safe_name}</span></div>'
        f'<div><a href="{viewer_url}" target="_blank" style="background:var(--cia-surface2); color:var(--cia-accent); border:1px solid var(--cia-border); padding:4px 12px; border-radius:6px; font-size:12px; text-decoration:none; font-weight:600;">Inspect Source ↗</a></div>'
        f'</div>'
        f'<div class="artifact-meta-grid">'
        f'<div class="artifact-meta-item"><div class="artifact-meta-label">1. ML Relationship Score</div><div class="artifact-meta-value" style="font-size:15px; color:var(--cia-accent);">{score_pct:.2f}% <span style="font-size:11px; font-weight:500; color:var(--cia-text-faint);">({ml_conf})</span></div></div>'
        f'<div class="artifact-meta-item"><div class="artifact-meta-label">2. Traceability Evidence</div><div style="margin-top:4px;">{trace_badge}</div></div>'
        f'<div class="artifact-meta-item"><div class="artifact-meta-label">3. Dependency Evidence</div><div style="margin-top:4px; font-size:13px;">{dep_badge}</div></div>'
        f'<div class="artifact-meta-item"><div class="artifact-meta-label">4. Overall Impact Risk</div><div style="margin-top:4px;">{risk_pill}</div></div>'
        f'</div>'
        f'<div style="font-size:12px; color:var(--cia-text-faint); padding-top:6px; border-top:1px dashed var(--cia-border); margin-top:6px;"><b>Risk Rationale:</b> {safe_rationale}</div>'
        f'</div>'
    )
