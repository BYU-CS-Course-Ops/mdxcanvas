from pathlib import Path
from typing import Callable

from .announcement_tags import AnnouncementTagProcessor
from .assignment_tags import AssignmentTagProcessor
from .mermaid_preprocessor import make_mermaid_preprocessor
from .navigation_tags import NavigationTagProcessor
from .quarto_slides_preprocessor import make_quarto_slides_preprocessor
from .syllabus_tags import SyllabusTagProcessor
from ..error_helpers import MissingFilesError
from ..resources import ResourceManager
from ..util import parse_soup_from_xml
from ..xml_processing.assignment_group_tags import AssignmentGroupTagProcessor
from ..xml_processing.group_category_tags import GroupCategoryTagProcessor
from ..xml_processing.module_tags import ModuleTagProcessor
from ..xml_processing.page_tags import PageTagProcessor
from ..xml_processing.quiz_tags import QuizTagProcessor
from ..xml_processing.tag_preprocessors import make_image_preprocessor, make_file_preprocessor, \
    make_zip_preprocessor, make_include_preprocessor, make_link_preprocessor, make_markdown_page_preprocessor, \
    make_course_settings_preprocessor


def _walk_xml(tag, tag_processors, missing: list[str] | None = None):
    """
    Call each tag's processor, then descend into its children.

    Given `missing`, a FileNotFoundError from a processor is recorded there
    and the walk continues, so one run names every absent file rather than
    only the first. That tag is left as it is and not descended into, since
    the content it would have pulled in is not there to examine; the caller
    raises once the walk finishes, so the half-built tree is never used.

    Only FileNotFoundError is gathered. Anything else means the template could
    not be understood rather than that a file is absent, and there is no
    reason to believe the rest of the walk is meaningful, so it propagates at
    once. Without `missing`, so does a FileNotFoundError.
    """
    if not hasattr(tag, 'children'):
        return
    for child in tag.children:
        if hasattr(child, 'name') and child.name in tag_processors:
            processor = tag_processors[child.name]
            try:
                processor(child)
            except MissingFilesError as e:
                if missing is None:
                    raise
                # Raised by a nested preprocess_xml: one file per entry already.
                missing.extend(e.messages)
                continue
            except FileNotFoundError as e:
                if missing is None:
                    raise
                missing.append(str(e))
                continue
        _walk_xml(child, tag_processors, missing)


def preprocess_xml(
        deploy_root: Path,
        parent: Path,
        text: str,
        resources: ResourceManager,
        process_file: Callable
) -> str:
    """
    Preprocess the XML/HTML text to handle special content tags
    e.g. links, images, files, includes, etc.

    Returns modified XML that uses local IDs in the links.
    These IDs will be replaced with real Canvas IDs during deployment.
    """
    tag_preprocessors = {
        'course-settings': make_course_settings_preprocessor(deploy_root, parent, resources),
        'img': make_image_preprocessor(deploy_root, parent, resources),
        'file': make_file_preprocessor(deploy_root, parent, resources),
        'zip': make_zip_preprocessor(deploy_root, parent, resources),
        'include': make_include_preprocessor(deploy_root, parent, process_file),
        'course-link': make_link_preprocessor(),
        'md-page': make_markdown_page_preprocessor(deploy_root, parent, process_file),
        'mermaid': make_mermaid_preprocessor(parent, resources),
        'quarto-slides': make_quarto_slides_preprocessor(deploy_root, parent, resources)
    }

    soup = parse_soup_from_xml(text)

    missing: list[str] = []
    _walk_xml(soup, tag_preprocessors, missing)
    if missing:
        raise MissingFilesError(missing)

    return str(soup)


def process_canvas_xml(resources: ResourceManager, text: str):
    """
    Process XML/HTML text into a DTOs that represent
    the content to be deployed to Canvas.

    :param text: The XML/HTML text to be processed
    :returns: Populated ResourceManager
    """

    # -- Strategy --
    # The algorithm walks the tree and calls the appropriate processor on each tag
    # Each custom tag is processed by a bespoke processor
    # The tag processor returns Canvas JSON
    # If the tag is not processed (no assigned processor),
    #  the algorithm recurses on its children

    tag_processors = {
        'announcement': AnnouncementTagProcessor(resources),
        'assignment': AssignmentTagProcessor(resources),
        'group': AssignmentGroupTagProcessor(resources),
        'group-category': GroupCategoryTagProcessor(resources),
        'module': ModuleTagProcessor(resources),
        'navigation': NavigationTagProcessor(resources),
        'page': PageTagProcessor(resources),
        'quiz': QuizTagProcessor(resources),
        'syllabus': SyllabusTagProcessor(resources)
    }

    soup = parse_soup_from_xml(text)
    _walk_xml(soup, tag_processors)

    return resources
