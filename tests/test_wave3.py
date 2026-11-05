"""Wave 3: external validation floor, database cross-check, reason codes,
and the second-look partition. Each test reads the results files the
wave-3 modules wrote (or builds the DB to a temp path), so the suite
verifies the shipped artifacts, not re-derivations."""

import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def _load(name: str) -> dict:
    return json.loads((ROOT / "results" / name).read_text())


def test_german_champion_auc_floor():
    ext = _load("external_validation.json")
    champ = ext["models"][ext["champion"]]
    assert champ["auc"] > 0.55, champ
    assert ext["models"]["gradient_boosting"]["auc"] > 0.55
    assert ext["dataset"]["rows"] == 1000
    assert ext["dataset"]["test_rows"] == 300


def test_german_auc_ci_present_and_brackets_estimate():
    ext = _load("external_validation.json")
    for name, m in ext["models"].items():
        ci = m["auc_ci95"]
        assert ci["lo95"] <= m["auc"] <= ci["hi95"], (name, ci, m["auc"])
        assert ci["width"] > 0.02  # n=300: intervals must be honestly wide


def test_database_matches_published_results(tmp_path):
    import build_db
    import credit_risk_lab as pipe

    db = tmp_path / "credit.db"
    build_db.build(db, pipe.load_config())
    published = _load("results.json")
    con = sqlite3.connect(db)
    try:
        counts = dict(con.execute(
            "SELECT stage, COUNT(*) FROM staging GROUP BY stage"))
        ecl = con.execute(
            "SELECT ROUND(SUM(ecl), 2) FROM staging").fetchone()[0]
        n_accounts = con.execute(
            "SELECT COUNT(*) FROM accounts").fetchone()[0]
        n_scores = con.execute(
            "SELECT COUNT(*) FROM scores").fetchone()[0]
    finally:
        con.close()
    want = {int(s["stage"]): int(s["accounts"])
            for s in published["staging"]["by_stage"]}
    assert counts == want, (counts, want)
    assert abs(ecl - float(published["staging"]["total_ecl"])) < 1.0
    assert n_accounts == 30000
    assert n_scores == 60000  # both models, full portfolio


def test_reason_codes_contract():
    rc = _load("reason_codes.json")
    study = json.loads((ROOT / "results" / "study.json").read_text())
    rejected = int(study["creditworthy_rejects"]["rejected"])
    assert rc["rejected_applicants"] == rejected
    total_freq = sum(row["count"] for row in rc["reason_frequencies"])
    # Every rejected applicant gets at least one reason code.
    assert total_freq >= rejected, (total_freq, rejected)
    assert total_freq == rc["total_reason_assignments"]
    allowed = set(rc["reason_map"].values())
    assert {row["reason"] for row in rc["reason_frequencies"]} <= allowed
    per = rc["per_applicant"]
    assert len(per) == rejected
    assert all(1 <= len(v) <= 3 for v in per.values())
    assert all(r in allowed for v in per.values() for r in v)


def test_second_look_partition():
    sl = _load("second_look.json")
    study = _load("study.json")
    h = sl["headline"]
    cw_total = int(study["creditworthy_rejects"]["creditworthy_rejects"])
    rejected = int(study["creditworthy_rejects"]["rejected"])
    def_total = rejected - cw_total
    assert h["stage1_rejected"] == rejected
    assert h["creditworthy_rejects_stage1"] == cw_total
    assert h["recovered_creditworthy"] <= cw_total
    assert h["admitted_defaults"] <= def_total
    assert h["recovered_total"] == (h["recovered_creditworthy"] +
                                    h["admitted_defaults"])
    assert h["approved_after"] == h["stage1_approved"] + h["recovered_total"]
    assert 0 < h["recovery_rate_of_creditworthy"] < 1
    ci = sl["bootstrap_ci95"]["recovery_rate_of_creditworthy"]
    assert ci["lo95"] <= h["recovery_rate_of_creditworthy"] <= ci["hi95"]


def test_rigor_multi_seed_reported():
    rigor = _load("rigor.json")
    ms = rigor["multi_seed"]
    assert ms["seeds"] == [42, 7, 123, 2024, 31337]
    assert len(ms["per_seed"]) == 5
    for side in ("v1", "v2"):
        assert 0.70 < ms[side]["mean_auc"] < 0.85
        assert ms[side]["std_auc"] >= 0
