# FINAL SYSTEM STATUS & ARCHITECTURE REPORT
### Project: "Intelligent Change Impact Analysis in Requirements Using ML and Traceability Links"

---

## 1. Final System Architecture

The Change Impact Analysis (CIA) system employs a **multi-layer hybrid architecture** that decouples machine learning inference, ground-truth traceability verification, and static code dependency analysis before synthesizing them into actionable risk tiers.

```
                      [ User Selection: Requirement / Code File ]
                                          │
                  ┌───────────────────────┴───────────────────────┐
                  ▼                                               ▼
         [ ML Layer (Inference) ]                      [ Traceability Layer ]
    • SBERT Cosine Similarity (1-dim)             • iTrust Solution Links (Ground Truth)
    • TF-IDF Text Feature Matrix (500-dim)        • Direct Link Existence Check (Binary)
    • XGBoost Classifier (150 trees)                              │
                  │                                               │
                  ▼                                               ▼
     ML Relationship Confidence (%)                    Verified Traceability Status
                  │                                               │
                  └───────────────────────┬───────────────────────┘
                                          │
                                          ▼
                             [ Dependency Analysis Layer ]
                         • Method-Level Call Graph (JSON)
                         • Direct Callers & Callees (calls / called_by)
                         • Class-Level Dependency Impact Set
                                          │
                                          ▼
                               Dependency Reach Tier
                             (HIGH / MEDIUM / LOW / NONE)
                                          │
                                          ▼
                           [ Decision Policy Synthesis ]
                                          │
                                          ▼
                  [ Structured Change Impact Report & Visual UI ]
                  • Candidate Ranking by Score & Risk Tier
                  • Verified vs. ML-Discovered Segregation
                  • Transitively Impacted Java Methods Table
                  • In-Source Syntax & Keyword Viewers
```

---

## 2. Technologies & Libraries Used

| Component | Technology | Version | Purpose |
|---|---|---|---|
| **Frontend UI** | Streamlit | 1.43+ | Interactive multi-page dashboard, risk filtering, file viewer |
| **Styling & Theme** | Vanilla CSS3 (Custom) | - | Dark/Light adaptive tokens, responsive multi-layer cards |
| **ML Classifier** | XGBoost (`XGBClassifier`) | 3.2.0 | Gradient boosted decision trees for relationship classification |
| **Text Vectorization** | Scikit-Learn (`TfidfVectorizer`)| 1.7.2 | Lexical feature extraction (`max_features=500, ngram_range=(1,2)`) |
| **Dense Embeddings** | Sentence-Transformers | 5.3.0 | Pretrained SBERT `all-MiniLM-L6-v2` for 384-dim dense vectors |
| **Data Manipulation** | Pandas & NumPy | 2.3+ | Dataframe construction, pairing, matrix manipulation |
| **Sparse Computing** | SciPy Sparse (`csr_matrix`) | 1.16+ | Memory-efficient stacking of sparse TF-IDF + scalar similarity |
| **Artifact Storage** | Joblib & Pickle | Standard | Fast binary serialization of models, vectorizer, and cached embeddings |

---

## 3. Data Flow & Execution Pipeline

```
1. Startup:
   Streamlit loads @st.cache_resource assets once:
   - models/xgb_model.pkl (Trained XGBoost)
   - models/tfidf_vectorizer.pkl (Fitted TF-IDF)
   - models/req_embeddings.pkl (131 precomputed 384-d vectors)
   - models/code_embeddings.pkl (226 precomputed 384-d vectors)
   - itrust_solution_links.txt (286 ground-truth links)
   - itrust_method_callgraph.json (1,235 method nodes)

2. User Interaction:
   User chooses mode:
   - Mode 1: Requirement -> Code (Selects a Requirement, e.g. UC10E1.txt)
   - Mode 2: Code -> Requirement (Selects a Java file, e.g. AuthDAO.java)

3. Inference (services/ml_engine.py):
   For every candidate pair:
   - Combined text = req_text + " " + code_text
   - TF-IDF = vectorizer.transform([combined_text]) (1, 500)
   - SBERT Cosine Similarity = cosine_similarity(req_emb, code_emb) (1, 1)
   - X = hstack([TF-IDF, Cosine Similarity]) (1, 501)
   - Score = xgb_model.predict_proba(X)[0][1]
   - Label = xgb_model.predict(X)[0]

4. Dependency Propagation (services/impact_engine.py):
   - Maps class name to call graph methods
   - Traverses direct callers and callees
   - Computes unique transitively affected methods

5. Overall Risk Assignment (Decision Table):
   - Synthesizes ML Score + Verified Status + Dependency Count
   - Assigns HIGH 🔴, MEDIUM 🟠, or LOW 🟢 with an explicit explanation

6. UI Display (ui/req_to_code.py, ui/code_to_req.py):
   - Renders summary metric counters
   - Displays ranked candidate cards with source inspection links
   - Exposes CSV downloads for impacted methods
```

---

## 4. Machine Learning Model & Features

- **Model Type**: `XGBClassifier`
- **Hyperparameters**: `n_estimators=150`, `max_depth=6`, `learning_rate=0.1`, `eval_metric='logloss'`, `random_state=42`
- **Feature Space (501 total features)**:
  - `Features 0–499`: TF-IDF word & bigram n-grams fitted exclusively on training split text.
  - `Feature 500`: Semantic cosine similarity derived from SBERT `all-MiniLM-L6-v2` dense embeddings.
- **Training Protocol**:
  - Balanced dataset: 286 verified positive links + 286 sampled negative pairs (`random_state=42`).
  - Train/Test Split: Stratified 80/20 split (`stratify=balanced_df['label']`, `random_state=42`) $\to$ 457 Train / 115 Test.
  - Leakage Guard: Vectorizer fitted **only** on the 457 training pairs.

---

## 5. Final Reproducible Evaluation Metrics

Evaluated on the untouched stratified test set (115 samples):

| Metric | Value | Interpretation |
|---|---|---|
| **Overall Accuracy** | **85.22%** | Correctly classified 98 out of 115 test pairs |
| **Precision (Linked / Class 1)** | **81.25%** | 52 true links out of 64 predicted links |
| **Recall (Linked / Class 1)** | **91.23%** | Identified 52 of 57 true links (**Only 5 missed**) |
| **F1-Score (Linked / Class 1)** | **85.95%** | High balance between precision and link recall |
| **Precision (Unlinked / Class 0)** | **90.20%** | 46 true non-links out of 51 predicted non-links |
| **Recall (Unlinked / Class 0)** | **79.31%** | Correctly rejected 46 out of 58 non-links |
| **F1-Score (Unlinked / Class 0)** | **84.40%** | |
| **Macro Average F1** | **85.18%** | Balanced mean across both classes |

### Final Confusion Matrix
```
                       Predicted Unlinked (0)    Predicted Linked (1)    Total
Actual Unlinked (0)              46                       12               58
Actual Linked (1)                 5                       52               57
Total                            51                       64              115
```

---

## 6. Functional Capabilities

1. **Bidirectional Change Impact Analysis**:
   - **Requirement $\to$ Code**: Predicts all impacted Java files, classes, and transitively called methods when a use case or requirement changes.
   - **Code $\to$ Requirement**: Identifies all requirement documents affected when a developer modifies a Java class or DAO.
2. **Multi-Layer Evidence Separation**:
   - Explicitly displays ML Relationship Score, Verified Traceability status, Dependency Evidence, and Overall Impact Risk.
3. **In-Source Highlighted Code Viewer**:
   - Clean pop-out browser tab highlighting exact method signatures affected in Java files using Highlight.js.
   - Requirement document viewer with interactive keyword search.
4. **Actionable Risk Filtering**:
   - Instant filtering for Actionable (High & Medium Risk), Ground-Truth Verified, or ML-Discovered candidates.
5. **Impact Report Export**:
   - Direct CSV export of all affected methods and dependency chains for auditing.

---

## 7. Explicit Decision Table Policy

| Verified Link | ML Relationship Score ($S$) | Dependency Reach ($D$) | Overall Impact Risk | Risk Rationale |
|---|---|---|---|---|
| **True (Verified)** | Any | HIGH ($>10$ methods) | 🔴 **HIGH** | Verified Traceability Link + HIGH Dependency Reach |
| **True (Verified)** | Any | MEDIUM ($6-10$ methods) | 🔴 **HIGH** | Verified Traceability Link + MEDIUM Dependency Reach |
| **True (Verified)** | Any | LOW / NONE ($\le 5$ methods) | 🟠 **MEDIUM** | Verified Traceability Link + Localized Reach |
| **False (Unverified)** | High ($S \ge 0.70$) | HIGH ($>10$ methods) | 🔴 **HIGH** | High ML Relationship Score + HIGH Dependency Reach |
| **False (Unverified)** | High ($S \ge 0.70$) | MEDIUM / LOW / NONE | 🟠 **MEDIUM** | High ML Relationship Score + Moderate/Localized Reach |
| **False (Unverified)** | Moderate ($0.40 \le S < 0.70$) | HIGH ($>10$ methods) | 🟠 **MEDIUM** | Moderate ML Score + HIGH Dependency Reach |
| **False (Unverified)** | Moderate ($0.40 \le S < 0.70$) | LOW / NONE | 🟢 **LOW** | Moderate ML Score with Localized Scope |
| **False (Unverified)** | Low ($S < 0.40$) | Any | 🟢 **LOW** | Unverified Link & Low ML Relationship Score |

---

## 8. File Structure & Responsibilities

```
iTrust/
├── app.py                      # Main Streamlit dashboard router & startup warm-up
├── itrust_solution_links.txt   # 286 ground-truth requirement-code traceability links
├── itrust_method_callgraph.json# 1,235 method nodes with calls/called_by lists
├── req/                        # 131 software requirement text documents
├── code/                       # 226 Java source code files
├── models/                     # Exported ML artifacts
│   ├── xgb_model.pkl           # Trained XGBoost model (Joblib)
│   ├── tfidf_vectorizer.pkl    # Fitted 500-feature TF-IDF vectorizer
│   ├── req_embeddings.pkl      # Precomputed SBERT requirement embeddings (384-d)
│   ├── code_embeddings.pkl     # Precomputed SBERT code embeddings (384-d)
│   └── metadata.json           # Model configuration, features & evaluation metrics
├── services/                   # Backend logic layer
│   ├── data_loader.py          # Cached loaders for links, call graph, file index & texts
│   ├── ml_engine.py            # ML inference engine (501-dim feature extraction & ranking)
│   ├── impact_engine.py        # Hybrid orchestrator combining ML + Traceability + Call Graph
│   ├── github_service.py       # GitHub REST API client (trees, raw files, commits, diffs)
│   └── github_impact_engine.py # Mode 1 (Predictive) & Mode 2 (Post-Change) analysis engine
├── ui/                         # Presentation layer
│   ├── styles.py               # CSS tokens, theme styling & artifact card renderer
│   ├── req_to_code.py          # Requirement -> Code UI with risk tabs & candidate ranking
│   ├── code_to_req.py          # Code -> Requirement UI with risk tabs & candidate ranking
│   ├── github_predictive.py    # GitHub Mode 1 (Predictive / Before Change) UI
│   └── github_post_change.py   # GitHub Mode 2 (Post-Change / Commit Comparison) UI
└── pages/                      # Streamlit multi-page routes
    └── viewer.py               # Unified 2-column local & GitHub file viewer
```

---

## 8. GitHub Integration Modes

### Mode 1 — Predictive Change Impact Analysis (Before Change)
- **Objective**: "I am planning to change this file. What could be impacted across the repository?"
- **Data Flow**: `UI -> github_service.get_file_tree -> Select File -> github_impact_engine.analyze_github_predictive -> Lightweight AST & ML Similarity -> External Risk Policy -> Multi-Tab Impact Cards`.
- **Output**: Model-based relationship evidence + repository structural evidence + caller/callee sets + overall impact risk.

### Mode 2 — Post-Change Change Impact Analysis (Commit Comparison)
- **Objective**: "I changed code between two commits. What is impacted by the actual diff?"
- **Data Flow**: `UI -> Select Base & New Commits -> github_service.compare_commits -> parse_diff_hunks -> extract_changed_methods -> github_impact_engine.analyze_github_post_change -> Per-File Ripple Risk`.
- **Output**: Change summary metrics (Added/Modified/Deleted) + changed line ranges + modified Java methods + structural reach + overall change risk.

---

## 9. How to Run the Application

```bash
# Navigate to project directory
cd c:\Users\Tanushree\OneDrive\Desktop\iTrust\iTrust

# Launch Streamlit server
streamlit run app.py
```

The application will be accessible at `http://localhost:8501`.

---

## 10. Known Technical Limitations

1. **Dataset Scope**: The model is trained and validated on the iTrust healthcare benchmark dataset.
2. **Negative Sampling Balance**: The model was trained on a 1:1 balanced sample (286 positive / 286 negative pairs). In natural repositories, negative pairs outnumber positive pairs $\approx 100:1$. Hence, the output is framed as **ML Relationship Confidence / Score**, not unconditional real-world probability.
3. **Static Call Graph**: Call graph information is pre-extracted. Dynamic reflection and runtime polymorphism in Java are not dynamically evaluated at runtime.

---

## 11. Example Workflows

### Example A: Requirement-to-Code (`UC10E1.txt` — Invalid Login)
1. Select `UC10E1.txt` $\to$ Click `Analyze Impact`.
2. Model ranks all 226 code files:
   - `AuthDAO.java`: **99.84% ML Score** | **✓ Verified Link** | **🔴 HIGH Reach (53 methods)** $\to$ **🔴 HIGH Overall Risk**.
   - `OfficeVisitDAO.java`: **99.72% ML Score** | **⚡ ML Candidate** | **🔴 HIGH Reach (78 methods)** $\to$ **🔴 HIGH Overall Risk**.
   - `GetUserNameAction.java`: **99.44% ML Score** | **✓ Verified Link** | **🟢 LOW Reach (3 methods)** $\to$ **🟠 MEDIUM Overall Risk**.
   - `BeanBuilder.java`: **0.12% ML Score** | **⚡ ML Candidate** | **🟢 LOW Reach (2 methods)** $\to$ **🟢 LOW Overall Risk**.

### Example B: Code-to-Requirement (`AuthDAO.java`)
1. Select `AuthDAO.java` $\to$ Click `Analyze Code Impact`.
2. Evaluates all 131 requirements against `AuthDAO.java`:
   - `UC10E1.txt`: **99.84% ML Score** | **✓ Verified Link** | **🔴 HIGH Reach (53 methods)** $\to$ **🔴 HIGH Overall Risk**.
   - `UC13E1.txt`: **99.89% ML Score** | **✓ Verified Link** | **🔴 HIGH Reach (53 methods)** $\to$ **🔴 HIGH Overall Risk**.
