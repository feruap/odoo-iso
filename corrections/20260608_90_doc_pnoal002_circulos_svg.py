import zipfile, base64, html as html_mod
import xml.etree.ElementTree as ET

NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
BLIP_TAG   = '{http://schemas.openxmlformats.org/drawingml/2006/main}blip'
EMBED_ATTR = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed'

path = '/tmp/pnoal/PNOAL-002.docx'

with zipfile.ZipFile(path) as zf:
    rels = ET.fromstring(zf.read('word/_rels/document.xml.rels'))
    rmap_file = {rel.get('Id'): rel.get('Target') for rel in rels if 'image' in rel.get('Type','')}
    rmap_b64 = {}
    for rid, target in rmap_file.items():
        img_path = 'word/' + target if not target.startswith('word/') else target
        ext = img_path.rsplit('.', 1)[-1].lower()
        mime = 'image/png' if ext == 'png' else f'image/{ext}'
        data = base64.b64encode(zf.read(img_path)).decode('ascii')
        rmap_b64[rid] = f'data:{mime};base64,{data}'
    file_to_b64 = {target: rmap_b64[rid] for rid, target in rmap_file.items()}

def img_tag(target, alt=''):
    src = file_to_b64.get(target, '')
    if not src: return ''
    return f'<img src="{src}" style="max-width:100%;height:auto;display:block;margin:8px 0;" alt="{html_mod.escape(alt)}"/>'

# Círculos SVG inline
circulo_amarillo = (
    '<svg width="32" height="32" style="vertical-align:middle;margin:0 6px;" '
    'xmlns="http://www.w3.org/2000/svg">'
    '<circle cx="16" cy="16" r="14" fill="#FFD700" stroke="#B8860B" stroke-width="1.5"/>'
    '</svg>'
)
circulo_verde = (
    '<svg width="32" height="32" style="vertical-align:middle;margin:0 6px;" '
    'xmlns="http://www.w3.org/2000/svg">'
    '<circle cx="16" cy="16" r="14" fill="#4CAF50" stroke="#2E7D32" stroke-width="1.5"/>'
    '</svg>'
)
circulo_rojo = (
    '<svg width="32" height="32" style="vertical-align:middle;margin:0 6px;" '
    'xmlns="http://www.w3.org/2000/svg">'
    '<circle cx="16" cy="16" r="14" fill="#F44336" stroke="#B71C1C" stroke-width="1.5"/>'
    '</svg>'
)

anexo1 = 'media/image1.png'
anexo2 = 'media/image2.png'
anexo3 = 'media/image3.png'
anexo4 = 'media/image4.png'
anexo5 = 'media/image5.png'

act3 = (
    '<p><strong>Identificación de producto</strong></p>'
    '<p>Colocar etiquetas de identificación a los empaques o contenedores de cada lote '
    'de insumos. Ver anexo 1</p>'
    + f'<p>{img_tag(anexo1, "Etiqueta de identificación")}</p>'
    + '<p>Adicional a la etiqueta de identificación colocar una etiqueta circular color '
    'amarillo ' + circulo_amarillo + ', la cual indica que el insumo se encuentra en cuarentena.</p>'
)

act6 = (
    '<p><strong>Resguardo (ubicación)</strong></p>'
    '<p>Realizar el registro del nuevo estatus del insumo analizado en el formato '
    'F-AL-002/001 Entradas, salidas y conciliación de insumos.</p>'
    '<p>Una vez reubicado el insumo en el resguardo correspondiente, la(s) bolsa(s) o '
    'paquete(s) del lote ingresado debe(n) marcarse con una etiqueta circular de acuerdo '
    'a las siguientes especificaciones:</p>'
    '<p>Etiqueta circular color verde para producto aprobado. ' + circulo_verde + '</p>'
    '<p>Etiqueta circular color rojo para producto rechazado. ' + circulo_rojo + '</p>'
    '<p>Esta etiqueta circular debe colocarse a un costado de la etiqueta de '
    'identificación y no sobre la misma.</p>'
    '<p>El propósito de estos círculos es identificar y registrar que el insumo se '
    'encuentra aprobado o rechazado dentro del área correspondiente, así como definir '
    'el orden de consumo de los mismos (para el caso de insumos aprobados).</p>'
)

act7 = (
    '<p>La etiqueta circular color rojo, de insumos rechazados, no debe contener alguna '
    'marca o indicación. ' + circulo_rojo + '</p>'
    '<p>La etiqueta circular color verde, de insumos aprobados, debe marcarse de acuerdo '
    'al siguiente sistema: ' + circulo_verde + '</p>'
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

DocModel = env['amunet.documento']
ActModel = env['amunet.documento.actividad']

doc = DocModel.search([('codigo', '=', 'PNOAL-002')], limit=1)
acts = ActModel.search([('documento_id', '=', doc.id)], order='sequence')

acts[2].write({'descripcion': act3})
acts[5].write({'descripcion': act6})
acts[6].write({'descripcion': act7})
env.cr.commit()
print('OK — círculos SVG amarillo/verde/rojo en actividades 3/6/7')
