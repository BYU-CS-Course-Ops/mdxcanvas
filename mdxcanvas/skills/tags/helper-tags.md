---
type: skill
description: Load for includes, generated pages, files/images/zips, internal links, timestamps, course settings, Quarto slides, or Mermaid diagrams.
---

# Special / Helper Tags

## When to Use This Reference

Use this reference whenever a request involves:

- Using `<include>` to embed a file or Jinja template
- Using `<md-page>` to create a Canvas page from a Markdown file
- Uploading files or images with `<file>`, `<img>`, or `<zip>`
- Creating internal links with `<course-link>`
- Setting course metadata with `<course-settings>`
- Inserting a deploy timestamp with `<timestamp/>`

These tags are infrastructure — using them incorrectly breaks resource links and uploads.

## Non-Negotiables

- Do not use plain Markdown links for internal course resources. Use `<course-link>` for automatic URL resolution.
- The `id` in `<course-link id="...">` refers to the target's stable resource ID, not its display title. For derived or fixed identities, use that derived or fixed value.
- All `path` values are relative to the file containing the tag, not the project root.

---

## Shared helper behavior

Examples are fragments requiring their containing resource and referenced local files/target IDs, unless explicitly complete. Helper preprocessors generally read specific attributes rather than applying the resource parser's unknown-attribute validation; an extra field may be ignored, not supported configuration. No helper field aliases are defined. See [Shared parsing rules](parsing-rules.md) for boolean parsing and date forwarding.

Paths resolve relative to the current source file's directory, including `args`, course banner images, zip overlays/additional files, and external diagram sources. Included files get their own directory context. Absolute paths work through normal Path resolution; relative paths are preferable for portability. Asset file/image IDs derive from basename, so avoid basename collisions. Upload helpers default the Canvas folder to `deployed_files` at deployment; optional lock/unlock values are forwarded unchanged.

## Overview

| Tag                 | Purpose                                    | Key Attributes                                                                  |
|---------------------|--------------------------------------------|---------------------------------------------------------------------------------|
| `<include>`         | Embed external file content inline         | `path`, `fenced`, `lines`, `args`, `usediv`                                     |
| `<md-page>`         | Create a Canvas page from a `.md` file     | `id`, `path`, `title`                                                                 |
| `<file>`            | Upload and link a single file to Canvas    | `path`, `title`, `canvas_folder`, `unlock_at`, `lock_at`                        |
| `<img>`             | Upload and embed an image inline           | `src`, `canvas_folder`                                                          |
| `<zip>`             | Upload a zip archive to Canvas             | `name`, `path`, `additional_files`, `priority_path`, `exclude`, `canvas_folder` |
| `<course-link>`     | Link to another course item by type and id | `type`, `id`, `fragment`                                                        |
| `<course-settings>` | Set course metadata (name, code, image)    | `name`, `code`, `image`                                                         |
| `<timestamp/>`      | Insert current date/time at deploy         | `format` (optional)                                                             |

---

## `<include>`

Embeds the content of another file at the point of inclusion. The `path` is relative to the file containing the
`<include>` tag.

### Attributes

| Attribute          | Required | Description                                                                          |
|--------------------|----------|--------------------------------------------------------------------------------------|
| `path`             | yes      | Relative path to the file to include                                                 |
| `fenced`           | no       | Boolean; default false; language is inferred from filename suffix |
| `include_filename` | no       | Add filename header to fenced code block (`"True"`)                                  |
| `lines`            | no       | Include only specific lines, format `"start:end"` (1-based, inclusive)               |
| `args`             | no       | Path to args file for Jinja template processing                                      |
| `usediv`           | no       | Wrap in `<div>` element (default `true`); set `"false"` to insert directly           |

### Examples

```xml
<!-- Embed a Markdown file -->
<assignment id="hw1" title="Homework 1">
    <include path="content/assignments/hw1.md"/>
</assignment>

        <!-- Code file as fenced block with filename header -->
<page id="sorting-example" title="Sorting Example">
<include path="code/sort.py" fenced="true" include_filename="true"/>
</page>

        <!-- Include only lines 10–25 -->
<include path="code/sort.py" fenced="true" lines="10:25"/>

        <!-- Render a Jinja template with an args file -->
<include path="templates/homework.md.jinja" args="content/hw3-args.yaml"/>

        <!-- Include without wrapper div -->
<include path="content.md" usediv="false"/>
```

---

`include_filename` defaults false. `lines="10"` means line 10 onward; `10:25` is inclusive. Selection occurs before Jinja/Markdown processing. `usediv` defaults true and adds source-tracking metadata; false is important for fragments whose parent requires direct children (notably quiz questions). `args` resolves beside the including source, not the included template. Only files whose final suffix is `.jinja` use it for Jinja rendering.

## `<md-page>`

Creates a Canvas page from a source file. If `title` is absent, only a first-line `# Heading` is used, otherwise the filename stem is used. An empty file cannot supply an inferred first line. Only `path`, `id`, and `title` are consumed; other page settings are not forwarded. Processing is through an include in the source file's directory context.

### Attributes

| Attribute | Required | Description                        |
|-----------|----------|------------------------------------|
| `id`      | yes      | Stable identity of the generated page |
| `path`    | yes      | Relative path to the markdown file |
| `title`   | no       | Override the auto-detected title   |

### Examples

```xml

<md-page id="week1-intro" path="content/pages/week1-intro.md"/>
<md-page id="week1" path="content/pages/week1.md" title="Week 1: Getting Started"/>
```

---

## `<file>`

Uploads a file to Canvas and creates a download link.

### Attributes

| Attribute       | Required | Description                                                      |
|-----------------|----------|------------------------------------------------------------------|
| `path`          | yes      | Relative path to the file                                        |
| `title`         | no       | HTML title attribute only; generated link text remains the basename                               |
| `canvas_folder` | no       | Canvas folder path to upload the file to                         |
| `unlock_at`     | no       | Raw unlock date passed to upload deployment; prefer offset ISO      |
| `lock_at`       | no       | Raw lock date passed to upload deployment; prefer offset ISO |

### Examples

```xml

<assignment id="project-1" title="Project 1">
    Download the starter files:
    <file path="files/project1-starter.zip" title="Project 1 Starter Files"/>
</assignment>

<file path="syllabus.pdf" canvas_folder="Course Documents"/>

<file path="midterm_exam.pdf"
      unlock_at="Feb 15, 2025, 9:00 AM"
      lock_at="Feb 15, 2025, 11:00 AM"
      canvas_folder="Exams"/>
```

---

## `<img>`

Uploads a local image and rewrites `src` to its resolved URI plus `/preview`. Only sources starting with `http` or internal `__@@` tokens are left unchanged; `@@PLUGINFILE@@` is not a recognized bypass. Local files must exist. Standard HTML attributes remain on the image; lock/unlock metadata is not read from images.

### Attributes

| Attribute       | Required | Description                                             |
|-----------------|----------|---------------------------------------------------------|
| `src`           | yes      | Local file path or external URL                         |
| `canvas_folder` | no       | Canvas folder to upload the image to (local files only) |

Standard HTML `img` attributes (`alt`, `width`, `height`) can also be used.

### Examples

```xml

<img src="images/diagram.png" alt="Course diagram"/>
<img src="images/circuit.png" canvas_folder="Lab Diagrams" alt="Lab 1 Circuit"/>
<img src="https://example.com/photo.jpg"/>
```

---

## `<zip>`

Uploads a zip archive to Canvas.

### Attributes

| Attribute          | Required | Description                                                         |
|--------------------|----------|---------------------------------------------------------------------|
| `path`             | yes      | Source directory to zip                                             |
| `name`             | no       | Archive identity/name; default removes dots from path, replaces `/` with `-`, strips edge hyphens, appends `.zip` |
| `additional_files` | no       | Comma-separated list of additional files to include                 |
| `priority_path`    | no       | Local overlay directory; matching archive paths win over base/additional files                                 |
| `exclude`          | no       | Regex pattern for files/folders to exclude                          |
| `canvas_folder`    | no       | Canvas folder to upload the zip to                                  |

### Examples

```xml

<zip path="labs/lab1"/>

<zip name="lab1_resources.zip"
     path="labs/lab1"
     additional_files="shared/utils.py,README.md"
     priority_path="labs/lab1/starter"
     exclude=".*\.log"
     canvas_folder="Lab Materials"/>
```

---

Zip also accepts optional `unlock_at` and `lock_at` (raw values). `additional_files` is comma-split without whitespace trimming (avoid spaces after commas), and accepts directories too. `exclude` is a regex searched against each discovered basename recursively; additional files bypass it. Priority files win on matching archive-relative paths; additional files first overwrite base entries. The link text is the archive name. Inspect the entire archive map: overlaying starter files does not remove unmatched solutions, keys, secrets, or caches.

## `<course-link>`

Creates a link to another course resource. The link resolves to the Canvas URL automatically at build time.

### Attributes

| Attribute  | Required | Description                                                                                     |
|------------|----------|-------------------------------------------------------------------------------------------------|
| `type`     | yes      | Exact lowercase type: `page`, `assignment`, `quiz`, `announcement`, `discussion`, `module`, `syllabus`, `file` |
| `id`       | yes      | The stable resource ID of the target                                 |
| `fragment` | no       | URL fragment to jump to a section on the target page                                            |

A simple string body becomes custom plain link text (not rich markup); otherwise the target title is used. Resolution occurs at deployment. The target must expose the requested URI/title fields. `discussion` is accepted by the link helper but no discussion resource tag is implemented here. Use explicit link text if the target lacks title metadata.

### Examples

```xml

<course-link type="assignment" id="hw1"/>

<page id="week2-intro" title="Week 2 Intro">
Before proceeding, complete
<course-link type="assignment" id="hw1">Homework 1</course-link>.
</page>

<course-link type="page" id="intro_page" fragment="my-fancy-title"/>
```

Note: `id` refers to the target's stable resource ID, not its display title. For example, the syllabus uses the fixed ID `syllabus`, while an uploaded file uses its filename-derived ID.

---

## `<timestamp/>`

Inserts the current date/time in the configured course timezone at deployment, not Jinja render time. This is a deployment string replacement, not a resource tag; use only `format` (Python strftime) and an empty element/body. Other attributes prevent matching rather than configure output.

### Attributes

| Attribute | Required | Description                                                                                            |
|-----------|----------|--------------------------------------------------------------------------------------------------------|
| `format`  | no       | Python `strftime` format string; default: `%B %d, %Y at %I:%M %p` (e.g., `March 11, 2026 at 02:30 PM`) |

### Examples

```xml
*Last updated:
<timestamp/>*

<timestamp format="%m/%d/%Y"/>
```

---

## `<course-settings>`

Sets singleton course metadata. At least one of `name`, `code`, or `image` must be nonempty. `canvas_folder` is additionally accepted for the banner upload, whose identity is the image basename. Missing optional metadata is stored as null, not filled with inferred course values.

### Attributes

| Attribute | Required | Description                          |
|-----------|----------|--------------------------------------|
| `name`    | no*      | Display name of the course           |
| `code`    | no*      | Course code (e.g., `CS 101`)         |
| `image`   | no*      | Relative path to course banner image |

\* At least one of `name`, `code`, or `image` must be specified.

### Examples

```xml

<course-settings name="CS 312: Algorithm Design" code="CS 312"/>

<course-settings name="Data Structures and Algorithms" code="CS 235" image="images/cs235_banner.png"/>
```

## `<quarto-slides>`

| Attribute | Required | Behavior |
|---|---|---|
| `path` | yes | Local `.qmd` input relative to current source |
| `name` | no | Stable output name/identity; defaults to input filename with `.qmd` replaced by `.slides.html` |
| `dependencies` | no | Comma-separated, trimmed paths/globs relative to the `.qmd` directory; unmatched patterns fail |
| `canvas_folder`, `unlock_at`, `lock_at` | no | Upload metadata; dates passed unchanged |

Registers a deck rendered by Quarto during deployment, then emits a download anchor with `?download_frd=1` (Canvas HTML previews cannot run the deck's Reveal.js). Keep `.qmd`, Quarto configuration, and assets as source, not generated HTML or `*_files/` output. Local references, project config, and `_extensions` are tracked automatically for checksums; `dependencies` covers otherwise undiscoverable inputs such as data read by executable code. Referenced directories are expanded. Rendering requires the external Quarto toolchain; registration alone does not validate rendered behavior.

Fragment requiring the local deck and data:

```xml
<quarto-slides path="slides/introduction.qmd" name="introduction.slides.html"
               dependencies="data/*.csv" />
```

## `<mermaid>`

Supply exactly one of a local `path` or nonempty inline diagram source. `name` optionally supplies stable identity; otherwise identity is `mermaid-` plus the first eight SHA-256 hex characters of source (editing source changes that identity). Use a stable name for a durable diagram.

| Attribute | Behavior |
|---|---|
| `path` | Optional local source, mutually exclusive with inline body |
| `name` | Optional explicit resource identity |
| `canvas_folder`, `unlock_at`, `lock_at` | Upload metadata; dates passed unchanged |
| `alt`, `class` | Copied to the generated image |
| Other attributes | Saved as renderer attributes, not arbitrary HTML image fields |

Deployment renders and uploads an image; the tag becomes an `<img>` preview with the resource identity as its image ID. Current rendering uses Playwright Chromium and loads Mermaid from a CDN; it can attempt a browser installation if missing. Do not invoke rendering as an offline check. Renderer attributes actually consumed are `background` (default `transparent`), `theme` (default `default`), and integer `svg_padding` (default 10); other saved attributes have no effect in this renderer. Verify alt text and output.

Inline fragment:

```xml
<mermaid name="processing-flow" alt="Source flows through parsing to deployment">
flowchart LR
    Source --> Parsing --> Deployment
</mermaid>
```

File-based alternative (requires the local source):

```xml
<mermaid path="diagrams/processing.mmd" name="processing-flow"
         alt="Source flows through parsing to deployment" />
```
