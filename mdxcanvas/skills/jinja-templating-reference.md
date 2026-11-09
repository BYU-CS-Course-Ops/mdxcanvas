---
type: skill
description: Load when writing or editing MDXCanvas Jinja templates or args files, or using template helpers, MarkdownData schemas, includes, loops, macros, and multiline Markdown.
---

# MDXCanvas Jinja Operational Reference

Use this reference for template mechanics. Use [Course-info and Global-args Principles](course-info-and-args-principles.md) for data ownership, the [Content Author](content-author-role.md) for authoring responsibilities, and [tag references](tags/description.md) for resource syntax. Deployment procedures belong to the Deployment Engineer.

The examples below are literal MDXCanvas source, not expressions for Myteam to evaluate. Choose templates when a small shared structural contract improves maintenance; unique content and exceptions can remain explicit.

{% raw %}
## Processing and argument scopes

A content file whose **final suffix** is `.jinja` is rendered first. The remaining suffixes control subsequent processing: for example, `pages.canvas.md.xml.jinja` renders Jinja, processes Markdown because `.md` is present, then preprocesses XML helpers such as `<include>`. A plain `.xml` file is not Jinja-rendered just because it contains expressions. Templates may emit fragments or multiple resources; they need not begin with one resource tag.

Global context is assembled in this order:

1. Start with the selected course-info mapping's `GLOBAL_ARGS` (or `{}`). Top-level course-info settings are not automatically template variables.
2. Shallow-update it with the mapping loaded from CLI `--global-args`. A conflicting top-level key is replaced, including an entire nested mapping; this is **not a recursive merge**.
3. Expose merged keys directly as template variables, including in included templates and Jinja-rendered data files.

For example, if course-info contains `GLOBAL_ARGS: {YEAR: 2027, Options: {a: true, b: true}}` and the standalone file contains `Options: {a: false}`, the result retains `YEAR` but `Options` contains only `a`. Avoid competing definitions except for deliberate, documented overrides. Global key names can also shadow injected helper names.

Per-template data is separate:

| Input | Meaning | Access |
|---|---|---|
| `--global-args offering.yaml` | Merged course-wide variables | `{{ YEAR }}`, `get_arg('YEAR')` |
| `--args catalog.md` | Data object for the entry template | `{{ args[0]['Title'] }}` |
| `<include ... args="catalog.md"/>` | Data object for that included template | `args` in that template |

These are invocation **fragments**, not deployment instructions. Neither `--args` nor an include's `args` merges row keys into globals. An include does not automatically inherit its caller's per-template `args`; supply its own args file. Currently the renderer adds `args` only when its loaded object is truthy: an empty list/mapping does not establish an `args` variable. Do not rely on it for required keys. The environment is not configured with StrictUndefined or automatic XML escaping; missing values may silently render empty. Use `is defined`/defaults only for genuinely optional data and preserve XML-safe attribute values.

### Supported data formats and suffix chaining

Per-template `--args`, include `args`, and `load(path)` accept:

| Suffix | Loader / expected shape |
|---|---|
| `.json` | JSON, normally dict or list |
| `.csv` | CSV DictReader, list of dicts; cells remain strings |
| `.yaml`, `.yml` | YAML safe_load, normally dict or list |
| `.md`, `.mdd` | MarkdownData, shape determined by source structure |
| Any above plus `.jinja` | Render with merged globals, then parse the preceding suffix |

For example `catalog.md.jinja` can contain `{{ REVIEW_DUE }}` in a table cell. It is rendered in the data file's own directory, with globals (not the calling template's local variables or per-template args), then parsed as MarkdownData. One trailing `.jinja` is stripped for data parsing; repeated `.jinja.jinja` chaining is not supported.

Course-info and CLI `--global-args` instead use the configuration loader: `.yaml`, `.yml`, `.json`, `.md`, `.mdd`, with a mapping required for global merging. They do **not** accept CSV or Jinja-rendered configuration. Filenames are explicitly selected; `global_args.yaml` and `global-args.yaml` have no special automatic discovery behavior. Keys such as `Group_Weights` have no implicit semantics: a template must consume them. Keep credentials outside authored args and committed configuration.

## Paths, includes, and discovery

- `exists`, `read_file`, `glob`, and `load` resolve relative paths against the directory of the MDXCanvas template being rendered. Absolute paths remain absolute. These runtime helpers do not implement Myteam's home-directory expansion.
- `parent(path)` is purely lexical: it returns the parent string, without opening or resolving the path.
- `<include path="..." args="..."/>` resolves **both attributes against the containing source file's directory**, not the included template's directory. Inside that included template, helpers use its own directory.
- Paths stored in data are just strings. `load` does not rebase them to the data file's directory; the eventual consumer determines their meaning.
- `read_file` inserts raw text: it does not recursively render Jinja or parse data. Use `load` for structured data, or MDXCanvas `<include>` for suffix-driven content processing.
- Native Jinja `{% include %}`, imports, and inheritance use FileSystemLoader. Its search paths are the current parent folder, the supplied args path (as implemented, not necessarily its directory), and CLI `--templates` directories. A native Jinja include does not independently reset the injected helpers' parent folder; prefer MDXCanvas includes when a file needs its own processing/path context.

Example: in `course.canvas.md.xml.jinja`, include a template and data with paths from the entry point:

```xml
<include path="shared/pages.canvas.md.xml.jinja"
         args="data/pages.md.jinja"/>
```

Inside `shared/pages.canvas.md.xml.jinja`, `load('catalog.yaml')` reads `shared/catalog.yaml`.

Generic discovery with a narrow active-content pattern:

```jinja
{% for metadata_path in glob('topics/*/page.yaml') %}
{% set record = load(metadata_path) %}
{% set folder = parent(metadata_path) %}
{% if record['Enabled'] and exists(folder ~ '/notes.md') %}
<page id="{{ record['ID'] }}" title="{{ record['Title'] }}">
    {{ read_file(folder ~ '/notes.md') | indent(4, blank=True) }}
</page>
{% endif %}
{% endfor %}
```

Each YAML record must supply an immutable literal `ID` (for example `source-evaluation`), mutable `Title`, and boolean `Enabled`. `glob` returns sorted relative strings and can match directories as well as files; narrow the pattern and exclude archives/drafts deliberately. Conditional omission changes the resource graph: ensure references follow the same inclusion rule. Sorted discovery is not automatically the intended module order.

## Injected helper contracts

These are MDXCanvas helpers, **not Myteam helpers with similar names**.

| Helper / signature | Runtime behavior |
|---|---|
| `zip(*iterables, strict=False)` | Python zip; parallel iteration, normally stops at shortest input; strict mismatch raises. |
| `enumerate(iterable, start=0)` | Python enumerate; `(index, value)` pairs. |
| `split_list(x)` | Exactly `x.split(';')`: no trimming, no empty-entry removal. |
| `exists(path)` | Path.exists relative to template directory; true for existing files or directories. |
| `read_file(f)` | Read text relative to template directory; no rendering. |
| `glob(*args, **kwargs)` | Forwards to Path.glob; usually `glob(pattern)`. Returns a sorted list of paths relative to template directory. Extra supported options depend on the Python version. |
| `parent(path)` | `str(Path(path).parent)`. |
| `load(path)` | Parse a supported data file relative to template directory, optionally rendering its `.jinja` suffix first. |
| `get_arg(key[, default])` | Merged global mapping's `.get`; missing without default returns None. Not per-template args lookup. |
| `search(pattern, string, flags=0)` | Python re.search; Match or None, not captured text. |
| `debug(msg)` | logger.debug(msg); visible with debug logging, returns None. Use a statement capture to avoid inserting its return value. |

```jinja
{% set _ = debug('Reading topic catalog') %}
{% for left, right in zip(['a', 'b'], ['c', 'd']) %}
{{ left ~ ':' ~ right }}
{% endfor %}
{% for position, label in enumerate(['Read', 'Reflect'], start=1) %}
{{ position }}. {{ label }}
{% endfor %}
{% if get_arg('AUDIENCE', 'all') == 'remote' %}
<page id="remote-participation" title="Remote Participation">
    Participation instructions for the remote audience.
</page>
{% endif %}
```

### Regex results and string composition

Check for None **before** accessing groups. A Match can be used directly as a truth test; call `.group()` when extracting text, not merely to test existence.

```jinja
{% set match = search('topic-([a-z]+)', 'topic-evidence') %}
{% if match is not none %}
{% set code = match.group(1) %}
{% set label = 'Topic: ' ~ code %}
{{ label }}
{% endif %}
```

`.group(0)` (or `.group()`) is the complete match; `.group(1)` is the first capture; `.groups()` returns all captures as a tuple. Use `~` to concatenate strings (it stringifies operands). Extracted labels are not a license to derive durable IDs from mutable titles or filenames without an established identity contract.

## Data contracts: tables versus keyed records

MarkdownData headings and table column names are case-sensitive keys. Preserve exact spelling, nesting, types, and heading levels. Do not interchange `Due_At`, `due_at`, or `Due`. A keyed file is not a table and is not necessarily a list.

### Flat table: list of dicts

`pages.md`:

```markdown
| ID | Title | Notes |
|---|---|---|
| source-evaluation | Evaluating Sources | Compare evidence and claims. |
| evidence-reflection | Evidence Reflection | Reflect on your approach. |
```

The table is a list of row dictionaries, accessed as follows:

```jinja
{% for row in args %}
<page id="{{ row['ID'] }}" title="{{ row['Title'] }}">
    {{ row['Notes'] | indent(4, blank=True) }}
</page>
{% endfor %}
```

Each `ID` cell is an explicit stable literal, not a slug generated from `Title`. An args table containing globals must be named, for example, `pages.md.jinja` rather than `pages.md`.

### Keyed MarkdownData: rich records

`pages.md`:

```markdown
# source-evaluation

===
Title: Evaluating Sources
===

## Description

Compare evidence and claims.

Explain your reasoning in a second paragraph.

# evidence-reflection

===
Title: Evidence Reflection
===

## Description

Reflect on your approach.
```

Its shape is a mapping such as:

```json
{
  "source-evaluation": {
    "content": {"Title": "Evaluating Sources"},
    "Description": "Compare evidence and claims.\n\nExplain your reasoning in a second paragraph."
  },
  "evidence-reflection": {
    "content": {"Title": "Evidence Reflection"},
    "Description": "Reflect on your approach."
  }
}
```

Use explicit stable heading keys, not student-facing titles, as identity:

```jinja
{% for resource_id, info in args.items() %}
<page id="{{ resource_id }}" title="{{ info['content']['Title'] }}">
    {{ info['Description'] | indent(4, blank=True) }}
</page>
{% endfor %}
```

`Description` exists because the source contains `## Description`. Unheaded prose is not automatically a `Description` key. Metadata inside `===` is under `content`; tables under other headings introduce different nesting. JSON/YAML can express equivalent structures directly; choose access expressions from the actual source schema.

## Loops, macros, and stable identity

Jinja provides `loop.index` (1-based), `loop.index0` (0-based), `loop.first`, and `loop.last`. Use these for presentation or separators, **never for durable resource or question IDs**. Reordering must not change identity. Questions likewise need explicit immutable keys in their data; consult the quiz/question tag reference for required nesting and attributes.

```jinja
{% for label in ['Read', 'Compare', 'Reflect'] %}
{{ loop.index }}. {{ label }}{% if loop.first %} (start here){% endif %}
{% if not loop.last %}

{% endif %}
{% endfor %}
```

A macro can express a small repeated navigation contract:

```jinja
{% macro page_item(resource_id) %}
<item type="page" content_id="{{ resource_id }}"/>
{% endmacro %}

<module id="evidence-path" title="Working with Evidence">
    {{ page_item('source-evaluation') }}
    {{ page_item('evidence-reflection') }}
</module>
```

The referenced pages must be included exactly once. Module item IDs may derive from `content_id`; this does not remove the need for stable resource IDs. Preserve existing explicit item IDs. Items without `content_id`, such as subheaders, need their own stable IDs according to the module tag contract. Keep exceptions visible rather than expanding macros into complex frameworks. Use `{# comments #}` for template-only notes.

## Multiline Markdown and indentation

Jinja's `indent(width=4, first=False, blank=False)` filter indents subsequent nonblank lines by default. `first=True` also indents the first line; `blank=True` indents blank lines. Match the surrounding source indentation so MDXCanvas's dedent and Markdown processing see the intended paragraphs, lists, and code blocks.

When the expression itself is already indented, leave `first=False`:

```jinja
<page id="source-evaluation" title="Evaluating Sources">
    {{ info['Description'] | indent(4, first=False, blank=True) }}
</page>
```

When the expression starts at column zero, indent every line:

```jinja
<page id="source-evaluation" title="Evaluating Sources">
{{ info['Description'] | indent(4, first=True, blank=True) }}
</page>
```

These are alternatives, not two resources to include together. Preserve real blank lines in the underlying Markdown between paragraphs and around block constructs. `blank=True` keeps blank lines aligned but does not create paragraph breaks or fix missing newlines. Avoid aggressive `{%-` / `-%}` whitespace stripping around Markdown: it can join paragraphs or list items. Do not blindly indent already-indented content twice.

## Source review checklist

- Trace the entry point, MDXCanvas includes, native Jinja includes/macros, and every args consumer.
- Confirm exact table columns, heading keys, metadata nesting, and data types.
- Check global shallow overrides and required keys across intended configuration pairs.
- Confirm path contexts and discovery matches; keep private/retired material out of active patterns.
- Preserve stable literal resource/question IDs, references, and explicit existing module item IDs.
- Check multiline indentation, blank lines, XML-safe text, and authoritative tag requirements.
- Hand operational validation and deployment to the Deployment Engineer; source review alone is not live-state verification.
{% endraw %}
