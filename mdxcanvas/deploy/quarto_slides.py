import base64
import mimetypes
import re
import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urlparse

from canvasapi.course import Course

from .file import deploy_file
from ..our_logging import get_logger
from ..resources import FileData
from ..resources import FileInfo
from ..resources import QuartoSlidesData
from ..util import relative_to_abs

logger = get_logger()


def _copy_quarto_dependencies(quarto_root: Path, temp_quarto_root: Path) -> None:
    """Copy the Quarto project files needed to render a slide deck."""
    temp_quarto_root.mkdir(parents=True, exist_ok=True)

    for config_name in ("_quarto.yaml", "_quarto.yml"):
        config = quarto_root / config_name
        if config.exists():
            shutil.copy2(config, temp_quarto_root / config_name)

    extensions = quarto_root / "_extensions"
    if extensions.exists():
        shutil.copytree(
            extensions,
            temp_quarto_root / "_extensions",
            dirs_exist_ok=True,
        )


def _copy_slide_to_temp(slide_file: Path, quarto_root: Path, temp_quarto_root: Path) -> Path:
    """Copy the target slide source into the same relative location under temp."""
    relative_slide_file = slide_file.relative_to(quarto_root)
    temp_slide_file = temp_quarto_root / relative_slide_file
    temp_slide_file.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(slide_file, temp_slide_file)
    return temp_slide_file


def _run_quarto_render(data: QuartoSlidesData, tmpdir: Path, deploy_root: Path) -> Path:
    # Copy just the target slide and Quarto project dependencies into a temp
    # project, render there, bundle the rendered HTML in place, and return the
    # temp HTML path for deployment.
    slide_file = relative_to_abs(Path(data['path']), deploy_root)
    quarto_root = relative_to_abs(Path(data['root_path']), deploy_root)
    temp_quarto_root = tmpdir.absolute()

    _copy_quarto_dependencies(quarto_root, temp_quarto_root)
    temp_slide_file = _copy_slide_to_temp(slide_file, quarto_root, temp_quarto_root)

    output_name = str(data['slides_name'])
    temp_output_file = (temp_slide_file.parent / output_name).absolute()

    cmd = [
        'quarto', 'render', temp_slide_file.name,
        '--output', output_name,
        '--log-level', 'info',
        '--no-cache'
    ]
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,  # decode to str instead of bytes
        cwd=temp_slide_file.parent
    )
    log = logger.debug
    if result.returncode != 0 or not temp_output_file.exists():
        log = logger.warning
    log(' '.join(cmd))
    log(result.stdout)
    log(result.stderr)

    result.check_returncode()  # raises CalledProcessError if non-zero
    if not temp_output_file.exists():
        raise FileNotFoundError('Missing quarto render output file: ' + str(temp_output_file))

    html = temp_output_file.read_text()
    html = _bundle_js(html, temp_output_file.parent)
    html = _inline_css(html, temp_output_file.parent)
    html = _inline_assets(html, temp_output_file.parent)
    temp_output_file.write_text(html)

    return temp_output_file


def _is_external(url: str) -> bool:
    if url.startswith("data:"):
        return True
    parsed = urlparse(url)
    return bool(parsed.scheme) and parsed.scheme not in ("", "file")


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _bundle_js(html: str, base_dir: Path) -> str:
    """Bundle RevealJS dependencies into the HTML so it functions as a standalone file"""
    src_attr_pattern = re.compile(
        r"""\bsrc\s*=\s*(?:"([^"]+)"|'([^']+)'|([^\s"'=<>`]+))""",
        re.IGNORECASE,
    )

    def repl(match: re.Match[str]) -> str:
        attrs = match.group(1)
        src_match = src_attr_pattern.search(attrs)
        if not src_match:
            return match.group(0)
        src = next(group for group in src_match.groups() if group is not None)
        if _is_external(src):
            return match.group(0)
        asset = (base_dir / src).resolve()
        if not asset.exists():
            return match.group(0)
        js = _read_text(asset)
        return f"<script>\n{js}\n</script>"

    pattern = re.compile(r"<script\b([^>]*)>\s*</script>", flags=re.IGNORECASE)
    return pattern.sub(repl, html)


def _data_url(url: str, base_dir: Path, source_dir: Path | None = None) -> str | None:
    """Return a data URL for a local asset, or None for non-local assets."""
    url = url.strip().strip(" \\\"'")
    if _is_external(url) or url.startswith('#'):
        return None

    # Query strings and fragments are not part of the filesystem path, but
    # should not prevent us from recognizing a local asset.
    parsed = urlparse(url)
    asset = ((source_dir or base_dir) / parsed.path).resolve()
    if not asset.is_file():
        return None

    mime, _ = mimetypes.guess_type(asset.name)
    mime = mime or "application/octet-stream"
    data = base64.b64encode(asset.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{data}"


def _inline_css_urls(css: str, stylesheet: Path, base_dir: Path) -> str:
    def repl(match: re.Match[str]) -> str:
        url = match.group(1).strip().strip(" \\\"'")
        data_url = _data_url(url, base_dir, stylesheet.parent)
        return f'url("{data_url}")' if data_url else match.group(0)

    return re.sub(r"url\(\s*([^)]*?)\s*\)", repl, css, flags=re.IGNORECASE)


def _inline_css(html: str, base_dir: Path) -> str:
    def repl(match: re.Match[str]) -> str:
        attrs = match.group(0)
        href_match = re.search(r"\bhref\s*=\s*(['\"])(.*?)\1", attrs, re.IGNORECASE)
        if not href_match:
            return attrs
        href = href_match.group(2)
        asset = (base_dir / urlparse(href).path).resolve()
        if _data_url(href, base_dir) is None or not asset.is_file():
            return attrs
        css = _inline_css_urls(_read_text(asset), asset, base_dir)
        return f"<style>\n{css}\n</style>"

    # Quarto does not guarantee the order of link attributes or quote style.
    def is_stylesheet(match: re.Match[str]) -> str:
        attrs = match.group(0)
        rel_match = re.search(r"\brel\s*=\s*(['\"])(.*?)\1", attrs, re.IGNORECASE)
        if rel_match and "stylesheet" in rel_match.group(2).lower().split():
            return repl(match)
        return attrs

    pattern = re.compile(r"<link\b[^>]*>", re.IGNORECASE)
    return pattern.sub(is_stylesheet, html)


def _inline_assets(html: str, base_dir: Path) -> str:
    def repl(match: re.Match[str]) -> str:
        attr, quote, url = match.group(1), match.group(2), match.group(3)
        data_url = _data_url(url, base_dir)
        if not data_url:
            return match.group(0)
        return f"{attr}={quote}{data_url}{quote}"

    # Inline image/script resources while leaving links between HTML pages
    # untouched. Stylesheets are handled separately by _inline_css.
    pattern = re.compile(
        r"<(?:img|script|source)\b[^>]*?\b(src)\s*=\s*(['\"])(.*?)\2",
        re.IGNORECASE,
    )
    return pattern.sub(repl, html)


def _build_slides(data: QuartoSlidesData, tmpdir: Path, deploy_root: Path) -> FileData:
    output_file = _run_quarto_render(data, tmpdir, deploy_root)

    return FileData(
        path=(p := str(output_file)),
        checksum_paths=[p],
        canvas_folder=data.get('canvas_folder'),
        lock_at=data.get('lock_at'),
        unlock_at=data.get('unlock_at')
    )


def deploy_quarto_slides(course: Course, data: QuartoSlidesData, deploy_root: Path) -> tuple[FileInfo, None]:
    with TemporaryDirectory() as tmpdir:
        filedata = _build_slides(data, Path(tmpdir), deploy_root)

        return deploy_file(course, filedata, deploy_root)
