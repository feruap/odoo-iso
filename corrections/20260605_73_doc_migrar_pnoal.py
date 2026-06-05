import sys, os, zipfile, re, html
import xml.etree.ElementTree as ET

env = env  # noqa: Odoo shell

NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

DOCS = {
    'PNOAL-001': ('PNOAL-001.docx', 'AL'),
    'PNOAL-002': ('PNOAL-002.docx', 'AL'),
    'PNOAL-003': ('PNOAL-003.docx', 'AL'),
    'PNOAL-004': ('PNOAL-004.docx', 'AL'),
    'PNOAL-005': ('PNOAL-005.docx', 'AL'),
    'PNOAL-006': ('PNOAL-006.docx', 'AL'),
    'PNOAL-007': ('PNOAL-007.docx', 'AL'),
    'PNOAL-008': ('PNOAL-008.docx', 'AL'),
    'PNOAL-010': ('PNOAL-010.docx', 'AL'),
    'PNOAL-011': ('PNOAL-011.docx', 'AL'),
}

BASE = '/tmp/pnoal'


def get_header_vals(zf):
    headers = sorted(n for n in zf.namelist() if n.startswith('word/header') and n.endswith('.xml'))
    vals = {'codigo': '', 'titulo': '', 'version': '', 'sustituye': '', 'fecha_emision': ''}
    for h in headers:
        root = ET.fromstring(zf.read(h))
        texts = []
        for para in root.findall('.//w:p', NS):
            t = ''.join(r.text or '' for r in para.findall('.//w:t', NS)).strip()
            if t:
                texts.append(t)
        for i, t in enumerate(texts):
            if re.match(r'^PNO[A-Z]+-\d+', t):
                vals['codigo'] = t.strip()
            elif re.match(r'^\d{2}$', t) and not vals['version']:
                vals['version'] = t.strip()
            elif re.match(r'^\d{2}/\d{2}/\d{4}$', t) and not vals['fecha_emision']:
                vals['fecha_emision'] = t.strip()
            elif re.match(r'^0\d$', t) and vals['version'] and not vals['sustituye']:
                vals['sustituye'] = t.strip()
        # Título: línea larga en mayúsculas
        for t in texts:
            if len(t) > 15 and t == t.upper() and re.search(r'[A-ZÁÉÍÓÚÑ]{4}', t):
                if not vals['titulo']:
                    vals['titulo'] = t.strip()
    return vals


def para_to_html(para_elem):
    runs = []
    for r in para_elem.findall('.//w:r', NS):
        rpr = r.find('w:rPr', NS)
        text = ''.join((t.text or '') for t in r.findall('w:t', NS))
        if not text:
            continue
        text = html.escape(text)
        if rpr is not None:
            if rpr.find('w:b', NS) is not None:
                text = f'<strong>{text}</strong>'
            if rpr.find('w:i', NS) is not None:
                text = f'<em>{text}</em>'
        runs.append(text)
    return ''.join(runs).strip()


def parse_actividades(zf):
    root = ET.fromstring(zf.read('word/document.xml'))
    tables = root.findall('.//w:tbl', NS)
    actividades = []
    for tbl in tables:
        rows = tbl.findall('w:tr', NS)
        if len(rows) < 2:
            continue
        header_cells = [
            ''.join(t.text or '' for t in row.findall('.//w:t', NS)).strip().upper()
            for row in rows[:1]
            for cell in row.findall('w:tc', NS)
            for t in [cell]
        ]
        header_text = ' '.join(
            ''.join(t.text or '' for t in cell.findall('.//w:t', NS)).strip().upper()
            for cell in rows[0].findall('w:tc', NS)
        )
        if not any(k in header_text for k in ('ACTIVIDAD', 'DESCRIPCI', 'RESPONSABLE', 'PASO')):
            continue
        # Map column positions
        col_headers = [
            ''.join(t.text or '' for t in cell.findall('.//w:t', NS)).strip().upper()
            for cell in rows[0].findall('w:tc', NS)
        ]
        idx_act = next((i for i, h in enumerate(col_headers) if 'ACTIVIDAD' in h or 'PASO' in h or 'No.' in h.upper()), 0)
        idx_desc = next((i for i, h in enumerate(col_headers) if 'DESCRIPCI' in h or 'PROCEDIMIENTO' in h), 1)
        idx_resp = next((i for i, h in enumerate(col_headers) if 'RESPONSABLE' in h), -1)
        idx_reg = next((i for i, h in enumerate(col_headers) if 'REGISTRO' in h or 'EVIDENCIA' in h), -1)
        for row in rows[1:]:
            cells = row.findall('w:tc', NS)
            if not cells:
                continue
            def cell_html(idx):
                if idx < 0 or idx >= len(cells):
                    return ''
                paras = cells[idx].findall('w:p', NS)
                parts = [para_to_html(p) for p in paras]
                return '<br/>'.join(p for p in parts if p)
            act = cell_html(idx_act)
            desc = cell_html(idx_desc)
            resp = cell_html(idx_resp)
            reg = cell_html(idx_reg)
            if act or desc:
                actividades.append({'actividad': act, 'descripcion': desc,
                                    'responsable': resp, 'registro': reg})
    return actividades


def parse_resp_term(zf):
    root = ET.fromstring(zf.read('word/document.xml'))
    tables = root.findall('.//w:tbl', NS)
    responsabilidades, terminos = [], []
    for tbl in tables:
        rows = tbl.findall('w:tr', NS)
        if not rows:
            continue
        header_text = ''.join(
            t.text or '' for t in rows[0].findall('.//w:t', NS)
        ).strip().upper()
        if 'RESPONSABILIDAD' in header_text or 'ROL' in header_text or 'PUESTO' in header_text:
            for row in rows[1:]:
                cells = row.findall('w:tc', NS)
                if len(cells) >= 2:
                    rol = ''.join(t.text or '' for t in cells[0].findall('.//w:t', NS)).strip()
                    desc = ''.join(t.text or '' for t in cells[1].findall('.//w:t', NS)).strip()
                    if rol:
                        responsabilidades.append({'rol': rol, 'descripcion': desc})
        elif any(k in header_text for k in ('TÉRMINO', 'TERMINO', 'DEFINICI', 'CONCEPTO', 'GLOSARIO')):
            for row in rows[1:]:
                cells = row.findall('w:tc', NS)
                if len(cells) >= 2:
                    concepto = ''.join(t.text or '' for t in cells[0].findall('.//w:t', NS)).strip()
                    definicion = ''.join(t.text or '' for t in cells[1].findall('.//w:t', NS)).strip()
                    if concepto:
                        terminos.append({'concepto': concepto, 'definicion': definicion})
    return responsabilidades, terminos


DocModel = env['amunet.documento']
ActModel = env['amunet.documento.actividad']
RespModel = env['amunet.documento.responsabilidad']
TermModel = env['amunet.documento.termino']

for codigo, (fname, area) in DOCS.items():
    path = os.path.join(BASE, fname)
    if not os.path.exists(path):
        print(f'FALTA: {path}')
        continue

    existing = DocModel.search([('codigo', '=', codigo)])
    if existing:
        print(f'YA EXISTE {codigo}, omitiendo')
        continue

    with zipfile.ZipFile(path) as zf:
        hv = get_header_vals(zf)
        actividades = parse_actividades(zf)
        responsabilidades, terminos = parse_resp_term(zf)

    titulo = hv['titulo'] or codigo
    version = hv['version'] or '01'

    doc = DocModel.create({
        'codigo': codigo,
        'name': titulo,
        'tipo': 'pno',
        'area': area,
        'version_actual': version,
        'state': 'borrador',
        'elabora_id': 1,
        'company_id': 1,
        'fecha_emision': '2024-01-01',
    })

    for seq, a in enumerate(actividades, 1):
        ActModel.create({
            'documento_id': doc.id,
            'sequence': seq,
            'actividad': a['actividad'],
            'descripcion': a['descripcion'],
            'responsable': a['responsable'],
            'registro': a['registro'],
        })

    for seq, r in enumerate(responsabilidades, 1):
        RespModel.create({
            'documento_id': doc.id,
            'sequence': seq,
            'rol': r['rol'],
            'descripcion': r['descripcion'],
        })

    for seq, t in enumerate(terminos, 1):
        TermModel.create({
            'documento_id': doc.id,
            'sequence': seq,
            'concepto': t['concepto'],
            'definicion': t['definicion'],
        })

    env.cr.commit()
    print(f'OK {codigo} | {titulo[:55]} | v{version} | {len(actividades)} acts | {len(responsabilidades)} resp | {len(terminos)} terms')

print('DONE')
