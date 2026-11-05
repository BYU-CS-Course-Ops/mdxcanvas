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

- Always set a `type` attribute on every `<question>` tag.
- Use `<correct>` and `<incorrect>` tags exactly as shown for each type — structure varies by type.
- Use `id` on questions generated programmatically so they can be updated without duplication.

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

These attributes apply to any question type:

| Attribute         | Required | Description                                                                     |
|-------------------|----------|---------------------------------------------------------------------------------|
| `type`            | yes      | Question type (see sections below)                                              |
| `id`              | no       | Stable identifier for the question (useful when generating questions in a loop) |
| `points_possible` | no       | Points for this question; also accepted as `points`                             |

### `id`

Assign a stable ID when generating questions programmatically or referencing them elsewhere:

```xml
<question type="essay" id="midterm-q0">
    What is a large language model?
</question>
```

### `points_possible` / `points`

Override the default point value per question. Use `points="0"` for checklist-style questions that carry no grade
weight:

```xml
<!-- Worth 0 points — used as a checklist -->
<question type="multiple-answers" points="0">
    Project checklist:
    <correct>I completed the baseline requirements</correct>
    <correct>I pushed my code to GitHub</correct>
</question>

<!-- Custom point value -->
<question type="essay" points_possible="3">
    Estimate your hours worked this week.
</question>
```

---

## `text`

Displays a block of instructional or contextual text. Does not require an answer.

```xml
<question type="text">
    This is a text question that provides instructions for the following questions.
</question>
```

---

## `true-false`

Presents a True/False question. Requires the `answer` attribute (`true` or `false`).
Feedback should be provided with the standard question-level `correct-comments` and `incorrect-comments` fields.

```xml
<question type="true-false" answer="true"
          correct-comments="Correct"
          incorrect-comments="The sky is blue under normal daylight conditions.">
    Is the sky blue?
</question>
```

---

## `multiple-choice`

Single-answer multiple choice. Requires at least one `<correct>` and one or more `<incorrect>` options. Optional per-answer feedback may be provided with `answer_comments`.

```xml
<question type="multiple-choice">
    What is the capital of France?

    <correct answer_comments="Exactly right">Paris</correct>
    <incorrect answer_comments="London is the capital of the UK">London</incorrect>
    <incorrect>Berlin</incorrect>
    <incorrect>Madrid</incorrect>
</question>
```

---

## `multiple-answers`

Allows selection of multiple correct answers. Optional per-answer feedback may be provided with `answer_comments`.

```xml
<question type="multiple-answers">
    Which of the following are programming languages?

    <correct answer_comments="Yes">Python</correct>
    <correct>JavaScript</correct>
    <incorrect answer_comments="HTML is markup, not a programming language">HTML</incorrect>
    <incorrect>CSS</incorrect>
</question>
```

---

## `matching`

Students match items from two columns. Use `<pair>` for correct matches and optionally `<distractors>` for extra
wrong-side items. Optional per-pair feedback may be provided with `answer_comments`.

```xml
<question type="matching">
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

Presents multiple True/False statements. Students select which are true. Optional `answer_comments` on each `<correct>` / `<incorrect>` child becomes question-level feedback on the generated true/false subquestion.

```xml
<question type="multiple-tf">
    Which of the following statements are true?

    <correct answer_comments="Yes, Python is a programming language.">Python is a programming language.</correct>
    <incorrect answer_comments="No, HTML is markup.">HTML is a programming language.</incorrect>
    <correct>JavaScript can be used for web development.</correct>
    <incorrect>CSS is a programming language.</incorrect>
</question>
```

---

## `fill-in-the-blank`

A single blank the student must fill in. Use `[blank]` in the sentence and `<correct text="..." />` for valid answers. Optional per-answer feedback may be provided with `answer_comments`.

```xml
<question type="fill-in-the-blank">
    The capital of France is [blank].

    <correct text="Paris" answer_comments="Exactly right." />
</question>
```

---

## `fill-in-multiple-blanks`

Multiple named blanks. Each `<correct>` must specify the matching `blank` name. Optional per-answer feedback may be provided with `answer_comments`.

```xml
<question type="fill-in-multiple-blanks">
    The U.S. flag has [stripes] stripes and [stars] stars.

    <correct text="13" blank="stripes" answer_comments="There are 13 original colonies." />
    <correct text="50" blank="stars" />
</question>
```

---

## `fill-in-multiple-blanks-filled-answers`

Shorthand: embed correct answers directly using `[[answer]]` syntax.

```xml
<question type="fill-in-multiple-blanks-filled-answers">
    The U.S. flag has [[13]] stripes and [[50]] stars.
</question>
```

---

## `essay`

Open-ended text response. No `answer` or child tags required.

```xml
<question type="essay">
    Discuss the impact of technology on modern education.
</question>
```

---

## `file-upload`

Prompts the student to upload a file as their response.

```xml
<question type="file-upload">
    Upload your project files for review.
</question>
```

---

## `numerical`

Accepts a numerical answer. Supports three modes via `numerical_answer_type`. Optional per-answer feedback may be provided with `answer_comments` on each `<correct>` tag.

### Exact Answer

```xml
<question type="numerical" numerical_answer_type="exact">
    What is π?

    <correct answer_exact="3.14159" answer_error_margin="0.0001" answer_comments="Rounded correctly." />
</question>
```

### Range Answer

```xml
<question type="numerical" numerical_answer_type="range">
    Give a value for x such that 1 ≤ x ≤ 10.

    <correct answer_range_start="1" answer_range_end="10" answer_comments="Any value in this interval is accepted." />
</question>
```

### Precision Answer

```xml
<question type="numerical" numerical_answer_type="precision">
    What is the value of π?

    <correct answer_approximate="3.14159" answer_precision="5" answer_comments="At least five digits are required." />
</question>
```
