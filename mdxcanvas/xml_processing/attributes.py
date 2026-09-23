import dataclasses
from datetime import datetime
from typing import Callable, Any

from bs4.element import Tag

from ..error_helpers import format_tag, get_file_path
from ..our_logging import get_logger
from ..resources import get_key
from ..util import retrieve_contents

logger = get_logger()


def parse_date(date: datetime | str | None) -> str:
    if isinstance(date, datetime):
        return datetime.isoformat(date)

    elif isinstance(date, str):
        # Check if the string is already in ISO format
        try:
            return datetime.isoformat(datetime.fromisoformat(date))
        except ValueError:
            pass

        try_formats = [
            "%b %d, %Y, %I:%M %p",
            "%b %d %Y %I:%M %p",
            "%Y-%m-%dT%H:%M:%S%z"
        ]
        for format_str in try_formats:
            try:
                parsed_date = datetime.strptime(date, format_str)
                break
            except ValueError:
                pass
        else:
            raise ValueError(f"Invalid date format: {date}")

        # Convert the parsed datetime object to the desired timezone
        # to_zone = pytz.timezone(time_zone)
        # parsed_date = parsed_date.replace(tzinfo=None)  # Remove existing timezone info
        # parsed_date = parsed_date.astimezone(to_zone)
        # TODO - Move this timezone block to deployment
        return datetime.isoformat(parsed_date)
    else:
        raise TypeError("Date must be a datetime object or a string")


def make_id_parser(resource_type: str):
    """Create a parser function for resource ID references."""
    return lambda text: get_key(resource_type, text, 'id')


def make_id_list_parser(resource_type: str):
    """Create a parser function for a list of resource ID references."""
    return lambda text: [get_key(resource_type, item.strip(), 'id') for item in parse_list(text)]


def parse_int(text):
    return int(text)


def parse_bool(text):
    # Forgiving boolean parser
    if isinstance(text, bool):
        return text

    if text.lower() == "true":
        return True
    elif text.lower() == "false":
        return False
    else:
        raise ValueError(f"Invalid boolean value: {text}")


def parse_list(text):
    items = text.strip().split(',')
    # Backward compatibility: if the list has only one item and it contains a '|', split on that instead
    if len(items) == 1 and '|' in items[0]:
        items = items[0].split('|')
    return [cell.strip() for cell in items if cell.strip()]


def parse_dict(text):
    # Assumes the string is a comma-separated list of key-value pairs
    # Example: "key1=value1, key2=value2 "
    return dict(cell.strip().split('=') for cell in text.split(',') if cell.strip())


@dataclasses.dataclass
class Attribute:
    name: str
    default: Any = None
    parser: Callable[[str | Any], Any] = lambda x: x
    new_name: str | None = None
    required: bool = False
    ignore: bool = False
    is_tag: bool = False


def get_tag_info(tag: Tag):
    name = tag.name
    hint = tag.get('title')
    if hint is None:
        hint = tag.get('name')
    display = name
    if hint:
        display += f'({hint})'
    return display


def get_tag_path(tag: Tag):
    tokens = [get_tag_info(tag)] + [get_tag_info(p) for p in tag.parents]
    return '.'.join(tokens[::-1])


def parse_settings(tag: Tag, attributes: list[Attribute]):
    settings = {}
    processed_fields = set()

    for attribute in attributes:
        processed_fields.add(attribute.name)
        if attribute.new_name:
            processed_fields.add(attribute.new_name)
        name = attribute.new_name or attribute.name

        if attribute.ignore:
            continue

        if (field := (
                tag.get(attribute.name)
                or (tag.get(attribute.new_name) if attribute.new_name else None)
        )):
            try:
                value = attribute.parser(field)
            except (ValueError, TypeError) as e:
                raise ValueError(
                    f"Invalid '{attribute.name}' value '{field}' for {tag.name} tag {format_tag(tag)}\n"
                    f" in {get_file_path(tag)}"
                ) from e
            settings[name] = value

        elif attribute.is_tag:
            if child := tag.find(attribute.name, recursive=False):
                value = retrieve_contents(child)
                try:
                    settings[name] = attribute.parser(value)
                except (ValueError, TypeError) as e:
                    raise ValueError(
                        f"Invalid '{attribute.name}' value for {tag.name} tag {format_tag(tag)}\n"
                        f" in {get_file_path(tag)}"
                    ) from e

        elif attribute.default:
            settings[name] = attribute.default

        elif attribute.required:
            raise Exception(
                f'Required field "{attribute.name}" missing from {tag.name} tag {format_tag(tag)}\n @ {get_tag_path(tag)} in {get_file_path(tag)}')

    if unknown := sorted(k for k in tag.attrs if k not in processed_fields):
        # A warning reached the deploy log and nowhere else, so a course could
        # set an attribute, watch the deploy go green, and never learn the value
        # was discarded before it left the machine.
        raise ValueError(
            f'Unknown attribute{"s" if len(unknown) > 1 else ""} '
            f'{", ".join(repr(k) for k in unknown)} on {tag.name} tag '
            f'{format_tag(tag)}\n'
            f' @ {get_tag_path(tag)} in {get_file_path(tag)}\n'
            f' accepted here: {", ".join(sorted(processed_fields))}'
        )

    return settings


def parse_children_tag_contents(tag: Tag, child_name):
    children = tag.find_all(child_name, recursive=False)
    return [retrieve_contents(child) for child in children]
