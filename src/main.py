"""
AI-Driven Phishing Threat Detection Prototype
=============================================
Unit 1 Mini Project - Introduction to AI and Cyber Security (ENSP355)
K.R. Mangalam University

End-to-end pipeline:
  Task 1. Environment bootstrap and reproducible configuration.
  Task 2. Threat-landscape EDA on the UCI Phishing Websites dataset (ID 327).
  Task 3. Supervised ML threat classification (Logistic Regression, Decision Tree).
  Task 4. Deep-learning prototype (MLP 64x32) and multi-metric benchmarking.
  Task 5. Operational threshold simulation and ethical cost analysis.

Outputs: figures (results/), metrics.json, model_comparison.csv,
         threshold_analysis.csv, descriptive_stats.csv, top_indicators.csv.

Author : Abhinav Kumar (2301730191), B.Tech CSE (AIML)-C
Usage  : python src/main.py
"""

from __future__ import annotations

import json
import platform
import sys
import time
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    matthews_corrcoef,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import GridSearchCV, StratifiedKFold, cross_val_score, train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

warnings.filterwarnings("ignore", category=FutureWarning)

# ---------------------------------------------------------------------------
# Task 1 - Reproducible configuration
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_FILE = BASE_DIR / "data" / "phishing_websites.csv"
RESULTS_DIR = BASE_DIR / "results"
RESULTS_DIR.mkdir(exist_ok=True)

RANDOM_STATE = 42
TEST_SIZE = 0.20

# Monochrome publication style: all figure text black, greyscale ink only.
plt.rcParams.update(
    {
        "figure.dpi": 150,
        "savefig.dpi": 300,
        "font.size": 9,
        "axes.titlesize": 10,
        "axes.titleweight": "bold",
        "axes.labelsize": 9,
        "axes.labelcolor": "black",
        "axes.edgecolor": "black",
        "axes.linewidth": 0.8,
        "xtick.color": "black",
        "ytick.color": "black",
        "text.color": "black",
        "axes.grid": True,
        "grid.color": "#d9d9d9",
        "grid.linewidth": 0.6,
        "axes.axisbelow": True,
        "legend.frameon": False,
        "legend.fontsize": 8.5,
        "font.family": "DejaVu Sans",
    }
)

INK = {"dark": "#1a1a1a", "mid": "#555555", "light": "#8f8f8f", "pale": "#c4c4c4"}
HATCH = ("", "//", "xx")

# Professional colour palette (figure *text* stays black).
C_PHISH = "#B23A48"   # crimson - phishing class / phishing-direction evidence
C_LEGIT = "#2E6FA7"   # steel blue - legitimate class / legitimate-direction evidence
C_ACCENT = "#1F3864"  # deep navy - emphasis lines
MODEL_COLORS = {
    "Logistic Regression": "#4472C4",   # blue
    "Decision Tree": "#E67E22",         # orange
    "MLP (64x32)": "#27AE60",           # green
}


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# Feature metadata used by the EDA figures and the report appendix.
FEATURE_GROUPS: dict[str, list[str]] = {
    "Address-bar based": [
        "having_IP_Address", "URL_Length", "Shortining_Service", "having_At_Symbol",
        "double_slash_redirecting", "Prefix_Suffix", "having_Sub_Domain", "SSLfinal_State",
        "Domain_registeration_length", "Favicon", "port", "HTTPS_token",
    ],
    "Abnormal request based": [
        "Request_URL", "URL_of_Anchor", "Links_in_tags", "SFH",
        "Submitting_to_email", "Abnormal_URL",
    ],
    "HTML / JavaScript based": [
        "Redirect", "on_mouseover", "RightClick", "popUpWidnow", "Iframe",
    ],
    "Domain based": [
        "age_of_domain", "DNSRecord", "web_traffic", "Page_Rank",
        "Google_Index", "Links_pointing_to_page", "Statistical_report",
    ],
}

FEATURE_DESCRIPTIONS: dict[str, str] = {
    "having_IP_Address": "URL host is an IP address rather than a named domain",
    "URL_Length": "URL abnormally long (more than 54 characters)",
    "Shortining_Service": "URL issued by a shortening service (tinyURL, bit.ly, ...)",
    "having_At_Symbol": "'@' symbol embedded in the URL",
    "double_slash_redirecting": "'//' redirection placed after the protocol",
    "Prefix_Suffix": "'-' used inside the domain name (prefix/suffix trick)",
    "having_Sub_Domain": "number of sub-domains and dots in the URL",
    "SSLfinal_State": "SSL certificate validity, trust issuer and certificate age",
    "Domain_registeration_length": "short domain registration/expiry window",
    "Favicon": "favicon loaded from outside the domain",
    "port": "non-standard ports kept open or unavailable",
    "HTTPS_token": "'https' token embedded misleadingly inside the domain",
    "Request_URL": "page objects (img/css/js) loaded from external domains",
    "URL_of_Anchor": "anchor tags linking outside the domain or to '#'",
    "Links_in_tags": "meta/script/link tags referencing external domains",
    "SFH": "form handler empty or pointing to a different domain",
    "Submitting_to_email": "form submitted through mailto() instead of a server",
    "Abnormal_URL": "URL does not match the domain's official registration record",
    "Redirect": "page applies more than one redirect",
    "on_mouseover": "status bar text hijacked on mouse-over",
    "RightClick": "right-click functionality disabled",
    "popUpWidnow": "pop-up window containing a form",
    "Iframe": "hidden iframe used to obtain personal data",
    "age_of_domain": "domain younger than six months",
    "DNSRecord": "DNS record missing or empty",
    "web_traffic": "Alexa traffic rank very low or unknown",
    "Page_Rank": "Google PageRank close to zero",
    "Google_Index": "page not indexed by Google",
    "Links_pointing_to_page": "abnormal number of inbound links",
    "Statistical_report": "domain flagged in statistical blacklist sources (PhishTank, ...)",
}


# ---------------------------------------------------------------------------
# Task 2 - Threat landscape EDA
# ---------------------------------------------------------------------------

def load_dataset() -> pd.DataFrame:
    log(f"Loading dataset: {DATA_FILE}")
    df = pd.read_csv(DATA_FILE)
    # Dataset coding: -1 = phishing signal, 0 = suspicious, +1 = legitimate.
    # Target: 'Result' (-1 phishing, +1 legitimate) -> binary 'phishing' label.
    df["phishing"] = (df["Result"] == -1).astype(int)
    return df


def eda_summary(df: pd.DataFrame) -> dict:
    log("Running descriptive statistics")
    features = [c for c in df.columns if c not in ("Result", "phishing")]
    desc = df[features].describe().T
    desc.to_csv(RESULTS_DIR / "descriptive_stats.csv")

    n_phish = int(df["phishing"].sum())
    n_legit = len(df) - n_phish

    # Signed Pearson correlation with the binary phishing label.
    corr_with_target = df[features].corrwith(df["phishing"]).sort_values(key=np.abs, ascending=False)
    corr_with_target.rename("pearson_r").to_csv(RESULTS_DIR / "top_indicators.csv")

    summary = {
        "n_samples": len(df),
        "n_features": len(features),
        "n_missing": int(df[features].isna().sum().sum()),
        "n_duplicates": int(df.duplicated().sum()),
        "phishing_count": n_phish,
        "legitimate_count": n_legit,
        "phishing_pct": round(100 * n_phish / len(df), 1),
        "legitimate_pct": round(100 * n_legit / len(df), 1),
        "imbalance_ratio": round(n_phish / n_legit, 3),
        "top_indicators": [
            {
                "feature": f,
                "group": next(g for g, members in FEATURE_GROUPS.items() if f in members),
                "pearson_r": round(float(corr_with_target[f]), 4),
                "description": FEATURE_DESCRIPTIONS[f],
            }
            for f in corr_with_target.index[:10]
        ],
    }
    return summary


def fig_class_distribution(summary: dict) -> None:
    fig, ax = plt.subplots(figsize=(5.2, 3.4))
    labels = ["Phishing\n(Result = -1)", "Legitimate\n(Result = +1)"]
    counts = [summary["phishing_count"], summary["legitimate_count"]]
    bars = ax.bar(labels, counts, width=0.55, color=[C_PHISH, C_LEGIT],
                  edgecolor="black", linewidth=0.8)
    for bar, pct in zip(bars, [summary["phishing_pct"], summary["legitimate_pct"]]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 90,
                f"{int(bar.get_height()):,}\n({pct}%)", ha="center", va="bottom", fontsize=8.5)
    ax.set_ylabel("Number of websites")
    ax.set_ylim(0, max(counts) * 1.22)
    ax.grid(axis="x", visible=False)
    ax.set_title("Class balance: phishing vs legitimate websites")
    fig.tight_layout()
    fig.savefig(RESULTS_DIR / "fig01_class_distribution.png", bbox_inches="tight")
    plt.close(fig)


def fig_correlation_heatmap(df: pd.DataFrame) -> None:
    features = [c for c in df.columns if c not in ("Result", "phishing")]
    corr = df[features + ["phishing"]].corr()
    fig, ax = plt.subplots(figsize=(7.4, 6.6))
    im = ax.imshow(corr.values, cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(len(corr)), corr.columns, rotation=90, fontsize=6.5)
    ax.set_yticks(range(len(corr)), corr.columns, fontsize=6.5)
    ax.grid(visible=False)
    ax.set_title("Pearson correlation matrix of threat indicators")
    cbar = fig.colorbar(im, ax=ax, shrink=0.78)
    cbar.ax.tick_params(labelsize=7, color="black", labelcolor="black")
    cbar.outline.set_edgecolor("black")
    fig.tight_layout()
    fig.savefig(RESULTS_DIR / "fig02_correlation_heatmap.png", bbox_inches="tight")
    plt.close(fig)


def fig_top_indicators(summary: dict) -> None:
    top = summary["top_indicators"]
    names = [t["feature"] for t in top][::-1]
    rs = [t["pearson_r"] for t in top][::-1]
    fig, ax = plt.subplots(figsize=(5.8, 3.9))
    colors = [C_LEGIT if r > 0 else C_PHISH for r in rs]
    ax.barh(names, rs, color=colors, edgecolor="black", linewidth=0.8)
    for i, r in enumerate(rs):
        ax.text(r + (0.012 if r > 0 else -0.012), i, f"{r:+.2f}",
                va="center", ha="left" if r > 0 else "right", fontsize=8)
    ax.axvline(0, color="black", linewidth=0.9)
    ax.set_xlabel("Pearson correlation with phishing label")
    ax.set_xlim(-1.05, 1.05)
    ax.grid(axis="y", visible=False)
    ax.set_title("Top 10 threat indicators ranked by correlation strength")
    fig.tight_layout()
    fig.savefig(RESULTS_DIR / "fig03_top_threat_indicators.png", bbox_inches="tight")
    plt.close(fig)


def fig_feature_distributions(df: pd.DataFrame) -> None:
    picks = ["SSLfinal_State", "URL_of_Anchor", "having_Sub_Domain",
             "web_traffic", "Prefix_Suffix", "Links_in_tags"]
    fig, axes = plt.subplots(2, 3, figsize=(7.6, 4.6))
    for ax, feat in zip(axes.flat, picks):
        ct = df.groupby([feat, "phishing"]).size().unstack(fill_value=0)
        ct = ct.reindex(sorted(ct.index))
        x = np.arange(len(ct.index))
        w = 0.38
        ax.bar(x - w / 2, ct[1] / 1000, width=w, color=C_PHISH, edgecolor="black",
               linewidth=0.7, label="Phishing")
        ax.bar(x + w / 2, ct[0] / 1000, width=w, color=C_LEGIT, edgecolor="black",
               linewidth=0.7, label="Legitimate")
        ax.set_xticks(x, [str(v) for v in ct.index], fontsize=8)
        ax.set_title(f"{feat}", fontsize=8.5)
        ax.set_ylabel("Count (thousands)", fontsize=8)
        ax.tick_params(labelsize=8)
    handles = [plt.Rectangle((0, 0), 1, 1, fc=C_PHISH, ec="black"),
               plt.Rectangle((0, 0), 1, 1, fc=C_LEGIT, ec="black")]
    fig.legend(handles, ["Phishing", "Legitimate"], loc="lower center", ncol=2, fontsize=9)
    fig.suptitle("Value distributions of key indicators by class "
                 "(-1 phishing signal, 0 suspicious, +1 legitimate)", fontsize=9.5)
    fig.tight_layout(rect=(0, 0.06, 1, 0.94))
    fig.savefig(RESULTS_DIR / "fig04_feature_distributions.png", bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Tasks 3-4 - Supervised ML and deep-learning prototype
# ---------------------------------------------------------------------------

def build_models() -> dict:
    log_reg = Pipeline([
        ("scaler", StandardScaler()),
        ("model", LogisticRegression(max_iter=1000, random_state=RANDOM_STATE)),
    ])
    tree = Pipeline([
        ("model", DecisionTreeClassifier(random_state=RANDOM_STATE)),
    ])
    mlp = Pipeline([
        ("scaler", StandardScaler()),
        ("model", MLPClassifier(hidden_layer_sizes=(64, 32), activation="relu", solver="adam",
                                early_stopping=True, validation_fraction=0.1,
                                max_iter=300, random_state=RANDOM_STATE)),
    ])
    return {"Logistic Regression": log_reg, "Decision Tree": tree, "MLP (64x32)": mlp}


def tune_tree(X_train, y_train) -> tuple[dict, float]:
    log("Grid-searching decision-tree hyperparameters (5-fold CV)")
    grid = GridSearchCV(
        DecisionTreeClassifier(random_state=RANDOM_STATE),
        param_grid={"max_depth": [4, 6, 8, 10, None],
                    "min_samples_leaf": [1, 2, 5, 10]},
        scoring="f1", cv=StratifiedKFold(5, shuffle=True, random_state=RANDOM_STATE),
        n_jobs=-1,
    )
    grid.fit(X_train, y_train)
    log(f"  best params: {grid.best_params_} (CV F1 = {grid.best_score_:.4f})")
    return grid.best_params_, float(grid.best_score_)


def cross_validate(models: dict, X_train, y_train) -> dict:
    log("5-fold stratified cross-validation on the training split")
    cv = StratifiedKFold(5, shuffle=True, random_state=RANDOM_STATE)
    out = {}
    for name, model in models.items():
        acc = cross_val_score(model, X_train, y_train, cv=cv, scoring="accuracy", n_jobs=1)
        f1 = cross_val_score(model, X_train, y_train, cv=cv, scoring="f1", n_jobs=1)
        out[name] = {"accuracy_mean": float(acc.mean()), "accuracy_std": float(acc.std()),
                     "f1_mean": float(f1.mean()), "f1_std": float(f1.std())}
        log(f"  {name}: acc {acc.mean():.4f} +/- {acc.std():.4f} | F1 {f1.mean():.4f} +/- {f1.std():.4f}")
    return out


def evaluate_models(models: dict, X_train, X_test, y_train, y_test) -> dict:
    results = {}
    fig_cm, axes_cm = plt.subplots(1, 3, figsize=(8.6, 2.9))
    fig_roc, ax_roc = plt.subplots(figsize=(5.4, 4.4))
    line_styles = ["-", "--", "-."]

    for idx, (name, model) in enumerate(models.items()):
        log(f"Training {name}")
        t0 = time.perf_counter()
        model.fit(X_train, y_train)
        train_s = time.perf_counter() - t0

        t0 = time.perf_counter()
        y_pred = model.predict(X_test)
        infer_s = (time.perf_counter() - t0) / len(X_test) * 1e6  # microseconds/sample

        y_prob = model.predict_proba(X_test)[:, 1]
        cm = confusion_matrix(y_test, y_pred)  # rows: legit(0), phishing(1)
        tn, fp, fn, tp = cm.ravel()

        results[name] = {
            "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
            "precision": round(float(precision_score(y_test, y_pred)), 4),
            "recall": round(float(recall_score(y_test, y_pred)), 4),
            "f1": round(float(f1_score(y_test, y_pred)), 4),
            "roc_auc": round(float(roc_auc_score(y_test, y_prob)), 4),
            "mcc": round(float(matthews_corrcoef(y_test, y_pred)), 4),
            "train_seconds": round(train_s, 3),
            "inference_us_per_sample": round(infer_s, 1),
            "true_positive": int(tp), "false_positive": int(fp),
            "false_negative": int(fn), "true_negative": int(tn),
        }
        log(f"  acc {results[name]['accuracy']:.4f} | F1 {results[name]['f1']:.4f} "
            f"| AUC {results[name]['roc_auc']:.4f} | train {train_s:.2f}s")

        # Confusion-matrix panel.
        ax = axes_cm[idx]
        ax.imshow(cm, cmap="Blues", vmin=0, vmax=cm.max() * 1.6)
        for (i, j), val in np.ndenumerate(cm):
            ax.text(j, i, f"{val:,}", ha="center", va="center", fontsize=9,
                    color="white" if cm[i, j] > cm.max() * 0.75 else "black")
        labels = ["Legit", "Phish"]
        ax.set_xticks([0, 1], labels, fontsize=8)
        ax.set_yticks([0, 1], labels, fontsize=8)
        ax.set_xlabel("Predicted", fontsize=8.5)
        if idx == 0:
            ax.set_ylabel("Actual", fontsize=8.5)
        ax.grid(visible=False)
        ax.set_title(f"{name}\nacc {results[name]['accuracy']:.3f}", fontsize=9)

        # ROC curve.
        fpr, tpr, _ = roc_curve(y_test, y_prob)
        ax_roc.plot(fpr, tpr, linestyle=line_styles[idx], color=MODEL_COLORS[name],
                    linewidth=1.7, label=f"{name} (AUC {results[name]['roc_auc']:.4f})")

    fig_cm.tight_layout()
    fig_cm.savefig(RESULTS_DIR / "fig05_confusion_matrices.png", bbox_inches="tight")
    plt.close(fig_cm)

    ax_roc.plot([0, 1], [0, 1], color=INK["pale"], linewidth=1.0, linestyle=":", label="Chance (AUC 0.5)")
    ax_roc.set_xlabel("False positive rate")
    ax_roc.set_ylabel("True positive rate")
    ax_roc.set_xlim(-0.01, 1.01)
    ax_roc.set_ylim(-0.01, 1.05)
    ax_roc.set_title("ROC curves on the held-out test split")
    ax_roc.legend(loc="lower right")
    fig_roc.tight_layout()
    fig_roc.savefig(RESULTS_DIR / "fig06_roc_curves.png", bbox_inches="tight")
    plt.close(fig_roc)
    return results


def fig_model_comparison(results: dict) -> None:
    names = list(results.keys())
    metrics = ["accuracy", "precision", "recall", "f1", "roc_auc"]
    labels = ["Accuracy", "Precision", "Recall", "F1-score", "ROC-AUC"]
    shades = [INK["dark"], INK["mid"], INK["light"]]
    x = np.arange(len(metrics))
    w = 0.26
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8.4, 3.4), gridspec_kw={"width_ratios": [3, 2]})

    for i, name in enumerate(names):
        vals = [results[name][m] for m in metrics]
        ax1.bar(x + (i - 1) * w, vals, width=w, color=MODEL_COLORS[name],
                edgecolor="black", linewidth=0.7, label=name)
    ax1.set_xticks(x, labels, fontsize=8)
    ax1.set_ylim(0.80, 1.005)
    ax1.set_ylabel("Score")
    ax1.grid(axis="x", visible=False)
    ax1.set_title("Test-set metrics by model")

    train_s = [results[n]["train_seconds"] for n in names]
    bars = ax2.bar(names, train_s, width=0.55, color=[MODEL_COLORS[n] for n in names],
                   edgecolor="black", linewidth=0.7)
    for bar, v in zip(bars, train_s):
        ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() * 1.18,
                 f"{v:.2f}s", ha="center", va="bottom", fontsize=8)
    ax2.set_ylabel("Training time (seconds)")
    ax2.set_yscale("log")
    ax2.set_ylim(0.02, 9)
    ax2.grid(axis="x", visible=False)
    ax2.tick_params(axis="x", labelsize=7.5)
    ax2.set_title("Training cost (log scale)")

    handles = [plt.Rectangle((0, 0), 1, 1, fc=MODEL_COLORS[n], ec="black") for n in names]
    fig.legend(handles, names, loc="lower center", ncol=3, fontsize=8.5)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(RESULTS_DIR / "fig07_model_comparison.png", bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Task 5 - Operational threshold simulation and cost analysis
# ---------------------------------------------------------------------------

def threshold_analysis(model, X_test, y_test) -> dict:
    log("Sweeping decision thresholds 0.05-0.95 on the MLP prototype")
    y_prob = model.predict_proba(X_test)[:, 1]
    rows = []
    for t in np.arange(0.05, 0.96, 0.05):
        y_pred = (y_prob >= t).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
        rows.append({
            "threshold": round(float(t), 2),
            "precision": round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
            "recall": round(float(recall_score(y_test, y_pred)), 4),
            "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
            "false_positive": int(fp), "false_negative": int(fn),
        })
    pd.DataFrame(rows).to_csv(RESULTS_DIR / "threshold_analysis.csv", index=False)

    # Linear operational-cost model: FN events are far costlier than FP alerts.
    cost_ratios = {"1:1": 1, "10:1": 10, "20:1": 20}
    optimal = {}
    for label, fn_cost in cost_ratios.items():
        costs = [(r["false_negative"] * fn_cost + r["false_positive"]) for r in rows]
        best = rows[int(np.argmin(costs))]
        optimal[label] = {"threshold": best["threshold"],
                          "min_cost": int(min(costs)),
                          "fp_at_optimum": best["false_positive"],
                          "fn_at_optimum": best["false_negative"]}
        log(f"  cost ratio FN:FP = {label} -> optimal threshold {best['threshold']:.2f}")

    return {"sweep": rows, "optimal_by_cost_ratio": optimal}


def fig_threshold_analysis(sweep: list[dict], optimal: dict) -> None:
    t = [r["threshold"] for r in sweep]
    fp = [r["false_positive"] for r in sweep]
    fn = [r["false_negative"] for r in sweep]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8.4, 3.4))
    ax1.plot(t, fn, marker="o", color=C_PHISH, linewidth=1.6, markersize=3.5,
             label="False negatives (missed phishing)")
    ax1.plot(t, fp, marker="s", color=C_LEGIT, linewidth=1.6, markersize=3.5,
             linestyle="--", label="False positives (legit sites blocked)")
    ax1.set_xlabel("Decision threshold")
    ax1.set_ylabel("Count on test split")
    ax1.set_title("Error trade-off across operating thresholds")
    ax1.legend(fontsize=7.5)
    ax1.set_xticks(np.arange(0.1, 0.95, 0.1))

    ratios = [10, 20, 1]
    styles = ["-", "--", ":"]
    cost_colors = ["#B23A48", "#8E44AD", "#7F8C8D"]
    for ratio, ls, cc in zip(ratios, styles, cost_colors):
        costs = [r["false_negative"] * ratio + r["false_positive"] for r in sweep]
        ax2.plot(t, costs, linestyle=ls, color=cc, linewidth=1.6, marker=None,
                 label=f"FN:FP cost {ratio}:1")
    ax2.set_xlabel("Decision threshold")
    ax2.set_ylabel("Simulated operational cost")
    ax2.set_title("Cost-minimising thresholds")
    ax2.legend(fontsize=7.5)
    ax2.set_xticks(np.arange(0.1, 0.95, 0.1))

    fig.tight_layout()
    fig.savefig(RESULTS_DIR / "fig08_threshold_analysis.png", bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def main() -> None:
    t_start = time.perf_counter()
    log("=" * 62)
    log("AI-Driven Phishing Threat Detection Prototype - pipeline start")
    log("=" * 62)

    # Task 2 - data + EDA
    df = load_dataset()
    summary = eda_summary(df)
    log(f"  {summary['n_samples']} samples | phishing {summary['phishing_pct']}% "
        f"| missing {summary['n_missing']} | duplicates {summary['n_duplicates']}")
    fig_class_distribution(summary)
    fig_correlation_heatmap(df)
    fig_top_indicators(summary)
    fig_feature_distributions(df)
    log("EDA figures written (fig01-fig04)")

    # Task 3/4 - modelling
    features = [c for c in df.columns if c not in ("Result", "phishing")]
    X, y = df[features].values, df["phishing"].values
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, stratify=y, random_state=RANDOM_STATE)
    log(f"Split: {len(X_train)} train / {len(X_test)} test (stratified, seed {RANDOM_STATE})")

    models = build_models()
    best_tree_params, tree_cv_f1 = tune_tree(X_train, y_train)
    models["Decision Tree"].set_params(
        model__max_depth=best_tree_params["max_depth"],
        model__min_samples_leaf=best_tree_params["min_samples_leaf"])

    cv_results = cross_validate(models, X_train, y_train)
    test_results = evaluate_models(models, X_train, X_test, y_train, y_test)
    fig_model_comparison(test_results)
    log("Model figures written (fig05-fig07)")

    # Task 5 - threshold / cost analysis on the best model (MLP)
    thr = threshold_analysis(models["MLP (64x32)"], X_test, y_test)
    fig_threshold_analysis(thr["sweep"], thr["optimal_by_cost_ratio"])
    log("Threshold figure written (fig08)")

    # Persist metrics bundle for the report generators.
    metrics = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "random_state": RANDOM_STATE,
        "test_size": TEST_SIZE,
        "dataset": summary,
        "split": {"train": len(X_train), "test": len(X_test)},
        "tree_best_params": {k: (v if v is not None else "None") for k, v in best_tree_params.items()},
        "tree_cv_f1": round(tree_cv_f1, 4),
        "cross_validation": cv_results,
        "models": test_results,
        "threshold_analysis": thr,
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
            "matplotlib": matplotlib.__version__,
            "platform": platform.platform(),
        },
    }
    with open(RESULTS_DIR / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    comp = pd.DataFrame(test_results).T
    comp.to_csv(RESULTS_DIR / "model_comparison.csv")

    log(f"metrics.json + model_comparison.csv written")
    log(f"Pipeline finished in {time.perf_counter() - t_start:.1f}s")
    log("=" * 62)


if __name__ == "__main__":
    main()
