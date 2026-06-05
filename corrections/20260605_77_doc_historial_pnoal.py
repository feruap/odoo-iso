import re, zipfile
import xml.etree.ElementTree as ET

env = env  # noqa

NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

DOCS = [
    'PNOAL-001', 'PNOAL-002', 'PNOAL-003', 'PNOAL-004', 'PNOAL-005',
    'PNOAL-006', 'PNOAL-007', 'PNOAL-008', 'PNOAL-010', 'PNOAL-011',
]

BASE = '/tmp/pnoal'

DocModel = env['amunet.documento']
VerModel = env['amunet.documento.version']


def parse_historial(zf):
    root = ET.fromstring(zf.read('word/document.xml'))
    tables = root.findall('.//w:tbl', NS)
    historial = []
    for tbl in tables:
        rows = tbl.findall('w:tr', NS)
        if not rows:
            continue
        header = ''.join(t.text or '' for t in rows[0].findall('.//w:t', NS)).upper()
        if 'VERSIÓN' not in header and 'VERSION' not in header:
            continue
        if 'DESCRIPCIÓN' not in header and 'DESCRIPCION' not in header:
            continue
        col_headers = [
            ''.join(t.text or '' for t in cell.findall('.//w:t', NS)).strip().upper()
            for cell in rows[0].findall('w:tc', NS)
        ]
        idx_ver = next((i for i, h in enumerate(col_headers) if 'VERSIÓN' in h or 'VERSION' in h), 0)
        idx_fecha = next((i for i, h in enumerate(col_headers) if 'FECHA' in h), 1)
        idx_desc = next((i for i, h in enumerate(col_headers) if 'DESCRIPCIÓN' in h or 'DESCRIPCION' in h), 2)
        idx_just = next((i for i, h in enumerate(col_headers) if 'JUSTIFIC' in h), -1)

        for row in rows[1:]:
            cells = row.findall('w:tc', NS)

            def cell_text(idx):
                if idx < 0 or idx >= len(cells):
                    return ''
                return ''.join(t.text or '' for t in cells[idx].findall('.//w:t', NS)).strip()

            ver = cell_text(idx_ver)
            if not re.match(r'^\d', ver):
                continue
            historial.append({
                'version': ver.zfill(2),
                'fecha': cell_text(idx_fecha),
                'descripcion': cell_text(idx_desc),
                'justificacion': cell_text(idx_just),
            })
        break
    return historial


total = 0
for codigo in DOCS:
    doc = DocModel.search([('codigo', '=', codigo)], limit=1)
    if not doc:
        print(f'NO ENCONTRADO: {codigo}')
        continue

    fname = f'{codigo}.docx'
    path = f'{BASE}/{fname}'
    try:
        with zipfile.ZipFile(path) as zf:
            historial = parse_historial(zf)
    except Exception as e:
        print(f'ERROR {codigo}: {e}')
        continue

    version_actual = doc.version_actual or '01'

    for h in historial:
        state_h = 'vigente' if h['version'] == version_actual else 'obsoleto'
        existing = VerModel.search([('documento_id', '=', doc.id), ('version', '=', h['version'])], limit=1)
        if existing:
            continue
        VerModel.create({
            'documento_id': doc.id,
            'version': h['version'],
            'fecha': '2024-01-01',
            'cambios': h['descripcion'] or 'Ver documento',
            'descripcion_cambio': h['descripcion'],
            'justificacion': h['justificacion'],
            'state_historico': state_h,
        })
        total += 1

    env.cr.commit()
    print(f'OK {codigo} | {len(historial)} versiones en historial')

print(f'DONE — {total} registros de historial creados')
