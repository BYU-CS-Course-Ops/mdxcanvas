import re
from pathlib import Path
from typing import Callable

from bs4.element import Tag

from ..error_helpers import MissingFilesError, format_tag, get_file_path, validate_required_attribute
from ..our_logging import get_logger
from ..processing_context import FileContext, get_current_file_str
from ..resources import ResourceManager, FileData, StrLike, ZipFileData, CanvasResource, get_key
from ..util import parse_soup_from_xml, to_relative_posix
from ..xml_processing.attributes import parse_bool

logger = get_logger()


def make_course_settings_preprocessor(deploy_root: Path, parent: Path, resources: ResourceManager):
    def process_course_settings(tag: Tag):
        name = tag.get('name')
        course_code = tag.get('code')
        image_path: Path | None = tag.get('image')  # type: ignore

        if not (any([name, course_code, image_path])):
            raise ValueError(
                f"Course settings tag must have at least one of: name, code, or image @ {format_tag(tag)}\n  in {get_file_path(tag)}")

        image_resource_key = None
        if image_path:
            image_path = (parent / image_path).resolve().absolute()
            if not image_path.is_file():
                raise FileNotFoundError(
                    f"Course image file not found @ {format_tag(tag)}\n  Image path: {image_path}\n  in {get_file_path(tag)}")

            # noinspection PyTypeChecker
            file = CanvasResource(
                type='file',
                id=image_path.name,
                data=FileData(
                    path=(p := to_relative_posix(image_path, deploy_root)),
                    checksum_paths=[p],
                    canvas_folder=tag.get('canvas_folder'),
                    lock_at=None,
                    unlock_at=None,
                ),
                content_path=get_current_file_str()
            )
            image_resource_key = resources.add_resource_get_field(file, 'id')

        course_settings = CanvasResource(
            type='course_settings',
            id='',
            data={
                'name': name,
                'code': course_code,
                'image': image_resource_key
            },
            content_path=get_current_file_str()
        )
        resources.add_resource_get_field(course_settings, 'name')

    return process_course_settings


def make_image_preprocessor(deploy_root: Path, parent: Path, resources: ResourceManager):
    def process_image(tag: Tag):
        # TODO - handle b64-encoded images

        src = validate_required_attribute(tag, 'src', 'img')
        if src.startswith('http') or src.startswith('__@@'):
            # No changes necessary
            return

        # Assume it's a local file
        src_path = (parent / src).resolve().absolute()
        if not src_path.is_file():
            raise FileNotFoundError(
                f"Image file not found @ {format_tag(tag)}\n  File path: {src_path}\n  in {get_file_path(tag)}")
        src = src_path

        # noinspection PyTypeChecker
        file = CanvasResource(
            type='file',
            id=src.name,
            data=FileData(
                path=(p := to_relative_posix(src, deploy_root)),
                checksum_paths=[p],
                canvas_folder=tag.get('canvas_folder'),
                lock_at=None,
                unlock_at=None
            ),
            content_path=get_current_file_str()
        )
        tag['src'] = resources.add_resource_get_field(file, 'uri') + '/preview'

    return process_image


def make_file_anchor_tag(resource_key: StrLike, filename: StrLike, **kwargs):
    attrs = {
        **kwargs,
        'href': f'{resource_key}?wrap=1',
        'class': 'instructure_file_link inline_disabled',
        'target': '_blank',
        'rel': 'noopener noreferrer'
    }

    new_tag = Tag(name='a', attrs=attrs)
    new_tag.string = filename  # pyright: ignore[reportAttributeAccessIssue]

    return new_tag


def make_file_preprocessor(deploy_root: Path, parent: Path, resources: ResourceManager):
    def process_file(tag: Tag):
        path_value = validate_required_attribute(tag, 'path', 'file')
        attrs = tag.attrs
        path = (parent / path_value).resolve().absolute()
        if not path.is_file():
            raise FileNotFoundError(f"File not found @ {format_tag(tag)}\n  File path: {path}\n  in {get_file_path(tag)}")
        # Only pop the path after validation succeeds
        attrs.pop('path')

        file = CanvasResource(
            type='file',
            id=path.name,
            data=FileData(
                path=(p := to_relative_posix(path, deploy_root)),
                checksum_paths=[p],
                canvas_folder=attrs.get('canvas_folder'),
                unlock_at=attrs.get('unlock_at'),
                lock_at=attrs.get('lock_at')
            ),
            content_path=get_current_file_str()
        )
        resource_key = resources.add_resource_get_field(file, 'uri')
        new_tag = make_file_anchor_tag(resource_key, path.name, **tag.attrs)

        tag.replace_with(new_tag)

    return process_file


def _determine_zip_contents(
        content_folder_path: Path,
        priority_folder: Path | None,
        exclude_pattern: str | None,
        additional_files: list[Path] | None) -> dict[str, Path]:
    exclude = re.compile(exclude_pattern) if exclude_pattern else None

    priority_files = _get_files(priority_folder, exclude, '') if priority_folder else {}
    files = _get_files(content_folder_path, exclude, '')
    if additional_files:
        files.update(_get_additional_files(additional_files))

    for zip_name, file in files.items():
        if zip_name not in priority_files:
            priority_files[zip_name] = file
        else:
            logger.debug(f'Preferring {priority_files[zip_name]} over {file}')

    return priority_files


def _get_files(folder_path: Path, exclude: re.Pattern | None, prefix) -> dict[str, Path]:
    if not folder_path.exists():
        raise FileNotFoundError(folder_path)

    files = {}
    for file in sorted(folder_path.glob('*')):
        if exclude and exclude.search(file.name):
            logger.debug(f'Excluding {file} from zip')
            continue

        if file.is_dir():
            files.update(_get_files(file, exclude, prefix + '/' + file.name))
        else:
            files[prefix + '/' + file.name] = file.absolute()

    return files


def _get_additional_files(additional_files: list[Path]) -> dict[str, Path]:
    files = {}
    for file in additional_files:
        if file.is_dir():
            files.update(_get_files(file, None, f'/{file.name}'))
        else:
            files[f'/{file.name}'] = file

    return files


def make_zip_preprocessor(deploy_root: Path, parent: Path, resources: ResourceManager):
    def process_zip(tag: Tag):
        content_folder = validate_required_attribute(tag, 'path', 'zip')

        name = tag.get("name")
        if not name:
            name = (
                       content_folder
                       .replace('.', '')
                       .replace('/', '-')
                       .strip('-')
                   ) + '.zip'

        content_folder_path = (parent / content_folder).resolve().absolute()
        if not content_folder_path.exists():
            raise FileNotFoundError(
                f"Folder not found @ {format_tag(tag)}\n  Folder path: {content_folder_path}\n  in {get_file_path(tag)}")

        additional_files = None
        if additional_files_str := tag.get("additional_files"):
            additional_files = [
                (parent / file).resolve().absolute()
                for file in additional_files_str.split(',')  # pyright: ignore[reportAttributeAccessIssue]
            ]

        priority_folder = None
        if priority_folder_str := tag.get("priority_path"):

            priority_folder = (
                parent / priority_folder_str   # pyright: ignore[reportOperatorIssue]
            ).resolve().absolute()

        exclude_pattern: str = tag.get("exclude")  # pyright: ignore[reportAssignmentType]

        zip_contents = _determine_zip_contents(
            content_folder_path, priority_folder, exclude_pattern,
            additional_files
        )
        zip_contents = {p: to_relative_posix(fpath, deploy_root) for p, fpath in zip_contents.items()}

        file = CanvasResource(
            type='zip',
            id=name,
            data=ZipFileData(
                zip_file_name=name,
                zip_contents=zip_contents,
                checksum_paths=[fpath for fpath in zip_contents.values()],
                canvas_folder=tag.get('canvas_folder'),
                lock_at=tag.get('lock_at'),
                unlock_at=tag.get('unlock_at')
            ),
            content_path=get_current_file_str()
        )

        resource_key = resources.add_resource_get_field(file, 'uri')

        new_tag = make_file_anchor_tag(resource_key, name)
        tag.replace_with(new_tag)

    return process_zip


def _parse_slice(field: StrLike) -> slice:
    """
    Parse a 1-based, inclusive slice
    So, the slice should match the line numbers shown in your IDE
    """
    tokens = field.split(':')  # pyright: ignore[reportAttributeAccessIssue]
    tokens = [
        int(token) if token else None
        for token in tokens
    ]

    if not tokens[0]:
        raise ValueError(f"Invalid slice: {field} - first token must be a number")

    tokens[0] -= 1  # make it 1-based

    if len(tokens) == 1:  # e.g. "3"
        tokens.append(None)

    # Tokens[1] +1 for inclusive, -1 for one-based, net: 0

    return slice(tokens[0], tokens[1])


def make_include_preprocessor(
        deploy_root: Path,
        parent_folder: Path,
        process_file: Callable
):
    def process_include(tag: Tag):
        imported_filename: str = tag.get('path')  # pyright: ignore[reportAssignmentType]
        imported_file = (parent_folder / imported_filename).resolve()
        args_file_path: str | None = tag.get('args')  # pyright: ignore[reportAssignmentType]

        # Check if the included file exists first
        if not imported_file.exists():
            containing_file = get_current_file_str()
            raise FileNotFoundError(
                f"Include file not found @ {format_tag(tag)}\n"
                f"  in {containing_file}"
            )

        args_file = None
        if args_file_path:
            args_file = (parent_folder / args_file_path).resolve().absolute()

            # Check if args file exists
            if not args_file.exists():
                containing_file = get_current_file_str()
                raise FileNotFoundError(
                    f"Args file not found @ {format_tag(tag)}\n"
                    f"  in {containing_file}"
                )

        # Track the included file in context for error messages
        with FileContext(imported_file):
            imported_raw_content = imported_file.read_text(encoding='utf-8')
            suffixes = imported_file.suffixes

            if lines := tag.get('lines'):
                grab = _parse_slice(lines)
                imported_raw_content = '\n'.join(imported_raw_content.splitlines()[grab])

            if parse_bool(tag.get('fenced', 'false')):
                suffix = imported_file.suffix.lstrip('.')
                filename_attr = f' {{: title="{imported_file.name}" }}' if parse_bool(
                    tag.get('include_filename', 'false')) else ''
                imported_raw_content = f'```{suffix}{filename_attr}\n{imported_raw_content}\n```\n'
                suffixes = suffixes + ['.md']

            imported_html = process_file(
                imported_file.parent,
                imported_raw_content,
                suffixes,
                args_file=args_file
            )

            use_div = parse_bool(tag.get('usediv', 'true'))

            include_result = parse_soup_from_xml(imported_html)

            if not use_div:
                tag.replace_with(include_result)

            else:
                new_tag = Tag(name='div')
                new_tag['data-source'] = str(to_relative_posix(imported_file, deploy_root))
                if lines:
                    new_tag['data-lines'] = lines
                new_tag.extend(include_result)
                tag.replace_with(new_tag)

    return process_include


def make_link_preprocessor():
    def process_link(tag: Tag):
        link_type = validate_required_attribute(tag, 'type', 'course-link')
        # TODO: Canvas supports `course navigation` links, do we?
        if link_type not in ['syllabus', 'page', 'assignment', 'quiz', 'announcement', 'discussion', 'module', 'file']:
            raise ValueError(f'Invalid course-link type "{link_type}" @ {format_tag(tag)}\n  in {get_file_path(tag)}')

        link_rid = validate_required_attribute(tag, 'id', 'course-link')

        new_tag = Tag(name='a')
        frag = tag.get('fragment')
        new_tag['href'] = get_key(link_type, link_rid, 'uri') + (f'#{frag}' if frag else '')
        link_text = tag.string.strip() if tag.string is not None else ''
        if not link_text:
            link_text = get_key(link_type, link_rid, 'title')
        new_tag.string = link_text
        tag.replace_with(new_tag)

    return process_link


def make_markdown_page_preprocessor(
        deploy_root: Path,
        parent_folder: Path,
        process_file: Callable
):
    def process_markdown_page(tag: Tag):
        content_path = validate_required_attribute(tag, 'path', 'md-page')
        page_id = validate_required_attribute(tag, 'id', 'md-page')
        content_path_obj = Path(parent_folder) / content_path

        page_title = tag.get('title')
        if page_title is None:
            # Only read file if it exists for getting the title
            if content_path_obj.exists():
                first_line = content_path_obj.read_text().splitlines()[0]
                if first_line.startswith('# '):
                    page_title = first_line.strip('#').strip()
                else:
                    page_title = content_path_obj.stem
            else:
                # File doesn't exist, use filename as title
                page_title = content_path_obj.stem

        include_tag = Tag(name='include', attrs={'path': content_path})

        page_tag = Tag(name='page', attrs={'title': page_title})
        page_tag.append(include_tag)
        page_tag['id'] = page_id

        include_processor = make_include_preprocessor(deploy_root, parent_folder, process_file)

        try:
            include_processor(include_tag)  # Replaces include_tag with new content
        except MissingFilesError:
            # The page itself was found; these came from inside it, and each
            # already names the tag and file it belongs to. Restating this
            # page over the top of them would bury what they say.
            raise
        except FileNotFoundError as e:
            raise FileNotFoundError(f"File not found @ {format_tag(tag)}\n  in {get_file_path(tag)}") from e

        tag.replace_with(page_tag)

    return process_markdown_page
