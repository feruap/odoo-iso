import os, re, zipfile, html as html_mod
import xml.etree.ElementTree as ET

env = env  # noqa

NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

SERIES = {
    'PNOCC': '/tmp/pnocc',
    'PNOAL': '/tmp/pnoal',
}

# Documentos de cada serie
CODIGOS = {
    'PNOCC': ['PNOCC-001','PNOCC-002','PNOCC-003','PNOCC-004','PNOCC-005',
              'PNOCC-006','PNOCC-007','PNOCC-008','PNOCC-009'],
    'PNOAL': ['PNOAL-001','PNOAL-002','PNOAL-003','PNOAL-004','PNOAL-005',
              'PNOAL-006','PNOAL-007','PNOAL-008','PNOAL-010','PNOAL-011'],
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

def paras_to_html(paras):
    """Convierte lista de párrafos Word a HTML, agrupando listas."""
    result = []
    in_list = False
    for p in paras:
        h = para_to_html(p)
        if not h: continue
        if h.startswith('<li>'):
            if not in_list:
                result.append('<ul>')
                in_list = True
            result.append(h)
        else:
            if in_list:
                result.append('</ul>')
                in_list = False
            result.append(h)
    if in_list:
        result.append('</ul>')
    return ''.join(result)

def para_raw_text(p):
    return ''.join(t.text or '' for t in p.findall('.//w:t', NS)).strip()


def extract_actividades(path, serie):
    with zipfile.ZipFile(path) as zf:
        root = ET.fromstring(zf.read('word/document.xml'))

    actividades = []
    for tbl in root.findall('.//w:tbl', NS):
        rows = tbl.findall('w:tr', NS)
        if len(rows) < 2: continue
        hdr = ''.join(t.text or '' for t in rows[0].findall('.//w:t', NS)).upper()

        # Excluir tablas de Control de Cambios
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

            def cell_html(idx):
                if idx < 0 or idx >= len(cells): return ''
                return paras_to_html(cells[idx].findall('w:p', NS))

            def cell_text(idx):
                if idx < 0 or idx >= len(cells): return ''
                return ''.join(t.text or '' for t in cells[idx].findall('.//w:t', NS)).strip()

            desc_paras = cells[idx_desc].findall('w:p', NS) if idx_desc < len(cells) else []

            if serie == 'PNOAL':
                # En PNOAL: primer párrafo no vacío = nombre de la actividad,
                # el resto = descripción real
                non_empty = [p for p in desc_paras if para_raw_text(p)]
                if not non_empty: continue
                act_title = para_raw_text(non_empty[0])
                desc_paras_rest = [p for p in desc_paras[desc_paras.index(non_empty[0])+1:]]
                desc_html = paras_to_html(desc_paras_rest)
                if not act_title and not desc_html: continue
                seq += 1
                actividades.append({
                    'actividad': act_title,
                    'descripcion': desc_html,
                    'responsable': cell_html(idx_resp),
                    'registro': cell_html(idx_reg),
                })

            else:  # PNOCC y otras series
                # En PNOCC: columna ACTIVIDAD usa numeración automática (vacía en XML)
                # Usamos el número de secuencia; descripción = único párrafo de col DESCRIPCIÓN
                desc_html = paras_to_html(desc_paras)
                if not desc_html: continue
                seq += 1
                actividades.append({
                    'actividad': str(seq),
                    'descripcion': desc_html,
                    'responsable': cell_html(idx_resp),
                    'registro': cell_html(idx_reg),
                })

        if actividades:
            break  # Solo la primera tabla válida

    return actividades


DocModel = env['amunet.documento']
ActModel = env['amunet.documento.actividad']

for serie, base in SERIES.items():
    for codigo in CODIGOS[serie]:
        doc = DocModel.search([('codigo', '=', codigo)], limit=1)
        if not doc:
            print(f'NO ENCONTRADO: {codigo}'); continue

        path = os.path.join(base, f'{codigo}.docx')
        if not os.path.exists(path):
            print(f'FALTA DOCX: {path}'); continue

        acts = extract_actividades(path, serie)

        doc.actividad_ids.unlink()
        for seq, a in enumerate(acts, 1):
            ActModel.create({'documento_id': doc.id, 'sequence': seq, **a})

        env.cr.commit()
        print(f'OK {codigo} | {len(acts)} actividades')

print('DONE')
