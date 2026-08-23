"""
services/github_service.py
GitHub REST API Service for Change Impact Analysis System.

Responsibilities:
1. Parse repository identifiers (URLs or owner/repo format).
2. Fetch repository metadata, branches, file trees, and file contents.
3. Fetch commit history and compare commits for diff analysis.
4. Parse unified diff hunks into changed line ranges and line numbers.
5. Securely handle authentication headers without logging or exposing tokens.
6. Robust error handling for rate limits, 404s, 401s, and network issues.
"""

import re
import base64
import urllib.parse
from typing import Dict, List, Tuple, Optional, Any
import requests


# GitHub API Constants
GITHUB_API_BASE = "https://api.github.com"
RAW_GITHUB_BASE = "https://raw.githubusercontent.com"
DEFAULT_TIMEOUT = 12  # seconds


class GitHubAPIError(Exception):
    """Custom exception for GitHub API failures."""
    def __init__(self, message: str, status_code: Optional[int] = None, response_json: Optional[dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_json = response_json or {}


def _get_headers(token: Optional[str] = None) -> Dict[str, str]:
    """
    Construct safe request headers.
    Never logs or exposes the token.
    """
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "CIA-System-Change-Impact-Analysis"
    }
    if token and isinstance(token, str) and token.strip():
        clean_token = token.strip()
        headers["Authorization"] = f"Bearer {clean_token}"
    return headers


def parse_repository(repo_input: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse a GitHub repository identifier from a URL or owner/repo string.
    
    Supported formats:
      - "owner/repo"
      - "https://github.com/owner/repo"
      - "https://github.com/owner/repo.git"
      - "http://github.com/owner/repo"
      - "git@github.com:owner/repo.git"
      
    Returns:
      Tuple of (owner, repo) or (None, None) if parsing fails.
    """
    if not repo_input or not isinstance(repo_input, str):
        return None, None

    cleaned = repo_input.strip().rstrip("/")
    if cleaned.endswith(".git"):
        cleaned = cleaned[:-4]

    # Pattern for git@github.com:owner/repo
    ssh_match = re.match(r"^git@github\.com:([\w\-\.]+)/([\w\-\.]+)$", cleaned, re.IGNORECASE)
    if ssh_match:
        return ssh_match.group(1), ssh_match.group(2)

    # Pattern for https?://github.com/owner/repo/...
    url_match = re.match(r"^https?://github\.com/([\w\-\.]+)/([\w\-\.]+)", cleaned, re.IGNORECASE)
    if url_match:
        return url_match.group(1), url_match.group(2)

    # Pattern for direct owner/repo
    parts = [p.strip() for p in cleaned.split("/") if p.strip()]
    if len(parts) == 2 and re.match(r"^[\w\-\.]+$", parts[0]) and re.match(r"^[\w\-\.]+$", parts[1]):
        return parts[0], parts[1]

    return None, None


def _format_rate_limit_error(resp: requests.Response) -> str:
    """Format a clear and helpful error message when rate limited."""
    remaining = resp.headers.get("x-ratelimit-remaining", "0")
    limit = resp.headers.get("x-ratelimit-limit", "60")
    reset_ts = resp.headers.get("x-ratelimit-reset")
    reset_str = ""
    if reset_ts and reset_ts.isdigit():
        import datetime
        reset_time = datetime.datetime.fromtimestamp(int(reset_ts), tz=datetime.timezone.utc).strftime('%H:%M:%S UTC')
        reset_str = f" Rate limit resets at {reset_time}."
    
    return (
        f"GitHub API rate limit reached ({remaining}/{limit} calls remaining).{reset_str} "
        f"Provide an optional GitHub Personal Access Token (PAT) to increase your quota to 5,000 requests/hour."
    )


def get_rate_limit_status(token: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetch current GitHub API rate limit status.
    Returns: {"limit": int, "remaining": int, "used": int, "reset_time": str, "is_authenticated": bool}
    """
    url = f"{GITHUB_API_BASE}/rate_limit"
    headers = _get_headers(token)
    try:
        resp = requests.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)
        if resp.status_code == 200:
            data = resp.json()
            core = data.get("resources", {}).get("core", {})
            limit = core.get("limit", 60)
            remaining = core.get("remaining", 0)
            reset_ts = core.get("reset", 0)
            import datetime
            reset_time = datetime.datetime.fromtimestamp(reset_ts, tz=datetime.timezone.utc).strftime('%H:%M UTC') if reset_ts else ""
            return {
                "limit": limit,
                "remaining": remaining,
                "used": core.get("used", limit - remaining),
                "reset_time": reset_time,
                "is_authenticated": bool(token and token.strip())
            }
    except Exception:
        pass
    return {"limit": 60, "remaining": 60, "used": 0, "reset_time": "", "is_authenticated": bool(token and token.strip())}


def get_repository_info(owner: str, repo: str, token: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetch repository overview metadata.
    """
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}"
    headers = _get_headers(token)

    try:
        resp = requests.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)
    except requests.RequestException as e:
        raise GitHubAPIError(f"Network error connecting to GitHub: {str(e)}")

    if resp.status_code == 200:
        data = resp.json()
        return {
            "name": data.get("name", repo),
            "full_name": data.get("full_name", f"{owner}/{repo}"),
            "description": data.get("description") or "No description provided.",
            "default_branch": data.get("default_branch", "main"),
            "stars": data.get("stargazers_count", 0),
            "forks": data.get("forks_count", 0),
            "open_issues": data.get("open_issues_count", 0),
            "is_private": data.get("private", False),
            "language": data.get("language") or "Mixed",
            "html_url": data.get("html_url", f"https://github.com/{owner}/{repo}")
        }
    elif resp.status_code == 404:
        raise GitHubAPIError(
            f"Repository '{owner}/{repo}' not found. Please verify the owner/name or provide a PAT if it is private.",
            status_code=404
        )
    elif resp.status_code == 401:
        raise GitHubAPIError("Invalid or expired GitHub Personal Access Token (401 Unauthorized).", status_code=401)
    elif resp.status_code == 403:
        rate_msg = _format_rate_limit_error(resp)
        raise GitHubAPIError(rate_msg, status_code=403)
    else:
        raise GitHubAPIError(f"GitHub API returned error status {resp.status_code}: {resp.text}", status_code=resp.status_code)


def get_branches(owner: str, repo: str, token: Optional[str] = None) -> List[str]:
    """
    Fetch all branch names for a repository, ordering the default branch first.
    """
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/branches"
    headers = _get_headers(token)

    try:
        resp = requests.get(url, headers=headers, timeout=DEFAULT_TIMEOUT, params={"per_page": 100})
    except requests.RequestException as e:
        raise GitHubAPIError(f"Network error fetching branches: {str(e)}")

    if resp.status_code == 200:
        branches = [b.get("name") for b in resp.json() if b.get("name")]
        # Prioritize main / master
        ordered = []
        for pref in ["main", "master"]:
            if pref in branches:
                ordered.append(pref)
                branches.remove(pref)
        ordered.extend(branches)
        return ordered if ordered else ["main"]
    elif resp.status_code == 404:
        raise GitHubAPIError(f"Repository '{owner}/{repo}' branches not found.", status_code=404)
    elif resp.status_code == 401:
        raise GitHubAPIError("Invalid GitHub token for branch retrieval.", status_code=401)
    elif resp.status_code == 403:
        raise GitHubAPIError("GitHub API rate limit exceeded while retrieving branches.", status_code=403)
    else:
        return ["main"]


def get_file_tree(
    owner: str,
    repo: str,
    branch: str = "main",
    token: Optional[str] = None,
    extensions: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Recursively fetch repository file tree for the specified branch.
    Optionally filter by file extensions (e.g. ['.java', '.py', '.txt', '.md']).
    """
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/git/trees/{branch}"
    headers = _get_headers(token)

    try:
        resp = requests.get(url, headers=headers, timeout=DEFAULT_TIMEOUT, params={"recursive": "1"})
    except requests.RequestException as e:
        raise GitHubAPIError(f"Network error fetching file tree: {str(e)}")

    if resp.status_code != 200:
        raise GitHubAPIError(
            f"Failed to fetch file tree for branch '{branch}' (HTTP {resp.status_code}).",
            status_code=resp.status_code
        )

    data = resp.json()
    tree_items = data.get("tree", [])
    files = []

    for item in tree_items:
        if item.get("type") == "blob":  # Regular file
            path = item.get("path", "")
            if not path:
                continue

            # Extension filtering
            if extensions:
                ext_match = any(path.lower().endswith(ext.lower()) for ext in extensions)
                if not ext_match:
                    continue

            filename = path.split("/")[-1]
            files.append({
                "path": path,
                "filename": filename,
                "size": item.get("size", 0),
                "sha": item.get("sha", "")
            })

    return files


def get_file_content(
    owner: str,
    repo: str,
    path: str,
    ref: str = "main",
    token: Optional[str] = None
) -> str:
    """
    Fetch the raw text content of a file in the repository at a given ref (branch or commit SHA).
    """
    headers = _get_headers(token)

    # Strategy 1: Raw GitHub UserContent (Fastest for public repos)
    encoded_path = urllib.parse.quote(path)
    raw_url = f"{RAW_GITHUB_BASE}/{owner}/{repo}/{ref}/{encoded_path}"

    try:
        raw_resp = requests.get(raw_url, headers=headers, timeout=DEFAULT_TIMEOUT)
        if raw_resp.status_code == 200:
            return raw_resp.text
    except requests.RequestException:
        pass  # Fall back to GitHub Contents API

    # Strategy 2: GitHub Contents REST API
    api_url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{encoded_path}"
    try:
        api_resp = requests.get(api_url, headers=headers, timeout=DEFAULT_TIMEOUT, params={"ref": ref})
    except requests.RequestException as e:
        raise GitHubAPIError(f"Network error retrieving file content for '{path}': {str(e)}")

    if api_resp.status_code == 200:
        data = api_resp.json()
        content_b64 = data.get("content", "")
        if content_b64:
            try:
                decoded_bytes = base64.b64decode(content_b64)
                return decoded_bytes.decode("utf-8", errors="replace")
            except Exception as e:
                raise GitHubAPIError(f"Error decoding base64 content for '{path}': {str(e)}")
        # If file is raw download
        download_url = data.get("download_url")
        if download_url:
            dl_resp = requests.get(download_url, headers=headers, timeout=DEFAULT_TIMEOUT)
            if dl_resp.status_code == 200:
                return dl_resp.text
        return ""
    elif api_resp.status_code == 404:
        raise GitHubAPIError(f"File '{path}' not found at ref '{ref}' (404).", status_code=404)
    else:
        raise GitHubAPIError(f"Failed to fetch content for '{path}' (HTTP {api_resp.status_code}).", status_code=api_resp.status_code)


def get_recent_commits(
    owner: str,
    repo: str,
    branch: str = "main",
    token: Optional[str] = None,
    limit: int = 30
) -> List[Dict[str, Any]]:
    """
    Fetch recent commit history for a repository branch.
    """
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/commits"
    headers = _get_headers(token)

    try:
        resp = requests.get(url, headers=headers, timeout=DEFAULT_TIMEOUT, params={"sha": branch, "per_page": limit})
    except requests.RequestException as e:
        raise GitHubAPIError(f"Network error fetching commits: {str(e)}")

    if resp.status_code != 200:
        raise GitHubAPIError(f"Failed to fetch commits for branch '{branch}' (HTTP {resp.status_code}).", status_code=resp.status_code)

    commits = []
    for c in resp.json():
        sha = c.get("sha", "")
        commit_obj = c.get("commit", {})
        author_obj = commit_obj.get("author", {})
        msg = commit_obj.get("message", "").split("\n")[0]  # First line of commit message

        commits.append({
            "sha": sha,
            "short_sha": sha[:7] if sha else "",
            "message": msg if msg else "No commit message",
            "author": author_obj.get("name") or c.get("author", {}).get("login", "Unknown"),
            "date": author_obj.get("date", "")[:10] if author_obj.get("date") else ""
        })

    return commits


def compare_commits(
    owner: str,
    repo: str,
    base_commit: str,
    new_commit: str,
    token: Optional[str] = None
) -> Dict[str, Any]:
    """
    Compare two commits using GitHub's comparison API.
    Returns comparison summary and list of changed files with diff patches.
    """
    if not base_commit or not new_commit:
        raise GitHubAPIError("Base commit and new commit must both be provided.")

    if base_commit.strip() == new_commit.strip():
        return {
            "status": "identical",
            "ahead_by": 0,
            "behind_by": 0,
            "total_commits": 0,
            "files": []
        }

    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/compare/{base_commit}...{new_commit}"
    headers = _get_headers(token)

    try:
        resp = requests.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)
    except requests.RequestException as e:
        raise GitHubAPIError(f"Network error comparing commits: {str(e)}")

    if resp.status_code != 200:
        raise GitHubAPIError(
            f"Failed to compare commits '{base_commit[:7]}' and '{new_commit[:7]}' (HTTP {resp.status_code}).",
            status_code=resp.status_code
        )

    data = resp.json()
    files_raw = data.get("files", [])
    parsed_files = []

    for f in files_raw:
        filename = f.get("filename", "")
        status = f.get("status", "modified")  # added, modified, removed, renamed
        patch = f.get("patch", "")
        changed_lines, changed_hunks = parse_diff_hunks(patch)

        parsed_files.append({
            "filename": filename,
            "basename": filename.split("/")[-1],
            "status": status,
            "additions": f.get("additions", 0),
            "deletions": f.get("deletions", 0),
            "changes": f.get("changes", 0),
            "patch": patch,
            "changed_lines": changed_lines,
            "changed_hunks": changed_hunks
        })

    return {
        "status": data.get("status", "diverged"),
        "ahead_by": data.get("ahead_by", 0),
        "behind_by": data.get("behind_by", 0),
        "total_commits": data.get("total_commits", len(data.get("commits", []))),
        "files": parsed_files
    }


def parse_diff_hunks(patch: str) -> Tuple[List[int], List[str]]:
    """
    Parse unified git diff patch to extract changed line numbers and human-readable line ranges.
    
    Returns:
        (changed_line_numbers, changed_hunks)
        Example: ([108, 109, 110, 362], ["Lines 108–110", "Line 362"])
    """
    if not patch or not isinstance(patch, str):
        return [], []

    changed_lines: List[int] = []
    changed_hunks: List[str] = []

    # Hunk header format: @@ -from_line,from_count +to_line,to_count @@
    hunk_regex = re.compile(r"@@\s+-\d+(?:,\d+)?\s+\+(\d+)(?:,(\d+))?\s+@@")

    current_line = 0
    in_hunk = False
    hunk_start = None
    hunk_end = None

    for raw_line in patch.splitlines():
        match = hunk_regex.match(raw_line)
        if match:
            # Save previous hunk range if any
            if hunk_start is not None:
                if hunk_start == hunk_end:
                    changed_hunks.append(f"Line {hunk_start}")
                else:
                    changed_hunks.append(f"Lines {hunk_start}–{hunk_end}")
            
            start_line = int(match.group(1))
            current_line = start_line
            in_hunk = True
            hunk_start = None
            hunk_end = None
            continue

        if in_hunk:
            if raw_line.startswith("+") and not raw_line.startswith("+++"):
                changed_lines.append(current_line)
                if hunk_start is None:
                    hunk_start = current_line
                hunk_end = current_line
                current_line += 1
            elif raw_line.startswith("-") and not raw_line.startswith("---"):
                # Deletion line in old file; line in new file does not advance
                if hunk_start is None:
                    hunk_start = current_line
                hunk_end = current_line
            else:
                # Context line (unchanged)
                current_line += 1

    # Add final hunk range
    if hunk_start is not None:
        if hunk_start == hunk_end:
            changed_hunks.append(f"Line {hunk_start}")
        else:
            changed_hunks.append(f"Lines {hunk_start}–{hunk_end}")

    return sorted(list(set(changed_lines))), changed_hunks
