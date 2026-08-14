# Forecast Report Template

```text
FORECAST · [question]
As of: [date and information cutoff]
Mode: [requested → effective]
Skill hash: [sha256]
Evidence robustness: [HIGH / MEDIUM / LOW — one-sentence reason]

CAPABILITY PREFLIGHT
Retrieval: [capability; completed; forecast_ready]
Isolation and model diversity: [contexts; model families]
External baseline: [status]
Calibration: [validated calibrator or “not calibrated”]
Ledger and scheduler: [status]
Limitations: [only decision-relevant limitations]

EXECUTIVE JUDGMENT
[Direct answer in 2–5 sentences.]

SCOREABLE FORECASTS
F1 [claim / outcome / metric]
   Forecast: [raw mechanical aggregate]
   Reconciled: [value and evidence-backed delta, or unchanged]
   Calibrated: [value, or “not calibrated”]
   Disagreement: [member range; explicitly not a CI]
   Resolves: [date, frozen rule, source]
   Prior/baseline: [reference class, statistical model, market, or human aggregate]
   Crux: [most probability-sensitive uncertainty]

F2 ...

DECISIVE EVIDENCE
| ID | Observation | Direction | Mechanism | Limitation | Source |
|---|---|---|---|---|---|
| E1 | ... | support / oppose / ambiguous | ... | ... | ... |
[Show 4–8 rows. Keep the full evidence snapshot outside the visible report.]

TRAJECTORY
Capability → reliability → economics → scale → adoption → institutionalization
[Current state and forecast at each relevant milestone.]

MECHANISMS AND HIGH-INERTIA DRIVERS
D1 [driver] — [mechanism]
   Break condition: [observable condition]
D2 ...

STRATEGIC INTERACTION — only when actor adaptation is material
Actors and moves: [...]
Incentives, power, information, and institutions: [...]
Likely adaptations: [...]
Behavioral corrections: [...]
Observable strategic signals: [...]
[Do not present a game-theory result as a probability.]

CAUSAL FRICTION
[Opposing drivers and which currently dominates.]

CRITICAL BOTTLENECK
[Currently binding constraint; not necessarily the only determinant.]

SIGNPOSTS AND TRIPWIRES
LEADING: [indicator and threshold]
BOTTLENECK: [indicator and threshold]
FALSIFIER: [indicator and threshold]

SCENARIOS — only when useful
BASE CASE: If [conditions], then [coherent path].
ACCELERATION: If [conditions], then [coherent path].
STALL / REVERSAL: If [conditions], then [coherent path].

DECISION IMPLICATIONS — only when a decision exists
Robust action: [works across top scenarios]
Reversible option: [preserves upside while limiting lock-in]
Defer until: [signpost or information threshold]
Highest-value unknown: [question worth resolving next]

BLIND SPOTS
[Missing evidence, inaccessible data, unstable definition, or unresolved mechanism.]

WHAT CHANGED — only for updates
Previous: [x on date] → Current: [y]
World delta: [new facts]
Mechanism delta: [driver, strategic response, or bottleneck change]
Reason for move: [evidence IDs]
Still unresolved: [crux]
```

## Report rules

- Forecasts are probabilities; scenarios are conditional paths.
- Evidence robustness is not the probability of the outcome.
- Forecaster spread is disagreement, not a confidence interval.
- Preserve raw, reconciled, and calibrated values separately.
- Include a preferred future only when the user requests strategy or backcasting.
- Keep the executive report concise; preserve audit detail in the evidence snapshot or ledger.

## Evidence-robustness language

- **HIGH:** decisive mechanisms are measured directly, independently corroborated, and stable enough for the horizon.
- **MEDIUM:** useful evidence exists, but an important adjustment relies on inference, disputed measurement, or a weak reference class.
- **LOW:** the forecast turns on inaccessible data, an unstable resolution concept, or several unresolved causal cruxes.
