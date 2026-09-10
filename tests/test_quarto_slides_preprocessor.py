from bs4 import BeautifulSoup

from mdxcanvas.resources import ResourceManager
from mdxcanvas.xml_processing.xml_processing import preprocess_xml


def test_quarto_slides_link_downloads_file_from_canvas(tmp_path):
    slide_file = tmp_path / "lecture.qmd"
    slide_file.write_text("---\nformat: revealjs\n---\n")
    resources = ResourceManager()

    html = preprocess_xml(
        deploy_root=tmp_path,
        parent=tmp_path,
        text='<quarto-slides path="lecture.qmd" />',
        resources=resources,
        process_file=lambda *_args, **_kwargs: "",
    )

    link = BeautifulSoup(html, "html.parser").a

    assert link is not None
    assert link["href"] == "__@@quarto-slides||lecture.slides.html||url@@__?download_frd=1"
    assert link["target"] == "_blank"
    assert link["rel"] == ["noopener", "noreferrer"]
    assert "class" not in link.attrs
    assert link.string == "lecture.slides.html"
