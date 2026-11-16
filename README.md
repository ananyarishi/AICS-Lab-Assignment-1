# AI-Driven Phishing Threat Detection Prototype

**Unit 1 Mini Project — Introduction to AI and Cyber Security (ENSP355)**
K.R. Mangalam University | Submitted by **Abhinav Kumar** (2301730191, B.Tech CSE (AIML)-C) | Submitted to **Ms. Monika Khatkar**

---

## Overview

An end-to-end, fully reproducible prototype that detects **phishing websites** from 30
structural and behavioural threat indicators, covering the complete lab workflow:

1. **Workspace bootstrap** — versioned layout (`data/`, `src/`, `results/`, `reports/`), pinned
   dependencies, one-command pipeline, fixed random seed.
2. **Threat landscape analysis (EDA)** — class balance, correlation structure, top threat
   indicators, per-class indicator distributions, data-quality audit (duplicates, coding quirks).
3. **Supervised ML threat classification** — standardised Logistic Regression baseline and a
   5-fold grid-search-tuned Decision Tree.
4. **Deep-learning prototype** — a Dense 64×32 Multi-Layer Perceptron benchmarked against the
   classical models on five test metrics plus training/inference latency.
5. **Ethical reflection & operational challenges** — decision-threshold simulation (0.05–0.95),
   explicit FN:FP cost modelling, recommended two-tier deployment posture, and a structured
   review of proxy bias, privacy (GDPR/DPDP), explainability and adversarial drift.

## Dataset

| Property | Value |
|---|---|
| Source | [UCI Machine Learning Repository — Phishing Websites (ID 327)](https://archive.ics.uci.edu/dataset/327/phishing+websites) |
| Authors | R. M. Mohammad, F. Thabtah, L. McCluskey (2012) |
| Licence | CC BY 4.0 |
| Instances | 11,055 websites |
| Features | 30 categorical indicators (-1 phishing signal / 0 suspicious / +1 legitimate) |
| Class balance | 4,898 phishing (44.3%) vs 6,157 legitimate (55.7%) |

The distributed archive ships the data as an ARFF file; `data/phishing_websites.csv` is its
converted, cached copy. `data/feature_descriptions_raw.txt` preserves the authors' original
feature documentation.

## Repository structure

```
├── data/                    # cached dataset + feature documentation
│   ├── phishing_websites.csv
│   └── feature_descriptions_raw.txt
├── src/
│   ├── main.py              # end-to-end pipeline: EDA -> tuning -> 3 models -> threshold analysis
│   └── generate_pdf_report.py  # rebuilds Technical_Report.pdf + technical_report.md from metrics.json
├── results/                 # 8 figures, metrics.json, comparison/threshold/stat tables
├── reports/
│   ├── Technical_Report.pdf # 15-page technical report (black text, monochrome figures)
│   └── technical_report.md  # Markdown twin of the PDF
├── requirements.txt
└── README.md
```

## Quickstart

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/macOS

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the full pipeline (EDA, training, benchmarking, threshold analysis)
python src/main.py

# 4. Rebuild the technical report from the persisted metrics
python src/generate_pdf_report.py
```

The pipeline is deterministic (seed 42, stratified 80/20 split → 8,844 train / 2,211 test).
Every number quoted in the report is generated from `results/metrics.json`, so re-running
steps 3–4 always regenerates a report consistent with the latest run.

## Results (held-out test split, n = 2,211)

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC | MCC | Train time |
|---|---|---|---|---|---|---|---|
| Logistic Regression | 0.9281 | 0.9344 | 0.9010 | 0.9174 | 0.9785 | +0.8542 | 0.06 s |
| Decision Tree (tuned) | **0.9697** | **0.9760** | **0.9551** | **0.9654** | 0.9764 | **+0.9386** | 0.04 s |
| MLP 64×32 (deep learning) | 0.9656 | 0.9699 | 0.9520 | 0.9609 | **0.9944** | +0.9304 | 3.4 s |

Key findings:

- **SSL certificate state** and **anchor-URL behaviour** dominate the threat signal
  (|r| ≈ 0.71 / 0.69 with the class label).
- The tuned Decision Tree is the best *single-threshold* classifier; the MLP offers the best
  *ranking quality* (ROC-AUC 0.9944) — the property that matters when the operating threshold
  must move.
- Threshold sweep: at 0.05 the prototype catches 99.0% of phishing at the cost of 177 false
  alarms; at 0.90 only 2 false alarms but 127 missed attacks. Balanced-cost optimum sits near
  0.65; recommended posture: autonomous blocking only above ~0.80–0.90, analyst review for
  0.40–0.80.

## Report deliverables

- **`reports/Technical_Report.pdf`** — 15-page publication-grade report: title page, table of
  contents, 10 numbered sections, 8 colour figures, 7 colour-styled tables, references and
  appendices. All report text renders in pure black; figures and tables use a professional
  colour palette.
- **`reports/technical_report.md`** — Markdown twin with the same content and numbers.
- **`results/metrics.json`** — machine-readable bundle of every metric, threshold sweep row and
  environment fingerprint.

## Ethical statement

The prototype consumes structural metadata (URL shape, certificate properties, page scripts),
not user content or identities. The report analyses proxy bias against young/small publishers,
GDPR & DPDP Act (2023) obligations for visit logs, explainability trade-offs between the
auditable classical models and the MLP, and adversarial drift, and recommends narrow autonomy
with human-in-the-loop review for irreversible actions.

## Academic integrity

This submission is original work prepared for ENSP355 Lab (Unit 1 mini project). The dataset
and its feature documentation are cited to the original authors; all libraries are cited in
the report's reference list.
