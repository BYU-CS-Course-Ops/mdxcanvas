# MDXCanvas project context

MDXCanvas is a Python tool for parsing Markdown/XML course content and deploying resources to Instructure Canvas through `canvasapi`. It is distributed as a library and through the `mdxcanvas` and `erasecanvas` command-line interfaces. The project uses Poetry and supports Python 3.10 and newer.

## Authoritative project sources

- `README.md` documents installation, CLI behavior, the public Python API, deployment reports, cleanup, dry-run behavior, and ledger compatibility.
- `mdxcanvas/cli.py`, `mdxcanvas/main.py`, and `mdxcanvas/erasecanvas/main.py` define the command-line and top-level Python interfaces.
- `mdxcanvas/resources.py`, `mdxcanvas/deployment_report.py`, and `mdxcanvas/deploy/` contain resource, report, planning, deployment, cleanup, and ledger behavior.
- `mdxcanvas/skills/` contain authoritative guidance on how to use `mdxcanvas`.

{% if 'testing' in context_tags %}
## Testing

{{ myteam_load('dev/skills/testing-philosophy.md') }}

Use `poetry run pytest` for the test suite. Prefer existing fixtures and fakes for Canvas interactions.
{% endif %}

{% if 'documentation' in context_tags %}
## Documentation

Update `README.md` for public CLI or Python API behavior and the relevant file(s) under `mdxcanvas/skills/`. 
{% endif %}

{% if 'release' in context_tags %}
## Release conventions

The package version is stored in `mdxcanvas/VERSION`; Poetry reads it through `poetry-version-from-file`. Release notes are maintained in `CHANGELOG.md` under a `## <version>` heading. Publishing is handled by `.github/workflows/poetry_publish.yaml` after changes reach `main`.
{% endif %}
