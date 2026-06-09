import zipfile, base64, html as html_mod, xml.etree.ElementTree as ET
from markupsafe import Markup

path = '/tmp/pnoge/PNOGE-010 Etiquetas de identificación.docx'
W  = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
R  = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
BLIP = '{http://schemas.openxmlformats.org/drawingml/2006/main}blip'

with zipfile.ZipFile(path) as zf:
    rels = ET.fromstring(zf.read('word/_rels/document.xml.rels'))
    rmap = {r.get('Id'): r.get('Target') for r in rels if 'image' in r.get('Type','')}

    def img_tag(filename):
        full_path = f'word/{filename}' if not filename.startswith('word/') else filename
        data = base64.b64encode(zf.read(full_path)).decode('ascii')
        return Markup(
            f'<img src="data:image/png;base64,{data}" '
            f'style="max-width:100%;height:auto;display:block;margin:8px 0;" alt=""/>'
        )

    def cell_to_html(cell):
        parts = []
        for p in cell.findall(f'.//{{{W}}}p'):
            runs = []
            for r in p.findall(f'.//{{{W}}}r'):
                bold = r.find(f'.//{{{W}}}b') is not None
                t = ''.join(n.text or '' for n in r.findall(f'{{{W}}}t'))
                if t:
                    runs.append(f'<strong>{html_mod.escape(t)}</strong>' if bold else html_mod.escape(t))
            if runs:
                parts.append('<p>' + ''.join(runs) + '</p>')
        return Markup(''.join(parts))

    doc = ET.fromstring(zf.read('word/document.xml'))
    body = doc.find(f'{{{W}}}body')
    elems = list(body)
    tbl = elems[57]  # activities table
    rows = tbl.findall(f'{{{W}}}tr')

    # rows[0] = header, rows[1..7] = activities 1..7
    act_data = {}
    for i, row in enumerate(rows[1:], start=1):
        cells = row.findall(f'.//{{{W}}}tc')
        desc_cell = cells[0] if cells else None
        blips = row.findall(f'.//{BLIP}')
        imgs = [rmap.get(b.get(f'{{{R}}}embed'), '') for b in blips]
        act_data[i] = {
            'text': cell_to_html(desc_cell) if desc_cell else Markup(''),
            'imgs': imgs,
        }

    # Build new descriptions
    ActModel = env['amunet.documento.actividad']
    doc_obj = env['amunet.documento'].search([('codigo', '=', 'PNOGE-010')], limit=1)
    acts = {a.sequence: a for a in ActModel.search([('documento_id', '=', doc_obj.id)])}

    for seq, data in act_data.items():
        if seq not in acts:
            continue
        nueva_desc = data['text']
        for img_file in data['imgs']:
            if img_file:
                nueva_desc = nueva_desc + Markup('<p>') + img_tag(img_file) + Markup('</p>')
        acts[seq].write({'descripcion': nueva_desc})

env.cr.commit()
print('OK — actividades 2-6 de PNOGE-010 corregidas con imágenes')
