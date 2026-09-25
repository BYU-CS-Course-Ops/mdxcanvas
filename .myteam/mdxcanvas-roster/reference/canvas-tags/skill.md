---
id: canvas-tags
description: Routing hub for Canvas resource tag syntax reference.
---

# Canvas Tags Reference

## When to Use This Reference

Use this reference when looking up syntax, attributes, or examples for any Canvas resource tag.

## Routing

| Tag type      | Skill                   |
|---------------|-------------------------|
| Assignment    | `assignment/skill.md`   |
| Quiz          | `quiz/skill.md`         |
| Page          | `page/skill.md`         |
| Module / Item | `module/skill.md`       |
| Announcement  | `announcement/skill.md` |
| Syllabus      | `syllabus/skill.md`     |
| Group category| `group-category/skill.md` |

---

## Supported Resource Tags

| Tag                   | Creates             | Key Attributes                                                               |
|-----------------------|---------------------|------------------------------------------------------------------------------|
| `<assignment>`        | Canvas assignment   | `title`, `due_at`, `points_possible`, `assignment_group`, `submission_types` |
| `<quiz>`              | Canvas quiz         | `title`, `due_at`, `shuffle_answers`, `allowed_attempts`, `scoring_policy`   |
| `<page>`              | Canvas page         | `title`, `id`                                                                |
| `<module>`            | Canvas module       | `id`, `title`, `prerequisite_module_ids`                                     |
| `<item>`              | Module item         | `type`, `content_id`, `indent`, `completion_requirement`                     |
| `<syllabus>`          | Course syllabus     | (no attributes — wraps content)                                              |
| `<announcement>`      | Course announcement | `title`, `published_at`                                                      |
| `<assignment-groups>` | Grade groups        | contains `<group name="..." weight="..."/>` children                         |
| `<group-category>`    | Student group set   | `id`, `name`, `self_signup`, `group_limit`, `auto_leader`                    |

---

## Date Format

All date attributes use this exact format:

```
MMM d, yyyy, h:mm AM/PM
```

Examples: `Jan 15, 2025, 11:59 PM` · `Aug 25, 2025, 9:00 AM`

The timezone is set by `LOCAL_TIME_ZONE` in `course_info`. Do not guess the format — use it exactly.

---

## Section-Specific Dates

Both `<assignment>` and `<quiz>` support different due dates per course section using `<overrides>`:

```xml
<assignment title="Homework 1" due_at="Jan 15, 2025, 11:59 PM">
    <overrides>
        <override section_id="12345" due_at="Jan 20, 2025, 11:59 PM"/>
        <override section_id="67890" due_at="Jan 22, 2025, 11:59 PM"/>
    </overrides>

    Assignment description here.
</assignment>
```

The `section_id` matches the numeric Canvas section ID. The `due_at` on the parent tag is the default for sections not
listed in `<overrides>`.
