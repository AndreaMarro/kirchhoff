/** Sanitizzazione condivisa dalle viste standalone e MCP App. */
export function safeSvg(svg:string):string {
 const doc=new DOMParser().parseFromString(svg,'image/svg+xml');
 if(doc.querySelector('parsererror')||doc.documentElement.localName!=='svg')return '';
 const allowed=new Set(['svg','g','path','rect','circle','text']);
 for(const el of [...doc.querySelectorAll('*')]){
  if(!allowed.has(el.localName)){el.remove();continue;}
  for(const attr of [...el.attributes])if(/^on/i.test(attr.name)||/href/i.test(attr.name)||(/url\s*\(/i.test(attr.value))||attr.name==='style')el.removeAttribute(attr.name);
 }
 return new XMLSerializer().serializeToString(doc.documentElement);
}
