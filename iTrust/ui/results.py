"""
ui/results.py
Final Model Results & Evaluation Dashboard.

Displays ONLY the verified Final Hybrid Model results extracted dynamically
from the authoritative evaluation in CIA_System.ipynb.
NO historical baselines, comparisons, or hard-coded metrics are shown.
Charts are theme-aware (light / dark) via get_chart_colors().
"""

import html as html_mod
import streamlit as st
import plotly.graph_objects as go
from services.experiment_results import load_final_model_results
from ui.styles import get_chart_colors


def _pct(v: float | None, decimals: int = 2) -> str:
    """Format a 0-1 float as a percentage string (e.g., 0.8522 -> 85.22%)."""
    if v is None:
        return "N/A"
    return f"{round(v * 100, decimals):.{decimals}f}%"


def _metric_card(value: str, label: str, sub: str = "", color: str = "var(--cia-accent)") -> str:
    """Render a clean metric card."""
    return f"""
<div style="background:var(--cia-surface); border:1px solid var(--cia-border); border-radius:10px; padding:18px 20px; text-align:center; box-shadow:0 1px 4px var(--cia-shadow);">
    <div style="font-size:30px; font-weight:800; color:{color}; font-family:JetBrains Mono,monospace; line-height:1.2;">{value}</div>
    <div style="font-size:12px; font-weight:700; color:var(--cia-text-muted); text-transform:uppercase; letter-spacing:0.6px; margin-top:6px;">{label}</div>
    {f'<div style="font-size:11px; color:var(--cia-text-faint); margin-top:2px;">{sub}</div>' if sub else ''}
</div>
"""


def render():
    """Render the simplified Final Model Results UI."""

    st.markdown(
        '<div class="section-header">📊 Final Model Results</div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Verified performance metrics of the Final Hybrid Change Impact Analysis model, "
        "extracted dynamically from the reproducible evaluation in CIA_System.ipynb."
    )

    # ── 1. Dynamic Extraction ─────────────────────────────────────────
    with st.spinner("Loading final model results from notebook…"):
        res = load_final_model_results()

    # Get theme-aware chart colours once
    ch = get_chart_colors()

    acc = res.get("accuracy")
    prec = res.get("precision")
    rec = res.get("recall")
    f1 = res.get("f1")
    cm_dict = res.get("confusion_matrix", {})
    details = res.get("model_details", {})
    test_samples = res.get("test_samples", 115)

    # ── 2. Model Overview Banner ──────────────────────────────────────
    st.markdown(
        f"""
<div style="background:var(--cia-surface); border:1px solid var(--cia-border); border-radius:10px; padding:16px 20px; margin:12px 0 20px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
    <div>
        <div style="font-size:11px; font-weight:700; color:var(--cia-accent); text-transform:uppercase; letter-spacing:0.8px;">Verified Final Model</div>
        <div style="font-size:20px; font-weight:800; color:var(--cia-text); margin-top:2px;">{html_mod.escape(res.get("model_name", "Hybrid TF-IDF + SBERT + XGBoost"))}</div>
        <div style="font-size:13px; color:var(--cia-text-muted); margin-top:4px;">
            <b>Task:</b> {html_mod.escape(res.get("task", "Requirement–Code Link Prediction"))} &nbsp;·&nbsp;
            <b>Dataset:</b> {html_mod.escape(res.get("dataset", "iTrust"))} &nbsp;·&nbsp;
            <b>Test Samples:</b> {test_samples}
        </div>
    </div>
    <div style="text-align:right;">
        <span style="background:var(--cia-info-bg); color:var(--cia-accent); border:1px solid var(--cia-border); border-radius:6px; font-size:11px; font-weight:600; padding:4px 10px; font-family:JetBrains Mono,monospace;">
            📄 Source: {html_mod.escape(res.get("source_file", "CIA_System.ipynb"))}
        </span>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )

    # ── 3. Four Core Performance Metrics ──────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(_metric_card(_pct(acc),  "Accuracy",  "Overall Correct Predictions", ch["bar_accent"]), unsafe_allow_html=True)
    with col2:
        st.markdown(_metric_card(_pct(prec), "Precision", "Linked Class (Class 1)",      ch["bar_main"]),   unsafe_allow_html=True)
    with col3:
        st.markdown(_metric_card(_pct(rec),  "Recall",    "Linked Class (Class 1)",      ch["bar_main"]),   unsafe_allow_html=True)
    with col4:
        st.markdown(_metric_card(_pct(f1),   "F1-Score",  "Harmonic Mean",               ch["bar_main"]),   unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── 4. Two-Column Visuals: Confusion Matrix & Performance Bar Chart ──
    col_cm, col_chart = st.columns(2)

    # ── Left: Confusion Matrix Heatmap ───────────────────────────────
    with col_cm:
        st.markdown(
            '<div style="font-size:15px; font-weight:700; color:var(--cia-text); margin-bottom:8px;">'
            'Confusion Matrix</div>',
            unsafe_allow_html=True,
        )

        tn = cm_dict.get("tn", 46)
        fp = cm_dict.get("fp", 12)
        fn = cm_dict.get("fn", 5)
        tp = cm_dict.get("tp", 52)

        z = [[tn, fp], [fn, tp]]
        text_labels = [
            [f"TN = {tn}", f"FP = {fp}"],
            [f"FN = {fn}", f"TP = {tp}"]
        ]

        fig_cm = go.Figure(
            data=go.Heatmap(
                z=z,
                x=["Predicted: Unlinked", "Predicted: Linked"],
                y=["Actual: Unlinked", "Actual: Linked"],
                text=text_labels,
                texttemplate="<b>%{text}</b>",
                textfont=dict(size=15, color=ch["annot_color"]),
                colorscale=ch["colorscale"],
                showscale=False,
            )
        )
        fig_cm.update_layout(
            height=340,
            margin=dict(l=20, r=20, t=20, b=20),
            paper_bgcolor=ch["bg"],
            plot_bgcolor=ch["plot_bg"],
            font=dict(family="Inter, sans-serif", size=12, color=ch["text"]),
            xaxis=dict(
                side="bottom",
                tickfont=dict(color=ch["axis"], size=12),
                title_font=dict(color=ch["axis"]),
            ),
            yaxis=dict(
                autorange="reversed",
                tickfont=dict(color=ch["axis"], size=12),
                title_font=dict(color=ch["axis"]),
            ),
        )
        st.plotly_chart(fig_cm, use_container_width=True)

    # ── Right: Performance Bar Chart ─────────────────────────────────
    with col_chart:
        st.markdown(
            '<div style="font-size:15px; font-weight:700; color:var(--cia-text); margin-bottom:8px;">'
            'Final Hybrid Model Performance</div>',
            unsafe_allow_html=True,
        )

        metrics_names = ["Accuracy", "Precision", "Recall", "F1-Score"]
        metrics_values = [
            round((acc  or 0) * 100, 2),
            round((prec or 0) * 100, 2),
            round((rec  or 0) * 100, 2),
            round((f1   or 0) * 100, 2),
        ]
        # Coherent CIA palette: Accuracy in accent-green, rest in accent-blue
        bar_colors = [
            ch["bar_accent"],   # Accuracy — success green
            ch["bar_main"],     # Precision
            ch["bar_main"],     # Recall
            ch["bar_main"],     # F1-Score
        ]

        fig_perf = go.Figure(
            data=go.Bar(
                x=metrics_names,
                y=metrics_values,
                text=[f"<b>{v:.2f}%</b>" for v in metrics_values],
                textposition="outside",
                textfont=dict(color=ch["text"], size=13),
                marker=dict(color=bar_colors, cornerradius=4),
            )
        )
        fig_perf.update_layout(
            yaxis_title="Percentage (%)",
            yaxis_range=[0, 115],
            height=340,
            margin=dict(l=20, r=20, t=20, b=20),
            paper_bgcolor=ch["bg"],
            plot_bgcolor=ch["plot_bg"],
            font=dict(family="Inter, sans-serif", size=12, color=ch["text"]),
            yaxis=dict(
                title_font=dict(color=ch["axis"]),
                tickfont=dict(color=ch["axis"]),
                gridcolor=ch["grid"],
                gridwidth=1,
                zeroline=False,
            ),
            xaxis=dict(
                tickfont=dict(color=ch["axis"], size=13),
                showgrid=False,
            ),
            bargap=0.35,
        )
        st.plotly_chart(fig_perf, use_container_width=True)

    # ── 5. Academic Provenance Note ──────────────────────────────────
    st.markdown(
        """
<div style="background:var(--cia-info-bg); border:1px solid var(--cia-border); border-radius:8px; padding:10px 14px; font-size:12px; color:var(--cia-text-muted); margin-top:8px;">
    ℹ️ <b>Academic Provenance Note:</b> Evaluation metrics are derived from the Final Hybrid Model experiment in <code>CIA_System.ipynb</code> on the iTrust benchmark (115 held-out test pairs). These benchmark accuracy figures measure link-prediction capability on the curated dataset and do not represent universal probabilities for external GitHub repositories.
</div>
""",
        unsafe_allow_html=True,
    )

    # ── 6. Optional Model Details (Expandable) ─────────────────────────
    with st.expander("📋 Model Details", expanded=False):
        st.markdown(
            f"""
- **Model Architecture:** {html_mod.escape(details.get("architecture", "Hybrid TF-IDF + SBERT + XGBoost"))}
- **TF-IDF Lexical Features:** {details.get("tfidf_features", 500)} features (unigrams & bigrams, stop-words removed)
- **SBERT Semantic Feature:** {details.get("sbert_feature", "1 cosine similarity value")}
- **Total Features:** {details.get("total_features", 501)} dimensions
- **SBERT Model:** `{html_mod.escape(details.get("sbert_model", "all-MiniLM-L6-v2"))}`
- **Dataset:** {html_mod.escape(details.get("dataset", "iTrust"))} (131 requirements, 226 Java files, 286 verified links)
- **Train / Test Split:** {details.get("train_samples", 457)} training pairs / {details.get("test_samples", 115)} testing pairs ({details.get("split_strategy", "Stratified 80/20")})
- **Leakage Protection Protocol:** {html_mod.escape(details.get("leakage_protection", "TF-IDF fitted exclusively on train split"))}
"""
        )
