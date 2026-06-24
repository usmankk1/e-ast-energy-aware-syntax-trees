"""
E-AST: Energy-Aware Abstract Syntax Trees
Phase 3 Implementation Demo — Muhammad Usman Khan, SAP 37906, BSCS-7

This script demonstrates the full E-AST pipeline:
  1. Sample Java programs (representing the 6 structural categories)
  2. AST parsing using javalang
  3. Extraction of 6 E-AST features per program
  4. Simulated energy labeling (RAPL-equivalent formula)
  5. Random Forest model training
  6. Evaluation: MAPE, R^2, and feature importance
"""

import javalang
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_percentage_error, r2_score
from sklearn.preprocessing import MinMaxScaler

print("=" * 70)
print("E-AST PIPELINE — PHASE 3 IMPLEMENTATION DEMO")
print("=" * 70)

# ──────────────────────────────────────────────────────────────────────
# STEP 1: Sample dataset — Java programs across 6 structural categories
# ──────────────────────────────────────────────────────────────────────

programs = {
    "flat_algorithm_1": """
        class Demo {
            int sumArray(int[] arr) {
                int total = 0;
                for (int i = 0; i < arr.length; i++) {
                    total = total + arr[i];
                }
                return total;
            }
        }
    """,
    "nested_loop_1": """
        class Demo {
            void matrixMultiply(int n) {
                for (int i = 0; i < n; i++) {
                    for (int j = 0; j < n; j++) {
                        compute(i, j);
                        compute(j, i);
                    }
                }
            }
            void compute(int a, int b) {}
        }
    """,
    "recursive_1": """
        class Demo {
            int fib(int n) {
                if (n <= 1) return n;
                return fib(n - 1) + fib(n - 2);
            }
        }
    """,
    "object_heavy_1": """
        class Demo {
            void buildStrings(int n) {
                for (int i = 0; i < n; i++) {
                    String s = new String("data" + i);
                    process(s);
                }
            }
            void process(String s) {}
        }
    """,
    "busy_wait_1": """
        class Demo {
            boolean flag = false;
            void waitLoop() {
                while (flag == false) {
                }
            }
        }
    """,
    "string_manip_1": """
        class Demo {
            String buildReport(int n) {
                String result = "";
                for (int i = 0; i < n; i++) {
                    result = result + "line" + i;
                }
                return result;
            }
        }
    """,
}

print(f"\n[STEP 1] Loaded {len(programs)} sample Java programs across structural categories.")
for name in programs:
    print(f"   - {name}")

# ──────────────────────────────────────────────────────────────────────
# STEP 2: Parse each program into an AST using javalang
# ──────────────────────────────────────────────────────────────────────

print("\n[STEP 2] Parsing source code into Abstract Syntax Trees (Tree-sitter equivalent: javalang)...")

ast_node_lists = {}
for name, source in programs.items():
    tree = javalang.parse.parse(source)
    node_types = [type(node).__name__ for path, node in tree]
    ast_node_lists[name] = node_types
    print(f"   - {name}: {len(node_types)} AST nodes extracted")

# ──────────────────────────────────────────────────────────────────────
# STEP 3: Extract the 6 E-AST features from each program's AST
# ──────────────────────────────────────────────────────────────────────

def extract_features(node_list, source_text):
    total = len(node_list)
    lines = max(len(source_text.strip().splitlines()), 1)

    for_count = node_list.count("ForStatement")
    for_depth = min(for_count, 5)

    method_in_loop = node_list.count("MethodInvocation") if for_count > 0 else 0
    obj_in_loop = node_list.count("ClassCreator") if for_count > 0 else 0
    mpi = round(node_list.count("ClassCreator") / total, 4) if total > 0 else 0

    while_count = node_list.count("WhileStatement")
    block_count = node_list.count("BlockStatement")
    busy_wait = 1 if (while_count > 0 and block_count <= while_count) else 0

    instr_density = round(total / lines, 4)

    return [for_depth, method_in_loop, obj_in_loop, mpi, busy_wait, instr_density]


print("\n[STEP 3] Extracting 6 E-AST structural features per program...")
print(f"   {'Program':<20}{'ForDepth':<10}{'MethodLoop':<12}{'ObjLoop':<9}{'MPI':<8}{'BusyWait':<10}{'InstrDens'}")

feature_names = ["ForStatement_depth", "MethodInvoc_in_loop", "ObjectCreation_in_loop",
                  "Memory_Pressure_Index", "WhileStmt_empty_body", "Instruction_density"]

X = []
program_names = list(programs.keys())
for name in program_names:
    feats = extract_features(ast_node_lists[name], programs[name])
    X.append(feats)
    print(f"   {name:<20}{feats[0]:<10}{feats[1]:<12}{feats[2]:<9}{feats[3]:<8}{feats[4]:<10}{feats[5]}")

X = np.array(X)

# ──────────────────────────────────────────────────────────────────────
# STEP 4: Simulate energy labels (RAPL-equivalent, since no Linux/Intel
#         hardware sensor is available in this environment)
# ──────────────────────────────────────────────────────────────────────

def simulate_energy(features):
    for_depth, meth_loop, obj_loop, mpi, busy, density = features
    energy = (for_depth * 4.0 +
              meth_loop * 0.8 +
              obj_loop * 3.5 +
              mpi * 20.0 +
              busy * 5.0 +
              density * 1.5)
    return round(energy + 2.0, 2)  # +2.0 baseline idle cost


print("\n[STEP 4] Simulating energy consumption labels (RAPL-equivalent formula)...")
y = np.array([simulate_energy(f) for f in X])
for name, energy in zip(program_names, y):
    print(f"   - {name:<20} -> {energy} joules")

# ──────────────────────────────────────────────────────────────────────
# STEP 5: Generate additional synthetic training samples by perturbing
#         the 6 base programs, so the model has enough data to train on
# ──────────────────────────────────────────────────────────────────────

print("\n[STEP 5] Expanding dataset via feature-space perturbation (60 total samples)...")
np.random.seed(42)
X_expanded = [X]
y_expanded = [y]
for _ in range(9):
    noise = np.random.normal(0, 0.15, X.shape)
    X_noisy = np.clip(X + X * noise, 0, None)
    y_noisy = np.array([simulate_energy(f) for f in X_noisy])
    X_expanded.append(X_noisy)
    y_expanded.append(y_noisy)

X_full = np.vstack(X_expanded)
y_full = np.concatenate(y_expanded)
print(f"   Dataset expanded to {X_full.shape[0]} samples x {X_full.shape[1]} features")

# ──────────────────────────────────────────────────────────────────────
# STEP 6: Train Random Forest and Linear Regression models
# ──────────────────────────────────────────────────────────────────────

print("\n[STEP 6] Training models (80/20 train-test split)...")

X_train, X_test, y_train, y_test = train_test_split(
    X_full, y_full, test_size=0.2, random_state=42
)

rf = RandomForestRegressor(n_estimators=100, max_depth=8, random_state=42)
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
mape_lr = mean_absolute_percentage_error(y_test, y_pred_lr) * 100
r2_lr = r2_score(y_test, y_pred_lr)

# ──────────────────────────────────────────────────────────────────────
# STEP 7: Results
# ──────────────────────────────────────────────────────────────────────

print("\n" + "=" * 70)
print("RESULTS")
print("=" * 70)
print(f"\n{'Metric':<25}{'Random Forest':<20}{'Linear Regression':<20}")
print(f"{'MAPE':<25}{mape_rf:<20.2f}{mape_lr:<20.2f}")
print(f"{'R-squared':<25}{r2_rf:<20.3f}{r2_lr:<20.3f}")
print(f"\nHypothesis target: MAPE <= 15%")
print(f"Random Forest result: {'CONFIRMED' if mape_rf <= 15 else 'NOT CONFIRMED'} ({mape_rf:.2f}%)")

print("\n--- Feature Importance (Random Forest) ---")
importances = rf.feature_importances_
ranked = sorted(zip(feature_names, importances), key=lambda x: -x[1])
for i, (fname, score) in enumerate(ranked, 1):
    print(f"   {i}. {fname:<28} {score:.3f}")

print("\n" + "=" * 70)
print("Pipeline complete.")
print("=" * 70)