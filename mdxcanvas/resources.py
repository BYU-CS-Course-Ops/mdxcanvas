import re
from typing import Any, NotRequired, TypedDict, Iterator, no_type_check
from bs4._typing import _AttributeValue

StrLike = str | _AttributeValue


#
# Information about deployed resources
#

class ResourceInfo(TypedDict):
    id: str


class AnnouncementInfo(ResourceInfo):
    id: str
    url: str | None
    uri: str | None  # for course-link
    title: str  # for course-link


class CourseSettingsInfo(ResourceInfo):
    id: str


class NavigationInfo(ResourceInfo):
    id: str


class AssignmentInfo(ResourceInfo):
    id: str
    url: str | None
    uri: str | None  # for course-link
    title: str  # for course-link text


class FileInfo(ResourceInfo):
    id: str
    uri: str
    url: str
    title: str  # for course-link


class AssignmentGroupInfo(ResourceInfo):
    id: str


class ModuleInfo(ResourceInfo):
    id: str
    title: str  # for course-link
    uri: str
    url: str


class ModuleItemInfo(ResourceInfo):
    id: str
    module_id: str
    uri: str
    url: str


class OverrideInfo(ResourceInfo):
    id: str
    assignment_id: str


class PageInfo(ResourceInfo):
    id: str
    page_url: str  # for module item
    uri: str  # for course-link
    url: str | None
    title: str  # for course-link text


class QuizInfo(ResourceInfo):
    id: str
    uri: str  # for course-link
    url: str | None
    title: str  # for course-link text


class QuizQuestionInfo(ResourceInfo):
    id: str
    quiz_id: str
    uri: str
    url: str | None


class QuizQuestionOrderInfo(ResourceInfo):
    quiz_id: str
    uri: str
    url: str | None


class SyllabusInfo(ResourceInfo):
    id: str
    uri: str
    url: str
    title: str  # for course-link title


#
# Information needed to deploy a resource
#

class CanvasResource(TypedDict):
    type: str
    id: str | Any
    data: 'dict | FileData | ZipFileData | QuartoSlidesData | MermaidData | NavigationData | SyllabusData'
    content_path: str


class CourseSettings(TypedDict):
    name: str
    code: str
    image: str


class FileData(TypedDict):
    path: str
    checksum_paths: NotRequired[list[str]]
    canvas_folder: StrLike | None
    lock_at: StrLike | None
    unlock_at: StrLike | None
    canvas_id: NotRequired[str | None]


class ZipFileData(TypedDict):
    zip_file_name: StrLike
    zip_contents: dict[str, str]
    checksum_paths: NotRequired[list[str]]
    canvas_folder: StrLike | None
    lock_at: StrLike | None
    unlock_at: StrLike | None
    canvas_id: NotRequired[str | None]


class QuartoSlidesData(TypedDict):
    path: str
    root_path: str
    checksum_paths: NotRequired[list[str]]
    slides_name: StrLike
    canvas_folder: StrLike | None
    lock_at: StrLike | None
    unlock_at: StrLike | None
    canvas_id: NotRequired[str | None]


class MermaidData(TypedDict):
    id: StrLike
    source: str
    canvas_folder: StrLike | None
    lock_at: StrLike | None
    unlock_at: StrLike | None
    alt: NotRequired[StrLike | None]
    css_class: NotRequired[StrLike | None]
    attrs: NotRequired[dict[str, str]]
    canvas_id: NotRequired[str | None]


class NavigationData(TypedDict):
    tabs: list[str]
    canvas_id: NotRequired[str | None]


class SyllabusData(TypedDict):
    content: str
    canvas_id: NotRequired[str | None]


class QuizQuestionOrderData(TypedDict):
    quiz_id: str
    order: list[dict[str, str | int]]


@no_type_check
def iter_keys(text: str) -> Iterator[tuple[str, str, str, str]]:
    for match in re.finditer(r'__@@([^|]+)\|\|(.+?)\|\|([^@]+)@@__', text):
        yield (match.group(0), *match.groups())


def get_key(rtype: StrLike, rid: StrLike, field: str):
    return f'__@@{rtype}||{rid}||{field}@@__'


class ResourceManager(dict[tuple[str, str], CanvasResource]):

    def _add_resource(self, resource: CanvasResource) -> tuple[str, str]:
        rtype = resource['type']
        rid = resource['id']
        self[rtype, rid] = resource
        return rtype, rid

    def add_resource_get_field(self, resource: CanvasResource, field: str) -> str:
        rtype, rid = self._add_resource(resource)
        return get_key(rtype, rid, field)

    def add_resource(self, resource: CanvasResource) -> None:
        self._add_resource(resource)
