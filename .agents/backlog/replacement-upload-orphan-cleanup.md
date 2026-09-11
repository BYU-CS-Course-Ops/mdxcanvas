# Prevent orphaned assets after replacement uploads

## Status

Deferred from the data-driven deployment refactor.

## Problem

Modified `file`, `zip`, `mermaid`, and `quarto-slides` resources are replacement uploads. Uploading the same filename to the same Canvas folder uses Canvas's overwrite behavior, but changing the destination folder while retaining the same MDXCanvas resource ID can create a new Canvas file and leave the previously tracked file behind.

The deployment refactor updates the ledger to the newly returned identity and propagates that identity to dependents. Once the ledger entry is replaced, ordinary stale cleanup cannot discover the prior Canvas identity because the source resource key itself is still present.

## Deferred design question

Decide how a replacement handler receives and disposes of the previous tracked identity. Possibilities include:

- pass optional previous `canvas_info` to replacement-Create handlers;
- add a distinct internal replacement contract;
- move the existing Canvas file before uploading with explicit overwrite behavior;
- upload first and delete the previous identity when the returned identity differs.

The design must account for partial failure. If the new upload succeeds but cleanup of the old identity fails, the new identity must not be lost and rerunning must not create further orphans.

## Scope constraints

- Keep the public transition as `MODIFIED` and successful outcome as `CREATED`.
- Do not expose prior Canvas identities in public reports.
- Preserve dependency propagation from the newly returned identity.
- Do not delete an old identity when Canvas reused that same identity.
- Handle already-absent prior files safely.

## Suggested tests

- same folder and filename uses overwrite behavior without an orphan;
- destination-folder change removes or moves the prior file;
- returned identity equal to prior identity is never deleted;
- prior identity already absent does not fail replacement;
- upload success followed by cleanup failure preserves enough state for safe recovery;
- dependent resources use the new identity.
