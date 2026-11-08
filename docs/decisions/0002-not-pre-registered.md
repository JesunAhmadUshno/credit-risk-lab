# 0002: Label the repo "not pre-registered"; no proposal tag

Date: 2026-11-08. Status: accepted.

Context: METHOD section 7 tags proposal-v1 only where git history
proves the plan came before any code or result. The first commit
(d083dad) carried SPEC.md together with code and results. H1 to H4
were registered at f5fb365, before the wave 3 code but after wave 1
and 2 results, and d12cccb later edited a registered parameter (the
Stage 1 target, 12.00% to 12.44%) as part of a rounding fix.

Decision: no proposal-v1 tag. The repo carries "not pre-registered"
and its verdict is capped at Functional. The wave 3 registration is
described honestly in PROPOSAL.md and REPORT.md section 7, not
promoted to a lock after the fact.

Consequence: Evaluated needs a confirmatory cycle under a new
PROPOSAL lock, tagged before it runs (the recalibration study, gap
G9, is the natural first one).
