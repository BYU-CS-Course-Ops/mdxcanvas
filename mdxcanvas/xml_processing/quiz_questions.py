import re
import string

from bs4.element import Tag

from .attributes import parse_settings, Attribute, parse_bool, parse_int, parse_children_tag_contents
from ..util import retrieve_contents
from ..resources import StrLike


NO_POINTS = 0
FULL_POINTS = 100

question_children_names = [
    'correct', 'incorrect', 'pair', 'distractors', 'correct-comments', 'neutral-comments', 'incorrect-comments'
]

default_fields = [
    Attribute('type', ignore=True),
    Attribute('name', ignore=True),
    Attribute('id', required=True, new_name='question_id')
]

common_fields = [
    Attribute('correct-comments', new_name='correct_comments'),
    Attribute('neutral-comments', new_name='neutral_comments'),
    Attribute('incorrect-comments', new_name='incorrect_comments'),
    Attribute('text-after-answers', new_name='text_after_answers'),
    *default_fields
]

mostly_common_fields = [
    Attribute('points', 1, parse_int, 'points_possible'),
    *common_fields
]


# `answer_comments` is read straight off the answer tag by _add_answer_comments,
# not through parse_settings. Declaring it as an ignored attribute keeps
# parse_settings from reporting it as an unprocessed field, without adding
# anything to the parsed answer.
ANSWER_COMMENTS_ATTRIBUTE = Attribute('answer_comments', ignore=True)


def _add_answer_comments(answer: dict, tag: Tag | None = None, answer_comments: str | None = None):
    if answer_comments is None and tag is not None:
        answer_comments = tag.get('answer_comments')

    if answer_comments:
        answer['comments_html'] = f"<p>{answer_comments}</p>"

    return answer


def parse_text_question(tag: Tag):
    question_text = retrieve_contents(tag)
    question = {
        "question_text": question_text,
        "question_type": 'text_only_question',
    }
    question.update(parse_settings(tag, default_fields))

    return [question]


def parse_true_false_question(tag: Tag):
    """
    <question id="q1" type='true-false' answer='true' points_possible='2'>
    The earth orbits the sun
    </question>

    <question id="q2" type='true-false' answer='false'>
    The earth is **flat**

    <correct-comments>
    Regular folks who like math and stars rely on the curvature on the earth to track the motion
    of heavenly bodies.
    </correct-comments>

    <incorrect-comments>
    A nationwide survey in 2022 by researchers at the University of New Hampshire found that
    10% of U.S. adults believed the earth was flat.
    </incorrect-comments>
    </question>
    """
    fields = [
        Attribute('answer', required=True, parser=parse_bool, default=False),
    ]
    question = parse_settings(tag, mostly_common_fields + fields)

    question.update({
        "question_text": retrieve_contents(tag, question_children_names),
        "question_type": 'true_false_question',
        "answers": [
            {
                "answer_text": "True",
                "answer_weight": FULL_POINTS if question["answer"] is True else NO_POINTS
            },
            {
                "answer_text": "False",
                "answer_weight": FULL_POINTS if question["answer"] is False else NO_POINTS
            }
        ]
    })

    return [question]


def parse_multiple_choice_question(tag: Tag):
    """
    <question id="q1" type='multiple-choice'>
    5 + 5 =
    <correct> 10 </correct>
    <incorrect> 11 </incorrect>
    <incorrect> 9 </incorrect>
    <incorrect> 8 </incorrect>
    </question>
    """
    return _parse_multiple_option_question('multiple_choice_question', tag)


def parse_multiple_answers_question(tag: Tag):
    """
    <question id="q1" type='multiple-answers'>
    Which of the following are prime numbers?
    <correct> 2 </correct>
    <correct> 3 </correct>
    <incorrect> 4 </incorrect>
    <correct> 5 </correct>
    <incorrect> 6 </incorrect>
    </question>
    """
    return _parse_multiple_option_question('multiple_answers_question', tag)


def _parse_multiple_option_question(question_type, tag):
    answers = tag.find_all(['correct', 'incorrect'], recursive=False)
    question = {
        "question_text": retrieve_contents(tag, question_children_names),
        "question_type": question_type,
        "answers": [
            _add_answer_comments({
                "answer_html": retrieve_contents(answer),
                "answer_weight": FULL_POINTS if answer.name == 'correct' else NO_POINTS
            }, answer) for answer in answers
        ]
    }
    question.update(parse_settings(tag, mostly_common_fields))
    return [question]


def parse_matching_question(tag: Tag):
    """
    <question id="q1" type='matching'>
    Match the following:
    <pair left='1' right='A' />
    <pair left='2' right='B' />
    <pair left='3' right='C' /
    <distractors>
    D
    E
    </distractors>
    <correct-comments>Good job!</correct-comments>
    </question>
    """
    left_field = Attribute('left', required=True)
    right_field = Attribute('right', required=True)
    pairs = tag.find_all('pair')
    distractors = '\n'.join(parse_children_tag_contents(tag, 'distractors'))
    distractors = '\n'.join(line for line in distractors.splitlines() if line.split())
    parsed_pairs = []
    for pair_tag in pairs:
        pair = parse_settings(pair_tag, [left_field, right_field])
        parsed_pairs.append(_add_answer_comments({
            "answer_match_left": pair['left'],
            "answer_match_right": pair['right'],
            "answer_weight": FULL_POINTS
        }, pair_tag))

    question = parse_settings(tag, mostly_common_fields)

    question.update({
        "question_text": retrieve_contents(tag, question_children_names + ['pair', 'distractors']),
        "question_type": 'matching_question',
        "points_possible": parse_int(tag.get('points') or len(pairs)),
        "answers": parsed_pairs,
        "matching_answer_incorrect_matches": distractors
    })

    return [question]


def parse_multiple_true_false_question(tag: Tag):
    """
    <question id="q1" type='multiple-tf'>
    Which of the following matrices are invertible?

    A: [[1, 0], [0, 1]]
    B: [[1, 0], [1, 0]]
    C: [[1, 1], [1, 1]]
    D: [[0, 0], [0, 0]]

    <correct> A </correct>
    <incorrect> B </incorrect>
    <incorrect> C </incorrect>
    <incorrect> D </incorrect>
    """
    resulting_questions = []

    header = {
        "question_text": retrieve_contents(tag, question_children_names),
        "question_type": 'text_only_question',
    }
    header.update(parse_settings(tag, default_fields))
    resulting_questions.append(header)

    answers = tag.find_all(re.compile(r'correct|incorrect'))

    question_attributes = [
        Attribute('points', default=len(answers), parser=parse_int, new_name='points_possible'),
    ]
    settings = parse_settings(tag, question_attributes + common_fields)
    total_points = settings['points_possible']

    # Distribute points evenly among the questions
    points_per_question = round(total_points // len(answers), 2)
    error = total_points - points_per_question * len(answers)
    num_to_change = round(error * 100)
    amount = 0.01 if error > 0 else -0.01

    qid = settings['question_id']
    for index, child in enumerate(answers):
        question = {
            "question_text": retrieve_contents(child),
            "question_type": 'true_false_question',
            "question_id": f'{qid}_{index}',
            "points_possible": points_per_question + amount if index < num_to_change else points_per_question,
            "answers": [
                {
                    "answer_text": "True",
                    "answer_weight": FULL_POINTS if child.name == 'correct' else NO_POINTS
                },
                {
                    "answer_text": "False",
                    "answer_weight": FULL_POINTS if child.name == 'incorrect' else NO_POINTS
                }
            ]
        }

        if answer_comments := child.get('answer_comments'):
            question['correct_comments'] = answer_comments

        resulting_questions.append(question)

    return resulting_questions


def _add_answers_to_multiple_blanks_question(text):
    def letter_generator():
        for repeat in range(1, 10):
            for letter in string.ascii_uppercase:
                yield letter * repeat

    letter_gen = letter_generator()
    answers = []

    def get_next_letter(match):
        answer = match.group()[2:-2]
        associated_id = next(letter_gen)
        answers.append({'answer_text': answer, 'blank_id': associated_id, 'answer_weight': FULL_POINTS})
        return f'[{associated_id}]'

    updated_text = re.sub(r"\[\[(.*?)\]\]", get_next_letter, text)

    return updated_text, answers


def parse_fill_in_multiple_blanks_filled_answers(tag: Tag):
    """
    Anything within a set of brackets will be turned into a fill in the blank question.
    Whatever is in the brackets will be the correct answer

    The default number of points is the number of fill in the blank questions, but can be overwritten using "points".

    <question id="q1" type='fill-in-multiple-blanks-filled-answers' points="5">
            The U.S. flag has [[13]] stripes and [[50]] stars.
    </question>

    This is also useful for tables
    <question id="q2" type="fill-in-multiple-blanks-filled-answers">
        Fill in the table using the algorithm discussed in class.

    | Node | 0        | 1        | 2         |
    |------|----------|----------|-----------|
    | A    | 0        | [[0]]    | [[0]]     |
    | B    | [[inf]]  | [[1]]    | [[1]]     |
    | C    | [[inf]]  | [[inf]]  | [[3]]     |
    | D    | [[inf]]  | inf      | [[inf]]   |
    | E    | [[inf]]  | [[4]]    | 4         |
    | F    | [[inf]]  | 8        | [[7]]     |
    | G    | inf      | [[inf]]  | [[7]]     |
    | H    | [[inf]]  | [[inf]]  | [[inf]]   |

    </question>
    """
    question_text = retrieve_contents(tag, question_children_names)
    blanks = re.findall(r'\[\[([^\]]+)\]\]', question_text)
    if not blanks:
        raise ValueError("Fill in multiple blanks questions with filled answers must contain at least one filled blank!")

    question_text, answers = _add_answers_to_multiple_blanks_question(question_text)

    question = {
        "question_text": question_text,
        "question_type": 'fill_in_multiple_blanks_question',
        "answers": answers,
    }

    question_attributes = [
        Attribute('points', default=len(answers), parser=parse_int, new_name='points_possible'),
    ]
    settings = parse_settings(tag, question_attributes + common_fields)
    question.update(settings)
    return [question]


def parse_fill_in_the_blank_question(tag: Tag):
    """
    <question id="q1" type='fill-in-the-blank'>
    The capital of France is [blank].
    <correct text='Paris' />
    </question>
    """
    question_text = retrieve_contents(tag, question_children_names)
    blanks = re.findall(r'\[([^]]+)]', question_text)
    if not blanks:
        raise ValueError("Fill in the blank questions must contain at least one blank!")

    answer_attributes = [
        Attribute('text', required=True, new_name='answer_text'),
        Attribute('blank_id', blanks[0]),
        Attribute('answer_weight', FULL_POINTS),
    ]

    question = {
        "question_text": retrieve_contents(tag, question_children_names),
        "question_type": 'fill_in_multiple_blanks_question',
        "answers": [
            _add_answer_comments(parse_settings(answer, [*answer_attributes, ANSWER_COMMENTS_ATTRIBUTE]), answer)
            for answer in tag.find_all('correct')
        ]
    }

    question.update(parse_settings(tag, mostly_common_fields))
    return [question]


def parse_fill_in_multiple_blanks_question(tag: Tag):
    """
    <question id="q1" type='fill-in-multiple-blanks'>
    The U.S. flag has [stripes] stripes and [stars] stars.
    <correct text='13' blank='stripes' />
    <correct text='50' blank='stars' />
    </question>

    The default number of points is the number of fill in the blank questions (ie the example above would be worth 2 points)
    """
    answer_attributes = [
        Attribute('text', required=True, new_name='answer_text'),
        Attribute('blank', required=True, new_name='blank_id'),
        Attribute('answer_weight', FULL_POINTS)
    ]

    answers = tag.find_all('correct')
    question = {
        "question_text": retrieve_contents(tag, question_children_names),
        "question_type": 'fill_in_multiple_blanks_question',
        "answers": [
            _add_answer_comments(parse_settings(answer, [*answer_attributes, ANSWER_COMMENTS_ATTRIBUTE]), answer)
            for answer in answers
        ]
    }

    question_attributes = [
        Attribute('points', default=len(answers), parser=parse_int, new_name='points_possible'),
    ]
    question.update(parse_settings(tag, question_attributes + common_fields))
    return [question]


def parse_essay_question(tag: Tag):
    question_text = retrieve_contents(tag)
    question = {
        "question_text": question_text,
        "question_type": 'essay_question',
    }
    question.update(parse_settings(tag, mostly_common_fields))
    return [question]


def parse_file_upload_question(tag: Tag):
    question_text = retrieve_contents(tag)
    question = {
        "question_text": question_text,
        "question_type": 'file_upload_question',
    }
    question.update(parse_settings(tag, mostly_common_fields))
    return [question]


def _parse_exact_answer_question(tag: Tag):
    """
    <question id="q1" type='numerical' numerical_answer_type="exact">
    Give one possible value for x. The margin of error is +- 0.0001.

    (x - pi)^2 = (x - pi)

    <correct answer_exact='3.14159' answer_error_margin='0.0001' />

    <correct answer_exact='4.14159' answer_error_margin='0.0001' />
    </question>
    """

    question_text = retrieve_contents(tag, ['answer_exact', 'answer_error_margin'])
    answer_attributes = [
        Attribute('answer_exact', required=True),
        Attribute('answer_error_margin', required=True)
    ]

    return question_text, answer_attributes


def _parse_range_answer_question(tag: Tag):
    """
    <question id="q1" type='numerical' numerical_answer_type="range">
    Give one possible value for x.

    1 <= x^2 <= 100

    <correct answer_range_start='1' answer_range_end='10' />

    <correct answer_range_start='-10' answer_range_end='-1' />
    </question>
    """
    question_text = retrieve_contents(tag, ['answer_range_start', 'answer_range_end'])

    answer_attributes = [
        Attribute('answer_range_start', required=True),
        Attribute('answer_range_end', required=True)
    ]

    return question_text, answer_attributes


def _parse_precision_answer_question(tag: Tag):
    """
    The precision number is how many digits are expected in the answer.
    Precision answers can be negative numbers and may include trailing zeroes.
    However, student responses will be marked as correct if they omit the trailing zeroes, as long as all preceding digits are correct.

    <question type='numerical' numerical_answer_type="precision">
    What is the value of pi?

    Ensure your answer gives at least 5 digits.

    <correct answer_approximate='3.14159' answer_precision='5' />
    </question>
    """

    question_text = retrieve_contents(tag, ['answer_approximate', 'answer_precision'])
    answer_attributes = [
        Attribute('answer_approximate', required=True),
        Attribute('answer_precision', required=True)
    ]

    return question_text, answer_attributes


def parse_numerical_question(tag: Tag):
    numerical_answer_types: dict[StrLike, tuple] = {
        'exact': (_parse_exact_answer_question, 'exact_answer'),
        'range': (_parse_range_answer_question, 'range_answer'),
        'precision': (_parse_precision_answer_question, 'precision_answer')
    }

    numerical_answer_type = tag['numerical_answer_type']
    if numerical_answer_type not in numerical_answer_types:
        raise ValueError(f"Invalid numerical answer type: {numerical_answer_type}")

    parse_function, answer_type = numerical_answer_types[numerical_answer_type]
    question_text, answer_attributes = parse_function(tag)

    question = {
        "question_text": question_text,
        "question_type": 'numerical_question',
        "answers": [
            _add_answer_comments(parse_settings(answer, [*answer_attributes, ANSWER_COMMENTS_ATTRIBUTE]), answer)
            for answer in tag.find_all('correct')
        ]
    }

    fields = [
        Attribute('numerical_answer_type', required=True, ignore=True)
    ]
    question.update(parse_settings(tag, fields + mostly_common_fields))

    for answer in question["answers"]:
        answer["numerical_answer_type"] = answer_type

    return [question]
