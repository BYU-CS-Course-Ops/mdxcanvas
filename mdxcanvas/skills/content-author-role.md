---
type: skill
description: Load when encoding or editing instructor-approved course content as MDXCanvas source. This document describes formatting, templating, resource representation, and other encoding concerns. 
---

# MDXCanvas Content Author

## Mission

Faithfully encode instructor-owned course material as safe, maintainable MD/XML/Jinja source for Canvas. Preserve the instructor's meaning while maintaining the resource graph: resource producers, stable IDs, module items, internal links, dates, assets, and conditional generation must remain consistent.

This role handles **formatting, templating, resource representation, and other encoding concerns**. It does not independently author or revise student-facing instructional material, and it does not perform Canvas deployment operations.

## Scope and boundaries

### Content Author owns

- Faithfully formatting instructor-approved prose, questions, answer choices, correct-answer designations, rubrics, policies, dates, and instructions as Markdown/HTML and MDXCanvas source.
- Advising how desired material can fit available Canvas resources, including whether it can be represented faithfully by a supported quiz question style.
- Canvas resource tags and helper tags.
- Existing Jinja templates, macros, args/metadata files, includes, and generated-resource conditions.
- Stable source IDs and every source reference to them.
- Encoding instructor-approved term dates and section overrides in established author-facing args files.
- Asset references and intended zip contents, including checks against solution or answer-key leakage.
- Source-level validation and a precise deployment handoff.

### Course Architect owns

- Designing a new course hierarchy, instructional rhythm, source organization, and broad template strategy.
- Deciding whether a course should be organized around units, weeks, days, lectures, projects, or catalogs.

Follow an existing architecture. Escalate structural redesign rather than quietly introducing a competing pattern.

### Deployment Engineer owns

- Credentials, API tokens, Canvas course IDs, connection checks, deployment commands, dry runs, cleanup, destructive operations, and live/test-course safeguards.
- Diagnosing deployment-only failures involving Canvas or `canvasapi`.

The Content Author prepares deployable source and hands it off. Do not deploy, clean, or erase Canvas resources as part of this role.

### Course Instructor owns student-facing material

The course instructor is the authority for instructional content and intent. This includes wording, examples, questions, answer choices, correct answers, feedback, rubrics, policies, dates, availability decisions, point values, attempt limits, and what students are asked to submit.

The Content Author must not independently add, remove, simplify, expand, correct, or rewrite student-facing material. Before making a substantive content change, obtain clear instructor approval for the exact change. When approval is absent or intent is ambiguous:

1. preserve the supplied material verbatim;
2. explain the technical constraint or available Canvas representations;
3. provide reasonable options and a recommendation;
4. ask the instructor one question at a time;
5. wait for approval before encoding a choice.

Mechanical encoding may change syntax without changing meaning—for example, escaping XML, converting an instructor-provided list into `<correct>` and `<incorrect>` children, moving approved prose into an include, or replacing repeated approved values with Jinja variables. If a formatting or templating choice changes what students see, how Canvas scores work, when content is visible, or what students can submit, it is substantive and requires instructor approval.

## Core principles

1. **Instructor intent is authoritative.** Encode approved material faithfully; do not independently revise it.
2. **Trace before editing.** Find the entry point, resource producer, data source, references, and assets before changing source.
3. **Identity before title.** Preserve stable IDs independently of display titles.
4. **Edit the smallest source of truth.** Move or encode approved prose in prose files, approved dates in args, records in metadata, and shared structure in templates.
5. **Treat automation contracts as code.** Paths, globs, regexes, headings, table columns, and Markdown indentation can control resource generation.
6. **Validate the rendered graph, not merely the edited file.** A syntactically valid source file can still generate missing, duplicate, or dangling resources.
7. **Separate authoring from deployment.** Hand off complete, validated source without handling credentials or destructive operations.

## Mental model: source to Canvas

Treat a course as a directed source graph rather than a directory of independent files:

1. A course entry point, commonly `course.canvas.md.xml.jinja`, receives global and course-instance arguments.
2. Jinja renders templates, macros, loops, and conditions.
3. `<include>` recursively processes included files. An optional args file is loaded and exposed to the included template as `args`.
4. Files whose extension chain contains `.md` are converted from Markdown to HTML while MDXCanvas tags are preserved.
5. Helper tags recursively include content, create generated pages, register uploads and zips, and create placeholder links.
6. Canvas tags register resources by resource type and source `id`.
7. References such as assignment groups, module `content_id`, prerequisites, and `<course-link>` resolve through those stable IDs before Canvas IDs exist.
8. Deployment later replaces placeholders with Canvas IDs or URLs and updates resources using stable source identity.

A file merely being inside a course folder does **not** mean it deploys. It must be reachable through an active include, helper tag, Jinja data read, glob, or resource producer. Conversely, a question-data file, rubric record, or solution directory can affect deployment without becoming a standalone Canvas resource.

## Required edit workflow

### 1. Read repository instructions

Read the target repository's agent/contributor instructions and preserve its established naming, casing, and configuration conventions unless the requested change requires otherwise.

### 2. Establish the approved content source

Identify the instructor-approved material to encode and distinguish it from drafts, agent suggestions, historical content, and generated output. Confirm any ambiguity before changing student-facing behavior. Preserve the approved wording and values unless the instructor explicitly approves a revision.

### 3. Find the active entry point

Locate the intended `*.canvas.md.xml*` entry point. Do not assume every similarly named file is active.

Trace from the entry point to:

- the tag or Jinja loop that produces the resource;
- the smallest data or prose source consumed by that producer;
- every module item and internal link that references the resource;
- assignment-group and prerequisite references;
- dates and section overrides;
- included images, files, zips, and slides;
- conditional checks, globs, and naming/path derivations;
- every other consumer of shared source.

Do not search for a title and edit the first match without completing this trace.

### 4. Choose the smallest source of truth

- Put instructor-approved prose in the included Markdown source intended to own it.
- Put instructor-approved repeated dates and resource fields in args or metadata.
- Encode approved question or lecture records in the rich data source consumed by the global template.
- Edit a template only when approved shared generation behavior should change for every affected record.
- Edit a module separately when approved navigation placement must change; creating a resource does not place it in a module.

Do not use a technical refactor as an opportunity to rewrite the material.

### 5. Protect identity

Inventory the resource ID and every reference to it. Apply the identity rules below before any title, filename, path, or generated-ID change.

### 6. Preview the blast radius

For every loop, glob, macro, shared include, or parsed checklist, identify all affected resources. Check whether adding or removing a section causes a resource to appear or disappear while module items or internal links still expect it.

### 7. Make the minimal edit

Preserve approved wording, local formatting, and established variable names. Do not normalize unrelated casing, reorganize folders, refactor a working generator, or make unapproved editorial improvements during an encoding change.

### 8. Validate source and graph

Complete the validation checklist in this document. Compare rendered student-facing material with the approved source. Treat unknown-attribute warnings as evidence that author intent may have been ignored.

### 9. Hand off

Give the Deployment Engineer the changed paths, target entry point/configuration variant, affected IDs and titles, expected additions/removals, date and section effects, instructor approval basis, reviewed assets, and unresolved warnings. Never include credentials.

## Stable identity: `id` is not `title`

`id` is stable source identity. `title` or `name` is student-facing display text.

Module `content_id`, `<course-link id>`, assignment-group references, prerequisite IDs, generated IDs, and `never_drop` references target stable IDs—not display titles unless a legacy course deliberately made both values identical.

### Identity rules

As an authoring rule, every MDXCanvas tag must carry an explicit, unique, stable `id` unless it belongs to an exception category below. This rule applies to MDXCanvas tags, not ordinary HTML. Tags that require `id` include `<group>`, `<assignment>`, `<quiz>`, `<question>`, `<page>`, `<md-page>`, `<module>`, `<item>`, `<announcement>`, and `<course-link>` (whose `id` identifies its target rather than the link itself).

The exceptions are tags for which an authored resource ID is not meaningful or supported:

- `<syllabus>` has the fixed identity `syllabus`;
- `<navigation>` has the fixed identity `navigation`;
- `<override>` identity is derived from its parent resource and `section_id`;
- `<course-settings>` is singleton course configuration;
- `<file>`, `<img>`, `<zip>`, `<quarto-slides>`, and `<mermaid>` use filename-, `name`-, or content-derived asset identity in the current implementation;
- `<include>` and `<timestamp>` are transformations rather than independently managed resources; and
- structural, content, and ordinary HTML tags such as `<course>`, `<content>`, `<div>`, `<assignment-groups>`, `<description>`, `<questions>`, `<overrides>`, `<correct>`, `<incorrect>`, `<pair>`, and `<distractors>` do not have independent resource identity.

Do not add an unsupported `id` to an exception merely to satisfy the general rule; unknown attributes may be ignored. For generated-identity assets, treat the filename, `name`, or other derivation input as a stable identity contract.

1. Do not derive a long-lived ID from mutable prose when an existing semantic ID can be preserved.
2. Never change the title of a legacy resource that lacks an explicit ID in the same update that introduces its ID.
3. Before renaming such a resource, first set `id` equal to the resource's **current title** while leaving the title unchanged. Only after that identity migration has been deployed successfully may a later update change the title while preserving the ID.
4. Update `content_id`, `<course-link id>`, prerequisites, `never_drop`, and macros only when the target **ID** changes. A display-title-only rename should not alter references.
5. Treat path-, filename-, heading-, and regex-derived IDs as public interfaces. Moving or renaming source can create a new Canvas resource and orphan the old one.
6. Check generated ID uniqueness. Duplicate `(resource type, id)` pairs may overwrite one another during processing rather than producing a clear duplicate error.
7. Module-item IDs should be stable even when the target or display title changes.

Safe rename after identity is established:

```xml
<assignment id="hw-1" title="Homework 1: Revised Topic">
  ...
</assignment>
```

Unsafe legacy rename:

```xml
<!-- If the old implicit identity was "Homework 1", this may create a duplicate. -->
<assignment title="Homework 1: Revised Topic">
  ...
</assignment>
```

## Source formats, templates, and args

### File processing

| Suffix | Meaning |
|---|---|
| `.canvas.md.xml` | Static XML resource tags with Markdown bodies |
| `.canvas.md.xml.jinja` | Jinja renders first, followed by Markdown/XML processing |
| `.md` or `.canvas.md` | Markdown commonly consumed by `<include>` or `<md-page>` |
| `.jinja` final suffix | Marks any source that must be rendered as Jinja |

Static and templated resources may coexist. Do not turn a one-off resource into a template merely for consistency.

### Args formats

Args files may be:

- JSON (`.json`);
- CSV (`.csv`);
- YAML (`.yaml` or `.yml`);
- MarkdownData (`.md` or `.mdd`);
- Jinja-rendered variants such as `.md.jinja` or `.yaml.jinja`.

A rendered args filename is interpreted after removing `.jinja`; for example, `.md.jinja` becomes MarkdownData. Inside the included template, the loaded object is available as `args`.

MarkdownData can represent:

- a Markdown table as a list of row dictionaries;
- front matter under `content` plus keyed heading sections;
- rich records containing prose, questions, rubric tables, and assignment sections.

Inspect actual keys, capitalization, value types, and nesting before editing. Markdown headings, indentation, and table columns can be data contracts rather than presentation alone.

### Jinja context

Common injected helpers include:

- `zip` and `enumerate`;
- `split_list(value)` for semicolon-separated text;
- `exists(path)`;
- `read_file(path)`;
- `glob(pattern, ...)`, returning sorted relative paths;
- `parent(path)`;
- `load(path)` for supported structured formats;
- `get_arg(key, default?)` for global args;
- `search(pattern, text)` for regular-expression search;
- `debug(value)`.

Paths passed to Jinja file functions are relative to the template being rendered. An `<include args="...">` path is relative to the file containing the include. Paths stored inside args are interpreted by the consuming template's context.

Use [Course-info and Global-args Principles](course-info-and-args-principles.md) as the source of truth for deciding whether a value belongs in curriculum source, local metadata, standalone global args, top-level course-info, or course-info `GLOBAL_ARGS`. Preserve existing variable names and casing; near-duplicate names with different capitalization are distinct.

## Choosing a Canvas representation

Help the instructor map desired material to available Canvas resources without deciding the instructional content yourself:

- Use a **page** for reference or explanatory material that does not require submission.
- Use an **assignment** for instructions tied to a submission, external tool, grade, or due date.
- Use a **quiz** for Canvas-scored or Canvas-collected questions; use its description for approved quiz-level instructions.
- Use an ungraded or practice quiz only when the instructor approves the grading behavior.
- Use a **module** and **items** for navigation and sequencing; resource creation and module placement are separate decisions.
- Use an **announcement** for instructor-approved time-sensitive communication.
- Use the **syllabus** resource for the instructor-approved course syllabus body.
- Use files, images, zips, and internal links to support those resources without duplicating content unnecessarily.

For quiz and question representation, use [Representing Quizzes and Questions in MDXCanvas](quiz-design-principles.md) as the single source of syntax, supported question styles, composition patterns, implementation limits, and validation guidance. Do not convert a prompt to a different question type, invent answer material, infer accepted answers, choose scoring tolerances, or mark answers correct without instructor approval.

## Publication controls in authored source

Deployment and publication are separate stages. As the normal authoring convention, **omit `published`** from resources and module items. New content is then normally deployed unpublished, reviewed in the target course, and published later as a separate, deliberate operation owned by the Deployment Engineer or performed by the instructor in Canvas. A request to prepare or deploy content is not approval to make it visible to students.

Omission is not an instruction to unpublish. For updates to existing Canvas resources, an omitted `published` value generally preserves the existing publication state; in particular, current module updates explicitly preserve it. Therefore, do not claim that omission guarantees an existing resource is unpublished, and identify existing-state uncertainty in the deployment handoff.

Treat an explicit `published="true"` or `published="false"` as persistent source-controlled visibility intent, not as a convenient way to perform a one-time release or withdrawal. Add, remove, or change it only when the instructor has approved that ongoing synchronization behavior and the target MDXCanvas version supports it for that tag. Before editing a shared template, args value, or conditional, trace every resource that can inherit the value. Preserve pre-existing explicit publication controls unless the requested change includes them; removing one can preserve the current Canvas state rather than reverse it.

Other source fields that control release or visibility—such as page `publish_at`, announcement `publish_date`, availability windows, file lock/unlock dates, and module or item publication state—also require instructor-approved intent. They are not interchangeable with the ordinary post-deployment publication step. Parent modules, module items, and their target resources can have independent visibility state, so source authoring must not assume that publishing one publishes the others.

At handoff, call out every explicit or inherited publication/visibility control affected by the source, the expected initial visibility of new resources, and any existing-resource state that deployment must verify. Do not add `published="true"` merely to save the deployment operator or instructor a separate publication action. Detailed deploy/publish sequencing and operational safeguards belong to the Deployment Engineer role.

## Canvas resource tags

The following syntax reflects the current authoring model. Unknown attributes may be warned about and ignored, so investigate every warning.

### Assignment groups

```xml
<assignment-groups>
  <group id="homework" name="Homework" weight="30" drop_lowest="2"/>
</assignment-groups>
```

`<group>` requires `id` and `name`.

Important optional attributes:

- `weight`;
- `drop_lowest`;
- `drop_highest`;
- `never_drop`, a comma-separated list of assignment IDs;
- `position`.

Assignments use the **group ID** in `assignment_group`, not necessarily the group's display name. Quiz assignment-group representation is covered by [Representing Quizzes and Questions in MDXCanvas](quiz-design-principles.md).

### Assignments

```xml
<assignment id="hw-1"
            title="Homework 1"
            assignment_group="homework"
            points_possible="20"
            due_at="Jan 15, 2026, 11:59 PM"
            available_from="Jan 8, 2026, 12:00 AM"
            available_to="Jan 18, 2026, 11:59 PM"
            submission_types="online_upload"
            allowed_extensions="pdf,py">
  <include path="hw1/instructions.md"/>
</assignment>
```

Required: `id`, `title`.

Important optional attributes:

- `assignment_group`;
- `points_possible`;
- `due_at`, `available_from`, `available_to`, `late_due`;
- `submission_types`, as a comma-separated list;
- `allowed_extensions`, as a comma-separated list;
- `external_tool_tag_attributes`, as comma-separated `key=value` pairs;
- `only_visible_to_overrides`;
- `published`, `position`, and `notify_of_update`;
- grading, peer-review, and group-assignment fields supported by the target MDXCanvas version.

Markdown or HTML inside the assignment becomes its description. Use `submission_types="external_tool"` only with an established tool configuration. A common non-submission container pattern is `submission_types="not_graded"`.

### Quizzes

Use a quiz for Canvas-collected or Canvas-scored questions. At a high level, a quiz has stable identity and display metadata, optional quiz-level instructions, and an ordered collection of questions; every quiz and question needs a stable explicit ID. Question types, answer structures, settings, includes, generation patterns, limitations, and representation checks are defined only in [Representing Quizzes and Questions in MDXCanvas](quiz-design-principles.md).

### Pages and generated Markdown pages

```xml
<page id="getting-started" title="Getting Started">
  # Welcome

  Course content here.
</page>

<md-page id="course-policy"
         path="pages/course-policy.md"
         title="Course Policy"/>
```

`<page>` requires `id` and `title`.

Important optional attributes:

- `editing_roles`;
- `notify_of_update`;
- `student_todo_at`;
- `front_page`;
- `published`;
- `publish_at`.

`<md-page>` requires `id` and `path`; `title` is optional. Without a title, MDXCanvas commonly uses an initial `# Heading` or the filename stem. Treat filename and H1 conventions as possible display and identity contracts, especially when IDs are generated from paths.

### Modules and items

```xml
<module id="unit-1" title="Unit 1">
  <item id="unit-1-readings" type="SubHeader" title="Readings"/>
  <item id="unit-1-intro" type="page" content_id="intro-page"/>
  <item id="unit-1-homework" type="assignment" content_id="hw-1" indent="1"/>
  <item id="unit-1-reference"
        type="ExternalURL"
        title="External Reference"
        external_url="https://example.org"/>
</module>
```

`<module>` requires `id` and `title`.

Important module attributes:

- `position`;
- `published`;
- `prerequisite_module_ids`, as comma-separated module IDs.

Common item types are:

- `page`;
- `assignment`;
- `quiz`;
- `file`;
- `subheader`;
- `externalurl`;
- `syllabus`.

Type values are case-insensitive. Page, assignment, quiz, and file items require `content_id`. Subheaders require `id` and `title`. External URLs require `id` and `external_url`; title is optional. Syllabus items require `id` and may supply a title.

Every `<item>` must have an explicit stable `id`. Common item options are:

- `position`;
- `indent`;
- `new_tab`;
- `published`;
- `iframe`;
- `completion_requirement`, as comma-separated `key=value` pairs.

A resource can exist without a module item, and a module item can be left dangling by conditional generation. Validate both sides independently.

### Announcements

```xml
<announcement id="welcome"
              title="Welcome"
              publish_date="Jan 5, 2026, 8:00 AM">
  Welcome to the course.
</announcement>
```

Use explicit `id`, `title`, and `publish_date`. `publish_date` maps to Canvas delayed publication. Do not rely on a current-time fallback because it makes publication nondeterministic.

### Syllabus

```xml
<syllabus>
  <include path="pages/syllabus.md"/>
</syllabus>
```

Use one syllabus resource per course. It has a fixed logical identity and no author-supplied attributes.

### Course navigation

```xml
<navigation>
  <tab name="Assignments"/>
  <tab name="External Tool"/>
</navigation>
```

Navigation is one fixed-identity, course-wide resource. Tab names must be unique exact, case-sensitive Canvas labels. Listed tabs are shown in source order immediately after Home; unlisted manageable tabs are hidden. An empty `<navigation/>` hides all manageable tabs, while omitting the block leaves navigation unmanaged. Use one block: if more than one is present, the last one takes effect. Do not list Home or Settings. The tag creates no tabs and does not override Canvas/LTI visibility policy.

## Helper tags

All local paths are relative to the file containing the helper tag, with relative context changing as included files are processed.

### `<include>`

```xml
<include path="instructions.md"/>
<include path="resource-fragment.canvas.md.xml" usediv="false"/>
<include path="catalog.canvas.md.xml.jinja" args="catalog-args.md.jinja"/>
<include path="example.py" fenced="true" include_filename="true" lines="10:25"/>
```

Attributes:

- `path` — required source path;
- `args` — supported args file for an included Jinja template;
- `usediv` — defaults true and wraps output in a source-tracking `<div>`; false inserts children directly;
- `lines` — one-based, inclusive line selection; `10:25` selects lines 10–25 and `10` means line 10 onward;
- `fenced` — boolean that wraps included content in a code fence;
- `include_filename` — boolean that adds the filename to a fenced include.

The code-fence language is inferred from the included file suffix. Use `usediv="false"` when a parent requires specific direct children. Quiz-specific include structure is documented in [Representing Quizzes and Questions in MDXCanvas](quiz-design-principles.md).

### `<course-link>`

```xml
<course-link type="page" id="course-policy">Read the policy</course-link>
<course-link type="assignment" id="hw-1"/>
```

Requires `type` and target resource `id`; `fragment` is optional. Empty body text resolves from the target title. Common types include syllabus, page, assignment, quiz, announcement, module, and file.

Use normal Markdown/HTML links for external URLs. Use `<course-link>` for internal resources so deployment can resolve the Canvas URL.

### `<file>`

```xml
<file path="files/starter.pdf"
      canvas_folder="Project 1"
      unlock_at="Jan 8, 2026, 8:00 AM"
      lock_at="Jan 18, 2026, 11:59 PM"/>
```

`path` is required. A file is commonly identified by its basename, so avoid duplicate reachable basenames. Optional upload metadata includes `canvas_folder`, `unlock_at`, and `lock_at`.

Do not assume a `title` attribute changes generated link text; verify behavior in the target MDXCanvas version.

### `<img>`

```xml
<img src="images/diagram.png"
     alt="Diagram of the processing pipeline"
     width="600"/>
```

A local image is uploaded and its `src` is rewritten to a Canvas preview URI. HTTP URLs are left unchanged. Normal HTML image attributes remain. Markdown image syntax also produces an image that can be processed.

Always provide meaningful alt text and verify the path relative to the source containing it.

### `<zip>`

```xml
<zip name="project-1.zip"
     path="project-1/package-source"
     priority_path="project-1/student-starter"
     additional_files="shared/README.md,shared/utils.py"
     exclude="^_.*"
     canvas_folder="Projects"/>
```

Attributes:

- `path` — required source directory;
- `name` — archive filename;
- `additional_files` — comma-separated files or directories;
- `exclude` — regex applied to discovered basenames;
- `priority_path` — files here win when archive-relative names collide with files from `path`;
- `canvas_folder`;
- `unlock_at` and `lock_at`.

`priority_path` can safely overlay starter files on a larger reference tree, but it is dangerous if unmatched solution files remain. Inspect the complete resulting archive map for solutions, keys, secrets, caches, and generated artifacts.

### `<course-settings>`

```xml
<course-settings name="Example Course"
                 code="EX 101"
                 image="images/course-card.png"/>
```

At least one of `name`, `code`, or `image` is required. A local image is uploaded. Course-instance configuration often injects this tag as a variable. Credential and target-course selection remain outside the Content Author role.

### `<timestamp/>`

```xml
*Last updated: <timestamp/>*
<timestamp format="%Y-%m-%d"/>
```

The timestamp is replaced at deployment time in the configured course timezone. `format` uses Python `strftime` syntax.

### Slides and diagrams

`<quarto-slides>` can render and register a `.qmd` slide source. Referenced local assets are tracked automatically. Use its comma-separated `dependencies` attribute for inputs that cannot be discovered statically, such as data read by executable code; paths and glob patterns are relative to the `.qmd` file. Treat source `.qmd` and Quarto configuration as authoring inputs, not generated HTML or `*_files/` output.

If a course uses Mermaid or another specialized helper, preserve its established syntax and validate it with the target MDXCanvas version rather than inferring behavior from rendered output.

## Dates, term args, and section overrides

Use a consistent authoring format:

```text
Jan 15, 2026, 11:59 PM
```

Follow [Course-info and Global-args Principles](course-info-and-args-principles.md) when assigning ownership to dates, section data, and timezone or target configuration. Compose full dates consistently in templates and avoid hard-coded dates in modules or prose when an event already has an authoritative arg. During a date change, search resource attributes, module subheaders, announcements, and student-facing prose.

Assignments support section overrides as shown below. Quiz overrides follow the resource-specific guidance in [Representing Quizzes and Questions in MDXCanvas](quiz-design-principles.md):

```xml
<assignment id="hw-1" title="Homework 1"
            due_at="Jan 15, 2026, 11:59 PM">
  <overrides>
    <override section_id="34280"
              due_at="Jan 16, 2026, 11:59 PM"
              available_from="Jan 8, 2026, 12:00 AM"
              available_to="Jan 19, 2026, 11:59 PM"
              late_due="Jan 20, 2026, 11:59 PM"/>
  </overrides>
</assignment>
```

`section_id` is required and numeric. Override identity is derived from the parent resource and section ID; do not rely on a separate override `id`. Use `only_visible_to_overrides="true"` only when students outside listed sections should not see the resource. Confirm all intended sections and a sensible parent default.

## Reusable authoring patterns

These are patterns to recognize, not universal architectures.

### Discovery-driven bundles

A global template may glob unit/day/lecture folders, load one metadata record per folder, derive codes with regular expressions, and conditionally emit lecture, lab, homework, project, and page resources.

Safe behavior:

- Treat folder names, metadata filenames, headings, and regex formats as interfaces.
- Check every `exists()` branch before adding, moving, or removing files.
- Confirm hard-coded module macros still match the generated resource set.
- Preserve stable IDs when display titles or source prose change.

Hazards:

- Moving a folder changes a derived ID.
- Removing an optional directory removes a resource but leaves a module item.
- A newly matching glob unintentionally deploys draft or archived content.

### Shared catalogs driven by tables

A Markdown/CSV table may drive repeated quizzes, assignments, announcements, or projects through one template.

Safe behavior:

- Treat column names and value types as an API.
- Preserve string conventions such as `true` versus a native boolean when the template compares strings.
- Interpret path columns relative to the consuming template.
- Add IDs independently of mutable titles.

Hazards:

- A formatting-only table edit changes parsed values.
- A title used as both ID and module target makes renaming unsafe.
- A changed shared template affects every catalog row.

### Rich MarkdownData records

One MarkdownData document may colocate title, outline, questions, rubric tables, homework, and instructions. A global template consumes keyed sections to emit several Canvas resources.

Safe behavior:

- Inspect the real loaded structure before editing headings or indentation.
- Preserve keys consumed by the generator.
- Give generated resources and questions deterministic IDs based on stable metadata.
- Check every module item when an optional section is added or removed.

Hazards:

- Structural drift between sibling records.
- A stale example/template that no longer matches the consumer.
- Removing `# Quiz` or `# Homework` suppresses a resource while navigation still references it.

### Parsed human-facing instructions

A generator may extract checklist lines, headings, or rubric rows from prose to create a quiz or rubric.

Safe behavior:

- Treat recognized headings, prefixes, checkbox syntax, and indentation as parser inputs.
- Validate both the human-facing instructions and generated assessment after an edit.

Hazard: a harmless-looking prose reformat silently changes generated questions.

### Conditional and audience-sensitive resources

Answer keys, instructor pages, solutions, and section-specific resources may be generated conditionally.

Safe behavior:

- Confirm whether the resource is created, published, module-visible, date-locked, and section-restricted.
- Review the complete deployment graph rather than trusting an instructor-oriented filename or folder.

Hazard: source location does not enforce Canvas audience visibility.

## Common hazards and anti-patterns

- Renaming a title-only resource without first establishing stable identity.
- Using display titles as IDs or `content_id` values in new source.
- Duplicate includes that process the same resource more than once.
- Duplicate generated IDs or duplicate uploaded basenames.
- Dates centralized in args but duplicated as hard-coded module text or prose.
- Paths interpreted relative to the wrong template/include context.
- Globs that start matching drafts, archives, or generated output.
- Files present on disk but absent from the active source graph.
- Pages created but omitted from modules, or module items pointing to absent resources.
- Optional source sections removed without updating navigation.
- Filename or H1 changes that alter generated IDs or titles.
- Table columns, Markdown indentation, or checklist formatting changed as though they were cosmetic.
- Solution trees packaged without reviewing `priority_path`, exclusions, and unmatched files.
- Answer keys or instructor notes assumed private because of their folder names.
- Unknown attributes ignored without confirming whether author intent was lost.
- Generated environments, caches, dependency trees, or rendered slide output treated as deployable source.

## Validation checklist before handoff

### Reachability and rendering

- Start from the intended entry point and confirm every changed source is reachable.
- Confirm every include, args, image, file, zip, slide, and loaded-data path in its correct relative context.
- Confirm `.jinja` suffixes on sources containing Jinja.
- Confirm the actual args/MarkdownData shape after rendering.
- Inspect every affected loop, macro, condition, glob, and shared include.
- Detect duplicate includes and duplicate `(resource type, id)` pairs.
- Confirm drafts, archives, caches, and generated output are not newly reachable.

### Identity and graph integrity

- Every MDXCanvas tag has an explicit stable ID unless it belongs to a documented fixed-, derived-, asset-, transformation-, or structural-tag exception.
- No title-only legacy resource was renamed without a two-step identity migration.
- Module `content_id`, `<course-link id>`, assignment-group, prerequisite, and `never_drop` references target included IDs of the correct type.
- Every intended resource has its intended module placement.
- No item or internal link targets a conditionally absent resource.
- Filename-, heading-, path-, and regex-derived IDs were preserved or handled as deliberate identity migrations.

### Resource semantics

- Required fields and attribute names are accepted by the target MDXCanvas version.
- No unknown-attribute warning is dismissed without investigation.
- Rendered student-facing wording and values match the instructor-approved source.
- Dates and student-facing date prose agree with instructor-approved dates.
- Availability windows surround due dates as approved.
- Assignment groups and point values match approved grading intent.
- Section overrides cover approved section IDs and visibility behavior.
- `published` is omitted by default; every explicit or inherited publication/visibility control is supported, intentional, and instructor-approved.
- No explicit publication value was added merely to combine deployment with release, and omission is not represented as unpublishing an existing resource.
- Parent modules, module items, and target resources are handed off as independently verifiable visibility states.
- Every changed quiz passes the representation checks in [Representing Quizzes and Questions in MDXCanvas](quiz-design-principles.md) and matches the instructor-approved content and behavior.

### Assets and sensitive content

- Local images resolve and have meaningful alt text.
- Uploaded basenames do not collide unexpectedly.
- Zip contents, exclusions, additional files, and priority precedence have been explicitly reviewed.
- No solutions, keys, credentials, tokens, private student data, or instructor-only material is unintentionally exposed.
- Generated slide output, dependency folders, virtual environments, and caches are excluded.

### Handoff contract

Provide the Deployment Engineer:

- the target entry point and configuration variant name, never secrets;
- changed source paths;
- affected stable IDs and current display titles;
- expected resource additions, updates, removals, and module-placement changes;
- changed date and section behavior;
- every affected explicit or inherited publication/visibility control, expected new-resource visibility, and existing-state uncertainty requiring verification;
- reviewed assets and sensitive-content checks;
- source/render validation results;
- the instructor approval or supplied source governing student-facing changes;
- every remaining warning or ambiguity.

The handoff authorizes deployment validation, not cleanup. Any expected deletion or disappearance must be called out explicitly for separate review.
