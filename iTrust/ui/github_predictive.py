"""
ui/github_predictive.py
Mode 1 — Predictive / Before Change Analysis UI.

User enters a GitHub repository, branch, and file to analyze
BEFORE making any changes. The system dynamically discovers
repository structure, identifies structural dependencies,
and evaluates model-based relationship evidence.
"""

import html
import urllib.parse
import streamlit as st
from ui.styles import metric_card, severity_pill
from services.github_service import (
    parse_repository,
    get_repository_info,
    get_branches,
    get_file_tree,
    get_file_content,
    get_rate_limit_status,
    GitHubAPIError
)
from services.github_impact_engine import (
    analyze_github_predictive,
    detect_language
)

# Supported source file extensions for repository discovery
SUPPORTED_EXTENSIONS = [
    ".java", ".py", ".js", ".jsx", ".ts", ".tsx",
    ".go", ".cpp", ".c", ".h", ".hpp", ".cs",
    ".rs", ".rb", ".php", ".sql", ".md", ".txt"
]


def render():
    """Render Mode 1 — Predictive Change Impact Analysis UI."""

    st.markdown(
        '<div class="section-header">🔵 Predictive Change Impact Analysis</div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Analyze the potential ripple impact of a planned change to a repository file BEFORE modifying it."
    )

    # ── Shared Repository & Token Connection ─────────────────────────────
    col_repo, col_token = st.columns([3, 2])
    
    default_repo = st.session_state.get("gh_shared_repo", "")
    default_token = st.session_state.get("gh_shared_token", "")

    with col_repo:
        repo_input = st.text_input(
            "GitHub Repository",
            value=default_repo,
            placeholder="owner/repository  or  https://github.com/owner/repo",
            key="gh_pred_repo",
        )
    with col_token:
        token_input = st.text_input(
            "GitHub Token (Optional)",
            value=default_token,
            type="password",
            placeholder="ghp_xxxx... (increases rate limit)",
            key="gh_pred_token",
        )

    # Preserve in shared session state
    if repo_input != default_repo:
        st.session_state["gh_shared_repo"] = repo_input
    if token_input != default_token:
        st.session_state["gh_shared_token"] = token_input

    token = token_input.strip() if token_input else None

    # Rate Limit Status Badge
    rl_info = get_rate_limit_status(token)
    rl_status_cls = "color:#3FB950;" if rl_info["remaining"] > 10 else "color:#E3B341;" if rl_info["remaining"] > 0 else "color:#F85149;"
    auth_label = "🔑 Authenticated" if rl_info["is_authenticated"] else "🌐 Public"
    reset_text = f" · Resets {rl_info['reset_time']}" if rl_info.get("reset_time") else ""
    st.markdown(
        f'<div style="font-size:11px; color:var(--cia-text-faint); margin-bottom:8px;">'
        f'{auth_label} API Quota: <b style="{rl_status_cls}">{rl_info["remaining"]}/{rl_info["limit"]}</b> calls remaining{reset_text}'
        f'</div>',
        unsafe_allow_html=True
    )

    if not repo_input or not repo_input.strip():
        st.info("Enter a GitHub repository URL or `owner/repo` to dynamically explore repository files.")
        return

    # ── Parse & Validate Repository ──────────────────────────────────────
    owner, repo = parse_repository(repo_input)
    if not owner or not repo:
        st.error("❌ Invalid repository format. Use `owner/repo` or a full GitHub URL.")
        return

    # ── Load Repository Info ─────────────────────────────────────────────
    try:
        repo_info = get_repository_info(owner, repo, token)
    except GitHubAPIError as e:
        st.error(f"❌ {str(e)}")
        return

    # Repo info banner
    st.markdown(
        f'<div style="background:rgba(9,105,218,0.06); border:1px solid rgba(9,105,218,0.25); '
        f'border-radius:8px; padding:12px 16px; margin:10px 0; display:flex; align-items:center; justify-content:space-between;">'
        f'<span><b>📦 Repository:</b> '
        f'<a href="{html.escape(repo_info["html_url"])}" target="_blank" '
        f'style="color:var(--cia-accent); text-decoration:none; font-weight:600;">'
        f'{html.escape(repo_info["full_name"])}</a>'
        f' &nbsp;⭐ {repo_info["stars"]} &nbsp;🍴 {repo_info["forks"]}'
        f' &nbsp;📝 Primary: {html.escape(repo_info["language"])}</span>'
        f'<span style="font-size:12px; color:var(--cia-text-faint);">'
        f'{"🔒 Private" if repo_info["is_private"] else "🌐 Public"}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Branch & File Selection ──────────────────────────────────────────
    try:
        branches = get_branches(owner, repo, token)
    except GitHubAPIError:
        branches = [repo_info.get("default_branch", "main")]

    col_branch, col_mode = st.columns([2, 2])
    with col_branch:
        selected_branch = st.selectbox(
            "Branch", branches, key="gh_pred_branch"
        )
    with col_mode:
        st.markdown(
            '<div style="padding:8px 0;">'
            '<span style="background:rgba(9,105,218,0.12); color:var(--cia-accent); '
            'padding:6px 14px; border-radius:6px; font-weight:600; font-size:13px;">'
            '🔵 Mode: Predictive — Before Change</span></div>',
            unsafe_allow_html=True,
        )

    # ── File Tree ────────────────────────────────────────────────────────
    try:
        with st.spinner("Discovering repository file tree…"):
            file_tree = get_file_tree(
                owner, repo, selected_branch, token, extensions=SUPPORTED_EXTENSIONS
            )
    except GitHubAPIError as e:
        st.error(f"❌ Failed to load file tree: {e}")
        return

    if not file_tree:
        st.warning("No supported source files discovered in this repository/branch.")
        return

    file_paths = [f["path"] for f in file_tree]

    # Searchable file selector
    file_search = st.text_input(
        "🔍 Search repository files",
        placeholder="Search filename or path (e.g. controller, service, .java, .py, .ts)…",
        key="gh_pred_file_search",
    )
    if file_search and file_search.strip():
        filtered_paths = [p for p in file_paths if file_search.strip().lower() in p.lower()]
        if not filtered_paths:
            filtered_paths = file_paths
            st.caption("⚠️ No match — showing all discovered files.")
    else:
        filtered_paths = file_paths

    col_file, col_btn = st.columns([4, 1])
    with col_file:
        selected_file = st.selectbox(
            "Select File to Analyze",
            filtered_paths,
            key="gh_pred_file_select",
            label_visibility="collapsed",
        )
    with col_btn:
        analyze_clicked = st.button("⚡ Analyze Potential Impact", key="btn_gh_pred_analyze")

    # ── Run Analysis ─────────────────────────────────────────────────────
    if analyze_clicked or st.session_state.get("gh_pred_last_file") == selected_file:
        st.session_state["gh_pred_last_file"] = selected_file

        with st.spinner(f"Analyzing potential change impact for `{selected_file}`…"):
            try:
                target_content = get_file_content(owner, repo, selected_file, ref=selected_branch, token=token)
            except GitHubAPIError as e:
                st.error(f"❌ Could not fetch file: {e}")
                return

            # Fetch content for related candidate files in the repository
            file_contents_map = {selected_file: target_content}
            scan_files = [f for f in file_tree if f["path"] != selected_file]
            target_ext = "." + selected_file.rsplit(".", 1)[-1] if "." in selected_file else ""
            same_lang = [f for f in scan_files if f["path"].endswith(target_ext)] if target_ext else scan_files
            other_files = [f for f in scan_files if not f["path"].endswith(target_ext)] if target_ext else []
            candidates = (same_lang[:40] + other_files[:10])

            for cf in candidates:
                try:
                    cf_content = get_file_content(owner, repo, cf["path"], ref=selected_branch, token=token)
                    file_contents_map[cf["path"]] = cf_content
                except Exception:
                    continue

            result = analyze_github_predictive(
                target_path=selected_file,
                target_content=target_content,
                repo_files=file_tree,
                file_contents_map=file_contents_map,
            )

        # ── Selected File Banner ─────────────────────────────────────────
        basename = selected_file.split("/")[-1]
        detected_lang = detect_language(basename)
        lang_icon = "☕" if "Java" in detected_lang else "🐍" if "Python" in detected_lang else "📜" if "Script" in detected_lang else "📄"
        viewer_url = (
            f"/viewer?type=github&repo={urllib.parse.quote(f'{owner}/{repo}')}"
            f"&branch={urllib.parse.quote(selected_branch)}"
            f"&file={urllib.parse.quote(selected_file)}"
        )
        st.markdown(
            f'<div style="background:rgba(9,105,218,0.06); border:1px solid rgba(9,105,218,0.25); '
            f'border-radius:8px; padding:12px 16px; margin:16px 0; display:flex; align-items:center; '
            f'justify-content:space-between;">'
            f'<span>{lang_icon} <b>Selected File:</b> '
            f'<code style="font-size:14px; font-weight:600; color:var(--cia-accent);">{html.escape(basename)}</code>'
            f' <span style="font-size:12px; color:var(--cia-text-faint);">({html.escape(detected_lang)} · {html.escape(selected_file)})</span></span>'
            f'<a href="{viewer_url}" target="_blank" style="background:var(--cia-accent); color:#ffffff; '
            f'padding:4px 14px; border-radius:6px; text-decoration:none; font-size:12px; font-weight:600;">'
            f'Inspect Source ↗</a></div>',
            unsafe_allow_html=True,
        )

        # ── Summary Metrics Row ──────────────────────────────────────────
        m1, m2, m3, m4, m5 = st.columns(5)
        with m1:
            st.markdown(metric_card(len(result["related_artifacts"]), "Scored Artifacts"), unsafe_allow_html=True)
        with m2:
            st.markdown(metric_card(result["connected_files_count"], "Structural Links"), unsafe_allow_html=True)
        with m3:
            st.markdown(metric_card(result["methods_count"], "Extracted Methods"), unsafe_allow_html=True)
        with m4:
            st.markdown(
                f'<div class="metric-card"><div class="metric-value">'
                f'{result["structural_badge"]} {result["structural_reach"]}'
                f'</div><div class="metric-label">Dependency Reach</div></div>',
                unsafe_allow_html=True,
            )
        with m5:
            st.markdown(
                f'<div class="metric-card"><div class="metric-value" style="font-size:20px;padding-top:4px;">'
                f'{severity_pill(result["overall_risk"])}</div>'
                f'<div class="metric-label">Overall Impact Risk</div></div>',
                unsafe_allow_html=True,
            )

        st.markdown('<hr class="cia-divider">', unsafe_allow_html=True)

        # ── Academic Limitation Disclaimer ───────────────────────────────
        st.markdown(
            '<div style="background:rgba(227,179,65,0.08); border:1px solid rgba(227,179,65,0.3); '
            'border-radius:8px; padding:10px 14px; margin-bottom:14px; font-size:12px; '
            'color:var(--cia-text-muted); line-height:1.6;">'
            'ℹ️ <b>Academic Note on External Repository Analysis:</b> '
            'For external repositories, ML scores represent <b>ML Relationship Evidence</b> generated using '
            'the model trained on the benchmark dataset and should be interpreted alongside structural repository evidence. '
            'Ground-truth traceability matrices are <b>not available</b> for arbitrary external repositories.'
            '</div>',
            unsafe_allow_html=True,
        )

        # ── Tabbed Results ───────────────────────────────────────────────
        tab_artifacts, tab_deps, tab_overview = st.tabs([
            "🎯 Potentially Related Artifacts",
            "🔗 Structural Dependency Graph",
            "📄 File Overview"
        ])

        with tab_artifacts:
            st.markdown(
                '<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">'
                '<span style="font-size:14px; font-weight:600; color:var(--cia-text);">'
                'Ranked by ML Relationship Evidence &amp; Structural Links</span></div>',
                unsafe_allow_html=True,
            )

            artifacts = result["related_artifacts"]
            if artifacts:
                filter_choice = st.radio(
                    "Filter:",
                    ["All Related Artifacts", "Structurally Linked Only", "High ML Score Only"],
                    horizontal=True,
                    label_visibility="collapsed",
                    key="gh_pred_filter",
                )
                if filter_choice == "Structurally Linked Only":
                    display_items = [a for a in artifacts if a["is_structurally_linked"]]
                elif filter_choice == "High ML Score Only":
                    display_items = [a for a in artifacts if a["ml_score"] >= 0.70]
                else:
                    display_items = artifacts[:30]

                if display_items:
                    for item in display_items:
                        _render_github_artifact_card(item, owner, repo, selected_branch)
                else:
                    st.info("No artifacts match the selected filter.")
            else:
                st.info("No related artifacts detected in the repository scope analyzed.")

        with tab_deps:
            st.markdown(
                '<div class="section-header">🔗 Repository Structural Dependencies</div>',
                unsafe_allow_html=True,
            )
            callers = result.get("caller_files", [])
            callees = result.get("callee_files", [])

            if callers:
                st.markdown(
                    f'<div style="font-size:13px; font-weight:600; color:var(--cia-text); margin:8px 0 4px;">'
                    f'📥 Inbound References to <code>{html.escape(basename)}</code> ({len(callers)})</div>',
                    unsafe_allow_html=True,
                )
                for cf in callers:
                    st.markdown(
                        f'<div style="margin:3px 0 3px 16px; font-size:13px;">'
                        f'<span style="color:var(--cia-accent);">→</span> {html.escape(cf)}</div>',
                        unsafe_allow_html=True,
                    )

            if callees:
                st.markdown(
                    f'<div style="font-size:13px; font-weight:600; color:var(--cia-text); margin:12px 0 4px;">'
                    f'📤 Outbound References from <code>{html.escape(basename)}</code> ({len(callees)})</div>',
                    unsafe_allow_html=True,
                )
                for cf in callees:
                    st.markdown(
                        f'<div style="margin:3px 0 3px 16px; font-size:13px;">'
                        f'<span style="color:var(--cia-med);">←</span> {html.escape(cf)}</div>',
                        unsafe_allow_html=True,
                    )

            if not callers and not callees:
                st.info("No structural dependencies detected across scanned repository files.")

        with tab_overview:
            st.markdown(
                '<div class="section-header">📄 File Overview</div>',
                unsafe_allow_html=True,
            )
            methods = result.get("methods", [])
            if methods:
                st.caption(f"{len(methods)} declared structures/methods in `{basename}`:")
                for m in methods:
                    st.markdown(
                        f'<div style="margin:4px 0 4px 8px; font-size:13px; font-family:JetBrains Mono, monospace;">'
                        f'<span style="color:var(--cia-text-faint);">L{m["line"]}</span> '
                        f'<span style="color:var(--cia-accent);">{html.escape(m.get("return_type", "def"))}</span> '
                        f'<b>{html.escape(m["signature"])}</b></div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.caption("No method or function declarations detected.")

            st.markdown(
                f'<div style="margin-top:16px; padding:12px; background:var(--cia-surface); '
                f'border:1px solid var(--cia-border); border-radius:8px;">'
                f'<div style="font-size:12px; font-weight:600; color:var(--cia-text-faint); '
                f'text-transform:uppercase; margin-bottom:6px;">Risk Rationale</div>'
                f'<div style="font-size:13px; color:var(--cia-text);">'
                f'{result["overall_badge"]} {html.escape(result["risk_rationale"])}</div></div>',
                unsafe_allow_html=True,
            )


def _render_github_artifact_card(item: dict, owner: str, repo: str, branch: str):
    """Render a single impact card for a GitHub repository artifact using native Streamlit containers."""
    score_pct = item["ml_score"] * 100.0
    safe_name = item["filename"]
    safe_path = item["path"]

    viewer_url = (
        f"/viewer?type=github&repo={urllib.parse.quote(f'{owner}/{repo}')}"
        f"&branch={urllib.parse.quote(branch)}"
        f"&file={urllib.parse.quote(item['path'])}"
    )

    with st.container(border=True):
        c_title, c_btn = st.columns([3.8, 1.2])
        with c_title:
            icon = "📄" if safe_name.endswith((".java", ".py", ".ts", ".js", ".go", ".cpp", ".c", ".cs")) else "📁"
            st.markdown(
                f'<div style="display:flex; align-items:center; gap:8px; margin-bottom:2px;">'
                f'<span style="font-size:18px;">{icon}</span>'
                f'<span style="font-family:JetBrains Mono, monospace; font-size:16px; font-weight:700; color:var(--cia-accent);">{html.escape(safe_name)}</span>'
                f'<span style="font-size:11px; color:var(--cia-text-faint); font-family:JetBrains Mono, monospace;">({html.escape(safe_path)})</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with c_btn:
            st.link_button("Inspect Source ↗", viewer_url, use_container_width=True)

        c_risk, c_ml, c_struct, c_trace = st.columns(4)
        with c_risk:
            st.caption("Overall Impact Risk")
            st.markdown(severity_pill(item["risk_tier"]), unsafe_allow_html=True)
        with c_ml:
            st.caption("ML Relationship Score")
            st.markdown(f'<b style="font-size:15px; font-family:JetBrains Mono, monospace; color:var(--cia-text);">{score_pct:.2f}%</b> <span style="font-size:11px; color:var(--cia-text-faint);">({item["confidence_level"]})</span>', unsafe_allow_html=True)
        with c_struct:
            st.caption("Structural Evidence")
            if item["is_structurally_linked"]:
                st.markdown('<span class="badge-verified">🔗 Structural Link</span>', unsafe_allow_html=True)
            else:
                st.markdown('<span class="badge-unverified">📊 ML Predicted</span>', unsafe_allow_html=True)
        with c_trace:
            st.caption("Traceability Status")
            st.markdown('<span style="font-size:11px; color:var(--cia-text-faint);">N/A (External Repo)</span>', unsafe_allow_html=True)

        if item.get("risk_rationale"):
            st.caption(f"**Rationale:** {item['risk_rationale']}")
