"""PDF vettoriale autonomo, dai medesimi snapshot SVG della lezione.

Supporta soltanto il vocabolario del nostro renderer, non SVG arbitrari.
Il font PDF standard usa traslitterazioni esplicite per simboli non WinAnsi.
Nessuna dipendenza di sistema, rete o processo di stampa.
"""
import re
import textwrap
import xml.etree.ElementTree as ET


def _plain(s):
    for a, b in {'Ω':'ohm', 'Σ':'Somma', '→':'->', '−':'-', '×':'x', '‖':' || ', '≠':'!=', 'Δ':'Delta', '…':'...'}.items():
        s = s.replace(a, b)
    return s.encode('cp1252', 'replace').decode('cp1252')


def _literal(s):
    return _plain(str(s)).replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')


def _text(x, y, text, size=11):
    return f'BT /F1 {size} Tf 1 0 0 1 {x:.2f} {y:.2f} Tm ({_literal(text)}) Tj ET\n'


def _rgb(color):
    if color == 'white':
        return '1 1 1'
    if not re.fullmatch(r'#[0-9a-fA-F]{6}', color):
        return '0.14 0.20 0.29'
    return ' '.join(str(int(color[i:i+2],16)/255) for i in (1,3,5))


def _drawing(svg):
    root = ET.fromstring(svg)
    _, _, w, h = map(float, root.attrib['viewBox'].split())
    scale = min(510/w, 320/h)
    xoff, ytop = (595-w*scale)/2, 727
    def xy(x, y):
        return xoff+float(x)*scale, ytop-float(y)*scale
    result = 'q\n'
    for el in root:
        a, tag = el.attrib, el.tag.split('}')[-1]
        result += f'{_rgb(a.get("stroke", "#24334b"))} RG {_rgb(a.get("fill", "#24334b"))} rg {float(a.get("stroke-width",2))*scale:.3f} w\n'
        if tag == 'text':
            value, size = ''.join(el.itertext()), float(a.get('font-size',17))*scale
            x, y = xy(a['x'], a['y'])
            length = len(_plain(value))*size*.48
            if a.get('text-anchor') == 'middle': x -= length/2
            if a.get('text-anchor') == 'end': x -= length
            result += _text(x,y,value,size)
        elif tag == 'path':
            parts = re.findall(r'[ML]|-?\d+(?:\.\d+)?', a['d'])
            for i in range(0,len(parts),3):
                command,x,y=parts[i:i+3];px,py=xy(x,y)
                result += f'{px:.3f} {py:.3f} {"m" if command=="M" else "l"}\n'
            result += 'S\n'
        elif tag == 'rect':
            x,y=xy(a['x'],a['y']);rw,rh=float(a['width'])*scale,float(a['height'])*scale
            result += f'{x:.3f} {y-rh:.3f} {rw:.3f} {rh:.3f} re '+('B' if 'stroke' in a else 'f')+'\n'
        elif tag == 'circle':
            x,y=xy(a['cx'],a['cy']);r=float(a['r'])*scale;k=r*.5522847498
            result += (f'{x+r:.3f} {y:.3f} m {x+r:.3f} {y+k:.3f} {x+k:.3f} {y+r:.3f} {x:.3f} {y+r:.3f} c '
                       f'{x-k:.3f} {y+r:.3f} {x-r:.3f} {y+k:.3f} {x-r:.3f} {y:.3f} c '
                       f'{x-r:.3f} {y-k:.3f} {x-k:.3f} {y-r:.3f} {x:.3f} {y-r:.3f} c '
                       f'{x+k:.3f} {y-r:.3f} {x+r:.3f} {y-k:.3f} {x+r:.3f} {y:.3f} c '
                       +('B' if 'stroke' in a else 'f')+'\n')
    return result+'Q\n', ytop-h*scale-28


def export_pdf(lesson):
    if lesson.get('outcome') != 'solved':
        raise ValueError('Il PDF richiede una lezione risolta.')
    objects = [b'', b'', b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>']
    pages=[]
    def page(stream):
        content=stream.encode('cp1252','replace');content_id=len(objects)+1
        objects.append(f'<< /Length {len(content)} >>\nstream\n'.encode()+content+b'endstream')
        page_id=len(objects)+1
        objects.append(f'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 3 0 R >> >> /Contents {content_id} 0 R >>'.encode())
        pages.append(page_id)
    for i, step in enumerate(lesson['steps']):
        stream='0.14 0.20 0.29 rg\n'+_text(42,800,'KIRCHHOFF / Il circuito, un passaggio alla volta',11)
        title=textwrap.wrap(_plain(step['title']),62)
        for j,line in enumerate(title): stream+=_text(42,771-j*18,line,15)
        drawing,y=_drawing(step['svg']);stream+=drawing
        for paragraph in [step['explanation'], *step['equations']]:
            for line in textwrap.wrap(_plain(paragraph),82,break_long_words=True):
                if y<70:
                    stream+=_text(42,35,f'Passaggio {i+1} - continua',9);page(stream)
                    stream='0.14 0.20 0.29 rg\n'+_text(42,790,step['title']+' (continua)',13);y=758
                stream+=_text(42,y,line);y-=16
            y-=13
        stream+=_text(42,35,f'{i+1}/{len(lesson["steps"])} - {lesson["title"]} - {lesson["answer"]["reference"]}',9)
        page(stream)
    objects[0]=b'<< /Type /Catalog /Pages 2 0 R >>'
    objects[1]=f'<< /Type /Pages /Count {len(pages)} /Kids [{" ".join(str(p)+" 0 R" for p in pages)}] >>'.encode()
    data=bytearray(b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n');offsets=[0]
    for i,obj in enumerate(objects,1):
        offsets.append(len(data));data.extend(f'{i} 0 obj\n'.encode()+obj+b'\nendobj\n')
    start=len(data);data.extend(f'xref\n0 {len(objects)+1}\n0000000000 65535 f \n'.encode())
    for offset in offsets[1:]:data.extend(f'{offset:010} 00000 n \n'.encode())
    data.extend(f'trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{start}\n%%EOF\n'.encode())
    return bytes(data)
