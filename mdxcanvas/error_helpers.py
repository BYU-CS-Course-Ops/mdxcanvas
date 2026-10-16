from pathlib import Path
from typing import Any, no_type_check

from bs4.element import Tag

from .processing_context import get_current_file_str


class MissingFilesError(FileNotFoundError):
    """
    Every file the preprocessing pass could not find, not only the first.

    A template naming several missing files is usually one mistake, such as a
    folder that moved and left its references behind. Stopping at the first
    hides the rest, so each one costs its own run to discover.

    Subclasses FileNotFoundError so callers already catching that catch this.
    """

    def __init__(self, messages: list[str]):
        # One shared file included by many pages reports once per page, word
        # for word the same each time. Seven copies of a line read as seven
        # problems and bury the others. Order is kept, so the list still
        # follows the document.
        self.messages = list(dict.fromkeys(messages))
        noun = "file" if len(self.messages) == 1 else "files"
        super().__init__(
            f"{len(self.messages)} missing {noun}:\n\n" + "\n\n".join(self.messages)
        )


@no_type_check
def get_tag_source_file(tag: Tag) -> Path | None:
    if tag and (source := tag.get('data-source')):
        return Path(source)

    for parent in tag.parents:
        if source := parent.get('data-source'):
            return Path(source)

    return None


def get_file_path(tag: Tag) -> Path:
    if source := get_tag_source_file(tag):
        return source

    if current := get_current_file_str():
        return Path(current)

    raise ValueError("No file context available")


def format_tag(tag: Tag) -> str:
    if not tag:
        return "<unknown tag>"

    tag_name = tag.name
    attrs = tag.attrs or {}

    if not attrs:
        return f"<{tag_name}>"

    # Build attribute strings
    attr_strs = [f'{k}="{" ".join(str(v) for v in val) if isinstance(val, list) else val}"' for k, val in attrs.items()]
    attrs_formatted = ' '.join(attr_strs)
    has_children = bool(tag.contents)

    # Build full tag
    full_tag = f"<{tag_name} {attrs_formatted}>" if has_children else f"<{tag_name} {attrs_formatted} />"

    return full_tag


def validate_required_attribute(tag: Tag, attr_name: str, tag_display_name: str | None = None) -> str | Any:
    if not (value := tag.get(attr_name)):
        display_name = tag_display_name if tag_display_name else tag.name
        raise ValueError(
            f'Required field "{attr_name}" missing from {display_name} tag {format_tag(tag)}\n  in {get_file_path(tag)}')
    return value
