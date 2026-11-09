---
type: skill
description: Load when declaring course-wide navigation with <navigation> and <tab>.
---

# Course navigation

`<navigation>` is a singleton resource with fixed identity `navigation`. It takes no attributes and only empty `<tab name="..."/>` children plus whitespace. Each tab requires exactly one nonempty `name`, with no other attributes or nested/non-whitespace content. Names must be unique. The parser preserves spelling and surrounding whitespace; deployment matches exact case-sensitive Canvas labels, so use labels exactly as shown in the target.

Complete declaration (only use labels confirmed in the approved target):

```xml
<navigation>
  <tab name="Assignments" />
  <tab name="Modules" />
</navigation>
```

Listed tabs are shown in source order immediately after Home. Unlisted manageable tabs are hidden. Home and Settings cannot be listed or managed. Missing/ambiguous labels fail before updates; the tag does not create tabs or override Canvas/LTI visibility policy. An empty `<navigation/>` hides all manageable tabs; omitting the declaration leaves navigation unmanaged. Declare one block: duplicate singleton declarations can overwrite one another, with the last taking effect. This is course-wide configuration requiring instructor approval, not a module-local content fragment.
