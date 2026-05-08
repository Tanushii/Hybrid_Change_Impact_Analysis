"""
ui/styles.py
Adaptive CSS that works with both Streamlit dark and light themes.
Uses CSS custom properties + prefers-color-scheme media queries.
The hamburger menu (☰) is preserved so users can switch themes via Settings.
Only the Deploy button is hidden.
"""
import streamlit as st

ADAPTIVE_CSS = """
<style>
/* ── Google Font ─────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* ── CSS Custom Properties — Light defaults ──────────────── */
:root {
    --cia-accent:        #0969DA;
    --cia-accent-soft:   #54AEFF;
    --cia-bg:            #F6F8FA;
    --cia-surface:       #FFFFFF;
    --cia-surface2:      #F0F2F5;
    --cia-border:        #D0D7DE;
    --cia-text:          #000000;
    --cia-text-muted:    #333333;
    --cia-text-faint:    #555555;
    --cia-high:          #CF222E;
    --cia-high-bg:       #FFEBE9;
    --cia-med:           #9A6700;
    --cia-med-bg:        #FFF8C5;
    --cia-low:           #1A7F37;
    --cia-low-bg:        #DAFBE1;
    --cia-shadow:        rgba(31,35,40,0.08);
}

/* ── CSS Custom Properties — Dark ───────────────────────── */
@media (prefers-color-scheme: dark) {
    :root {
        --cia-accent:        #58A6FF;
        --cia-accent-soft:   #81D4FA;
        --cia-bg:            #0D1117;
        --cia-surface:       #161B22;
        --cia-surface2:      #21262D;
        --cia-border:        #30363D;
        --cia-text:          #FFFFFF;
        --cia-text-muted:    #C9D1D9;
        --cia-text-faint:    #8B949E;
        --cia-high:          #F85149;
        --cia-high-bg:       #3D1A1A;
        --cia-med:           #E3B341;
        --cia-med-bg:        #2D2208;
        --cia-low:           #3FB950;
        --cia-low-bg:        #0F2A1A;
        --cia-shadow:        rgba(0,0,0,0.4);
    }
}

/* ── Streamlit also toggles a data-theme attribute ────────
   Mirror same tokens for Streamlit's own theme toggle.     */
[data-theme="dark"] {
    --cia-accent:        #58A6FF;
    --cia-accent-soft:   #81D4FA;
    --cia-bg:            #0D1117;
    --cia-surface:       #161B22;
    --cia-surface2:      #21262D;
    --cia-border:        #30363D;
    --cia-text:          #FFFFFF;
    --cia-text-muted:    #C9D1D9;
    --cia-text-faint:    #8B949E;
    --cia-high:          #F85149;
    --cia-high-bg:       #3D1A1A;
    --cia-med:           #E3B341;
    --cia-med-bg:        #2D2208;
    --cia-low:           #3FB950;
    --cia-low-bg:        #0F2A1A;
    --cia-shadow:        rgba(0,0,0,0.4);
}

[data-theme="light"] {
    --cia-accent:        #0969DA;
    --cia-accent-soft:   #54AEFF;
    --cia-bg:            #F6F8FA;
    --cia-surface:       #FFFFFF;
    --cia-surface2:      #F0F2F5;
    --cia-border:        #D0D7DE;
    --cia-text:          #000000;
    --cia-text-muted:    #333333;
    --cia-text-faint:    #555555;
    --cia-high:          #CF222E;
    --cia-high-bg:       #FFEBE9;
    --cia-med:           #9A6700;
    --cia-med-bg:        #FFF8C5;
    --cia-low:           #1A7F37;
    --cia-low-bg:        #DAFBE1;
    --cia-shadow:        rgba(31,35,40,0.08);
}

/* ── Remove Streamlit branding & Deploy ─────────────────── */
.stAppDeployButton { display: none !important; }
footer { visibility: hidden !important; }
[data-testid="stFooter"] { visibility: hidden !important; }

/* ── Hide auto-generated sidebar pages nav ─────────────── */
[data-testid="stSidebarNav"] { display: none !important; }

/* ── Title / subtitle ───────────────────────────────────── */
.cia-title {
    font-size: 36px;
    font-weight: 700;
    background: linear-gradient(135deg, var(--cia-accent) 0%, var(--cia-accent-soft) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-align: center;
    letter-spacing: -0.5px;
    padding: 10px 0 4px;
}
.cia-subtitle {
    font-size: 15px;
    color: var(--cia-text-muted);
    text-align: center;
    margin-bottom: 28px;
}

/* ── Metric cards ───────────────────────────────────────── */
.metric-card {
    background: var(--cia-surface);
    border: 1px solid var(--cia-border);
    border-radius: 12px;
    padding: 20px 16px;
    text-align: center;
    box-shadow: 0 2px 8px var(--cia-shadow);
    transition: border-color 0.2s, transform 0.2s, box-shadow 0.2s;
}
.metric-card:hover {
    border-color: var(--cia-accent);
    transform: translateY(-2px);
    box-shadow: 0 4px 16px var(--cia-shadow);
}
.metric-value {
    font-size: 32px;
    font-weight: 700;
    color: var(--cia-accent);
    line-height: 1.1;
}
.metric-label {
    font-size: 12px;
    color: var(--cia-text-muted);
    margin-top: 6px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.6px;
}

/* ── Severity pills ─────────────────────────────────────── */
.pill-high {
    background: var(--cia-high-bg);
    color: var(--cia-high);
    border: 1px solid var(--cia-high);
    border-radius: 20px; padding: 4px 14px;
    font-weight: 700; font-size: 14px;
}
.pill-medium {
    background: var(--cia-med-bg);
    color: var(--cia-med);
    border: 1px solid var(--cia-med);
    border-radius: 20px; padding: 4px 14px;
    font-weight: 700; font-size: 14px;
}
.pill-low {
    background: var(--cia-low-bg);
    color: var(--cia-low);
    border: 1px solid var(--cia-low);
    border-radius: 20px; padding: 4px 14px;
    font-weight: 700; font-size: 14px;
}

/* ── View-file link buttons ─────────────────────────────── */
.view-link a {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: var(--cia-surface);
    color: var(--cia-accent) !important;
    border: 1px solid var(--cia-border);
    border-radius: 8px;
    padding: 5px 14px;
    font-size: 13px;
    font-weight: 500;
    text-decoration: none !important;
    font-family: 'JetBrains Mono', monospace;
    transition: background 0.15s, border-color 0.15s;
}
.view-link a:hover {
    background: var(--cia-surface2);
    border-color: var(--cia-accent);
}

/* ── Section headers ────────────────────────────────────── */
.section-header {
    font-size: 17px;
    font-weight: 600;
    color: var(--cia-text);
    margin: 22px 0 10px;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* ── Dividers ───────────────────────────────────────────── */
.cia-divider {
    border: none;
    border-top: 1px solid var(--cia-border);
    margin: 20px 0;
}

/* ── Search input ───────────────────────────────────────── */
[data-testid="stTextInput"] input {
    border-radius: 8px !important;
    border-color: var(--cia-border) !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}
[data-testid="stTextInput"] input:focus {
    border-color: var(--cia-accent) !important;
    box-shadow: 0 0 0 3px color-mix(in srgb, var(--cia-accent) 20%, transparent) !important;
}

/* ── DataFrames ─────────────────────────────────────────── */
[data-testid="stDataFrame"] {
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid var(--cia-border) !important;
}

/* ── Sidebar ────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    border-right: 1px solid var(--cia-border) !important;
}

/* ── Buttons ────────────────────────────────────────────── */
.stButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    width: 100%;
    transition: opacity 0.2s, transform 0.15s !important;
    border: none !important;
    background: linear-gradient(135deg, var(--cia-accent) 0%, var(--cia-accent-soft) 100%) !important;
    color: #fff !important;
    padding: 10px 24px !important;
}
.stButton > button:hover {
    opacity: 0.88 !important;
    transform: translateY(-1px) !important;
}

/* ── Caption / footnote text ────────────────────────────── */
.stCaption, [data-testid="stCaptionContainer"] {
    color: var(--cia-text-faint) !important;
}
</style>
"""


def inject_styles():
    st.markdown(ADAPTIVE_CSS, unsafe_allow_html=True)


def metric_card(value, label):
    return (
        f'<div class="metric-card">'
        f'<div class="metric-value">{value}</div>'
        f'<div class="metric-label">{label}</div>'
        f'</div>'
    )


def severity_pill(severity):
    cls   = {"HIGH": "pill-high", "MEDIUM": "pill-medium", "LOW": "pill-low"}.get(severity, "pill-low")
    icons = {"HIGH": "🔴", "MEDIUM": "🟠", "LOW": "🟢"}
    return f'<span class="{cls}">{icons.get(severity, "")} {severity}</span>'
