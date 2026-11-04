"""credit-risk-lab: behavioural PD v2, transition-feature challenger.

v1 (the published champion) uses level features: current delinquency,
means and maxima over the six-month payment history. v2 adds the *path* of
delinquency through time, computed from PAY_0..PAY_6 in chronological
order (PAY_6 oldest, PAY_0 most recent):

    dpd_worsen_steps   count of adjacent months where DPD increased
    dpd_max_consec     longest run of consecutive months delinquent (DPD >= 1)
    dpd_slope          linear slope of clipped DPD over the six months
    dpd_recent3_mean   mean clipped DPD over the three most recent months

DPD is the payment-status code clipped at 0 (codes -2/-1 mean no
delinquency). The challenger is the same gradient boosting model, same
train/test split and seed as v1; only the feature set grows. Results land
in results/behavioural_v2.json, with v1 recomputed on the same split and
cross-checked against results/results.json. The comparison is reported
either way: if v2 does not beat v1, the JSON and the README say so.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

import credit_risk_lab as pipe

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "behavioural_v2.json"

# Chronological order, oldest first. The dataset has no PAY_1 column.
PAY_CHRONO = ["PAY_6", "PAY_5", "PAY_4", "PAY_3", "PAY_2", "PAY_0"]
RECENT3 = ["PAY_3", "PAY_2", "PAY_0"]
TRANSITION_FEATURES = ["dpd_worsen_steps", "dpd_max_consec",
                       "dpd_slope", "dpd_recent3_mean"]


def add_transition_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add the four DPD transition features. Requires only the PAY columns."""
    df = df.copy()
    dpd = df[PAY_CHRONO].clip(lower=0).to_numpy(dtype=float)
    steps = np.diff(dpd, axis=1)
    df["dpd_worsen_steps"] = (steps > 0).sum(axis=1)

    delinquent = dpd >= 1
    max_run = np.zeros(len(df), dtype=int)
    run = np.zeros(len(df), dtype=int)
    for t in range(delinquent.shape[1]):
        run = np.where(delinquent[:, t], run + 1, 0)
        max_run = np.maximum(max_run, run)
    df["dpd_max_consec"] = max_run

    x = np.arange(dpd.shape[1], dtype=float)
    x_centered = x - x.mean()
    denom = float((x_centered ** 2).sum())
    df["dpd_slope"] = (dpd - dpd.mean(axis=1, keepdims=True)) @ x_centered / denom
    df["dpd_recent3_mean"] = df[RECENT3].clip(lower=0).mean(axis=1)
    return df


def _make_pipe_v2(model) -> Pipeline:
    pre = ColumnTransformer([
        ("num", Pipeline([("imp", SimpleImputer(strategy="median")),
                          ("sc", StandardScaler())]),
         pipe.FEATURES + TRANSITION_FEATURES),
        ("cat", OneHotEncoder(handle_unknown="ignore"), pipe.CATS),
    ])
    return Pipeline([("pre", pre), ("model", model)])


def _metrics(y, p) -> dict:
    return {
        "auc": round(float(roc_auc_score(y, p)), 4),
        "ks": round(pipe.ks_stat(np.asarray(y), p), 4),
        "brier": round(float(brier_score_loss(y, p)), 4),
    }


def compute(cfg: dict = None) -> dict:
    cfg = cfg or pipe.load_config()
    seed = int(cfg["seed"])
    df = add_transition_features(pipe.add_features(pipe.load()))
    X, y = df[pipe.FEATURES + pipe.CATS], df["default"]
    X2 = df[pipe.FEATURES + TRANSITION_FEATURES + pipe.CATS]
    Xtr, Xte, ytr, yte = train_test_split(
        X, y, test_size=float(cfg["test_size"]), stratify=y, random_state=seed)
    X2tr = X2.loc[Xtr.index]
    X2te = X2.loc[Xte.index]

    def gbm():
        return HistGradientBoostingClassifier(
            max_iter=300, learning_rate=0.06, max_depth=3, random_state=seed)

    v1 = pipe.make_pipe(gbm()).fit(Xtr, ytr)
    m1 = _metrics(yte.values, v1.predict_proba(Xte)[:, 1])
    v2 = _make_pipe_v2(gbm()).fit(X2tr, ytr)
    m2 = _metrics(yte.values, v2.predict_proba(X2te)[:, 1])

    published = json.loads((ROOT / "results" / "results.json").read_text())
    pub = published["models"]["gradient_boosting"]
    assert m1["auc"] == pub["auc"] and m1["ks"] == pub["ks"], (m1, pub)

    return {
        "generated_from": ("Same split, seed, model and hyperparameters as "
                           "the published v1 champion; v2 adds only the "
                           "four transition features."),
        "transition_features": TRANSITION_FEATURES,
        "pay_chronological_order": PAY_CHRONO,
        "v1_gradient_boosting": m1,
        "v2_gradient_boosting_plus_transitions": m2,
        "delta_auc": round(m2["auc"] - m1["auc"], 4),
        "v2_beats_v1": bool(m2["auc"] > m1["auc"]),
        "verdict": ("v2 beats v1 on held-out AUC" if m2["auc"] > m1["auc"]
                    else "v2 does not beat v1 on held-out AUC"),
    }


def main() -> dict:
    out = compute()
    OUT.write_text(json.dumps(out, indent=1))
    return out


if __name__ == "__main__":
    r = main()
    print("v1:", r["v1_gradient_boosting"])
    print("v2:", r["v2_gradient_boosting_plus_transitions"])
    print("delta AUC:", r["delta_auc"], "|", r["verdict"])
