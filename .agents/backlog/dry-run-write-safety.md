# Make `--dry-run` reliably read-only

## Problem

The documented `--dry-run` behavior is to preview modified resources without deploying them. Current deployment flow passes `dryrun=True` into resource logging, but continues into resource deployers afterward. Stale-resource cleanup also appears to remain active.

A dry run may therefore perform Canvas writes despite reporting that no resources were deployed.

## Desired investigation

Audit the complete deployment pipeline and ensure dry-run mode performs no Canvas mutations, including:

- creating or updating resources;
- deleting stale resources;
- changing course-scoped desired state;
- recording successful deployment checksums or Canvas metadata.

Dry-run mode may perform reads needed to validate input or describe proposed changes. Apply the fix consistently across all resource types rather than adding resource-specific safeguards.
