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

- Do not rename a page's `title` without first adding `id` equal to the current title.
- Always set `id` when creating a new page if it will be referenced via `<item content_id>`.

---

## Attributes

| Attribute | Required | Description                                                |
|-----------|----------|------------------------------------------------------------|
| `title`   | yes      | Page title shown in Canvas and referenced in `<item>` tags |
| `id`      | no       | Stable identifier; defaults to `title`                     |

### `id`

Use an explicit `id` when you need to rename the page later without creating a new resource. `id` will become required
in a future version — add it now when you touch a resource.

```xml
<page id="intro_page" title="Introduction (Updated)">
    ...
</page>
```

**When modifying a resource with no `id`:** first add `id` equal to the current `title` value and keep `title`
unchanged. Then make other edits. Changing `title` without an `id` creates a new resource instead of updating the
existing one.

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

## Example

```xml
<page title="Example Page">
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
```

---

## Creating a Page from a Markdown File

Use `<md-page>` to create a Canvas page directly from a `.md` file. The first `# Heading` becomes the page title:

```xml
<md-page path="content/pages/week1-intro.md"/>
```

Override the auto-detected title with the `title` attribute:

```xml
<md-page path="content/pages/week1.md" title="Week 1: Getting Started"/>
```

---

## Skeleton Template

```xml
<page title="[PAGE TITLE]">
    # [PAGE TITLE]

    [Page introduction or overview here.]

    ## Section 1

    [Section content here.]

    ## Section 2

    [Section content here.]

    ---

    ## Resources

    - [Resource 1](link)
    - [Resource 2](link)

</page>
```
