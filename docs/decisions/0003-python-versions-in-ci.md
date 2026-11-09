# 0003: Full suite on Python 3.12; standard checks on 3.11

Date: 2026-11-08. Status: accepted.

Context: the standard asks for CI on Python 3.11 and 3.12. The pinned
freeze in requirements.txt (numpy 2.5.4, pandas 3.1.1) requires Python
3.12 or newer; docs/analysis/AUDIT.md section 2 records that CI on 3.11
used to install different library versions and so never tested the
environment behind the published numbers.

Decision: the full test suite and the results rebuild run on 3.12
with the exact pins. The 3.11 job runs the standard checks
(tests/test_layout.py, stdlib only) and byte-compiles every Python
file, so syntax that 3.11 cannot parse still fails CI. No second,
looser requirements file is kept.

Consequence: numbers are only ever produced under the pinned 3.12
environment. Revisit when the pins move.
