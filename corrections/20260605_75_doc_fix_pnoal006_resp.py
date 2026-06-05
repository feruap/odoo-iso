import re, zipfile
import xml.etree.ElementTree as ET

env = env  # noqa

NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

with zipfile.ZipFile('/tmp/pnoal/PNOAL-006.docx') as zf:
    root = ET.fromstring(zf.read('word/document.xml'))
    texts = [''.join(r.text or '' for r in p.findall('.//w:t', NS)).strip()
             for p in root.findall('.//w:p', NS)]

start = next((i+1 for i, t in enumerate(texts) if t == 'RESPONSABILIDADES'), None)
rows = []
for t in texts[start:]:
    if re.match(r'^(TÉRMINOS|TERMINOS|CONDICIONES)', t, re.I):
        break
    if t and re.match(r'^Del? ', t, re.I):
        parts = re.split(r',\s*', t, maxsplit=1)
        rows.append({'rol': parts[0], 'descripcion': parts[1] if len(parts) > 1 else ''})

doc = env['amunet.documento'].search([('codigo', '=', 'PNOAL-006')], limit=1)
doc.responsabilidad_ids.unlink()
for seq, r in enumerate(rows, 1):
    env['amunet.documento.responsabilidad'].create({
        'documento_id': doc.id,
        'sequence': seq,
        'rol': r['rol'],
        'descripcion': r['descripcion'],
    })
env.cr.commit()
print(f"OK PNOAL-006 | {len(rows)} resp")
print("DONE")
