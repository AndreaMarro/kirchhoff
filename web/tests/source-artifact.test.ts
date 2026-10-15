import {it,expect} from 'vitest';
import {imageBytesHash,makeSourceArtifact,readSourceArtifact,sourceFileHash} from '../src/student/sourceArtifact.ts';
const image='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Y9b4wAAAABJRU5ErkJggg==';

it('conserva i byte originali e preparati separatamente senza inventare una conferma',async()=>{
 const original={name:'foto.png',mediaType:'image/png',dataURL:image,sha256:await imageBytesHash(image)};
 const source=await makeSourceArtifact(image,'image',original);
 expect(await readSourceArtifact(JSON.parse(JSON.stringify(source)))).toEqual(source);
 expect(source.original?.dataURL).toBe(image);
 expect(source).not.toHaveProperty('confirmation_token');
});
it('rileva la sostituzione dei byte o della impronta anche se il circuito non cambia',async()=>{
 const source=await makeSourceArtifact(image,'image');
 await expect(readSourceArtifact({...source,prepared:{...source.prepared,sha256:'a'.repeat(64)}})).rejects.toThrow('modificata');
 await expect(readSourceArtifact({...source,prepared:{...source.prepared,dataURL:image.replace('ggg==','ggh==')}})).rejects.toThrow();
 await expect(readSourceArtifact({...source,original:{name:'foto.png',mediaType:'image/png',dataURL:image,sha256:'b'.repeat(64)}})).rejects.toThrow('originale');
});
it('rifiuta URL remoti, SVG attivo e dichiarazioni di formato false',async()=>{
 for(const bad of ['https://example.org/foto.png','data:image/svg+xml;base64,PHN2Zz4=',image.replace('image/png','image/jpeg'),'data:image/png;base64,YQ=='])
  await expect(imageBytesHash(bad)).rejects.toThrow();
 await expect(imageBytesHash(image,8)).rejects.toThrow('limite');
});
it('distingue un ritaglio della lavagna da un file originale caricato',async()=>{
 const source=await makeSourceArtifact(image,'board');
 expect(source.original).toBeNull();
 await expect(readSourceArtifact({...source,original:{name:'foto.png',mediaType:'image/png',dataURL:image,sha256:await imageBytesHash(image)}})).rejects.toThrow('lavagna');
});
it('lega la pagina e il ritaglio al PDF originale senza promuoverli a trascrizione verificata',async()=>{
 const dataURL='data:application/pdf;base64,'+btoa('%PDF-1.4\n% contract test');
 const original={name:'documento.pdf',mediaType:'application/pdf',dataURL,sha256:await sourceFileHash(dataURL)};
 const selection={page:2,totalPages:3,crop:{x:.1,y:.2,width:.8,height:.6}};
 const source=await makeSourceArtifact(image,'pdf',original,selection);
 expect((await readSourceArtifact(source)).selection).toEqual(selection);
 await expect(readSourceArtifact({...source,selection:{...selection,page:4}})).rejects.toThrow('pagina');
 await expect(readSourceArtifact({...source,selection:{...selection,crop:{...selection.crop,width:1}}})).rejects.toThrow('ritaglio');
 await expect(readSourceArtifact({...source,original:null})).rejects.toThrow('PDF originale');
 await expect(readSourceArtifact({...source,kind:'image'})).rejects.toThrow('tipo');
 await expect(readSourceArtifact({...source,original:{...original,sha256:'a'.repeat(64)}})).rejects.toThrow('originale');
});
