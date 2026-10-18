"""La correttezza del calcolo non approva automaticamente i testi didattici."""
import io

import pytest
from pypdf import PdfReader

from kirchhoff.pipeline.lesson import create_lesson
from kirchhoff.pipeline.lesson_pdf import export_pdf


@pytest.mark.parametrize('netlist', [
    'V1 a 0 12 volt\nR1 a 0 1000 ohm\n? voltage R1',
    '@ac 100 rad/s\nV1 a 0 10 volt 0deg\nR1 a 0 5 ohm\n? current R1',
    '@laplace\nV1 e 0 10 volt step\nR1 e a 2 ohm\nC1 a 0 1/3 farad\n@initial C1 voltage 4 volt\n? voltage C1',
])
def test_calcolo_e_pdf_distinguono_testo_draft_da_verifica_elettrica(netlist):
    lesson = create_lesson(netlist)
    assert lesson['outcome'] == 'solved'
    assert lesson.get('editorial_status') == 'DRAFT'
    assert lesson['verification']['product_verified'] is False
    pages = PdfReader(io.BytesIO(export_pdf(lesson))).pages
    assert len(pages) > 1
    assert all('Spiegazioni DRAFT' in page.extract_text() for page in pages)
