import zipfile, base64, html as html_mod

path = '/tmp/pnoge/PNOGE-007 Vestimenta del personal listo.docx'

with zipfile.ZipFile(path) as zf:
    data = base64.b64encode(zf.read('word/media/image1.png')).decode('ascii')

nuevo_anexos = (
    '<div style="background:#e8f4fd;border-left:4px solid #1565c0;'
    'padding:10px 14px;margin:24px 0 8px 0;border-radius:0 4px 4px 0;">'
    '<strong style="font-size:1.05em;color:#0d47a1;">Anexo 1. Vestimenta de personal</strong></div>'
    f'<p><img src="data:image/png;base64,{data}" '
    'style="max-width:100%;height:auto;display:block;margin:8px 0;" '
    'alt="Vestimenta de personal"/></p>'
)

doc = env['amunet.documento'].search([('codigo', '=', 'PNOGE-007')], limit=1)
doc.write({'seccion_anexos': nuevo_anexos})
env.cr.commit()
print('OK — Anexo 1 con imagen en PNOGE-007')
