import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from credit_risk_lab import main  # noqa: E402

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


if __name__ == "__main__":
    print(json.dumps(R["models"], indent=1))
