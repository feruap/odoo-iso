import os, re, glob, zipfile
import xml.etree.ElementTree as ET

env = env  # noqa

NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

BASES = {
    'PNOAL':  '/tmp/pnoal',
    'PNOCC':  '/tmp/pnocc',
    'PNOEST': '/tmp/pnoest',
}

def get_sustituye(path):
    with zipfile.ZipFile(path) as zf:
        headers = sorted(n for n in zf.namelist() if n.startswith('word/header') and n.endswith('.xml'))
        texts = []
        for h in headers:
            root = ET.fromstring(zf.read(h))
            for para in root.findall('.//w:p', NS):
                t = ''.join(r.text or '' for r in para.findall('.//w:t', NS)).strip()
                if t:
                    texts.append(t)

    for i, t in enumerate(texts):
        if re.search(r'sustituye\s+a', t, re.I):
            # puede venir en el mismo texto "Sustituye a: 01" o en el siguiente
            after = re.split(r':\s*', t, maxsplit=1)
            cand = after[1].strip() if len(after) > 1 and after[1].strip() else ''
            if not cand and i + 1 < len(texts):
                cand = texts[i + 1].strip()
            # validar que sea un número de versión (ej. "01", "02", "1", "2")
            if re.match(r'^\d{1,3}$', cand):
                return cand.zfill(2)
    return None

def find_docx(serie, codigo):
    base = BASES.get(serie)
    if not base: return None
    clean = os.path.join(base, f'{codigo}.docx')
    if os.path.exists(clean): return clean
    matches = glob.glob(os.path.join(base, f'{codigo}*.docx'))
    return matches[0] if matches else None

DocModel = env['amunet.documento']
ok = sin_dato = falta = 0

docs = DocModel.search([('tipo', '=', 'pno'), ('sustituye_version', '=', False)])
for doc in docs:
    m = re.match(r'^(PNO[A-Z]+)', doc.codigo)
    if not m or m.group(1) not in BASES:
        continue

    serie = m.group(1)
    path = find_docx(serie, doc.codigo)
    if not path:
        print(f'FALTA: {doc.codigo}'); falta += 1; continue

    val = get_sustituye(path)
    if val:
        doc.write({'sustituye_version': val})
        env.cr.commit()
        print(f'OK {doc.codigo} | v{doc.version_actual} sustituye a {val}')
        ok += 1
    else:
        print(f'SIN DATO: {doc.codigo}')
        sin_dato += 1

print(f'\nDONE — {ok} actualizados | {sin_dato} sin dato en Word | {falta} sin archivo')
