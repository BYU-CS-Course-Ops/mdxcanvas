# Changelog

## 0.8.0 - 2026-09-10

### Added

- Added deterministic deployment planning shared by dry-run and live deployment, with dependency-aware concurrent execution, cycle handling, progress logging, and partial-success reporting.
- Added nested JSON deployment reports with per-action outcomes, contextual errors, manual-review metadata, and grouped Canvas links in human output.
- Added versioned ledger validation and migration, including rejection of ledgers created by newer MDXCanvas versions.

### Changed

- Made source authoritative by default: omitted tracked resources are deleted or untracked according to resource policy. Use `--no-cleanup` for targeted deployments; the former `--cleanup` option is removed.
- Made dry-run read-only for Canvas resources and the deployment ledger while reporting the exact planned actions.
- Updated deployment and erase behavior to use the unified resource-handler pipeline and deterministic ledger state.

### Fixed

- Preserved completed ledger state after partial failures and, when possible, interrupted deployments.
- Preserved actionable quiz review names and links, including nullable review URLs.
- Added Canvas links for file-like resources and contextualized deployment failures while summarizing blocked resources.

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
