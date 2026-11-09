---
type: skill
description: Load for shared tag conversions, accepted date formats, effective defaults, aliases, and assignment/quiz section overrides.
---

# Shared tag parsing rules

These tag skills are authoritative for syntax. Instructor approval governs assessment settings, content, release dates, and visibility. Parser acceptance is not a promise that Canvas supports a value in every course or configuration.

## Attributes and defaults

Resource processors using `parse_settings` reject unknown attributes. A documented alias is accepted as input, not just an output name. If both spellings have nonempty values, the first documented/source spelling wins. Required attributes must be nonempty. Omitted optional fields are not sent unless a truthy default is documented. In particular declared `false`, empty-list, and empty-dictionary defaults are **not emitted**. Explicit `"false"` and `"0"` are nonempty strings and are parsed. Omission on update does not request a reset; do not infer Canvas creation defaults from parser omission.

- Booleans: case-insensitive `true` / `false` only, not `yes`, `1`, or a language name.
- Integers use Python `int`; finite decimals use `float` with NaN/infinity rejected.
- Lists: comma-separated, whitespace stripped, empty cells removed; legacy `|` separator works only when there is no comma.
- Dictionaries: comma-separated `key=value` pairs, with string values (no nested structures or escaping for commas/extra equals). Whitespace is stripped around each whole pair, not separately around its key and value.
- Stable resource references resolve source IDs through the resource graph, even for aliases ending in `_id`; they are not raw Canvas IDs.

## Dates

Fields using `parse_date` accept Python `datetime.fromisoformat` strings (for example `2026-01-15T23:59:00`, `2026-01-15T23:59:00-07:00`, or `2026-01-15`), plus `%b %d, %Y, %I:%M %p`, `%b %d %Y %I:%M %p`, and `%Y-%m-%dT%H:%M:%S%z`. Examples: `Jan 15, 2026, 11:59 PM` and `Jan 15 2026 11:59 PM`. They are serialized with `datetime.isoformat`; no timezone conversion occurs in this parser.

The active deployment binding only substitutes references and timestamps; it does **not** call the legacy `make_iso` date helper or automatically localize naive dates. Use explicit offsets when an unambiguous instant matters. Do not claim UTC conversion. File/zip/slides/mermaid lock/unlock values bypass `parse_date` and are forwarded as supplied; use explicit ISO timestamps for these and validate target behavior.

`late_due` on assignments and overrides is parsed and forwarded under that name. Current deployment does not translate it into `lock_at` or implement a separate late cutoff. Do not promise late-submission enforcement from it; `available_to` / `lock_at` is the mapped closing field.

## Section overrides (`assignment` and `quiz`)

An optional direct `<overrides>` child contains `<override>` children. Each override accepts exactly:

| Attribute | Required | Parsing |
|---|---|---|
| `section_id` / `course_section_id` | yes | Integer Canvas section ID |
| `available_from` / `unlock_at` | no | Date |
| `available_to` / `lock_at` | no | Date |
| `due_at` | no | Date |
| `late_due` | no | Date; forwarding caveat above |

No defaults are emitted. Identity derives from parent source ID and section ID; no separate `id` is accepted. Quiz overrides deploy through the quiz's backing Canvas assignment, so not every quiz configuration necessarily supports them. `only_visible_to_overrides` is a separate parent setting, not an automatic consequence of using overrides or an access code.

Resource fragment (section 12345 must exist in the approved target):

```xml
<assignment id="analysis-report" title="Analysis Report">
  <overrides>
    <override section_id="12345" due_at="2026-01-15T23:59:00-07:00" />
  </overrides>
  Submit the approved analysis report.
</assignment>
```

## Examples and wrappers

Examples labeled fragments require their containing resource and/or referenced files and IDs. Ellipses and bracketed skeleton placeholders are explanatory, not complete inputs. Markdown bodies require a `.md` suffix in the source suffix chain; Jinja requires final `.jinja` and runs before Markdown and helper preprocessing. Ordinary wrapper tags such as `<course>`, `<content>`, `<assignment-groups>`, and `<group-categories>` have no bespoke resource processor; their children are traversed. Do not treat arbitrary wrapper attributes as Canvas configuration.
