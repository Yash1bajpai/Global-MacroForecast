# Global MacroForecast

GDP forecasting research for the US, India, Japan and Germany using LightGBM
and ARMA (the current SARIMAX configurations have no seasonal term).
The code is MIT licensed. Third-party data remains subject to provider terms.

Dashboard: https://global-macro-forecast.vercel.app/

## Status: no demonstrated forecast skill

The legacy dashboard snapshot and saved models are retained, not promoted or
rewritten by this change. Their old accuracy claims are not reliable: they used
same-quarter indicators, hindsight recession/COVID flags, and test-derived
ensemble weights. The new evaluation is a research backtest on revised data,
not proof of real-time forecasting performance.

### Reproducible rolling results

Evaluation uses 16 validation origins (2016 Q1 through 2019 Q4), then 26 test
origins (2020 Q1 through 2026 Q2). At origin t, only observations through t-2
enter training or indicator features. This allows a full quarter for releases.
All fits expand through time; ARMA makes a two-step forecast from t-2. Last-value
baseline also uses t-2. Seasonal naive uses t-4. Training-mean is recomputed at
each origin. Configurations and blend weights are selected using validation
RMSE only, then frozen before test. Test labels do not pick parameters or weights.

| Country | Candidate RMSE | Mean RMSE | Last RMSE | Seasonal RMSE | Candidate MAE | Mean MAE |
|---|---:|---:|---:|---:|---:|---:|
| US | 2.451 | 2.280 | 3.366 | 3.322 | 1.207 | 1.056 |
| India | 10.440 | 7.468 | 11.285 | 8.563 | 5.175 | 3.349 |
| Japan | 1.873 | 1.839 | 2.388 | 2.817 | 1.015 | 0.934 |
| Germany | 2.807 | 2.574 | 3.841 | 3.789 | 1.351 | 1.106 |

Errors are percentage points in each country's stored GDP-growth units, not
percent accuracy. None beats the training-mean baseline on test RMSE or MAE.
The validation choice is 50% LightGBM / 50% ARMA for the US and 100% ARMA for the
other countries. A blend is allowed to select an endpoint, not forced to mix.

Sign accuracy means expansion vs contraction, not whether growth increased
relative to the prior quarter. Candidate vs always-positive: US 84.6% vs 88.5%,
India 88.5% vs 92.3%, Japan 65.4% vs 69.2%, Germany 53.8% vs 61.5%.
No sign-prediction advantage is shown.

### Legacy comparison, not an apples-to-apples improvement claim

Recomputed from the checked-in models on the same 26 dates:

| Country | Legacy ensemble RMSE | Fixed pre-2020 mean RMSE |
|---|---:|---:|
| US | 2.261 | 2.274 |
| India | 7.426 | 7.453 |
| Japan | 1.641 | 1.836 |
| Germany | 2.361 | 2.571 |

Legacy numbers combine different forecast horizons and leaked inputs, and the
weights were picked on that test period. They are not a valid benchmark for
claiming improved model quality. See `reports/legacy_metrics.json`,
`reports/evaluation.json` and the per-origin CSVs for exact values.

## What changed

- A whitelist builds only embargoed GDP/indicator lags, lagged differences,
  shifted rolling stats and known calendar quarter. No raw current-quarter
  indicators, annual World Bank features, recession or COVID flags enter models.
  Annual data backfill was also removed. The OECD leading index is excluded
  pending verification of its raw series grouping.
- One shared implementation replaces the duplicated country trainers. The old
  pooled model entry point is retired until a panel-specific evaluation exists.
- Two small LightGBM configurations, two ARMA orders and five blend weights
  are compared on validation, not test. Nonconverged ARMA fits cannot enter a
  nonzero-weight blend. Failed predictions do not become fabricated metrics.
- The monthly workflow produces isolated downloadable candidates. It has
  read-only repository permission, no commit/push or production JSON export.
  A fail-closed gate requires strict RMSE and MAE wins over all three baselines
  on validation and test, plus no regression vs an approved causal incumbent on
  identical test dates. There is no approved causal incumbent yet. The gate
  therefore rejects publication even if baseline skill later appears. Manual
  review is required to establish one or change the evaluation window.
- Legacy export is disabled pending approval. Stored deployment assets are
  unchanged. Do not mix regenerated causal features with legacy model binaries.

## Limits

A two-quarter offset is a conservative release assumption, not a verified
historical availability calendar. GDP/indicators are latest revised values,
not vintage observations; release delays and later revisions remain unmeasured.
Latest source CSVs extend into 2026 Q2 and were not refreshed in this experiment.
GDP-unit provenance and all original source-series definitions still need an
independent audit. No interval calibration, multi-horizon validation, deployment
or live-data fetch was tested here. Legacy charts/screenshots are not evidence
for this evaluation. The historical Optuna notebooks remain experiments, not
part of the validated pipeline.

Repeated inspection of the post-2020 test set makes it an operational regression
window, not a forever-unseen scientific holdout. New research should reserve a
new untouched future period or collect prospective forecasts.

## Reproduce

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows: .venv\Scripts\activate
pip install -r requirements-test.txt
python -m unittest discover -s tests -v
python -m src.models.validation --output candidate_artifacts
python -m src.models.train_candidate --output candidate_artifacts
# Expected to fail with present results; never deploys anything:
python -m src.models.metric_gate --candidate candidate_artifacts/evaluation.json
```

For optional source ingestion, install `requirements.txt`, supply a FRED API key
through your own environment, run `src/data/fetch_all.py` and
`src/data/preprocess.py`, then rerun candidate evaluation. Never commit keys.
`src/data/build_features.py` regenerates research tables only; existing deployed
models cannot consume the changed schema. `candidate_artifacts/` is ignored by git.

## Structure

- `src/data/`: source ingestion, master tables, causal feature construction
- `src/models/validation.py`: origins, model selection, baselines, quality gate
- `src/models/train_candidate.py`: isolated full-history research fits
- `reports/`: reproducible rolling predictions and legacy comparison
- `tests/`: causal invariance, embargo, split, selection and gate regressions
- `frontend/`, `src/api/`, `models_saved/`: retained legacy deployment

Built by Yash Bajpai. See [LICENSE](LICENSE).
