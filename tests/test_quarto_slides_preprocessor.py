from copy import deepcopy

from bs4 import BeautifulSoup

from mdxcanvas.deploy.checksums import compute_md5
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


def test_quarto_slides_checksum_changes_when_an_image_changes(tmp_path):
    slide_file = tmp_path / "lecture.qmd"
    slide_file.write_text("---\nformat: revealjs\n---\n\n![](images/diagram.svg)\n")
    images = tmp_path / "images"
    images.mkdir()
    image = images / "diagram.svg"
    image.write_text("<svg />")
    resources = ResourceManager()

    preprocess_xml(
        deploy_root=tmp_path,
        parent=tmp_path,
        text='<quarto-slides path="lecture.qmd" />',
        resources=resources,
        process_file=lambda *_args, **_kwargs: "",
    )
    data = resources["quarto-slides", "lecture.slides.html"]["data"]
    original_checksum = compute_md5(data, tmp_path)

    image.write_text("<svg><circle /></svg>")

    assert compute_md5(data, tmp_path) != original_checksum


def test_quarto_slides_checksum_is_independent_of_dependency_order(tmp_path):
    slide_file = tmp_path / "lecture.qmd"
    slide_file.write_text("---\nformat: revealjs\n---\n\n![](images/diagram.svg)\n")
    images = tmp_path / "images"
    images.mkdir()
    (images / "diagram.svg").write_text("<svg />")
    resources = ResourceManager()

    preprocess_xml(
        deploy_root=tmp_path,
        parent=tmp_path,
        text='<quarto-slides path="lecture.qmd" />',
        resources=resources,
        process_file=lambda *_args, **_kwargs: "",
    )
    data = resources["quarto-slides", "lecture.slides.html"]["data"]
    reordered_data = deepcopy(data)
    reordered_data["checksum_paths"] = list(reversed(data["checksum_paths"]))

    assert compute_md5(reordered_data, tmp_path) == compute_md5(data, tmp_path)


def test_quarto_slides_checksum_ignores_unrelated_project_files(tmp_path):
    (tmp_path / "_quarto.yml").write_text("project:\n  type: default\n")
    slide_file = tmp_path / "slides" / "lecture.qmd"
    slide_file.parent.mkdir()
    slide_file.write_text("---\nformat: revealjs\n---\n")
    unrelated_file = tmp_path / "assignments" / "homework.md"
    unrelated_file.parent.mkdir()
    unrelated_file.write_text("Original assignment")
    resources = ResourceManager()

    preprocess_xml(
        deploy_root=tmp_path,
        parent=tmp_path,
        text='<quarto-slides path="slides/lecture.qmd" />',
        resources=resources,
        process_file=lambda *_args, **_kwargs: "",
    )
    data = resources["quarto-slides", "lecture.slides.html"]["data"]
    original_checksum = compute_md5(data, tmp_path)

    unrelated_file.write_text("Updated assignment")

    assert compute_md5(data, tmp_path) == original_checksum


def test_quarto_slides_checksum_tracks_explicit_dependencies(tmp_path):
    slides = tmp_path / "slides"
    slides.mkdir()
    (slides / "lecture.qmd").write_text("---\nformat: revealjs\n---\n")
    data_dir = slides / "data"
    data_dir.mkdir()
    data_file = data_dir / "results.csv"
    data_file.write_text("score\n10\n")
    resources = ResourceManager()

    preprocess_xml(
        deploy_root=tmp_path,
        parent=tmp_path,
        text='<quarto-slides path="slides/lecture.qmd" dependencies="data/*.csv" />',
        resources=resources,
        process_file=lambda *_args, **_kwargs: "",
    )
    data = resources["quarto-slides", "lecture.slides.html"]["data"]
    original_checksum = compute_md5(data, tmp_path)

    data_file.write_text("score\n20\n")

    assert compute_md5(data, tmp_path) != original_checksum


def test_quarto_slides_checksum_tracks_config_and_extensions(tmp_path):
    config = tmp_path / "_quarto.yml"
    config.write_text("project:\n  type: default\n")
    slide_file = tmp_path / "slides" / "lecture.qmd"
    slide_file.parent.mkdir()
    slide_file.write_text("---\nformat: revealjs\n---\n")
    extension_file = tmp_path / "_extensions" / "course" / "extension.yml"
    extension_file.parent.mkdir(parents=True)
    extension_file.write_text("title: Course extension\n")
    resources = ResourceManager()

    preprocess_xml(
        deploy_root=tmp_path,
        parent=tmp_path,
        text='<quarto-slides path="slides/lecture.qmd" />',
        resources=resources,
        process_file=lambda *_args, **_kwargs: "",
    )
    data = resources["quarto-slides", "lecture.slides.html"]["data"]
    original_checksum = compute_md5(data, tmp_path)

    config.write_text("project:\n  type: website\n")
    config_checksum = compute_md5(data, tmp_path)
    extension_file.write_text("title: Updated extension\n")

    assert config_checksum != original_checksum
    assert compute_md5(data, tmp_path) != config_checksum
