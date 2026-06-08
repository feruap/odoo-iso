import zipfile, base64, html as html_mod, re
import xml.etree.ElementTree as ET

NS = {'w':  'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
      'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
      'a':  'http://schemas.openxmlformats.org/drawingml/2006/main',
      'r':  'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}

path = '/tmp/pnopr/PNOPR-003.docx'

with zipfile.ZipFile(path) as zf:
    # Mapa rId → datos base64 de imagen
    rels = ET.fromstring(zf.read('word/_rels/document.xml.rels'))
    rmap = {}
    for rel in rels:
        if 'image' in rel.get('Type', ''):
            rid = rel.get('Id')
            target = rel.get('Target')
            img_path = 'word/' + target if not target.startswith('word/') else target
            data = base64.b64encode(zf.read(img_path)).decode('ascii')
            rmap[rid] = f'data:image/png;base64,{data}'

    root = ET.fromstring(zf.read('word/document.xml'))
    body = root.find('.//w:body', NS)

    html_parts = []
    in_anexos = False

    for child in body:
        tag = child.tag.split('}')[-1]
        if tag == 'p':
            text = ''.join(t.text or '' for t in child.findall('.//w:t', NS)).strip()
            tu = text.upper()

            if 'ANEXOS' == tu:
                in_anexos = True
                continue
            if in_anexos and tu in ('CONTROL DE CAMBIOS', 'FIRMAS DE CONOCIMIENTO'):
                break
            if not in_anexos:
                continue

            # ¿tiene imagen?
            blips = child.findall('.//{http://schemas.openxmlformats.org/drawingml/2006/main}blip')
            if blips:
                for blip in blips:
                    rid = blip.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
                    src = rmap.get(rid, '')
                    if src:
                        html_parts.append(
                            f'<p><img src="{src}" '
                            f'style="max-width:100%;height:auto;display:block;margin:8px 0;" '
                            f'alt="{html_mod.escape(text)}"/></p>'
                        )
                continue

            if not text:
                continue

            # Encabezados Anexo N
            if re.match(r'^Anexo\s+\d+', text):
                html_parts.append(f'<h3>{html_mod.escape(text)}</h3>')
            else:
                # Bold si tiene formato bold en runs
                runs = child.findall('.//w:r', NS)
                is_bold = any(r.find('w:rPr/w:b', NS) is not None for r in runs)
                if is_bold:
                    html_parts.append(f'<p><strong>{html_mod.escape(text)}</strong></p>')
                else:
                    html_parts.append(f'<p>{html_mod.escape(text)}</p>')

html_anexos = ''.join(html_parts)

# Actualizar en Odoo
DocModel = env['amunet.documento']
doc = DocModel.search([('codigo', '=', 'PNOPR-003')], limit=1)
if not doc:
    print('NO ENCONTRADO')
else:
    doc.write({'seccion_anexos': html_anexos})
    env.cr.commit()
    img_count = html_anexos.count('<img ')
    print(f'OK PNOPR-003 | {img_count} imagenes incluidas | {len(html_anexos)} chars')
