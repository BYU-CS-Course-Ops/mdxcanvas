import logging

import pytest
from bs4 import BeautifulSoup

from mdxcanvas.xml_processing.quiz_questions import (
    parse_fill_in_multiple_blanks_question,
    parse_fill_in_the_blank_question,
    parse_matching_question,
    parse_multiple_answers_question,
    parse_multiple_choice_question,
    parse_multiple_true_false_question,
    parse_numerical_question,
    parse_true_false_question,
)


def _parse_question(xml: str):
    return BeautifulSoup(xml, 'html.parser').find('question')


def test_multiple_choice_answer_comments_are_included():
    question = _parse_question("""
    <question id="q1" type="multiple-choice">
        What is the capital of France?
        <correct answer_comments="Exactly right">Paris</correct>
        <incorrect answer_comments="This is the UK capital">London</incorrect>
        <incorrect>Berlin</incorrect>
    </question>
    """)

    parsed = parse_multiple_choice_question(question)[0]

    assert parsed['answers'] == [
        {
            'answer_html': 'Paris',
            'answer_weight': 100,
            'comments_html': '<p>Exactly right</p>',
        },
        {
            'answer_html': 'London',
            'answer_weight': 0,
            'comments_html': '<p>This is the UK capital</p>',
        },
        {
            'answer_html': 'Berlin',
            'answer_weight': 0,
        },
    ]


def test_multiple_answers_answer_comments_are_included():
    question = _parse_question("""
    <question id="q1" type="multiple-answers">
        Which are programming languages?
        <correct answer_comments="Yes">Python</correct>
        <correct>JavaScript</correct>
        <incorrect answer_comments="Markup language">HTML</incorrect>
    </question>
    """)

    parsed = parse_multiple_answers_question(question)[0]

    assert parsed['answers'] == [
        {
            'answer_html': 'Python',
            'answer_weight': 100,
            'comments_html': '<p>Yes</p>',
        },
        {
            'answer_html': 'JavaScript',
            'answer_weight': 100,
        },
        {
            'answer_html': 'HTML',
            'answer_weight': 0,
            'comments_html': '<p>Markup language</p>',
        },
    ]


def test_true_false_uses_question_level_feedback_fields():
    question = _parse_question("""
    <question id="q1"
              type="true-false"
              answer="true"
              correct-comments="Correct"
              incorrect-comments="False is not correct here">
        The earth orbits the sun.
    </question>
    """)

    parsed = parse_true_false_question(question)[0]

    assert parsed['answers'] == [
        {
            'answer_text': 'True',
            'answer_weight': 100,
        },
        {
            'answer_text': 'False',
            'answer_weight': 0,
        },
    ]
    assert parsed['correct_comments'] == 'Correct'
    assert parsed['incorrect_comments'] == 'False is not correct here'


def test_existing_multiple_choice_without_answer_comments_still_parses():
    question = _parse_question("""
    <question id="q1" type="multiple-choice">
        2 + 2 =
        <correct>4</correct>
        <incorrect>3</incorrect>
    </question>
    """)

    parsed = parse_multiple_choice_question(question)[0]

    assert parsed['answers'] == [
        {
            'answer_html': '4',
            'answer_weight': 100,
        },
        {
            'answer_html': '3',
            'answer_weight': 0,
        },
    ]


def test_matching_pair_answer_comments_are_included():
    question = _parse_question("""
    <question id="q1" type="matching">
        Match the following:
        <pair left="France" right="Paris" answer_comments="Paris is the capital of France." />
        <pair left="Germany" right="Berlin" />
    </question>
    """)

    parsed = parse_matching_question(question)[0]

    assert parsed['answers'] == [
        {
            'answer_match_left': 'France',
            'answer_match_right': 'Paris',
            'answer_weight': 100,
            'comments_html': '<p>Paris is the capital of France.</p>',
        },
        {
            'answer_match_left': 'Germany',
            'answer_match_right': 'Berlin',
            'answer_weight': 100,
        },
    ]


def test_multiple_true_false_answer_comments_become_correct_feedback():
    question = _parse_question("""
    <question id="q1" type="multiple-tf">
        Which statements are true?
        <correct answer_comments="Yes, Python is a programming language.">Python is a programming language.</correct>
        <incorrect answer_comments="No, HTML is markup.">HTML is a programming language.</incorrect>
    </question>
    """)

    parsed = parse_multiple_true_false_question(question)

    assert parsed[1]['correct_comments'] == 'Yes, Python is a programming language.'
    assert parsed[1]['answers'] == [
        {
            'answer_text': 'True',
            'answer_weight': 100,
        },
        {
            'answer_text': 'False',
            'answer_weight': 0,
        },
    ]
    assert parsed[2]['correct_comments'] == 'No, HTML is markup.'
    assert parsed[2]['answers'] == [
        {
            'answer_text': 'True',
            'answer_weight': 0,
        },
        {
            'answer_text': 'False',
            'answer_weight': 100,
        },
    ]


def test_fill_in_the_blank_answer_comments_are_included():
    question = _parse_question("""
    <question id="q1" type="fill-in-the-blank">
        The capital of France is [blank].
        <correct text="Paris" answer_comments="Exactly right" />
    </question>
    """)

    parsed = parse_fill_in_the_blank_question(question)[0]

    assert parsed['answers'] == [
        {
            'answer_text': 'Paris',
            'blank_id': 'blank',
            'answer_weight': 100,
            'comments_html': '<p>Exactly right</p>',
        },
    ]


def test_fill_in_multiple_blanks_answer_comments_are_included():
    question = _parse_question("""
    <question id="q1" type="fill-in-multiple-blanks">
        The U.S. flag has [stripes] stripes and [stars] stars.
        <correct text="13" blank="stripes" answer_comments="There are 13 original colonies." />
        <correct text="50" blank="stars" />
    </question>
    """)

    parsed = parse_fill_in_multiple_blanks_question(question)[0]

    assert parsed['answers'] == [
        {
            'answer_text': '13',
            'blank_id': 'stripes',
            'answer_weight': 100,
            'comments_html': '<p>There are 13 original colonies.</p>',
        },
        {
            'answer_text': '50',
            'blank_id': 'stars',
            'answer_weight': 100,
        },
    ]


def test_numerical_answer_comments_are_included():
    question = _parse_question("""
    <question id="q1" type="numerical" numerical_answer_type="exact">
        What is pi to 5 decimal places?
        <correct answer_exact="3.14159" answer_error_margin="0.00001" answer_comments="Rounded correctly." />
    </question>
    """)

    parsed = parse_numerical_question(question)[0]

    assert parsed['answers'] == [
        {
            'answer_exact': '3.14159',
            'answer_error_margin': '0.00001',
            'numerical_answer_type': 'exact_answer',
            'comments_html': '<p>Rounded correctly.</p>',
        },
    ]


# The three question types below run parse_settings over their <correct> tags,
# so answer_comments has to be declared there or it gets reported as an
# unprocessed field. The comments themselves are applied by _add_answer_comments
# regardless, which is why the assertions above cannot catch a regression here.
ANSWER_COMMENT_CASES = [
    pytest.param(
        parse_fill_in_the_blank_question,
        """
        <question id="q1" type="fill-in-the-blank">
            The capital of France is [blank].
            <correct text="Paris" answer_comments="Exactly right" />
        </question>
        """,
        id='fill-in-the-blank',
    ),
    pytest.param(
        parse_fill_in_multiple_blanks_question,
        """
        <question id="q1" type="fill-in-multiple-blanks">
            The U.S. flag has [stripes] stripes and [stars] stars.
            <correct text="13" blank="stripes" answer_comments="There are 13 original colonies." />
            <correct text="50" blank="stars" answer_comments="One star per state." />
        </question>
        """,
        id='fill-in-multiple-blanks',
    ),
    pytest.param(
        parse_numerical_question,
        """
        <question id="q1" type="numerical" numerical_answer_type="exact">
            What is pi to 5 decimal places?
            <correct answer_exact="3.14159" answer_error_margin="0.00001" answer_comments="Rounded correctly." />
        </question>
        """,
        id='numerical',
    ),
]


def _unprocessed_field_warnings(caplog):
    return [
        record.getMessage()
        for record in caplog.records
        if 'Unprocessed_fields' in record.getMessage()
    ]


@pytest.mark.parametrize('parser, xml', ANSWER_COMMENT_CASES)
def test_answer_comments_do_not_warn_about_unprocessed_fields(parser, xml, caplog):
    with caplog.at_level(logging.WARNING, logger='MDXCANVAS'):
        parser(_parse_question(xml))

    assert _unprocessed_field_warnings(caplog) == []


def test_genuinely_unknown_answer_attributes_are_rejected():
    """Guards the test above: it must fail if unknown attributes stop being caught.

    The message names the attribute and lists what the tag accepts, because the
    author reading it has to tell a typo apart from an attribute mdxcanvas does
    not support.
    """
    question = _parse_question("""
    <question id="q1" type="fill-in-the-blank">
        The capital of France is [blank].
        <correct text="Paris" answer_comments="Exactly right" not_a_real_attribute="x" />
    </question>
    """)

    with pytest.raises(ValueError) as caught:
        parse_fill_in_the_blank_question(question)

    message = str(caught.value)
    named, accepted = message.split('accepted here:')
    # Only the part before " on <tag>", since the message quotes the tag itself
    # and the tag naturally contains every attribute including the good ones.
    reported = named.split(' on ')[0]
    assert "Unknown attribute 'not_a_real_attribute'" in reported
    # answer_comments is read elsewhere, so it is accepted rather than unknown.
    assert 'answer_comments' not in reported
    assert 'answer_comments' in accepted
