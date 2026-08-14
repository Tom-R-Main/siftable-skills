# Technology Trajectory Reference

Use this reference when the user asks where a technology is going, when it will matter, what will win, or whether it will displace an incumbent system.

## Decompose broad questions into milestones

Forecast the path rather than one vague endpoint:

1. **Capability** — credible task performance under reproducible evaluation.
2. **Reliability** — repeated performance under real operating conditions, including failure modes.
3. **Economics** — unit cost, total cost of ownership, and cost-performance threshold.
4. **Scale** — supply, compute, energy, materials, manufacturing yield, staffing, and operations.
5. **Integration** — workflow fit, interoperability, switching costs, security, and complement availability.
6. **Adoption** — paid deployment, retention, expansion, procurement, and substitution behavior.
7. **Institutionalization** — standards, regulation, insurance, liability, social license, and durable organizational change.

Create separate scoreable forecasts for the milestones that can fail independently. Do not multiply subjective milestone probabilities mechanically; dependencies are rarely independent.

## Mechanism channels

Inspect the channels that are causally relevant:

- scientific feasibility and unresolved theory;
- benchmark progress and replication quality;
- reliability, latency, efficiency, yield, and safety;
- learning curves and cost decline;
- compute, power, materials, fabrication, and supply-chain constraints;
- complementary infrastructure and standards;
- APIs, open source, developer activity, and distribution;
- integration burden and switching costs;
- customer usage, retention, willingness to pay, and budget ownership;
- procurement, pilots, production deployments, and contract expansion;
- patents, standards proposals, certification, and regulatory filings;
- hiring, compensation, team formation, and research migration;
- capex, capacity reservations, equipment orders, and supplier revenue;
- incumbent response, bundling, price competition, and substitutes;
- national policy, export controls, security, and geopolitical concentration.

## Signal maturity

Classify evidence by where it sits in the innovation chain:

- **research signal** — paper, theorem, benchmark, negative result;
- **prototype signal** — lab or demo capability;
- **product signal** — purchasable or deployable offering;
- **usage signal** — real users and recurring workflow;
- **economic signal** — viable price, margin, or total cost;
- **scale signal** — repeatable volume and operational capacity;
- **institutional signal** — standards, regulation, procurement, insurance, or organizational redesign.

A large quantity of early-stage signals does not substitute for a missing downstream signal. Explicitly identify stage gaps.

## Leading versus lagging indicators

Prefer indicators that precede adoption rather than merely celebrate it.

Potential leading indicators:

- cost-performance crossing a customer threshold;
- reliability on long-horizon or adversarial evaluations;
- supplier orders and capacity commitments;
- standards convergence;
- integration time and failure-rate reduction;
- paid pilot conversion and cohort retention;
- developer migration and complement formation;
- procurement language and budget reallocation;
- insurer, auditor, or regulator acceptance.

Common lagging or noisy indicators:

- press volume;
- undifferentiated funding totals;
- raw patent counts;
- benchmark claims without replication;
- demo virality;
- vendor-reported users without activity or retention definitions.

## Reference-class dimensions

Compare analogues on:

- capital intensity;
- novelty of underlying science;
- complement dependence;
- regulatory burden;
- network effects;
- switching costs;
- incumbent distribution power;
- production learning curve;
- safety and liability exposure;
- prototype-to-scale timeline.

Always list the strongest disanalogy. A good story is not automatically a good reference class.

## Recommended trajectory output

```text
CURRENT STAGE
[research / prototype / product / usage / economics / scale / institution]

MILESTONE FORECASTS
M1 Capability threshold by [date]: [probability or quantiles]
M2 Reliability/economic threshold by [date]: [probability or quantiles]
M3 Material deployment by [date]: [probability]
M4 Mainstream or institutional adoption by [date]: [probability]

BOTTLENECK
[Currently binding constraint]

STAGE GAP
[Downstream evidence that is still absent]

LEADING SIGNPOST
[Indicator, threshold, and expected date]

FALSIFIER
[Observation that would materially lower the trajectory]
```
