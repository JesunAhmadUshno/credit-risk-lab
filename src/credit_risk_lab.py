"""credit-risk-lab: PD modelling, validation, IFRS 9 style staging and ECL.

Dataset: UCI default of credit card clients (30,000 accounts, Taiwan 2005).
Method mirrors a risk-modelling posting: develop and validate ML and
statistical models for credit decisioning, behavioural features, model
validation metrics, staging, and expected credit loss.

All measured numbers land in results/results.json. Assumptions (LGD, lifetime
PD horizon) are constants below and are stated in the README.
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

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "default of credit card clients.xls"
OUT = ROOT / "results" / "results.json"

LGD = 0.45            # lab assumption: Basel-style unsecured benchmark
LIFETIME_YEARS = 3    # lab assumption for the lifetime PD approximation
SEED = 42


def load() -> pd.DataFrame:
    df = pd.read_excel(DATA, header=1)
    df = df.rename(columns={"default payment next month": "default"})
    df["EDUCATION"] = df["EDUCATION"].replace({0: 4, 5: 4, 6: 4})
    df["MARRIAGE"] = df["MARRIAGE"].replace({0: 3})
    return df


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    pay = [f"PAY_{i}" for i in range(0, 7) if f"PAY_{i}" in df.columns]
    pay = [c for c in ["PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6"]]
    df["utilization"] = df["BILL_AMT1"] / df["LIMIT_BAL"].replace(0, np.nan)
    df["pay_ratio"] = df["PAY_AMT1"] / df["BILL_AMT1"].replace(0, np.nan)
    df["pay_ratio"] = df["pay_ratio"].fillna(0).clip(-1, 5)
    df["delinq_mean"] = df[pay].clip(lower=0).mean(axis=1)
    df["delinq_max"] = df[pay].clip(lower=0).max(axis=1)
    df["bill_trend"] = (df["BILL_AMT1"] - df["BILL_AMT6"]) / df["LIMIT_BAL"].replace(0, np.nan)
    df["dpd_months"] = df["PAY_0"].clip(lower=0)
    return df


FEATURES = (["LIMIT_BAL", "AGE", "BILL_AMT1", "PAY_AMT1", "utilization",
             "pay_ratio", "delinq_mean", "delinq_max", "bill_trend"] +
            ["PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6"])
CATS = ["SEX", "EDUCATION", "MARRIAGE"]


def make_pipe(model) -> Pipeline:
    pre = ColumnTransformer([
        ("num", Pipeline([("imp", SimpleImputer(strategy="median")),
                          ("sc", StandardScaler())]), FEATURES),
        ("cat", OneHotEncoder(handle_unknown="ignore"), CATS),
    ])
    return Pipeline([("pre", pre), ("model", model)])


def ks_stat(y, p) -> float:
    order = np.argsort(-p)
    y = np.asarray(y)[order]
    tp = np.cumsum(y) / max(y.sum(), 1)
    fp = np.cumsum(1 - y) / max((1 - y).sum(), 1)
    return float(np.max(tp - fp))


def psi(expected, actual, bins=10) -> float:
    qs = np.quantile(expected, np.linspace(0, 1, bins + 1))
    qs[0], qs[-1] = -np.inf, np.inf
    e = np.histogram(expected, qs)[0] / len(expected)
    a = np.histogram(actual, qs)[0] / len(actual)
    e = np.where(e == 0, 1e-4, e)
    a = np.where(a == 0, 1e-4, a)
    return float(np.sum((a - e) * np.log(a / e)))


def calibration(y, p, bins=10) -> list:
    df = pd.DataFrame({"y": y, "p": p})
    df["bin"] = pd.qcut(df["p"], bins, duplicates="drop")
    g = df.groupby("bin", observed=True).agg(
        n=("y", "size"), pred=("p", "mean"), obs=("y", "mean")).reset_index(drop=True)
    return g.round(4).to_dict("records")


def staging(df: pd.DataFrame, pd_scores: np.ndarray) -> pd.DataFrame:
    """IFRS 9 style staging policy (lab rules, stated in the README).

    Stage 3: 90+ days past due proxy (PAY_0 >= 3 months delayed).
    Stage 2: significant increase in credit risk: 30+ DPD (PAY_0 >= 1), or
             modelled PD at least twice the portfolio median and above 10%.
    Stage 1: everyone else.
    """
    out = df.copy()
    out["pd"] = pd_scores
    median_pd = np.median(pd_scores)
    sicr = (out["pd"] >= 2 * median_pd) & (out["pd"] > 0.10)
    out["stage"] = np.where(out["dpd_months"] >= 3, 3,
                            np.where((out["dpd_months"] >= 1) | sicr, 2, 1))
    out["pd_applied"] = np.where(out["stage"] == 3, 1.0,
                                 np.where(out["stage"] == 2,
                                          1 - (1 - out["pd"]) ** LIFETIME_YEARS,
                                          out["pd"]))
    out["ead"] = out["BILL_AMT1"].clip(lower=0)
    out["ecl"] = out["pd_applied"] * LGD * out["ead"]
    return out


def main() -> dict:
    df = add_features(load())
    X, y = df[FEATURES + CATS], df["default"]
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.30,
                                          stratify=y, random_state=SEED)
    models = {
        "logistic_regression": LogisticRegression(max_iter=1000, C=0.1),
        "gradient_boosting": HistGradientBoostingClassifier(
            max_iter=300, learning_rate=0.06, max_depth=3, random_state=SEED),
    }
    results = {"dataset": {"rows": int(len(df)),
                           "default_rate": round(float(y.mean()), 4),
                           "train_rows": int(len(Xtr)), "test_rows": int(len(Xte))},
               "models": {}}
    best_name, best_auc, best_pipe = None, -1.0, None
    for name, m in models.items():
        pipe = make_pipe(m).fit(Xtr, ytr)
        p = pipe.predict_proba(Xte)[:, 1]
        auc = roc_auc_score(yte, p)
        results["models"][name] = {
            "auc": round(float(auc), 4),
            "ks": round(ks_stat(yte.values, p), 4),
            "gini": round(float(2 * auc - 1), 4),
            "brier": round(float(brier_score_loss(yte, p)), 4),
        }
        if auc > best_auc:
            best_name, best_auc, best_pipe = name, auc, pipe
    results["champion"] = best_name
    p_test = best_pipe.predict_proba(Xte)[:, 1]
    p_train = best_pipe.predict_proba(Xtr)[:, 1]
    results["validation"] = {
        "score_psi_train_vs_test": round(psi(p_train, p_test), 4),
        "calibration_test": calibration(yte.values, p_test),
    }
    full = best_pipe.fit(X, y)
    staged = staging(df, full.predict_proba(X)[:, 1])
    stage_rows = (staged.groupby("stage")
                  .agg(accounts=("default", "size"), ead=("ead", "sum"),
                       ecl=("ecl", "sum"), observed_default_rate=("default", "mean"))
                  .round(2).reset_index())
    results["staging"] = {
        "policy": "Stage 3: PAY_0 >= 3 (90+ DPD proxy). Stage 2: PAY_0 >= 1 (30+ DPD) or PD >= 2x median PD and > 10%. Stage 1: rest.",
        "lgd_assumption": LGD, "lifetime_years_assumption": LIFETIME_YEARS,
        "by_stage": stage_rows.to_dict("records"),
        "total_ecl": round(float(staged["ecl"].sum()), 2),
        "total_ead": round(float(staged["ead"].sum()), 2),
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(results, indent=1))
    return results


if __name__ == "__main__":
    r = main()
    print(json.dumps(r, indent=1))
