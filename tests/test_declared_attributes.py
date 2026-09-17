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
