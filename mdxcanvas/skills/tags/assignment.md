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

- Do not rename an assignment's `title` without first adding an explicit `id` equal to the current title.
- Do not leave `assignment_group` blank if grade weights matter — it must match a `<group>` defined in
  `<assignment-groups>`.
- Always use `MMM d, yyyy, h:mm AM/PM` for all date values.

---

## Attributes

| Attribute                      | Required | Description                                                             |
|--------------------------------|----------|-------------------------------------------------------------------------|
| `title`                        | yes      | Assignment title shown in Canvas                                        |
| `id`                           | no       | Stable identifier; defaults to `title`                                  |
| `due_at`                       | no       | Due date: `MMM d, yyyy, h:mm AM/PM`                                     |
| `available_from`               | no       | Date when assignment becomes available                                  |
| `available_to`                 | no       | Date when assignment closes                                             |
| `late_due`                     | no       | Latest date to accept late submissions                                  |
| `points_possible`              | no       | Maximum points (integer)                                                |
| `assignment_group`             | no       | Grade category name (must match an `<assignment-groups>` group)         |
| `submission_types`             | no       | e.g., `online_upload`, `external_tool`, `not_graded`                    |
| `external_tool_tag_attributes` | no       | Used with `submission_types="external_tool"`                            |
| `only_visible_to_overrides`    | no       | `"True"` — hide assignment from students not in an `<override>` section |

---

## Key Attribute Details

### `id`

Use an explicit `id` when you need to rename an assignment later without creating a new resource. `id` will become
required in a future version — add it now when you touch a resource.

**When modifying a resource with no `id`:** first add `id` equal to the current `title` value and keep `title`
unchanged. Then make other edits. Changing `title` without an `id` creates a new resource instead of updating the
existing one.

```xml
<assignment id="hw1" title="Homework 1 (Revised)">
    ...
</assignment>
```

### `late_due`

Students can still submit after `due_at` but before `late_due`.

```xml
<assignment
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
<assignment title="Section-Specific Homework"
            only_visible_to_overrides="True">
    <overrides>
        <override section_id="12345" due_at="Jan 20, 2025, 11:59 PM"/>
    </overrides>
    ...
</assignment>
```

### `external_tool_tag_attributes`

Add `new_tab=true` to open the tool in a new browser tab:

```xml
<assignment
    title="Gradescope Submission"
    submission_types="external_tool"
    external_tool_tag_attributes="url=https://lti.int.turnitin.com/launch/gs-proxy">
    ...
</assignment>

<!-- Open in new tab -->
<assignment
    title="Progress Check"
    submission_types="external_tool"
    external_tool_tag_attributes="url=https://lti.int.turnitin.com/launch/gs-proxy,new_tab=true">
    ...
</assignment>
```

---

## Assignment Content

Place Markdown or HTML directly inside the tag:

```xml
<assignment title="Homework 1">
    # Homework 1

    Complete the following exercises and submit via Gradescope.

    ## Instructions
    1. Read the assignment.
    2. Complete the tasks.
    3. Submit before the deadline.
</assignment>
```

Use `<include>` to pull content from an external file:

```xml
<assignment title="Homework 1">
    <include path="content/assignments/hw1.md"/>
</assignment>
```

---

## Section-Specific Dates

```xml
<assignment title="Homework 1" due_at="Jan 15, 2025, 11:59 PM">
    <overrides>
        <override section_id="12345" due_at="Jan 20, 2025, 11:59 PM" />
        <override section_id="67890" due_at="Jan 22, 2025, 11:59 PM" />
    </overrides>

    Complete the homework assignment...
</assignment>
```

---

## Full Example

```xml
<assignment
    title="Example Homework"
    due_at="Jan 1, 2025, 11:59 PM"
    available_from="Jan 1, 2025, 9:00 AM"
    available_to="Jan 1, 2025, 11:59 PM"
    points_possible="30"
    assignment_group="Homework"
    submission_types="external_tool"
    external_tool_tag_attributes="url=https://lti.int.turnitin.com/launch/gs-proxy">

    Complete the homework by following [these instructions](instructions).

    Then upload your `.py` files to Gradescope.
</assignment>
```

---

## Skeleton Template

```xml
<assignment
    title="[ASSIGNMENT TITLE]"
    due_at="[MMM d, yyyy, h:mm AM/PM]"
    available_from="[MMM d, yyyy, h:mm AM/PM]"
    points_possible="[POINTS]"
    assignment_group="[GROUP NAME]">

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
