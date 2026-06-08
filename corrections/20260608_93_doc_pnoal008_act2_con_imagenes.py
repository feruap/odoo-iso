import zipfile, base64, html as html_mod
import xml.etree.ElementTree as ET

NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
      'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}

path = '/tmp/pnoal/PNOAL-008.docx'

with zipfile.ZipFile(path) as zf:
    rels = ET.fromstring(zf.read('word/_rels/document.xml.rels'))
    rmap = {}
    for rel in rels:
        if 'image' in rel.get('Type', ''):
            rid = rel.get('Id')
            target = rel.get('Target')
            img_path = 'word/' + target if not target.startswith('word/') else target
            ext = img_path.rsplit('.', 1)[-1].lower()
            mime = 'image/png' if ext == 'png' else f'image/{ext}'
            data = base64.b64encode(zf.read(img_path)).decode('ascii')
            rmap[rid] = f'data:{mime};base64,{data}'

    def run_to_html(r):
        rpr = r.find('w:rPr', NS)
        text = html_mod.escape(''.join((t.text or '') for t in r.findall('w:t', NS)))
        if not text: return ''
        if rpr is not None:
            if rpr.find('w:b', NS) is not None: text = f'<strong>{text}</strong>'
            if rpr.find('w:i', NS) is not None: text = f'<em>{text}</em>'
        return text

    def get_blip_src(node):
        for b in node.findall('.//{http://schemas.openxmlformats.org/drawingml/2006/main}blip'):
            rid = b.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed', '')
            if rid in rmap: return rmap[rid]
        return None

    def para_to_html_with_img(p):
        runs_html = ''.join(run_to_html(r) for r in p.findall('.//w:r', NS))
        img_src = get_blip_src(p)
        parts = []
        if runs_html.strip(): parts.append(runs_html)
        if img_src:
            parts.append(f'<img src="{img_src}" style="max-width:100%;height:auto;vertical-align:middle;margin:0 4px;" alt=""/>')
        return f'<p>{"".join(parts)}</p>' if parts else ''

    def table_to_html(tbl):
        rows = tbl.findall('w:tr', NS)
        if not rows: return ''
        html_rows = []
        for i, row in enumerate(rows):
            tag = 'th' if i == 0 else 'td'
            cells = row.findall('w:tc', NS)
            html_rows.append('<tr>' + ''.join(
                f'<{tag} style="padding:4px;border:1px solid #ccc;">' +
                html_mod.escape(''.join(t.text or '' for t in c.findall('.//w:t', NS)).strip()) +
                f'</{tag}>' for c in cells) + '</tr>')
        return '<table style="border-collapse:collapse;width:100%;font-size:inherit;">' + ''.join(html_rows) + '</table>'

    def cell_to_html_with_imgs(cell):
        parts = []; in_list = False
        for child in cell:
            tag = child.tag.split('}')[-1]
            if tag == 'p':
                h = para_to_html_with_img(child)
                if not h: continue
                if in_list: parts.append('</ul>'); in_list = False
                parts.append(h)
            elif tag == 'tbl':
                if in_list: parts.append('</ul>'); in_list = False
                th = table_to_html(child)
                if th: parts.append(th)
        if in_list: parts.append('</ul>')
        return ''.join(parts)

    root = ET.fromstring(zf.read('word/document.xml'))
    new_desc = ''
    for tbl in root.findall('.//w:tbl', NS):
        rows = tbl.findall('w:tr', NS)
        if len(rows) < 2: continue
        hdr = ''.join(t.text or '' for t in rows[0].findall('.//w:t', NS)).upper()
        if 'VERSIÓN' in hdr or 'VERSION' in hdr: continue
        if not any(k in hdr for k in ('ACTIVIDAD','DESCRIPCI','PASO')): continue
        cells = rows[2].findall('w:tc', NS)  # rows[2] = actividad 2
        new_desc = cell_to_html_with_imgs(cells[1])
        break

img_count = new_desc.count('<img ')
print(f"HTML: {len(new_desc)} chars | {img_count} imágenes")

DocModel = env['amunet.documento']
ActModel = env['amunet.documento.actividad']
doc = DocModel.search([('codigo', '=', 'PNOAL-008')], limit=1)
if not doc:
    print('PNOAL-008 no encontrado'); exit()
acts = ActModel.search([('documento_id', '=', doc.id)], order='sequence')
acts[1].write({'descripcion': new_desc})
env.cr.commit()
print(f'OK PNOAL-008 — actividad 2 actualizada con {img_count} imágenes')
