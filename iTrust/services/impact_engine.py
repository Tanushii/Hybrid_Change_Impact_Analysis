"""
services/impact_engine.py
Core impact analysis logic, separated from UI rendering.
"""
from services.data_loader import load_callgraph


def get_impacted_methods(changed_method, callgraph):
    """Return all methods that call or are called by the given method."""
    impacted = []
    if changed_method in callgraph:
        impacted.extend(callgraph[changed_method].get("calls", []))
        impacted.extend(callgraph[changed_method].get("called_by", []))
    return list(set(impacted))


def compute_severity(count):
    if count > 10:
        return "HIGH", "🔴"
    elif count > 5:
        return "MEDIUM", "🟠"
    return "LOW", "🟢"


def analyze_req_to_code(requirement, req_to_code, callgraph, file_index):
    """
    Given a requirement, find related code files and impacted methods.
    Returns dict with: related_codes, impacted_methods, severity, severity_color,
    and code_to_methods mapping (filename -> list of impacted method names).
    """
    related_codes = req_to_code.get(requirement, [])
    impacted_methods = []
    code_to_methods = {}   # filename -> [method, ...]

    for method_key in callgraph:
        class_name = callgraph[method_key].get("class_name", "")
        for code in related_codes:
            if code.replace(".java", "") == class_name:
                hits = get_impacted_methods(method_key, callgraph)
                impacted_methods.extend(hits)
                code_to_methods.setdefault(code, []).extend(hits)

    impacted_methods = list(set(impacted_methods))
    for k in code_to_methods:
        code_to_methods[k] = list(set(code_to_methods[k]))

    severity, severity_color = compute_severity(len(impacted_methods))
    return {
        "related_codes": related_codes,
        "impacted_methods": impacted_methods,
        "code_to_methods": code_to_methods,
        "severity": severity,
        "severity_color": severity_color,
    }


def analyze_code_to_req(selected_code, code_to_req, callgraph):
    """
    Given a code file, find related requirements and impacted Java methods
    (from the callgraph — NOT from requirement .txt files).
    Returns dict with: related_requirements, impacted_methods, severity, severity_color.
    """
    related_requirements = code_to_req.get(selected_code, [])
    impacted_methods = []

    for method_key in callgraph:
        class_name = callgraph[method_key].get("class_name", "")
        if selected_code.replace(".java", "") == class_name:
            # Include the method itself and its neighbors
            impacted_methods.append(method_key)
            hits = get_impacted_methods(method_key, callgraph)
            impacted_methods.extend(hits)

    impacted_methods = list(set(impacted_methods))
    severity, severity_color = compute_severity(len(impacted_methods))
    return {
        "related_requirements": related_requirements,
        "impacted_methods": impacted_methods,   # Java side only — correct semantics
        "severity": severity,
        "severity_color": severity_color,
    }
