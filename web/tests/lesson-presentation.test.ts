import {describe,it,expect} from 'vitest';
import {verificationDescription,decimalForReading,isAcLesson,isLaplaceLesson,supportsDcTools,answerPrefix} from '../src/student/lessonPresentation';

const ac={method:'phasor',verification:{electrical_claim:'PHASOR_PATHS_CROSSCHECKED',backend:'PHASOR_RESIDUALS_CHECKED',lesson:'phasor-all-branches-crosscheck',product_verified:false}};
const power={method:'phasor',verification:{electrical_claim:'PHASOR_POWER_CROSSCHECKED',backend:'PHASOR_RESIDUALS_AND_POWER_CHECKED',lesson:'phasor-power-all-branches-crosscheck',product_verified:false}};
const impedance={method:'test_current',conventions:{domain:'ac_sinusoidal'},verification:{electrical_claim:'PHASOR_PORT_PATHS_CROSSCHECKED',backend:'PHASOR_PORT_RESIDUALS_CHECKED',lesson:'phasor-port-crosscheck',product_verified:false}};
describe('ambito della verifica visibile',()=>{
 it('presenta Laplace come trasformata e tiene disattivati gli strumenti limitati alla continua',()=>{
  const laplace={method:'laplace',conventions:{domain:'laplace'},verification:{electrical_claim:'LAPLACE_ALGEBRA_CROSSCHECKED',backend:'SYMBOLIC_MNA_AND_ALGEBRA_CHECKED',lesson:'laplace-exact-algebra-crosscheck',product_verified:false}};
  expect(isLaplaceLesson(laplace)).toBe(true);expect(isAcLesson(laplace)).toBe(false);
  expect(supportsDcTools(laplace)).toBe(false);expect(supportsDcTools(impedance)).toBe(false);
  expect(supportsDcTools({method:'test_current'})).toBe(true);expect(supportsDcTools(null)).toBe(false);
  expect(answerPrefix('voltage','laplace')).toBe('V(s) = ');expect(answerPrefix('current','laplace')).toBe('I(s) = ');
  expect(verificationDescription(laplace)).toContain('funzione del tempo non è ancora calcolata');
  for(const key of ['electrical_claim','backend','lesson','product_verified'] as const)
   expect(verificationDescription({...laplace,verification:{...laplace.verification,[key]:key==='product_verified'?true:'inventato'}})).toContain('non è riconosciuto');
  expect(verificationDescription({...laplace,conventions:{domain:'ac_sinusoidal'}})).toContain('non è riconosciuto');
 });
 it('riconosce il dominio AC anche con corrente di prova e lascia distinta la porta DC',()=>{
  expect(isAcLesson(impedance)).toBe(true);
  expect(isAcLesson(ac)).toBe(true);
  expect(isAcLesson({method:'test_current'})).toBe(false);
  expect(isAcLesson(null)).toBe(false);
  expect(answerPrefix('equivalent_impedance')).toBe('Z = ');
  expect(answerPrefix('power')).toBe('S = ');
  expect(answerPrefix()).toBe('');
 });
 it('dichiara i controlli della porta AC e rifiuta tutte le alterazioni della tupla',()=>{
  expect(verificationDescription(impedance)).toContain('corrente di prova');
  expect(verificationDescription(impedance)).toContain('non ha una certificazione VERIFIED');
  for(const key of ['electrical_claim','backend','lesson','product_verified'] as const)
   expect(verificationDescription({...impedance,verification:{...impedance.verification,[key]:key==='product_verified'?true:'inventato'}})).toContain('non è riconosciuto');
  expect(verificationDescription({...impedance,method:'phasor'})).toContain('non è riconosciuto');
 });
 it('nomina il confronto indipendente delle potenze e il bilancio senza certificare la lezione',()=>{
  expect(verificationDescription(power)).toContain('prodotto rettangolare indipendente');
  expect(verificationDescription(power)).toContain('bilancio di P e Q è nullo');
  expect(verificationDescription(power)).toContain('non ha una certificazione VERIFIED');
 });
 it.each(['electrical_claim','backend','lesson','product_verified'] as const)('rifiuta la tupla di potenza alterata: %s',key=>{
  expect(verificationDescription({...power,verification:{...power.verification,[key]:key==='product_verified'?true:'inventato'}})).toContain('non è riconosciuto');
 });
 it('nomina il confronto AC senza promuoverlo a lezione certificata',()=>{
  expect(verificationDescription(ac)).toContain('due assemblaggi esatti indipendenti');
  expect(verificationDescription(ac)).toContain('non ha una certificazione VERIFIED');
 });
 it.each(['electrical_claim','backend','lesson','product_verified'] as const)('rifiuta il contratto alterato: %s',key=>{
  const changed={...ac,verification:{...ac.verification,[key]:key==='product_verified'?true:'inventato'}};
  expect(verificationDescription(changed)).toContain('non è riconosciuto');
 });
 it('distingue DC canonico da sottoprove di porta',()=>{
  expect(verificationDescription({verification:{electrical_claim:'VERIFIED',backend:'CLOSED',lesson:'exact-answer-crosscheck',product_verified:false}})).toContain('risultato elettrico');
  expect(verificationDescription({verification:{electrical_claim:'PORT_SUBPROOFS_CROSSCHECKED',backend:'SUBPROOFS_CLOSED',lesson:'port-subproof-crosscheck',product_verified:false}})).toContain('sottoprove');
 });
 it('formatta entrambe le componenti senza modificare segno o esponente',()=>{
  expect(decimalForReading('(2.2767090) + j*(-0.61004234)')).toBe('(2,2767090) + j*(-0,61004234)');
  expect(decimalForReading('1.2e-10')).toBe('1,2e-10');
 });
});
