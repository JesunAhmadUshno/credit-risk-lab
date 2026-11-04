# credit-risk-lab web dashboard

React + Vite + TypeScript single-page dashboard for the credit-risk-lab
pipeline: overview KPIs, model grading with named deductions, ROC curves,
IFRS 9 staging portfolio views, calibration / gains / drift validation, and
an ECL sensitivity simulator. Deployed to GitHub Pages by
`.github/workflows/pages.yml` on every push to `main`.

Live: https://jesunahmadushno.github.io/credit-risk-lab/

## Data rule

No number is typed into a component. The app imports one generated file,
`src/data/results.ts`, produced from the pipeline outputs:

    # from the repo root, after a pipeline run
    .venv/bin/python scripts/export_dashboard_data.py

The export passes through `results/results.json` and
`results/model_grades.json`, and recomputes the chart series (ROC curves,
champion decile gains/lift, per-stage simulator aggregates) with the
pipeline's own functions, same config, seed and split. It asserts the
headline metrics reproduce exactly and refuses to write if they move.

## Develop

    npm install
    npm run dev      # local dev server
    npm run build    # production build into dist/ (base /credit-risk-lab/)

## Simulator note

The Simulator tab recomputes ECL by stage in the browser from the exported
per-stage aggregates only. It is a sensitivity calculation on published
aggregates, not a model re-run; the baseline position reproduces the
pipeline ECL total exactly.
