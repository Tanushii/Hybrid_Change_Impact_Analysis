"""
ui/code_to_req.py
Code → Requirement Mode UI.
Displays 3-layer hybrid impact analysis with ML Relationship Scores,
Traceability Evidence, Dependency Reach, and Overall Risk.
"""
import urllib.parse
import pandas as pd
import streamlit as st
from ui.styles import metric_card, severity_pill, render_artifact_card, render_artifact_card_native
from services.impact_engine import analyze_code_to_req


def render(code_to_req, callgraph, file_index, all_req_texts=None, all_code_texts=None):
    st.markdown('<div class="section-header">🔧 Code Change Impact Analysis</div>', unsafe_allow_html=True)
    st.caption("Predict which requirements and software components are affected when a Java file is modified.")

    # ── Searchable code file selector ────────────────────────────────────
    search = st.text_input(
        "🔍 Search code files",
        placeholder="Type filename (e.g. AuthDAO, PatientDAO, EditPatientAction)…",
        key="code_search",
    )
    all_codes = sorted(code_to_req.keys())
    filtered = [c for c in all_codes if search.strip().lower() in c.lower()] if search.strip() else all_codes
    if not filtered:
        filtered = all_codes
        st.caption("⚠️ No direct match — showing all code files.")

    c_sel, c_btn = st.columns([4, 1])
    with c_sel:
        selected_code = st.selectbox("Select Modified Code File", filtered, key="code_select", label_visibility="collapsed")
    with c_btn:
        analyze_clicked = st.button("⚡ Analyze Code Impact", key="btn_code_analyze")

    if analyze_clicked or st.session_state.get("last_analyzed_code") == selected_code:
        st.session_state["last_analyzed_code"] = selected_code

        with st.spinner(f"Evaluating ML Relationship Scores & Dependency Propagation for {selected_code}…"):
            result = analyze_code_to_req(
                selected_code=selected_code,
                code_to_req=code_to_req,
                callgraph=callgraph,
                all_req_texts=all_req_texts,
                all_code_texts=all_code_texts
            )

        # Selected code file banner
        viewer_java_url = f"/viewer?type=java&file={urllib.parse.quote(selected_code)}"
        st.markdown(
            f'<div style="background:rgba(9,105,218,0.06); border:1px solid rgba(9,105,218,0.25); border-radius:8px; padding:12px 16px; margin:16px 0; display:flex; align-items:center; justify-content:space-between;">'
            f'<span><b>🔍 Selected Code Artifact:</b> <code style="font-size:14px; font-weight:600; color:var(--cia-accent);">{selected_code}</code></span>'
            f'<a href="{viewer_java_url}" target="_blank" style="background:var(--cia-accent); color:#ffffff; padding:4px 14px; border-radius:6px; text-decoration:none; font-size:12px; font-weight:600;">Inspect Source ↗</a>'
            f'</div>',
            unsafe_allow_html=True
        )

        metrics = result["summary_metrics"]
        artifacts_report = result["artifacts_report"]
        impacted_methods = result["impacted_methods"]
        related_reqs = result["related_requirements"]

        # ── 1. Top Summary Metric Row ─────────────────────────────────────────
        m1, m2, m3, m4, m5 = st.columns(5)
        with m1:
            st.markdown(metric_card(metrics["total_candidates_analyzed"], "Scored Requirements"), unsafe_allow_html=True)
        with m2:
            st.markdown(metric_card(metrics["verified_links_count"], "Verified Links"), unsafe_allow_html=True)
        with m3:
            st.markdown(metric_card(metrics["ml_predicted_links_count"], "ML Predicted Links"), unsafe_allow_html=True)
        with m4:
            st.markdown(metric_card(f"{len(impacted_methods):,}", "Impacted Methods"), unsafe_allow_html=True)
        with m5:
            st.markdown(
                f'<div class="metric-card"><div class="metric-value" style="font-size:20px;padding-top:4px;">'
                f'{severity_pill(metrics["top_overall_risk"])}</div><div class="metric-label">Top Overall Risk</div></div>',
                unsafe_allow_html=True,
            )

        st.markdown('<hr class="cia-divider">', unsafe_allow_html=True)

        # ── 2. Structured Multi-Tab View ──────────────────────────────────────
        tab_ranked, tab_verified, tab_methods = st.tabs([
            "🎯 Potentially Related Requirements",
            "📄 Verified Traced Requirements",
            "🔗 Java Dependency Ripple (Call Graph)"
        ])

        with tab_ranked:
            st.markdown(
                '<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">'
                '<span style="font-size:14px; font-weight:600; color:var(--cia-text);">Ranked by ML Relationship Score &amp; Overall Impact Risk</span>'
                '</div>',
                unsafe_allow_html=True
            )

            # Filter options
            c_filter, c_count = st.columns([3, 1])
            with c_filter:
                filter_choice = st.radio(
                    "Filter Requirements:",
                    ["Actionable (High & Medium Risk)", "All Candidates (Top 30)"],
                    horizontal=True,
                    label_visibility="collapsed"
                )
            with c_count:
                st.caption(f"Showing results for **{selected_code}**")

            # Apply filter
            if filter_choice == "Actionable (High & Medium Risk)":
                display_items = [a for a in artifacts_report if a["overall_impact_risk"] in ["HIGH", "MEDIUM"]]
            else:
                display_items = artifacts_report[:30]

            if display_items:
                for item in display_items:
                    code_param = urllib.parse.quote(selected_code)
                    score_param = f"{item['ml_relationship_score']:.4f}"
                    verified_param = "1" if item["verified_traceability"] else "0"
                    risk_param = item["overall_impact_risk"]
                    dep_param = item["dependency_reach"]

                    viewer_url = (
                        f"/viewer?type=req&file={urllib.parse.quote(item['artifact_name'])}"
                        f"&code={code_param}&score={score_param}&verified={verified_param}"
                        f"&risk={risk_param}&dep={dep_param}"
                    )

                    render_artifact_card_native(
                        artifact_name=item["artifact_name"],
                        overall_risk=item["overall_impact_risk"],
                        ml_score=item["ml_relationship_score"],
                        dependency_reach=item["dependency_reach"],
                        method_count=item["impacted_method_count"],
                        is_verified=item["verified_traceability"],
                        viewer_url=viewer_url,
                        risk_rationale=item["risk_rationale"],
                        title_label="Requirement",
                        btn_label="Inspect Requirement ↗",
                    )
            else:
                st.info("No requirements match the selected filter.")

        with tab_verified:
            st.markdown('<div class="section-header">📄 Verified Traced Requirements</div>', unsafe_allow_html=True)
            if related_reqs:
                st.caption(f"{len(related_reqs)} requirement documents verified in iTrust solution dataset for this code file:")
                for req_fname in related_reqs:
                    code_param = urllib.parse.quote(selected_code)
                    viewer_url = f"/viewer?type=req&file={urllib.parse.quote(req_fname)}&code={code_param}&verified=1"
                    st.markdown(
                        f'<div class="view-link" style="margin:6px 0;">'
                        f'<a href="{viewer_url}" target="_blank">📄 {req_fname} &nbsp; <span style="font-size:11px; color:#3FB950;">(Verified Link)</span></a>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.info("No verified traceability links recorded in dataset for this code file.")

        with tab_methods:
            st.markdown('<div class="section-header">🔗 Impacted Java Methods (From Call Graph)</div>', unsafe_allow_html=True)
            if impacted_methods:
                st.caption(f"{len(impacted_methods)} methods directly and transitively connected to {selected_code}:")
                df_methods = pd.DataFrame({"Impacted Method": impacted_methods[:50]})
                st.dataframe(df_methods, use_container_width=True, hide_index=True)

                csv = pd.DataFrame({"Impacted Method": impacted_methods}).to_csv(index=False).encode("utf-8")
                st.download_button(
                    "⬇ Download Complete Methods List (CSV)",
                    data=csv,
                    file_name=f"impacted_methods_{selected_code}.csv",
                    mime="text/csv",
                )
            else:
                st.info("No impacted methods detected in call graph for this code file.")
