"""credit-risk-lab: scenario-weighted IFRS 9 style ECL engine.

IFRS 9 asks for a probability-weighted expected credit loss across forward
-looking macroeconomic scenarios. This module runs the lab's existing
staging policy and champion PD model under three scenarios whose weights
and PD multipliers live in config.json (stated lab assumptions, not
measured values):

    base      weight 0.50, PD multiplier 1.00
    upside    weight 0.20, PD multiplier 0.85
    downside  weight 0.30, PD multiplier 1.30

Each scenario scales the champion's PDs, re-runs the unchanged staging
policy on the scaled PDs, and recomputes ECL per stage. The
probability-weighted ECL is the weight sum of the scenario ECLs. The base
scenario (multiplier 1.00, LGD from config) is the published pipeline
baseline and must reproduce results/results.json total ECL exactly; this
module asserts that rather than assuming it.

It also computes the Basel floor view: portfolio EL with the QRRE
foundation LGD floor of 50 percent beside the lab's 45 percent assumption,
through the same staging code path.

Output: results/scenarios.json.
"""
import json
from pathlib import Path

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier

import credit_risk_lab as pipe

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "scenarios.json"
QRRE_LGD_FLOOR = 0.50


def _champion_full(df, cfg):
    """Champion model refit on the full portfolio (same path as main())."""
    X, y = df[pipe.FEATURES + pipe.CATS], df["default"]
    model = HistGradientBoostingClassifier(
        max_iter=300, learning_rate=0.06, max_depth=3,
        random_state=int(cfg["seed"]))
    full = pipe.make_pipe(model).fit(X, y)
    return full.predict_proba(X)[:, 1]


def _stage_rows(staged) -> list:
    rows = (staged.groupby("stage")
            .agg(accounts=("default", "size"), ead=("ead", "sum"),
                 ecl=("ecl", "sum"),
                 observed_default_rate=("default", "mean"))
            .round(2).reset_index())
    return rows.to_dict("records")


def compute(cfg: dict = None) -> dict:
    cfg = cfg or pipe.load_config()
    scen_cfg = cfg["scenarios"]
    weights = {k: float(v) for k, v in scen_cfg["weights"].items()}
    multipliers = {k: float(v) for k, v in scen_cfg["pd_multipliers"].items()}
    total_weight = sum(weights.values())
    assert abs(total_weight - 1.0) < 1e-9, f"scenario weights sum to {total_weight}"

    df = pipe.add_features(pipe.load())
    pds = _champion_full(df, cfg)

    published = json.loads((ROOT / "results" / "results.json").read_text())
    published_total = float(published["staging"]["total_ecl"])

    scenarios, weighted = {}, 0.0
    for name in ("base", "upside", "downside"):
        scaled = np.clip(pds * multipliers[name], 0.0, 1.0)
        staged = pipe.staging(df, scaled, cfg=cfg)
        total = round(float(staged["ecl"].sum()), 2)
        scenarios[name] = {
            "weight": weights[name],
            "pd_multiplier": multipliers[name],
            "total_ecl": total,
            "total_ead": round(float(staged["ead"].sum()), 2),
            "by_stage": _stage_rows(staged),
        }
        weighted += weights[name] * total

    baseline_total = scenarios["base"]["total_ecl"]
    assert abs(baseline_total - published_total) < 0.05, (
        f"base scenario ECL {baseline_total} does not reproduce the "
        f"published baseline {published_total}")

    floor_cfg = json.loads(json.dumps(cfg))
    floor_cfg["lgd"] = QRRE_LGD_FLOOR
    staged_floor = pipe.staging(df, pds, cfg=floor_cfg)
    basel = {
        "lgd_assumption": float(cfg["lgd"]),
        "ecl_at_lgd_assumption": baseline_total,
        "qrre_lgd_floor": QRRE_LGD_FLOOR,
        "ecl_at_qrre_lgd_floor": round(float(staged_floor["ecl"].sum()), 2),
        "note": ("Basel CRE32 foundation approach sets a 50 percent LGD "
                 "floor for qualifying revolving retail exposures (QRRE). "
                 "The lab's 45 percent LGD is a stated assumption below "
                 "that floor; both figures come from the same staging "
                 "code path."),
    }

    return {
        "generated_from": ("Champion PDs refit on the full portfolio with "
                           "the pipeline's own functions; staging policy "
                           "unchanged; scenario weights and PD multipliers "
                           "from config.json (stated assumptions)."),
        "weights": weights,
        "pd_multipliers": multipliers,
        "lgd": float(cfg["lgd"]),
        "baseline_total_ecl": baseline_total,
        "baseline_matches_results_json": True,
        "scenarios": scenarios,
        "weighted_ecl": round(weighted, 2),
        "basel_floor": basel,
    }


def main() -> dict:
    out = compute()
    OUT.write_text(json.dumps(out, indent=1))
    return out


if __name__ == "__main__":
    r = main()
    for name, s in r["scenarios"].items():
        print(f"{name:9} weight {s['weight']:.2f}  x{s['pd_multiplier']:.2f}  "
              f"ECL {s['total_ecl']:,.2f}")
    print(f"weighted ECL {r['weighted_ecl']:,.2f} "
          f"(baseline {r['baseline_total_ecl']:,.2f})")
    b = r["basel_floor"]
    print(f"Basel floor view: LGD {b['lgd_assumption']:.0%} -> "
          f"{b['ecl_at_lgd_assumption']:,.2f}; QRRE floor "
          f"{b['qrre_lgd_floor']:.0%} -> {b['ecl_at_qrre_lgd_floor']:,.2f}")
