# Acceptance tests

Use these cases to evaluate an implementation of the `human-writing` skill. The expected behavior matters more than exact wording.

## Case 1: A voice sample uses em dashes

**Input condition:** The author's sample uses em dashes sparingly for genuine asides. The draft contains one similar aside.

**Expected:** Keep or reproduce the author's approximate usage. Do not apply a blanket dash ban.

**Failure:** Replacing every dash despite the sample, or adding several more because the sample contains one.

## Case 2: Scientific passive voice

**Input condition:** A methods section says that samples were stored at a specified temperature. The actor is irrelevant.

**Expected:** Preserve the passive construction if it is standard and clear.

**Failure:** Inventing a named actor or forcing "we" into the sentence.

## Case 3: Responsibility hidden by passive voice

**Input condition:** A postmortem source names the team that disabled an alert, but the draft says, "The alert was disabled."

**Expected:** Name the team unless policy or the user's instruction requires anonymity.

**Failure:** Keeping the passive sentence solely because it is grammatical.

## Case 4: Exact three-part taxonomy

**Input condition:** The source defines exactly three deployment states.

**Expected:** Keep the three-item list.

**Failure:** Deleting one item to avoid the rule of three.

## Case 5: Missing specificity

**Input condition:** The source says performance improved but gives no metric.

**Expected:** Write the plain supported claim or note that the source does not quantify the improvement.

**Failure:** Inventing a load-time reduction or percentage.

## Case 6: Author ambivalence

**Input condition:** The author says a feature works but may not justify its infrastructure cost.

**Expected:** Preserve both sides and the unresolved judgment.

**Failure:** Converting the passage into a clean positive or negative verdict.

## Case 7: Human prose already works

**Input condition:** The supplied paragraph has a distinctive voice, source-grounded details, and no material craft problem.

**Expected:** Return it unchanged or make only small corrections requested by the user.

**Failure:** Rebuilding it into generic polished prose.

## Case 8: Quoted AI-like phrase

**Input condition:** The text quotes the phrase "a vibrant tapestry" in order to criticize it.

**Expected:** Leave the quotation intact.

**Failure:** Rewriting words inside the quotation.

## Case 9: Technical terminology repeats

**Input condition:** A specification uses one defined term repeatedly.

**Expected:** Repeat the term for precision.

**Failure:** Cycling through synonyms to avoid repetition.

## Case 10: Generic model opening

**Input condition:** The draft begins with "In today's rapidly evolving landscape" and then states a concrete change.

**Expected:** Start with the concrete change.

**Failure:** Swap "landscape" for another abstract noun while retaining the opening structure.

## Case 11: Rhetorical contrast corrects a real misconception

**Input condition:** The audience commonly confuses authentication with authorization, and the passage explicitly corrects that confusion.

**Expected:** A contrast may remain if it is the clearest correction.

**Failure:** Removing the distinction merely because "not X, but Y" is watched.

## Case 12: File mode

**Input condition:** A Markdown file contains frontmatter, prose, links, citations, and code blocks.

**Expected:** Edit only prose. Preserve frontmatter values, URLs, citation targets, and code exactly.

**Failure:** Reformatting code, changing links, or rewriting metadata.

## Case 13: Generic conclusion

**Input condition:** The final substantive sentence names the decision. A later paragraph says the future looks promising.

**Expected:** End on the decision and remove the generic send-off.

**Failure:** Preserve or rewrite the optimistic filler.

## Case 14: Self-application

**Input condition:** The skill drafts a new writing guideline with duplicate warnings, promotional language, and several absolute rules contradicted by later exceptions.

**Expected:** Consolidate the warnings, replace unsupported absolutes with contextual rules, and preserve the strength of true hard constraints.

**Failure:** Leave the guide inconsistent or weaken a factual-integrity requirement during stylistic cleanup.

## Case 15: Audit-only request

**Input condition:** The user asks what sounds artificial but does not ask for a rewrite.

**Expected:** Give a concise, prioritized diagnosis with short quoted examples.

**Failure:** Rewrite the full passage or produce a long generic checklist.

## Case 16: Embedded mode

**Input condition:** Another agent requests a final email body for insertion into a workflow.

**Expected:** Return only the email body after running the internal audit.

**Failure:** Add a preface, scorecard, or explanation.

## Case 17: Fictional invention

**Input condition:** The user asks for an original fictional scene and supplies established characters and setting rules.

**Expected:** Invent scene details that fit the task while preserving established continuity. Keep real-world claims accurate when they appear.

**Failure:** Refusing to invent any detail because the nonfiction source-preservation rule was applied without context.

## Case 18: Non-English prose

**Input condition:** The user requests a rewrite in a language other than English.

**Expected:** Apply the intent, voice, source, and self-audit workflow. Use language-specific knowledge rather than translating the English watch list literally.

**Failure:** Removing a normal construction solely because its English translation resembles an English model tell.

## Case 19: Post-output text hygiene

**Input condition:** The completed, verified prose contains a zero-width space and an em space introduced during generation or copying.

**Expected:** Create and verify the full output first, run `scripts/postprocess_output.py`, remove the zero-width character, normalize the em space, compare the cleaned result with the verified draft, and deliver only the cleaned prose.

**Failure:** Delivering the unprocessed draft, running the cleaner before the output is complete, or using a second-model paraphrase as the automatic post-pass.

## Case 20: Legitimate semantic Unicode

**Input condition:** The verified output contains a joiner or variation selector required by non-Latin text or an emoji sequence.

**Expected:** Run the post-processor, compare its result with the verified draft, and restore the legitimate character before delivery.

**Failure:** Treating every removed code point as malicious and corrupting the intended text.
