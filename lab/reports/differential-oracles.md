# Differential oracles — P1-M0

Run locale del 2026-09-02, Python 3.12, Lcapy 1.26 e ngspice 45.2. Il corpus
pubblico `generated_cases(200)` e' limitato a DC, resistori e sorgenti
indipendenti. Non e' holdout e non produce Claim.

| Path | Cases | Result | Mismatches | Authority |
|---|---:|---:|---:|---|
| Kirchhoff MNA | 200 | exact `Fraction` | 0 | product internal oracle |
| Kirchhoff independent tableau | 200 | exact equality with MNA | 0 | product independent check |
| Lcapy 1.26 | 200 | 200 exact rational matches | 0 | challenge only |
| ngspice 45.2 | 200 | 200 numeric matches | 0 | challenge only |

The original 200 are retained as a **numerical-template** corpus: they repeat
four small structural families and remain valid only for that stated purpose.
A second, separately reported topology-diverse subset adapts the existing
recursive series/parallel generator, adds the source-fed didactic tail required
by the current DC slice, and selects fingerprints that ignore values.

| Path | Topology-diverse cases | Result | Mismatches | Authority |
|---|---:|---|---:|---|
| Kirchhoff MNA / independent tableau | 100 | exact equality | 0 | product internal checks |
| Lcapy 1.26 | 100 | exact rational matches | 0 | challenge only |
| ngspice 45.2 | 100 | numeric matches under the stated tolerance | 0 | challenge only |

ngspice uses only the laboratory tolerance
`abs(a-b) <= 1e-10 + 1e-8 * max(abs(a), abs(b))`; it never converts a core
value or changes exact comparison.  The 15 named mapping fixtures cover source
polarity/current orientation, passive sign, both ground placements, floating
source/simple supernode, zero source, non-integer fractions, extreme ratio,
parallel path and multiple sources.

Two disagreements during adapter bring-up were triaged and fixed as adapter
conventions: Lcapy orients an independent current source opposite to the
Kirchhoff p→q convention, and ngspice 45.2 rejects `v(a,0)` in `wrdata`.
The adapter reverses only Lcapy current-source netlist terminals and uses a
ground-aware ngspice vector. They are not Kirchhoff solver defects. No
unresolved differential disagreement remains in either the original 200-case
numerical-template subset or the separate 100-case topology-diverse subset.

Sources: [Lcapy documentation](https://lcapy.readthedocs.io/en/stable/) and
[ngspice manual](https://ngspice.sourceforge.io/docs/ngspice-manual.pdf).
