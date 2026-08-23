"""
ui/styles.py
Adaptive CSS & Component Renderers for the CIA Hybrid Dashboard.
Works seamlessly in both Streamlit Dark and Light themes.
"""
import streamlit as st
import html

ADAPTIVE_CSS = """
<style>
/* ── Google Fonts ─────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* ── CSS Custom Properties — Light defaults ──────────────── */
:root {
    --cia-accent:        #0969DA;
    --cia-accent-soft:   #54AEFF;
    --cia-bg:            #F6F8FA;
    --cia-surface:       #FFFFFF;
    --cia-surface2:      #F0F2F5;
    --cia-border:        #D0D7DE;
    --cia-text:          #1F2328;
    --cia-text-muted:    #424A53;
    --cia-text-faint:    #656D76;
    --cia-high:          #CF222E;
    --cia-high-bg:       #FFEBE9;
    --cia-high-border:   #FF8182;
    --cia-med:           #9A6700;
    --cia-med-bg:        #FFF8C5;
    --cia-med-border:    #D4A72C;
    --cia-low:           #1A7F37;
    --cia-low-bg:        #DAFBE1;
    --cia-low-border:    #4AC26B;
    --cia-info:          #0969DA;
    --cia-info-bg:       #DDF4FF;
    --cia-shadow:        rgba(31,35,40,0.06);
    --cia-card-bg:       #FFFFFF;
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
        --cia-text:          #F0F6FC;
        --cia-text-muted:    #C9D1D9;
        --cia-text-faint:    #8B949E;
        --cia-high:          #F85149;
        --cia-high-bg:       #3D1A1A;
        --cia-high-border:   #B62324;
        --cia-med:           #E3B341;
        --cia-med-bg:        #2D2208;
        --cia-med-border:    #9E6A03;
        --cia-low:           #3FB950;
        --cia-low-bg:        #0F2A1A;
        --cia-low-border:    #238636;
        --cia-info:          #58A6FF;
        --cia-info-bg:       #0C2D6B;
        --cia-shadow:        rgba(0,0,0,0.4);
        --cia-card-bg:       #161B22;
    }
}

[data-theme="dark"] {
    --cia-accent:        #58A6FF;
    --cia-accent-soft:   #81D4FA;
    --cia-bg:            #0D1117;
    --cia-surface:       #161B22;
    --cia-surface2:      #21262D;
    --cia-border:        #30363D;
    --cia-text:          #F0F6FC;
    --cia-text-muted:    #C9D1D9;
    --cia-text-faint:    #8B949E;
    --cia-high:          #F85149;
    --cia-high-bg:       #3D1A1A;
    --cia-high-border:   #B62324;
    --cia-med:           #E3B341;
    --cia-med-bg:        #2D2208;
    --cia-med-border:    #9E6A03;
    --cia-low:           #3FB950;
    --cia-low-bg:        #0F2A1A;
    --cia-low-border:    #238636;
    --cia-info:          #58A6FF;
    --cia-info-bg:       #0C2D6B;
    --cia-shadow:        rgba(0,0,0,0.4);
    --cia-card-bg:       #161B22;
}

[data-theme="light"] {
    --cia-accent:        #0969DA;
    --cia-accent-soft:   #54AEFF;
    --cia-bg:            #F6F8FA;
    --cia-surface:       #FFFFFF;
    --cia-surface2:      #F0F2F5;
    --cia-border:        #D0D7DE;
    --cia-text:          #1F2328;
    --cia-text-muted:    #424A53;
    --cia-text-faint:    #656D76;
    --cia-high:          #CF222E;
    --cia-high-bg:       #FFEBE9;
    --cia-high-border:   #FF8182;
    --cia-med:           #9A6700;
    --cia-med-bg:        #FFF8C5;
    --cia-med-border:    #D4A72C;
    --cia-low:           #1A7F37;
    --cia-low-bg:        #DAFBE1;
    --cia-low-border:    #4AC26B;
    --cia-info:          #0969DA;
    --cia-info-bg:       #DDF4FF;
    --cia-shadow:        rgba(31,35,40,0.06);
    --cia-card-bg:       #FFFFFF;
}

/* ── Global Streamlit Layout Resets ─────────────────────── */
.stAppDeployButton { display: none !important; }
footer { visibility: hidden !important; }
[data-testid="stFooter"] { visibility: hidden !important; }
[data-testid="stSidebarNav"] { display: none !important; }

/* ── Header Title & Subtitle ────────────────────────────── */
.cia-title {
    font-size: 32px;
    font-weight: 700;
    background: linear-gradient(135deg, var(--cia-accent) 0%, var(--cia-accent-soft) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-align: center;
    letter-spacing: -0.5px;
    padding: 6px 0 2px;
}
.cia-subtitle {
    font-size: 14px;
    color: var(--cia-text-muted);
    text-align: center;
    margin-bottom: 22px;
}

/* ── Metric Summary Cards ───────────────────────────────── */
.metric-card {
    background: var(--cia-surface);
    border: 1px solid var(--cia-border);
    border-radius: 10px;
    padding: 14px 12px;
    text-align: center;
    box-shadow: 0 2px 6px var(--cia-shadow);
    transition: border-color 0.2s, transform 0.2s;
}
.metric-card:hover {
    border-color: var(--cia-accent);
    transform: translateY(-2px);
}
.metric-value {
    font-size: 26px;
    font-weight: 700;
    color: var(--cia-accent);
    line-height: 1.1;
}
.metric-label {
    font-size: 11px;
    color: var(--cia-text-muted);
    margin-top: 5px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* ── Risk Pills ─────────────────────────────────────────── */
.pill-high {
    background: var(--cia-high-bg);
    color: var(--cia-high);
    border: 1px solid var(--cia-high-border);
    border-radius: 16px; padding: 3px 12px;
    font-weight: 700; font-size: 12px;
    display: inline-flex; align-items: center; gap: 5px;
}
.pill-medium {
    background: var(--cia-med-bg);
    color: var(--cia-med);
    border: 1px solid var(--cia-med-border);
    border-radius: 16px; padding: 3px 12px;
    font-weight: 700; font-size: 12px;
    display: inline-flex; align-items: center; gap: 5px;
}
.pill-low {
    background: var(--cia-low-bg);
    color: var(--cia-low);
    border: 1px solid var(--cia-low-border);
    border-radius: 16px; padding: 3px 12px;
    font-weight: 700; font-size: 12px;
    display: inline-flex; align-items: center; gap: 5px;
}

/* ── Evidence Badges ────────────────────────────────────── */
.badge-verified {
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
}
.badge-unverified {
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
}

/* ── Multi-Layer Artifact Impact Card ───────────────────── */
.artifact-impact-card {
    background: var(--cia-card-bg);
    border: 1px solid var(--cia-border);
    border-radius: 10px;
    padding: 16px 18px;
    margin-bottom: 14px;
    box-shadow: 0 2px 6px var(--cia-shadow);
    transition: border-color 0.2s, box-shadow 0.2s;
}
.artifact-impact-card:hover {
    border-color: var(--cia-accent);
    box-shadow: 0 4px 12px var(--cia-shadow);
}
.artifact-card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
    padding-bottom: 10px;
    border-bottom: 1px solid var(--cia-border);
}
.artifact-name {
    font-family: 'JetBrains Mono', monospace;
    font-size: 16px;
    font-weight: 600;
    color: var(--cia-accent);
}
.artifact-meta-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 12px;
    margin-bottom: 10px;
}
.artifact-meta-item {
    font-size: 13px;
    color: var(--cia-text-muted);
}
.artifact-meta-label {
    font-size: 11px;
    text-transform: uppercase;
    color: var(--cia-text-faint);
    font-weight: 600;
    margin-bottom: 2px;
}
.artifact-meta-value {
    font-weight: 600;
    color: var(--cia-text);
}

/* Progress bar inside cards */
.score-bar-bg {
    background: var(--cia-surface2);
    border-radius: 6px;
    height: 8px;
    width: 100%;
    overflow: hidden;
    margin-top: 4px;
}
.score-bar-fill {
    height: 100%;
    border-radius: 6px;
    background: linear-gradient(90deg, var(--cia-accent) 0%, var(--cia-accent-soft) 100%);
    transition: width 0.3s ease;
}

/* ── Section Headers ────────────────────────────────────── */
.section-header {
    font-size: 16px;
    font-weight: 600;
    color: var(--cia-text);
    margin: 20px 0 10px;
    display: flex;
    align-items: center;
    gap: 8px;
}

.cia-divider {
    border: none;
    border-top: 1px solid var(--cia-border);
    margin: 18px 0;
}
</style>
"""


def inject_styles():
    st.markdown(ADAPTIVE_CSS, unsafe_allow_html=True)


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
    """
    Renders the exact multi-layer impact card designed for the UI.
    """
    score_pct = ml_score * 100.0
    safe_name = html.escape(artifact_name)
    safe_title = html.escape(title_label)
    safe_rationale = html.escape(risk_rationale)
    
    # Traceability badge
    if is_verified:
        trace_badge = '<span class="badge-verified">✓ Verified Traceability</span>'
    else:
        trace_badge = '<span class="badge-unverified">⚡ ML Predicted Candidate</span>'

    # Dependency Evidence Badge
    dep_tier = dependency_reach.upper()
    dep_icon = {"HIGH": "🔴", "MEDIUM": "🟠", "LOW": "🟢", "NONE": "⚪"}.get(dep_tier, "⚪")
    dep_badge = f'<span style="font-weight:600;">{dep_icon} {dep_tier} ({method_count} methods)</span>'

    # Overall Risk Pill
    risk_pill = severity_pill(overall_risk)

    return f"""
<div class="artifact-impact-card">
    <div class="artifact-card-header">
        <div>
            <span style="font-size:12px; color:var(--cia-text-faint); font-weight:600; text-transform:uppercase;">{safe_title}:</span>
            <span class="artifact-name" style="margin-left:6px;">{safe_name}</span>
        </div>
        <div>
            <a href="{viewer_url}" target="_blank" style="background:var(--cia-surface2); color:var(--cia-accent); border:1px solid var(--cia-border); padding:3px 10px; border-radius:6px; font-size:12px; text-decoration:none; font-weight:600;">Inspect Source ↗</a>
        </div>
    </div>
    
    <div class="artifact-meta-grid">
        <div class="artifact-meta-item">
            <div class="artifact-meta-label">1. ML Relationship Score</div>
            <div class="artifact-meta-value" style="font-size:15px; color:var(--cia-accent);">
                {score_pct:.2f}% <span style="font-size:11px; font-weight:500; color:var(--cia-text-faint);">({ml_conf})</span>
            </div>
            <div class="score-bar-bg">
                <div class="score-bar-fill" style="width: {min(max(score_pct, 4), 100):.1f}%;"></div>
            </div>
        </div>
        <div class="artifact-meta-item">
            <div class="artifact-meta-label">2. Traceability Evidence</div>
            <div style="margin-top:4px;">{trace_badge}</div>
        </div>
        <div class="artifact-meta-item">
            <div class="artifact-meta-label">3. Dependency Evidence</div>
            <div style="margin-top:4px; font-size:13px;">{dep_badge}</div>
        </div>
        <div class="artifact-meta-item">
            <div class="artifact-meta-label">4. Overall Impact Risk</div>
            <div style="margin-top:4px;">{risk_pill}</div>
        </div>
    </div>

    <div style="font-size:12px; color:var(--cia-text-faint); padding-top:6px; border-top:1px dashed var(--cia-border); margin-top:6px;">
        <b>Risk Rationale:</b> {safe_rationale}
    </div>
</div>
"""
