"""Stella→triangolo per il ponte resistivo, con osservazione esterna preservata.

Derivazione didattica, non apertura del catalogo dei certificati. Il chiamante
confronta il risultato con la chiusura canonica sul circuito originale.
"""
from dataclasses import replace
from fractions import Fraction as F
from kirchhoff.domain.ir import Component
from kirchhoff.pipeline.lesson_svg import schematic


def bridge_lesson(ir):
    from kirchhoff.pipeline.lesson import branches, potential, _step
    sources=[c for c in ir.components if c.type=='voltage_source_dc']
    if len(ir.nodes)!=4 or len(ir.components)!=6 or len(sources)!=1:
        return None
    source=sources[0];p,q=source.terminals
    middle=sorted(n for n in ir.nodes if n not in (p,q))
    req=ir.requests[0];target=ir.component(req.target)
    if target.type not in {'resistor','voltage_source_dc'}:
        return None
    pairs=[(p,middle[0]),(middle[0],q),(p,middle[1]),(middle[1],q),tuple(middle)]
    if any(sum(c.type=='resistor' and set(c.terminals)==set(pair) for c in ir.components)!=1 for pair in pairs):
        return None
    center=next((n for n in middle if n not in target.terminals and n!='0'),None)
    if center is None:
        return None  # Non cancellare la grandezza interna che lo studente cerca.
    star=[c for c in ir.components if center in c.terminals]
    legs={next(n for n in c.terminals if n!=center):c for c in star}
    external=sorted(legs)
    product_sum=sum((legs[external[i]].value.amount*legs[external[j]].value.amount for i,j in ((0,1),(0,2),(1,2))),F(0))
    remaining=[c for c in ir.components if c not in star]
    equations=[];new=[]
    def fresh(prefix):
        existing={c.id for c in ir.components}|{c.id for c in new}
        name=prefix
        while name in existing:name+='x'
        return name
    for i,j in ((0,1),(0,2),(1,2)):
        a,b=external[i],external[j];opposite=next(n for n in external if n not in (a,b))
        val=product_sum/legs[opposite].value.amount
        c=Component.of(fresh(f'Rdelta{i}{j}'),'resistor',(a,b),val,'Rdelta')
        new.append(c)
        equations.append(f'{c.id} ({a}–{b}) = (Ra×Rb + Rb×Rc + Rc×Ra) / R opposta = {val} Ω')
    transformed=replace(ir,nodes=tuple(n for n in ir.nodes if n!=center),components=tuple(remaining+new))
    result=[_step('Trasformiamo la stella in un triangolo',
        f'Nel nodo {center} si incontrano soltanto tre resistori: '+', '.join(c.id for c in star)+'. '
        f'La domanda su {target.id} riguarda l’esterno di questa stella. Possiamo sostituirla con un triangolo che conserva il comportamento ai tre morsetti. '
        'Ogni lato del triangolo è la somma dei tre prodotti a coppie divisa per la resistenza della stella opposta a quel lato. '
        'Il nodo centrale scompare; gli altri morsetti restano gli stessi.',
        schematic(transformed),equations,[c.id for c in star])]
    groups={}
    for c in transformed.components:
        if c.type=='resistor':groups.setdefault(tuple(sorted(c.terminals)),[]).append(c)
    merged=[source];eq=[]
    for pair, group in groups.items():
        if len(group)==1:merged+=group;continue
        value=1/sum((1/c.value.amount for c in group),F(0))
        name=fresh('Req'+str(len(merged)))
        merged.append(Component.of(name,'resistor',pair,value,name))
        eq.append(f'{name} = '+' || '.join(c.id for c in group)+f' = {value} Ω')
    # I target delle viste intermedie sono osservazioni originali: la nuova IR
    # non dichiara richieste su componenti consumati. La relazione si ricostruisce.
    reduced=replace(transformed,components=tuple(merged),requests=())
    topology=branches(reduced)
    if topology is None:return None
    result.append(_step('Riconosciamo i paralleli comparsi',
        'Ogni coppia evidenziata dalle formule collega gli stessi due nodi. Le tensioni sono uguali: sommiamo le conduttanze. '
        f'Se {target.id} entra in un parallelo, la sua tensione è quella dell’equivalente; la sua corrente andrà recuperata con la resistenza originale.',
        schematic(reduced,topology),eq))
    top,bottom,bs=topology
    u, currents=potential(bs)
    voltages={top:u,bottom:F(0)}
    for branch,current in zip(bs,currents):
        v=u;node=top
        for c,sign in branch.parts:
            v-=current*c.value.amount if c.type=='resistor' else sign*c.value.amount
            node=c.terminals[1] if sign==1 else c.terminals[0]
            voltages[node]=v
    voltage=voltages[target.terminals[0]]-voltages[target.terminals[1]]
    if req.quantity=='voltage':answer=voltage
    elif target.type=='resistor':answer=voltage/target.value.amount
    else:
        i=next(i for i,b in enumerate(bs) if any(c.id==target.id for c,_ in b.parts))
        sign=next(sign for c,sign in bs[i].parts if c.id==target.id)
        answer=sign*currents[i]
    result.append(_step('Partitore e ritorno al resistore originale',
        'Il ponte è diventato una rete di rami semplici. La sorgente impone la tensione totale del ramo in serie; '
        'la ripartiamo sulle resistenze equivalenti. Poi torniamo ai morsetti del componente originale: '
        'la sua tensione è conservata, la sua corrente si calcola usando il suo valore originale.',
        schematic(ir),[f'V({target.terminals[0]}) − V({target.terminals[1]}) = {voltage} V',
                       f'{target.id}: {answer} {"V" if req.quantity=="voltage" else "A"}']))
    return answer,result
