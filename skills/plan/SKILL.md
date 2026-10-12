---
name: plan
description: "Produce a visual, grounded plan for an objective. Use when the user asks to \"plan\", \"plan out my week / day / sprint\", \"sequence\", \"prioritize\", \"schedule\", \"what should I do first\", \"map out\", \"break down\", \"de-risk\", or \"show a diagrammed plan\" of work. Grounds the plan in the repository and authorized context, tasks, and work queue and renders it as a Mermaid flowchart. Read-only: it plans, it does not execute."
metadata:
  author: siftable
---

# Plan — visual, grounded, read-only

Treat this file as executable instructions. Your job is to turn an objective into
a **plan the user can see**: a short decision-grade summary, a rendered Mermaid
graph of the work, and an auditable breakdown. You are in **read-only planning
mode** — inspect and propose; never edit files, mutate tasks, claim work items,
send messages, or run destructive commands. End at a review boundary.

If an available work tracker has a deterministic dependency-graph command, prefer it for the actual queue graph. This skill also covers weekly plans, project plans, implementation plans, and mixed objectives; a queue integration is optional.

## Ground every plan in relevant authorized context

Before sequencing anything, inspect only lanes relevant and available for this task:

```mermaid
flowchart TD
  U[User Request] --> A[Planning Assistant]
  A --> LC[Local Codebase]
  A --> ST[Project Tasks]
  A --> NC[Authorized Context]
  A --> AQ[Agent Queue]
```

For each lane ask: what's relevant, what's blocked, what's in flight, what has a
deadline, what unlocks downstream work, what needs *me* vs what an agent can
take? Pull context with read-only tools where you have them — list tasks, list
work items, read the calendar, search notes/CRM, inspect repo state. Cite what
you used; do not dump raw tool output into the plan.

## What to produce (every time)

**1. A plan card** — 4-6 lines, decision-grade:

```text
◇ plan · proposed
Objective: <restate>
Main move: <the one recommendation>
Critical path: <the chain that gates completion>
Biggest uncertainty: <what to frame before committing>
Execution boundary: <existing authority and any new action needing approval>
```

**2. A Mermaid flowchart** in a fenced ` ```mermaid ` block — **just write the
block**. Some hosts render it inline; check the actual renderer rather than promising automatic display. The diagram source is usable even when no renderer is exposed. Model the *dependency structure*, not a generic org chart: nodes are
tasks/decisions/reviews; edges are "blocks / unlocks / must precede".

**3. A structured plan** with these sections, in order:

```text
Assumptions
Context used        (per lane: Local Codebase / Project Tasks / Authorized Context / Agent Queue)
Suggested sequence  (numbered; hard dependencies first, then deadlines, then unlock count)
Parallelism         (what can run at once; what shares scope and must serialize)
Critical path       (the chain that determines finish time)
Risks / uncertainty (and "frame before committing" items — scope these first)
Execution gates     (what must be approved before any mutation)
Verification        (how you'll know the plan worked)
```

If durations are unknown, say so — "forecast unavailable: no estimates" — rather
than inventing precision.

## Portable Mermaid rules

Use `flowchart TD` (top-down) for dependency plans; `LR` only for small maps.
Node shapes — **ONLY these four**: `[rect]`, `(rounded)`, `((circle))`,
`{decision}`. Edges: `-->`, `-->|label|`. Keep labels short (a few words; there
is no wrapping). **NEVER** use `subgraph`, `style`, `classDef`, `:::class`,
`click`, `<br/>`, `A & B`, exotic shapes (`([])` `[()]` `{{}}` `[[]]`), a
`--- title ---` block, or `end` as a node id. See the `mermaid` skill for the
portable subset. Validate a tricky diagram through an already available renderer when possible. If no renderer exists, provide the source and label rendering as unverified; do not install one implicitly.

A weekly / mixed plan looks like this (example):

```mermaid
flowchart TD
  O[Plan the week] --> G[Ground context]
  G --> T[Project Tasks]
  G --> Q[Agent Queue]
  G --> C[Calendar & CRM]
  T --> F[Frame uncertain work]
  Q --> R[Run ready agent work]
  C --> P[Protect focus blocks]
  F --> D[Do first-pass design]
  D --> B[Build]
  B --> V{Verify}
  V -->|pass| S[Ship]
  V -->|fail| B
  R --> V
  P --> V
```

A pure dependency / sequencing plan (example):

```mermaid
flowchart TD
  A[Scope spike] --> B[Design]
  B --> C[Implement core]
  C --> D[Tests]
  C --> E[Docs]
  D --> F{Review}
  E --> F
  F -->|approve| G[Land]
  F -->|changes| C
```

## Workflow

1. Restate the objective and classify it (week / project / implementation /
   queue / mixed).
2. Ground in relevant available lanes with read-only reads; note missing capabilities.
3. Build the dependency graph in your head, then write it as `flowchart TD`.
4. If the graph has more than ~5 nodes or you're unsure of syntax, validate it
   once through an available renderer and fix parser errors before presenting. If a renderer is unavailable, report that limit without inventing a render pass.
5. Emit the plan card, the ```mermaid block, and the structured plan.
6. Stop at the review boundary — propose execution gates; do not execute.
