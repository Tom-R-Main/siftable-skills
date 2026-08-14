# Forecast Evaluation Reference

## Proper scores by forecast type

- **Binary:** Brier score; optionally log score.
- **Categorical:** multiclass Brier; ranked probability score when outcomes are ordered.
- **Numeric distribution:** interval score, pinball loss, or CRPS.
- **Milestone trajectory:** score each milestone independently and analyze dependency errors separately.

## Baselines

Compare against the baseline appropriate to the question:

- unconditional empirical base rate;
- 50/50 only when it is genuinely the no-information binary baseline;
- last value or naive trend;
- simple statistical or physical model;
- prediction market or expert aggregate;
- previous system version;
- single model without search;
- single model without ensembling.

A Brier score of 0.25 is the result of issuing 50% on a binary question, not a universal chance-level score for every dataset.

## Diagnostics

Track:

- mean proper score and skill relative to baseline;
- calibration by probability range with counts and uncertainty;
- discrimination or resolution, not calibration alone;
- score by domain, horizon, forecast type, and evidence regime;
- raw versus reconciled versus calibrated performance;
- incremental value of search, model diversity, market data, and supervisor reconciliation;
- miss clusters by driver, source type, or unresolved crux;
- stability and usefulness of updates;
- question and resolution quality.

Do not draw strong calibration conclusions from tiny buckets.

## Leakage control

Prefer live, unresolved questions. For backtests:

- freeze the information cutoff;
- archive the evidence snapshot;
- prevent post-resolution snippets, pages, and model memories from entering the run;
- record uncertainty about retrieval-time filtering;
- do not compare a historically blinded model with a market price that contains later information.

Preserve every issued forecast to avoid cherry-picking.

## Calibration policy

- Calibrate the actual production pipeline, not a generic model name.
- Segment only where sample size supports it.
- Fit on past data; evaluate on held-out or forward data.
- Compare raw and calibrated scores.
- Do not transfer a calibrator across domains or horizons without validation.
- Store calibrator version and training window.

## Iteration order before fine-tuning

1. Improve question and resolution specifications.
2. Improve retrieval quality, freshness, and source diversity.
3. Improve mechanism decomposition and statistical baselines.
4. Increase genuine ensemble diversity.
5. Improve disagreement-focused supervisor search.
6. Fit and validate post-hoc calibration.
7. Consider fine-tuning or outcome-based training only after a sufficiently large, leakage-controlled ledger exists.
