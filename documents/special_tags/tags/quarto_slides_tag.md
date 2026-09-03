# `<quarto-slides>` Tag

The `<quarto-slides>` tag renders a Quarto `.qmd` slide source and uploads the generated HTML deck to Canvas as a file link.

The link opens the standalone HTML file in a new browser tab rather than Canvas's file preview pane, allowing Reveal.js to render the deck correctly.

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
- `_quarto.yaml` or `_quarto.yml` in the detected Quarto project root
- the `_extensions/` folder in that same root (if present)

This means updates to project config/extensions can trigger slide redeployments.

## Example

```xml
<page id="week-1-slides" title="Week 1 Slides">
    <p>Download or open the slide deck:</p>
    <quarto-slides
        path="slides/week1-intro.qmd"
        name="week1-intro.html"
        canvas_folder="Slides" />
</page>
```

See the demo course example:

- `demo-course/demo-quarto-slides.canvas.md.xml.jinja`
- `demo-course/slides/example-slides.qmd`
