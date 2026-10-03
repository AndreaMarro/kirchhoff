"""Potenza AC: kernel esistente e controllo rettangolare indipendente.

Il secondo prodotto usa coppie (razionale, coefficiente di sqrt(3)) e i
valori del tableau. Non riusa il coniugato o il prodotto complesso del
kernel: un errore comune di segno o di fattore non basta a concordare.
"""
from fractions import Fraction as F

from kirchhoff.domain.exact import Cyc12, ZERO
from kirchhoff.domain.ir import IR
from kirchhoff.domain.refusal import Refusal
from kirchhoff.domain.verify import phasor_complex_powers


def _rectangular(value: Cyc12) -> tuple[tuple[F, F], tuple[F, F]]:
    a, b, c, d = value.c
    return (a + c / 2, b / 2), (d + b / 2, c / 2)


def _real_product(a: tuple[F, F], b: tuple[F, F]) -> tuple[F, F]:
    return a[0] * b[0] + 3 * a[1] * b[1], a[0] * b[1] + a[1] * b[0]


def _rectangular_power(voltage: Cyc12, current: Cyc12, amplitude: str) -> Cyc12:
    """P = Vr Ir + Vi Ii; Q = Vi Ir - Vr Ii, poi scala RMS/picco."""
    vr, vi = _rectangular(voltage)
    ir, ii = _rectangular(current)
    rr, xx = _real_product(vr, ir), _real_product(vi, ii)
    xr, rx = _real_product(vi, ir), _real_product(vr, ii)
    divisor = 2 if amplitude == 'peak' else 1
    p, pr = ((rr[index] + xx[index]) / divisor for index in (0, 1))
    q, qr = ((xr[index] - rx[index]) / divisor for index in (0, 1))
    return Cyc12((p - qr, 2 * pr, 2 * qr, q - pr))


def checked_complex_powers(ir: IR, primary: dict, independent: dict,
                           amplitude: str) -> dict[str, Cyc12] | Refusal:
    """Richiede scala esplicita, copertura completa, confronto e bilancio."""
    if amplitude not in {'rms', 'peak'}:
        return Refusal('claim_unsupported', 'power', 'request',
                       'La potenza richiede @amplitude rms oppure @amplitude peak: unspecified non basta.')
    powers = phasor_complex_powers(ir, primary, amplitude=amplitude)
    if set(powers) != {component.id for component in ir.components}:
        return Refusal('path_disagreement', 'power', 'request',
                       'Il calcolo delle potenze non copre tutti e soli i componenti.')
    for component in ir.components:
        cid = component.id
        expected = _rectangular_power(independent[cid]['voltage'], independent[cid]['current'], amplitude)
        if not isinstance(powers[cid], Cyc12) or powers[cid] != expected:
            return Refusal('path_disagreement', cid, 'component',
                           f'{cid}: la potenza non coincide con il prodotto rettangolare indipendente.')
    if sum(powers.values(), ZERO) != ZERO:
        return Refusal('residual', 'power', 'request',
                       'Il bilancio delle potenze complesse non è esattamente nullo.')
    return powers
