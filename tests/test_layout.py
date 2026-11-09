"""Portfolio standard checks: required files exist and no public grade."""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REQUIRED = ["README.md", "PROPOSAL.md", "REPORT.md", "CHANGELOG.md", "CITATION.cff", "SECURITY.md",
            "HYPOTHESES.md", "requirements.txt", "src/run_all.py", "results/run_manifest.json",
            "data/default of credit card clients.xls", "data/german.data",
            "docs/decisions/0001-keep-existing-file-names.md", "docs/decisions/0002-not-pre-registered.md",
            "docs/decisions/0003-python-versions-in-ci.md"]
# Repo grades are internal. The PD model scorecard (src/grading.py, "/1000") is a lab output and allowed.
GRADE = re.compile(r"of 10,000|/ ?10,?000\b|\bGrade:|\bOverall: [A-F]|rubric")


def test_required_files_exist():
    missing = [p for p in REQUIRED if not os.path.exists(os.path.join(ROOT, p))]
    assert not missing, "missing: " + ", ".join(missing)


def test_readme_abstract():
    text = open(os.path.join(ROOT, "README.md")).read()
    for key in ("**Question.**", "**Headline.**", "**Field.**", "**Job family.**", "**Verdict.**",
                "## Lifecycle", "## Layout"):
        assert key in text, key


def test_no_public_grade():
    hits = []
    for dirpath, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in (".git", "node_modules", "dist", ".venv", "results")]
        for name in files:
            if name.endswith((".md", ".html", ".jsx", ".tsx", ".ts")):
                path = os.path.join(dirpath, name)
                for n, line in enumerate(open(path, encoding="utf-8", errors="ignore"), 1):
                    if GRADE.search(line):
                        hits.append(f"{os.path.relpath(path, ROOT)}:{n}")
    assert not hits, "public grade text (grades are internal): " + ", ".join(hits)


if __name__ == "__main__":
    test_required_files_exist()
    test_readme_abstract()
    test_no_public_grade()
    print("layout check: PASS")
