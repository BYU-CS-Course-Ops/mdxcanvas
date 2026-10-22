"""
A template that names several missing files reports all of them at once.

Stopping at the first one turns a single mistake into one run per broken
reference. A folder that moved and left three references behind cost three
full dry runs to find, because each run could only ever name the earliest.
"""

import pytest

from mdxcanvas.error_helpers import MissingFilesError
from mdxcanvas.resources import ResourceManager
from mdxcanvas.xml_processing.xml_processing import preprocess_xml


def _preprocess(tmp_path, text, process_file=None):
    return preprocess_xml(
        deploy_root=tmp_path,
        parent=tmp_path,
        text=text,
        resources=ResourceManager(),
        process_file=process_file or (lambda *_args, **_kwargs: ""),
    )


def test_every_missing_include_is_named_not_only_the_first(tmp_path):
    with pytest.raises(MissingFilesError) as caught:
        _preprocess(
            tmp_path,
            '<page>'
            '<include path="first.md" />'
            '<include path="second.md" />'
            '<include path="third.md" />'
            '</page>',
        )

    assert len(caught.value.messages) == 3
    message = str(caught.value)
    for name in ("first.md", "second.md", "third.md"):
        assert name in message


def test_the_count_leads_the_message(tmp_path):
    with pytest.raises(MissingFilesError) as caught:
        _preprocess(
            tmp_path,
            '<page><include path="a.md" /><include path="b.md" /></page>',
        )

    assert str(caught.value).startswith("2 missing files:")


def test_one_missing_file_is_not_reported_as_plural(tmp_path):
    with pytest.raises(MissingFilesError) as caught:
        _preprocess(tmp_path, '<page><include path="only.md" /></page>')

    assert str(caught.value).startswith("1 missing file:")


def test_a_present_file_either_side_of_a_missing_one_is_still_processed(tmp_path):
    (tmp_path / "there.md").write_text("here\n")

    with pytest.raises(MissingFilesError) as caught:
        _preprocess(
            tmp_path,
            '<page>'
            '<include path="there.md" />'
            '<include path="gone.md" />'
            '<include path="there.md" />'
            '</page>',
        )

    # The walk did not stop, and the file that exists raised nothing.
    assert len(caught.value.messages) == 1
    assert "gone.md" in str(caught.value)


def test_the_same_missing_file_named_twice_is_reported_once(tmp_path):
    """
    A shared file included by many pages produces one identical message per
    page. Repeating it buries the other problems in the list.
    """
    with pytest.raises(MissingFilesError) as caught:
        _preprocess(
            tmp_path,
            '<page>'
            '<include path="shared.md" />'
            '<include path="shared.md" />'
            '<include path="other.md" />'
            '</page>',
        )

    assert len(caught.value.messages) == 2
    assert str(caught.value).startswith("2 missing files:")


def test_a_missing_image_is_gathered_like_a_missing_include(tmp_path):
    """
    The image, file and zip tags reported a missing file as a ValueError,
    which the gathering walk does not catch, so one absent image still
    stopped everything. They name an absent file like the rest.
    """
    with pytest.raises(MissingFilesError) as caught:
        _preprocess(
            tmp_path,
            '<page>'
            '<img src="gone.png" />'
            '<include path="also-gone.md" />'
            '</page>',
        )

    assert len(caught.value.messages) == 2
    message = str(caught.value)
    assert "gone.png" in message
    assert "also-gone.md" in message


def test_a_missing_file_is_still_a_filenotfounderror(tmp_path):
    """Callers that already catch FileNotFoundError keep working."""
    with pytest.raises(FileNotFoundError):
        _preprocess(tmp_path, '<page><include path="gone.md" /></page>')


def test_everything_resolving_raises_nothing(tmp_path):
    (tmp_path / "there.md").write_text("here\n")

    html = _preprocess(tmp_path, '<page><include path="there.md" /></page>')

    assert html is not None


def test_an_error_that_is_not_a_missing_file_still_stops_the_walk(tmp_path):
    """
    Gathering is for absent files only. Anything else means the template was
    not understood, and the rest of the walk is not worth trusting.
    """
    seen = []

    def explode(*_args, **_kwargs):
        seen.append(1)
        raise ValueError("this template makes no sense")

    (tmp_path / "there.md").write_text("here\n")

    with pytest.raises(ValueError):
        _preprocess(
            tmp_path,
            '<page>'
            '<include path="there.md" />'
            '<include path="there.md" />'
            '</page>',
            process_file=explode,
        )

    assert seen == [1], "the walk carried on past an error it should have stopped at"
