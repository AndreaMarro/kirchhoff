# P1-M0 technology register

Fresh research pass: 2026-09-02.  “License confidence” is **high** only when
the upstream license text or a primary project page was checked.  `NO CODE
COPYING` applies to every entry with unknown or restrictive licensing.  These
recommendations concern a research lab, never Kirchhoff runtime authority.

| Technology | Primary source | Role | License / confidence | Activity and maintenance risk | Runtime? / lab? | Recommendation |
|---|---|---|---|---|---|---|
| Hypothesis 6.167.0 | [upstream](https://github.com/HypothesisWorks/hypothesis) | property and stateful testing | MPL-2.0 / high | actively released; rapid API cadence / low | no / yes | ADOPT_NOW |
| Cosmic Ray 8.7.0 | [official docs](https://cosmic-ray.readthedocs.io/en/latest/) | primary targeted Python mutation runner | MIT / high | current release; persistent SQLite sessions / medium run-time cost | no / yes | ADOPT_NOW |
| mutmut 3.4.0 | [upstream](https://github.com/boxed/mutmut) | historical secondary mutation diagnostic | BSD-3-Clause / high | runner segfaults observed in this checkpoint / high | no / optional | HOLD / SECONDARY DIAGNOSTIC |
| CrossHair | [docs](https://crosshair.readthedocs.io/en/stable/get_started.html) | contract counterexample spike | Apache-2.0 / high | bounded Python-contract scope / medium | no / spike | HOLD |
| Atheris | [upstream](https://github.com/google/atheris) | coverage-guided parser fuzzing | Apache-2.0 / high | Google-maintained, CPython-version-sensitive / medium | no / future lab | HOLD |
| Lcapy 1.26 | [docs](https://lcapy.readthedocs.io/en/stable/) | symbolic DC differential oracle | GPL-3.0 / high | mature symbolic package; import warnings observed / medium | no / yes | ADOPT_NOW |
| ngspice 45.2 used | [manual](https://ngspice.sourceforge.io/docs/ngspice-manual.pdf) | independent batch numeric DC oracle | modified BSD, component exceptions / high | mature external executable / low | no / yes | ADOPT_NOW |
| Xyce 7.10 | [releases](https://github.com/Xyce/Xyce/releases) | larger-signal simulator alternative | GPL-3.0 / high | actively released but heavyweight build / high | no / spike only | HOLD |
| PySpice | [upstream](https://github.com/PySpice-org/PySpice) | Python wrapper around ngspice | GPL-3.0 / high | wrapper adds an authority-looking layer / medium | no / no | REJECT |
| Qucs-S | [releases](https://github.com/ra3xdh/qucs_s/releases) | GUI simulator study | GPL-2.0 / high | active but GUI-centred / medium | no / no | REJECT |
| SKiDL 2.3.0 | [PyPI](https://pypi.org/project/skidl/) | design/netlist authoring | MIT / high | active, KiCad-facing / low | no / future import study | HOLD |
| ahkab | [upstream](https://github.com/ahkab/ahkab) | Python SPICE-like oracle | GPL, exact version 0.18 / high | latest release 2015 / high | no / no | REJECT |
| NetworkX 3.6.1 | [license](https://github.com/networkx/networkx/blob/main/LICENSE.txt) | topology measurements | BSD-3-Clause / high | mature and active / low | no / yes | ADOPT_NOW |
| imacat/spqrtree | [upstream](https://github.com/imacat/spqrtree) | SPQR decomposition spike | Apache-2.0 / high | alpha/young API / high | no / spike only | TRIAL |
| Centaur toolkit | [upstream](https://github.com/centaur-toolkit/centaur) | query-aware rewrite architecture study | no license found / high | prototype / high | no / reading only | HOLD — NO CODE COPYING |
| egglog / egglog-python | [upstream](https://github.com/egraphs-good/egglog) | e-graph experiment | Apache-2.0 / high | experimental modelling burden / high | no / no | HOLD |
| SymPy manualintegrate | [docs](https://docs.sympy.org/latest/modules/integrals/integrals.html) | rule-tree architecture study | BSD-3-Clause / high | mature, but no core dependency justified / low | no / conceptual only | HOLD |
| Schemdraw 0.23 | [contributing guide](https://schemdraw.readthedocs.io/en/stable/contributing.html) | reference SVG renderer | MIT / high | focused active library / low | no / yes | ADOPT_NOW |
| netlistsvg | [upstream](https://github.com/nturley/netlistsvg) | ELK-backed SVG layout reference | MIT / high | 1.0.2, old publish cadence / medium | no / later lab | HOLD |
| ELK / elkjs | [project](https://projects.eclipse.org/projects/modeling.elk) | automatic graph layout | EPL-2.0 with GPL secondary / high | 0.12 active / medium integration cost | no / lab only | TRIAL |
| Circuitikz | [upstream](https://github.com/circuitikz/circuitikz) | TeX reference rendering | LPPL / high | mature, offline toolchain / medium | no / later lab | HOLD |
| Dynamica | [upstream](https://github.com/M4rulli/Dynamica) | editor/analysis UX study | Apache-2.0 / high | early, small project / high | no / conceptual only | HOLD |
| repath | [upstream](https://github.com/repath-studio/repath-studio) | vector-editor study | AGPL-3.0 / high | specialised tool, strong copyleft / high | no / no | REJECT |
| Excalidraw | [upstream](https://github.com/excalidraw/excalidraw) | whiteboard UX candidate | MIT / high | active / medium integration cost | no / conceptual only | TRIAL |
| tldraw | [upstream](https://github.com/tldraw/tldraw) | whiteboard UX candidate | license-key/production terms / high | active but commercial integration constraint / high | no / no | HOLD |
| AITEE | [dataset](https://github.com/CKnievel/aitee-dataset) | circuit-image perception evaluation | Apache-2.0 / high | 831 labelled images / low | no / future evaluation | HOLD |
| CircuitReason-1K | [paper](https://arxiv.org/abs/2608.09374) | multimodal circuit reasoning methodology | code/data license not verified / low | very recent / high | no / reading only | HOLD — NO CODE COPYING |
| CircuitPile / CircuitHub | public project references | circuit data | commercial-training terms not verified / low | provenance unresolved / high | no / no | REJECT pending license |
| Razavi-bench | [upstream](https://github.com/Arcadia-1/razavi-bench) | analog reasoning benchmark | code Apache-2.0; content research/non-commercial / high | active research asset / medium | no / local methodology only | HOLD |
| CircuitsU | [service](https://www.circuitsu.com/Home) | competitive baseline | site content CC BY 4.0; product terms not assessed / medium | public service / medium | no / research only | ADOPT_NOW (audit) |

The high-value retained stack is therefore Hypothesis, Cosmic Ray, NetworkX,
Lcapy, ngspice and Schemdraw, all confined to development or `lab/`. Mutmut is
retained only as historical/secondary evidence. GPL and
unknown-license packages are not copied, linked into production, or allowed to
decide a Kirchhoff result.
