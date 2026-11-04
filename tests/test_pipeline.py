import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from credit_risk_lab import main, FEATURES, CATS  # noqa: E402

R = main()


def test_dataset_shape():
    assert R["dataset"]["rows"] == 30000
    assert 0.15 < R["dataset"]["default_rate"] < 0.30


def test_champion_auc_floor():
    champ = R["champion"]
    assert R["models"][champ]["auc"] > 0.65


def test_both_models_beat_chance():
    for m in R["models"].values():
        assert m["auc"] > 0.60
        assert 0 <= m["ks"] <= 1


def test_staging_partitions_portfolio():
    total = sum(s["accounts"] for s in R["staging"]["by_stage"])
    assert total == 30000


def test_ecl_positive_and_stage3_riskiest():
    assert R["staging"]["total_ecl"] > 0
    rates = {s["stage"]: s["observed_default_rate"] for s in R["staging"]["by_stage"]}
    assert rates[3] > rates[2] > rates[1]


def test_calibration_bins():
    assert len(R["validation"]["calibration_test"]) == 10


def test_data_quality_section():
    dq = R["data_quality"]
    assert dq["duplicate_id_count"] == 0
    assert dq["rows"] == 30000
    rates = dq["missing_rate_per_column"]
    assert "ID" in rates and "default" in rates
    assert all(0.0 <= v <= 1.0 for v in rates.values())


def test_feature_drift_section():
    drift = R["feature_drift"]
    for col in FEATURES + CATS:
        assert col in drift
        assert drift[col] < 0.10  # random split: no feature drifts materially


def test_config_recorded_and_applied():
    cfg = R["config"]
    assert cfg["seed"] == 42
    assert R["staging"]["lgd_assumption"] == cfg["lgd"]
    assert R["staging"]["lifetime_years_assumption"] == cfg["lifetime_years"]


def test_per_model_validation_present():
    for m in R["models"].values():
        assert len(m["calibration"]) == 10
        assert 0.0 <= m["score_psi"] < 0.10
    dist = R["validation"]["score_distribution"]
    total = sum(r["default"] + r["non_default"] for r in dist)
    assert total == R["dataset"]["test_rows"]


if __name__ == "__main__":
    print(json.dumps(R["models"], indent=1))
