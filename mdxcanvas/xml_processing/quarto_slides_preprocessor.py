from pathlib import Path

from bs4.element import Tag

from ..error_helpers import validate_required_attribute, format_tag, get_file_path
from ..processing_context import get_current_file_str
from ..resources import QuartoSlidesData
from ..resources import ResourceManager, CanvasResource
from ..util import find_quarto_root, to_relative_posix


def _find_quarto_dependencies(quarto_root: Path, deploy_root: Path) -> list[str]:
    deps = []

    quarto_yaml = quarto_root / '_quarto.yaml'
    if quarto_yaml.exists():
        deps.append(to_relative_posix(quarto_yaml, deploy_root))

    quarto_yaml = quarto_root / '_quarto.yml'
    if quarto_yaml.exists():
        deps.append(to_relative_posix(quarto_yaml, deploy_root))

    extensions = quarto_root / '_extensions'
    if extensions.exists():
        deps.append(to_relative_posix(extensions, deploy_root))

    return deps


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
        checksum_paths = [to_relative_posix(qmd_file, deploy_root)] + _find_quarto_dependencies(quarto_root, deploy_root)

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
