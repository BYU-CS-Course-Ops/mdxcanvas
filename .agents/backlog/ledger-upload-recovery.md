# Recover from failed checksum-ledger uploads

## Motivation

MDXCanvas updates the in-memory `_md5sums.json` ledger after successful Canvas mutations and uploads the ledger at the end of deployment. If Canvas mutations succeed but the final ledger upload fails, Canvas and the remote ledger diverge. Newly created Canvas identities may be lost from the remote ledger, so immediately rerunning deployment can create duplicates or misclassify resources.

The existing system has operated without durable recovery, so this work is intentionally deferred from the deployment-action refactor.

## Proposed design

Before attempting the final Canvas ledger upload, retain enough information to write the exact intended ledger as a durable recovery artifact if upload fails.

On failure:

1. Write the intended ledger and target metadata atomically to the process's current working directory.
2. Use a clear UTC-timestamped filename containing the course ID, such as `mdxcanvas-ledger-recovery-course-12345-20260903T194530Z.json`.
3. Avoid overwriting an existing file and use user-only permissions where supported.
4. Record a `ledger_persistence` error containing the absolute recovery path.
5. Explain that Canvas changed but its remote ledger did not, and warn against rerunning deployment before restoring consistency.
6. Print the exact recovery command without putting credentials on the command line.

The recovery artifact should be a wrapper rather than a bare `_md5sums.json`. It should contain:

- the exact intended ledger payload;
- configured Canvas API host;
- Canvas course ID;
- MDXCanvas version;
- UTC creation time;
- source deployment-report path when available.

It must not contain API credentials, signed/private URLs, student data, or other secrets.

## Recovery command

Provide a supported command:

```bash
mdxcanvas upload-ledger \
  --course-info /reviewed/path/course-info.yaml \
  /absolute/path/to/ledger-recovery.json
```

`upload-ledger` should:

- read the token only from `CANVAS_API_TOKEN`;
- validate the artifact schema and ledger payload before connecting;
- require artifact host/course ID to match course-info;
- fetch and display the live Canvas course identity;
- proceed without an interactive prompt once artifact, course-info, and live target agree;
- upload or replace only the canonical `_md5sums.json` in its expected Canvas location;
- avoid rendering source, migrations, cleanup, and resource handlers;
- read the uploaded ledger back and verify that it matches the recovery payload;
- use the same canonical serializer and persistence implementation as ordinary deployment;
- report structured success or failure;
- leave the local recovery artifact intact after success for operator-controlled removal.

Invoking this narrowly scoped command after three-way target validation is explicit authorization. Operational documentation should still require exact target verification before use.

## Tests

Cover at minimum:

- atomic recovery-artifact creation after final upload failure;
- clear absolute recovery path with no secrets in output;
- malformed artifact rejection before Canvas access;
- host/course mismatch rejection before mutation;
- upload of only the canonical ledger;
- read-back payload verification;
- artifact retention after successful recovery;
- structured handling of another upload failure.
