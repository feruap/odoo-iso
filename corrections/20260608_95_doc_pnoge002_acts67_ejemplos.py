import zipfile, base64, html as html_mod
import xml.etree.ElementTree as ET

NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

path = '/tmp/pnoge/PNOGE-002 BPD ver 03.docx'

with zipfile.ZipFile(path) as zf:
    rels = ET.fromstring(zf.read('word/_rels/document.xml.rels'))
    file_to_b64 = {}
    for rel in rels:
        if 'image' in rel.get('Type', ''):
            target = rel.get('Target')
            img_path = 'word/' + target if not target.startswith('word/') else target
            ext = img_path.rsplit('.', 1)[-1].lower()
            mime = f'image/{ext}'
            data = base64.b64encode(zf.read(img_path)).decode('ascii')
            file_to_b64[target] = f'data:{mime};base64,{data}'

ej = 'style="background:#f5f5f5;border-left:3px solid #1976d2;padding:6px 12px;margin:4px 0;"'

img_ejemplo_act6 = (
    f'<img src="{file_to_b64.get("media/image1.png","")}" '
    f'style="max-width:100%;height:auto;display:block;margin:8px 0;" '
    f'alt="Ejemplo de corrección"/>'
)

act6 = (
    '<p><strong>Queda PROHIBIDO</strong></p>'
    '<p>En caso de cometer errores durante el llenado de los documentos NO realizar lo siguiente:</p>'
    '<ul>'
    '<li>Borrar.</li>'
    '<li>Sobre escribir la información.</li>'
    '<li>Utilizar corrector ni etiquetas.</li>'
    '<li>Tratar de eliminar la información errónea.</li>'
    '</ul>'
    '<p>Corregir los errores de la siguiente manera:</p>'
    '<ul>'
    '<li>Trazar una línea que abarque la información errónea.</li>'
    '<li>Colocar antefirma (inicial del nombre y primer apellido) de la persona que '
    'realizó la corrección y fecha en que se realizó.</li>'
    '<li>Anotar la información correcta lo más cercano posible de la corrección, '
    'asegurándose de que el registro original y la corrección sean legibles.</li>'
    '</ul>'
    '<p><strong>Ejemplo:</strong></p>'
    + img_ejemplo_act6 +
    '<p><em>Nota 01: En caso de que el espacio no sea suficiente, colocar un asterisco * '
    'seguido de un número consecutivo y posteriormente, en la parte inferior o lo más '
    'cerca posible del error, colocar el número y la información correspondiente.</em></p>'
)

act7 = (
    '<p>En caso de contar con espacios en blanco que no sean utilizados, '
    'cancelar de la siguiente forma:</p>'
    '<ul>'
    '<li>Trazar una línea que abarque el espacio en blanco.</li>'
    '<li>Colocar antefirma (inicial del nombre y primer apellido) de la persona que '
    'va a realizar la cancelación y fecha en que se realizó.</li>'
    '</ul>'
    '<p><strong>Ejemplo:</strong></p>'
    f'<p {ej}>B. Jiménez &nbsp; 23.05.19</p>'
    '<p>Cuando el espacio en blanco sea una celda dentro de un registro, '
    'la cancelación se realiza de la misma forma:</p>'
    '<table border="1" style="border-collapse:collapse;width:100%;font-size:inherit;">'
    '<tbody>'
    '<tr>'
    '<th style="padding:6px;background:#f0f0f0;">Fecha</th>'
    '<th style="padding:6px;background:#f0f0f0;">Solución</th>'
    '<th style="padding:6px;background:#f0f0f0;">Cantidad</th>'
    '</tr>'
    '<tr>'
    '<td style="padding:6px;">23.04.24</td>'
    '<td style="padding:6px;color:#999;text-align:center;">———</td>'
    '<td style="padding:6px;">35 mL</td>'
    '</tr>'
    '</tbody>'
    '</table>'
)

DocModel = env['amunet.documento']
ActModel = env['amunet.documento.actividad']
doc = DocModel.search([('codigo', '=', 'PNOGE-002')], limit=1)
acts = ActModel.search([('documento_id', '=', doc.id)], order='sequence')
acts[5].write({'descripcion': act6})
acts[6].write({'descripcion': act7})
env.cr.commit()
print('OK — PNOGE-002 actividades 6 y 7 corregidas')
