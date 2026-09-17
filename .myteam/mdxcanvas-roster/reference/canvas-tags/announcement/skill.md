---
id: canvas-tags-announcement
description: Syntax and attribute reference for the <announcement> tag.
---

# `<announcement>` Tag

## When to Use This Reference

Use this reference when working with:

- Creating course announcements
- Scheduling announcements for future publication
- Sending an announcement to some sections rather than the whole course

## Non-Negotiables

- Use `MMM d, yyyy, h:mm AM/PM` for `publish_date`.
- `specific_sections` does nothing unless `is_section_specific` is `true`.

---

## Attributes

| Attribute             | Required | Description                                                                   |
|-----------------------|----------|-------------------------------------------------------------------------------|
| `id`                  | yes      | Stable identifier                                                             |
| `title`               | yes      | Announcement title shown in Canvas                                            |
| `publish_date`        | no       | When the announcement publishes: `MMM d, yyyy, h:mm AM/PM`. Defaults to now    |
| `is_section_specific` | no       | `true` to send to named sections instead of the whole course                   |
| `specific_sections`   | no       | Canvas section IDs to send to, comma separated                                 |

---

## Content

The body of the tag supports Markdown or HTML.

---

## Example

```xml
<announcement id="welcome"
              title="Welcome to the Course"
              publish_date="Jan 13, 2025, 8:00 AM">
    # Welcome!

    Welcome to the course. Please review the syllabus and complete the orientation quiz before our first class.

    See you soon!
</announcement>
```

Scoped to two sections:

```xml
<announcement id="lab-swap"
              title="Lab sections swap rooms this week"
              publish_date="Jan 20, 2025, 8:00 AM"
              is_section_specific="true"
              specific_sections="37341,40884">
    Sections 002 and 004 meet in the other room on Thursday.
</announcement>
```

---

## Skeleton Template

```xml
<announcement id="[STABLE ID]"
              title="[ANNOUNCEMENT TITLE]"
              publish_date="[MMM d, yyyy, h:mm AM/PM]">
    # [ANNOUNCEMENT TITLE]

    [Announcement body here.]
</announcement>
```
