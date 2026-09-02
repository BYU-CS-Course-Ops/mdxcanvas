import os

from pathlib import Path

import pytest

from mdxcanvas.main import get_course, load_config, main as deploy
from mdxcanvas.erasecanvas.main import main as erasecanvas


CANVAS_API_TOKEN = os.environ.get("CANVAS_API_TOKEN", "")

pytestmark = pytest.mark.skipif(
    not CANVAS_API_TOKEN,
    reason="CANVAS_API_TOKEN is required for Canvas integration tests",
)


def _test_canvas_object_update_name(
    course_info_file: Path,
    main_input_file: Path,
    updated_input_file: Path,
    get_objects_method: str,
    get_objects_kwargs: dict,
    name_attribute: str,
    object_type_name: str
):
    """
    Generic test helper for testing canvas object name/title updates.

    Args:
        course_info_file: Path to the course info JSON file
        main_input_file: Path to the main XML file to deploy
        updated_input_file: Path to the updated XML file to deploy
        get_objects_method: Name of the method to call on course object (e.g., 'get_assignments')
        get_objects_kwargs: Kwargs to pass to the get objects method (e.g., {'only_announcements': True})
        name_attribute: Name of the attribute to check (e.g., 'name' or 'title')
        object_type_name: Human-readable name for the object type (e.g., 'Assignment', 'Page')
    """
    course_info = load_config(course_info_file)
    course = get_course(CANVAS_API_TOKEN, course_info['CANVAS_API_URL'], course_info['CANVAS_COURSE_ID'])

    # Erase canvas to start fresh
    erasecanvas(
        canvas_api_token=CANVAS_API_TOKEN,
        course_info=course_info,
        confirmed_delete=True,
    )

    # Deploy the main file
    deploy(
        canvas_api_token=CANVAS_API_TOKEN,
        course_info_file=course_info_file,
        input_file=main_input_file
    )

    # Get the objects from Canvas
    get_method = getattr(course, get_objects_method)
    objects = list(get_method(**get_objects_kwargs))

    assert len(objects) == 1, f"Expected 1 {object_type_name}, got {len(objects)}"

    # Get the initial name/title
    initial_name = getattr(objects[0], name_attribute)
    print(f"\n{object_type_name} {name_attribute}: {initial_name}")

    # Deploy the updated file
    deploy(
        canvas_api_token=CANVAS_API_TOKEN,
        course_info_file=course_info_file,
        input_file=updated_input_file
    )

    # Get the updated objects
    updated_objects = list(get_method(**get_objects_kwargs))

    assert len(updated_objects) == 1, f"Expected 1 {object_type_name}, got {len(updated_objects)}"

    # Get the updated name/title
    updated_name = getattr(updated_objects[0], name_attribute)
    print(f"Updated {object_type_name} {name_attribute}: {updated_name}")

    # Verify the name changed
    assert initial_name != updated_name, f"{object_type_name} {name_attribute} did not change"
    print(f"{object_type_name} {name_attribute} updated successfully from '{initial_name}' to '{updated_name}'")


def test_assignment_update_names(
    course_info_file: Path,
    main_input_file: Path,
    updated_input_file: Path
):
    _test_canvas_object_update_name(
        course_info_file=course_info_file,
        main_input_file=main_input_file,
        updated_input_file=updated_input_file,
        get_objects_method='get_assignments',
        get_objects_kwargs={},
        name_attribute='name',
        object_type_name='Assignment'
    )


def test_page_update_names(
    course_info_file: Path,
    page_main_input_file: Path,
    page_updated_input_file: Path
):
    _test_canvas_object_update_name(
        course_info_file=course_info_file,
        main_input_file=page_main_input_file,
        updated_input_file=page_updated_input_file,
        get_objects_method='get_pages',
        get_objects_kwargs={},
        name_attribute='title',
        object_type_name='Page'
    )


def test_quiz_update_names(
    course_info_file: Path,
    quiz_main_input_file: Path,
    quiz_updated_input_file: Path
):
    _test_canvas_object_update_name(
        course_info_file=course_info_file,
        main_input_file=quiz_main_input_file,
        updated_input_file=quiz_updated_input_file,
        get_objects_method='get_quizzes',
        get_objects_kwargs={},
        name_attribute='title',
        object_type_name='Quiz'
    )


def test_module_update_names(
    course_info_file: Path,
    module_main_input_file: Path,
    module_updated_input_file: Path
):
    _test_canvas_object_update_name(
        course_info_file=course_info_file,
        main_input_file=module_main_input_file,
        updated_input_file=module_updated_input_file,
        get_objects_method='get_modules',
        get_objects_kwargs={},
        name_attribute='name',
        object_type_name='Module'
    )


def test_announcement_update_names(
    course_info_file: Path,
    announcement_main_input_file: Path,
    announcement_updated_input_file: Path
):
    _test_canvas_object_update_name(
        course_info_file=course_info_file,
        main_input_file=announcement_main_input_file,
        updated_input_file=announcement_updated_input_file,
        get_objects_method='get_discussion_topics',
        get_objects_kwargs={'only_announcements': True},
        name_attribute='title',
        object_type_name='Announcement'
    )


def test_group_update_names(
    course_info_file: Path,
    group_main_input_file: Path,
    group_updated_input_file: Path
):
    _test_canvas_object_update_name(
        course_info_file=course_info_file,
        main_input_file=group_main_input_file,
        updated_input_file=group_updated_input_file,
        get_objects_method='get_assignment_groups',
        get_objects_kwargs={},
        name_attribute='name',
        object_type_name='Assignment Group'
    )
