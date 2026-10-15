import {defineConfig} from 'vite';
export default defineConfig({base:'./',publicDir:false,resolve:{dedupe:['react','react-dom']},build:{outDir:'../web/public/board',emptyOutDir:true,chunkSizeWarningLimit:2500}});
