import {defineConfig} from 'vite';

export default defineConfig({
 build:{
  outDir:'dist/mcp',emptyOutDir:false,target:'es2022',sourcemap:false,
  lib:{entry:'src/mcp-app.ts',name:'KirchhoffMcpApp',formats:['iife'],fileName:'kirchhoff-mcp-app'},
 },
});
