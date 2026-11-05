"""credit-risk-lab: statistical rigor pack (wave 3).

Point estimates without intervals are half a result. This module adds:

1. Bootstrap 95 percent confidence intervals (1,000 resamples of the
   test set, fixed bootstrap seed) for the headline numbers:
   - champion AUC on Taiwan (results.json -> validation.auc_ci95)
   - champion-model AUC on German Credit (external_validation.json)
   - thin-file AUC and the creditworthy-reject share (study.json)
   - the second-look recovery rate (second_look.json)
   The approval statistics are bootstrapped honestly: each resample
   re-runs the whole procedure (cut-off selection, band definition,
   recovery counting) on the resampled accounts, so the interval prices
   the procedure's variance, not just the ratio's.

2. Multi-seed robustness: the champion (v1 features) and behavioural
   v2 (v1 plus transition features) trained under 5 seeds - each seed
   drives its own stratified split and its own model seed - reporting
   AUC mean and standard deviation per variant. This is the H3 test
   from HYPOTHESES.md.

Outputs: results/rigor.json, plus "bootstrap_ci95" / "auc_ci95" fields
merged into the results files above so the number is never quoted
without its interval downstream.
"""
import json
from pathlib import Path

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

import behavioural_v2
import credit_risk_lab as pipe
import external_validation as ext
import second_look as sl
import study as study_mod

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "rigor.json"
N_BOOT = 1000
BOOT_SEED = 20261104
MULTI_SEEDS = [42, 7, 123, 2024, 31337]


def _ci(values) -> dict:
    arr = np.asarray(values, dtype=float)
    return {
        "n_resamples": int(len(arr)),
        "mean": round(float(arr.mean()), 4),
        "lo95": round(float(np.percentile(arr, 2.5)), 4),
        "hi95": round(float(np.percentile(arr, 97.5)), 4),
        "width": round(float(np.percentile(arr, 97.5) -
                             np.percentile(arr, 2.5)), 4),
    }


def _gbm(seed):
    return HistGradientBoostingClassifier(
        max_iter=300, learning_rate=0.06, max_depth=3, random_state=seed)


def _taiwan_test(cfg):
    """Champion + thin-file predictions on the published test split."""
    seed = int(cfg["seed"])
    df = pipe.add_features(pipe.load())
    X, y = df[pipe.FEATURES + pipe.CATS], df["default"]
    Xtr, Xte, ytr, yte = train_test_split(
        X, y, test_size=float(cfg["test_size"]), stratify=y,
        random_state=seed)
    champ = pipe.make_pipe(_gbm(seed)).fit(Xtr, ytr)
    p = champ.predict_proba(Xte)[:, 1]
    from sklearn.compose import ColumnTransformer
    from sklearn.impute import SimpleImputer
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
    thin_pre = ColumnTransformer([
        ("num", Pipeline([("imp", SimpleImputer(strategy="median")),
                          ("sc", StandardScaler())]),
         study_mod.THIN_FEATURES)])
    thin = Pipeline([("pre", thin_pre), ("model", _gbm(seed))])
    thin.fit(df.loc[Xtr.index, study_mod.THIN_FEATURES], ytr)
    thin_p = thin.predict_proba(
        df.loc[Xte.index, study_mod.THIN_FEATURES])[:, 1]
    return yte.values, p, thin_p


def bootstrap_taiwan(cfg, stage1_rate: float) -> dict:
    y, p, thin_p = _taiwan_test(cfg)
    rng = np.random.default_rng(BOOT_SEED)
    n = len(y)
    aucs, thin_aucs, shares, recoveries = [], [], [], []
    for _ in range(N_BOOT):
        idx = rng.integers(0, n, n)
        yb, pb, tb = y[idx], p[idx], thin_p[idx]
        if yb.min() == yb.max():
            continue
        aucs.append(roc_auc_score(yb, pb))
        thin_aucs.append(roc_auc_score(yb, tb))
        thr, _, _ = study_mod.choose_cutoff(pb, yb, stage1_rate)
        rejected = pb > thr
        cw = int(((yb == 0) & rejected).sum())
        shares.append(cw / max(int(rejected.sum()), 1))
        band = float(np.median(tb[pb <= thr])) if (pb <= thr).any() else 1.0
        recovered_cw = int(((yb == 0) & rejected & (tb <= band)).sum())
        recoveries.append(recovered_cw / max(cw, 1))
    return {
        "champion_auc": _ci(aucs),
        "thin_file_auc": _ci(thin_aucs),
        "creditworthy_reject_share": _ci(shares),
        "second_look_recovery_rate": _ci(recoveries),
    }


def bootstrap_german(cfg) -> dict:
    _, y_test, preds, _ = ext.fit_test(cfg)
    rng = np.random.default_rng(BOOT_SEED)
    n = len(y_test)
    out = {}
    for name, p in preds.items():
        vals = []
        for _ in range(N_BOOT):
            idx = rng.integers(0, n, n)
            if y_test[idx].min() == y_test[idx].max():
                continue
            vals.append(roc_auc_score(y_test[idx], p[idx]))
        out[name] = _ci(vals)
    return out


def multi_seed(cfg) -> dict:
    df = behavioural_v2.add_transition_features(
        pipe.add_features(pipe.load()))
    X, y = df[pipe.FEATURES + pipe.CATS], df["default"]
    X2 = df[pipe.FEATURES + behavioural_v2.TRANSITION_FEATURES + pipe.CATS]
    rows = []
    for seed in MULTI_SEEDS:
        Xtr, Xte, ytr, yte = train_test_split(
            X, y, test_size=float(cfg["test_size"]), stratify=y,
            random_state=seed)
        v1 = pipe.make_pipe(_gbm(seed)).fit(Xtr, ytr)
        auc1 = float(roc_auc_score(yte, v1.predict_proba(Xte)[:, 1]))
        v2 = behavioural_v2._make_pipe_v2(_gbm(seed)).fit(
            X2.loc[Xtr.index], ytr)
        auc2 = float(roc_auc_score(
            yte, v2.predict_proba(X2.loc[Xte.index])[:, 1]))
        rows.append({"seed": seed, "v1_auc": round(auc1, 4),
                     "v2_auc": round(auc2, 4),
                     "delta": round(auc2 - auc1, 4)})
    a1 = np.array([r["v1_auc"] for r in rows])
    a2 = np.array([r["v2_auc"] for r in rows])
    return {
        "seeds": MULTI_SEEDS,
        "per_seed": rows,
        "v1": {"mean_auc": round(float(a1.mean()), 4),
               "std_auc": round(float(a1.std(ddof=1)), 4)},
        "v2": {"mean_auc": round(float(a2.mean()), 4),
               "std_auc": round(float(a2.std(ddof=1)), 4)},
        "mean_delta": round(float((a2 - a1).mean()), 4),
        "h3_verdict_rule": ("CONFIRMED if mean(v2) >= mean(v1); REFUTED "
                            "if mean(v2) < mean(v1) - 0.002; otherwise "
                            "INCONCLUSIVE (HYPOTHESES.md, H3)."),
    }


def _merge(path: Path, key: str, value) -> None:
    data = json.loads(path.read_text())
    data[key] = value
    path.write_text(json.dumps(data, indent=1))


def compute(cfg: dict = None) -> dict:
    cfg = cfg or pipe.load_config()
    results = json.loads((ROOT / "results" / "results.json").read_text())
    stage1_rate = float(next(s["observed_default_rate"]
                             for s in results["staging"]["by_stage"]
                             if int(s["stage"]) == 1))
    tw = bootstrap_taiwan(cfg, stage1_rate)
    de = bootstrap_german(cfg)
    ms = multi_seed(cfg)

    rigor = {
        "generated_from": (f"Bootstrap: {N_BOOT} resamples of each test "
                           f"set, seed {BOOT_SEED}; approval statistics "
                           "recompute their full procedure per resample. "
                           "Multi-seed: 5 seeds, each with its own split "
                           "and model seed."),
        "bootstrap_seed": BOOT_SEED,
        "n_resamples": N_BOOT,
        "taiwan": tw,
        "german": de,
        "multi_seed": ms,
    }

    res = json.loads((ROOT / "results" / "results.json").read_text())
    res["validation"]["auc_ci95"] = {
        "champion_gradient_boosting": tw["champion_auc"]}
    (ROOT / "results" / "results.json").write_text(json.dumps(res, indent=1))

    _merge(ROOT / "results" / "study.json", "bootstrap_ci95", {
        "creditworthy_reject_share": tw["creditworthy_reject_share"],
        "thin_file_auc": tw["thin_file_auc"]})
    _merge(ROOT / "results" / "second_look.json", "bootstrap_ci95", {
        "recovery_rate_of_creditworthy":
            tw["second_look_recovery_rate"]})
    ext_path = ROOT / "results" / "external_validation.json"
    ext_data = json.loads(ext_path.read_text())
    for name, ci in de.items():
        ext_data["models"][name]["auc_ci95"] = ci
    ext_path.write_text(json.dumps(ext_data, indent=1))
    return rigor


def main() -> dict:
    out = compute()
    OUT.write_text(json.dumps(out, indent=1))
    return out


if __name__ == "__main__":
    r = main()
    tw, de, ms = r["taiwan"], r["german"], r["multi_seed"]
    print(f"Taiwan champion AUC CI95: [{tw['champion_auc']['lo95']:.4f}, "
          f"{tw['champion_auc']['hi95']:.4f}] width "
          f"{tw['champion_auc']['width']:.4f}")
    print(f"German LR AUC CI95: [{de['logistic_regression']['lo95']:.4f}, "
          f"{de['logistic_regression']['hi95']:.4f}] width "
          f"{de['logistic_regression']['width']:.4f}; GB: "
          f"[{de['gradient_boosting']['lo95']:.4f}, "
          f"{de['gradient_boosting']['hi95']:.4f}]")
    print(f"creditworthy share CI95: "
          f"[{tw['creditworthy_reject_share']['lo95']:.3f}, "
          f"{tw['creditworthy_reject_share']['hi95']:.3f}]; thin-file AUC "
          f"CI95: [{tw['thin_file_auc']['lo95']:.4f}, "
          f"{tw['thin_file_auc']['hi95']:.4f}]; recovery CI95: "
          f"[{tw['second_look_recovery_rate']['lo95']:.3f}, "
          f"{tw['second_look_recovery_rate']['hi95']:.3f}]")
    print(f"multi-seed: v1 {ms['v1']['mean_auc']:.4f} ± "
          f"{ms['v1']['std_auc']:.4f} | v2 {ms['v2']['mean_auc']:.4f} ± "
          f"{ms['v2']['std_auc']:.4f} | mean delta {ms['mean_delta']:+.4f}")
