---
type: skill
description: Load when deciding where MDXCanvas curriculum, offering, target, or term-rollover data belongs. This document describes the course-info and global-args YAML files with a guide on deciding what information goes in each source of configuration.
---

# Course-info and Global-args Principles

## Purpose

Use this document as the source of truth for deciding whether MDXCanvas data belongs in:

- stable curriculum source or local metadata;
- the offering's `global-args.yaml` or `global_args.yaml`;
- top-level course-info configuration; or
- course-info `GLOBAL_ARGS`.

The distinction is determined by **what a value must remain synchronized with**, not simply whether the value is student-facing or whether it changes between terms.

Preserve the target repository's established filename, key casing, and configuration conventions. `global-args.yaml` and `global_args.yaml` are examples of the same role, not a reason to rename an existing file.

## Configuration layers

For runtime mechanics, load the [Jinja Operational Reference](jinja-templating-reference.md): course-info `GLOBAL_ARGS` is shallow-overridden by CLI `--global-args`, while `--args` and include `args` supply separate per-template data. It also documents supported formats, path contexts, and exact data access patterns.

### Stable curriculum and local metadata

Stable curriculum commonly includes outcomes, explanations, assignment intent and instructions, questions, rubrics, starter material, and stable resource IDs. Keep it in the unit, lesson, project, or shared curriculum source that owns it.

A fact used only by one lesson, project, or other bundle should normally remain in that bundle's local metadata, even if it varies by offering. Do not make a value global merely because it is a date or a Jinja variable.

### Offering-wide global args

The standalone global-args file contains facts that describe the rendered offering and should normally remain the same when that offering is rendered to different Canvas destinations.

Typical examples include:

- term and year;
- course start and end dates;
- lecture dates;
- assignment, quiz, project, and exam dates;
- offering-wide links;
- offering-wide instructor or staff information; and
- values reused by content throughout the course.

A useful test is:

> If this offering were rendered into both its production course and a test course, should this value normally remain the same?

If yes, the standalone global-args file is usually the correct owner.

### Top-level course-info

Top-level course-info values identify or control the deployment destination. Common examples are:

- `CANVAS_API_URL`;
- `CANVAS_COURSE_ID`;
- `LOCAL_TIME_ZONE`; and
- `DEPLOY_ROOT`.

These values tell MDXCanvas where or how to deploy; they are not curriculum or offering content. Credentials and tokens belong outside committed course-info files and outside version control.

A useful test is:

> Would changing this value cause MDXCanvas to target or interpret a different Canvas environment?

If yes, it belongs at the top level of course-info.

### Course-info `GLOBAL_ARGS`

`GLOBAL_ARGS` nested in course-info contains render data whose correctness is coupled to that particular Canvas target. These values are available to course templates like other global rendering arguments, but they must be selected together with the destination profile.

Typical examples include:

- `COURSE_SETTINGS` containing the target shell's name, code, and image;
- Canvas section IDs, because those IDs exist only inside a particular Canvas course;
- section lists represented by a combined Canvas shell;
- staffing or support information that differs between destination shells; and
- conspicuous production-versus-testing branding.

A useful test is:

> Could this value be correct for one Canvas destination and wrong for another destination receiving the same offering content?

If yes, course-info `GLOBAL_ARGS` is usually the correct owner.

## Decision order

Choose the first owner that fits:

1. **Stable instructional content?** Keep it in curriculum source.
2. **Owned by one local bundle?** Keep it in local metadata.
3. **Secret or credential?** Keep it outside committed source and configuration.
4. **Controls destination or deployment interpretation?** Put it at top-level course-info.
5. **Renderable data whose correctness depends on the selected destination?** Put it under course-info `GLOBAL_ARGS`.
6. **Shared fact about the offering regardless of destination?** Put it in the standalone global-args file.

Give every fact one authoritative home. Do not duplicate a value between local metadata, global args, and course-info to make templates convenient.

## Similar values can have different owners

Student visibility does not determine ownership. For example, a TA-hours link may belong in standalone global args when one offering-wide schedule should appear in production and test renders. A detailed TA schedule may instead belong in course-info `GLOBAL_ARGS` when different Canvas shells represent different sections and staff.

Likewise, offering-specific does not automatically mean standalone global args. Canvas-assigned section IDs are offering-specific, but they are also destination-specific and therefore belong with the target profile.

Determine ownership from the repository's actual deployment model and consumers rather than from the variable's name alone.

## Observed repository patterns

Example course repositories illustrate these boundaries:

- **CS 110:** the standalone global-args file owns its instructional calendar. Course-info `GLOBAL_ARGS` owns course branding, Canvas section IDs, section descriptions, TA schedules, and final-exam details that vary with the combined Canvas shell.
- **CS 301R:** the standalone global-args file owns dates, shared links, and TA information. Production and testing course-info profiles primarily vary destination settings and `COURSE_SETTINGS` branding.
- **CS 312:** the standalone global-args file owns dates, staff, support links, and other offering-wide content. Current course-info profiles own destination settings and production-versus-testing `COURSE_SETTINGS`.

These are examples of the synchronization rule, not schemas to copy blindly.

## Pairing course-info and global args

Course-info and standalone global args form an explicit deployment pair:

- global args select the offering's content and calendar;
- course-info selects the Canvas destination receiving that offering and supplies any target-bound render values.

A successful parse does not prove that the pair is correct. A retained course-info profile for an older term can be accidentally combined with current dates, staff, links, or section data. Conversely, a test target can receive production branding or target-only IDs if its profile is incomplete.

For every supported deployment variant:

1. name or document the intended course-info/global-args pairing;
2. confirm that required render keys exist across the combined configuration;
3. verify that term, year, dates, course name, code, image, sections, and staff describe the same offering and target;
4. inspect old, testing, and scratch profiles for stale assumptions;
5. audit hard-coded dates and target IDs outside both files; and
6. hand the exact pair to deployment validation.

Do not assume that storing files in the same directory makes every combination valid.

## Authoring workflow

Before adding or moving a variable:

1. Find every consumer, including templates, includes, conditions, section overrides, module labels, prose, and deployment commands.
2. Identify what event should cause the value to change: curriculum revision, local bundle maintenance, offering rollover, section/staffing change, or Canvas target change.
3. Select the owner using the decision order above.
4. Preserve established key spelling and casing; near-duplicate names are distinct Jinja variables.
5. Remove competing definitions rather than relying on undocumented precedence.
6. Render with every affected course-info/global-args pair.
7. Compare student-facing output and target-sensitive behavior, especially dates, sections, visibility, branding, and links.

Paths stored in args are interpreted by the template that consumes them. Confirm their relative context before moving values or files.

## Term rollover

Term rollover should be finite and reviewable:

1. select or create the intended standalone global-args file;
2. select or create the matching course-info profile;
3. update offering-wide dates, links, and staff in their authoritative locations;
4. update target IDs, branding, sections, and target-bound render data in course-info;
5. inspect local offering metadata;
6. search for hard-coded term values and Canvas IDs;
7. verify section overrides and exam windows; and
8. hand off the exact configuration pair for test deployment.

Do not move every changing value into one giant global file. Locality and synchronization remain more important than centralization.

## Anti-patterns

Avoid:

- treating all student-facing data as standalone global args;
- treating all term-varying data as course-info data;
- putting Canvas course or section IDs in curriculum source;
- storing credentials in either file;
- duplicating a value in course-info and standalone global args;
- depending on undocumented merge precedence;
- putting lesson-owned facts in a giant course-wide args file;
- renaming established files or keys only for stylistic consistency;
- assuming old, test, and production profiles are interchangeable; and
- validating one configuration while intending to deploy another.

## Handoff requirements

A Content Author or Course Architect handing work to deployment must identify:

- the entry point;
- the exact course-info file;
- the exact standalone global-args file;
- any target-bound `GLOBAL_ARGS`;
- affected terms, sections, staff, dates, links, and Canvas IDs;
- expected production-versus-testing differences; and
- unresolved pairing or stale-profile risks.

Never include credentials in the handoff.
