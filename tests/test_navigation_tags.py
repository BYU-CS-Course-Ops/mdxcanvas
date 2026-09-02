from pathlib import Path

import pytest

from mdxcanvas.processing_context import FileContext
from mdxcanvas.resources import ResourceManager
from mdxcanvas.xml_processing.xml_processing import process_canvas_xml


def process_navigation(xml: str, source: Path | None = None) -> ResourceManager:
    resources = ResourceManager()
    with FileContext(source or Path("course.xml")):
        process_canvas_xml(resources, xml)
    return resources


def test_navigation_preserves_tab_source_order_and_registers_one_resource(tmp_path):
    source = tmp_path / "course.xml"

    resources = process_navigation(
        """
        <course>
          <navigation>
            <tab name="Assignments" />
            <tab name="External Tool" />
            <tab name="Pages" />
          </navigation>
        </course>
        """,
        source,
    )

    assert resources[("navigation", "navigation")] == {
        "type": "navigation",
        "id": "navigation",
        "data": {"tabs": ["Assignments", "External Tool", "Pages"]},
        "content_path": str(source.resolve()),
    }


def test_empty_navigation_registers_an_authoritative_empty_resource():
    resources = process_navigation("<course><navigation /></course>")

    assert resources[("navigation", "navigation")]["data"] == {"tabs": []}


def test_absent_navigation_registers_no_resource():
    resources = process_navigation("<course><page id='intro' title='Intro'>Hello</page></course>")

    assert ("navigation", "navigation") not in resources


@pytest.mark.parametrize(
    ("xml", "diagnostic"),
    [
        ("<navigation mode='authoritative' />", "mode"),
        ("<navigation><page /></navigation>", "page"),
        ("<navigation>unexpected text</navigation>", "unexpected text"),
        ("<navigation><tab /></navigation>", "name"),
        ("<navigation><tab name='' /></navigation>", "name"),
        ("<navigation><tab name='   ' /></navigation>", "name"),
        ("<navigation><tab name='Pages' hidden='true' /></navigation>", "hidden"),
        ("<navigation><tab name='Pages'>content</tab></navigation>", "content"),
        ("<navigation><tab name='Pages'><span /></tab></navigation>", "span"),
        (
            "<navigation><tab name='Pages' /><tab name='Pages' /></navigation>",
            "Pages",
        ),
    ],
)
def test_navigation_rejects_invalid_structure_with_source_context(tmp_path, xml, diagnostic):
    source = tmp_path / "invalid-navigation.xml"

    with pytest.raises(Exception) as exc_info:
        process_navigation(xml, source)

    message = str(exc_info.value)
    assert diagnostic in message
    assert str(source.resolve()) in message


def test_multiple_navigation_blocks_keep_existing_last_write_wins_behavior():
    resources = process_navigation(
        """
        <course>
          <navigation><tab name="Assignments" /></navigation>
          <navigation><tab name="Pages" /></navigation>
        </course>
        """
    )

    assert resources[("navigation", "navigation")]["data"] == {"tabs": ["Pages"]}
