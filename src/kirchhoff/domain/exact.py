"""Aritmetica esatta: campo ciclotomico Q(zeta_12) e algebra lineare su un campo."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

_Q0 = Fraction(0)
_Q1 = Fraction(1)


class SingularSystemError(ValueError):
    """Il sistema lineare è matematicamente singolare."""


@dataclass(frozen=True, slots=True, eq=False)
class Cyc12:
    """Elemento di Q(zeta_12), come quattro razionali sulla base (1, z, z^2, z^3)."""

    c: tuple[Fraction, Fraction, Fraction, Fraction]

    @staticmethod
    def of(x: int | Fraction) -> Cyc12:
        if not isinstance(x, (int, Fraction)):
            raise TypeError(
                f"valore non esatto nel campo ciclotomico: {type(x).__name__}. "
                "Serve un int o una Fraction; un float porta rumore binario.")
        return Cyc12((Fraction(x), _Q0, _Q0, _Q0))

    def __add__(self, o: object) -> Cyc12:
        q = _lift(o)
        return Cyc12((self.c[0] + q.c[0], self.c[1] + q.c[1],
                      self.c[2] + q.c[2], self.c[3] + q.c[3]))

    __radd__ = __add__

    def __neg__(self) -> Cyc12:
        return Cyc12((-self.c[0], -self.c[1], -self.c[2], -self.c[3]))

    def __sub__(self, o: object) -> Cyc12:
        return self + (-_lift(o))

    def __rsub__(self, o: object) -> Cyc12:
        return _lift(o) + (-self)

    def __mul__(self, o: object) -> Cyc12:
        q = _lift(o)
        p = [_Q0] * 7
        for i, a in enumerate(self.c):
            for k, b in enumerate(q.c):
                p[i + k] += a * b
        return Cyc12((p[0] - p[4] - p[6], p[1] - p[5], p[2] + p[4], p[3] + p[5]))

    __rmul__ = __mul__

    def inverse(self) -> Cyc12:
        if not self:
            raise ZeroDivisionError("inverso di zero nel campo ciclotomico")
        cols = [(self * b).c for b in (ONE, ZETA, ZETA2, ZETA3)]
        m = [[cols[k][row] for k in range(4)] for row in range(4)]
        x = solve_linear(m, [_Q1, _Q0, _Q0, _Q0])
        return Cyc12((x[0], x[1], x[2], x[3]))

    def __truediv__(self, o: object) -> Cyc12:
        return self * _lift(o).inverse()

    def __rtruediv__(self, o: object) -> Cyc12:
        return _lift(o) * self.inverse()

    def conjugate(self) -> Cyc12:
        a0, a1, a2, a3 = self.c
        return Cyc12((a0 + a2, a1, -a2, -a1 - a3))

    def __eq__(self, o: object) -> bool:
        if isinstance(o, Cyc12):
            return self.c == o.c
        if isinstance(o, (int, Fraction)):
            return self.c == (Fraction(o), _Q0, _Q0, _Q0)
        return NotImplemented

    def __bool__(self) -> bool:
        return any(x != 0 for x in self.c)

    def __hash__(self) -> int:
        return hash(self.c)


def _lift(x: object) -> Cyc12:
    if isinstance(x, Cyc12):
        return x
    return Cyc12.of(x)  # type: ignore[arg-type]


ZERO = Cyc12((_Q0, _Q0, _Q0, _Q0))
ONE = Cyc12((_Q1, _Q0, _Q0, _Q0))
ZETA = Cyc12((_Q0, _Q1, _Q0, _Q0))
ZETA2 = Cyc12((_Q0, _Q0, _Q1, _Q0))
ZETA3 = Cyc12((_Q0, _Q0, _Q0, _Q1))

J = ZETA3
SQRT3 = Cyc12((_Q0, Fraction(2), _Q0, Fraction(-1)))
A120 = Cyc12((Fraction(-1), _Q0, _Q1, _Q0))
A240 = Cyc12((_Q0, _Q0, Fraction(-1), _Q0))


def zeta_pow(k: int) -> Cyc12:
    out = ONE
    for _ in range(k % 12):
        out = out * ZETA
    return out


def solve_linear(a: list[list], b: list) -> list:
    n = len(b)
    m = [list(row) + [b[i]] for i, row in enumerate(a)]
    for col in range(n):
        pivot = next((r for r in range(col, n) if m[r][col]), None)
        if pivot is None:
            raise SingularSystemError(f"sistema singolare alla colonna {col}")
        m[col], m[pivot] = m[pivot], m[col]
        p = m[col][col]
        m[col] = [v / p for v in m[col]]
        for r in range(n):
            if r != col and m[r][col]:
                f = m[r][col]
                m[r] = [vr - f * vc for vr, vc in zip(m[r], m[col])]
    return [m[i][n] for i in range(n)]


def determinant(m: list[list[Fraction]]) -> Fraction:
    n = len(m)
    rows = [row[:] for row in m]
    det = _Q1
    for col in range(n):
        pivot = next((r for r in range(col, n) if rows[r][col] != 0), None)
        if pivot is None:
            return _Q0
        if pivot != col:
            rows[col], rows[pivot] = rows[pivot], rows[col]
            det = -det
        det *= rows[col][col]
        inv = _Q1 / rows[col][col]
        rows[col] = [v * inv for v in rows[col]]
        for r in range(col + 1, n):
            if rows[r][col] != 0:
                f = rows[r][col]
                rows[r] = [vr - f * vc for vr, vc in zip(rows[r], rows[col])]
    return det
