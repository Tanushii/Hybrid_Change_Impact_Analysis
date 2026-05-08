"""
app.py — CIA System main entry point.
Thin routing shell: loads data, injects styles, renders selected mode.
"""
import streamlit as st

st.set_page_config(
    page_title="CIA System — Change Impact Analysis",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Imports (after set_page_config) ─────────────────────────────────────────
from ui.styles import inject_styles
from services.data_loader import load_traceability_links, load_callgraph, build_file_index
import ui.req_to_code as mode_r2c
import ui.code_to_req as mode_c2r

# ── Global styles ────────────────────────────────────────────────────────────
inject_styles()

# ── Load data (cached) ───────────────────────────────────────────────────────
req_to_code, code_to_req = load_traceability_links()
callgraph   = load_callgraph()
file_index  = build_file_index()

# ── Title ────────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="cia-title">⚡ AI-Assisted Change Impact Analysis</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="cia-subtitle">'
    'Bidirectional Traceability &amp; Dependency-Aware Impact Prediction — iTrust'
    '</div>',
    unsafe_allow_html=True,
)

# ── Sidebar navigation ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<p style="font-size:20px;font-weight:700;color:#E6EDF3;margin-bottom:4px;">⚙️ Navigation</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p style="font-size:12px;color:#8B949E;margin-bottom:16px;">Select analysis direction</p>',
        unsafe_allow_html=True,
    )
    mode = st.radio(
        "Analysis Mode",
        ["📋  Requirement → Code", "🔧  Code → Requirement"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.markdown(
        '<p style="font-size:12px;color:#484F58;line-height:1.6;">'
        'Data sources:<br>'
        '• itrust_solution_links.txt<br>'
        '• itrust_method_callgraph.json<br><br>'
        f'<b style="color:#3FB950;">{len(req_to_code)}</b> requirements tracked<br>'
        f'<b style="color:#3FB950;">{len(code_to_req)}</b> code files indexed<br>'
        f'<b style="color:#3FB950;">{len(callgraph):,}</b> methods in call graph'
        '</p>',
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.caption("Powered by Sentence Transformers · XGBoost · TF-IDF")

# ── Route to selected mode ───────────────────────────────────────────────────
if mode == "📋  Requirement → Code":
    mode_r2c.render(req_to_code, callgraph, file_index)
else:
    mode_c2r.render(code_to_req, callgraph, file_index)