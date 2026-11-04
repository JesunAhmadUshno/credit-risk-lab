"""Model grading scorecard for credit-risk-lab.

Grades each trained model on a 0 to 1000 scorecard, computed entirely from
results/results.json (the pipeline run output). Nothing is hand-typed:
change the run and the grades change.

Scorecard (1000 points):
  Discrimination  500   AUC 250 (benchmark 0.90), KS 150 (benchmark 0.60),
                        Gini 100 (benchmark 0.80). Each maps linearly from
                        the no-skill floor to the benchmark, capped.
  Calibration     300   Brier score 150 (0.10 full marks, 0.25 zero),
                        mean absolute calibration error across the 10-bin
                        table 150 (0.01 full marks, 0.10 zero).
  Stability       200   Score PSI, train vs test: 200 at PSI 0, 100 at
                        PSI 0.10, 0 at PSI 0.25 or worse (piecewise linear,
                        the standard PSI reading bands).

Letter bands: A 900+, B 800+, C 700+, D 600+, F below 600.
Every component reports its awarded points, its deduction, and the measured
value behind the deduction.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "results.json"
OUT = ROOT / "results" / "model_grades.json"

AUC_BENCH, KS_BENCH, GINI_BENCH = 0.90, 0.60, 0.80
BRIER_FULL, BRIER_ZERO = 0.10, 0.25
MAE_FULL, MAE_ZERO = 0.01, 0.10


def letter_band(score: float) -> str:
    if score >= 900:
        return "A"
    if score >= 800:
        return "B"
    if score >= 700:
        return "C"
    if score >= 600:
        return "D"
    return "F"


def _lin(value, floor, bench, max_points):
    """Linear points between a floor (0 points) and a benchmark (full points)."""
    frac = (value - floor) / (bench - floor) if bench != floor else 0.0
    return round(max(0.0, min(1.0, frac)) * max_points, 2)


def _lin_inverse(value, full_at, zero_at, max_points):
    """Points for lower-is-better metrics: full at full_at, zero at zero_at."""
    frac = (zero_at - value) / (zero_at - full_at) if zero_at != full_at else 0.0
    return round(max(0.0, min(1.0, frac)) * max_points, 2)


def _psi_points(psi_value, max_points=200):
    if psi_value <= 0.10:
        frac = 1.0 - 0.5 * (psi_value / 0.10)
    elif psi_value <= 0.25:
        frac = 0.5 * (1.0 - (psi_value - 0.10) / 0.15)
    else:
        frac = 0.0
    return round(max(0.0, min(1.0, frac)) * max_points, 2)


def _component(name, awarded, max_points, detail):
    return {"component": name, "points": awarded, "max_points": max_points,
            "deduction": round(max_points - awarded, 2), "detail": detail}


def grade_model(name: str, metrics: dict) -> dict:
    auc, ks, gini = metrics["auc"], metrics["ks"], metrics["gini"]
    brier, psi_value = metrics["brier"], metrics["score_psi"]
    calib = metrics["calibration"]
    mae = sum(abs(b["pred"] - b["obs"]) for b in calib) / len(calib)
    components = [
        _component("AUC", _lin(auc, 0.50, AUC_BENCH, 250), 250,
                   f"AUC {auc:.4f} vs benchmark {AUC_BENCH:.2f} (floor 0.50)"),
        _component("KS", _lin(ks, 0.0, KS_BENCH, 150), 150,
                   f"KS {ks:.4f} vs benchmark {KS_BENCH:.2f}"),
        _component("Gini", _lin(gini, 0.0, GINI_BENCH, 100), 100,
                   f"Gini {gini:.4f} vs benchmark {GINI_BENCH:.2f}"),
        _component("Brier score", _lin_inverse(brier, BRIER_FULL, BRIER_ZERO, 150), 150,
                   f"Brier {brier:.4f}; full marks at {BRIER_FULL:.2f}, zero at {BRIER_ZERO:.2f}"),
        _component("Calibration MAE", _lin_inverse(mae, MAE_FULL, MAE_ZERO, 150), 150,
                   f"mean |predicted - observed| {mae:.4f} across {len(calib)} bins; "
                   f"full marks at {MAE_FULL:.2f}, zero at {MAE_ZERO:.2f}"),
        _component("Score PSI (stability)", _psi_points(psi_value), 200,
                   f"score PSI {psi_value:.4f} train vs test; 100 of 200 at PSI 0.10, "
                   f"zero at PSI 0.25"),
    ]
    groups = {
        "discrimination": round(sum(c["points"] for c in components[:3]), 2),
        "calibration": round(sum(c["points"] for c in components[3:5]), 2),
        "stability": round(components[5]["points"], 2),
    }
    total = round(sum(groups.values()), 2)
    return {"model": name, "total_points": total, "letter_band": letter_band(total),
            "groups": groups, "components": components,
            "inputs": {"auc": auc, "ks": ks, "gini": gini, "brier": brier,
                       "score_psi": psi_value, "calibration_mae": round(mae, 4)}}


def grade_all(results: dict) -> dict:
    grades = {name: grade_model(name, m) for name, m in results["models"].items()}
    ranking = sorted(grades.values(), key=lambda g: -g["total_points"])
    return {
        "generated_from": "results/results.json (pipeline run output; no hand-typed figures)",
        "scorecard": "Discrimination 500 (AUC/KS/Gini), Calibration 300 (Brier + "
                     "calibration MAE), Stability 200 (score PSI). Bands: A 900+, "
                     "B 800+, C 700+, D 600+, F below 600.",
        "champion": results.get("champion"),
        "ranking": [g["model"] for g in ranking],
        "models": grades,
    }


def main() -> dict:
    results = json.loads(RESULTS.read_text())
    grades = grade_all(results)
    OUT.write_text(json.dumps(grades, indent=1))
    for g in grades["models"].values():
        print(f"{g['model']}: {g['total_points']:.2f}/1000 band {g['letter_band']} "
              f"(discrimination {g['groups']['discrimination']}/500, "
              f"calibration {g['groups']['calibration']}/300, "
              f"stability {g['groups']['stability']}/200)")
    print(f"champion: {grades['champion']} | ranking: {', '.join(grades['ranking'])}")
    return grades


if __name__ == "__main__":
    main()
