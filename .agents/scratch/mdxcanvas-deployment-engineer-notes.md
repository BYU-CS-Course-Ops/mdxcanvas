# MDXCanvas deployment notes

## New assignment groups with drop rules can fail

Observed with effective MDXCanvas 0.8.1 and CanvasAPI 3.5.0 on 2026-09-11.

A full deployment that created new assignment groups with `drop_lowest="1"` or `drop_highest="1"` failed when Canvas received the rule before assignments had been added to each group:

```text
Drop rules cannot be higher than the number of assignments
```

The group shells were created, their full update failed, and dependent resources were blocked. Independent resources completed and a 30-entry ledger was saved. A dry run did not predict the Canvas-side validation failure.

Operational guidance:

- Treat adding a drop rule to a new/empty group as a possible partial-deployment risk.
- After this failure, do not blindly rerun. Inspect the report, Canvas resources, and saved ledger first.
- A safe source-level workaround for a smoke-test fixture is to omit drop rules during initial deployment. Adding rules later requires separate review because the groups must contain enough assignments first.

## Editable-install version reporting

In this checkout, distribution metadata reported `mdxcanvas 0.6.21`, while the imported editable package read `mdxcanvas/VERSION` as `0.8.1`. Record both package location and effective `mdxcanvas.__version__`; do not rely only on `importlib.metadata.version()`.
