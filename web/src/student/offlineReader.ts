/** Il service worker conserva solo risorse pubbliche della build, mai API o quaderni. */
export async function prepareOfflineReader():Promise<boolean>{
 if(!('serviceWorker' in navigator)||!window.isSecureContext)return false;
 try{
  await navigator.serviceWorker.register(new URL('offline-sw.js',document.baseURI),{scope:'./'});
  await navigator.serviceWorker.ready;
  return true;
 }catch{return false;}
}
