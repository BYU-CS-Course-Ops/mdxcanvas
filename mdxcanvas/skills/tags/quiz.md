---
type: skill
description: Load when creating or editing <quiz> containers, settings, descriptions, or section overrides.
---

# `<quiz>` Tag

## When to Use This Reference

Use this reference when working with:

- Creating or editing any quiz
- Setting availability windows, time limits, or attempt counts
- Adding access codes or show-answers dates
- Configuring `only_visible_to_overrides` or section-specific overrides
- Understanding the quiz structure (`<description>`, `<questions>`)

## Non-Negotiables

- For response-bearing quizzes, provide a `<questions>` block. The parser permits its omission; an empty block warns rather than fails.
- Shuffling, attempt limits, access controls, and answer visibility are instructor choices, not universal requirements.
- Every quiz requires `id` and `title`, and every question requires `id` and `type`. Preserve IDs when changing display text.
- See [Shared parsing rules](parsing-rules.md) for dates, defaults, aliases, and overrides.

---

## Quiz Structure

The `<quiz>` tag contains two child elements:

- `<description>` — optional instructions shown to students before they begin
- `<questions>` — optional to the parser; only direct `<question>` children are processed. An empty block logs a warning. Top-level prose outside recognized child elements is ignored.
- Some question types support per-answer feedback:
  `answer_comments` on `<correct>` / `<incorrect>`, `answer_comments` on `<pair>`, `answer_comments` on `<correct>` for fill-in and numerical questions, `answer_comments` on `<correct>` / `<incorrect>` for `multiple-tf`, and question-level `correct-comments` / `incorrect-comments` on `true-false`

```xml
<quiz id="chapter-1" title="Chapter 1 Quiz"
      due_at="Jan 20, 2025, 11:59 PM"
      shuffle_answers="true"
      allowed_attempts="2"
      scoring_policy="keep_highest">

    <description>
        Answer all questions. You have 2 attempts.
    </description>

    <questions>
        <question id="addition" type="multiple-choice">
            What is 2 + 2?
            <correct>4</correct>
            <incorrect>3</incorrect>
            <incorrect>5</incorrect>
        </question>
    </questions>
</quiz>
```

---

## Default Settings

When not specified, MDXCanvas emits these defaults:

- `quiz_type="assignment"`
- `show_correct_answers="true"`
- `allowed_attempts="-1"` (unlimited attempts)
- `scoring_policy="keep_highest"`

Although `shuffle_answers` is declared with a false default, the current `parse_settings` implementation skips falsy defaults. Omitting it sends no `shuffle_answers` key: creation uses Canvas's default, and updates do not explicitly disable existing shuffling. Set `shuffle_answers="false"` when no shuffling must be enforced, or `"true"` to enable it.

These are implementation facts, not recommended assessment settings. The examples below explicitly choose some settings.

---

## Attributes

| Attribute                   | Required | Description                                                         |
|-----------------------------|----------|---------------------------------------------------------------------|
| `title`                     | yes      | Quiz title shown in Canvas                                          |
| `id`                        | yes      | Stable identifier; no title fallback                                |
| `due_at`                    | no       | Date in any supported form (see shared parsing rules) |
| `available_from`            | no       | Date when quiz becomes available                                    |
| `available_to`              | no       | Date when quiz closes                                               |
| `assignment_group`          | no       | Stable `id` of a `<group>` declared in `<assignment-groups>`          |
| `shuffle_answers`           | no       | `"true"` to randomize answer order per student                      |
| `time_limit`                | no       | Integer minutes; omission sends no limit setting (does not clear an existing limit) |
| `allowed_attempts`          | no       | Number of attempts; `-1` for unlimited                              |
| `scoring_policy`            | no       | `keep_highest` (default), `keep_latest`, `keep_average`             |
| `access_code`               | no       | Passcode students must enter to access the quiz                     |
| `quiz_type`                 | no       | `assignment` (default), `practice_quiz`, `graded_survey`            |
| `points_possible`           | no       | Finite decimal total forwarded to Canvas; MDXCanvas does not calculate a total here |
| `show_correct_answers_at`   | no       | Date when correct answers become visible; all supported date forms accepted |
| `only_visible_to_overrides` | no       | `"True"` — hide quiz from students not in an `<override>` section   |

---

### Remaining supported attributes and aliases

| Attribute(s) | Parsing / effective default |
|---|---|
| `assignment_group_id` | Alias of `assignment_group`; stable assignment-group source ID |
| `unlock_at`, `lock_at` | Date aliases of `available_from`, `available_to` |
| `hide_correct_answers_at` | Date |
| `show_correct_answers` | Boolean; emitted default true |
| `show_correct_answers_last_attempt`, `one_question_at_a_time`, `cant_go_back`, `one_time_results`, `published` | Boolean; omitted when absent |
| `hide_results` | String, not boolean-parsed |
| `position` | Integer |

All other optional attributes without the emitted defaults above are omitted. `quiz_type`, `scoring_policy`, `hide_results`, and `access_code` are string pass-throughs; the parser does not validate Canvas enums. Survey variants include `survey` and `graded_survey`; choose only instructor-approved settings. See [Shared parsing rules](parsing-rules.md).

## Key Attribute Details

Examples containing `...` are setting fragments, not complete response-bearing quizzes.

### `id`

`id` is required now. Preserve it when changing the quiz title.

```xml
<quiz id="midterm_exam" title="Midterm Exam">
    ...
</quiz>
```

For a legacy quiz deployed by an older version using implicit title identity, first add `id` equal to the previously deployed title without renaming it. Deploy that identity migration separately before a later rename. Current parsing rejects quizzes without `id`.

### `shuffle_answers`

```xml
<quiz id="quiz-1" title="Quiz 1" shuffle_answers="true">
    ...
</quiz>
```

### `time_limit`

```xml
<quiz id="quiz-1" title="Quiz 1" time_limit="30">
    ...
</quiz>
```

### `allowed_attempts`

```xml
<quiz id="quiz-1" title="Quiz 1" allowed_attempts="3">
    ...
</quiz>
```

Use `-1` for unlimited attempts.

### `access_code`

```xml
<quiz id="quiz-1" title="Quiz 1" access_code="secure123">
    ...
</quiz>
```

### `quiz_type`

```xml
<quiz id="practice-quiz" title="Practice Quiz" quiz_type="practice_quiz">
    ...
</quiz>
```

### `scoring_policy`

```xml
<quiz id="quiz-1" title="Quiz 1" allowed_attempts="3" scoring_policy="keep_highest">
    ...
</quiz>
```

### `show_correct_answers_at`

```xml
<quiz id="quiz-1" title="Quiz 1" show_correct_answers_at="Jan 20, 2025, 12:00 PM">
    ...
</quiz>
```

### `only_visible_to_overrides`

Requests visibility restricted to overrides. This is independent of `access_code`; choose either or both only according to instructor-approved access policy. Example section IDs must exist in the target.

```xml
<quiz id="lecture-3a" title="Lecture 3a Quiz"
      access_code="bit-is-cool"
      only_visible_to_overrides="True">
    <overrides>
        <override section_id="34280" due_at="Jan 13, 2026, 11:59 PM"/>
    </overrides>
    ...
</quiz>
```

---

## Section-Specific Dates

Use `<overrides>` to set different due dates per course section:

```xml
<quiz id="midterm-exam" title="Midterm Exam" due_at="Feb 15, 2025, 11:59 PM">
    <overrides>
        <override section_id="12345" due_at="Feb 20, 2025, 11:59 PM" />
        <override section_id="67890" due_at="Feb 22, 2025, 11:59 PM" />
    </overrides>

    <description>
        Complete the midterm exam...
    </description>

    <questions>
        ...
    </questions>
</quiz>
```

---

## Resource example (requires assignment group `quizzes`)

```xml
<quiz id="example-quiz"
    title="Example Quiz"
    due_at="Jan 1, 2025, 11:59 PM"
    available_from="Jan 1, 2025, 9:00 AM"
    available_to="Jan 1, 2025, 11:59 PM"
    assignment_group="quizzes"
    shuffle_answers="true"
    time_limit="30"
    allowed_attempts="3"
    scoring_policy="keep_highest"
    points_possible="2">

    <description>
        This quiz includes various question types.
    </description>

    <questions>
        <question id="sky-color" type="true-false" answer="true"
                  correct-comments="Correct" incorrect-comments="The sky is blue under normal daylight conditions.">
            Is the sky blue?
        </question>

        <question id="france-capital" type="multiple-choice">
            What is the capital of France?

            <correct answer_comments="Exactly right">Paris</correct>
            <incorrect answer_comments="London is the capital of the UK">London</incorrect>
            <incorrect>Berlin</incorrect>
            <incorrect>Madrid</incorrect>
        </question>
    </questions>
</quiz>
```

---

## Quick Example

A response-bearing resource example, requiring assignment group `quizzes`:

```xml
<quiz id="python-basics" title="Python Basics Quiz"
      due_at="Jan 15, 2025, 11:59 PM"
      assignment_group="quizzes"
      shuffle_answers="true"
      allowed_attempts="2"
      scoring_policy="keep_highest">

    <description>
        This quiz covers Python variables, data types, and basic operators.
    </description>

    <questions>
        <question id="case-sensitive" type="true-false" answer="true"
                  correct-comments="Correct" incorrect-comments="Python variable names are case-sensitive.">
            Python variable names are case-sensitive.
        </question>

        <question id="variable-name" type="multiple-choice">
            Which of the following is a valid Python variable name?

            <correct answer_comments="Underscores are allowed after the first character">my_var</correct>
            <incorrect answer_comments="Variable names cannot start with a number">2myvar</incorrect>
            <incorrect>my-var</incorrect>
            <incorrect>my var</incorrect>
        </question>

        <question id="float-type" type="fill-in-the-blank">
            The result of `type(3.14)` in Python is [blank].

            <correct text="float" />
            <correct text="&lt;class 'float'&gt;" />
        </question>
    </questions>
</quiz>
```

---

For question types, see [Question types](quiz-questions.md).
