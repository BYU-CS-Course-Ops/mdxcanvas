from pathlib import Path

from bs4 import BeautifulSoup

from mdxcanvas.deploy.quarto_slides import _build_slides, _inline_assets, _inline_css


def test_inline_quarto_stylesheet_and_assets(tmp_path):
    styles = tmp_path / "styles"
    images = tmp_path / "images"
    styles.mkdir()
    images.mkdir()
    (images / "logo.svg").write_text("<svg />")
    (styles / "slides.css").write_text(
        "body { background-image: url('../images/logo.svg'); }"
    )

    html = (
        "<link href='styles/slides.css' rel='stylesheet'>"
        "<img alt='logo' src=\"images/logo.svg\">"
        "<img src='https://example.com/logo.svg'>"
    )

    bundled = _inline_assets(_inline_css(html, tmp_path), tmp_path)

    assert "<link" not in bundled
    assert bundled.count("data:image/svg+xml;base64,") == 2
    assert '<img alt=\'logo\' src="data:image/svg+xml;base64,' in bundled
    assert "https://example.com/logo.svg" in bundled


def test_inline_assets_does_not_rewrite_html_links(tmp_path):
    (tmp_path / "next.html").write_text("next")

    html = '<a href="next.html">Next</a>'

    assert _inline_assets(html, tmp_path) == html


def test_built_slides_embed_images_referenced_by_qmd(tmp_path):
    project = tmp_path / "project"
    images = project / "images"
    images.mkdir(parents=True)
    (images / "diagram.svg").write_text("<svg xmlns='http://www.w3.org/2000/svg' />")
    (project / "lecture.qmd").write_text(
        "---\nformat: revealjs\n---\n\n![Diagram](images/diagram.svg)\n"
    )

    slides = _build_slides(
        {
            "path": "lecture.qmd",
            "root_path": ".",
            "slides_name": "lecture.slides.html",
            "canvas_folder": None,
            "lock_at": None,
            "unlock_at": None,
        },
        tmp_path / "output",
        project,
    )
    html = Path(slides["path"]).read_text()

    image = BeautifulSoup(html, "html.parser").find("img")
    assert image is not None
    source = image.get("src") or image.get("data-src")
    assert source.startswith("data:image/svg+xml;base64,")
