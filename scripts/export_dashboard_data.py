#!/usr/bin/env python3
"""Export dashboard data for the React app.

Reads results/results.json and results/model_grades.json (both produced by
the Python pipeline) and writes web/src/data/results.ts. On top of that
pass-through it computes the chart series the dashboard needs (ROC curves
for both models, the champion decile gains/lift table, per-stage simulator
aggregates) by importing the pipeline's own functions with the same config,
seed and split, so every derived figure is consistent with the published
results. The script asserts the headline metrics reproduce exactly and
refuses to write output if they move.

Regenerate after every pipeline run:

    .venv/bin/python scripts/export_dashboard_data.py
"""
import json
import sys
from pathlib import Path

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, roc_curve
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "web" / "src" / "data" / "results.ts"
sys.path.insert(0, str(ROOT / "src"))

import credit_risk_lab as pipe  # noqa: E402


def roc_points(y, p, max_points=150):
    fpr, tpr, _ = roc_curve(y, p)
    if len(fpr) > max_points:
        idx = np.unique(np.linspace(0, len(fpr) - 1, max_points).astype(int))
        fpr, tpr = fpr[idx], tpr[idx]
    return [{"fpr": round(float(a), 4), "tpr": round(float(b), 4)}
            for a, b in zip(fpr, tpr)]


def decile_table(y, p):
    """Gains/lift deciles for the champion, test set, decile 1 = riskiest."""
    y = np.asarray(y)
    order = np.argsort(-np.asarray(p))
    ys = y[order]
    groups = np.array_split(ys, 10)
    total_defaults = int(ys.sum())
    overall_rate = float(ys.mean())
    rows, cum_d, cum_n = [], 0, 0
    for i, g in enumerate(groups, start=1):
        defaults = int(g.sum())
        cum_d += defaults
        cum_n += len(g)
        rate = float(g.mean())
        rows.append({
            "decile": i,
            "accounts": int(len(g)),
            "defaults": defaults,
            "defaultRate": round(rate, 4),
            "lift": round(rate / overall_rate, 3) if overall_rate else 0.0,
            "cumulativeCapture": round(cum_d / total_defaults, 4),
            "cumulativeShare": round(cum_n / len(ys), 4),
        })
    return rows


def derived_series(results: dict) -> dict:
    """Recompute chart series with the pipeline's own functions.

    Same config, seed and split as the published run; asserts the headline
    metrics reproduce exactly before returning anything.
    """
    cfg = pipe.load_config()
    seed = int(cfg["seed"])
    df = pipe.add_features(pipe.load())
    X, y = df[pipe.FEATURES + pipe.CATS], df["default"]
    Xtr, Xte, ytr, yte = train_test_split(
        X, y, test_size=float(cfg["test_size"]), stratify=y, random_state=seed)
    models = {
        "logistic_regression": LogisticRegression(max_iter=1000, C=0.1),
        "gradient_boosting": HistGradientBoostingClassifier(
            max_iter=300, learning_rate=0.06, max_depth=3, random_state=seed),
    }
    roc, preds = {}, {}
    for name, model in models.items():
        fitted = pipe.make_pipe(model).fit(Xtr, ytr)
        p = fitted.predict_proba(Xte)[:, 1]
        preds[name] = p
        auc = round(float(roc_auc_score(yte, p)), 4)
        published = results["models"][name]
        assert auc == published["auc"], (name, auc, published["auc"])
        assert round(pipe.ks_stat(yte.values, p), 4) == published["ks"], name
        roc[name] = roc_points(yte.values, p)

    champion = results["champion"]
    deciles = decile_table(yte.values, preds[champion])

    full = pipe.make_pipe(models[champion]).fit(X, y)
    staged = pipe.staging(df, full.predict_proba(X)[:, 1], cfg=cfg)
    simulator = []
    published_stages = {int(s["stage"]): s for s in results["staging"]["by_stage"]}
    for stage, g in sorted(staged.groupby("stage")):
        stage = int(stage)
        ead_total = float(g["ead"].sum())
        w = g["ead"] / ead_total if ead_total else g["ead"] * 0
        row = {
            "stage": stage,
            "accounts": int(len(g)),
            "ead": round(ead_total, 2),
            "ecl": round(float(g["ecl"].sum()), 2),
            "meanPd": round(float((g["pd"] * w).sum()), 8),
            "meanPdApplied": round(float((g["pd_applied"] * w).sum()), 8),
            "observedDefaultRate": round(float(g["default"].mean()), 4),
        }
        pub = published_stages[stage]
        assert row["accounts"] == int(pub["accounts"]), (stage, row, pub)
        assert abs(row["ecl"] - float(pub["ecl"])) < 0.05, (stage, row, pub)
        simulator.append(row)
    total_ecl = round(sum(r["ecl"] for r in simulator), 2)
    assert abs(total_ecl - float(results["staging"]["total_ecl"])) < 0.05, (
        total_ecl, results["staging"]["total_ecl"])
    return {"roc": roc, "deciles": deciles, "simulatorStages": simulator}


def main() -> None:
    results = json.loads((ROOT / "results" / "results.json").read_text())
    grades = json.loads((ROOT / "results" / "model_grades.json").read_text())
    derived = derived_series(results)
    print("headline metrics reproduced exactly: AUCs, KS, staging, total ECL")

    payload = {
        "dataset": results["dataset"],
        "config": results["config"],
        "dataQuality": results["data_quality"],
        "featureDrift": results["feature_drift"],
        "models": results["models"],
        "champion": results["champion"],
        "validation": results["validation"],
        "staging": results["staging"],
        "roc": derived["roc"],
        "deciles": derived["deciles"],
        "simulatorStages": derived["simulatorStages"],
        "grades": {
            "scorecard": grades["scorecard"],
            "champion": grades["champion"],
            "ranking": grades["ranking"],
            "models": grades["models"],
        },
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(payload, indent=1)
    OUT.write_text(
        "// GENERATED by scripts/export_dashboard_data.py from\n"
        "// results/results.json and results/model_grades.json plus chart\n"
        "// series recomputed with the pipeline's own functions.\n"
        "// Do not edit by hand. Regenerate: .venv/bin/python scripts/export_dashboard_data.py\n"
        f"export const data = {body} as const;\n"
        "\nexport type DashboardData = typeof data;\n"
    )
    print(f"wrote {OUT} ({len(body)} bytes of measured data)")


if __name__ == "__main__":
    main()
