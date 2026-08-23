"""
services/impact_engine.py
Hybrid Change Impact Analysis Orchestrator.

Combines three distinct evidence layers:
1. ML Relationship Analysis (XGBoost Relationship Confidence + Semantic Cosine Similarity)
2. Traceability Evidence (Verified ground-truth traceability links)
3. Dependency Propagation (Call graph traversal for direct/indirect impacted methods)

Outputs structured impact reports and transparent overall impact risk assessments.
"""

from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path
from services.ml_engine import (
    load_ml_artifacts,
    predict_pair,
    rank_code_candidates_for_req,
    rank_req_candidates_for_code
)
from services.data_loader import (
    load_all_requirements,
    load_all_code_texts,
    build_file_index
)


def get_impacted_methods(changed_method: str, callgraph: Dict[str, dict]) -> List[str]:
    """Return all methods that directly call or are called by the given method."""
    impacted = []
    if changed_method in callgraph:
        impacted.extend(callgraph[changed_method].get("calls", []))
        impacted.extend(callgraph[changed_method].get("called_by", []))
    return list(set(impacted))


def get_methods_for_class(class_name: str, callgraph: Dict[str, dict]) -> List[str]:
    """Return all methods belonging to a specific class in the call graph."""
    methods = []
    for method_key, meta in callgraph.items():
        if meta.get("class_name") == class_name:
            methods.append(method_key)
    return methods


def get_class_dependency_impact(class_name: str, callgraph: Dict[str, dict]) -> List[str]:
    """
    Find all direct and transitively connected methods for a class.
    Includes the class's own methods plus all methods calling or called by them.
    """
    impacted = []
    for method_key, meta in callgraph.items():
        if meta.get("class_name") == class_name:
            impacted.append(method_key)
            neighbors = get_impacted_methods(method_key, callgraph)
            impacted.extend(neighbors)
    return list(set(impacted))


def compute_dependency_reach(method_count: int) -> Tuple[str, str]:
    """
    Compute dependency reach tier from the count of impacted methods.
    Returns: (reach_tier, badge)
    """
    if method_count > 10:
        return "HIGH", "🔴"
    elif method_count > 5:
        return "MEDIUM", "🟠"
    elif method_count > 0:
        return "LOW", "🟢"
    return "NONE", "⚪"


def evaluate_overall_impact_risk(
    is_verified: bool,
    ml_score: float,
    dependency_count: int
) -> Tuple[str, str, str]:
    """
    Explicit, transparent decision table for Overall Impact Risk.
    
    Returns:
        (overall_risk, badge, rationale)
    """
    reach_tier, _ = compute_dependency_reach(dependency_count)

    # Policy 1: Verified Link + Significant Dependency Reach -> HIGH
    if is_verified and reach_tier in ["HIGH", "MEDIUM"]:
        return "HIGH", "🔴", f"Verified Traceability Link + {reach_tier} Dependency Reach ({dependency_count} methods)"

    # Policy 2: High ML Confidence + High Dependency Reach -> HIGH
    if ml_score >= 0.70 and reach_tier == "HIGH":
        return "HIGH", "🔴", f"High ML Relationship Score ({ml_score*100:.1f}%) + High Dependency Reach ({dependency_count} methods)"

    # Policy 3: Verified Link with localized/zero reach -> MEDIUM
    if is_verified:
        return "MEDIUM", "🟠", f"Verified Traceability Link + Localized Reach ({dependency_count} methods)"

    # Policy 4: High ML Confidence with moderate/low reach -> MEDIUM
    if ml_score >= 0.70:
        return "MEDIUM", "🟠", f"High ML Relationship Score ({ml_score*100:.1f}%) + {reach_tier} Dependency Reach ({dependency_count} methods)"

    # Policy 5: Moderate ML Confidence + High Dependency Reach -> MEDIUM
    if ml_score >= 0.40 and reach_tier == "HIGH":
        return "MEDIUM", "🟠", f"Moderate ML Score ({ml_score*100:.1f}%) + High Dependency Reach ({dependency_count} methods)"

    # Policy 6: Moderate ML Confidence with lower reach -> LOW
    if ml_score >= 0.40:
        return "LOW", "🟢", f"Moderate ML Score ({ml_score*100:.1f}%) with Localized Scope ({dependency_count} methods)"

    # Policy 7: Low ML Confidence, Unverified -> LOW
    return "LOW", "🟢", f"Unverified Link & Low ML Relationship Score ({ml_score*100:.1f}%)"


# Backward-compatible severity alias
def compute_severity(count: int) -> Tuple[str, str]:
    """Preserved for backward compatibility."""
    reach, badge = compute_dependency_reach(count)
    if reach == "NONE":
        return "LOW", "🟢"
    return reach, badge


def analyze_req_to_code(
    requirement: str,
    req_to_code: Dict[str, list],
    callgraph: Dict[str, dict],
    file_index: Optional[Dict[str, str]] = None,
    all_req_texts: Optional[Dict[str, str]] = None,
    all_code_texts: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Execute 3-layer hybrid impact analysis for Requirement -> Code mode.
    
    Returns structured report with:
      - related_codes (verified ground truth)
      - impacted_methods (call graph neighbors)
      - code_to_methods (mapping)
      - artifacts_report (full per-artifact multi-layer breakdown)
      - summary_metrics (overview counters)
    """
    if file_index is None:
        file_index = build_file_index()
    if all_req_texts is None:
        all_req_texts = load_all_requirements()
    if all_code_texts is None:
        all_code_texts = load_all_code_texts()

    req_text = all_req_texts.get(requirement, "")
    verified_codes = set(req_to_code.get(requirement, []))

    # 1. Layer 1: ML Relationship Ranking
    artifacts = load_ml_artifacts()
    ml_rankings = rank_code_candidates_for_req(requirement, req_text, all_code_texts, artifacts)

    # 2. Layer 2 & 3: Dependency Propagation & Risk Synthesis
    detailed_artifacts = []
    all_impacted_methods = []
    code_to_methods = {}

    for item in ml_rankings:
        code_file = item["code_file"]
        class_name = code_file.replace(".java", "")
        is_verified = code_file in verified_codes

        # Call graph propagation for this code artifact
        methods_impacted = get_class_dependency_impact(class_name, callgraph)
        dep_count = len(methods_impacted)
        reach_tier, reach_badge = compute_dependency_reach(dep_count)

        # Risk assessment
        risk_tier, risk_badge, rationale = evaluate_overall_impact_risk(
            is_verified=is_verified,
            ml_score=item["relationship_score"],
            dependency_count=dep_count
        )

        if is_verified or item["predicted_label"] == 1 or risk_tier in ["HIGH", "MEDIUM"]:
            code_to_methods[code_file] = methods_impacted
            all_impacted_methods.extend(methods_impacted)

        detailed_artifacts.append({
            "artifact_name": code_file,
            "artifact_type": "Java Source Code",
            "ml_relationship_score": item["relationship_score"],
            "ml_predicted_label": item["predicted_label"],
            "ml_confidence_level": item["confidence_level"],
            "cosine_similarity": item["cosine_similarity"],
            "verified_traceability": is_verified,
            "dependency_reach": reach_tier,
            "dependency_badge": reach_badge,
            "impacted_method_count": dep_count,
            "impacted_methods": methods_impacted,
            "overall_impact_risk": risk_tier,
            "risk_badge": risk_badge,
            "risk_rationale": rationale
        })

    unique_impacted_methods = list(set(all_impacted_methods))
    overall_reach, reach_color = compute_dependency_reach(len(unique_impacted_methods))

    # Calculate overall top risk
    high_count = sum(1 for a in detailed_artifacts if a["overall_impact_risk"] == "HIGH")
    med_count = sum(1 for a in detailed_artifacts if a["overall_impact_risk"] == "MEDIUM")
    low_count = sum(1 for a in detailed_artifacts if a["overall_impact_risk"] == "LOW")

    if high_count > 0:
        top_risk, top_risk_color = "HIGH", "🔴"
    elif med_count > 0:
        top_risk, top_risk_color = "MEDIUM", "🟠"
    else:
        top_risk, top_risk_color = "LOW", "🟢"

    return {
        # Preserved backward-compatible keys
        "related_codes": list(verified_codes),
        "impacted_methods": unique_impacted_methods,
        "code_to_methods": code_to_methods,
        "severity": overall_reach if overall_reach != "NONE" else "LOW",
        "severity_color": reach_color,

        # New Multi-Layer Evidence Structure
        "artifacts_report": detailed_artifacts,
        "summary_metrics": {
            "requirement_file": requirement,
            "total_candidates_analyzed": len(detailed_artifacts),
            "verified_links_count": len(verified_codes),
            "ml_predicted_links_count": sum(1 for a in detailed_artifacts if a["ml_predicted_label"] == 1),
            "high_risk_count": high_count,
            "medium_risk_count": med_count,
            "low_risk_count": low_count,
            "total_impacted_methods": len(unique_impacted_methods),
            "overall_dependency_reach": overall_reach,
            "top_overall_risk": top_risk,
            "top_overall_risk_badge": top_risk_color
        }
    }


def analyze_code_to_req(
    selected_code: str,
    code_to_req: Dict[str, list],
    callgraph: Dict[str, dict],
    all_req_texts: Optional[Dict[str, str]] = None,
    all_code_texts: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Execute 3-layer hybrid impact analysis for Code -> Requirement mode.
    
    Returns structured report with:
      - related_requirements (verified ground truth)
      - impacted_methods (call graph neighbors for the selected code)
      - artifacts_report (full per-requirement multi-layer breakdown)
      - summary_metrics (overview counters)
    """
    if all_req_texts is None:
        all_req_texts = load_all_requirements()
    if all_code_texts is None:
        all_code_texts = load_all_code_texts()

    code_text = all_code_texts.get(selected_code, "")
    verified_reqs = set(code_to_req.get(selected_code, []))
    class_name = selected_code.replace(".java", "")

    # 1. Dependency Analysis for the selected code
    impacted_methods = get_class_dependency_impact(class_name, callgraph)
    dep_reach, reach_badge = compute_dependency_reach(len(impacted_methods))

    # 2. Layer 1: ML Relationship Ranking across all requirements
    artifacts = load_ml_artifacts()
    ml_rankings = rank_req_candidates_for_code(selected_code, code_text, all_req_texts, artifacts)

    # 3. Layer 2 & 3: Risk Synthesis per candidate requirement
    detailed_artifacts = []
    for item in ml_rankings:
        req_file = item["req_file"]
        is_verified = req_file in verified_reqs

        risk_tier, risk_badge, rationale = evaluate_overall_impact_risk(
            is_verified=is_verified,
            ml_score=item["relationship_score"],
            dependency_count=len(impacted_methods)
        )

        detailed_artifacts.append({
            "artifact_name": req_file,
            "artifact_type": "Software Requirement Document",
            "ml_relationship_score": item["relationship_score"],
            "ml_predicted_label": item["predicted_label"],
            "ml_confidence_level": item["confidence_level"],
            "cosine_similarity": item["cosine_similarity"],
            "verified_traceability": is_verified,
            "dependency_reach": dep_reach,
            "dependency_badge": reach_badge,
            "impacted_method_count": len(impacted_methods),
            "impacted_methods": impacted_methods,
            "overall_impact_risk": risk_tier,
            "risk_badge": risk_badge,
            "risk_rationale": rationale
        })

    high_count = sum(1 for a in detailed_artifacts if a["overall_impact_risk"] == "HIGH")
    med_count = sum(1 for a in detailed_artifacts if a["overall_impact_risk"] == "MEDIUM")
    low_count = sum(1 for a in detailed_artifacts if a["overall_impact_risk"] == "LOW")

    if high_count > 0:
        top_risk, top_risk_color = "HIGH", "🔴"
    elif med_count > 0:
        top_risk, top_risk_color = "MEDIUM", "🟠"
    else:
        top_risk, top_risk_color = "LOW", "🟢"

    return {
        # Preserved backward-compatible keys
        "related_requirements": list(verified_reqs),
        "impacted_methods": impacted_methods,
        "severity": dep_reach if dep_reach != "NONE" else "LOW",
        "severity_color": reach_badge,

        # New Multi-Layer Evidence Structure
        "artifacts_report": detailed_artifacts,
        "summary_metrics": {
            "code_file": selected_code,
            "total_candidates_analyzed": len(detailed_artifacts),
            "verified_links_count": len(verified_reqs),
            "ml_predicted_links_count": sum(1 for a in detailed_artifacts if a["ml_predicted_label"] == 1),
            "high_risk_count": high_count,
            "medium_risk_count": med_count,
            "low_risk_count": low_count,
            "total_impacted_methods": len(impacted_methods),
            "overall_dependency_reach": dep_reach,
            "top_overall_risk": top_risk,
            "top_overall_risk_badge": top_risk_color
        }
    }
