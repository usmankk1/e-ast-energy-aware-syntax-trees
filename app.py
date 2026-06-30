"""
E-AST Live Demo — Streamlit App
Muhammad Usman Khan | SAP 37906 | BSCS-7 | TOPL — Dr. Ayesha Kashif

Run with:  streamlit run app.py
"""

import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx

import east_core as core

st.set_page_config(page_title="E-AST — Energy-Aware AST", layout="wide", page_icon="⚡")

# ──────────────────────────────────────────────────────────────────────
# Cached model training (runs once per session, exact same logic as
# Phase_Completion.py — same 60 programs, same Random Forest config)
# ──────────────────────────────────────────────────────────────────────

@st.cache_resource
def get_trained_model():
    return core.train_models()

results = get_trained_model()

# ──────────────────────────────────────────────────────────────────────
# Header
# ──────────────────────────────────────────────────────────────────────

st.title("⚡ E-AST: Energy-Aware Abstract Syntax Trees")
st.caption("Predicting software energy consumption from code structure — before execution")

with st.expander("ℹ️  About this demo", expanded=False):
    st.markdown("""
    This app wraps the **Phase 3 & 4 implementation** (`Phase_Completion.py`) in a live interface.

    - The Random Forest model was trained on **60 real Java programs** across 6 structural categories.
    - Paste **any Java method or class** below and the app will parse it into an AST, extract the
      same 6 E-AST features, and predict its energy cost using the trained model.
    - Energy labels are **simulated** using a weighted antipattern formula (documented limitation —
      no Intel RAPL hardware access in this environment). See the *Model Performance* tab for full transparency.
    """)

tab1, tab2, tab3 = st.tabs(["🔬 Live Code Analyzer", "📊 Model Performance", "📁 Training Dataset"])

# ════════════════════════════════════════════════════════════════════════
# TAB 1 — Live Code Analyzer
# ════════════════════════════════════════════════════════════════════════

with tab1:
    col_in, col_out = st.columns([1, 1])

    with col_in:
        st.subheader("Paste Java code")
        default_code = """class Demo {
    void process(int n) {
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) {
                compute(i, j);
            }
        }
    }
    void compute(int a, int b) {}
}"""
        code_input = st.text_area("Java source", value=default_code, height=300,
                                   label_visibility="collapsed")

        examples = st.selectbox("Or load a real program from the training dataset:", [
            "— select —",
            "FlatSum — flat_algorithm category",
            "NestedMatMul — nested_loop category",
            "RecFib — recursive category",
            "ObjList — object_heavy category",
            "BusyFlag — busy_wait category",
            "StrReport — string_manipulation category",
        ])

        # These 6 examples are pulled directly from east_pipeline.py / Phase_Completion.py —
        # the same 60-program dataset the model was trained on (one per category).
        example_map = {
            "FlatSum — flat_algorithm category": """class FlatSum {
    int sum(int[] arr) {
        int total = 0;
        for (int i = 0; i < arr.length; i++) {
            total = total + arr[i];
        }
        return total;
    }
}""",
            "NestedMatMul — nested_loop category": """class NestedMatMul {
    void matrixMultiply(int n) {
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) {
                compute(i, j);
                compute(j, i);
            }
        }
    }
    void compute(int a, int b) {}
}""",
            "RecFib — recursive category": """class RecFib {
    int fib(int n) {
        if (n <= 1) return n;
        return fib(n - 1) + fib(n - 2);
    }
}""",
            "ObjList — object_heavy category": """class ObjList {
    void buildList(int n) {
        java.util.List<String> list = new java.util.ArrayList<>();
        for (int i = 0; i < n; i++) {
            list.add(new String("item" + i));
        }
    }
}""",
            "BusyFlag — busy_wait category": """class BusyFlag {
    boolean flag = false;
    void waitFlag() {
        while (flag == false) {
        }
    }
}""",
            "StrReport — string_manipulation category": """class StrReport {
    String buildReport(int n) {
        String result = "";
        for (int i = 0; i < n; i++) {
            result = result + "line" + i;
        }
        return result;
    }
}""",
        }
        if examples != "— select —":
            code_input = example_map[examples]
            st.code(code_input, language="java")
            st.caption("📁 This program is one of the 60 used to train the model (see Training Dataset tab).")

        analyze_btn = st.button("🔍 Analyze & Predict Energy", type="primary", use_container_width=True)

    with col_out:
        st.subheader("AST features → energy prediction")

        if analyze_btn or examples != "— select —":
            nodes, err = core.parse_ast(code_input)

            if err:
                st.error(f"Parse error — this is not valid Java: {err}")
            elif len(nodes) == 0:
                st.warning("No AST nodes found. Paste a complete Java class.")
            else:
                feats = core.extract_features(nodes, code_input)
                energy = core.simulate_energy(feats)
                predicted = results["rf"].predict([feats])[0]

                # Energy gauge-style metric
                risk_level = "🟢 LOW" if energy < 6 else ("🟡 MEDIUM" if energy < 14 else "🔴 HIGH")
                c1, c2, c3 = st.columns(3)
                c1.metric("Simulated energy", f"{energy} J")
                c2.metric("RF model prediction", f"{predicted:.2f} J")
                c3.metric("Risk level", risk_level)

                st.markdown("**6 E-AST features extracted:**")
                feat_df = pd.DataFrame({
                    "Feature": core.FEATURE_LABELS_SHORT,
                    "Value": feats,
                    "What it means": [core.INTERP_MAP[n] for n in core.FEATURE_NAMES]
                })
                st.dataframe(feat_df, hide_index=True, use_container_width=True)

                # Bar chart of this program's feature values vs typical ranges
                fig, ax = plt.subplots(figsize=(6, 3))
                colors = ["#C0392B" if (n == "WhileStmt_empty_body" and v == 1) else
                          "#BA7517" if n == "ForStatement_depth" and v >= 2 else "#2E5F8A"
                          for n, v in zip(core.FEATURE_NAMES, feats)]
                ax.barh(core.FEATURE_LABELS_SHORT[::-1], feats[::-1], color=colors[::-1])
                ax.set_xlabel("Feature value")
                ax.set_title("Extracted feature values for this program")
                plt.tight_layout()
                st.pyplot(fig)

                st.divider()
                st.markdown("**AST node breakdown (color = energy risk)**")

                node_counts = pd.Series(nodes).value_counts()
                cols = st.columns(4)
                for i, (ntype, count) in enumerate(node_counts.items()):
                    color = core.node_risk_color(ntype, in_loop_context=(feats[0] > 0))
                    with cols[i % 4]:
                        st.markdown(
                            f"<div style='padding:8px 10px;border-radius:6px;background:{color}22;"
                            f"border-left:4px solid {color};margin-bottom:6px;font-size:13px'>"
                            f"<b>{ntype}</b><br><span style='color:{color};font-weight:600'>{count}×</span></div>",
                            unsafe_allow_html=True
                        )

                st.divider()
                st.markdown("**AST tree diagram**")
                try:
                    tree_pairs = core.parse_ast_tree(code_input)
                    G = nx.DiGraph()
                    node_id_map = {}
                    counter = [0]

                    def get_id(path, node):
                        key = id(node)
                        if key not in node_id_map:
                            node_id_map[key] = counter[0]
                            counter[0] += 1
                        return node_id_map[key]

                    for path, node in tree_pairs[:40]:  # cap for readability
                        nid = get_id(path, node)
                        G.add_node(nid, label=type(node).__name__)
                        if path:
                            parent = path[-1]
                            pid = id(parent)
                            if pid in node_id_map:
                                G.add_edge(node_id_map[pid], nid)

                    if len(G.nodes) > 1:
                        fig2, ax2 = plt.subplots(figsize=(9, 5))
                        try:
                            pos = nx.nx_agraph.graphviz_layout(G, prog="dot")
                        except Exception:
                            pos = nx.spring_layout(G, k=0.6, seed=42)
                        labels = nx.get_node_attributes(G, "label")
                        node_colors = [core.node_risk_color(labels.get(n, ""), feats[0] > 0) for n in G.nodes]
                        nx.draw(G, pos, ax=ax2, labels=labels, with_labels=True, node_color=node_colors,
                                node_size=1400, font_size=7, font_color="white", edge_color="#999",
                                arrows=True, arrowsize=10)
                        plt.tight_layout()
                        st.pyplot(fig2)
                        st.caption("🔴 Red = highest energy risk (busy-wait, allocation)  🟠 Amber = loop-related  🟢 Green = safe/structural  ⚪ Gray = neutral")
                    else:
                        st.info("Tree too small to render meaningfully.")
                except Exception as e:
                    st.warning(f"Tree rendering skipped: {e}")
        else:
            st.info("👈 Paste Java code and click **Analyze & Predict Energy**, or pick an example.")

# ════════════════════════════════════════════════════════════════════════
# TAB 2 — Model Performance
# ════════════════════════════════════════════════════════════════════════

with tab2:
    st.subheader("Phase 3 results — trained on the 60-program dataset")

    c1, c2, c3 = st.columns(3)
    c1.metric("Random Forest MAPE", f"{results['mape_rf']:.2f}%", help="Target: ≤ 15%")
    c2.metric("Random Forest R²", f"{results['r2_rf']:.3f}", help="Target: ≥ 0.80")
    c3.metric("Hypothesis verdict", "✅ CONFIRMED" if results['mape_rf'] <= 15 else "❌ NOT MET")

    st.markdown("##### Random Forest vs. Linear Regression")
    perf_df = pd.DataFrame({
        "Metric": ["MAPE (%)", "R²", "MAE (joules)"],
        "Random Forest": [round(results['mape_rf'], 2), round(results['r2_rf'], 3), round(results['mae_rf'], 3)],
        "Linear Regression": [round(results['mape_lr'], 2), round(results['r2_lr'], 3), round(results['mae_lr'], 3)],
    })
    st.dataframe(perf_df, hide_index=True, use_container_width=True)

    st.warning(
        "**Honest note:** Linear Regression outperforms Random Forest here because the simulated "
        "energy label (Step 4 of the pipeline) is itself a linear combination of the 6 features. "
        "This is expected given the synthetic ground truth — it does not mean real-world energy "
        "is linear. Random Forest remains the primary model because it still clears the ≤15% MAPE "
        "hypothesis threshold **and** provides feature importance scores, which a linear model cannot."
    )

    st.markdown("##### Feature importance (Random Forest) — answers Research Question 1")
    ranked = results["ranked_importance"]
    imp_df = pd.DataFrame(ranked, columns=["Feature", "Importance"])
    imp_df["Interpretation"] = imp_df["Feature"].map(core.INTERP_MAP)

    fig3, ax3 = plt.subplots(figsize=(8, 4))
    ax3.barh([f[0] for f in ranked][::-1], [f[1] for f in ranked][::-1], color="#2E5F8A")
    ax3.set_xlabel("Importance score")
    ax3.set_title("E-AST Feature Importance — Random Forest")
    plt.tight_layout()
    st.pyplot(fig3)
    st.dataframe(imp_df, hide_index=True, use_container_width=True)

    st.markdown("##### Predicted vs. actual energy (test set)")
    fig4, ax4 = plt.subplots(figsize=(6, 5))
    ax4.scatter(results["y_test"], results["y_pred_rf"], color="#2E5F8A", label="Random Forest", s=60)
    lims = [min(results["y_test"].min(), results["y_pred_rf"].min()),
            max(results["y_test"].max(), results["y_pred_rf"].max())]
    ax4.plot(lims, lims, "k--", alpha=0.4, label="Perfect prediction")
    ax4.set_xlabel("Actual energy (J)")
    ax4.set_ylabel("Predicted energy (J)")
    ax4.legend()
    plt.tight_layout()
    st.pyplot(fig4)

# ════════════════════════════════════════════════════════════════════════
# TAB 3 — Training Dataset
# ════════════════════════════════════════════════════════════════════════

with tab3:
    st.subheader(f"Training dataset — {results['n_programs']} Java programs, 6 structural categories")

    cat_counts = pd.Series(results["category_labels"]).value_counts()
    st.bar_chart(cat_counts)

    st.markdown("##### Full feature matrix")
    full_df = pd.DataFrame(results["X"], columns=core.FEATURE_NAMES)
    full_df.insert(0, "category", results["category_labels"])
    full_df["simulated_energy_J"] = results["y"]
    st.dataframe(full_df, use_container_width=True, height=400)

    csv = full_df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download dataset as CSV", csv, "east_dataset.csv", "text/csv")
