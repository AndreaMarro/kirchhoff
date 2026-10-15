"""Il trasporto riconosce il vocabolario strutturale, mai nuove licenze."""
import ast
import re
from pathlib import Path

import pytest

from kirchhoff.domain.transform.catalog import IDENTITY_ATTRIBUTES

RADICE = Path(__file__).resolve().parent.parent


@pytest.mark.parametrize("file", [
    "web/src/session/guards.ts", "web/scripts/artifact-contract.mjs",
])
def test_k4_attributi_di_identita_dei_reader_uguali_alla_fonte(file):
    testo = (RADICE / file).read_text(encoding="utf-8")
    dichiarazioni = re.findall(
        r"export const STEP_IDENTITY_ATTRIBUTES = (\[[\s\S]*?\])", testo)
    assert len(dichiarazioni) == 1
    # Letterali di sole stringhe, niente import di un secondo Catalogo.
    assert tuple(ast.literal_eval(dichiarazioni[0])) == IDENTITY_ATTRIBUTES
