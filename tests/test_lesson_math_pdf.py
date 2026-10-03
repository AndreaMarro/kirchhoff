"""Frazioni vettoriali, notazione complessa e provenienza del PDF offline."""
from fractions import Fraction as F
import re

import pytest

from kirchhoff.domain.exact import J, zeta_pow
from kirchhoff.pipeline.lesson import create_lesson
from kirchhoff.pipeline.lesson_math import add, divide, equation, multiply, number, symbol, equation_text
from kirchhoff.pipeline.lesson_pdf import export_pdf, _literal
from kirchhoff.pipeline.lesson_pdf_math import actual_text, draw_box, equation_boxes, expression_box


def test_fraction_has_distinct_baselines_and_a_vector_bar():
    box = expression_box(divide(number(7),number(29)))
    seven = next(cmd for cmd in box.commands if cmd[0]=='text' and cmd[3]=='7')
    denominator = next(cmd for cmd in box.commands if cmd[0]=='text' and cmd[3]=='29')
    bar = next(cmd for cmd in box.commands if cmd[0]=='line')
    assert seven[2] > bar[2] > denominator[2]
    assert box.above > seven[2] and box.below > -denominator[2]
    assert ' l S' in draw_box(box,42,600,_literal)


@pytest.mark.parametrize('value', [F(0),F(-3),F(5,7),J,-J,3-J,zeta_pow(1),zeta_pow(2),1+2*zeta_pow(1)])
def test_exact_numbers_render_as_vector_math_without_wire_dump(value):
    expr = equation(symbol('V(a)'),number(value),'V')
    boxes = equation_boxes(expr)
    assert all(box.width>0 and box.above>0 and box.below>=0 for box in boxes)
    commands = ''.join(draw_box(box,42,600,_literal) for box in boxes)
    assert 'j*' not in commands and 'sqrt(3)' not in commands
    assert actual_text(expr).startswith('FEFF')
    assert bytes.fromhex(actual_text(expr)[4:]).decode('utf-16-be') == equation_text(expr)


def test_long_sum_wraps_instead_of_losing_terms():
    expr = equation(add(*(multiply(number(F(i+1,37)),symbol(f'V(n{i})')) for i in range(20))),number(1),'A','E1')
    boxes = equation_boxes(expr,max_width=300)
    assert len(boxes)>1
    text = [cmd[3] for box in boxes for cmd in box.commands if cmd[0]=='text']
    assert all(f'n{i}' in text for i in range(20))
    assert all(box.width<=300 for box in boxes)


def test_complex_constant_as_factor_keeps_parentheses_even_one_basis_coordinate():
    box = expression_box(multiply(number(zeta_pow(2)),symbol('V(a)')))
    text = [cmd[3] for cmd in box.commands if cmd[0]=='text']
    assert '(' in text and ')' in text and 'j' in text
    simple = expression_box(multiply(number(3),symbol('V(a)')))
    assert '(' not in [cmd[3] for cmd in simple.commands if cmd[0]=='text']
    subtraction = expression_box(add(symbol('V(a)'),multiply(number(-1),symbol('V(b)'))))
    text = [cmd[3] for cmd in subtraction.commands if cmd[0]=='text']
    assert ' - ' in text and ' + ' not in text and '-1' not in text
    source = expression_box(add(symbol('V(a)'),multiply(number(1),number(-10))))
    text = [cmd[3] for cmd in source.commands if cmd[0]=='text']
    assert ' - ' in text and ' + ' not in text and '-10' not in text
    coefficient = expression_box(add(symbol('V(a)'),multiply(number(-2),symbol('V(b)'))))
    text = [cmd[3] for cmd in coefficient.commands if cmd[0]=='text']
    assert ' - ' in text and '2' in text and ' + ' not in text and '-2' not in text


def test_pdf_has_unicode_title_author_revision_and_accessible_math():
    lesson = create_lesson('@ac 10 rad/s\nV1 a 0 2 volt 30deg\nR1 a 0 3 ohm\n? current R1')
    pdf = export_pdf(lesson)
    assert pdf == export_pdf(lesson), 'La stessa lezione produce lo stesso documento.'
    title = re.search(rb'/Title <FEFF([A-F0-9]+)>',pdf).group(1)
    assert bytes.fromhex(title.decode()).decode('utf-16-be') == lesson['title']
    author = re.search(rb'/Author <FEFF([A-F0-9]+)>',pdf).group(1)
    assert bytes.fromhex(author.decode()).decode('utf-16-be') == 'Kirchhoff / con Andrea Marro'
    subject = re.search(rb'/Subject <FEFF([A-F0-9]+)>',pdf).group(1)
    subject = bytes.fromhex(subject.decode()).decode('utf-16-be')
    assert lesson['lesson_build'] in subject and lesson['fingerprint'] in subject
    assert b'/BaseFont /Times-Italic' in pdf and b'/BaseFont /Symbol' in pdf
    assert b'/ActualText <FEFF' in pdf
    assert b'Revisione '+lesson['lesson_build'][:12].encode() in pdf
    assert re.search(rb'/Info \d+ 0 R',pdf)


def test_invalid_math_is_not_silently_discarded():
    with pytest.raises(ValueError,match='AST matematico'):
        expression_box(dict(kind='invented'))
    with pytest.raises(ValueError,match='equazione'):
        equation_boxes(number(1))
    lesson = create_lesson('@ac 10 rad/s\nV1 a 0 2 volt 30deg\nR1 a 0 3 ohm\n? current R1')
    step = next(step for step in lesson['steps'] if 'math' in step)
    step['math'][0]['right'] = number(999)
    with pytest.raises(ValueError,match='non coincidono'):
        export_pdf(lesson)
