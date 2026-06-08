import zipfile, base64

path = '/tmp/pnoge/PNOGE-002 BPD ver 03.docx'
with zipfile.ZipFile(path) as zf:
    data = base64.b64encode(zf.read('word/media/image2.png')).decode('ascii')
img_src = f'data:image/png;base64,{data}'

act7 = (
    '<p>En caso de contar con espacios en blanco que no sean utilizados, '
    'cancelar de la siguiente forma:</p>'
    '<ul>'
    '<li>Trazar una línea que abarque el espacio en blanco.</li>'
    '<li>Colocar antefirma (inicial del nombre y primer apellido) de la persona '
    'que va a realizar la cancelación y fecha en que se realizó.</li>'
    '</ul>'
    '<p><strong>Ejemplo:</strong></p>'
    f'<p><img src="{img_src}" style="max-width:100%;height:auto;display:block;margin:8px 0;" alt="Ejemplo cancelación espacio en blanco"/></p>'
)

DocModel = env['amunet.documento']
ActModel = env['amunet.documento.actividad']
doc = DocModel.search([('codigo', '=', 'PNOGE-002')], limit=1)
acts = ActModel.search([('documento_id', '=', doc.id)], order='sequence')
acts[6].write({'descripcion': act7})
env.cr.commit()
print('OK — actividad 7 actualizada con imagen del ejemplo')
