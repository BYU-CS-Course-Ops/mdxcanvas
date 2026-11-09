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

- Every module requires `id` and `title`; preserve `id` when changing its title.
- Every `<item content_id>` must reference the stable resource ID of an existing, included resource, not its display title.

---

## `<module>` Tag

The `<module>` tag defines a Canvas module.

### Attributes

| Attribute                 | Required | Description                                                                                  |
|---------------------------|----------|----------------------------------------------------------------------------------------------|
| `title`                   | yes      | Module title shown in Canvas                                                                 |
| `id`                      | yes      | Stable identifier; no title fallback                                                         |
| `prerequisite_module_ids` | no       | Comma-separated list of module `id` values that must be completed before this module unlocks |

Additional module fields: `name` is an alias for required `title`; `position` is passed as a string; `published` is boolean; `previous-module` takes a stable module source ID. Optional fields are omitted when absent. Modules also carry an ordering dependency on the preceding module; `previous-module` replaces that dependency, not completion prerequisites. Prerequisite lists use stable IDs and the shared comma/legacy-pipe list parser. See [Shared parsing rules](parsing-rules.md).

### `id`

`id` is required now; preserve it when changing the module title. Prerequisite references use this stable ID.

For a legacy module deployed by an older version using implicit title identity, first add `id` equal to the previously deployed title without renaming it. Deploy that identity migration separately before a later rename. Current parsing rejects modules without `id`.

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
| `id`                     | varies   | Optional for page/assignment/quiz/file: defaults to `content_id`; required for subheader/externalurl/syllabus |
| `title`                  | no       | Display name in module; defaults to linked content's title         |
| `indent`                 | no       | Indentation level (integer)                                        |
| `completion_requirement` | no       | How the item must be completed (comma-separated `key=value` pairs) |

Additional common item fields: `position` (integer), `new_tab` (boolean, emitted default true), `published` (boolean), and `iframe` (string). `iframe` is accepted but has no supported ExternalTool branch, so do not promise an iframe launch. `completion_requirement` is a string-valued dictionary; Canvas—not the parser—validates its semantics. Omitted position starts at 1 and increments through implicit items; an explicit truthy position resets the counter to that value without incrementing it, so a following implicit item can share it. Other optional fields are omitted. Item type-specific fields below are exhaustive; no additional content-ID forms are supported.

### Valid `type` Values

- `page` — link to a course page
- `assignment` — link to an assignment
- `quiz` — link to a quiz
- `file` — link to a course file
- `subheader` — section divider with text
- `externalurl` — link to an external website
- `syllabus` — link to the course syllabus

`type` values are case-insensitive. `SubHeader` and `subheader` both work. Although `discussion` and `externaltool` are recognized by the casing lookup, both reach `NotImplementedError`; they are not supported item forms.

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

References the target's stable resource ID. For page, assignment, quiz, and file items, `id` is optional and defaults to `content_id`. Every item identity is namespaced as `<module id>|<item id or content_id>`. Changing `content_id` changes a derived item identity; supply its previous derived value as `id` if it must remain the same item.

```xml
<page id="intro_page" title="Introduction to the Course">
    ...
</page>

<module id="week-1" title="Week 1">
    <item type="page" content_id="intro_page" />
</module>
```

#### For `subheader`

Requires `id` and `title` for the divider. No `content_id` needed.

```xml
<item id="readings" type="subheader" title="Week 1 Readings" />
```

#### `external_url` — for `externalurl`

Requires `id` and `external_url`. Title is optional and defaults to the URL. Syllabus items likewise require `id`; their optional title defaults to `Syllabus`.

```xml
<item id="example-site" type="externalurl" external_url="https://example.com" title="Example Website" />
```

---

## Examples

These are module fragments. Every `content_id` and prerequisite must be supplied elsewhere in the reachable graph; they do not declare their target resources. External URLs are illustrative placeholders, not approved course destinations.

### Basic module with various item types

```xml
<module id="week-1" title="Week 1: Getting Started">
    <item id="introduction" type="subheader" title="Introduction" />
    <item type="page" content_id="welcome_page" />
    <item type="page" content_id="syllabus_page" title="Read the Syllabus" />

    <item id="assignments" type="subheader" title="Assignments" />
    <item type="assignment" content_id="hw1" indent="1" />
    <item type="quiz" content_id="week1_quiz" indent="1" />

    <item id="resources" type="subheader" title="Resources" />
    <item type="file" content_id="lecture_notes.pdf" indent="1" />
    <item id="external-docs" type="externalurl" external_url="https://docs.example.com" title="External Documentation" indent="1" />
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
