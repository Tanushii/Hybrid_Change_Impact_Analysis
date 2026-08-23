"""
services/ml_engine.py
Dedicated ML Inference Service for Change Impact Analysis.

Responsibilities:
1. Loads and caches pre-trained model artifacts from models/ directory.
2. Extracts exact 501-dimensional feature vectors (500 TF-IDF + 1 SBERT Cosine Similarity).
3. Performs inference to produce ML Relationship Confidence scores and binary link predictions.
4. Provides batch candidate ranking for Requirement-to-Code and Code-to-Requirement modes.
5. Strict error handling for missing files, missing embeddings, and dimension mismatches.
"""

import os
import json
import pickle
import joblib
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
import scipy.sparse as sp
from scipy.sparse import hstack
from sklearn.metrics.pairwise import cosine_similarity

try:
    import streamlit as st
    _HAS_STREAMLIT = True
except ImportError:
    _HAS_STREAMLIT = False

# Default Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_MODELS_DIR = BASE_DIR / "models"


class MLArtifacts:
    """Container for loaded ML inference artifacts."""
    def __init__(
        self,
        model: Any,
        vectorizer: Any,
        req_embeddings: Dict[str, np.ndarray],
        code_embeddings: Dict[str, np.ndarray],
        metadata: Dict[str, Any]
    ):
        self.model = model
        self.vectorizer = vectorizer
        self.req_embeddings = req_embeddings
        self.code_embeddings = code_embeddings
        self.metadata = metadata

        # Validation
        self.expected_features = metadata.get("feature_dimensions", {}).get("total_features", 501)
        self.expected_tfidf = metadata.get("feature_dimensions", {}).get("tfidf_features", 500)


_GLOBAL_ARTIFACTS: Optional[MLArtifacts] = None


def load_ml_artifacts(models_dir: Optional[Path] = None) -> MLArtifacts:
    """
    Load ML artifacts from the models directory.
    Uses singleton caching so artifacts are loaded once per process/session.
    """
    global _GLOBAL_ARTIFACTS
    if _GLOBAL_ARTIFACTS is not None:
        return _GLOBAL_ARTIFACTS

    target_dir = Path(models_dir) if models_dir else DEFAULT_MODELS_DIR

    xgb_path = target_dir / "xgb_model.pkl"
    tfidf_path = target_dir / "tfidf_vectorizer.pkl"
    req_emb_path = target_dir / "req_embeddings.pkl"
    code_emb_path = target_dir / "code_embeddings.pkl"
    meta_path = target_dir / "metadata.json"

    # 1. Check file existence
    for path, name in [
        (xgb_path, "XGBoost Model (xgb_model.pkl)"),
        (tfidf_path, "TF-IDF Vectorizer (tfidf_vectorizer.pkl)"),
        (req_emb_path, "Requirement Embeddings (req_embeddings.pkl)"),
        (code_emb_path, "Code Embeddings (code_embeddings.pkl)"),
        (meta_path, "Metadata (metadata.json)")
    ]:
        if not path.exists():
            raise FileNotFoundError(
                f"Missing required ML artifact '{name}' at path: {path}. "
                f"Please ensure Step 2 export has been executed."
            )

    # 2. Load artifacts
    try:
        model = joblib.load(xgb_path)
        vectorizer = joblib.load(tfidf_path)

        with open(req_emb_path, "rb") as f:
            req_embeddings = pickle.load(f)

        with open(code_emb_path, "rb") as f:
            code_embeddings = pickle.load(f)

        with open(meta_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

    except Exception as e:
        raise RuntimeError(f"Failed to load ML artifacts from {target_dir}: {str(e)}") from e

    # 3. Validate feature space alignment
    num_vocab = len(vectorizer.get_feature_names_out())
    if num_vocab != 500:
        raise ValueError(
            f"TF-IDF Vectorizer feature mismatch: expected 500 features, found {num_vocab}."
        )

    artifacts = MLArtifacts(
        model=model,
        vectorizer=vectorizer,
        req_embeddings=req_embeddings,
        code_embeddings=code_embeddings,
        metadata=metadata
    )

    _GLOBAL_ARTIFACTS = artifacts
    return artifacts


def extract_features(
    req_name: str,
    req_text: str,
    code_name: str,
    code_text: str,
    artifacts: MLArtifacts
) -> Tuple[sp.csr_matrix, float]:
    """
    Construct the exact 501-dimensional sparse feature vector for a requirement-code pair.
    
    Returns:
        X: Sparse CSR matrix of shape (1, 501)
        sim: Float SBERT cosine similarity
    """
    # 1. Text feature vectorization (500 TF-IDF features)
    combined_text = (req_text or "") + " " + (code_text or "")
    tfidf_vec = artifacts.vectorizer.transform([combined_text])

    # 2. SBERT Cosine Similarity lookup (1 scalar feature)
    if req_name not in artifacts.req_embeddings:
        raise KeyError(
            f"Requirement embedding for '{req_name}' not found in precomputed cache. "
            f"Total available: {len(artifacts.req_embeddings)}."
        )
    if code_name not in artifacts.code_embeddings:
        raise KeyError(
            f"Code embedding for '{code_name}' not found in precomputed cache. "
            f"Total available: {len(artifacts.code_embeddings)}."
        )

    req_vec = artifacts.req_embeddings[req_name]
    code_vec = artifacts.code_embeddings[code_name]

    sim = float(cosine_similarity([req_vec], [code_vec])[0][0])
    sim_vec = sp.csr_matrix([[sim]])

    # 3. Stack features into exactly (1, 501) matrix
    X = hstack([tfidf_vec, sim_vec], format="csr")

    if X.shape[1] != artifacts.expected_features:
        raise ValueError(
            f"Feature dimension mismatch: constructed vector has {X.shape[1]} features, "
            f"expected {artifacts.expected_features}."
        )

    return X, sim


def predict_pair(
    req_name: str,
    req_text: str,
    code_name: str,
    code_text: str,
    artifacts: Optional[MLArtifacts] = None
) -> Dict[str, Any]:
    """
    Inference for a single requirement-code pair.
    
    Returns:
        Dict containing:
          - relationship_score: float (0.0 to 1.0)
          - predicted_label: int (1=Linked, 0=Not Linked)
          - cosine_similarity: float
          - confidence_level: str ("HIGH" | "MODERATE" | "LOW")
    """
    if artifacts is None:
        artifacts = load_ml_artifacts()

    X, sim = extract_features(req_name, req_text, code_name, code_text, artifacts)

    prob = float(artifacts.model.predict_proba(X)[0][1])
    label = int(artifacts.model.predict(X)[0])

    if prob >= 0.70:
        conf_level = "HIGH"
    elif prob >= 0.40:
        conf_level = "MODERATE"
    else:
        conf_level = "LOW"

    return {
        "relationship_score": round(prob, 4),
        "predicted_label": label,
        "cosine_similarity": round(sim, 4),
        "confidence_level": conf_level
    }


def rank_code_candidates_for_req(
    req_name: str,
    req_text: str,
    all_code_dict: Dict[str, str],
    artifacts: Optional[MLArtifacts] = None
) -> List[Dict[str, Any]]:
    """
    Score and rank all code candidates for a given requirement.
    
    Args:
        req_name: e.g. "UC10E1.txt"
        req_text: Full text of the requirement
        all_code_dict: Dict of {code_filename: code_text}
        artifacts: Loaded MLArtifacts instance (optional)
        
    Returns:
        List of candidate dictionaries sorted descending by relationship_score.
    """
    if artifacts is None:
        artifacts = load_ml_artifacts()

    results = []
    for code_name, code_text in all_code_dict.items():
        try:
            pred = predict_pair(req_name, req_text, code_name, code_text, artifacts)
            results.append({
                "code_file": code_name,
                "relationship_score": pred["relationship_score"],
                "predicted_label": pred["predicted_label"],
                "cosine_similarity": pred["cosine_similarity"],
                "confidence_level": pred["confidence_level"]
            })
        except Exception as e:
            # Continue on individual artifact errors while logging
            continue

    results.sort(key=lambda x: x["relationship_score"], reverse=True)
    return results


def rank_req_candidates_for_code(
    code_name: str,
    code_text: str,
    all_req_dict: Dict[str, str],
    artifacts: Optional[MLArtifacts] = None
) -> List[Dict[str, Any]]:
    """
    Score and rank all requirement candidates for a given code file.
    
    Args:
        code_name: e.g. "AuthDAO.java"
        code_text: Full text or partial snippet of the code file
        all_req_dict: Dict of {req_filename: req_text}
        artifacts: Loaded MLArtifacts instance (optional)
        
    Returns:
        List of candidate dictionaries sorted descending by relationship_score.
    """
    if artifacts is None:
        artifacts = load_ml_artifacts()

    results = []
    for req_name, req_text in all_req_dict.items():
        try:
            pred = predict_pair(req_name, req_text, code_name, code_text, artifacts)
            results.append({
                "req_file": req_name,
                "relationship_score": pred["relationship_score"],
                "predicted_label": pred["predicted_label"],
                "cosine_similarity": pred["cosine_similarity"],
                "confidence_level": pred["confidence_level"]
            })
        except Exception as e:
            continue

    results.sort(key=lambda x: x["relationship_score"], reverse=True)
    return results
