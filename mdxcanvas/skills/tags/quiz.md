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

- Always include a `<questions>` block. A quiz without questions is invalid.
- Use `shuffle_answers="true"` for multiple-choice quizzes to prevent answer sharing.
- Do not rename a quiz's `title` without first adding `id` equal to the current title.
- Always use `MMM d, yyyy, h:mm AM/PM` for all date values.
- Use `access_code` + `only_visible_to_overrides` together for locked exam quizzes.

---

## Quiz Structure

The `<quiz>` tag contains two child elements:

- `<description>` — optional instructions shown to students before they begin
- `<questions>` — required; contains one or more `<question>` tags
- Some question types support per-answer feedback:
  `answer_comments` on `<correct>` / `<incorrect>`, `answer_comments` on `<pair>`, `answer_comments` on `<correct>` for fill-in and numerical questions, `answer_comments` on `<correct>` / `<incorrect>` for `multiple-tf`, and question-level `correct-comments` / `incorrect-comments` on `true-false`

```xml
<quiz title="Chapter 1 Quiz"
      due_at="Jan 20, 2025, 11:59 PM"
      shuffle_answers="true"
      allowed_attempts="2"
      scoring_policy="keep_highest">

    <description>
        Answer all questions. You have 2 attempts.
    </description>

    <questions>
        <question type="multiple-choice">
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

When not specified, MDXCanvas quizzes default to:

- `shuffle_answers="true"`
- `allowed_attempts="2"`
- `scoring_policy="keep_highest"`

---

## Attributes

| Attribute                   | Required | Description                                                         |
|-----------------------------|----------|---------------------------------------------------------------------|
| `title`                     | yes      | Quiz title shown in Canvas                                          |
| `id`                        | no       | Stable identifier; defaults to `title`                              |
| `due_at`                    | no       | Due date: `MMM d, yyyy, h:mm AM/PM`                                 |
| `available_from`            | no       | Date when quiz becomes available                                    |
| `available_to`              | no       | Date when quiz closes                                               |
| `assignment_group`          | no       | Grade category name                                                 |
| `shuffle_answers`           | no       | `"true"` to randomize answer order per student                      |
| `time_limit`                | no       | Time limit in minutes; omit for no limit                            |
| `allowed_attempts`          | no       | Number of attempts; `-1` for unlimited                              |
| `scoring_policy`            | no       | `keep_highest` (default), `keep_latest`, `keep_average`             |
| `access_code`               | no       | Passcode students must enter to access the quiz                     |
| `quiz_type`                 | no       | `assignment` (default), `practice_quiz`, `graded_survey`            |
| `points_possible`           | no       | Total points; if omitted, calculated from question points           |
| `show_correct_answers_at`   | no       | Date when correct answers become visible: `MMM d, yyyy, h:mm AM/PM` |
| `only_visible_to_overrides` | no       | `"True"` — hide quiz from students not in an `<override>` section   |

---

## Key Attribute Details

### `id`

Use an explicit `id` when you need to rename the quiz later without creating a new resource. `id` will become required
in a future version — add it now when you touch a resource.

```xml
<quiz id="midterm_exam" title="Midterm Exam">
    ...
</quiz>
```

**When modifying a resource with no `id`:** first add `id` equal to the current `title` value and keep `title`
unchanged. Then make other edits. Changing `title` without an `id` creates a new resource.

### `shuffle_answers`

```xml
<quiz title="Quiz 1" shuffle_answers="true">
    ...
</quiz>
```

### `time_limit`

```xml
<quiz title="Quiz 1" time_limit="30">
    ...
</quiz>
```

### `allowed_attempts`

```xml
<quiz title="Quiz 1" allowed_attempts="3">
    ...
</quiz>
```

Use `-1` for unlimited attempts.

### `access_code`

```xml
<quiz title="Quiz 1" access_code="secure123">
    ...
</quiz>
```

### `quiz_type`

```xml
<quiz title="Practice Quiz" quiz_type="practice_quiz">
    ...
</quiz>
```

### `scoring_policy`

```xml
<quiz title="Quiz 1" allowed_attempts="3" scoring_policy="keep_highest">
    ...
</quiz>
```

### `show_correct_answers_at`

```xml
<quiz title="Quiz 1" show_correct_answers_at="Jan 20, 2025, 12:00 PM">
    ...
</quiz>
```

### `only_visible_to_overrides`

Hides the quiz from students who are not in any `<override>` section. Use this for password-locked quizzes that only
specific sections should see.

```xml
<quiz title="Lecture 3a Quiz"
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
<quiz title="Midterm Exam" due_at="Feb 15, 2025, 11:59 PM">
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

## Full Example

```xml
<quiz
    title="Example Quiz"
    due_at="Jan 1, 2025, 11:59 PM"
    available_from="Jan 1, 2025, 9:00 AM"
    available_to="Jan 1, 2025, 11:59 PM"
    assignment_group="Quizzes"
    shuffle_answers="true"
    time_limit="30"
    allowed_attempts="3"
    scoring_policy="keep_highest"
    points_possible="100">

    <description>
        This quiz includes various question types.
    </description>

    <questions>
        <question type="true-false" answer="true"
                  correct-comments="Correct" incorrect-comments="The sky is blue under normal daylight conditions.">
            Is the sky blue?
        </question>

        <question type="multiple-choice">
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

A minimal working quiz:

```xml
<quiz title="Python Basics Quiz"
      due_at="Jan 15, 2025, 11:59 PM"
      assignment_group="Quizzes"
      shuffle_answers="true"
      allowed_attempts="2"
      scoring_policy="keep_highest">

    <description>
        This quiz covers Python variables, data types, and basic operators.
    </description>

    <questions>
        <question type="true-false" answer="true"
                  correct-comments="Correct" incorrect-comments="Python variable names are case-sensitive.">
            Python variable names are case-sensitive.
        </question>

        <question type="multiple-choice">
            Which of the following is a valid Python variable name?

            <correct answer_comments="Underscores are allowed after the first character">my_var</correct>
            <incorrect answer_comments="Variable names cannot start with a number">2myvar</incorrect>
            <incorrect>my-var</incorrect>
            <incorrect>my var</incorrect>
        </question>

        <question type="fill-in-the-blank">
            The result of `type(3.14)` in Python is [blank].

            <correct text="float" />
            <correct text="&lt;class 'float'&gt;" />
        </question>
    </questions>
</quiz>
```

---

For question types, see [Question types](quiz-questions.md).
