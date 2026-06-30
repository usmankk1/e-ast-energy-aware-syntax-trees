"""
east_core.py — Shared E-AST logic for the Streamlit live demo.

This module re-implements the SAME feature extraction, energy simulation,
and model training logic as Phase_Completion.py (Phase 3 & 4 script),
exposed as importable functions/objects so the Streamlit app can:
  1. Re-train the exact same Random Forest on the exact same 60-program
     dataset at app startup (cached so it only happens once).
  2. Accept NEW Java code pasted live by the user, parse it, extract the
     same 6 features, and run it through the trained model.

No logic differs from Phase_Completion.py — this is a clean import-friendly
copy so the original grading script stays untouched.
"""

import javalang
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_percentage_error, r2_score, mean_absolute_error
from sklearn.preprocessing import MinMaxScaler

FEATURE_NAMES = [
    "ForStatement_depth",
    "MethodInvoc_in_loop",
    "ObjectCreation_in_loop",
    "Memory_Pressure_Index",
    "WhileStmt_empty_body",
    "Instruction_density",
]

FEATURE_LABELS_SHORT = ["F1: Loop depth", "F2: Calls in loop", "F3: Objects in loop",
                         "F4: Memory pressure", "F5: Busy-wait", "F6: Instr. density"]

INTERP_MAP = {
    "WhileStmt_empty_body":   "Busy-wait — 100% CPU waste; highest-value check",
    "ForStatement_depth":     "Nested loops — iterations multiply exponentially",
    "ObjectCreation_in_loop": "GC events in loops — proportional energy spikes",
    "Memory_Pressure_Index":  "Normalized GC pressure — sustained allocation load",
    "MethodInvoc_in_loop":    "Call overhead × loop count",
    "Instruction_density":    "Density alone — poor standalone predictor",
}


# ─────────────────────────────────────────────────────────────────────────
# Same 60-program dataset as Phase_Completion.py (import directly to avoid
# duplicating 700 lines of Java source strings)
# ─────────────────────────────────────────────────────────────────────────

def _load_dataset():
    """Import PROGRAMS list from the original Phase 3/4 script without
    re-executing its print statements, by exec-ing only up to that point."""
    import re
    with open("east_pipeline.py", "r", encoding="utf-8") as f:
        src = f.read()
    # Cut the file at the point CATEGORY_LABELS is defined — everything
    # before that is pure data + helper defs with no print side effects
    # except the PROGRAMS list construction (also silent).
    cutoff = src.index("CATEGORY_LABELS = [cat for cat, _ in PROGRAMS]")
    end = src.index("\n", src.index("N = len(PROGRAMS)"))
    data_src = src[:end]
    namespace = {}
    exec(compile(data_src, "east_pipeline_data", "exec"), namespace)
    return namespace["PROGRAMS"], namespace["CATEGORY_LABELS"]


PROGRAMS, CATEGORY_LABELS = _load_dataset()


# ─────────────────────────────────────────────────────────────────────────
# Feature extraction — identical logic to Phase_Completion.py Step 3
# ─────────────────────────────────────────────────────────────────────────

def parse_ast(source_text):
    """Parse Java source into AST node type list. Returns (node_list, error)."""
    try:
        tree = javalang.parse.parse(source_text)
        nodes = [type(node).__name__ for _, node in tree]
        return nodes, None
    except Exception as e:
        return [], str(e)


def parse_ast_tree(source_text):
    """Parse Java source and return the raw (path, node) pairs for tree rendering."""
    tree = javalang.parse.parse(source_text)
    return list(tree)


def extract_features(node_list, source_text):
    """Identical to Phase_Completion.py extract_features()."""
    total = max(len(node_list), 1)
    lines = max(len(source_text.strip().splitlines()), 1)

    for_count = node_list.count("ForStatement")
    for_depth = min(for_count, 5)

    method_in_loop = node_list.count("MethodInvocation") if for_count > 0 else 0
    obj_in_loop = node_list.count("ClassCreator") if for_count > 0 else 0
    mpi = round(node_list.count("ClassCreator") / total, 4)

    while_count = node_list.count("WhileStatement")
    block_count = node_list.count("BlockStatement")
    busy_wait = 1 if (while_count > 0 and block_count <= while_count) else 0

    instr_density = round(total / lines, 4)

    return [for_depth, method_in_loop, obj_in_loop, mpi, busy_wait, instr_density]


def simulate_energy(features):
    """Identical to Phase_Completion.py simulate_energy()."""
    f1, f2, f3, f4, f5, f6 = features
    energy = (f1 * 4.0 + f2 * 0.8 + f3 * 3.5 + f4 * 20.0 + f5 * 5.0 + f6 * 0.05)
    return round(energy + 2.0, 2)


# Risky AST node types highlighted in red for the visualizer
RISKY_NODES = {"ForStatement", "WhileStatement", "ClassCreator", "MethodInvocation"}
SAFE_NODES = {"BlockStatement", "IfStatement", "ReturnStatement", "VariableDeclarator",
              "BinaryOperation", "MethodDeclaration", "ClassDeclaration"}


def node_risk_color(node_type, in_loop_context=False):
    if node_type == "WhileStatement":
        return "#C0392B"  # busy-wait risk — darkest red
    if node_type == "ClassCreator" and in_loop_context:
        return "#C0392B"
    if node_type == "ForStatement":
        return "#BA7517"  # amber — loop, risk depends on nesting/content
    if node_type == "MethodInvocation" and in_loop_context:
        return "#BA7517"
    if node_type in RISKY_NODES:
        return "#D9A23B"
    if node_type in SAFE_NODES:
        return "#2E7D5B"
    return "#6B7280"  # neutral gray


# ─────────────────────────────────────────────────────────────────────────
# Model training — identical logic to Phase_Completion.py Steps 5–6
# ─────────────────────────────────────────────────────────────────────────

def train_models():
    """Trains RF + LR on the same 60-program dataset, returns everything
    the app needs: models, scaler, metrics, test data, feature importances."""

    ast_node_lists = []
    for cat, src in PROGRAMS:
        nodes, err = parse_ast(src)
        ast_node_lists.append(nodes)

    X = np.array([extract_features(ast_node_lists[i], src)
                  for i, (cat, src) in enumerate(PROGRAMS)], dtype=float)
    y = np.array([simulate_energy(f) for f in X])

    cat_to_int = {c: i for i, c in enumerate(sorted(set(CATEGORY_LABELS)))}
    strat_labels = np.array([cat_to_int[c] for c in CATEGORY_LABELS])

    X_train, X_test, y_train, y_test, strat_train, strat_test = train_test_split(
        X, y, strat_labels, test_size=0.2, random_state=42, stratify=strat_labels
    )

    rf = RandomForestRegressor(n_estimators=100, max_depth=8, min_samples_split=2, random_state=42)
    rf.fit(X_train, y_train)
    y_pred_rf = rf.predict(X_test)

    scaler = MinMaxScaler()
    X_train_sc = scaler.fit_transform(X_train)
    X_test_sc = scaler.transform(X_test)
    lr = LinearRegression()
    lr.fit(X_train_sc, y_train)
    y_pred_lr = lr.predict(X_test_sc)

    mape_rf = mean_absolute_percentage_error(y_test, y_pred_rf) * 100
    r2_rf = r2_score(y_test, y_pred_rf)
    mae_rf = mean_absolute_error(y_test, y_pred_rf)

    mape_lr = mean_absolute_percentage_error(y_test, y_pred_lr) * 100
    r2_lr = r2_score(y_test, y_pred_lr)
    mae_lr = mean_absolute_error(y_test, y_pred_lr)

    importances = rf.feature_importances_
    ranked = sorted(zip(FEATURE_NAMES, importances), key=lambda x: -x[1])

    return {
        "rf": rf, "lr": lr, "scaler": scaler,
        "X": X, "y": y, "X_train": X_train, "X_test": X_test,
        "y_train": y_train, "y_test": y_test,
        "y_pred_rf": y_pred_rf, "y_pred_lr": y_pred_lr,
        "mape_rf": mape_rf, "r2_rf": r2_rf, "mae_rf": mae_rf,
        "mape_lr": mape_lr, "r2_lr": r2_lr, "mae_lr": mae_lr,
        "ranked_importance": ranked,
        "category_labels": CATEGORY_LABELS,
        "n_programs": len(PROGRAMS),
    }
