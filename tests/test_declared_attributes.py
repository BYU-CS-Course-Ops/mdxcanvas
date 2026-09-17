"""Attributes that were declared or parsed in a way Canvas cannot use.

Each test here corresponds to a field that a course could set, deploy green,
and never see take effect -- the failure mode being that nothing is logged and
nothing reaches Canvas.
"""
import pytest
from bs4 import BeautifulSoup

from mdxcanvas.xml_processing.quiz_questions import parse_file_upload_question


def _tag(xml: str, name: str):
    return BeautifulSoup(xml, 'html.parser').find(name)


def test_file_upload_question_honours_points():
    """Every other question type maps `points` to `points_possible` through
    mostly_common_fields; this one parsed with default_fields alone, so the
    attribute was dropped with an Unprocessed_fields warning."""
    question = _tag("""
    <question id="q1" type="file-upload" points="5">
        Attach your written work.
    </question>
    """, 'question')

    parsed = parse_file_upload_question(question)[0]

    assert parsed['points_possible'] == 5


def test_file_upload_question_defaults_to_one_point():
    """mostly_common_fields carries the default, so omitting `points` behaves
    the way every other question type does rather than sending nothing."""
    question = _tag("""
    <question id="q1" type="file-upload">
        Attach your written work.
    </question>
    """, 'question')

    parsed = parse_file_upload_question(question)[0]

    assert parsed['points_possible'] == 1


def test_announcement_can_be_scoped_to_sections():
    """is_section_specific and specific_sections were named in a comment and
    declared nowhere, so setting them deployed a course-wide announcement that
    looked scoped."""
    from mdxcanvas.resources import ResourceManager
    from mdxcanvas.xml_processing.announcement_tags import AnnouncementTagProcessor

    resources = ResourceManager()
    AnnouncementTagProcessor(resources)(_tag("""
    <announcement id="a1" title="Sign-up" publish_date="Jan 5, 2026, 9:00 AM"
                  is_section_specific="true" specific_sections="1234,5678">
        Please sign up.
    </announcement>
    """, 'announcement'))

    data = next(iter(resources.values()))['data']
    assert data['is_section_specific'] is True
    assert data['specific_sections'] == '1234,5678'


def test_external_tool_module_items_are_not_supported():
    """Documents current behaviour rather than asserting it is right.

    `externaltool` is in _module_item_type_casing, so it reads as a supported
    type, but no branch handles it and it reaches the NotImplementedError. That
    also makes the `iframe` attribute unreachable: it is declared for every
    module item, and Canvas only honours it on an ExternalTool launch.

    Delete this test when ExternalTool items are implemented.
    """
    from mdxcanvas.resources import ResourceManager
    from mdxcanvas.xml_processing.module_tags import ModuleTagProcessor

    module = _tag("""
    <module id="m1" title="Week 1">
        <item type="ExternalTool" id="tool1" iframe="width=800,height=600"/>
    </module>
    """, 'module')

    with pytest.raises(NotImplementedError, match="ExternalTool"):
        ModuleTagProcessor(ResourceManager())(module)
