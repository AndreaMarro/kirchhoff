"""Campo Q(s): coefficienti Fraction ascendenti, nessuna dipendenza simbolica."""
from dataclasses import dataclass
from fractions import Fraction as F


def _q(value):
    if isinstance(value, bool) or not isinstance(value, (int, F)):
        raise TypeError('Il coefficiente deve essere un int o una Fraction esatta.')
    return F(value)


def _trim(values):
    result = list(values)
    if not result:
        raise ValueError('Un polinomio richiede almeno il coefficiente costante.')
    while len(result) > 1 and result[-1] == 0:
        result.pop()
    return tuple(result)


def _add(a, b):
    return _trim(tuple((a[i] if i < len(a) else F(0)) + (b[i] if i < len(b) else F(0))
                       for i in range(max(len(a), len(b)))))


def _multiply(a, b):
    result = [F(0)] * (len(a)+len(b)-1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            result[i+j] += x*y
    return _trim(result)


def _divide(a, b):
    """Divisione euclidea fra polinomi: quoziente e resto esatti."""
    a, b = _trim(a), _trim(b)
    if b == (F(0),):
        raise ZeroDivisionError('Divisione per il polinomio nullo.')
    quotient = [F(0)] * max(1, len(a)-len(b)+1)
    remainder = list(a)
    while tuple(remainder) != (F(0),) and len(remainder) >= len(b):
        shift, factor = len(remainder)-len(b), remainder[-1]/b[-1]
        quotient[shift] += factor
        for i, value in enumerate(b):
            remainder[i+shift] -= factor*value
        remainder = list(_trim(remainder))
    return _trim(quotient), tuple(remainder)


def _gcd(a, b):
    while b != (F(0),):
        a, b = b, _divide(a, b)[1]
    return tuple(x/a[-1] for x in a)


def _lift(value):
    return value if isinstance(value, RationalFunction) else RationalFunction.of(value)


@dataclass(frozen=True, slots=True, eq=False)
class RationalFunction:
    """n(s)/d(s), senza fattori comuni e con denominatore monico.

    Le tuple vanno dal termine costante al coefficiente del grado maggiore.
    Il costruttore richiede Fraction; ``of`` e ``polynomial`` accettano anche int.
    """
    numerator: tuple[F, ...]
    denominator: tuple[F, ...] = (F(1),)

    def __post_init__(self):
        if (not isinstance(self.numerator, tuple) or not isinstance(self.denominator, tuple)
                or any(not isinstance(c, F) for c in self.numerator+self.denominator)):
            raise TypeError('Numeratore e denominatore devono essere tuple di Fraction.')
        num, den = _trim(self.numerator), _trim(self.denominator)
        if den == (F(0),):
            raise ZeroDivisionError('Il denominatore della funzione razionale è nullo.')
        if num == (F(0),):
            den = (F(1),)
        else:
            common = _gcd(num, den)
            num, den = _divide(num, common)[0], _divide(den, common)[0]
            leading = den[-1]
            num, den = tuple(c/leading for c in num), tuple(c/leading for c in den)
        object.__setattr__(self, 'numerator', num)
        object.__setattr__(self, 'denominator', den)

    @staticmethod
    def of(value):
        return RationalFunction((_q(value),))

    @staticmethod
    def polynomial(*coefficients):
        return RationalFunction(tuple(_q(c) for c in coefficients))

    @property
    def numerator_degree(self):
        return len(self.numerator)-1 if self else -1

    @property
    def denominator_degree(self):
        return len(self.denominator)-1

    @property
    def proper(self):
        """Comprende il grado uguale: una costante rappresenta anche un impulso."""
        return self.numerator_degree <= self.denominator_degree

    def __bool__(self):
        return self.numerator != (F(0),)

    def __eq__(self, other):
        if isinstance(other, RationalFunction):
            return self.numerator == other.numerator and self.denominator == other.denominator
        if isinstance(other, (int, F)) and not isinstance(other, bool):
            return self.denominator == (F(1),) and self.numerator == (F(other),)
        return NotImplemented

    def __hash__(self):
        if self.denominator == (F(1),) and len(self.numerator) == 1:
            return hash(self.numerator[0])
        return hash((self.numerator, self.denominator))

    def __add__(self, other):
        value = _lift(other)
        return RationalFunction(_add(_multiply(self.numerator, value.denominator),
                                     _multiply(value.numerator, self.denominator)),
                                _multiply(self.denominator, value.denominator))

    __radd__ = __add__

    def __neg__(self):
        return RationalFunction(tuple(-c for c in self.numerator), self.denominator)

    def __sub__(self, other):
        return self + -_lift(other)

    def __rsub__(self, other):
        return _lift(other) + -self

    def __mul__(self, other):
        value = _lift(other)
        return RationalFunction(_multiply(self.numerator, value.numerator),
                                _multiply(self.denominator, value.denominator))

    __rmul__ = __mul__

    def inverse(self):
        if not self:
            raise ZeroDivisionError('Inverso della funzione razionale nulla.')
        return RationalFunction(self.denominator, self.numerator)

    def __truediv__(self, other):
        return self * _lift(other).inverse()

    def __rtruediv__(self, other):
        return _lift(other) * self.inverse()

    def __pow__(self, exponent):
        if isinstance(exponent, bool) or not isinstance(exponent, int):
            raise TypeError('L’esponente della funzione razionale deve essere intero.')
        if exponent < 0:
            return self.inverse() ** (-exponent)
        result, base = RationalFunction.of(1), self
        while exponent:
            if exponent % 2:
                result = result * base
            base, exponent = base * base, exponent // 2
        return result

    def evaluate(self, value):
        """Valuta solo in un punto razionale; un polo resta un errore esplicito."""
        value = _q(value)
        def horner(coefficients):
            result = F(0)
            for coefficient in reversed(coefficients):
                result = result*value+coefficient
            return result
        return horner(self.numerator)/horner(self.denominator)

    def limit_at_zero(self):
        return self.evaluate(F(0))

    def limit_at_infinity(self):
        """Limite algebrico in s, senza applicare il teorema del valore finale."""
        difference = self.numerator_degree-self.denominator_degree
        if difference > 0:
            raise ValueError('La funzione razionale non ha un limite finito all’infinito.')
        return F(0) if difference < 0 else self.numerator[-1]/self.denominator[-1]

    def to_json(self):
        return {'numerator':[str(c) for c in self.numerator],
                'denominator':[str(c) for c in self.denominator]}

    @staticmethod
    def from_json(value):
        if not isinstance(value, dict) or set(value) != {'numerator', 'denominator'}:
            raise ValueError('La funzione razionale richiede numeratore e denominatore.')
        coefficients = []
        for name in ('numerator', 'denominator'):
            raw = value[name]
            if not isinstance(raw, list) or not raw or any(not isinstance(c, str) for c in raw):
                raise ValueError('I coefficienti serializzati devono essere stringhe razionali.')
            try:
                coefficients.append(tuple(F(c) for c in raw))
            except (ValueError, ZeroDivisionError):
                raise ValueError('Un coefficiente serializzato non è razionale.') from None
        result = RationalFunction(*coefficients)
        if result.to_json() != value:
            raise ValueError('La funzione razionale serializzata non è in forma canonica.')
        return result


ZERO = RationalFunction.of(0)
ONE = RationalFunction.of(1)
S = RationalFunction.polynomial(0, 1)
