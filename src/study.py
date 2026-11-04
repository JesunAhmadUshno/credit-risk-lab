"""credit-risk-lab: the fair access study.

Three measured questions from RESEARCH.md, all on the held-out test set
with the published champion model (same split and seed):

(a) Creditworthy rejects. The approval cut-off is set by a stated risk
    appetite: approve at every PD up to the threshold where the observed
    default rate of the approved book matches the Stage 1 observed
    default rate in results/results.json (the lab's performing-book
    rate). Among the rejected, count how many did NOT default in the
    observed outcome: the creditworthy rejects a cut-off scorecard
    turns away at that risk appetite.

(b) Thin-file model. The champion retrained on behavioural features only
    (engineered behavioural features plus the PAY history), excluding the
    bureau-style fields (LIMIT_BAL, AGE, SEX, EDUCATION, MARRIAGE, and
    the BILL_AMT / PAY_AMT amounts). This is the newcomer question in
    miniature: how much discrimination survives with no file?

(c) Fairness audit. Approval rate at the same cut-off, and AUC, by SEX,
    AGE band, EDUCATION and MARRIAGE, with group sizes next to every
    rate. The dataset is Taiwan 2005, not Canada; group findings are a
    method demonstration, stated as such in STUDY.md.

Outputs: results/study.json and STUDY.md (generated, numbers from code).
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

import credit_risk_lab as pipe

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "study.json"
STUDY_MD = ROOT / "STUDY.md"

PAY_COLS = ["PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6"]
THIN_FEATURES = (["utilization", "pay_ratio", "delinq_mean", "delinq_max",
                  "bill_trend", "dpd_months"] + PAY_COLS)
EXCLUDED_AS_BUREAU_STYLE = ["LIMIT_BAL", "AGE", "SEX", "EDUCATION",
                            "MARRIAGE", "BILL_AMT1..BILL_AMT6",
                            "PAY_AMT1..PAY_AMT6"]

SEX_LABELS = {1: "Male", 2: "Female"}
EDUCATION_LABELS = {1: "Graduate school", 2: "University",
                    3: "High school", 4: "Other"}
MARRIAGE_LABELS = {1: "Married", 2: "Single", 3: "Other"}


def _gbm(seed):
    return HistGradientBoostingClassifier(
        max_iter=300, learning_rate=0.06, max_depth=3, random_state=seed)


def choose_cutoff(pd_scores, y, target_rate):
    """Largest-information threshold whose approved book matches target.

    Candidates are the observed PDs; approve PD <= t. The chosen t is the
    one whose approved-set observed default rate is closest to the target
    (ties break toward approving more accounts).
    """
    order = np.argsort(pd_scores)
    p_sorted = np.asarray(pd_scores)[order]
    y_sorted = np.asarray(y)[order]
    cum_defaults = np.cumsum(y_sorted)
    counts = np.arange(1, len(y_sorted) + 1)
    rates = cum_defaults / counts
    diffs = np.abs(rates - target_rate)
    # among the closest thresholds prefer the largest approved count
    tied = np.where(diffs == diffs.min())[0]
    best = int(tied.max())
    return float(p_sorted[best]), float(rates[best]), int(counts[best])


def _group_rows(frame, variable, pd_col="pd"):
    rows = []
    for label, g in frame.groupby(variable, observed=True):
        auc = None
        if g["default"].nunique() == 2 and (g["default"] == 1).sum() >= 5 \
                and (g["default"] == 0).sum() >= 5:
            auc = round(float(roc_auc_score(g["default"], g[pd_col])), 4)
        rows.append({
            "group": str(label),
            "n": int(len(g)),
            "approved": int(g["approved"].sum()),
            "approval_rate": round(float(g["approved"].mean()), 4),
            "default_rate": round(float(g["default"].mean()), 4),
            "auc": auc,
        })
    return rows


def compute(cfg: dict = None) -> dict:
    cfg = cfg or pipe.load_config()
    seed = int(cfg["seed"])
    results = json.loads((ROOT / "results" / "results.json").read_text())
    stage1_rate = float(next(s["observed_default_rate"]
                             for s in results["staging"]["by_stage"]
                             if int(s["stage"]) == 1))
    full_auc = float(results["models"]["gradient_boosting"]["auc"])

    df = pipe.add_features(pipe.load())
    X, y = df[pipe.FEATURES + pipe.CATS], df["default"]
    Xtr, Xte, ytr, yte = train_test_split(
        X, y, test_size=float(cfg["test_size"]), stratify=y, random_state=seed)
    champ = pipe.make_pipe(_gbm(seed)).fit(Xtr, ytr)
    p_test = champ.predict_proba(Xte)[:, 1]
    auc_check = round(float(roc_auc_score(yte, p_test)), 4)
    assert auc_check == full_auc, (auc_check, full_auc)

    test = Xte.copy()
    test["default"] = yte.values
    test["pd"] = p_test

    # (a) creditworthy rejects at the stated risk appetite
    threshold, achieved, n_approved = choose_cutoff(p_test, yte.values,
                                                    stage1_rate)
    test["approved"] = (test["pd"] <= threshold).astype(int)
    rejected = test[test["approved"] == 0]
    creditworthy = int((rejected["default"] == 0).sum())
    part_a = {
        "risk_appetite": {
            "rule": ("Approve every account with PD at or below the "
                     "threshold where the approved book's observed "
                     "default rate matches the Stage 1 observed default "
                     "rate (the lab's performing-book rate) from "
                     "results/results.json."),
            "target_approved_default_rate": stage1_rate,
        },
        "cutoff_pd": round(threshold, 6),
        "achieved_approved_default_rate": round(achieved, 4),
        "test_accounts": int(len(test)),
        "approved": int(n_approved),
        "rejected": int(len(test) - n_approved),
        "approval_rate": round(float(n_approved / len(test)), 4),
        "creditworthy_rejects": creditworthy,
        "creditworthy_share_of_rejected": round(
            float(creditworthy / max(len(rejected), 1)), 4),
        "creditworthy_share_of_test_set": round(
            float(creditworthy / len(test)), 4),
    }

    # (b) thin-file model: behavioural features only
    thin_pre = ColumnTransformer([
        ("num", Pipeline([("imp", SimpleImputer(strategy="median")),
                          ("sc", StandardScaler())]), THIN_FEATURES)])
    thin = Pipeline([("pre", thin_pre), ("model", _gbm(seed))])
    thin.fit(df.loc[Xtr.index, THIN_FEATURES], ytr)
    thin_auc = round(float(roc_auc_score(
        yte, thin.predict_proba(df.loc[Xte.index, THIN_FEATURES])[:, 1])), 4)
    part_b = {
        "features": THIN_FEATURES,
        "excluded_as_bureau_style": EXCLUDED_AS_BUREAU_STYLE,
        "auc": thin_auc,
        "full_model_auc": full_auc,
        "auc_gap_vs_full": round(thin_auc - full_auc, 4),
    }

    # (c) fairness audit at the same cut-off
    test["SEX"] = test["SEX"].map(SEX_LABELS)
    test["EDUCATION"] = test["EDUCATION"].map(EDUCATION_LABELS)
    test["MARRIAGE"] = test["MARRIAGE"].map(MARRIAGE_LABELS)
    test["AGE_BAND"] = pd.cut(test["AGE"], bins=[-np.inf, 29, 44, 59, np.inf],
                              labels=["Under 30", "30-44", "45-59", "60+"])
    by_variable, largest = {}, None
    for variable in ("SEX", "AGE_BAND", "EDUCATION", "MARRIAGE"):
        rows = _group_rows(test, variable)
        hi = max(rows, key=lambda r: r["approval_rate"])
        lo = min(rows, key=lambda r: r["approval_rate"])
        gap = round(hi["approval_rate"] - lo["approval_rate"], 4)
        by_variable[variable] = {"groups": rows, "approval_rate_gap": gap}
        if largest is None or gap > largest["gap"]:
            largest = {"variable": variable, "gap": gap,
                       "higher_group": hi, "lower_group": lo}
    part_c = {"by_variable": by_variable, "largest_gap": largest}

    return {
        "generated_from": ("Champion model, same split and seed as the "
                           "published run; all counts observed on the "
                           "held-out test set."),
        "creditworthy_rejects": part_a,
        "thin_file": part_b,
        "fairness": part_c,
    }


def _fmt_pct(x, digits=1):
    return f"{x * 100:.{digits}f}%"


def write_study_md(r: dict) -> str:
    a, b, c = r["creditworthy_rejects"], r["thin_file"], r["fairness"]
    lg = c["largest_gap"]
    lines = [
        "# credit-risk-lab: the fair access study",
        "",
        "Three questions from [RESEARCH.md](RESEARCH.md), answered with "
        "measured work on the held-out test set "
        f"({a['test_accounts']:,} accounts) using the published champion "
        "model. Every number below is generated by `src/study.py` from the "
        "run; nothing is typed in.",
        "",
        "## 1. Creditworthy rejects",
        "",
        "Risk appetite, stated as a rule: " + a["risk_appetite"]["rule"],
        "",
        f"- Target approved-book default rate (Stage 1 observed): "
        f"{_fmt_pct(a['risk_appetite']['target_approved_default_rate'], 2)}",
        f"- Cut-off PD chosen on the test set: {a['cutoff_pd']:.4f} "
        f"(achieved approved-book default rate "
        f"{_fmt_pct(a['achieved_approved_default_rate'], 2)})",
        f"- Approved: {a['approved']:,} "
        f"({_fmt_pct(a['approval_rate'])}); rejected: {a['rejected']:,}",
        f"- **Creditworthy rejects: {a['creditworthy_rejects']:,} of the "
        f"{a['rejected']:,} rejected applicants did not default** "
        f"({_fmt_pct(a['creditworthy_share_of_rejected'])} of all rejects; "
        f"{_fmt_pct(a['creditworthy_share_of_test_set'])} of the test set).",
        "",
        "These are observed outcomes, not estimates: at this risk appetite "
        "the cut-off turns away that many people who, in the event, repaid.",
        "",
        "## 2. Thin-file model (behavioural features only)",
        "",
        "The champion retrained without the bureau-style fields "
        "(excluded: " + ", ".join(b["excluded_as_bureau_style"]) + "). "
        "Features kept: " + ", ".join(b["features"]) + ".",
        "",
        f"- Thin-file AUC: **{b['auc']:.4f}**, against the full model's "
        f"{b['full_model_auc']:.4f} (gap {b['auc_gap_vs_full']:+.4f}).",
        "",
        "Behavioural history alone carries most of the signal. That is the "
        "newcomer question in miniature: a thin file is not an empty file "
        "when payment behaviour can be observed.",
        "",
        "## 3. Fairness audit (approval rate and AUC by group)",
        "",
        "Approval is at the same cut-off as section 1. Group sizes are "
        "printed next to every rate; small groups swing on small counts.",
        "",
    ]
    for variable, block in c["by_variable"].items():
        lines += [f"### {variable}", "",
                  "| Group | n | Approval rate | Default rate | AUC |",
                  "| --- | --- | --- | --- | --- |"]
        for g in block["groups"]:
            auc = f"{g['auc']:.4f}" if g["auc"] is not None else "n/a"
            lines.append(f"| {g['group']} | {g['n']:,} | "
                         f"{_fmt_pct(g['approval_rate'])} | "
                         f"{_fmt_pct(g['default_rate'])} | {auc} |")
        lines += ["", f"Approval-rate gap within {variable}: "
                  f"{_fmt_pct(block['approval_rate_gap'])}.", ""]
    lines += [
        f"**Largest gap: {lg['variable']}, "
        f"{_fmt_pct(lg['gap'])}** between "
        f"{lg['higher_group']['group']} "
        f"({_fmt_pct(lg['higher_group']['approval_rate'])} approved, "
        f"n={lg['higher_group']['n']:,}) and "
        f"{lg['lower_group']['group']} "
        f"({_fmt_pct(lg['lower_group']['approval_rate'])} approved, "
        f"n={lg['lower_group']['n']:,}).",
        "",
        "## Limits, on the same page",
        "",
        "- The dataset is Taiwan, 2005 (UCI dataset 350), not Canada. "
        "Group patterns here demonstrate the audit method; they are not "
        "evidence about Canadian borrowers or any Canadian lender.",
        "- Outcomes are a single month (default next month), not lifetime "
        "repayment. A 'creditworthy reject' repaid in that window; longer "
        "horizons would change some counts.",
        "- The cut-off is set on the same test set it is audited on. A "
        "production study would fix the appetite on a validation sample "
        "first; the lab states the rule and applies it once, openly.",
        "- AUC is reported per group only where both outcome classes have "
        "at least 5 accounts; smaller cells show n/a rather than a noisy "
        "number.",
        "",
    ]
    text = "\n".join(lines)
    STUDY_MD.write_text(text)
    return text


def main() -> dict:
    out = compute()
    OUT.write_text(json.dumps(out, indent=1))
    write_study_md(out)
    return out


if __name__ == "__main__":
    r = main()
    a, b, c = r["creditworthy_rejects"], r["thin_file"], r["fairness"]
    print(f"cut-off PD {a['cutoff_pd']:.4f} | approved {a['approved']} / "
          f"{a['test_accounts']} | creditworthy rejects "
          f"{a['creditworthy_rejects']} "
          f"({_fmt_pct(a['creditworthy_share_of_rejected'])})")
    print(f"thin-file AUC {b['auc']:.4f} vs full {b['full_model_auc']:.4f}")
    lg = c["largest_gap"]
    print(f"largest fairness gap: {lg['variable']} {lg['gap']:.4f} "
          f"({lg['higher_group']['group']} vs {lg['lower_group']['group']})")
