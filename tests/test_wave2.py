"""Wave-2 tests: scenario engine, fair access study, transition features.

The compute functions are run once at module level (same pattern as
test_pipeline.py). Each refits models with the published split and seed,
so the numbers under test are the numbers in the results files.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import credit_risk_lab as pipe  # noqa: E402
import behavioural_v2  # noqa: E402
import scenarios as scen  # noqa: E402
import study  # noqa: E402

SCEN = scen.compute()
STUDY = study.compute()
BV2 = behavioural_v2.compute()


# --- scenario engine -------------------------------------------------------

def test_scenario_weights_sum_to_one():
    total = sum(SCEN["weights"].values())
    assert total == pytest.approx(1.0)
    cfg_weights = pipe.load_config()["scenarios"]["weights"]
    assert SCEN["weights"] == {k: float(v) for k, v in cfg_weights.items()}


def test_scenario_baseline_reproduces_published_ecl():
    published = json.loads((ROOT / "results" / "results.json").read_text())
    assert SCEN["baseline_total_ecl"] == pytest.approx(
        published["staging"]["total_ecl"], abs=0.05)
    assert SCEN["scenarios"]["base"]["pd_multiplier"] == 1.0


def test_scenario_ordering_and_weighted_between():
    totals = {k: v["total_ecl"] for k, v in SCEN["scenarios"].items()}
    assert totals["upside"] < totals["base"] < totals["downside"]
    assert min(totals.values()) < SCEN["weighted_ecl"] < max(totals.values())


def test_basel_floor_view_scales_with_lgd():
    b = SCEN["basel_floor"]
    assert b["qrre_lgd_floor"] == 0.50
    assert b["ecl_at_qrre_lgd_floor"] == pytest.approx(
        b["ecl_at_lgd_assumption"] * 0.50 / 0.45, rel=1e-6)


# --- fair access study -----------------------------------------------------

def test_study_reject_counts_partition_test_set():
    a = STUDY["creditworthy_rejects"]
    assert a["approved"] + a["rejected"] == a["test_accounts"] == 9000
    assert 0 <= a["creditworthy_rejects"] <= a["rejected"]
    assert a["cutoff_pd"] > 0


def test_study_cutoff_holds_stage1_risk_appetite():
    a = STUDY["creditworthy_rejects"]
    target = a["risk_appetite"]["target_approved_default_rate"]
    assert abs(a["achieved_approved_default_rate"] - target) < 0.01


def test_study_target_is_the_observed_stage1_rate_not_a_rounded_one():
    # The risk appetite is "the Stage 1 observed default rate". Recompute
    # it from the champion's staging and check the study used it, not a
    # 2-dp rounding (0.12 instead of 0.1244 moves the cut-off).
    cfg = pipe.load_config()
    df = pipe.add_features(pipe.load())
    X, y = df[pipe.FEATURES + pipe.CATS], df["default"]
    champ = pipe.make_pipe(study._gbm(int(cfg["seed"]))).fit(X, y)
    staged = pipe.staging(df, champ.predict_proba(X)[:, 1], cfg=cfg)
    observed = float(staged.loc[staged["stage"] == 1, "default"].mean())
    target = STUDY["creditworthy_rejects"]["risk_appetite"][
        "target_approved_default_rate"]
    assert abs(target - observed) < 1e-6, (target, observed)


def test_thin_file_auc_in_range():
    b = STUDY["thin_file"]
    assert 0.5 < b["auc"] <= b["full_model_auc"] + 0.05
    assert "LIMIT_BAL" not in b["features"]
    assert "BILL_AMT1" not in b["features"]


def test_fairness_groups_cover_test_set():
    for variable, block in STUDY["fairness"]["by_variable"].items():
        assert sum(g["n"] for g in block["groups"]) == 9000, variable
        assert 0.0 <= block["approval_rate_gap"] <= 1.0
    lg = STUDY["fairness"]["largest_gap"]
    assert lg["gap"] == max(
        b["approval_rate_gap"]
        for b in STUDY["fairness"]["by_variable"].values())


# --- behavioural v2 --------------------------------------------------------

def _pay_frame(rows):
    cols = ["PAY_6", "PAY_5", "PAY_4", "PAY_3", "PAY_2", "PAY_0"]
    return pd.DataFrame(rows, columns=cols)


def test_transition_features_strictly_worsening():
    out = behavioural_v2.add_transition_features(
        _pay_frame([[0, 1, 2, 3, 4, 5]]))
    row = out.iloc[0]
    assert row["dpd_worsen_steps"] == 5
    assert row["dpd_max_consec"] == 5  # the leading 0 month is not delinquent
    assert row["dpd_slope"] > 0
    assert row["dpd_recent3_mean"] == pytest.approx((3 + 4 + 5) / 3)


def test_transition_features_flat_and_clean():
    out = behavioural_v2.add_transition_features(
        _pay_frame([[-1, -1, -2, 0, -1, -1], [2, 2, 0, 0, 1, 1]]))
    clean, mixed = out.iloc[0], out.iloc[1]
    assert clean["dpd_worsen_steps"] == 0
    assert clean["dpd_slope"] == pytest.approx(0.0)
    assert clean["dpd_max_consec"] == 0
    assert mixed["dpd_max_consec"] == 2
    assert mixed["dpd_worsen_steps"] == 1  # only the 0 -> 1 step worsens


def test_transition_features_shape_preserved():
    frame = _pay_frame([[0, 0, 1, 1, 2, 2], [5, 4, 3, 2, 1, 0]])
    out = behavioural_v2.add_transition_features(frame)
    assert len(out) == len(frame)
    for col in behavioural_v2.TRANSITION_FEATURES:
        assert col in out.columns
        assert out[col].notna().all()


def test_behavioural_v2_reported_either_way():
    assert BV2["v1_gradient_boosting"]["auc"] == pytest.approx(0.7810)
    assert BV2["v2_beats_v1"] == (BV2["delta_auc"] > 0)
    assert BV2["delta_auc"] == pytest.approx(
        BV2["v2_gradient_boosting_plus_transitions"]["auc"]
        - BV2["v1_gradient_boosting"]["auc"], abs=1e-4)
