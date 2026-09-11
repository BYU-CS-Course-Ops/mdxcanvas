from pathlib import Path

from canvasapi.course import Course

from ..resources import PageInfo


def deploy_page(course: Course, page_info: dict, _: Path) -> tuple[PageInfo, None]:
    if page_id := page_info.get('canvas_id'):
        canvas_page = course.get_page(page_id)
        canvas_page.edit(wiki_page=page_info)
    else:
        canvas_page = course.create_page(wiki_page=page_info)

    page_object_info: PageInfo = {
        'id': canvas_page.page_id,
        'title': canvas_page.title,
        'page_url': canvas_page.url,
        'uri': f'/courses/{course.id}/pages/{canvas_page.url}',

        # Following fields have been observed to be missing in some cases
        'url': getattr(canvas_page, 'html_url', None)
    }

    return page_object_info, None
