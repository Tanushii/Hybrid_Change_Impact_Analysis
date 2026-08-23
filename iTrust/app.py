"""
app.py — CIA System Main Entry Point.
Multi-Layer Hybrid Change Impact Analysis:
- ML Relationship Analysis (XGBoost + SBERT + TF-IDF)
- Verified Traceability Links (Ground Truth)
- Dependency Propagation (Call Graph)
"""
import streamlit as st

st.set_page_config(
    page_title="CIA System — Change Impact Analysis",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Imports (after set_page_config) ─────────────────────────────────────────
from ui.styles import inject_styles
from services.data_loader import (
    load_traceability_links,
    load_callgraph,
    build_file_index,
    load_all_requirements,
    load_all_code_texts
)
from services.ml_engine import load_ml_artifacts
import ui.req_to_code as mode_r2c
import ui.code_to_req as mode_c2r

# ── Global styles ────────────────────────────────────────────────────────────
inject_styles()

# ── Load data & ML artifacts (cached) ────────────────────────────────────────
req_to_code, code_to_req = load_traceability_links()
callgraph = load_callgraph()
file_index = build_file_index()
all_req_texts = load_all_requirements()
all_code_texts = load_all_code_texts()
ml_artifacts = load_ml_artifacts()

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="cia-title">⚡ AI-Assisted Change Impact Analysis</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="cia-subtitle">'
    'Multi-Layer Traceability &amp; Dependency-Aware Impact Prediction — iTrust'
    '</div>',
    unsafe_allow_html=True,
)

# ── Sidebar navigation ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<p style="font-size:18px;font-weight:700;color:var(--cia-text);margin-bottom:4px;">⚙️ Navigation</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p style="font-size:12px;color:var(--cia-text-faint);margin-bottom:14px;">Select analysis direction</p>',
        unsafe_allow_html=True,
    )
    mode = st.radio(
        "Analysis Mode",
        ["📋  Requirement → Code", "🔧  Code → Requirement"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.markdown(
        '<p style="font-size:12px;color:var(--cia-text-muted);line-height:1.7;">'
        '<b style="color:var(--cia-text);">System Knowledge Base:</b><br>'
        f'• <b style="color:#3FB950;">{len(all_req_texts)}</b> Software Requirements<br>'
        f'• <b style="color:#3FB950;">{len(all_code_texts)}</b> Java Code Artifacts<br>'
        f'• <b style="color:#3FB950;">{sum(len(v) for v in req_to_code.values())}</b> Verified Ground-Truth Links<br>'
        f'• <b style="color:#3FB950;">{len(callgraph):,}</b> Method Call Graph Nodes<br>'
        f'• <b style="color:#3FB950;">501</b> Hybrid ML Features (XGBoost)'
        '</p>',
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.markdown(
        '<div style="font-size:11px;color:var(--cia-text-faint);line-height:1.5;">'
        '<b>ML Architecture:</b><br>'
        '• SBERT (all-MiniLM-L6-v2)<br>'
        '• TF-IDF Vectorizer (500 features)<br>'
        '• XGBoost Classifier (150 trees)<br>'
        '• Baseline Accuracy: <b>85.22%</b>'
        '</div>',
        unsafe_allow_html=True
    )

# ── Route to selected mode ───────────────────────────────────────────────────
if mode == "📋  Requirement → Code":
    mode_r2c.render(
        req_to_code=req_to_code,
        callgraph=callgraph,
        file_index=file_index,
        all_req_texts=all_req_texts,
        all_code_texts=all_code_texts
    )
else:
    mode_c2r.render(
        code_to_req=code_to_req,
        callgraph=callgraph,
        file_index=file_index,
        all_req_texts=all_req_texts,
        all_code_texts=all_code_texts
    )