from typing import Callable

from bs4.element import Tag

from .attributes import (
    Attribute,
    parse_float,
    parse_int,
    parse_bool,
    parse_date,
    parse_settings,
    make_id_parser,
)
from ..util import retrieve_contents
from .quiz_questions import parse_text_question, parse_true_false_question, parse_multiple_choice_question, \
    parse_multiple_answers_question, parse_matching_question, parse_multiple_true_false_question, \
    parse_fill_in_the_blank_question, parse_essay_question, parse_file_upload_question, parse_numerical_question, \
    parse_fill_in_multiple_blanks_question, parse_fill_in_multiple_blanks_filled_answers
from ..resources import ResourceManager, CanvasResource, StrLike, get_key
from .override_parsing import parse_overrides_container
from ..error_helpers import format_tag, get_file_path, validate_required_attribute
from ..processing_context import get_current_file_str
from ..our_logging import get_logger

logger = get_logger()


class QuizTagProcessor:
    def __init__(self, resources: ResourceManager):
        self._resources = resources
        self.question_types: dict[StrLike, Callable[[Tag], list[dict]]] = {
            'text': parse_text_question,
            'true-false': parse_true_false_question,
            'multiple-choice': parse_multiple_choice_question,
            'multiple-answers': parse_multiple_answers_question,
            'matching': parse_matching_question,
            'multiple-tf': parse_multiple_true_false_question,
            'fill-in-the-blank': parse_fill_in_the_blank_question,
            'fill-in-multiple-blanks': parse_fill_in_multiple_blanks_question,
            'fill-in-multiple-blanks-filled-answers': parse_fill_in_multiple_blanks_filled_answers,
            'essay': parse_essay_question,
            'file-upload': parse_file_upload_question,
            'numerical': parse_numerical_question
        }

    def __call__(self, quiz_tag: Tag):
        quiz = {
            "type": "quiz",
        }
        quiz.update(self._parse_quiz_settings(quiz_tag))

        rid = quiz.pop('id')

        for tag in quiz_tag.children:
            if not isinstance(tag, Tag):
                continue  # Top-level content is not supported in a quiz tag

            if tag.name == "questions":
                self._parse_questions(rid, tag)

            elif tag.name == "description":
                quiz["description"] = retrieve_contents(tag)

        info = CanvasResource(
            type='quiz',
            id=rid,
            data=quiz,
            content_path=get_current_file_str()
        )
        self._resources.add_resource(info)

        # Process <overrides> child tag if present
        for tag in quiz_tag.children:
            if isinstance(tag, Tag) and tag.name == "overrides":
                parse_overrides_container(tag, 'quiz', rid, self._resources)

    def _parse_quiz_settings(self, settings_tag):
        fields = [
            Attribute('id', required=True),
            Attribute('title', required=True),
            Attribute('quiz_type', 'assignment'),
            Attribute('assignment_group', parser=make_id_parser('assignment_group'), new_name='assignment_group_id'),
            Attribute('time_limit', parser=parse_int),
            Attribute('shuffle_answers', False, parse_bool),
            Attribute('hide_results'),  # TODO - should be boolean?
            Attribute('show_correct_answers', True, parse_bool),
            Attribute('show_correct_answers_last_attempt', False, parse_bool),
            Attribute('show_correct_answers_at', parser=parse_date),
            Attribute('hide_correct_answers_at', parser=parse_date),
            Attribute('allowed_attempts', -1, parse_int),
            Attribute('scoring_policy', 'keep_highest'),
            Attribute('one_question_at_a_time', False, parse_bool),
            Attribute('cant_go_back', False, parse_bool),
            Attribute('available_from', parser=parse_date, new_name='unlock_at'),
            Attribute('available_to', parser=parse_date, new_name='lock_at'),
            Attribute('due_at', parser=parse_date),
            Attribute('access_code'),
            Attribute('position', parser=parse_int),
            Attribute('published', parser=parse_bool),
            Attribute('one_time_results', False, parse_bool),
            Attribute('only_visible_to_overrides', parser=parse_bool),
            Attribute('points_possible', parser=parse_float)
        ]

        return parse_settings(settings_tag, fields)

    def _parse_questions(self, quiz_rid: StrLike, questions_tag: Tag):
        order_items = []

        for tag in questions_tag.find_all('question', recursive=False):
            q_type = validate_required_attribute(tag, 'type', 'question')

            if not (parse_question := self.question_types.get(q_type)):  # pyright: ignore[reportArgumentType]
                raise ValueError(
                    f"Question type '{q_type}' not supported @ {format_tag(tag)}\n  "
                    f"Supported types: {', '.join(self.question_types.keys())}\n  "  # type: ignore
                    f"in {get_file_path(tag)}")

            for question in parse_question(tag):
                question_id = question.pop('question_id')
                question_rid = f"{quiz_rid}|{question_id}"
                question['quiz_id'] = get_key('quiz', quiz_rid, 'id')

                self._resources.add_resource(CanvasResource(
                    type='quiz_question',
                    id=question_rid,
                    data=question,
                    content_path=get_current_file_str()
                ))

                order_items.append({
                    'id': get_key('quiz_question', question_rid, 'id'),
                    'type': 'question'
                })

        if not order_items:
            logger.warning(f"No questions found for quiz {quiz_rid} @ {get_file_path(questions_tag)}")
        else:
            self._resources.add_resource(CanvasResource(
                type='quiz_question_order',
                id=f'{quiz_rid}|order',
                data={
                    'quiz_id': get_key('quiz', quiz_rid, 'id'),
                    'order': order_items
                },
                content_path=get_current_file_str()
            ))
