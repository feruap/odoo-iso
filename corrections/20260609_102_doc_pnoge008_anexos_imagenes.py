import zipfile, base64, html as html_mod

path = '/tmp/pnoge/PNOGE-008 Diseño de flujo listo.docx'

with zipfile.ZipFile(path) as zf:
    def img_tag(filename, alt=''):
        data = base64.b64encode(zf.read(f'word/media/{filename}')).decode('ascii')
        return (f'<img src="data:image/png;base64,{data}" '
                f'style="max-width:100%;height:auto;display:block;margin:8px 0;" '
                f'alt="{html_mod.escape(alt)}"/>')

    hdr = lambda n, titulo: (
        '<div style="background:#e8f4fd;border-left:4px solid #1565c0;'
        'padding:10px 14px;margin:24px 0 8px 0;border-radius:0 4px 4px 0;">'
        f'<strong style="font-size:1.05em;color:#0d47a1;">Anexo {n}. {titulo}</strong></div>'
    )

    nuevo_anexos = (
        hdr(1, 'Flujo de personal')
        + f'<p>{img_tag("image1.png", "Flujo de personal")}</p>'
        + hdr(2, 'Flujo de insumos')
        + f'<p>{img_tag("image2.png", "Flujo de insumos")}</p>'
        + hdr(3, 'Flujo de producto en proceso')
        + f'<p>{img_tag("image3.png", "Flujo de producto en proceso")}</p>'
        + hdr(4, 'Flujo de producto terminado')
        + f'<p>{img_tag("image4.png", "Flujo de producto terminado")}</p>'
        + hdr(5, 'Flujo de desechos (RPBI/Urbanos)')
        + f'<p>{img_tag("image5.png", "Flujo de desechos RPBI")}</p>'
        + f'<p>{img_tag("image6.png", "Flujo de desechos Urbanos")}</p>'
    )

doc = env['amunet.documento'].search([('codigo', '=', 'PNOGE-008')], limit=1)
doc.write({'seccion_anexos': nuevo_anexos})
env.cr.commit()
print('OK — 5 anexos con imágenes en PNOGE-008')
