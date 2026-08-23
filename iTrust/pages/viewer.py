"""
pages/viewer.py
Streamlined, High-Fidelity Multi-Layer File & Method Viewer for Change Impact Analysis.

Features:
1. Header: Back to Dashboard button, file icon, filename, repository context, download button.
2. Left Panel:
   - Change Impact Context (Trigger, Traceability, ML Score, Dependency Reach, Overall Risk, Rationale).
   - Impacted Methods Navigator (Search, Selectbox, Method details with Line number, Calls & Called By).
3. Right Panel:
   - Code Viewer with Line Numbers and Method Highlighting.
   - Call Graph Matrix Tab.
   - Traced Requirements Tab.
4. Requirement Viewer:
   - Requirement Context & Linked Artifacts on Left.
   - Clean Requirement Document with In-Text Search on Right.
5. Zero native sidebar, zero empty boxes, zero raw HTML leaks, full horizontal space utilization.
"""

import sys
import re
import html
import urllib.parse
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Allow imports from project root
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import streamlit as st
import pandas as pd
from services.data_loader import (
    build_file_index,
    load_callgraph,
    load_traceability_links,
    load_all_requirements
)
from services.impact_engine import compute_dependency_reach, evaluate_overall_impact_risk
from services.github_service import (
    parse_repository,
    get_file_content as get_gh_file_content,
    GitHubAPIError
)
from services.github_impact_engine import extract_methods_for_file, detect_language
from ui.styles import inject_styles, severity_pill

# ── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Artifact & Method Impact Viewer — CIA System",
    layout="wide",
    initial_sidebar_state="collapsed"
)

inject_styles()

# ── Custom CSS for Viewer (Full Width, No Native Sidebar) ───────────────────
st.markdown("""
<style>
/* ── Completely Hide Native Streamlit Sidebar & Collapse/Expand Toggle ─── */
[data-testid="stSidebar"],
section[data-testid="stSidebar"],
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarNavCollapseButton"],
[data-testid="stSidebarNav"],
button[data-testid="stSidebarCollapseButton"],
button[kind="header"],
div[data-testid="collapsedControl"] {
    display: none !important;
    visibility: hidden !important;
    width: 0px !important;
    height: 0px !important;
    min-width: 0px !important;
    max-width: 0px !important;
    margin: 0 !important;
    padding: 0 !important;
    opacity: 0 !important;
    pointer-events: none !important;
    position: absolute !important;
    left: -9999px !important;
}

/* ── Expand Main App Content to True Full Browser Width ─────────────────── */
.main,
.main .block-container,
[data-testid="block-container"],
[data-testid="stMainBlockContainer"],
[data-testid="stAppViewBlockContainer"] {
    max-width: 100% !important;
    width: 100% !important;
    padding-top: 1rem !important;
    padding-left: 1.5rem !important;
    padding-right: 1.5rem !important;
    padding-bottom: 2rem !important;
    margin-left: 0 !important;
    margin-right: 0 !important;
}

[data-testid="stHeader"] {
    background: transparent !important;
    height: 0 !important;
    min-height: 0 !important;
}

/* Header banner */
.viewer-top-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 16px;
    background: var(--cia-surface);
    border: 1px solid var(--cia-border);
    border-radius: 8px;
    margin-bottom: 16px;
    box-shadow: 0 2px 5px var(--cia-shadow);
}
.viewer-file-title {
    font-family: 'JetBrains Mono', monospace;
    font-size: 18px;
    font-weight: 700;
    color: var(--cia-accent);
}
.viewer-sub-badge {
    font-size: 11px;
    color: var(--cia-text-faint);
    background: var(--cia-surface2);
    border: 1px solid var(--cia-border);
    padding: 2px 8px;
    border-radius: 10px;
    font-weight: 500;
    margin-left: 6px;
}

/* Left Impact Panel Card */
.impact-card-box {
    background: var(--cia-card-bg);
    border: 1px solid var(--cia-border);
    border-radius: 8px;
    padding: 14px 16px;
    margin-bottom: 14px;
    box-shadow: 0 2px 5px var(--cia-shadow);
}
.impact-card-title {
    font-size: 12px;
    text-transform: uppercase;
    font-weight: 700;
    color: var(--cia-text-faint);
    letter-spacing: 0.5px;
    margin-bottom: 10px;
    border-bottom: 1px solid var(--cia-border);
    padding-bottom: 4px;
    display: flex;
    align-items: center;
    gap: 6px;
}
.impact-field {
    margin-bottom: 10px;
}
.impact-field:last-child {
    margin-bottom: 0;
}
.impact-label {
    font-size: 11px;
    text-transform: uppercase;
    color: var(--cia-text-faint);
    font-weight: 600;
    margin-bottom: 2px;
}
.impact-val {
    font-size: 13px;
    font-weight: 600;
    color: var(--cia-text);
}

/* Selected Method Detail Box */
.selected-method-box {
    background: var(--cia-surface2);
    border: 1px solid var(--cia-border);
    border-left: 3px solid var(--cia-accent);
    border-radius: 6px;
    padding: 10px 12px;
    margin-top: 10px;
    font-size: 12px;
    line-height: 1.5;
}

/* Code container table */
.code-container {
    background: var(--cia-card-bg);
    border: 1px solid var(--cia-border);
    border-radius: 8px;
    overflow-x: auto;
    max-height: 740px;
    overflow-y: auto;
    font-family: 'JetBrains Mono', Consolas, monospace;
    font-size: 13px;
    line-height: 1.6;
}
.code-table {
    width: 100%;
    border-collapse: collapse;
}
.code-table tr:hover td {
    background: rgba(88,166,255,0.06);
}
.line-num {
    width: 48px;
    text-align: right;
    padding: 0 10px;
    color: var(--cia-text-faint);
    user-select: none;
    border-right: 1px solid var(--cia-border);
    background: var(--cia-surface2);
    font-size: 11px;
    vertical-align: top;
}
.line-code {
    padding-left: 12px;
    white-space: pre-wrap;
    word-break: break-all;
    color: var(--cia-text);
}
.line-highlight {
    background: rgba(248,81,73,0.12) !important;
    border-left: 4px solid var(--cia-high);
}
.line-highlight .line-num {
    color: var(--cia-high) !important;
    font-weight: 700;
    background: rgba(248,81,73,0.18) !important;
}
.line-highlight-active {
    background: rgba(9,105,218,0.18) !important;
    border-left: 4px solid var(--cia-accent);
}
.line-highlight-active .line-num {
    color: var(--cia-accent) !important;
    font-weight: 700;
    background: rgba(9,105,218,0.22) !important;
}
</style>
""", unsafe_allow_html=True)

# ── 1. Query Parameter Management & State Preservation ──────────────────────
qp = st.query_params

if qp.get("file"):
    st.session_state["v_filename"] = qp.get("file", "")
    st.session_state["v_type"] = qp.get("type", "java")
    st.session_state["v_repo"] = qp.get("repo", "")
    st.session_state["v_branch"] = qp.get("branch", "main")
    st.session_state["v_lines"] = qp.get("lines", "")
    st.session_state["v_req"] = qp.get("req", "")
    st.session_state["v_code"] = qp.get("code", "")
    st.session_state["v_score"] = qp.get("score", "")
    st.session_state["v_verified"] = qp.get("verified", "")
    st.session_state["v_risk"] = qp.get("risk", "")
    st.session_state["v_dep"] = qp.get("dep", "")
    st.session_state["v_methods"] = qp.get("methods", "")

filename = st.session_state.get("v_filename", "")
v_type = st.session_state.get("v_type", "java")
gh_repo = st.session_state.get("v_repo", "")
gh_branch = st.session_state.get("v_branch", "main")
gh_lines_raw = st.session_state.get("v_lines", "")
req_trigger = st.session_state.get("v_req", "")
code_trigger = st.session_state.get("v_code", "")
score_param = st.session_state.get("v_score", "")
verified_param = st.session_state.get("v_verified", "")
risk_param = st.session_state.get("v_risk", "")
dep_param = st.session_state.get("v_dep", "")
methods_raw = st.session_state.get("v_methods", "")

if not filename:
    st.info("⚠️ No file specified. Please open this viewer by clicking **'Inspect Source'** from the main CIA dashboard.")
    st.markdown('<a href="/" target="_self" style="display:inline-block; margin-top:10px; background:var(--cia-accent); color:#fff; padding:6px 16px; border-radius:6px; text-decoration:none; font-weight:600;">⬅ Back to Impact Dashboard</a>', unsafe_allow_html=True)
    st.stop()

filename = urllib.parse.unquote(filename)
gh_repo = urllib.parse.unquote(gh_repo) if gh_repo else ""
gh_branch = urllib.parse.unquote(gh_branch) if gh_branch else "main"
req_trigger = urllib.parse.unquote(req_trigger) if req_trigger else ""
code_trigger = urllib.parse.unquote(code_trigger) if code_trigger else ""

# Load Knowledge Base Data
file_index = build_file_index()
callgraph = load_callgraph()
req_to_code, code_to_req = load_traceability_links()
all_req_texts = load_all_requirements()

# Parse Impacted Methods from query param
impacted_methods_list = []
if methods_raw:
    unquoted = urllib.parse.unquote(methods_raw)
    impacted_methods_list = [m.strip() for m in unquoted.split(",") if m.strip()]

# ── 2. Top Header Navigation ─────────────────────────────────────────────────
if v_type == "github":
    file_icon = "☕" if filename.endswith(".java") else "🐍" if filename.endswith(".py") else "📄"
    file_badge = f"GitHub · {html.escape(gh_repo)} ({html.escape(gh_branch)})" if gh_repo else "GitHub Remote File"
elif v_type == "java":
    file_icon = "📂"
    file_badge = "Java Source Code · iTrust Repository"
else:
    file_icon = "📄"
    file_badge = "Software Requirement Document · iTrust"

c_head_left, c_head_right = st.columns([3, 1])
with c_head_left:
    header_html = (
        f'<div style="display:flex; align-items:center; gap:12px; margin-bottom:8px;">'
        f'<a href="/" target="_self" style="background:var(--cia-surface2); color:var(--cia-text); border:1px solid var(--cia-border); padding:5px 12px; border-radius:6px; text-decoration:none; font-size:12px; font-weight:600;">⬅ Back to Impact Analysis</a>'
        f'<span style="font-size:20px;">{file_icon}</span>'
        f'<span class="viewer-file-title">{html.escape(filename.split("/")[-1])}</span>'
        f'<span class="viewer-sub-badge">{file_badge}</span>'
        f'</div>'
    )
    st.markdown(header_html, unsafe_allow_html=True)


# ── Helper: Locate Method Definition in Source Lines ─────────────────────────
def find_method_definition_line(lines_list: List[str], method_signature: str) -> Tuple[Optional[int], str]:
    """Finds the most accurate line where a method is declared in Java source."""
    bare_name = method_signature.split(".")[-1].split("(")[0].strip()
    
    # Check definition with access modifier
    def_pattern = re.compile(r'\b(public|private|protected|static|synchronized|final)\s+[\w\<\>\[\]]+\s+' + re.escape(bare_name) + r'\s*\(')
    for idx, line in enumerate(lines_list, 1):
        if def_pattern.search(line):
            return idx, line.strip()

    # Fallback to any line with methodName(
    call_pattern = re.compile(r'\b' + re.escape(bare_name) + r'\s*\(')
    for idx, line in enumerate(lines_list, 1):
        if call_pattern.search(line):
            return idx, line.strip()

    return None, ""


# ── 3. Handle Java Source File View ───────────────────────────────────────────
if v_type == "java":
    file_path = file_index.get(filename)
    if not file_path or not Path(file_path).exists():
        st.error(f"Source file `{filename}` was not found in the project `code/` directory.")
        st.stop()

    source_code = Path(file_path).read_text(encoding="utf-8", errors="replace")
    class_name = filename.replace(".java", "")
    lines = source_code.splitlines()

    with c_head_right:
        st.download_button(
            "⬇ Download Source",
            source_code,
            file_name=filename,
            mime="text/plain",
            use_container_width=True
        )

    # Resolve class methods from callgraph
    class_methods = [m for m in callgraph if callgraph[m].get("class_name") == class_name]
    
    # If no methods were passed in query params, fallback to all class methods in callgraph
    if not impacted_methods_list:
        impacted_methods_list = class_methods

    # Map all method signatures to line numbers
    method_lines_map = {}
    for m in impacted_methods_list:
        l_no, _ = find_method_definition_line(lines, m)
        if l_no:
            method_lines_map[m] = l_no

    # Resolve context metrics (with fallback calculation if opened directly)
    is_verified = (verified_param == "1") or (filename in req_to_code.get(req_trigger, []))
    
    # ML Score resolution
    ml_score_val = None
    if score_param:
        try:
            ml_score_val = float(score_param) * 100.0
        except ValueError:
            ml_score_val = None

    # Dependency Reach resolution
    dep_count = len(impacted_methods_list)
    dep_reach, dep_badge = compute_dependency_reach(dep_count)
    if dep_param:
        dep_reach = dep_param.upper()
        dep_badge = {"HIGH": "🔴", "MEDIUM": "🟠", "LOW": "🟢", "NONE": "⚪"}.get(dep_reach, "🟢")

    # Overall Risk resolution
    if risk_param:
        overall_risk_tier = risk_param.upper()
    else:
        score_dec = (ml_score_val / 100.0) if ml_score_val is not None else 0.50
        overall_risk_tier, _, _ = evaluate_overall_impact_risk(is_verified, score_dec, dep_count)

    # Risk Rationale resolution
    if is_verified and dep_reach in ["HIGH", "MEDIUM"]:
        rationale_text = f"Verified Traceability Link + {dep_reach} Dependency Reach ({dep_count} methods)"
    elif is_verified:
        rationale_text = f"Verified Traceability Link + Localized Reach ({dep_count} methods)"
    elif ml_score_val is not None and ml_score_val >= 70.0 and dep_reach == "HIGH":
        rationale_text = f"High ML Relationship Score ({ml_score_val:.1f}%) + High Dependency Reach ({dep_count} methods)"
    elif ml_score_val is not None and ml_score_val >= 70.0:
        rationale_text = f"High ML Relationship Score ({ml_score_val:.1f}%) + {dep_reach} Reach"
    elif ml_score_val is not None and ml_score_val >= 40.0 and dep_reach == "HIGH":
        rationale_text = f"Moderate ML Score ({ml_score_val:.1f}%) + High Dependency Reach ({dep_count} methods)"
    elif ml_score_val is not None:
        rationale_text = f"Moderate ML Score ({ml_score_val:.1f}%) with Localized Scope"
    else:
        rationale_text = f"Class-level static analysis ({dep_count} methods identified in call graph)"

    # ── Two-Column Layout: Left (3.2) + Right (6.8) ──────────────────────────
    col_panel, col_code = st.columns([3.2, 6.8])

    # ── LEFT PANEL: Change Impact Context & Navigator ─────────────────────────
    with col_panel:
        # 1. CHANGE IMPACT CONTEXT (Single complete HTML card - No leading indentation)
        trigger_row = ""
        if req_trigger:
            trigger_row = (
                f'<div class="impact-field">'
                f'<div class="impact-label">Triggered by Requirement</div>'
                f'<div class="impact-val" style="color:var(--cia-accent);">{html.escape(req_trigger)}</div>'
                f'</div>'
            )

        trace_badge_html = '<span class="badge-verified">✓ Verified Traceability</span>' if is_verified else '<span class="badge-unverified">⚡ ML Predicted Candidate</span>'

        ml_score_row = ""
        if ml_score_val is not None:
            ml_score_row = (
                f'<div class="impact-field">'
                f'<div class="impact-label">ML Relationship Score</div>'
                f'<div class="impact-val" style="color:var(--cia-accent);">{ml_score_val:.2f}%</div>'
                f'<div class="score-bar-bg" style="margin-top:3px;">'
                f'<div class="score-bar-fill" style="width:{min(max(ml_score_val, 5), 100):.1f}%;"></div>'
                f'</div>'
                f'</div>'
            )

        context_card_html = (
            f'<div class="impact-card-box">'
            f'<div class="impact-card-title">📊 Change Impact Context</div>'
            f'{trigger_row}'
            f'<div class="impact-field">'
            f'<div class="impact-label">Traceability Evidence</div>'
            f'<div style="margin-top:2px;">{trace_badge_html}</div>'
            f'</div>'
            f'{ml_score_row}'
            f'<div class="impact-field">'
            f'<div class="impact-label">Dependency Reach</div>'
            f'<div class="impact-val">{dep_badge} {dep_reach} ({dep_count} methods)</div>'
            f'</div>'
            f'<div class="impact-field">'
            f'<div class="impact-label">Overall Impact Risk</div>'
            f'<div style="margin-top:3px;">{severity_pill(overall_risk_tier)}</div>'
            f'</div>'
            f'<div class="impact-field" style="border-top:1px dashed var(--cia-border); padding-top:6px; margin-top:6px;">'
            f'<div class="impact-label">Risk Rationale</div>'
            f'<div style="font-size:12px; color:var(--cia-text-muted); line-height:1.4;">{html.escape(rationale_text)}</div>'
            f'</div>'
            f'</div>'
        )
        st.markdown(context_card_html, unsafe_allow_html=True)

        # 2. IMPACTED METHODS NAVIGATOR
        st.markdown(
            (
                f'<div style="font-size:12px; text-transform:uppercase; font-weight:700; color:var(--cia-text-faint); letter-spacing:0.5px; margin-bottom:8px; display:flex; align-items:center; gap:6px;">'
                f'🔗 Impacted Methods Navigator ({len(impacted_methods_list)})'
                f'</div>'
            ),
            unsafe_allow_html=True
        )

        method_search = st.text_input(
            "Method search",
            placeholder="Search method name…",
            key="method_search_box",
            label_visibility="collapsed"
        )

        filtered_methods = [
            m for m in impacted_methods_list
            if method_search.lower() in m.lower()
        ] if method_search else impacted_methods_list

        selected_method = None
        if filtered_methods:
            options = ["Show all impacted methods"] + filtered_methods
            selected_option = st.selectbox(
                "Select method to inspect:",
                options,
                key="method_selectbox",
                label_visibility="collapsed"
            )
            if selected_option != "Show all impacted methods":
                selected_method = selected_option
        else:
            st.caption("No methods match search.")

        # Selected Method Detail Box (Only shown when a method is explicitly selected)
        if selected_method:
            line_no = method_lines_map.get(selected_method)
            meta = callgraph.get(selected_method, {})
            calls_list = meta.get("calls", [])
            called_by_list = meta.get("called_by", [])
            
            bare_name = selected_method.split(".")[-1]
            line_str = f"📍 Line: {line_no}" if line_no else "📍 Line: (inside method body)"

            selected_method_html = (
                f'<div class="selected-method-box">'
                f'<div style="font-weight:700; color:var(--cia-accent); margin-bottom:4px; font-family:\'JetBrains Mono\',monospace;">'
                f'{html.escape(bare_name)}'
                f'</div>'
                f'<div style="font-size:11px; color:var(--cia-text-faint); margin-bottom:4px;">'
                f'{line_str}'
                f'</div>'
                f'<div style="font-size:11px; color:var(--cia-text-muted);">'
                f'<b>→ Calls ({len(calls_list)}):</b> {html.escape(", ".join([c.split(".")[-1] for c in calls_list[:3]])) if calls_list else "None"}<br>'
                f'<b>← Called by ({len(called_by_list)}):</b> {html.escape(", ".join([c.split(".")[-1] for c in called_by_list[:3]])) if called_by_list else "None"}'
                f'</div>'
                f'</div>'
            )
            st.markdown(selected_method_html, unsafe_allow_html=True)

    # ── RIGHT AREA: Source Code Viewer & Analysis Tabs ────────────────────────
    with col_code:
        tab_code, tab_graph, tab_trace = st.tabs([
            f"💻 Source Code ({len(lines)} lines)",
            f"🔗 Call Graph Matrix ({len(class_methods)} methods)",
            f"📋 Linked Requirements ({len(code_to_req.get(filename, []))})"
        ])

        with tab_code:
            c_s1, c_s2 = st.columns([3, 2])
            with c_s1:
                kw_search = st.text_input("Search in code", placeholder="Search in source code (e.g. SQL, variable, method)…", key="code_kw_box", label_visibility="collapsed")
            with c_s2:
                st.caption(f"**{len(lines)} lines** · {len(method_lines_map)} impacted method markers")

            all_impacted_lines = set(method_lines_map.values())
            active_line = method_lines_map.get(selected_method) if selected_method else None

            rows_html = []
            for line_idx, line_str in enumerate(lines, 1):
                escaped_line = html.escape(line_str) if line_str else "&nbsp;"

                if kw_search and kw_search.strip():
                    escaped_kw = html.escape(kw_search.strip())
                    escaped_line = re.sub(
                        f"({re.escape(escaped_kw)})",
                        r'<mark style="background:rgba(255,220,0,0.35); color:inherit; border-radius:2px; padding:0 2px;">\1</mark>',
                        escaped_line,
                        flags=re.IGNORECASE
                    )

                row_cls = ""
                if active_line and line_idx == active_line:
                    row_cls = "line-highlight-active"
                elif line_idx in all_impacted_lines:
                    row_cls = "line-highlight"

                rows_html.append(
                    f'<tr class="{row_cls}">'
                    f'<td class="line-num">{line_idx}</td>'
                    f'<td class="line-code">{escaped_line}</td>'
                    f'</tr>'
                )

            table_content = "".join(rows_html)
            code_html = f'<div class="code-container"><table class="code-table">{table_content}</table></div>'
            st.markdown(code_html, unsafe_allow_html=True)

        with tab_graph:
            st.markdown('<div class="section-header">🔗 Class Method Call Graph Matrix</div>', unsafe_allow_html=True)
            if class_methods:
                graph_rows = []
                for m in class_methods:
                    meta = callgraph.get(m, {})
                    is_impacted = m in impacted_methods_list
                    graph_rows.append({
                        "Method Signature": m,
                        "Impacted Status": "🔴 IMPACTED" if is_impacted else "⚪ Clean",
                        "Outgoing Calls": len(meta.get("calls", [])),
                        "Incoming Callers": len(meta.get("called_by", []))
                    })
                df_graph = pd.DataFrame(graph_rows)
                st.dataframe(df_graph, use_container_width=True, hide_index=True)
            else:
                st.info(f"No direct method entries registered in call graph for class `{class_name}`.")

        with tab_trace:
            st.markdown('<div class="section-header">📄 Ground-Truth Traced Requirements</div>', unsafe_allow_html=True)
            linked_reqs = code_to_req.get(filename, [])
            if linked_reqs:
                st.caption(f"{len(linked_reqs)} requirement documents are traced to `{filename}` in the iTrust answer matrix:")
                for r_name in linked_reqs:
                    req_viewer_url = f"/viewer?type=req&file={urllib.parse.quote(r_name)}&code={urllib.parse.quote(filename)}"
                    st.markdown(
                        f'<div class="view-link" style="margin:6px 0;">'
                        f'<a href="{req_viewer_url}">📄 {r_name} &nbsp; <span style="font-size:11px; color:#3FB950;">(Verified Link)</span></a>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
            else:
                st.info(f"No verified requirement links recorded for `{filename}` in the ground truth dataset.")

# ── 4. Handle Requirement Document View ───────────────────────────────────────
elif v_type == "req":
    req_path = BASE_DIR / "req" / filename
    if not req_path.exists():
        st.error(f"Requirement file `{filename}` was not found in the `req/` directory.")
        st.stop()

    content = req_path.read_text(encoding="utf-8", errors="replace")

    with c_head_right:
        st.download_button(
            "⬇ Download Requirement",
            content,
            file_name=filename,
            mime="text/plain",
            use_container_width=True
        )

    linked_codes = req_to_code.get(filename, [])

    # Resolve context metrics for requirement
    is_verified = (verified_param == "1") or (filename in code_to_req.get(code_trigger, []))
    
    ml_score_val = None
    if score_param:
        try:
            ml_score_val = float(score_param) * 100.0
        except ValueError:
            ml_score_val = None

    overall_risk_tier = risk_param.upper() if risk_param else ("HIGH" if len(linked_codes) > 3 else "MEDIUM" if len(linked_codes) > 0 else "LOW")

    if is_verified and len(linked_codes) > 3:
        rationale_text = f"Verified Traceability Link + High Linked Artifact Count ({len(linked_codes)} files)"
    elif is_verified:
        rationale_text = f"Verified Traceability Link + Localized Reach ({len(linked_codes)} files)"
    elif ml_score_val is not None:
        rationale_text = f"ML Relationship Score: {ml_score_val:.1f}%"
    else:
        rationale_text = f"Requirement document with {len(linked_codes)} linked code files"

    # ── Two-Column Layout ─────────────────────────────────────────────────────
    col_panel, col_content = st.columns([3.2, 6.8])

    with col_panel:
        # REQUIREMENT CONTEXT (Single complete HTML card - No leading indentation)
        trigger_row = ""
        if code_trigger:
            trigger_row = (
                f'<div class="impact-field">'
                f'<div class="impact-label">Triggered by Code File</div>'
                f'<div class="impact-val" style="color:var(--cia-accent);">{html.escape(code_trigger)}</div>'
                f'</div>'
            )

        trace_badge_html = '<span class="badge-verified">✓ Verified Traceability</span>' if is_verified else '<span class="badge-unverified">⚡ ML Predicted Candidate</span>'

        ml_score_row = ""
        if ml_score_val is not None:
            ml_score_row = (
                f'<div class="impact-field">'
                f'<div class="impact-label">ML Relationship Score</div>'
                f'<div class="impact-val" style="color:var(--cia-accent);">{ml_score_val:.2f}%</div>'
                f'<div class="score-bar-bg" style="margin-top:3px;">'
                f'<div class="score-bar-fill" style="width:{min(max(ml_score_val, 5), 100):.1f}%;"></div>'
                f'</div>'
                f'</div>'
            )

        req_card_html = (
            f'<div class="impact-card-box">'
            f'<div class="impact-card-title">📊 Requirement Context</div>'
            f'{trigger_row}'
            f'<div class="impact-field">'
            f'<div class="impact-label">Traceability Evidence</div>'
            f'<div style="margin-top:2px;">{trace_badge_html}</div>'
            f'</div>'
            f'{ml_score_row}'
            f'<div class="impact-field">'
            f'<div class="impact-label">Linked Code Artifacts</div>'
            f'<div class="impact-val">{len(linked_codes)} verified code files</div>'
            f'</div>'
            f'<div class="impact-field">'
            f'<div class="impact-label">Overall Impact Risk</div>'
            f'<div style="margin-top:3px;">{severity_pill(overall_risk_tier)}</div>'
            f'</div>'
            f'<div class="impact-field" style="border-top:1px dashed var(--cia-border); padding-top:6px; margin-top:6px;">'
            f'<div class="impact-label">Risk Rationale</div>'
            f'<div style="font-size:12px; color:var(--cia-text-muted); line-height:1.4;">{html.escape(rationale_text)}</div>'
            f'</div>'
            f'</div>'
        )
        st.markdown(req_card_html, unsafe_allow_html=True)

        # DOCUMENT SEARCH (Single clean search box)
        st.markdown(
            (
                f'<div style="font-size:12px; text-transform:uppercase; font-weight:700; color:var(--cia-text-faint); letter-spacing:0.5px; margin-bottom:8px;">'
                f'🔍 Document Search'
                f'</div>'
            ),
            unsafe_allow_html=True
        )
        req_kw = st.text_input(
            "Highlight keyword",
            placeholder="Search keywords in requirement…",
            key="req_kw_box",
            label_visibility="collapsed"
        )

    with col_content:
        tab_text, tab_linked = st.tabs([
            "📄 Requirement Document Content",
            f"📁 Linked Code Artifacts ({len(linked_codes)})"
        ])

        with tab_text:
            disp_content = html.escape(content)
            if req_kw and req_kw.strip():
                escaped_kw = html.escape(req_kw.strip())
                disp_content = re.sub(
                    f"({re.escape(escaped_kw)})",
                    r'<mark style="background:rgba(255,220,0,0.35); color:inherit; border-radius:3px; padding:0 3px;">\1</mark>',
                    disp_content,
                    flags=re.IGNORECASE
                )

            doc_html = (
                f'<div style="background:var(--cia-surface); border:1px solid var(--cia-border); border-radius:8px; padding:20px 24px; line-height:1.8; white-space:pre-wrap; font-size:14px; color:var(--cia-text); box-shadow:0 2px 5px var(--cia-shadow);">'
                f'{disp_content}'
                f'</div>'
            )
            st.markdown(doc_html, unsafe_allow_html=True)

        with tab_linked:
            st.markdown('<div class="section-header">📁 Ground-Truth Traced Code Files</div>', unsafe_allow_html=True)
            if linked_codes:
                st.caption(f"{len(linked_codes)} Java source files are verified in the iTrust solution links for this requirement:")
                for c_name in linked_codes:
                    java_viewer_url = f"/viewer?type=java&file={urllib.parse.quote(c_name)}&req={urllib.parse.quote(filename)}"
                    st.markdown(
                        f'<div class="view-link" style="margin:6px 0;">'
                        f'<a href="{java_viewer_url}">📂 {c_name} &nbsp; <span style="font-size:11px; color:#3FB950;">(Verified Link)</span></a>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
            else:
                st.info("No verified code files linked to this requirement in dataset.")

# ── 5. Handle GitHub Remote File View ─────────────────────────────────────────
elif v_type == "github":
    token = st.session_state.get("gh_shared_token") or st.session_state.get("gh_token") or st.session_state.get("gh_pred_token") or st.session_state.get("gh_post_token")

    # Resolve owner and repo dynamically
    owner, repo_name = parse_repository(gh_repo) if gh_repo else (None, None)
    if not owner or not repo_name:
        if "/" in gh_repo:
            parts = gh_repo.split("/")
            owner, repo_name = parts[0], parts[1]
        else:
            st.error("❌ No valid repository specified. Please navigate from the Repository Analysis dashboard.")
            st.markdown('<a href="/" target="_self" style="display:inline-block; margin-top:10px; background:var(--cia-accent); color:#fff; padding:6px 16px; border-radius:6px; text-decoration:none; font-weight:600;">⬅ Back to Dashboard</a>', unsafe_allow_html=True)
            st.stop()

    # Fetch remote file content
    try:
        source_code = get_gh_file_content(owner, repo_name, filename, ref=gh_branch, token=token)
    except GitHubAPIError as e:
        st.error(f"❌ Could not fetch GitHub file `{filename}` from `{owner}/{repo_name}`: {str(e)}")
        st.markdown('<a href="/" target="_self" style="display:inline-block; margin-top:10px; background:var(--cia-accent); color:#fff; padding:6px 16px; border-radius:6px; text-decoration:none; font-weight:600;">⬅ Back to Dashboard</a>', unsafe_allow_html=True)
        st.stop()
    except Exception as e:
        st.error(f"❌ Error fetching file: {str(e)}")
        st.stop()

    if not source_code:
        st.warning(f"File `{filename}` is empty or could not be decoded.")
        st.stop()

    lines = source_code.splitlines()
    basename = filename.split("/")[-1]
    detected_lang = detect_language(basename)

    with c_head_right:
        st.download_button(
            "⬇ Download Source",
            source_code,
            file_name=basename,
            mime="text/plain",
            use_container_width=True
        )

    # Extract declared methods / functions across languages
    methods = extract_methods_for_file(source_code, filename)
    method_lines_map = {}
    for m in methods:
        method_lines_map[m["name"]] = m["line"]

    # Parse changed lines from diff if present
    changed_lines_set = set()
    if gh_lines_raw:
        try:
            for part in urllib.parse.unquote(gh_lines_raw).split(","):
                part_clean = part.strip()
                if part_clean.isdigit():
                    changed_lines_set.add(int(part_clean))
        except Exception:
            pass

    # ── Two-Column Layout ─────────────────────────────────────────────────────
    col_panel, col_code = st.columns([3.2, 6.8])

    with col_panel:
        # GITHUB FILE CONTEXT CARD
        diff_info_row = ""
        if changed_lines_set:
            diff_info_row = (
                f'<div class="impact-field">'
                f'<div class="impact-label">Changed Lines (Diff)</div>'
                f'<div class="impact-val" style="color:var(--cia-high); font-weight:700;">'
                f'📍 {len(changed_lines_set)} lines modified in commit'
                f'</div>'
                f'</div>'
            )

        gh_card_html = (
            f'<div class="impact-card-box">'
            f'<div class="impact-card-title">🐙 GitHub Remote Context</div>'
            f'<div class="impact-field">'
            f'<div class="impact-label">Repository</div>'
            f'<div class="impact-val" style="color:var(--cia-accent); font-weight:600;">{html.escape(owner)}/{html.escape(repo_name)}</div>'
            f'</div>'
            f'<div class="impact-field">'
            f'<div class="impact-label">Branch / Commit Ref</div>'
            f'<div class="impact-val"><code style="font-size:12px;">{html.escape(gh_branch)}</code></div>'
            f'</div>'
            f'<div class="impact-field">'
            f'<div class="impact-label">File Path</div>'
            f'<div class="impact-val" style="font-size:12px; word-break:break-all;">{html.escape(filename)}</div>'
            f'</div>'
            f'<div class="impact-field">'
            f'<div class="impact-label">File Stats & Language</div>'
            f'<div class="impact-val">{html.escape(detected_lang)} · {len(lines)} lines · {len(methods)} structures/functions</div>'
            f'</div>'
            f'{diff_info_row}'
            f'<div class="impact-field" style="border-top:1px dashed var(--cia-border); padding-top:6px; margin-top:6px;">'
            f'<div class="impact-label">Traceability Status</div>'
            f'<div style="font-size:12px; color:var(--cia-text-faint);">⚠️ External Repository (No ground truth)</div>'
            f'</div>'
            f'</div>'
        )
        st.markdown(gh_card_html, unsafe_allow_html=True)

        # METHOD NAVIGATOR (If methods exist)
        selected_method = None
        if methods:
            st.markdown(
                (
                    f'<div style="font-size:12px; text-transform:uppercase; font-weight:700; color:var(--cia-text-faint); letter-spacing:0.5px; margin-bottom:8px; display:flex; align-items:center; gap:6px;">'
                    f'🔗 Methods Navigator ({len(methods)})'
                    f'</div>'
                ),
                unsafe_allow_html=True
            )

            method_search = st.text_input(
                "Search methods",
                placeholder="Filter methods…",
                key="gh_method_search",
                label_visibility="collapsed"
            )

            method_names = [m["name"] for m in methods]
            filtered_methods = [
                m for m in method_names
                if method_search.lower() in m.lower()
            ] if method_search else method_names

            if filtered_methods:
                options = ["Show all methods"] + filtered_methods
                selected_option = st.selectbox(
                    "Select method to inspect:",
                    options,
                    key="gh_method_select",
                    label_visibility="collapsed"
                )
                if selected_option != "Show all methods":
                    selected_method = selected_option
            else:
                st.caption("No methods match search.")

            if selected_method:
                line_no = method_lines_map.get(selected_method)
                sig_match = next((m["signature"] for m in methods if m["name"] == selected_method), selected_method)
                line_str = f"📍 Line {line_no}" if line_no else "📍 Line: (body)"
                st.markdown(
                    f'<div class="selected-method-box">'
                    f'<div style="font-weight:700; color:var(--cia-accent); font-family:\'JetBrains Mono\',monospace;">{html.escape(sig_match)}</div>'
                    f'<div style="font-size:11px; color:var(--cia-text-faint); margin-top:2px;">{line_str}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

    # ── RIGHT AREA: Code Viewer ───────────────────────────────────────────────
    with col_code:
        tab_code, tab_methods = st.tabs([
            f"💻 Source Code ({len(lines)} lines)",
            f"📋 Declared Methods ({len(methods)})"
        ])

        with tab_code:
            c_s1, c_s2 = st.columns([3, 2])
            with c_s1:
                kw_search = st.text_input(
                    "Search in code",
                    placeholder="Search in source code…",
                    key="gh_code_kw",
                    label_visibility="collapsed"
                )
            with c_s2:
                diff_tag = f" · <b style='color:var(--cia-high);'>{len(changed_lines_set)} changed lines</b>" if changed_lines_set else ""
                st.markdown(
                    f"<div style='font-size:12px; color:var(--cia-text-muted); padding-top:6px;'>"
                    f"<b>{len(lines)} lines</b>{diff_tag}"
                    f"</div>",
                    unsafe_allow_html=True
                )

            active_line = method_lines_map.get(selected_method) if selected_method else None

            rows_html = []
            for line_idx, line_str in enumerate(lines, 1):
                escaped_line = html.escape(line_str) if line_str else "&nbsp;"

                if kw_search and kw_search.strip():
                    escaped_kw = html.escape(kw_search.strip())
                    escaped_line = re.sub(
                        f"({re.escape(escaped_kw)})",
                        r'<mark style="background:rgba(255,220,0,0.35); color:inherit; border-radius:2px; padding:0 2px;">\1</mark>',
                        escaped_line,
                        flags=re.IGNORECASE
                    )

                is_active = (active_line == line_idx)
                is_changed = (line_idx in changed_lines_set)

                if is_active:
                    row_cls = "code-row line-highlight-active"
                elif is_changed:
                    row_cls = "code-row line-highlight"
                else:
                    row_cls = "code-row"

                rows_html.append(
                    f'<tr class="{row_cls}">'
                    f'<td class="line-num">{line_idx}</td>'
                    f'<td class="line-code">{escaped_line}</td>'
                    f'</tr>'
                )

            code_table_html = (
                f'<div class="code-container">'
                f'<table class="code-table">'
                f'<tbody>'
                f'{"".join(rows_html)}'
                f'</tbody>'
                f'</table>'
                f'</div>'
            )
            st.markdown(code_table_html, unsafe_allow_html=True)

        with tab_methods:
            if methods:
                st.caption(f"{len(methods)} declared methods detected in `{basename}`:")
                methods_df = pd.DataFrame([
                    {"Line": m["line"], "Return Type": m["return_type"], "Method Signature": m["signature"]}
                    for m in methods
                ])
                st.dataframe(methods_df, use_container_width=True, hide_index=True)
            else:
                st.info("No method declarations detected.")

