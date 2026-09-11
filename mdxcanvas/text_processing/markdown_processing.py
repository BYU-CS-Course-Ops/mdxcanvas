import re
import textwrap
from pathlib import Path
from typing import Generator

import markdown as md
from bs4.element import NavigableString, PageElement, Tag, Comment
from pymdownx.highlight import makeExtension as makeCodehiliteExtension
from pymdownx.inlinehilite import makeExtension as makeInlineHiliteExtension
from pymdownx.superfences import makeExtension as makeSuperfencesExtension
from pymdownx.tilde import makeExtension as makeTildeExtension

from .inline_math import InlineMathExtension
from .mermaid_fence import make_mermaid_fence_shortcut
from ..util import parse_soup_from_xml

# Load CSS from file
_CSS_FILES = [Path(__file__).parent / 'mdxcanvas.css', Path(__file__).parent / 'github-light.css']
_CODE_BLOCK_CSS_CONTENT = "\n".join(file.read_text() for file in _CSS_FILES)
CODE_BLOCK_CSS = f'<style>\n{_CODE_BLOCK_CSS_CONTENT}\n</style>'


def replace_characters(text: str, replacements: dict[str, str]) -> str:
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def replace_problematic_characters(text: str, replacements: dict[str, str]) -> str:
    output_lines = []
    lines = iter(text.splitlines())

    # Matches inline code like `code`
    inline_code_pattern = re.compile(r'`([^`]+)`')

    for line in lines:
        if line.strip().startswith('```'):
            output_lines.append(line)
            for code_line in lines:
                output_lines.append(replace_characters(code_line, replacements))
                if code_line.strip().startswith('```'):
                    break
        elif inline_code_pattern.search(line):
            def replacer(match):
                code = match.group(1)
                if any(char in code for char in replacements):
                    return f"`{replace_characters(code, replacements)}`"
                return match.group(0)

            output_lines.append(inline_code_pattern.sub(replacer, line))
        else:
            output_lines.append(line)

    return '\n'.join(output_lines)


def process_markdown_text(text: str) -> str:
    dedented = textwrap.dedent(text)

    html = md.markdown(dedented, extensions=[
        'fenced_code',
        'tables',
        'attr_list',

        makeSuperfencesExtension(custom_fences=[
            {
                'name': 'mermaid',
                'class': 'mermaid',
                'format': make_mermaid_fence_shortcut(),
            }
        ]),

        # Use CSS classes for syntax highlighting (styled by CODE_BLOCK_CSS)
        makeCodehiliteExtension(noclasses=False),
        makeInlineHiliteExtension(css_class='highlight', style_plain_text='text'),

        # This allows for strikethrough with ~~text~~
        makeTildeExtension(subscript=False),

        # This preserves \(...\) inline math expressions
        #  so Canvas will render them with MathJax
        InlineMathExtension(),
    ])

    # Include CSS to override Canvas's pre block styling
    if '<div class="highlight">' in html or '<code class="highlight">' in html:
        html = CODE_BLOCK_CSS + html

    return html


def _form_blocks(tag: Tag, excluded: list[str], inline: list[str]
                 ) -> Generator[tuple[bool, list[PageElement | Tag]], None, None]:
    block_tags = []

    for child in list(tag.children):  # Make a copy because .children will change after the yield
        if isinstance(child, Comment) or (isinstance(child, Tag) and child.name in excluded):
            if block_tags:
                yield True, block_tags
            block_tags = []

        elif isinstance(child, NavigableString) or (isinstance(child, Tag) and child.name in inline):
            block_tags.append(child)

        else:
            # Some other kind of tag -> breaks up a block
            if block_tags:
                yield True, block_tags
            yield False, [child]
            block_tags = []

    if block_tags:
        yield True, block_tags


def _process_markdown(parent, excluded: list[str], inline: list[str]):
    for needs_markdown, block in _form_blocks(parent, excluded, inline):
        if needs_markdown:
            result = parse_soup_from_xml(
                process_markdown_text(
                    ''.join((str(b) for b in block))
                )
            )
            for tag in block:
                tag.replace_with(result)
        else:
            for tag in block:
                _process_markdown(tag, excluded, inline)


def process_markdown(text: str, excluded: list[str], inline: list[str]) -> str:
    """
    Process Markdown text and return XML text

    This purpose of this function is only the Markdown to XML step
    Custom XML/HTML tags should be handled by the XML processor
    This function simply converts all Markdown formatting to HTML

    This function processes Markdown in ALL XML/HTML tags
    (including nested tags) except those listed in `excluded`.

    :param text: the Markdown text to process
    :param excluded: a list of tag names to exclude; their contents are left untouched
    :param inline: a list of tag names to treat as inline tags; their contents are processed as Markdown but not wrapped in <p> tags
    :returns: The XML/HTML text
    """
    content = replace_problematic_characters(text, {'<': '&lt;'})
    soup = parse_soup_from_xml(content)
    _process_markdown(soup, excluded, inline)
    return str(soup)
