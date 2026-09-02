import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unicodedata

import requests
from canvasapi.course import Course

from .file import get_file, deploy_file
from ..our_logging import get_logger
from ..resources import CanvasResource, FileData, MermaidData, NavigationData, QuartoSlidesData, SyllabusData, ZipFileData
from ..util import to_relative_posix, relative_to_abs

logger = get_logger()

MD5_FILE_NAME = '_md5sums.json'


def _compute_checksum_of_path(resource_path: Path) -> bytes:
    """Compute checksum of file-tree identified by path"""

    if resource_path.is_file():
        return hashlib.md5(resource_path.read_bytes()).hexdigest().encode('utf-8')

    if resource_path.is_dir():
        file_digests = []
        for file_path in sorted(p for p in resource_path.glob('*')):
            file_digests.append(_compute_checksum_of_path(file_path))

        return hashlib.md5(b''.join(file_digests)).hexdigest().encode('utf-8')

    raise FileNotFoundError(f'Path does not exist or is not a file/directory: {resource_path}')


def _normalize_json_for_hashing(data: dict) -> str:
    """Normalize JSON data for consistent hashing across platforms"""
    json_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
    normalized = unicodedata.normalize('NFC', json_str).replace('\r\n', '\n').replace('\r', '\n')
    return normalized


def compute_md5(obj: CanvasResource | FileData | ZipFileData | MermaidData | NavigationData | QuartoSlidesData | SyllabusData,
                deploy_root: Path) -> str:
    # Keys that should not affect change detection:
    # - canvas_id: injected by the deployment system at runtime
    FILTERED_KEYS = {'canvas_id'}

    hashable = b''

    # Hash file *contents* from checksum_paths
    paths = obj.get('checksum_paths', [])
    for path in sorted(paths):
        hashable += _compute_checksum_of_path(relative_to_abs(Path(path), deploy_root))

    # Build a dict for JSON hashing
    filtered = {k: v for k, v in obj.items() if k not in FILTERED_KEYS}

    # Normalize the JSON string to ensure consistent encoding and line endings across platforms
    json_str = _normalize_json_for_hashing(filtered)
    hashable += json_str.encode('utf-8')

    return hashlib.md5(hashable).hexdigest()


class MD5Sums:
    """
    Format:
    {
        "mdxcanvas_version": <str>,
        "resources": {
            "{rtype}|{rid}": {
                "canvas_info": {
                    "id":  <str>,
                    "uri": <str | None>,
                    "url": <str | None>
                },
                "checksum": <str>
            }
        }
    }
    """

    def __init__(self, course: Course, deploy_root: Path):
        self._version = None
        self._course = course
        self._deploy_root = deploy_root

    def _download_md5s(self):
        md5_file = get_file(self._course, MD5_FILE_NAME)
        if md5_file is None:
            self._version = None
            self._md5s = {}
        else:
            data = json.loads(requests.get(md5_file.url).text)
            if 'resources' in data:
                # New nested format
                self._version = data.get('mdxcanvas_version')
                self._md5s = {
                    tuple(k.split('|', maxsplit=1)): v
                    for k, v in data['resources'].items()
                }
            else:
                # Old flat format — no version existed in this format
                self._version = None
                self._md5s = {
                    tuple(k.split('|', maxsplit=1)): v
                    for k, v in data.items()
                }
        self._save_md5s()

    def _save_md5s(self):
        data = {
            'mdxcanvas_version': self._version,
            'resources': {'|'.join(k): v for k, v in self._md5s.items()}
        }
        with TemporaryDirectory() as tmpdir:
            tmpfile = Path(tmpdir) / MD5_FILE_NAME
            tmpfile.write_text(_normalize_json_for_hashing(data), encoding='utf-8')
            deploy_file(self._course, FileData(
                path=(p := to_relative_posix(tmpfile.absolute(), self._deploy_root)),
                checksum_paths=[p],
                canvas_folder="_md5s",
                lock_at=None, unlock_at=None
            ), self._deploy_root)

    def items(self):
        return self._md5s.items()

    def get(self, item, *args, **kwargs):
        return self._md5s.get(item, *args, **kwargs)

    def add_mdxcanvas_version(self, version):
        self._version = version

    def get_mdxcanvas_version(self):
        return self._version

    def has_mdxcanvas_version(self):
        return self._version is not None

    def get_canvas_info(self, item):
        return self.get(item, {}).get('canvas_info')

    def has_canvas_info(self, item):
        return self.get_canvas_info(item) is not None

    def get_checksum(self, item):
        entry = self.get(item)
        return entry.get('checksum') if entry else None

    def has_checksum(self, item):
        return self.get_checksum(item) is not None

    def remove(self, item):
        if item in self._md5s:
            del self._md5s[item]

    def __getitem__(self, item):
        # Act like a dictionary
        return self._md5s[item]

    def __setitem__(self, key, value):
        self._md5s[key] = value

    def __enter__(self):
        self._download_md5s()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._save_md5s()
