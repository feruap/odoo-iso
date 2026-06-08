import zipfile, base64, html as html_mod
import xml.etree.ElementTree as ET

NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
BLIP_TAG   = '{http://schemas.openxmlformats.org/drawingml/2006/main}blip'
EMBED_ATTR = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed'

path = '/tmp/pnoal/PNOAL-002.docx'

with zipfile.ZipFile(path) as zf:
    rels = ET.fromstring(zf.read('word/_rels/document.xml.rels'))
    rmap_file = {rel.get('Id'): rel.get('Target')
                 for rel in rels if 'image' in rel.get('Type', '')}
    rmap_b64 = {}
    for rid, target in rmap_file.items():
        img_path = 'word/' + target if not target.startswith('word/') else target
        ext = img_path.rsplit('.', 1)[-1].lower()
        mime = 'image/png' if ext == 'png' else f'image/{ext}'
        data = base64.b64encode(zf.read(img_path)).decode('ascii')
        rmap_b64[rid] = f'data:{mime};base64,{data}'

    # Mapeo Anexo N → src base64
    # Orden según el documento: image1=Anexo1, image2=Anexo2 ... image5=Anexo5
    file_to_b64 = {}
    for rid, target in rmap_file.items():
        file_to_b64[target] = rmap_b64[rid]

    def img_tag(target, alt='', inline=False):
        src = file_to_b64.get(target, '')
        if not src: return ''
        style = ('max-height:40px;vertical-align:middle;margin:0 6px;'
                 if inline else
                 'max-width:300px;height:auto;display:block;margin:8px 0;')
        return f'<img src="{src}" style="{style}" alt="{html_mod.escape(alt)}"/>'

    anexo1 = 'media/image1.png'  # etiqueta identificación
    anexo2 = 'media/image2.png'  # círculo amarillo cuarentena
    anexo3 = 'media/image3.png'  # círculo verde aprobado
    anexo4 = 'media/image4.png'  # círculo rojo rechazado
    anexo5 = 'media/image5.png'  # diagrama marcado

    # ── ACTIVIDAD 3 ──────────────────────────────────────────────────────────
    act3 = (
        '<p><strong>Identificación de producto</strong></p>'
        '<p>Colocar etiquetas de identificación a los empaques o contenedores de cada lote '
        'de insumos. Ver anexo 1</p>'
        + f'<p>{img_tag(anexo1, "Etiqueta de identificación")}</p>'
        + '<p>Adicional a la etiqueta de identificación colocar una etiqueta circular color '
        'amarillo, la cual indica que el insumo se encuentra en cuarentena. '
        + img_tag(anexo2, 'Círculo amarillo - cuarentena', inline=True)
        + '</p>'
    )

    # ── ACTIVIDAD 6 ──────────────────────────────────────────────────────────
    act6 = (
        '<p><strong>Resguardo (ubicación)</strong></p>'
        '<p>Realizar el registro del nuevo estatus del insumo analizado en el formato '
        'F-AL-002/001 Entradas, salidas y conciliación de insumos.</p>'
        '<p>Una vez reubicado el insumo en el resguardo correspondiente, la(s) bolsa(s) o '
        'paquete(s) del lote ingresado debe(n) marcarse con una etiqueta circular de acuerdo '
        'a las siguientes especificaciones:</p>'
        '<p>Etiqueta circular color verde para producto aprobado. '
        + img_tag(anexo3, 'Círculo verde - aprobado', inline=True)
        + '</p>'
        '<p>Etiqueta circular color rojo para producto rechazado. '
        + img_tag(anexo4, 'Círculo rojo - rechazado', inline=True)
        + '</p>'
        '<p>Esta etiqueta circular debe colocarse a un costado de la etiqueta de '
        'identificación y no sobre la misma.</p>'
        '<p>El propósito de estos círculos es identificar y registrar que el insumo se '
        'encuentra aprobado o rechazado dentro del área correspondiente, así como definir '
        'el orden de consumo de los mismos (para el caso de insumos aprobados).</p>'
    )

    # ── ACTIVIDAD 7 ──────────────────────────────────────────────────────────
    act7 = (
        '<p>La etiqueta circular color rojo, de insumos rechazados, no debe contener alguna '
        'marca o indicación. '
        + img_tag(anexo4, 'Círculo rojo - rechazado', inline=True)
        + '</p>'
        '<p>La etiqueta circular color verde, de insumos aprobados, debe marcarse de acuerdo '
        'al siguiente sistema: '
        + img_tag(anexo3, 'Círculo verde - aprobado', inline=True)
        + '</p>'
        '<p><strong>1.1 | 1.1</strong></p>'
        '<p>Donde:</p>'
        '<p>El primer número indica el número de lote ingresado, este número es consecutivo '
        'para cada lote aprobado, de cada insumo.</p>'
        '<p>El segundo número corresponde a la cantidad de bolsas o paquetes que conforman '
        'el lote, de ser el caso.</p>'
        '<p>El orden para marcar las bolsas o paquetes de los insumos ingresados al resguardo '
        'de producto aprobado se debe realizar de acuerdo al siguiente ejemplo:</p>'
        + f'<p>{img_tag(anexo5, "Diagrama de marcado de lotes")}</p>'
        + '<p>Si ya se encuentran resguardados lotes del insumo, las bolsas o paquetes '
        'ingresados se deben numerar y colocar de manera consecutiva. Suponiendo que existan '
        'paquetes de lotes con la siguiente numeración en la etiqueta: 5.1, 6.1, 6.2, 6.3 y '
        '7.1; y suponiendo que se van a ingresar dos paquetes de un nuevo lote, los paquetes '
        'nuevos se identifican de la siguiente forma: 8.1 y 8.2.</p>'
    )

    # ── ANEXOS completos ──────────────────────────────────────────────────────
    anexos_html = (
        '<h3>Anexo 1 — Etiqueta de identificación</h3>'
        + f'<p>{img_tag(anexo1, "Etiqueta de identificación")}</p>'
        + '<h3>Anexo 2 — Etiqueta circular amarillo (cuarentena)</h3>'
        + f'<p>{img_tag(anexo2, "Círculo amarillo - cuarentena")}</p>'
        + '<h3>Anexo 3 — Etiqueta circular verde (aprobado)</h3>'
        + f'<p>{img_tag(anexo3, "Círculo verde - aprobado")}</p>'
        + '<h3>Anexo 4 — Etiqueta circular rojo (rechazado)</h3>'
        + f'<p>{img_tag(anexo4, "Círculo rojo - rechazado")}</p>'
        + '<h3>Anexo 5 — Diagrama de marcado de lotes</h3>'
        + f'<p>{img_tag(anexo5, "Diagrama de marcado")}</p>'
    )

# ── Actualizar en Odoo ────────────────────────────────────────────────────────
DocModel = env['amunet.documento']
ActModel = env['amunet.documento.actividad']

doc = DocModel.search([('codigo', '=', 'PNOAL-002')], limit=1)
if not doc:
    print('PNOAL-002 no encontrado'); exit()

acts = ActModel.search([('documento_id', '=', doc.id)], order='sequence')
print(f'Total actividades: {len(acts)}')

acts[2].write({'descripcion': act3})
acts[5].write({'descripcion': act6})
acts[6].write({'descripcion': act7})
doc.write({'seccion_anexos': anexos_html})
env.cr.commit()
print('OK PNOAL-002 — actividades 3/6/7 con círculos + 5 Anexos guardados')
