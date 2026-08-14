---
name: human-writing
description: >-
  Draft, rewrite, and review prose so it sounds like a particular human writer
  rather than generic model output. Preserve facts, meaning, voice, and genre;
  remove formulaic patterns without flattening legitimate style. Use for prose,
  messages, essays, reports, product writing, documentation, and source-based edits.
---

# Human writing

## Purpose

Produce prose that reads as the work of a person with a specific purpose and voice. The writer's stance toward the reader should be clear, the rhythm should suit the material, and every factual claim should remain true to the source.

This skill is not an AI-detector evasion system. Do not optimize for detector scores, perplexity, burstiness, or random imperfection. Optimize for truthful, readable writing that the author could defend sentence by sentence.

The diagnostic catalog is written for English. The workflow can transfer to other languages, but English-specific words, punctuation habits, and rhetorical patterns must not be translated into universal rules.

## Priority order

When rules conflict, use this order:

1. The user's explicit instructions and immutable source material.
2. Factual fidelity, quotations, citations, links, code, and required terminology.
3. The communication goal, audience, genre, and channel.
4. The author's demonstrated voice.
5. Coherence, precision, and readability.
6. Removal of generic model patterns.
7. Default surface preferences in this skill.

A lower priority rule never overrides a higher one. Naturalness does not permit invention. A style heuristic does not justify changing a fact.

## Determine the mode

Infer the mode from the request. Do not force the user through a questionnaire when the answer is already visible in the material.

- **Draft mode:** Turn a brief, notes, evidence, or an outline into finished prose.
- **Rewrite mode:** Rebuild existing prose while preserving its claims and constraints.
- **Light edit mode:** Keep the author's structure and wording where possible; repair only clear defects.
- **Audit mode:** Diagnose voice, craft, and generic model patterns without rewriting unless asked.
- **Voice profile mode:** Extract reusable writing characteristics from samples by the intended author.
- **Embedded mode:** Return only the requested prose. Run the full process internally.
- **File mode:** Edit prose in the file while leaving code, frontmatter, data, links, citations, and quoted material intact.

When the user gives human-written text that already works, prefer a light edit. Do not "humanize" it into a different person's voice.

## Core loop

Every drafting or rewriting task follows the same internal sequence:

1. **Map:** Identify the purpose, reader, immutable claims, and source boundaries.
2. **Calibrate:** Infer the author's voice and the genre's legitimate conventions.
3. **Draft:** Rebuild the prose from the intended thought rather than swapping words sentence by sentence.
4. **Review:** Restore supported human qualities, then remove generic model patterns that weaken the piece.
5. **Verify:** Compare the revision with the source and check quotations, citations, names, numbers, dates, links, code, and qualifications.
6. **Revise:** Read the piece aloud, name its most material defects internally, and repair them.
7. **Re-verify:** Compare the final revision with the claim ledger.
8. **Post-process:** After the output is complete, run the deterministic text-hygiene pass in `scripts/postprocess_output.py`.
9. **Final check:** Compare the cleaned text with the verified draft, restore any legitimate semantic Unicode, and deliver the cleaned result.

Finish with a source check. Style changes can alter scope or certainty even when they improve the prose.

## Run the post-output text-hygiene pass

Run this step after the prose has been created and verified, including in embedded and file modes. Resolve `HUMAN_WRITING_SKILL` to the directory containing this `SKILL.md`, stage the completed prose without interpolating it into a shell command, and run:

```bash
python3 "$HUMAN_WRITING_SKILL/scripts/postprocess_output.py" DRAFT -o CLEANED --stats
```

For a safe stdin/stdout pipeline:

```bash
python3 "$HUMAN_WRITING_SKILL/scripts/postprocess_output.py" - --stats < DRAFT > CLEANED
```

Treat `CLEANED` as the delivery candidate. Inspect the reported counts and compare it with `DRAFT` before delivery. The pass removes invisible or directional format characters, variation selectors, tag characters, and soft hyphens, and normalizes exotic spaces. Restore a removed character when it is semantically required, such as a joiner in non-Latin text or an emoji sequence. Never alter quoted material, code, identifiers, URLs, or required formatting merely to maximize the removal count.

This is the deterministic Layer A text-cleaning approach adapted from [`guillaumemeyer/watermarks-remover`](https://github.com/guillaumemeyer/watermarks-remover), pinned in the bundled license note. It does not rewrite wording, detect statistical token-sampling marks, prove human authorship, or certify that vendor detectors will fail. Do not run an automatic Layer B paraphrase after the final verification; a rewrite would need a fresh claim, voice, and source audit.

## Build the writing brief

Before drafting, establish these facts internally:

- What should the reader know, believe, feel, or do after reading?
- Who is the reader, and what do they already know?
- What form is this: email, memo, essay, post, report, documentation, speech, or something else?
- What position does the author take? How certain are they?
- Which facts, qualifications, quotations, dates, numbers, names, citations, links, and terms must survive unchanged?
- Is there a voice sample? Is it the same author, genre, and audience?
- What length, formatting, or policy constraints apply?

Infer missing details conservatively. Ask only when a missing answer would materially change the result and cannot be resolved from context.

## Protect the source before editing

Create an internal claim ledger. Separate the material into:

- immutable facts and required claims;
- direct quotations and attributed statements;
- citations, links, code, commands, and identifiers;
- editable explanation, organization, wording, and emphasis;
- unsupported filler that may be removed.

Every required claim must survive. Preserve meaning rather than sentence shape. You may merge paragraphs, split sentences, reorder supporting points, compress routine material, and spend more space where the argument carries weight.

Outside explicitly fictional or imaginative work, never add a fact, date, number, name, quote, citation, source, event, result, personal experience, or concrete example that the user or source did not supply. In fiction, preserve established continuity and do not insert real-world claims that the task does not support. Do not turn a vague nonfiction statement into a specific one by guessing. State the uncertainty plainly or omit the claim.

## Calibrate the voice

Voice emerges from stance, syntax, pacing, punctuation, evidence, and diction. Model the following dimensions from the best available sample:

- **Register:** casual, formal, technical, intimate, journalistic, academic, sales-oriented, or mixed.
- **Reader relationship:** peer, customer, executive, friend, general public, specialist, or adversarial audience.
- **Stance:** confident, tentative, skeptical, enthusiastic, dry, combative, warm, detached, or mixed.
- **Sentence behavior:** typical length, range, fragments, run-ons, coordination, subordination, and preferred openings.
- **Paragraph behavior:** compact or expansive, linear or associative, frequent or sparse topic sentences.
- **Diction:** plain or specialized words, contractions, slang, profanity, recurring phrases, and tolerated repetition.
- **Punctuation:** commas, semicolons, colons, parentheses, dashes, quotation marks, and exclamation points.
- **Reasoning habits:** examples before claims or claims before examples; caveats; counterarguments; self-correction; explicit uncertainty.
- **Emotional range:** humor, irritation, warmth, ambivalence, restraint, or bluntness.
- **Evidence style:** anecdotes, figures, citations, concrete observations, analogies, or compressed assertions.

Use this evidence hierarchy:

1. A recent sample by the same author in the same genre.
2. A sample by the same author in a nearby genre.
3. The user's explicit voice description.
4. Strong cues in the draft or conversation.
5. A plain genre-appropriate default.

The sample outranks generic style rules. Match habits without turning them into a caricature. Keep meaningful quirks. Do not regularize every fragment, contraction, repeated word, or dash merely because a style guide dislikes it.


When voice profile mode is requested, return a compact profile with:

- the sample's context and how confidently it represents the author;
- stable tendencies in register, stance, diction, syntax, paragraphs, punctuation, humor, evidence, and reader relationship;
- habits to preserve, supported by short examples from the sample;
- habits that appear situational rather than stable;
- patterns the author avoids or uses rarely;
- explicit cautions against caricature and overgeneralization.

Do not turn a one-off phrase or typo into a permanent rule. Express tendencies with confidence levels and exceptions rather than converting the samples into a rigid template.

## Draft from the thought, not the wording

Write the first full pass from the communication goal and claim ledger. Avoid sentence-by-sentence synonym replacement. That preserves the shape of model prose even when individual words change.

A useful draft usually does the following:

- gives the strongest idea the clearest sentence;
- spends detail where the writer has evidence, interest, or uncertainty;
- uses concrete subjects and verbs when the actor matters;
- lets sentence complexity follow thought complexity;
- varies paragraph length for a reason, not by randomization;
- allows a qualified or unresolved ending when the subject remains unresolved;
- uses first person, opinion, humor, or an aside only when the author and genre support it.

Human writing can be orderly. Naturalness does not require fake mistakes, gratuitous fragments, invented anecdotes, arbitrary slang, or deliberate loss of polish.

## Run the authenticity pass

Look for places where the prose lacks a person behind it.

Add or restore only what the source and voice support:

- a defensible opinion instead of bloodless reporting;
- a concrete detail instead of an available abstraction;
- mixed feelings where the evidence points in two directions;
- honest uncertainty with the reason for that uncertainty;
- a natural aside, qualification, or self-correction;
- uneven emphasis based on what the author actually cares about;
- a direct relationship with the reader when the channel calls for one.

Do not manufacture these signals. Never claim that the author saw, felt, tried, remembers, or believes something unless the source supports it.

## Run the generic-pattern pass

Search at sentence, paragraph, and document level. Look for clusters, not isolated tokens. One em dash, one formal transition, or one three-part list proves nothing. Revise when several patterns combine, when a device repeats mechanically, or when it weakens the prose.

### Inflated importance and promotion

Watch for claims that something "stands as" a testament, marks a pivotal moment, reflects a broader shift, showcases excellence, unlocks potential, or belongs to a vibrant and evolving landscape. Replace ceremony with the concrete event, function, consequence, or evidence. Remove unsupported claims of importance.

### Fake depth and trailing analysis

Watch for participial tails such as "highlighting," "underscoring," "ensuring," "reflecting," or "fostering" when they append interpretation without explaining it. Split the sentence and state the actual causal or interpretive claim. Cut it when no claim exists.

Also flag abstract nouns that conceal the action, strings of implications with no mechanism, and "from X to Y" ranges whose endpoints do not form a real scale.

### Vague attribution and hidden agency

Replace "experts say," "observers note," or "research suggests" with a named source when one exists. Otherwise narrow or remove the claim.

Use active voice when naming the actor improves clarity. Keep passive voice when the actor is unknown, irrelevant, obvious, strategically omitted, or conventional in the genre. Do not invent an actor to satisfy a grammar rule.

### Formulaic rhetoric

Inspect these structures:

- "not X, but Y" and "it is not just X; it is Y";
- questions answered immediately as a staged reveal;
- repeated groups of three used as padding;
- a sequence of clipped sentences designed to sound profound;
- "the real question," "at its core," or "what really matters" followed by an ordinary point;
- aphorism templates such as "X is the language of Y";
- negative lists that delay the actual claim;
- generic "challenges and future outlook" sections.

Keep a structure when the logic requires it. Otherwise state the point directly.

### Metronomic rhythm

Check for runs of sentences with similar length, syntax, openings, and clause count. Also check for paragraphs that all have the same size or all end with a manufactured punchline.

Repair rhythm through thought and syntax, not random noise. Combine related claims. Split a sentence when the idea turns. Let a dense explanation take space, then use a short sentence only when it earns the emphasis.

### Chat and template residue

Remove conversational wrappers that do not belong in the artifact: "Of course," "Great question," "Here is a breakdown," "I hope this helps," offers to continue, knowledge-cutoff disclaimers, and generic reassurance.

Delete tutorial signposting such as "let's dive in" or "now let's explore" when the next sentence can simply begin the explanation. Remove heading restatements and meta-commentary about what the document will say unless the genre requires a roadmap.

### Generic endings

Do not end with "the future looks bright," "exciting times lie ahead," or a summary that merely repeats the introduction. End on the last concrete finding, the actual unresolved tension, a decision, a consequence, or a next action. Some pieces need no concluding paragraph.

### Surface habits

Use formatting because the medium needs it, not because a template expects it. Avoid decorative bold, mechanical inline-header lists, unnecessary emojis, and automatic title case. Keep typography consistent with the author and destination.

Dashes, adverbs, passive voice, formal vocabulary, questions, sentence-initial question words, fragments, three-item lists, and curly quotation marks are not authorship tests. Use them deliberately and at a frequency consistent with the voice and destination. Empty modifiers, evasive passive constructions, and repetitive punctuation are the problem.

## Do not overcorrect

Preserve these when they are doing real work:

- specific, unusual, source-grounded detail;
- mixed register used naturally by the author;
- precise technical or academic vocabulary;
- repeated terms that should remain terminologically stable;
- clean grammar and professional polish;
- genuine asides, self-corrections, and unresolved tension;
- quotations, titles, proper names, citations, and examples under discussion;
- conventional passive voice in scientific, legal, or procedural writing;
- exact lists that happen to contain three items.

Do not flatten competent prose to make it seem less polished. Do not remove every transition, adverb, subordinate clause, or long sentence. Do not replace clear language with choppiness.

## Audit truth and preservation

Compare the draft against the claim ledger and source. Check every name, number, date, quotation, citation, link, and technical term. Confirm that qualifications and uncertainty survived. Confirm that no causal claim became stronger, no opinion became a fact, and no attributed statement lost its attribution.

For source-based work, a fluent fabrication is a critical failure. Repair accuracy before style.

## Read aloud and revise

Run this audit after the first complete rewrite:

1. What is the piece trying to do, in one sentence?
2. Which line sounds as though any model could have written it?
3. Where does the prose announce significance instead of showing the reason?
4. Do sentence lengths, openings, and paragraph endings repeat mechanically?
5. Is any rhetorical contrast, list, or punchline present mainly for effect?
6. Is an abstraction hiding a concrete actor, object, action, or result already available in the source?
7. Did the rewrite add a fact, experience, stance, certainty level, or attribution?
8. Did it erase a useful quirk from the author's voice?
9. Can the opening start later? Can the ending stop earlier?
10. Does it sound natural when spoken at a normal pace?

Name the three most material defects internally. Revise the text. Run the truth check again after the style revision.

## Score before delivery

A draft must pass every critical check and score at least 85 out of 100. Use the detailed rubric in `references/evaluation-rubric.md`.

- Factual and semantic fidelity: 25
- Voice fidelity: 20
- Purpose, audience, and genre fit: 15
- Specificity and explanatory value: 15
- Rhythm and sentence craft: 10
- Structural naturalness: 10
- Surface restraint: 5

Critical failures override the score: invented information, altered meaning, fake personal experience, corrupted quotations or citations, removed material qualifications, or imitation so aggressive that it becomes parody.

## Output contract

- In draft, rewrite, light edit, embedded, and file modes, return only the finished prose unless the user asks for commentary.
- In audit mode, give a concise diagnosis organized by impact. Quote only enough text to identify each issue.
- When the user requests an audit plus rewrite, return the diagnosis and the final revision. Do not expose hidden chain-of-thought or a long account of every edit.
- Preserve requested formatting and length. Do not add a preface such as "Here is the revised version" when the text will be pasted directly into another artifact.
- When several versions would serve different purposes, label the tradeoff between them. Do not produce random synonym variants.

## Self-application

Apply this skill to its own writing instructions, prompts, style guides, rubrics, and documentation before delivery.

For instructional prose:

- preserve normative meaning and requirement strength;
- consolidate duplicate rules and keep terminology stable;
- remove canned transitions, promotional claims, fake urgency, and decorative rhetoric;
- vary sentence and paragraph structure only where it improves comprehension;
- prefer a direct rule plus a useful exception over an absolute rule followed by scattered corrections;
- verify that examples demonstrate the rule without adding unsupported facts;
- run the same claim, voice, rhythm, generic-pattern, and final truth audits used for other prose.

Self-revision must improve the wording without weakening the specification. After revising, compare the final instructions with the pre-revision requirements and restore anything lost. Stop only when the text is accurate, internally consistent, executable, and no longer exhibits a material pattern it warns against.

## Supporting material

- `scripts/postprocess_output.py`: mandatory after-output deterministic Unicode and space cleanup.
- `references/pattern-catalog.md`: expanded diagnostic catalog with contextual repairs.
- `references/evaluation-rubric.md`: scoring anchors and critical-failure checks.
- `references/voice-profile-schema.md`: reusable format for evidence-based voice profiles.
- `references/watermarks-remover-license.txt`: upstream source pin and MIT license.
- `tests/test-cases.md`: acceptance cases for voice matching, source preservation, genre exceptions, and overcorrection.
