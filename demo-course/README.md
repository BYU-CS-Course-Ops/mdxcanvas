# MDXCanvas integration course

This is a deliberately small course for release-candidate smoke tests. Its source layout follows the unit-oriented pattern used by CS 110 and CS 301R: one top-level course file, a global-args file, generated content discovered beneath unit folders, and modules assembled at the course level.

The student-facing material is intentionally generic. The course is a feature fixture, not a model curriculum.

## Deploy

Create a private course-info file outside version control (or copy `course-info.example.yaml` and fill in the course ID), then run from the repository root:

```bash
poetry run mdxcanvas \
  --course-info demo-course/course-info.yaml \
  --global-args demo-course/canvas/global-args.yaml \
  --css demo-course/canvas/course.css \
  --dry-run \
  demo-course/canvas/course.canvas.md.xml.jinja
```

Remove `--dry-run` only for a dedicated Canvas sandbox. The source intentionally manages course settings, navigation, assignment groups, the syllabus, and tracked content, so a normal deployment is authoritative. Use `--no-cleanup` when testing only a subset.

`TEST_SECTION_IDS` is empty by default. Add valid section IDs in `canvas/global-args.yaml` to exercise assignment and quiz overrides; never use an ID from a production course.

Quarto and Mermaid must be installed to process the slide and diagram examples.

## Organization

- `canvas/course.canvas.md.xml.jinja` — single full-course entry point and module organization
- `canvas/content.canvas.md.xml.jinja` — discovers unit content files
- `canvas/unit0-introduction/` — pages, syllabus/navigation links, and setup quiz
- `canvas/unit1-content/` — data-driven assignments and common course patterns
- `canvas/unit2-features/` — uncommon tags and edge-case feature coverage
- `assets/` — course-level assets

## Feature coverage

| Area | Demonstrated in |
|---|---|
| Course settings, image, navigation, CSS, syllabus, assignment groups and drop rules | `course.canvas.md.xml.jinja` |
| Stable IDs, module item types, indentation, custom titles, positions, completion requirements and prerequisites | `course.canvas.md.xml.jinja` |
| Includes, Markdown pages, local/external images, internal links and timestamps | `unit0-introduction/` |
| Jinja globals, macros, loops, `glob`, `load`, `exists`, `parent`, `search`, `get_arg`, `enumerate`, `split_list`, and `debug` | course/content/unit templates |
| Include args with YAML, assignment dates, late date, upload restrictions, not-graded and external-tool submissions | `unit1-content/` |
| Quiz settings, overrides, all supported question types, points and answer feedback | `unit0-introduction/` and `unit2-features/questions.canvas.md.xml.jinja` |
| File upload metadata, zip overlays/additional files/exclusions, Mermaid (fence/inline/file), and Quarto slides | `unit2-features/` |
| Page publication/front-page/to-do/scheduled-publish fields and announcements | `unit0-introduction/content.canvas.md.xml.jinja` |

The three reference courses collectively use course-wide structure, pages, assignments, quizzes, overrides, files, zips, Quarto, internal links, MarkdownData-style generation, and timestamps. The feature unit adds supported capabilities not exercised there, notably Mermaid, module prerequisites/completion rules, the syllabus module-item type, assignment-group drop rules, advanced include options, file availability metadata, page scheduling/front-page fields, and less-common quiz settings/question variants.
