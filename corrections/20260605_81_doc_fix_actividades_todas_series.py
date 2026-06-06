import os, re, glob, zipfile, html as html_mod
import xml.etree.ElementTree as ET

env = env  # noqa

NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

BASES = {
    'PNOGE':  '/tmp/pnoge',
    'PNODC':  '/tmp/pnodc',
    'PNOAD':  '/tmp/pnoad',
    'PNOMA':  '/tmp/pnoma',
    'PNOTV':  '/tmp/pnotv',
    'PNOAL':  '/tmp/pnoal',
    'PNOCC':  '/tmp/pnocc',
    'PNOEST': '/tmp/pnoest',
}

SOLO = os.environ.get('SERIE', '')  # filtrar por serie si se pasa

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
        html_rows.append('<tr>' + ''.join(
            f'<{tag} style="padding:4px;">' +
            ' '.join(''.join(run_to_html(r) for r in p.findall('.//w:r', NS))
                     for p in cell.findall('.//w:p', NS)).strip() +
            f'</{tag}>' for cell in cells
        ) + '</tr>')
    return ('<table border="1" style="width:100%;border-collapse:collapse;font-size:inherit;">'
            + ''.join(html_rows) + '</table>')

def cell_to_html(cell):
    result = []; in_list = False
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

def cell_plain_text(cell):
    return ''.join(t.text or '' for t in cell.findall('.//w:t', NS)).strip()

def extract_actividades(path):
    with zipfile.ZipFile(path) as zf:
        root = ET.fromstring(zf.read('word/document.xml'))
    actividades = []
    for tbl in root.findall('.//w:tbl', NS):
        rows = tbl.findall('w:tr', NS)
        if len(rows) < 2: continue
        hdr = ''.join(t.text or '' for t in rows[0].findall('.//w:t', NS)).upper()
        if 'VERSIÓN' in hdr or 'VERSION' in hdr: continue
        if not any(k in hdr for k in ('ACTIVIDAD','DESCRIPCI','PASO')): continue
        col_hdrs = [''.join(t.text or '' for t in c.findall('.//w:t', NS)).upper()
                    for c in rows[0].findall('w:tc', NS)]
        idx_act  = next((i for i,h in enumerate(col_hdrs) if 'ACTIVIDAD' in h or 'PASO' in h), 0)
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
            act_text = cell_plain_text(cells[idx_act]) if idx_act < len(cells) else ''
            seq += 1
            actividades.append({'actividad': act_text if act_text else str(seq),
                                 'descripcion': desc_html,
                                 'responsable': ch(idx_resp),
                                 'registro':    ch(idx_reg)})
        if actividades: break
    return actividades

def find_docx(serie, codigo):
    base = BASES.get(serie)
    if not base: return None
    clean = os.path.join(base, f'{codigo}.docx')
    if os.path.exists(clean): return clean
    matches = glob.glob(os.path.join(base, f'{codigo}*.docx'))
    return matches[0] if matches else None

DocModel = env['amunet.documento']
ActModel = env['amunet.documento.actividad']

docs = DocModel.search([('tipo','=','pno')])
ok = skip = falta = 0

for doc in docs:
    m = re.match(r'^(PNO[A-Z]+)', doc.codigo)
    if not m: continue
    serie = m.group(1)
    if serie not in BASES: continue
    if SOLO and serie != SOLO: continue

    path = find_docx(serie, doc.codigo)
    if not path:
        print(f'FALTA: {doc.codigo}'); falta += 1; continue
    try:
        acts = extract_actividades(path)
    except Exception as e:
        print(f'ERROR {doc.codigo}: {e}'); skip += 1; continue
    if not acts:
        print(f'SIN ACTS: {doc.codigo}'); skip += 1; continue

    doc.actividad_ids.unlink()
    for seq, a in enumerate(acts, 1):
        ActModel.create({'documento_id': doc.id, 'sequence': seq, **a})
    env.cr.commit()
    ok += 1
    print(f'OK {doc.codigo} | {len(acts)} acts')

print(f'DONE {SOLO or "ALL"} — {ok} ok | {falta} sin archivo | {skip} omitidos')
