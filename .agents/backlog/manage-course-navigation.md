# Manage Canvas course navigation

## Goal

Add declarative `mdxcanvas` support for the left-hand **Course Navigation** pane (the same settings shown in Canvas under **Settings → Navigation**). This should allow course source to control which existing navigation entries are visible and their order.

This feature manages navigation tabs already available to a course. Installing or configuring an LTI tool such as Gradescope is a separate External Tools concern; after installation, its course-navigation placement is exposed as a tab and can be reordered or hidden here.

## How to discover navigation with `canvasapi`

Given an authenticated `canvasapi.Canvas` and a course:

```python
from canvasapi import Canvas

canvas = Canvas(canvas_url, api_token)
course = canvas.get_course(course_id)
tabs = list(course.get_tabs())

for tab in tabs:
    print(
        tab.id,          # stable API identifier used when updating
        tab.label,       # display label, not necessarily unique or stable
        tab.position,    # 1-based Canvas position
        getattr(tab, "hidden", False),
        tab.type,        # commonly "internal" or "external"
        tab.visibility,  # public, members, admins, or none
        tab.html_url,
    )
```

`Course.get_tabs()` wraps:

```text
GET /api/v1/courses/:course_id/tabs
```

It returns a `PaginatedList[canvasapi.tab.Tab]`. Materialize or iterate the whole paginated result before validating desired configuration.

Use `tab.id` as the identity. Built-in IDs include values such as `home`, `pages`, and `assignments`; an LTI placement may have an ID such as `context_external_tool_<number>`. Do not identify tabs only by `label`, since labels may change or collide.

A typical returned tab has these useful fields:

- `id`
- `label`
- `position`
- `hidden` (Canvas may omit this attribute when false, so use `getattr(tab, "hidden", False)`)
- `type`
- `visibility`
- `html_url`

## How to manage navigation with `canvasapi`

Update the `Tab` object returned by `course.get_tabs()`:

```python
# Hide or show an existing tab.
tab.update(hidden=True)
tab.update(hidden=False)

# Move it to a 1-based Canvas position.
tab.update(position=desired_position)

# Both may be sent together.
tab.update(position=desired_position, hidden=False)
```

`Tab.update()` wraps:

```text
PUT /api/v1/courses/:course_id/tabs/:tab_id
```

The supported mutation fields are `position` and `hidden`. `canvasapi` updates the `Tab` object's attributes from Canvas's response and returns the same object.

Do not use the deprecated `Course.update_tab()` API. In supported CanvasAPI versions, retrieve tabs with `Course.get_tabs()` and call `Tab.update()`.

## Canvas constraints and edge cases

- **Home** and **Settings** are not manageable: Canvas does not allow them to be hidden or moved.
- Positions are Canvas's 1-based positions and include fixed entries. Do not infer positions solely from the index of the desired configurable-tab list.
- Some tabs can be restricted by Canvas/account policy or LTI configuration. `visibility` describes availability; it is not managed by the Tabs update endpoint.
- A tab can exist but be unavailable to students for reasons other than the `hidden` flag.
- External-tool tab IDs contain Canvas installation-specific numeric IDs. A configuration copied between Canvas targets may therefore need target-specific identity resolution or an explicit mapping strategy.
- The Tabs API controls existing placements; it does not create built-in tabs, install LTI tools, or add arbitrary URLs.
- API responses are paginated.

## Proposed `mdxcanvas` behavior

Introduce one course-scoped navigation resource/configuration that:

1. Calls `course.get_tabs()` once to discover the current state.
2. Validates every configured tab before making any mutation.
3. Resolves entries by exact `id`; optionally support a carefully validated external-tool selector later.
4. Rejects duplicate IDs, unknown IDs, attempts to manage Home/Settings, and ambiguous selectors.
5. Applies visibility through `Tab.update(hidden=...)`.
6. Applies ordering through `Tab.update(position=...)`, accounting for fixed tab positions and Canvas's reindexing after each move.
7. Refetches `course.get_tabs()` after mutation and verifies the resulting visible order and hidden states.
8. Reports changes and failures through the normal deployment report.

Prefer **partial-management semantics initially**: only tabs named in source are changed; unspecified tabs retain their existing order and hidden state. This avoids unexpectedly hiding institution-installed tools. If authoritative/full-list semantics are added, require an explicit mode and clearly report every unspecified tab that will be hidden.

Because external-tool IDs vary by target, the first implementation should require exact IDs and permit target-specific configuration. A later enhancement can resolve external tabs by an explicit compound selector (for example, tool/domain plus label), but it must fail on zero or multiple matches rather than guessing.

## Idempotency and deployment

Navigation should be treated as desired course state, not as a newly created Canvas resource:

- Compare desired properties with freshly fetched tab state.
- Skip `Tab.update()` when no managed property differs.
- Be careful with checksum-only skipping: navigation can be changed manually in Canvas after an `mdxcanvas` deployment. A deployment should inspect current Canvas state before deciding no operation is needed.
- For reordering, compute updates against current positions and refetch/verify after the sequence because each move can renumber other tabs.
- Mutation must remain subject to the existing deployment preview/authorization safeguards.

## Suggested source shape

The exact syntax should be decided with the broader course configuration design. A possible representation is:

```yaml
course_navigation:
  mode: partial
  tabs:
    - id: modules
      hidden: false
      order: 1
    - id: assignments
      hidden: false
      order: 2
    - id: pages
      hidden: true
    - id: context_external_tool_123
      hidden: false
      order: 3
```

`order` should mean relative order among explicitly ordered manageable tabs; the deployer should translate that intent to Canvas positions rather than requiring authors to account for fixed tabs such as Home.

## Acceptance criteria

- A read-only inspection path lists each tab's ID, label, type, visibility, hidden state, and position.
- Source can hide/show and reorder existing manageable tabs.
- Unknown, duplicate, fixed, or ambiguous tab references fail validation before any updates occur.
- External-tool tabs such as Gradescope can be managed when addressed by their discovered tab ID.
- Unspecified tabs remain untouched in partial mode.
- A second deployment with unchanged source and unchanged Canvas state performs no writes.
- Manual Canvas drift is detected and corrected on the next authorized deployment.
- Post-deploy state is refetched and verified.
- Unit tests cover omitted `hidden`, fixed tabs, unknown IDs, external tabs, position reindexing, partial semantics, idempotency, and verification failures.

## References

- Canvas Tabs API: https://developerdocs.instructure.com/services/canvas/resources/tabs
- CanvasAPI `Course.get_tabs()`: https://canvasapi.readthedocs.io/en/stable/course-ref.html
- CanvasAPI `Tab.update()`: https://canvasapi.readthedocs.io/en/stable/tab-ref.html
