"""
ui/code_to_req.py
Code → Requirement mode UI.
BUG FIX: Shows only Java-side impacted methods from call graph.
         Does NOT show fabricated methods for requirement .txt files.
"""
import urllib.parse
import pandas as pd
import streamlit as st
from ui.styles import metric_card, severity_pill
from services.impact_engine import analyze_code_to_req


def render(code_to_req, callgraph, file_index):
    st.markdown('<div class="section-header">🔧 Code Change Impact Analysis</div>', unsafe_allow_html=True)

    # ── Searchable code file selector ────────────────────────────────────
    search = st.text_input(
        "🔍 Search code files",
        placeholder="Type filename (e.g. PatientDAO, AuthDAO, EditPatient)…",
        key="code_search",
    )
    all_codes = sorted(code_to_req.keys())
    filtered = [c for c in all_codes if search.strip().lower() in c.lower()] if search.strip() else all_codes
    if not filtered:
        filtered = all_codes
        st.caption("⚠️ No matches — showing all code files.")

    selected_code = st.selectbox("Select Modified Code File", filtered, key="code_select")

    # ── Analyze button ───────────────────────────────────────────────────
    if st.button("⚡ Analyze Code Impact", key="btn_code_analyze"):
        with st.spinner("Analyzing impact…"):
            result = analyze_code_to_req(selected_code, code_to_req, callgraph)

        # Prominent Inspect Source for the selected file
        st.markdown(
            f'<div style="background:rgba(79,195,247,0.05); border:1px solid rgba(79,195,247,0.2); border-radius:8px; padding:12px; margin-bottom:20px; display:flex; align-items:center; justify-content:space-between;">'
            f'<span style="color:#4FC3F7; font-weight:600;">🔍 Selected: {selected_code}</span>'
            f'<a href="/viewer?type=java&file={urllib.parse.quote(selected_code)}" target="_blank" style="background:#4FC3F7; color:#0D1117; padding:4px 12px; border-radius:4px; text-decoration:none; font-size:13px; font-weight:600;">Inspect Source</a>'
            f'</div>',
            unsafe_allow_html=True
        )

        related_reqs     = result["related_requirements"]
        impacted_methods = result["impacted_methods"]  # Java-side only
        severity         = result["severity"]
        severity_color   = result["severity_color"]

        # ── Metric row ───────────────────────────────────────────────────
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(metric_card(len(related_reqs), "Traced Requirements"), unsafe_allow_html=True)
        with c2:
            st.markdown(metric_card(len(impacted_methods), "Impacted Methods"), unsafe_allow_html=True)
        with c3:
            st.markdown(
                f'<div class="metric-card"><div class="metric-value" style="font-size:22px;padding-top:6px;">'
                f'{severity_pill(severity)}</div><div class="metric-label">Risk Severity</div></div>',
                unsafe_allow_html=True,
            )

        st.markdown('<hr class="cia-divider">', unsafe_allow_html=True)

        # ── Related requirement files with viewer links ───────────────────
        st.markdown('<div class="section-header">📄 Traced Requirement Files</div>', unsafe_allow_html=True)
        if related_reqs:
            for req_file in related_reqs:
                viewer_url = f"/viewer?type=req&file={urllib.parse.quote(req_file)}"
                st.markdown(
                    f'<div class="view-link" style="margin:6px 0;">'
                    f'<a href="{viewer_url}" target="_blank">📄 {req_file}</a></div>',
                    unsafe_allow_html=True,
                )
        else:
            st.info("No requirements traced to this code file.")

        st.markdown('<hr class="cia-divider">', unsafe_allow_html=True)

        # ── Impacted Java methods (call graph — correct semantics) ────────
        st.markdown(
            '<div class="section-header">🔗 Impacted Java Methods'
            '<span style="font-size:12px;color:#8B949E;font-weight:400;margin-left:8px;">'
            '(from call graph)</span></div>',
            unsafe_allow_html=True,
        )
        if impacted_methods:
            # Highlight methods in the viewer when clicking this
            methods_param = urllib.parse.quote(",".join(impacted_methods[:30]))
            st.info(f"The following {len(impacted_methods)} methods are potentially affected by changes in **{selected_code}**.")

            df = pd.DataFrame({"Impacted Method": impacted_methods[:25]})
            st.dataframe(df, use_container_width=True, hide_index=True)
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇ Download as CSV",
                data=csv,
                file_name=f"impact_{selected_code}.csv",
                mime="text/csv",
            )
        else:
            st.info("No impacted methods found via call graph for this file.")
