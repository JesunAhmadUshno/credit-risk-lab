# Audit: credit-risk-lab (wave 3, 2026-11-04)

Scope: the full repository at the wave-3 build. Methods: pattern scans,
a dependency pin review, a line-level read of the wave-3 modules, and a
clean-checkout reproduction. Findings are stated with their evidence;
nothing is marked clean on the basis of not looking.

## 1. Secret scan

Patterns scanned across every tracked and untracked file (excluding
.venv, node_modules, and .git internals): API key and token shapes
(`sk-`, `ghp_`, `gho_`, `AKIA`, `xox`, `-----BEGIN`), and
key/token/password/secret assignments with plausible values.

Result: **clean.** No credentials, tokens, or private keys exist in the
repo. Two notes for precision:

- A naive substring scan false-positives on this repo: the string
  "sk-" occurs inside "credit-risk-lab" (in URLs and paths). The
  precise patterns above are the ones that matter, and they return
  nothing.
- `.github/workflows/pages.yml` carries `id-token: write`, which is
  the standard GitHub Pages OIDC permission, not a stored secret.

## 2. Dependency pinning

requirements.txt previously named packages without versions. It is
now a full freeze of the venv that produced the published results
(pandas 3.1.1, numpy 2.5.4, scikit-learn 1.9.1, scipy 1.18.1,
xlrd 2.0.2, openpyxl 3.1.5, pytest 9.2.0, plus transitive pins), with
a header stating what it is. Gap G5, closed.

## 3. Clean-checkout reproducibility proof

Procedure: the repo was copied to /tmp/repro-check excluding .venv,
node_modules, .git, web/dist, caches, and the generated database. A
fresh venv was created there and installed from the pinned
requirements.txt. The single reproduction command was then run:

    .venv/bin/python src/run_all.py

Outcome: **PASS, exact match.** The clean build's run_all completed
all 14 steps (522.0s wall on a heavily loaded shared machine;
reason codes were the long pole at 300.9s) and its invariant check
passed. A field-by-field comparison of the clean build against this
repo's published results found every value identical: logistic AUC
0.7518, gradient boosting AUC 0.7810, KS 0.4196, staging counts
22,099 / 7,438 / 463, baseline ECL NT$187,548,414.49,
probability-weighted ECL NT$192,303,983.68, and both German Credit
AUCs (0.8022 logistic, 0.7848 gradient boosting). The comparison
script printed REPRO_MATCH; the clean copy's manifest is at
/tmp/repro-check/results/run_manifest.json (its git commit reads
"unknown" because .git was excluded from the copy by design; this
repo's own manifest carries the commit).

The dataset SHA256 checksums and output hashes for both builds are in
each copy's results/run_manifest.json.

## 4. Code review findings (wave-3 pass)

- **results.json merge drift (fixed).** The headline JSON's contents
  depended on script order: the pipeline alone dropped the validation
  blocks that validation_pack.py merges. run_all.py now fixes the
  order and hash-records the outputs. Gap G11.
- **Database values are stored at full precision (fixed during the
  wave).** The first build_db draft rounded ECL to cents at insert
  time; the SQL total then drifted from the published JSON by more
  than rounding tolerance. Values are now stored unrounded and the
  cross-check test asserts agreement within NT$1 on a ~NT$187.5M
  total.
- **Determinism discipline.** Every wave-3 module takes its seed from
  config.json or a named constant (BOOT_SEED in rigor.py), writes
  with sorted or fixed ordering where a dict could leak iteration
  order into a document, and states its rule in its docstring before
  its code.
- **No dead code carried.** The wave-2 modules were re-read during
  integration; the one redundancy found (validation_pack recomputing
  per-feature CSI that the pipeline already computes) is upstream
  behaviour kept deliberately: the pack is self-contained by design,
  and both computations agree because they share the function.
- **Reason vocabulary fixed a priori.** All nine mapped features
  carry positive permutation importance on the test set (strongest:
  recent payment delay, 0.0370 AUC drop; weakest: payment ratio,
  0.0012). The vocabulary in src/reason_codes.py was documented
  before the ranking was computed and was not pruned to flatter it;
  the weakest feature stays, because a mapping revised after seeing
  importances would be a different, weaker claim. One mapping note:
  the "payment delay in the most recent month" reason is measured on
  dpd_months (PAY_0 clipped at zero, the lab's DPD proxy) while its
  importance is inherited from the model input PAY_0; the code says
  so where it happens.
- **Generated files are labelled generated.** MONITORING.md,
  VALIDATION.md, STUDY.md sections, dashboard.html, and
  web/src/data/results.ts all carry their generator and regeneration
  command.

## 5. What the audit did not do

- No penetration testing: the repo is analysis code and a static
  site; there is no server surface to test.
- No licence audit of the datasets beyond their UCI terms of use;
  both are public research datasets used with attribution.
- No review of GitHub account security settings; out of scope for a
  repo audit.
