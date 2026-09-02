# Supported Tags

The following tags are supported in MDXCanvas content files. These tags define course structure, assignments, quizzes, 
pages, and more.

Click on a tag to view its full documentation and usage examples.

For legacy repositories that need explicit resource IDs added across course files and documentation examples, see the [AI migration prompt](../migrating_to_explicit_ids.md).

## Module Structure

- [`<item>`](tags/item_tag.md) - Specifies an item (e.g., page, assignment, quiz) inside a module.
- [`<module>`](tags/module_tag.md) - Defines a Canvas module containing one or more items.

## Content Types

- [`<page>`](tags/page_tag.md) - Creates a standalone content page using Markdown or HTML.
- [`<assignment>`](tags/assignment_tag.md) - Creates a Canvas assignment with due dates, point values, and submission settings.
- [`<quiz>`](tags/quiz_tag.md) - Defines a quiz, including availability settings and a `<questions>` block.
  - [`<question>`](tags/quiz_question_types.md) types - Describes all supported quiz question types: multiple choice, true/false, 
    fill-in-the-blank, etc.

## Course-Wide Elements

- [`<navigation>`](tags/navigation_tag.md) - Authoritatively controls visible Canvas Course Navigation tabs and their order.
- [`<syllabus>`](tags/syllabus_tag.md) - Sets the content of the course syllabus page.
- [`<override>`](tags/override_tag.md) - Apply section-specific dates to assignments or quizzes.
- [`<announcement>`](tags/announcement_tag.md) - Post course-wide announcements with optional scheduled publishing.
