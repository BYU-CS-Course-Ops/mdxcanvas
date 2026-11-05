# MDXCanvas Myteam Skill Content-Gap Plan

## Goal

Make `mdxcanvas/skills/` the complete, current, distributable Myteam skill source, then retire `.myteam/mdxcanvas-roster/` without preserving obsolete loader machinery or stale guidance.

This is a content migration, not a file-for-file migration. Behavior must be reconciled against the MDXCanvas version being documented. For this change, current runtime source and tests are authoritative for implemented behavior; packaged skills express policy; `documents/` and `.myteam/` are evidence that must be checked rather than assumed correct.

## Current-state finding

The five packaged skills already absorb most substantive material from the 24 legacy `skill.md` files:

- `content-author-role.md`: resource tags, helper tags, identity, dates, includes, args, and update safety.
- `quiz-design-principles.md`: quiz settings and all supported question representations.
- `course-architect-role.md`: course setup, source organization, units/days/lectures/weeks, planning, and new-course design.
- `course-info-and-args-principles.md`: ownership and pairing of course-info and global args.
- `deployment-engineer-role.md`: validation, credentials, dry runs, deployment, cleanup, erase, publication, and post-deploy review.

The remaining gaps are narrower than the old file count suggests. Most legacy tag and workflow files should not be recreated as separate skills.

## Latest Myteam format to use

`myteam explain` and `myteam new skill` show the current model:

- A skill is a Markdown file discoverable by its frontmatter.
- Use:

  ```yaml
  ---
  type: skill
  description: Load when ...
  ---
  ```

- Descriptions must state when the agent should load the skill.
- A skill folder uses `description.md` to tell an agent when to list that folder.
- Do not create or preserve `load.py`.
- Do not copy legacy `name:` or `skill:` frontmatter.
- Do not recreate `info.md`; use `description.md` only where a folder needs routing context.
- Keep relative Markdown links valid after packaging.

## Required pre-migration audit

Complete the audit before finalizing the additions below or changing any skill. For every heading or coherent subsection in each legacy `skill.md`, record:

| Legacy file and section | Current destination and section | Runtime/test evidence | Disposition | Required change |
|---|---|---|---|---|
| Exact path and heading | Exact packaged path and heading, or `none` | Parser/deployer/test path when the claim describes behavior | `covered`, `copy`, `modify`, or `reject` | Concrete edit or reason for no edit |

Also audit all five packaged skills rather than treating them as correct merely because they are newer. In particular:

- Compare every XML example with current required parser attributes. Every resource, question, and module item example must either include its required stable `id` or explicitly explain a real runtime-derived exception.
- Fix the known `<item>` examples in `course-architect-role.md` that omit IDs; `module_tags.py` currently requires IDs.
- Reconcile assignment-group references with `assignment_tags.py`, `quiz_tags.py`, and `group_tags.py`; older `documents/` still describe display-name lookup while current runtime resolves stable resource IDs.
- Reconcile announcement requirements with `announcement_tags.py`; older documentation says `publish_date` is optional while current runtime marks it required.
- Verify accepted dates, resource attributes, item types, args precedence, and helper behavior against source and focused tests.
- Distinguish implementation facts from authoring policy. For example, an attribute may be parser-optional while packaged policy deliberately requires authors to set it.

The migration structure remains provisional until this matrix confirms that no additional independently loadable topic is needed.

## Recommended organization

Keep the existing five skills at their current paths to avoid breaking their public names. Provisionally add only:

```text
mdxcanvas/skills/
├── content-author-role.md
├── course-architect-role.md
├── course-info-and-args-principles.md
├── deployment-engineer-role.md
├── jinja-templating-reference.md       # new, subject to audit
└── quiz-design-principles.md
```

The root skill directory does **not** need `description.md` because callers list that directory directly. Do **not** introduce a nested skill folder unless the pre-migration matrix identifies multiple independently loadable references that justify another listing step. If such a folder is created, only that nested folder gets a `description.md`.

Do **not** create managed Myteam workflows from the three legacy files named “workflow.” They are procedural guidance, not orchestration definitions, and their current equivalents already live in the role skills.

## Specific gap inventory and migration action

These are candidate gaps established by the initial comparison. Confirm them through the pre-migration matrix before editing.

### 1. Jinja and template-args operational reference

**Legacy source:** `.myteam/mdxcanvas-roster/reference/jinja/skill.md`

**Gap:** `content-author-role.md` names the available helpers and args formats, but omits several operational details that are easy to get wrong:

- `search()` returns a regex match object; capture text requires `.group(0)` or `.group(n)` and an unmatched search must be handled.
- Jinja string concatenation uses `~`.
- `loop.index`, `loop.index0`, `loop.first`, and `loop.last` behavior.
- `indent(width, first=False, blank=False)` usage, especially `blank=True` for multiline Markdown.
- Concrete iteration patterns for MarkdownData tables (`list[dict]`) and keyed MarkdownData (`dict` with `content` plus heading sections).
- Concrete `load()`, `glob()`, `exists()`, and conditional examples with path-relative behavior.
- A compact function signature table for `zip`, `enumerate`, `split_list`, `exists`, `read_file`, `glob`, `parent`, `load`, `get_arg`, `search`, and `debug`.
- The distinction between top-level merged global arguments and the `args` object supplied by `--args` or `<include args="...">`.

**Action:** Add `mdxcanvas/skills/jinja-templating-reference.md` as a root sibling skill. Link it from `content-author-role.md`, `course-architect-role.md`, and `course-info-and-args-principles.md` where templates or args are discussed.

**Copy:** The legacy helper table, loop-variable table, regex capture explanation, multiline-indent example, and table/keyed-data loop shapes are useful source material.

**Modify before copying:**

- Remove the mandatory “template after more than three repetitions” rule. Use the current architecture rule: template only when repetition is stable and the generated result remains inspectable.
- Correct processing/precedence wording to current behavior: course-info `GLOBAL_ARGS` are merged with `--global-args`, with the CLI file overriding collisions; per-template data is exposed as `args`.
- Explain that `search()` can return `None`; do not advise an unconditional `.group()` unless a match is guaranteed.
- Give every example resource and question an explicit stable ID; never derive durable IDs from mutable titles or current list positions.
- Preserve exact key casing in examples and explain that MarkdownData headings/table columns are data contracts.
- Use generic examples rather than the legacy weekly-prep-quiz assumptions.
- Keep deployment commands in `deployment-engineer-role.md`; include only enough invocation syntax to explain `--args`, `--global-args`, and `<include args>` semantics.

### 2. Module completion requirements

**Legacy source:** `.myteam/mdxcanvas-roster/reference/canvas-tags/module/skill.md`

**Gap:** `content-author-role.md` lists `completion_requirement` but does not document the concrete supported forms:

- `type=must_view`
- `type=must_submit`
- `type=min_score,min_score=<number>`

**Action:** Add a short table and example beside the existing module-item options in `content-author-role.md`.

**Copy:** The three completion forms.

**Modify:** Add explicit stable item IDs to every example, state which target types make sense for each requirement, and avoid implying that every module should enforce completion or prerequisites.

### 3. External-tool assignment syntax

**Legacy source:** `.myteam/mdxcanvas-roster/reference/canvas-tags/assignment/skill.md`

**Gap:** `content-author-role.md` identifies `external_tool_tag_attributes` as comma-separated `key=value` pairs but gives no concrete representation, including `new_tab=true`.

**Action:** Add one compact example beside assignment attributes in `content-author-role.md`.

**Copy:** The shape `submission_types="external_tool"` plus `external_tool_tag_attributes="url=...,new_tab=true"`.

**Modify:** Replace the institution/vendor-specific Turnitin URL with a placeholder. State that the exact launch URL and tool configuration must already be approved and verified; the Content Author must not invent it.

### 4. Timestamp default behavior

**Legacy source:** `.myteam/mdxcanvas-roster/reference/helper-tags/skill.md`

**Gap:** `content-author-role.md` explains custom Python `strftime` formatting but omits the default output format.

**Action:** Add the verified current default, `%B %d, %Y at %I:%M %p`, beside the existing `<timestamp/>` explanation.

**Copy:** The format string and representative output.

**Modify:** State that timestamps are generated at deployment time in `LOCAL_TIME_ZONE` and, as already documented by the Deployment Engineer skill, do not themselves force checksum changes.

### 5. Packaged-example consistency and cross-skill handoffs

**Legacy source:** routing statements throughout the old roster.

**Gaps:**

- `course-architect-role.md` currently says to load “the current MDXCanvas workflow and reference skills,” but no packaged skills have those names.
- Several of its concrete module-path examples omit required `<item id="...">` attributes and contradict `content-author-role.md` and current `module_tags.py`.
- The new Jinja reference will need discoverable links.

**Action:** Audit every packaged XML/Jinja example, correct required IDs and other parser contracts, and replace vague or legacy routing language with links to concrete packaged skill filenames. Ensure:

- Course Architect hands implementation to Content Author and operations to Deployment Engineer.
- Content Author links to the Jinja reference, quiz reference, configuration-ownership skill, and Deployment Engineer handoff.
- Configuration skill links to the Jinja reference for syntax and Deployment Engineer for invocation/target validation.
- Every example conforms to current runtime requirements and packaged stable-identity policy.

**Modify:** Do not copy recursive “read parent, then child” rules from the old hierarchy; direct Myteam discovery replaces them.

## Initial legacy disposition map

The pre-migration audit must expand these rows to individual sections and attach runtime/test evidence before edits begin.

| Legacy skill file or group | Initial destination | Initial disposition |
|---|---|---|
| roster root; `reference/skill.md`; `workflows/skill.md`; category routing skills | None | Reject legacy routing wrappers; direct listing and current frontmatter replace them. |
| `canvas-tags/announcement/skill.md` | `content-author-role.md` | Covered, but verify current required `id`, `title`, and `publish_date`; reject `published_at` and optional/default-now claims. |
| `canvas-tags/assignment/skill.md` | `content-author-role.md` | Covered except candidate external-tool example; verify every attribute and assignment-group ID behavior. |
| `canvas-tags/module/skill.md` | `content-author-role.md` | Covered except candidate completion-requirement forms; audit all packaged item IDs. |
| `canvas-tags/page/skill.md` | `content-author-role.md` | Covered by newer material; verify required fields and publication attributes. |
| `canvas-tags/quiz/skill.md`; `quiz/questions/skill.md` | `quiz-design-principles.md` | Covered by broader current material; verify settings, direct-child structure, feedback, and every question parser. |
| `canvas-tags/syllabus/skill.md` | `content-author-role.md`; `deployment-engineer-role.md` | Covered; retain fixed identity and deployment semantics rather than old wrapper structure. |
| `course-setup/skill.md` | `course-architect-role.md` | Covered conceptually; reject mandatory generic scaffold and verify current entry/config examples. |
| `course-setup/course_info/skill.md` | `course-info-and-args-principles.md`; `deployment-engineer-role.md` | Covered by newer material; reject uncommitted course-info and add/verify `DEPLOY_ROOT`. |
| `course-setup/global_args/skill.md` | configuration principles; candidate Jinja reference | Ownership is covered; syntax/examples require section-level audit for the Jinja reference. |
| `helper-tags/skill.md` | `content-author-role.md` | Mostly covered; candidate timestamp default remains. Audit all helpers against preprocessors and tests. |
| `jinja/skill.md` | candidate `jinja-templating-reference.md` | Partial gap; copy only corrected operational mechanics. |
| `organization-patterns/skill.md`; days; lectures; modules; units | `course-architect-role.md` | Covered by more nuanced architecture. Reject mandatory weekly organization and globalizing unit-local metadata. |
| `workflows/new-course/skill.md` | `course-architect-role.md`; `content-author-role.md` | Planning and approval gates covered; reject questionnaire-at-once, fixed scaffold, repetition threshold, typical-week rule, and quiz percentages. |
| `workflows/update-resource/skill.md` | `content-author-role.md` | Covered, including staged identity migration; verify cross-role handoff wording. |
| `workflows/deploy/skill.md` | `deployment-engineer-role.md` | Superseded by a more complete current procedure; verify commands against the target installed version. |

## Legacy content that appears already covered

Confirm these conclusions in the audit rather than duplicating old file boundaries:

- Announcement, assignment, page, module, syllabus, and helper-tag basics are already in `content-author-role.md`.
- Quiz container settings, overrides, feedback, and all question types are already more completely covered by `quiz-design-principles.md`.
- Course-info/global-args ownership is already more accurate in `course-info-and-args-principles.md`.
- Days, lectures, units, modules, source trees, and representation choices are already treated more carefully in `course-architect-role.md`.
- New-course planning gates, safe updates, identity migration, validation, dry run, deployment, post-deploy review, and erase safeguards are already covered by the three role skills.

Examples from legacy files should be copied only when they teach one of the identified missing mechanics—not to recreate a second full tag reference.

## Legacy content to reject or rewrite

Do not migrate the following as authoritative guidance:

| Legacy guidance | Required treatment |
|---|---|
| `load.py`, `info.md`, nested routing `skill.md` wrappers | Delete; modern Myteam does not require them. |
| “Never commit `course_info`” | Reject. Current guidance requires non-secret course-info to be committed; only credentials and `.env` remain uncommitted. |
| Course-info without `DEPLOY_ROOT` | Update all examples to include and explain current required fields. |
| Only one valid human-readable date syntax | Reject. Keep one recommended authoring format, while Deployment Engineer documents all currently accepted forms. |
| Announcement `published_at` | Replace with current `publish_date`. |
| Optional IDs/default-to-title as normal practice | Replace with explicit stable IDs, preserving only the staged migration procedure for legacy implicit IDs. |
| Assignments referencing assignment-group display names | Use stable group IDs under current packaged guidance. |
| More-than-three repetitions must use Jinja | Replace with evidence-based templating guidance; repetition alone is not sufficient. |
| Mandatory weekly prep quiz/lecture/assignment/module pattern | Reject. Course rhythm must come from instructor practice and evidence. |
| Fixed quiz question-type percentages and mandatory settings | Reject. These are instructional decisions owned by the instructor. |
| Always call `.group()` on `search()` | Rewrite: first account for a possible `None`, then use `.group()` to extract matched text. |
| Institution-specific URLs, dates, courses, and directory names | Generalize unless the value is necessary to explain syntax. |
| Asking all intake questions at once | Reject; current interaction policy and Course Architect require one question at a time. |
| Deployment automatically followed by publication | Reject; deployment and student visibility remain separate authorized actions. |

## Implementation sequence

1. Produce the section-level pre-migration matrix and reconcile legacy material, all packaged claims/examples, current `documents/`, runtime source, and focused tests. Resolve contradictions before editing skills.
2. Finalize the topology. Keep the root flat unless the completed matrix demonstrates that multiple nested references are valuable.
3. Add `jinja-templating-reference.md` if the audit confirms it is independently useful, using current frontmatter and corrected examples.
4. Add confirmed missing mechanics to the appropriate existing skills; initial candidates are completion requirements, external-tool representation, and timestamp default.
5. Correct all packaged examples, especially missing module-item IDs, and update concrete cross-links and vague references to nonexistent packaged workflow/reference skills.
6. Check frontmatter parsing and all relative Markdown links.
7. Build a wheel into `.agents/scratch/` and install it in an isolated environment. Inspect the wheel and confirm every intended Markdown file ships under `mdxcanvas/skills/`.
8. In that isolated environment, first verify the installed console command itself:
   - `mdxcanvas skilldir` must return the installed package's skill directory.
   - If it fails, treat that as a packaging/entry-point defect to fix; do not silently validate with a source-tree fallback.
   - For source-tree diagnosis only, `poetry run mdxcanvas skilldir` or `python -m mdxcanvas.cli skilldir` may distinguish a stale external console script from checkout behavior.
9. Run `myteam list "$(mdxcanvas skilldir)"` against the isolated installation, then `myteam load <each exact displayed skill name>`.
10. Remove `.myteam/mdxcanvas-roster/` only after the matrix, runtime reconciliation, packaged-example audit, wheel inspection, installed `skilldir`, listing, and loading all pass. Do not retain compatibility `load.py` files.

## Acceptance criteria

- Every legacy section has a matrix row with an exact current destination, runtime/test evidence where applicable, disposition, and reason.
- Every retained behavioral claim has been reconciled against the target runtime; known documentation/runtime contradictions are resolved explicitly.
- Every XML/Jinja example satisfies current parser contracts and stable-identity policy, including explicit module-item IDs where required.
- Confirmed Jinja, completion-requirement, external-tool, and timestamp gaps are present in packaged skills; candidates disproved by the audit are not added.
- No current skill points to legacy `.myteam` paths or nonexistent workflow/reference skills.
- All skills use current `type: skill` / `description:` frontmatter.
- The root skill directory remains flat and has no unnecessary `description.md`; any justified nested folder uses `description.md` and no legacy loader.
- The isolated wheel contains the intended skill tree, its installed `mdxcanvas skilldir` works, and every displayed skill is discoverable with `myteam list` and loadable with `myteam load`.
- There are no `load.py` or `info.md` compatibility files in the packaged skill tree.
- Stale, unsafe, contradictory, or unverified legacy guidance is absent.
