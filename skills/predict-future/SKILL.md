---
name: predict-future
description: Produce evidence-grounded, scoreable probabilistic forecasts and technology trajectories with explicit resolution rules, current evidence, mechanisms, odds, update triggers, and decision implications. Use when the user asks what is likely to happen, requests probabilities or timelines, compares future paths, or wants monitored strategic signposts. Real-world forecasts require current retrieval. Includes deterministic helpers and an optional append-only Siftable ledger; does not require Siftable.
---

# Predict Future

Produce forecasts that are falsifiable, updateable, and useful for a decision. Treat forecasting as a pipeline with auditable seams, not as one eloquent answer.

Resolve every bundled path relative to this `SKILL.md`. The standard-library helper is `scripts/forecast.py`.

## Operating modes

- **QUICK:** one scoreable object, current retrieval, one estimate plus a sensitivity range. Never call this an ensemble.
- **STANDARD:** one to four scoreable objects, mechanism map, and at least three isolated forecasters when available. Reconcile only high-impact disagreements.
- **DEEP:** STANDARD plus multiple model families, an applicable external baseline, a held-out validated calibrator, persistent ledger, and scheduled review/resolution checks.

Infer the lightest mode appropriate to the stakes. Run capability preflight before promising the mode. Automatically downgrade when requirements are absent and state the limitations.

```bash
python3 scripts/forecast.py preflight \
  --requested standard \
  --retrieval-capability yes \
  --retrieval-completed no \
  --isolated-contexts 3 \
  --model-families 1
```

Run preflight once before research to establish available capability, then again before reporting with `--retrieval-completed yes`. `forecast_ready: false` means the workflow may continue but no probability may be issued yet.

## Keep the objects separate

- **Nowcast:** estimate of the current state.
- **Forecast:** probability distribution over a future observable outcome.
- **Trajectory:** linked sequence of scoreable milestones.
- **Scenario:** conditional pathway, not itself a probability.
- **Strategy:** action evaluated against forecasts and scenarios.
- **Forecaster disagreement:** spread among member outputs, not a confidence interval.
- **Evidence robustness:** directness, independence, and stability of decisive support, not probability.

## Governing rules

1. Establish an information cutoff.
2. Freeze the adjudication and resolution contract before research.
3. Search adaptively for unresolved mechanisms, priors, and disconfirming cases.
4. Use outside and inside views together.
5. Use simple statistical, physical, market, or human baselines when available.
6. Count a forecast member only when produced in an isolated context without other members' outputs.
7. Prefer diversity of model families, evidence paths, and non-LLM baselines over role-played personas.
8. Reconcile disagreement with new evidence or corrected facts, not persuasive prose.
9. Apply calibration only when validated on held-out forecasts from a relevant system, domain, horizon, and forecast type.
10. Never overwrite history. Every update is a new version with a probability and evidence delta.
11. Connect the forecast to actions only when the user has a decision.
12. Treat strategic forecasts as monitored signposts, not automatic build mandates.

# Workflow

## 0. Capture the decision and capabilities

Record:

- the user's reason for asking or actual decision;
- horizon, stakes, and reversibility;
- as-of date and information cutoff;
- fresh forecast or update;
- requested and effective mode;
- capability limitations from preflight.

For historical backtests, use only evidence available before the cutoff. Ordinary web retrieval may be temporally contaminated unless publication-time filtering is reliable.

## 1. Pass the forecast-object adjudication gate

Create a question specification before broad research. It needs:

- stable `question_id` and original wording;
- `forecast_type`: binary, categorical, numeric, or milestone;
- precise claim, metric, or mutually exclusive outcomes;
- resolution date or window end;
- frozen resolution rule and preferred/fallback sources;
- information cutoff;
- assumptions, exclusions, and void conditions;
- conditional or unconditional status;
- explicit interpretations for resolution-sensitive terms and rejected alternatives.

Show the user interpretations that could materially change the result. Terms such as “major,” “stable,” “standard,” “qualifying,” “receipt,” and “widely adopted” often need adjudication.

Run syntactic validation:

```bash
python3 scripts/forecast.py validate-question --input question_spec.json
```

The validator catches missing structure and likely ambiguity. It does not certify real-world scoreability; the forecaster and eventual resolver still own that judgment.

For broad technology questions, read `references/technology-trajectory.md`. In QUICK, keep one primary scoreable object and treat linked milestones as unforecasted monitoring signposts or separate future questions. Upgrade to STANDARD when the current run assigns probabilities to multiple milestone questions. Beyond a reliably resolvable horizon, switch to exploratory foresight: wide ranges, conditions, and signposts.

## 2. Build the mechanism and bottleneck map

Before collecting large amounts of evidence, identify:

- causal mechanisms and opposing drivers;
- high, medium, or low inertia;
- currently binding bottlenecks;
- decisive unknowns;
- observability and break conditions;
- leading, bottleneck, and falsifying indicators;
- linked forecast objects.

Do not call a driver “locked.” High inertia is not certainty.

### Optional strategic-interaction composition

When the outcome depends materially on identifiable actors adapting to one another—competition, standards, regulation, bargaining, coordination, signaling, or principal-agent behavior—read `references/strategic-interaction.md` and use its compact pass.

If the user is also making a consequential strategic decision, use `$strategic-decision-mapping` alongside this skill when it is installed. Its full decision map may include recommendations and a next turn; keep those in the decision-implications section rather than treating them as forecast evidence.

For forecast composition, extract only:

- actors and materially available moves;
- incentives, information asymmetries, power, and institutional constraints;
- likely adaptations and credible commitments;
- observable strategic signals and break conditions;
- behavioral departures from a rational-actor model.

`predict-future` retains ownership of probabilities, evidence, aggregation, resolution, and scoring. Never convert a payoff table or alleged equilibrium directly into odds. If no strategic decision exists or the related skill is unavailable, the compact lens is sufficient.

## 3. Retrieve and structure evidence

Search iteratively. Each query should target an unresolved mechanism, disputed fact, prior, or disconfirming case.

For each distinct evidence item record:

- evidence ID and concise observation;
- source, publication date, and observed window;
- observation versus source claim versus model inference;
- directness, reliability, incentives, independence, and timeliness;
- supporting, opposing, or ambiguous direction;
- affected mechanism and limitations.

“Primary” does not mean unbiased. Correlated sources do not become independent because several pages repeat the same origin.

Stop when decisive factual claims are cited, critical mechanisms are supported or labeled as inference, a serious bear case has been investigated, and additional retrieval mostly repeats known information.

## 4. Establish priors and non-LLM baselines

Use narrow, medium, and broad reference classes when useful. State selection rules, disanalogies, tipping conditions, and whether each class supports a numeric prior, a range, or only a causal lesson.

When numeric history exists, calculate a transparent baseline before narrative adjustment: last value, historical mean/base rate, trend, learning curve, diffusion curve, or an appropriate domain model. Show market prices, expert aggregates, and surveys separately unless held-out evidence supports a combination rule.

## 5. Generate separated forecasts

A member counts only if generated in a separate context without seeing other members' outputs. Each member returns a compact structured record:

- probability or distribution;
- prior/baseline;
- upward and downward adjustments;
- cited evidence IDs;
- decisive assumptions and top cruxes;
- strongest disconfirming evidence;
- update triggers;
- concise auditable rationale;
- model family and evidence-packet identifier.

Do not request or store private chain-of-thought. Preserve conclusions, evidence, assumptions, and adjustment summaries.

If isolated calls are unavailable, produce one estimate, contradiction check, and sensitivity range. Label it **single-model estimate**.

## 6. Aggregate, reconcile, and calibrate

Use the helper for binary or categorical mechanical aggregation:

```bash
python3 scripts/forecast.py aggregate --input members.json
```

Report member values, arithmetic mean, median, min–max disagreement, available trimmed mean, and represented diversity.

The supervisor then:

1. separates factual contradictions, prior differences, and causal disagreements;
2. ranks them by expected forecast impact;
3. retrieves or calculates against the highest-impact disputes;
4. changes the mechanical aggregate only when new evidence or a corrected fact justifies it;
5. preserves pre- and post-reconciliation values and explains the delta.

If a crux remains unresolved, retain the mechanical aggregate and expose it. Preserve raw, reconciled, and calibrated values separately. Report “not calibrated” when no relevant held-out calibrator exists.

## 7. Report

Read `references/report-template.md` and use its concise decisive-evidence table. Keep the visible table to the 4–8 items that most affect the judgment; retain the full evidence snapshot separately.

Re-run preflight before reporting. For real-world forecasts, stop before issuing odds unless it returns `forecast_ready: true`.

```bash
python3 scripts/forecast.py render-evidence --input evidence.json --limit 8
python3 scripts/forecast.py fingerprint
```

Store or display the content hash, effective mode, model identifiers, and information cutoff with every forecast version. The hash covers behavior-bearing skill content and intentionally excludes decorative assets and the legacy README.

Use exact probability language for forecasts and explicit if–then language for scenarios. Include normative backcasting only when the user asks for strategy, policy design, or a desired future.

## 8. Persist, update, resolve, and score

Persistence is optional. The skill works without Siftable.

For a personal Siftable ledger, read `references/ledger-schema.md`. Use one append-only dataset for v1. The helper defaults all create and append operations to dry-run:

```bash
python3 scripts/forecast.py ledger-contract
python3 scripts/forecast.py ledger-init
python3 scripts/forecast.py ledger-append --dataset-id DATASET_ID --input record.json
python3 scripts/forecast.py ledger-read --dataset-id DATASET_ID --question-id QUESTION_ID
```

Require explicit authorization before the first `ledger-init --execute` or any `ledger-append --execute`. Once the user intentionally enables persistence, store the dataset ID in `PREDICT_FUTURE_LEDGER_ID` or pass it explicitly. The helper only creates, adds, and queries; it exposes no update or delete operation.

When a review or resolution is executable work rather than data, use the host scheduler or `sift work`; dataset rows remain the forecast record, not a task queue.

Every update states the world delta, mechanism delta, previous and current values, reason for movement, and remaining crux. A scheduler—not this prompt—must invoke due reviews.

At resolution, read `references/evaluation.md` and score mechanically where supported:

```bash
python3 scripts/forecast.py score --input resolution.json
```

The helper supports binary Brier/log loss, categorical multiclass Brier/log loss, and numeric quantile pinball loss. Compare against relevant baselines. Do not call 0.25 a universal chance-level Brier score.

# Anti-patterns

- Ambiguous forecast object researched before adjudication.
- Same-context estimates labeled an ensemble.
- Role prompts treated as meaningful model diversity.
- Fixed search counts used as rigor.
- Exact base rates forced from tiny or selected analogue classes.
- Supervisor choosing persuasive prose without new evidence.
- Unvalidated calibration transforms.
- Forecaster spread described as a confidence interval.
- Strategic actors modeled as perfectly rational by default.
- Payoff matrices or equilibria converted directly into probabilities.
- Scenarios presented as probability buckets.
- Previous forecasts overwritten.
- Siftable writes performed merely because the CLI is available.
- Forecasts treated as automatic product or investment mandates.
- Long-range precision attached to an unstable resolution concept.

# Boundary

The helper performs deterministic validation, preflight, aggregation, hashing, evidence rendering, scoring, and opt-in ledger I/O. It does not perform research, causal judgment, forecasting, reconciliation, calibration, scheduling, or adjudication. Keep those claims honest in every report.
