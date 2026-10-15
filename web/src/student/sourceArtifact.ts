/** Portable source bytes. Integrity does not certify the interpretation of a source. */
export type SourceFile = {name:string;mediaType:string;dataURL:string;sha256:string};
export type SourceSelection={page:number|null;totalPages:number|null;crop:{x:number;y:number;width:number;height:number}};
export type SourceArtifact = {
 schema:'kirchhoff-source.v1';kind:'image'|'board'|'pdf';
 original:SourceFile|null;
 prepared:{dataURL:string;sha256:string};
 selection?:SourceSelection;
};
const record=(v:unknown):v is Record<string,unknown>=>Boolean(v)&&typeof v==='object'&&!Array.isArray(v);
export async function imageBytesHash(dataURL:string,maxBytes=2_000_000):Promise<string>{
 if(typeof dataURL!=='string'||dataURL.length>Math.ceil(maxBytes/3)*4+64)throw new Error('La fonte supera il limite consentito.');
 const match=/^data:image\/(png|jpeg|webp);base64,([A-Za-z0-9+/]+={0,2})$/.exec(dataURL);
 if(!match||match[2].length%4!==0)throw new Error('La fonte deve essere una immagine PNG, JPEG o WebP.');
 let binary:string;
 try{binary=atob(match[2]);}catch{throw new Error('I byte della fonte non sono leggibili.');}
 if(!binary.length||binary.length>maxBytes||btoa(binary)!==match[2])throw new Error('I byte della fonte non sono validi.');
 const valid=match[1]==='png'?binary.startsWith('\x89PNG\r\n\x1a\n'):match[1]==='jpeg'?binary.startsWith('\xff\xd8\xff'):binary.startsWith('RIFF')&&binary.slice(8,12)==='WEBP';
 if(!valid)throw new Error('Il contenuto della fonte non corrisponde al formato dichiarato.');
 const bytes=Uint8Array.from(binary,c=>c.charCodeAt(0));
 return [...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(v=>v.toString(16).padStart(2,'0')).join('');
}
export async function preserveImageFile(file:File):Promise<SourceFile>{
 if(file.size>20_000_000)throw new Error('La fonte originale supera 20 MB.');
 const dataURL=await new Promise<string>((resolve,reject)=>{
  const reader=new FileReader();reader.onerror=()=>reject(new Error('Lettura della fonte originale non riuscita.'));
  reader.onload=()=>resolve(String(reader.result));reader.readAsDataURL(file);
 });
 return {name:file.name.slice(0,255),mediaType:file.type,dataURL,sha256:await sourceFileHash(dataURL)};
}
export async function sourceFileHash(dataURL:string):Promise<string>{
 if(!dataURL.startsWith('data:application/pdf;'))return imageBytesHash(dataURL,20_000_000);
 if(dataURL.length>26_666_700)throw new Error('Il PDF originale supera 20 MB.');
 const match=/^data:application\/pdf;base64,([A-Za-z0-9+/]+={0,2})$/.exec(dataURL);
 if(!match||match[1].length%4!==0)throw new Error('Il PDF originale non è valido.');
 const bytes=atob(match[1]);
 if(!bytes.startsWith('%PDF-')||bytes.length>20_000_000||btoa(bytes)!==match[1])throw new Error('Il PDF originale non è valido.');
 return [...new Uint8Array(await crypto.subtle.digest('SHA-256',Uint8Array.from(bytes,c=>c.charCodeAt(0))))].map(v=>v.toString(16).padStart(2,'0')).join('');
}
export async function makeSourceArtifact(image:string,kind:SourceArtifact['kind'],original:SourceFile|null=null,selection?:SourceSelection):Promise<SourceArtifact>{
 const value:SourceArtifact={schema:'kirchhoff-source.v1',kind,original,prepared:{dataURL:image,sha256:await imageBytesHash(image)},...(selection?{selection}:{})};
 return readSourceArtifact(value);
}
export async function readSourceArtifact(value:unknown):Promise<SourceArtifact>{
 if(!record(value)||value.schema!=='kirchhoff-source.v1'||!['image','board','pdf'].includes(String(value.kind))||!record(value.prepared)||
    typeof value.prepared.dataURL!=='string'||typeof value.prepared.sha256!=='string')throw new Error('La fonte nel quaderno non è valida.');
 if(await imageBytesHash(value.prepared.dataURL)!==value.prepared.sha256)throw new Error('La fonte preparata è stata modificata.');
 if(value.original!==null){
  const source=value.original;
  if(!record(source)||typeof source.name!=='string'||!source.name||source.name.length>255||
     !['image/png','image/jpeg','image/webp','application/pdf'].includes(String(source.mediaType))||typeof source.dataURL!=='string'||
     !source.dataURL.startsWith(`data:${source.mediaType};base64,`)||typeof source.sha256!=='string'||
     await sourceFileHash(source.dataURL)!==source.sha256)throw new Error('La fonte originale è stata modificata o non è valida.');
 }
 if(value.kind==='board'&&value.original!==null)throw new Error('La fonte della lavagna non può dichiarare un file fotografico originale.');
 if(value.selection!==undefined){
  const s=value.selection,c=record(s)?s.crop:null;
  if(!record(s)||!record(c)||![c.x,c.y,c.width,c.height].every(v=>typeof v==='number'&&Number.isFinite(v))||
     Number(c.x)<0||Number(c.y)<0||Number(c.width)<=0||Number(c.height)<=0||Number(c.x)+Number(c.width)>1.00000001||Number(c.y)+Number(c.height)>1.00000001||
     !(s.page===null&&s.totalPages===null||Number.isInteger(s.page)&&Number.isInteger(s.totalPages)&&Number(s.page)>=1&&Number(s.page)<=Number(s.totalPages)&&Number(s.totalPages)<=2000))
   throw new Error('La pagina o il ritaglio della fonte non sono validi.');
 }
 if(value.kind==='pdf'&&(!record(value.original)||value.original.mediaType!=='application/pdf'||!record(value.selection)||value.selection.page===null))throw new Error('Manca il PDF originale o la pagina selezionata.');
 if(value.kind!=='pdf'&&(record(value.original)&&value.original.mediaType==='application/pdf'||record(value.selection)&&value.selection.page!==null))throw new Error('Il tipo della fonte non coincide con la pagina selezionata.');
 return value as SourceArtifact;
}
