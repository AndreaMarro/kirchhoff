import {expect,it} from 'vitest';
import {lessonMathMarkup,lessonExpressionMarkup} from '../src/student/lessonMath';
const n=(...c:string[])=>({kind:'number',coefficients:[...c,...Array(4-c.length).fill('0')]});
const symbol=(name:string)=>({kind:'symbol',name});
const equation=(right:unknown)=>[{kind:'equation',left:symbol('V(A)'),right,unit:'V'}];

it('compone frazioni esatte e numeri complessi senza parti nulle',()=>{
 const html=lessonMathMarkup(equation(n('700/29','0','0','300/29')))!;
 expect(html).toContain('<mfrac><mn>700</mn><mn>29</mn></mfrac>');
 expect(html).toContain('<mfrac><mn>300</mn><mn>29</mn></mfrac>');
 expect(html).toContain('<mi>j</mi>');expect(html).not.toContain('<mn>0</mn>');
 expect(html).toContain('<msub><mi>V</mi><mtext>A</mtext></msub>');
});
it('proietta la base ciclotomica in forma rettangolare esatta',()=>{
 const html=lessonMathMarkup(equation(n('0','2','0','-1')))!;
 expect(html).toContain('<msqrt><mn>3</mn></msqrt>');
 expect(html).not.toContain('<mi>j</mi>');
 expect(lessonMathMarkup(equation(n('0','0','0','-1')))).toContain('<mo>−</mo><mi>j</mi>');
 const product=lessonExpressionMarkup({kind:'multiply',args:[n('0','0','1'),symbol('V(A)')]})!;
 expect(product).toContain('<mo>(</mo>');expect(product).toContain('<mo>)</mo>');
});
it('mantiene la struttura di KCL, frazione e segno senza interpretare testo come codice',()=>{
 const difference={kind:'add',args:[symbol('V(A)'),{kind:'multiply',args:[n('-1'),symbol('V(b)')]}]};
 const html=lessonMathMarkup(equation({kind:'divide',numerator:difference,denominator:n('2')}))!;
 expect(html).toContain('<mfrac>');expect(html).toContain('<mo>−</mo>');
 expect(html).not.toContain('<mn>1</mn>');
 const escaped=lessonMathMarkup([{kind:'equation',left:symbol('<img src=x onerror=alert(1)>'),right:n('0'),label:'<script>'}])!;
 expect(escaped).not.toContain('<script>');expect(escaped).not.toContain('<img');expect(escaped).toContain('&lt;img');
});
it('rifiuta campi non validi e alberi profondi senza perdere il fallback testuale',()=>{
 expect(lessonMathMarkup(equation(n('1/0')))).toBeNull();
 expect(lessonMathMarkup(equation({kind:'html',content:'<script>'}))).toBeNull();
 expect(lessonMathMarkup(equation(n('1'.repeat(401))))).toBeNull();
 let tree:unknown=n('1');for(let i=0;i<35;i++)tree={kind:'add',args:[tree]};
 expect(lessonMathMarkup(equation(tree))).toBeNull();
 expect(lessonMathMarkup(undefined)).toBeNull();
});

it('estrae i segni dai prodotti anche con fattori unitari o coefficienti diversi da uno',()=>{
 const result=lessonMathMarkup(equation({kind:'add',args:[symbol('V(A)'),{kind:'multiply',args:[n('1'),n('-10')]},{kind:'multiply',args:[n('-2'),symbol('V(b)')]}]}))!;
 expect(result).not.toContain('<mo>+</mo>');
 expect(result.match(/<mo>−<\/mo>/g)).toHaveLength(2);
});

it('compone il prodotto di due fattori negativi senza due segni consecutivi',()=>{
 const result=lessonExpressionMarkup({kind:'multiply',args:[n('-1'),n('-2'),symbol('V(b)')]})!;
 expect(result).not.toContain('<mo>−</mo>');
 expect(result).toContain('<mn>2</mn>');
});
