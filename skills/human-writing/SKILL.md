---
name: human-writing
description: >-
  Use for publicly facing writing, product copy, documentation, and durable
  user-visible strings such as frontend labels, messages, errors, empty states,
  and onboarding text. For internal, personal, or model-facing prose, use
  semantic-density instead.
metadata:
  version: "1.0.0"
  language: "English-first"
  aliases:
    - humanizer
    - voice-editor
---

# Human writing

## Purpose and limits

Produce prose that sounds like a person with a purpose, a reader in mind, and a defensible relationship to the subject. Preserve truth, voice, genre, and useful polish while removing generic model patterns.

This is not an AI-detector-evasion system. Do not optimize for detector scores, perplexity, burstiness, or artificial imperfection. Naturalness does not require fake mistakes, invented experience, random variation, or reduced precision. The catalog is English-first; transfer its reasoning across languages, not its English-specific word lists.

## Scope and routing

Use this skill for public-facing writing, product copy, documentation, and durable user-visible strings, including frontend labels, messages, errors, empty states, and onboarding text. Apply voice, genre, authenticity, source, and pattern checks because the text will represent an author or product over time.

For personal notes, internal planning, messages to models, scratch notes, and temporary technical explanations, use `semantic-density` instead. That skill optimizes for precise, concise, executable information without imposing a public-facing human voice. Do not use either writing skill to rewrite code, schemas, commands, identifiers, structured data, or quoted material unless the request explicitly includes them.

## Priority order

When instructions conflict, follow this order:

1. The user's instructions and immutable source material.
2. Factual fidelity, quotations, citations, links, code, identifiers, and required terminology.
3. Communication goal, audience, genre, channel, and formatting constraints.
4. The author's demonstrated voice.
5. Coherence, precision, readability, and semantic density.
6. Removal of generic model patterns.
7. This skill's default surface preferences.

A lower priority rule never overrides a higher one. Style never licenses invention or a change in certainty.

## Modes

Infer the mode from the request and material; ask only when the missing answer would materially change the result.

- **Draft:** turn a brief, notes, evidence, or outline into prose.
- **Rewrite:** rebuild prose while preserving claims and constraints.
- **Light edit:** preserve the author's structure and wording except for clear defects.
- **Audit:** diagnose voice, craft, and generic patterns without rewriting unless asked.
- **Voice profile:** extract reusable characteristics from samples by the intended author.
- **Embedded:** return only the requested prose; run the process internally.
- **File:** edit prose in a file while leaving code, frontmatter, data, links, citations, and quoted material intact.

When supplied prose already works, prefer a light edit. Do not turn it into a different person's voice.

## Core workflow

1. **Map.** Identify purpose, reader, genre, author stance, certainty, source boundaries, and output constraints.
2. **Calibrate.** Infer voice from the strongest available sample: same author and genre first, then nearby genre, explicit description, draft cues, and finally a plain genre default.
3. **Protect.** Build an internal claim ledger separating immutable claims; quotations and attributed statements; names, numbers, dates, citations, links, code, commands, and identifiers; editable structure and wording; and unsupported filler that may be cut.
4. **Draft.** Write from the intended thought and claim ledger, not by replacing words sentence by sentence.
5. **Review.** Restore supported human qualities, then remove generic patterns that weaken the piece.
6. **Verify.** Reconcile the text with the source and ledger. Recheck names, numbers, dates, quotations, citations, links, technical terms, qualifications, attribution, causality, and certainty.
7. **Revise aloud.** Identify the three most material defects, repair them, and run the truth check again.
8. **Post-process.** After verification, run the mandatory deterministic text-hygiene pass below. Inspect its counts, compare cleaned text with the verified draft, and restore any semantically required character.
9. **Deliver.** Treat the cleaned text as the candidate. Preserve requested formatting and length; return only finished prose unless commentary is requested.

Outside fiction, never add a fact, date, number, name, quote, citation, source, event, result, personal experience, or concrete example that the user or source did not provide. In fiction, preserve continuity and do not add unsupported real-world claims. If a nonfiction claim is vague, keep the uncertainty or omit it; do not guess.

## Mandatory text-hygiene pass

Run this after the prose is created and verified, including embedded and file modes. Resolve `HUMAN_WRITING_SKILL` to the directory containing this `SKILL.md`, stage the completed prose without interpolating it into a shell command, and run:

```bash
python3 "$HUMAN_WRITING_SKILL/scripts/postprocess_output.py" DRAFT -o CLEANED --stats
```

Or use stdin/stdout:

```bash
python3 "$HUMAN_WRITING_SKILL/scripts/postprocess_output.py" - --stats < DRAFT > CLEANED
```

The pass removes invisible or directional format characters, variation selectors, tag characters, soft hyphens, and exotic spaces. It does not rewrite wording, detect statistical token marks, prove authorship, or certify detector results. Restore a removed character when semantically required, such as a joiner in non-Latin text or an emoji sequence. Never alter quoted material, code, identifiers, URLs, or required formatting to increase the removal count. Do not run an automatic paraphrase after final verification; a rewrite requires a fresh claim, voice, and source audit.

## Build and calibrate the brief

Establish internally:

- what the reader should know, believe, feel, or do;
- who the reader is and what they already know;
- the form: email, memo, essay, post, report, documentation, speech, interface copy, or other artifact;
- the author's position and certainty;
- facts, qualifications, quotations, dates, numbers, names, citations, links, terms, length, and formatting that must survive;
- whether a voice sample represents the same author, genre, and audience.

Model voice through register, reader relationship, stance, sentence and paragraph behavior, diction, punctuation, reasoning habits, emotional range, and evidence style. Preserve meaningful quirks, contractions, fragments, repetition, and mixed register when characteristic and useful. Do not turn one typo or phrase into a permanent rule, and do not caricature the sample.

In voice-profile mode, return a compact profile covering sample context and confidence; stable tendencies with brief evidence; habits to preserve; situational habits; avoided or rare patterns; and cautions against overgeneralization.

## Draft from the thought

Give the strongest idea the clearest sentence. Spend detail where the evidence, interest, or uncertainty lies. Use concrete subjects and verbs when the actor matters. Let sentence complexity follow thought complexity. Vary paragraph length for a reason, allow qualified or unresolved endings, and use first person, opinion, humor, asides, or self-correction only when source, author, and genre support them.

Prefer a stronger verb, concrete mechanism, or measured result to a weak verb plus adverb. Compress filler such as “in order to,” “due to the fact that,” and “it is important to note that” when it adds no meaning.

## Authenticity pass

Look for places with no person behind the prose. Add or restore only source-supported qualities: a defensible opinion, concrete detail, mixed feeling, honest uncertainty and its reason, a natural qualification or aside, uneven emphasis based on what the author cares about, or a direct reader relationship appropriate to the channel. Never invent what the author saw, felt, tried, remembers, or believes.

## Generic-pattern pass

Search at sentence, paragraph, and document level. Clusters, repetition, and weakened meaning matter more than isolated tokens. Keep a device when logic, voice, or genre requires it.

### Importance, prestige, and promotion

Replace “stands as,” “testament,” “pivotal moment,” “broader shift,” “showcases excellence,” “unlocks potential,” and “vibrant and evolving landscape” with the concrete event, function, consequence, or evidence. Remove unsupported importance.

Flag prestige by association: lists of publications, companies, awards, or authorities that add status without evidence. Keep a named source when its relevance is clear; otherwise explain its contribution, narrow the reference, or cut it. Treat “serves as,” “stands as,” “boasts,” and “features” as possible evasions of “is” or “has.”

### Abstraction, attribution, and agency

Cut participial tails such as “highlighting,” “underscoring,” “ensuring,” “reflecting,” or “fostering” when they append interpretation without a causal or interpretive claim. Replace abstract nouns that conceal action, implication strings with no mechanism, and false “from X to Y” ranges with the actual action or topics.

Replace “experts say,” “observers note,” and “research suggests” with a named source when one exists; otherwise narrow or remove the claim. Use active voice when naming the actor clarifies the sentence. Keep passive voice when the actor is unknown, irrelevant, obvious, strategically omitted, or conventional.

Treat “substrate,” “vector,” “bedrock,” “scaffolding,” “flywheel,” “north star,” and “endgame” as diagnostic examples of metaphorical technical jargon, not banned words. Replace them when they hide the actual mechanism, decision, or stage; retain established technical terms when precise and understood.

Run a project-specificity check: if a sentence could appear unchanged in another project's documentation, name the relevant actor, object, action, result, decision, or uncertainty when the source supports it. Otherwise cut the generic claim.

### Formula and structure

Inspect “not X, but Y”; “not just X; Y”; staged questions with immediate answers; padded groups of three; clipped sentences designed to sound profound; “the real question,” “at its core,” and “what really matters” followed by ordinary points; aphorisms such as “X is the language of Y”; negative lists that delay the claim; and generic “challenges and future outlook” sections. State the point directly unless the structure carries real logic.

Check for metronomic sentence length, syntax, openings, clause counts, paragraph sizes, or manufactured punchlines. Repair rhythm through thought and syntax, not random noise. Combine related claims; split at a real turn; let dense explanations take the space they need.

### Template residue and surface habits

Remove wrappers that do not belong in the artifact: “Of course,” “Great question,” “Here is a breakdown,” “I hope this helps,” offers to continue, cutoff disclaimers, generic reassurance, “let's dive in,” and “now let's explore.” Remove heading restatements and meta-commentary unless the genre needs a roadmap.

Use formatting because the medium needs it. Avoid decorative bold, mechanical inline-header lists, unnecessary emojis, and automatic title case. Dashes, adverbs, passive voice, formal vocabulary, questions, fragments, three-item lists, and curly quotes are not authorship tests. Use them deliberately and consistently with voice and destination.

In technical or instructional prose, ask what each sentence tells the reader to know or do. Prefer a concrete fact, instruction, mechanism, result, decision, or stated uncertainty over language that only signals confidence or atmosphere. This is a diagnostic, not a demand for terse or literal prose.

### Endings and filler

Avoid generic conclusions such as “the future looks bright,” “exciting times lie ahead,” or a summary that repeats the introduction. End on the last concrete finding, unresolved tension, decision, consequence, or next action; some pieces need no conclusion.

## Do not overcorrect

Preserve source-grounded detail, precise technical or academic vocabulary, stable terminology, clean grammar, professional polish, meaningful asides and uncertainty, quotations, titles, names, citations, examples under discussion, conventional passive voice, and exact lists that happen to contain three items. Do not remove every transition, adverb, subordinate clause, long sentence, dash, or curly quote. Do not replace clear language with choppiness.

## Final audit

Read aloud and ask:

1. What is the piece trying to do in one sentence?
2. Which line could any model have written?
3. Where does it announce significance instead of showing the reason?
4. Do sentence lengths, openings, and paragraph endings repeat mechanically?
5. Is a contrast, list, or punchline present mainly for effect?
6. Does an abstraction hide an available actor, object, action, or result?
7. Did the rewrite add a fact, experience, stance, certainty, or attribution?
8. Did it erase a useful voice quirk?
9. Can the opening start later or the ending stop earlier?
10. Does it sound natural at a normal speaking pace?

Repair the three most material defects, then recheck truth, source preservation, and the claim ledger.

## Delivery and evaluation

For draft, rewrite, light-edit, embedded, and file modes, return only finished prose unless commentary is requested. In audit mode, give a concise impact-ordered diagnosis and quote only enough to identify each issue. For audit plus rewrite, return the diagnosis and final revision without hidden reasoning or a long edit log. Preserve requested formatting and length; do not add a preface when the text will be pasted into an artifact. If versions serve different purposes, label the tradeoff rather than producing random synonym variants.

Use `references/evaluation-rubric.md` and require at least 85/100:

- factual and semantic fidelity: 25;
- voice fidelity: 20;
- purpose, audience, and genre fit: 15;
- specificity and explanatory value: 15;
- rhythm and sentence craft: 10;
- structural naturalness: 10;
- surface restraint: 5.

Critical failures override the score: invented information, altered meaning, fake personal experience, corrupted quotations or citations, removed material qualifications, or imitation so aggressive that it becomes parody.

## Self-application

Apply this skill to its own instructions, prompts, style guides, rubrics, and documentation before delivery. Preserve requirement strength and normative meaning. Consolidate duplicate rules, keep terminology stable, remove canned transitions and decorative rhetoric, and prefer a direct rule with a useful exception over an absolute followed by scattered corrections. Verify that examples demonstrate the rule without adding unsupported facts. Run the same claim, voice, rhythm, generic-pattern, source, and final-truth audits. Stop only when the instructions are accurate, internally consistent, executable, semantically dense, and free of material patterns they warn against.

## Supporting material

- `scripts/postprocess_output.py`: mandatory deterministic Unicode and space cleanup.
- `references/pattern-catalog.md`: expanded diagnostic catalog and contextual repairs.
- `references/evaluation-rubric.md`: scoring anchors and critical-failure checks.
- `references/voice-profile-schema.md`: evidence-based voice-profile format.
- `references/watermarks-remover-license.txt`: upstream source pin and MIT license.
- `tests/test-cases.md`: acceptance cases for voice matching, source preservation, genre exceptions, and overcorrection.
