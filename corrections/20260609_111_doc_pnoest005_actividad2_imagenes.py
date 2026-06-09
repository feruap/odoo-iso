import base64, zipfile
from markupsafe import Markup

DOCX = '/tmp/PNOEST-005.docx'

def img_tag(zf, img_name):
    data = base64.b64encode(zf.read(f'word/media/{img_name}')).decode()
    ext  = img_name.rsplit('.', 1)[-1].lower()
    mime = 'image/jpeg' if ext == 'jpg' else f'image/{ext}'
    return Markup(f'<img src="data:{mime};base64,{data}" style="max-width:100%;"/>')

with zipfile.ZipFile(DOCX) as zf:
    c1 = img_tag(zf, 'image1.png')   # círculo azul  — 9h
    c2 = img_tag(zf, 'image2.png')   # círculo naranja — 13h
    c3 = img_tag(zf, 'image3.png')   # círculo verde — 18h
    g  = img_tag(zf, 'image4.png')   # gráfica de línea

act2 = Markup('''
<p>Realizar la toma de temperatura basado en la siguiente tabla. En términos comunes la
temperatura se va a redondear dependiendo el valor que registre el termohigrómetro.</p>

<table border="1" style="border-collapse:collapse;width:auto;margin:8px 0;">
  <tr>
    <th style="padding:6px 12px;background:#e3f2fd;">Valor más próximo</th>
    <th style="padding:6px 12px;background:#e3f2fd;">Decimales</th>
  </tr>
  <tr>
    <td style="padding:6px 12px;text-align:center;">1</td>
    <td style="padding:6px 12px;">0.1 / 0.2 / 0.3</td>
  </tr>
  <tr>
    <td style="padding:6px 12px;text-align:center;">1.5</td>
    <td style="padding:6px 12px;">0.4 / 0.5 / 0.6</td>
  </tr>
  <tr>
    <td style="padding:6px 12px;text-align:center;">2</td>
    <td style="padding:6px 12px;">0.7 / 0.8 / 0.9</td>
  </tr>
</table>

<p><strong>Por ejemplo:</strong></p>
<ul>
  <li>''') + c1 + Markup(''' La temperatura a las 09:00 am es de 22.3 °C → se registra en el recuadro de <strong>22 °C</strong>.</li>
  <li>''') + c2 + Markup(''' La temperatura a las 13:00 pm es de 24.7 °C → se registra en el recuadro de <strong>25 °C</strong>.</li>
  <li>''') + c3 + Markup(''' La temperatura a las 18:00 pm es de 23.4 °C → se registra en el recuadro de <strong>23.5 °C</strong>.</li>
</ul>

<p>''') + g + Markup('''</p>
''')

ActModel = env['amunet.documento.actividad']
doc = env['amunet.documento'].search([('codigo', '=', 'PNOEST-005')], limit=1)
acts = {a.sequence: a for a in ActModel.search([('documento_id', '=', doc.id)])}

acts[2].write({'descripcion': act2})
env.cr.commit()
print('OK — Actividad 2 de PNOEST-005 actualizada con imágenes y tabla')
