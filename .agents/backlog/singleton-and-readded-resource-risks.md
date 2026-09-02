# Singleton and re-added resource lifecycle risks

## Goal

Investigate two related source-processing risks and define consistent behavior across MDXCanvas resources.

## Duplicate singleton-style tags

Course-wide source constructs may appear more than once after rendering and include expansion. Current processing may overwrite an earlier definition rather than report the conflict.

Future work should inventory singleton-style constructs (for example, syllabus and course navigation), decide whether duplicate definitions should fail, merge, or follow a documented precedence rule, and apply that behavior consistently.

## Removing and re-adding resources

Checksum state may outlive a resource's presence in source. If a resource is removed, left unmanaged in Canvas, and later re-added with the same source data, its old checksum may cause deployment to skip it even when Canvas state changed while it was unmanaged.

Future work should define lifecycle semantics for removal and re-addition across resource types, including:

- whether absence clears or retires stored checksum/resource metadata;
- how cleanup mode affects that metadata;
- whether re-adding identical source forces reconciliation;
- how intentionally unmanaged Canvas changes are preserved;
- how behavior remains consistent across ordinary and singleton-style resources.

## Navigation-specific consequence

For course navigation, no `<navigation>` block means navigation is unmanaged and Canvas is left unchanged. Until the general lifecycle issue is addressed, removing and later re-adding the same block may not reliably trigger reconciliation.
