"""credit-risk-lab: adverse-action style reason codes for rejected applicants.

When a lender declines an applicant, practice (and, in several
jurisdictions, law) expects the principal reasons. This module produces
them for the lab's rejected test applicants in a documented, auditable
way:

1. Driver ranking comes from permutation importance on the champion
   model (test set, same split and seed as the published run; AUC drop
   when each feature is shuffled, 5 repeats). This ranks which features
   the model actually leans on, globally.
2. Per applicant, a factor counts as present under a two-tier rule, both
   tiers documented here and applied in code order:
   - Tier 1 (strong evidence): the applicant's value crosses a stated
     adverse threshold for that feature (absolute thresholds for the
     delinquency codes; test-set adverse quartiles for amounts).
   - Tier 2 (relative evidence): if fewer than three factors are present
     after tier 1, remaining mapped features are ranked by adverse
     z-deviation from the approved group's mean, and the worst fill the
     list. The approved group is the natural reference: an adverse-action
     reason says how this applicant differs from those approved.
3. Each applicant's factors are ordered by the feature's permutation
   importance, and the top 3 are emitted as their reason codes.

The mapping below (feature -> plain-language reason, adverse direction)
is the whole vocabulary: reasons are drawn only from it. Demographic
attributes (AGE, SEX, EDUCATION, MARRIAGE) are deliberately excluded:
decline reasons should cite behaviour and financial position, not who
the applicant is.

These are model-derived explanations, not causal findings. A reason
says "the model scored this applicant down in part because of X", never
"X caused the default risk". The output file repeats that label.

Output: results/reason_codes.json.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.inspection import permutation_importance
from sklearn.model_selection import train_test_split

import credit_risk_lab as pipe
import study as study_mod

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "reason_codes.json"
TOP_K = 3
N_REPEATS = 5

# feature -> (plain-language reason, adverse direction +1/-1)
REASON_MAP = {
    "utilization": ("High utilisation: the statement balance is high "
                    "relative to the credit limit", +1),
    "delinq_max": ("Severe past delinquency: the worst payment status in "
                   "the last six months shows an extended delay", +1),
    "dpd_months": ("Payment delay in the most recent month", +1),
    "delinq_mean": ("Repeated payment delays across the last six months", +1),
    "pay_ratio": ("Low repayment ratio: recent payments cover a small "
                  "share of the statement balance", -1),
    "bill_trend": ("Rising balance trend over the last six months", +1),
    "BILL_AMT1": ("High current statement balance", +1),
    "PAY_AMT1": ("Low most recent payment amount", -1),
    "LIMIT_BAL": ("Low credit limit relative to approved applicants", -1),
}

# Tier-1 absolute thresholds for the delinquency codes. Amount and ratio
# features use test-set adverse quartiles instead (computed in code).
TIER1_ABSOLUTE = {
    "dpd_months": 1.0,      # any delay in the most recent month
    "delinq_max": 2.0,      # worst month at 2+ months delayed
    "delinq_mean": 1.0,     # average delay of a month or more
    "utilization": 0.8,     # balance at 80%+ of the limit
    "pay_ratio": 0.05,      # payments at 5% or less of the balance (low side)
}


def _fit_champion(cfg):
    seed = int(cfg["seed"])
    df = pipe.add_features(pipe.load())
    X, y = df[pipe.FEATURES + pipe.CATS], df["default"]
    Xtr, Xte, ytr, yte = train_test_split(
        X, y, test_size=float(cfg["test_size"]), stratify=y,
        random_state=seed)
    champ = pipe.make_pipe(HistGradientBoostingClassifier(
        max_iter=300, learning_rate=0.06, max_depth=3,
        random_state=seed)).fit(Xtr, ytr)
    ids = df.loc[Xte.index, "ID"]
    return Xte, yte, champ, ids


def compute(cfg: dict = None) -> dict:
    cfg = cfg or pipe.load_config()
    seed = int(cfg["seed"])
    Xte, yte, champ, ids = _fit_champion(cfg)
    p_test = champ.predict_proba(Xte)[:, 1]

    results = json.loads((ROOT / "results" / "results.json").read_text())
    stage1_rate = float(next(s["observed_default_rate"]
                             for s in results["staging"]["by_stage"]
                             if int(s["stage"]) == 1))
    threshold, _, _ = study_mod.choose_cutoff(p_test, yte.values, stage1_rate)

    # The applicant frame carries every mapped feature, including the
    # engineered dpd_months (PAY_0 clipped at 0), which is not itself a
    # model input column: the model consumes PAY_0. Its driver strength
    # below is therefore PAY_0's permutation importance.
    full = pipe.add_features(pipe.load())
    test = full.loc[Xte.index, list(REASON_MAP)].copy()
    test["default"] = yte.values
    test["pd"] = p_test
    test["account_id"] = ids.values
    approved = test[test["pd"] <= threshold]
    rejected = test[test["pd"] > threshold].copy()

    perm = permutation_importance(
        champ, Xte, yte, n_repeats=N_REPEATS, random_state=seed,
        scoring="roc_auc", n_jobs=4)
    importance = {f: float(v) for f, v in zip(Xte.columns, perm.importances_mean)}
    if "PAY_0" in importance:
        importance["dpd_months"] = importance["PAY_0"]
    mapped_ranking = sorted(
        (f for f in REASON_MAP if f in importance),
        key=lambda f: -importance[f])

    # Tier-1 thresholds: absolutes where defined, else the adverse
    # quartile of the rejected+approved test distribution.
    quartile = {}
    for feat, (_, direction) in REASON_MAP.items():
        if feat in TIER1_ABSOLUTE:
            continue
        q = test[feat].quantile(0.75 if direction > 0 else 0.25)
        quartile[feat] = float(q)

    def tier1_present(feat, value) -> bool:
        direction = REASON_MAP[feat][1]
        if feat in TIER1_ABSOLUTE:
            t = TIER1_ABSOLUTE[feat]
            return value >= t if direction > 0 else value <= t
        t = quartile[feat]
        return value >= t if direction > 0 else value <= t

    approved_mean = {f: float(approved[f].mean()) for f in REASON_MAP}
    approved_std = {f: float(approved[f].std()) or 1.0 for f in REASON_MAP}

    per_applicant = {}
    freq = {f: 0 for f in REASON_MAP}
    for idx, row in rejected.iterrows():
        present = [f for f in REASON_MAP if tier1_present(f, float(row[f]))]
        present.sort(key=lambda f: -importance[f])
        chosen = present[:TOP_K]
        if len(chosen) < TOP_K:
            rest = [f for f in mapped_ranking if f not in chosen]
            def adverse_z(f, row=row):
                return (REASON_MAP[f][1] *
                        (float(row[f]) - approved_mean[f]) / approved_std[f])
            rest.sort(key=lambda f: -adverse_z(f))
            for f in rest:
                if len(chosen) >= TOP_K:
                    break
                if adverse_z(f) > 0:
                    chosen.append(f)
        if not chosen:
            chosen = [mapped_ranking[0]]
        for f in chosen:
            freq[f] += 1
        per_applicant[str(int(row["account_id"]))] = \
            [REASON_MAP[f][0] for f in chosen]

    ranked_reasons = sorted(
        ({"feature": f, "reason": REASON_MAP[f][0], "count": freq[f],
          "share_of_rejected": round(freq[f] / max(len(rejected), 1), 4),
          "permutation_importance": round(importance[f], 4)}
         for f in REASON_MAP),
        key=lambda r: -r["count"])

    return {
        "generated_from": ("Champion model, same split and seed as the "
                           "published run. Permutation importance on the "
                           "test set (AUC drop, "
                           f"{N_REPEATS} repeats); per-applicant factors "
                           "under the two-tier rule documented in "
                           "src/reason_codes.py."),
        "label": ("Reason codes are model-derived explanations of the "
                  "score, not causal findings, and not legal "
                  "adverse-action notices."),
        "cutoff_pd": round(float(threshold), 6),
        "rejected_applicants": int(len(rejected)),
        "reasons_per_applicant": TOP_K,
        "reason_map": {f: REASON_MAP[f][0] for f in REASON_MAP},
        "global_importance_ranking": [
            {"feature": f, "permutation_importance": round(importance[f], 4)}
            for f in mapped_ranking],
        "reason_frequencies": ranked_reasons,
        "total_reason_assignments": int(sum(freq.values())),
        "per_applicant": per_applicant,
    }


def main() -> dict:
    out = compute()
    OUT.write_text(json.dumps(out, indent=1))
    return out


if __name__ == "__main__":
    r = main()
    print(f"rejected applicants: {r['rejected_applicants']}; "
          f"assignments: {r['total_reason_assignments']}")
    for row in r["reason_frequencies"][:5]:
        print(f"  {row['count']:5d} ({row['share_of_rejected']:.1%})  "
              f"{row['reason']}")
