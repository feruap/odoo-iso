import os, re, zipfile, glob
import xml.etree.ElementTree as ET
from datetime import date

env = env  # noqa

NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

MESES = {
    'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4, 'may': 5, 'jun': 6,
    'jul': 7, 'ago': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dic': 12,
}

BASES = {
    'PNOGE': '/tmp/pnoge',
    'PNODC': '/tmp/pnodc',
    'PNOAD': '/tmp/pnoad',
    'PNOMA': '/tmp/pnoma',
    'PNOTV': '/tmp/pnotv',
    'PNOAL': '/tmp/pnoal',
}

# Nombre limpio del archivo por codigo
FILE_MAP = {}
for serie, base in BASES.items():
    if not os.path.isdir(base):
        continue
    for f in os.listdir(base):
        if not f.endswith('.docx'):
            continue
        # Extraer código del nombre de archivo
        m = re.match(r'(PNO[A-Z]+-\d+)', f)
        if m:
            FILE_MAP[m.group(1)] = os.path.join(base, f)


def parse_iso(s):
    """Convierte 'Abr.2025', 'Jul. 2024', '2024-07-01', 'Jul.2024' a 'YYYY-MM-DD'."""
    s = s.strip().replace('\xa0', ' ')
    # Ya en formato ISO
    m = re.match(r'^(\d{4})-(\d{2})-(\d{2})$', s)
    if m:
        return s
    # Formato YYYY
    m = re.match(r'^(\d{4})$', s)
    if m:
        return f'{m.group(1)}-01-01'
    # Formato mes.año o mes año
    m = re.match(r'^([A-Za-záéíóúñ]+)[\.\s]+(\d{4})$', s.strip())
    if m:
        mes_str = m.group(1)[:3].lower()
        mes = MESES.get(mes_str)
        if mes:
            return f'{m.group(2)}-{mes:02d}-01'
    return None


def get_dates_from_header(path):
    """Devuelve (fecha_emision, fecha_vigencia) del encabezado del DOCX."""
    with zipfile.ZipFile(path) as zf:
        headers = sorted(n for n in zf.namelist() if n.startswith('word/header') and n.endswith('.xml'))
        texts = []
        for h in headers:
            root = ET.fromstring(zf.read(h))
            for para in root.findall('.//w:p', NS):
                t = ''.join(r.text or '' for r in para.findall('.//w:t', NS)).strip()
                if t:
                    texts.append(t)

    fecha_emision = None
    fecha_vigencia = None

    for i, t in enumerate(texts):
        tl = t.lower().strip()
        # "Vigente a partir de:" → siguiente token es la fecha
        if re.search(r'vigente\s+a\s+partir', tl):
            # La fecha puede estar en el mismo texto después de ':' o en el siguiente
            after = re.split(r':\s*', t, maxsplit=1)
            candidate = after[1].strip() if len(after) > 1 and after[1].strip() else (texts[i+1] if i+1 < len(texts) else '')
            parsed = parse_iso(candidate)
            if parsed:
                fecha_emision = parsed
        # "Próxima Revisión:" o "Próxima revisión:"
        elif re.search(r'próxima\s+revis', tl) or re.search(r'proxima\s+revis', tl):
            after = re.split(r':\s*', t, maxsplit=1)
            candidate = after[1].strip() if len(after) > 1 and after[1].strip() else (texts[i+1] if i+1 < len(texts) else '')
            parsed = parse_iso(candidate)
            if parsed:
                fecha_vigencia = parsed
        # Fecha simple como "dd/mm/yyyy" o año solo
        elif re.match(r'^\d{2}/\d{2}/\d{4}$', t) and not fecha_emision:
            parts = t.split('/')
            fecha_emision = f'{parts[2]}-{parts[1]}-{parts[0]}'

    return fecha_emision, fecha_vigencia


DocModel = env['amunet.documento']
docs = DocModel.search([])
updated = 0
sin_archivo = 0
sin_fechas = 0

for doc in docs:
    path = FILE_MAP.get(doc.codigo)
    if not path:
        sin_archivo += 1
        continue

    try:
        fe, fv = get_dates_from_header(path)
    except Exception as e:
        print(f'ERROR {doc.codigo}: {e}')
        continue

    vals = {}
    if fe:
        vals['fecha_emision'] = fe
    if fv:
        vals['fecha_vigencia'] = fv

    if vals:
        doc.write(vals)
        updated += 1
        print(f'OK {doc.codigo} | emision={fe} | vigencia={fv}')
    else:
        sin_fechas += 1
        print(f'SIN FECHA {doc.codigo}')

env.cr.commit()
print(f'\nDONE — {updated} actualizados | {sin_archivo} sin archivo | {sin_fechas} sin fechas')
