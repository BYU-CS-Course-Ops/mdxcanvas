from mdxcanvas.deploy.quarto_slides import _inline_assets, _inline_css


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
    assert "https://example.com/logo.svg" in bundled


def test_inline_assets_does_not_rewrite_html_links(tmp_path):
    (tmp_path / "next.html").write_text("next")

    html = '<a href="next.html">Next</a>'

    assert _inline_assets(html, tmp_path) == html
