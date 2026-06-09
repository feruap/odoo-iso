import zipfile, base64, html as html_mod

path = '/tmp/pnoge/PNOGE-010 Etiquetas de identificación.docx'

with zipfile.ZipFile(path) as zf:
    def img_tag(filename, alt=''):
        data = base64.b64encode(zf.read(f'word/media/{filename}')).decode('ascii')
        return (f'<img src="data:image/png;base64,{data}" '
                f'style="max-width:100%;height:auto;display:block;margin:8px 0;" '
                f'alt="{html_mod.escape(alt)}"/>')

    ActModel = env['amunet.documento.actividad']
    DocModel = env['amunet.documento']
    doc = DocModel.search([('codigo', '=', 'PNOGE-010')], limit=1)
    acts = {a.sequence: a for a in ActModel.search([('documento_id', '=', doc.id)])}

    # Act seq=2: image1 + image2
    a2 = acts[2]
    a2.write({'descripcion': a2.descripcion + f'<p>{img_tag("image1.png")}</p><p>{img_tag("image2.png")}</p>'})

    # Act seq=3: image3
    a3 = acts[3]
    a3.write({'descripcion': a3.descripcion + f'<p>{img_tag("image3.png")}</p>'})

    # Act seq=4: image4 + image5
    a4 = acts[4]
    a4.write({'descripcion': a4.descripcion + f'<p>{img_tag("image4.png")}</p><p>{img_tag("image5.png")}</p>'})

    # Act seq=5: image6
    a5 = acts[5]
    a5.write({'descripcion': a5.descripcion + f'<p>{img_tag("image6.png")}</p>'})

    # Act seq=6: image7 + image8
    a6 = acts[6]
    a6.write({'descripcion': a6.descripcion + f'<p>{img_tag("image7.png")}</p><p>{img_tag("image8.png")}</p>'})

env.cr.commit()
print('OK — imágenes agregadas a actividades 2-6 de PNOGE-010')
