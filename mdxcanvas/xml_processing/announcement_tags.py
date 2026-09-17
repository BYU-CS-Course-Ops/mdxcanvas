from datetime import datetime

from bs4.element import Tag

from .attributes import parse_settings, Attribute, parse_date, parse_bool
from ..resources import ResourceManager, CanvasResource
from ..util import retrieve_contents
from ..processing_context import get_current_file_str


class AnnouncementTagProcessor:
    def __init__(self, resources: ResourceManager):
        self._resources = resources

    def __call__(self, announcement_tag: Tag):
        fields = [
            Attribute('id', required=True),
            Attribute('title', required=True),
            Attribute('is_announcement', True, parser=parse_bool),
            Attribute('publish_date', required=True, new_name='delayed_post_at', parser=parse_date,
                      default=datetime.now().isoformat()),
            Attribute('is_section_specific', parser=parse_bool),
            # Canvas takes specific_sections as a
            # comma-separated list of section ids.
            Attribute('specific_sections'),
        ]

        # https://canvas.instructure.com/doc/api/discussion_topics.html#method.discussion_topics.create
        # permissions.reply
        # published

        settings = {
            "type": "discussion_topics",
            "message": retrieve_contents(announcement_tag)
        }

        settings.update(parse_settings(announcement_tag, fields))

        announcement = CanvasResource(
            type='announcement',
            id=settings.pop('id'),
            data=settings,
            content_path=get_current_file_str()
        )
        self._resources.add_resource(announcement)
