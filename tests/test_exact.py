"""Aritmetica esatta sul campo ciclotomico Q(zeta_12).

Il campo esiste per una ragione sola: il trifase. `e^(j120)` = -1/2 + j*sqrt(3)/2
non e' un complesso razionale, e con i float un confronto a zero esatto non esiste
piu'. Q(zeta_12) e' la piu' piccola estensione di Q che contiene insieme `j` e
`sqrt(3)`.
"""

from fractions import Fraction

import pytest

from kirchhoff.domain.exact import (
    A120,
    A240,
    J,
    ONE,
    SQRT3,
    ZERO,
    Cyc12,
    determinant,
    solve_linear,
    zeta_pow,
)


def test_potenze_di_zeta():
    assert zeta_pow(0) == ONE
    assert zeta_pow(3) == J
    assert zeta_pow(4) == A120
    assert zeta_pow(-4) == A240        # -120 gradi
    assert zeta_pow(12) == ONE


def test_j_al_quadrato_fa_meno_uno():
    assert J * J == -ONE


def test_sqrt3_al_quadrato_fa_tre():
    assert SQRT3 * SQRT3 == Cyc12.of(3)


def test_rotazione_di_120_gradi_e_di_ordine_tre():
    """Given la rotazione di 120 gradi, when la si applica tre volte, then torna l'identita'."""
    assert A120 * A120 == A240
    assert A120 * A120 * A120 == ONE


def test_le_tre_fasi_sommano_esattamente_a_zero():
    """Il criterio che nessun float puo' soddisfare: la somma delle tre fasi e' zero."""
    assert ONE + A120 + A240 == ZERO


def test_a120_ha_la_forma_attesa():
    """e^(j120) = -1/2 + j*sqrt(3)/2, espresso nella base del campo."""
    assert A120 == Cyc12.of(Fraction(-1, 2)) + J * SQRT3 / Cyc12.of(2)


def test_inverso_e_divisione():
    z = Cyc12.of(3) + J * Cyc12.of(4)          # 3 + 4j, modulo 5
    assert z * z.inverse() == ONE
    assert z / z == ONE
    assert (z * z) / z == z


def test_inverso_di_zero_rifiutato():
    with pytest.raises(ZeroDivisionError):
        ZERO.inverse()


def test_coniugio():
    z = Cyc12.of(3) + J * Cyc12.of(4)
    assert z.conjugate() == Cyc12.of(3) - J * Cyc12.of(4)
    assert z * z.conjugate() == Cyc12.of(25)     # modulo al quadrato, esatto
    assert A120.conjugate() == A240


def test_coercizione_da_interi_e_frazioni():
    assert J + 0 == J
    assert 0 + J == J
    assert J - 0 == J
    assert 1 - ONE == ZERO
    assert J * 1 == J
    assert 1 * J == J
    assert Fraction(1, 2) * Cyc12.of(2) == ONE
    assert 1 / J == -J                            # 1/j = -j
    assert J / 1 == J
    assert ONE == 1                               # confronto diretto con un intero
    assert ZERO == Fraction(0)


def test_negazione_e_verita():
    assert -J == ZERO - J
    assert bool(J) is True
    assert bool(ZERO) is False


def test_uguaglianza_con_tipi_estranei():
    assert (J == "non un numero") is False
    assert J != ONE


def test_solve_linear_su_razionali():
    """2x + y = 5 ; x - y = 1  ->  x = 2, y = 1."""
    x = solve_linear([[Fraction(2), Fraction(1)], [Fraction(1), Fraction(-1)]],
                     [Fraction(5), Fraction(1)])
    assert x == [Fraction(2), Fraction(1)]


def test_solve_linear_scambia_le_righe_quando_il_pivot_e_nullo():
    x = solve_linear([[Fraction(0), Fraction(1)], [Fraction(1), Fraction(0)]],
                     [Fraction(3), Fraction(4)])
    assert x == [Fraction(4), Fraction(3)]


def test_solve_linear_su_campo_ciclotomico():
    x = solve_linear([[J]], [ONE])
    assert x == [-J]


def test_sistema_singolare_rifiutato():
    with pytest.raises(ValueError):
        solve_linear([[Fraction(1), Fraction(2)], [Fraction(2), Fraction(4)]],
                     [Fraction(1), Fraction(2)])


def test_determinante():
    assert determinant([[Fraction(2), Fraction(1)], [Fraction(1), Fraction(-1)]]) == Fraction(-3)
    assert determinant([[Fraction(1), Fraction(2)], [Fraction(2), Fraction(4)]]) == 0
    assert determinant([]) == Fraction(1)


def test_determinante_con_scambio_di_righe_cambia_segno():
    assert determinant([[Fraction(0), Fraction(1)], [Fraction(1), Fraction(0)]]) == Fraction(-1)
