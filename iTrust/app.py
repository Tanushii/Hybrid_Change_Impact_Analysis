"""
app.py — CIA System Main Entry Point.
AI-Assisted Hybrid Change Impact Analysis Platform:
1. Live Repository Analysis (Predictive & Post-Change Modes for GitHub repositories)
2. Academic Benchmark & Validation Environment (iTrust Ground-Truth Traceability & Call Graph Propagation)
"""
import streamlit as st

st.set_page_config(
    page_title="CIA System — Change Impact Analysis",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Imports (after set_page_config) ─────────────────────────────────────────
from ui.styles import inject_styles, inject_theme_script, render_theme_toggle
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
import ui.github_predictive as mode_gh_pred
import ui.github_post_change as mode_gh_post
import ui.results as mode_results

# ── Initialize theme — default: Light Mode ─────────────────────────────────
if "theme" not in st.session_state:
    st.session_state["theme"] = "light"

# ── Global styles + activate theme ───────────────────────────────────
inject_styles()
inject_theme_script()   # sets data-theme on <html> to activate CSS tokens

# ── Load data & ML artifacts (cached) ────────────────────────────────────────
req_to_code, code_to_req = load_traceability_links()
callgraph = load_callgraph()
file_index = build_file_index()
all_req_texts = load_all_requirements()
all_code_texts = load_all_code_texts()
ml_artifacts = load_ml_artifacts()

# ── Header (title + toggle) ───────────────────────────────────────────
_h_title, _h_gap, _h_toggle = st.columns([7, 1, 2])
with _h_title:
    st.markdown(
        '<div class="cia-title">⚡ AI-Assisted Change Impact Analysis</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="cia-subtitle">'
        'Multi-Layer Traceability, Semantic Relationships &amp; Structural Dependency Propagation'
        '</div>',
        unsafe_allow_html=True,
    )
with _h_toggle:
    render_theme_toggle()

# ── Sidebar Navigation ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<p style="font-size:18px;font-weight:700;color:var(--cia-text);margin-bottom:2px;">⚙️ Navigation</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p style="font-size:12px;color:var(--cia-text-faint);margin-bottom:12px;">Select analysis source &amp; workflow</p>',
        unsafe_allow_html=True,
    )

    # ── Grouped Navigation Options ───────────────────────────────────────
    mode = st.radio(
        "Select Workflow",
        [
            "🔵  Predictive Impact Analysis (Before Change)",
            "🟠  Post-Change Impact Analysis (Commit Diff)",
            "📋  iTrust: Requirement → Code",
            "🔧  iTrust: Code → Requirement",
            "📊  Results & Evaluation",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")

    # ── Context-Aware Sidebar Information ────────────────────────────────
    if "iTrust" in mode:
        st.markdown(
            '<p style="font-size:12px;color:var(--cia-text-muted);line-height:1.7;">'
            '<b style="color:var(--cia-text);">🧪 iTrust Benchmark Baseline:</b><br>'
            f'• <b style="color:#3FB950;">{len(all_req_texts)}</b> Software Requirements<br>'
            f'• <b style="color:#3FB950;">{len(all_code_texts)}</b> Java Code Artifacts<br>'
            f'• <b style="color:#3FB950;">{sum(len(v) for v in req_to_code.values())}</b> Ground-Truth Answer Links<br>'
            f'• <b style="color:#3FB950;">{len(callgraph):,}</b> Method Call Graph Nodes<br>'
            f'• <b style="color:#3FB950;">501</b> Hybrid Features (TF-IDF + SBERT)'
            '</p>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<p style="font-size:12px;color:var(--cia-text-muted);line-height:1.7;">'
            '<b style="color:var(--cia-text);">🌐 Repository Analysis Engine:</b><br>'
            '• Dynamic Multi-Language Discovery<br>'
            '• Lightweight Static Dependency Reach<br>'
            '• Model-Based Semantic Relationships<br>'
            '• Unified Diff &amp; Changed Function Detection<br>'
            '• Extensible Risk Synthesis Policy'
            '</p>',
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown(
        '<div style="font-size:11px;color:var(--cia-text-faint);line-height:1.6;">'
        '<b>ML Architecture &amp; Evaluation:</b><br>'
        '• Model: XGBoost Classifier (150 trees)<br>'
        '• Embeddings: SBERT (all-MiniLM-L6-v2)<br>'
        '• Lexical: TF-IDF (500 features)<br>'
        '• Evaluated on iTrust Benchmark<br>'
        '• Test Split Accuracy: <b>85.22%</b>'
        '</div>',
        unsafe_allow_html=True
    )

# ── Route to Selected Mode ───────────────────────────────────────────────────
if mode == "🔵  Predictive Impact Analysis (Before Change)":
    mode_gh_pred.render()
elif mode == "🟠  Post-Change Impact Analysis (Commit Diff)":
    mode_gh_post.render()
elif mode == "📋  iTrust: Requirement → Code":
    mode_r2c.render(
        req_to_code=req_to_code,
        callgraph=callgraph,
        file_index=file_index,
        all_req_texts=all_req_texts,
        all_code_texts=all_code_texts
    )
elif mode == "🔧  iTrust: Code → Requirement":
    mode_c2r.render(
        code_to_req=code_to_req,
        callgraph=callgraph,
        file_index=file_index,
        all_req_texts=all_req_texts,
        all_code_texts=all_code_texts
    )
elif mode == "📊  Results & Evaluation":
    mode_results.render()