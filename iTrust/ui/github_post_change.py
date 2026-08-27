"""
ui/github_post_change.py
Mode 2 — Post-Change / Commit Comparison Analysis UI.

User enters a GitHub repository, branch, base commit, and new commit.
The system dynamically discovers commits, computes diffs, detects modified methods/functions
across languages, and evaluates the ripple impact of actual changes.
"""

import html
import urllib.parse
import streamlit as st
from ui.styles import metric_card, severity_pill
from services.github_service import (
    parse_repository,
    get_repository_info,
    get_branches,
    get_recent_commits,
    get_rate_limit_status,
    GitHubAPIError
)
from services.github_impact_engine import analyze_github_post_change, detect_language


def render():
    """Render Mode 2 — Post-Change Impact Analysis UI."""

    st.markdown(
        '<div class="section-header">🟠 Post-Change Impact Analysis</div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Compare two commits to analyze the actual impact of code modifications — "
        "changed files, modified functions, dependency reach, and ripple risk assessment."
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
            key="gh_post_repo",
        )
    with col_token:
        token_input = st.text_input(
            "GitHub Token (Optional)",
            value=default_token,
            type="password",
            placeholder="ghp_xxxx... (increases rate limit)",
            key="gh_post_token",
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
        st.info("Enter a GitHub repository URL or `owner/repo` to compare commits and analyze actual changes.")
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

    st.markdown(
        f'<div style="background:rgba(9,105,218,0.06); border:1px solid rgba(9,105,218,0.25); '
        f'border-radius:8px; padding:12px 16px; margin:10px 0; display:flex; align-items:center; '
        f'justify-content:space-between;">'
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

    # ── Branch Selection ─────────────────────────────────────────────────
    try:
        branches = get_branches(owner, repo, token)
    except GitHubAPIError:
        branches = [repo_info.get("default_branch", "main")]

    col_branch, col_mode = st.columns([2, 2])
    with col_branch:
        selected_branch = st.selectbox("Branch", branches, key="gh_post_branch")
    with col_mode:
        st.markdown(
            '<div style="padding:8px 0;">'
            '<span style="background:rgba(227,179,65,0.15); color:var(--cia-med); '
            'padding:6px 14px; border-radius:6px; font-weight:600; font-size:13px;">'
            '🟠 Mode: Post-Change — Compare Commits</span></div>',
            unsafe_allow_html=True,
        )

    # ── Load Commits ─────────────────────────────────────────────────────
    try:
        with st.spinner("Loading recent commits…"):
            commits = get_recent_commits(owner, repo, selected_branch, token, limit=30)
    except GitHubAPIError as e:
        st.error(f"❌ {str(e)}")
        return

    if len(commits) < 2:
        st.warning("This branch needs at least 2 commits for comparison.")
        return

    commit_labels = [
        f"{c['short_sha']} — {c['message'][:60]} ({c['date']})" for c in commits
    ]

    col_base, col_new = st.columns(2)
    with col_base:
        base_idx = st.selectbox(
            "Base Commit (older)",
            range(len(commit_labels)),
            index=min(1, len(commit_labels) - 1),
            format_func=lambda i: commit_labels[i],
            key="gh_post_base",
        )
    with col_new:
        new_idx = st.selectbox(
            "New Commit (newer)",
            range(len(commit_labels)),
            index=0,
            format_func=lambda i: commit_labels[i],
            key="gh_post_new",
        )

    base_sha = commits[base_idx]["sha"]
    new_sha = commits[new_idx]["sha"]

    if base_sha == new_sha:
        st.warning("Base and new commits must be different. Please select different commits.")
        return

    analyze_clicked = st.button("🔍 Analyze Change Impact", key="btn_gh_post_analyze")

    # ── Run Analysis ─────────────────────────────────────────────────────
    if analyze_clicked or st.session_state.get("gh_post_last_comparison") == f"{base_sha}_{new_sha}":
        st.session_state["gh_post_last_comparison"] = f"{base_sha}_{new_sha}"

        with st.spinner("Comparing commits and analyzing change impact…"):
            try:
                result = analyze_github_post_change(
                    owner, repo, base_sha, new_sha, token
                )
            except GitHubAPIError as e:
                st.error(f"❌ Comparison failed: {str(e)}")
                return

        if result["status"] == "identical":
            st.info("The selected commits are identical — no changes detected.")
            return

        # ── Change Summary Metrics Row ───────────────────────────────────
        st.markdown(
            '<div style="font-size:16px; font-weight:700; color:var(--cia-text); margin:16px 0 10px;">'
            '📊 Change Summary</div>',
            unsafe_allow_html=True,
        )

        m1, m2, m3, m4, m5 = st.columns(5)
        with m1:
            st.markdown(metric_card(result["total_files_changed"], "Files Changed"), unsafe_allow_html=True)
        with m2:
            st.markdown(metric_card(result["modified_count"], "Modified"), unsafe_allow_html=True)
        with m3:
            st.markdown(metric_card(result["added_count"], "Added"), unsafe_allow_html=True)
        with m4:
            st.markdown(metric_card(result["deleted_count"], "Deleted"), unsafe_allow_html=True)
        with m5:
            st.markdown(
                f'<div class="metric-card"><div class="metric-value" style="font-size:20px;padding-top:4px;">'
                f'{severity_pill(result["top_overall_risk"])}</div>'
                f'<div class="metric-label">Top Change Risk</div></div>',
                unsafe_allow_html=True,
            )

        st.markdown('<hr class="cia-divider">', unsafe_allow_html=True)

        # ── Academic Limitation Disclaimer ───────────────────────────────
        st.markdown(
            '<div style="background:rgba(227,179,65,0.08); border:1px solid rgba(227,179,65,0.3); '
            'border-radius:8px; padding:10px 14px; margin-bottom:14px; font-size:12px; '
            'color:var(--cia-text-muted); line-height:1.6;">'
            'ℹ️ <b>Academic Note on External Repository Analysis:</b> '
            'Structural ripple evidence and risk assessments are evaluated using lightweight static analysis. '
            'Ground-truth traceability matrices are <b>not available</b> for arbitrary external repositories. '
            'Function extraction uses regex-based boundary detection across supported languages.'
            '</div>',
            unsafe_allow_html=True,
        )

        # ── Per-File Impact Reports ──────────────────────────────────────
        st.markdown(
            '<div style="font-size:16px; font-weight:700; color:var(--cia-text); margin:10px 0;">'
            '📄 File-Level Impact Analysis</div>',
            unsafe_allow_html=True,
        )

        file_reports = result["file_reports"]
        if not file_reports:
            st.info("No file changes detected between the selected commits.")
            return

        fr_filter = st.radio(
            "Filter changed files:",
            ["All Changed Files", "Modified Only", "Added Only", "Deleted Only"],
            horizontal=True,
            label_visibility="collapsed",
            key="gh_post_file_filter",
        )
        if fr_filter == "Modified Only":
            display_files = [fr for fr in file_reports if fr["status"] == "modified"]
        elif fr_filter == "Added Only":
            display_files = [fr for fr in file_reports if fr["status"] == "added"]
        elif fr_filter == "Deleted Only":
            display_files = [fr for fr in file_reports if fr["status"] == "removed"]
        else:
            display_files = file_reports

        for fr in display_files:
            _render_changed_file_card(fr, owner, repo, selected_branch, new_sha)


def _render_changed_file_card(fr: dict, owner: str, repo: str, branch: str, commit_sha: str):
    """Render an impact card for a single changed file in Mode 2 using native Streamlit containers."""
    safe_name = fr["basename"]
    safe_path = fr["filename"]
    lang_label = fr.get("language", detect_language(fr["basename"]))
    status = fr["status"]

    status_icons = {"added": "🟢 Added", "modified": "🟡 Modified", "removed": "🔴 Deleted", "renamed": "🔄 Renamed"}
    status_label = status_icons.get(status, f"⚪ {status}")

    viewer_url = (
        f"/viewer?type=github&repo={urllib.parse.quote(f'{owner}/{repo}')}"
        f"&branch={urllib.parse.quote(commit_sha)}"
        f"&file={urllib.parse.quote(fr['filename'])}"
    )
    if fr.get("changed_lines"):
        lines_param = ",".join(str(l) for l in fr["changed_lines"][:50])
        viewer_url += f"&lines={lines_param}"

    with st.container(border=True):
        c_title, c_btn = st.columns([3.8, 1.2])
        with c_title:
            st.markdown(
                f'<div style="display:flex; align-items:center; gap:8px; margin-bottom:2px; flex-wrap:wrap;">'
                f'<span style="font-size:12px; font-weight:600; color:var(--cia-text-faint);">{status_label}</span>'
                f'<span style="font-family:JetBrains Mono, monospace; font-size:16px; font-weight:700; color:var(--cia-accent);">{html.escape(safe_name)}</span>'
                f'<span style="font-size:11px; color:var(--cia-text-faint); font-family:JetBrains Mono, monospace;">({lang_label} · {html.escape(safe_path)})</span>'
                f'<span style="font-size:12px; font-family:JetBrains Mono, monospace; margin-left:6px;"><span style="color:#3FB950;">+{fr["additions"]}</span> <span style="color:#F85149;">−{fr["deletions"]}</span></span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with c_btn:
            st.link_button("Inspect Source ↗", viewer_url, use_container_width=True)

        c_risk, c_lines, c_dep, c_trace = st.columns(4)
        with c_risk:
            st.caption("Overall Impact Risk")
            st.markdown(severity_pill(fr["risk_tier"]), unsafe_allow_html=True)
        with c_lines:
            st.caption("Diff Summary")
            st.markdown(f'<b style="font-size:14px; color:var(--cia-text);">{fr["changes"]} lines</b> (<span style="color:#3FB950;">+{fr["additions"]}</span> <span style="color:#F85149;">−{fr["deletions"]}</span>)', unsafe_allow_html=True)
        with c_dep:
            st.caption("Dependency Reach")
            st.markdown(f'<span style="font-size:13px; font-weight:600;">{fr["structural_badge"]} {fr["structural_reach"]}</span>', unsafe_allow_html=True)
        with c_trace:
            st.caption("Traceability Status")
            st.markdown('<span style="font-size:11px; color:var(--cia-text-faint);">N/A (External Repo)</span>', unsafe_allow_html=True)

        # Changed methods / functions pills
        if fr.get("changed_methods"):
            method_pills = []
            for m in fr["changed_methods"][:8]:
                mod_icon = "🔧" if m.get("is_directly_modified") else "📌"
                method_pills.append(
                    f'<span style="background:var(--cia-surface2); border:1px solid var(--cia-border); '
                    f'padding:2px 8px; border-radius:4px; font-size:11px; font-family:JetBrains Mono,monospace; '
                    f'margin:2px; display:inline-block;">{mod_icon} {html.escape(m["name"])}()</span>'
                )
            st.markdown(
                '<div style="margin-top:6px;">'
                '<span style="font-size:11px; font-weight:600; color:var(--cia-text-faint); text-transform:uppercase;">Changed Methods: </span>'
                + "".join(method_pills)
                + '</div>',
                unsafe_allow_html=True,
            )

        if fr.get("risk_rationale"):
            st.caption(f"**Rationale:** {fr['risk_rationale']}")

