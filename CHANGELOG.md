# Changelog

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
