"""
ui/req_to_code.py
Requirement → Code mode UI.
"""
import urllib.parse
import pandas as pd
import streamlit as st
from ui.styles import metric_card, severity_pill
from services.impact_engine import analyze_req_to_code


def render(req_to_code, callgraph, file_index):
    st.markdown('<div class="section-header">📋 Requirement Impact Analysis</div>', unsafe_allow_html=True)

    # ── Searchable requirement selector ──────────────────────────────────
    search = st.text_input(
        "🔍 Search requirements",
        placeholder="Type UC ID or keyword (e.g. UC1S1, password, allergy)…",
        key="req_search",
    )
    all_reqs = sorted(req_to_code.keys())
    filtered = [r for r in all_reqs if search.strip().lower() in r.lower()] if search.strip() else all_reqs
    if not filtered:
        filtered = all_reqs
        st.caption("⚠️ No matches — showing all requirements.")

    requirement = st.selectbox("Select Changed Requirement", filtered, key="req_select")

    # ── Analyze button ───────────────────────────────────────────────────
    if st.button("⚡ Analyze Impact", key="btn_req_analyze"):
        with st.spinner("Analyzing impact…"):
            result = analyze_req_to_code(requirement, req_to_code, callgraph, file_index)

        # Prominent Inspect Source for the selected requirement
        st.markdown(
            f'<div style="background:rgba(79,195,247,0.05); border:1px solid rgba(79,195,247,0.2); border-radius:8px; padding:12px; margin-bottom:20px; display:flex; align-items:center; justify-content:space-between;">'
            f'<span style="color:#4FC3F7; font-weight:600;">📄 Selected: {requirement}</span>'
            f'<a href="/viewer?type=req&file={urllib.parse.quote(requirement)}" target="_blank" style="background:#4FC3F7; color:#0D1117; padding:4px 12px; border-radius:4px; text-decoration:none; font-size:13px; font-weight:600;">Inspect Document</a>'
            f'</div>',
            unsafe_allow_html=True
        )

        related_codes    = result["related_codes"]
        impacted_methods = result["impacted_methods"]
        code_to_methods  = result["code_to_methods"]
        severity         = result["severity"]
        severity_color   = result["severity_color"]

        # ── Metric row ───────────────────────────────────────────────────
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(metric_card(len(related_codes), "Related Code Files"), unsafe_allow_html=True)
        with c2:
            st.markdown(metric_card(len(impacted_methods), "Impacted Methods"), unsafe_allow_html=True)
        with c3:
            st.markdown(
                f'<div class="metric-card"><div class="metric-value" style="font-size:22px;padding-top:6px;">'
                f'{severity_pill(severity)}</div><div class="metric-label">Risk Severity</div></div>',
                unsafe_allow_html=True,
            )

        st.markdown('<hr class="cia-divider">', unsafe_allow_html=True)

        # ── Related Java files with clickable viewer links ────────────────
        st.markdown('<div class="section-header">📁 Related Code Files</div>', unsafe_allow_html=True)
        if related_codes:
            for fname in related_codes:
                methods_for_file = code_to_methods.get(fname, impacted_methods)
                methods_param = urllib.parse.quote(",".join(methods_for_file[:30]))
                viewer_url = f"/viewer?type=java&file={urllib.parse.quote(fname)}&methods={methods_param}"
                st.markdown(
                    f'<div class="view-link" style="margin:6px 0;">'
                    f'<a href="{viewer_url}" target="_blank">📂 {fname}</a></div>',
                    unsafe_allow_html=True,
                )
        else:
            st.info("No code files linked to this requirement.")

        st.markdown('<hr class="cia-divider">', unsafe_allow_html=True)

        # ── Impacted methods table ────────────────────────────────────────
        st.markdown('<div class="section-header">🔗 Potentially Impacted Methods</div>', unsafe_allow_html=True)
        if impacted_methods:
            df = pd.DataFrame({"Method": impacted_methods[:25]})
            st.dataframe(df, use_container_width=True, hide_index=True)
            # CSV download
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇ Download as CSV",
                data=csv,
                file_name=f"impact_{requirement}.csv",
                mime="text/csv",
            )
        else:
            st.info("No impacted methods found via call graph.")
