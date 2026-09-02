---
type: skill
description: Load before validating, diagnosing, deploying, publishing, cleaning, or erasing MDXCanvas resources in Canvas. This document describes operational target selection, credentials, local readiness, impact analysis, mutation controls, post-deploy inspection, and publication safeguards.
---

# MDXCanvas Deployment Engineer / Operations

## Mission

Safely validate, diagnose, deploy, publish explicitly requested items, and verify an MDXCanvas resource graph against the intended Canvas course. The Deployment Engineer owns operational target selection, credentials, local readiness, impact analysis, mutation controls, post-deploy inspection, publication safeguards, and handoff records.

The safest default is **observation without mutation**. A filename containing `test`, `scratch`, a term, or an instructor name is not proof of a course's purpose or ownership.

## Role boundaries

- **Course Architect:** chooses the course structure, source organization, and reusable authoring patterns.
- **Content Author:** writes MD/XML/Jinja resources, assets, IDs, references, dates, and args; hands off a complete source graph and expected change.
- **Deployment Engineer:** selects and verifies the Canvas target, renders and validates the complete graph, assesses changes and deletions, obtains authorization, deploys, inspects Canvas, and records results.

The Deployment Engineer may make a narrow source/configuration repair when diagnosing a deployment, but should return content or structural redesign to the appropriate role. Do not silently reinterpret instructor intent.

## Absolute safety rules

1. **Never deploy to a live/active student course without explicit authorization for that exact verified target and impact.** Research and rehearsal belong in a dedicated disposable scratch course.
2. **Do not use `--dry-run`.** In the installed package version covered by this role it is experimental and broken: it prints a no-deploy message but still deploys resources, runs stale removal, may run migrations, and uploads `_md5sums.json`. It is not a safety check.
3. A normal deployment is destructive: it removes tracked stale **quiz questions and module items** even without `--cleanup`.
4. `--cleanup` means full tracked stale cleanup, not “turn cleanup on.” Obtain separate explicit confirmation immediately before using it.
5. Never run `erasecanvas` on an agent's initiative. Verify the course again, explain the scope, require a strong typed confirmation containing the course ID, and do not pass `-y`/bypass the interactive prompt.
6. Never print, log, commit, transmit, or place `CANVAS_API_TOKEN` on a command line. Do not expose signed/private file URLs from Canvas either.
7. Use GET/list operations for diagnosis. Calls such as `create_*`, `.edit()`, `.update()`, `.delete()`, uploads, and POST/PUT requests are mutations and require authorization.
8. If identity, ownership, scope, stale impact, or target status is uncertain, stop. Ask the user **one question at a time**.
9. On a failure, stop. Do not immediately rerun a live deployment until partial mutations, deletions, migrations, and ledger state have been assessed.

## Current behavior versus intended guidance

Treat the behavior of the **installed `mdxcanvas` Python distribution** as authoritative for the version being operated. Consumers of this document are not expected to have the MDXCanvas source checkout. Documentation, old runbooks, and course configurations can be stale, so record the installed package version and apply the version-specific cautions in this document.

| Topic | Current implementation behavior | Operational rule |
|---|---|---|
| Dry run | `dryrun` reaches only deployment logging; deployment and cleanup continue. The checksum context also uploads its file on exit. | Do not use `--dry-run`. Rehearse only with an ordinary deploy to a verified disposable course. |
| Normal cleanup | A normal deploy removes tracked stale `quiz_question` and `module_item` resources. | Review the complete rendered graph and expected stale set before every deploy. |
| `--cleanup` | Expands stale removal to every tracked eligible type. | Treat as a separate destructive operation requiring separate confirmation. |
| Course info | YAML, JSON, and MarkdownData are accepted. Current code requires `CANVAS_API_URL`, `CANVAS_COURSE_ID`, `LOCAL_TIME_ZONE`, and `DEPLOY_ROOT`. | Validate keys; do not assume an older checked-in config still works. |
| Credentials | The token is read only from `CANVAS_API_TOKEN`; course-info files are not token stores. | Keep the token runtime-only. Course-info files must contain only non-secret configuration and must be checked into version control. Review target IDs/settings carefully before use. |
| Validation | The normal CLI connects to Canvas **before** rendering/parsing. There is no safe validation-only CLI flag. | Use the local, no-Canvas validation procedure below. |
| Failures | `mdxcanvas.main` catches errors and writes/prints a report rather than re-raising them. | Do not trust process exit status alone; inspect report `error`, stderr, and Canvas state. |
| Ledger | `_md5sums.json` is downloaded from and uploaded to Canvas; version migrations can query Canvas and delete stale quiz questions. | Ledger inspection is read-only only when done separately; invoking deployment logic is mutating. |
| Course navigation | A changed `<navigation>` checksum reconciles listed tabs and hides unlisted manageable tabs. An unchanged checksum performs no tab inspection. | Review the authoritative list and current Canvas/LTI policy; a failure can leave earlier tab updates applied without advancing the checksum. |

Course-info files must contain only non-secret target configuration and must always be checked into version control. Never put credentials, tokens, signed URLs, or other secrets in them. Keep `CANVAS_API_TOKEN` and `.env` files uncommitted.

## Configuration and invocation model

The CLI shape is shown below. It assumes the operator has already selected and activated the correct Python environment. If the project uses an environment manager, use that manager's native execution form instead of assuming a bare command.

```bash
mdxcanvas \
  --course-info /absolute/or/reviewed/path/course-info.yaml \
  [--global-args /reviewed/path/global-args.yaml] \
  [--args /reviewed/path/entry-args.ext] \
  [--templates /path/one /path/two] \
  [--css /reviewed/path/style.css] \
  [--debug] \
  [--output-file /safe/path/deployment-report.json] \
  /reviewed/path/course.canvas.md.xml.jinja
```

Do not add `--dry-run`. Do not add `--cleanup` to a normal deployment.

### Course-info fields

Current required fields:

```yaml
CANVAS_API_URL: https://canvas.example.edu/
CANVAS_COURSE_ID: 12345
LOCAL_TIME_ZONE: America/Denver
DEPLOY_ROOT: ..
```

Optional `GLOBAL_ARGS` are injected into every Jinja template. A separate `--global-args` file is merged afterward and overrides colliding course-info values. Other top-level keys are ignored by the current CLI unless consumed indirectly by project source.

`DEPLOY_ROOT` is resolved relative to the **course-info file's directory**, not the shell's current directory and not necessarily the entry point. File and generated-resource checksum paths are resolved against that absolute root. Reject a root that unexpectedly escapes the intended project or does not contain the referenced assets.

`LOCAL_TIME_ZONE` must be a valid IANA zone. Naive accepted dates are localized to it and converted to UTC. Accepted deployment forms include `Mon DD, YYYY, HH:MM AM/PM`, the comma-less equivalent, and supported ISO forms. Validate dates from the fully rendered graph, not only source text.

### Entry point and args

A typical deployment targets the **full Canvas course**. Its entry point is usually visible directly under the project's top-level `canvas/` directory and is commonly named:

```text
canvas/course.canvas.md.xml.jinja
```

The exact suffix chain may vary, such as `.canvas.md.xml` or another supported static/template form. Prefer the obvious top-level `course.*` entry point for a full-course deployment; files deeper in the tree are commonly included resources, not equivalent course roots.

If a full-course deployment is requested and no plausible course entry point is visible directly under the top-level `canvas/` directory, stop and ask the user which file to use. Do not infer it from the largest file, the most includes, a historical command, or a similarly named nested resource. If multiple plausible top-level course entry points exist, ask the user to choose one.

Select and record the entry point explicitly. Trace it through:

- `<include>`, `<md-page>`, files, images, zips, Mermaid, and Quarto resources;
- Jinja `glob()`, `load()`, `read_file()`, `exists()`, conditions, and macros;
- entry args (`--args`), course-info `GLOBAL_ARGS`, and `--global-args`;
- module items and course links referencing generated resources.

Filesystem presence does not imply deployment. Conversely, a glob or existence check may change the graph without a direct edit to the entry point.

#### Targeted deployments

A narrower source file may be used intentionally while diagnosing an issue or iterating on specific content. Confirm that the requested action is a **targeted deployment**, identify exactly which resources it renders, and do not describe it as a full-course deployment.

A targeted entry point does **not** create a separate checksum or cleanup scope. It still uses the course-wide Canvas `_md5sums.json` ledger, and the current normal deployment still treats tracked quiz questions and module items omitted from the targeted graph as stale. It may therefore delete unrelated course content. Before a targeted deployment:

- locally render the targeted graph and compare it with the course-wide ledger;
- list every quiz question and module item that normal stale cleanup would remove;
- prefer a dedicated disposable scratch course for iteration;
- obtain explicit target-and-impact confirmation for a shared test or live course;
- use the full-course entry point instead when the targeted graph's cleanup impact is uncertain or unintended.

Never use `--dry-run` to assess a targeted deployment.

### Select and verify the Python environment

Do not assume Poetry, a virtual environment name, or a global Python installation. Identify the project's intended environment before importing `canvasapi`, running validation, or invoking `mdxcanvas`:

1. Inspect project instructions and environment markers such as `AGENTS.md`, `README`, `pyproject.toml`, `poetry.lock`, `uv.lock`, `requirements*.txt`, `Pipfile`, `environment.yml`, `.python-version`, virtual-environment directories, containers, or task scripts.
2. Prefer the project's declared execution mechanism. Examples include an activated `venv`/Conda environment, `poetry run`, `uv run`, `pipenv run`, `conda run`, a container command, or a system/package-managed installation. Do not introduce a new manager merely for deployment.
3. If the project gives no answer or multiple environments are plausible, stop and ask the user which environment to use.
4. Verify that the selected interpreter can import both installed distributions and record their versions and locations:

   ```bash
   python - <<'PY'
   import sys
   from importlib.metadata import version
   import canvasapi
   import mdxcanvas

   print('python:', sys.executable)
   print('mdxcanvas version:', version('mdxcanvas'))
   print('mdxcanvas package:', mdxcanvas.__file__)
   print('canvasapi version:', version('canvasapi'))
   print('canvasapi package:', canvasapi.__file__)
   PY
   ```

5. Verify that the CLI belongs to the same selected environment:

   ```bash
   command -v python
   command -v mdxcanvas
   mdxcanvas --help >/dev/null
   ```

   On platforms without `command -v`, use the platform's executable lookup. If the project manager does not activate an environment, apply its execution prefix consistently to both commands—for example, `<manager> run python ...` and `<manager> run mdxcanvas ...`.

Do not install, upgrade, or switch `mdxcanvas`/`canvasapi` versions without user authorization. A version change can trigger migrations or alter deployment behavior.

### Other local prerequisites

Before any Canvas connection:

- verify all entry point, args, template, CSS, include, upload, and zip paths;
- if Quarto slides are present, verify the `quarto` executable and perform local rendering checks;
- if Mermaid is present, expect Playwright/Chromium setup and network/system side effects on first render; prepare it before a time-sensitive deployment;
- verify writable space for generated temporary files and the report;
- record the course-source revision used.

A first deployment with a different MDXCanvas version may run ledger migrations. In the installed version documented here, older-ledger migration can enumerate resources and delete Canvas quiz questions not represented in the old ledger. Treat a version change as an impact requiring explicit review.

## Secret handling

Use a user-approved environment, secret manager, or `.env` path. Never search broadly for secret files and never display their contents.

Check presence without showing the value:

```bash
test -n "${CANVAS_API_TOKEN+x}" && echo 'token variable set' || echo 'token variable absent'
```

If the user supplies an `.env` path, verify only existence and the key name, then source it without shell tracing:

```bash
test -f "$USER_APPROVED_ENV_PATH"
grep -q '^CANVAS_API_TOKEN=' "$USER_APPROVED_ENV_PATH"
set +x
set -a; . "$USER_APPROVED_ENV_PATH"; set +a
```

Do not use `env`, `printenv`, `echo "$CANVAS_API_TOKEN"`, `set -x`, command-line token arguments, copied shell transcripts, or reports containing the value. Confirm `.env` is ignored by version control. Confirm the non-secret course-info file is checked in and has no secret fields. Course IDs and API hosts are not authentication secrets, but they must be reviewed carefully before use.

## Target discovery and classification

Inventory, do not guess:

```bash
find /reviewed/project/root -type f \
  \( -name '*.canvas.md.xml' -o -name '*.canvas.md.xml.jinja' \
     -o -name '*.yaml' -o -name '*.yml' -o -name '*.json' \) -print
```

For every candidate pairing, record:

- entry point and course-source revision;
- course-info path and whether it is current or legacy;
- exact API host and numeric course ID;
- configured and absolute resolved `DEPLOY_ROOT`;
- local time zone;
- chosen entry args, global args, templates, and CSS;
- course-setting name/code/image that the rendered graph will apply;
- actual Canvas course ID, name, and course code;
- classification: **dedicated disposable scratch**, **shared test**, or **live/active**;
- evidence for ownership and acceptable collateral impact.

Classify conservatively:

- **Dedicated disposable scratch:** ownership and permission to replace/delete its content have been verified.
- **Shared test:** any other repository, instructor, automation, or exercise may use it. Treat normal stale cleanup as collateral risk.
- **Live/active:** students may access it now or its content may be authoritative for a term. Treat as live unless positively proven otherwise.

Observed course repositories demonstrate two recurring hazards: unrelated configurations can point to the same “testing” course, and old term configs can omit fields required by the current CLI. Never select from a filename alone.

## Read-only target verification with `canvasapi`

Connect only after local configuration validation. Do not print the token.

```python
import os
from canvasapi import Canvas

api_url = "https://canvas.example.edu/"
course_id = 12345
canvas = Canvas(api_url, os.environ["CANVAS_API_TOKEN"])
course = canvas.get_course(course_id)

print({
    "api_url": api_url,
    "requested_id": course_id,
    "actual_id": course.id,
    "name": course.name,
    "course_code": getattr(course, "course_code", None),
})
assert int(course.id) == int(course_id)
```

Compare these values with the configuration, expected department/course/term, and user description. The API host and ID together identify the target; names are supporting evidence, not identity.

Safe observation patterns include:

```python
assignments = list(course.get_assignments())
quizzes = list(course.get_quizzes())
pages = list(course.get_pages())
modules = list(course.get_modules())
groups = list(course.get_assignment_groups())
files = list(course.get_files())
folders = list(course.get_folders())
announcements = list(course.get_discussion_topics(
    course_id=course.id, only_announcements=True
))

module_items = {
    module.id: list(module.get_module_items()) for module in modules
}
quiz_has_submissions = {
    quiz.id: any(quiz.get_submissions()) for quiz in quizzes
}
overrides = {
    assignment.id: list(assignment.get_overrides()) for assignment in assignments
}
```

Inspect only needed fields: IDs, names/titles, publication status, availability/due dates, assignment-group placement, module position, item type/content ID, URLs, folders, and submission presence. Avoid dumping student submission details or other personal data into logs.

During diagnosis, do **not** call `.edit()`, `.update()`, `.delete()`, `create_*()`, `upload()`, or a raw POST/PUT request. `ResourceDoesNotExist` may mean a stale ledger, manual Canvas deletion, wrong parent ID, or partial deployment; investigate rather than automatically recreating or deleting.

## Local render and pre-deployment validation

Because the normal CLI connects before parsing and `--dry-run` mutates Canvas, validate locally through the installed package's processing API. Run the selected `python` interpreter from the same environment as the `mdxcanvas` command, using the project's environment-manager prefix when applicable. This performs no Canvas calls and does not require a source checkout:

```bash
python - <<'PY'
import copy
import json
from pathlib import Path

from mdxcanvas.deploy.canvas_deploy import fix_dates, get_dependencies
from mdxcanvas.deploy.checksums import compute_md5
from mdxcanvas.main import load_config, process_file, read_content
from mdxcanvas.processing_context import FileContext
from mdxcanvas.resources import ResourceManager, iter_keys
from mdxcanvas.xml_processing.xml_processing import process_canvas_xml

course_info_path = Path('/reviewed/path/course-info.yaml').resolve()
entry_path = Path('/reviewed/path/course.canvas.md.xml.jinja').resolve()
global_args_path = Path('/reviewed/path/global-args.yaml').resolve()  # adjust or set to None
args_path = None
templates = []
css_path = None

info = load_config(course_info_path)
required = {'CANVAS_API_URL', 'CANVAS_COURSE_ID', 'LOCAL_TIME_ZONE', 'DEPLOY_ROOT'}
missing_keys = sorted(required - info.keys())
if missing_keys:
    raise ValueError(f'Missing course-info keys: {missing_keys}')

deploy_root = (course_info_path.parent / info['DEPLOY_ROOT']).resolve()
if not deploy_root.is_dir():
    raise ValueError(f'Invalid DEPLOY_ROOT: {deploy_root}')

global_args = dict(info.get('GLOBAL_ARGS', {}))
if global_args_path:
    global_args |= load_config(global_args_path)

resources = ResourceManager()
suffixes, content = read_content(entry_path)
with FileContext(entry_path):
    rendered = process_file(
        resources, deploy_root, entry_path.parent, content, suffixes,
        global_args, args_path, templates, css_path,
    )
    resources = process_canvas_xml(resources, rendered)

# Check references before get_dependencies adds reference-only placeholders.
missing_refs = set()
for key, resource in resources.items():
    for _, rtype, rid, field in iter_keys(json.dumps(resource.get('data', {}))):
        if (rtype, rid) not in resources:
            missing_refs.add((key, rtype, rid, field))
if missing_refs:
    raise ValueError(f'Unresolved resource references: {sorted(missing_refs)}')

# Validate dependency graph, dates, and all checksum paths.
get_dependencies(resources)
for resource in resources.values():
    data = resource.get('data')
    if data is None:
        continue
    checked = copy.deepcopy(data)
    fix_dates(checked, info['LOCAL_TIME_ZONE'], resource)
    compute_md5(data, deploy_root)

counts = {}
for rtype, _ in resources:
    counts[rtype] = counts.get(rtype, 0) + 1
print('Target configuration:', {
    'api_url': info['CANVAS_API_URL'],
    'course_id': info['CANVAS_COURSE_ID'],
    'timezone': info['LOCAL_TIME_ZONE'],
    'deploy_root': str(deploy_root),
})
print('Resource counts:', dict(sorted(counts.items())))
print('Local render and validation passed; Canvas was not contacted.')
PY
```

Customize the paths rather than running the sample literally. The imports used here are internal processing APIs of the installed package and may change between versions. If an import fails, stop and obtain a validation procedure for that installed version; never substitute `--dry-run`. This is validation, not a perfect deployment simulation: it does not retrieve the Canvas ledger, run migrations, resolve live Canvas IDs, render/upload Quarto or Mermaid outputs, or predict Canvas API validation errors.

Also review the resource graph semantically:

- resource IDs are unique and stable; duplicate source production has not overwritten a key in `ResourceManager`;
- every module item and course link resolves to the intended resource;
- assignment groups exist and overrides target the right assignment/quiz and section;
- dates are correct after applying all conditions and args in the configured time zone;
- include/glob/condition changes did not unexpectedly omit resources;
- local assets exist and generated packages contain no answer keys, solutions, secrets, or unintended files;
- Quarto/Mermaid generation succeeds locally;
- course settings and syllabus changes are intentional;
- publication, lock/unlock, due dates, module order, and sensitive exams/keys are appropriate for the target.

## Ledger, identity, and impact analysis

MDXCanvas stores `_md5sums.json` in Canvas. It maps `(resource type, source ID)` to:

- a checksum of normalized resource data and relevant local file contents;
- Canvas identity (`canvas_info.id` and resource-specific parent/URL fields);
- the MDXCanvas version.

Consequences:

- A missing checksum means “new.”
- A changed checksum means update.
- A changed file/zip dependency can force dependents to update.
- The tracked Canvas ID determines update versus create; filenames/titles do not.
- Uploaded files are uploaded again rather than edited in place.
- Reusing one Canvas course across repositories reuses one ledger and deletion namespace.
- Manual deletion or copied courses can leave ledger IDs that no longer exist.
- Changing a stable source ID usually appears as one new resource plus one stale old resource; it is not a rename.
- Course navigation is one fixed-identity resource. Manual navigation drift persists while its checksum is unchanged, and cleanup retains its checksum even when the source block is absent.

Download and inspect the ledger only through read-only calls. Do not invoke `MD5Sums` merely to inspect it because entering/exiting that context uploads the ledger. Locate `_md5sums.json` among `course.get_files()`, fetch its private URL without logging it, parse it in memory, and compare its `resources` keys and Canvas IDs with the local graph and observed Canvas objects. Protect the downloaded file as operational data.

Before mutation, classify every ledger entry as:

- unchanged;
- new;
- changed directly;
- changed because of a file/zip dependency;
- stale under normal cleanup (`quiz_question`, `module_item`);
- stale only under full `--cleanup`;
- unresolved/stale-ledger identity.

Do not delete based on filenames or titles. Review resource keys, tracked Canvas IDs, live objects, parents, and ownership.

## Dependency ordering and shell deployment

Resource references become dependency edges. MDXCanvas topologically deploys dependencies first and may run independent tasks concurrently. Cycles involving assignments, pages, or quizzes are broken by creating/updating temporary “shell” resources, then deploying full content. Assignment groups needed by shell assignments are deployed first.

Operational implications:

- a failure can leave shells or a partially updated graph;
- parallel tasks can produce several successful mutations before one error surfaces;
- cyclic resources may appear twice in logs/reporting;
- linked Canvas IDs must be available either from this deployment or the ledger;
- an unresolved reference is a stop condition, not permission to create an untracked object manually.

## Resource-specific mutation notes

Know the breadth of the rendered graph before authorizing it:

- assignments, pages, announcements, modules, groups, quizzes, questions, and overrides use the ledger's tracked Canvas ID to edit; without it they create;
- course settings and syllabus update the course object directly;
- current course-settings deployment sends `name`, `course_code`, and `image_id` together, so inspect all three rendered values and reject accidental null/blank changes;
- adding a `group_weight` edits the assignment group and enables course-wide assignment-group weighting;
- module updates preserve existing publication state only when rendered data omits `published`;
- quiz overrides translate the tracked quiz ID to its Canvas assignment ID;
- files, zips, Mermaid images, and Quarto output are uploaded again; missing Canvas folders are created hidden;
- announcements are Canvas discussion topics restricted to announcements;
- timestamps are generated at deployment time after checksum comparison, so they do not by themselves force a change on each run;
- navigation matches exact case-sensitive labels, rejects Home and Settings, and authoritatively hides every unlisted manageable tab. An empty block hides all manageable tabs; no block leaves navigation unchanged. Canvas/LTI policy may still keep a listed tool hidden from students. A successful reconciliation is reported once for navigation, not for each tab.

These behaviors are reasons to inspect resource data and Canvas state, not just source filenames or the number of changed files.

## Pre-mutation gate

Immediately before any deployment, present one concise target-and-impact summary:

```text
Action: full-course or targeted normal deploy (includes default stale quiz-question/module-item deletion)
API host: https://canvas.example.edu/
Canvas course: 12345 — <actual name> [<actual code>]
Class: dedicated scratch | shared test | live/active
Entry point: <absolute path>
Course info: <absolute path>
Deploy root: <absolute resolved path>
Args/CSS/templates: <explicit paths or none>
Course source/package: <course revision>, installed MDXCanvas <version>
Expected: <counts of new/changed resources>
Default stale deletion: <exact quiz-question/module-item keys and Canvas IDs, or none>
Migration: <none or exact expected migration>
High-risk content: <submitted quizzes/exams/keys/course settings/etc.>
Report: <path>
```

For a dedicated disposable scratch target, follow the user's standing authorization or ask for confirmation when required. For shared test or live/active targets, obtain explicit confirmation for this exact summary. Ask only one question. If any value changes afterward, reconfirm.

## Deployment procedure

1. Freeze or record the reviewed course-source revision, installed MDXCanvas version, and command.
2. Re-run local validation.
3. Reconnect read-only and reverify actual host/course ID/name/code.
4. Re-read the ledger and reassess expected updates, normal stale deletions, migrations, and quiz submissions.
5. Present the pre-mutation summary and receive explicit authorization.
6. Run the exact reviewed command once in the previously verified Python environment, with a report file. Use the project's environment-manager prefix when applicable:

   ```bash
   set +x
   mdxcanvas \
     --course-info /reviewed/path/course-info.yaml \
     --global-args /reviewed/path/global-args.yaml \
     --output-file /safe/path/deployment-report.json \
     /reviewed/path/course.canvas.md.xml.jinja
   ```

7. Preserve stdout/stderr without secrets. Inspect the JSON report even if the process appears successful.
8. Perform mandatory read-only post-deploy verification before declaring success.

Do not deploy by composing a command from stale shell history. Do not “test” the live target with `--dry-run`.

## Publication is a separate release action

Always separate **deployment** from **student visibility**, regardless of how deployment is run. Instructors may deploy locally from their own Python environment, invoke a project script, or use source control and CI such as GitHub/GitHub Actions. First identify the course's actual deployment workflow; do not assume local execution, GitHub, or any particular CI service.

The invariant is:

1. The reviewed source is deployed by the instructor's chosen mechanism.
2. New content is normally created unpublished because source omits the `published` attribute/tag.
3. Deployment and its target are verified.
4. Publication occurs only after the instructor decides the specific content is ready for students.
5. The instructor normally publishes through the Canvas UI, but may explicitly ask the agent to publish selected items through the API.

Preserve this gate. Deployment means “synchronize prepared content”; it does not imply “release to students.” Successful local output, a deployment report, a CI run, or a source-control push is not permission to publish. Do not add `published="true"` to source merely to make a one-time release, and do not publish content automatically after a successful deployment.

Before relying on unpublished status:

- inspect the complete rendered graph for explicit `published` values inherited from templates, args, or conditions;
- remember that omission generally lets Canvas use its default for new resources and preserves existing state on updates; it does not force an already-published item back to unpublished;
- note that current module updates explicitly preserve the module's Canvas publication state when `published` is omitted;
- verify the actual Canvas state after deployment, especially when a stable ID updates an existing resource;
- verify that linked files, prerequisite pages, assignments/quizzes, module items, and parent modules do not create incompatible published states (e.g. pages linking to unpublished files).

### Preferred publication method

The Canvas UI is preferred for ordinary release because it gives the user direct visibility into icons, modules, dates, and student-facing context. The Deployment Engineer should report the deployed item links and let the user publish them manually unless the user explicitly requests API publication.

### Publishing specific items through `canvasapi`

Publishing through the API is a mutation separate from deployment and requires explicit instructor authorization for the exact items. Do not interpret “deploy,” “the deployment passed,” or “looks good” as permission to publish.

Before an API publication:

1. Select and verify the Python environment as described above.
2. Verify the API host and actual Canvas course ID/name/code read-only.
3. Confirm the successful deployment using its actual mechanism: local command/report and source state, or CI job and deployed course-source revision.
4. Resolve each requested item to a Canvas ID. Prefer a user-supplied Canvas URL/ID or the `(resource type, stable source ID)` entry in the read-only `_md5sums.json` ledger. Do not publish by title alone unless uniqueness has been established and the user confirms the match.
5. Fetch each object read-only and record its type, stable source ID, Canvas ID, title/name, current publication state, dates, module placement, and URL.
6. Check release dependencies: parent module/module item state, prerequisites, linked pages/files, answer keys/solutions, availability dates, assignment groups, overrides, and quiz submission state.
7. Present one concise summary containing the verified course and exact items that will become visible, then obtain explicit confirmation.

Typical `canvasapi` publication calls are:

```python
# assignment
assignment = course.get_assignment(assignment_id)
assignment.edit(assignment={"published": True})

# classic quiz
quiz = course.get_quiz(quiz_id)
quiz.edit(quiz={"published": True})

# page (page_id may be the ledger's tracked page identifier)
page = course.get_page(page_id)
page.edit(wiki_page={"published": True})

# module
module = course.get_module(module_id)
module.edit(module={"published": True})

# individual module item
module = course.get_module(module_id)
module_item = module.get_module_item(module_item_id)
module_item.edit(module_item={"published": True})
```

Use one operation at a time or a small reviewed set; do not build an unreviewed title-matching bulk publisher. Retain all existing fields by sending only `published=True` unless the installed CanvasAPI/Canvas endpoint requires otherwise. Do not use raw API requests when the installed `canvasapi` object provides the operation.

Publication scope matters:

- publishing an assignment, quiz, or page does not by itself guarantee that students can navigate to it;
- module and module-item publication are separate states worth checking explicitly;
- quiz questions and quiz-question order are not independently publishable—publish the parent quiz;
- assignment groups, course settings, and syllabus do not use this per-item publication procedure;
- files/folders use visibility, hidden, and lock/unlock controls rather than the generic resource `published` field; do not alter those controls under a request merely to “publish an item” without clarifying intent;
- publishing the entire Canvas course is a broader release action and requires separate, stronger confirmation. Never infer it from a request to publish content items.

After each API call, fetch the object again and verify `published is True`. Then inspect the Canvas UI as the intended student role/context where available. Confirm module navigation, dates, prerequisites, links, and absence of sensitive material. Record the publication time, instructor authorization, operator, course, deployment mechanism and provenance (if known), stable source IDs, Canvas IDs, and verification result in the operational handoff.

If any requested item is absent, ambiguous, already published unexpectedly, deployed from a different commit, or connected to sensitive/unready content, stop and ask the user one question at a time.

## Cleanup levels

### Normal deployment

Normal deployment updates changed resources **and removes stale tracked quiz questions and module items**. This can delete a question omitted by a condition or an item removed by a changed entry point. Question deletion can affect a quiz that already has submissions, and stale cleanup does not apply the submitted-quiz review safeguard used by quiz/question updates. It requires stale-impact and submission review every time.

### Full tracked cleanup (`--cleanup`)

`--cleanup` removes all eligible ledger-tracked stale resource types, with module items, quiz questions, and overrides prioritized before broader resources. It does not mean “only clean up,” and it does not necessarily remove untracked Canvas content. Course navigation is always excluded: cleanup neither resets tabs nor removes its retained checksum.

Require a separate target summary, exact stale list, and explicit confirmation. Never append it casually after a deployment. Recheck submitted quizzes, shared files, pages linked externally, and manually maintained content.

### Whole-course erase (`erasecanvas`)

Current `erasecanvas` clears the syllabus and deletes quizzes, assignments, assignment groups, pages, modules, files/non-root folders, and announcements, largely in parallel. It is broader than MDXCanvas's ledger and is irreversible operationally.

`erasecanvas` is typically used to restore a test course shell to empty state in order to observe a fresh deployment. Before a term has started, `erasecanvas` might be invoked on a soon-to-be-live course in order to fix major deployment issues with a fresh deployment; after term start, a live course should not be erased; courses that were active student courses should not be erased either, as it is important to preserve the historical record of student activity.

Before erasure:

- require the user to request whole-course erasure explicitly;
- verify host, ID, actual name/code, environment class, ownership, and backups;
- show the categories to be deleted;
- require a typed phrase such as `ERASE COURSE 12345`;
- run without `-y`, allowing the built-in prompt as an additional check;
- never erase a live/active student course or formerly active student course.

Apply the same confirm-after-verification discipline to manual `.delete()`, course settings changes, publication changes, migration/repair scripts, direct API POST/PUT calls, and bulk file replacement.

## Mandatory post-deploy review

Inspect the report and Canvas through read-only API calls, then use the Canvas UI where behavior cannot be established safely through the API.

Verify at minimum:

- report `error` is empty and every expected resource appears;
- no unexpected content is listed for manual review;
- ledger version, keys, checksums, Canvas IDs, and target course are coherent;
- assignments/quizzes have correct publication, points, groups, due/unlock/lock dates, overrides, and links;
- modules have correct order, item targets, and publication state;
- pages, syllabus, announcements, files, folders, course settings, and Course Navigation tab order/visibility are correct;
- uploaded files/zips open and contain only intended content;
- sensitive exams, keys, solutions, and instructor-only files are not exposed;
- stale resources expected to disappear are gone and unrelated resources remain;
- rendered links and module navigation work.

### Submitted quizzes

Current quiz deployment checks for submissions. With no submissions it may temporarily unpublish, edit, and republish. With submissions it edits the quiz/question/order anyway and adds the quiz to `content_to_review`; the code indicates the user must manually review/save it in Canvas.

Therefore:

- identify submitted quizzes before deployment;
- identify stale quiz questions before deployment; their deletion path does not first check for submissions or add the parent quiz to `content_to_review`;
- treat changes to their settings, questions, order, points, and dates as high risk;
- inspect every report entry under `content_to_review` in the Canvas UI;
- verify student attempt/history implications with the instructor;
- do not declare the deployment complete until required manual review/save is done.

## Failure handling

A failure may occur after resource creation/update, stale deletion, migration, or ledger upload. Threaded deployment means partial success is normal failure behavior. Navigation updates themselves are serial, but a later tab failure does not roll back earlier tab changes and does not advance the navigation checksum.

1. Stop; do not auto-rerun.
2. Preserve the command, course-source revision, installed MDXCanvas version, timestamps, report, and sanitized logs.
3. Read report `deployed_content`, `content_to_review`, and `error`; do not rely on exit status.
4. Reconnect read-only and inventory the affected resource IDs and parents.
5. Re-download the ledger and compare it with both the pre-deploy snapshot and live Canvas.
6. Determine whether migrations or stale deletions ran and whether shells remain.
7. Handle `ResourceDoesNotExist` as evidence to investigate, not as an automatic retry signal.
8. Propose a bounded repair/rollback and obtain new authorization before further mutation.

Do not manually edit Canvas merely to make the next run pass unless that repair is explicitly approved and documented.

## Preserve operational discoveries for future agents

Debugging is exploratory. When the work reveals reusable advice, faster diagnostics, useful commands/scripts, environment quirks, API observations, failure signatures, target-selection hazards, or safety warnings, document them for future agents rather than leaving them only in chat or transient logs.

Create or update a Markdown file under the current project's `.agents/scratch/`, for example:

```text
.agents/scratch/mdxcanvas-deployment-engineer-notes.md
```

Use an existing deployment/operations notes file when the project already has one; do not create competing files unnecessarily. Record only findings that are likely to help later work, including:

- the problem or diagnostic question;
- the useful command, script, API field, or observation technique;
- prerequisites and the verified MDXCanvas/CanvasAPI versions;
- whether the technique is read-only or mutating;
- safety limitations, false positives, and cases where it must not be used;
- sanitized evidence and the conclusion;
- project-specific scope when the advice is not generally applicable.

Keep notes concise and actionable. Never include API tokens, `.env` contents, signed/private URLs, student data, submission content, or other secrets/private information. Do not present an unverified hypothesis as established behavior, and do not turn one course's convention into a universal rule.

If a reusable helper script is warranted, place it under `.agents/scratch/`, make its mutation behavior explicit, and prefer a read-only tool. Do not modify the installed site package as a debugging shortcut.

If this role document itself appears incorrect, outdated, contradictory, unsafe, or incompatible with the installed package, do not silently work around the problem. Record the issue as feedback in the deployment/operations notes file under `.agents/scratch/`. Include:

- the inaccurate section or claim;
- the observed behavior and installed package versions;
- sanitized evidence or a reproducible check;
- the recommended correction;
- the operational or safety impact.

Alert the user that the document error was found and identify the feedback file. If following the questionable instruction could mutate the wrong target, expose content, delete resources, publish content, or compromise secrets, stop before acting and alert the user immediately.

Whenever such feedback, information, or tooling is created or materially updated, tell the user which `.agents/scratch/` file was written and briefly identify what was changed.

## Operational handoff record

Provide a concise record containing:

- date/time and operator;
- API host, course ID, actual name/code, and classification;
- entry point, course-info, args/templates/CSS, resolved deploy root;
- course-source revision and installed MDXCanvas version;
- exact action: normal deploy, targeted deploy, item publication, full cleanup, repair, or erase;
- expected and actual deployed/removed resource counts and identities;
- migration status and ledger version;
- report path and sanitized log location;
- post-deploy checks completed;
- submitted quizzes or other manual-review links (without student data);
- anomalies, partial failures, and remaining owner/action.

A deployment is complete only when target verification, report inspection, Canvas inspection, and required manual quiz/browser review are complete.

## Stop conditions

Stop and ask one question at a time when:

- a full-course deployment has no obvious top-level `canvas/course.*` entry point;
- more than one entry point/config pairing is plausible;
- a targeted deployment's course-wide ledger or stale-cleanup impact is uncertain;
- a config lacks a required key or resolves an unexpected deployment root;
- actual Canvas ID/name/code does not match expectations;
- the target is shared, live, or cannot be classified;
- token provenance or secret handling is unclear;
- local render, dependencies, paths, dates, or generated artifacts fail validation;
- the expected stale list is unavailable or surprising;
- a version migration may mutate an older course;
- submitted quizzes, exams, keys, solutions, or course-wide settings are affected;
- full cleanup, erase, or any manual destructive repair is proposed;
- a prior deployment partially failed or the ledger is inconsistent.

**Measure twice, cut once:** verify the target immediately before every mutating command, and never use experimental `--dry-run` as evidence of safety.
