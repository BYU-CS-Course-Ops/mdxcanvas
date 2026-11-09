---
type: skill
description: Load for assignment groups (<assignment-groups>/<group>), student group categories, or assignment references to either.
---

# Assignment groups and student group categories

## `<assignment-groups>` and `<group>`

Assignment groups organize graded work; they are not student teams. `<assignment-groups>` is a structural wrapper. Each `<group>` accepts:

| Attribute | Required | Parsing / default |
|---|---|---|
| `id` | yes | Stable source identity |
| `name` | yes | Display name |
| `weight` / `group_weight` | no | Integer |
| `never_drop` | no | List of stable assignment IDs |
| `drop_lowest`, `drop_highest`, `position` | no | Integers |

Setting `weight` (including explicit zero) makes deployment enable course-wide assignment-group weighting. This requires approved grading intent; omitting it does not disable existing weighting.

No defaults are emitted. Truthy drop fields and `never_drop` move into `rules`; explicit zero drop counts remain top-level rather than entering `rules`, so do not rely on zero to clear existing rules. Assignment and quiz `assignment_group` references use `id`, not `name`. See [Shared parsing rules](parsing-rules.md).

Complete resource fragment (grading weights are illustrative instructor choices):

```xml
<assignment-groups>
  <group id="homework" name="Homework" weight="30" />
</assignment-groups>
<assignment id="analysis-report" title="Analysis Report" assignment_group="homework">
  Submit the approved report.
</assignment>
```

`never_drop="analysis-report"` can be added to that group after the group and assignment have been deployed and their identities are tracked. Do not create a new group with `never_drop` referencing a new assignment that also references that group in the same initial deployment: this creates a dependency cycle the current planner cannot bootstrap. Coordinate any staged deployment with the Deployment Engineer.

## `<group-category>` Tag

## When to Use This Reference

Use this reference when working with:

- Group assignments, where one submission covers several students
- Declaring the teams a course uses, such as project teams or lab pairs
- Deciding what belongs in source and what stays in Canvas

## Non-Negotiables

- An `<assignment>` joins a category by the **`id` you declared**, not by the
  category's Canvas name. `group_category` is resolved the same way
  `assignment_group` is.
- A `<group-categories>` wrapper can organize categories, as `<assignment-groups>` organizes grading groups; the wrapper is not required by the parser.
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

No defaults or aliases are defined. Optional string fields are forwarded without enum validation; `group_limit` uses integer parsing. `<group-categories>` is only a wrapper. The parser accepts a category wherever reachable; no fixed file location is required.

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
<group-categories>
    <group-category id="project-teams"
                    name="Project Teams"
                    self_signup="enabled"
                    group_limit="4" />
</group-categories>

<assignment id="final-project"
            title="Final Project"
            group_category="project-teams"
            points_possible="100">
    Work in teams of up to four.
</assignment>
```

An instructor-assigned category, with no self sign-up:

```xml
<group-categories>
    <group-category id="lab-pairs" name="Lab Pairs" />
</group-categories>
```

---

## Skeleton Template (replace placeholders; not runnable)

```xml
<group-categories>
    <group-category id="[STABLE ID]" name="[CATEGORY NAME]" />
</group-categories>

<assignment id="[ASSIGNMENT ID]"
            title="[ASSIGNMENT TITLE]"
            group_category="[STABLE ID]">
    [Assignment body here.]
</assignment>
```
