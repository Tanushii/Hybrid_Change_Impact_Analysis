# Hybrid Change Impact Analysis (CIA)

## 📌 Overview
This project addresses the challenges of managing evolving requirements in large-scale software development. By leveraging a hybrid approach—combining structural analysis with advanced logic—the system automates the process of identifying how changes in requirements impact codebases, design, and testing activities.

## ⚠️ Problem Statement
In large and evolving software projects, changes in requirements are inevitable and can have cascading effects on design, implementation, testing, and maintenance activities. 

Traditional change impact analysis methods rely heavily on manual inspection and rule-based traceability, which are:
*   **Time-consuming & Error-prone:** Requiring significant human effort to track every dependency.
*   **Static:** Failing to adapt to complex and dynamic dependencies between artifacts.

As a result, developers often struggle to accurately predict the potential impacts of requirement changes, leading to increased rework, cost overruns, and project delays.

## 🚀 Key Features
*   **Automated Traceability:** Maps requirements to specific Java classes and methods.
*   **Impact Prediction:** Visualizes and reports potential "impact zones" of a proposed requirement change.
*   **Hybrid Logic:** Utilizes a combination of static analysis and predictive models to improve accuracy.
*   **Integrated Viewer:** Inspect Java source code and requirement documents directly within the dashboard.

## 📂 Project Structure
*   `iTrust/`: The core application folder containing the source code, datasets, and logic.
*   `presentation/`: (Upcoming) Project presentation and slide decks.
*   `synopsis/`: (Upcoming) Detailed project synopsis and technical documentation.

## 🛠️ Getting Started

### Prerequisites
Ensure you have **Python 3.8+** installed on your system.

### Installation
1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Tanushii/Hybrid_Change_Impact_Analysis.git
    cd Hybrid_Change_Impact_Analysis
    ```

2.  **Navigate to the source folder:**
    ```bash
    cd iTrust
    ```

3.  **Install dependencies:**
    *(If you don't have a requirements file, install these core libraries)*
    ```bash
    pip install streamlit pandas xgboost scikit-learn matplotlib seaborn nltk
    ```

### Running the Application
To launch the interactive dashboard, run:
```bash
streamlit run app.py
