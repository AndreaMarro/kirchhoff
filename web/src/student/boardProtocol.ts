/** Confine iframe: nessuna immagine/scena da finestre o origini diverse. */
export type BoardMessage={type:'kirchhoff:board-ready'}|{type:'kirchhoff:board-state';scene:string}|{type:'kirchhoff:board-image';image:string;scene:string;selectedElementIds:string[];selectionOnly:boolean}|{type:'kirchhoff:board-snapshot';scene:string;requestId:string};
function sourceElements(scene:string,selected:unknown,selectionOnly:unknown):selected is string[]{
 if(typeof scene!=='string'||scene.length>10000000||!Array.isArray(selected)||!selected.length||selected.length>10000||typeof selectionOnly!=='boolean'||
    !selected.every(id=>typeof id==='string'&&id.length>0&&id.length<=128)||new Set(selected).size!==selected.length)return false;
 try{
  const parsed=JSON.parse(scene) as {elements?:unknown;files?:unknown};
  if(!parsed||!Array.isArray(parsed.elements)||parsed.elements.length>10000||!parsed.files||typeof parsed.files!=='object')return false;
  const live=parsed.elements.filter((item:unknown):item is {id:string;isDeleted?:boolean}=>
   Boolean(item)&&typeof item==='object'&&typeof (item as {id?:unknown}).id==='string'&&!(item as {isDeleted?:boolean}).isDeleted);
  const ids=new Set(live.map(item=>item.id));
  return selected.every(id=>ids.has(id))&&(selectionOnly||selected.length===ids.size&&ids.size===live.length);
 }catch{return false;}
}
export function readBoardMessage(event:Pick<MessageEvent,'origin'|'source'|'data'>,frame:Window|null|undefined,origin:string):BoardMessage|null{
 if(!frame||event.origin!==origin||event.source!==frame)return null;
 const data=event.data;if(!data||typeof data!=='object')return null;
 if(data.type==='kirchhoff:board-ready')return {type:data.type};
 if(data.type==='kirchhoff:board-state'&&typeof data.scene==='string'&&data.scene.length<=10000000)return {type:data.type,scene:data.scene};
 if(data.type==='kirchhoff:board-snapshot'&&typeof data.scene==='string'&&data.scene.length<=10000000&&typeof data.requestId==='string'&&/^[a-f0-9-]{36}$/.test(data.requestId))return {type:data.type,scene:data.scene,requestId:data.requestId};
 if(data.type==='kirchhoff:board-image'&&typeof data.image==='string'&&data.image.length<=2800000&&/^data:image\/(png|jpeg);base64,[A-Za-z0-9+/=]+$/.test(data.image)&&sourceElements(data.scene,data.selectedElementIds,data.selectionOnly))return {type:data.type,image:data.image,scene:data.scene,selectedElementIds:data.selectedElementIds,selectionOnly:data.selectionOnly};
 return null;
}
