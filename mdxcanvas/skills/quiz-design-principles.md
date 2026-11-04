---
type: skill
description: Load when representing or editing Canvas Classic Quizzes and questions in MDXCanvas. If you need to edit content using the `<quiz>` tag, load this document.
---

# Representing Quizzes and Questions in MDXCanvas

This guide describes how to represent Canvas Classic Quizzes with MDXCanvas. It focuses on the question structures that the current parser can produce, ways to combine those structures to represent common question styles, and implementation limits that affect authoring.

## 1. Quiz container

A quiz contains an optional `<description>` and a required, non-empty `<questions>` block. Give the quiz and every question explicit, stable IDs. Quiz-level prose must be inside `<description>`; top-level prose directly inside `<quiz>` is not treated as description content.

```xml
<quiz id="unit-1-checkpoint"
      title="Unit 1 Checkpoint"
      assignment_group="quizzes"
      available_from="Jan 15, 2026, 9:00 AM"
      due_at="Jan 20, 2026, 11:59 PM"
      available_to="Jan 20, 2026, 11:59 PM"
      shuffle_answers="true"
      allowed_attempts="2"
      scoring_policy="keep_highest"
      published="false">
    <description>
        Complete all questions. Decimal answers should be rounded to four places.
    </description>

    <questions>
        <question id="central-idea" type="multiple-choice" points="1">
            Which statement matches the result?
            <correct>The result is proportional to the input.</correct>
            <incorrect>The result is independent of the input.</incorrect>
            <incorrect>The result is always zero.</incorrect>
        </question>
    </questions>
</quiz>
```

The authoring contract requires a non-empty `<questions>` block. Some empty-question cases produce a warning rather than a parser failure; such a quiz is still incomplete.

### Quiz attributes

| Attribute | Representation |
|---|---|
| `id` | Stable source identity. Required by the current implementation. |
| `title` | Displayed Canvas title. Required. |
| `quiz_type` | Canvas Classic Quiz type: `assignment`, `practice_quiz`, `graded_survey`, or `survey` (ungraded survey). |
| `assignment_group` | Stable ID of an assignment group. |
| `due_at` | Due date. |
| `available_from` | Opening date; mapped to Canvas `unlock_at`. |
| `available_to` | Closing date; mapped to Canvas `lock_at`. |
| `time_limit` | Integer number of minutes. |
| `shuffle_answers` | Boolean controlling option shuffling. |
| `allowed_attempts` | Integer attempt count; `-1` means unlimited. |
| `scoring_policy` | `keep_highest`, `keep_latest`, or `keep_average`. |
| `access_code` | Passcode required to open the quiz. |
| `points_possible` | Explicit numeric quiz total; integer and decimal values are accepted. If used, keep it consistent with the represented question scores. |
| `published` | Boolean publication state. |
| `show_correct_answers` | Boolean controlling whether correct answers can be shown. |
| `show_correct_answers_last_attempt` | Boolean restricting correct-answer display to the final attempt. |
| `show_correct_answers_at` | Start of the correct-answer display window. |
| `hide_correct_answers_at` | End of the correct-answer display window. |
| `hide_results` | Canvas result-visibility value. |
| `one_time_results` | Boolean limiting result display to one view. |
| `one_question_at_a_time` | Boolean enabling sequential question display. |
| `cant_go_back` | Boolean preventing backward navigation; use only with `one_question_at_a_time`. |
| `only_visible_to_overrides` | Boolean hiding the quiz from users not covered by an override. |
| `position` | Integer Canvas position. |

Use the date format `MMM d, yyyy, h:mm AM/PM`, for example `Jan 20, 2026, 11:59 PM`.

Do not rely on defaults when a quiz setting affects the intended Canvas representation. Set attempts, answer shuffling, result visibility, scoring policy, publication state, timing, and navigation controls explicitly whenever their values matter.

Section-specific dates are nested under the quiz:

```xml
<quiz id="section-checkpoint"
      title="Section Checkpoint"
      due_at="Feb 15, 2026, 11:59 PM"
      only_visible_to_overrides="true"
      access_code="example-code">
    <overrides>
        <override section_id="12345"
                  due_at="Feb 16, 2026, 11:59 PM" />
        <override section_id="67890"
                  due_at="Feb 17, 2026, 11:59 PM" />
    </overrides>
    <questions>
        <question id="confirmation" type="true-false" answer="true">
            The supplied value is positive.
        </question>
    </questions>
</quiz>
```

## 2. Identity, ordering, and updates

The quiz `id` is its durable source identity; `title` is display text. Preserve the ID when changing the title.

For a legacy quiz without an explicit ID, first add `id` equal to its current title without changing the title. Deploy that identity-preserving update before renaming the title. Changing a title and introducing a different ID at the same time can create a second Canvas resource.

Questions do not have titles. Their visible wording is question text. A question ID must be:

- explicit;
- unique within its quiz; and
- unchanged when its text, answers, or position changes.

MDXCanvas combines the quiz ID and question ID internally. For generated questions, use an immutable source key such as `runtime-comparison`, or numbering that is never recomputed. Do not derive IDs from current list positions if inserting a question would renumber everything after it.

Questions are ordered as direct `<question>` children of `<questions>`. The deployment process creates an explicit Canvas order from that source order. A `multiple-tf` element is an exception: it expands into a text header followed by one true/false Canvas question for each statement.

## 3. Content available inside questions

Question bodies and answer bodies can contain Markdown. This permits prose, emphasis, lists, tables, fenced code, inline or display math, links, and images.

```xml
<question id="code-result" type="multiple-choice" points="1">
    What does this code print?

    ```python
    values = [2, 4, 6]
    print(sum(values))
    ```

    <correct>`12`</correct>
    <incorrect>`6`</incorrect>
    <incorrect>`24`</incorrect>
</question>
```

An image can appear in a question body:

```xml
<question id="diagram-label" type="multiple-choice" points="1">
    Refer to the diagram.

    ![A directed graph with vertices A, B, and C](images/graph.png)

    Which vertex has no outgoing edge?
    <correct>C</correct>
    <incorrect>A</incorrect>
    <incorrect>B</incorrect>
</question>
```

Image paths are resolved from the relevant source/include context. Use meaningful alternative text. Markdown tables should have a header row; visually complex tables and images still need a text representation sufficient for the intended response.

MDXCanvas helper tags can also occur in question content after preprocessing. For example, a question can link to another course resource:

```xml
<question id="reference-confirmation" type="true-false" answer="true">
    I opened the <course-link type="page" id="formula-reference" /> page.
</question>
```

A text-only question can expose a generated download:

```xml
<question id="starter-files" type="text">
    Download the files used by the following questions.
    <zip path="materials/source"
         priority_path="materials/starter"
         exclude="^_"
         name="question-materials.zip" />
</question>
```

The referenced course resource or local files must exist, and relative paths follow normal helper-tag path resolution. The link or download is part of the rendered question content; it does not create a response field.

XML still applies around the Markdown. Escape XML-sensitive attribute characters such as `&` and `<`, and make sure element tags are correctly closed.

## 4. Supported question types

Every `<question>` requires `id` and `type`. Question point values may be finite decimals as well as integers. Most answer-bearing types accept `points` or `points_possible`; these names map to the same Canvas field. Use `points`, not `points_possible`, for `matching`: the current implementation overwrites a matching question's `points_possible` value with its pair count unless `points` is present. The current implementation does not parse point attributes on `text` or `file-upload`.

### `text`: shared material or a section heading

`text` creates a Canvas text-only question. It has no response and does not accept authored points. Use it to place a passage, image, data set, instructions, or heading in the ordered question stream.

```xml
<question id="graph-context" type="text">
    Use this graph for the next two questions.

    ![An undirected graph with five labeled vertices](images/network.png)

    When two choices are available, choose the alphabetically first vertex.
</question>
```

A text question does not formally attach itself to later questions. Its effect depends on source order. When a quiz displays one question at a time, verify that learners can still access any context placed in a preceding text question; repeating essential context in each question may be necessary.

### `true-false`: one Boolean response

Set `answer` to `true` or `false`.

```xml
<question id="is-connected"
          type="true-false"
          answer="false"
          points="1"
          correct-comments="The graph has two components."
          incorrect-comments="Check whether every vertex is reachable from A.">
    Every vertex in the displayed graph is reachable from A.
</question>
```

Question-level feedback uses the attributes `correct-comments`, `neutral-comments`, and `incorrect-comments`.

### `multiple-choice`: one correct option

Use exactly one `<correct>` child and at least one `<incorrect>` child. Each answer body may contain Markdown. The current parser may accept a missing or malformed option set, but that does not constitute a complete question.

```xml
<question id="single-category" type="multiple-choice" points="1">
    Which category contains the value `17`?
    <correct answer_comments="17 is divisible only by 1 and itself.">Prime</correct>
    <incorrect answer_comments="17 has no factor other than 1 and 17.">Composite</incorrect>
    <incorrect>Neither</incorrect>
</question>
```

MDXCanvas sends each `<correct>` answer with weight 100 and each `<incorrect>` answer with weight 0. The syntax does not expose arbitrary per-option weights.

### `multiple-answers`: zero or more selected options

Use one `<correct>` child for every option that should be selected and `<incorrect>` for every option that should not be selected. Include at least one option in total. A question may deliberately have zero correct options, but that behavior and its scoring consequences require instructor approval and Canvas verification.

```xml
<question id="select-properties" type="multiple-answers" points="2">
    Select every property satisfied by the value `12`.
    <correct>Even</correct>
    <correct>Composite</correct>
    <incorrect>Prime</incorrect>
    <incorrect>Negative</incorrect>
</question>
```

This is also the available representation for checkbox-style acknowledgements or checklists. Use `points="0"` when the represented question should carry no score:

```xml
<question id="submission-checklist" type="multiple-answers" points="0">
    Select the items included in this submission.
    <correct>Source files</correct>
    <correct>Report</correct>
    <correct>Test output</correct>
</question>
```

Canvas determines the grading behavior for combinations of selected correct and incorrect options. MDXCanvas does not provide custom partial-credit weights for individual options; test the resulting Canvas behavior if the distinction matters.

### `matching`: pairs, classification, and category assignment

Each `<pair>` supplies one left prompt and its correct right response. Include at least one pair. `<distractors>` is an optional newline-separated list of additional right-side choices. Set an explicit total with `points`; in the current implementation, `points_possible` alone is overwritten by the pair count.

```xml
<question id="term-matching" type="matching" points="3">
    Match each symbol to its meaning.
    <pair left="μ" right="Population mean" />
    <pair left="σ" right="Population standard deviation" />
    <pair left="n" right="Sample size" />
    <distractors>
        Sample mean
        Sample variance
    </distractors>
</question>
```

Matching can also represent classification when several left prompts share the same small set of right-side categories:

```xml
<question id="edge-classification" type="matching" points="4">
    Classify each edge.
    <pair left="A → B" right="Tree edge" />
    <pair left="B → A" right="Back edge" />
    <pair left="A → C" right="Tree edge" />
    <pair left="C → B" right="Cross edge" />
    <distractors>
        Tree edge
        Back edge
        Forward edge
        Cross edge
    </distractors>
</question>
```

This same structure can approximate “assign each item to a category.” It is not a drag-and-drop ordering question, and the syntax provides no dedicated ranking type.

### `multiple-tf`: one source element expanded into several true/false questions

Place true statements in `<correct>` and false statements in `<incorrect>`. Include at least one statement.

```xml
<question id="property-set" type="multiple-tf" points="4">
    Mark each statement true or false.
    <correct answer_comments="This statement follows from the definition.">
        Every square is a rectangle.
    </correct>
    <incorrect answer_comments="A rectangle need not have four equal sides.">
        Every rectangle is a square.
    </incorrect>
    <correct>A square has four equal sides.</correct>
    <incorrect>A square has three vertices.</incorrect>
</question>
```

MDXCanvas emits:

1. a text-only header containing the outer question body; and
2. one Canvas true/false question per `<correct>` or `<incorrect>` child.

Generated subquestion IDs use the outer ID plus a numeric suffix. Per-statement `answer_comments` becomes correct-answer feedback on the generated statement. General question-level comment fields are not carried through this expansion.

The current point-distribution implementation is reliable only when the outer integer `points` value is evenly divisible by the number of statements. Otherwise the generated subquestion points may not add up to the authored total. Until that implementation is corrected, use at least one statement, choose an evenly divisible total, and verify the generated question scores.

### `fill-in-the-blank`: one blank with one or more accepted answers

Put a bracketed blank name in the body and add one `<correct>` child per accepted text value. The conventional single blank name is `[blank]`.

```xml
<question id="single-blank" type="fill-in-the-blank" points="1">
    The hexadecimal representation of decimal 15 is [blank].
    <correct text="F" />
    <correct text="f" />
    <correct text="0xF" />
    <correct text="0xf" />
</question>
```

Include at least one `<correct>` child. All `<correct>` children apply to the first bracketed blank found in the question. This representation performs Canvas fill-in matching, not numeric tolerance matching. Use `numerical` when tolerance, range, or numeric precision is required.

### `fill-in-multiple-blanks`: named blanks with explicit accepted answers

Put named blanks such as `[base]` and `[exponent]` in the body. Every `<correct>` identifies its target with `blank`.

```xml
<question id="named-blanks" type="fill-in-multiple-blanks" points="2">
    In the expression 2³, the base is [base] and the exponent is [exponent].
    <correct blank="base" text="2" />
    <correct blank="exponent" text="3" />
</question>
```

Multiple accepted forms can target the same blank:

```xml
<question id="named-blanks-alternates" type="fill-in-multiple-blanks" points="2">
    The Boolean values are [first] and [second].
    <correct blank="first" text="true" />
    <correct blank="first" text="True" />
    <correct blank="second" text="false" />
    <correct blank="second" text="False" />
</question>
```

Include at least one `<correct>` child. Blank names in `<correct blank="...">` must exactly match the names in the question text, and every intended blank must have at least one accepted answer.

### `fill-in-multiple-blanks-filled-answers`: inline-answer shorthand

Wrap each accepted answer in `[[double brackets]]`. MDXCanvas replaces the answers with generated blank IDs and stores the enclosed text as each blank's single accepted answer.

```xml
<question id="inline-blanks" type="fill-in-multiple-blanks-filled-answers" points="3">
    The point ([[2]], [[5]]) lies in quadrant [[I]].
</question>
```

This shorthand is particularly useful for structured worksheets because blanks can appear inside Markdown tables:

```xml
<question id="table-completion" type="fill-in-multiple-blanks-filled-answers" points="4">
    Complete the trace table.

    | Step | Input | Running total |
    |---:|---:|---:|
    | 1 | 3 | [[3]] |
    | 2 | 4 | [[7]] |
    | 3 | 2 | [[9]] |
    | 4 | 5 | [[14]] |
</question>
```

It can also represent a matrix, algorithm trace, sequence, coordinate list, factorization, or multi-field calculation:

```xml
<question id="algorithm-trace" type="fill-in-multiple-blanks-filled-answers" points="5">
    Fill in the missing states.

    | Iteration | Current | Remaining |
    |---:|---:|---:|
    | 0 | 0 | 8 |
    | 1 | [[2]] | [[6]] |
    | 2 | [[5]] | [[3]] |
    | 3 | [[8]] | [[0]] |

    Final result: [[8]]
</question>
```

Important limits of the shorthand:

- Each `[[answer]]` creates a separate blank, even when the same answer appears elsewhere.
- Each generated blank has one accepted text value. Use explicit `fill-in-multiple-blanks` when a blank needs alternate accepted forms.
- The enclosed answer is present in source and should not appear in student-visible prose outside the conversion process.
- Literal `[[...]]` text in the body is interpreted as an answer marker.
- Point defaults depend on the generated blank count; set `points` explicitly when that is not the intended total.

### `essay`: open text response

The question body becomes an essay prompt. No answer children are required.

```xml
<question id="explanation" type="essay" points="5">
    Show the intermediate states of the algorithm and explain the final result.
</question>
```

This is the available representation for proofs, derivations, explanations, free-form calculations, and other responses that cannot be represented by the automatically graded types. MDXCanvas does not encode an answer key or rubric inside the essay question syntax.

### `file-upload`: uploaded response

The question body describes the requested upload.

```xml
<question id="worked-solution" type="file-upload">
    Upload the worked solution as a PDF, PNG, or JPG file.
</question>
```

The current implementation does not parse `points` or `points_possible` on `file-upload`; adding one produces an unprocessed-field warning and does not set the value. File types and naming requirements are instructions, not constraints enforced by this tag.

### `numerical`: exact value, range, or precision

A numerical question requires `numerical_answer_type` and at least one `<correct>` answer. The accepted attributes depend on the mode.

#### Exact value with error margin

```xml
<question id="numeric-exact"
          type="numerical"
          numerical_answer_type="exact"
          points="1">
    Enter π rounded to five decimal places.
    <correct answer_exact="3.14159" answer_error_margin="0.00001" />
</question>
```

Multiple `<correct>` children can represent multiple exact values:

```xml
<question id="numeric-two-roots"
          type="numerical"
          numerical_answer_type="exact"
          points="2">
    Enter either real root of x² = 4.
    <correct answer_exact="2" answer_error_margin="0" />
    <correct answer_exact="-2" answer_error_margin="0" />
</question>
```

#### Inclusive range

```xml
<question id="numeric-range"
          type="numerical"
          numerical_answer_type="range"
          points="1">
    Enter a value in the accepted interval.
    <correct answer_range_start="1" answer_range_end="10" />
</question>
```

Multiple `<correct>` children can represent disjoint accepted ranges.

#### Precision

```xml
<question id="numeric-precision"
          type="numerical"
          numerical_answer_type="precision"
          points="1">
    Enter π to five digits of precision.
    <correct answer_approximate="3.14159" answer_precision="5" />
</question>
```

Numerical answer attributes are strings passed to Canvas. Units belong in the prompt; this syntax does not define a separate unit field.

## 5. Feedback fields

MDXCanvas supports answer-level comments for these structures:

- `multiple-choice` and `multiple-answers`: `answer_comments` on `<correct>` and `<incorrect>`;
- `matching`: `answer_comments` on `<pair>`;
- fill-in types: `answer_comments` on `<correct>`;
- `numerical`: `answer_comments` on `<correct>`; and
- `multiple-tf`: `answer_comments` on each statement.

Most answer-bearing types also accept these question attributes:

- `correct-comments`;
- `neutral-comments`;
- `incorrect-comments`; and
- `text-after-answers`.

The current implementation does not parse those question-level fields for `text` or `file-upload`, and does not carry them through `multiple-tf` expansion.

```xml
<question id="feedback-example"
          type="multiple-choice"
          points="1"
          correct-comments="The selected option satisfies all constraints."
          incorrect-comments="Compare the option against each constraint."
          text-after-answers="The constraints are listed in the preceding table.">
    Which option is valid?
    <correct answer_comments="This option satisfies A, B, and C.">Option 1</correct>
    <incorrect answer_comments="This option violates constraint B.">Option 2</incorrect>
</question>
```

Use attribute-safe text in feedback attributes. For long or heavily formatted feedback, verify the rendered Canvas result because these fields are serialized to Canvas HTML differently from ordinary question body content.

## 6. Representing compound question styles

Canvas does not expose every conceivable interaction through these tags. Compound styles can often be represented by combining supported types.

### Information-only quiz or survey

A `practice_quiz` or `survey` can consist of one or more `text` questions when the Canvas quiz is being used as an ordered container for instructions, links, or downloads rather than responses. The authoring contract still requires `<questions>` and each text question still requires an ID.

```xml
<quiz id="materials-release"
      title="Materials Release"
      quiz_type="survey"
      access_code="example-code">
    <description>Open this item to retrieve the materials.</description>
    <questions>
        <question id="download" type="text">
            Download the supplied archive:
            <zip path="materials" name="materials.zip" />
        </question>
    </questions>
</quiz>
```

### Shared scenario followed by several questions

Place the scenario in a `text` question, then place each response question immediately after it:

```xml
<questions>
    <question id="case-context" type="text">
        Use the following measurements for questions 2–4.

        | Trial | Value |
        |---:|---:|
        | 1 | 4.2 |
        | 2 | 4.6 |
        | 3 | 4.4 |
    </question>

    <question id="case-mean" type="numerical" numerical_answer_type="exact">
        What is the mean?
        <correct answer_exact="4.4" answer_error_margin="0.01" />
    </question>

    <question id="case-category" type="multiple-choice">
        Which interval contains every measurement?
        <correct>4.0–5.0</correct>
        <incorrect>3.0–4.0</incorrect>
        <incorrect>5.0–6.0</incorrect>
    </question>

    <question id="case-explanation" type="essay">
        Explain the observed variation.
    </question>
</questions>
```

### Table, matrix, or algorithm-state completion

Use `fill-in-multiple-blanks-filled-answers` when every cell has one exact textual answer. Use explicit `fill-in-multiple-blanks` when cells need alternate accepted forms. Use `numerical` as separate questions when numeric tolerance is required; inline table blanks do not support per-cell tolerance.

### Classifying many items into a small set of categories

Use `matching` with repeated right-side values. Put the complete category vocabulary in `<distractors>` so Canvas has all right-side choices. This represents classification but not free movement between arbitrary bins.

### Several independent true/false statements under one heading

Use `multiple-tf` when expansion into separate Canvas true/false questions is acceptable. Use individual `true-false` elements instead when each statement needs its own stable semantic ID, point value, or question-level feedback.

### Calculation plus submitted work

Represent the automatically checked result with `numerical` or a fill-in type, then add an `essay` response for typed work or a `file-upload` response for an uploaded artifact. These are separate Canvas questions and therefore separate ordered entries.

```xml
<questions>
    <question id="calculation-result"
              type="numerical"
              numerical_answer_type="exact"
              points="2">
        Enter the final result.
        <correct answer_exact="42" answer_error_margin="0" />
    </question>

    <question id="calculation-work" type="file-upload">
        Upload the work supporting the result.
    </question>
</questions>
```

### Ordering or ranking

There is no dedicated ordering type in the current MDXCanvas question registry. Available approximations are:

- named fill-in blanks for positions, such as `[first]`, `[second]`, and `[third]`;
- matching each item to a position label; or
- an essay response containing the ordered list.

Choose based on whether exact automatic checking or free-form response is required.

### Formula, hotspot, stimulus, and question-bank behavior

The current registry does not provide dedicated formula-generated, hotspot, stimulus, question-group, question-bank, or random-draw tags. Do not invent type names for them. Represent a fixed formula result with `numerical`, an image-based selection with `multiple-choice`, shared stimulus with `text` plus ordered questions, or leave the behavior for separate Canvas-side configuration.

## 7. Reuse and generation

### Including a question fragment

Question content can live in a separate file. The included fragment must resolve to direct `<question>` children of `<questions>`.

`quiz.canvas.md.xml`:

```xml
<quiz id="calculation-quiz" title="Calculation Quiz">
    <description>Enter all results in decimal form.</description>
    <questions>
        <include path="questions/calculations.canvas.md.xml" usediv="false" />
    </questions>
</quiz>
```

`questions/calculations.canvas.md.xml`:

```xml
<question id="sum" type="numerical" numerical_answer_type="exact">
    What is 18 + 24?
    <correct answer_exact="42" answer_error_margin="0" />
</question>

<question id="product" type="numerical" numerical_answer_type="exact">
    What is 6 × 7?
    <correct answer_exact="42" answer_error_margin="0" />
</question>
```

`usediv="false"` is important for question fragments because an inserted wrapper would prevent the questions from being direct children.

### Generating repeated questions with Jinja

A template can generate questions from structured data. IDs must come from stable data keys, not from a changing loop position.

```xml
{% set items = [
    {"id": "speed", "label": "speed", "answer": "distance / time"},
    {"id": "density", "label": "density", "answer": "mass / volume"}
] %}

<quiz id="formula-check" title="Formula Check">
    <questions>
        {% for item in items %}
        <question id="formula-{{ item.id }}" type="fill-in-the-blank">
            The formula for {{ item.label }} is [blank].
            <correct text="{{ item.answer }}" />
        </question>
        {% endfor %}
    </questions>
</quiz>
```

Question sources can also be loaded from structured Markdown and emitted as essay or option-based questions. The consuming template defines the actual data contract; heading names, table columns, and dictionary keys are therefore part of the quiz source format.

Conditional generation can add or omit a question, but any omitted question disappears from the resource graph. Preserve its ID if it later returns, and check that the resulting `<questions>` block remains non-empty.

## 8. Representation checks

Before handing off quiz source, verify the representation itself:

- Every quiz has explicit `id` and `title`.
- Every `<question>` is a direct child of `<questions>` after includes and Jinja rendering.
- Every question has an explicit, stable, unique ID and one of the supported type strings.
- Each type has a complete child structure: exactly one correct and at least one incorrect option for multiple choice; a deliberate nonempty option set for multiple answers; at least one pair for matching; at least one statement for `multiple-tf`; and nonempty, correctly targeted answers for fill-in and numerical questions.
- Matching questions use `points`, not `points_possible`, when overriding the default pair-count score.
- A `multiple-tf` point total is evenly divisible by its nonzero statement count, and the generated total has been verified.
- `text` and `file-upload` do not contain unsupported point attributes.
- Fill-in blank markers match their answer definitions exactly.
- Inline `[[answer]]` markers create the intended number and order of blanks.
- Matching distractors are one choice per non-empty line.
- Multiple-choice and multiple-answer correctness is represented only with `<correct>` and `<incorrect>`.
- Numerical exact margins, range endpoints, and precision values are represented with the attributes for the selected mode.
- Markdown tables, code, math, links, and images render inside the question body.
- Shared context remains available under the quiz's one-question-at-a-time and navigation settings.
- Question point totals and any quiz-level `points_possible` agree.
- Dates, attempts, answer visibility, access code, publication state, and overrides are represented explicitly where their values matter.
- Module items and other references use the stable quiz ID rather than a mutable title.
- Parser warnings about unknown or unprocessed attributes are resolved; an ignored attribute does not configure Canvas.

The supported `type` values are exactly:

```text
text
true-false
multiple-choice
multiple-answers
matching
multiple-tf
fill-in-the-blank
fill-in-multiple-blanks
fill-in-multiple-blanks-filled-answers
essay
file-upload
numerical
```
