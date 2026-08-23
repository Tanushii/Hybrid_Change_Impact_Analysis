"""
ui/req_to_code.py
Requirement → Code Mode UI.
Displays 3-layer hybrid impact analysis with ML Relationship Scores,
Traceability Evidence, Dependency Reach, and Overall Risk.
"""
import urllib.parse
import pandas as pd
import streamlit as st
from ui.styles import metric_card, severity_pill, render_artifact_card
from services.impact_engine import analyze_req_to_code


def render(req_to_code, callgraph, file_index, all_req_texts=None, all_code_texts=None):
    st.markdown('<div class="section-header">📋 Requirement Change Impact Analysis</div>', unsafe_allow_html=True)
    st.caption("Predict which code artifacts and methods are impacted when a requirement changes.")

    # ── Searchable requirement selector ──────────────────────────────────
    search = st.text_input(
        "🔍 Search requirements",
        placeholder="Type UC ID or keyword (e.g. UC10E1, password, allergy)…",
        key="req_search",
    )
    all_reqs = sorted(req_to_code.keys())
    filtered = [r for r in all_reqs if search.strip().lower() in r.lower()] if search.strip() else all_reqs
    if not filtered:
        filtered = all_reqs
        st.caption("⚠️ No direct match — showing all requirements.")

    c_sel, c_btn = st.columns([4, 1])
    with c_sel:
        requirement = st.selectbox("Select Changed Requirement", filtered, key="req_select", label_visibility="collapsed")
    with c_btn:
        analyze_clicked = st.button("⚡ Analyze Impact", key="btn_req_analyze")

    if analyze_clicked or st.session_state.get("last_analyzed_req") == requirement:
        st.session_state["last_analyzed_req"] = requirement

        with st.spinner(f"Computing ML Relationship Scores & Dependency Propagation for {requirement}…"):
            result = analyze_req_to_code(
                requirement=requirement,
                req_to_code=req_to_code,
                callgraph=callgraph,
                file_index=file_index,
                all_req_texts=all_req_texts,
                all_code_texts=all_code_texts
            )

        # Selected requirement banner
        viewer_req_url = f"/viewer?type=req&file={urllib.parse.quote(requirement)}"
        st.markdown(
            f'<div style="background:rgba(9,105,218,0.06); border:1px solid rgba(9,105,218,0.25); border-radius:8px; padding:12px 16px; margin:16px 0; display:flex; align-items:center; justify-content:space-between;">'
            f'<span><b>📄 Selected Requirement:</b> <code style="font-size:14px; font-weight:600; color:var(--cia-accent);">{requirement}</code></span>'
            f'<a href="{viewer_req_url}" target="_blank" style="background:var(--cia-accent); color:#ffffff; padding:4px 14px; border-radius:6px; text-decoration:none; font-size:12px; font-weight:600;">Inspect Document ↗</a>'
            f'</div>',
            unsafe_allow_html=True
        )

        metrics = result["summary_metrics"]
        artifacts_report = result["artifacts_report"]
        code_to_methods = result["code_to_methods"]
        impacted_methods = result["impacted_methods"]
        related_codes = result["related_codes"]

        # ── 1. Top Summary Metric Row ─────────────────────────────────────────
        m1, m2, m3, m4, m5 = st.columns(5)
        with m1:
            st.markdown(metric_card(metrics["total_candidates_analyzed"], "Scored Candidates"), unsafe_allow_html=True)
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
            "🎯 Potentially Related Code Artifacts",
            "📋 Verified Traceability Links",
            "🔗 Impacted Methods (Call Graph)"
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
                    "Filter Candidates:",
                    ["Actionable (High & Medium Risk)", "All Candidates (Top 30)", "Verified Links Only", "ML Predicted Only"],
                    horizontal=True,
                    label_visibility="collapsed"
                )
            with c_count:
                st.caption(f"Showing results for **{requirement}**")

            # Apply filter
            if filter_choice == "Actionable (High & Medium Risk)":
                display_items = [a for a in artifacts_report if a["overall_impact_risk"] in ["HIGH", "MEDIUM"]]
            elif filter_choice == "Verified Links Only":
                display_items = [a for a in artifacts_report if a["verified_traceability"]]
            elif filter_choice == "ML Predicted Only":
                display_items = [a for a in artifacts_report if a["ml_predicted_label"] == 1]
            else:
                display_items = artifacts_report[:30]

            if display_items:
                for item in display_items:
                    methods_for_file = code_to_methods.get(item["artifact_name"], item["impacted_methods"])
                    methods_param = urllib.parse.quote(",".join(methods_for_file[:30])) if methods_for_file else ""
                    
                    req_param = urllib.parse.quote(requirement)
                    score_param = f"{item['ml_relationship_score']:.4f}"
                    verified_param = "1" if item["verified_traceability"] else "0"
                    risk_param = item["overall_impact_risk"]
                    dep_param = item["dependency_reach"]

                    viewer_url = (
                        f"/viewer?type=java&file={urllib.parse.quote(item['artifact_name'])}"
                        f"&req={req_param}&score={score_param}&verified={verified_param}"
                        f"&risk={risk_param}&dep={dep_param}&methods={methods_param}"
                    )

                    card_html = render_artifact_card(
                        title_label="Code File",
                        artifact_name=item["artifact_name"],
                        ml_score=item["ml_relationship_score"],
                        ml_conf=item["ml_confidence_level"],
                        is_verified=item["verified_traceability"],
                        dependency_reach=item["dependency_reach"],
                        method_count=item["impacted_method_count"],
                        overall_risk=item["overall_impact_risk"],
                        risk_rationale=item["risk_rationale"],
                        viewer_url=viewer_url
                    )
                    st.markdown(card_html, unsafe_allow_html=True)
            else:
                st.info("No candidates match the selected filter.")

        with tab_verified:
            st.markdown('<div class="section-header">📁 Verified Ground-Truth Links</div>', unsafe_allow_html=True)
            if related_codes:
                st.caption(f"{len(related_codes)} code files verified in iTrust solution dataset for this requirement:")
                for fname in related_codes:
                    methods_for_file = code_to_methods.get(fname, [])
                    methods_param = urllib.parse.quote(",".join(methods_for_file[:30])) if methods_for_file else ""
                    req_param = urllib.parse.quote(requirement)
                    viewer_url = f"/viewer?type=java&file={urllib.parse.quote(fname)}&req={req_param}&verified=1&methods={methods_param}"
                    st.markdown(
                        f'<div class="view-link" style="margin:6px 0;">'
                        f'<a href="{viewer_url}" target="_blank">📂 {fname} &nbsp; <span style="font-size:11px; color:#3FB950;">(Verified Link)</span></a>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.info("No verified traceability links recorded in dataset for this requirement.")

        with tab_methods:
            st.markdown('<div class="section-header">🔗 Transitively Impacted Methods (Call Graph)</div>', unsafe_allow_html=True)
            if impacted_methods:
                st.caption(f"{len(impacted_methods)} methods transitively called or calling impacted classes:")
                df_methods = pd.DataFrame({"Impacted Method": impacted_methods[:50]})
                st.dataframe(df_methods, use_container_width=True, hide_index=True)

                csv = pd.DataFrame({"Impacted Method": impacted_methods}).to_csv(index=False).encode("utf-8")
                st.download_button(
                    "⬇ Download Complete Methods List (CSV)",
                    data=csv,
                    file_name=f"impacted_methods_{requirement}.csv",
                    mime="text/csv",
                )
            else:
                st.info("No impacted methods detected in call graph.")
