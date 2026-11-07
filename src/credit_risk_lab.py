"""credit-risk-lab: PD modelling, validation, IFRS 9 style staging and ECL.

Dataset: UCI default of credit card clients (30,000 accounts, Taiwan 2005).
Method mirrors a risk-modelling posting: develop and validate ML and
statistical models for credit decisioning, behavioural features, model
validation metrics, staging, and expected credit loss.

All measured numbers land in results/results.json. Run parameters (LGD,
lifetime horizon, staging thresholds, seed, test size) live in config.json
at the repo root. LGD and the lifetime horizon are stated lab assumptions,
not measured values, and are labelled as such everywhere they appear.
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
CONFIG_PATH = ROOT / "config.json"
TARGET_RAW = "default payment next month"

REQUIRED_COLUMNS = (
    ["ID", "LIMIT_BAL", "SEX", "EDUCATION", "MARRIAGE", "AGE"] +
    ["PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6"] +
    [f"BILL_AMT{i}" for i in range(1, 7)] +
    [f"PAY_AMT{i}" for i in range(1, 7)] +
    [TARGET_RAW]
)

DEFAULT_CONFIG = {
    "lgd": 0.45,
    "lifetime_years": 3,
    "seed": 42,
    "test_size": 0.30,
    "calibration_bins": 10,
    "psi_bins": 10,
    "score_distribution_bins": 20,
    "staging": {
        "stage3_dpd_months": 3,
        "stage2_dpd_months": 1,
        "sicr_pd_multiple_of_median": 2.0,
        "sicr_pd_floor": 0.10,
    },
    "scenarios": {
        "weights": {"base": 0.5, "upside": 0.2, "downside": 0.3},
        "pd_multipliers": {"base": 1.0, "upside": 0.85, "downside": 1.3},
    },
}


def load_config(path: Path = CONFIG_PATH) -> dict:
    """Load run parameters from config.json, merged over the defaults."""
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))
    if path is not None and Path(path).exists():
        loaded = json.loads(Path(path).read_text())
        for key, value in loaded.items():
            if isinstance(value, dict) and isinstance(cfg.get(key), dict):
                cfg[key].update(value)
            else:
                cfg[key] = value
    return cfg


def validate_raw(df: pd.DataFrame) -> pd.DataFrame:
    """Validate the raw frame as read from the source file.

    Raises ValueError with a specific message on any structural problem:
    missing required columns, zero rows, or a target outside {0, 1}.
    """
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"input data is missing required columns: {missing}")
    if len(df) == 0:
        raise ValueError("input data has 0 rows; expected the UCI credit "
                         "dataset (30,000 rows)")
    target = df[TARGET_RAW]
    if target.isna().any():
        raise ValueError(f"target column '{TARGET_RAW}' contains "
                         f"{int(target.isna().sum())} missing values")
    bad = sorted(set(target.unique()) - {0, 1})
    if bad:
        raise ValueError(f"target column '{TARGET_RAW}' must contain only "
                         f"0/1 values; found {bad}")
    return df


def load(path: Path = DATA) -> pd.DataFrame:
    df = pd.read_excel(path, header=1)
    validate_raw(df)
    df = df.rename(columns={TARGET_RAW: "default"})
    df["EDUCATION"] = df["EDUCATION"].replace({0: 4, 5: 4, 6: 4})
    df["MARRIAGE"] = df["MARRIAGE"].replace({0: 3})
    return df


def data_quality(df: pd.DataFrame) -> dict:
    """Missing rate per column and duplicate ID count, for results.json."""
    return {
        "rows": int(len(df)),
        "columns": int(df.shape[1]),
        "missing_rate_per_column": {
            c: round(float(df[c].isna().mean()), 4) for c in df.columns},
        "duplicate_id_count": int(df["ID"].duplicated().sum())
        if "ID" in df.columns else None,
    }


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
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
    expected = np.asarray(expected, dtype=float)
    actual = np.asarray(actual, dtype=float)
    expected = expected[~np.isnan(expected)]
    actual = actual[~np.isnan(actual)]
    qs = np.quantile(expected, np.linspace(0, 1, bins + 1))
    qs = np.unique(qs)
    qs[0], qs[-1] = -np.inf, np.inf
    e = np.histogram(expected, qs)[0] / len(expected)
    a = np.histogram(actual, qs)[0] / len(actual)
    e = np.where(e == 0, 1e-4, e)
    a = np.where(a == 0, 1e-4, a)
    return float(np.sum((a - e) * np.log(a / e)))


def psi_categorical(expected, actual) -> float:
    cats = sorted(set(expected) | set(actual))
    e = np.array([np.mean(np.asarray(expected) == c) for c in cats])
    a = np.array([np.mean(np.asarray(actual) == c) for c in cats])
    e = np.where(e == 0, 1e-4, e)
    a = np.where(a == 0, 1e-4, a)
    return float(np.sum((a - e) * np.log(a / e)))


def feature_drift(Xtr: pd.DataFrame, Xte: pd.DataFrame, bins=10) -> dict:
    """PSI per feature between the train and test splits."""
    drift = {}
    for col in FEATURES:
        drift[col] = round(psi(Xtr[col].values, Xte[col].values, bins=bins), 4)
    for col in CATS:
        drift[col] = round(psi_categorical(Xtr[col].values, Xte[col].values), 4)
    return drift


def calibration(y, p, bins=10) -> list:
    df = pd.DataFrame({"y": y, "p": p})
    df["bin"] = pd.qcut(df["p"], bins, duplicates="drop")
    g = df.groupby("bin", observed=True).agg(
        n=("y", "size"), pred=("p", "mean"), obs=("y", "mean")).reset_index(drop=True)
    return g.round(4).to_dict("records")


def score_distribution(y, p, bins=20) -> list:
    """Test-set score counts by outcome, in fixed 0..1 bins (for the dashboard)."""
    edges = np.linspace(0, 1, bins + 1)
    y = np.asarray(y)
    rows = []
    for i in range(bins):
        lo, hi = edges[i], edges[i + 1]
        in_bin = (p >= lo) & (p < hi if i < bins - 1 else p <= hi)
        rows.append({
            "bin_start": round(float(lo), 2), "bin_end": round(float(hi), 2),
            "non_default": int(np.sum(in_bin & (y == 0))),
            "default": int(np.sum(in_bin & (y == 1))),
        })
    return rows


def staging(df: pd.DataFrame, pd_scores: np.ndarray, cfg: dict = None) -> pd.DataFrame:
    """IFRS 9 style staging policy (lab rules, stated in the README).

    Stage 3: DPD at or beyond the stage-3 threshold (90+ DPD proxy at 3).
    Stage 2: significant increase in credit risk: DPD at or beyond the
             stage-2 threshold (30+ DPD at 1), or modelled PD at least the
             configured multiple of the portfolio median and above the
             configured PD floor.
    Stage 1: everyone else.
    Thresholds, LGD and the lifetime horizon come from config.json; the LGD
    and horizon are assumptions, not measured values.
    """
    merged = json.loads(json.dumps(DEFAULT_CONFIG))
    if cfg:
        for key, value in cfg.items():
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key].update(value)
            else:
                merged[key] = value
    st = merged["staging"]
    lgd = float(merged["lgd"])
    lifetime = int(merged["lifetime_years"])
    out = df.copy()
    out["pd"] = pd_scores
    median_pd = np.median(pd_scores)
    sicr = (out["pd"] >= st["sicr_pd_multiple_of_median"] * median_pd) & \
           (out["pd"] > st["sicr_pd_floor"])
    out["stage"] = np.where(out["dpd_months"] >= st["stage3_dpd_months"], 3,
                            np.where((out["dpd_months"] >= st["stage2_dpd_months"]) | sicr, 2, 1))
    out["pd_applied"] = np.where(out["stage"] == 3, 1.0,
                                 np.where(out["stage"] == 2,
                                          1 - (1 - out["pd"]) ** lifetime,
                                          out["pd"]))
    out["ead"] = out["BILL_AMT1"].clip(lower=0)
    out["ecl"] = out["pd_applied"] * lgd * out["ead"]
    return out


def main(cfg: dict = None, out: Path = OUT) -> dict:
    """Run the pipeline and write results to `out` (tests pass a temp path
    so they never overwrite the published results/results.json)."""
    cfg = cfg or load_config()
    seed = int(cfg["seed"])
    raw = load()
    quality = data_quality(raw)
    df = add_features(raw)
    X, y = df[FEATURES + CATS], df["default"]
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=float(cfg["test_size"]),
                                          stratify=y, random_state=seed)
    models = {
        "logistic_regression": LogisticRegression(max_iter=1000, C=0.1),
        "gradient_boosting": HistGradientBoostingClassifier(
            max_iter=300, learning_rate=0.06, max_depth=3, random_state=seed),
    }
    results = {"dataset": {"rows": int(len(df)),
                           "default_rate": round(float(y.mean()), 4),
                           "train_rows": int(len(Xtr)), "test_rows": int(len(Xte))},
               "config": cfg,
               "data_quality": quality,
               "feature_drift": feature_drift(Xtr, Xte, bins=int(cfg["psi_bins"])),
               "models": {}}
    best_name, best_auc, best_pipe = None, -1.0, None
    for name, m in models.items():
        pipe = make_pipe(m).fit(Xtr, ytr)
        p = pipe.predict_proba(Xte)[:, 1]
        p_tr = pipe.predict_proba(Xtr)[:, 1]
        auc = roc_auc_score(yte, p)
        results["models"][name] = {
            "auc": round(float(auc), 4),
            "ks": round(ks_stat(yte.values, p), 4),
            "gini": round(float(2 * auc - 1), 4),
            "brier": round(float(brier_score_loss(yte, p)), 4),
            "score_psi": round(psi(p_tr, p, bins=int(cfg["psi_bins"])), 4),
            "calibration": calibration(yte.values, p,
                                       bins=int(cfg["calibration_bins"])),
        }
        if auc > best_auc:
            best_name, best_auc, best_pipe = name, auc, pipe
    results["champion"] = best_name
    p_test = best_pipe.predict_proba(Xte)[:, 1]
    results["validation"] = {
        "score_psi_train_vs_test": results["models"][best_name]["score_psi"],
        "calibration_test": results["models"][best_name]["calibration"],
        "score_distribution": score_distribution(
            yte.values, p_test, bins=int(cfg["score_distribution_bins"])),
    }
    full = best_pipe.fit(X, y)
    staged = staging(df, full.predict_proba(X)[:, 1], cfg=cfg)
    stage_rows = (staged.groupby("stage")
                  .agg(accounts=("default", "size"), ead=("ead", "sum"),
                       ecl=("ecl", "sum"), observed_default_rate=("default", "mean"))
                  .round(2).reset_index())
    st = cfg["staging"]
    results["staging"] = {
        "policy": (f"Stage 3: PAY_0 >= {st['stage3_dpd_months']} (90+ DPD proxy). "
                   f"Stage 2: PAY_0 >= {st['stage2_dpd_months']} (30+ DPD) or PD >= "
                   f"{st['sicr_pd_multiple_of_median']}x median PD and > "
                   f"{st['sicr_pd_floor']}. Stage 1: rest."),
        "lgd_assumption": cfg["lgd"], "lifetime_years_assumption": cfg["lifetime_years"],
        "by_stage": stage_rows.to_dict("records"),
        "total_ecl": round(float(staged["ecl"].sum()), 2),
        "total_ead": round(float(staged["ead"].sum()), 2),
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=1))
    return results


if __name__ == "__main__":
    r = main()
    print(json.dumps(r["models"], indent=1))
    print("champion:", r["champion"], "| total ECL:", r["staging"]["total_ecl"])
