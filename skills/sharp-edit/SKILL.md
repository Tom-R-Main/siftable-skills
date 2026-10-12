---
name: sharp-edit
description: >
  Edit existing business writing or turn supplied business material into concise,
  decision-ready prose while preserving facts, certainty, intent, and voice. Use
  for explicit requests to edit, tighten, sharpen, shorten, rewrite, restructure,
  or memoize emails, reports, proposals, executive summaries, decision documents,
  and slide copy. Do not use for deal diagnosis, buyer strategy, objection handling,
  or deciding what a sales motion should say; use sales-deal-strategy first. Use
  human-writing instead for general voice matching or non-business prose.
---

# Sharp Edit

Produce writing that sounds like a sharp, credible person with firsthand knowledge of the subject.

Preserve the writer’s meaning, judgment, personality, and relationship with the reader. Remove anything that feels generated, performative, inflated, generic, overproduced, or unnecessarily formal.

The goal is not polished writing for its own sake. The goal is to help the reader understand, decide, or act.

# Instruction priority

Follow the user’s explicit instructions on meaning, tone, audience, format, length, and degree of revision. These override the skill’s defaults.

Preserve factual meaning, certainty, scope, chronology, causality, commitments, names, numbers, quotations, and attribution.

Do not strengthen, soften, broaden, or narrow a claim merely to improve its style.

Preserve the source format unless restructuring clearly improves usability or the user requests another format.

# Routing and composition

Use this skill as an editorial layer, not a source of domain evidence or strategy.

- For sales material that requires deal diagnosis, buyer strategy, objection handling, evidence selection, or a recommended next move, use `$sales-deal-strategy` first. Apply Sharp Edit only after the strategy and factual claims are settled.
- For settled sales copy that only needs tightening, restructuring, or tone control, use Sharp Edit directly. Do not query the sales corpus unless the user also asks to reconsider the substance.
- For general voice matching, personal writing, creative prose, essays, or non-business material, use `$human-writing` instead.
- Preserve the upstream skill's selected claims, numbers, certainty, audience, and call to action as immutable unless the user explicitly asks to change them.

# 1. Select the mode

## EDIT MODE

Use when the user provides existing writing and wants it improved.

Examples:

- Edit this
- Tighten this
- Clean this up
- Make this sharper
- Review this email
- What would you cut?
- This feels too long
- Edit this memo

The content already exists. Improve it without changing its essential meaning.

## MEMO MODE

Use when the user wants content written or reorganized as a memo.

Examples:

- Write a memo on this
- Draft a memo
- Turn these notes into a memo
- Structure this as a memo
- Help me write this up

The source may be raw notes, fragmented ideas, a wall of text, or no draft at all. Distill the content, exercise judgment, and produce a decision-ready memo.

“Edit this memo” is EDIT MODE.

“Turn this into a memo” is MEMO MODE.

# 2. Select the editing intensity

Infer the appropriate level of intervention from the request.

## LIGHT EDIT

Correct grammar, spelling, punctuation, and obvious awkwardness. Preserve the wording and structure wherever possible.

Typical requests:

- Proofread this
- Check the grammar
- Any errors?
- Light edit

## STANDARD EDIT

Tighten language, improve sequence, remove filler, clarify meaning, and sharpen the ask while preserving the writer’s structure and voice.

Typical requests:

- Edit this
- Tighten this
- Clean this up
- Make this sharper

Use STANDARD EDIT when the requested intensity is unclear.

## HEAVY EDIT

Rebuild the writing for clarity, brevity, logic, and impact while preserving its facts, intent, point of view, and essential tone.

Typical requests:

- Rewrite this
- This is a mess
- Make this much better
- Rework this completely

Do not perform a heavy rewrite when the user asks only for proofreading or a light edit.

# Core editing standard

For every sentence, ask:

1. What does this tell the reader?
2. Does the reader need it?
3. Is it concrete enough to understand or act on?
4. Is there a shorter or clearer way to say it?
5. Does it sound like this writer or like generic generated prose?

Cut, combine, or rewrite anything that fails.

Do not rewrite merely to make the language different.

# Preserve

Preserve the writer’s:

- Meaning and point of view
- Facts, numbers, names, dates, quotations, and attribution
- Level of certainty and commitment
- Material nuance and qualifications
- Intended tone
- Relationship with the reader
- Specific ask
- Useful personality

Match the writer’s natural:

- Directness
- Warmth
- Formality
- Sentence rhythm
- Use of contractions
- Bluntness
- Humor
- Enthusiasm
- Vocabulary

Do not normalize every writer into one executive house style.

The final version should sound like this writer with better judgment and control, not like a generic executive communications team.

Do not flatten distinctive language merely because a more conventional phrase is available.

Leave strong writing alone.

# Priorities

In order:

1. Correct meaning
2. Clear point
3. Reader relevance
4. Specific action or decision
5. Logical flow
6. Brevity
7. Natural voice
8. Polish

Never sacrifice meaning, necessary context, or voice simply to make the writing shorter.

# Edit proportionately

Brevity is not the goal by itself.

Retain context that affects:

- Meaning
- Trust
- Emotional tone
- Credibility
- Interpretation
- The reader’s ability to act

Be especially careful not to overcompress:

- Apologies
- Rejections
- Sensitive feedback
- Escalations
- Bad news
- Requests for help
- Relationship-driven messages

Cut accidental repetition.

Keep deliberate repetition when it improves emphasis, comprehension, sincerity, navigation, or actionability.

# Human executive voice

Write like an informed executive speaking plainly to another capable adult.

The voice should be:

- Direct, not abrupt
- Confident, not theatrical
- Specific, not exhaustive
- Conversational, not casual
- Candid, not needlessly diplomatic
- Concise, not skeletal
- Polished, not conspicuously polished

Use natural sentence variation. Mix short sentences with longer ones when the thought requires it.

Do not make every sentence, paragraph, or bullet structurally parallel.

Use contractions when they fit the writer and the surface.

Allow mild asymmetry, emphasis, informality, and personality. Human writing does not need every idea packaged into a balanced framework.

Match the relationship, not only the reader’s title.

A note to a close colleague may be candid and compressed. A customer escalation may require greater ownership and context. A board memo may require more evidence and formality.

Write for the actual interaction, not an abstract category called “executive communication.”

# Reader orientation

Organize the writing around what the reader needs to understand, decide, or do.

Ask:

- What does the reader need to know first?
- What decision are they making?
- What question or concern are they likely to have?
- What action do they need to take?
- What context do they need to act confidently?
- What can they safely skip?

Do not organize the writing around the order in which the writer thought of the information.

# The I:you principle

In reader-facing writing, watch the balance between writer-centered and reader-centered language.

Writer-centered language focuses on:

- What I wanted to share
- What we are excited about
- What our company has built
- What I need from you
- What we believe is important

Reader-centered language focuses on:

- What the reader needs
- What changes for them
- What question is being answered
- What action is required
- What benefit, risk, or consequence matters to them

Weak:

> I wanted to share an update on the work we have been doing to improve the reporting process.

Stronger:

> Starting next month, your team will receive one consolidated report instead of three separate files.

Weak:

> We are excited to offer a new feature that allows users to create reports more efficiently.

Stronger:

> You can now create the report without exporting data or rebuilding the analysis in Excel.

Do not force “you” or “your” into every sentence.

Reader orientation is a structural principle, not a pronoun quota.

Use “I” and “we” when they serve a real purpose, including:

- Accepting responsibility
- Making a commitment
- Stating a recommendation or judgment
- Explaining what the writer or organization will do
- Expressing sincere appreciation, apology, or conviction
- Clarifying ownership

Good:

> We told you the issue was fixed before testing was complete. That was our mistake.

Good:

> I recommend approving the pilot for one market.

Cut “I” or “we” when it merely delays the point.

Weak:

> I wanted to ask if you could send the revised agreement by Friday.

Stronger:

> Could you send the revised agreement by Friday?

The goal is not to remove the writer. It is to keep the reader’s needs and next action at the center.

# Inverted-pyramid structure

Organize business writing in descending order of importance.

The reader should encounter:

1. The conclusion, decision, ask, or material change
2. Why it matters
3. The essential context needed to interpret it
4. Supporting evidence and analysis
5. Secondary detail, history, and reference material

Do not make the reader follow the writer’s chronology to discover the point.

Weak sequence:

1. Background
2. Process history
3. Meetings held
4. Analysis performed
5. Recommendation

Stronger sequence:

1. Recommendation
2. Core rationale
3. Main risk or tradeoff
4. Relevant background
5. Supporting analysis

Apply the inverted pyramid at every level:

- The document
- Each section
- Each paragraph
- Each email
- Each slide

A paragraph should usually begin with its main point.

A section heading should communicate its conclusion when possible.

A slide title should state the takeaway rather than merely name the topic.

Do not withhold critical information for dramatic effect. Business writing is not a mystery story.

# Concrete writing rules

## Lead with the point

Put the conclusion, request, decision, problem, or important update early.

Do not begin with:

- Generic context
- Polite throat-clearing
- A summary of what the document will cover
- Broad observations about the market or world
- Background the reader already knows

## Name actors and actions

Prefer:

- Who did what
- Who needs to do what
- What changes
- Why it matters
- What happens next

Avoid hiding agency behind passive voice, nominalizations, or “stakeholders.”

Weak:

> Expectations were not clearly communicated.

Strong:

> We told the client the fix was permanent before engineering had finished testing it.

## Show the mechanism

Do not claim that something improves alignment, efficiency, engagement, visibility, decision-making, or outcomes without explaining how.

Weak:

> The platform improves collaboration and drives better decisions.

Strong:

> The platform gives sales and customer success one account record, so they stop working from conflicting spreadsheets.

## Prefer plain verbs

Prefer:

- use
- help
- show
- build
- cut
- fix
- improve
- start
- stop
- decide
- send
- review
- change

Use words such as “leverage,” “facilitate,” “enable,” “optimize,” or “operationalize” only when they are genuinely more precise.

## Replace abstractions with observable facts

Weak:

> We need stronger cross-functional alignment.

Strong:

> Product and sales need to agree on the launch date and customer promise before marketing announces it.

Weak:

> This creates meaningful value.

Strong:

> This removes roughly five hours of manual account research from each rep’s week.

## Make asks executable

When relevant, specify:

- Action
- Owner
- Deadline
- Decision required
- Deliverable

Do not invent missing details.

Use only what the user provided or what can safely be inferred.

# Preserve epistemic accuracy

Do not turn:

- An estimate into a fact
- A possibility into a plan
- A plan into a commitment
- A correlation into a cause
- An individual example into a broad conclusion
- A proposed action into an approved action
- A partial result into a complete result
- A likely explanation into a confirmed root cause

Every specific fact, example, number, causal claim, quotation, and attribution must come from the source material or clearly established context.

Do not manufacture authority, certainty, or precision.

# Handle ambiguity carefully

Resolve minor ambiguity from context when the intended meaning is clear.

If ambiguity could materially change the message, do not guess.

Preserve the original meaning as closely as possible or flag the issue briefly.

Do not interrupt a straightforward editing task with unnecessary clarification questions.

# What to cut or rewrite

## Empty setup

Remove phrases such as:

- I wanted to reach out
- I am writing to
- It is important to note
- It is worth mentioning
- There are several factors to consider
- To better understand this
- With that context in mind
- As you may know
- In today’s rapidly evolving environment

Start with the substance.

## Redundancy

Cut:

- Repeated ideas
- Sentences that paraphrase the previous sentence
- Redundant pairs
- Lists whose items substantially overlap
- Conclusions that merely restate the introduction

Examples:

- review and assess
- each and every
- future plans
- collaborate together
- efficient and effective
- clear and transparent, when one will do

## Unsupported adjectives and adverbs

Question words such as:

- meaningful
- thoughtful
- strategic
- significant
- compelling
- robust
- seamless
- transformative
- holistic
- actionable
- impactful
- effectively
- successfully
- proactively

Replace them with evidence or remove them.

## Unnecessary hedging

Cut hedges that do not reflect real uncertainty:

- somewhat
- potentially
- may possibly
- in many cases
- generally speaking
- arguably
- to some extent

Keep uncertainty where it matters.

Distinguish fact, assumption, and judgment rather than pretending certainty.

## Inflated framing

Do not turn routine events into:

- Transformations
- Journeys
- Milestones
- Paradigm shifts
- Defining moments
- Fundamental reimaginings
- Tests of leadership
- Broader reflections on the future

Match the language to the actual stakes.

## Generic corporate language

Avoid or rewrite phrases such as:

- unlock value
- drive impact
- elevate the conversation
- navigate complexity
- evolving landscape
- data-driven decisions
- actionable insights
- scalable foundation
- sustainable growth
- best-in-class
- move the needle
- meet customers where they are
- position us for success
- foster collaboration
- accelerate strategic priorities
- human-centered approach
- people are at the heart of everything we do

Use the actual action, result, mechanism, or tradeoff.

# LLM writing patterns to avoid

The patterns below are warnings, not absolute bans.

Do not use them mechanically or as default rhetorical devices.

Keep one only when it is natural to the writer, carries specific meaning, and clearly improves the sentence.

The broader rule:

> Do not manufacture polish, symmetry, profundity, warmth, balance, or completeness.

## Manufactured contrast

Avoid:

- Not just X, but Y
- It is not X. It is Y.
- More than X
- Less about X and more about Y
- The question is not whether, but how
- This is not merely a technology issue; it is a people issue

State the actual distinction directly.

## Artificial punchiness

Avoid repeated constructions such as:

- The result?
- The challenge?
- The opportunity?
- The bottom line?
- Simple.
- Think again.
- That changes everything.

A rhetorical fragment may remain if it is natural to the writer, but do not use it as a default style.

## Polished symmetry

Do not manufacture:

- Three-part lists
- Perfectly parallel clauses
- Equal-length sections
- Matching sentence structures
- Three adjectives where one fact would be stronger

Use three items only when there are genuinely three distinct items.

## Excessive signposting

Avoid announcing the structure:

- Let’s break this down
- Here is what you need to know
- There are three key reasons
- Let’s take a closer look
- The key takeaway is
- In summary
- In conclusion

Deliver the point instead.

## Fake insight

Cut sentences that sound wise but are difficult to disagree with:

- At its core, leadership is about people.
- Technology is only as powerful as the people using it.
- Change is inevitable.
- True innovation begins with curiosity.
- The future belongs to those willing to adapt.

Replace them with a specific judgment or delete them.

## Empty causal chains

Do not assume:

> Visibility improves decisions, which improves execution and drives outcomes.

Explain the actual mechanism and evidence.

## Benefit stacking

Do not attach several downstream benefits to one feature unless each is supported.

## False balance

Do not give every side equal weight merely to sound measured.

Identify:

- The main issue
- The strongest evidence
- The best option
- The decisive tradeoff

## Excessive completeness

Do not answer every adjacent question or create a framework merely because one is possible.

Include what helps this reader understand or decide.

## Generic reassurance

Avoid:

- The good news is
- This does not have to be overwhelming
- With the right approach
- Start small
- Progress over perfection

Use reassurance only when the reader has expressed concern and reassurance helps.

## Formulaic empathy

Avoid automatic validation such as:

- That is a great question
- I completely understand
- You are absolutely right
- I appreciate you sharing this

Respond to the substance.

## Sanitized disagreement

Do not obscure a clear judgment with excessive diplomacy.

Weak:

> This approach may present certain challenges.

Strong:

> This approach creates more work than it removes.

## Moral bow-tying

Do not end practical writing with a generic statement about responsibility, empathy, innovation, trust, or the future unless it materially advances the point.

## Faux authority

Do not write:

- Research shows
- Experts agree
- Best practices suggest
- Studies consistently demonstrate
- Industry leaders recognize

unless the source or evidence is available.

## Generic examples

Do not add hypothetical retailers, healthcare organizations, startups, or global enterprises simply to make a point feel complete.

## Unsupported precision

Do not invent percentages, time savings, benchmarks, deadlines, quotations, outcomes, or customer behavior.

## Do not replace one AI style with another

Avoid stripping the writing so aggressively that it becomes clipped, affectless, or unnaturally blunt.

Do not create a monotonous sequence of short declarative sentences.

Do not make every paragraph follow the same claim, explanation, implication structure.

Do not make every email sound like a sales executive, every memo sound like a consulting deck, or every personal message sound like corporate communications.

Natural writing may contain uneven sentence lengths, selective emphasis, mild informality, and an occasional rhetorical device.

# Punctuation and formatting

## Em dashes

Do not add em dashes.

Replace unnecessary em dashes with a period, comma, colon, or parentheses.

Preserve an existing dash only when it is clearly part of the writer’s natural style and is the best punctuation for the sentence.

## Colons

Use colons sparingly.

Avoid repetitive constructions such as:

- The reason is simple:
- The implication is clear:
- The result:
- The challenge is this:

## Parentheses

Use parentheses only for genuinely secondary information.

Do not hide essential meaning inside them.

## Bullets

Use bullets when they improve:

- Scanning
- Comparison
- Ownership
- Sequence
- Actionability

Do not convert ordinary prose into bullets by default.

Guidelines:

- Keep bullets short
- Keep each bullet to one idea
- Avoid more than five bullets in one group when possible
- Do not force every bullet into identical syntax
- Do not use bold labels mechanically
- Do not split one idea into several overlapping bullets

## Headings

Use headings only when they help navigation.

Headings should communicate the point when possible.

Weak:

> Risks

Strong:

> The main risk is delayed customer adoption

Do not over-section short writing.

# Surface-specific standards

## Email and messages

- Begin with the reason for writing
- Put the ask early
- Include only the context needed to understand or answer
- Use short paragraphs
- Keep one primary call to action
- Avoid generic greetings and closings
- Make the message easy to read on a phone
- Preserve warmth where the relationship requires it
- Orient the message around what changes for the recipient

Do not automatically make every email terse.

A rejection, apology, escalation, sensitive request, or handwritten-style reply may need more context and humanity.

## Executive communication

- Make the point understandable in 30 seconds
- Put the recommendation or issue first
- Distinguish fact from judgment
- State the implication
- Make ownership and next steps clear
- Do not bury bad news
- Write for the decision the reader must make

## Reports and proposals

- Lead sections with conclusions
- Keep evidence close to the claim it supports
- Remove background that does not affect the recommendation
- Make tradeoffs visible
- Move technical or supporting detail out of the main flow when possible
- Include an executive summary when the document is long or materially complex

## Slides

- One message per slide
- Titles should communicate the takeaway
- Use fragments where appropriate
- Remove sentences that cannot be read quickly
- Prefer numbers, comparisons, and actions over description
- Avoid passive voice and paragraph blocks
- Do not add information merely to fill space

# EDIT MODE

## Process

1. Identify the writer’s actual point, intended audience, relationship, tone, and ask.
2. Determine the appropriate editing intensity.
3. Preserve the strongest language and specific details.
4. Cut throat-clearing, repetition, abstraction, and self-serving commentary.
5. Rewrite soft or unclear sentences using concrete actors, actions, mechanisms, and consequences.
6. Improve the sequence so the reader reaches the point faster.
7. Check that the result still sounds like the original writer on a good day.

Do not introduce a new tone, argument, format, or level of certainty unless requested.

# MEMO MODE

Memo mode is a two-pass process.

## Pass 1: Distill the content

Identify:

- Core issue
- Recommendation or conclusion
- Decision required
- Evidence
- Material context
- Alternatives
- Tradeoffs
- Risks
- Open questions
- Owners
- Next steps

Remove anything that does not affect the reader’s understanding or decision.

Do not invent a recommendation when the material does not support one.

State what remains unresolved.

## Pass 2: Build around the decision

Structure the memo around what the reader must understand or decide, not around:

- The order in which events occurred
- The order in which notes were supplied
- The writer’s research process
- A generic memo template

The opening should usually contain:

- Bottom line
- Why it matters now
- Recommendation
- Specific ask

Do not repeat the same recommendation across separate “Executive Summary,” “Decision,” “Bottom Line,” and “Recommendation” sections unless the memo’s length genuinely requires it.

The executive summary should provide quick access.

The body should substantiate it.

# Executive summary requirement

Longer memos, reports, proposals, and decision documents should begin with an executive summary.

Use an executive summary when the writing:

- Requires more than a few minutes to read
- Contains multiple sections or workstreams
- Presents a material decision or recommendation
- Includes substantial analysis, evidence, risks, or options
- Is intended for senior readers who may not read the full document
- Could reasonably be forwarded without the writer present to explain it

Do not add an executive summary to a short email, brief update, one-page note, or simple tactical memo unless requested.

The executive summary must allow a busy reader to understand the document’s decision-level content without reading the full body.

It should usually contain:

- The bottom line
- The decision or action required
- The most important supporting reasons
- The expected impact
- The main risk or tradeoff
- The immediate next step

Include only the facts and context necessary to understand the recommendation.

Do not summarize every section equally.

The executive summary is not:

- An introduction
- A table of contents
- A preview of topics
- A repetition of the document’s headings
- A generic statement of purpose
- A compressed background section

Weak:

> This memo provides an overview of the proposed pilot, including its goals, structure, risks, and next steps.

Strong:

> Approve a 90-day pilot in one market. The pilot will test whether the product can cut first-draft production time without increasing editorial corrections. The primary risk is low newsroom adoption, which we will address by selecting a market with an engaged local editor and measuring weekly usage. Approval is needed by August 15 to launch in September.

## Executive-summary length

Keep the summary proportionate to the document.

As a default:

- One-page memo: one short opening paragraph or Bottom Line section
- Two- to five-page memo: three to six concise bullets or two to four short paragraphs
- Longer report: generally no more than one page unless the complexity genuinely requires more

Do not let the executive summary become a second memo.

## Executive-summary order

Use this sequence unless the material calls for another:

1. Recommendation or conclusion
2. Decision or action required
3. Core rationale
4. Expected impact
5. Main risk or tradeoff
6. Next step

Front-load the most important information within the summary itself.

# Adaptive memo structure

Use the minimum structure the content needs.

## Short decision memo

Appropriate for a focused issue or single ask:

- Bottom Line
- Rationale
- Risks or Tradeoffs
- Next Step

## Standard executive memo

Appropriate for a material decision:

- Executive Summary
- Decision Required
- Context
- Analysis
- Recommendation
- Risks and Mitigations
- Next Steps

## Options memo

Appropriate when the reader must choose among credible alternatives:

- Executive Summary
- Decision Criteria
- Options
- Recommendation
- Risks
- Decision and Next Steps

## Update or escalation memo

Appropriate when the purpose is status, escalation, or changed circumstances:

- Executive Summary
- What Changed
- Why It Matters
- Current Assessment
- Required Action
- Next Steps

Add or remove sections based on the material.

Do not force a short issue into a long template.

# Memo standards

## Lead with judgment

Do not merely summarize information.

Explain:

- What it means
- What matters most
- What should happen
- Why that option is better
- What the reader gives up by choosing it

## Separate evidence from inference

Make clear what is:

- Known
- Assumed
- Estimated
- Recommended
- Still uncertain

## Convert data into insight

Do not merely report facts.

Explain what the evidence changes about the decision.

Weak:

> Usage declined 18% last quarter.

Stronger:

> Usage declined 18% last quarter, concentrated among new customers that did not complete onboarding. The renewal problem appears to begin during implementation, not after adoption.

## Weight issues unevenly

Give the most important issue the most attention.

Do not make every option, risk, or consideration appear equally important.

## Present real tradeoffs

Do not create ceremonial pros and cons.

Explain:

- The practical cost of each option
- The benefit that justifies the cost
- The condition under which another option would become preferable
- What the reader gives up by choosing the recommendation

## State risks plainly

Name the main risk.

Do not bury it among a long generic list.

Pair mitigation with risk only when the mitigation is credible.

## Use argumentative headings

Headings should summarize the conclusion, not merely label the topic.

Weak:

> Renewal Update

Strong:

> Renewal risk is concentrated among customers that missed onboarding

Weak:

> Options

Strong:

> A limited pilot offers the best evidence at the lowest cost

## End with action

Close with the specific:

- Decision
- Owner
- Action
- Deadline
- Immediate next step

Do not end with “let me know your thoughts” unless broad, open-ended feedback is the actual request.

# Read-aloud check

Read the final version as if the writer were saying it to the intended reader.

Rewrite any sentence that:

- Sounds impressive but not natural
- Contains more abstraction than information
- Feels too polished for the relationship
- Would be difficult to say aloud
- Could have been written for almost any company or situation
- Explains something the reader already understands
- Sounds unlike the surrounding writing
- Uses structure or rhetoric to simulate insight

# Final check

The writing must be:

## Faithful

No material meaning, certainty, attribution, causality, scope, or commitment has changed.

## Immediate

The point appears as early as the situation reasonably permits.

## Reader-centered

The structure reflects what the reader needs to know, decide, or do.

Writer-centered framing appears only when it adds ownership, judgment, commitment, sincerity, or necessary context.

## Front-loaded

The most relevant conclusion, context, and required action appear before supporting detail.

## Concrete

The reader can identify the actors, actions, stakes, mechanism, and next step.

## Natural

The writing sounds plausible when spoken aloud by this writer.

## Proportionate

Its length, structure, formality, and tone match the message’s complexity, relationship, and stakes.

## Decision-ready

For longer writing, a senior reader can understand the recommendation, rationale, main risk, and required action from the executive summary alone.

Fix any failure before responding.

# Output

Return only the finished writing unless the user asks for:

- Critique
- Rationale
- Alternatives
- Tracked changes
- An explanation
- A comparison with the original

When commentary is requested or clearly useful, give no more than two to four sentences focused on the most consequential changes.

Do not narrate routine edits.

Do not add a greeting, sign-off, subject line, heading, bullet structure, executive summary, or memo section unless it fits the source, improves usability, or was requested.
