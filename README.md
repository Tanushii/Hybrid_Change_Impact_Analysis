# Intelligent Change Impact Analysis in Requirements Using ML and Traceability Links

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.43%2B-FF4B4B.svg)](https://streamlit.io/)
[![XGBoost](https://img.shields.io/badge/XGBoost-3.2.0-orange.svg)](https://xgboost.readthedocs.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An AI-assisted, multi-layer Software Change Impact Analysis (CIA) system designed to accurately identify, trace, and visualize the cascading ripple effects of software requirement and code modifications across local benchmarks and remote GitHub repositories.

---

## 📌 1. Project Overview & Problem Statement

In evolving software systems, a single requirement or source code modification can trigger ripple effects across multiple modules, database entities, and dependent classes. Traditional Change Impact Analysis techniques rely either on manual inspection (which is error-prone, subjective, and labor-intensive) or simple keyword matching (which yields high false positive rates).

This project provides an intelligent, **hybrid multi-mode CIA engine** supporting:
1. **Local iTrust Benchmark Analysis** (Requirement → Code & Code → Requirement with ground-truth verification and call graph propagation),
2. **GitHub Mode 1 — Predictive Analysis** (Analyze potential impact before modifying a remote repository file), and
3. **GitHub Mode 2 — Post-Change Analysis** (Compare commits, extract diff hunks, identify modified methods, and evaluate ripple effects).

---

## 🔬 2. System Architecture: Hybrid Multi-Layer Pipeline

```
                                  [ User Interface ]
                       (Streamlit Sidebar Navigation in app.py)
                         │                                 │
                         ▼                                 ▼
           [ 📁 Local iTrust Benchmark ]         [ 🐙 GitHub Analysis ]
           • Requirement → Code                   • 🔵 Mode 1: Predictive (Before Change)
           • Code → Requirement                   • 🟠 Mode 2: Post-Change (Commit Diff)
                         │                                 │
                         ▼                                 ▼
               [ services/ml_engine.py ]         [ services/github_service.py ]
               [ services/impact_engine.py ]     • Repo info, branch trees & raw files
                         │                       • Commits & diff comparison API
                         │                                 │
                         │                                 ▼
                         │                   [ services/github_impact_engine.py ]
                         │                   • Lightweight static dependency reach
                         │                   • Model-based lexical/semantic similarity
                         │                   • External repository 7-tier risk policy
                         │                                 │
                         └─────────────────┬───────────────┘
                                           ▼
                                [ pages/viewer.py ]
                       • Local Source / Requirement Viewer
                       • GitHub Remote Source Viewer with Highlighted Diffs
```

---

## 📊 3. Analysis Modes & Capabilities

### 1. Local Benchmark Analysis (`iTrust`)
- **Requirement → Code (`Req → Code`)**: Evaluates 226 Java classes for a selected requirement, computing ML confidence scores, verifying ground-truth links, and mapping call graph reach.
- **Code → Requirement (`Code → Req`)**: Evaluates 131 requirements for a modified Java file, identifying affected use cases and downstream methods.

### 2. GitHub Mode 1 — Predictive Analysis (Before Change)
- **Question**: *"I am planning to change this file. What could be impacted across the repository?"*
- **Workflow**: Connects to any public/private GitHub repository, fetches branch file trees, performs lightweight static dependency analysis (imports, class usages, method references), and computes model-based relationship evidence against other repository files.

### 3. GitHub Mode 2 — Post-Change Analysis (Commit Comparison)
- **Question**: *"I changed code between two commits. What is impacted by the actual diff?"*
- **Workflow**: Compares two commits via the GitHub Comparison API, extracts added/modified/deleted files, detects changed line ranges, identifies modified Java methods, and ranks affected repository artifacts.

### 4. High-Fidelity Artifact & Method Viewer (`/viewer`)
- **Local Files**: 2-column full-width layout with line-numbered source code, method declaration highlights, and call graph matrix.
- **GitHub Remote Files**: Displays fetched remote source code with line-level highlights for modified lines and changed methods.

---

## 📈 4. Machine Learning Pipeline & Benchmark Performance

### Feature Engineering & Evaluation
- **Feature Vector**: Exactly **501 Features** (500 TF-IDF lexical n-grams fitted on training split + 1 SBERT `all-MiniLM-L6-v2` semantic cosine similarity).
- **Classifier**: `XGBClassifier(n_estimators=150, max_depth=6, learning_rate=0.1, random_state=42)`.
- **Evaluation Split**: Stratified 80/20 train/test split on 572 balanced pairs (457 train / 115 test).

| Metric | Verified Score | Details |
|---|---|---|
| **Overall Accuracy** | **85.22%** | 98 / 115 test pairs correctly classified |
| **Precision (Linked Class)** | **81.25%** | 52 / 64 positive predictions correct |
| **Recall (Linked Class)** | **91.23%** | 52 / 57 ground-truth links recovered |
| **F1-Score (Linked Class)** | **85.95%** | Harmonic mean of linked class precision & recall |
| **Macro Average F1** | **85.18%** | Balanced performance across classes |

---

## ⚠️ 5. External Repository Transparent Disclaimers

1. **Traceability Evidence**: External GitHub repositories do not have predefined ground-truth answer matrices. The system explicitly displays `Traceability: Not Available for External Repository` rather than inventing links.
2. **ML Relationship Scores**: ML scores on external repositories represent **lexical/semantic relationship evidence** based on a model trained on the iTrust benchmark, not universally calibrated probabilities.
3. **Static Dependency Analysis**: Dependency reach for external repositories uses lightweight static regex/AST parsing (imports, class references, method names) rather than full compiler runtime resolution.

---

## 📂 6. Repository Directory Structure

```
.
├── Signed Project Synopsis.docx     # Academic project submission document
├── README.md                        # Comprehensive system documentation
├── requirements.txt                 # Python package dependencies
├── .gitignore                       # Git ignore configuration
└── iTrust/                          # Main Application Package
    ├── app.py                       # Main Streamlit dashboard router (4 modes)
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
    │   ├── github_service.py        # GitHub REST API client & diff hunk parser
    │   ├── github_impact_engine.py  # Mode 1 & Mode 2 GitHub analysis engine
    │   └── __init__.py
    ├── ui/                          # Frontend UI Presentation
    │   ├── styles.py                # CSS design system & multi-layer cards
    │   ├── req_to_code.py           # Requirement → Code analysis UI
    │   ├── code_to_req.py           # Code → Requirement analysis UI
    │   ├── github_predictive.py     # GitHub Mode 1 (Predictive) UI
    │   ├── github_post_change.py    # GitHub Mode 2 (Post-Change) UI
    │   └── __init__.py
    ├── pages/
    │   └── viewer.py                # Unified 2-column local & GitHub file viewer
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
