# E-AST: Energy-Aware Abstract Syntax Trees

**Muhammad Usman Khan | SAP 37906 | BSCS-7**
**Theory of Programming Languages — Dr. Ayesha Kashif**

Predicting software energy consumption from Abstract Syntax Tree (AST) structure,
before execution, using machine learning.

## What this is

This project trains a Random Forest model on 60 Java programs (across 6 structural
categories) to predict energy consumption in joules from 6 AST-derived structural
features — without ever running the code. It includes a live Streamlit demo where
any Java snippet can be pasted and analyzed in real time.

## Files

| File | Purpose |
|---|---|
| `east_pipeline.py` | Full Phase 3 & 4 implementation — dataset, AST parsing, feature extraction, model training, evaluation, hypothesis verdict (console output) |
| `east_core.py` | Same core logic, refactored as importable functions for the Streamlit app |
| `app.py` | Interactive Streamlit demo — live code analyzer, model performance, training dataset viewer |
| `requirements.txt` | Python dependencies |

## How to run

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows PowerShell
# source .venv/bin/activate       # macOS/Linux

pip install -r requirements.txt

# Run the console pipeline (Phase 3 & 4 full output):
python east_pipeline.py

# Run the live interactive demo:
streamlit run app.py
```

## Key result

Random Forest achieves **4.76% MAPE** against the research hypothesis target of
≤15% MAPE, on a held-out test set — confirming the hypothesis that AST structural
features predict software energy consumption with practical accuracy.

## Known limitation

Energy labels are simulated via a weighted antipattern formula, since Intel RAPL
hardware access was not available in the development environment. This is
documented as a stated limitation in Phase 4 — see `east_pipeline.py` for details.
