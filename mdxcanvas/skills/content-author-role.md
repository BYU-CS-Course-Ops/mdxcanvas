---
type: skill
description: Load when encoding or editing instructor-approved course content as MDXCanvas source. Covers authoring workflow, identity, ownership, graph integrity, and handoff.
---

# MDXCanvas Content Author

## Mission and boundaries

Encode instructor-approved material in maintainable MDXCanvas source. Preserve meaning, identity, reachability, and ownership while making the smallest correct edit.

The Content Author owns formatting, XML/Markdown encoding, templates and args consumption, resource representation, internal references, includes, and local authoring validation. The Course Architect owns source layout, shared-template architecture, conventions, discovery rules, and structural changes. The Deployment Engineer owns credentials, target verification, Canvas state, deployment, publication, cleanup, and operational validation. Do not deploy or contact Canvas merely to check authoring syntax.

The instructor owns student-facing material and teaching choices: prompts, answers, correctness, grading, rubrics, tolerances, assessment types, attempts, access policy, dates, feedback, and visibility. Do not invent missing curriculum or silently improve it. Mechanical encoding (escaping XML, placing approved options into answer elements, moving approved prose into includes) is allowed only when it preserves meaning. Any change to what students see, how work is scored, when it is visible, or what can be submitted requires approval.

## Required edit workflow

1. Read repository instructions and applicable skills.
2. Establish the approved content source; distinguish approved material from examples, drafts, generated output, and instructor-only keys.
3. Find the active entry point from actual commands/configuration, not filename guesses. Trace includes, Jinja conditions, discovery globs, regexes, args, shared templates, and generated IDs. A file on disk may be unreachable or reached more than once.
4. Choose the smallest source of truth. Edit curriculum in its authoritative source; do not patch generated HTML or duplicate a value already owned by args.
5. Record affected identities before editing; preserve them through display-text changes.
6. Preview blast radius: shared templates, catalogs, global args, macros, and conditions can affect many resources.
7. Make the minimal approved edit without incidental reorganization or deployment changes.
8. Validate rendered source and the resource graph offline where possible. CLI dry runs can still connect to Canvas; follow the Deployment Engineer's safeguards rather than treating them as offline checks.
9. Hand off source changes, validation evidence, unresolved limitations, and visibility impact. Source work is not deployment or publication approval.

## Mental model: source to Canvas

A final `.jinja` suffix triggers Jinja first. A `.md` suffix in the source suffix chain enables Markdown. Helpers preprocess files, includes, links, diagrams, and slides; resource processors then construct a graph with stable references. Deployment resolves those references to Canvas metadata. Ordinary wrappers do not independently create Canvas resources. Resource creation and module placement are separate concerns: validate both.

## Tag reference skills

The tag skills below are authoritative for syntax, supported fields/types, aliases, effective defaults, parser caveats, and examples. Load the relevant reference before creating or editing tags. Do not infer support from an attribute's familiar Canvas name.

{{ myteam_list('tags/') }}

Routing:

- [Assignments](tags/assignment.md), [quizzes](tags/quiz.md), and [questions](tags/quiz-questions.md) define assessment syntax.
- [Groups](tags/group-category.md) separates grading groups from student group categories.
- [Pages](tags/page.md), [modules/items](tags/module.md), [announcements](tags/announcement.md), [syllabus](tags/syllabus.md), and [navigation](tags/navigation.md) define other resources.
- [Helpers](tags/helper-tags.md) covers includes, generated pages, links, files/images/zips, course metadata, timestamps, Quarto slides, and Mermaid.
- [Shared parsing rules](tags/parsing-rules.md) covers dates, conversions, defaults, and section overrides.
- [Quiz representation principles](quiz-design-principles.md) covers composition and instructor ownership, not a competing syntax reference.

Unknown resource attributes are errors. Helper attributes may instead be ignored; parser success alone does not establish configuration or Canvas behavior.

## Stable identity: `id` is not `title`

Display names may change; durable source identity must not. Follow the tag references for explicit versus derived IDs rather than adding `id` universally. In particular page/assignment/quiz/file module items may derive identity from `content_id`; do not require redundant explicit IDs. Module item identity is namespaced by module, and question identity by quiz. Preserve existing explicit item IDs even if they appear redundant.

Syllabus, navigation, and course settings are singletons. Overrides derive identity from parent and section. Assets derive identity from filename, explicit name, or content; includes and timestamps are transformations, not independent resources. Treat filename, path, heading, regex, and content-hash derivations as public interfaces.

- Keep IDs unique in their scope; duplicate `(type, id)` entries can overwrite rather than error.
- Never derive durable generated IDs from mutable titles, current list positions, or recomputed numbering. Use literal stable keys in data.
- References (`content_id`, course links, assignment groups, prerequisites, `never_drop`, macros) target source IDs, not current display labels.
- A title-only rename should not change references.
- For a legacy resource whose implicit identity was its title, introduce an explicit ID equal to that previously deployed title without renaming; deploy that migration separately before changing display text. Current parsers require explicit IDs where documented.
- Changing an item's `content_id` changes its derived identity. Preserve its former value as explicit item ID if that item must remain the same resource.
- Moving/renaming files can change asset identity or discovery results. Verify the whole graph, not just edited text.

## Source formats, templates, and args

Load the [Jinja Operational Reference](jinja-templating-reference.md) when editing templates or args: it covers helper signatures, path contexts, MarkdownData schemas, merged globals, loops, and multiline Markdown.

Static `.canvas.md.xml` and templated `.canvas.md.xml.jinja` sources may coexist. Do not template a one-off resource merely for consistency. Markdown files can be consumed by includes/generated pages; final `.jinja` is what enables template rendering.

Args support JSON, CSV, YAML, MarkdownData, and Jinja-rendered variants. The included template receives the loaded object as `args`. Inspect actual keys, capitalization, types, nesting, heading structure, indentation, and table columns before editing: these may be data contracts, not presentation.

Jinja file helpers operate relative to the template being rendered. Include/args paths operate in the containing source context; paths stored inside args are interpreted by the consumer. Available Jinja utilities include `zip`, `enumerate`, `split_list`, `exists`, `read_file`, `glob`, `parent`, `load`, `get_arg`, `search`, and `debug`. Inspect existing consumers rather than inventing new schemas or assuming similarly named keys are interchangeable.

Use [Course-info and Global-args Principles](course-info-and-args-principles.md) for ownership of curriculum versus offering/target data. Keep credentials outside authored content. Dates and section data should use their established authoritative args; during a date change search attributes, subheaders, announcements, and prose for duplicated values. Timezone and target assumptions must be verified, not inferred from a displayed date.

## Choosing a representation

Use pages for reference material; assignments for approved submission/grade workflows; quizzes for collected responses; modules for navigation; announcements for approved time-sensitive communication; syllabus for the course syllabus body. Files, internal links, diagrams, and archives support these resources without duplicating content. Selection must preserve the instructor's intent; do not convert question types or infer answer material to fit a convenient encoding.

For compound quizzes, consult representation principles and then the authoritative tag skills. Distinguish a resource from its module item and check both sides of every reference. Navigation is course-wide and should not be changed as an incidental content edit.

## Publication and visibility controls

Deployment and publication are separate stages. As the normal authoring convention, omit `published` unless persistent synchronization of publication state was explicitly approved. A request to prepare or deploy content is not permission to make it visible. New resources normally require target review and a separate publication operation owned by the Deployment Engineer/instructor.

Omission does not unpublish an existing resource or guarantee invisibility; updates generally preserve existing state. Preserve existing explicit controls unless changing them is authorized. Removing an explicit value may preserve the current Canvas state instead of reversing it.

Dates, availability, page scheduling, announcement scheduling, file locks, overrides, and publication are distinct controls. Parent modules, module items, and target resources have independent state. Trace inherited visibility through shared templates and conditions. Call out affected controls and existing-state uncertainty at handoff; do not add `published="true"` to save the operator a step.

## Reusable authoring patterns

### Discovery-driven bundles

Trace directory globs, ordering, filtering, and path-to-ID transformations before adding or moving files. A filename or directory can be an API to a template. Confirm every newly discovered resource's ID and reachability, including unintended matches.

### Shared catalogs driven by tables

Treat row keys and columns as a schema. Keep immutable source IDs separate from mutable titles. Check all consumers before changing a column name/type or introducing a new row. Preserve order only where it intentionally controls display, not identity.

### Rich MarkdownData records

Inspect parsed structure before editing heading levels, indentation, frontmatter, or nested sections. Records may combine prose, question data, rubric tables, and assignment sections. Update the authoritative record rather than copied rendered prose.

### Parsed human-facing instructions

Headings, prefixes, checkboxes, and indentation may be consumed by custom parsers. Locate those parsers and verify the structured result; a document that looks right can still break generation.

### Conditional and audience-sensitive resources

Render relevant branches and audiences, including empty collections. A conditional omission removes a resource from the graph and may trigger cleanup during deployment. Preserve identity if it returns. Validate dangling references and resource/item visibility separately.

### Shared helpers and assets

Use the helper reference instead of copying helper contracts here. Check path context, source availability, basename/name collisions, archive contents, and specialized renderer dependencies. An overlay of starter files is not proof that solutions were excluded. Keep Quarto/Mermaid sources, not generated output, as authoring inputs.

## Common hazards

- Editing an unused entry point or generated output.
- Changing a shared template without tracing every consumer.
- Using mutable prose or loop indices as durable IDs.
- Changing IDs as part of a title rename or silently replacing explicit item IDs with derived ones.
- Treating ignored attributes, successful parsing, or a clean CLI exit as proof of Canvas behavior.
- Assuming omitted defaults reset existing Canvas values.
- Leaking answers, instructor notes, keys, tokens, or unmatched solution files through includes/downloads.
- Treating an offline source check as deployment, publication, or live-state verification.

## Validation and handoff checklist

### Reachability and rendering

Confirm the active entry point, include paths, args schemas, discovery matches, conditional branches, and intended Markdown/Jinja processing. Render representative generated content. Check XML-sensitive characters, balanced elements, tables, math, code, links, image alt text, and direct-child constraints.

### Identity and graph integrity

Compare pre/post `(type, id)` inventories. Check uniqueness, unchanged identity through renames, valid references, module item reachability, and potential cleanup caused by omissions. Keep stable literal data keys in generated examples.

### Resource semantics

Validate against the relevant tag reference, not a duplicated role table. Quiz work also follows the representation checks in the quiz principles. Confirm instructor-approved answers, points, tolerances, dates, attempts, access, overrides, and feedback; do not silently resolve substantive ambiguity.

### Assets and sensitive content

Verify local file existence and path context, complete archive maps, naming collisions, approved external tool/URL configuration, renderer inputs, and absence of secrets or instructor-only content in student-facing output.

### Handoff contract

Report changed files and authoritative sources, affected IDs and references, local validation commands/results, known limitations, inherited/explicit visibility controls, target-state checks still required, and any cleanup implications. Distinguish source-ready from deployed and published. Hand operational work to the Deployment Engineer without implying authorization for extra mutation.
