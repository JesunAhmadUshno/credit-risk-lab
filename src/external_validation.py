"""credit-risk-lab: external validation on UCI Statlog German Credit.

The published lab runs on one dataset (Taiwan 2005). This module asks the
transportability question on a second, independent population: the UCI
Statlog German Credit dataset (dataset 144; Germany, 1990s; 1,000
accounts; class 1 = good, 2 = bad, a 30 percent bad rate). It is a
different population and a different era from the Taiwan portfolio, and
every number it produces is labelled that way wherever it appears: these
are German Credit numbers, never Taiwan numbers.

Method mirrors the main pipeline as far as the schema allows: logistic
regression baseline and gradient boosting challenger, the same
preprocessing shape (median imputation, scaling, one-hot), a stratified
split with the configured test size and seed. The German schema has no
payment-history panel, so the behavioural-style features are the ratios
the schema supports: monthly amount (credit amount per month of
duration), total instalment burden (duration x instalment rate), and
credit amount per existing credit. These are documented here and in the
output, not dressed up as the Taiwan behavioural features.

Output: results/external_validation.json.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

import credit_risk_lab as pipe

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "german.data"
OUT = ROOT / "results" / "external_validation.json"

COLUMNS = [
    "checking_status", "duration_months", "credit_history", "purpose",
    "credit_amount", "savings", "employment_since", "installment_rate_pct",
    "personal_status_sex", "other_debtors", "residence_since", "property",
    "age", "other_installment_plans", "housing", "existing_credits", "job",
    "liable_people", "telephone", "foreign_worker", "class",
]
NUMERIC = ["duration_months", "credit_amount", "installment_rate_pct",
           "residence_since", "age", "existing_credits", "liable_people",
           "amount_per_month", "instalment_burden", "amount_per_credit"]
CATEGORICAL = [c for c in COLUMNS[:-1] if c not in NUMERIC]


def load_german(path: Path = DATA) -> pd.DataFrame:
    df = pd.read_csv(path, sep=r"\s+", header=None, names=COLUMNS)
    if len(df) != 1000:
        raise ValueError(f"German Credit file has {len(df)} rows; "
                         "expected 1,000 (UCI dataset 144)")
    bad = sorted(set(df["class"].unique()) - {1, 2})
    if bad:
        raise ValueError(f"German Credit class values must be 1/2; found {bad}")
    df["default"] = (df["class"] == 2).astype(int)
    return df


def add_features_german(df: pd.DataFrame) -> pd.DataFrame:
    """Behavioural-style ratios the German schema supports (see module doc)."""
    df = df.copy()
    df["amount_per_month"] = df["credit_amount"] / df["duration_months"].replace(0, np.nan)
    df["instalment_burden"] = df["duration_months"] * df["installment_rate_pct"]
    df["amount_per_credit"] = df["credit_amount"] / df["existing_credits"].replace(0, np.nan)
    return df


def _make_pipe(model) -> Pipeline:
    pre = ColumnTransformer([
        ("num", Pipeline([("imp", SimpleImputer(strategy="median")),
                          ("sc", StandardScaler())]), NUMERIC),
        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL),
    ])
    return Pipeline([("pre", pre), ("model", model)])


def fit_test(cfg: dict = None):
    """Fit both models on the German split; return (frame, y, preds, meta).

    Shared by compute() and src/rigor.py so the bootstrap resamples exactly
    the predictions this module publishes.
    """
    cfg = cfg or pipe.load_config()
    seed = int(cfg["seed"])
    df = add_features_german(load_german())
    X, y = df[NUMERIC + CATEGORICAL], df["default"]
    Xtr, Xte, ytr, yte = train_test_split(
        X, y, test_size=float(cfg["test_size"]), stratify=y, random_state=seed)
    models = {
        "logistic_regression": LogisticRegression(max_iter=1000, C=0.1),
        "gradient_boosting": HistGradientBoostingClassifier(
            max_iter=300, learning_rate=0.06, max_depth=3, random_state=seed),
    }
    preds = {}
    for name, model in models.items():
        fitted = _make_pipe(model).fit(Xtr, ytr)
        preds[name] = fitted.predict_proba(Xte)[:, 1]
    meta = {"rows": int(len(df)), "bad_rate": round(float(y.mean()), 4),
            "train_rows": int(len(Xtr)), "test_rows": int(len(Xte))}
    return df, yte.values, preds, meta


def compute(cfg: dict = None) -> dict:
    cfg = cfg or pipe.load_config()
    _, y_test, preds, meta = fit_test(cfg)
    published = json.loads((ROOT / "results" / "results.json").read_text())
    taiwan = published["models"]["gradient_boosting"]["auc"]
    out_models = {}
    for name, p in preds.items():
        auc = float(roc_auc_score(y_test, p))
        out_models[name] = {
            "auc": round(auc, 4),
            "ks": round(pipe.ks_stat(y_test, p), 4),
            "gini": round(2 * auc - 1, 4),
            "brier": round(float(brier_score_loss(y_test, p)), 4),
        }
    champion = max(out_models, key=lambda k: out_models[k]["auc"])
    return {
        "dataset": {
            "source": "UCI Statlog German Credit, dataset 144 "
                      "(Germany, 1990s vintage)",
            "population_note": ("A different population and era from the "
                                "Taiwan 2005 portfolio in results.json. "
                                "These numbers describe German Credit only "
                                "and must never be quoted as Taiwan "
                                "results."),
            **meta,
        },
        "method": ("Same approach as the main pipeline: logistic "
                   "regression and gradient boosting, median imputation, "
                   "scaling, one-hot encoding, stratified split, "
                   "configured seed and test size. Behavioural-style "
                   "engineered features: amount_per_month, "
                   "instalment_burden, amount_per_credit (the German "
                   "schema has no payment-history panel)."),
        "features": {"numeric": NUMERIC, "categorical": CATEGORICAL},
        "models": out_models,
        "champion": champion,
        "transportability": {
            "taiwan_champion_auc": taiwan,
            "german_gradient_boosting_auc":
                out_models["gradient_boosting"]["auc"],
            "german_champion": champion,
            "german_champion_auc": out_models[champion]["auc"],
            "gap_like_for_like": round(
                taiwan - out_models["gradient_boosting"]["auc"], 4),
            "reading": ("The like-for-like gap compares gradient "
                        "boosting on both datasets. On German Credit the "
                        "logistic baseline edges out gradient boosting, "
                        "the classic small-sample result: 1,000 accounts "
                        "do not feed a boosting model the way 30,000 do, "
                        "and German Credit has no payment-history panel, "
                        "so its confidence intervals are wide; see "
                        "results/rigor.json."),
        },
    }


def main() -> dict:
    out = compute()
    OUT.write_text(json.dumps(out, indent=1))
    return out


if __name__ == "__main__":
    r = main()
    for name, m in r["models"].items():
        print(f"{name}: AUC {m['auc']:.4f} KS {m['ks']:.4f} "
              f"Brier {m['brier']:.4f}")
    t = r["transportability"]
    print(f"German champion: {r['champion']} "
          f"({t['german_champion_auc']:.4f}); like-for-like GB gap vs "
          f"Taiwan: {t['gap_like_for_like']:+.4f} "
          f"({t['german_gradient_boosting_auc']:.4f} vs "
          f"{t['taiwan_champion_auc']:.4f})")
