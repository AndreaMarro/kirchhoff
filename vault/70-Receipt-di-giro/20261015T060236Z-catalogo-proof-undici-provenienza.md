---
storia: catalogo-proof-undici-provenienza
istante: 20261015T060236Z
sha: 4a93e24c2cfea75c8d1038e68a0c4126ec49a27f
ramo: codex/pr17-notebook-20261015
esito: verde-locale-non-promosso
tipo: receipt-di-giro
---

# Giro 20261015T060236Z — catalogo proof a undici esempi

## Requisito, origine e perimetro

Recupero selettivo del delta catalogo0adc22503e235e55e7323d00c51e3acd62614485 rispetto al parentbfa5e25c387ca8c36cebf0a64c4f708e3cbdfa6c soprad11d001e9bdffb96623fe4d170b7e77838077054. Tredici sorgenti/test più dodici JSON (indice+undici viste); gli originali restano nelle ref/bundle. bfa/0adc non sono ancora antenati: recupero parziale tracciato, non assorbimento o chiusura della PR16. Host, script operativi, guida e playbook del parent sono la prossima tranche.

Nove chiusure e due rifiuti nel solo Proof Workbench DC: non undici famiglie o ampliamento implicito del catalogo StudentApp lessons. Preservati i quattro esempi storici. Aggiunti partitore-tensione5volt, due-rami-parallelo12volt, serie-parallelo-misto3/55ampere, scala-tre-riduzioni2/3ampere, ramo-derivato3/50ampere, generatore-flottante5/2volt e rifiuto-domanda. Nessuna nuova trasformazione/solver/capability/Verified/soglia. Guardie forti15/17 e ingresso StudentApp default preservati; i test del banco mantengono view=proof. Il selettore porta la scelta nella porzione visibile della barra orizzontale.

## Produttore ricostruibile e artefatti

Csrc reale `4a93e24c2cfea75c8d1038e68a0c4126ec49a27f`, tree`f0aeb7477ae292328963824b6bac021fb8845a10`, parentD11. Commit normale preparatorio13file, non promosso/pubblicato come tip pronto: vecchi artifact4. Conservati tre FAIL Python e tre FAIL web attesi per drift/corpi mancanti (7/74PASS rispettivi); non sono regressioni matematiche né un gate verde. Il primo tentativo Python collection2ERROR era setup e resta separato.

Da Csrc pulito prima/dopo, vero CLI `scripts/generate_workbench.py --out DIR_PRIVATA_NUOVA --source-sha 4a93e24c2cfea75c8d1038e68a0c4126ec49a27f` con Python 3.12.12 e clock/entropia fissi già nel generatore. Trasferiti soltanto i12file verificati; indice/file senza orfani, nove closed/due refusal, tutti gli undici provenance.source_sha uguali aCsrc e product_verifiedFalse. La sorgente dichiarata contiene davvero il generatore11; i vecchi JSON originali dichiaravano bfa con generatore4. Nessun fakeSHA, amend, plumbing orfano o nuova promessa H3.

Closure controllata:112file tracked, tutti src/kirchhoff (108.py fisici e settracked identico), generatore con netlist/layout letterali, pyproject.toml, uv.lock, hatch_build.py. Mode/blobOID/SHA256 confrontati conCsrc e byte filesystem, import fisico esatto; nessun produttore Python ignorato/untracked. Dopo i gate tutti i 112 hash invariati. Il successivo commit artifact deve mantenere questa closure byte-identica aCsrc. Non basta il drift che normalizza source_sha.

## Verifiche effettive

- Full Python corretto2526PASS/0FAIL/0ERROR/0SKIP,227.97s; coverage97.3837413200533%, dominio100%. Setcoverage esattamente108file fisici attesi, inclusi42domain: nessun verde vacuo per prefisso assente. Soglia globale95% e dominio100% invariati.
- Web161PASS/11suite; typecheck e build normale+MCP PASS. Browser default114PASS/50SKIP, nessuno skip aggiunto; non eseguiti qui tutti i liveAPI. Le E2E sono trasformate/eseguite daPlaywright, fuori dal projecttsc.
- Probe browser reale aggiuntivo4PASS20s desktop1440x900/mobile390x844: ogni volta indice11/undici viste, noveesatti+unità e duerifiuti senza risposta;20fotogrammi prima/dopo disponibili perviewport,40totali; pageerror0. Verificati source_sha=Csrc effettivamente serviti. DefaultStudentApp distinto resta sano.
- Altri due callback dello stesso run: hash da fondo a centro a inizio senza clickautoPlaywright, sceltaalmeno95%nelviewport, scorrimentosolodelcontenitore, nessuntraboccoXpagina e windowY0. I quattro test totali comprendono duecallback ×dueviewport, non quattrotest piùquesti.
- QuattroPNG reali ispezionati dalwriter: generatoreflottante/rifiutodomanda desktop/mobile. Sulmobile dettaglio risposta parzialmente sotto piega, valore compatto visibile nella barra; non ispezione manuale di tutti gli undici esempi. Nessun pilot/hardware o designglobale certificato.
- HTML/assetJS/CSS/indice del preview4175 confrontati byte-per-byte col dist appena costruito, cwdprocessoverificato. Prima concatenazioneURL del verifier privato malformata4175. era setup senza browseravviato, corretta conURLjoin; non fallimento prodotto.
- Quattrocheck preledger BMAD/con-loop, confini, indice53note e diffexit0; checkdominio fresco exit0. Dopo receipt/ledger/indice occorre riverifica e pin finale.

## Ambiente, esiti negativi conservati

Prima suite completa2520PASS/6FAIL,exit1: treCLI e treMCPstdio in processifigli con ModuleNotFoundkirchhoff. Il .pth editable aveva flag64 prima e32832 (include UF_HIDDEN) dopo il run; contenuto SHA256ab4b5a75a63adea9126e5ee262875c82a7d126f8eb6bb937abbca1a02d9aa172 invariato. Lo stdlibsite.py salta i .pthhidden; causa della ricorrenza sconosciuta, nessun processo colpevole identificato. Non sono sei bug matematici dimostrati e il run non è PASS.

Riparazione solo dell'installazione editable nella venv locale: nuovo symlink site-packages/kirchhoff verso lo stesso src/kirchhoff risolto, .pth originale tenuto identico/nascosto; nessun watcher/background/PYTHONPATH/site.py/deps/lock/test/gate/sorgente/settingsglobale cambiato. Freshprocess risolve gli stessi108source, runtimeSnapshotroot esatto e source_sha=Csrc. Sei casi prima falliti6PASS3.91s, poi il full fresco2526PASS sopra. Assessmentambiente separato SHA2568efb5a52562874c2b5a0aeb3d967533b34b17a91735ac1e6912d6d0bee9a0ad5: repairammissibile, nonfixportabile della causa e nonnecessariamente permanente dopo reinstallazione. Canonicalizzazione coverage verificata e set fresco completo poi misurato.

## Review, destinazioni e limiti

Assessment delimitazione/provenienza8064b6 e review preliminare fonte/closuree6d265d; reviewer Codex avversario in contesto separato, modello specifico nonesposto. Verifiche proprie dichiarate:112closureGit/fs,13source,12JSON, tutti11compatibili con guardiaunita15/17; sei formule elementari indipendenti concordi. Gate finali e quattro PNG letti dal reviewer: APPROVE tecnico precommit sui tredici sorgenti e dodici artifact, report SHA256 35070c780b9137d004bb499a35a6ee0cfb128b6b1fae7974e68f7d1d6826c99a; pin del futuro commit/receipt/indice ancora PENDING; nonquorum non-Codex, GitHubapproval o main.

Tuttiottofinding parent16 restano destinati alla prossima tranche, tranne la provenienzacatalogo qui corretta: routehost/pubblico; smoke4/tuttiicorpi; verifiernuovibody; verifierassetHTMLremoto; CTAstessopassocatturatosoloiniziale; playbookautodeploy/deleteobsoleto; delimitazionebrief/misurestoriche. Non usare i vecchi script come attestazione completa. H5/K4, designautorevole,21famiglie, StudentTrace/pilot e altri requisiti restano aperti. D11 ha CIremota4PASS distinta; non è CI di questo recupero. Nessunpushdiquestatranchesenza finalreview/gate, nessun main/deploy/release/PRclosure.

## Hash artefatti generati (SHA256)

- `66486040bf7d70dbe7ec4455fe0ee44e4e4b17958321b1f2485e2e57d695383c` `due-rami-parallelo.json`
- `022d2e036c1dd68babf2183a12b6f5fedc6414e73ea3e6ec7141b3b428cd1048` `generatore-flottante.json`
- `e733e726fe2e497fbeffb057b9de26861a0a8ef5f661b1fb545a4d8a2199b655` `index.json`
- `2517830e35ddfff985a3f5778f726e4765ca7d11b7d8c048f94f8d612bca58a5` `partitore-d1.json`
- `e4a591ef8e15f40bb96230467d2aa1dd18c47743b32f663a347351eda957138e` `partitore-tensione.json`
- `db66bf7ca562b7da2f2ac21bed9d2f70d01da39e030bcab70af69ce926816b7a` `ponte-nodale.json`
- `36700a57fb21d0f7825cdec2dcced1a9aed311a6bf26d5f805095ae8f795b40c` `ramo-derivato.json`
- `db1d9ac43311152001247584538848165ff155c5230c90e38f5ef949fd946e12` `rifiuto-domanda.json`
- `303aeea9ed856c5391dea1a593952d479ddd6fe64604524c8a8d58d9d8c5d769` `rifiuto-reattivo.json`
- `42b558b6a62834e5b8c0bebd026d5b62e4ac0c62182f3dc6a7f41013563323cf` `scala-due-riduzioni.json`
- `08bf1e5747f28a16f8b89c045074642e6822be67633ae3062b95016239d7a560` `scala-tre-riduzioni.json`
- `cd78d3e836d59210b38bb1fac4a6e8aa375e4c232a7b71e928b889ddcba7bdf4` `serie-parallelo-misto.json`

## Archi

- [[00-INDICE]]
