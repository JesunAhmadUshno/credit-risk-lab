"""credit-risk-lab: one-command autonomous rebuild of the entire lab.

    .venv/bin/python src/run_all.py

Rebuilds everything end to end, in dependency order:

    pipeline -> grading -> static dashboard -> scenarios -> behavioural
    v2 -> study -> second look -> reason codes -> external validation
    -> validation pack -> monitoring -> database -> rigor -> dashboard
    data export

Then it asserts the headline invariants (the published AUCs, KS,
staging counts, baseline and scenario-weighted ECL) and writes
results/run_manifest.json: per-step durations, the git commit being
built, SHA256 checksums of both dataset files, and SHA256 hashes of
every output in results/. If any step fails or any invariant breaks,
the command exits nonzero and says which one. The manifest is written
only on success, so a manifest on disk is a receipt for a clean build.

This is the single reproduction command documented in the README. The
wave-3 clean-checkout audit (docs/analysis/AUDIT.md) ran exactly this
inside a fresh copy with a fresh venv.
"""
import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(ROOT / "scripts"))

import behavioural_v2  # noqa: E402
import build_db  # noqa: E402
import credit_risk_lab as pipe  # noqa: E402
import dashboard  # noqa: E402
import external_validation  # noqa: E402
import grading  # noqa: E402
import monitoring  # noqa: E402
import reason_codes  # noqa: E402
import rigor  # noqa: E402
import scenarios  # noqa: E402
import second_look  # noqa: E402
import study  # noqa: E402
import validation_pack  # noqa: E402
import export_dashboard_data  # noqa: E402

RESULTS = ROOT / "results"
MANIFEST = RESULTS / "run_manifest.json"

# The published headline numbers. A rebuild that moves any of these has
# changed the science, not just the plumbing, and must fail loudly.
INVARIANTS = {
    "logistic_auc": 0.7518,
    "champion_auc": 0.7810,
    "champion_ks": 0.4196,
    "staging_counts": [22099, 7438, 463],
    "baseline_ecl": 187548414.49,
    "weighted_ecl": 192303983.68,
}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _git_commit() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
            text=True, timeout=15)
        return out.stdout.strip() if out.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


def check_invariants() -> dict:
    results = json.loads((RESULTS / "results.json").read_text())
    scen = json.loads((RESULTS / "scenarios.json").read_text())
    got = {
        "logistic_auc": results["models"]["logistic_regression"]["auc"],
        "champion_auc": results["models"]["gradient_boosting"]["auc"],
        "champion_ks": results["models"]["gradient_boosting"]["ks"],
        "staging_counts": [int(s["accounts"])
                           for s in results["staging"]["by_stage"]],
        "baseline_ecl": results["staging"]["total_ecl"],
        "weighted_ecl": scen["weighted_ecl"],
    }
    failures = []
    for key, want in INVARIANTS.items():
        g = got[key]
        ok = abs(g - want) < 0.05 if isinstance(want, float) else g == want
        if not ok:
            failures.append(f"{key}: got {g}, expected {want}")
    if failures:
        raise AssertionError("headline invariants broken: " +
                             "; ".join(failures))
    return got


def main() -> dict:
    steps = [
        ("pipeline", lambda: pipe.main()),
        ("grading", lambda: grading.main()),
        ("static_dashboard", lambda: dashboard.build()),
        ("scenarios", lambda: scenarios.main()),
        ("behavioural_v2", lambda: behavioural_v2.main()),
        ("study", lambda: study.main()),
        ("second_look", lambda: second_look.main()),
        ("reason_codes", lambda: reason_codes.main()),
        ("external_validation", lambda: external_validation.main()),
        ("validation_pack", lambda: validation_pack.main()),
        ("monitoring", lambda: monitoring.main()),
        ("database", lambda: build_db.main()),
        ("rigor", lambda: rigor.main()),
        ("dashboard_export", lambda: export_dashboard_data.main()),
    ]
    started = datetime.now(timezone.utc)
    timings = []

    def flush_manifest(complete: bool) -> dict:
        datasets = {}
        for rel in ("data/default of credit card clients.xls",
                    "data/german.data"):
            p = ROOT / rel
            if p.exists():
                datasets[rel] = _sha256(p)
        outputs = {p.name: _sha256(p)
                   for p in sorted(RESULTS.glob("*.json"))
                   if p.name != "run_manifest.json"}
        manifest = {
            "built_at_utc": started.isoformat(),
            "finished_at_utc": datetime.now(timezone.utc).isoformat(),
            "git_commit": _git_commit(),
            "complete": complete,
            "steps": timings,
            "total_seconds": round(sum(t["seconds"] for t in timings), 2),
            "dataset_sha256": datasets,
            "output_sha256": outputs,
        }
        if complete:
            manifest["invariants_verified"] = check_invariants()
        MANIFEST.write_text(json.dumps(manifest, indent=1))
        return manifest

    for name, fn in steps:
        t0 = time.perf_counter()
        try:
            fn()
        except Exception as exc:
            print(f"FAILED step {name}: {exc!r}", file=sys.stderr)
            raise
        dt = round(time.perf_counter() - t0, 2)
        timings.append({"step": name, "seconds": dt})
        print(f"[run_all] {name}: {dt:.2f}s")
        # Progressive manifest: a build interrupted here still leaves
        # a receipt naming the steps that finished (complete=false).
        flush_manifest(complete=False)

    manifest = flush_manifest(complete=True)
    print("[run_all] headline invariants verified:",
          manifest["invariants_verified"])
    print(f"[run_all] manifest written: {MANIFEST} "
          f"(total {manifest['total_seconds']:.1f}s, commit "
          f"{manifest['git_commit'][:12]})")
    return manifest


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"run_all FAILED: {exc!r}", file=sys.stderr)
        sys.exit(1)
