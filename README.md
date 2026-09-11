# MDXCanvas

**MDXCanvas** allows you to define Canvas course content using source files (`.md`, `.xml`, `.jinja`, etc.) and deploy it programmatically to a Canvas instance via the API.

## Installation

Install via pip:

```bash
pip install mdxcanvas
```

You must also create a **Canvas API Token** from your Canvas account settings and store it as an environment variable:

```bash
export CANVAS_API_TOKEN="your_token_here"
```

## Usage

To deploy content to Canvas, run:

```bash
mdxcanvas --course-info <course_info.yaml> <content_file>
```

### `course_info`

A configuration file specifying course deployment details. Supported formats:

- **YAML** (`.yaml`, `.yml`) - Recommended
- **JSON** (`.json`)
- **MarkdownData** (`.md`, `.mdd`)

The file must include:

- `CANVAS_API_URL`
- `CANVAS_COURSE_ID`
- `LOCAL_TIME_ZONE`
- `DEPLOY_ROOT`

Example (YAML):

```yaml
CANVAS_API_URL: https://byu.instructure.com/
CANVAS_COURSE_ID: 12345
LOCAL_TIME_ZONE: America/Denver
DEPLOY_ROOT: ..
```

For more information, and extended options like `GLOBAL_ARGS`, see the
[Course Info Guide](documents/course_info.md).

### `content_file`

The content file defines what will be pushed to Canvas. Supported formats:

- `.md`
- `.xml`
- `.html`
- `.jinja`

Example (`.xml` quiz):

```xml
<quiz id="hp_quiz" title="Example Quiz">

    <description>
        # Attention

        The following questions test your knowledge of the wizarding world of **Harry Potter**.
    </description>

    <questions>
        <question type="multiple-choice">
            Who is the author of the Harry Potter series?

            <correct answer_comments="Correct">J.K. Rowling</correct>
            <incorrect answer_comments="Tolkien wrote The Lord of the Rings">J.R.R. Tolkien</incorrect>
            <incorrect>George R.R. Martin</incorrect>
            <incorrect>Stephen King</incorrect>
        </question>

        <question type="true-false" answer="true"
                  correct-comments="Correct" incorrect-comments="Harry is a wizard.">
            Is Harry Potter a wizard?
        </question>
    </questions>
</quiz>
```

As shown above, Markdown formatting is supported within content.

See the [Demo Course](demo-course) for complete examples.

## Command-Line Options

The `mdxcanvas` command supports the following options:

- `--course-info <file>` - Path to course configuration file (YAML/JSON/MarkdownData)
- `--args <file>` - Path to template arguments file (for Jinja templates)
- `--global-args <file>` - Path to global arguments file (merged with `GLOBAL_ARGS` from course_info)
- `--templates <files>` - List of template files to import
- `--css <file>` - Path to CSS file for styling
- `--debug` - Enable debug logging
- `--dryrun` or `--dry-run` - Build and report the deployment plan without mutating Canvas or the ledger
- `--no-cleanup` - Keep tracked resources omitted from this invocation (recommended for targeted deployments)
- `--output-file <file>` - Save the nested JSON deployment report to the specified file

Source is authoritative by default: omitted tracked resources are stale. Most are deleted from Canvas; course settings, navigation, quiz-question order, and syllabus are untracked without changing Canvas. `--no-cleanup` suppresses all stale handling. Reports separate processing failures from planned and completed deployment changes. Either kind of failure produces a nonzero exit status.

Both dry-run and deployment immediately log a grouped planned-action summary by resource type, separated into create, update, delete, and untrack. The total counts planned action nodes, so supported shell/full cycle actions are counted separately. Live deployment then logs concise completion progress such as `1338/1344: create quiz_question_order lab0a|order`; completion order may differ from report order. It ends with elapsed successful, failed, and blocked counts. Dry-run emits no action-completion or deployment-completion records. The JSON report remains deterministically ordered.

After deployment, the human report groups successful actions that share a Canvas URL, including authenticated file links. Resources without a dedicated URL are grouped under the course URL. Attempted failures include action, resource, source, and redacted error context. Blocked resources are omitted individually and summarized once as `X resources not deployed`; inspect the JSON report for their individual records. During dry-run, the human report lists expected changes instead.

Ledger loading is read-only. A missing ledger starts in memory, and supported older ledgers are migrated as needed. If the recorded ledger version is newer than the running package, both dry-run and deployment stop before interpreting it. Upgrade MDXCanvas to at least the recorded version before retrying. If deployment is interrupted with Ctrl-C, MDXCanvas waits for active deployment calls to finish, makes one best-effort save of completed ledger state, and then propagates the interrupt. Because saving is best-effort, inspect Canvas, the report, and the ledger before rerunning an interrupted deployment.

Example with options:

```bash
mdxcanvas --course-info course.yaml \
          --global-args globals.yaml \
          --css styles.css \
          --dryrun \
          --no-cleanup \
          content.xml
```

The JSON report has this shape:

```json
{
  "processing": {"error": ""},
  "deployment": {
    "mode": "deploy",
    "cleanup": "enabled",
    "expected_changes": [
      {"change": "modified", "resource_type": "quiz", "resource_id": "chapter-check"}
    ],
    "changes_made": [
      {
        "change": "modified",
        "resource_type": "quiz",
        "resource_id": "chapter-check",
        "outcome": "updated",
        "url": "https://canvas.example/courses/1/quizzes/2",
        "review": {"name": "Chapter check", "url": null}
      }
    ],
    "content_to_review": [
      {"resource_type": "quiz", "name": "Chapter check", "url": null}
    ],
    "errors": []
  }
}
```

`content_to_review` is always present, including in dry-run and error reports. A successful change requires manual review only when it has a `review` object; there is no separate boolean flag. A review URL may be `null`. The change's `url` describes the deployment outcome and may differ from the review URL.

The review summary follows deterministic plan order. Every applicable change retains its own `review` object, while `content_to_review` retains only the first entry with the same resource type, name, and URL.

## Python API

Applications that call `mdxcanvas.main.main` can use the same options as the CLI. The cleanup argument is `no_cleanup` and defaults to `False`; the former `cleanup` argument is not supported.

```python
from pathlib import Path
from mdxcanvas.main import main

report = main(
    canvas_api_token=token,
    course_info_file=Path("course.yaml"),
    input_file=Path("content.xml"),
    dryrun=True,
    no_cleanup=True,
)
if report.has_errors:
    # Inspect report.report before deciding how to handle the failure.
    raise RuntimeError("MDXCanvas did not complete")
```

The returned report uses the JSON structure shown above. Treat `expected_changes`, `changes_made`, `content_to_review`, and `errors` as public report data; they contain resource identifiers, transition/outcome information, and URLs where available. Execution errors include `status` (`failed` or `blocked`) and `action` when associated with a planned action; their resource and source fields provide context for the redacted error message. Course-URL fallback and link grouping affect only human output and are not written into `changes_made`. Use the JSON report—not live log order or the grouped human presentation—as the authoritative integration result.

## Erasing Course Content

The `erasecanvas` command removes all content from a Canvas course.

**WARNING:** This is a destructive operation that cannot be undone.

Usage:

```bash
erasecanvas --course-info <course_info.yaml>
```

Options:

- `--course-info <file>` - Path to course configuration file (required)
- `-y` - Skip confirmation prompt (use with caution!)

The command will delete:

- Syllabus content
- All assignments and quizzes
- All pages
- All modules
- All files and folders
- All announcements

Without the `-y` flag, you will be prompted to confirm before deletion proceeds.

## Tutorials

These guides cover the full feature set of MDXCanvas:

### [Course Info](documents/course_info.md)

Configure course metadata such as name, code, and dashboard image.

### [Supported Tags](documents/supported_tags/supported_tags.md)

Full reference of standard content tags like `<assignment>`, `<quiz>`, `<page>`, and more.

### [Special Tags](documents/special_tags/special_tags.md)

Advanced features like `<include>`, `<file>`, and `<zip>` for modular, reusable content.

### [Jinja Templates](documents/jinja_templates.md)

Use variables and loops to dynamically generate content using `.jinja` templates.

### [CSS Styling](documents/css.md)

Apply custom styling across your content using external CSS files.

## Demo Course

Explore the [`demo_course`](demo-course) folder to see MDXCanvas in action.
