# UI stress catalog

Select cases for fields the actual component renders. Values are candidates, not universal requirements or proof of a defect. Check the schema and product semantics first; a contract-valid value belongs in the production fixture, while an invalid, historical, or corrupted value belongs in a separately labeled defensive probe. Record **no limit found** or **unknown** when a bound is not established.

Use `example.com`, `example.org`, or `.test` domains for displayed emails and URLs. Do not navigate to them, deliver mail, or load remote media. Intercept requests or use local fixtures. Prefer meaningful examples over repeated-character strings; use accepted schema limits when boundary length matters.

## People

| Candidate | Observe |
|---|---|
| `Aleksandra Wiśniewska-Kowalczyk`, `Konstantin Oberhauser-Wettstein` | Compound names, wrapping, diacritics, row height, and trailing actions. |
| `Christopher Alexander Montgomery III`, `María José de la Cruz y Fernández` | Suffixes and particles; verify the product's display, sorting, and initials conventions rather than assuming first/last tokens. |
| `Jo`, `J`, `dana` | Short names, case preservation, click-target size, and fallback consistency. A one-letter initial is not automatically wrong. |
| `Ólafur Darri Ólafsson`, `Đặng Thị Ngọc Hân` | Accents and tall marks; inspect line height and clipping. |
| `王秀英`, `نور الهدى عبد الرحمن` | Non-Latin scripts, word segmentation, bidirectional punctuation, and script-appropriate display. |
| `Seán O'Brien-Ó Súilleabháin` | Apostrophes, accents, search, and correct text rendering. |
| `🦊 Fox`, `👩🏽‍💻 Priya` | Grapheme-safe slicing and fallback glyphs. Do not assume every product accepts emoji in names. |
| `  Sam   Lee `; missing name with email available | Contract-defined normalization and fallback behavior; missing and whitespace values may be invalid at this boundary. |

Names do not share one universal family-name or initials rule. Use the product's documented convention, preserve user-provided names, and make fallbacks meaningful. If initials are derived, grapheme-aware processing such as `Intl.Segmenter` avoids splitting emoji or combining sequences; it does not decide cultural naming policy.

## Identifiers

| Candidate | Observe |
|---|---|
| `bartholomew.fitzgerald@northwind-industries-holdings.example.com` | Long email, intrinsic width, and action access. |
| `a@b.test`, `first.last+billing-notifications@example.com` | Short values and plus-addressing, if accepted by the actual contract. |
| `ops@sub.department.region.example.org` | Nested-domain display and extraction; use a locally stubbed multi-part-suffix case if the product parses public suffixes. |
| `https://example.com/workspaces/acme/projects/q3-launch/docs/9f8e7d6c5b4a?tab=comments&filter=unresolved` | Long URL display, meaningful query suffix, and copyability; never navigate during this test. |
| `9f8e7d6c-5b4a-4c3d-8e2f-1a0b9c8d7e6f` | Monospace width and distinguishability among similar identifiers. |
| `Q3 Board Deck — FINAL (revised) v12 [approved by legal].pdf`, `IMG_20250914_183022_HDR_portrait_edited_edited.HEIC` | Version/extension visibility, unbroken segments, and file-name rendering. |
| `@a`, the longest accepted handle | Contract bounds and the part users need to distinguish. |

Long strings can still have break opportunities at punctuation; inspect the browser's actual layout. If a secondary field truncates, preserve distinguishing information and provide an accessible way to inspect and copy the full value. Do not truncate critical compared identifiers; provide scrolling, expansion, or a responsive detail view that exposes their full values.

## Copy

| Candidate | Observe |
|---|---|
| `Senior Product Design Engineer, Platform Infrastructure` | Long secondary text and alignment with multiline names. |
| `Invitation expired 12 days ago` | Status-badge width and whether essential adjacent content remains accessible. |
| `Benachrichtigungseinstellungen`, `Paramètres de confidentialité et de sécurité` | Translation expansion and unbroken words, only where supported copy can take those values. |
| Twelve realistic tags; one `customer-feedback-from-enterprise-onboarding` tag | Wrapping, disclosure, and access to every tag; a `+N` control is one option, not a requirement. |
| `Untitled`, empty string, whitespace-only text | Product-defined absence semantics and heading/row geometry. |
| A newline in an accepted field; a plausible pasted description at its accepted limit | Whitespace behavior, clamping, expansion, and textarea growth. |
| Literal `<b>draft</b>`, `&amp;`, `**bold**` | Render according to the field's declared text/markup contract at the existing correct boundary. Do not double escape text or insert untrusted HTML. |

For an explicitly authorized malformed-input probe, a harmless markup-shaped value can check defensive text handling. Keep it distinct from valid rich-text or Markdown content; literal Markdown is not inherently a rendering failure.

## Numbers

| Candidate | Observe |
|---|---|
| `0`, `1`, `1284`, `1000000`, and the accepted upper bound | Empty states, plural rules, locale formatting, badge width, and precision. |
| `12345678.9` as currency; `-42.5` where negatives are valid | Currency fraction digits, sign/accounting format, comparison, and overflow. |
| A computed decimal such as `0.1 + 0.2` | Display rounding without changing stored meaning. |
| `142%`, `-3%` where the metric permits them | Whether over/under-target values are valid; display and meter geometry must match that contract. |
| `99` → `100`; values formatted in supported `de-DE` and `en-US` locales | Width changes, alignment, grouping, and decimal separators. Tabular figures may help changing columns. |
| Separately labeled `null`, `undefined`, `NaN`, or out-of-range numbers | Defensive behavior only when relevant to this boundary; do not call schema-invalid values expected production input. |

Use existing locale-aware formatters, such as `Intl.NumberFormat` or `Intl.PluralRules`, where appropriate. Do not hide precision needed for comparison behind a compact count or truncate critical numbers, amounts, and dates; use an accessible responsive representation that exposes the full values.

## Collections

| Candidate | Observe |
|---|---|
| Empty and one-item lists | No-results state, pluralization, controls, and one-card layouts. |
| Exactly page size and page size + 1 | Page boundaries, totals, and empty extra pages. |
| Realistic upper-bound list; 1,000+ only when plausible and supported | Render/scroll cost, pagination or virtualization behavior, and memory. Record baseline and test conditions before attributing a performance failure. |
| One item with much more valid content than adjacent items | Row/card height, alignment, and access to actions. |
| Identical names with different stable IDs or secondary attributes | Distinguishability, selection, stable keys, and correct item actions. |

## Time

| Candidate | Observe |
|---|---|
| Now; just across the app's minute/day/month/year thresholds | Relative-time wording and update boundaries. Freeze the fixture clock for replay. |
| 12 days ago, 11 months ago, 3 years ago; a future date | Product-defined relative/absolute formatting and correct tense. |
| `1970-01-01`; separately missing/invalid timestamps | Distinguish a legitimate epoch date from a documented sentinel; do not assume it is always a defect. |
| `2025-12-31T23:30:00-08:00`; relevant daylight-saving boundaries | Supported timezone and calendar-day behavior. |
| `1,284 hours` or the accepted long duration | Duration units, precision, and width. |

Prefer the project's locale/time utilities or `Intl.RelativeTimeFormat` and `Intl.DateTimeFormat`. There is no universal threshold for switching to an absolute date.

## Media

| Local or stubbed candidate | Observe |
|---|---|
| Missing avatar; intercepted image failure or slow response | Fallback parity, alt text, loading state, and layout shift. |
| 4000×200 panorama; 200×4000 portrait fixture | Aspect ratio, crop semantics, and card bounds; `object-fit: cover` is suitable only when cropping is intended. |
| Transparent logo; low-contrast logo in supported dark mode | Visibility against actual backgrounds. |

Use generated/local assets or existing fixtures, not real people's media or external hosts. Reserve dimensions or aspect ratio when the layout calls for it; do not prescribe cropping for content whose full extent matters.

## State

| Candidate | Observe |
|---|---|
| Loading, API error, retry, and no-results states | Layout continuity, readable recovery, focus, and actions; do not trigger live failures. |
| Partial optional data mixed across rows | Fallbacks, omitted lines, orphan separators, and alignment. |
| All accepted status enum values | Label width, badge contrast, and valid action differences. |
| No permission; current user; selected/unselected items | Reachable controls, correct disabled semantics, selection, and identity-specific actions through stubs. |

## Environment and diagnosis

Use the real container first: a 280px sidebar is different from a full-width page. Cover relevant narrow/wide supported bounds, browser zoom or larger text, locales, dark mode, RTL, keyboard, and touch/pointer. A 320px viewport or 2560px screen is a useful candidate only if it exercises the product's supported layout. Inspect focus, selection, copy, and full-value disclosure; hover alone and `title` alone are insufficient access paths.

| Observed symptom | Investigate before choosing a fix |
|---|---|
| Squashed avatar/icon, clipped trailing action | Computed flex basis/shrink, intrinsic sizes, available width, and the intended yielding element. Fixed-size elements may need nonshrinking space. |
| Overflowing text or grid column | Intrinsic minimum sizes and break opportunities. `min-width: 0`, `minmax(0, 1fr)`, or `overflow-wrap` may apply at the actual responsible element. |
| Wrapped badge or long button label | Supported label length, width constraints, and a deliberate wrap/overflow policy; `nowrap` can merely move the failure elsewhere. |
| Clipped glyphs or final row | Computed line height, fixed height, overflow, scroll reachability, and intentional masks. |
| Misaligned multiline row | Alignment semantics and variable height; top alignment is one product choice. |
| Indistinguishable truncated values | Which characters carry identity, responsive space, and accessible full-value/copy paths. Middle truncation or expansion may help. |
| Large-list stutter | Measured rendering/interaction cost and data volume; pagination or virtualization has product and accessibility tradeoffs. |

Treat a visual symptom as observed only with an actual rendered observation. A likely mechanism from source is inferred until checked. Record unavailable environments or captures; do not invent screenshots or claim exhaustive coverage.
