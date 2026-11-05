---
type: skill
description: Load when creating or editing <module> and <item> tags, ordering items, or setting completion requirements and prerequisites.
---

# `<module>` and `<item>` Tags

## When to Use This Reference

Use this reference when working with:

- Creating or editing Canvas modules
- Adding or reordering module items
- Setting completion requirements or module prerequisites
- Linking pages, assignments, quizzes, or files into a module
- Adding subheaders, external URLs, or syllabus links to a module

## Non-Negotiables

- Do not rename a module's `title` without first adding `id` equal to the current title.
- Set an explicit `id` on any module used as a prerequisite target.
- Every `<item content_id>` must match the `id` (or `title`) of an existing, included resource.

---

## `<module>` Tag

The `<module>` tag defines a Canvas module.

### Attributes

| Attribute                 | Required | Description                                                                                  |
|---------------------------|----------|----------------------------------------------------------------------------------------------|
| `title`                   | yes      | Module title shown in Canvas                                                                 |
| `id`                      | no       | Stable identifier; defaults to `title`                                                       |
| `prerequisite_module_ids` | no       | Comma-separated list of module `id` values that must be completed before this module unlocks |

### `id`

Use an explicit `id` when referencing the module in `prerequisite_module_ids` or when you may want to rename the module
later. `id` will become required in a future version — add it now when you touch a resource.

**When modifying a module with no `id`:** first add `id` equal to the current `title` value and keep `title` unchanged.
Then make other edits.

```xml
<module id="week-1" title="Week 1: Introduction">
    ...
</module>
```

### `prerequisite_module_ids`

A module with prerequisites is locked until all completion requirements of the listed modules are satisfied.

```xml
<module id="week-3" title="Week 3: NP-Complete Problems" prerequisite_module_ids="week-1,week-2">
    ...
</module>
```

---

## `<item>` Tag

The `<item>` tag defines items within a module.

### Common Attributes

| Attribute                | Required | Description                                                        |
|--------------------------|----------|--------------------------------------------------------------------|
| `type`                   | yes      | Item type (see valid values below)                                 |
| `title`                  | no       | Display name in module; defaults to linked content's title         |
| `indent`                 | no       | Indentation level (integer)                                        |
| `completion_requirement` | no       | How the item must be completed (comma-separated `key=value` pairs) |

### Valid `type` Values

- `page` — link to a course page
- `assignment` — link to an assignment
- `quiz` — link to a quiz
- `file` — link to a course file
- `subheader` — section divider with text
- `externalurl` — link to an external website
- `syllabus` — link to the course syllabus

`type` values are case-insensitive. `SubHeader` and `subheader` both work.

### `completion_requirement`

Common values:

- `type=must_view` — student must view the item
- `type=must_submit` — student must submit (for assignments/quizzes)
- `type=min_score,min_score=80` — student must score at least 80

```xml
<item type="quiz" content_id="quiz1" completion_requirement="type=min_score,min_score=100" />
```

### Type-Specific Attributes

#### `content_id` — for `page`, `assignment`, `quiz`, `file`

References the `id` attribute of the target resource (or `title` if no `id` was set).

```xml
<page id="intro_page" title="Introduction to the Course">
    ...
</page>

<module title="Week 1">
    <item type="page" content_id="intro_page" />
</module>
```

#### For `subheader`

Uses `title` for the divider text. No `content_id` needed.

```xml
<item type="subheader" title="Week 1 Readings" />
```

#### `external_url` — for `externalurl`

```xml
<item type="externalurl" external_url="https://example.com" title="Example Website" />
```

---

## Examples

### Basic module with various item types

```xml
<module title="Week 1: Getting Started">
    <item type="subheader" title="Introduction" />
    <item type="page" content_id="welcome_page" />
    <item type="page" content_id="syllabus_page" title="Read the Syllabus" />

    <item type="subheader" title="Assignments" />
    <item type="assignment" content_id="hw1" indent="1" />
    <item type="quiz" content_id="week1_quiz" indent="1" />

    <item type="subheader" title="Resources" />
    <item type="file" content_id="lecture_notes.pdf" indent="1" />
    <item type="externalurl" external_url="https://docs.example.com" title="External Documentation" indent="1" />
</module>
```

### Module with completion requirements and prerequisites

```xml
<module id="week-1" title="Week 1">
    <item type="page" content_id="intro" completion_requirement="type=must_view" />
    <item type="quiz" content_id="quiz1" completion_requirement="type=min_score,min_score=80" />
</module>

<module id="week-2" title="Week 2" prerequisite_module_ids="week-1">
    <item type="page" content_id="lesson2" />
</module>
```
