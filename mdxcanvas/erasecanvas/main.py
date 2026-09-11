import argparse
import os
import threading
from dataclasses import dataclass
from pathlib import Path

from canvasapi import exceptions
from canvasapi.exceptions import ResourceDoesNotExist

from ..main import get_course, load_config
from ..our_logging import get_logger
from ..deploy.executor import execute_dag, retry_rate_limit


@dataclass(frozen=True)
class _Task:
    key: str
    predecessors: frozenset[str]
    plan_order: int
    action: object


def _run_tasks(tasks):
    result = execute_dag(tasks, lambda node: retry_rate_limit(node.action, key=node.key))
    if result.failures:
        raise next(iter(result.failures.values()))
    if result.blocked:
        raise next(iter(result.blocked.values()))
    return result


def get_item_name(item):
    if hasattr(item, 'title'):
        return item.title
    elif hasattr(item, 'name'):
        return item.name
    elif hasattr(item, 'display_name'):
        return item.display_name
    elif hasattr(item, 'filename'):
        return item.filename
    else:
        return str(item)


def get_item_type(item):
    if hasattr(item, 'is_quiz_assignment'):
        if item.is_quiz_assignment:
            return 'Quiz'
        else:
            return 'Assignment'


def delete_item(item, item_type, item_name):
    logger = get_logger()

    try:
        item.delete()
    except ResourceDoesNotExist:
        logger.info(f'{item_type} already deleted: {item_name}')
    except exceptions.BadRequest as e:
        if "Can't delete the root folder" in str(e):
            logger.info(f'Skipping root folder: {item_name}')
        else:
            logger.warning(f'Failed to delete {item_type}: {item_name}')


def parallel_delete(items, item_type=None):
    """Delete a list of Canvas items in parallel."""
    logger = get_logger()
    items = list(items)
    if not items:
        return

    def execute(task):
        item, itype, name = task
        logger.info(f'Deleting {itype}: {name}')
        delete_item(item, itype, name)

    tasks = []
    for i, item in enumerate(items):
        data = (item, item_type or get_item_type(item), get_item_name(item))
        tasks.append(_Task(str(i), frozenset(), i, lambda data=data: execute(data)))
    _run_tasks(tasks)


def delete_all_files(course):
    """
    Delete all files and non-root folders from the course.
    Collects everything first, then deletes files in parallel,
    then folders in parallel (leaf-first by depth).
    """
    logger = get_logger()
    folders = list(course.get_folders())

    # Collect all files across all folders in parallel
    all_files = []
    files_lock = threading.Lock()

    def collect_files(folder):
        files = list(folder.get_files())
        with files_lock:
            all_files.extend(files)

    _run_tasks([_Task(str(i), frozenset(), i, lambda folder=folder: collect_files(folder))
                for i, folder in enumerate(folders)])

    # Delete all files in parallel
    if all_files:
        logger.info(f'Deleting {len(all_files)} files in parallel')
        parallel_delete(all_files, 'File')

    # Retry stragglers - Canvas sometimes doesn't return all files on first query
    remaining_files = []

    def collect_remaining(folder):
        files = list(folder.get_files())
        with files_lock:
            remaining_files.extend(files)

    _run_tasks([_Task(str(i), frozenset(), i, lambda folder=folder: collect_remaining(folder))
                for i, folder in enumerate(folders)])

    if remaining_files:
        logger.info(f'Deleting {len(remaining_files)} remaining files')
        parallel_delete(remaining_files, 'File')

    # Delete non-root folders deepest-first so children are removed before parents
    non_root = [f for f in folders if f.parent_folder_id is not None]
    # Sort by full_name length descending (deeper folders have longer paths)
    non_root.sort(key=lambda f: len(getattr(f, 'full_name', '')), reverse=True)
    parallel_delete(non_root, 'Folder')


def main(
        canvas_api_token: str,
        course_info: dict,
        confirmed_delete: bool
):
    logger = get_logger()
    logger.info('Connecting to Canvas...')

    course = get_course(canvas_api_token,
                        course_info['CANVAS_API_URL'],
                        course_info['CANVAS_COURSE_ID'])
    logger.info(f'Connected to {course.name} ({course.id})')

    if not confirmed_delete:
        print(f'Course: {course.name} ({course.id})')
        confirm = input('Are you sure you want to delete all course content? (y/[n]): ')
        if confirm.lower() != 'y':
            logger.info('Exiting...')
            return

    course.update(course={'syllabus_body': ''})
    logger.info('Deleting Syllabus')

    def delete_quizzes():
        parallel_delete(course.get_quizzes(), 'Quiz')

    def delete_assignments():
        parallel_delete(course.get_assignments())

    def delete_assignment_groups():
        parallel_delete(course.get_assignment_groups(), 'Assignment Group')

    def delete_pages():
        parallel_delete(course.get_pages(), 'Page')

    def delete_modules():
        parallel_delete(course.get_modules(), 'Module')

    def delete_folders():
        delete_all_files(course)

    def delete_announcements():
        parallel_delete(course.get_discussion_topics(course_id=course.id, only_announcements=True), 'Announcement')

    dependencies = {
        'assignments': ['quizzes'],
        'assignment_groups': ['assignments'],
    }

    actions = [
        ('quizzes', delete_quizzes),
        ('assignments', delete_assignments),
        ('assignment_groups', delete_assignment_groups),
        ('pages', delete_pages),
        ('modules', delete_modules),
        ('folders', delete_folders),
        ('announcements', delete_announcements),
    ]
    tasks = [_Task(key, frozenset(dependencies.get(key, [])), index, action)
             for index, (key, action) in enumerate(actions)]
    _run_tasks(tasks)


def entry():
    parser = argparse.ArgumentParser()
    parser.add_argument("--course-info", type=Path)
    parser.add_argument('-y', action='store_true')
    args = parser.parse_args()

    course_settings = load_config(args.course_info)

    api_token = os.environ.get("CANVAS_API_TOKEN")
    if api_token is None:
        raise ValueError("Please set the CANVAS_API_TOKEN environment variable")

    main(
        canvas_api_token=api_token,
        course_info=course_settings,
        confirmed_delete=args.y
    )


if __name__ == '__main__':
    entry()
