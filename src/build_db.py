"""credit-risk-lab: SQLite database layer.

The lab's outputs lived only in JSON files and notebooks of code. This
module builds a queryable SQLite database, data/credit.db, from the UCI
source file and the pipeline outputs:

    accounts          one row per account: raw attributes, the target,
                      and the engineered behavioural features.
    scores            one row per account per model: the PD from each
                      model refit on the full portfolio (the same refit
                      the staging engine uses for the champion).
    staging           one row per account: stage, PD, PD applied, EAD
                      and ECL under the lab's staging policy (champion).
    scenario_staging  stage aggregates per macro scenario, from
                      results/scenarios.json, so scenario ECL totals are
                      queryable beside the baseline.
    meta              build parameters a query needs: the study cut-off,
                      the LGD assumption, the seed.

sql/queries.sql holds the standing analytics queries against this
schema. The cross-check test (tests/test_wave3.py) asserts the SQL
staging counts and total ECL match results/results.json.

Usage: .venv/bin/python src/build_db.py [optional output path]
"""
import json
import sqlite3
import sys
from pathlib import Path

import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression

import credit_risk_lab as pipe

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "credit.db"
QUERIES = ROOT / "sql" / "queries.sql"

ACCOUNT_COLS = (
    ["ID", "LIMIT_BAL", "SEX", "EDUCATION", "MARRIAGE", "AGE"] +
    ["PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6"] +
    [f"BILL_AMT{i}" for i in range(1, 7)] +
    [f"PAY_AMT{i}" for i in range(1, 7)] +
    ["default", "utilization", "pay_ratio", "delinq_mean", "delinq_max",
     "bill_trend", "dpd_months"]
)


def build(db_path: Path = DEFAULT_DB, cfg: dict = None) -> dict:
    cfg = cfg or pipe.load_config()
    seed = int(cfg["seed"])
    df = pipe.add_features(pipe.load())
    X, y = df[pipe.FEATURES + pipe.CATS], df["default"]
    models = {
        "logistic_regression": LogisticRegression(max_iter=1000, C=0.1),
        "gradient_boosting": HistGradientBoostingClassifier(
            max_iter=300, learning_rate=0.06, max_depth=3, random_state=seed),
    }
    score_rows = []
    champion_pd = None
    for name, model in models.items():
        fitted = pipe.make_pipe(model).fit(X, y)
        p = fitted.predict_proba(X)[:, 1]
        if name == "gradient_boosting":
            champion_pd = p
        # Stored at full precision: the database is the precise layer, so
        # SQL aggregates reconcile with results.json to float precision.
        # Rounding belongs to presentation, not storage.
        score_rows.append(pd.DataFrame(
            {"account_id": df["ID"].astype(int), "model": name,
             "pd": [float(v) for v in p]}))
    scores = pd.concat(score_rows, ignore_index=True)

    staged = pipe.staging(df, champion_pd, cfg=cfg)
    staging = pd.DataFrame({
        "account_id": staged["ID"].astype(int),
        "stage": staged["stage"].astype(int),
        "pd": staged["pd"],
        "pd_applied": staged["pd_applied"],
        "ead": staged["ead"],
        "ecl": staged["ecl"],
    })

    scenarios = json.loads((ROOT / "results" / "scenarios.json").read_text())
    scen_rows = []
    for name, s in scenarios["scenarios"].items():
        for row in s["by_stage"]:
            scen_rows.append({
                "scenario": name, "weight": s["weight"],
                "pd_multiplier": s["pd_multiplier"],
                "stage": int(row["stage"]), "accounts": int(row["accounts"]),
                "ead": float(row["ead"]), "ecl": float(row["ecl"]),
                "observed_default_rate": float(row["observed_default_rate"]),
            })
    scen_rows.append({
        "scenario": "probability_weighted", "weight": None,
        "pd_multiplier": None, "stage": 0, "accounts": int(len(df)),
        "ead": float(scenarios["scenarios"]["base"]["total_ead"]),
        "ecl": float(scenarios["weighted_ecl"]),
        "observed_default_rate": float(df["default"].mean()),
    })
    scenario_staging = pd.DataFrame(scen_rows)

    study = json.loads((ROOT / "results" / "study.json").read_text())
    meta = pd.DataFrame([
        {"key": "study_cutoff_pd",
         "value": str(study["creditworthy_rejects"]["cutoff_pd"])},
        {"key": "lgd_assumption", "value": str(cfg["lgd"])},
        {"key": "lifetime_years_assumption",
         "value": str(cfg["lifetime_years"])},
        {"key": "seed", "value": str(seed)},
        {"key": "source_dataset",
         "value": "UCI dataset 350, default of credit card clients"},
    ])

    accounts = df[ACCOUNT_COLS].copy()
    accounts.columns = [c.lower() if c != "ID" else "account_id"
                        for c in accounts.columns]

    db_path = Path(db_path)
    if db_path.exists():
        db_path.unlink()
    con = sqlite3.connect(db_path)
    try:
        accounts.to_sql("accounts", con, index=False)
        scores.to_sql("scores", con, index=False)
        staging.to_sql("staging", con, index=False)
        scenario_staging.to_sql("scenario_staging", con, index=False)
        meta.to_sql("meta", con, index=False)
        con.execute("CREATE INDEX idx_scores_account ON scores(account_id)")
        con.execute("CREATE INDEX idx_staging_account ON staging(account_id)")
        con.commit()
        counts = {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                  for t in ("accounts", "scores", "staging",
                            "scenario_staging", "meta")}
    finally:
        con.close()
    return {"db_path": str(db_path), "tables": counts,
            "total_ecl": round(float(staging["ecl"].sum()), 2)}


def main() -> dict:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DB
    out = build(path)
    print(f"built {out['db_path']}: {out['tables']}; "
          f"staging total ECL {out['total_ecl']:,.2f}")
    return out


if __name__ == "__main__":
    main()
