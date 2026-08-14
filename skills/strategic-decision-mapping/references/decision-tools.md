# Decision tools

Use the least elaborate tool that changes the decision. State units, inputs, and uncertainty. Numbers clarify assumptions; they do not manufacture evidence.

## Payoff sketches

Use an ordinal scale such as `best / acceptable / bad / unacceptable` when cardinal utilities are unsupported. If using numbers, define what a one-unit difference means and whether interpersonal comparisons are intended.

For a two-player normal-form table, each cell contains both players' payoffs for one pair of simultaneous choices. Best responses and pure-strategy equilibria are conditional on that supplied table.

Do not force a sequential, multi-party, or information-asymmetric situation into a two-by-two matrix if the simplification changes likely responses.

## Expected value

For outcome values `v_i` and probabilities `p_i`:

`EV = sum(p_i * v_i)`

Use expected value only when probabilities and outcome values are comparable enough to support multiplication. Show downside distribution and constraints separately; a positive average does not make a catastrophic tail acceptable.

## Regret

Regret compares a chosen move with the best move after a state is known:

`regret(move, state) = best payoff in state - payoff(move, state)`

Minimax regret chooses the move with the smallest worst-case regret. It is useful when probabilities are weak but plausible states can be enumerated. It reflects a decision attitude, not a universal rule.

## Security level and maximin

The security level of a strategy is its worst payoff across the modeled opponent responses. Maximin chooses the highest security level.

Use it when protecting a floor is genuinely the objective. It can be too conservative when downside is reversible or learning has high value.

## Value of information

Information is valuable when it can change the chosen action before commitment.

Compare:

- the decision with current information;
- the decision after the proposed signal or experiment;
- the experiment's cost, delay, bias, and failure modes.

Do not count information that arrives after the irreversible decision or that nobody will act on.

## Reversibility and option value

Separate the cost of trying a move from the cost of becoming unable to change course. A pilot, staged contract, narrow launch, or expiry can preserve future choices while exposing real responses.

Option value rises with uncertainty and irreversibility, but waiting can destroy value through delay, learning by rivals, expiring windows, or eroding trust.

## BATNA and ZOPA

The BATNA is the best available outcome without agreement. The reservation point is the least favorable acceptable deal after accounting for that alternative. A ZOPA exists when reservation points overlap.

Estimate these independently for each side. Include time, execution risk, internal approval, and switching costs. Do not reveal a reservation point merely because the framework contains one.

## Credible commitments

A commitment changes behavior only when it is observable, within the actor's authority, costly or impossible to reverse, and rational to honor when tested.

Check enforcement, renegotiation, hidden escape routes, and whether the commitment transfers risk to an actor who can block implementation.

## Backward induction

For a sequential choice, start at the last meaningful decision and ask what that actor would choose. Work backward to earlier moves.

If later incentives make a threat or promise irrational, the earlier actor should discount it unless a commitment mechanism changes the future choice.

## Sensitivity and break-even analysis

Vary the few assumptions most capable of changing the ranking. Prefer break-even statements such as:

> Stage first unless the cost of delay exceeds X or the probability of response Y falls below Z.

Use ranges and scenarios when point estimates imply false precision. Report assumptions that do not matter as well as those that flip the answer.

## Dominance

A strategy is strictly dominated when another strategy produces a better payoff for every modeled response. Removing it is mechanically justified only if the action set and payoffs are credible.

Weak dominance is more fragile because ties and omitted considerations can matter. Treat it as a prompt for scrutiny rather than automatic elimination.
