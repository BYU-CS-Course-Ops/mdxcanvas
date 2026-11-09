# Packaged Myteam skill installation validation

## Result

Passed against a wheel built from this checkout, after fixing the installed console entry point. Focused project parser/runtime checks were **explicitly skipped at the user's request**. This is distribution/discovery validation, not proof of runtime parser behavior or live Canvas correctness.

## Artifact and isolation

- Wheel: `.agents/scratch/skill-wheel/mdxcanvas-0.8.13-py3-none-any.whl`.
- SHA-256: `7940eeae6acc0fdf8bb0df4462046781f1e57fd36039941efa61d66d358d3f00`.
- Created a fresh venv at `.agents/scratch/skill-install-env/`, without system site packages; installed the wheel and declared runtime dependencies using pip. `pip check` passed.
- Ran the installed console command from `.agents/scratch/installed-skill-check/`, with `PYTHONPATH` and `CANVAS_API_TOKEN` removed. Package import identity and skilldir both pointed inside this venv's `site-packages`, not the checkout.
- Myteam itself was the existing configured tool, reading the installed package's Markdown. It was not a source-tree replacement for the installed `mdxcanvas` command.

## Entry-point defect and correction

Initial `mdxcanvas skilldir` was interpreted as an input filename and attempted to read the default course-info file, failing before any Canvas connection. The preexisting `--skilldir` option was not an equivalent successful validation of the requested command.

`mdxcanvas/cli.py` now handles exactly `skilldir` or `--skilldir` before importing deployment code. Both print the installed skill directory and exit without credentials or course-info. Rebuilt/reinstalled the wheel after that fix; both installed spellings passed. No project tests were added or run because focused runtime checks were waived.

## Checks passed

1. Wheel contents match every intended source Markdown file byte-for-byte: **18 Markdown files**, consisting of **17 skills** plus `tags/description.md`.
2. Installed Markdown matches both the source and wheel bytes.
3. No `load.py` or `info.md` compatibility files ship under the skill tree.
4. `mdxcanvas skilldir` returns the installed package directory. The compatibility `--skilldir` spelling also works.
5. `myteam list` against the installed root and `tags/` discovers exactly all 17 intended skills; `myteam load` succeeds for every exact displayed name.
6. Loaded Content Author dynamically lists the **installed** tag skills through its document-relative `myteam_list('tags/')` expression.
7. Literal Jinja examples remain literal when loaded, rather than being evaluated as course data during Myteam skill rendering.
8. All relative Markdown links resolve within the installed skill tree.
9. Final `git diff --check` passes.

## Reproduction and artifacts

The source wheel was built with `poetry build --format wheel --output .agents/scratch/skill-wheel`. The final package reinstall used the isolated venv's pip with `--no-deps --force-reinstall`, after its initial full dependency installation. No production/project environment dependencies were changed.

Scratch implementation/report artifacts: `validate-installed-skills.py`, `installed-skill-validation.json`, `installed-skill-check/listing.txt`, rendered skill files under `installed-skill-check/`, and install logs. These are local evidence, not distributable package inputs.

## Explicit exclusions

- No focused project tests, full Markdown/XML parser checks, template runtime probes, Canvas calls, deployment, browser launches, or publication.
- Current `documents/` files remain historical evidence where they conflict with authoritative packaged skill/runtime descriptions; a general documentation rewrite is outside this migration.
- Packaging validation was completed before removing the legacy roster. The durable section matrix records the removed file paths and pre-retirement hashes.
