# Intelligent Change Impact Analysis in Requirements Using ML and Traceability Links

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.43%2B-FF4B4B.svg)](https://streamlit.io/)
[![XGBoost](https://img.shields.io/badge/XGBoost-3.2.0-orange.svg)](https://xgboost.readthedocs.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An AI-assisted, multi-layer Software Change Impact Analysis (CIA) system designed to accurately identify, trace, and visualize the cascading ripple effects of software requirement and code modifications in enterprise software systems.

---

## 📌 1. Project Overview & Problem Statement

In evolving software systems, a single requirement or source code modification can trigger ripple effects across multiple modules, database entities, and dependent classes. Traditional Change Impact Analysis techniques rely either on manual inspection (which is error-prone, subjective, and labor-intensive) or simple keyword matching (which yields high false positive rates).

This project develops an intelligent, **bidirectional hybrid CIA engine** that evaluates requirement-code relationships by combining:
1. **Machine Learning Relationship Confidence** (Lexical n-grams + Dense Semantic Embeddings + Gradient Boosting),
2. **Ground-Truth Traceability Matrix Verification**,
3. **Static Method Call Graph Traversal**, and
4. **Deterministic Multi-Layer Risk Decision Policy**.

---

## 🔬 2. System Architecture: 4-Stage Hybrid Pipeline

```
                                [ User Input ]
               (Requirement UC ID  OR  Java Code Artifact)
                                      │
                                      ▼
     ┌─────────────────────────────────────────────────────────────────┐
     │  STAGE 1: ML Relationship Prediction                            │
     │  • Feature Extractor: 500 TF-IDF + 1 SBERT Cosine Similarity    │
     │  • Classifier: XGBoost Inference Engine (models/xgb_model.pkl)  │
     │  • Output: ML Relationship Score (0.00% – 100.00%)              │
     │            ML Confidence Level (HIGH ≥ 70%, MODERATE, LOW)      │
     └────────────────────────────────┬────────────────────────────────┘
                                      │
                                      ▼
     ┌─────────────────────────────────────────────────────────────────┐
     │  STAGE 2: Traceability Verification                             │
     │  • Cross-references candidate pair with iTrust answer matrix    │
     │  • Output: Traceability Evidence Status                         │
     │            (✓ Verified Traceability  /  ⚡ ML Predicted Candidate)│
     └────────────────────────────────┬────────────────────────────────┘
                                      │
                                      ▼
     ┌─────────────────────────────────────────────────────────────────┐
     │  STAGE 3: Call Graph / Dependency Reach Analysis                │
     │  • Static Call Graph Traversal (itrust_method_callgraph.json)   │
     │  • Extracts direct callers/callees & transitive method reach    │
     │  • Output: Dependency Reach Tier (HIGH > 10, MEDIUM, LOW, NONE) │
     └────────────────────────────────┬────────────────────────────────┘
                                      │
                                      ▼
     ┌─────────────────────────────────────────────────────────────────┐
     │  STAGE 4: Composite Impact Risk Policy & Classification         │
     │  • 7-Tier Deterministic Decision Policy Table                   │
     │  • Synthesizes Stages 1, 2, and 3 into actionable outcomes:     │
     │    🔴 HIGH  /  🟠 MEDIUM  /  🟢 LOW                             │
     │  • Generates human-readable Risk Rationale for every candidate  │
     └─────────────────────────────────────────────────────────────────┘
```

---

## 📊 3. Deterministic 7-Tier Risk Decision Policy

The system deterministically synthesizes evidence from all analysis stages using an explicit decision matrix:

| Rule | Traceability Status (Stage 2) | ML Confidence (Stage 1) | Dependency Reach (Stage 3) | Overall Impact Risk (Stage 4) | Risk Rationale |
|:---:|:---:|:---:|:---:|:---:|:---|
| **1** | Verified | Any | HIGH / MEDIUM | **🔴 HIGH** | Verified Traceability Link + High Dependency Reach |
| **2** | Unverified | $\ge 70\%$ (HIGH) | HIGH | **🔴 HIGH** | High ML Relationship Score + High Dependency Reach |
| **3** | Verified | Any | LOW / NONE | **🟠 MEDIUM** | Verified Traceability Link + Localized Reach |
| **4** | Unverified | $\ge 70\%$ (HIGH) | MEDIUM / LOW | **🟠 MEDIUM** | High ML Relationship Score + Moderate/Low Reach |
| **5** | Unverified | $40\% - 69\%$ (MODERATE) | HIGH | **🟠 MEDIUM** | Moderate ML Score + High Dependency Reach |
| **6** | Unverified | $40\% - 69\%$ (MODERATE) | LOW / NONE | **🟢 LOW** | Moderate ML Score with Localized Scope |
| **7** | Unverified | $< 40\%$ (LOW) | Any | **🟢 LOW** | Unverified Link & Low ML Relationship Score |

---

## 📈 4. Machine Learning Pipeline & Verified Performance

### Dataset Specifications (iTrust Traceability Benchmark)
- **Source Artifacts**: 131 Software Requirement Documents (Use Cases)
- **Target Artifacts**: 226 Java Source Code Classes (DAO, Action, Bean layers)
- **Ground-Truth Matrix**: 286 Verified Traceability Links
- **Total Possible Pairs**: 29,606 pairs

### Feature Engineering & Leakage Protection
- **Feature Vector**: Exactly **501 Features**
  - **500 Features**: TF-IDF lexical n-grams (fitted exclusively on the training split with zero data leakage)
  - **1 Feature**: SBERT semantic cosine similarity (`sentence-transformers/all-MiniLM-L6-v2`)
- **Evaluation Protocol**: Stratified 80/20 train/test split on 572 balanced pairs (457 train / 115 test, `random_state=42`, `negative_sampling_seed=42`).

### Verified Evaluation Results (Stratified Test Split)

| Evaluation Metric | Score | Details |
|---|---|---|
| **Overall Accuracy** | **85.22%** | 98 / 115 test pairs correctly classified |
| **Precision (Linked Class)** | **81.25%** | 52 / 64 positive predictions correct |
| **Recall (Linked Class)** | **91.23%** | 52 / 57 ground-truth links recovered |
| **F1-Score (Linked Class)** | **85.95%** | Harmonic mean of linked class precision & recall |
| **Precision (Unlinked Class)** | **90.20%** | 46 / 51 negative predictions correct |
| **Recall (Unlinked Class)** | **79.31%** | 46 / 58 unlinked pairs correctly identified |
| **Macro Average F1** | **85.18%** | Balanced harmonic mean across both classes |

### Confusion Matrix
```
               Predicted Negative    Predicted Positive
Actual Negative        46 (TN)               12 (FP)
Actual Positive         5 (FN)               52 (TP)
```

> **Note on Metric Interpretation**: The XGBoost classifier was trained on a 1:1 balanced sample of positive and negative pairs. The model score represents **ML Relationship Confidence** that a requirement-code pair shares a traceability link.

---

## 🖥️ 5. User Interface & Key Capabilities

1. **Requirement-to-Code Analysis (`Req → Code`)**:
   - Search requirements by Use Case ID or keyword (e.g. `UC10E1`, `password`, `allergy`).
   - Generates ranked candidate code artifacts with live ML relationship confidence scores, traceability badges, and dependency reach badges.
   - Interactive filtering (Actionable High/Medium risk, Verified links only, ML predicted candidates).

2. **Code-to-Requirement Analysis (`Code → Req`)**:
   - Select a Java class (e.g. `AuthDAO.java`, `PatientDAO.java`).
   - Identifies affected use case specifications and downstream calling/called methods across the system.

3. **High-Fidelity Full-Screen Artifact & Method Viewer (`/viewer`)**:
   - **Left Panel (Impact Context)**: Displays trigger requirement, verified traceability badge, ML score with visual progress bar, dependency reach, overall risk pill, and interactive **Impacted Methods Navigator**.
   - **Right Panel (Main Code Viewer)**: Line-numbered Java source viewer with automatic highlighting of impacted method declaration lines, live in-code keyword search, Call Graph Matrix tab, and Traced Requirements tab.

---

## 📂 6. Repository Directory Structure

```
.
├── Signed Project Synopsis.docx     # Academic project submission document
├── README.md                        # Comprehensive system documentation
├── requirements.txt                 # Python package dependencies
├── .gitignore                       # Git ignore configuration
└── iTrust/                          # Main Application Package
    ├── app.py                       # Main Streamlit dashboard router
    ├── FINAL_SYSTEM_STATUS.md       # Full engineering audit and system reference
    ├── XGBoost.ipynb                # Leakage-free training and validation notebook
    ├── CIA_System.ipynb             # Interactive system analysis notebook
    ├── .streamlit/
    │   └── config.toml              # Streamlit theme & UI styling configuration
    ├── models/                      # Exported ML model artifacts (< 1 MB)
    │   ├── xgb_model.pkl            # Trained XGBoost model (501 features)
    │   ├── tfidf_vectorizer.pkl     # Fitted TF-IDF vectorizer (500 features)
    │   ├── req_embeddings.pkl       # SBERT requirement embeddings
    │   ├── code_embeddings.pkl      # SBERT code embeddings
    │   └── metadata.json            # Model lineage & verified metrics
    ├── services/                    # Backend Analysis Services
    │   ├── ml_engine.py             # Sub-millisecond cached ML inference service
    │   ├── impact_engine.py         # 4-stage hybrid analysis & 7-tier decision policy
    │   ├── data_loader.py           # Cached dataset, call graph & requirement loaders
    │   └── __init__.py
    ├── ui/                          # Frontend UI Presentation
    │   ├── styles.py                # CSS design system & multi-layer cards
    │   ├── req_to_code.py           # Requirement → Code analysis UI
    │   ├── code_to_req.py           # Code → Requirement analysis UI
    │   └── __init__.py
    ├── pages/
    │   └── viewer.py                # 2-column source, method & requirement viewer
    ├── code/                        # 226 iTrust Java source files
    ├── req/                         # 131 iTrust requirement text files
    ├── req_preprocessed/            # Preprocessed requirement files
    ├── metrics/                     # Static analysis metric CSVs
    └── itrust_method_callgraph.json # Static method call graph
```

---

## ⚡ 7. Quickstart Guide

### Prerequisites
- Python 3.10+ (Tested on Python 3.10 – 3.13)
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/Tanushii/Hybrid_Change_Impact_Analysis.git
cd Hybrid_Change_Impact_Analysis
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Launch the Application
```bash
cd iTrust
streamlit run app.py
```

Access the interactive dashboard in your browser at `http://localhost:8501`.

---

## 👥 8. Author & Academic Context

- **Author**: Tanushree ([@Tanushii](https://github.com/Tanushii))
- **Project Title**: Intelligent Change Impact Analysis in Requirements Using ML and Traceability Links
- **Dataset Source**: iTrust Medical Records Benchmark Dataset
