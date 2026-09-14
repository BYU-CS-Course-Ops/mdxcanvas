import csv
import json
import re
import traceback
from pathlib import Path

import jinja2.exceptions
import markdowndata
import yaml
from jinja2 import Environment, FileSystemLoader

from ..our_logging import get_logger
from ..processing_context import get_current_file_str

logger = get_logger()


def _get_args(args_path: Path, global_args: dict) -> dict | list:
    if args_path.suffix == '.jinja':
        content = _render_template(args_path.read_text(), global_args, args_path.parent)
        args_path = Path(args_path.stem)
    else:
        content = args_path.read_text()

    if args_path.suffix == '.json':
        return json.loads(content)

    elif args_path.suffix == '.csv':
        return list(csv.DictReader(content.splitlines()))

    elif args_path.suffix in ['.md', '.mdd']:
        return markdowndata.loads(content)

    elif args_path.suffix in ['.yaml', '.yml']:
        return yaml.safe_load(content)

    else:
        raise NotImplementedError('Args file of type: ' + args_path.suffix)


def _render_template(
        template: str,
        global_args: dict,
        parent_folder: Path,
        args_path: Path | None = None,
        args: dict | list | None = None,
        templates: list[Path] | None = None
) -> str:
    loader_paths = [parent_folder, args_path, *(templates or [])]
    loader_paths = [p for p in loader_paths if p]

    env = Environment(
        loader=FileSystemLoader(loader_paths),
    )

    context = {
        "zip": zip,
        "enumerate": enumerate,
        "split_list": lambda x: x.split(";"),
        "exists": lambda path: (parent_folder / path).exists(),
        "read_file": lambda f: (parent_folder / f).absolute().read_text(),
        "glob": lambda *args, **kwargs: list(sorted(str(f.relative_to(parent_folder)) for f in
                                         parent_folder.glob(*args, **kwargs))),
        "parent": lambda path: str(Path(path).parent),
        "load": lambda path: _get_args((parent_folder / path).absolute(), global_args),
        "debug": lambda msg: logger.debug(msg),
        "get_arg": lambda *args: global_args.get(*args),
        # "grep": lambda pattern, string, *args: m.groups() if (m := re.search(pattern, string, *args)) else None
        "search": re.search
    }

    if global_args:
        context |= global_args

    if args:
        context |= {"args": args}

    try:
        jj_template = env.from_string(template)
        return jj_template.render(context)
    
    except Exception as ex:
        error_message = f'Error processing {get_current_file_str()}'
        match = re.search(
            r'File "<template>", line (\d+), in top-level template code',
            traceback.format_exc(),
        )
        if match:
            line_number = int(match.group(1))
            template_lines = template.splitlines()
            if 1 <= line_number <= len(template_lines):
                error_message += f' (line {line_number}: {template_lines[line_number - 1].strip()})'

        raise Exception(error_message, ex) from ex


def process_jinja(
        template: str,
        global_args: dict,
        parent_folder: Path,
        args_path: Path | None = None,
        templates: list[Path] | None = None
) -> str:
    if args_path:
        args = _get_args(args_path, global_args)
    else:
        args = {}

    return _render_template(
        template,
        global_args,
        parent_folder,
        args_path=args_path,
        args=args,
        templates=templates
    )
