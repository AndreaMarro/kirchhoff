/// <reference types="vite/client" />
import workerUrl from 'pdfjs-dist/build/pdf.worker.min.mjs?url';
export type Crop={x:number;y:number;width:number;height:number};
export const wholePage:Crop={x:0,y:0,width:1,height:1};
export function validateCrop(crop:Crop):Crop{
 const {x,y,width,height}=crop;
 if(![x,y,width,height].every(Number.isFinite)||x<0||y<0||width<=0||height<=0||x+width>1.00000001||y+height>1.00000001)
  throw new Error('Il ritaglio deve restare dentro la pagina.');
 return {x,y,width,height};
}
/** Read only page paint operators. No viewer, links, form actions or scripts are mounted. */
export async function openPdfSource(file:File){
 if(file.size>20_000_000||file.size<5)throw new Error('Usa un PDF entro 20 MB.');
 const bytes=new Uint8Array(await file.arrayBuffer());
 if(new TextDecoder().decode(bytes.slice(0,5))!=='%PDF-')throw new Error('Il file non contiene un PDF leggibile.');
 const pdfjs=await import('pdfjs-dist');pdfjs.GlobalWorkerOptions.workerSrc=workerUrl;
 const task=pdfjs.getDocument({data:bytes,useSystemFonts:true});
 try{
  const pdf=await task.promise;
  if(pdf.numPages>2000){await task.destroy();throw new Error('Il PDF supera 2000 pagine. Scegli un documento più piccolo.');}
  return {pdf,dispose:()=>task.destroy()};
 }catch(error){await task.destroy();throw error;}
}
export async function cropSourceImage(dataURL:string,crop:Crop=wholePage):Promise<string>{
 validateCrop(crop);
 const image=new Image();await new Promise<void>((resolve,reject)=>{image.onload=()=>resolve();image.onerror=()=>reject(new Error('La pagina non è leggibile.'));image.src=dataURL;});
 const width=Math.max(1,Math.round(image.naturalWidth*crop.width)),height=Math.max(1,Math.round(image.naturalHeight*crop.height));
 const scale=Math.min(1,2000/Math.max(width,height));
 const canvas=document.createElement('canvas');canvas.width=Math.max(1,Math.round(width*scale));canvas.height=Math.max(1,Math.round(height*scale));
 const context=canvas.getContext('2d');if(!context)throw new Error('Il browser non può preparare il ritaglio.');
 context.fillStyle='white';context.fillRect(0,0,canvas.width,canvas.height);
 context.drawImage(image,Math.round(image.naturalWidth*crop.x),Math.round(image.naturalHeight*crop.y),width,height,0,0,canvas.width,canvas.height);
 for(const quality of [.94,.84,.7]){const result=canvas.toDataURL('image/jpeg',quality);if(result.length<=2_666_600)return result;}
 throw new Error('Il ritaglio è troppo grande per l’analisi. Scegli una zona più piccola.');
}
