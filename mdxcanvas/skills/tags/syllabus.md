---
type: skill
description: Load when setting the Canvas course syllabus body with the <syllabus> tag.
---

# `<syllabus>` Tag

## When to Use This Reference

Use this reference when working with:

- Setting the Canvas course syllabus body

## Non-Negotiables

- Only one `<syllabus>` tag per course.
- Place it anywhere reachable from the active entry point, including an included fragment. Its fixed resource identity is `syllabus`; duplicate declarations can overwrite one another.

---

## Overview

The `<syllabus>` tag sets the content of the Canvas course syllabus page. It has no attributes — it wraps content
directly. The processor does not validate attributes, but none configure the syllabus; do not add identity or scheduling attributes.

---

## Structure

```xml
<syllabus>
    <include path="content/syllabus.md"/>
</syllabus>
```

The body supports Markdown, HTML, and `<include>` tags.

---

## Example: Inline Content

```xml
<syllabus>
    # Course Syllabus

    ## Course Description

    This course covers data structures and algorithms.

    ## Grading

    | Category | Weight |
    |---|---|
    | Homework | 40% |
    | Quizzes | 20% |
    | Projects | 40% |
</syllabus>
```

---

## Example: Included File

```xml
<syllabus>
    <include path="content/syllabus.md"/>
</syllabus>
```
