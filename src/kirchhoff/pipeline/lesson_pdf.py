"""PDF vettoriale autonomo, dai medesimi snapshot SVG della lezione.

Supporta soltanto il vocabolario del nostro renderer, non SVG arbitrari.
Il font PDF standard usa traslitterazioni esplicite per simboli non WinAnsi.
Nessuna dipendenza di sistema, rete o processo di stampa.
"""
import re
import textwrap
import xml.etree.ElementTree as ET

from kirchhoff.pipeline.lesson_pdf_math import actual_text, draw_box, equation_boxes
from kirchhoff.pipeline.lesson_math import equation_text
from kirchhoff.runtime_identity import assert_runtime_current


def _plain(s):
    for a, b in {'Ω':'ohm', 'Σ':'Somma', '→':'->', '−':'-', '×':'x', '‖':' || ', '≠':'!=', 'Δ':'Delta', '…':'...', '∠':'angolo', 'ω':'omega', 'δ':'delta'}.items():
        s = s.replace(a, b)
    return s.encode('cp1252', 'replace').decode('cp1252')


def _literal(s):
    return _plain(str(s)).replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')


def _text(x, y, text, size=11, font='F1'):
    return f'BT /{font} {size} Tf 1 0 0 1 {x:.2f} {y:.2f} Tm ({_literal(text)}) Tj ET\n'


def _rgb(color):
    if color == 'white':
        return '1 1 1'
    if not re.fullmatch(r'#[0-9a-fA-F]{6}', color):
        return '0.14 0.20 0.29'
    return ' '.join(str(int(color[i:i+2],16)/255) for i in (1,3,5))


def _drawing(svg, ytop=727, max_height=320):
    root = ET.fromstring(svg)
    _, _, w, h = map(float, root.attrib['viewBox'].split())
    scale = min(510/w, max_height/h)
    xoff = (595-w*scale)/2
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
            # Le bobine usano C: conservarne i controlli evita di trasformare
            # silenziosamente una curva in segmenti con coordinate sbagliate.
            parts = re.findall(r'[A-Za-z]|-?\d+(?:\.\d+)?', a['d'])
            i = 0
            while i < len(parts):
                command = parts[i]
                if command not in {'M', 'L', 'C'}:
                    raise ValueError(f'Comando SVG non supportato dal PDF: {command}.')
                count = 6 if command == 'C' else 2
                coords = parts[i+1:i+1+count]
                if len(coords) != count:
                    raise ValueError('Coordinate SVG incomplete per il PDF.')
                points = [xy(coords[j], coords[j+1]) for j in range(0, count, 2)]
                result += ' '.join(f'{px:.3f} {py:.3f}' for px, py in points)
                result += f' {dict(M="m", L="l", C="c")[command]}\n'
                i += 1 + count
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
    assert_runtime_current()
    if lesson.get('outcome') != 'solved':
        raise ValueError('Il PDF richiede una lezione risolta.')
    objects = [b'', b'', b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>',
               b'<< /Type /Font /Subtype /Type1 /BaseFont /Times-Roman /Encoding /WinAnsiEncoding >>',
               b'<< /Type /Font /Subtype /Type1 /BaseFont /Times-Italic /Encoding /WinAnsiEncoding >>',
               b'<< /Type /Font /Subtype /Type1 /BaseFont /Symbol >>']
    pages=[]
    def page(stream):
        revision = lesson.get('lesson_build', '')[:12]
        source = lesson.get('fingerprint', '')[:12]
        if revision or source:
            stream += _text(42,20,f'Revisione {revision or "non disponibile"} / input {source or "non disponibile"}',8)
        content=stream.encode('cp1252','replace');content_id=len(objects)+1
        objects.append(f'<< /Length {len(content)} >>\nstream\n'.encode()+content+b'endstream')
        page_id=len(objects)+1
        objects.append(f'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 3 0 R /F2 4 0 R /F3 5 0 R /F4 6 0 R >> >> /Contents {content_id} 0 R >>'.encode())
        pages.append(page_id)
    # La prima pagina orienta lo studio: domanda, originale e percorso effettivo.
    stream='0.14 0.20 0.29 rg\n'+_text(42,800,'KIRCHHOFF / con Andrea Marro',10)
    stream+=_text(42,757,'Il circuito, passo per passo.',29,'F2')
    stream+=_text(42,730,lesson['title']+' / riferimento '+lesson['answer']['reference'],12)
    drawing,y=_drawing(lesson['original'],ytop=699,max_height=265);stream+=drawing
    stream+='0.16 0.27 0.68 rg\n'+_text(42,y,'IL PERCORSO DEL RAGIONAMENTO',10)+'0.14 0.20 0.29 rg\n';y-=25
    provenance=lesson.get('input_provenance')
    if provenance:
        # La ricevuta e' sul PDF ma la fotografia resta fuori dal documento.
        stream+=_text(42,60,'Foto SHA256: '+provenance['source_sha256'],8)
        stream+=_text(42,49,'Circuito confermato SHA256: '+provenance['circuit_sha256'],8)
    for i,step in enumerate(lesson['steps']):
        for line in textwrap.wrap(f'{i+1:02d}  '+_plain(step['title']),80):
            if y<80:
                stream+=_text(42,35,'Il percorso - continua',9);page(stream)
                stream='0.14 0.20 0.29 rg\n'+_text(42,790,'Il percorso del ragionamento',20,'F2');y=755
            stream+=_text(42,y,line,11);y-=16
        y-=7
    stream+=_text(42,35,'Schemi e calcoli provengono dalla stessa lezione. Conserva i riferimenti indicati.',9)
    page(stream)
    for i, step in enumerate(lesson['steps']):
        if 'math' in step and step['equations'] != [equation_text(expr) for expr in step['math']]:
            raise ValueError('Le formule del PDF non coincidono con le equazioni della lezione.')
        stream='0.14 0.20 0.29 rg\n'+_text(42,800,f'KIRCHHOFF / PASSAGGIO {i+1:02d}',10)
        title=textwrap.wrap(_plain(step['title']),62)
        for j,line in enumerate(title): stream+=_text(42,771-j*20,line,19,'F2')
        drawing,y=_drawing(step['svg']);stream+=drawing
        paragraphs = [(step['explanation'], None)] + ([(None,expr) for expr in step['math']] if 'math' in step else [(text,None) for text in step['equations']])
        for index, (paragraph,expr) in enumerate(paragraphs):
            if index in (0,1):
                if y<105:
                    page(stream);stream='0.14 0.20 0.29 rg\n';y=770
                stream+='0.16 0.27 0.68 rg\n'+_text(42,y,'IL RAGIONAMENTO' if index==0 else 'IL CALCOLO',9)+'0.14 0.20 0.29 rg\n';y-=22
            if expr is not None:
                stream += f'/Span << /ActualText <{actual_text(expr)}> >> BDC\n'
                for box in equation_boxes(expr):
                    if y-box.above-box.below<70:
                        stream+='EMC\n'+_text(42,35,f'Passaggio {i+1} - continua',9);page(stream)
                        stream='0.14 0.20 0.29 rg\n'+_text(42,790,step['title']+' (continua)',13);y=758
                        stream += f'/Span << /ActualText <{actual_text(expr)}> >> BDC\n'
                    baseline=y-box.above
                    stream+=draw_box(box,42,baseline,_literal)
                    y=baseline-box.below-10
                stream+='EMC\n';y-=5
                continue
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
    def metadata_text(value):
        return '<FEFF'+str(value).encode('utf-16-be').hex().upper()+'>'
    info_id=len(objects)+1
    subject = ('Revisione: '+lesson.get('lesson_build','non disponibile')+'; input: '+lesson.get('fingerprint','non disponibile')
               +'; source_sha: '+lesson.get('source_sha','non disponibile')+'; verifica: '+lesson.get('verification',{}).get('lesson','non disponibile'))
    objects.append(('<< /Title '+metadata_text(lesson['title'])+' /Author '+metadata_text('Kirchhoff / con Andrea Marro')
                    +' /Subject '+metadata_text(subject)+' /Producer (Kirchhoff - AST vettoriale) >>').encode())
    data=bytearray(b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n');offsets=[0]
    for i,obj in enumerate(objects,1):
        offsets.append(len(data));data.extend(f'{i} 0 obj\n'.encode()+obj+b'\nendobj\n')
    start=len(data);data.extend(f'xref\n0 {len(objects)+1}\n0000000000 65535 f \n'.encode())
    for offset in offsets[1:]:data.extend(f'{offset:010} 00000 n \n'.encode())
    data.extend(f'trailer\n<< /Size {len(objects)+1} /Root 1 0 R /Info {info_id} 0 R >>\nstartxref\n{start}\n%%EOF\n'.encode())
    return bytes(data)
