// Riutilizzato da MAESTRO-Studio/src/loadFile.ts (imageToDataURL).
// Nessuna rete: FileReader -> decodifica del browser -> eventuale riduzione locale.
export function imageToDataURL(file:File):Promise<{dataURL:string;width:number;height:number}>{
 return new Promise((resolve,reject)=>{
  const r=new FileReader();r.onerror=()=>reject(new Error('Lettura della foto non riuscita.'));
  r.onload=()=>{const dataURL=String(r.result),img=new Image();img.onload=()=>resolve({dataURL,width:img.naturalWidth,height:img.naturalHeight});img.onerror=()=>reject(new Error('Il file non contiene un’immagine leggibile.'));img.src=dataURL;};
  r.readAsDataURL(file);
 });
}
export async function prepareCircuitImage(file:File):Promise<string>{
 if(!['image/png','image/jpeg','image/webp'].includes(file.type)||file.size>20000000)throw new Error('Usa una foto PNG, JPEG o WebP entro 20 MB.');
 const image=await imageToDataURL(file);
 if(!image.width||!image.height||image.width*image.height>80000000)throw new Error('Dimensioni della foto non supportate.');
 if(file.size<=2000000&&Math.max(image.width,image.height)<=2400)return image.dataURL;
 const scale=Math.min(1,2000/Math.max(image.width,image.height));
 const canvas=document.createElement('canvas');canvas.width=Math.round(image.width*scale);canvas.height=Math.round(image.height*scale);
 const context=canvas.getContext('2d');if(!context)throw new Error('Il browser non può preparare la foto.');
 const source=new Image();await new Promise<void>((resolve,reject)=>{source.onload=()=>resolve();source.onerror=()=>reject(new Error('Foto non leggibile.'));source.src=image.dataURL;});
 context.fillStyle='#ffffff';context.fillRect(0,0,canvas.width,canvas.height);context.drawImage(source,0,0,canvas.width,canvas.height);
 for(const quality of [.92,.82,.7]){const value=canvas.toDataURL('image/jpeg',quality);if(value.length<=2666600)return value;}
 throw new Error('La foto resta troppo grande: ritaglia il solo circuito prima di caricarla.');
}
