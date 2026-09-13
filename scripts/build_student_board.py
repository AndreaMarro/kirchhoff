"""Ricompila la lavagna usando un'installazione esistente: non installa pacchetti.

python scripts/build_student_board.py --donor /percorso/whiteboard-studio/studio
Il bundle autosufficiente e le licenze vengono conservati in web/public/board.
"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess

ROOT=Path(__file__).resolve().parent.parent
parser=argparse.ArgumentParser()
parser.add_argument('--donor',type=Path,required=True)
args=parser.parse_args()
donor=args.donor.resolve()
modules=donor/'node_modules'
package=modules/'@excalidraw/excalidraw'
license_path=ROOT/'companion-board/EXCALIDRAW-LICENSE.txt'
if not license_path.is_file():raise SystemExit('Manca la licenza Excalidraw conservata nel repository.')
version=json.loads((package/'package.json').read_text())['version']
if version!='0.18.1':raise SystemExit('Questa integrazione è validata con Excalidraw 0.18.1.')
link=ROOT/'companion-board/node_modules'
if not link.exists():link.symlink_to(modules,target_is_directory=True)
if link.resolve()!=modules:raise SystemExit('node_modules punta a un altro donor: non lo sovrascrivo.')
subprocess.run(['node',str(modules/'typescript/bin/tsc'),'--noEmit','--jsx','react-jsx','--module','esnext','--moduleResolution','bundler','--target','ES2022','--lib','ES2022,DOM','--skipLibCheck','--esModuleInterop','main.tsx'],cwd=link.parent,check=True)
subprocess.run(['node',str(modules/'vite/bin/vite.js'),'build','--config','vite.config.mjs'],cwd=link.parent,check=True)
out=ROOT/'web/public/board'
for font in (package/'dist/prod/fonts').iterdir():
    if font.is_dir():shutil.copytree(font,out/font.name,dirs_exist_ok=True)
    else:shutil.copy2(font,out/font.name)
# Il package pubblicato omette LICENSE: copia ufficiale dal tag v0.18.1,
# https://raw.githubusercontent.com/excalidraw/excalidraw/v0.18.1/LICENSE
notices=['Excalidraw 0.18.1\n'+license_path.read_text()]
for pattern in ('*/LICENSE*','@*/*/LICENSE*'):
    for license in sorted(modules.glob(pattern)):
        if license.is_file() and license.stat().st_size<100000:
            notices.append(str(license.relative_to(modules))+'\n'+license.read_text(errors='replace'))
(out/'THIRD-PARTY-NOTICES.txt').write_text('\n'.join(line.rstrip() for line in '\n\n'.join(notices).splitlines())+'\n')
manifest={'excalidraw':version,'donor_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=donor,text=True).strip(),'source':'MAESTRO-Studio: Room.tsx Excalidraw pattern; loadFile.ts image decoder','source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'companion-board').iterdir()) if p.is_file()},'files':{str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.rglob('*')) if p.is_file()}}
(out/'build-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
