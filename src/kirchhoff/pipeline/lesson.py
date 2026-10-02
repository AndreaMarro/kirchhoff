"""Lezione deterministica derivata da una chiusura del kernel.

Le identità, i Claim e il certificatore non cambiano. Il percorso didattico
è una derivazione di presentazione: ogni risposta viene confrontata ESATTAMENTE
con la radice canonica prima dell'esposizione. Non è un nuovo Claim VERIFIED.
Nessun LLM, nessun arrotondamento nel ragionamento, nessuna dipendenza esterna.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from fractions import Fraction as F
import hashlib
from decimal import Decimal, localcontext
import itertools
from pathlib import Path

from kirchhoff.domain.ir import IR, Component
from kirchhoff.domain.refusal import Refusal
from kirchhoff.domain.proof.session import DOCUMENT_PROFILE
from kirchhoff.pipeline.failure import Failure
from kirchhoff.pipeline.netlist import leggi
from kirchhoff.pipeline.proof_run import run_proof_session_con_run
from kirchhoff.pipeline.resolve import _source_sha
from kirchhoff.pipeline.presentation import equazione_analitica
from kirchhoff.pipeline.lesson_svg import schematic


def number(v: F) -> str:
    """Forma esatta compatta; i decimali finiti dell'ingresso restano esatti."""
    return str(v.numerator) if v.denominator == 1 else str(v)


@dataclass(frozen=True)
class Branch:
    parts: tuple[tuple[Component, int], ...]

    @property
    def resistance(self) -> F:
        return sum((c.value.amount for c, _ in self.parts if c.type == 'resistor'), F(0))

    def emf(self, active: str | None = None) -> F:
        return sum((s*c.value.amount for c, s in self.parts
                    if c.type == 'voltage_source_dc' and (active is None or c.id == active)), F(0))

    def imposed(self, active: str | None = None) -> F | None:
        sources = [(c, s) for c, s in self.parts if c.type == 'current_source_dc']
        if not sources:
            return None
        if len(sources) != 1:
            raise ValueError('Più sorgenti di corrente nello stesso ramo: usare il percorso generale.')
        c, sign = sources[0]
        return sign*c.value.amount if active is None or c.id == active else F(0)


def branches(ir: IR) -> tuple[str, str, tuple[Branch, ...]] | None:
    """Riconosce rami fra due morsetti; nessuna ipotesi sul nome dei nodi."""
    if any(c.type not in {'resistor', 'voltage_source_dc', 'current_source_dc'} for c in ir.components):
        return None
    adjacency: dict[str, list[Component]] = {n: [] for n in ir.nodes}
    for c in ir.components:
        for n in c.terminals:
            adjacency[n].append(c)
    hubs = [n for n in ir.nodes if len(adjacency[n]) != 2]
    if not hubs:
        source = next((c for c in ir.components if c.type != 'resistor'), None)
        if source is None:
            return None
        hubs = list(source.terminals)
        if source.type == 'current_source_dc' and ir.requests:
            target = ir.component(ir.requests[0].target)
            if target.type == 'resistor':
                hubs = list(target.terminals)
    if len(hubs) != 2:
        return None
    p, q = sorted(hubs, key=lambda n: (n == '0', n))
    used: set[str] = set()
    result = []
    for first in sorted(adjacency[p], key=lambda c: (c.type == 'resistor', c.id)):
        current, c, path = p, first, []
        while True:
            if c.id in used:
                return None
            used.add(c.id)
            sign = 1 if c.terminals[0] == current else -1
            path.append((c, sign))
            current = c.terminals[1] if sign == 1 else c.terminals[0]
            if current == q:
                break
            candidates = [x for x in adjacency[current] if x.id != c.id]
            if len(candidates) != 1 or current == p:
                return None
            c = candidates[0]
        result.append(Branch(tuple(path)))
    if len(used) != len(ir.components):
        return None
    return p, q, tuple(result)


def potential(bs: tuple[Branch, ...], active: str | None = None) -> tuple[F, list[F]]:
    """Millman e Ohm, con ramo a tensione imposta trattato esplicitamente."""
    currents = [b.imposed(active) for b in bs]
    fixed = [i for i, b in enumerate(bs) if b.resistance == 0 and currents[i] is None]
    if len(fixed) > 1:
        raise ValueError('Le correnti di più sorgenti ideali parallele non sono determinate separatamente.')
    g = sum((1/b.resistance for i, b in enumerate(bs) if currents[i] is None and b.resistance), F(0))
    if fixed:
        u = bs[fixed[0]].emf(active)
    elif g:
        u = (sum((b.emf(active)/b.resistance for i, b in enumerate(bs) if currents[i] is None), F(0))
             - sum((x for x in currents if x is not None), F(0)))/g
    else:
        raise ValueError('La tensione non è determinata dai rami disponibili.')
    for i, b in enumerate(bs):
        if currents[i] is None and b.resistance:
            currents[i] = (u-b.emf(active))/b.resistance
    if fixed:
        currents[fixed[0]] = -sum((x for x in currents if x is not None), F(0))
    return u, [F(x) for x in currents]  # type: ignore[arg-type]


def observed(bs: tuple[Branch, ...], target: str, quantity: str, active: str | None = None) -> F:
    u, currents = potential(bs, active)
    for b, current in zip(bs, currents):
        for c, sign in b.parts:
            if c.id != target:
                continue
            if quantity == 'current':
                return sign*current
            if c.type == 'resistor':
                return sign*current*c.value.amount
            if c.type == 'voltage_source_dc':
                return c.value.amount if active is None or active == c.id else F(0)
            return sign*(u-b.emf(active)-current*b.resistance)
    raise ValueError('Bersaglio assente dai rami riconosciuti.')


def _verify_thevenin_port(ir: IR, target: str, p: str, q: str, vth: F, rth: F) -> None:
    """Controlla i due risultati intermedi con il tableau di ramo indipendente.

    La sorgente di prova a corrente zero misura la porta a vuoto senza
    ricostruire le equazioni del percorso Millman. La prova a 1 A, dopo lo
    spegnimento delle sorgenti, misura la resistenza vista dai medesimi morsetti.
    """
    from kirchhoff.domain.independent_dc import solve_dc_tableau

    remaining = tuple(c for c in ir.components if c.id != target)
    probe_id = 'I_port_verifica'
    while any(c.id == probe_id for c in remaining):
        probe_id += 'x'
    open_probe = Component.of(probe_id, 'current_source_dc', (p, q), F(0), probe_id)
    opened = replace(ir, components=remaining + (open_probe,), requests=())
    independent_vth = solve_dc_tableau(opened)[probe_id]['voltage']
    if vth != independent_vth:
        raise ValueError('La tensione a vuoto di Thévenin non coincide con il tableau indipendente: lezione non esposta.')

    deactivated = tuple(Component.of(c.id, c.type, c.terminals, F(0), c.symbolic)
                        if c.type in {'voltage_source_dc', 'current_source_dc'} else c
                        for c in remaining)
    test_probe = Component.of(probe_id, 'current_source_dc', (q, p), F(1), probe_id)
    test_ir = replace(ir, components=deactivated + (test_probe,), requests=())
    independent_rth = -solve_dc_tableau(test_ir)[probe_id]['voltage']
    if rth != independent_rth:
        raise ValueError('La resistenza vista di Thévenin non coincide con il tableau indipendente: lezione non esposta.')


def _verify_superposition_contribution(ir: IR, active: str, target: str,
                                       quantity: str, p: str, q: str,
                                       contribution: F, port_voltage: F) -> None:
    """Controlla separatamente il sottocircuito e la sua tensione di porta.

    Il tableau usa tensioni/correnti di ramo e KVL su un albero, indipendenti
    dal riconoscitore Millman che ha generato il passaggio da pubblicare.
    Una sonda ideale da 0 A misura V(p)-V(q) senza perturbare il circuito.
    """
    from kirchhoff.domain.independent_dc import solve_dc_tableau

    off = tuple(Component.of(c.id, c.type, c.terminals,
                             c.value.amount if c.id == active or c.type == 'resistor' else F(0),
                             c.symbolic) for c in ir.components)
    probe_id = 'I_port_sovrapposizione'
    while any(c.id == probe_id for c in off):
        probe_id += 'x'
    probe = Component.of(probe_id, 'current_source_dc', (p, q), F(0), probe_id)
    subcircuit = replace(ir, components=off + (probe,), requests=())
    independent = solve_dc_tableau(subcircuit)
    if independent[target][quantity] != contribution:
        raise ValueError(f'Il contributo di {active} in sovrapposizione non coincide con il tableau indipendente: lezione non esposta.')
    if independent[probe_id]['voltage'] != port_voltage:
        raise ValueError(f'La tensione del sottocircuito {active} in sovrapposizione non coincide con il tableau indipendente: lezione non esposta.')


def _verify_branch_state(ir: IR, bs: tuple[Branch, ...], u: F, currents: list[F]) -> None:
    """Ogni ramo mostrato deve concordare col tableau, anche fuori dalla domanda.

    Un controllo della sola risposta finale non vede una corrente sbagliata su
    un altro ramo né una tensione comune errata se si chiede una corrente
    impressa. Il tableau è assemblato senza il riconoscitore Millman.
    """
    from kirchhoff.domain.independent_dc import solve_dc_tableau

    independent = solve_dc_tableau(ir)
    for branch, current in zip(bs, currents, strict=True):
        for component, sign in branch.parts:
            if sign * current != independent[component.id]['current']:
                raise ValueError('La corrente di un passaggio intermedio non coincide con il tableau indipendente: lezione non esposta.')
        drop = sum((sign * independent[component.id]['voltage']
                    for component, sign in branch.parts), F(0))
        if drop != u:
            raise ValueError('La tensione comune di un passaggio intermedio non coincide con il tableau indipendente: lezione non esposta.')


def _step(title: str, explanation: str, svg: str, equations: list[str] | None = None,
          focus: list[str] | None = None) -> dict:
    return dict(title=title, explanation=explanation, svg=svg,
                equations=equations or [], focus=focus or [])


def create_lesson(text: str, method: str = 'auto', source_sha: str = '') -> dict:
    """Un solo ingresso per catalogo, input editato, web e PDF."""
    if method not in {'auto', 'millman', 'norton', 'thevenin', 'superposition', 'nodal', 'star_delta'}:
        raise ValueError('Metodo sconosciuto.')
    if len(text) > 16000:
        raise ValueError('Circuito troppo lungo: massimo 16000 caratteri.')
    ir = leggi(text)
    if len(ir.components) > 32 or len(ir.nodes) > 24:
        raise ValueError('Questo banco accetta al massimo 32 componenti e 24 nodi.')
    if len(ir.requests) != 1:
        raise ValueError('Indica una domanda alla volta: ? voltage R2 oppure ? current R2.')
    req = ir.requests[0]
    source_sha = _source_sha(source_sha or None)
    if isinstance(source_sha, Failure):
        return dict(outcome='failure', message=source_sha.messaggio)
    count = itertools.count(1)
    class Clock:
        def now(self):
            return datetime(2026, 9, 13, tzinfo=timezone.utc)
    result = run_proof_session_con_run(
        ir, req, clock=Clock(), entropy=lambda: next(count).to_bytes(10, 'big'),
        document_profile=DOCUMENT_PROFILE, source_sha=source_sha,
        detail='CircuitCheck: richiesta utente e lezione deterministica')
    if isinstance(result, Refusal):
        return dict(outcome='refusal', message=result.diagnosis, cause=result.cause)
    if isinstance(result, Failure):
        return dict(outcome='failure', message=result.messaggio)
    closure, run = result
    answer = run.final_execution.execution.resolved.value.amount
    unit = 'V' if req.quantity == 'voltage' else 'A'
    topology = branches(ir)
    original = schematic(ir, topology)
    target = ir.component(req.target)
    direction = f'{target.terminals[0]} → {target.terminals[1]}'
    question = f'{"Tensione" if req.quantity == "voltage" else "Corrente"} di {req.target}'
    steps = [_step('Leggiamo il circuito e la domanda',
                   f'Cerchiamo la {question.lower()}. Il riferimento è {direction}: '
                   'per la tensione sottraiamo il potenziale del secondo nodo da quello del primo; '
                   'per la corrente il verso positivo va dal primo al secondo. '
                   'Un risultato negativo indica il verso opposto, non un errore.', original)]
    available = ['auto', 'nodal']
    chosen = 'nodal'
    if topology is not None:
        p, q, bs = topology
        try:
            calculated = observed(bs, req.target, req.quantity)
        except ValueError:
            topology = None
        else:
            if calculated != answer:
                raise ValueError('La derivazione non coincide con il nucleo esatto: risultato non esposto.')
            available += ['millman', 'superposition']
            if any(b.resistance and b.imposed() is None and any(c.type == 'voltage_source_dc' for c,_ in b.parts) for b in bs):
                available += ['norton']
            load = next((i for i, b in enumerate(bs) if len(b.parts) == 1 and b.parts[0][0].id == req.target and target.type == 'resistor'), None)
            if load is not None and len(bs) > 1 and any(b.resistance and b.imposed() is None for i, b in enumerate(bs) if i != load):
                available += ['thevenin']
            divider = (len(bs) == 2
                       and sum(b.resistance == 0 and b.imposed() is None for b in bs) == 1
                       and all(all(c.type == 'resistor' for c, _ in b.parts)
                               for b in bs if b.resistance))
            chosen = method if method != 'auto' else ('divider' if divider else 'current_divider' if sum(b.imposed() is not None for b in bs) == 1 and all(b.emf() == 0 for b in bs) else 'millman')
            if method != 'auto' and method not in available:
                raise ValueError('Il metodo selezionato non è applicabile a questa topologia e a questa domanda.')
            if chosen != 'nodal':
                steps += _human_steps(ir, topology, req.target, req.quantity, chosen, load, original)
    if topology is None:
        from kirchhoff.pipeline.lesson_bridge import bridge_lesson
        bridge_path = bridge_lesson(ir)
        if bridge_path is not None:
            available.append('star_delta')
            if method in {'auto', 'star_delta'}:
                value, bridge_steps = bridge_path
                if value != answer:
                    raise ValueError('La trasformazione del ponte non coincide col nucleo esatto.')
                steps += bridge_steps
                chosen = 'star_delta'
    if chosen == 'nodal':
        if method not in {'auto', 'nodal'}:
            raise ValueError('Questa topologia richiede il percorso generale: seleziona Automatico o Nodi.')
        # Proiettiamo l'esecuzione reale: non scriviamo equazioni fittizie.
        view_steps = []
        for execution in run.transform_executions:
            view_steps.append(dict(action=execution.plan.actions[0].kind,
                                   equations=[str(r.equation) for r in execution.results],
                                   svg=schematic(execution.after, branches(execution.after))))
        for act in run.final_execution.execution.steps:
            view_steps.append(dict(action=act.kind,
                                   equations=[equazione_analitica(e) for e in act.equations],
                                   svg=schematic(run.final_ir, branches(run.final_ir))))
        for st in view_steps:
            explanation = {
                'choose_reference': 'Fissiamo il nodo 0 a potenziale zero. Le altre tensioni sono differenze rispetto a questo riferimento: la scelta non modifica il circuito.',
                'define_nodal_unknowns': 'Separiamo le tensioni già imposte dai generatori dalle tensioni ancora incognite. Solo queste ultime richiedono equazioni.',
                'write_kcl': 'In questo nodo la carica non si accumula: la somma algebrica delle correnti è zero. Per ogni resistore scriviamo la differenza dei potenziali divisa per la sua resistenza, usando lo stesso verso in tutta l’equazione.',
                'write_voltage_constraint': 'Il generatore ideale impone una differenza di potenziale fra i suoi morsetti. Aggiungiamo questo vincolo alle equazioni delle correnti.',
                'serie': 'Nel nodo intermedio non esistono diramazioni: i resistori hanno la stessa corrente. Sommiamo le resistenze; il collegamento con la grandezza originale è conservato dalla derivazione.',
                'parallelo': 'I resistori condividono entrambi i nodi, quindi hanno la stessa tensione. Sommiamo le conduttanze e prendiamo il reciproco per ottenere la resistenza equivalente.',
            }.get(st['action'], 'Seguiamo l’equazione della derivazione e conserviamo i riferimenti della domanda iniziale.')
            titles = {'choose_reference':'Scegliamo il riferimento', 'define_nodal_unknowns':'Quali tensioni dobbiamo trovare?', 'write_kcl':'Scriviamo il bilancio delle correnti', 'write_voltage_constraint':'La tensione imposta dal generatore', 'solve_system':'Risolviamo le equazioni', 'recover_observable':'Ritroviamo la grandezza richiesta', 'serie':'Sommiamo le resistenze in serie', 'parallelo':'Riduciamo le resistenze in parallelo'}
            steps.append(_step(titles.get(st['action'], st['action'].replace('_', ' ')), explanation,
                               st['svg'], st['equations']))
        chosen = 'nodal'
    steps.append(_step('Torniamo al circuito originale',
                 f'La risposta alla domanda iniziale è {number(answer)} {unit}, nel riferimento {direction}. '
                 'Ritrova il componente nello schema di partenza: gli equivalenti servono a calcolare, '
                 'ma la domanda riguarda sempre questo circuito. Il valore della derivazione è confrontato '
                 'esattamente con il risultato del nucleo verificato.',
                 schematic(ir, topology, focus=[req.target]), [f'{question} = {number(answer)} {unit}'], [req.target]))
    with localcontext() as ctx:
        ctx.prec = 8
        decimal = format(Decimal(answer.numerator)/Decimal(answer.denominator), 'g')
    return dict(schema='circuit-lesson.v1', outcome='solved', title=question,
                netlist=text, method=chosen, available=available, original=original,
                steps=steps, answer=dict(exact=number(answer), decimal=decimal, unit=unit, reference=direction),
                verification=dict(electrical_claim='VERIFIED', backend='CLOSED',
                                  lesson='exact-answer-crosscheck', product_verified=False),
                source_sha=source_sha, lesson_build=hashlib.sha256(b''.join((Path(__file__).parent/name).read_bytes() for name in ('lesson.py','lesson_svg.py','lesson_pdf.py','lesson_bridge.py'))).hexdigest(), fingerprint=hashlib.sha256(text.encode()).hexdigest())


def _human_steps(ir, topology, target, quantity, method, load, original):
    p, q, bs = topology
    u, currents = potential(bs)
    _verify_branch_state(ir, bs, u, currents)
    equations = [f'R ramo {i+1} = ' + ' + '.join(number(c.value.amount) for c, _ in b.parts if c.type == 'resistor') + f' = {number(b.resistance)} Ω'
                 for i, b in enumerate(bs) if sum(c.type == 'resistor' for c, _ in b.parts) > 1]
    result = []
    if method not in {'superposition', 'thevenin'}:
        irrelevant_series = [i for i,b in enumerate(bs) if b.imposed() is not None and len(b.parts)>1 and all(c.id != target for c,_ in b.parts)]
        if irrelevant_series:
            result.append(_step('Una corrente imposta rende superflui alcuni dettagli interni',
                'Il generatore ideale di corrente impone già la corrente del ramo. I componenti in serie cambiano '
                'le tensioni interne e la potenza del generatore, ma non la relazione esterna fra i morsetti. '
                'Qui la domanda non riguarda quei componenti: li nascondiamo nell’equivalente. Se chiedessi '
                'una delle loro grandezze, dovremmo mantenerli o tornare all’originale.',
                schematic(ir,topology,collapsed_current=irrelevant_series)))
        ideal_voltage = [b for b in bs if b.resistance==0 and b.imposed() is None]
        if ideal_voltage and not any(c.id==target for b in ideal_voltage for c,_ in b.parts):
            ignored=[c.id for b in bs if all(c.type=='resistor' and c.id != target for c,_ in b.parts) for c,_ in b.parts]
            if ignored:
                result.append(_step('Una tensione imposta rende irrilevante il ramo in parallelo',
                    'Il generatore ideale fissa la tensione fra questi nodi anche senza il ramo resistivo evidenziato dalla rimozione. '
                    'La sua corrente cambierebbe: per questo possiamo fare questa semplificazione soltanto perché '
                    'la domanda non riguarda né quel ramo né il generatore. Conserviamo sempre il circuito originale per recuperare tali grandezze.',
                    schematic(ir,topology,omit=ignored)))
    if equations:
        result.append(_step('Riconosciamo le resistenze in serie',
            'All’interno di ciascun ramo non ci sono diramazioni. La corrente è comune: possiamo sommare le resistenze. '
            'Conserviamo i nomi originali per ricostruire poi tensioni e correnti su ciascun componente.',
            schematic(ir, topology, reduced=True), equations))
    g = sum((1/b.resistance for b in bs if b.resistance and b.imposed() is None), F(0))
    if method == 'superposition':
        sources = [c for c in ir.components if c.type != 'resistor']
        contributions = []
        for source in sources:
            value = observed(bs, target, quantity, source.id)
            contributions.append(value)
            us, _ = potential(bs, source.id)
            _verify_superposition_contribution(ir, source.id, target, quantity, p, q, value, us)
            fixed = any(b.resistance == 0 and b.imposed(source.id) is None for b in bs)
            numerator = sum((b.emf(source.id)/b.resistance for b in bs if b.resistance and b.imposed(source.id) is None), F(0)) - sum((b.imposed(source.id) or F(0) for b in bs), F(0))
            formula = f'V = numeratore / G = ({number(numerator)}) / ({number(g)}) = {number(us)} V' if not fixed else f'La sorgente ideale impone V = {number(us)} V'
            result.append(_step(f'Lasciamo attivo soltanto {source.id}',
                'Spegniamo gli altri generatori indipendenti: tensione nulla significa cortocircuito; '
                'corrente nulla significa circuito aperto. I resistori restano. Risolviamo questo sottoproblema '
                'con gli stessi riferimenti dell’originale. Qui tutti i componenti sono lineari e indipendenti.',
                schematic(ir, topology, active=source.id, focus=[source.id]),
                [formula, f'V({p}) − V({q}) = {number(us)} V', f'Contributo di {source.id} a {target} = {number(value)} {"V" if quantity == "voltage" else "A"}']))
        from kirchhoff.domain.independent_dc import solve_dc_tableau
        if sum(contributions, F(0)) != solve_dc_tableau(ir)[target][quantity]:
            raise ValueError('La somma dei contributi in sovrapposizione non coincide con il tableau indipendente: lezione non esposta.')
        result.append(_step('Sommiamo i contributi con il loro segno',
            'Ricongiungiamo i sottoproblemi. Sommiamo tensioni o correnti nella medesima orientazione. '
            'Non si applica questa somma alle potenze, che dipendono quadraticamente da tensioni e correnti.', original,
            [' + '.join(f'({number(x)})' for x in contributions) + f' = {number(sum(contributions, F(0)))}']))
        return result
    if method == 'thevenin':
        assert load is not None
        remaining = tuple(b for i, b in enumerate(bs) if i != load)
        vth, _ = potential(remaining)
        ideal = any(b.resistance == 0 and b.imposed() is None for b in remaining)
        gr = sum((1/b.resistance for b in remaining if b.resistance and b.imposed() is None), F(0))
        rth = F(0) if ideal else 1/gr
        _verify_thevenin_port(ir, target, p, q, vth, rth)
        emf_sum = sum((b.emf()/b.resistance for b in remaining if b.resistance and b.imposed() is None), F(0))
        imposed_sum = sum((b.imposed() or F(0) for b in remaining), F(0))
        result.append(_step('Stacchiamo il carico: troviamo la tensione a vuoto',
            f'{target} è il carico. Staccandolo, nessuna corrente attraversa i suoi morsetti aperti. '
            'I generatori del resto della rete rimangono accesi: la tensione fra questi morsetti è Vth. '
            'Usiamo il vincolo della sorgente ideale se presente, altrimenti Millman sui rami rimasti.',
            schematic(ir, topology, omit=[target]),
            [f'Vth = V({p}) − V({q}) = {number(vth)} V'] if ideal else
            [f'G a vuoto = Σ(1/R) = {number(gr)} S',
             f'Vth = (Σ(E/R) − ΣI) / G = ({number(emf_sum)} − ({number(imposed_sum)})) / ({number(gr)}) = {number(vth)} V']))
        result.append(_step('Spegniamo le sorgenti: troviamo la resistenza vista',
            'Il carico resta staccato. Ora azzeriamo soltanto i generatori indipendenti: '
            'ogni generatore di tensione diventa un cortocircuito e ogni generatore di corrente un ramo aperto. '
            'Guardiamo dentro la rete dai due morsetti del carico. ' +
            ('Il cortocircuito fra i morsetti impone Rth = 0.' if ideal else
             'I rami rimasti conducenti sono in parallelo: sommiamo le loro conduttanze e invertiamo.'),
            schematic(ir, topology, omit=[target], active='__all_off__'),
            [f'Rth = {number(rth)} Ω'] if ideal else
            ['G vista = ' + ' + '.join(f'1/({number(b.resistance)})' for b in remaining if b.resistance and b.imposed() is None) + f' = {number(gr)} S',
             f'Rth = 1 / G vista = 1 / ({number(gr)}) = {number(rth)} Ω']))
        iload = vth/(rth+bs[load].resistance)
        result.append(_step('Ricolleghiamo il carico all’equivalente Thévenin',
            'Riaccendiamo la rete attraverso il suo equivalente: Vth in serie a Rth. '
            f'Ricolleghiamo {target} ai medesimi morsetti. Le resistenze sono ora in serie: '
            'troviamo la corrente con la legge di Ohm e la tensione del carico con il partitore. '
            f'I valori qui sotto seguono il verso {p} → {q}; sull’originale recuperiamo il riferimento della domanda.',
            schematic(ir, topology, thevenin=(load, vth, rth)),
            [f'I carico = Vth / (Rth + R carico) = ({number(vth)}) / ({number(rth)} + {number(bs[load].resistance)}) = {number(iload)} A',
             f'V carico = I carico × R carico = ({number(iload)}) × ({number(bs[load].resistance)}) = {number(iload*bs[load].resistance)} V']))
        return result
    if method == 'norton':
        converted = []
        for i, b in enumerate(bs):
            if b.resistance and b.imposed() is None and any(c.type == 'voltage_source_dc' for c, _ in b.parts):
                converted.append(i)
                result.append(_step(f'Trasformiamo il ramo {i+1} in Norton',
                    'Un generatore di tensione con resistenza in serie equivale, ai morsetti del ramo, '
                    'a un generatore di corrente in parallelo alla stessa resistenza. La freccia di Norton va '
                    f'da {q} a {p} quando E/R è positivo. L’equivalenza riguarda il comportamento esterno: '
                    'le grandezze interne verranno recuperate sull’originale.',
                    schematic(ir, topology, norton=converted),
                    [f'I_N{i+1} = E / R = ({number(b.emf())}) / ({number(b.resistance)}) = {number(b.emf()/b.resistance)} A']))
    if method == 'current_divider':
        total = -sum((b.imposed() or F(0) for b in bs), F(0))
        result.append(_step('Il partitore di corrente',
            'I rami resistivi condividono la tensione. La corrente del generatore si divide in proporzione alle conduttanze: un ramo con resistenza minore conduce più corrente. Prima calcoliamo la conduttanza totale, poi moltiplichiamo la corrente entrante per la frazione di conduttanza del ramo cercato.',
            original, [f'I entrante = {number(total)} A', f'G totale = {number(g)} S'] +
            [f'I ramo {i+1} = I entrante × (1/R ramo) / G totale = {number(total/(b.resistance*g))} A' for i,b in enumerate(bs) if b.imposed() is None]))
    elif method == 'divider':
        result.append(_step('Usiamo il partitore, senza un sistema di equazioni',
            'La sorgente impone la tensione ai capi del ramo resistivo. La stessa corrente attraversa '
            'tutti i suoi resistori: I = V / R totale. Ogni caduta vale I × R, cioè V × R / R totale.',
            schematic(ir, topology, reduced=True), [f'V({p}) − V({q}) = {number(u)} V'] +
            [f'I ramo {i+1} = ({number(u)}) / ({number(b.resistance)}) = {number(currents[i])} A' for i,b in enumerate(bs) if b.resistance] +
            [f'V({c.id}) = ({number(currents[i])}) × ({number(c.value.amount)}) = {number(currents[i]*c.value.amount)} V (verso del ramo)' for i,b in enumerate(bs) for c,_ in b.parts if c.type == 'resistor']))
    else:
        fixed = any(b.resistance == 0 and b.imposed() is None for b in bs)
        explanation = ('Una sorgente ideale impone direttamente la tensione fra i due morsetti. Non dividiamo per una resistenza nulla: usiamo il vincolo del generatore.' if fixed else
            'Tutti i rami collegano gli stessi due morsetti. Per ciascun ramo resistivo la corrente uscente è (V − E)/R. '
            'Sommandole a zero e raccogliendo V otteniamo Millman. Un ramo senza sorgente ha E = 0; '
            'una sorgente di corrente orientata dal morsetto alto a quello basso entra con segno meno nel numeratore.')
        numerator = ' + '.join(f'({number(b.emf())})/({number(b.resistance)})' for b in bs if b.resistance and b.imposed() is None)
        injections = sum((b.imposed() or F(0) for b in bs), F(0))
        branch_equations = []
        for i, b in enumerate(bs):
            if b.resistance and b.imposed() is None:
                branch_current = (u-b.emf())/b.resistance
                if branch_current != currents[i]:
                    raise ValueError('La corrente del ramo non coincide con la relazione tensione-resistenza.')
                branch_equations.append(
                    f'I ramo {i+1} = ({number(u)} - ({number(b.emf())})) / ({number(b.resistance)}) = {number(branch_current)} A')
        expected_equations = tuple(
            ([f'G = Σ(1/R) = {number(g)} S', f'V = ({numerator} − ({number(injections)})) / ({number(g)}) = {number(u)} V']
             if not fixed else [f'V = {number(u)} V']) + branch_equations)
        expected_svg = schematic(ir, topology, norton=converted if method == 'norton' else [])
        step = _step('Tensione comune: il teorema di Millman' if not fixed else 'La tensione è già imposta',
                     explanation, expected_svg, list(expected_equations))
        if tuple(step['equations']) != expected_equations or step['svg'] != expected_svg:
            raise ValueError('Il passaggio intermedio non coincide con il circuito e le equazioni calcolate.')
        result.append(step)
    for i, b in enumerate(bs):
        if any(c.id == target for c, _ in b.parts):
            focus = [c.id for c, _ in b.parts]
            result.append(_step('Recuperiamo la grandezza nel ramo originale',
                f'Nel ramo che contiene {target}, la corrente di riferimento {p} → {q} vale {number(currents[i])} A. '
                'Per la tensione di un resistore usiamo V = R × I; se il componente ha i morsetti nell’ordine opposto '
                'cambiamo il segno. Una sorgente di corrente impone I, mentre una sorgente di tensione impone la propria caduta.',
                schematic(ir, topology, focus=focus),
                [f'{target}: {number(observed(bs, target, quantity))} {"V" if quantity == "voltage" else "A"}'], focus))
    return result
