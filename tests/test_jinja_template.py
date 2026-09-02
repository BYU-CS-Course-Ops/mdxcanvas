import uuid
from pathlib import Path
from tempfile import NamedTemporaryFile
from textwrap import dedent

from mdxcanvas.text_processing.jinja_processing import process_jinja


def test_split_list(tmp_path):
    template_str = """
    {% for name in split_list(data["NAMES"]) %}{{ name }}
    {% endfor %}
    """
    expected_output = """
    John
    Juan
    Jack
    
    """
    actual_output = process_jinja(
        template_str,
        global_args={
            "data": {
                "NAMES": "John;Juan;Jack"
            }
        },
        parent_folder=tmp_path,
    )
    assert actual_output == expected_output


def test_glob():
    uid = str(uuid.uuid4())
    with NamedTemporaryFile(suffix=f'.{uid}.jinja') as tmpf:
        tmpf.write(dedent(
            f"""
            {{% for name in glob('*.{uid}.jinja') %}}{{{{ name }}}}
            {{% endfor %}}
            """
        ).encode())
        tmpf.seek(0)
        tmpf.flush()

        tmppath = Path(tmpf.name)
        print(list(tmppath.parent.glob(f'*.{uid}.jinja')))
        expected_output = dedent(
            f"""
            {tmppath.name}
            """
        )
        actual_output = process_jinja(
            tmppath.read_text(),
            {},
            tmppath.parent,
        )
        assert actual_output == expected_output
