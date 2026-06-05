import os, re, zipfile, html as html_mod
import xml.etree.ElementTree as ET

env = env  # noqa

NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

# Todas las series que tienen ACTIVIDAD vacía (no PNOGE/PNODC/PNOMA/PNOTV/PNOAD)
SERIES = {
    'PNOAL':  ('/tmp/pnoal',  ['PNOAL-001','PNOAL-002','PNOAL-003','PNOAL-004','PNOAL-005',
                                'PNOAL-006','PNOAL-007','PNOAL-008','PNOAL-010','PNOAL-011']),
    'PNOCC':  ('/tmp/pnocc',  ['PNOCC-001','PNOCC-002','PNOCC-003','PNOCC-004','PNOCC-005',
                                'PNOCC-006','PNOCC-007','PNOCC-008','PNOCC-009']),
    'PNOEST': ('/tmp/pnoest', ['PNOEST-001','PNOEST-002','PNOEST-003','PNOEST-004','PNOEST-005']),
}

# ── Helpers HTML ─────────────────────────────────────────────────────────────
def run_to_html(r):
    rpr = r.find('w:rPr', NS)
    text = html_mod.escape(''.join((t.text or '') for t in r.findall('w:t', NS)))
    if not text: return ''
    if rpr is not None:
        if rpr.find('w:b', NS) is not None: text = f'<strong>{text}</strong>'
        if rpr.find('w:i', NS) is not None: text = f'<em>{text}</em>'
    return text

def para_to_html(p):
    runs = ''.join(run_to_html(r) for r in p.findall('.//w:r', NS))
    if not runs.strip(): return ''
    ppr = p.find('w:pPr', NS)
    if ppr is not None and ppr.find('w:numPr', NS) is not None:
        return f'<li>{runs}</li>'
    return f'<p>{runs}</p>'

def table_to_html(tbl):
    rows = tbl.findall('w:tr', NS)
    if not rows: return ''
    html_rows = []
    for i, row in enumerate(rows):
        cells = row.findall('w:tc', NS)
        tag = 'th' if i == 0 else 'td'
        cell_html = ''.join(
            f'<{tag} style="padding:4px;">' +
            ' '.join(''.join(run_to_html(r) for r in p.findall('.//w:r', NS))
                     for p in cell.findall('.//w:p', NS)).strip() +
            f'</{tag}>'
            for cell in cells
        )
        html_rows.append(f'<tr>{cell_html}</tr>')
    return ('<table border="1" style="width:100%;border-collapse:collapse;font-size:inherit;">'
            + ''.join(html_rows) + '</table>')

def cell_to_html(cell):
    """Convierte la celda en HTML respetando el orden de párrafos Y tablas anidadas."""
    result = []
    in_list = False
    for child in cell:
        tag = child.tag.split('}')[-1]
        if tag == 'p':
            h = para_to_html(child)
            if not h: continue
            if h.startswith('<li>'):
                if not in_list: result.append('<ul>'); in_list = True
                result.append(h)
            else:
                if in_list: result.append('</ul>'); in_list = False
                result.append(h)
        elif tag == 'tbl':
            if in_list: result.append('</ul>'); in_list = False
            th = table_to_html(child)
            if th: result.append(th)
    if in_list: result.append('</ul>')
    return ''.join(result)


def extract_actividades(path):
    with zipfile.ZipFile(path) as zf:
        root = ET.fromstring(zf.read('word/document.xml'))

    actividades = []
    for tbl in root.findall('.//w:tbl', NS):
        rows = tbl.findall('w:tr', NS)
        if len(rows) < 2: continue
        hdr = ''.join(t.text or '' for t in rows[0].findall('.//w:t', NS)).upper()
        if 'VERSIÓN' in hdr or 'VERSION' in hdr: continue
        if not any(k in hdr for k in ('ACTIVIDAD', 'DESCRIPCI', 'PASO')): continue

        col_hdrs = [''.join(t.text or '' for t in c.findall('.//w:t', NS)).upper()
                    for c in rows[0].findall('w:tc', NS)]
        idx_desc = next((i for i,h in enumerate(col_hdrs) if 'DESCRIPCI' in h or 'PROCEDIM' in h), 1)
        idx_resp = next((i for i,h in enumerate(col_hdrs) if 'RESPONSABLE' in h), -1)
        idx_reg  = next((i for i,h in enumerate(col_hdrs) if 'REGISTRO' in h or 'EVIDENCIA' in h), -1)

        seq = 0
        for row in rows[1:]:
            cells = row.findall('w:tc', NS)
            if not cells: continue

            def ch(idx):
                if idx < 0 or idx >= len(cells): return ''
                return cell_to_html(cells[idx])

            desc_html = ch(idx_desc)
            if not desc_html: continue
            seq += 1
            actividades.append({
                'actividad': str(seq),
                'descripcion': desc_html,
                'responsable': ch(idx_resp),
                'registro': ch(idx_reg),
            })

        if actividades: break
    return actividades


DocModel = env['amunet.documento']
ActModel = env['amunet.documento.actividad']

for serie, (base, codigos) in SERIES.items():
    for codigo in codigos:
        doc = DocModel.search([('codigo', '=', codigo)], limit=1)
        if not doc:
            print(f'NO ENCONTRADO: {codigo}'); continue

        path = os.path.join(base, f'{codigo}.docx')
        if not os.path.exists(path):
            print(f'FALTA: {path}'); continue

        acts = extract_actividades(path)
        doc.actividad_ids.unlink()
        for seq, a in enumerate(acts, 1):
            ActModel.create({'documento_id': doc.id, 'sequence': seq, **a})

        env.cr.commit()
        print(f'OK {codigo} | {len(acts)} actividades')

print('DONE')
