# Ispezionare la provenienza dichiarata

Nel banco proof, «Perché fidarsi» espone i tre campi già presenti in
`ProvenanceView`: produttore, revisione sorgente completa e contesto.
La revisione non viene più abbreviata a dodici caratteri: due valori
con quel prefisso comune restano distinguibili.

È una proiezione dei valori ricevuti. Il banco non sostituisce la revisione
con quella dell'applicazione corrente, non costruisce un collegamento a un
repository e non ricalcola la provenienza. Produttore e contesto sono testo,
anche quando contengono caratteri HTML o sequenze che assomigliano a URL.
Gli identificatori lunghi possono andare a capo usando i token esistenti.

## Confine di fiducia

`SessionProvenance` dichiara esplicitamente che `source_sha` è fornito dal
produttore e che il modello non ne verifica la corrispondenza al sorgente
eseguito. La sezione lo chiama «Provenienza dichiarata», senza spunta di
verifica e con il limite di autenticità visibile. Le spunte dei distinti
stati Claim elettrico e chiusura backend mantengono il significato precedente.

Il parser di presentazione esistente accetta stringhe senza imporre qui
un nuovo formato SHA. Questa correzione non cambia quel contratto: conserva
i valori non vuoti e mostra «Non dichiarato/a» per i soli campi vuoti o
composti di spazi. Un oggetto `provenance: null` espone invece il messaggio
di provenienza non disponibile. Non viene dedotta una provenienza mancante.

## Verifica delimitata

La regressione browser usa il catalogo reale e verifica apertura da tastiera,
reload, tre valori completi e assenza di overflow su desktop/mobile. Un
secondo caso distingue due revisioni di quaranta caratteri con lo stesso
prefisso e rende produttore e contesto opachi come testo. Altri due casi
coprono `null` e campi vuoti, mantenendo visibili risposta e navigazione del
Claim dove pertinente. Le varianti di payload sono controlli del consumer,
non nuove sessioni certificate dal kernel.

Questa unità affronta la leggibilità della provenienza nel debito H5/K4.
Non attesta autenticità H3, integrità storica, corrispondenza con un servizio
esterno o Product Verified; non completa residui, cross-check, terminal
mapping, accessibilità globale o prove con utenti. Schema, parser, kernel,
cataloghi e valori originali restano quelli dei rispettivi produttori.
