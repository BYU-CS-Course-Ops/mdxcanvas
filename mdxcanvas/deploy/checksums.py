import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unicodedata

import requests
from canvasapi.course import Course

import mdxcanvas

from .file import get_file, deploy_file
from ..resources import CanvasResource, FileData, MermaidData, NavigationData, QuartoSlidesData, SyllabusData, ZipFileData
from ..util import relative_to_abs, to_relative_posix

MD5_FILE_NAME = "_md5sums.json"


def _compute_checksum_of_path(resource_path: Path) -> bytes:
    if resource_path.is_file():
        return hashlib.md5(resource_path.read_bytes()).hexdigest().encode()
    if resource_path.is_dir():
        return hashlib.md5(b"".join(_compute_checksum_of_path(path) for path in sorted(resource_path.glob("*")))).hexdigest().encode()
    raise FileNotFoundError(f"Path does not exist or is not a file/directory: {resource_path}")


def _normalize_json_for_hashing(data: dict) -> str:
    return unicodedata.normalize("NFC", json.dumps(data, sort_keys=True, ensure_ascii=False)).replace("\r\n", "\n").replace("\r", "\n")


def compute_md5(obj: CanvasResource | FileData | ZipFileData | MermaidData | NavigationData | QuartoSlidesData | SyllabusData,
                deploy_root: Path) -> str:
    hashable = b""
    for path in sorted(set(obj.get("checksum_paths", []))):
        hashable += unicodedata.normalize("NFC", path).encode() + b"\0"
        hashable += _compute_checksum_of_path(relative_to_abs(Path(path), deploy_root))
    filtered = {key: value for key, value in obj.items() if key not in {"canvas_id", "checksum_paths"}}
    hashable += _normalize_json_for_hashing(filtered).encode()
    return hashlib.md5(hashable).hexdigest()


class MD5Sums:
    def __init__(self, course: Course, deploy_root: Path, **_ignored):
        self._course = course
        self._deploy_root = deploy_root

    def load(self) -> dict:
        md5_file = get_file(self._course, MD5_FILE_NAME)
        if md5_file is None:
            return {"mdxcanvas_version": mdxcanvas.__version__, "resources": {}}
        return json.loads(requests.get(md5_file.url).text)

    def save(self, envelope: dict):
        with TemporaryDirectory() as tmpdir:
            tmpfile = Path(tmpdir) / MD5_FILE_NAME
            tmpfile.write_text(json.dumps(envelope, ensure_ascii=False), encoding="utf-8")
            deploy_file(self._course, FileData(
                path=to_relative_posix(tmpfile.absolute(), self._deploy_root),
                checksum_paths=[to_relative_posix(tmpfile.absolute(), self._deploy_root)],
                canvas_folder="_md5s", lock_at=None, unlock_at=None,
            ), self._deploy_root)
