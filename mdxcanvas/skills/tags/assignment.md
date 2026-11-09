---
type: skill
description: Load when creating or editing <assignment> tags, submission settings, external tools, or section overrides.
---

# `<assignment>` Tag

## When to Use This Reference

Use this reference when working with:

- Creating or editing any assignment
- Setting due dates, late due dates, or availability windows
- Configuring submission types (upload, external tool, not graded)
- Adding section-specific overrides
- Renaming an existing assignment without creating a duplicate

## Non-Negotiables

- Every assignment requires `id` and `title`. Preserve `id` when renaming `title`.
- Do not leave `assignment_group` blank if grade weights matter — it must match a `<group>` defined in
  `<assignment-groups>`.
- Dates follow [Shared parsing rules](parsing-rules.md); assessment choices belong to the instructor.

---

## Attributes

| Attribute                      | Required | Description                                                             |
|--------------------------------|----------|-------------------------------------------------------------------------|
| `title`                        | yes      | Assignment title shown in Canvas                                        |
| `id`                           | yes      | Stable identifier; no title fallback                                    |
| `due_at`                       | no       | Date in any supported form (see shared parsing rules) |
| `available_from`               | no       | Date when assignment becomes available                                  |
| `available_to`                 | no       | Date when assignment closes                                             |
| `late_due`                     | no       | Parsed date forwarded unchanged; no implemented cutoff translation (see below) |
| `points_possible`              | no       | Maximum points (integer)                                                |
| `assignment_group`             | no       | Stable `id` of a `<group>` declared in `<assignment-groups>`             |
| `submission_types`             | no       | e.g., `online_upload`, `external_tool`, `not_graded`                    |
| `external_tool_tag_attributes` | no       | Used with `submission_types="external_tool"`                            |
| `only_visible_to_overrides`    | no       | `"True"` — hide assignment from students not in an `<override>` section |

---

### Remaining supported attributes and aliases

Optional fields are omitted unless a default is stated. See [Shared parsing rules](parsing-rules.md) for conversions and aliases.

| Attribute(s) | Parsing / effective default |
|---|---|
| `name` | Alias of required `title` |
| `unlock_at`, `lock_at` | Aliases of `available_from`, `available_to`; dates |
| `assignment_group_id` | Alias of `assignment_group`; stable source ID, not Canvas numeric ID |
| `group_category`, `group_category_id` | Stable group-category source ID; aliases |
| `allowed_attempts` | Integer, or literal `not_graded` converted to -1 |
| `allowed_extensions` | List |
| `grading_type` | String; emitted default `points` |
| `position` | Integer |
| `published`, `automatic_peer_reviews`, `grade_group_students_individually`, `grader_comments_visible_to_graders`, `grader_names_visible_to_final_grader`, `graders_anonymous_to_graders`, `hide_in_gradebook`, `moderated_grading`, `notify_of_update`, `omit_from_final_grade`, `peer_reviews`, `turnitin_enabled`, `vericite_enabled` | Boolean; omitted when absent, including declared false defaults |
| `annotatable_attachment_id`, `final_grader_id`, `grading_standard_id`, `grader_count`, `integration_data`, `quiz_lti`, `turnitin_settings` | Strings; parser acceptance does not validate Canvas compatibility |

`submission_types` and `allowed_extensions` use list parsing; `external_tool_tag_attributes` uses string-valued dictionary parsing, including `new_tab=true`.

## Key Attribute Details

### `id`

`id` is required now. Renaming `title` while preserving `id` updates the same resource.

For a legacy resource deployed by an older version using its title as implicit identity, first add `id` equal to that previously deployed title and leave the title unchanged. Deploy that identity migration separately before a later rename. Current parsing rejects assignments without `id`.

```xml
<assignment id="hw1" title="Homework 1 (Revised)">
    ...
</assignment>
```

### `late_due`

`late_due` is handled during deployment; see [Shared parsing rules](parsing-rules.md).

```xml
<assignment id="hw1"
    title="Homework 1"
    due_at="Jan 15, 2025, 11:59 PM"
    late_due="Jan 17, 2025, 11:59 PM">
    ...
</assignment>
```

### `submission_types`

Common values:

- `online_upload` — students upload files
- `external_tool` — uses an LTI tool (requires `external_tool_tag_attributes`)
- `not_graded` — assignment appears in Canvas but no submission is expected; used for lecture material containers

### `only_visible_to_overrides`

Hides the assignment from students who are not in any `<override>` section.

```xml
<assignment id="section-homework" title="Section-Specific Homework"
            only_visible_to_overrides="True">
    <overrides>
        <override section_id="12345" due_at="Jan 20, 2025, 11:59 PM"/>
    </overrides>
    ...
</assignment>
```

### `external_tool_tag_attributes`

This is an unconfigured placeholder URL, not a working integration. Replace it only with an instructor-approved, institution-configured URL. `new_tab=true` requests a new tab. Resource fragment:

```xml
<assignment id="tool-submission" title="External Tool Submission"
    submission_types="external_tool"
    external_tool_tag_attributes="url=https://unconfigured-tool.example.invalid/launch,new_tab=true">
    Follow the approved submission instructions.
</assignment>
```

---

## Assignment Content

Place Markdown or HTML directly inside the tag:

```xml
<assignment id="hw1" title="Homework 1">
    # Homework 1

    Complete the instructor-approved exercises and submission process.

    ## Instructions
    1. Read the assignment.
    2. Complete the tasks.
    3. Submit before the deadline.
</assignment>
```

Use `<include>` to pull content from an external file:

```xml
<assignment id="hw1" title="Homework 1">
    <include path="content/assignments/hw1.md"/>
</assignment>
```

---

## Section-Specific Dates

```xml
<assignment id="hw1" title="Homework 1" due_at="Jan 15, 2025, 11:59 PM">
    <overrides>
        <override section_id="12345" due_at="Jan 20, 2025, 11:59 PM" />
        <override section_id="67890" due_at="Jan 22, 2025, 11:59 PM" />
    </overrides>

    Complete the homework assignment...
</assignment>
```

---

## Resource example (requires the `homework` group and approved tool configuration)

```xml
<assignment id="example-homework"
    title="Example Homework"
    due_at="Jan 1, 2025, 11:59 PM"
    available_from="Jan 1, 2025, 9:00 AM"
    available_to="Jan 1, 2025, 11:59 PM"
    points_possible="30"
    assignment_group="homework"
    submission_types="external_tool"
    external_tool_tag_attributes="url=https://unconfigured-tool.example.invalid/launch">

    Complete the homework following the instructor-approved instructions.

    Then submit using the approved tool.
</assignment>
```

---

## Skeleton Template (replace bracketed placeholders; not runnable)

```xml
<assignment id="[STABLE ID]"
    title="[ASSIGNMENT TITLE]"
    due_at="[MMM d, yyyy, h:mm AM/PM]"
    available_from="[MMM d, yyyy, h:mm AM/PM]"
    points_possible="[POINTS]"
    assignment_group="[GROUP ID]">

    # [ASSIGNMENT TITLE]

    [Assignment description and instructions here.]

    ## Instructions

    1. [Step 1]
    2. [Step 2]
    3. [Step 3]

    ## Submission

    [Describe how students should submit their work.]

</assignment>
```
