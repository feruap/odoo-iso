import sys, os, zipfile, re
import xml.etree.ElementTree as ET

env = env  # noqa

NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

BASE = '/tmp/pnoal'

TITLES = {
    'PNOAL-001': 'CONTROL DE ALMACENES DE INSUMOS',
    'PNOAL-002': 'SOLICITUD DE ADQUISICIÓN, RECEPCIÓN, RESGUARDO, ANÁLISIS Y SURTIDO DE INSUMOS',
    'PNOAL-003': 'MANTENIMIENTO, LIMPIEZA Y SANITIZACIÓN DE ALMACENES',
    'PNOAL-004': 'GESTIÓN DEL MUSEO DE RETENCIÓN',
    'PNOAL-005': 'ASIGNACIÓN DE CLAVE Y LOTE INTERNO',
    'PNOAL-006': 'MANEJO DE RESIDUOS Y PRODUCTO RECHAZADO',
    'PNOAL-007': 'CONTROL DE REACTIVOS',
    'PNOAL-008': 'CONTROL DE TEMPERATURA Y HUMEDAD',
    'PNOAL-010': 'ASIGNACIÓN DE CLAVE Y LOTE INTERNO (PNOAL-010)',
    'PNOAL-011': 'REINGRESO DE MATERIA PRIMA Y MATERIAL DE EMPAQUE',
}

# Sections that mark end of responsabilidades
NEXT_SECTION_RE = re.compile(
    r'^(TÉRMINOS|TERMINOS|CONDICIONES GENERALES|DESARROLLO DEL PROCESO|FORMATOS DERIVADOS|'
    r'REFERENCIAS|ANEXOS|CONTROL DE CAMBIOS|FIRMAS)',
    re.I
)

ROL_RE = re.compile(r'^(De |Del |De la )', re.I)


def parse_responsabilidades(zf):
    root = ET.fromstring(zf.read('word/document.xml'))
    paragraphs = root.findall('.//w:p', NS)
    texts = [
        ''.join(r.text or '' for r in p.findall('.//w:t', NS)).strip()
        for p in paragraphs
    ]

    # Find the UPPERCASE "RESPONSABILIDADES" heading (skip index/TOC lowercase version)
    start = None
    for i, t in enumerate(texts):
        if t == 'RESPONSABILIDADES':
            start = i + 1
            break
    if start is None:
        return []

    # Collect until next major uppercase section
    section_texts = []
    for t in texts[start:]:
        if NEXT_SECTION_RE.match(t):
            break
        if t:
            section_texts.append(t)

    # Group: lines starting with "De /Del /..." that are short (<= 60 chars) are ROL headers
    responsabilidades = []
    current_rol = None
    current_desc = []

    for t in section_texts:
        is_rol = ROL_RE.match(t) and len(t) <= 60
        if is_rol:
            if current_rol:
                responsabilidades.append({
                    'rol': current_rol,
                    'descripcion': ' '.join(current_desc),
                })
            current_rol = t
            current_desc = []
        elif current_rol:
            current_desc.append(t)

    if current_rol:
        responsabilidades.append({
            'rol': current_rol,
            'descripcion': ' '.join(current_desc),
        })

    return responsabilidades


DocModel = env['amunet.documento']
RespModel = env['amunet.documento.responsabilidad']

for codigo, titulo in TITLES.items():
    doc = DocModel.search([('codigo', '=', codigo)], limit=1)
    if not doc:
        print(f'NO ENCONTRADO: {codigo}')
        continue

    doc.write({'name': titulo})
    doc.responsabilidad_ids.unlink()

    fname = f'{codigo}.docx'
    path = os.path.join(BASE, fname)
    if not os.path.exists(path):
        print(f'FALTA DOCX: {path}')
        continue

    with zipfile.ZipFile(path) as zf:
        responsabilidades = parse_responsabilidades(zf)

    for seq, r in enumerate(responsabilidades, 1):
        RespModel.create({
            'documento_id': doc.id,
            'sequence': seq,
            'rol': r['rol'],
            'descripcion': r['descripcion'],
        })

    env.cr.commit()
    print(f'OK {codigo} | {titulo[:50]} | {len(responsabilidades)} resp')

print('DONE')
