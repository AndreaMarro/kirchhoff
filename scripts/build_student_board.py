"""Ricompila la lavagna dal lockfile pubblico, senza checkout esterni.

Prima installa con ``npm ci --prefix companion-board``; poi esegui questo
script. Il bundle autosufficiente e le licenze vivono in web/public/board.
"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess

ROOT=Path(__file__).resolve().parent.parent
argparse.ArgumentParser(description='Ricompila la lavagna dal lockfile locale.').parse_args()
board=ROOT/'companion-board'
modules=board/'node_modules'
package=modules/'@excalidraw/excalidraw'
license_path=ROOT/'companion-board/EXCALIDRAW-LICENSE.txt'
if not license_path.is_file():raise SystemExit('Manca la licenza Excalidraw conservata nel repository.')
if modules.is_symlink() or not package.is_dir():
    raise SystemExit('Dipendenze lavagna assenti o collegate a un donor: esegui npm ci --prefix companion-board.')
version=json.loads((package/'package.json').read_text())['version']
if version!='0.18.1':raise SystemExit('Questa integrazione è validata con Excalidraw 0.18.1.')
subprocess.run(['npm','run','build'],cwd=board,check=True)
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
manifest={'excalidraw':version,'lock_sha256':hashlib.sha256((board/'package-lock.json').read_bytes()).hexdigest(),'source':'Kirchhoff companion-board; Excalidraw 0.18.1','source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(board.iterdir()) if p.is_file()},'files':{str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.rglob('*')) if p.is_file()}}
(out/'build-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
