# MDXCanvas Myteam skill migration

## Goal and current status

Make `mdxcanvas/skills/` the complete, current distributable skill source and retire `.myteam/mdxcanvas-roster/` without compatibility loaders or obsolete guidance.

Content migration, section-level audit, isolated wheel validation, and legacy roster removal are complete. All 75 legacy files (25 skill files and their loader/info wrappers) were removed after checking their hashes against the audit inventory. Focused runtime checks were explicitly waived by the user; do not represent them as passed.

This record supersedes the initial provisional flat-layout plan. User decisions during implementation changed the topology: full tag references are independently loadable under `tags/`, and authoring requirements match actual parser behavior rather than imposing redundant IDs.

## Durable records

- [Section-level audit and dispositions](myteam-skill-content-gap-audit.md): **256 section rows across 25 legacy skill files**, exact current destinations, runtime/test evidence, rejected guidance, and pre-retirement file hashes.
- [Installed wheel validation](myteam-skill-content-gap-validation.md): distribution contents, installed entry-point correction, isolation, discovery/loading/link checks, limitations and artifact hash.

## Final topology

```text
mdxcanvas/skills/
├── content-author-role.md
├── course-architect-role.md
├── course-info-and-args-principles.md
├── deployment-engineer-role.md
├── jinja-templating-reference.md
├── quiz-design-principles.md
└── tags/
    ├── description.md
    ├── announcement.md
    ├── assignment.md
    ├── group-category.md
    ├── helper-tags.md
    ├── module.md
    ├── navigation.md
    ├── page.md
    ├── parsing-rules.md
    ├── quiz-questions.md
    ├── quiz.md
    └── syllabus.md
```

The five original public skill names remain. Root callers list the root directly; no root `description.md` is needed. `tags/description.md` provides nested discovery. Each skill uses `type: skill` and an actionable load description. Content Author renders `{{ myteam_list('tags/') }}` document-relatively. Literal course Jinja examples are raw-protected from Myteam rendering.

## Completed content work

- Copied and modernized meaningful individual tag/tag-group references, retaining useful syntax and examples rather than legacy routing boundaries.
- Reconciled attribute names/aliases, effective defaults, required fields, accepted dates, path resolution, helper behavior, question representations and deployment caveats against current source.
- Centralized tag syntax under `tags/`; Content Author retains role/workflow/ownership/identity/graph/handoff guidance, and quiz principles retains composition/representation/instructor-ownership guidance.
- Preserved optional derived IDs for content-backed module items. Explicit IDs remain required where the parser actually requires them. Existing explicit IDs must not be silently discarded.
- Corrected announcement fallback interpretation, stable assignment-group references, omitted falsy defaults, active date handling, file-upload points and other source-confirmed contradictions.
- Preserved completion-requirement forms, approved external-tool configuration syntax, and timestamp default/timezone/checksum behavior.
- Removed instructional mandates, rigid scaffolds, weekly-pattern assumptions, quiz percentages/settings, recursive loaders and unsafe configuration/credential guidance.
- Added the dedicated Jinja operational reference: helpers, regex Match/None handling, concatenation, loops/macros, multiline indent, MarkdownData data contracts, path contexts, data formats, argument scopes, and shallow-global override precedence. Linked it from authoring, architecture and configuration roles.
- Independent review corrected a new-group/assignment dependency cycle in an example and documented staged `never_drop` use.

## Distribution validation

- Built and installed a wheel into a clean isolated venv with declared dependencies.
- Corrected `mdxcanvas skilldir`: it previously fell through as a course filename. CLI now handles both `skilldir` and `--skilldir` before deployment imports.
- Verified 18 packaged Markdown files: 17 discoverable/loadable skills plus the nested description.
- Verified installed paths, byte equality with source/wheel, dynamic tag listing, literal Jinja survival, relative links and absence of loader/info compatibility files.
- No source-tree fallback was used to declare the installed command successful.

## Retirement gate

- [x] Every legacy Markdown heading outside fenced examples has a section-level disposition; meaningful unheaded content is included in its containing section.
- [x] Known legacy/runtime contradictions and final topology recorded.
- [x] Packaged syntax/examples reviewed and Myteam discovery/rendering checked.
- [x] Jinja operational gap completed by delegation.
- [x] Isolated wheel contents, installed skilldir, listing, loading and links pass.
- [x] Focused project/runtime checks explicitly waived by the user; not run in this final phase.
- [x] Removed `.myteam/mdxcanvas-roster/` after all above checks, including the explicit waiver.
- [x] Verified no active packaged guidance refers to the removed roster; historical paths remain only in migration evidence.

No managed Myteam workflows are created from legacy procedural guidance. No compatibility `load.py` or `info.md` is retained. General stale `documents/` cleanup and focused runtime checks are outside the completed migration scope, not hidden claims of verification.
