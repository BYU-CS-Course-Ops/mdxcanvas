---
type: skill
description: Load when creating, editing, or scheduling announcements with the <announcement> tag.
---

# `<announcement>` Tag

## When to Use This Reference

Use this reference when working with:

- Creating course announcements
- Scheduling announcements for future publication
- Sending an announcement to some sections rather than the whole course

## Non-Negotiables

- Use an accepted date form from [Shared parsing rules](parsing-rules.md) for `publish_date`.
- `specific_sections` is what scopes an announcement, and naming sections is all it
  takes. Canvas sets `is_section_specific` itself; that attribute is not supported
  here, and setting it will be reported as an unprocessed field.

---

## Attributes

| Attribute             | Required | Description                                                                   |
|-----------------------|----------|-------------------------------------------------------------------------------|
| `id`                  | yes      | Stable identifier                                                             |
| `title`               | yes      | Announcement title shown in Canvas                                            |
| `publish_date`        | no       | When the announcement publishes; omission currently defaults to the local current time during parsing |
| `specific_sections`   | no       | Canvas section IDs to send to, comma separated. Scopes the announcement |

---

Additional supported attributes: `is_announcement` is boolean with emitted default true; `delayed_post_at` is an accepted alias for `publish_date`. `specific_sections` is passed as a raw string, not list-parsed; no `is_section_specific` input is accepted. All fields other than the current-time fallback and `is_announcement` default are omitted when absent. See [Shared parsing rules](parsing-rules.md) for accepted dates and aliases.

## Publication default

`id` and `title` are required. Although the parser declares `publish_date` with `required=True`, `parse_settings` applies its non-empty default before checking required fields. Omitting it therefore uses `datetime.now().isoformat()` evaluated during parsing, not deployment time. Set an explicit approved date for deterministic scheduling. This describes current parser behavior, not a requirement to schedule every announcement.

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
              specific_sections="37341,40884">
    Sections 002 and 004 meet in the other room on Thursday.
</announcement>
```

---

## Skeleton Template (replace placeholders; not runnable)

```xml
<announcement id="[STABLE ID]"
              title="[ANNOUNCEMENT TITLE]"
              publish_date="[MMM d, yyyy, h:mm AM/PM]">
    # [ANNOUNCEMENT TITLE]

    [Announcement body here.]
</announcement>
```
