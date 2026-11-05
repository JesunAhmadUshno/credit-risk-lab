-- credit-risk-lab: standing analytics queries for data/credit.db
-- Build the database first:  .venv/bin/python src/build_db.py
-- Run any single query:      sqlite3 data/credit.db "<query>"
-- Amounts are NT$ as recorded in UCI dataset 350. LGD and the lifetime
-- horizon are stated lab assumptions (see the meta table), not measures.

-- Q1: Staging summary. Accounts, exposure, expected loss and the average
-- applied PD per IFRS 9 style stage, worst stage last.
SELECT stage,
       COUNT(*)                                   AS accounts,
       ROUND(SUM(ead), 2)                         AS total_ead,
       ROUND(SUM(ecl), 2)                         AS total_ecl,
       ROUND(AVG(pd_applied), 4)                  AS mean_pd_applied,
       ROUND(SUM(ecl) / NULLIF(SUM(ead), 0), 4)   AS ecl_rate
FROM staging
GROUP BY stage
ORDER BY stage;

-- Q2: Score decile default rates for the champion model. Decile 1 is the
-- lowest PD (safest) tenth of the scored portfolio; the observed default
-- rate should climb monotonically toward decile 10.
WITH ranked AS (
    SELECT s.pd,
           a."default" AS defaulted,
           NTILE(10) OVER (ORDER BY s.pd) AS decile
    FROM scores s
    JOIN accounts a ON a.account_id = s.account_id
    WHERE s.model = 'gradient_boosting'
)
SELECT decile,
       COUNT(*)                    AS accounts,
       SUM(defaulted)              AS defaults,
       ROUND(AVG(defaulted), 4)   AS observed_default_rate,
       ROUND(MIN(pd), 4)           AS pd_min,
       ROUND(MAX(pd), 4)           AS pd_max
FROM ranked
GROUP BY decile
ORDER BY decile;

-- Q3: Approval rates by education group at the study cut-off. Approval
-- means the champion PD (full-portfolio refit) is at or below the study
-- cut-off stored in meta. Education codes follow the pipeline recode:
-- 1 graduate school, 2 university, 3 high school, 4 other.
SELECT CASE a.education
           WHEN 1 THEN 'Graduate school'
           WHEN 2 THEN 'University'
           WHEN 3 THEN 'High school'
           ELSE 'Other'
       END                                       AS education_group,
       COUNT(*)                                  AS accounts,
       SUM(CASE WHEN s.pd <= CAST(m.value AS REAL)
                THEN 1 ELSE 0 END)               AS approved,
       ROUND(AVG(CASE WHEN s.pd <= CAST(m.value AS REAL)
                      THEN 1.0 ELSE 0.0 END), 4) AS approval_rate
FROM accounts a
JOIN scores s ON s.account_id = a.account_id AND s.model = 'gradient_boosting'
JOIN meta m ON m.key = 'study_cutoff_pd'
GROUP BY education_group
ORDER BY approval_rate DESC;

-- Q4: Scenario ECL totals. Per-stage rows for the three macro scenarios,
-- plus the probability-weighted portfolio total (stage 0 row), so a
-- reader can reconcile the weighted ECL against its components.
SELECT scenario,
       stage,
       accounts,
       ROUND(ead, 2) AS ead,
       ROUND(ecl, 2) AS ecl
FROM scenario_staging
ORDER BY CASE scenario
             WHEN 'base' THEN 1
             WHEN 'upside' THEN 2
             WHEN 'downside' THEN 3
             ELSE 4
         END,
         stage;
