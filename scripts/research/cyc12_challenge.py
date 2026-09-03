"""Challenge indipendente per Q(ζ12) — SymPy come oracolo esatto, Cyc12 come SUT.

Eseguire effimero:
    uv run --with sympy python scripts/research/cyc12_challenge.py

Non modifica il dominio. Se fallisce, si apre decisione:
    KEEP_CUSTOM_WITH_VALIDATED_SCOPE | FIX_CUSTOM_THEN_RETEST | MIGRATE
"""
from fractions import Fraction
import sys

try:
    import sympy as sp
except ImportError:
    print("sympy non installato: esegui `uv run --with sympy python scripts/research/cyc12_challenge.py`")
    sys.exit(2)

from kirchhoff.domain.exact import Cyc12, ONE, ZETA, ZETA2, ZETA3, J, SQRT3, A120, A240, zeta_pow, solve_linear, determinant

def F(n,d=1): return Fraction(n,d)

# SymPy zeta12 as exp(2*pi*I/12)
zeta_sym = sp.exp(2*sp.pi*sp.I/12)
# mapping Cyc12 -> SymPy
def to_sym(c: Cyc12):
    # base (1, z, z^2, z^3)
    return c.c[0] + c.c[1]*zeta_sym + c.c[2]*zeta_sym**2 + c.c[3]*zeta_sym**3

def check(name, cyc_val, sym_expected):
    sym_val = to_sym(cyc_val)
    diff = sp.simplify(sym_val - sym_expected)
    ok = diff == 0 or diff.equals(0)  # sympy structural
    if not ok:
        # fallback numeric
        try:
            ok = abs(complex(sym_val.evalf()) - complex(sym_expected.evalf())) < 1e-9
            diff = f"numeric diff {abs(complex(sym_val.evalf()) - complex(sym_expected.evalf()))}"
        except Exception:
            pass
    print(f"{name:30} {'PASS' if ok else 'FAIL'}  cyc={cyc_val.c} sym={sym_expected} diff={diff}")
    return ok

ok_all = True

# identità base
ok_all &= check("zeta^12=1", zeta_pow(12), sp.Integer(1))
ok_all &= check("zeta^6=-1", zeta_pow(6), sp.Integer(-1))
ok_all &= check("zeta^3=j", zeta_pow(3), sp.I)
ok_all &= check("j^2=-1", J*J, sp.Integer(-1))
ok_all &= check("sqrt3^2=3", SQRT3*SQRT3, sp.Integer(3))
ok_all &= check("a120 = zeta^4", A120, zeta_sym**4)
ok_all &= check("a240 = zeta^8", A240, zeta_sym**8)
ok_all &= check("1 + a + a^2=0", ONE + A120 + A120*A120, sp.Integer(0))
ok_all &= check("zeta * zeta^-1 =1", ZETA * zeta_pow(11), sp.Integer(1))

# operazioni campo
a = Cyc12((F(1,2), F(3), F(-1), F(2)))
b = Cyc12((F(2), F(-1,3), F(5), F(0)))
ok_all &= check("add", a+b, to_sym(a)+to_sym(b))
ok_all &= check("sub", a-b, to_sym(a)-to_sym(b))
ok_all &= check("mul", a*b, to_sym(a)*to_sym(b))
ok_all &= check("inv", a * a.inverse(), sp.Integer(1))
ok_all &= check("div", a / b * b, to_sym(a))  # (a/b)*b == a
ok_all &= check("conj", a.conjugate(), sp.conjugate(to_sym(a)))  # may differ by simplification but check property: a*conj in R

# Round-trip Fraction
ok_all &= check("Fraction roundtrip", Cyc12.of(F(7,3)), sp.Rational(7,3))

# Determinante e solve lineare vs SymPy
def sym_det(mat):
    return sp.Matrix([[sp.Rational(str(v)) if isinstance(v, Fraction) else to_sym(v) for v in row] for row in mat]).det()

m = [[F(2), F(1), F(0)], [F(1), F(2), F(1)], [F(0), F(1), F(2)]]
det_cyc = determinant(m)
det_sym = sym_det(m)
print(f"{'det 3x3':30} {'PASS' if det_cyc == det_sym else 'FAIL'}  cyc={det_cyc} sym={det_sym}")
ok_all &= det_cyc == det_sym

# Solve lineare 2x2
a_mat = [[F(2), F(1)], [F(1), F(3)]]
b_vec = [F(5), F(6)]
sol = solve_linear([row[:] for row in a_mat], b_vec)
# verifica A*sol == b
ok = all(sum(a_mat[i][j]*sol[j] for j in range(2)) == b_vec[i] for i in range(2))
print(f"{'solve_linear 2x2':30} {'PASS' if ok else 'FAIL'}  sol={sol}")
ok_all &= ok
# confronto SymPy
sym_sol = sp.Matrix([[sp.Rational(2), sp.Rational(1)],[sp.Rational(1), sp.Rational(3)]]).LUsolve(sp.Matrix([sp.Rational(5), sp.Rational(6)]))
ok_all &= all(sol[i] == Fraction(sym_sol[i]) for i in range(2))

# piccolo sistema fasoriale: partitore AC con Cyc12 già verificato in domain, qui solo sanity
print("\nCYC12_CHALLENGE_RESULT:", "PASS" if ok_all else "FAIL")
sys.exit(0 if ok_all else 1)
