"""
services/github_impact_engine.py
GitHub Change Impact Analysis Engine for Mode 1 (Predictive) and Mode 2 (Post-Change).

Responsibilities:
1. Dynamic Language Detection & Lightweight Structural Extraction (Java, Python, JS/TS, Go, C/C++/C#, Docs).
2. Model-based Relationship Similarity Scoring (TF-IDF + SBERT semantic cosine similarity).
3. External Repository Risk Policy & Academic Rationale Generation.
4. Mode 1: Predictive impact analysis for planned file modifications.
5. Mode 2: Post-change impact analysis comparing commits, changed line ranges, and modified methods.
6. Purely dynamic repository exploration without hardcoded dataset paths.
"""

import re
import html
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple, Optional, Any, Set
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from services.ml_engine import load_ml_artifacts, MLArtifacts
from services.github_service import compare_commits, get_file_content, parse_diff_hunks, get_file_tree

logger = logging.getLogger(__name__)

# ── Concurrent file-fetching helper ──────────────────────────────────────────

def _fetch_files_concurrent(
    owner: str,
    repo: str,
    paths: List[str],
    ref: str,
    token: Optional[str] = None,
    max_workers: int = 12,
    existing_map: Optional[Dict[str, str]] = None
) -> Dict[str, str]:
    """
    Fetch multiple file contents from GitHub in parallel using a thread pool.
    Skips paths already present in existing_map.
    Returns a dict of {path: content}.
    """
    result: Dict[str, str] = {}
    skip = set(existing_map.keys()) if existing_map else set()
    to_fetch = [p for p in paths if p not in skip]

    def _fetch_one(path: str):
        try:
            return path, get_file_content(owner, repo, path, ref=ref, token=token)
        except Exception:
            return path, None

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_fetch_one, p): p for p in to_fetch}
        for future in as_completed(futures):
            path, content = future.result()
            if content is not None:
                result[path] = content

    return result


# ── 1. Language Detection & Lightweight Structural Extractors ────────────────

def detect_language(filename: str) -> str:
    """
    Detect programming language or file type from filename extension.
    """
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    lang_map = {
        ".java": "Java",
        ".py": "Python",
        ".js": "JavaScript",
        ".jsx": "JavaScript (React)",
        ".ts": "TypeScript",
        ".tsx": "TypeScript (React)",
        ".go": "Go",
        ".c": "C",
        ".cpp": "C++",
        ".cc": "C++",
        ".h": "C/C++ Header",
        ".hpp": "C++ Header",
        ".cs": "C#",
        ".rs": "Rust",
        ".rb": "Ruby",
        ".php": "PHP",
        ".sql": "SQL",
        ".md": "Markdown",
        ".txt": "Plain Text",
        ".json": "JSON",
        ".xml": "XML",
        ".yaml": "YAML",
        ".yml": "YAML"
    }
    return lang_map.get(ext, "Generic Source / Text")


def extract_methods_for_file(source_code: str, filename: str) -> List[Dict[str, Any]]:
    """
    Extract declared method, function, or section signatures with line numbers.
    Provides lightweight, extensible structural extraction with graceful fallback.
    """
    if not source_code or not isinstance(source_code, str):
        return []

    lines = source_code.splitlines()
    methods = []
    lang = detect_language(filename)

    # 1. Java Parser
    if lang == "Java":
        method_pattern = re.compile(
            r'^\s*(?:(?:public|private|protected|static|final|native|synchronized|abstract|default)\s+)+'
            r'([\w\<\>\[\]]+)\s+([a-zA-Z_]\w*)\s*\(([^)]*)\)\s*(?:throws\s+[\w\s,]+)?\s*[{;]'
        )
        control_keywords = {"if", "for", "while", "switch", "catch", "synchronized"}

        for idx, line in enumerate(lines, 1):
            clean = line.strip()
            if not clean or clean.startswith("//") or clean.startswith("*") or clean.startswith("/*"):
                continue
            match = method_pattern.match(line)
            if match:
                return_type = match.group(1).strip()
                method_name = match.group(2).strip()
                params = match.group(3).strip()
                if method_name in control_keywords:
                    continue
                methods.append({
                    "name": method_name,
                    "signature": f"{method_name}({params})",
                    "return_type": return_type,
                    "line": idx
                })

    # 2. Python Parser
    elif lang == "Python":
        py_func_pattern = re.compile(r'^\s*(?:async\s+)?def\s+([a-zA-Z_]\w*)\s*\(([^)]*)\)')
        py_class_pattern = re.compile(r'^\s*class\s+([a-zA-Z_]\w*)(?:\([^)]*\))?:')

        for idx, line in enumerate(lines, 1):
            clean = line.strip()
            if not clean or clean.startswith("#"):
                continue
            func_m = py_func_pattern.match(line)
            if func_m:
                f_name = func_m.group(1).strip()
                params = func_m.group(2).strip()
                methods.append({
                    "name": f_name,
                    "signature": f"{f_name}({params})",
                    "return_type": "def",
                    "line": idx
                })
                continue
            class_m = py_class_pattern.match(line)
            if class_m:
                c_name = class_m.group(1).strip()
                methods.append({
                    "name": c_name,
                    "signature": f"class {c_name}",
                    "return_type": "class",
                    "line": idx
                })

    # 3. JavaScript / TypeScript Parser
    elif "JavaScript" in lang or "TypeScript" in lang:
        js_func_pattern = re.compile(r'^\s*(?:export\s+)?(?:async\s+)?function\s+([a-zA-Z_]\w*)\s*\(([^)]*)\)')
        js_arrow_pattern = re.compile(r'^\s*(?:export\s+)?(?:const|let|var)\s+([a-zA-Z_]\w*)\s*=\s*(?:async\s+)?\(([^)]*)\)\s*=>')
        js_method_pattern = re.compile(r'^\s*(?:async\s+)?([a-zA-Z_]\w*)\s*\(([^)]*)\)\s*[{]')

        for idx, line in enumerate(lines, 1):
            clean = line.strip()
            if not clean or clean.startswith("//") or clean.startswith("/*"):
                continue
            f_m = js_func_pattern.match(line)
            if f_m:
                methods.append({
                    "name": f_m.group(1),
                    "signature": f"{f_m.group(1)}({f_m.group(2)})",
                    "return_type": "function",
                    "line": idx
                })
                continue
            a_m = js_arrow_pattern.match(line)
            if a_m:
                methods.append({
                    "name": a_m.group(1),
                    "signature": f"{a_m.group(1)}({a_m.group(2)})",
                    "return_type": "const",
                    "line": idx
                })
                continue
            m_m = js_method_pattern.match(line)
            if m_m and m_m.group(1) not in {"if", "for", "while", "switch", "catch"}:
                methods.append({
                    "name": m_m.group(1),
                    "signature": f"{m_m.group(1)}({m_m.group(2)})",
                    "return_type": "method",
                    "line": idx
                })

    # 4. Go Parser
    elif lang == "Go":
        go_func_pattern = re.compile(r'^\s*func\s+(?:\((?:[^)]*)\)\s+)?([a-zA-Z_]\w*)\s*\(([^)]*)\)')
        for idx, line in enumerate(lines, 1):
            clean = line.strip()
            if not clean or clean.startswith("//"):
                continue
            m = go_func_pattern.match(line)
            if m:
                methods.append({
                    "name": m.group(1),
                    "signature": f"{m.group(1)}({m.group(2)})",
                    "return_type": "func",
                    "line": idx
                })

    # 5. Markdown Header Sections
    elif lang == "Markdown":
        md_pattern = re.compile(r'^(#{1,3})\s+(.+)$')
        for idx, line in enumerate(lines, 1):
            m = md_pattern.match(line.strip())
            if m:
                level = len(m.group(1))
                title = m.group(2).strip()
                methods.append({
                    "name": title,
                    "signature": f"{'#' * level} {title}",
                    "return_type": f"H{level}",
                    "line": idx
                })

    return methods


# Backward compatibility alias
def extract_java_methods(source_code: str) -> List[Dict[str, Any]]:
    """Alias for Java method extraction."""
    return extract_methods_for_file(source_code, "File.java")


def extract_changed_methods_for_file(
    file_content: str,
    changed_lines: List[int],
    filename: str
) -> List[Dict[str, Any]]:
    """
    Identify which declared methods/functions overlap with the changed line numbers from git diff.
    """
    if not file_content:
        return []

    methods = extract_methods_for_file(file_content, filename)
    if not methods or not changed_lines:
        return methods[:5] if methods else []

    lines = file_content.splitlines()
    changed_set = set(changed_lines)
    impacted_methods = []

    for i, m in enumerate(methods):
        m_start = m["line"]
        m_end = methods[i + 1]["line"] - 1 if i + 1 < len(methods) else len(lines)

        method_range = set(range(m_start, m_end + 1))
        if method_range.intersection(changed_set):
            impacted_methods.append({
                "name": m["name"],
                "signature": m["signature"],
                "return_type": m.get("return_type", "method"),
                "line": m["line"],
                "is_directly_modified": True
            })

    if not impacted_methods:
        for m in methods[:5]:
            impacted_methods.append({
                "name": m["name"],
                "signature": m["signature"],
                "return_type": m.get("return_type", "method"),
                "line": m["line"],
                "is_directly_modified": False
            })

    return impacted_methods


# ── 2. Repository Structural Dependency Analysis ─────────────────────────────

def analyze_repository_dependencies(
    target_path: str,
    target_content: str,
    repo_files: List[Dict[str, Any]],
    file_contents_map: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Perform dynamic, lightweight static dependency analysis across arbitrary files in the GitHub repository.
    Does NOT assume iTrust paths or fixed directory structures.
    """
    filename = target_path.split("/")[-1]
    base_symbol = filename.rsplit(".", 1)[0] if "." in filename else filename

    methods = extract_methods_for_file(target_content, filename)
    method_names = {m["name"] for m in methods}

    connected_files = []
    caller_files = []
    callee_files = []

    if file_contents_map:
        for fpath, fcontent in file_contents_map.items():
            if fpath == target_path or not fcontent:
                continue

            other_filename = fpath.split("/")[-1]

            # 1. Other file references target class / module / file symbol (Incoming callers)
            if len(base_symbol) >= 3 and re.search(r'\b' + re.escape(base_symbol) + r'\b', fcontent):
                caller_files.append(fpath)
                connected_files.append(fpath)
                continue

            # 2. Other file references target function / method names
            for m_name in list(method_names)[:10]:
                if len(m_name) >= 3 and re.search(r'\b' + re.escape(m_name) + r'\s*\(', fcontent):
                    caller_files.append(fpath)
                    connected_files.append(fpath)
                    break

            # 3. Target references other file base symbol (Outgoing callees)
            other_base = other_filename.rsplit(".", 1)[0] if "." in other_filename else other_filename
            if len(other_base) >= 3 and re.search(r'\b' + re.escape(other_base) + r'\b', target_content):
                callee_files.append(fpath)
                connected_files.append(fpath)

    unique_connected = sorted(list(set(connected_files)))
    total_count = len(unique_connected)

    if total_count >= 5:
        reach_tier = "HIGH"
        reach_badge = "🔴"
    elif total_count >= 2:
        reach_tier = "MEDIUM"
        reach_badge = "🟠"
    elif total_count == 1:
        reach_tier = "LOW"
        reach_badge = "🟢"
    else:
        reach_tier = "NONE"
        reach_badge = "⚪"

    return {
        "reach_tier": reach_tier,
        "reach_badge": reach_badge,
        "reach_count": total_count,
        "connected_files": unique_connected,
        "caller_files": sorted(list(set(caller_files))),
        "callee_files": sorted(list(set(callee_files))),
        "methods_count": len(methods),
        "methods": methods,
        "language": detect_language(filename)
    }


# ── 3. Model-Based ML Relationship Evidence Scoring ──────────────────────────

def compute_model_relationship_score(
    text_a: str,
    text_b: str,
    artifacts: Optional[MLArtifacts] = None
) -> float:
    """
    Compute lexical & semantic relationship similarity between two texts.
    Returns float score between 0.00 and 1.00.
    """
    if not text_a or not text_b:
        return 0.10

    try:
        if artifacts is None:
            artifacts = load_ml_artifacts()

        # TF-IDF feature cosine similarity
        vec_a = artifacts.vectorizer.transform([text_a[:2000]])
        vec_b = artifacts.vectorizer.transform([text_b[:2000]])
        tfidf_sim = float(cosine_similarity(vec_a, vec_b)[0][0])
        
        final_score = min(max(tfidf_sim * 1.5, 0.05), 0.99)
        return round(final_score, 4)
    except Exception:
        words_a = set(re.findall(r'\w+', text_a.lower()))
        words_b = set(re.findall(r'\w+', text_b.lower()))
        if not words_a or not words_b:
            return 0.10
        jaccard = len(words_a.intersection(words_b)) / float(len(words_a.union(words_b)))
        return round(min(max(jaccard * 2.0, 0.05), 0.95), 4)


# ── 4. External Repository Risk Policy ───────────────────────────────────────

def calculate_external_risk(
    ml_score: float,
    reach_tier: str,
    connected_count: int,
    is_modified_in_diff: bool = False
) -> Tuple[str, str, str]:
    """
    Deterministic risk policy for external GitHub repositories.
    Returns (risk_tier, badge, rationale).
    """
    reach_upper = reach_tier.upper()

    if reach_upper == "HIGH" or (ml_score >= 0.70 and connected_count >= 3):
        return (
            "HIGH",
            "🔴",
            f"High repository structural reach ({connected_count} connected artifacts) and strong model-based relationships."
        )
    elif reach_upper == "MEDIUM" or ml_score >= 0.50 or connected_count >= 2:
        return (
            "MEDIUM",
            "🟠",
            f"Moderate structural connections ({connected_count} related artifacts) across repository."
        )
    else:
        return (
            "LOW",
            "🟢",
            f"Localized artifact with limited structural scope ({connected_count} connections)."
        )


# ── 5. Mode 1: Predictive Analysis (Before Change) ───────────────────────────

def analyze_github_predictive(
    target_path: str,
    target_content: str,
    repo_files: List[Dict[str, Any]],
    file_contents_map: Optional[Dict[str, str]] = None,
    artifacts: Optional[MLArtifacts] = None
) -> Dict[str, Any]:
    """
    Execute Mode 1 Predictive Analysis for a selected repository file.
    """
    filename = target_path.split("/")[-1]

    # 1. Structural Dependency Analysis
    struct_info = analyze_repository_dependencies(target_path, target_content, repo_files, file_contents_map)

    # 2. Score related artifacts in repository
    related_artifacts = []
    if file_contents_map:
        for fpath, fcontent in file_contents_map.items():
            if fpath == target_path:
                continue

            fname = fpath.split("/")[-1]
            score = compute_model_relationship_score(target_content, fcontent, artifacts)
            is_struct_linked = fpath in struct_info["connected_files"]

            effective_score = min(score + (0.20 if is_struct_linked else 0.0), 0.99)
            conf = "HIGH" if effective_score >= 0.70 else "MODERATE" if effective_score >= 0.40 else "LOW"

            risk, badge, rat = calculate_external_risk(effective_score, "HIGH" if is_struct_linked else "LOW", 1 if is_struct_linked else 0)

            related_artifacts.append({
                "path": fpath,
                "filename": fname,
                "language": detect_language(fname),
                "ml_score": effective_score,
                "confidence_level": conf,
                "is_structurally_linked": is_struct_linked,
                "risk_tier": risk,
                "risk_badge": badge,
                "risk_rationale": rat
            })

    related_artifacts.sort(key=lambda x: (x["is_structurally_linked"], x["ml_score"]), reverse=True)

    # Top metrics
    top_ml_score = related_artifacts[0]["ml_score"] if related_artifacts else 0.50
    overall_risk, overall_badge, overall_rationale = calculate_external_risk(
        top_ml_score,
        struct_info["reach_tier"],
        struct_info["reach_count"]
    )

    return {
        "target_file": filename,
        "target_path": target_path,
        "language": struct_info["language"],
        "methods_count": struct_info["methods_count"],
        "methods": struct_info["methods"],
        "structural_reach": struct_info["reach_tier"],
        "structural_badge": struct_info["reach_badge"],
        "connected_files_count": struct_info["reach_count"],
        "connected_files": struct_info["connected_files"],
        "caller_files": struct_info["caller_files"],
        "callee_files": struct_info["callee_files"],
        "top_ml_score": top_ml_score,
        "overall_risk": overall_risk,
        "overall_badge": overall_badge,
        "risk_rationale": overall_rationale,
        "related_artifacts": related_artifacts[:30],
        "traceability_status": "Not Available for External Repository"
    }


# ── 6. Mode 2: Post-Change Analysis (Commit Comparison) ──────────────────────

def analyze_github_post_change(
    owner: str,
    repo: str,
    base_commit: str,
    new_commit: str,
    token: Optional[str] = None,
    file_contents_map: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Execute Mode 2 Post-Change Analysis comparing two commits.
    """
    comparison = compare_commits(owner, repo, base_commit, new_commit, token)
    files = comparison.get("files", [])

    file_reports = []
    added_count = 0
    modified_count = 0
    deleted_count = 0

    t_start = time.perf_counter()

    # ── Stage 1: Build file_contents_map if not pre-populated ────────────────
    if file_contents_map is None:
        file_contents_map = {}

    if not file_contents_map:
        try:
            t0 = time.perf_counter()
            repo_tree = get_file_tree(owner, repo, new_commit, token=token)
            logger.debug("[Mode2] Tree fetch: %.2fs (%d files)", time.perf_counter() - t0, len(repo_tree))

            # Build candidate set: for each changed file fetch same-language neighbours
            # Prioritise same-extension files (same language = stronger dependency signal)
            candidate_paths: List[str] = []
            seen_candidates: set = set()
            for f in files:
                fname = f["filename"]
                if f["status"] == "removed":
                    continue
                target_ext = "." + fname.rsplit(".", 1)[-1] if "." in fname else ""
                for tf in repo_tree:
                    p = tf["path"]
                    if p == fname or p in seen_candidates:
                        continue
                    # Cap: 50 same-language + 5 other-language per changed file
                    if target_ext and p.endswith(target_ext):
                        candidate_paths.append(p)
                        seen_candidates.add(p)
                    elif len([c for c in candidate_paths if not c.endswith(target_ext)]) < 5:
                        candidate_paths.append(p)
                        seen_candidates.add(p)
                    if len(candidate_paths) >= 55:
                        break

            t0 = time.perf_counter()
            fetched = _fetch_files_concurrent(
                owner, repo, candidate_paths, ref=new_commit, token=token,
                max_workers=14, existing_map=file_contents_map
            )
            file_contents_map.update(fetched)
            logger.debug(
                "[Mode2] Concurrent file fetch: %.2fs (%d files, %d workers)",
                time.perf_counter() - t0, len(fetched), 14
            )
        except Exception as exc:
            logger.debug("[Mode2] Tree/fetch error: %s", exc)

    logger.debug("[Mode2] file_contents_map size: %d", len(file_contents_map))

    # ── Stage 2: Per-file analysis (no additional API calls) ─────────────────
    for f in files:
        fname = f["filename"]
        status = f["status"]

        if status == "added":
            added_count += 1
        elif status == "removed":
            deleted_count += 1
        else:
            modified_count += 1

        # Use already-fetched content; only fall back to an API call if missing
        content = file_contents_map.get(fname, "")
        if not content and status != "removed":
            try:
                content = get_file_content(owner, repo, fname, ref=new_commit, token=token)
                file_contents_map[fname] = content
            except Exception:
                content = ""

        # Extract changed methods using already-fetched content
        changed_methods = []
        if content:
            changed_methods = extract_changed_methods_for_file(content, f.get("changed_lines", []), fname)

        # Structural dependency reach — uses in-memory map (no new API calls)
        struct_info = analyze_repository_dependencies(fname, content, [], file_contents_map) if content else {
            "reach_tier": "LOW",
            "reach_badge": "🟢",
            "reach_count": 0,
            "connected_files": [],
            "caller_files": [],
            "callee_files": [],
            "language": detect_language(fname)
        }

        # Calculate file risk
        file_risk, file_badge, file_rationale = calculate_external_risk(
            0.75 if status == "modified" else 0.50,
            struct_info["reach_tier"],
            struct_info["reach_count"],
            is_modified_in_diff=True
        )

        file_reports.append({
            "filename": fname,
            "basename": fname.split("/")[-1],
            "language": struct_info.get("language", detect_language(fname)),
            "status": status,
            "additions": f.get("additions", 0),
            "deletions": f.get("deletions", 0),
            "changes": f.get("changes", 0),
            "changed_lines": f.get("changed_lines", []),
            "changed_hunks": f.get("changed_hunks", []),
            "changed_methods": changed_methods,
            "structural_reach": struct_info["reach_tier"],
            "structural_badge": struct_info["reach_badge"],
            "connected_files": struct_info["connected_files"],
            "risk_tier": file_risk,
            "risk_badge": file_badge,
            "risk_rationale": file_rationale
        })

    # Summary overall change risk
    if any(fr["risk_tier"] == "HIGH" for fr in file_reports):
        top_risk = "HIGH"
    elif any(fr["risk_tier"] == "MEDIUM" for fr in file_reports):
        top_risk = "MEDIUM"
    else:
        top_risk = "LOW"

    return {
        "status": comparison.get("status", "ok"),
        "total_commits": comparison.get("total_commits", 0),
        "total_files_changed": len(files),
        "modified_count": modified_count,
        "added_count": added_count,
        "deleted_count": deleted_count,
        "top_overall_risk": top_risk,
        "file_reports": file_reports
    }
