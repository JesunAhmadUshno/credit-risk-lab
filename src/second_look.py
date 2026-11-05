"""credit-risk-lab: the Second-Look Recovery Policy (wave 3, H1).

Pre-registered as H1 in HYPOTHESES.md before this code ran.

The policy, formalized. A two-stage decision rule for cut-off lending:

    Stage 1 (the scorecard's answer): approve iff the champion model's
    PD is at or below the study cut-off (the threshold whose approved
    book matches the Stage 1 observed default rate; src/study.py).

    Stage 2 (the second look): an applicant rejected at stage 1 is
    re-scored by the independent thin-file behavioural model. If their
    behavioural PD is at or below the band threshold - defined as the
    median thin-file PD of the stage-1 approved applicants, i.e. their
    behavioural evidence is at least as strong as the typical approved
    applicant's - the application is approved on second look.

Everything else stays rejected. The band is defined from the score
distributions on the same test set, stated here and in STUDY.md, and is
not tuned per applicant.

Measured on the held-out test set: stage-1 rejects recovered (split
into creditworthy, who did not default, and additional defaults
admitted), the recovery rate against the study's creditworthy-reject
count, the approved book's default rate before and after, and the
fairness read: recovery rates by the study's audit groups.

How this differs from classic reject inference is written up in
RESEARCH.md: reject inference reweights or re-labels the rejected
region so a single model can be retrained on it; the second-look policy
instead brings a second, independent score to the rejected region and
pays for its recoveries with measured admitted defaults.

Outputs: results/second_look.json, and a findings section appended to
STUDY.md between SECOND-LOOK markers (idempotent: rerunning replaces
the section, and src/study.py regenerating STUDY.md removes it until
this module runs again; src/run_all.py runs study before second look).
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

import credit_risk_lab as pipe
import study as study_mod

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "second_look.json"
STUDY_MD = ROOT / "STUDY.md"
MARK_START = "<!-- SECOND-LOOK:START -->"
MARK_END = "<!-- SECOND-LOOK:END -->"


def _gbm(seed):
    return HistGradientBoostingClassifier(
        max_iter=300, learning_rate=0.06, max_depth=3, random_state=seed)


def compute(cfg: dict = None) -> dict:
    cfg = cfg or pipe.load_config()
    seed = int(cfg["seed"])
    results = json.loads((ROOT / "results" / "results.json").read_text())
    stage1_rate = float(next(s["observed_default_rate"]
                             for s in results["staging"]["by_stage"]
                             if int(s["stage"]) == 1))

    df = pipe.add_features(pipe.load())
    X, y = df[pipe.FEATURES + pipe.CATS], df["default"]
    Xtr, Xte, ytr, yte = train_test_split(
        X, y, test_size=float(cfg["test_size"]), stratify=y,
        random_state=seed)
    champ = pipe.make_pipe(_gbm(seed)).fit(Xtr, ytr)
    p_test = champ.predict_proba(Xte)[:, 1]

    thin_pre = ColumnTransformer([
        ("num", Pipeline([("imp", SimpleImputer(strategy="median")),
                          ("sc", StandardScaler())]),
         study_mod.THIN_FEATURES)])
    thin = Pipeline([("pre", thin_pre), ("model", _gbm(seed))])
    thin.fit(df.loc[Xtr.index, study_mod.THIN_FEATURES], ytr)
    thin_test = thin.predict_proba(
        df.loc[Xte.index, study_mod.THIN_FEATURES])[:, 1]

    threshold, achieved, n_approved = study_mod.choose_cutoff(
        p_test, yte.values, stage1_rate)

    test = Xte.copy()
    test["default"] = yte.values
    test["pd"] = p_test
    test["thin_pd"] = thin_test
    test["approved_stage1"] = (test["pd"] <= threshold).astype(int)

    approved1 = test[test["approved_stage1"] == 1]
    rejected1 = test[test["approved_stage1"] == 0].copy()
    band = float(approved1["thin_pd"].median())
    rejected1["second_look"] = (rejected1["thin_pd"] <= band).astype(int)
    recovered_frame = rejected1[rejected1["second_look"] == 1]

    creditworthy_total = int((rejected1["default"] == 0).sum())
    recovered_creditworthy = int((recovered_frame["default"] == 0).sum())
    admitted_defaults = int((recovered_frame["default"] == 1).sum())
    recovered_total = int(len(recovered_frame))

    book1_rate = float(approved1["default"].mean())
    book2 = pd.concat([approved1, recovered_frame])
    book2_rate = float(book2["default"].mean())

    # Fairness read: per audit group, how many of the group's rejected
    # applicants the second look recovers, and how many of its
    # creditworthy rejects.
    test["approved_stage1"] = test["approved_stage1"].astype(int)
    rejected1["SEX"] = rejected1["SEX"].map(study_mod.SEX_LABELS)
    rejected1["EDUCATION"] = rejected1["EDUCATION"].map(
        study_mod.EDUCATION_LABELS)
    rejected1["MARRIAGE"] = rejected1["MARRIAGE"].map(
        study_mod.MARRIAGE_LABELS)
    rejected1["AGE_BAND"] = pd.cut(
        rejected1["AGE"], bins=[-np.inf, 29, 44, 59, np.inf],
        labels=["Under 30", "30-44", "45-59", "60+"])
    fairness = {}
    for variable in ("SEX", "AGE_BAND", "EDUCATION", "MARRIAGE"):
        rows = []
        for label, g in rejected1.groupby(variable, observed=True):
            cw = int((g["default"] == 0).sum())
            rec = int(((g["second_look"] == 1) & (g["default"] == 0)).sum())
            rows.append({
                "group": str(label),
                "rejected": int(len(g)),
                "creditworthy_rejects": cw,
                "recovered": int((g["second_look"] == 1).sum()),
                "recovered_creditworthy": rec,
                "recovery_rate_of_rejects": round(
                    float((g["second_look"] == 1).mean()), 4),
                "recovery_rate_of_creditworthy": round(
                    rec / cw, 4) if cw else None,
            })
        fairness[variable] = rows

    return {
        "generated_from": ("Champion and thin-file models, same split "
                           "and seed as the published run and the fair "
                           "access study; all counts observed on the "
                           "held-out test set."),
        "policy": {
            "name": "Second-Look Recovery Policy",
            "stage1": ("Approve iff champion PD <= the study cut-off "
                       "(approved book matches the Stage 1 observed "
                       "default rate)."),
            "stage2": ("A stage-1 reject is approved on second look iff "
                       "their thin-file behavioural PD is at or below "
                       "the band threshold."),
            "band_rule": ("Band threshold = median thin-file PD of the "
                          "stage-1 approved applicants, computed on the "
                          "test set."),
            "band_threshold_thin_pd": round(band, 6),
            "cutoff_pd": round(float(threshold), 6),
        },
        "headline": {
            "test_accounts": int(len(test)),
            "stage1_approved": int(n_approved),
            "stage1_rejected": int(len(rejected1)),
            "creditworthy_rejects_stage1": creditworthy_total,
            "recovered_total": recovered_total,
            "recovered_creditworthy": recovered_creditworthy,
            "admitted_defaults": admitted_defaults,
            "recovery_rate_of_creditworthy": round(
                recovered_creditworthy / max(creditworthy_total, 1), 4),
            "approved_book_default_rate_stage1": round(book1_rate, 4),
            "approved_book_default_rate_after": round(book2_rate, 4),
            "cost_default_rate_pp": round((book2_rate - book1_rate) * 100, 3),
            "approved_after": int(len(book2)),
        },
        "fairness": fairness,
    }


def _fmt_pct(x, digits=1):
    return f"{x * 100:.{digits}f}%"


def findings_md(r: dict) -> str:
    h = r["headline"]
    lines = [
        MARK_START,
        "",
        "## 4. Findings: the Second-Look Recovery Policy",
        "",
        "Pre-registered as H1 in `HYPOTHESES.md`. A two-stage rule on "
        "top of the study's stage-1 cut-off:",
        "",
        "1. **Stage 1:** approve iff the champion PD is at or below "
        f"{r['policy']['cutoff_pd']:.4f} (the cut-off from section 1).",
        "2. **Stage 2 (the second look):** a stage-1 reject is approved "
        "iff their thin-file behavioural PD is at or below the band "
        "threshold, defined as the median thin-file PD of stage-1 "
        f"approved applicants: {r['policy']['band_threshold_thin_pd']:.4f}. "
        "Their behavioural evidence must be at least as strong as the "
        "typical approved applicant's.",
        "",
        "| Measure | Value |",
        "| --- | --- |",
        f"| Stage-1 rejected | {h['stage1_rejected']:,} |",
        f"| Creditworthy rejects at stage 1 | "
        f"{h['creditworthy_rejects_stage1']:,} |",
        f"| Recovered on second look (total) | {h['recovered_total']:,} |",
        f"| Recovered creditworthy (did not default) | "
        f"{h['recovered_creditworthy']:,} |",
        f"| Additional defaults admitted | {h['admitted_defaults']:,} |",
        f"| **Recovery rate of creditworthy rejects** | "
        f"**{_fmt_pct(h['recovery_rate_of_creditworthy'])}** |",
        f"| Approved book default rate, stage 1 only | "
        f"{_fmt_pct(h['approved_book_default_rate_stage1'], 2)} |",
        f"| Approved book default rate, after second look | "
        f"{_fmt_pct(h['approved_book_default_rate_after'], 2)} |",
        f"| **Cost (default-rate increase)** | "
        f"**{h['cost_default_rate_pp']:+.2f} percentage points** |",
        "",
        "The trade is explicit: every recovered creditworthy applicant "
        "is bought with a measured number of admitted defaults, and the "
        "price shows up in the approved book's default rate rather than "
        "hiding in an assumption. A lender adopting this shape of policy "
        "sets its own band; the lab's band is a stated rule, not a "
        "tuned optimum.",
        "",
        "Fairness read (share of each group's creditworthy rejects "
        "recovered):",
        "",
    ]
    for variable, rows in r["fairness"].items():
        parts = []
        for g in rows:
            rate = g["recovery_rate_of_creditworthy"]
            parts.append(f"{g['group']} "
                         f"{_fmt_pct(rate) if rate is not None else 'n/a'} "
                         f"(of {g['creditworthy_rejects']:,})")
        lines.append(f"- {variable}: " + "; ".join(parts) + ".")
    lines += [
        "",
        "Position against reject inference, the classic alternative, is "
        "in `RESEARCH.md`. Full per-group counts are in "
        "`results/second_look.json`; the bootstrap confidence interval "
        "for the recovery rate is in `results/rigor.json`.",
        "",
        MARK_END,
    ]
    return "\n".join(lines)


def write_study_section(r: dict) -> None:
    section = findings_md(r)
    text = STUDY_MD.read_text() if STUDY_MD.exists() else ""
    if MARK_START in text and MARK_END in text:
        before = text.split(MARK_START)[0].rstrip()
        after = text.split(MARK_END, 1)[1].lstrip("\n")
        text = before + "\n\n" + section + ("\n" + after if after else "\n")
    else:
        text = text.rstrip() + "\n\n" + section + "\n"
    STUDY_MD.write_text(text)


def main() -> dict:
    out = compute()
    OUT.write_text(json.dumps(out, indent=1))
    write_study_section(out)
    return out


if __name__ == "__main__":
    r = main()
    h = r["headline"]
    print(f"band (median approved thin PD): "
          f"{r['policy']['band_threshold_thin_pd']:.4f}")
    print(f"recovered {h['recovered_total']} of "
          f"{h['stage1_rejected']} rejects: "
          f"{h['recovered_creditworthy']} creditworthy, "
          f"{h['admitted_defaults']} defaults admitted")
    print(f"recovery rate of creditworthy rejects: "
          f"{h['recovery_rate_of_creditworthy']:.1%} | cost "
          f"{h['cost_default_rate_pp']:+.2f} pp (book default rate "
          f"{h['approved_book_default_rate_stage1']:.2%} -> "
          f"{h['approved_book_default_rate_after']:.2%})")
