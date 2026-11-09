---
type: skill
description: Load for quiz representation, compound question composition, instructor ownership, reuse, generation, and validation. Load tag references for syntax.
---

# Representing quizzes and questions

## Authority and instructor ownership

[Quiz tags](tags/quiz.md) and [question tags](tags/quiz-questions.md) are authoritative for syntax, settings, supported types, scoring defaults, feedback, and parser limitations. [Helpers](tags/helper-tags.md) defines includes, links, downloads, diagrams, and slides; [shared parsing rules](tags/parsing-rules.md) defines conversions, dates, and overrides. Load these before implementation rather than treating this document as a second attribute reference.

The instructor owns prompts, correctness, accepted answers, tolerances, scoring, attempts, answer visibility, navigation restrictions, access codes, dates, and publication. Encode approved choices; do not invent answer keys, select settings to prevent sharing, or substitute a different interaction without approval. A parser capability is an option, not a teaching recommendation.

## Identity, ordering, and updates

Preserve quiz identity through title changes. For older implicit-title identities, establish the previously deployed title as explicit ID in a separate migration before renaming. Each question must have an explicit, unique, durable ID within its quiz. Generated IDs come from immutable data keys, not current list positions or mutable wording.

Source order determines question order after includes and rendering. A resource omitted by a conditional disappears from the graph and can affect cleanup; preserve its ID if it returns. Some source elements expand into several Canvas questions; consult the question reference before reordering their children because generated sub-identities may be positional. Use independently identified questions when statement-level identity must survive insertion/reordering.

Existing submissions affect update handling: deployment may require a manual Canvas review/save rather than ordinary unpublish/edit/republish. Do not infer that successful source validation establishes safe live editing. Handoff operational review to the Deployment Engineer.

## Rich content and representation

Markdown question content can represent prose, emphasis, lists, tables, code, math, links, and images. Its availability depends on the source suffix and preprocessing context. Escape XML-sensitive attribute characters and balance XML tags around Markdown. Verify actual rendering, especially code fences, tables, math, and any content that resembles blank markers or answer elements.

Use meaningful alternative text and a text representation sufficient for the intended response when images/tables are complex. Helper paths follow the current source/include context. A link or download inside a question is content, not a response field. Referenced assets and target resources must exist in the reachable graph.

Keep answer keys and instructor-only material out of prompts/downloads. Parser extraction is not uniform across types: consult the question reference's prompt/feedback caveats and inspect rendered output rather than assuming answer tags were removed.

## Compound question styles

These are composition options to discuss with the instructor, not new parser types.

### Information-only containers

An instructor-approved quiz may act as an ordered collection of instructions, links, or downloads using text-only entries. Choosing its grading/survey behavior is still a substantive decision. Check target behavior; the parser permitting an empty or informational container does not establish the intended student workflow.

### Shared scenario followed by responses

Place approved context before the response questions. Verify the scenario remains accessible under the instructor's one-question-at-a-time and backtracking choices. Keep each response independently identified; avoid wording tied to mutable question numbers.

### Tables, matrices, and algorithm-state completion

Inline-filled blanks suit cells with one exact textual answer; explicit named blanks permit alternate accepted forms. Separate numerical questions are more suitable when tolerance is needed. Table blanks do not imply numeric interpretation or per-cell tolerance. Confirm that any representation change preserves the approved task.

### Classification

Matching with repeated right-side labels can represent assignment to categories. Review the offered vocabulary and distractors with the instructor. This is not an arbitrary drag-and-drop interaction. Do not promise Canvas semantics beyond the validated representation.

### Independent true/false statements

Expanded statements are convenient, but individual questions are preferable when independently stable IDs, distinct points, or separate feedback are required. The question reference documents the expansion's positional IDs and parsing restrictions.

### Calculation plus submitted work

Combine an automatically checked result with a separate essay or file-upload response when approved. These remain separate ordered Canvas questions with their own point values; they are not a single combined response or shared rubric.

### Ordering or ranking

There is no dedicated ordering type in the current registry. Named position blanks, matching items to position labels, or essay responses can approximate it. Choose only with instructor approval based on exact checking versus free response, not implementation convenience.

### Unsupported interactions

Do not invent formula, hotspot, stimulus, bank, group, or random-draw type names. A fixed numerical result, an image-based option question, or shared context plus responses may represent part of the intent. Otherwise leave the interaction for a separately approved Canvas-side workflow and document the limitation.

## Reuse and generation

Keep reusable question fragments in authoritative source files. The helper reference explains direct insertion versus wrapper insertion; questions must be direct children of the question container after preprocessing. Includes can change path context and require local args, so validate the rendered result, not just the fragment in isolation.

Jinja generation can consume structured MarkdownData, YAML, or other supported args. Heading names, table columns, and dictionary keys become a source schema. Preserve that contract and stable literal keys. Example template fragment (requires a containing questions block and final `.jinja` suffix):

{% raw %}
```xml
{% set items = [
  {"id": "speed", "label": "speed", "answer": "distance / time"},
  {"id": "density", "label": "density", "answer": "mass / volume"}
] %}
{% for item in items %}
<question id="formula-{{ item.id }}" type="fill-in-the-blank">
  The formula for {{ item.label }} is [blank].
  <correct text="{{ item.answer }}" />
</question>
{% endfor %}
```
{% endraw %}

The literal `id` values are stable data, not titles or positions. Conditional generation must preserve uniqueness and intentionally handle empty sets. Do not regenerate IDs when wording or ordering changes.

## Representation validation

Before handoff:

- Load the quiz, question, and relevant helper references; check their current parser caveats.
- Verify direct-child structure after Jinja/includes and stable unique quiz/question IDs.
- Confirm the chosen representation preserves the instructor's prompt, approved answers, scoring, tolerances, and interaction.
- Validate meaningful nonempty answer sets and complete marker/answer coverage even where the parser does not enforce them.
- Verify matching score overrides, expanded-question point distribution and identity, and intended blank counts/accepted alternatives against the question reference.
- Check totals deliberately: quiz-level totals are not an MDXCanvas substitute for reviewing represented question scores.
- Inspect rendered prompts and feedback for malformed HTML, ignored settings, answer leakage, and inaccessible shared context.
- Validate links, local assets, archive maps, tables, code, math, image alternatives, and audience-specific branches.
- Confirm all affected release/access/visibility controls match approved intent; omitted values do not necessarily reset existing state.
- Resolve unknown-attribute errors; ignored fields do not configure Canvas.
- Keep module references on stable quiz IDs.
- Report offline checks separately from target-state validation, deployment, publication, and manual review required for quizzes with submissions.
