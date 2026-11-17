"""credit-risk-lab: post-registration amendments A1 and A2.

Registered in AMENDMENTS.md on 2026-11-16 BEFORE this code ran.
Exploratory, post-hoc analyses for version 2 of the fair-access
preprint. They change no registered hypothesis or verdict.

A1: second-look recovery-cost curve. The stage-2 band is swept over
multiples k of the registered band (the median thin-file PD of
stage-1 approved applicants); recovery and cost are reported per k.
The k = 1.0 row must reproduce the published H1 headline exactly or
the run is void.

A2: paired bootstrap interval for the thin-file AUC gap. 2,000
resamples of the test accounts (seed 20261116); both AUCs recomputed
per resample; the gap distribution is reported. No verdict issued.

Outputs: results/amendments.json.
"""
import json
from pathlib import Path

import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score

import credit_risk_lab as pipe
import study as study_mod
from second_look import _gbm

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "amendments.json"

BAND_MULTIPLIERS = [1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0]
BOOT_SEED = 20261116
BOOT_N = 2000


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

    yv = yte.values
    threshold, achieved, n_approved = study_mod.choose_cutoff(
        p_test, yv, stage1_rate)
    approved = p_test <= threshold
    rejected = ~approved
    band0 = float(np.median(thin_test[approved]))
    book1_rate = float(yv[approved].mean())
    creditworthy_total = int(((yv == 0) & rejected).sum())

    # ---- A1: band sweep ----
    sweep = []
    for k in BAND_MULTIPLIERS:
        band = band0 * k
        rec = rejected & (thin_test <= band)
        rec_cw = int(((yv == 0) & rec).sum())
        rec_def = int(((yv == 1) & rec).sum())
        book2 = np.concatenate([yv[approved], yv[rec]])
        book2_rate = float(book2.mean())
        sweep.append({
            "multiplier": k,
            "band_threshold_thin_pd": round(band, 6),
            "recovered_total": int(rec.sum()),
            "recovered_creditworthy": rec_cw,
            "admitted_defaults": rec_def,
            "recovery_rate_of_creditworthy": round(
                rec_cw / max(creditworthy_total, 1), 4),
            "approved_book_default_rate_after": round(book2_rate, 4),
            "cost_default_rate_pp": round((book2_rate - book1_rate) * 100, 3),
        })
    first15 = next(
        (row for row in sweep
         if row["recovery_rate_of_creditworthy"] >= 0.15), None)

    # ---- A2: paired bootstrap of the AUC gap ----
    auc_full = float(roc_auc_score(yv, p_test))
    auc_thin = float(roc_auc_score(yv, thin_test))
    rng = np.random.default_rng(BOOT_SEED)
    n = len(yv)
    gaps = []
    for _ in range(BOOT_N):
        idx = rng.integers(0, n, n)
        if len(np.unique(yv[idx])) < 2:
            continue
        gaps.append(float(roc_auc_score(yv[idx], thin_test[idx])
                          - roc_auc_score(yv[idx], p_test[idx])))
    gaps = np.array(gaps)

    return {
        "registered_in": "AMENDMENTS.md (2026-11-16, before this run)",
        "status": "exploratory post-hoc amendments; no registered verdict changes",
        "stage1": {
            "cutoff_pd": round(float(threshold), 6),
            "approved": int(approved.sum()),
            "rejected": int(rejected.sum()),
            "creditworthy_rejects": creditworthy_total,
            "approved_book_default_rate": round(book1_rate, 4),
            "registered_band_thin_pd": round(band0, 6),
        },
        "A1_band_sweep": {
            "rows": sweep,
            "first_band_reaching_15pct_recovery": first15,
            "validation_k1_must_match_published": {
                "recovered_total": 21,
                "recovered_creditworthy": 17,
                "recovery_rate_of_creditworthy": 0.0122,
                "cost_default_rate_pp": 0.023,
            },
        },
        "A2_auc_gap_bootstrap": {
            "auc_full": round(auc_full, 4),
            "auc_thin": round(auc_thin, 4),
            "point_gap_thin_minus_full": round(auc_thin - auc_full, 4),
            "n_resamples": int(len(gaps)),
            "seed": BOOT_SEED,
            "bootstrap_mean_gap": round(float(gaps.mean()), 4),
            "ci95_percentile": [round(float(np.percentile(gaps, 2.5)), 4),
                                round(float(np.percentile(gaps, 97.5)), 4)],
        },
    }


def main() -> int:
    r = compute()
    OUT.write_text(json.dumps(r, indent=1))
    print(json.dumps(r, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
