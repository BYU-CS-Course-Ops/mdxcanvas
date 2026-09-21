import glob
import re
from pathlib import Path
from urllib.parse import unquote, urlparse

import markdown
import yaml
from bs4 import BeautifulSoup
from bs4.element import Tag

from ..error_helpers import validate_required_attribute, format_tag, get_file_path
from ..processing_context import get_current_file_str
from ..resources import QuartoSlidesData
from ..resources import ResourceManager, CanvasResource
from ..util import find_quarto_root, to_relative_posix


REFERENCE_ATTRIBUTES = ("src", "data-src", "poster", "data-background-image")
TEXT_DEPENDENCY_SUFFIXES = {".css", ".html", ".md", ".qmd"}


def _resolve_local_reference(reference: str, base_dir: Path) -> list[Path]:
    reference = reference.strip().strip("<>\"'")
    parsed = urlparse(reference)
    if not parsed.path or parsed.scheme or parsed.netloc or reference.startswith(("#", "data:")):
        return []

    relative_path = unquote(parsed.path)
    if Path(relative_path).is_absolute():
        return []
    if glob.has_magic(relative_path):
        return [path.resolve() for path in base_dir.glob(relative_path) if path.exists()]

    path = (base_dir / relative_path).resolve()
    return [path] if path.exists() else []


def _iter_yaml_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _iter_yaml_strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from _iter_yaml_strings(item)


def _yaml_dependencies(text: str, base_dir: Path, *, frontmatter: bool = False) -> set[Path]:
    if frontmatter:
        match = re.match(r"^---\s*\n(.*?)(?:\n---|\n\.\.\.)\s*(?:\n|$)", text, re.DOTALL)
        if not match:
            return set()
        text = match.group(1)

    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError:
        return set()

    dependencies = set()
    for value in _iter_yaml_strings(data):
        dependencies.update(_resolve_local_reference(value, base_dir))
    return dependencies


def _markup_dependencies(text: str, base_dir: Path, *, render_markdown: bool) -> set[Path]:
    rendered = markdown.markdown(text, extensions=["fenced_code"]) if render_markdown else text
    soup = BeautifulSoup(rendered, "html.parser")
    dependencies = set()
    for element in soup.find_all(True):
        for attribute in REFERENCE_ATTRIBUTES:
            reference = element.get(attribute)
            if isinstance(reference, str):
                dependencies.update(_resolve_local_reference(reference, base_dir))

    for link in soup.find_all("link"):
        reference = link.get("href")
        if isinstance(reference, str):
            dependencies.update(_resolve_local_reference(reference, base_dir))

    patterns = (
        r"\{\{<\s*include\s+([^\s>]+)",
        r"(?:background-image|data-background-image)\s*=\s*['\"]([^'\"]+)",
    )
    for pattern in patterns:
        for reference in re.findall(pattern, text):
            dependencies.update(_resolve_local_reference(reference, base_dir))
    return dependencies


def _css_dependencies(text: str, base_dir: Path) -> set[Path]:
    dependencies = set()
    references = re.findall(r"url\(\s*([^)]*?)\s*\)|@import\s+(?:url\()?\s*['\"]?([^'\"\s;)]+)", text)
    for url_reference, import_reference in references:
        dependencies.update(_resolve_local_reference(url_reference or import_reference, base_dir))
    return dependencies


def _expand_directories(paths: set[Path]) -> set[Path]:
    files = set()
    for path in paths:
        if path.is_dir():
            files.update(child.resolve() for child in path.rglob("*") if child.is_file())
        elif path.is_file():
            files.add(path)
    return files


def _referenced_dependencies(initial_paths: set[Path]) -> set[Path]:
    dependencies = set()
    pending = list(initial_paths)

    while pending:
        path = pending.pop()
        if path in dependencies:
            continue
        dependencies.add(path)
        if not path.is_file() or path.suffix.lower() not in TEXT_DEPENDENCY_SUFFIXES:
            continue

        text = path.read_text(encoding="utf-8")
        if path.suffix.lower() == ".css":
            discovered = _css_dependencies(text, path.parent)
        else:
            discovered = _markup_dependencies(
                text,
                path.parent,
                render_markdown=path.suffix.lower() in {".md", ".qmd"},
            )
            if path.suffix.lower() in {".md", ".qmd"}:
                discovered.update(_yaml_dependencies(text, path.parent, frontmatter=True))
        pending.extend(discovered - dependencies)

    return dependencies


def _explicit_dependencies(value: str, slide_file: Path, tag: Tag) -> set[Path]:
    dependencies = set()
    for pattern in (item.strip() for item in value.split(",")):
        if not pattern:
            continue
        matches = _resolve_local_reference(pattern, slide_file.parent)
        if not matches:
            raise ValueError(
                f"Quarto dependency not found @ {format_tag(tag)}\n"
                f"  Dependency: {pattern}\n"
                f"  in {get_file_path(tag)}"
            )
        dependencies.update(matches)
    return dependencies


def _find_quarto_dependencies(
        slide_file: Path,
        quarto_root: Path,
        deploy_root: Path,
        explicit_dependencies: set[Path],
) -> list[str]:
    dependencies = {slide_file, *explicit_dependencies}

    for config_name in ("_quarto.yaml", "_quarto.yml"):
        config = quarto_root / config_name
        if config.is_file():
            dependencies.add(config)
            dependencies.update(_yaml_dependencies(config.read_text(encoding="utf-8"), quarto_root))

    extensions = quarto_root / "_extensions"
    if extensions.exists():
        dependencies.add(extensions)

    dependencies = _expand_directories(_referenced_dependencies(dependencies))
    return sorted(to_relative_posix(path, deploy_root) for path in dependencies)


def make_quarto_slides_preprocessor(deploy_root: Path, parent: Path, resources: ResourceManager):
    def process_quarto_slides(tag: Tag):
        qmd_file = (
                parent
                / validate_required_attribute(tag, 'path', 'quarto-slides')
        ).resolve().absolute()

        if not qmd_file.exists():
            raise ValueError(
                f"File not found @ {format_tag(tag)}\n  File path: {qmd_file}\n  in {get_file_path(tag)}")

        name = tag.get("name")
        if not name:
            name = qmd_file.name.replace('.qmd', '.slides.html')

        quarto_root = find_quarto_root(qmd_file)
        explicit_dependencies = set()
        if dependencies_value := tag.get("dependencies"):
            explicit_dependencies = _explicit_dependencies(str(dependencies_value), qmd_file, tag)
        checksum_paths = _find_quarto_dependencies(
            qmd_file,
            quarto_root,
            deploy_root,
            explicit_dependencies,
        )

        file = CanvasResource(
            type='quarto-slides',
            id=name,
            data=QuartoSlidesData(
                path=to_relative_posix(qmd_file, deploy_root),
                root_path=to_relative_posix(quarto_root, deploy_root),
                checksum_paths=checksum_paths,
                slides_name=name,
                canvas_folder=tag.get('canvas_folder'),
                lock_at=tag.get("lock_at"),
                unlock_at=tag.get("unlock_at")
            ),
            content_path=get_current_file_str()
        )

        resource_key = resources.add_resource_get_field(file, 'url')

        # Canvas sandboxes HTML file responses, so Reveal.js cannot run when
        # the generated deck is opened in Canvas. Requesting the file with
        # download_frd=1 gives students a direct download instead.
        new_tag = Tag(
            name='a',
            attrs={
                'href': f'{resource_key}?download_frd=1',
                'target': '_blank',
                'rel': 'noopener noreferrer',
            },
        )
        new_tag.string = name
        tag.replace_with(new_tag)

    return process_quarto_slides
