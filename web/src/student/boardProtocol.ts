/** Confine iframe: nessuna immagine/scena da finestre o origini diverse. */
export type BoardMessage={type:'kirchhoff:board-ready'}|{type:'kirchhoff:board-state';scene:string}|{type:'kirchhoff:board-image';image:string};
export function readBoardMessage(event:Pick<MessageEvent,'origin'|'source'|'data'>,frame:Window|null|undefined,origin:string):BoardMessage|null{
 if(!frame||event.origin!==origin||event.source!==frame)return null;
 const data=event.data;if(!data||typeof data!=='object')return null;
 if(data.type==='kirchhoff:board-ready')return {type:data.type};
 if(data.type==='kirchhoff:board-state'&&typeof data.scene==='string'&&data.scene.length<=10000000)return {type:data.type,scene:data.scene};
 if(data.type==='kirchhoff:board-image'&&typeof data.image==='string'&&data.image.length<=2800000&&/^data:image\/(png|jpeg);base64,[A-Za-z0-9+/=]+$/.test(data.image))return {type:data.type,image:data.image};
 return null;
}
