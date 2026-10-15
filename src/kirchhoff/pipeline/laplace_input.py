"""Ingresso Laplace esplicito: forme d'onda, unità e stati a t=0−."""
from dataclasses import dataclass, replace
from fractions import Fraction as F

from kirchhoff.domain.ir import IR
from kirchhoff.domain.laplace_rational import RationalFunction as RF, S


@dataclass(frozen=True, slots=True)
class LaplaceSource:
    component: str
    quantity: str
    waveform: str
    amplitude: F

    def __post_init__(self):
        if self.quantity not in {'voltage', 'current'} or self.waveform not in {'step', 'impulse'}:
            raise ValueError('Sorgente Laplace: servono tensione/corrente e step/impulse espliciti.')
        if not isinstance(self.amplitude, F):
            raise TypeError('L’ampiezza o area della sorgente deve essere una Fraction.')

    @property
    def unit(self):
        return ('V' if self.quantity == 'voltage' else 'A') + ('*s' if self.waveform == 'impulse' else '')

    @property
    def transform(self):
        return RF.of(self.amplitude)/S if self.waveform == 'step' else RF.of(self.amplitude)

    @property
    def label(self):
        return f'{self.amplitude} {self.unit} · {"u(t)" if self.waveform == "step" else "δ(t)"}'

    def to_json(self):
        return dict(component=self.component, quantity=self.quantity, waveform=self.waveform,
                    amplitude=dict(exact=str(self.amplitude), unit=self.unit), transform=self.transform.to_json())


@dataclass(frozen=True, slots=True)
class LaplaceInput:
    ir: IR
    sources: tuple[LaplaceSource, ...]
    capacitor_voltages: tuple[tuple[str, F], ...]
    inductor_currents: tuple[tuple[str, F], ...]

    @property
    def solver_inputs(self):
        return dict(source_transforms={source.component:source.transform for source in self.sources},
                    capacitor_voltages=dict(self.capacitor_voltages), inductor_currents=dict(self.inductor_currents))

    @property
    def source_labels(self):
        return {source.component:source.label for source in self.sources}

    def to_json(self):
        return dict(schema='laplace-inputs.v1', initial_time='0-', sources=[source.to_json() for source in self.sources],
                    capacitor_voltages=[dict(component=cid, exact=str(value), unit='V') for cid,value in self.capacitor_voltages],
                    inductor_currents=[dict(component=cid, exact=str(value), unit='A') for cid,value in self.inductor_currents])


def parse_laplace(text: str) -> LaplaceInput:
    """Il carrier IR delle sorgenti vale zero: soltanto la metadata è autorevole.

    Non attribuiamo all'area di un impulso l'unità di una tensione ordinaria.
    Il renderer Laplace richiede le etichette derivate dalle sorgenti qui lette.
    """
    from kirchhoff.pipeline.netlist import leggi

    electrical, sources, initials = [], [], {}
    declared, questioned = False, False
    def amount(raw, row):
        try:
            return F(raw)
        except (ValueError, ZeroDivisionError):
            raise ValueError(f'riga {row}: valore Laplace non razionale esatto.') from None
    for row, line in enumerate(text.splitlines(), 1):
        tokens = line.split('#', 1)[0].split()
        if not tokens:
            continue
        if tokens[0] == '@laplace':
            if declared or electrical or initials or len(tokens) != 1:
                raise ValueError(f'riga {row}: usa una sola direttiva @laplace, prima di tutti i dati.')
            declared = True
            continue
        if not declared:
            raise ValueError(f'riga {row}: il circuito Laplace deve iniziare con @laplace.')
        if tokens[0] == '@initial':
            if questioned or len(tokens) != 5:
                raise ValueError(f'riga {row}: usa @initial C1 voltage <valore> volt oppure @initial L1 current <valore> ampere, prima della domanda.')
            _, cid, quantity, value, unit = tokens
            if cid in initials:
                raise ValueError(f'riga {row}: condizione iniziale ripetuta per {cid}.')
            if (quantity, unit) not in {('voltage', 'volt'), ('current', 'ampere')}:
                raise ValueError(f'riga {row}: grandezza o unità della condizione iniziale non valida.')
            initials[cid] = (quantity, amount(value, row))
            continue
        if tokens[0].startswith('@'):
            raise ValueError(f'riga {row}: direttiva {tokens[0]} non ammessa con @laplace.')
        if tokens[0] == '?':
            if questioned or len(tokens) != 3 or tokens[1] not in {'voltage', 'current'}:
                raise ValueError(f'riga {row}: Laplace serve una sola domanda ? voltage/current <componente>.')
            questioned = True
            electrical.append(' '.join(tokens))
            continue
        if questioned:
            raise ValueError(f'riga {row}: scrivi tutti i componenti prima della domanda.')
        kind = tokens[0][0].upper()
        if kind in {'V', 'I'}:
            if len(tokens) != 6 or tokens[-1] not in {'step', 'impulse'}:
                raise ValueError(f'riga {row}: una sorgente Laplace richiede step o impulse esplicito.')
            cid, p, q, value, unit, waveform = tokens
            expected = ('volt' if kind == 'V' else 'ampere') + ('*s' if waveform == 'impulse' else '')
            if unit != expected:
                raise ValueError(f'riga {row}: {waveform} richiede {expected}; l’impulso dichiara un’area.')
            sources.append(LaplaceSource(cid, 'voltage' if kind == 'V' else 'current', waveform, amount(value, row)))
            electrical.append(f'{cid} {p} {q} 0 {"volt" if kind == "V" else "ampere"}')
        elif kind in {'R', 'L', 'C'}:
            electrical.append(' '.join(tokens))
        else:
            raise ValueError(f'riga {row}: la lezione Laplace ammette R, L, C e sorgenti indipendenti V/I.')
    if not declared or not questioned:
        raise ValueError('La lezione Laplace richiede @laplace e una domanda esplicita.')
    ir = replace(leggi('\n'.join(electrical)), domain='laplace')
    required = {c.id:('voltage' if c.type == 'capacitor' else 'current')
                for c in ir.components if c.type in {'capacitor', 'inductor'}}
    if set(initials) != set(required) or any(initials[cid][0] != quantity for cid, quantity in required.items()):
        raise ValueError('Dichiara una tensione iniziale per ogni C e una corrente iniziale per ogni L, anche se zero; nessun’altra condizione iniziale è ammessa.')
    return LaplaceInput(ir, tuple(sources),
                        tuple((cid, initials[cid][1]) for cid, q in required.items() if q == 'voltage'),
                        tuple((cid, initials[cid][1]) for cid, q in required.items() if q == 'current'))
