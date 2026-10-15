/** Ambito pubblicato della verifica, condiviso dalla pagina e dalla MCP App. */
export type Verification={electrical_claim:string;backend:string;lesson:string;product_verified:boolean};
export type VerifiedLesson={method?:string;verification?:Verification;conventions?:{domain?:string}};

export const isAcLesson=(value:VerifiedLesson|null):boolean=>
 value?.conventions?.domain==='ac_sinusoidal'||value?.method==='phasor';
export const isLaplaceLesson=(value:VerifiedLesson|null):boolean=>
 value?.conventions?.domain==='laplace'||value?.method==='laplace';
export const supportsDcTools=(value:VerifiedLesson|null):boolean=>Boolean(value)&&!isAcLesson(value)&&!isLaplaceLesson(value);
export const answerPrefix=(quantity?:string,domain?:string):string=>
 domain==='laplace' ? quantity==='voltage'?'V(s) = ':quantity==='current'?'I(s) = ':'' :
 quantity==='power'?'S = ':quantity==='equivalent_impedance'?'Z = ':'';

export function verificationDescription(value:VerifiedLesson):string{
 const proof=value.verification;
 if(proof?.product_verified!==false)return 'Lo stato di verifica della lezione non è riconosciuto.';
 if(value.method==='laplace'&&value.conventions?.domain==='laplace'&&
    proof.electrical_claim==='LAPLACE_ALGEBRA_CROSSCHECKED'&&proof.backend==='SYMBOLIC_MNA_AND_ALGEBRA_CHECKED'&&
    proof.lesson==='laplace-exact-algebra-crosscheck')
  return 'Le trasformate e i passaggi algebrici sono controllati con identità esatte, includendo le condizioni iniziali dichiarate. La risposta è nel dominio di Laplace; la funzione del tempo non è ancora calcolata. La lezione completa non ha una certificazione VERIFIED.';
 if(value.method==='test_current'&&proof.electrical_claim==='PHASOR_PORT_PATHS_CROSSCHECKED'&&
    proof.backend==='PHASOR_PORT_RESIDUALS_CHECKED'&&proof.lesson==='phasor-port-crosscheck')
  return 'L’impedenza di porta coincide in due assemblaggi esatti indipendenti della rete con sorgenti azzerate e corrente di prova. Sono controllati il verso della sonda, la trasformazione e l’algebra. La lezione completa non ha una certificazione VERIFIED.';
 if(value.method==='phasor'&&proof.electrical_claim==='PHASOR_POWER_CROSSCHECKED'&&
    proof.backend==='PHASOR_RESIDUALS_AND_POWER_CHECKED'&&proof.lesson==='phasor-power-all-branches-crosscheck')
  return 'Tensioni e correnti coincidono nei due assemblaggi esatti. La potenza di ogni ramo coincide con un prodotto rettangolare indipendente e il bilancio di P e Q è nullo. La lezione completa non ha una certificazione VERIFIED.';
 if(value.method==='phasor'&&proof.electrical_claim==='PHASOR_PATHS_CROSSCHECKED'&&
    proof.backend==='PHASOR_RESIDUALS_CHECKED'&&proof.lesson==='phasor-all-branches-crosscheck')
  return 'Tensioni e correnti fasoriali coincidono in due assemblaggi esatti indipendenti. Sono controllate anche le leggi dei componenti, KCL e KVL. La lezione completa non ha una certificazione VERIFIED.';
 if(proof.electrical_claim==='PORT_SUBPROOFS_CROSSCHECKED'&&proof.backend==='SUBPROOFS_CLOSED'&&proof.lesson==='port-subproof-crosscheck')
  return 'Le due sottoprove di porta sono chiuse e il risultato è confrontato con il kernel indipendente. La certificazione riguarda le sottoprove; il prodotto completo richiede ulteriori controlli.';
 if(proof.electrical_claim==='VERIFIED'&&proof.backend==='CLOSED'&&proof.lesson==='exact-answer-crosscheck')
  return 'Il risultato elettrico proviene dal nucleo verificato; la risposta della derivazione didattica è confrontata in aritmetica esatta. Questo controllo non certifica da solo ogni scelta grafica e didattica.';
 return 'Lo stato di verifica della lezione non è riconosciuto.';
}

export const decimalForReading=(value:string)=>value.replaceAll('.',',');
