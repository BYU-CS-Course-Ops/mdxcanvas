# Changelog

## 0.8.6 - 2026-09-17

### Added

- `is_section_specific` and `specific_sections` on `<announcement>` send an announcement to named sections instead of the whole course.

## 0.8.5 - 2026-09-17

### Fixed

- `points` on a `file-upload` question is now honoured (previously only recognized `points_possible`). 

## 0.8.4 - 2026-09-15

### Added

- `mdxcanvas --version` prints the version
- `mdxcanvas --skilldir` prints the location of installed `myteam`-compatible skills (these skills are agent-legible without `myteam`)

## 0.8.3 - 2026-09-15

### Fixed

- Human-facing report had too-much inactionable error content; dependency-failed errors are now summarized.

## 0.8.2 - 2026-09-14

### Added

- Exceptions originating in Jinja template rendering now give a best-effort attempt at including the template line causing the error. Helps with debugging.

## 0.8.1 - 2026-09-11

### Fixed

- Quarto slide rendering now includes local project assets before embedding them in standalone HTML, and asset changes trigger redeployment.

## 0.8.0 - 2026-09-10

While a major version increase (0.7 → 0.8), 0.8 does not introduce any breaking changes in syntax or behavior. It involved a significant re-write of the deployment machinery, so there is some risk of new bugs. Keep this in mind when upgrading from 0.7.x. 

### Added

- Added deterministic deployment planning shared by dry-run and live deployment, with dependency-aware concurrent execution, cycle handling, progress logging, and partial-success reporting.
- Added nested JSON deployment reports with per-action outcomes, contextual errors, manual-review metadata, and grouped Canvas links in human output.
- Added versioned ledger validation and migration, including rejection of ledgers created by newer MDXCanvas versions.

### Changed

- Made source authoritative by default: omitted tracked resources are deleted or untracked according to resource policy. Use `--no-cleanup` for targeted deployments; the former `--cleanup` option is removed.
- Made `--dry-run` read-only for Canvas resources and the deployment ledger while reporting the exact planned actions.
- Updated deployment and erase behavior to use the unified resource-handler pipeline and deterministic ledger state.

### Fixed

- `--dry-run` now correctly reports expected changes without changing Canvas resources.

## 0.7.11 - 2026-09-10

### Fixed

- Made Quarto slide downloads self-contained by bundling local JavaScript, CSS, images, and other assets into the generated HTML file.

## 0.7.10 - 2026-09-02

### Fixed

- Changed Quarto slide links to open standalone Reveal.js decks in a new browser tab instead of Canvas's file preview pane.

## 0.7.9 - 2026-09-02

### Added

- Added control for Canvas Course Navigation using `<navigation>` and ordered `<tab name="..."/>` elements.

## 0.7.8 - 2026-08-21

### Fixed

- Stopped reporting `answer_comments` as an unprocessed field on fill-in-the-blank, fill-in-multiple-blanks, and numerical answers. The attribute was always applied -- `_add_answer_comments` reads it directly from the tag -- but the three question types that also run `parse_settings` over their `<correct>` tags did not list it, so every answer carrying feedback logged a spurious warning. Parsed answers are unchanged.

## 0.7.7 - 2026-08-18

### Added

- Added `mdxcanvas skilldir` to print the installed MDXCanvas skills directory for use with tools such as `myteam`.

### Fixed

- Corrected normal stale-resource cleanup to remove stale quiz questions rather than entire stale quizzes. Stale module items continue to be removed by default.
- Updated CLI help to describe the corrected default cleanup behavior.
