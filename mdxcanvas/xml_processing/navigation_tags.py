from bs4.element import NavigableString, Tag

from ..processing_context import get_current_file_str
from ..resources import CanvasResource, NavigationData, ResourceManager


def _error(message: str) -> ValueError:
    return ValueError(f"Invalid navigation: {message}\n  in {get_current_file_str()}")


class NavigationTagProcessor:
    def __init__(self, resources: ResourceManager):
        self._resources = resources

    def __call__(self, tag: Tag):
        if tag.attrs:
            names = ", ".join(tag.attrs)
            raise _error(f"unsupported attribute(s) on <navigation>: {names}")

        tabs = []
        for child in tag.children:
            if isinstance(child, NavigableString):
                if child.strip():
                    raise _error(f"unexpected content {child.strip()!r} in <navigation>")
                continue

            if not isinstance(child, Tag) or child.name != "tab":
                name = getattr(child, "name", type(child).__name__)
                raise _error(f"unsupported child <{name}> in <navigation>")

            tabs.append(self._parse_tab(child))

        duplicates = sorted({name for name in tabs if tabs.count(name) > 1})
        if duplicates:
            raise _error(f"duplicate tab name(s): {', '.join(duplicates)}")

        self._resources.add_resource(CanvasResource(
            type="navigation",
            id="navigation",
            data=NavigationData(tabs=tabs),
            content_path=get_current_file_str(),
        ))

    @staticmethod
    def _parse_tab(tag: Tag) -> str:
        unsupported = [name for name in tag.attrs if name != "name"]
        if unsupported:
            raise _error(f"unsupported attribute(s) on <tab>: {', '.join(unsupported)}")

        if set(tag.attrs) != {"name"}:
            raise _error('<tab> requires exactly one non-empty "name" attribute')

        name = tag.get("name")
        if not isinstance(name, str) or not name.strip():
            raise _error('<tab> requires exactly one non-empty "name" attribute')

        for child in tag.children:
            if isinstance(child, Tag):
                raise _error(f"<tab name={name!r}> cannot contain <{child.name}>")
            if not isinstance(child, NavigableString) or child.strip():
                content = str(child).strip()
                raise _error(f"<tab name={name!r}> cannot contain content {content!r}")

        return name
