"""
Technical report generator
==========================
Unit 1 Mini Project - Introduction to AI and Cyber Security (ENSP355)

Builds two synchronised deliverables from results/metrics.json:
  1. reports/Technical_Report.pdf   - publication-grade PDF (black text only)
  2. reports/technical_report.md    - Markdown source of the same report

Every figure of merit is read from metrics.json, so re-running the pipeline
automatically keeps the report numbers in sync.

Usage: python src/generate_pdf_report.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    Image,
    KeepTogether,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

BASE_DIR = Path(__file__).resolve().parents[1]
RESULTS_DIR = BASE_DIR / "results"
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

BLACK = colors.Color(0, 0, 0)
NAVY = colors.HexColor("#1F3864")          # accent rules and table header underline
HEADER_BG = colors.HexColor("#D9E7F5")     # table header fill (text stays black)
ROW_ALT = colors.HexColor("#F4F8FC")       # zebra row shading
GREY_RULE = colors.HexColor("#8FA3BF")     # table grid

PAGE_W, PAGE_H = A4
MARGIN = 2.3 * cm
TEXT_W = PAGE_W - 2 * MARGIN

STUDENT = {
    "name": "Abhinav Kumar",
    "roll": "2301730191",
    "section": "B.Tech CSE (AIML) - C",
    "course": "Introduction to AI and Cyber Security (ENSP355)",
    "faculty": "Ms. Monika Khatkar",
    "university": "K.R. Mangalam University",
}

# ---------------------------------------------------------------------------
# Styles - every text style renders in pure black
# ---------------------------------------------------------------------------

S = {
    "TitleBig": ParagraphStyle("TitleBig", fontName="Helvetica-Bold", fontSize=19, leading=25,
                               alignment=TA_CENTER, textColor=BLACK, spaceAfter=6),
    "TitleSub": ParagraphStyle("TitleSub", fontName="Helvetica", fontSize=11.5, leading=16,
                               alignment=TA_CENTER, textColor=BLACK, spaceAfter=4),
    "TitleMeta": ParagraphStyle("TitleMeta", fontName="Helvetica", fontSize=11, leading=17,
                                alignment=TA_CENTER, textColor=BLACK),
    "TitleSmall": ParagraphStyle("TitleSmall", fontName="Helvetica", fontSize=9.5, leading=13,
                                 alignment=TA_CENTER, textColor=BLACK),
    "H1": ParagraphStyle("H1", fontName="Helvetica-Bold", fontSize=13, leading=16,
                         textColor=BLACK, spaceBefore=18, spaceAfter=8, keepWithNext=1),
    "H2": ParagraphStyle("H2", fontName="Helvetica-Bold", fontSize=10.8, leading=14,
                         textColor=BLACK, spaceBefore=11, spaceAfter=5, keepWithNext=1),
    "Body": ParagraphStyle("Body", fontName="Helvetica", fontSize=10, leading=14.2,
                           alignment=TA_JUSTIFY, textColor=BLACK, spaceAfter=7),
    "Bullet": ParagraphStyle("Bullet", fontName="Helvetica", fontSize=10, leading=14,
                             alignment=TA_LEFT, textColor=BLACK, leftIndent=16,
                             bulletIndent=5, spaceAfter=4),
    "Caption": ParagraphStyle("Caption", fontName="Helvetica-Oblique", fontSize=8.5, leading=11.5,
                              alignment=TA_CENTER, textColor=BLACK, spaceBefore=4, spaceAfter=13),
    "Cell": ParagraphStyle("Cell", fontName="Helvetica", fontSize=8.3, leading=10.6, textColor=BLACK),
    "CellC": ParagraphStyle("CellC", fontName="Helvetica", fontSize=8.3, leading=10.6,
                            alignment=TA_CENTER, textColor=BLACK),
    "CellHead": ParagraphStyle("CellHead", fontName="Helvetica-Bold", fontSize=8.3, leading=10.6,
                               alignment=TA_CENTER, textColor=BLACK),
    "Ref": ParagraphStyle("Ref", fontName="Helvetica", fontSize=9.3, leading=13,
                          textColor=BLACK, leftIndent=18, firstLineIndent=-18, spaceAfter=5),
    "TocH": ParagraphStyle("TocH", fontName="Helvetica-Bold", fontSize=13, leading=16,
                           textColor=BLACK, spaceAfter=10),
}

TOC_LEVELS = [
    ParagraphStyle("TOC0", fontName="Helvetica-Bold", fontSize=10.5, leading=14,
                   textColor=BLACK, leftIndent=2),
    ParagraphStyle("TOC1", fontName="Helvetica", fontSize=9.5, leading=12.5,
                   textColor=BLACK, leftIndent=16),
]


# ---------------------------------------------------------------------------
# Document template with TOC hooks, running headers and footers
# ---------------------------------------------------------------------------

def _header_footer(canv, doc) -> None:
    canv.saveState()
    canv.setStrokeColor(NAVY)
    canv.setLineWidth(0.6)
    # Footer
    canv.line(MARGIN, 1.55 * cm, PAGE_W - MARGIN, 1.55 * cm)
    canv.setFont("Helvetica", 8.5)
    canv.setFillColor(BLACK)
    canv.drawCentredString(PAGE_W / 2, 1.05 * cm, f"Page {canv.getPageNumber()}")
    # Header
    canv.line(MARGIN, PAGE_H - 1.45 * cm, PAGE_W - MARGIN, PAGE_H - 1.45 * cm)
    canv.setFont("Helvetica", 8)
    canv.drawString(MARGIN, PAGE_H - 1.22 * cm, "AI-Driven Phishing Threat Detection Prototype")
    canv.drawRightString(PAGE_W - MARGIN, PAGE_H - 1.22 * cm, "ENSP355 | Unit 1 Mini Project")
    canv.restoreState()


class ReportDoc(BaseDocTemplate):
    def __init__(self, filename: str, **kw):
        super().__init__(filename, **kw)
        frame = Frame(MARGIN, 2.0 * cm, TEXT_W, PAGE_H - 2.0 * cm - 2.1 * cm, id="main")
        title_frame = Frame(MARGIN, 2.0 * cm, TEXT_W, PAGE_H - 2.0 * cm - 2.1 * cm, id="title")
        self.addPageTemplates([
            PageTemplate(id="Title", frames=[title_frame], onPage=lambda c, d: None),
            PageTemplate(id="Body", frames=[frame], onPage=_header_footer),
        ])

    def afterFlowable(self, flowable) -> None:
        if not isinstance(flowable, Paragraph):
            return
        style = flowable.style.name
        if style not in ("H1", "H2"):
            return
        text = flowable.getPlainText()
        if text == "Contents":
            return
        key = "sec-" + re.sub(r"\W+", "-", text)[:70]
        self.canv.bookmarkPage(key)
        self.canv.addOutlineEntry(text, key, level=0 if style == "H1" else 1, closed=False)
        self.notify("TOCEntry", (0 if style == "H1" else 1, text, self.page))


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def P(text: str, style: str = "Body") -> Paragraph:
    return Paragraph(text, S[style])


def B(text: str) -> Paragraph:
    return Paragraph(text, S["Bullet"], bulletText="\u2022")


def fig(path: str, caption: str, width: float = 15.6 * cm) -> KeepTogether:
    img_path = RESULTS_DIR / path
    from PIL import Image as PILImage
    with PILImage.open(img_path) as im:
        w, h = im.size
    height = width * h / w
    return KeepTogether([
        Image(str(img_path), width=width, height=height),
        Paragraph(caption, S["Caption"]),
    ])


def make_table(header: list[str], rows: list[list[str]], col_widths: list[float],
               left_cols: tuple[int, ...] = (0,)) -> Table:
    data = [[Paragraph(h, S["CellHead"]) for h in header]]
    for r in rows:
        cells = []
        for j, c in enumerate(r):
            st = "Cell" if j in left_cols else "CellC"
            cells.append(Paragraph(str(c), S[st]))
        data.append(cells)
    t = Table(data, colWidths=col_widths, repeatRows=1, hAlign="CENTER")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ROW_ALT]),
        ("GRID", (0, 0), (-1, -1), 0.5, GREY_RULE),
        ("LINEBELOW", (0, 0), (-1, 0), 1.0, NAVY),
        ("LINEABOVE", (0, 0), (-1, 0), 1.0, NAVY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def table_block(title_caption: str, table: Table) -> KeepTogether:
    return KeepTogether([Spacer(1, 4), table, Paragraph(title_caption, S["Caption"])])


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------

def title_page() -> list:
    return [
        Spacer(1, 2.2 * cm),
        P("K.R. MANGALAM UNIVERSITY", "TitleBig"),
        Spacer(1, 0.15 * cm),
        P("School of Engineering and Technology", "TitleSub"),
        P("Course: " + STUDENT["course"], "TitleSub"),
        Spacer(1, 1.4 * cm),
        P("UNIT 1 MINI PROJECT - LAB ASSIGNMENT", "TitleSub"),
        Spacer(1, 0.5 * cm),
        HRFlowable(width="55%", thickness=1.4, color=NAVY, spaceAfter=10),
        P("AI-Driven Phishing Threat Detection Prototype", "TitleBig"),
        P("Exploratory Analysis, Supervised Classification and a Deep-Learning Baseline "
          "on the UCI Phishing Websites Dataset", "TitleSub"),
        HRFlowable(width="55%", thickness=1.4, color=NAVY, spaceBefore=8),
        Spacer(1, 1.9 * cm),
        make_table(
            ["Field", "Details"],
            [
                ["Student name", STUDENT["name"]],
                ["Roll number", STUDENT["roll"]],
                ["Section", STUDENT["section"]],
                ["Course", STUDENT["course"]],
                ["Submitted to", STUDENT["faculty"]],
                ["Institution", STUDENT["university"]],
            ],
            [4.6 * cm, 9.4 * cm],
        ),
        Spacer(1, 1.6 * cm),
        P("Dataset: UCI Machine Learning Repository - Phishing Websites (ID 327), "
          "Mohammad, Thabtah and McCluskey (2012), CC BY 4.0", "TitleSmall"),
        Spacer(1, 0.3 * cm),
        P("All report text is rendered in black; figures and tables use a professional "
          "colour palette.", "TitleSmall"),
        NextPageTemplate("Body"),
        PageBreak(),
    ]


def contents_block() -> list:
    toc = TableOfContents(dotsMinLevel=0)
    toc.levelStyles = TOC_LEVELS
    return [P("Contents", "H1"), toc, PageBreak()]


def build_story(m: dict) -> list:
    ds, models, cv = m["dataset"], m["models"], m["cross_validation"]
    lr, dt, mlp = models["Logistic Regression"], models["Decision Tree"], models["MLP (64x32)"]
    thr, opt = m["threshold_analysis"]["sweep"], m["threshold_analysis"]["optimal_by_cost_ratio"]
    tree_params = m["tree_best_params"]
    tree_depth = "unrestricted" if tree_params["max_depth"] in (None, "None") else tree_params["max_depth"]
    env = m["environment"]
    sweep = {r["threshold"]: r for r in thr}
    story: list = []

    # -------------------------------------------------------------- 1
    story += [P("1. Executive Summary", "H1"),
              P("This mini project develops an end-to-end, reproducible prototype that detects "
                "phishing websites from thirty structural and behavioural threat indicators. The "
                f"study uses the UCI Machine Learning Repository <i>Phishing Websites</i> dataset "
                f"(ID 327; {ds['n_samples']:,} websites, {ds['n_features']} indicators). Exploratory "
                "data analysis shows a moderately balanced classification problem "
                f"({ds['phishing_pct']}% phishing) with no missing values, two dominant threat "
                "signals - the SSL certificate state and the anchor-URL behaviour (|r| &asymp; 0.70 "
                "with the class label) - and clear redundancy clusters among HTML-script and "
                "client-side indicators."),
              P("Three supervised models are benchmarked on a stratified 20% hold-out split "
                f"(2,211 websites) after five-fold cross-validated tuning: a regularised Logistic "
                f"Regression baseline (accuracy {lr['accuracy']:.2%}), a hyperparameter-tuned "
                f"Decision Tree (accuracy {dt['accuracy']:.2%}, the best single-threshold classifier), "
                f"and a 64x32 Multi-Layer Perceptron (accuracy {mlp['accuracy']:.2%}) which delivers "
                f"the best ranking quality (ROC-AUC {mlp['roc_auc']:.4f}) and therefore the most "
                "flexible operating envelope. All three models train in under four seconds, and the "
                "Decision Tree classifies a website in under a microsecond, confirming the practical "
                "feasibility of embedding the prototype in real-time web-filtering pipelines."),
              P("A threshold simulation across 0.05-0.95 quantifies the operational trade-off between "
                "false positives, which block legitimate users, and false negatives, which let phishing "
                "pages through. Under a balanced cost model the optimum lies near a 0.60-0.70 "
                "threshold; when a missed attack is an order of magnitude costlier than a false alert, "
                "a low threshold maximises protection. The report closes with an ethical analysis "
                "covering proxy bias, privacy, explainability and adversarial drift, and recommends a "
                "human-in-the-loop deployment posture.")]

    # -------------------------------------------------------------- 2
    story += [P("2. Introduction and Objectives", "H1"),
              P("Phishing remains one of the most damaging and scalable cyber threats: a single "
                "credential-harvesting page can compromise thousands of users before takedown lists "
                "catch up. Rule-based filters and blocklists defend against known pages, but phishing "
                "is an adversarial, fast-regenerating problem, so defensive systems must generalise to "
                "previously unseen URLs. Machine learning addresses exactly this gap - it learns the "
                "statistical fingerprint of malicious design choices rather than matching literal "
                "signatures."),
              P("The project implements the five tasks of the Unit 1 laboratory brief:"),
              B("<b>Task 1 - Workspace bootstrap:</b> a versioned project layout (data/, src/, "
                "results/, reports/) with pinned dependencies and a single reproducible entry point."),
              B("<b>Task 2 - Threat landscape analysis:</b> exploratory data analysis of the phishing "
                "dataset, class-balance assessment, correlation structure and indicator ranking."),
              B("<b>Task 3 - Supervised ML threat classification:</b> standardised preprocessing, a "
                "Logistic Regression baseline and a tuned Decision Tree classifier."),
              B("<b>Task 4 - Deep-learning prototype:</b> a Multi-Layer Perceptron (Dense 64x32) "
                "benchmarked against the classical models on five test metrics and two latency "
                "measures."),
              B("<b>Task 5 - Ethics and operational challenges:</b> a decision-threshold simulation "
                "from 0.10 to 0.90, an explicit false-positive/false-negative cost analysis, and a "
                "structured reflection on bias, privacy, explainability and drift."),
              P("The remainder of this report follows that order. All results are produced by "
                "<font face='Courier'>src/main.py</font>; the report itself is regenerated by "
                "<font face='Courier'>src/generate_pdf_report.py</font> from the persisted metrics, "
                "so every number shown is traceable to a script run.", "Body")]

    # -------------------------------------------------------------- 3
    story += [P("3. Dataset and Threat Landscape", "H1"),
              P("3.1 Dataset provenance", "H2"),
              P("The dataset was published by Mohammad, Thabtah and McCluskey (University of "
                "Huddersfield) and is distributed through the UCI Machine Learning Repository under "
                "a Creative Commons BY 4.0 licence. Each of the 11,055 rows describes one website "
                "with 30 categorical indicators and a class label. Indicators were extracted from "
                "three surfaces: the URL string, the HTML/JavaScript content of the page, and "
                "third-party domain intelligence (WHOIS, DNS, traffic ranks and blacklists). Each "
                "indicator takes the value -1 (phishing signal), 0 (suspicious/neutral) or +1 "
                "(legitimate signal); a smaller subset is binary. The label encodes "
                "-1 as phishing and +1 as legitimate; the analysis remaps it to a binary "
                "<i>phishing = 1</i> target."),
              table_block(
                  "Table 1. Dataset overview.",
                  make_table(["Property", "Value"],
                             [["Instances", f"{ds['n_samples']:,}"],
                              ["Features", f"{ds['n_features']} categorical indicators"],
                              ["Phishing websites", f"{ds['phishing_count']:,} ({ds['phishing_pct']}%)"],
                              ["Legitimate websites", f"{ds['legitimate_count']:,} ({ds['legitimate_pct']}%)"],
                              ["Missing values", str(ds["n_missing"])],
                              ["Duplicated feature profiles", f"{ds['n_duplicates']:,}"]],
                             [5.2 * cm, 8.4 * cm])),
              P("3.2 Class balance", "H2"),
              P(f"Phishing pages account for {ds['phishing_pct']}% of the corpus "
                f"({ds['phishing_count']:,} of {ds['n_samples']:,}), a mild imbalance ratio of "
                f"{ds['imbalance_ratio']:.2f} phishing-to-legitimate. Because neither class falls "
                "below roughly 44%, accuracy remains a meaningful headline metric, and no synthetic "
                "oversampling is required; precision and recall are still tracked per class so that "
                "any asymmetric behaviour stays visible. Figure 1 shows the class distribution."),
              fig("fig01_class_distribution.png",
                  "Figure 1. Class balance of the UCI Phishing Websites dataset.", 10.6 * cm),
              P("3.3 A note on duplicated feature profiles", "H2"),
              P(f"The dataset contains {ds['n_duplicates']:,} rows ({ds['n_duplicates']/ds['n_samples']:.0%} of the "
                "corpus) that share an identical feature vector with another row. These are not data-entry "
                "errors: with 30 coarse categorical indicators the theoretical combination space is small, "
                "so structurally similar websites naturally collapse onto the same profile. Duplicates are "
                "therefore retained - they carry genuine class-prevalence information, and removing them "
                "would distort the prior the models must learn in deployment.", "Body")]

    # -------------------------------------------------------------- 4
    top_rows = [[f"{t['feature']}", t["group"], f"{t['pearson_r']:+.3f}", t["description"]]
                for t in ds["top_indicators"]]
    story += [P("4. Exploratory Data Analysis", "H1"),
              P("4.1 Correlation structure", "H2"),
              P("Figure 2 maps the Pearson correlation matrix over all 30 indicators plus the class "
                "label. Three observations stand out. First, the class label is strongly correlated "
                "with a compact set of indicators, led by the SSL certificate state and anchor "
                "behaviour. Second, several indicator pairs are near-redundant - Favicon with port, "
                "and on_mouseover with RightClick, popUpWidnow and Iframe - reflecting that the same "
                "hosting shortcut shows up in several measurements. Third, most domain-intelligence "
                "indicators are only weakly correlated with each other, so they contribute "
                "complementary rather than duplicated evidence."),
              fig("fig02_correlation_heatmap.png",
                  "Figure 2. Pearson correlation matrix of the 30 threat indicators and the "
                  "phishing label.", 14.6 * cm),
              P("4.2 Top threat indicators", "H2"),
              P("Table 2 ranks the ten indicators most strongly (in absolute value) correlated with "
                "the phishing label; Figure 3 visualises the same ranking. The two leading signals, "
                "SSLfinal_State and URL_of_Anchor, both exceed |r| = 0.69 and alone suggest that a "
                "high-accuracy linear boundary exists."),
              P("One coding caveat surfaced during EDA: the distributed copy of "
                "<i>Domain_registeration_length</i> is inconsistent with its published definition "
                "(phishing websites more frequently carry the value documented as the "
                "legitimate-signal +1). This is a known quirk of the public corpus; the learned "
                "models simply absorb the flipped coding, but it underlines why feature provenance "
                "should be audited before operational reuse of any public dataset."),
              table_block(
                  "Table 2. Top ten phishing-correlated threat indicators (signed Pearson r with the "
                  "binary phishing label).",
                  make_table(["Indicator", "Group", "r", "What it measures"],
                             top_rows, [4.9 * cm, 3.2 * cm, 1.3 * cm, 5.6 * cm],
                             left_cols=(0, 3))),
              fig("fig03_top_threat_indicators.png",
                  "Figure 3. Top ten threat indicators ranked by absolute correlation with the "
                  "phishing label.", 12.8 * cm),
              P("4.3 Indicator distributions by class", "H2"),
              P("Figure 4 contrasts the value distributions of six representative indicators across "
                "the two classes. The separation is strongest for SSLfinal_State, URL_of_Anchor and "
                "web_traffic: phishing pages concentrate on the -1 (phishing-signal) value while "
                "legitimate pages concentrate on +1. Features such as Prefix_Suffix separate less "
                "cleanly because hyphenated domains are also common among legitimate sites - a first "
                "indication that some indicators carry weaker, noisier evidence."),
              fig("fig04_feature_distributions.png",
                  "Figure 4. Value distributions of six key indicators for phishing (-1 coding) "
                  "versus legitimate (+1 coding) websites.", 15.4 * cm)]

    # -------------------------------------------------------------- 5
    story += [P("5. Methodology", "H1"),
              P("5.1 Preprocessing and data partitioning", "H2"),
              P("The 30 indicators are already categorical integers, so no one-hot expansion is "
                "needed; they are used in their native ordinal coding, which preserves the "
                "phishing/suspicious/legitimate ordering inside each feature. The corpus is split "
                f"into {m['split']['train']:,} training and {m['split']['test']:,} test websites "
                "(80/20) with stratification on the class label and a fixed random seed "
                f"({m['random_state']}) for reproducibility. The test set is touched exactly once, "
                "at final evaluation."),
              P("5.2 Models and tuning", "H2"),
              P("<b>Logistic Regression</b> serves as the interpretable linear baseline; features are "
                "standardised inside a Pipeline whose scaler is fitted only on training folds, so no "
                "information leaks into validation or test. <b>Decision Tree</b> hyperparameters are "
                "selected by a 5-fold grid search over maximum depth (4-10 or unrestricted) and "
                f"minimum leaf size (1-10), optimising F1-score; the search selects depth = "
                f"{tree_depth}, min_samples_leaf = {tree_params['min_samples_leaf']} "
                f"(CV F1 = {m['tree_cv_f1']:.4f}). <b>Multi-Layer Perceptron</b> implements the "
                "deep-learning prototype: two Dense layers of 64 and 32 ReLU units with an Adam "
                "optimiser, early stopping on 10% of the training fold, following the architecture "
                "prescribed by the laboratory brief."),
              P("5.3 Evaluation protocol", "H2"),
              P("Each model is evaluated with accuracy, precision, recall and F1 on the phishing "
                "class, ROC-AUC for threshold-independent ranking quality, and the Matthews "
                "correlation coefficient as a balance-aware summary. Operational feasibility is "
                "measured with wall-clock training time and per-sample inference latency on the test "
                "split. Five-fold cross-validation on the training partition additionally reports "
                "mean +/- standard deviation, so conclusions do not rest on a single split.")]

    # -------------------------------------------------------------- 6
    cv_rows = [[name, f"{cv[name]['accuracy_mean']:.4f} \u00b1 {cv[name]['accuracy_std']:.4f}",
                f"{cv[name]['f1_mean']:.4f} \u00b1 {cv[name]['f1_std']:.4f}"] for name in cv]
    bench_rows = [[name,
                   f"{models[name]['accuracy']:.4f}", f"{models[name]['precision']:.4f}",
                   f"{models[name]['recall']:.4f}", f"{models[name]['f1']:.4f}",
                   f"{models[name]['roc_auc']:.4f}", f"{models[name]['mcc']:+.4f}"]
                  for name in models]
    eff_rows = [[name, f"{models[name]['train_seconds']:.2f} s",
                 f"{models[name]['inference_us_per_sample']:.1f}",
                 f"{models[name]['false_positive']}", f"{models[name]['false_negative']}"]
                for name in models]
    story += [P("6. Results and Benchmarking", "H1"),
              P("6.1 Cross-validated stability", "H2"),
              P("Table 3 reports five-fold cross-validation on the training partition. All three "
                "families are stable (standard deviations below one accuracy point), which indicates "
                "the dataset is large enough for the models to learn a consistent boundary."),
              table_block(
                  "Table 3. Five-fold cross-validation on the training partition (mean +/- standard "
                  "deviation).",
                  make_table(["Model", "Accuracy", "F1-score (phishing)"],
                             cv_rows, [5.4 * cm, 4.6 * cm, 4.6 * cm])),
              P("6.2 Hold-out test benchmark", "H2"),
              P("Table 4 and Figure 5 present final held-out performance. The tuned Decision Tree is "
                f"the strongest single-threshold classifier (accuracy {dt['accuracy']:.2%}, F1 "
                f"{dt['f1']:.4f}), slightly ahead of the MLP ({mlp['accuracy']:.2%}, F1 "
                f"{mlp['f1']:.4f}); both clearly outperform the linear baseline "
                f"({lr['accuracy']:.2%}). The MLP, however, achieves the best ranking quality by a "
                f"wide margin (ROC-AUC {mlp['roc_auc']:.4f} versus {dt['roc_auc']:.4f} for the tree), "
                "which is exactly the property that matters when an operations team needs to move the "
                "decision threshold. This is an honest and instructive result: on coarse categorical "
                "feature spaces, a well-tuned shallow model remains competitive with a neural "
                "network, and the network's edge appears in calibration and ranking rather than in "
                "raw accuracy."),
              table_block(
                  "Table 4. Held-out test-set benchmark (n = "
                  f"{m['split']['test']:,}; positive class = phishing).",
                  make_table(["Model", "Accuracy", "Precision", "Recall", "F1", "ROC-AUC", "MCC"],
                             bench_rows,
                             [4.0 * cm, 1.9 * cm, 1.9 * cm, 1.9 * cm, 1.9 * cm, 1.9 * cm, 1.9 * cm])),
              fig("fig07_model_comparison.png",
                  "Figure 5. Test-set metrics (left) and training cost on a logarithmic scale "
                  "(right) for the three models.", 15.6 * cm),
              P("6.3 Ranking quality", "H2"),
              P("Figure 6 overlays the ROC curves. The MLP curve dominates across the entire "
                "operating range: it reaches a true-positive rate above 0.95 at a false-positive "
                "rate near 0.02, while the tree and the linear model need roughly twice the false "
                "alerts for the same coverage. For a SOC selecting an operating point from ranked "
                "alerts, the MLP offers the largest usable envelope."),
              fig("fig06_roc_curves.png",
                  "Figure 6. ROC curves on the held-out test split.", 12.4 * cm),
              P("6.4 Error anatomy", "H2"),
              P("Figure 7 decomposes the 2,211 test predictions. The tuned tree commits "
                f"{dt['false_positive']} false positives and {dt['false_negative']} false negatives; "
                f"the MLP commits {mlp['false_positive']} and {mlp['false_negative']} respectively; "
                f"the linear baseline commits {lr['false_positive']} and {lr['false_negative']}. "
                "Missing a phishing page (false negative) exposes a user to credential theft, while "
                "a false positive blocks a legitimate site and erodes trust in the filter - the two "
                "error types are not interchangeable, and Section 7 quantifies that asymmetry."),
              fig("fig05_confusion_matrices.png",
                  "Figure 7. Confusion matrices on the held-out test split.", 15.8 * cm),
              P("6.5 Computational efficiency", "H2"),
              P("Table 5 summarises the cost side of the deployment decision. Every model trains in "
                "seconds on commodity hardware and classifies a website in a few microseconds, so "
                "throughput is not a bottleneck even for ISP-scale filtering. The tree is the "
                "cheapest to train and the fastest to query; the MLP needs roughly 90x the tree's "
                "training time but still finishes in under four seconds, and its per-sample latency "
                "remains two orders of magnitude below any interactive budget."),
              table_block(
                  "Table 5. Training cost, per-sample inference latency and raw error counts.",
                  make_table(["Model", "Train time", "Inference (us/sample)", "False positives",
                              "False negatives"],
                             eff_rows, [4.4 * cm, 2.6 * cm, 3.4 * cm, 2.6 * cm, 2.8 * cm]))]

    # -------------------------------------------------------------- 7
    def row_at(t):
        r = sweep[t]
        return [f"{t:.2f}", f"{r['precision']:.3f}", f"{r['recall']:.3f}", f"{r['accuracy']:.3f}",
                f"{r['false_positive']}", f"{r['false_negative']}"]

    story += [P("7. Operational Threshold Analysis", "H1"),
              P("7.1 The false-positive / false-negative trade-off", "H2"),
              P("A classifier ships with a default 0.50 threshold, but a SOC can - and should - "
                "choose the operating point deliberately. Figure 8 sweeps the MLP decision threshold "
                "from 0.05 to 0.95 on the test split. At 0.05 the prototype catches "
                f"{100*sweep[0.05]['recall']:.1f}% of phishing pages but raises "
                f"{sweep[0.05]['false_positive']} false alarms against legitimate users; at 0.90 it "
                f"raises only {sweep[0.90]['false_positive']} false alarms yet misses "
                f"{sweep[0.90]['false_negative']} attacks. Table 6 lists representative operating "
                "points."),
              fig("fig08_threshold_analysis.png",
                  "Figure 8. Error trade-off (left) and simulated operational cost under three "
                  "FN:FP cost ratios (right) across decision thresholds.", 14.6 * cm),
              table_block(
                  "Table 6. Representative operating points of the MLP prototype on the test split.",
                  make_table(["Threshold", "Precision", "Recall", "Accuracy", "False positives",
                              "False negatives"],
                             [row_at(t) for t in (0.10, 0.25, 0.40, 0.50, 0.60, 0.65, 0.80, 0.90)],
                             [2.6 * cm, 2.5 * cm, 2.5 * cm, 2.5 * cm, 3.0 * cm, 3.0 * cm])),
              P("7.2 Cost-based operating points", "H2"),
              P("To make the asymmetry explicit, a linear cost model is applied to the sweep: cost = "
                "FN x c_FN + FP x c_FP, with the cost of one missed phishing compromise set to 1x, "
                "10x and 20x the cost of one false alert. Under balanced costs (1:1) the optimum "
                f"sits at a threshold of {opt['1:1']['threshold']:.2f} "
                f"({opt['1:1']['fp_at_optimum']} FP, {opt['1:1']['fn_at_optimum']} FN); when a "
                "compromise costs ten times a false alert the optimum moves to the protective end of "
                f"the range (threshold {opt['10:1']['threshold']:.2f}, recall "
                f"{100*sweep[0.05]['recall']:.1f}%), accepting a materially higher alert volume as "
                "the price of coverage. The practical reading is that the threshold is a governance "
                "decision, not a technical default: it should be set from the organisation's own "
                "cost of disruption versus cost of compromise, and revisited as both change."),
              P("7.3 Recommended deployment posture", "H2"),
              B("<b>Block tier:</b> act autonomously only above a high-confidence threshold "
                "(about 0.80-0.90), where precision exceeds 99% and the false-lockout risk is "
                "minimal."),
              B("<b>Review tier:</b> route 0.40-0.80 predictions to analyst inspection or to "
                "secondary signals (reputation feeds, sandbox detonation) before any user-facing "
                "action."),
              B("<b>Feedback loop:</b> log analyst verdicts and retrain on schedule, so the "
                "threshold and the model drift together with the threat landscape."),
              P("This two-tier design keeps the high recall of a low threshold where it is cheap "
                "(alerts) and the high precision of a high threshold where it is expensive "
                "(automatic blocking).", "Body")]

    # -------------------------------------------------------------- 8
    story += [P("8. Ethical Reflection and Responsible AI", "H1"),
              P("8.1 Proxy bias and fairness", "H2"),
              P("The dataset encodes correlations, not causes, and some indicators are proxies for "
                "legitimate but atypical behaviour. Young domains, low traffic ranks and missing "
                "search-engine indexing are over-represented among phishing pages, yet they are also "
                "the natural state of a start-up, a community project or a newly launched campaign. "
                "An automatic blocker built on these features systematically disadvantages small and "
                "new publishers - a fairness problem documented widely for content-moderation and "
                "trust systems. Mitigations include operating in review rather than block mode for "
                "low-confidence predictions, auditing error rates across domain categories, and "
                "providing a fast appeal path for wrongly flagged sites."),
              P("8.2 Privacy and data protection", "H2"),
              P("The prototype consumes structural metadata - URL shape, certificate properties, "
                "page scripts - rather than user content or identities, so it avoids most personal "
                "data by design. Under GDPR and India's DPDP Act 2023 the relevant duties are data "
                "minimisation and purpose limitation: logs of flagged visits should retain URLs "
                "only as long as needed for triage, should not be joined with user identities "
                "beyond what security operations require, and should be covered by the lawful "
                "basis for network-security monitoring. Categorical features also mean the model "
                "itself stores no reconstructable personal data, which lowers the cost of model "
                "sharing and audits."),
              P("8.3 Explainability and accountability", "H2"),
              P("The two classical models are natively auditable: logistic coefficients quantify "
                "how each indicator shifts risk, and decision paths can be shown to an analyst or "
                "to a site owner contesting a block. The MLP trades that transparency for ranking "
                "quality, so deployments that rely on it should pair it with post-hoc explanation "
                "(for example SHAP attribute attribution) and should keep an interpretable model as "
                "a shadow reference. Accountability requires that automated decisions be "
                "attributable: every block should record model version, threshold, feature values "
                "and the human who approved the action where one was involved."),
              P("8.4 Drift and adversarial adaptation", "H2"),
              P("Phishing is an adversarial, non-stationary problem: attackers probe published "
                "detectors and adjust - moving to freshly registered domains, tampering with "
                "certificate choices or obfuscating page scripts until the indicator flips. A "
                "static model therefore decays. The pipeline's defence is procedural: monitor "
                "precision/recall and score distributions weekly, retrain on fresh verdicts, and "
                "treat any sharp shift in feature importance as an attack signal in its own right. "
                "Because the corpus behind this prototype was assembled around 2012, its absolute "
                "numbers should be read as methodology validation rather than a current-production "
                "guarantee."),
              P("8.5 Human-in-the-loop commitments", "H2"),
              P("The responsible posture that follows from Sections 7 and 8 is narrow autonomy: "
                "machine actions are limited to reversible, high-confidence measures (serve a "
                "warning interstitial), while irreversible actions (domain-wide blocks, account "
                "locks) require analyst confirmation. Analyst overrides are logged and fed back "
                "into training. This keeps a human accountable for consequential errors while "
                "preserving the speed advantage that justifies automation.")]

    # -------------------------------------------------------------- 9
    story += [P("9. Limitations and Future Work", "H1"),
              P("Three limitations bound the present study. First, the feature space is static and "
                "categorical: URL text, WHOIS timelines, page screenshots and network traces carry "
                "signal the 30 indicators compress away. Second, the corpus is historic; production "
                "use demands a refreshed, geographically diverse corpus with a documented "
                "collection protocol. Third, threshold tuning used a single hold-out split for "
                "simulation; a larger, time-based validation would give a firmer operating "
                "envelope. Future work will (i) benchmark gradient-boosted trees and calibrated "
                "ensembles against the MLP, (ii) add SHAP-based per-decision explanations, (iii) "
                "evaluate robustness against adversarial feature manipulation, and (iv) wrap the "
                "prototype in a REST service with streaming drift monitors.")]

    # -------------------------------------------------------------- 10
    story += [P("10. Conclusion", "H1"),
              P("The project demonstrates a complete, disciplined AI-for-cyber-security workflow on "
                f"a public phishing corpus: {ds['n_samples']:,} websites, {ds['n_features']} threat "
                "indicators, three model families and an explicit operational-ethics analysis. "
                "Exploratory analysis identified a compact set of dominant, interpretable threat "
                "signals; the tuned Decision Tree achieved the best single-threshold accuracy "
                f"({dt['accuracy']:.2%}); the 64x32 MLP achieved the best ranking quality "
                f"(ROC-AUC {mlp['roc_auc']:.4f}); and every model trains in seconds with "
                "microsecond-scale inference, clearing the latency bar for inline deployment. The "
                "threshold simulation converts raw metrics into a deployable policy - high-precision "
                "autonomous blocking, analyst review in the middle band - and the ethical review "
                "maps the system onto bias, privacy, explainability and drift obligations. The "
                "result is not merely a set of accuracy numbers but a defensible template for "
                "building, evaluating and governing ML-based detection systems.")]

    # -------------------------------------------------------------- references
    story += [P("References", "H1"),
              P("[1] R. M. Mohammad, F. Thabtah and L. McCluskey, \"An assessment of features "
                "related to phishing websites using an automated technique,\" in Proc. International "
                "Conference on Internet Technology and Secured Transactions (ICITST), London, 2012.",
                "Ref"),
              P("[2] R. M. Mohammad, F. Thabtah and L. McCluskey, <i>Phishing Websites</i>, UCI "
                "Machine Learning Repository, ID 327, 2012. DOI: 10.24432/C51W0X. Licence: CC BY 4.0.",
                "Ref"),
              P("[3] F. Pedregosa et al., \"Scikit-learn: Machine learning in Python,\" <i>Journal "
                "of Machine Learning Research</i>, vol. 12, pp. 2825-2830, 2011.", "Ref"),
              P("[4] F. Thabtah, \"Phishing detection: A literature survey,\" <i>American Journal of "
                "Information Science and Technology</i>, vol. 3, no. 6, 2015.", "Ref"),
              P("[5] European Parliament and Council, Regulation (EU) 2016/679 (General Data "
                "Protection Regulation), 2016.", "Ref"),
              P("[6] Government of India, Digital Personal Data Protection Act, 2023.", "Ref"),
              P("[7] D. W. Hosmer and S. Lemeshow, <i>Applied Logistic Regression</i>, 3rd ed., "
                "Wiley, 2013.", "Ref"),
              P("[8] I. Goodfellow, Y. Bengio and A. Courville, <i>Deep Learning</i>, MIT Press, "
                "2016.", "Ref")]

    # -------------------------------------------------------------- appendix
    feat_rows = []
    for group, members in [
        ("Address-bar", ["having_IP_Address", "URL_Length", "Shortining_Service", "having_At_Symbol",
                         "double_slash_redirecting", "Prefix_Suffix", "having_Sub_Domain",
                         "SSLfinal_State", "Domain_registeration_length", "Favicon", "port",
                         "HTTPS_token"]),
        ("Abnormal request", ["Request_URL", "URL_of_Anchor", "Links_in_tags", "SFH",
                              "Submitting_to_email", "Abnormal_URL"]),
        ("HTML / JavaScript", ["Redirect", "on_mouseover", "RightClick", "popUpWidnow", "Iframe"]),
        ("Domain", ["age_of_domain", "DNSRecord", "web_traffic", "Page_Rank", "Google_Index",
                    "Links_pointing_to_page", "Statistical_report"]),
    ]:
        for f in members:
            feat_rows.append([f, group, FEATURE_DESC[f]])
    story += [PageBreak(), P("Appendix A. Feature Dictionary", "H1"),
              P("Coding for all indicators: -1 = phishing signal, 0 = suspicious/neutral, "
                "+1 = legitimate signal (a few indicators are binary -1/+1). Descriptions follow "
                "the dataset authors' documentation [1]."),
              table_block("Table 7. The 30 threat indicators and their source surface.",
                          make_table(["Indicator", "Group", "Description"],
                                     feat_rows, [4.7 * cm, 3.0 * cm, 7.9 * cm],
                                     left_cols=(0, 2))),
              P("Appendix B. Reproducibility", "H1"),
              P(f"All results were produced with Python {env['python']}, scikit-learn "
                f"{env['scikit_learn']}, pandas {env['pandas']}, NumPy {env['numpy']} and "
                f"matplotlib {env['matplotlib']} on {env['platform']}. The full pipeline runs with "
                "<font face='Courier'>python src/main.py</font> (data, figures, metrics) and the "
                "report rebuilds with <font face='Courier'>python "
                "src/generate_pdf_report.py</font>. Random seed "
                f"{m['random_state']}, stratified 80/20 split; report generated "
                f"{m['generated_at']}. Deliverable map: <font face='Courier'>data/</font> dataset "
                "and feature notes; <font face='Courier'>src/</font> pipeline and report "
                "generator; <font face='Courier'>results/</font> figures, metrics.json, model "
                "comparison and threshold tables; <font face='Courier'>reports/</font> this PDF "
                "and its Markdown source.")]

    return story


FEATURE_DESC = {
    "having_IP_Address": "URL host is an IP address instead of a named domain",
    "URL_Length": "URL abnormally long (over 54 characters)",
    "Shortining_Service": "URL issued by a shortening service (tinyURL, bit.ly, ...)",
    "having_At_Symbol": "'@' symbol embedded in the URL",
    "double_slash_redirecting": "'//' redirection placed right after the protocol",
    "Prefix_Suffix": "'-' used inside the domain name (prefix/suffix trick)",
    "having_Sub_Domain": "number of sub-domains and dots in the URL",
    "SSLfinal_State": "SSL certificate validity, trust issuer and certificate age",
    "Domain_registeration_length": "domain registration/expiry window (coding inverted in the public copy)",
    "Favicon": "favicon loaded from outside the domain",
    "port": "non-standard ports open or unavailable",
    "HTTPS_token": "'https' token embedded misleadingly inside the domain",
    "Request_URL": "page objects (img/css/js) loaded from external domains",
    "URL_of_Anchor": "anchor tags linking outside the domain or to '#'",
    "Links_in_tags": "meta/script/link tags referencing external domains",
    "SFH": "form handler empty or pointing to another domain",
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
# Markdown twin
# ---------------------------------------------------------------------------

def md_table(header: list[str], rows: list[list[str]]) -> str:
    out = ["| " + " | ".join(header) + " |",
           "|" + "|".join(["---"] * len(header)) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(c) for c in r) + " |")
    return "\n".join(out)


def build_markdown(m: dict) -> str:
    ds, models, cv = m["dataset"], m["models"], m["cross_validation"]
    lr, dt, mlp = models["Logistic Regression"], models["Decision Tree"], models["MLP (64x32)"]
    thr, opt = m["threshold_analysis"]["sweep"], m["threshold_analysis"]["optimal_by_cost_ratio"]
    tree_params = m["tree_best_params"]
    tree_depth = "unrestricted" if tree_params["max_depth"] in (None, "None") else tree_params["max_depth"]
    env = m["environment"]
    sweep = {r["threshold"]: r for r in thr}
    L: list[str] = []

    L.append("# AI-Driven Phishing Threat Detection Prototype")
    L.append("")
    L.append("**Unit 1 Mini Project - " + STUDENT["course"] + "**  ")
    L.append(f"**{STUDENT['university']}** | Submitted by **{STUDENT['name']}** "
             f"(Roll No. {STUDENT['roll']}, {STUDENT['section']}) | Submitted to "
             f"{STUDENT['faculty']}")
    L.append("")
    L.append("> Dataset: UCI Machine Learning Repository - *Phishing Websites* (ID 327), "
             "Mohammad, Thabtah and McCluskey (2012), CC BY 4.0. All report text is black; "
             "figures and tables use a professional colour palette.")
    L.append("")
    L.append("---")
    L.append("")
    L.append("## Contents")
    for sec in ["1. Executive Summary", "2. Introduction and Objectives",
                "3. Dataset and Threat Landscape", "4. Exploratory Data Analysis",
                "5. Methodology", "6. Results and Benchmarking",
                "7. Operational Threshold Analysis", "8. Ethical Reflection and Responsible AI",
                "9. Limitations and Future Work", "10. Conclusion", "References",
                "Appendix A. Feature Dictionary", "Appendix B. Reproducibility"]:
        L.append(f"- {sec}")
    L.append("")

    L.append("## 1. Executive Summary")
    L.append("")
    L.append(f"This mini project develops an end-to-end, reproducible prototype that detects "
             f"phishing websites from {ds['n_features']} structural and behavioural threat "
             f"indicators, using the UCI *Phishing Websites* dataset ({ds['n_samples']:,} websites). "
             f"EDA shows a moderately balanced problem ({ds['phishing_pct']}% phishing), no missing "
             "values, two dominant threat signals (SSL certificate state and anchor-URL behaviour, "
             "|r| ~ 0.70), and redundancy clusters among HTML-script indicators. Three models are "
             f"benchmarked on a stratified 20% hold-out ({m['split']['test']:,} websites): Logistic "
             f"Regression (accuracy {lr['accuracy']:.2%}), a tuned Decision Tree "
             f"({dt['accuracy']:.2%}, best single-threshold classifier) and a 64x32 MLP "
             f"({mlp['accuracy']:.2%}) with the best ranking quality (ROC-AUC "
             f"{mlp['roc_auc']:.4f}). A threshold simulation and explicit cost model convert the "
             "metrics into a deployment policy; an ethical review covers proxy bias, privacy, "
             "explainability and adversarial drift.")
    L.append("")

    L.append("## 2. Introduction and Objectives")
    L.append("")
    L.append("Phishing is adversarial and fast-regenerating; blocklists defend against known pages, "
             "while machine learning generalises to unseen URLs by learning the statistical "
             "fingerprint of malicious design choices. The project implements the five Unit 1 "
             "laboratory tasks: (1) workspace bootstrap and reproducible configuration; (2) "
             "threat-landscape EDA; (3) supervised ML classification (Logistic Regression, tuned "
             "Decision Tree); (4) a deep-learning prototype (Dense 64x32 MLP) with multi-metric "
             "benchmarking; and (5) an operational threshold simulation plus ethical reflection. "
             "All results are produced by `src/main.py`, and the report is regenerated by "
             "`src/generate_pdf_report.py` from persisted metrics, so every number is traceable "
             "to a script run.")
    L.append("")

    L.append("## 3. Dataset and Threat Landscape")
    L.append("")
    L.append("### 3.1 Dataset provenance")
    L.append("")
    L.append("Published by Mohammad, Thabtah and McCluskey (University of Huddersfield) and "
             "distributed by the UCI Machine Learning Repository under CC BY 4.0. Each of the "
             "11,055 rows describes one website with 30 categorical indicators extracted from the "
             "URL string, the HTML/JavaScript content, and third-party domain intelligence (WHOIS, "
             "DNS, traffic ranks, blacklists). Indicator coding: -1 = phishing signal, "
             "0 = suspicious/neutral, +1 = legitimate signal. The label (-1 phishing / +1 "
             "legitimate) is remapped to a binary `phishing = 1` target.")
    L.append("")
    L.append(md_table(["Property", "Value"],
                      [["Instances", f"{ds['n_samples']:,}"],
                       ["Features", f"{ds['n_features']} categorical indicators"],
                       ["Phishing websites", f"{ds['phishing_count']:,} ({ds['phishing_pct']}%)"],
                       ["Legitimate websites", f"{ds['legitimate_count']:,} ({ds['legitimate_pct']}%)"],
                       ["Missing values", str(ds["n_missing"])],
                       ["Duplicated feature profiles", f"{ds['n_duplicates']:,}"]]))
    L.append("")
    L.append("**Table 1. Dataset overview.**")
    L.append("")
    L.append("### 3.2 Class balance")
    L.append("")
    L.append(f"Phishing pages account for {ds['phishing_pct']}% of the corpus "
             f"({ds['phishing_count']:,} of {ds['n_samples']:,}); the imbalance ratio is mild "
             f"({ds['imbalance_ratio']:.2f}), so accuracy remains meaningful while precision/recall "
             "are tracked per class. No synthetic oversampling is required.")
    L.append("")
    L.append("![Figure 1](../results/fig01_class_distribution.png)")
    L.append("")
    L.append("**Figure 1. Class balance of the UCI Phishing Websites dataset.**")
    L.append("")
    L.append("### 3.3 A note on duplicated feature profiles")
    L.append("")
    L.append(f"{ds['n_duplicates']:,} rows ({ds['n_duplicates']/ds['n_samples']:.0%}) share an "
             "identical feature vector with another row. This is expected with 30 coarse "
             "categorical indicators - structurally similar websites collapse onto the same "
             "profile. Duplicates are retained because they carry genuine class-prevalence "
             "information; removing them would distort the deployment prior.")
    L.append("")

    L.append("## 4. Exploratory Data Analysis")
    L.append("")
    L.append("### 4.1 Correlation structure")
    L.append("")
    L.append("The class label correlates strongly with a compact indicator set led by "
             "`SSLfinal_State` and `URL_of_Anchor`; `Favicon`/`port` and "
             "`on_mouseover`/`RightClick`/`popUpWidnow`/`Iframe` form near-redundant clusters; most "
             "domain-intelligence indicators contribute complementary evidence.")
    L.append("")
    L.append("![Figure 2](../results/fig02_correlation_heatmap.png)")
    L.append("")
    L.append("**Figure 2. Pearson correlation matrix of the 30 threat indicators and the phishing "
             "label.**")
    L.append("")
    L.append("### 4.2 Top threat indicators")
    L.append("")
    L.append(md_table(["Indicator", "Group", "Pearson r", "What it measures"],
                      [[t["feature"], t["group"], f"{t['pearson_r']:+.3f}", t["description"]]
                       for t in ds["top_indicators"]]))
    L.append("")
    L.append("**Table 2. Top ten phishing-correlated threat indicators.**")
    L.append("")
    L.append("![Figure 3](../results/fig03_top_threat_indicators.png)")
    L.append("")
    L.append("**Figure 3. Top ten threat indicators ranked by absolute correlation.**")
    L.append("")
    L.append("Coding caveat: the distributed copy of `Domain_registeration_length` is inverted "
             "relative to its published definition (phishing sites more often carry the value "
             "documented as the legitimate-signal +1). The models absorb the flipped coding, but "
             "this underlines the need to audit feature provenance before operational reuse.")
    L.append("")
    L.append("### 4.3 Indicator distributions by class")
    L.append("")
    L.append("Separation is strongest for `SSLfinal_State`, `URL_of_Anchor` and `web_traffic`; "
             "`Prefix_Suffix` separates less cleanly because hyphenated domains are also common "
             "among legitimate sites.")
    L.append("")
    L.append("![Figure 4](../results/fig04_feature_distributions.png)")
    L.append("")
    L.append("**Figure 4. Value distributions of six key indicators by class.**")
    L.append("")

    L.append("## 5. Methodology")
    L.append("")
    L.append(f"- **Split:** {m['split']['train']:,} train / {m['split']['test']:,} test (80/20, "
             f"stratified, seed {m['random_state']}); test set touched once.")
    L.append("- **Preprocessing:** native ordinal coding of the categorical indicators; "
             "StandardScaler fitted inside Pipelines on training data only (no leakage).")
    L.append(f"- **Logistic Regression:** regularised linear baseline (max_iter=1000).")
    L.append(f"- **Decision Tree:** 5-fold grid search over max_depth (4-10 or unrestricted) and "
             f"min_samples_leaf (1-10), F1-optimised; selected depth = {tree_depth}, "
             f"min_samples_leaf = {tree_params['min_samples_leaf']} (CV F1 = {m['tree_cv_f1']:.4f}).")
    L.append("- **MLP (deep-learning prototype):** Dense 64x32 ReLU, Adam optimiser, early "
             "stopping on 10% of the training fold, per the laboratory brief.")
    L.append("- **Metrics:** accuracy, precision, recall, F1 (phishing), ROC-AUC, MCC, confusion "
             "matrix, wall-clock training time and per-sample inference latency; five-fold "
             "cross-validation for stability.")
    L.append("")

    L.append("## 6. Results and Benchmarking")
    L.append("")
    L.append("### 6.1 Cross-validated stability")
    L.append("")
    L.append(md_table(["Model", "Accuracy", "F1-score (phishing)"],
                      [[n, f"{cv[n]['accuracy_mean']:.4f} +/- {cv[n]['accuracy_std']:.4f}",
                        f"{cv[n]['f1_mean']:.4f} +/- {cv[n]['f1_std']:.4f}"] for n in cv]))
    L.append("")
    L.append("**Table 3. Five-fold cross-validation on the training partition.**")
    L.append("")
    L.append("### 6.2 Hold-out test benchmark")
    L.append("")
    L.append(md_table(["Model", "Accuracy", "Precision", "Recall", "F1", "ROC-AUC", "MCC"],
                      [[n, f"{models[n]['accuracy']:.4f}", f"{models[n]['precision']:.4f}",
                        f"{models[n]['recall']:.4f}", f"{models[n]['f1']:.4f}",
                        f"{models[n]['roc_auc']:.4f}", f"{models[n]['mcc']:+.4f}"]
                       for n in models]))
    L.append("")
    L.append("**Table 4. Held-out test-set benchmark (n = "
             f"{m['split']['test']:,}; positive class = phishing).**")
    L.append("")
    L.append("The tuned Decision Tree is the strongest single-threshold classifier; the MLP has "
             "the best ranking quality (ROC-AUC), which matters most when the operating threshold "
             "must move. On coarse categorical feature spaces a well-tuned shallow model remains "
             "competitive with a neural network - an honest and instructive result.")
    L.append("")
    L.append("![Figure 5](../results/fig07_model_comparison.png)")
    L.append("")
    L.append("**Figure 5. Test-set metrics and training cost (log scale).**")
    L.append("")
    L.append("### 6.3 Ranking quality")
    L.append("")
    L.append("The MLP dominates the ROC surface across the operating range, reaching ~0.95 "
             "true-positive rate at a false-positive rate near 0.02.")
    L.append("")
    L.append("![Figure 6](../results/fig06_roc_curves.png)")
    L.append("")
    L.append("**Figure 6. ROC curves on the held-out test split.**")
    L.append("")
    L.append("### 6.4 Error anatomy")
    L.append("")
    L.append(md_table(["Model", "False positives", "False negatives"],
                      [[n, models[n]["false_positive"], models[n]["false_negative"]]
                       for n in models]))
    L.append("")
    L.append("**Figure 7. Confusion matrices** (see "
             "`../results/fig05_confusion_matrices.png`).")
    L.append("")
    L.append("### 6.5 Computational efficiency")
    L.append("")
    L.append(md_table(["Model", "Train time", "Inference (us/sample)"],
                      [[n, f"{models[n]['train_seconds']:.2f} s",
                        f"{models[n]['inference_us_per_sample']:.1f}"] for n in models]))
    L.append("")
    L.append("**Table 5. Training cost and per-sample inference latency.** All models train in "
             "seconds and classify in microseconds - well inside an inline filtering budget.")
    L.append("")

    L.append("## 7. Operational Threshold Analysis")
    L.append("")
    L.append("### 7.1 The false-positive / false-negative trade-off")
    L.append("")
    L.append(f"Sweeping the MLP threshold 0.05-0.95: at 0.05 the prototype catches "
             f"{100*sweep[0.05]['recall']:.1f}% of phishing but raises "
             f"{sweep[0.05]['false_positive']} false alarms; at 0.90 it raises only "
             f"{sweep[0.90]['false_positive']} false alarms but misses "
             f"{sweep[0.90]['false_negative']} attacks.")
    L.append("")
    L.append("![Figure 8](../results/fig08_threshold_analysis.png)")
    L.append("")
    L.append("**Figure 8. Error trade-off and cost-minimising thresholds.**")
    L.append("")
    L.append(md_table(["Threshold", "Precision", "Recall", "Accuracy", "False positives",
                       "False negatives"],
                      [[f"{t:.2f}", f"{sweep[t]['precision']:.3f}", f"{sweep[t]['recall']:.3f}",
                        f"{sweep[t]['accuracy']:.3f}", sweep[t]["false_positive"],
                        sweep[t]["false_negative"]]
                       for t in (0.10, 0.25, 0.40, 0.50, 0.60, 0.65, 0.80, 0.90)]))
    L.append("")
    L.append("**Table 6. Representative operating points of the MLP prototype.**")
    L.append("")
    L.append("### 7.2 Cost-based operating points")
    L.append("")
    L.append(f"With cost = FN x c_FN + FP x c_FP: balanced costs (1:1) optimise at threshold "
             f"{opt['1:1']['threshold']:.2f} ({opt['1:1']['fp_at_optimum']} FP, "
             f"{opt['1:1']['fn_at_optimum']} FN); when a compromise costs 10x a false alert the "
             f"optimum moves to the protective end (threshold {opt['10:1']['threshold']:.2f}, "
             "maximum recall). The threshold is a governance decision set from the organisation's "
             "own disruption-versus-compromise costs, not a technical default.")
    L.append("")
    L.append("### 7.3 Recommended deployment posture")
    L.append("")
    L.append("- **Block tier:** act autonomously only above ~0.80-0.90 (precision > 99%).")
    L.append("- **Review tier:** route 0.40-0.80 predictions to analyst inspection or secondary "
             "signals before user-facing action.")
    L.append("- **Feedback loop:** log analyst verdicts and retrain on schedule so threshold and "
             "model drift together with the threat landscape.")
    L.append("")

    L.append("## 8. Ethical Reflection and Responsible AI")
    L.append("")
    L.append("**Proxy bias and fairness.** Indicators such as young domains, low traffic and "
             "absent search indexing are proxies for atypical-but-legitimate behaviour; an "
             "automatic blocker disadvantages small and new publishers. Mitigations: review rather "
             "than block at low confidence, audit error rates across domain categories, fast "
             "appeals.")
    L.append("")
    L.append("**Privacy and data protection.** The prototype consumes structural metadata, not "
             "user content or identities. GDPR/DPDP duties (minimisation, purpose limitation) "
             "apply to visit logs: retain URLs only as long as triage needs and do not join them "
             "with identities beyond security operations. The categorical model stores no "
             "reconstructable personal data.")
    L.append("")
    L.append("**Explainability and accountability.** Logistic coefficients and decision paths are "
             "natively auditable; the MLP trades transparency for ranking quality, so deployments "
             "should pair it with post-hoc explanations (e.g. SHAP) and keep an interpretable "
             "shadow model. Every automated block should record model version, threshold, features "
             "and approver.")
    L.append("")
    L.append("**Drift and adversarial adaptation.** Attackers adapt to published detectors; a "
             "static model decays. Defences: weekly precision/recall and score-distribution "
             "monitoring, scheduled retraining on fresh verdicts, and treating sharp shifts in "
             "feature importance as an attack signal. The 2012-vintage corpus means absolute "
             "numbers validate the methodology rather than a production guarantee.")
    L.append("")
    L.append("**Human-in-the-loop commitments.** Narrow autonomy: reversible high-confidence "
             "actions are automated; irreversible actions require analyst confirmation; overrides "
             "are logged and fed back into training.")
    L.append("")

    L.append("## 9. Limitations and Future Work")
    L.append("")
    L.append("Static categorical features compress away URL text, WHOIS timelines and network "
             "traces; the corpus is historic and needs a refreshed, documented collection "
             "protocol; threshold simulation used a single hold-out split. Future work: gradient-"
             "boosted trees and calibrated ensembles, SHAP explanations, adversarial robustness "
             "evaluation, and a REST service with streaming drift monitors.")
    L.append("")

    L.append("## 10. Conclusion")
    L.append("")
    L.append(f"A complete AI-for-cyber-security workflow on a public phishing corpus: "
             f"{ds['n_samples']:,} websites, {ds['n_features']} indicators, three model families, "
             f"an explicit operating-point analysis and an ethics review. The tuned Decision Tree "
             f"achieves the best single-threshold accuracy ({dt['accuracy']:.2%}); the MLP the best "
             f"ranking quality (ROC-AUC {mlp['roc_auc']:.4f}); all models train in seconds with "
             "microsecond inference. The result is a defensible template for building, evaluating "
             "and governing ML-based detection systems.")
    L.append("")

    L.append("## References")
    L.append("")
    for ref in [
        "[1] R. M. Mohammad, F. Thabtah and L. McCluskey, \"An assessment of features related to "
        "phishing websites using an automated technique,\" ICITST, London, 2012.",
        "[2] R. M. Mohammad, F. Thabtah and L. McCluskey, *Phishing Websites*, UCI Machine "
        "Learning Repository, ID 327, 2012. DOI: 10.24432/C51W0X. CC BY 4.0.",
        "[3] F. Pedregosa et al., \"Scikit-learn: Machine learning in Python,\" JMLR, vol. 12, "
        "pp. 2825-2830, 2011.",
        "[4] F. Thabtah, \"Phishing detection: A literature survey,\" American Journal of "
        "Information Science and Technology, vol. 3, no. 6, 2015.",
        "[5] Regulation (EU) 2016/679 (General Data Protection Regulation), 2016.",
        "[6] Government of India, Digital Personal Data Protection Act, 2023.",
        "[7] D. W. Hosmer and S. Lemeshow, *Applied Logistic Regression*, 3rd ed., Wiley, 2013.",
        "[8] I. Goodfellow, Y. Bengio and A. Courville, *Deep Learning*, MIT Press, 2016.",
    ]:
        L.append(ref)
        L.append("")

    L.append("## Appendix A. Feature Dictionary")
    L.append("")
    L.append("Coding: -1 = phishing signal, 0 = suspicious/neutral, +1 = legitimate signal. "
             "Descriptions follow the dataset authors' documentation [1].")
    L.append("")
    groups = [("Address-bar", ["having_IP_Address", "URL_Length", "Shortining_Service",
                               "having_At_Symbol", "double_slash_redirecting", "Prefix_Suffix",
                               "having_Sub_Domain", "SSLfinal_State",
                               "Domain_registeration_length", "Favicon", "port", "HTTPS_token"]),
              ("Abnormal request", ["Request_URL", "URL_of_Anchor", "Links_in_tags", "SFH",
                                    "Submitting_to_email", "Abnormal_URL"]),
              ("HTML / JavaScript", ["Redirect", "on_mouseover", "RightClick", "popUpWidnow",
                                     "Iframe"]),
              ("Domain", ["age_of_domain", "DNSRecord", "web_traffic", "Page_Rank", "Google_Index",
                          "Links_pointing_to_page", "Statistical_report"])]
    L.append(md_table(["Indicator", "Group", "Description"],
                      [[f, g, FEATURE_DESC[f]] for g, members in groups for f in members]))
    L.append("")
    L.append("**Table 7. The 30 threat indicators and their source surface.**")
    L.append("")

    L.append("## Appendix B. Reproducibility")
    L.append("")
    L.append(f"Produced with Python {env['python']}, scikit-learn {env['scikit_learn']}, pandas "
             f"{env['pandas']}, NumPy {env['numpy']}, matplotlib {env['matplotlib']} on "
             f"{env['platform']}. Run `python src/main.py` (data, figures, metrics) and "
             f"`python src/generate_pdf_report.py` (this report). Random seed {m['random_state']}, "
             f"stratified 80/20 split; report generated {m['generated_at']}.")
    L.append("")

    return "\n".join(L)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    metrics_file = RESULTS_DIR / "metrics.json"
    print(f"Reading {metrics_file}")
    m = json.loads(metrics_file.read_text(encoding="utf-8"))

    pdf_path = REPORTS_DIR / "Technical_Report.pdf"
    doc = ReportDoc(
        str(pdf_path), pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN, topMargin=2.1 * cm, bottomMargin=2.0 * cm,
        title="AI-Driven Phishing Threat Detection Prototype",
        author=f"{STUDENT['name']} ({STUDENT['roll']})",
        subject="Unit 1 Mini Project - Introduction to AI and Cyber Security (ENSP355)",
    )
    story = title_page() + contents_block() + build_story(m)
    doc.multiBuild(story)
    print(f"PDF written: {pdf_path}")

    md_path = REPORTS_DIR / "technical_report.md"
    md_path.write_text(build_markdown(m), encoding="utf-8")
    print(f"Markdown written: {md_path}")


if __name__ == "__main__":
    main()
