# `<quarto-slides>` Tag

The `<quarto-slides>` tag renders a Quarto `.qmd` slide source and uploads the generated HTML deck to Canvas as a file link.

The link downloads the generated HTML deck directly from Canvas. Canvas sandboxes HTML file responses, so Reveal.js cannot run from a Canvas file preview; students should open the downloaded HTML file locally.

This is useful when you want to keep lecture slides in Quarto while still distributing them through course content pages.

For repository-wide migration help when updating legacy content to explicit `id` attributes, see the [AI migration prompt](../../migrating_to_explicit_ids.md).

## Requirements

- Quarto must be installed and available on your `PATH` (the command `quarto render` is executed during deployment).

## Attributes

### `path` (required)

Relative path to the `.qmd` file.

```xml
<quarto-slides path="slides/week1-intro.qmd" />
```

### `name` (optional)

Output filename for the generated slides HTML. If omitted, defaults to `<qmd-file-name>.slides.html`.

```xml
<!-- Explicit output name -->
<quarto-slides path="slides/week1-intro.qmd" name="week1-intro.html" />

<!-- Auto-generated output name: week1-intro.slides.html -->
<quarto-slides path="slides/week1-intro.qmd" />
```

### `dependencies` (optional)

Comma-separated files or glob patterns, relative to the `.qmd` file, for inputs that cannot be discovered from the document. This is useful for data read by executable code.

```xml
<quarto-slides
    path="slides/week1-intro.qmd"
    dependencies="data/*.csv,images/generated/**" />
```

A pattern that matches no files is reported as an error.

### `canvas_folder` (optional)

Canvas files folder where the rendered slide deck will be uploaded.

```xml
<quarto-slides path="slides/week1-intro.qmd" canvas_folder="Slides" />
```

### `unlock_at` / `lock_at` (optional)

Availability dates for the uploaded file.

```xml
<quarto-slides
    path="slides/week1-intro.qmd"
    unlock_at="Jan 08, 2026, 08:00 AM"
    lock_at="Jan 31, 2026, 11:59 PM" />
```

## Quarto Project Dependency Tracking

When checksums are computed, MDXCanvas tracks:

- the `.qmd` file itself
- local files referenced by Markdown, HTML, YAML frontmatter, CSS, and Quarto include shortcodes
- files and glob patterns listed in `dependencies`
- `_quarto.yaml` or `_quarto.yml` in the detected Quarto project root, including local files referenced by that configuration
- the `_extensions/` folder in that same root (if present)

Unrelated files elsewhere in the Quarto project do not trigger slide redeployments. Use `dependencies` for inputs that cannot be discovered statically, such as data files opened by executable code.

## Example

```xml
<page id="week-1-slides" title="Week 1 Slides">
    <p>Download the slide deck and open the downloaded HTML file:</p>
    <quarto-slides
        path="slides/week1-intro.qmd"
        name="week1-intro.html"
        canvas_folder="Slides" />
</page>
```

See the demo course example:

- `demo-course/demo-quarto-slides.canvas.md.xml.jinja`
- `demo-course/slides/example-slides.qmd`
