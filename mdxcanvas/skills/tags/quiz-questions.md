---
type: skill
description: Load when writing or editing <question> tags, selecting a question type, or encoding answers, points, and feedback.
---

# `<question>` Types

## When to Use This Reference

Use this reference when working with:

- Writing any quiz question
- Choosing between question types (multiple-choice, matching, fill-in, numerical, etc.)
- Setting per-question point values
- Using `id` on questions generated in a loop

## Non-Negotiables

- Every `<question>` requires an explicit `id` and `type`, not only questions generated in loops.
- Use `<correct>` and `<incorrect>` tags exactly as shown for each type — structure varies by type.
- Preserve each question's `id` when changing its text; IDs are namespaced by their quiz.

## Answer Feedback

Some question types support per-answer feedback that maps directly to the Canvas API:

- `multiple-choice` and `multiple-answers`: use `answer_comments="..."` on `<correct>` and `<incorrect>`
- `matching`: use `answer_comments="..."` on `<pair>`
- `fill-in-the-blank` and `fill-in-multiple-blanks`: use `answer_comments="..."` on `<correct>`
- `numerical`: use `answer_comments="..."` on `<correct>`
- `multiple-tf`: use `answer_comments="..."` on `<correct>` and `<incorrect>` to populate `correct-comments` on each generated true/false subquestion
- `true-false`: use question-level `correct-comments` and `incorrect-comments`

---

## Common Question Attributes

Examples here are question fragments to place as direct children of `<quiz><questions>`. All types require `type` and `id` (alias `question_id`); `name` is accepted but ignored. `text` accepts only those identity/type fields, not points or feedback. Other types normally accept the common fields below, with the `multiple-tf` limitation noted later. See [Shared parsing rules](parsing-rules.md).

| Attribute         | Required | Description                                                                     |
|-------------------|----------|---------------------------------------------------------------------------------|
| `type`            | yes      | Question type (see sections below)                                              |
| `id`              | yes      | Stable identifier required for every question, including static questions      |
| `points_possible` | no       | Points for this question; also accepted as `points`                             |

| Additional common attribute(s) | Behavior |
|---|---|
| `correct-comments` / `correct_comments` | String feedback |
| `neutral-comments` / `neutral_comments` | String feedback |
| `incorrect-comments` / `incorrect_comments` | String feedback |
| `text-after-answers` / `text_after_answers` | String appended-field value |
| `name` | Ignored, not a display title |

Feedback attributes are not parsed from child elements. On types that strip answer/feedback children, legacy `<correct-comments>` children are removed from the body but do not set feedback. Essay and file-upload retrieve the whole body, so such children remain content, not feedback settings. Prefer the documented attributes.

### `id`

Assign a stable ID to every question. Current parsing rejects questions without `id`:

```xml
<question type="essay" id="midterm-q0">
    What is a large language model?
</question>
```

### `points_possible` / `points`

Points are finite decimals. Default is 1 for true-false, multiple-choice, multiple-answers, single-blank, essay, file-upload, and numerical. Matching defaults to pair count; explicit multi-blank defaults to the number of `<correct>` elements (not unique blank count); inline-filled blanks defaults to the generated answer count; multiple-tf defaults to statement count and divides the total evenly across generated questions. `text` has no points field. Override the default point value per question. Use `points="0"` for checklist-style questions that carry no grade
weight:

```xml
<!-- Worth 0 points — used as a checklist -->
<question id="project-checklist" type="multiple-answers" points="0">
    Project checklist:
    <correct>I completed the baseline requirements</correct>
    <correct>I pushed my code to GitHub</correct>
</question>

<!-- Custom point value -->
<question id="hours-worked" type="essay" points_possible="3">
    Estimate your hours worked this week.
</question>
```

---

## `text`

Displays a block of instructional or contextual text. Does not require an answer.

```xml
<question id="instructions" type="text">
    This is a text question that provides instructions for the following questions.
</question>
```

---

## `true-false`

Presents a True/False question. Requires the `answer` attribute (`true` or `false`).
Feedback should be provided with the standard question-level `correct-comments` and `incorrect-comments` fields.

```xml
<question id="sky-color" type="true-false" answer="true"
          correct-comments="Correct"
          incorrect-comments="The sky is blue under normal daylight conditions.">
    Is the sky blue?
</question>
```

---

## `multiple-choice`

Single-answer multiple choice. For a usable single-answer question, supply exactly one `<correct>` and a nonempty set of `<incorrect>` options; the parser itself does not enforce those counts. Optional per-answer feedback may be provided with `answer_comments`.

```xml
<question id="france-capital" type="multiple-choice">
    What is the capital of France?

    <correct answer_comments="Exactly right">Paris</correct>
    <incorrect answer_comments="London is the capital of the UK">London</incorrect>
    <incorrect>Berlin</incorrect>
    <incorrect>Madrid</incorrect>
</question>
```

---

## `multiple-answers`

Allows selection of multiple correct answers. Direct `<correct>` / `<incorrect>` children become options with weights 100 / 0; the same fixed weights apply to multiple choice. No arbitrary per-option partial-credit field is exposed, and Canvas determines combination grading. Option bodies may contain rendered Markdown. These option children are not parsed with `parse_settings`, so extra option attributes can be silently ignored; only `answer_comments` is consumed. Provide a deliberate nonempty answer set; the parser does not validate counts. Optional per-answer feedback may be provided with `answer_comments`.

```xml
<question id="programming-languages" type="multiple-answers">
    Which of the following are programming languages?

    <correct answer_comments="Yes">Python</correct>
    <correct>JavaScript</correct>
    <incorrect answer_comments="HTML is markup, not a programming language">HTML</incorrect>
    <incorrect>CSS</incorrect>
</question>
```

---

## `matching`

Use `points`, not `points_possible`, to override the score: the current parser accepts the alias but then overwrites it with pair count unless `points` is supplied. Each `<pair>` requires string `left` and `right`, and accepts `answer_comments`. Distractors are joined from direct `<distractors>` children and blank lines removed. Pair search is recursive. No minimum pair count is enforced by the parser; provide a meaningful nonempty set.

Students match items from two columns. Use `<pair>` for correct matches and optionally `<distractors>` for extra
wrong-side items. Optional per-pair feedback may be provided with `answer_comments`.

```xml
<question id="country-capitals" type="matching">
    Match the following countries with their capitals.

    <pair left="France" right="Paris" answer_comments="Paris is the capital of France." />
    <pair left="Germany" right="Berlin" />
    <pair left="Spain" right="Madrid" />

    <distractors>
        London
        Rome
        Lisbon
    </distractors>
</question>
```

---

## `multiple-tf`

Expands into a text-only header with the source ID, then separate true/false questions with IDs `<id>_0`, `<id>_1`, etc. Reordering or inserting statements changes generated identities; use individual true-false questions for independently stable identities. Provide at least one statement: an empty set fails. Total points are divided evenly; fractional results are allowed. The first header parse accepts only identity/type/name and points, so question-level feedback attributes are rejected even though the later expansion parse lists them. Statement discovery is recursive and regex-based; avoid nesting answer or feedback elements inside statements. Optional `answer_comments` on each `<correct>` / `<incorrect>` child becomes question-level feedback on the generated true/false subquestion.

```xml
<question id="language-statements" type="multiple-tf">
    Which of the following statements are true?

    <correct answer_comments="Yes, Python is a programming language.">Python is a programming language.</correct>
    <incorrect answer_comments="No, HTML is markup.">HTML is a programming language.</incorrect>
    <correct>JavaScript can be used for web development.</correct>
    <incorrect>CSS is a programming language.</incorrect>
</question>
```

---

## `fill-in-the-blank`

A single blank the student must fill in. At least one `[name]` marker is checked. Each `<correct>` requires `text` (alias `answer_text`), optionally `blank_id` (defaults to the first marker), `answer_weight` (default 100; explicit value passed as string), and `answer_comments`. The parser does not require exactly one marker or verify answer coverage. Use `[blank]` in the sentence and `<correct text="..." />` for valid answers. Optional per-answer feedback may be provided with `answer_comments`.

```xml
<question id="capital-blank" type="fill-in-the-blank">
    The capital of France is [blank].

    <correct text="Paris" answer_comments="Exactly right." />
</question>
```

---

## `fill-in-multiple-blanks`

Multiple named blanks. Each `<correct>` requires `text` / `answer_text` and `blank` / `blank_id`; `answer_weight` defaults to 100 (explicit values stay strings). The parser does not check marker/answer coverage. Multiple accepted forms for a blank are separate answers and each contributes to the default point total. Each `<correct>` must specify the matching `blank` name. Optional per-answer feedback may be provided with `answer_comments`.

```xml
<question id="flag-counts" type="fill-in-multiple-blanks">
    The U.S. flag has [stripes] stripes and [stars] stars.

    <correct text="13" blank="stripes" answer_comments="There are 13 original colonies." />
    <correct text="50" blank="stars" />
</question>
```

---

## `fill-in-multiple-blanks-filled-answers`

Shorthand: embed correct answers directly using `[[answer]]` syntax. At least one filled marker is required. Replacement is regex-based, not mathematical interpretation: avoid literal double brackets elsewhere. Generated blank IDs are A…Z, AA…ZZ, etc. in encounter order (up to nine repeated letters). Each gets weight 100; there is no per-blank tolerance, alternate answer, or feedback field.

```xml
<question id="inline-flag-counts" type="fill-in-multiple-blanks-filled-answers">
    The U.S. flag has [[13]] stripes and [[50]] stars.
</question>
```

---

### Table example

Question fragment for a `.md` source: only cells with double brackets become response blanks; other values remain given context.

```xml
<question id="path-state" type="fill-in-multiple-blanks-filled-answers" points="4">
    Complete the approved algorithm-state table.

    | Node | Initial | After step |
    |---|---|---|
    | A | 0 | [[0]] |
    | B | inf | [[1]] |
    | C | inf | [[3]] |
    | D | inf | [[inf]] |
</question>
```

## `essay`

Open-ended text response. No `answer` or child tags required. Common points and feedback attributes are supported; no rubric or answer-key child structure is defined. Body retrieval retains all child content.

```xml
<question id="technology-impact" type="essay">
    Discuss the impact of technology on modern education.
</question>
```

---

## `file-upload`

Prompts the student to upload a file as their response. Supports common finite-decimal `points` / `points_possible` (default 1) and feedback attributes, just like essay. File-type/naming instructions in prose are not enforced by this tag.

```xml
<question id="project-upload" type="file-upload">
    Upload your project files for review.
</question>
```

---

## `numerical`

Accepts a numerical answer. `numerical_answer_type` is required and must be `exact`, `range`, or `precision`. Each `<correct>` requires both attributes shown for that mode, plus optional `answer_comments`; no `answer_weight` is accepted here. Values are passed as strings without numeric validation. At least one meaningful answer should be supplied; the parser does not enforce answer count. Units belong in the prompt. The current numerical prompt retrieval retains `<correct>` elements in its HTML, unlike the option/fill-in parsers; inspect rendered output for answer leakage before release. Supports three modes via `numerical_answer_type`. Optional per-answer feedback may be provided with `answer_comments` on each `<correct>` tag.

### Exact Answer

```xml
<question id="pi-exact" type="numerical" numerical_answer_type="exact">
    What is π?

    <correct answer_exact="3.14159" answer_error_margin="0.0001" answer_comments="Rounded correctly." />
</question>
```

### Range Answer

```xml
<question id="interval-value" type="numerical" numerical_answer_type="range">
    Give a value for x such that 1 ≤ x ≤ 10.

    <correct answer_range_start="1" answer_range_end="10" answer_comments="Any value in this interval is accepted." />
</question>
```

### Precision Answer

`answer_precision` is forwarded unchanged; verify instructor-approved significant-digit/tolerance behavior in the target rather than inferring it from this example.

```xml
<question id="pi-precision" type="numerical" numerical_answer_type="precision">
    What is the value of π?

    <correct answer_approximate="3.14159" answer_precision="5" answer_comments="Review the instructor-approved precision requirement." />
</question>
```
