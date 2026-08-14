---
name: strategic-decision-mapping
description: Map consequential decisions as actors, incentives, moves, countermoves, commitments, information, and timing. Use for negotiations, partnerships, product or company bets, organizational conflicts, competitive responses, escalation risks, strategic forks, game-theory questions, next-move recommendations, or choices where the best action depends on how other people will respond.
---

# Strategic Decision Mapping

Turn a strategic question into an explicit model of interaction and a usable next move. Treat game theory as a mechanism lens, not a prediction engine. Most real decisions are only partly specified, shaped by power, institutions, relationships, bounded rationality, and events outside the model.

## Frame the decision

State one decision in the decision-maker's control:

- the move or commitment being considered;
- the decision deadline and relevant time horizon;
- the objective, constraints, and unacceptable outcomes;
- what is reversible, costly to reverse, or irreversible;
- what happens if nobody acts.

Ask a forcing question only when the missing answer could reverse the recommendation. Otherwise proceed with a labeled assumption.

## Separate evidence from the model

Create four buckets before reasoning:

1. **Observed:** directly supported by current evidence.
2. **Reported:** asserted by an actor or source but not independently established.
3. **Assumed:** needed to construct the model.
4. **Unknown:** material uncertainty that remains unresolved.

Use current repository, document, market, or web evidence when the question depends on changing facts. Cite evidence close to the claim. Do not mistake an actor's statement of intent for an incentive-compatible commitment.

## Map the actors

For every actor who can materially change the outcome, record:

- objective and likely priority order;
- available moves and authority;
- constraints, dependencies, and vetoes;
- outside option and cost of delay;
- information they possess or lack;
- relationship, reputation, and repeated-game exposure;
- likely response to each serious move.

Include coalitions and implementers when they have different incentives from formal decision-makers. Do not collapse a company, team, customer, or government into one rational actor when internal agency problems matter.

## Generate the move set

Include at least three materially different choices when credible:

- act or commit now;
- stage, test, narrow, or condition the move;
- wait, gather information, or preserve the status quo;
- change the rules, sequence, audience, or coalition;
- exit or use the outside option.

Remove impossible moves, not merely unattractive ones. Keep a move if its value comes from information, option preservation, signaling, or changing another actor's incentives.

## Model interaction

Read `references/game-shapes.md` to select only the interaction patterns that fit. Then test:

1. What is each actor's best response to each serious move?
2. Which threats, promises, and signals are credible given later incentives?
3. Does the sequence create first-mover, second-mover, or waiting value?
4. What changes under repetition, reputation, coalition formation, or private information?
5. Can the decision-maker improve the game by changing payoffs, information, timing, participation, or reversibility?

When explicit two-player payoffs are useful, keep the scale ordinal unless the inputs support cardinal utility. Use `scripts/analyze_game.py` to identify pure-strategy best responses, strictly dominated strategies, security strategies, and minimax-regret strategies. The script analyzes the supplied table; it does not validate the payoffs or solve an incompletely specified real-world game.

## Compare robustly

Read `references/decision-tools.md` before using expected value, regret, value of information, BATNA/ZOPA, commitments, or sensitivity analysis.

Prefer a move that:

- performs acceptably across plausible responses;
- limits irreversible downside;
- preserves or creates options;
- produces useful information;
- is executable by a named owner;
- improves future bargaining or coordination rather than only today's score.

Show what would flip the ranking. Do not hide disputed assumptions inside a single weighted score.

## Recommend a next turn

Classify the conclusion:

- **Robust move:** survives the important plausible responses and assumptions.
- **Contingent move:** best only if a named condition holds; pair it with a trigger.
- **Judgment call:** viable paths express different values or risk preferences.
- **Challenge:** the favored move is dominated, relies on a noncredible response, or ignores a stronger outside option.

Name the immediate move, owner, timing, observable response, stop condition, and next decision point. Prefer a staged move when it can cheaply reveal the game before a larger commitment.

Use `references/decision-map-format.md` for the final output. Keep the payoff sketch legible and proportional to the evidence.

## Guardrails

- Do not claim a Nash equilibrium unless strategies, payoffs, and response rules are specified well enough to support it.
- Do not turn a payoff table into an empirical probability forecast.
- Do not assume rationality erases power, identity, ethics, inertia, mistakes, or institutional constraints.
- Do not recommend deceptive signaling, coercion, collusion, or evasion of legal or fiduciary duties.
- Do not optimize the modeled metric at the expense of an explicit unacceptable outcome.
- Label conclusions as analysis, not observed fact, when live evidence is unavailable.
