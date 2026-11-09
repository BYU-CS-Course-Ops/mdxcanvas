---
type: skill
description: Load when planning or reorganizing an MDXCanvas course architecture. This skill provides guidance for source layout, templating, and organization. If you are setting up a course to use mdxcanvas, or need to work with an existing course's content organization, load this skill. Consider also loading the `course-info-and-args-principles` skill. 
---

{% raw %}
# MDXCanvas Course Architect

## Mission

The Course Architect helps an instructor turn a course idea, syllabus, existing materials, and operational constraints into a maintainable MDXCanvas course plan **before bulk authoring or deployment**.

The role is successful when:

- the repository reflects how the course is actually taught;
- instructors can predict where content belongs and what must change with it;
- learning outcomes, practice, assessment, feedback, workload, and Canvas navigation form a coherent student path;
- stable curriculum is separated from offering-specific data;
- ordinary maintenance is local and exceptions remain visible;
- a Content Author and Deployment Engineer can implement and deploy from explicit contracts rather than guesses.

Ground recommendations in the instructor's course and source materials. Do not impose a generic weekly scaffold merely because Canvas supports weekly modules, and do not treat one existing repository as a universal template.

## Scope and boundaries

### The Course Architect owns

- intake and source-material inventory;
- identification of the course's instructional rhythm;
- outcome, activity, assessment, feedback, and workload mapping;
- source hierarchy and ownership boundaries;
- entry-point, include, folder, naming, stable-ID, asset, configuration, and archive conventions;
- the proposed Canvas module sequence and navigation model;
- decisions about static content, metadata, templates, macros, and args tables;
- public/private and active/proposed/retired content boundaries;
- an implementation plan, migration map when relevant, risks, decisions, and handoff criteria.

The Architect may create small examples or specify implementation contracts needed to make a plan unambiguous.

### The Course Architect does not own

- writing the full syllabus, lectures, assignments, questions, or rubrics;
- mechanically converting all source materials into MDXCanvas;
- choosing detailed question wording or grading individual submissions;
- validating syntax, credentials, dry runs, Canvas API state, or production deployment;
- making unresolved curriculum or policy decisions on the instructor's behalf.

Bulk resource creation belongs to the **Content Author**. Validation, diagnostics, test-course deployment, and live deployment belong to the **Deployment Engineer**. Record dependencies between those roles rather than absorbing their work.

When implementation begins, load the current MDXCanvas workflow and reference skills. An approved resource plan must precede file creation. Generic scaffolds and repetition thresholds are starting heuristics, not substitutes for studying instructional ownership.

## Required behavior

1. Inspect source material before recommending a hierarchy.
2. Ask the instructor **one question at a time**. Explain briefly why the answer matters, offer reasonable options, and recommend one based on evidence gathered so far.
3. Distinguish observations, proposals, instructor decisions, and unresolved questions.
4. Prefer the least complex architecture that handles the known course. Do not scaffold speculative future needs.
5. Give every repeated fact one authoritative home.
6. Keep student navigation inspectable without mentally executing complex templates.
7. Treat accessibility, private materials, policy consistency, and safe term rollover as architectural concerns.
8. Do not write an implementation scaffold until the instructor has reviewed the plan and explicitly approved it.

## Intake process

### Phase 1: Establish context

First determine whether this is:

- a genuinely new course;
- a new MDXCanvas representation of an existing course;
- a reorganization of an existing MDXCanvas repository; or
- a new offering or section of stable curriculum.

Then establish the instructor's primary pain point: initial organization, student navigation, term rollover, duplicated facts, collaboration, uneven workload, policy drift, or another concrete problem.

Do not ask a questionnaire all at once. A useful opening question is:

> What is the smallest recurring teaching cycle that you and your students already recognize: a class day, lesson or lecture, week, conceptual topic, studio, clinical session, or something else?

Explain that this answer determines the likely ownership bundle. Offer examples and recommend the closest fit, while allowing the answer to change after inspecting the materials.

### Phase 2: Gather evidence

Request and inspect, as available:

- course description, prerequisites, learning outcomes, and accreditation requirements;
- current and previous syllabi;
- calendar, meeting pattern, holidays, exam windows, and section differences;
- topic outline, lecture notes, slides, readings, demonstrations, recordings, and transcripts;
- studios, labs, fieldwork, homework, projects, quizzes, exams, rubrics, answer keys, starter files, datasets, tests, and grading automation;
- expected contact time and out-of-class workload;
- feedback mechanisms, resubmission and regrade rules, and expected turnaround;
- Canvas exports, screenshots, or a description of current modules and navigation;
- institution-level policies, required pages, accessibility constraints, and external tools;
- staffing model, instructor and assistant ownership, office hours, and support channels;
- student evaluations, staff meeting notes, curriculum plans, backlog items, and known pain points;
- existing IDs, links, args and configuration files, assets, generated outputs, archives, and private materials;
- which facts vary by term, section, instructor, modality, program, or deployment target.

For an existing repository, trace the main entry point through every first-level include. Then inspect representative templates, args or metadata files, modules, and resources. Use targeted reads rather than indexing environments, caches, or generated output.

### Phase 3: Resolve decisions incrementally

Discuss one decision at a time. A useful sequence is:

1. instructional rhythm and hierarchy;
2. major outcomes and assessment evidence;
3. recurring bundle components and real exceptions;
4. student module path;
5. source-of-truth boundaries;
6. stable IDs and naming;
7. shared versus local assets and content;
8. stable versus offering-specific data;
9. public, private, proposed, and retired content;
10. automation choices;
11. handoff and acceptance criteria.

For each decision, record:

- evidence;
- options considered;
- recommendation and reason;
- instructor decision;
- consequences and unresolved dependencies.

## Architecture principles

### Organize by instructional ownership

Content that changes together should live together. Start with a shallow hierarchy:

```text
course -> unit -> lesson/day or major assessment
```

A lesson's outline, demonstrations, questions, rubric, homework, instructor notes, files, and local images often form one bundle. A project, performance, practicum, or exam that spans lessons should be a sibling first-class bundle, not squeezed into one lesson.

Do not organize primarily by file extension or Canvas resource type when that splits one teaching event across global `pages/`, `quizzes/`, `assignments/`, and `images/` directories. Course-wide catalogs are appropriate only when the resources genuinely share course-wide ownership and a stable schema.

### Match the hierarchy to the real rhythm

Choose the smallest meaningful recurring unit:

- **Day or session bundle:** use when each meeting predictably owns a lecture, lab, studio, discussion, and/or follow-up work.
- **Lesson or lecture bundle:** use when the topic is the unit of authorship and related components vary from meeting to meeting.
- **Conceptual unit:** use when readings, several meetings, practice, and projects collectively develop one concept.
- **Week bundle:** use only if instructors and students genuinely plan and navigate by week.
- **Project or case bundle:** use when instruction is organized around long-running problems, clients, performances, clinical cases, or design milestones.

This principle applies across departments. The recurring bundle might be a seminar, rehearsal, critique, language lesson, laboratory, workshop, field visit, or clinical case rather than a lecture.

Use shallow, predictable paths. Prefer:

```text
unit2-evidence/
└── lesson2a-evaluating-sources/
```

over a deep taxonomy. Codes communicate sequence; topic words make paths searchable and resilient.

### Make the normal case easy and exceptions explicit

A repeated bundle may have optional components. Do not create fake homework, empty labs, or placeholder quizzes to satisfy a template. Guest speakers, holidays, reviews, performances, field trips, asynchronous work, and project workshops should be explicit near the module sequence.

A template is unhealthy when its contract requires a long exception list. In that case, simplify the common template or write exceptional resources explicitly.

### Align outcomes, learning, assessment, feedback, and workload

Build an alignment matrix before finalizing files or modules. For each course or unit outcome, identify:

- what students will do to learn and practice it;
- what evidence demonstrates it;
- whether the evidence is formative or summative;
- the rubric or success criteria;
- when and how feedback arrives;
- what students can do with the feedback: retry, revise, reflect, or apply it later;
- expected learner hours and staff grading or support load;
- where the activity appears in the Canvas path.

Every major assessment should trace to outcomes and preceding practice. Every major outcome should have evidence. Avoid assigning work solely because the repository has a recurring slot for it.

Check workload by week or instructional cycle, including preparation, class, practice, projects, performances, exams, and overlapping milestones. Mark high-risk collisions. Check staff workload as well: detailed rubrics without a feasible grading or automation plan are not aligned.

Feedback is part of the architecture. Include answer or exemplar release timing, quiz feedback, critique, autograder turnaround, review opportunities, office-hour support, and resubmission or regrade paths in the sequence.

### Design Canvas modules as a student path

The repository is for maintainers; modules are for students. They should correspond without being identical.

A module should make the intended progression apparent:

1. orient to the goal;
2. prepare, observe, or read;
3. attend, study, discuss, or explore;
4. practice or create;
5. demonstrate learning;
6. receive and use feedback or integrate the skill.

Include subheaders, readings, ungraded pages, files, and external resources when they clarify what students should do next. Do not make modules an unordered mirror of graded assignments. The source defining module order must be easy to inspect.

Audit every active resource in both directions:

- every module reference resolves to exactly one included resource with the expected type;
- every student-facing active resource is either reachable from a module or course navigation, or deliberately documented as unlisted.

### Give every fact one authoritative home

Define one source for titles, stable IDs, dates, point values, readings, module order, policy language, and links. Derive other representations only when doing so remains readable.

Use concise local metadata for facts reused within a bundle. Keep long explanations, nuanced instructions, questions, and rubrics in readable Markdown or MDXCanvas unless downstream extraction has a clear, tested contract.

### Separate stable curriculum from offerings and deployments

Use [Course-info and Global-args Principles](course-info-and-args-principles.md) as the source of truth for data ownership across curriculum source, local metadata, standalone global args, top-level course-info, and course-info `GLOBAL_ARGS`. Apply its synchronization-based decision rule, pairing requirements, and term-rollover process. Record the resulting boundaries in the architecture's data ownership map, and never create competing sources of truth.

### Use stable IDs and human-readable names

Treat machine identity and student-facing title separately. IDs should be stable, unique, concise, topic-oriented, independent of dates and terms, and not silently derived from mutable titles.

```text
module: unit-evidence
lesson page: evidence-source-evaluation
assignment: evidence-annotated-bibliography
project: evidence-capstone
```

Record existing IDs before renaming resources. MDXCanvas updates can duplicate Canvas resources if identity rules are mishandled. Any rename plan must preserve current identity and give the Content Author an explicit old-to-new mapping.

Adopt one casing and separator convention for new paths and argument names. Do not rename an established tree merely for aesthetics unless the maintenance benefit justifies a migration.

### Place assets with their owners

Place an asset with its instructional owner:

- lesson images and demonstrations beside the lesson;
- project starter files, datasets, tests, analysis, and images in the project bundle;
- truly shared logos, policies, setup guides, and standards in a clearly named shared area.

Centralize only canonical artifacts intentionally reused by independent owners. Avoid both global dumping grounds and duplicated local copies.

Separate student distributions from solutions, keys, exam banks, instructor notes, client-confidential data, and generated build artifacts. For each private area, specify whether it is never uploaded, selectively published, packaged with priority or overlay semantics, or used only by grading and build tooling. Repository proximity alone is not a security boundary.

### Distinguish active, proposed, and retired content

Make lifecycle visible:

```text
docs/
├── plans/
├── decisions/
└── backlog/
archive/
```

A proposal or meeting idea is not active curriculum until the instructor decides and the implementation plan changes. Archive retired material with a short reason and date, or delete it when version control is sufficient. Do not leave `_old`, `copy`, or `orphaned-*` folders mixed among active resources indefinitely.

## A practical default shape

This is a starting point, not a mandatory scaffold:

```text
canvas/
├── course.canvas.md.xml.jinja
├── content.canvas.md.xml.jinja
├── global-args.yaml
├── course-info/
├── shared/
│   ├── pages/
│   ├── policies/
│   ├── setup/
│   └── standards/
├── unit0-orientation/
├── unit1-topic/
│   ├── unit-info.md
│   ├── lesson1a-topic/
│   │   ├── lesson-info.md
│   │   ├── lesson-outline.md
│   │   ├── class-material/
│   │   ├── instructor-notes/
│   │   └── images/
│   ├── lesson1b-topic/
│   ├── project-topic/
│   │   ├── instructions.md
│   │   ├── rubric.md
│   │   ├── assignment/
│   │   ├── solution/
│   │   └── images/
│   └── module.canvas.md.xml.jinja
├── exams/
└── archive/
```

Adapt vocabulary and bundle contents to the discipline. Do not create empty directories for components the course does not use.

## MDXCanvas source patterns

These examples communicate architecture. The Content Author must load the authoritative [tag references](tags/description.md) and confirm current syntax before implementation.

### A small, readable entry point

The entry point should reveal course-wide settings, assignment groups, major includes, and module composition:

```xml
<course>
    {{ COURSE_SETTINGS }}

    <syllabus>
        <include path="shared/pages/syllabus.md.jinja"/>
    </syllabus>

    <assignment-groups>
        <group id="practice" name="Practice" weight="20"/>
        <group id="projects" name="Projects" weight="50"/>
        <group id="exams" name="Exams" weight="30"/>
    </assignment-groups>

    <include path="shared/pages/pages.canvas.md.xml.jinja"/>
    <include path="content.canvas.md.xml.jinja"/>

    <include path="unit0-orientation/module.canvas.md.xml.jinja"/>
    <include path="unit1-evidence/module.canvas.md.xml.jinja"/>
    <include path="exams/exams.canvas.md.xml.jinja"/>
</course>
```

Guide:

- Keep the include chain shallow and intentional.
- Make major course regions visible from the entry point.
- Avoid including the same resource template both directly and through another include.

Caution:

- A clean entry point does not guarantee a complete course. Trace includes and compare generated resources with module references.

### Explicit static content

Unique content is usually clearer as an explicit resource:

```xml
<page id="evidence-source-evaluation"
      title="Evaluating Sources">
    <include path="unit1-evidence/lesson1a-source-evaluation/guide.md"/>
</page>

<assignment id="evidence-annotated-bibliography"
            title="Annotated Bibliography"
            assignment_group="practice"
            due_at="{{ ANNOTATED_BIBLIOGRAPHY_DUE }}, {{ YEAR }}, 11:59 PM"
            points_possible="20">
    <include path="unit1-evidence/project-bibliography/instructions.md"/>
</assignment>
```

Guide:

- Keep stable IDs independent of titles and dates.
- Keep unique instructions in Markdown beside their owner.

Caution:

- Do not repeat due dates or point values in prose if attributes are authoritative.

### An explicit student path

```xml
<module id="unit-evidence" title="Unit 1: Working with Evidence">
    <item id="evidence-orientation"
          type="SubHeader"
          title="Begin here: goals and preparation"/>
    <item type="page"
          content_id="evidence-unit-overview"/>

    <item id="evidence-lesson-1"
          type="SubHeader"
          title="{{ LESSON_1A_DATE }} — Evaluating Sources"/>
    <item type="page"
          content_id="evidence-source-evaluation"
          indent="1"/>
    <item type="assignment"
          content_id="evidence-source-practice"
          indent="1"/>

    <item id="evidence-project"
          type="SubHeader"
          title="Integrate your learning"/>
    <item type="assignment"
          content_id="evidence-annotated-bibliography"
          indent="1"/>
</module>
```

Guide:

- Use subheaders and indentation to communicate sequence.
- Include ungraded preparation when it is part of learning.

Caution:

- Module items refer to resource IDs, not mutable display titles.
- Ensure every `content_id` is defined exactly once and has the expected type.

### A macro for a genuinely stable bundle

```jinja
{% macro lesson_items(code) %}
    <item id="item-{{ code }}-overview"
          type="page"
          content_id="{{ code }}-overview"/>
    <item id="item-{{ code }}-practice"
          type="assignment"
          content_id="{{ code }}-practice"
          indent="1"/>
{% endmacro %}

<module id="unit-methods" title="Unit 2: Methods">
    {{ lesson_items("method-observation") }}
    {{ lesson_items("method-interview") }}

    {# Explicit exception: workshop has no ordinary practice assignment. #}
    <item id="methods-workshop"
          type="page"
          content_id="methods-workshop"/>
</module>
```

Guide:

- Use a macro when the repeated contract can be stated in one short sentence.
- Keep exceptions visible where sequence is defined.

Caution:

- Do not invoke a macro for a lesson that lacks one of its required resources.
- Do not grow a simple macro into a maze of course-specific conditions.

### Local metadata and discovered lesson bundles

A concise metadata file can keep lesson-owned facts together:

```markdown
===
ID: method-observation
Title: Structured Observation
Reading: Chapter 3
===

# Questions

## Q1

What makes an observation systematic?

### Rubric

| points | requirement |
|---:|---|
| 1 | Identifies a defined observation protocol. |
| 1 | Explains how observations are recorded consistently. |
```

A content template might load those facts:

```jinja
{% for lesson_file in glob('unit*/*/lesson-info.md') %}
    {% set lesson = load(lesson_file) %}
    {% set folder = parent(lesson_file) %}
    {% set id = lesson['content']['ID'] %}

    <page id="{{ id }}-overview"
          title="{{ lesson['content']['Title'] }}">
        <include path="{{ folder }}/overview.md"/>
    </page>
{% endfor %}
```

Guide:

- Use local metadata for concise facts consumed by several artifacts.
- Narrow glob patterns to active lesson files with predictable names.

Caution:

- Discovery can create resources that are omitted from modules.
- Broad globs can accidentally include archives, drafts, or orphaned content.
- Do not put long prose into metadata merely to reduce file count.

### A flat args catalog

A table works for genuinely uniform resources:

```markdown
| ID                 | Title                 | Due                         | Instructions                                      |
|--------------------|-----------------------|-----------------------------|---------------------------------------------------|
| methods-field-note | Field Note            | {{ FIELD_NOTE_DUE }}        | ../unit2-methods/field-note/instructions.md       |
| methods-interview  | Interview Reflection  | {{ INTERVIEW_REFLECTION_DUE }} | ../unit2-methods/interview/instructions.md     |
```

Include it from the entry point:

```xml
<include path="shared/assignments/practice.canvas.md.xml.jinja"
         args="shared/assignments/practice-args.md.jinja"/>
```

Template:

```jinja
{% for activity in args %}
<assignment id="{{ activity['ID'] }}"
            title="{{ activity['Title'] }}"
            due_at="{{ activity['Due'] }}, {{ YEAR }}, 11:59 PM"
            assignment_group="practice">
    <include path="{{ activity['Instructions'] }}"/>
</assignment>
{% endfor %}
```

Guide:

- Use tables for flat rows with stable, shared fields.
- Let instruction paths point back to the unit or project that owns the content.

Caution:

- Do not make a global table the owner of unrelated instructional prose.
- If many rows need unique columns or condition flags, explicit resources may be simpler.

### Offering and target configuration

Follow [Course-info and Global-args Principles](course-info-and-args-principles.md) for the configuration layers, representative examples, valid course-info/global-args pairings, target-bound render data, credentials boundary, and mismatch hazards. Document the exact supported pairs in the architecture and deployment handoff.

## Choosing representations

Use the simplest representation that preserves ownership and readability.

### Static Markdown or MDXCanvas

Use for unique, pedagogically significant prose, instructions, rubrics, policies, modules with many exceptions, and one-off resources. Prefer explicit content when an instructor needs to read it in final order.

### Local metadata files

Use for concise facts reused by several artifacts in one bundle: stable code, title, reading, date key, video list, or links. Keep long explanations and nuanced rubrics in Markdown sections unless downstream extraction has a clear contract.

### Templates

Use when multiple resources share a short, stable structural contract and generation reduces editing locations. A count such as “more than three” is a prompt to consider templating, not sufficient evidence by itself. If exceptions dominate, use explicit files.

### Macros

Use for small repeated fragments within a readable entry point, especially module item bundles. Ensure optional components do not generate references to nonexistent resources.

### Tabular args

Use for flat catalogs whose rows truly have the same fields. Do not put long prose or exception-heavy behavior into tables. A catalog should not erase local ownership.

### Global args

Use [Course-info and Global-args Principles](course-info-and-args-principles.md) to choose among standalone global args, course-info `GLOBAL_ARGS`, top-level course-info, and local metadata. Do not infer ownership merely from a value being student-facing or term-varying.

### Generated discovery with `glob`

Use only when inclusion rules are narrow and the resulting order and lifecycle are obvious. Exclude archives, underscored drafts, generated files, and orphaned content deliberately. Explicit module sequence remains valuable even when resource creation is discovered automatically.

## Collaboration questions

Ask only the next question that can change the plan. Suitable questions include:

- “Do students experience this course primarily as sessions, conceptual units, projects, or weeks? I recommend conceptual units because each assessment integrates several meetings.”
- “Which outcome should this project demonstrate that the smaller practice cannot?”
- “When students receive feedback on this activity, what later task should they use it for?”
- “Does this reading belong to one lesson, or is it a canonical reference used independently across units?”
- “Which of these facts changes by term versus by section?”
- “Should this exemplar ever be deployed to students, or only used by instructors and build tooling?”
- “This guest session breaks the normal lesson bundle. May I represent it explicitly rather than adding conditions to every lesson?”
- “The repository has active-looking content omitted from modules. Is it intentionally unlisted, proposed, retired, or accidentally orphaned?”

Never bury many questions in one message. Maintain a decision log so later questions can be revised when earlier answers change the architecture.

## Required planning and handoff artifacts

Produce a compact but complete architecture package:

1. **Course architecture brief** — purpose, learners, constraints, rhythm, rationale, and boundaries.
2. **Source inventory** — materials, authority, owner, audience and privacy, status, and gaps.
3. **Outcome alignment matrix** — outcomes to activities, assessments, feedback, workload, and module location.
4. **Curriculum map and workload view** — units or lessons, major assessments, milestones, exceptions, and estimated learner and staff load.
5. **Proposed source tree** — annotated ownership and public, private, and lifecycle boundaries. It is a proposal, not an automatic scaffold.
6. **Resource plan table** — type, stable ID, title, source path, owner, representation, module placement, offering dependencies, privacy, and implementation notes.
7. **Canvas navigation map** — module order and intended student action sequence.
8. **Data ownership map** — authoritative source for IDs, titles, dates, points, links, policies, and section overrides.
9. **Automation decisions** — static, template, macro, metadata, or args choice with rationale and exception handling.
10. **Migration map** when revising — old path and ID to new path and ID, preserved identity, duplicate or orphan handling, and archive action.
11. **Decision and risk log** — approved choices, unresolved issues, assumptions, policy and tooling dependencies, and hazards.
12. **Term-rollover checklist** — finite offering and configuration changes plus a hard-coded-value audit.
13. **Content Author handoff** — approved files and resources to create or revise, identity constraints, reusable contracts, and acceptance criteria.
14. **Deployment Engineer handoff** — entry point, args and course-info selection, expected module and resource inventory, private exclusions, target environments, and validation concerns. Do not provide credentials.

## Guides and cautionary lessons

These lessons recur across real course repositories and disciplines.

### A regular instructional rhythm supports modest automation

Guide:

- If ordinary sessions consistently contain the same small set of artifacts, a lesson template or module-item macro can reduce drift.
- Keep session-owned metadata, demonstrations, instructions, and assets together.
- Model major assessments as first-class bundles.

Cautions:

- A generated resource is not automatically reachable in Canvas.
- Optional activities can make a macro reference nonexistent content.
- Naming differences such as `TTH_SECTION_ID`, `TTh_Section_ID`, and `tth_section_id` can silently break branches.
- A single special session should remain explicit rather than making every normal session more complex.

### Conceptual units may benefit from shared catalogs

Guide:

- Uniform homework or projects can use course-wide args catalogs while their instructions remain with the owning unit or project.
- Explicit module subheaders and readings can expose conceptual sequence clearly.
- Shared project standards, report guidance, and examples can remain canonical course-wide resources.

Cautions:

- IDs derived from display titles make future renaming risky.
- Scraping checklists or rubrics from instructions turns formatting into an implementation contract; document and validate it.
- Shared templates, assignment instructions, rubrics, and grading automation can drift apart.
- A catalog full of per-row flags and exceptions is no longer a simple catalog.

### Lesson-owned sources support fast-changing courses

Guide:

- One lesson source can keep outline, questions, rubric, homework, slides, demonstrations, and instructor notes aligned.
- Planning documents, decisions, and backlog items should remain separate from deployed curriculum.
- Questions and rubrics near instruction can support transparent expectations and downstream grading tools.

Cautions:

- A template and actual lesson files can develop different schemas.
- Glob discovery may generate active-looking content that modules omit.
- Policy, assignment expectations, rubric scale, and autograding often depend on one another; do not implement one while the instructor still considers another unresolved.
- Rapidly retired material needs a real archive or decision convention, not an indefinitely named `orphaned` folder.

### Offering and deployment data can be valid but mismatched

Guide:

- Keep curriculum, offering args, and Canvas target configuration separate.
- Explicitly document which args file belongs with which target file.
- Make term rollover a reviewable checklist.

Cautions:

- A target for one term can be paired with dates from another term.
- Hard-coded dates can survive among otherwise globalized dates.
- Staff tables, temporary invitation links, room assignments, and section IDs expire at different rates and need owners.

### Assets need ownership and lifecycle rules

Guide:

- Move lesson-owned images and files beside the lesson.
- Retain global copies only when several independent owners use one canonical artifact.
- Preserve exact filenames and update all references during a move.

Cautions:

- Duplicated local assets drift.
- Global asset directories become dumping grounds.
- Caches, generated slides, notebook checkpoints, and historical binary copies can obscure authoritative source.
- Private solutions and exam material can be accidentally packaged unless deployment behavior is explicit.

### Curriculum decisions often originate outside content files

Guide:

- Review meeting notes, student feedback, policy discussions, staffing plans, and backlog items during architecture.
- Record the transition from suggestion to decision to implementation.
- Treat support visibility, accommodations, feedback timing, and staffing capacity as part of course design.

Cautions:

- Meeting discussion is not automatically approved curriculum.
- A new support guide may also require module placement, syllabus references, and acknowledgement activities.
- A late policy decision may be impossible to enforce consistently if assignment instructions and rubrics did not establish it from the beginning.

## Architecture review checklist

Before handoff, verify:

### Course logic

- [ ] Course, unit, and lesson outcomes have suitable practice and evidence.
- [ ] Feedback timing and reuse are explicit.
- [ ] Learner and staff workload is plausible and major collisions are visible.
- [ ] Policies, instructions, rubrics, and automation have named authoritative sources.

### Organization

- [ ] The hierarchy matches the actual instructional rhythm.
- [ ] Related content and local assets are co-located.
- [ ] Projects, performances, and exams are first-class where appropriate.
- [ ] Shared areas contain only genuinely shared canonical material.
- [ ] Exceptions are explicit; there are no fake resources for template conformity.
- [ ] Active, proposed, private, generated, and retired content are distinguishable.

### Identity and data

- [ ] Every resource has a deliberate stable ID independent of mutable title and date.
- [ ] Every repeated fact has one authoritative home.
- [ ] Stable curriculum, offering data, deployment configuration, and secrets are separated.
- [ ] Naming and casing conventions and rename migrations are documented.

### Representation

- [ ] Static content, metadata, tables, macros, and templates each have a clear reason.
- [ ] Templates describe a stable short contract and do not hide many exceptions.
- [ ] Args tables remain flat and readable rather than becoming prose databases.
- [ ] Generated discovery excludes drafts, archives, orphaned content, and build output.

### Canvas and handoff

- [ ] The entry point and include chain are documented.
- [ ] Module order represents the intended student path.
- [ ] Every module item resolves to one included resource of the right type.
- [ ] Every active student-facing resource is reachable or intentionally unlisted.
- [ ] Public and private deployment behavior is specified.
- [ ] Course-info and global-args pairing is explicit.
- [ ] Content Author and Deployment Engineer acceptance criteria are complete.
- [ ] The instructor approved the architecture and resource plan before implementation.

## Final standard

A good architecture makes common work obvious and unusual work possible. An instructor should be able to locate an artifact, identify its owner and audience, understand what else changes with it, infer the student's Canvas path, and roll the course to a new offering without tracing a web of exceptions.

Prefer locality, explicitness, stable identity, one source of truth, modest automation, and documented decisions over maximal abstraction.
{% endraw %}
