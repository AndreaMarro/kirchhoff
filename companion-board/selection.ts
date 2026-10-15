/** Solo i tratti scelti entrano nel ritaglio; il resto della scena rimane salvato. */
export function elementsForInterpretation<T extends {id:string;isDeleted?:boolean}>(
 elements:readonly T[],selected:Readonly<Record<string,boolean>>,selectionOnly:boolean,
):T[]{
 const live=elements.filter(element=>!element.isDeleted);
 if(!selectionOnly)return live;
 const chosen=live.filter(element=>selected[element.id]===true);
 if(!chosen.length)throw new Error('Seleziona i tratti o la regione da interpretare sulla lavagna.');
 return chosen;
}
