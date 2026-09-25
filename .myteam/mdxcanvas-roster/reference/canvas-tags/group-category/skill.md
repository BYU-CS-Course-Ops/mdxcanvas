---
id: canvas-tags-group-category
description: Syntax and attribute reference for the <group-category> tag, and how Canvas group membership works.
---

# `<group-category>` Tag

## When to Use This Reference

Use this reference when working with:

- Group assignments, where one submission covers several students
- Declaring the teams a course uses, such as project teams or lab pairs
- Deciding what belongs in source and what stays in Canvas

## Non-Negotiables

- An `<assignment>` joins a category by the **`id` you declared**, not by the
  category's Canvas name. `group_category` is resolved the same way
  `assignment_group` is.
- `auto_leader` requires `self_signup`. Canvas rejects it on its own.
- Membership is not declared here. See below.

---

## How Canvas groups work

A **category** holds **groups**, and groups hold **students**. The category is
what an assignment points at; the groups inside it are the actual teams. A course
usually has more than one category, for example project teams and lab pairs.

With a group assignment, one submission covers the group. Grades can then be
applied per group or per student.

Membership is set four ways, and they can be mixed:

| How | What happens |
|-----|--------------|
| Manually | An instructor puts students into groups in the Canvas UI |
| Self sign-up | Students choose their own group; `restricted` confines them to their own section |
| Auto-assign | Canvas distributes unassigned students across the existing groups in one call |
| Auto leader | Canvas names a group leader as members arrive, either the `first` to join or a `random` one |

A category and its groups exist perfectly well with no members at all, which is
why the structure can be declared ahead of enrolment.

---

## What is declared, and what is not

**Declared here:** the category, and the sign-up rules that govern it.

**Left in Canvas:** the groups inside the category, and who is in them.
Membership follows enrolment and changes all term, so it does not belong in
version control. Declaring it would mean a deploy could silently reshuffle teams
mid-project.

---

## Attributes

| Attribute      | Required | Description                                                                 |
|----------------|----------|-----------------------------------------------------------------------------|
| `id`           | yes      | Stable identifier; this is what an `<assignment>` references                  |
| `name`         | yes      | Category name shown in Canvas                                                 |
| `self_signup`  | no       | `enabled` lets students pick a group; `restricted` confines them to their section |
| `group_limit`  | no       | Maximum members per group. Only meaningful with `self_signup`                 |
| `auto_leader`  | no       | `first` or `random`. Requires `self_signup`                                   |

---

## Example

```xml
<group-category id="project-teams"
                name="Project Teams"
                self_signup="enabled"
                group_limit="4" />

<assignment id="final-project"
            title="Final Project"
            group_category="project-teams"
            points_possible="100">
    Work in teams of up to four.
</assignment>
```

An instructor-assigned category, with no self sign-up:

```xml
<group-category id="lab-pairs" name="Lab Pairs" />
```

---

## Skeleton Template

```xml
<group-category id="[STABLE ID]" name="[CATEGORY NAME]" />

<assignment id="[ASSIGNMENT ID]"
            title="[ASSIGNMENT TITLE]"
            group_category="[STABLE ID]">
    [Assignment body here.]
</assignment>
```
