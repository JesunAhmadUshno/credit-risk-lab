"""Unit tests: staging policy, grading bands, config, loader validation,
dashboard smoke. No full pipeline run needed for these.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from credit_risk_lab import (REQUIRED_COLUMNS, TARGET_RAW, add_features,  # noqa: E402
                             load_config, staging, validate_raw)
from grading import grade_all, letter_band  # noqa: E402
from dashboard import build_html  # noqa: E402


def _frame(pay0_values):
    n = len(pay0_values)
    df = pd.DataFrame({
        "PAY_0": pay0_values, "PAY_2": [0] * n, "PAY_3": [0] * n,
        "PAY_4": [0] * n, "PAY_5": [0] * n, "PAY_6": [0] * n,
        "BILL_AMT1": [10000] * n, "BILL_AMT6": [9000] * n,
        "LIMIT_BAL": [50000] * n, "PAY_AMT1": [1000] * n,
    })
    return add_features(df)


def test_staging_stage3_at_pay0_3():
    out = staging(_frame([3]), np.array([0.01]))
    assert out["stage"].iloc[0] == 3
    assert out["pd_applied"].iloc[0] == 1.0


def test_staging_stage2_at_30dpd():
    out = staging(_frame([1, 2]), np.array([0.02, 0.02]))
    assert list(out["stage"]) == [2, 2]


def test_staging_stage2_sicr_rule():
    # median PD 0.05, so 2x median = 0.10; a PD of 0.50 with no DPD is SICR.
    out = staging(_frame([-1] * 5), np.array([0.50, 0.05, 0.05, 0.05, 0.05]))
    assert out["stage"].iloc[0] == 2
    assert list(out["stage"].iloc[1:]) == [1, 1, 1, 1]


def test_staging_stage1_clean():
    out = staging(_frame([0, -1, 0]), np.array([0.05, 0.06, 0.04]))
    assert list(out["stage"]) == [1, 1, 1]


def test_staging_honours_config_lgd():
    df = _frame([0])
    base = staging(df, np.array([0.20]))
    doubled = staging(df, np.array([0.20]), cfg={"lgd": 0.90})
    assert doubled["ecl"].iloc[0] == pytest.approx(2 * base["ecl"].iloc[0])


def test_letter_band_boundaries():
    assert letter_band(1000) == "A"
    assert letter_band(900) == "A"
    assert letter_band(899.99) == "B"
    assert letter_band(800) == "B"
    assert letter_band(700) == "C"
    assert letter_band(600) == "D"
    assert letter_band(599.99) == "F"
    assert letter_band(0) == "F"


def test_config_loading_from_file():
    cfg = load_config()
    assert cfg["lgd"] == 0.45
    assert cfg["lifetime_years"] == 3
    assert cfg["seed"] == 42
    assert cfg["test_size"] == 0.30
    assert cfg["staging"]["stage3_dpd_months"] == 3
    assert cfg["staging"]["stage2_dpd_months"] == 1


def test_config_override_merges(tmp_path):
    p = tmp_path / "cfg.json"
    p.write_text(json.dumps({"lgd": 0.60}))
    cfg = load_config(p)
    assert cfg["lgd"] == 0.60
    assert cfg["seed"] == 42  # untouched keys fall back to defaults


def _raw_frame(target=(0, 1, 0)):
    data = {c: [0] * len(target) for c in REQUIRED_COLUMNS}
    data[TARGET_RAW] = list(target)
    data["ID"] = list(range(len(target)))
    return pd.DataFrame(data)


def test_validate_raw_accepts_good_frame():
    validate_raw(_raw_frame())


def test_validate_raw_missing_column():
    df = _raw_frame().drop(columns=["LIMIT_BAL"])
    with pytest.raises(ValueError, match="missing required columns"):
        validate_raw(df)


def test_validate_raw_bad_target():
    with pytest.raises(ValueError, match="only 0/1"):
        validate_raw(_raw_frame(target=(0, 2, 1)))


def test_dashboard_smoke():
    results = json.loads((ROOT / "results" / "results.json").read_text())
    html = build_html(results, grade_all(results))
    champ = results["champion"]
    champ_auc = f"{results['models'][champ]['auc']:.4f}"
    assert champ_auc in html
    assert "<script" not in html
    assert "Stage 3" in html
