# `<navigation>`

Controls Canvas Course Navigation as one course-wide, checksum-managed resource.

```xml
<navigation>
  <tab name="Assignments"/>
  <tab name="External Tool"/>
  <tab name="Pages"/>
</navigation>
```

`<navigation>` accepts no attributes. Its only children are `<tab>` elements, and each `<tab>` must have one non-empty `name` attribute and no content. Duplicate names are invalid. Use one navigation block per document; if more than one is present, the last one takes effect.

Names match Canvas tab labels exactly and case-sensitively. A requested label must identify exactly one existing Canvas tab; missing and ambiguous labels fail deployment. Tabs are not created, and external-tool installation or configuration is not managed.

## Authoritative behavior

Listed tabs are made visible and ordered as written, in consecutive positions immediately after Home. Every manageable tab not listed is hidden. This applies to built-in and external-tool tabs.

Home and Settings are fixed Canvas tabs and cannot be listed or managed. Referencing either one is an error.

An empty block is authoritative and hides every manageable tab:

```xml
<navigation/>
```

If the document has no `<navigation>` block, navigation is unmanaged: deployment does not inspect or change Canvas tabs. Removing a previously deployed block also does not reset navigation.

## Deployment behavior and limitations

Navigation is inspected and reconciled only when its source checksum changes. If the checksum is unchanged, manual Canvas drift is intentionally preserved and no tab API request is made. Because cleanup retains the old checksum, removing and later restoring identical navigation source may also be skipped.

Before making changes, deployment validates the Canvas tab information and every requested label. Updates are then applied serially. A successful deployment is reported once for navigation, not for each tab. An API failure stops deployment immediately, but earlier tab updates are not rolled back; inspect Canvas before retrying. There is no post-deployment verification.

Canvas and LTI visibility policies can still prevent a listed external-tool tab from appearing to students. This tag does not manage those policies, install tools, or change tool configuration.
