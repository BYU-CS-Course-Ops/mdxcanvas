---
type: skill
description: Load when creating or editing <page> tags or generating pages with <md-page>.
---

# `<page>` Tag

## When to Use This Reference

Use this reference when working with:

- Creating or editing a Canvas page
- Writing lecture content, reference material, or course notes
- Using `<md-page>` to generate a page from a `.md` file
- Renaming a page without creating a duplicate

## Non-Negotiables

- Every `<page>` requires `id` and `title`; preserve `id` when changing the display title.
- Every `<md-page>` requires `id` and `path`; its title may be derived from the file.

---

## Attributes

| Attribute | Required | Description                                                |
|-----------|----------|------------------------------------------------------------|
| `title`   | yes      | Page title shown in Canvas                                |
| `id`      | yes      | Stable identifier referenced by `<item content_id>`        |

| Additional optional attribute | Parsing / effective default |
|---|---|
| `editing_roles` | String; emitted default `teachers` |
| `notify_of_update`, `front_page`, `published` | Boolean; omitted when absent (declared false defaults are skipped) |
| `student_todo_at`, `publish_at` | Dates; omitted when absent |

See [Shared parsing rules](parsing-rules.md). `<page>` has no title alias. For `<md-page>` helper fields and path/title derivation, see [Helpers](helper-tags.md); it does not forward arbitrary page settings.

### `id`

`id` is required now. Preserve it when renaming a page so references and Canvas identity remain unchanged.

```xml
<page id="intro_page" title="Introduction (Updated)">
    ...
</page>
```

For legacy pages deployed by older versions using implicit title identity, first add `id` equal to the previously deployed title without renaming it. Deploy that identity migration separately before a later rename. Current parsing rejects pages without `id`.

---

## Content

The body of a `<page>` tag supports:

- Markdown headings, bold, italic, lists
- HTML
- Fenced code blocks
- Tables
- Links (inline or reference)

All standard Markdown and Canvas HTML formatting is supported.

---

## Complete page example

````xml
<page id="example-page" title="Example Page">
    # Welcome to the Example Page

    Things like headers and `MD` formatting can be used here.

    ## Code Example

    ```python
    def example_function():
        print("This is an example function.")
    ```

    ## Links

    You can also include links to other resources, such as
    [Canvas Documentation](https://canvas.instructure.com/doc/api/).

    ## Table Example

    | Header 1 | Header 2 |
    | -------- | -------- |
    | Row 1    | Row 2    |
    | Row 3    | Row 4    |
</page>
````

---

## Creating a Page from a Markdown File

Use `<md-page>` with required `id` and `path` to create a Canvas page directly from a `.md` file. A first-line `# Heading` becomes the title; otherwise the filename stem is used. These fragments require the local source files:

```xml
<md-page id="week1-intro" path="content/pages/week1-intro.md"/>
```

Override the auto-detected title with the `title` attribute:

```xml
<md-page id="week1" path="content/pages/week1.md" title="Week 1: Getting Started"/>
```

---

## Skeleton Template (replace placeholders; not runnable)

```xml
<page id="[STABLE ID]" title="[PAGE TITLE]">
    # [PAGE TITLE]

    [Page introduction or overview here.]

    ## Section 1

    [Section content here.]

    ## Section 2

    [Section content here.]

    ---

    ## Resources

    - [Insert approved resource links here.]

</page>
```
